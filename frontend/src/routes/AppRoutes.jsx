import { Navigate, Route, Routes } from 'react-router-dom';
import ProtectedRoute from '../components/common/ProtectedRoute';
import Dashboard from '../pages/Dashboard';
import Emergency from '../pages/Emergency';
import EmergencyDetails from '../pages/EmergencyDetails';
import History from '../pages/History';
import LiveLocation from '../pages/LiveLocation';
import Notifications from '../pages/Notifications';
import Profile from '../pages/Profile';
import TrustedContacts from '../pages/TrustedContacts';
import Login from '../pages/auth/Login';
import Register from '../pages/auth/Register';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/emergency" element={<ProtectedRoute><Emergency /></ProtectedRoute>} />
      <Route path="/emergency/:id" element={<ProtectedRoute><EmergencyDetails /></ProtectedRoute>} />
      <Route path="/live-location" element={<ProtectedRoute><LiveLocation /></ProtectedRoute>} />
      <Route path="/trusted-contacts" element={<ProtectedRoute><TrustedContacts /></ProtectedRoute>} />
      <Route path="/notifications" element={<ProtectedRoute><Notifications /></ProtectedRoute>} />
      <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
