import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { uiEmojis } from '../utils/sportDetection';

export function Navigation() {
  const location = useLocation();
  const navigate = useNavigate();
  const { username, logout } = useAuth();
  const [settingsDropdownOpen, setSettingsDropdownOpen] = useState(false);
  const [learnDropdownOpen, setLearnDropdownOpen] = useState(false);
  const settingsRef = useRef<HTMLDivElement>(null);
  const learnRef = useRef<HTMLDivElement>(null);

  // Main nav items (always visible)
  const mainNavItems = [
    { path: '/', label: '', emoji: uiEmojis.fire },
    { path: '/multi-sport', label: 'Multi-Sport', emoji: uiEmojis.target },
    { path: '/odds', label: 'Odds', emoji: uiEmojis.chart },
    { path: '/analytics', label: 'Analytics', emoji: uiEmojis.search },
    { path: '/alerts', label: 'Alerts', emoji: uiEmojis.lightning },
    { path: '/props', label: 'Props', emoji: uiEmojis.book },
  ];

  // Settings dropdown items
  const settingsItems = [
    { path: '/strategy-settings', label: 'Strategies', emoji: uiEmojis.trophy },
    { path: '/settings', label: 'Bookmaker Settings', emoji: uiEmojis.gear },
  ];

  // Learn dropdown items
  const learnItems = [
    { path: '/learn', label: 'Learn Articles', emoji: uiEmojis.graduation },
    { path: '/getting-started', label: 'Getting Started', emoji: uiEmojis.rocket },
  ];

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const isDropdownActive = (items: typeof settingsItems) => {
    return items.some(item => isActive(item.path));
  };

  // Close dropdowns when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (settingsRef.current && !settingsRef.current.contains(event.target as Node)) {
        setSettingsDropdownOpen(false);
      }
      if (learnRef.current && !learnRef.current.contains(event.target as Node)) {
        setLearnDropdownOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <nav className="sticky top-0 z-50 bg-black border-b border-slate-700 shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-24 py-4">
          {/* Logo */}
          <Link to="/" className="hover:opacity-80 transition-opacity flex-shrink-0">
            <img 
              src="/logo.png" 
              alt="Max EV Sports" 
              className="h-24 w-auto object-contain"
              style={{ minWidth: '120px', maxWidth: '200px' }}
            />
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-1">
            {/* Main Nav Items */}
            {mainNavItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-5 py-2.5 rounded-lg font-semibold transition-all text-base flex items-center gap-2 ${
                  isActive(item.path)
                    ? item.path === '/' 
                      ? 'bg-black text-white border-2 border-yellow-500 shadow-lg shadow-yellow-500/30'
                      : 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-slate-100'
                }`}
              >
                {item.emoji && (
                  <img 
                    src={item.emoji} 
                    alt={item.label || 'Home'} 
                    className={item.label ? "w-5 h-5" : "w-8 h-8"} 
                    style={{ imageRendering: 'crisp-edges' }} 
                  />
                )}
                {item.label}
              </Link>
            ))}

            {/* Learn Dropdown */}
            <div className="relative" ref={learnRef}>
              <button
                onClick={() => setLearnDropdownOpen(!learnDropdownOpen)}
                className={`px-5 py-2.5 rounded-lg font-semibold transition-all text-base flex items-center gap-2 ${
                  isDropdownActive(learnItems)
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-slate-100'
                }`}
              >
                <img src={uiEmojis.graduation} alt="" className="w-5 h-5" style={{ imageRendering: 'crisp-edges' }} />
                Learn
                <svg className={`w-5 h-5 transition-transform ${learnDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {learnDropdownOpen && (
                <div className="absolute top-full mt-1 left-0 bg-slate-800 border border-slate-700 rounded-lg shadow-xl min-w-[220px] py-2 z-50">
                  {learnItems.map((item) => (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setLearnDropdownOpen(false)}
                      className={`px-4 py-2.5 flex items-center gap-3 transition-all ${
                        isActive(item.path)
                          ? 'bg-blue-600 text-white'
                          : 'text-slate-300 hover:bg-slate-700 hover:text-slate-100'
                      }`}
                    >
                      <img src={item.emoji} alt="" className="w-5 h-5" style={{ imageRendering: 'crisp-edges' }} />
                      <span className="font-semibold text-base">{item.label}</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            {/* Pricing - standalone */}
            <Link
              to="/pricing"
              className={`px-5 py-2.5 rounded-lg font-semibold transition-all text-base flex items-center gap-2 ${
                isActive('/pricing')
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-slate-100'
              }`}
            >
              <img src={uiEmojis.dollar} alt="" className="w-5 h-5" style={{ imageRendering: 'crisp-edges' }} />
              Pricing
            </Link>
          </div>

          {/* Right Side Actions */}
          <div className="flex items-center gap-3 ml-auto">
            {/* Settings Dropdown - moved to far right */}
            <div className="relative hidden md:block" ref={settingsRef}>
              <button
                onClick={() => setSettingsDropdownOpen(!settingsDropdownOpen)}
                className={`px-5 py-2.5 rounded-lg font-semibold transition-all text-base flex items-center gap-2 ${
                  isDropdownActive(settingsItems)
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-slate-100'
                }`}
              >
                <img src={uiEmojis.gear} alt="" className="w-5 h-5" style={{ imageRendering: 'crisp-edges' }} />
                Settings
                <svg className={`w-5 h-5 transition-transform ${settingsDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {settingsDropdownOpen && (
                <div className="absolute top-full mt-1 right-0 bg-slate-800 border border-slate-700 rounded-lg shadow-xl min-w-[220px] py-2 z-50">
                  {settingsItems.map((item) => (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setSettingsDropdownOpen(false)}
                      className={`px-4 py-2.5 flex items-center gap-3 transition-all ${
                        isActive(item.path)
                          ? 'bg-blue-600 text-white'
                          : 'text-slate-300 hover:bg-slate-700 hover:text-slate-100'
                      }`}
                    >
                      <img src={item.emoji} alt="" className="w-5 h-5" style={{ imageRendering: 'crisp-edges' }} />
                      <span className="font-semibold text-base">{item.label}</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center gap-3 bg-slate-800/50 border-2 border-slate-700 rounded-lg px-4 py-2">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center text-white font-bold text-sm">
                  {username ? username.charAt(0).toUpperCase() : 'U'}
                </div>
                <span className="text-slate-300 text-sm font-semibold">{username}</span>
              </div>
              <button
                onClick={() => {
                  logout();
                  navigate('/login');
                }}
                className="px-4 py-1.5 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition-all text-xs"
              >
                Logout
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation - Scrollable */}
        <div className="md:hidden flex gap-1 pb-3 overflow-x-auto scrollbar-hide">
          {mainNavItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`px-3 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
                isActive(item.path)
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-slate-300'
              }`}
            >
              {item.emoji && (
                <img src={item.emoji} alt="" className="w-3.5 h-3.5" style={{ imageRendering: 'crisp-edges' }} />
              )}
              {item.label}
            </Link>
          ))}
          {settingsItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`px-3 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
                isActive(item.path)
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-slate-300'
              }`}
            >
              {item.emoji && (
                <img src={item.emoji} alt="" className="w-3.5 h-3.5" style={{ imageRendering: 'crisp-edges' }} />
              )}
              {item.label}
            </Link>
          ))}
          {learnItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`px-3 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
                isActive(item.path)
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-slate-300'
              }`}
            >
              {item.emoji && (
                <img src={item.emoji} alt="" className="w-3.5 h-3.5" style={{ imageRendering: 'crisp-edges' }} />
              )}
              {item.label}
            </Link>
          ))}
          <Link
            to="/pricing"
            className={`px-3 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
              isActive('/pricing')
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-300'
            }`}
          >
            <img src={uiEmojis.dollar} alt="" className="w-3.5 h-3.5" style={{ imageRendering: 'crisp-edges' }} />
            Pricing
          </Link>
        </div>
      </div>
    </nav>
  );
}
