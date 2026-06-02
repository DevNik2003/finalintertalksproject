"""
Query Service — production-grade retrieval pipeline.

Pipeline:
  1. Multi-variant query expansion (short queries)
  2. Embed ALL variants, average vectors
  3. Search Qdrant (APPROVED only, top_k=10 for re-ranking pool)
  4. Compute composite score per chunk:
       final = 0.4×semantic + 0.3×keyword + 0.2×title_match + 0.1×exact_match
  5. Sort by final_score, select top 1–2
  6. Strict filter: discard if semantic < threshold AND keyword == 0
  7. Log full debug info (per-chunk scores)
"""

from typing import Dict, Any, List, Set
from uuid import UUID
from sqlalchemy.orm import Session
from collections import defaultdict
from sentence_transformers import CrossEncoder
import re
import logging

from app.services.embedding_service import EmbeddingService
from app.repositories.embedding_repository import EmbeddingRepository
from app.models.document import QueryAuditLog
from app.models.user import User

logger = logging.getLogger(__name__)


# ── Configuration ───────────────────────────────────────────────
TOP_K = 10  # Retrieve 10 candidates for re-ranking

# Adaptive thresholds
THRESHOLD_SHORT = 0.40   # < 4 words (lowered — re-ranking handles precision)
THRESHOLD_MEDIUM = 0.50  # 4-8 words
THRESHOLD_LONG = 0.60    # > 8 words

# Re-ranking weights
W_SEMANTIC = 0.4
W_KEYWORD = 0.3
W_TITLE = 0.2
W_EXACT = 0.1

# Minimum final score to accept
MIN_FINAL_SCORE = 0.20

# Stop words for keyword matching
_STOP_WORDS: Set[str] = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'shall', 'can', 'must', 'need',
    'and', 'or', 'but', 'if', 'then', 'else', 'when', 'where', 'how',
    'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
    'to', 'of', 'in', 'on', 'at', 'by', 'for', 'with', 'from', 'about',
    'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'not', 'no', 'nor', 'so', 'too', 'very', 'just', 'also', 'only',
    'such', 'than', 'both', 'each', 'all', 'any', 'few', 'more', 'most',
    'other', 'some', 'its', 'own', 'same', 'as', 'per', 'etc',
    'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'she', 'it',
    'they', 'them', 'their', 'his', 'her', 'get', 'many', 'much'
}


