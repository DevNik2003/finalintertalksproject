import api from './api';

/**
 * Get all documents (admin/reviewer)
 */
export const getDocuments = async () => {
    const { data } = await api.get('/documents/');
    return data;
};

/**
 * Upload a document
 */
export const uploadDocument = async (title, department, file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('department', department);
    // Note: backend uses filename from the file, title is separate concept
    // The backend currently uses file.filename as title

    const { data } = await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
};

/**
 * Approve a document version
 */
export const approveDocument = async (versionId) => {
    const { data } = await api.post(`/documents/${versionId}/approve`);
    return data;
};

/**
 * Submit a RAG query to the retrieval pipeline
 */
export const askQuery = async (query) => {
    const { data } = await api.post('/query/', { query });
    return data;
};
