import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getApiUrl } from '../config';
import { useBetAlertNotification } from '../contexts/BetAlertNotificationContext';

export function Navigation() {
  const location = useLocation();
  const navigate = useNavigate();
  const { username, role, token, logout } = useAuth();
  const { isAudioMuted, toggleAudioMute } = useBetAlertNotification();

  const [rankingsDropdownOpen, setRankingsDropdownOpen] = useState(false);
  const [edgesDropdownOpen, setEdgesDropdownOpen] = useState(false);
  const [strategyDropdownOpen, setStrategyDropdownOpen] = useState(false);
  const [toolsDropdownOpen, setToolsDropdownOpen] = useState(false);
  const [marketsDropdownOpen, setMarketsDropdownOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

  const rankingsRef = useRef<HTMLDivElement>(null);
  const edgesRef = useRef<HTMLDivElement>(null);
  const strategyRef = useRef<HTMLDivElement>(null);
  const toolsRef = useRef<HTMLDivElement>(null);
  const marketsRef = useRef<HTMLDivElement>(null);
  const userRef = useRef<HTMLDivElement>(null);

  const isActive = (path: string) =>
    path === '/live-games'
      ? location.pathname === '/' || location.pathname === '/live-games'
      : location.pathname.startsWith(path);

  const isDropdownActive = (items: { path: string }[]) =>
    items.some(item => isActive(item.path));

  const handleLogout = () => { logout(); navigate('/login'); };

  const mainNavItems = [
    { path: '/live-games', label: 'GAME CARDS' },
    { path: '/odds',       label: 'ODDS' },
    { path: '/alerts',     label: 'ALERTS', live: true },
  ];

  const rankingsItems = [
    { path: '/team-rankings',     label: 'TEAM RANKINGS'     },
    { path: '/advanced-metrics',  label: 'ADVANCED METRICS'  },
    { path: '/player-leaders',    label: 'PLAYER LEADERS'    },
    { path: '/statcast',          label: 'STATCAST'          },
  ];

  const edgesItems = [
    { path: '/picks',               label: 'PICKS' },
    { path: '/f5-edge',             label: 'F5 EDGE ENGINE' },
    { path: '/max-ev-edges',        label: 'ML EDGES' },
    { path: '/model-performance',   label: 'MODEL PERFORMANCE' },
    { path: '/predictions-database', label: 'PREDICTIONS DB' },
  ];

  const strategyItems: { path: string; label: string }[] = [];

  const marketsItems = [
    { path: '/kalshi', label: 'KALSHI' },
  ];

  const toolsItems = [
    { path: '/tools',            label: 'BETTING TOOLS' },
    { path: '/line-movement',    label: 'LINE MOVEMENT' },
    { path: '/settings',         label: 'BOOKMAKER SETTINGS' },
    { path: '/system-overview',  label: 'HOW WE PICK: ALL SPORTS' },
    { path: '/system-nfl',       label: 'HOW WE PICK: NFL' },
    { path: '/system-health',    label: 'SYSTEM HEALTH' },
    ...(role === 'admin' ? [{ path: '/admin-dashboard', label: 'ADMIN DASHBOARD' }] : []),
  ];

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (rankingsRef.current && !rankingsRef.current.contains(e.target as Node)) setRankingsDropdownOpen(false);
      if (edgesRef.current && !edgesRef.current.contains(e.target as Node)) setEdgesDropdownOpen(false);
      if (strategyRef.current && !strategyRef.current.contains(e.target as Node)) setStrategyDropdownOpen(false);
      if (toolsRef.current && !toolsRef.current.contains(e.target as Node)) setToolsDropdownOpen(false);
      if (marketsRef.current && !marketsRef.current.contains(e.target as Node)) setMarketsDropdownOpen(false);
      if (userRef.current && !userRef.current.contains(e.target as Node)) setUserDropdownOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const navBtn = (active: boolean, extra = '') =>
    `px-4 py-2 rounded-lg font-bold text-base transition-all italic flex items-center gap-1.5 ${extra} ${
      active ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
    }`;

  const dropdownLink = (active: boolean) =>
    `px-4 py-2.5 flex items-center gap-3 text-base font-semibold italic transition-all ${
      active ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-700 hover:text-white'
    }`;

  const chevron = (open: boolean) => (
    <svg className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  );

  const dropdownPanel = (children: React.ReactNode) => (
    <div className="absolute top-full mt-1 left-0 bg-slate-800 border border-slate-700 rounded-lg shadow-xl min-w-[220px] py-1 z-50">
      {children}
    </div>
  );

  return (
    <nav className="sticky top-0 z-50 bg-black border-b border-slate-700 shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-20">

          {/* Logo */}
          <Link to="/live-games" className="hover:opacity-80 transition-opacity flex-shrink-0">
            <img src="/3DMaxLogo.png" alt="Max EV Sports" className="h-20 w-auto object-contain" style={{ mixBlendMode: 'screen' }} />
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">

            {/* Main flat items */}
            {mainNavItems.map(item => (
              <Link key={item.path} to={item.path} className={navBtn(isActive(item.path))}>
                {item.label}
                {item.live && (
                  <span className="flex items-center gap-1 ml-0.5">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
                    </span>
                    <span className="text-xs text-red-400 font-bold">LIVE</span>
                  </span>
                )}
              </Link>
            ))}

            {/* RANKINGS dropdown */}
            <div className="relative" ref={rankingsRef}>
              <button
                onClick={() => setRankingsDropdownOpen(o => !o)}
                className={navBtn(isDropdownActive(rankingsItems))}
              >
                RANKINGS {chevron(rankingsDropdownOpen)}
              </button>
              {rankingsDropdownOpen && dropdownPanel(
                rankingsItems.map(item => (
                  <Link key={item.path} to={item.path} onClick={() => setRankingsDropdownOpen(false)} className={dropdownLink(isActive(item.path))}>
                    {item.label}
                  </Link>
                ))
              )}
            </div>

            {/* MAX-EV EDGE dropdown */}
            <div className="relative" ref={edgesRef}>
              <button
                onClick={() => setEdgesDropdownOpen(o => !o)}
                className={navBtn(isDropdownActive(edgesItems))}
              >
                MAX-EV EDGE {chevron(edgesDropdownOpen)}
              </button>
              {edgesDropdownOpen && dropdownPanel(
                edgesItems.map(item => (
                  <Link key={item.path} to={item.path} onClick={() => setEdgesDropdownOpen(false)} className={dropdownLink(isActive(item.path))}>
                    {item.label}
                  </Link>
                ))
              )}
            </div>

            {/* TOOLS dropdown */}
            <div className="relative" ref={toolsRef}>
              <button
                onClick={() => setToolsDropdownOpen(o => !o)}
                className={navBtn(isDropdownActive(toolsItems))}
              >
                TOOLS {chevron(toolsDropdownOpen)}
              </button>
              {toolsDropdownOpen && dropdownPanel(
                toolsItems.map(item => (
                  <Link key={item.path} to={item.path} onClick={() => setToolsDropdownOpen(false)} className={dropdownLink(isActive(item.path))}>
                    {item.label}
                  </Link>
                ))
              )}
            </div>

            {/* PREDICTION MARKETS dropdown */}
            <div className="relative" ref={marketsRef}>
              <button
                onClick={() => setMarketsDropdownOpen(o => !o)}
                className={navBtn(isDropdownActive(marketsItems))}
              >
                PREDICTION MARKETS {chevron(marketsDropdownOpen)}
              </button>
              {marketsDropdownOpen && dropdownPanel(
                marketsItems.map(item => (
                  <Link key={item.path} to={item.path} onClick={() => setMarketsDropdownOpen(false)} className={dropdownLink(isActive(item.path))}>
                    {item.label}
                  </Link>
                ))
              )}
            </div>

          </div>

          {/* User menu */}
          <div className="relative hidden md:block" ref={userRef}>
            <button
              onClick={() => setUserDropdownOpen(o => !o)}
              className="flex items-center gap-2 bg-slate-800/50 border border-slate-700 hover:border-slate-500 rounded-lg px-3 py-2 transition-all"
            >
              <div className="w-7 h-7 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center text-white font-bold text-xs">
                {username ? username.charAt(0).toUpperCase() : 'U'}
              </div>
              <span className="text-slate-300 text-sm font-semibold">{username}</span>
              {chevron(userDropdownOpen)}
            </button>

            {userDropdownOpen && (
              <div className="absolute top-full mt-1 right-0 bg-slate-800 border border-slate-700 rounded-lg shadow-xl min-w-[190px] py-1 z-50">
                <button
                  onClick={toggleAudioMute}
                  className={`w-full px-4 py-2.5 flex items-center gap-3 text-sm font-semibold text-left transition-all ${
                    isAudioMuted ? 'text-slate-400 hover:bg-slate-700' : 'text-green-400 hover:bg-green-900/30'
                  }`}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {isAudioMuted
                      ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                      : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                    }
                  </svg>
                  Alert Audio: {isAudioMuted ? 'OFF' : 'ON'}
                </button>
                <button
                  onClick={() => { setUserDropdownOpen(false); handleLogout(); }}
                  className="w-full px-4 py-2.5 flex items-center gap-3 text-sm font-semibold text-slate-300 hover:bg-red-900/30 hover:text-red-400 transition-all text-left"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  Logout
                </button>
              </div>
            )}
          </div>

        </div>

        {/* Mobile nav — horizontal scroll */}
        <div className="md:hidden flex gap-1 pb-2 overflow-x-auto scrollbar-hide">
          {[...mainNavItems, ...rankingsItems, ...edgesItems, ...strategyItems, ...toolsItems, ...marketsItems].map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all italic ${
                isActive(item.path) ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-300'
              }`}
            >
              {item.label}
            </Link>
          ))}
          <button
            onClick={handleLogout}
            className="px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap bg-red-900/50 text-red-300"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
