import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './components/context/AuthContext';
import ProtectedRoute from './routes/ProtectedRoute';

import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import AdminDashboard from './pages/AdminDashboard';
import EmployeeDashboard from './pages/EmployeeDashboard';
import UploadPage from './pages/UploadPage';
import AskPage from './pages/AskPage';

export default function App() {
    return (
        <BrowserRouter>
            <AuthProvider>
                <Routes>
                    {/* Public routes */}
                    <Route path="/" element={<LoginPage />} />
                    <Route path="/signup" element={<SignupPage />} />

                    {/* Admin routes */}
                    <Route
                        path="/admin"
                        element={
                            <ProtectedRoute allowedRoles={['ADMIN', 'REVIEWER']}>
                                <AdminDashboard />
                            </ProtectedRoute>
                        }
                    />

                    {/* Employee routes */}
                    <Route
                        path="/employee"
                        element={
                            <ProtectedRoute allowedRoles={['VIEWER', 'CONTRIBUTOR', 'REVIEWER', 'ADMIN']}>
                                <EmployeeDashboard />
                            </ProtectedRoute>
                        }
                    />

                    {/* Upload — CONTRIBUTOR+ */}
                    <Route
                        path="/upload"
                        element={
                            <ProtectedRoute allowedRoles={['CONTRIBUTOR', 'REVIEWER', 'ADMIN']}>
                                <UploadPage />
                            </ProtectedRoute>
                        }
                    />

                    {/* Ask — All authenticated */}
                    <Route
                        path="/ask"
                        element={
                            <ProtectedRoute allowedRoles={['VIEWER', 'CONTRIBUTOR', 'REVIEWER', 'ADMIN']}>
                                <AskPage />
                            </ProtectedRoute>
                        }
                    />
                </Routes>
            </AuthProvider>
        </BrowserRouter>
    );
}
