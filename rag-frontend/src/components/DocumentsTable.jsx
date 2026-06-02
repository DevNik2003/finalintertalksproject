import { useState } from 'react';
import { approveDocument } from '../services/documentService';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const LIFECYCLE_COLORS = {
    UPLOADED: 'badge-yellow',
    UNDER_REVIEW: 'badge-orange',
    APPROVED: 'badge-green',
    DEPRECATED: 'badge-red',
};

export default function DocumentsTable({ documents, userRole, onRefresh }) {
    const [approvingId, setApprovingId] = useState(null);
    const [error, setError] = useState('');

    const handleApprove = async (versionId) => {
        setError('');
        setApprovingId(versionId);
        try {
            await approveDocument(versionId);
            onRefresh();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to approve document');
        } finally {
            setApprovingId(null);
        }
    };

    const canApprove = userRole === 'ADMIN' || userRole === 'REVIEWER';

    return (
        <div className="table-container">
            {error && <div className="alert alert-error">{error}</div>}
            <table className="data-table">
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Department</th>
                        <th>Version</th>
                        <th>Lifecycle</th>
                        <th>Uploaded</th>
                        <th>View</th>
                        {canApprove && <th>Actions</th>}
                    </tr>
                </thead>
                <tbody>
                    {documents.map((doc) => {
                        const versions = doc.versions || [];
                        if (versions.length === 0) {
                            return (
                                <tr key={doc.id}>
                                    <td>{doc.title}</td>
                                    <td>{doc.department}</td>
                                    <td>—</td>
                                    <td>—</td>
                                    <td className="cell-date">
                                        {new Date(doc.created_at).toLocaleDateString('en-US', {
                                            year: 'numeric',
                                            month: 'short',
                                            day: 'numeric',
                                        })}
                                    </td>
                                    <td>—</td>
                                    {canApprove && <td>—</td>}
                                </tr>
                            );
                        }

                        return versions.map((ver) => (
                            <tr key={ver.id}>
                                <td className="cell-name">{doc.title}</td>
                                <td>{doc.department}</td>
                                <td>v{ver.version_number}</td>
                                <td>
                                    <span className={`lifecycle-badge ${LIFECYCLE_COLORS[ver.lifecycle_state] || ''}`}>
                                        {ver.lifecycle_state}
                                    </span>
                                </td>
                                <td className="cell-date">
                                    {new Date(ver.uploaded_at).toLocaleDateString('en-US', {
                                        year: 'numeric',
                                        month: 'short',
                                        day: 'numeric',
                                    })}
                                </td>
                                <td>
                                    <a
                                        href={`${API_BASE_URL}/documents/${ver.id}/view`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="btn btn-sm btn-ghost"
                                        onClick={(e) => {
                                            // Attach auth token as query param for file download
                                            e.preventDefault();
                                            const token = window.__accessToken;
                                            window.open(`${API_BASE_URL}/documents/${ver.id}/view?token=${token}`, '_blank');
                                        }}
                                    >
                                        📄 View
                                    </a>
                                </td>
                                {canApprove && (
                                    <td>
                                        {(ver.lifecycle_state === 'UPLOADED' || ver.lifecycle_state === 'UNDER_REVIEW') ? (
                                            <button
                                                className="btn btn-sm btn-primary"
                                                onClick={() => handleApprove(ver.id)}
                                                disabled={approvingId === ver.id}
                                            >
                                                {approvingId === ver.id ? '...' : 'Approve'}
                                            </button>
                                        ) : (
                                            <span className="text-muted">—</span>
                                        )}
                                    </td>
                                )}
                            </tr>
                        ));
                    })}
                    {documents.length === 0 && (
                        <tr>
                            <td colSpan={canApprove ? 7 : 6} className="empty-row">No documents found</td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}