class QueryService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService(db)
        self.embedding_repo = EmbeddingRepository()
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    def execute_query(self, query_text: str, current_user: User) -> Dict[str, Any]:
        """Execute the full retrieval pipeline with re-ranking."""
        original_query = query_text.strip()
        word_count = len(original_query.split())
        query_keywords = self._extract_query_keywords(original_query)

        # ── Step 1: Multi-variant expansion ─────────────────────
        variants = self._expand_query(original_query)

        # ── Step 2: Adaptive threshold ──────────────────────────
        threshold = self._get_adaptive_threshold(word_count)

        # ── Step 3: Embed all variants, average vectors ─────────
        query_embedding = self._embed_multi_variant(variants)

        # ── Step 4: Search Qdrant (APPROVED only, top 10) ───────
        results = self.embedding_repo.search_similar(
            query_embedding=query_embedding,
            limit=TOP_K
        )

        # ── Step 5: No results → Refuse ─────────────────────────
        if not results:
            self._log_query_audit(
                user_id=current_user.id,
                query_text=original_query,
                top_similarity=0.0,
                result_status="REFUSED_NO_RESULTS",
                metadata={
                    "reason": "No approved chunks found",
                    "variants": variants,
                    "threshold": threshold
                }
            )
            return {
                "status": "refused",
                "reason": "No approved content found to answer this query.",
                "answer": None,
                "citations": []
            }

        # ── Step 6: Re-rank with composite scoring ──────────────
        scored_results = self._rerank_results(results, original_query, query_keywords)

        # ── Step 7: Debug log ALL scored chunks ─────────────────
        debug_chunks = [
            {
                "section_title": r["section_title"],
                "semantic": round(r["similarity"], 4),
                "keyword": round(r["keyword_score"], 4),
                "title_match": round(r["title_score"], 4),
                "exact_match": round(r["exact_score"], 4),
                "final_score": round(r["final_score"], 4)
            }
            for r in scored_results
        ]
        logger.info(f"Query: '{original_query}' | Variants: {variants} | Scored chunks: {debug_chunks}")

        # ── Step 8: Filter — discard noise ──────────────────────
        # Strict: discard if semantic < threshold AND keyword == 0
        filtered = [
            r for r in scored_results
            if not (r["similarity"] < threshold and r["keyword_score"] == 0)
        ]

        # Also enforce minimum final score
        filtered = [r for r in filtered if r["final_score"] >= MIN_FINAL_SCORE]

        if not filtered:
            top_sim = scored_results[0]["similarity"] if scored_results else 0.0
            self._log_query_audit(
                user_id=current_user.id,
                query_text=original_query,
                top_similarity=top_sim,
                result_status="REFUSED_LOW_RELEVANCE",
                metadata={
                    "reason": "No chunk passed re-ranking filters.",
                    "threshold": threshold,
                    "min_final_score": MIN_FINAL_SCORE,
                    "variants": variants,
                    "scored_chunks": debug_chunks[:5]
                }
            )
            return {
                "status": "refused",
                "reason": "Insufficient approved evidence found.",
                "answer": None,
                "citations": []
            }

        # ── Step 9: Cross-encoder re-ranking (precision) ────────
        if filtered:
            # Cross-encoder picks the single best chunk
            selected = self._cross_encoder_rerank(original_query, filtered, top_k=1)
        else:
            selected = []

        # If cross-encoder returns nothing, fallback to composite scoring selection
        if not selected:
            selected = self._select_top_chunks(filtered)

        # Optionally add a 2nd chunk if it's from the same doc and very close in relevance
        if len(selected) == 1 and len(filtered) > 1:
            top = selected[0]
            for candidate in filtered:
                if candidate["chunk_id"] == top["chunk_id"]:
                    continue
                same_doc = candidate["document_id"] == top["document_id"]
                close_cross = abs(top.get("cross_score", 0) - candidate.get("cross_score", -99)) < 2.0
                decent_score = candidate["final_score"] >= 0.40
                if same_doc and close_cross and decent_score:
                    selected.append(candidate)
                break  # Only consider the next best

        # ── Step 10: Conflict detection ───────────────────────────
        conflict = self._detect_conflicts(selected, threshold) if selected else None

        # ── Step 11: Construct answer ───────────────────────────
        answer_parts = []
        citations = []

        for result in selected:
            answer_parts.append(result["content"])
            citations.append({
                "document": result["document_title"],
                "version": result["version_number"],
                "section": result["section_title"],
                "section_number": result["section_number"],
                "chunk_id": result["chunk_id"],
                "similarity": round(result["final_score"], 4)
            })

        answer = "\n\n".join(answer_parts)

        # ── Step 12: Audit log with full debug ──────────────────
        self._log_query_audit(
            user_id=current_user.id,
            query_text=original_query,
            top_similarity=selected[0]["similarity"],
            result_status="SUCCESS",
            metadata={
                "chunks_returned": len(selected),
                "top_final_score": round(selected[0]["final_score"], 4),
                "threshold": threshold,
                "variants": variants,
                "sections_used": [s["section_title"] for s in selected],
                "scored_chunks": debug_chunks[:5]
            }
        )

        self.db.commit()

        return {
            "status": "success",
            "reason": None,
            "answer": answer,
            "citations": citations
        }

    # ══════════════════════════════════════════════════════════════
    # ── QUERY EXPANSION ──────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════

    def _expand_query(self, query: str) -> List[str]:
        """
        Multi-variant expansion for short queries (<4 words).
        Returns list of query variants to embed and average.
        """
        words = query.split()
        if len(words) >= 4:
            return [query]

        return [
            query,
            f"{query} policy",
            f"{query} rules",
            f"{query} eligibility",
            f"What is the company policy regarding {query}?"
        ]

    def _embed_multi_variant(self, variants: List[str]) -> List[float]:
        """
        Embed all query variants and average the vectors.
        This gives a stronger, more robust semantic signal.
        """
        if len(variants) == 1:
            return self.embedding_service.embed_query(variants[0])

        import numpy as np

        embeddings = []
        for variant in variants:
            emb = self.embedding_service.embed_query(variant)
            embeddings.append(emb)

        # Average all variant embeddings
        avg = np.mean(embeddings, axis=0)
        # Normalize to unit vector (cosine similarity expects this)
        norm = np.linalg.norm(avg)
        if norm > 0:
            avg = avg / norm
        return avg.tolist()

    def _extract_query_keywords(self, query: str) -> Set[str]:
        """Extract meaningful keywords from query (stop-word filtered)."""
        words = set(re.findall(r'[a-zA-Z]{2,}', query.lower()))
        return words - _STOP_WORDS

    def _get_adaptive_threshold(self, word_count: int) -> float:
        """Return semantic similarity threshold based on query length."""
        if word_count < 4:
            return THRESHOLD_SHORT
        elif word_count <= 8:
            return THRESHOLD_MEDIUM
        else:
            return THRESHOLD_LONG

    # ══════════════════════════════════════════════════════════════
    # ── RE-RANKING (COMPOSITE SCORING) ───────────────────────────
    # ══════════════════════════════════════════════════════════════

    # def _rerank_results(
    #     self,
    #     results: List[Dict],
    #     query: str,
    #     query_keywords: Set[str]
    # ) -> List[Dict]:
    #     """
    #     Re-rank results using composite score:
    #       final = 0.4×semantic + 0.3×keyword + 0.2×title_match + 0.1×exact_match
    #     """
    #     query_lower = query.lower()

    #     for result in results:
    #         semantic = result["similarity"]
    #         keyword = self._compute_keyword_score(result, query_keywords)
    #         title = self._compute_title_score(result, query_keywords)
    #         exact = self._compute_exact_match(result, query_lower)

    #         final = (
    #             W_SEMANTIC * semantic +
    #             W_KEYWORD * keyword +
    #             W_TITLE * title +
    #             W_EXACT * exact
    #         )

    #         result["keyword_score"] = keyword
    #         result["title_score"] = title
    #         result["exact_score"] = exact
    #         result["final_score"] = final

    #     # Sort by final_score descending
    #     results.sort(key=lambda r: r["final_score"], reverse=True)
    #     return results

    def _rerank_results(self, results: List[Dict], query: str, query_keywords: Set[str]) -> List[Dict]:
        word_count = len(query.split())

        # Adjust weights dynamically for short queries
        if word_count < 4:
            w_semantic = 0.2
            w_keyword = 0.6
            w_title = 0.1
            w_exact = 0.1
        elif word_count <= 8:
            w_semantic = 0.4
            w_keyword = 0.3
            w_title = 0.2
            w_exact = 0.1
        else:
            w_semantic = 0.5
            w_keyword = 0.2
            w_title = 0.2
            w_exact = 0.1

        query_lower = query.lower()

        for result in results:
            semantic = result["similarity"]
            keyword = self._compute_keyword_score(result, query_keywords)
            title = self._compute_title_score(result, query_keywords)
            exact = self._compute_exact_match(result, query_lower)

            final = (w_semantic * semantic +
                     w_keyword * keyword +
                     w_title * title +
                     w_exact * exact)

            result["keyword_score"] = keyword
            result["title_score"] = title
            result["exact_score"] = exact
            result["final_score"] = final

        results.sort(key=lambda r: r["final_score"], reverse=True)
        return results

    def _cross_encoder_rerank(self, query: str, candidates: List[Dict], top_k: int = 1) -> List[Dict]:
        """
        Re-rank candidates using cross-encoder for precise relevance.
        Returns top_k candidates sorted by cross-encoder score.
        Filters out preamble/metadata-only chunks (< 20 words).
        """
        if not candidates:
            return []

        # Filter out tiny preamble chunks before scoring
        viable = [c for c in candidates if len(c["content"].split()) >= 20]
        if not viable:
            viable = candidates  # Fallback if all chunks are small

        pairs = [(query, cand["content"]) for cand in viable]
        scores = self.cross_encoder.predict(pairs)

        for i, score in enumerate(scores):
            viable[i]["cross_score"] = float(score)

        # Sort by cross_score descending
        viable.sort(key=lambda x: x["cross_score"], reverse=True)

        logger.info(f"Cross-encoder scores: {[(c['section_title'], round(c['cross_score'], 3)) for c in viable[:5]]}")

        return viable[:top_k] if viable else []

    def _compute_keyword_score(self, result: Dict, query_keywords: Set[str]) -> float:
        """
        % of query keywords found in chunk's keywords list.
        Returns 0.0 to 1.0.
        """
        if not query_keywords:
            return 0.0

        chunk_keywords = set(kw.lower() for kw in result.get("keywords", []))
        # Also check individual words within multi-word keywords
        expanded_chunk_kw = set()
        for kw in chunk_keywords:
            expanded_chunk_kw.add(kw)
            for word in kw.split():
                expanded_chunk_kw.add(word)

        matches = query_keywords & expanded_chunk_kw
        return len(matches) / len(query_keywords)

    def _compute_title_score(self, result: Dict, query_keywords: Set[str]) -> float:
        """
        % of query keywords found in section_title.
        Returns 0.0 to 1.0.
        """
        if not query_keywords:
            return 0.0

        title_words = set(re.findall(r'[a-zA-Z]{2,}', result["section_title"].lower()))
        matches = query_keywords & title_words
        return len(matches) / len(query_keywords)

    def _compute_exact_match(self, result: Dict, query_lower: str) -> float:
        """
        1.0 if the exact query phrase appears in content or title, else 0.0.
        This is the AGGRESSIVE boost for exact matches.
        """
        content_lower = result["content"].lower()
        title_lower = result["section_title"].lower()

        if query_lower in content_lower or query_lower in title_lower:
            return 1.0
        return 0.0

    # ══════════════════════════════════════════════════════════════
    # ── SELECTION & VALIDATION ───────────────────────────────────
    # ══════════════════════════════════════════════════════════════

    def _select_top_chunks(self, results: List[Dict]) -> List[Dict]:
        """
        Select top 1 chunk (or top 2 if from same document and close in score).
        Results are already sorted by final_score.
        """
        if not results:
            return []

        top = results[0]
        selected = [top]

        if len(results) > 1:
            second = results[1]
            same_doc = second["document_id"] == top["document_id"]
            close_score = (top["final_score"] - second["final_score"]) < 0.10
            if same_doc and close_score:
                selected.append(second)

        return selected

    def _detect_conflicts(self, results: List[Dict], threshold: float) -> dict | None:
        """Detect if top chunks come from different versions of the same document."""
        doc_versions = defaultdict(set)

        for result in results[:5]:  # Only check top 5
            doc_versions[result["document_id"]].add(result["version_id"])

        for doc_id, versions in doc_versions.items():
            if len(versions) > 1:
                doc_title = next(
                    r["document_title"] for r in results
                    if r["document_id"] == doc_id
                )
                return {
                    "document_title": doc_title,
                    "versions": list(versions)
                }

        return None

    # ══════════════════════════════════════════════════════════════
    # ── AUDIT LOGGING ────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════

    def _log_query_audit(
        self,
        user_id: UUID,
        query_text: str,
        top_similarity: float,
        result_status: str,
        metadata: dict = None
    ):
        """Write a query audit log entry with full debug info."""
        log = QueryAuditLog(
            user_id=user_id,
            query_text=query_text,
            top_similarity=top_similarity,
            result_status=result_status,
            extra_metadata=metadata
        )
        self.db.add(log)
        self.db.flush()
        return log
