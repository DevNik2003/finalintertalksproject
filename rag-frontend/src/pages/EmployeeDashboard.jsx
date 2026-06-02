import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../components/context/AuthContext';
import Navbar from '../components/Navbar';
import DocumentsTable from '../components/DocumentsTable';
import { getDocuments } from '../services/documentService';

export default function EmployeeDashboard() {
    const { role, user } = useAuth();
    const navigate = useNavigate();
    const [activeSection, setActiveSection] = useState('home');
    const [documents, setDocuments] = useState([]);
    const [loadingDocs, setLoadingDocs] = useState(false);

    const fetchDocuments = async () => {
        setLoadingDocs(true);
        try {
            const data = await getDocuments();
            setDocuments(data);
        } catch {
            // May fail if endpoint isn't available
        } finally {
            setLoadingDocs(false);
        }
    };

    useEffect(() => {
        if (activeSection === 'documents') {
            fetchDocuments();
        }
    }, [activeSection]);

    return (
        <div className="layout">
            <Navbar />
            <div className="layout-body">
                <aside className="sidebar">
                    <div className="sidebar-section">
                        <h3 className="sidebar-title">Quick Actions</h3>
                        <button
                            className={`sidebar-link ${activeSection === 'home' ? 'active' : ''}`}
                            onClick={() => setActiveSection('home')}
                        >
                            <span className="sidebar-icon">◫</span>
                            Home
                        </button>
                        <button className="sidebar-link" onClick={() => navigate('/ask')}>
                            <span className="sidebar-icon">⟐</span>
                            Ask Query
                        </button>
                        {(role === 'CONTRIBUTOR' || role === 'REVIEWER' || role === 'ADMIN') && (
                            <button className="sidebar-link" onClick={() => navigate('/upload')}>
                                <span className="sidebar-icon">⇪</span>
                                Upload Document
                            </button>
                        )}
                        <button
                            className={`sidebar-link ${activeSection === 'documents' ? 'active' : ''}`}
                            onClick={() => setActiveSection('documents')}
                        >
                            <span className="sidebar-icon">📄</span>
                            Documents
                        </button>
                    </div>

                    <div className="sidebar-section">
                        <h3 className="sidebar-title">Profile</h3>
                        <div className="sidebar-info">
                            <p><strong>{user?.full_name || 'User'}</strong></p>
                            <p className="text-muted">{user?.email}</p>
                            <span className="user-role-badge">{role}</span>
                        </div>
                    </div>
                </aside>

                <main className="main-content">
                    {activeSection === 'home' && (
                        <>
                            <div className="welcome-banner">
                                <h2>Welcome back, {user?.full_name?.split(' ')[0] || 'there'}</h2>
                                <p>Access your documents and query the knowledge base from your dashboard.</p>
                            </div>

                            <div className="quick-actions-grid">
                                <div className="action-card" onClick={() => navigate('/ask')}>
                                    <div className="action-icon">⟐</div>
                                    <h3>Ask a Question</h3>
                                    <p>Query the RAG system for intelligent answers from approved documents.</p>
                                </div>

                                {(role === 'CONTRIBUTOR' || role === 'REVIEWER' || role === 'ADMIN') && (
                                    <div className="action-card" onClick={() => navigate('/upload')}>
                                        <div className="action-icon">⇪</div>
                                        <h3>Upload Document</h3>
                                        <p>Submit new documents for review and inclusion in the knowledge base.</p>
                                    </div>
                                )}

                                <div className="action-card" onClick={() => setActiveSection('documents')}>
                                    <div className="action-icon">📄</div>
                                    <h3>Browse Documents</h3>
                                    <p>View all uploaded documents and open them directly.</p>
                                </div>

                                <div className="action-card info">
                                    <div className="action-icon">ℹ</div>
                                    <h3>Your Role: {role}</h3>
                                    <p>
                                        {role === 'VIEWER' && 'You can query approved documents and view files.'}
                                        {role === 'CONTRIBUTOR' && 'You can upload documents, query, and view files.'}
                                        {role === 'REVIEWER' && 'You can review, approve documents, and query the knowledge base.'}
                                        {role === 'ADMIN' && 'Full access to all system features.'}
                                    </p>
                                </div>
                            </div>
                        </>
                    )}

                    {activeSection === 'documents' && (
                        <section>
                            <div className="section-header">
                                <h2>Documents</h2>
                                <button className="btn btn-ghost" onClick={fetchDocuments} disabled={loadingDocs}>
                                    {loadingDocs ? 'Loading...' : '↻ Refresh'}
                                </button>
                            </div>
                            {loadingDocs ? (
                                <div className="loader-container">
                                    <div className="spinner" />
                                </div>
                            ) : (
                                <DocumentsTable documents={documents} userRole={role} onRefresh={fetchDocuments} />
                            )}
                        </section>
                    )}
                </main>
            </div>
        </div>
    );
}
