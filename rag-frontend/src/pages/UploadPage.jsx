import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { uploadDocument } from '../services/documentService';

const DEPARTMENTS = [
    'Engineering',
    'Product',
    'Design',
    'Marketing',
    'Sales',
    'HR',
    'Finance',
    'Legal',
    'Operations',
    'Other',
];

export default function UploadPage() {
    const [department, setDepartment] = useState('');
    const [file, setFile] = useState(null);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(null);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess(null);

        if (!file) {
            setError('Please select a file');
            return;
        }

        const ext = file.name.split('.').pop().toLowerCase();
        if (!['pdf', 'docx'].includes(ext)) {
            setError('Only .pdf and .docx files are allowed');
            return;
        }

        setLoading(true);
        try {
            const result = await uploadDocument(file.name, department, file);
            setSuccess({
                message: result.message || 'Document uploaded successfully',
                state: result.lifecycle_state,
            });
            setFile(null);
            setDepartment('');
        } catch (err) {
            setError(err.response?.data?.detail || 'Upload failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="layout">
            <Navbar />
            <div className="layout-body">
                <aside className="sidebar">
                    <div className="sidebar-section">
                        <h3 className="sidebar-title">Navigation</h3>
                        <button className="sidebar-link" onClick={() => navigate('/employee')}>
                            <span className="sidebar-icon">◫</span>
                            Dashboard
                        </button>
                        <button className="sidebar-link active">
                            <span className="sidebar-icon">⇪</span>
                            Upload
                        </button>
                        <button className="sidebar-link" onClick={() => navigate('/ask')}>
                            <span className="sidebar-icon">⟐</span>
                            Ask Query
                        </button>
                    </div>
                </aside>

                <main className="main-content">
                    <div className="section-header">
                        <h2>Upload Document</h2>
                    </div>

                    <div className="form-card">
                        {success && (
                            <div className="alert alert-success">
                                <strong>{success.message}</strong>
                                <p>Status: <span className="lifecycle-badge badge-yellow">{success.state}</span> — Waiting for review</p>
                            </div>
                        )}

                        {error && <div className="alert alert-error">{error}</div>}

                        <form onSubmit={handleSubmit} className="upload-form">
                            <div className="form-group">
                                <label htmlFor="department">Department</label>
                                <select
                                    id="department"
                                    value={department}
                                    onChange={(e) => setDepartment(e.target.value)}
                                    required
                                >
                                    <option value="" disabled>Select department</option>
                                    {DEPARTMENTS.map((d) => (
                                        <option key={d} value={d}>{d}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="form-group">
                                <label htmlFor="file-upload">Document File</label>
                                <div className="file-drop-zone">
                                    <input
                                        id="file-upload"
                                        type="file"
                                        accept=".pdf,.docx"
                                        onChange={(e) => setFile(e.target.files[0] || null)}
                                        className="file-input"
                                    />
                                    <div className="file-drop-content">
                                        {file ? (
                                            <>
                                                <span className="file-icon">📎</span>
                                                <p className="file-name">{file.name}</p>
                                                <p className="text-muted">{(file.size / 1024).toFixed(1)} KB</p>
                                            </>
                                        ) : (
                                            <>
                                                <span className="file-icon">⇪</span>
                                                <p>Click to select a file</p>
                                                <p className="text-muted">PDF or DOCX, max 50MB</p>
                                            </>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <button type="submit" className="btn btn-primary" disabled={loading}>
                                {loading ? <span className="spinner-sm" /> : 'Upload Document'}
                            </button>
                        </form>
                    </div>
                </main>
            </div>
        </div>
    );
}
