import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getMe, logout as logoutApi, refreshToken as refreshApi } from '../../services/authService';

const AuthContext = createContext(null);

/**
 * Decode JWT payload (no verification — that's server-side)
 */
function decodeToken(token) {
    try {
        const payload = token.split('.')[1];
        return JSON.parse(atob(payload));
    } catch {
        return null;
    }
}

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [role, setRole] = useState(null);
    const [accessToken, setAccessToken] = useState(null);
    const [loading, setLoading] = useState(true);

    // Sync access token to window global for Axios interceptor
    useEffect(() => {
        window.__accessToken = accessToken;
    }, [accessToken]);

    // Callback for interceptor to update token after refresh
    useEffect(() => {
        window.__onTokenRefresh = (newAccessToken) => {
            setAccessToken(newAccessToken);
            const decoded = decodeToken(newAccessToken);
            if (decoded?.role) {
                setRole(decoded.role);
            }
        };

        window.__onAuthFailure = () => {
            setUser(null);
            setRole(null);
            setAccessToken(null);
            setLoading(false);
        };

        return () => {
            window.__onTokenRefresh = null;
            window.__onAuthFailure = null;
        };
    }, []);

    // On mount: try to restore session by refreshing from httpOnly cookie
    useEffect(() => {
        const tryRestore = async () => {
            try {
                const data = await refreshApi();
                const token = data.access_token;
                setAccessToken(token);
                window.__accessToken = token;

                const decoded = decodeToken(token);
                setRole(decoded?.role || 'VIEWER');

                // Fetch full user profile
                const userData = await getMe();
                setUser(userData);
            } catch {
                // No valid cookie / expired — user needs to login
            } finally {
                setLoading(false);
            }
        };

        tryRestore();
    }, []);

    const login = useCallback((tokenData) => {
        const { access_token } = tokenData;
        setAccessToken(access_token);
        window.__accessToken = access_token;

        const decoded = decodeToken(access_token);
        const userRole = decoded?.role || 'VIEWER';
        setRole(userRole);

        // Fetch full user profile
        getMe()
            .then((userData) => setUser(userData))
            .catch(() => { });

        return userRole;
    }, []);

    const logout = useCallback(async () => {
        try {
            await logoutApi();
        } catch {
            // Ignore errors during logout
        } finally {
            setUser(null);
            setRole(null);
            setAccessToken(null);
            window.__accessToken = null;
        }
    }, []);

    const value = {
        user,
        role,
        accessToken,
        loading,
        login,
        logout,
        isAuthenticated: !!accessToken,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

export default AuthContext;
