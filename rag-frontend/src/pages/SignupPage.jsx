import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { register } from '../services/authService';

export default function SignupPage() {
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        // Client-side domain check
        const domain = email.split('@')[1];
        if (!domain || !['company.com', 'intertalks.com'].includes(domain)) {
            setError('Only company email addresses are allowed (@company.com or @intertalks.com)');
            setLoading(false);
            return;
        }

        try {
            await register(fullName, email, password);
            setSuccess(true);
            setTimeout(() => navigate('/', { replace: true }), 2000);
        } catch (err) {
            const detail = err.response?.data?.detail || 'Registration failed. Please try again.';
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
                    <p className="auth-subtitle">Create your account</p>
                </div>

                {success ? (
                    <div className="alert alert-success">
                        <strong>Account created!</strong> Redirecting to login...
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="auth-form">
                        {error && <div className="alert alert-error">{error}</div>}

                        <div className="form-group">
                            <label htmlFor="fullName">Full Name</label>
                            <input
                                id="fullName"
                                type="text"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                placeholder="John Doe"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="signupEmail">Email</label>
                            <input
                                id="signupEmail"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="name@company.com"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="signupPassword">Password</label>
                            <input
                                id="signupPassword"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Create a strong password"
                                required
                                minLength={6}
                            />
                        </div>

                        <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
                            {loading ? <span className="spinner-sm" /> : 'Create Account'}
                        </button>
                    </form>
                )}

                <p className="auth-footer">
                    Already have an account?{' '}
                    <a href="/" onClick={(e) => { e.preventDefault(); navigate('/'); }}>
                        Sign In
                    </a>
                </p>
            </div>
        </div>
    );
}
