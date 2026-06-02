import { useState } from 'react';
import { updateUser } from '../services/userService';

const ROLES = ['VIEWER', 'CONTRIBUTOR', 'REVIEWER', 'ADMIN'];

export default function UsersTable({ users, currentUserId, onRefresh }) {
    const [updatingId, setUpdatingId] = useState(null);
    const [error, setError] = useState('');

    const handleRoleChange = async (userId, newRole) => {
        setError('');
        setUpdatingId(userId);
        try {
            await updateUser(userId, { role: newRole });
            onRefresh();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to update role');
        } finally {
            setUpdatingId(null);
        }
    };

    const handleToggleActive = async (userId, currentStatus) => {
        setError('');
        setUpdatingId(userId);
        try {
            await updateUser(userId, { is_active: !currentStatus });
            onRefresh();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to update status');
        } finally {
            setUpdatingId(null);
        }
    };

    return (
        <div className="table-container">
            {error && <div className="alert alert-error">{error}</div>}
            <table className="data-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Status</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {users.map((u) => {
                        const isSelf = String(u.id) === String(currentUserId);
                        return (
                            <tr key={u.id} className={isSelf ? 'row-self' : ''}>
                                <td className="cell-name">{u.full_name || '—'}</td>
                                <td className="cell-email">{u.email}</td>
                                <td>
                                    <select
                                        value={u.role}
                                        onChange={(e) => handleRoleChange(u.id, e.target.value)}
                                        disabled={isSelf || updatingId === u.id}
                                        className="role-select"
                                    >
                                        {ROLES.map((r) => (
                                            <option key={r} value={r}>{r}</option>
                                        ))}
                                    </select>
                                </td>
                                <td>
                                    <span className={`status-badge ${u.is_active ? 'active' : 'inactive'}`}>
                                        {u.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                </td>
                                <td className="cell-date">
                                    {u.created_at
                                        ? new Date(u.created_at).toLocaleDateString('en-US', {
                                            year: 'numeric',
                                            month: 'short',
                                            day: 'numeric',
                                        })
                                        : '—'}
                                </td>
                                <td>
                                    {!isSelf && (
                                        <button
                                            className={`btn btn-sm ${u.is_active ? 'btn-warning' : 'btn-success'}`}
                                            onClick={() => handleToggleActive(u.id, u.is_active)}
                                            disabled={updatingId === u.id}
                                        >
                                            {updatingId === u.id ? '...' : u.is_active ? 'Deactivate' : 'Activate'}
                                        </button>
                                    )}
                                </td>
                            </tr>
                        );
                    })}
                    {users.length === 0 && (
                        <tr>
                            <td colSpan="6" className="empty-row">No users found</td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}
