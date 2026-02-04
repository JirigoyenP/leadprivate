import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { Mail, Upload, Database, Linkedin, Rocket } from 'lucide-react';
import VerifyPage from './pages/VerifyPage';
import BatchPage from './pages/BatchPage';
import HubSpotPage from './pages/HubSpotPage';
import LinkedInPage from './pages/LinkedInPage';
import ApolloPage from './pages/ApolloPage';

function App() {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Single Verify', icon: Mail },
    { path: '/batch', label: 'Batch Upload', icon: Upload },
    { path: '/apollo', label: 'Apollo', icon: Rocket },
    { path: '/hubspot', label: 'HubSpot', icon: Database },
    { path: '/linkedin', label: 'LinkedIn', icon: Linkedin },
  ];

  return (
    <div className="min-h-screen">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold text-indigo-600">EbomboLeadManager</h1>
              </div>
              <div className="hidden sm:ml-8 sm:flex sm:space-x-4">
                {navItems.map(({ path, label, icon: Icon }) => (
                  <Link
                    key={path}
                    to={path}
                    className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                      location.pathname === path
                        ? 'bg-indigo-100 text-indigo-700'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {label}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <Routes>
          <Route path="/" element={<VerifyPage />} />
          <Route path="/batch" element={<BatchPage />} />
          <Route path="/apollo" element={<ApolloPage />} />
          <Route path="/hubspot" element={<HubSpotPage />} />
          <Route path="/linkedin" element={<LinkedInPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
