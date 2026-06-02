import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../components/context/AuthContext';
import { login as loginApi } from '../services/authService';

export default function LoginPage() {
    const [activeTab, setActiveTab] = useState('employee');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { login } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const tokenData = await loginApi(email, password);
            const userRole = login(tokenData);

            // Redirect based on role
            if (userRole === 'ADMIN' || userRole === 'REVIEWER') {
                navigate('/admin', { replace: true });
            } else {
                navigate('/employee', { replace: true });
            }
        } catch (err) {
            const detail = err.response?.data?.detail || 'Login failed. Please check your credentials.';
            setError(detail);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-card">
                <div className="auth-header">
                    <div className="auth-logo">
                        <svg viewBox="0 0 24 24" fill="none" className="logo-icon">
                            <path d="M12 2L2 7l10 5 10-5-10-5z" fill="currentColor" opacity="0.8" />
                            <path d="M2 17l10 5 10-5" stroke="currentColor" strokeWidth="2" fill="none" />
                            <path d="M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2" fill="none" />
                        </svg>
                        <h1>InterTalks</h1>
                    </div>
                    <p className="auth-subtitle">RAG Governance Platform</p>
                </div>

                <div className="tab-switcher">
                    <button
                        className={`tab-btn ${activeTab === 'employee' ? 'active' : ''}`}
                        onClick={() => { setActiveTab('employee'); setError(''); }}
                    >
                        Employee Login
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'admin' ? 'active' : ''}`}
                        onClick={() => { setActiveTab('admin'); setError(''); }}
                    >
                        Admin Login
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="auth-form">
                    {error && <div className="alert alert-error">{error}</div>}

                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="name@company.com"
                            required
                            autoComplete="email"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter your password"
                            required
                            autoComplete="current-password"
                        />
                    </div>

                    <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
                        {loading ? <span className="spinner-sm" /> : 'Sign In'}
                    </button>
                </form>

                {activeTab === 'employee' && (
                    <p className="auth-footer">
                        Don't have an account?{' '}
                        <a href="/signup" onClick={(e) => { e.preventDefault(); navigate('/signup'); }}>
                            Sign Up
                        </a>
                    </p>
                )}
            </div>
        </div>
    );
}
