import { useState, useEffect } from 'react';
import { useAuth } from '../components/context/AuthContext';
import Navbar from '../components/Navbar';
import UsersTable from '../components/UsersTable';
import DocumentsTable from '../components/DocumentsTable';
import { getUsers } from '../services/userService';
import { getDocuments } from '../services/documentService';

export default function AdminDashboard() {
    const { user, role } = useAuth();
    const [activeSection, setActiveSection] = useState('users');
    const [users, setUsers] = useState([]);
    const [documents, setDocuments] = useState([]);
    const [loadingUsers, setLoadingUsers] = useState(false);
    const [loadingDocs, setLoadingDocs] = useState(false);
    const [error, setError] = useState('');

    const fetchUsers = async () => {
        setLoadingUsers(true);
        setError('');
        try {
            const data = await getUsers();
            setUsers(data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to load users');
        } finally {
            setLoadingUsers(false);
        }
    };

    const fetchDocuments = async () => {
        setLoadingDocs(true);
        setError('');
        try {
            const data = await getDocuments();
            setDocuments(data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to load documents');
        } finally {
            setLoadingDocs(false);
        }
    };

    useEffect(() => {
        if (activeSection === 'users' && role === 'ADMIN') {
            fetchUsers();
        } else if (activeSection === 'documents') {
            fetchDocuments();
        }
    }, [activeSection, role]);

    return (
        <div className="layout">
            <Navbar />
            <div className="layout-body">
                <aside className="sidebar">
                    <div className="sidebar-section">
                        <h3 className="sidebar-title">Management</h3>
                        {role === 'ADMIN' && (
                            <button
                                className={`sidebar-link ${activeSection === 'users' ? 'active' : ''}`}
                                onClick={() => setActiveSection('users')}
                            >
                                <span className="sidebar-icon">👥</span>
                                Users
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
                </aside>

                <main className="main-content">
                    {error && <div className="alert alert-error">{error}</div>}

                    {activeSection === 'users' && role === 'ADMIN' && (
                        <section>
                            <div className="section-header">
                                <h2>Users Management</h2>
                                <button className="btn btn-ghost" onClick={fetchUsers} disabled={loadingUsers}>
                                    {loadingUsers ? 'Loading...' : '↻ Refresh'}
                                </button>
                            </div>
                            {loadingUsers ? (
                                <div className="loader-container">
                                    <div className="spinner" />
                                </div>
                            ) : (
                                <UsersTable users={users} currentUserId={user?.id} onRefresh={fetchUsers} />
                            )}
                        </section>
                    )}

                    {activeSection === 'documents' && (
                        <section>
                            <div className="section-header">
                                <h2>Document Overview</h2>
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
