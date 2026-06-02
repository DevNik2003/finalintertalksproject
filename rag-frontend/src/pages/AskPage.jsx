import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../components/context/AuthContext';
import Navbar from '../components/Navbar';
import { askQuery } from '../services/documentService';

export default function AskPage() {
    const { role } = useAuth();
    const navigate = useNavigate();
    const [query, setQuery] = useState('');
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        setError('');
        setResult(null);
        setLoading(true);

        try {
            const data = await askQuery(query);
            setResult(data);
        } catch (err) {
            const detail = err.response?.data?.detail || 'Query failed. Please try again.';
            setError(detail);
        } finally {
            setLoading(false);
        }
    };

    const sidebarHome = role === 'ADMIN' || role === 'REVIEWER' ? '/admin' : '/employee';

    return (
        <div className="layout">
            <Navbar />
            <div className="layout-body">
                <aside className="sidebar">
                    <div className="sidebar-section">
                        <h3 className="sidebar-title">Navigation</h3>
                        <button className="sidebar-link" onClick={() => navigate(sidebarHome)}>
                            <span className="sidebar-icon">◫</span>
                            Dashboard
                        </button>
                        <button className="sidebar-link active">
                            <span className="sidebar-icon">⟐</span>
                            Ask Query
                        </button>
                        {(role === 'CONTRIBUTOR' || role === 'REVIEWER' || role === 'ADMIN') && (
                            <button className="sidebar-link" onClick={() => navigate('/upload')}>
                                <span className="sidebar-icon">⇪</span>
                                Upload
                            </button>
                        )}
                    </div>
                </aside>

                <main className="main-content">
                    <div className="section-header">
                        <h2>Ask the Knowledge Base</h2>
                        <p className="section-subtitle">Search approved documents using semantic search</p>
                    </div>

                    <div className="form-card">
                        <form onSubmit={handleSubmit} className="ask-form">
                            <div className="form-group">
                                <label htmlFor="query">Your Question</label>
                                <textarea
                                    id="query"
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    placeholder="What would you like to know from the approved documents?"
                                    rows={4}
                                    required
                                />
                            </div>

                            <button type="submit" className="btn btn-primary" disabled={loading}>
                                {loading ? <span className="spinner-sm" /> : '🔍 Search'}
                            </button>
                        </form>
                    </div>

                    {error && (
                        <div className="answer-card">
                            <div className="alert alert-error">{error}</div>
                        </div>
                    )}

                    {result && result.status === 'refused' && (
                        <div className="answer-card">
                            <div className="refusal-banner">
                                <span className="refusal-icon">⚠️</span>
                                <div>
                                    <strong>Query Refused</strong>
                                    <p>{result.reason}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {result && result.status === 'success' && (
                        <div className="answer-card">
                            <div className="answer-header">
                                <h3>📄 Answer</h3>
                                <span className="answer-badge success">Grounded Answer</span>
                            </div>
                            <div className="answer-text">
                                {result.answer}
                            </div>

                            {result.citations && result.citations.length > 0 && (
                                <div className="citations-section">
                                    <h4>📌 Citations</h4>
                                    {result.citations.map((cite, i) => (
                                        <div key={i} className="citation-item">
                                            <span className="citation-number">[{i + 1}]</span>
                                            <div className="citation-details">
                                                <strong>{cite.document}</strong>
                                                <span className="text-muted"> · v{cite.version}</span>
                                                {cite.section && <span className="text-muted"> · §{cite.section_number || ''} {cite.section}</span>}
                                                <div className="citation-meta">
                                                    <span className="similarity-badge" style={{
                                                        background: cite.similarity >= 0.8 ? 'var(--color-success)' :
                                                            cite.similarity >= 0.65 ? 'var(--color-warning)' :
                                                                'var(--color-error)',
                                                        color: '#fff',
                                                        padding: '2px 8px',
                                                        borderRadius: '12px',
                                                        fontSize: '0.75rem'
                                                    }}>
                                                        {(cite.similarity * 100).toFixed(1)}% match
                                                    </span>
                                                    <span className="chunk-id text-muted" style={{ fontSize: '0.7rem', marginLeft: '8px' }}>
                                                        ID: {cite.chunk_id.slice(0, 8)}…
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}
