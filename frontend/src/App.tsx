import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { LayoutDashboard, Mail, Upload, Database, Linkedin, Users, Send, LogOut, Zap } from 'lucide-react';
import { useAuth } from './context/AuthContext';
import DashboardPage from './pages/DashboardPage';
import VerifyPage from './pages/VerifyPage';
import BatchPage from './pages/BatchPage';
import HubSpotPage from './pages/HubSpotPage';
import LinkedInPage from './pages/LinkedInPage';
import LeadsPage from './pages/LeadsPage';
import OutreachPage from './pages/OutreachPage';
import PipelinePage from './pages/PipelinePage';
import LoginPage from './pages/LoginPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function Dashboard() {
  const location = useLocation();
  const { logout } = useAuth();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/leads', label: 'Leads', icon: Users },
    { path: '/verify', label: 'Verify', icon: Mail },
    { path: '/batch', label: 'Batch Upload', icon: Upload },
    { path: '/hubspot', label: 'HubSpot', icon: Database },
    { path: '/linkedin', label: 'LinkedIn', icon: Linkedin },
    { path: '/outreach', label: 'Outreach', icon: Send },
    { path: '/pipeline', label: 'Pipeline', icon: Zap },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-slate-950 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-light text-white tracking-tight">
                  Ebombo<span className="font-semibold text-indigo-400">Lead</span>Manager
                </h1>
              </div>
              <div className="hidden sm:ml-8 sm:flex sm:space-x-1">
                {navItems.map(({ path, label, icon: Icon }) => (
                  <Link
                    key={path}
                    to={path}
                    className={`inline-flex items-center px-4 py-2 text-sm font-medium transition-colors ${
                      location.pathname === path
                        ? 'bg-indigo-600 text-white'
                        : 'text-slate-400 hover:text-white hover:bg-slate-800'
                    }`}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {label}
                  </Link>
                ))}
              </div>
            </div>
            <div className="flex items-center">
              <button
                onClick={logout}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/leads" element={<LeadsPage />} />
          <Route path="/verify" element={<VerifyPage />} />
          <Route path="/batch" element={<BatchPage />} />
          <Route path="/hubspot" element={<HubSpotPage />} />
          <Route path="/linkedin" element={<LinkedInPage />} />
          <Route path="/outreach" element={<OutreachPage />} />
          <Route path="/pipeline" element={<PipelinePage />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />}
      />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;
