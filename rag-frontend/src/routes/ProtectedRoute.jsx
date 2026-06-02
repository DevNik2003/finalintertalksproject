import { Navigate } from 'react-router-dom';
import { useAuth } from '../components/context/AuthContext';

/**
 * ProtectedRoute component
 * - Blocks unauthenticated users → redirects to login
 * - Blocks role-mismatched users → redirects to appropriate dashboard
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children - The protected content
 * @param {string[]} props.allowedRoles - Roles that can access this route
 */
export default function ProtectedRoute({ children, allowedRoles }) {
    const { isAuthenticated, role, loading } = useAuth();

    if (loading) {
        return (
            <div className="page-loader">
                <div className="spinner" />
            </div>
        );
    }

    if (!isAuthenticated) {
        return <Navigate to="/" replace />;
    }

    if (allowedRoles && allowedRoles.length > 0 && !allowedRoles.includes(role)) {
        // Redirect to appropriate dashboard based on their actual role
        if (role === 'ADMIN' || role === 'REVIEWER') {
            return <Navigate to="/admin" replace />;
        }
        return <Navigate to="/employee" replace />;
    }

    return children;
}
