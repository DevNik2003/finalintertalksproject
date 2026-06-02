import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../components/context/AuthContext';

export default function Navbar() {
    const { user, role, logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const handleLogout = async () => {
        await logout();
        navigate('/', { replace: true });
    };

    const navLinks =
        role === 'ADMIN' || role === 'REVIEWER'
            ? [
                { path: '/admin', label: 'Dashboard', icon: '◫' },
                { path: '/ask', label: 'Ask Query', icon: '⟐' },
            ]
            : [
                { path: '/employee', label: 'Dashboard', icon: '◫' },
                { path: '/ask', label: 'Ask Query', icon: '⟐' },
                ...(role === 'CONTRIBUTOR'
                    ? [{ path: '/upload', label: 'Upload', icon: '⇪' }]
                    : []),
            ];

    return (
        <nav className="navbar">
            <div className="nav-brand" onClick={() => navigate(role === 'ADMIN' || role === 'REVIEWER' ? '/admin' : '/employee')}>
                <svg viewBox="0 0 24 24" fill="none" className="nav-logo-icon">
                    <path d="M12 2L2 7l10 5 10-5-10-5z" fill="currentColor" opacity="0.8" />
                    <path d="M2 17l10 5 10-5" stroke="currentColor" strokeWidth="2" fill="none" />
                    <path d="M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2" fill="none" />
                </svg>
                <span>InterTalks</span>
            </div>

            <div className="nav-links">
                {navLinks.map((link) => (
                    <button
                        key={link.path}
                        className={`nav-link ${location.pathname === link.path ? 'active' : ''}`}
                        onClick={() => navigate(link.path)}
                    >
                        <span className="nav-icon">{link.icon}</span>
                        {link.label}
                    </button>
                ))}
            </div>

            <div className="nav-user">
                <div className="user-info">
                    <span className="user-name">{user?.full_name || user?.email || 'User'}</span>
                    <span className="user-role-badge">{role}</span>
                </div>
                <button className="btn btn-ghost" onClick={handleLogout} id="logout-btn">
                    Sign Out
                </button>
            </div>
        </nav>
    );
}
