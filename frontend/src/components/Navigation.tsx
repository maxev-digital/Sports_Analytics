import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { uiEmojis } from '../utils/sportDetection';
import { useSoundEffect } from '../hooks/useSoundEffect';
import { isElectron } from '../utils/isElectron';

export function Navigation() {
  const location = useLocation();
  const navigate = useNavigate();
  const { username, role, token, logout } = useAuth();
  const [strategyDropdownOpen, setStrategyDropdownOpen] = useState(false);
  const [strategyResultsDropdownOpen, setStrategyResultsDropdownOpen] = useState(false);
  const [toolsDropdownOpen, setToolsDropdownOpen] = useState(false);
  const [learnDropdownOpen, setLearnDropdownOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const [unreadFeedbackCount, setUnreadFeedbackCount] = useState(0);
  const strategyRef = useRef<HTMLDivElement>(null);
  const strategyResultsRef = useRef<HTMLDivElement>(null);
  const toolsRef = useRef<HTMLDivElement>(null);
  const learnRef = useRef<HTMLDivElement>(null);
  const userRef = useRef<HTMLDivElement>(null);
  // Sound effects - DISABLED for menu buttons
  // const playTabSwitch = useSoundEffect('tab-switch.mp3', 0.3);
  // const playDropdown = useSoundEffect('dropdown.mp3', 0.3);
  // const playLogout = useSoundEffect('logout.mp3', 0.4);

  // Check if running in desktop (Electron) mode
  const isDesktop = isElectron();

  // Load unread feedback count
  useEffect(() => {
    const loadUnreadCount = async () => {
      if (!token) return;
      try {
        const response = await fetch(`${window.location.origin}/api/feedback/my-feedback`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        if (response.ok) {
          const data = await response.json();
          const count = data.feedback.filter(
            (f: any) => f.admin_response && !f.response_viewed
          ).length;
          setUnreadFeedbackCount(count);
        }
      } catch (error) {
        console.error('Error loading unread feedback:', error);
      }
    };

    loadUnreadCount();
    // Check every minute for new responses
    const interval = setInterval(loadUnreadCount, 60000);
    return () => clearInterval(interval);
  }, [token]);

  const handleNavClick = () => { /* Sound disabled */ };
  const handleDropdownToggle = (dropdownSetter: (val: boolean) => void, currentState: boolean) => { /* Sound disabled */ dropdownSetter(!currentState); };
  const handleLogout = () => { /* Sound disabled */ logout(); navigate('/login'); };

  // Main nav items (always visible)
  const mainNavItems = [
    { path: '/live-games', label: 'Game Cards', emoji: uiEmojis.fire },
    { path: '/odds', label: 'Odds', emoji: uiEmojis.chart },
    { path: '/analytics', label: 'My Analytics', emoji: uiEmojis.search },
    { path: '/alerts', label: 'Alerts', emoji: uiEmojis.lightning },
    { path: '/props', label: 'Player Props', emoji: uiEmojis.book },
    { path: '/handicapper-picks', label: 'Cappers Picks', emoji: uiEmojis.star },
  ];

  // Strategy Results dropdown items (Live vs Pre-Game)
  const strategyResultsItems = [
    { path: '/strategy-results', label: 'Live Strategies', emoji: uiEmojis.fire },
    { path: '/pre-game-strategy-results', label: 'Pre-Game Strategies', emoji: uiEmojis.trophy },
  ];

  // Strategy Settings dropdown items
  const strategyItems = [
    { path: '/strategy-settings', label: 'Strategy Settings', emoji: uiEmojis.trophy },
  ];

  // Tools dropdown items (includes Bookmaker Settings)
  const toolsItems = [
    { path: '/tools', label: 'Betting Tools', emoji: uiEmojis.wrench },
    { path: '/settings', label: 'Bookmaker Settings', emoji: uiEmojis.gear },
    { path: '/my-feedback', label: 'My Feedback', emoji: uiEmojis.book, badge: unreadFeedbackCount },
    ...(role === 'admin' ? [{ path: '/admin-dashboard', label: 'Admin Dashboard', emoji: uiEmojis.star }] : []),
  ];

  // Learn dropdown items
  const learnItems = [
    { path: '/learn', label: 'Learn Articles', emoji: uiEmojis.graduation },
    { path: '/getting-started', label: 'Getting Started', emoji: uiEmojis.rocket },
    { path: '/odds-explained', label: 'Odds Explained', emoji: uiEmojis.chart },
  ];

  const isActive = (path: string) => {
    if (path === '/live-games') {
      return location.pathname === '/' || location.pathname === '/live-games';
    }
    return location.pathname.startsWith(path);
  };

  const isDropdownActive = (items: typeof strategyItems) => {
    return items.some(item => isActive(item.path));
  };

  // Close dropdowns when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (strategyRef.current && !strategyRef.current.contains(event.target as Node)) {
        setStrategyDropdownOpen(false);
      }
      if (strategyResultsRef.current && !strategyResultsRef.current.contains(event.target as Node)) {
        setStrategyResultsDropdownOpen(false);
      }
      if (toolsRef.current && !toolsRef.current.contains(event.target as Node)) {
        setToolsDropdownOpen(false);
      }
      if (learnRef.current && !learnRef.current.contains(event.target as Node)) {
        setLearnDropdownOpen(false);
      }
      if (userRef.current && !userRef.current.contains(event.target as Node)) {
        setUserDropdownOpen(false);
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
          <Link to="/live-games" onClick={handleNavClick} className="hover:opacity-80 transition-opacity flex-shrink-0">
            <img
              src="/logo.png"
              alt="Max EV Sports"
              className="h-24 w-auto object-contain"
              style={{ minWidth: '120px', maxWidth: '200px' }}
            />
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-1">
            {/* Main Nav Items - First 5 items (Game Cards through Player Props) */}
            {mainNavItems.slice(0, 5).map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-5 py-2.5 rounded-lg font-semibold transition-all text-base flex items-center gap-2 ${
                  isActive(item.path)
                    ? item.path === '/live-games'
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

            {/* Strategy Results Dropdown - Live vs Pre-Game */}
            <div className="relative" ref={strategyResultsRef}>
              <button
                onClick={() => handleDropdownToggle(setStrategyResultsDropdownOpen, strategyResultsDropdownOpen)}
                className={`px-5 py-2.5 rounded-lg font-semibold transition-all text-base flex items-center gap-2 ${
                  isDropdownActive(strategyResultsItems)
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-slate-100'
                }`}
              >
                <img src={uiEmojis.trophy} alt="" className="w-5 h-5" style={{ imageRendering: 'crisp-edges' }} />
                Strategy Results
                <svg className={`w-5 h-5 transition-transform ${strategyResultsDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {strategyResultsDropdownOpen && (
                <div className="absolute top-full mt-1 left-0 bg-slate-800 border border-slate-700 rounded-lg shadow-xl min-w-[220px] py-2 z-50">
                  {strategyResultsItems.map((item) => (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => { /* Sound disabled */ setStrategyResultsDropdownOpen(false); }}
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

            {/* Main Nav Items - Remaining items (Cappers Picks) */}
            {mainNavItems.slice(5).map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-5 py-2.5 rounded-lg font-semibold transition-all text-base flex items-center gap-2 ${
                  isActive(item.path)
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
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

            {/* Strategies Dropdown - Strategy Settings */}
            <div className="relative" ref={strategyRef}>
              <button
                onClick={() => handleDropdownToggle(setStrategyDropdownOpen, strategyDropdownOpen)}
                className={`px-5 py-2.5 rounded-lg font-semibold transition-all text-base flex items-center gap-2 ${
                  isDropdownActive(strategyItems)
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-slate-100'
                }`}
              >
                <img src={uiEmojis.trophy} alt="" className="w-5 h-5" style={{ imageRendering: 'crisp-edges' }} />
                Strategies
                <svg className={`w-5 h-5 transition-transform ${strategyDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {strategyDropdownOpen && (
                <div className="absolute top-full mt-1 left-0 bg-slate-800 border border-slate-700 rounded-lg shadow-xl min-w-[220px] py-2 z-50">
                  {strategyItems.map((item) => (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => { /* Sound disabled */ setStrategyDropdownOpen(false); }}
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

            {/* Tools Dropdown */}
            <div className="relative" ref={toolsRef}>
              <button
                onClick={() => handleDropdownToggle(setToolsDropdownOpen, toolsDropdownOpen)}
                className={`px-5 py-2.5 rounded-lg font-semibold transition-all text-base flex items-center gap-2 relative ${
                  isDropdownActive(toolsItems)
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-slate-100'
                }`}
              >
                <img src={uiEmojis.wrench} alt="" className="w-5 h-5" style={{ imageRendering: 'crisp-edges' }} />
                Tools
                <svg className={`w-5 h-5 transition-transform ${toolsDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
                {/* Notification Badge */}
                {unreadFeedbackCount > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-600 text-white text-xs font-bold px-1.5 py-0.5 rounded-full min-w-[20px] text-center animate-pulse">
                    {unreadFeedbackCount}
                  </span>
                )}
              </button>

              {toolsDropdownOpen && (
                <div className="absolute top-full mt-1 left-0 bg-slate-800 border border-slate-700 rounded-lg shadow-xl min-w-[220px] py-2 z-50">
                  {toolsItems.map((item) => (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => { /* Sound disabled */ setToolsDropdownOpen(false); }}
                      className={`px-4 py-2.5 flex items-center gap-3 transition-all ${
                        isActive(item.path)
                          ? 'bg-blue-600 text-white'
                          : 'text-slate-300 hover:bg-slate-700 hover:text-slate-100'
                      }`}
                    >
                      <img src={item.emoji} alt="" className="w-5 h-5" style={{ imageRendering: 'crisp-edges' }} />
                      <span className="font-semibold text-base flex-1">{item.label}</span>
                      {item.badge && item.badge > 0 && (
                        <span className="bg-red-600 text-white text-xs font-bold px-2 py-1 rounded-full">
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  ))}
                </div>
              )}
            </div>

            {/* Learn Dropdown - Hidden in desktop mode */}
            {!isDesktop && (
              <div className="relative" ref={learnRef}>
                <button
                  onClick={() => handleDropdownToggle(setLearnDropdownOpen, learnDropdownOpen)}
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
                        onClick={() => { /* Sound disabled */ setLearnDropdownOpen(false); }}
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
            )}

          </div>

          {/* Right Side Actions */}
          <div className="flex items-center gap-3 ml-auto">
            {/* User Dropdown Menu */}
            <div className="relative hidden md:block" ref={userRef}>
              <button
                onClick={() => handleDropdownToggle(setUserDropdownOpen, userDropdownOpen)}
                className="flex items-center gap-3 bg-slate-800/50 border-2 border-slate-700 hover:border-slate-600 rounded-lg px-4 py-2 transition-all"
              >
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center text-white font-bold text-sm">
                    {username ? username.charAt(0).toUpperCase() : 'U'}
                  </div>
                  <span className="text-slate-300 text-sm font-semibold">{username}</span>
                </div>
                <svg className={`w-4 h-4 text-slate-400 transition-transform ${userDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {userDropdownOpen && (
                <div className="absolute top-full mt-1 right-0 bg-slate-800 border border-slate-700 rounded-lg shadow-xl min-w-[200px] py-2 z-50">
                  {/* Pricing link - Hidden in desktop mode */}
                  {!isDesktop && (
                    <Link
                      to="/pricing"
                      onClick={() => { /* Sound disabled */ setUserDropdownOpen(false); }}
                      className={`px-4 py-2.5 flex items-center gap-3 transition-all ${
                        isActive('/pricing')
                          ? 'bg-blue-600 text-white'
                          : 'text-slate-300 hover:bg-slate-700 hover:text-slate-100'
                      }`}
                    >
                      <img src={uiEmojis.dollar} alt="" className="w-5 h-5" style={{ imageRendering: 'crisp-edges' }} />
                      <span className="font-semibold text-base">Pricing</span>
                    </Link>
                  )}
                  <button
                    onClick={() => {
                      /* Sound disabled */
                      setUserDropdownOpen(false);
                      setTimeout(() => {
                        logout();
                        navigate('/login');
                      }, 200);
                    }}
                    className="w-full px-4 py-2.5 flex items-center gap-3 text-slate-300 hover:bg-red-900/30 hover:text-red-400 transition-all text-left"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    <span className="font-semibold text-base">Logout</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Mobile Navigation - Scrollable */}
        <div className="md:hidden flex gap-1 pb-3 overflow-x-auto scrollbar-hide">
          {mainNavItems.slice(0, 5).map((item) => (
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
          {strategyResultsItems.map((item) => (
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
          {mainNavItems.slice(5).map((item) => (
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
          {strategyItems.map((item) => (
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
          {toolsItems.map((item) => (
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
          {/* Learn items - Hidden in desktop mode */}
          {!isDesktop && learnItems.map((item) => (
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
          {/* Mobile Pricing Link - Hidden in desktop mode */}
          {!isDesktop && (
            <Link
              to="/pricing" onClick={handleNavClick}
              className={`px-3 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
                isActive('/pricing')
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-slate-300'
              }`}
            >
              <img src={uiEmojis.dollar} alt="" className="w-3.5 h-3.5" style={{ imageRendering: 'crisp-edges' }} />
              Pricing
            </Link>
          )}
          {/* Mobile Logout */}
          <button
            onClick={handleLogout}
            className="px-3 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 bg-red-900/50 text-red-300"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
