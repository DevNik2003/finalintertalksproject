import api from './api';

/**
 * Get all users (admin only)
 */
export const getUsers = async () => {
    const { data } = await api.get('/admin/users');
    return data;
};

/**
 * Update a user (role and/or is_active)
 */
export const updateUser = async (userId, updates) => {
    const { data } = await api.patch(`/admin/users/${userId}`, updates);
    return data;
};
