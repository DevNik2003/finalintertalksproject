import api from './api';

/**
 * Login — uses form-encoded data to match backend OAuth2PasswordRequestForm.
 * Refresh token is set as httpOnly cookie by the backend automatically.
 */
export const login = async (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const { data } = await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return data; // { access_token, token_type }
};

/**
 * Register a new user
 */
export const register = async (fullName, email, password) => {
    const { data } = await api.post('/auth/register', {
        full_name: fullName,
        email,
        password,
    });
    return data;
};

/**
 * Refresh token — cookie is sent automatically, no body needed
 */
export const refreshToken = async () => {
    const { data } = await api.post('/auth/refresh', {});
    return data;
};

/**
 * Logout — backend reads cookie, revokes token, and clears cookie
 */
export const logout = async () => {
    const { data } = await api.post('/auth/logout', {});
    return data;
};

/**
 * Get current user info
 */
export const getMe = async () => {
    const { data } = await api.get('/auth/me');
    return data;
};
