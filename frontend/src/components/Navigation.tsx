import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useBetAlertNotification } from '../contexts/BetAlertNotificationContext';
import { getUserTier, canAccessRoute, getRouteTier, AccessTier } from '../lib/accessMap';
import { UpgradeModal } from './UpgradeModal';

interface NavItem {
  path: string;
  label: string;
}

interface UpgradeTarget {
  featureLabel: string;
  requiredTier: 'member' | 'pro';
}

export function Navigation() {
  const location = useLocation();
  const navigate = useNavigate();
  const { username, role, token, logout, isAuthenticated, subscriptionTier } = useAuth();
  const { isAudioMuted, toggleAudioMute } = useBetAlertNotification();

  const userTier = getUserTier(isAuthenticated, subscriptionTier, role);

  const [rankingsDropdownOpen, setRankingsDropdownOpen]   = useState(false);
  const [edgesDropdownOpen,    setEdgesDropdownOpen]      = useState(false);
  const [dataLabDropdownOpen,  setDataLabDropdownOpen]    = useState(false);
  const [toolsDropdownOpen,    setToolsDropdownOpen]      = useState(false);
  const [marketsDropdownOpen,  setMarketsDropdownOpen]    = useState(false);
  const [userDropdownOpen,     setUserDropdownOpen]       = useState(false);
  const [upgradeModal,         setUpgradeModal]           = useState<UpgradeTarget | null>(null);

  const rankingsRef = useRef<HTMLDivElement>(null);
  const edgesRef    = useRef<HTMLDivElement>(null);
  const dataLabRef  = useRef<HTMLDivElement>(null);
  const toolsRef    = useRef<HTMLDivElement>(null);
  const marketsRef  = useRef<HTMLDivElement>(null);
  const userRef     = useRef<HTMLDivElement>(null);

  const isActive = (path: string) =>
    path === '/live-games'
      ? location.pathname === '/' || location.pathname === '/live-games'
      : location.pathname.startsWith(path);

  const isDropdownActive = (items: NavItem[]) => items.some(item => isActive(item.path));

  const handleLogout = () => { logout(); navigate('/login'); };

  // ── Nav item lists ─────────────────────────────────────────────────────
  const mainNavItems: NavItem[] = [
    { path: '/live-games', label: 'GAME CARDS' },
    { path: '/odds',       label: 'ODDS'        },
    { path: '/alerts',     label: 'ALERTS'      },
  ];

  const rankingsItems: NavItem[] = [
    { path: '/power-rankings',   label: 'POWER RANKINGS'    },
    { path: '/team-rankings',    label: 'STANDINGS'         },
    { path: '/advanced-metrics', label: 'ADVANCED METRICS'  },
    { path: '/player-leaders',   label: 'PLAYER LEADERS'    },
    { path: '/statcast',         label: 'STATCAST'          },
    { path: '/madden-ratings',   label: 'MADDEN 26 RATINGS' },
  ];

  const edgesItems: NavItem[] = [
    { path: '/todays-plays',         label: "TODAY'S PLAYS"    },
    { path: '/accuracy',             label: 'PICKS RECORD'     },
    { path: '/picks',                label: 'PICKS'            },
    { path: '/model-projections',    label: 'MODEL PROJECTIONS'},
    { path: '/model-research',       label: 'MODEL RESEARCH'   },
    { path: '/f5-edge',              label: 'F5 EDGE ENGINE'   },
    { path: '/betting-rankings',     label: 'BETTING RANKINGS' },
    { path: '/max-ev-edges',         label: 'ML EDGES'         },
    { path: '/model-performance',    label: 'MODEL PERFORMANCE'},
    { path: '/predictions-database', label: 'PREDICTIONS DB'   },
  ];

  const dataLabItems: NavItem[] = [
    { path: '/nfl-schedule',    label: 'NFL SCHEDULE'     },
    { path: '/matchup-lab',     label: 'MATCHUP LAB'      },
    { path: '/trends',          label: 'TEAM TRENDS'      },
    { path: '/nfl-trends',      label: 'NFL ATS & TRENDS' },
    { path: '/cfb-ratings',     label: 'CFB TEAM RATINGS' },
    { path: '/mlb-team-stats',  label: 'MLB TEAM STATS'   },
    { path: '/nfl-team-stats',  label: 'NFL TEAM STATS'   },
    { path: '/referee-trends',  label: 'REFEREE TRACKER'  },
    { path: '/line-movement',   label: 'LINE MOVEMENT'    },
    { path: '/track-record',    label: 'TRACK RECORD'     },
    { path: '/recap',           label: 'DAILY RECAP'      },
    { path: '/survivor',        label: 'SURVIVOR HELPER'  },
    { path: '/confidence-pool', label: 'CONFIDENCE POOL'  },
  ];

  const marketsItems: NavItem[] = [
    { path: '/kalshi', label: 'KALSHI' },
  ];

  const toolsItems: NavItem[] = [
    { path: '/injury-impact',   label: 'INJURY IMPACT ENGINE'    },
    { path: '/injury-heatmap',  label: 'INJURY HEAT MAP'         },
    { path: '/open-bets',       label: 'MY BETS'                 },
    { path: '/tools',           label: 'BETTING TOOLS'           },
    { path: '/settings',        label: 'BOOKMAKER SETTINGS'      },
    { path: '/system-overview', label: 'HOW WE PICK: ALL SPORTS' },
    { path: '/system-nfl',      label: 'HOW WE PICK: NFL'        },
    { path: '/data-points',     label: 'DATA POINTS'             },
    { path: '/system-health',   label: 'SYSTEM HEALTH'           },
    ...(role === 'admin' ? [{ path: '/admin-dashboard', label: 'ADMIN DASHBOARD' }] : []),
  ];

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (rankingsRef.current && !rankingsRef.current.contains(e.target as Node)) setRankingsDropdownOpen(false);
      if (edgesRef.current    && !edgesRef.current.contains(e.target as Node))    setEdgesDropdownOpen(false);
      if (dataLabRef.current  && !dataLabRef.current.contains(e.target as Node))  setDataLabDropdownOpen(false);
      if (toolsRef.current    && !toolsRef.current.contains(e.target as Node))    setToolsDropdownOpen(false);
      if (marketsRef.current  && !marketsRef.current.contains(e.target as Node))  setMarketsDropdownOpen(false);
      if (userRef.current     && !userRef.current.contains(e.target as Node))     setUserDropdownOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  // ── Style helpers ──────────────────────────────────────────────────────
  const navBtn = (active: boolean) =>
    `px-4 py-2 rounded-lg font-bold text-base transition-all italic flex items-center gap-1.5 ${
      active ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
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

  // Lock icon SVG
  const LockIcon = () => (
    <svg className="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
    </svg>
  );

  // ── Render a single dropdown item, locked or accessible ───────────────
  const renderDropdownItem = (item: NavItem, closeDropdown: () => void) => {
    const routeTier = getRouteTier(item.path);
    const accessible = canAccessRoute(userTier, routeTier);

    if (accessible) {
      return (
        <Link
          key={item.path}
          to={item.path}
          onClick={closeDropdown}
          className={`px-4 py-2.5 flex items-center gap-3 text-base font-semibold italic transition-all ${
            isActive(item.path) ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-700 hover:text-white'
          }`}
        >
          {item.label}
        </Link>
      );
    }

    // Locked item
    const req = routeTier as 'member' | 'pro';
    const badgeColor = req === 'member' ? '#22c55e' : '#60a5fa';
    const badgeText  = req === 'member' ? 'FREE' : 'PRO';

    return (
      <button
        key={item.path}
        onClick={() => {
          closeDropdown();
          setUpgradeModal({ featureLabel: item.label, requiredTier: req });
        }}
        className="px-4 py-2.5 flex items-center gap-3 text-base font-semibold italic transition-all w-full text-left text-slate-600 hover:bg-slate-700/40 hover:text-slate-500"
      >
        <LockIcon />
        <span className="flex-1">{item.label}</span>
        <span style={{ fontSize: '0.6rem', fontWeight: 800, color: badgeColor, border: `1px solid ${badgeColor}44`, borderRadius: 4, padding: '1px 5px', letterSpacing: '0.05em' }}>
          {badgeText}
        </span>
      </button>
    );
  };

  // ── Render a flat (top-level) nav item ────────────────────────────────
  const renderFlatNavItem = (item: NavItem & { live?: boolean }) => {
    const routeTier = getRouteTier(item.path);
    const accessible = canAccessRoute(userTier, routeTier);

    if (accessible) {
      return (
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
      );
    }

    const req = routeTier as 'member' | 'pro';
    return (
      <button
        key={item.path}
        onClick={() => setUpgradeModal({ featureLabel: item.label, requiredTier: req })}
        className="px-4 py-2 rounded-lg font-bold text-base italic flex items-center gap-1.5 text-slate-600 hover:bg-slate-800/50 hover:text-slate-500 transition-all"
      >
        <LockIcon />
        {item.label}
      </button>
    );
  };

  return (
    <>
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
              {[
                { path: '/live-games', label: 'GAME CARDS' },
                { path: '/odds',       label: 'ODDS'        },
                { path: '/alerts',     label: 'ALERTS', live: true },
              ].map(item => renderFlatNavItem(item))}

              {/* RANKINGS dropdown */}
              <div className="relative" ref={rankingsRef}>
                <button onClick={() => setRankingsDropdownOpen(o => !o)} className={navBtn(isDropdownActive(rankingsItems))}>
                  RANKINGS {chevron(rankingsDropdownOpen)}
                </button>
                {rankingsDropdownOpen && dropdownPanel(
                  rankingsItems.map(item => renderDropdownItem(item, () => setRankingsDropdownOpen(false)))
                )}
              </div>

              {/* MAX-EV EDGE dropdown */}
              <div className="relative" ref={edgesRef}>
                <button onClick={() => setEdgesDropdownOpen(o => !o)} className={navBtn(isDropdownActive(edgesItems))}>
                  MAX-EV EDGE {chevron(edgesDropdownOpen)}
                </button>
                {edgesDropdownOpen && dropdownPanel(
                  edgesItems.map(item => renderDropdownItem(item, () => setEdgesDropdownOpen(false)))
                )}
              </div>

              {/* DATA LAB dropdown */}
              <div className="relative" ref={dataLabRef}>
                <button onClick={() => setDataLabDropdownOpen(o => !o)} className={navBtn(isDropdownActive(dataLabItems))}>
                  DATA LAB {chevron(dataLabDropdownOpen)}
                </button>
                {dataLabDropdownOpen && dropdownPanel(
                  dataLabItems.map(item => renderDropdownItem(item, () => setDataLabDropdownOpen(false)))
                )}
              </div>

              {/* TOOLS dropdown */}
              <div className="relative" ref={toolsRef}>
                <button onClick={() => setToolsDropdownOpen(o => !o)} className={navBtn(isDropdownActive(toolsItems))}>
                  TOOLS {chevron(toolsDropdownOpen)}
                </button>
                {toolsDropdownOpen && dropdownPanel(
                  toolsItems.map(item => renderDropdownItem(item, () => setToolsDropdownOpen(false)))
                )}
              </div>

              {/* PREDICTION MARKETS dropdown */}
              <div className="relative" ref={marketsRef}>
                <button onClick={() => setMarketsDropdownOpen(o => !o)} className={navBtn(isDropdownActive(marketsItems))}>
                  PREDICTION MARKETS {chevron(marketsDropdownOpen)}
                </button>
                {marketsDropdownOpen && dropdownPanel(
                  marketsItems.map(item => renderDropdownItem(item, () => setMarketsDropdownOpen(false)))
                )}
              </div>

            </div>

            {/* User menu */}
            <div className="relative hidden md:block" ref={userRef}>
              {isAuthenticated ? (
                <>
                  <button
                    onClick={() => setUserDropdownOpen(o => !o)}
                    className="flex items-center gap-2 bg-slate-800/50 border border-slate-700 hover:border-slate-500 rounded-lg px-3 py-2 transition-all"
                  >
                    <div className="w-7 h-7 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center text-white font-bold text-xs">
                      {username ? username.charAt(0).toUpperCase() : 'U'}
                    </div>
                    <span className="text-slate-300 text-sm font-semibold">{username}</span>
                    {userTier === 'pro' && (
                      <span className="text-xs font-bold text-blue-400 border border-blue-400/30 rounded px-1.5 py-0.5 leading-none">PRO</span>
                    )}
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
                </>
              ) : (
                <div className="flex items-center gap-2">
                  <Link
                    to="/login"
                    className="px-4 py-2 rounded-lg text-sm font-bold text-slate-300 hover:bg-slate-800 hover:text-white transition-all italic"
                  >
                    SIGN IN
                  </Link>
                  <Link
                    to="/signup"
                    className="px-4 py-2 rounded-lg text-sm font-bold bg-blue-600 text-white hover:bg-blue-500 transition-all italic shadow-lg shadow-blue-600/30"
                  >
                    SIGN UP FREE
                  </Link>
                </div>
              )}
            </div>

          </div>

          {/* Mobile nav — horizontal scroll */}
          <div className="md:hidden flex gap-1 pb-2 overflow-x-auto scrollbar-hide">
            {[...mainNavItems, ...rankingsItems, ...edgesItems, ...dataLabItems, ...toolsItems, ...marketsItems].map(item => {
              const routeTier = getRouteTier(item.path);
              const accessible = canAccessRoute(userTier, routeTier);
              if (accessible) {
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all italic ${
                      isActive(item.path) ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-300'
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              }
              return (
                <button
                  key={item.path}
                  onClick={() => setUpgradeModal({ featureLabel: item.label, requiredTier: routeTier as 'member' | 'pro' })}
                  className="px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap italic bg-slate-900 text-slate-600"
                >
                  🔒 {item.label}
                </button>
              );
            })}
            {isAuthenticated ? (
              <button onClick={handleLogout} className="px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap bg-red-900/50 text-red-300">
                Logout
              </button>
            ) : (
              <Link to="/signup" className="px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap bg-blue-600 text-white italic">
                SIGN UP
              </Link>
            )}
          </div>
        </div>
      </nav>

      {/* Upgrade modal */}
      {upgradeModal && (
        <UpgradeModal
          featureLabel={upgradeModal.featureLabel}
          requiredTier={upgradeModal.requiredTier}
          onClose={() => setUpgradeModal(null)}
        />
      )}
    </>
  );
}
