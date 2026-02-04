import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

function AnimatedBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {/* Floating circles */}
      <svg className="absolute top-0 left-0 w-full h-full" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#6366f1" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.1" />
          </linearGradient>
          <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ec4899" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.1" />
          </linearGradient>
        </defs>

        {/* Animated circle 1 */}
        <circle cx="10%" cy="20%" r="150" fill="url(#grad1)">
          <animate attributeName="cx" values="10%;15%;10%" dur="8s" repeatCount="indefinite" />
          <animate attributeName="cy" values="20%;25%;20%" dur="6s" repeatCount="indefinite" />
          <animate attributeName="r" values="150;180;150" dur="4s" repeatCount="indefinite" />
        </circle>

        {/* Animated circle 2 */}
        <circle cx="85%" cy="70%" r="200" fill="url(#grad2)">
          <animate attributeName="cx" values="85%;80%;85%" dur="10s" repeatCount="indefinite" />
          <animate attributeName="cy" values="70%;75%;70%" dur="7s" repeatCount="indefinite" />
          <animate attributeName="r" values="200;170;200" dur="5s" repeatCount="indefinite" />
        </circle>

        {/* Animated circle 3 */}
        <circle cx="50%" cy="90%" r="100" fill="url(#grad1)">
          <animate attributeName="cx" values="50%;55%;50%" dur="9s" repeatCount="indefinite" />
          <animate attributeName="cy" values="90%;85%;90%" dur="8s" repeatCount="indefinite" />
        </circle>

        {/* Animated circle 4 */}
        <circle cx="70%" cy="10%" r="80" fill="url(#grad2)">
          <animate attributeName="cx" values="70%;65%;70%" dur="7s" repeatCount="indefinite" />
          <animate attributeName="cy" values="10%;15%;10%" dur="5s" repeatCount="indefinite" />
        </circle>
      </svg>

      {/* Grid pattern */}
      <svg className="absolute inset-0 w-full h-full opacity-[0.03]" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
            <path d="M 60 0 L 0 0 0 60" fill="none" stroke="currentColor" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      {/* Animated lines */}
      <svg className="absolute inset-0 w-full h-full" xmlns="http://www.w3.org/2000/svg">
        <line x1="0" y1="30%" x2="100%" y2="70%" stroke="url(#grad1)" strokeWidth="1" opacity="0.3">
          <animate attributeName="y1" values="30%;35%;30%" dur="6s" repeatCount="indefinite" />
          <animate attributeName="y2" values="70%;65%;70%" dur="6s" repeatCount="indefinite" />
        </line>
        <line x1="0" y1="60%" x2="100%" y2="20%" stroke="url(#grad2)" strokeWidth="1" opacity="0.2">
          <animate attributeName="y1" values="60%;55%;60%" dur="8s" repeatCount="indefinite" />
          <animate attributeName="y2" values="20%;25%;20%" dur="8s" repeatCount="indefinite" />
        </line>
      </svg>
    </div>
  );
}

function AnimatedLogo() {
  return (
    <svg width="64" height="64" viewBox="0 0 64 64" className="mb-8">
      <defs>
        <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#8b5cf6" />
        </linearGradient>
      </defs>

      {/* Outer ring */}
      <circle cx="32" cy="32" r="28" fill="none" stroke="url(#logoGrad)" strokeWidth="2" strokeDasharray="176" strokeDashoffset="176">
        <animate attributeName="stroke-dashoffset" values="176;0" dur="1s" fill="freeze" />
      </circle>

      {/* Inner shape */}
      <path d="M32 16 L44 28 L44 40 L32 48 L20 40 L20 28 Z" fill="url(#logoGrad)" opacity="0">
        <animate attributeName="opacity" values="0;1" dur="0.5s" begin="0.5s" fill="freeze" />
        <animateTransform attributeName="transform" type="rotate" values="0 32 32;360 32 32" dur="20s" repeatCount="indefinite" />
      </path>

      {/* Center dot */}
      <circle cx="32" cy="32" r="4" fill="white" opacity="0">
        <animate attributeName="opacity" values="0;1" dur="0.3s" begin="0.8s" fill="freeze" />
        <animate attributeName="r" values="4;5;4" dur="2s" repeatCount="indefinite" />
      </circle>
    </svg>
  );
}

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 500));

    if (login(username, password)) {
      navigate('/');
    } else {
      setError('Credenciales inválidas');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center relative">
      <AnimatedBackground />

      <div className="relative z-10 w-full max-w-md px-8">
        <div className="flex flex-col items-center mb-12">
          <AnimatedLogo />
          <h1 className="text-3xl font-light text-white tracking-tight">
            Ebombo<span className="font-semibold">Lead</span>Manager
          </h1>
          <p className="text-slate-500 mt-2 text-sm tracking-wide">
            Plataforma de Gestión de Leads
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Usuario
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-transparent border-0 border-b-2 border-slate-800 focus:border-indigo-500 text-white text-lg py-3 px-0 outline-none transition-colors placeholder-slate-700"
              placeholder="Ingrese usuario"
              autoComplete="username"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Contraseña
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-transparent border-0 border-b-2 border-slate-800 focus:border-indigo-500 text-white text-lg py-3 px-0 outline-none transition-colors placeholder-slate-700"
              placeholder="Ingrese contraseña"
              autoComplete="current-password"
            />
          </div>

          {error && (
            <div className="flex items-center space-x-2 text-rose-400 text-sm">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full mt-8 bg-gradient-to-r from-indigo-600 to-violet-600 text-white py-4 font-medium tracking-wide uppercase text-sm hover:from-indigo-500 hover:to-violet-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed relative overflow-hidden group"
          >
            <span className={isLoading ? 'opacity-0' : ''}>Iniciar Sesión</span>
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center">
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              </div>
            )}

            {/* Hover effect line */}
            <span className="absolute bottom-0 left-0 w-full h-0.5 bg-white transform scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
          </button>
        </form>

      </div>
    </div>
  );
}
