📘 Policy Compliance RAG System

Production-Grade Retrieval & Evidence-Controlled AI Assistant

🚀 Overview

This project is a production-focused Retrieval-Augmented Generation (RAG) system designed for compliance and policy document querying.

It enables users to ask natural language questions and receive:

✅ Strictly evidence-backed responses

✅ Version-controlled document retrieval

✅ Approval-based indexing

✅ Deterministic refusal when evidence is insufficient

✅ No hallucinated answers

This system is built for real engineering reliability, not demo-level behavior.

🏗 Architecture
Core Stack

PostgreSQL – Structured document storage

Vector Database (pgvector / vector store) – Embedding storage

Sentence Transformers (all-MiniLM-L6-v2) – Embedding generation

FastAPI – API layer

LLM (controlled prompt) – Context-bound answer generation

📂 System Design
1️⃣ Document Ingestion

Documents uploaded (PDF)

Parsed into structured sections

Chunked strictly by logical section (NOT page-based)

Stored in PostgreSQL with metadata

Each chunk contains:

doc_id
section_number
section_title
section_text
version
is_active
approval_status
embedding_vector

Only approved + active documents are indexed.

2️⃣ Section-Based Chunking (Critical Engineering Decision)

We DO NOT chunk by:

Token count

Page size

Arbitrary character length

We chunk by:

Logical policy section

Example:

2.2 Sick Leave
Employees are entitled to 12 days of paid sick leave per year...

Each section = 1 embedding.

This prevents cross-policy leakage.

3️⃣ Embedding Strategy

Model Used:

sentence-transformers/all-MiniLM-L6-v2

Process:

Extract section text

Generate embedding

Store embedding in vector DB

Store structured metadata in PostgreSQL

4️⃣ Query Pipeline

Production Retrieval Flow:

Receive user query

Normalize query

Expand short queries (<4 words)

Generate query embedding

Retrieve top_k = 5

Apply similarity threshold

Select top 1 (or 2 max)

Send ONLY selected chunk(s) to LLM

Generate answer strictly from context

If similarity is below threshold:

Query Refused
Insufficient approved evidence found.
🧠 Short Query Handling

Short queries like:

“sick leave”

“overtime”

“maternity leave”

are expanded internally to improve semantic matching:

Example:

"What is the company policy regarding sick leave? 
How many days are allowed and what conditions apply?"

This dramatically improves retrieval accuracy.

🛡 Hallucination Prevention

Strict prompt rules enforce:

Answer ONLY using provided context

No summarization of unrelated sections

No external knowledge

Refuse if not explicitly found

The system never guesses.

📊 Similarity Threshold Strategy

Adaptive thresholding:

Query Type	Threshold Range
Short	0.65–0.72
Medium	0.72–0.80
Long	0.80+

This prevents false refusals and irrelevant matches.

🔐 Governance & Control

Admin-only document activation

Version control support

is_active flag filtering

Deprecated documents excluded

No unapproved indexing

Only approved policies are searchable.

🧪 Example Behavior
✅ Valid Query

Input:

How many sick leave days are allowed?

Output:

Employees are entitled to 12 days of paid sick leave per year.
❌ Invalid Query

Input:

How many casual leave days are allowed?

Output:

Query Refused
Insufficient approved evidence found.

Because casual leave does not exist in the document.

📁 Project Structure (Suggested)
├── app/
│   ├── main.py
│   ├── routes/
│   ├── services/
│   ├── embeddings/
│   ├── retrieval/
│   ├── prompts/
│   └── models/
├── database/
│   ├── schema.sql
│   └── migrations/
├── documents/
├── tests/
├── requirements.txt
└── README.md
⚙️ Setup
1️⃣ Install Dependencies
pip install -r requirements.txt
2️⃣ Set Environment Variables
DATABASE_URL=postgresql://...
HF_TOKEN=your_huggingface_token
3️⃣ Run Server
uvicorn app.main:app --reload
🧪 Testing Strategy

Test for:

Section precision

Refusal accuracy

Cross-policy leakage

Version filtering

Short query behavior

Threshold tuning

This is not a chatbot.
This is a controlled compliance engine.

🎯 Engineering Philosophy

This project prioritizes:

Deterministic behavior

Strict evidence grounding

Controlled AI output

Production-ready architecture

No demo shortcuts

It is designed as a foundation for:

Enterprise compliance tools

Internal knowledge bases

Legal policy assistants

Governance automation systems

🔮 Future Enhancements

Cross-encoder re-ranking

Multi-document support

Audit logging for queries

Confidence scoring API

Role-based retrieval restrictions

Monitoring & evaluation dashboard
