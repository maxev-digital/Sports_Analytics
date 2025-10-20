import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { uiEmojis } from '../utils/sportDetection';

export function Navigation() {
  const location = useLocation();
  const { username, logout } = useAuth();

  const navItems = [
    { path: '/', label: 'Live Games', emoji: uiEmojis.fire },
    { path: '/multi-sport', label: 'Multi-Sport', emoji: uiEmojis.target },
    { path: '/alerts', label: 'Alerts', emoji: uiEmojis.lightning },
    { path: '/tools', label: 'Tools', emoji: uiEmojis.search },
    { path: '/analytics', label: 'Analytics', emoji: uiEmojis.chart },
    { path: '/props', label: 'Props', emoji: uiEmojis.book },
    { path: '/settings', label: 'Settings', emoji: uiEmojis.gear },
    { path: '/learn', label: 'Learn', emoji: uiEmojis.graduation },
    { path: '/getting-started', label: 'Get Started', emoji: uiEmojis.rocket },
    { path: '/pricing', label: 'Pricing', emoji: uiEmojis.dollar },
  ];

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur-sm border-b border-slate-700 shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <div>
              <div className="text-xl font-bold text-slate-100">Max EV Sports</div>
              <div className="text-[10px] text-blue-400 -mt-0.5">Maximum EV Is Our Specialty</div>
            </div>
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-4 py-2 rounded-lg font-semibold transition-all text-sm flex items-center gap-2 ${
                  isActive(item.path)
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-slate-100'
                }`}
              >
                {item.emoji && (
                  <img src={item.emoji} alt="" className="w-4 h-4" style={{ imageRendering: 'crisp-edges' }} />
                )}
                {item.label}
              </Link>
            ))}
          </div>

          {/* Right Side Actions */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-3 bg-slate-800/50 border-2 border-slate-700 rounded-lg px-4 py-2">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center text-white font-bold text-sm">
                  {username ? username.charAt(0).toUpperCase() : 'U'}
                </div>
                <span className="text-slate-300 text-sm font-semibold">{username}</span>
              </div>
              <button
                onClick={logout}
                className="px-4 py-1.5 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition-all text-xs"
              >
                Logout
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden flex gap-1 pb-3 overflow-x-auto scrollbar-hide">
          {navItems.map((item) => (
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
        </div>
      </div>
    </nav>
  );
}
