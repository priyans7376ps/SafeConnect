import { Navigate, useLocation } from 'react-router-dom';
import Navbar from './components/common/Navbar';
import Sidebar from './components/common/Sidebar';
import { AuthProvider } from './context/AuthContext';
import { EmergencyProvider } from './context/EmergencyContext';
import { useAuth } from './hooks/useAuth';
import AppRoutes from './routes/AppRoutes';

const AUTH_ROUTES = ['/login', '/register'];

function AppShell() {
  const { user } = useAuth();
  const location = useLocation();
  const isAuthPage = AUTH_ROUTES.includes(location.pathname);

  // Unauthenticated users trying to reach protected pages → redirect to login
  if (!user && !isAuthPage) {
    return <Navigate to="/login" replace />;
  }

  // Auth pages render FULL-SCREEN — no app-shell / sidebar / navbar wrapper
  if (isAuthPage) {
    return <AppRoutes />;
  }

  // Authenticated app pages get the normal shell
  return (
    <div className="app-shell">
      <Navbar />
      <div className="content-shell">
        <Sidebar />
        <main className="main-area">
          <AppRoutes />
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <EmergencyProvider>
        <AppShell />
      </EmergencyProvider>
    </AuthProvider>
  );
}
