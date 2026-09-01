import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiUrl } from '../config';
import { SurvivorStrategy, findHolidayDoubles, getWeekHazard } from './SurvivorStrategy';
import { SurvivorPathBuilder } from './SurvivorPathBuilder';
import { SurvivorSimulator } from './SurvivorSimulator';
import { SurvivorMultiEntry } from './SurvivorMultiEntry';
import { type CustomPath } from './survivorAlgo';

// ── Semantic color tokens (theme-agnostic) ────────────────────────────────────
const BG     = 'var(--c-bg)';
const PANEL  = 'var(--c-panel)';
const BORDER = 'var(--c-border)';
const FG     = 'var(--c-fg)';
const MUTED  = 'var(--c-muted)';

// ── Fixed accent colors (same in both themes) ────────────────────────────────
const EMERALD = 'oklch(69.6% .17 162.48)';
const RED     = 'oklch(63.2% .204 25.331)';
const YELLOW  = 'oklch(79.5% .184 86.047)';
const BLUE    = 'oklch(62.3% .214 259.815)';
const ORANGE  = 'oklch(72% .19 50)';

// ── Theme CSS variable sets ───────────────────────────────────────────────────
const LIGHT_VARS: Record<string, string> = {
  '--c-bg':     'oklch(96.5% 0 0)',
  '--c-panel':  'oklch(100% 0 0)',
  '--c-border': 'oklch(0% 0 0 / .15)',
  '--c-fg':     'oklch(13% 0 0)',
  '--c-muted':  'oklch(46% 0 0)',
  '--c-track':  'oklch(0% 0 0 / .1)',
  '--c-rowsel': 'oklch(0% 0 0 / .06)',
  '--c-btnsel': 'oklch(0% 0 0 / .07)',
  '--c-pathbg': 'oklch(97% 0 0)',
};
const DARK_VARS: Record<string, string> = {
  '--c-bg':     'oklch(22.5% 0 0)',
  '--c-panel':  'oklch(24% 0 0)',
  '--c-border': 'oklch(100% 0 0 / .15)',
  '--c-fg':     'oklch(98.5% 0 0)',
  '--c-muted':  'oklch(70.8% 0 0)',
  '--c-track':  'oklch(100% 0 0 / .1)',
  '--c-rowsel': 'oklch(100% 0 0 / .06)',
  '--c-btnsel': 'oklch(100% 0 0 / .1)',
  '--c-pathbg': 'oklch(20.5% 0 0)',
};

const LABEL_COLOR: Record<string, string> = {
  GREAT: EMERALD,
  GOOD:  'oklch(70% .15 150)',
  LEAN:  YELLOW,
  TOUGH: 'oklch(70% .15 30)',
  TRAP:  RED,
};

const TIER_COLOR: Record<string, string> = {
  ELITE:     EMERALD,
  CONTENDER: BLUE,
  AVERAGE:   MUTED,
  BELOW:     YELLOW,
  BOTTOM:    RED,
};

type View = 'grid' | 'weekly' | 'paths' | 'strategy' | 'my-paths' | 'simulator' | 'multi-entry';

interface TeamWeek {
  week: number;
  opp: string;
  home: boolean;
  wp: number;
  label: string;
  team_rating: number;
  opp_rating: number;
  date: string;
}

interface Team {
  team: string;
  team_name: string;
  rating: number;
  tier: string;
  schedule: TeamWeek[];
}

interface Game {
  home: string;
  away: string;
  home_name: string;
  away_name: string;
  date: string;
  home_rating: number;
  away_rating: number;
  home_wp: number;
  away_wp: number;
  home_tier: string;
  away_tier: string;
  home_label: string;
  away_label: string;
}

interface PathPick {
  week: number;
  team: string;
  wp: number;
  label: string;
  opp: string;
  home: boolean;
}

interface OptimalPath {
  id: string;
  name: string;
  desc: string;
  color: string;
  picks: Record<number, PathPick>;
}

interface OddsEntry {
  event_id: string;
  away: string;
  home: string;
  spread: number | null;
  details: string;
  over_under: number | null;
  away_ml: number;
  home_ml: number;
  away_implied: number;
  home_implied: number;
}

interface GameTags {
  isTNF: boolean;
  isMNF: boolean;
  isThanksgiving: boolean;
  isChristmas: boolean;
  isOpener: boolean;
}

function getGameTags(date: string): GameTags {
  if (!date) return { isTNF: false, isMNF: false, isThanksgiving: false, isChristmas: false, isOpener: false };
  const d = new Date(date + 'T12:00:00');
  const mm = d.getMonth() + 1;
  const dd = d.getDate();
  const dow = d.getDay(); // 0=Sun,1=Mon,...,4=Thu
  return {
    isTNF:          dow === 4 && !(mm === 11 && dd === 26) && !(mm === 12 && dd === 25),
    isMNF:          dow === 1,
    isThanksgiving: mm === 11 && dd === 26,
    isChristmas:    mm === 12 && dd === 25,
    isOpener:       date === '2026-09-10',
  };
}

function computePaths(weeks: Record<number, Game[]>): OptimalPath[] {
  const weekNums = Object.keys(weeks).map(Number).sort((a, b) => a - b);

  type Cand = { team: string; wp: number; label: string; opp: string; home: boolean };

  function getCandidates(wk: number, used: Set<string>): Cand[] {
    return (weeks[wk] ?? []).flatMap(g => {
      const picks: Cand[] = [];
      if (!used.has(g.home)) picks.push({ team: g.home, wp: g.home_wp, label: g.home_label, opp: g.away, home: true });
      if (!used.has(g.away)) picks.push({ team: g.away, wp: g.away_wp, label: g.away_label, opp: g.home, home: false });
      return picks;
    });
  }

  function getBestFutureWp(team: string, afterWeek: number, horizon = 5): number {
    let best = 0;
    for (let fw = afterWeek + 1; fw <= afterWeek + horizon; fw++) {
      for (const g of weeks[fw] ?? []) {
        if (g.home === team) best = Math.max(best, g.home_wp);
        if (g.away === team) best = Math.max(best, g.away_wp);
      }
    }
    return best;
  }

  function buildPath(scoreFn: (c: Cand, wk: number) => number): Record<number, PathPick> {
    const used = new Set<string>();
    const picks: Record<number, PathPick> = {};
    for (const wk of weekNums) {
      const cands = getCandidates(wk, used);
      if (!cands.length) continue;
      const best = cands.reduce((a, b) => scoreFn(b, wk) > scoreFn(a, wk) ? b : a);
      picks[wk] = { week: wk, ...best };
      used.add(best.team);
    }
    return picks;
  }

  return [
    {
      id: 'maxwp',
      name: 'MAX WIN PROB',
      desc: 'Always pick highest available probability — most aggressive',
      color: EMERALD,
      picks: buildPath(c => c.wp),
    },
    {
      id: 'futurevalue',
      name: 'FUTURE VALUE',
      desc: 'Penalizes teams with better matchups coming — preserves elite picks',
      color: BLUE,
      picks: buildPath((c, wk) => {
        const futureBest = getBestFutureWp(c.team, wk, 5);
        const penalty = Math.max(0, futureBest - c.wp) * 0.55;
        return c.wp - penalty;
      }),
    },
    {
      id: 'safeearly',
      name: 'SAFE EARLY',
      desc: 'Takes the biggest favorites in Wks 1–9 — maximizes early survival, accepts whatever is left for the second half',
      color: YELLOW,
      picks: buildPath((c, wk) => {
        if (wk <= 9 && c.label === 'GREAT') return c.wp + 0.15;
        return c.wp;
      }),
    },
    {
      id: 'riskearly',
      name: 'RISK EARLY',
      desc: 'Avoids burning top teams in Wks 1–9 — uses solid GOOD picks early, preserves elite teams for late-season pressure',
      color: ORANGE,
      picks: buildPath((c, wk) => {
        if (wk <= 9 && c.label === 'GREAT') return 0.595;
        return c.wp;
      }),
    },
  ];
}

const STORAGE_KEY      = 'survivor_2026_used';
const PICK_KEY         = 'survivor_2026_picks';
const THK_KEY          = 'survivor_2026_thk';
const XMAS_KEY         = 'survivor_2026_xmas';
const THEME_KEY        = 'survivor_theme';
const CUSTOM_PATHS_KEY = 'survivor_2026_custom_paths';

function loadUsed(): Set<string> {
  try { return new Set(JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '[]')); }
  catch { return new Set(); }
}
function loadPicks(): Record<number, string> {
  try { return JSON.parse(localStorage.getItem(PICK_KEY) ?? '{}'); }
  catch { return {}; }
}

function getLogo(abbr: string): string {
  const map: Record<string, string> = {
    ARI:'ari',ATL:'atl',BAL:'bal',BUF:'buf',CAR:'car',CHI:'chi',CIN:'cin',CLE:'cle',
    DAL:'dal',DEN:'den',DET:'det',GB:'gb',HOU:'hou',IND:'ind',JAX:'jax',KC:'kc',
    LAC:'lac',LAR:'lar',LV:'lv',MIA:'mia',MIN:'min',NE:'ne',NO:'no',NYG:'nyg',
    NYJ:'nyj',PHI:'phi',PIT:'pit',SEA:'sea',SF:'sf',TB:'tb',TEN:'ten',WSH:'wsh',
  };
  const slug = map[abbr] ?? abbr.toLowerCase();
  return `https://a.espncdn.com/i/teamlogos/nfl/500/${slug}.png`;
}

function WpBar({ wp, label }: { wp: number; label: string }) {
  const color = LABEL_COLOR[label] ?? MUTED;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ width: 48, height: 4, background: 'var(--c-track)', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ width: `${wp * 100}%`, height: '100%', background: color, borderRadius: 2 }} />
      </div>
      <span style={{ fontSize: '0.7rem', fontWeight: 700, color, minWidth: 32 }}>{Math.round(wp * 100)}%</span>
    </div>
  );
}

// ── Holiday game card used in weekly view ────────────────────────────────────
function HolidayGameCard({
  game, currentPick, onPick, used, accentColor,
}: {
  game: Game;
  currentPick: string | null;
  onPick: (team: string) => void;
  used: Set<string>;
  accentColor: string;
}) {
  const awayPicked  = currentPick === game.away;
  const homePicked  = currentPick === game.home;
  const awayBlocked = used.has(game.away) && !awayPicked;
  const homeBlocked = used.has(game.home) && !homePicked;

  return (
    <div style={{
      background: PANEL,
      border: `1px solid ${awayPicked || homePicked ? accentColor + '80' : BORDER}`,
      borderRadius: 10, padding: '12px 16px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
        {/* Away */}
        <button
          onClick={() => !awayBlocked && onPick(game.away)}
          disabled={awayBlocked}
          style={{
            flex: 1, background: awayPicked ? accentColor + '18' : 'transparent',
            border: `1px solid ${awayPicked ? accentColor : 'transparent'}`,
            borderRadius: 8, padding: '8px 12px', cursor: awayBlocked ? 'default' : 'pointer',
            textAlign: 'left',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <img src={getLogo(game.away)} alt={game.away} style={{ width: 28, height: 28, opacity: awayBlocked ? 0.35 : 1 }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: awayBlocked ? MUTED : FG, fontFamily: 'Nunito' }}>
                {game.away} {awayBlocked ? <span style={{ fontSize: '0.6rem', color: RED }}>USED</span> : ''}
                {awayPicked && <span style={{ fontSize: '0.6rem', color: accentColor, marginLeft: 4 }}>✓ PICK</span>}
              </div>
              <div style={{ fontSize: '0.65rem', color: MUTED }}>{game.away_name}</div>
              <WpBar wp={game.away_wp} label={game.away_label} />
            </div>
          </div>
        </button>

        <div style={{ padding: '0 12px', color: MUTED, fontSize: '0.8rem', flexShrink: 0 }}>@</div>

        {/* Home */}
        <button
          onClick={() => !homeBlocked && onPick(game.home)}
          disabled={homeBlocked}
          style={{
            flex: 1, background: homePicked ? accentColor + '18' : 'transparent',
            border: `1px solid ${homePicked ? accentColor : 'transparent'}`,
            borderRadius: 8, padding: '8px 12px', cursor: homeBlocked ? 'default' : 'pointer',
            textAlign: 'left',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <img src={getLogo(game.home)} alt={game.home} style={{ width: 28, height: 28, opacity: homeBlocked ? 0.35 : 1 }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: homeBlocked ? MUTED : FG, fontFamily: 'Nunito' }}>
                {game.home} {homeBlocked ? <span style={{ fontSize: '0.6rem', color: RED }}>USED</span> : ''}
                {homePicked && <span style={{ fontSize: '0.6rem', color: accentColor, marginLeft: 4 }}>✓ PICK</span>}
              </div>
              <div style={{ fontSize: '0.65rem', color: MUTED }}>{game.home_name}</div>
              <WpBar wp={game.home_wp} label={game.home_label} />
            </div>
          </div>
        </button>

        <div style={{ flexShrink: 0, padding: '0 8px', textAlign: 'center', minWidth: 64 }}>
          {(() => {
            const best = game.home_wp >= game.away_wp
              ? { label: game.home_label }
              : { label: game.away_label };
            return <span style={{ fontSize: '0.6rem', fontWeight: 700, letterSpacing: '0.05em', color: LABEL_COLOR[best.label] ?? MUTED }}>{best.label}</span>;
          })()}
        </div>
      </div>
    </div>
  );
}

export function Survivor() {
  const navigate = useNavigate();
  const [dark, setDark] = useState(() => localStorage.getItem(THEME_KEY) === 'dark');
  const [teams, setTeams] = useState<Team[]>([]);
  const [weeks, setWeeks] = useState<Record<number, Game[]>>({});
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<View>('weekly');
  const [selectedWeek, setSelectedWeek] = useState(1);
  const [used, setUsed] = useState<Set<string>>(loadUsed);
  const [picks, setPicks] = useState<Record<number, string>>(loadPicks);
  const [thkPick,  setThkPickState]  = useState<string | null>(() => localStorage.getItem(THK_KEY));
  const [xmasPick, setXmasPickState] = useState<string | null>(() => localStorage.getItem(XMAS_KEY));
  const [odds, setOdds] = useState<Record<string, OddsEntry>>({});
  const fetchedOddsWeeks = useState<Set<number>>(() => new Set())[0];
  const [customPaths, setCustomPaths] = useState<CustomPath[]>(() => {
    try { return JSON.parse(localStorage.getItem(CUSTOM_PATHS_KEY) ?? '[]'); }
    catch { return []; }
  });

  const handleCustomPathsChange = useCallback((next: CustomPath[]) => {
    setCustomPaths(next);
    localStorage.setItem(CUSTOM_PATHS_KEY, JSON.stringify(next));
  }, []);

  const toggleTheme = () => {
    setDark(prev => {
      const next = !prev;
      localStorage.setItem(THEME_KEY, next ? 'dark' : 'light');
      return next;
    });
  };

  const themeVars = dark ? DARK_VARS : LIGHT_VARS;

  useEffect(() => {
    fetch(getApiUrl('f5/survivor'))
      .then(r => r.json())
      .then(d => {
        setTeams(d.teams ?? []);
        setWeeks(d.weeks ?? {});
        const today = new Date();
        const weekNums = Object.keys(d.weeks ?? {}).map(Number).sort((a, b) => a - b);
        for (const wk of weekNums) {
          const games: Game[] = d.weeks[wk] ?? [];
          if (games.length && games[0].date >= today.toISOString().slice(0, 10)) {
            setSelectedWeek(wk);
            break;
          }
        }
        setLoading(false);
        // Pre-fetch Week 1 odds on load
        fetchOddsForWeek(1);
      })
      .catch(() => setLoading(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function fetchOddsForWeek(wk: number) {
    if (fetchedOddsWeeks.has(wk)) return;
    fetchedOddsWeeks.add(wk);
    fetch(getApiUrl(`f5/survivor/odds?week=${wk}`))
      .then(r => r.json())
      .then(d => {
        const entries: Record<string, OddsEntry> = {};
        for (const g of d.games ?? []) {
          entries[`${g.away}:${g.home}`] = g;
        }
        setOdds(prev => ({ ...prev, ...entries }));
      })
      .catch(() => { fetchedOddsWeeks.delete(wk); });
  }

  useEffect(() => {
    if (!loading) fetchOddsForWeek(selectedWeek);
  }, [selectedWeek, loading]); // eslint-disable-line react-hooks/exhaustive-deps

  // Look up odds for a team in a given week using its schedule entry
  function getOddsEntry(team: string, opp: string, isHome: boolean): OddsEntry | null {
    const key = isHome ? `${opp}:${team}` : `${team}:${opp}`;
    return odds[key] ?? null;
  }

  const paths = useMemo(() => computePaths(weeks), [weeks]);
  const [selectedPathId, setSelectedPathId] = useState<string | null>(null);
  const [oddsMode, setOddsMode] = useState<boolean>(true);
  const activePath = paths.find(p => p.id === selectedPathId) ?? null;

  const toggleUsed = useCallback((team: string) => {
    setUsed(prev => {
      const next = new Set(prev);
      if (next.has(team)) next.delete(team);
      else next.add(team);
      localStorage.setItem(STORAGE_KEY, JSON.stringify([...next]));
      return next;
    });
  }, []);

  const setPick = useCallback((week: number, team: string) => {
    setPicks(prev => {
      const next = { ...prev };
      if (next[week] === team) {
        delete next[week];
      } else {
        next[week] = team;
        setUsed(u => {
          const nu = new Set(u);
          nu.add(team);
          localStorage.setItem(STORAGE_KEY, JSON.stringify([...nu]));
          return nu;
        });
      }
      localStorage.setItem(PICK_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const setHolidayPick = useCallback((type: 'thk' | 'xmas', team: string) => {
    const storeKey = type === 'thk' ? THK_KEY : XMAS_KEY;
    const setter   = type === 'thk' ? setThkPickState : setXmasPickState;
    setter(prev => {
      const next = prev === team ? null : team;
      if (next) {
        localStorage.setItem(storeKey, next);
        setUsed(u => {
          const nu = new Set(u);
          nu.add(next);
          localStorage.setItem(STORAGE_KEY, JSON.stringify([...nu]));
          return nu;
        });
      } else {
        localStorage.removeItem(storeKey);
      }
      return next;
    });
  }, []);

  const clearAll = () => {
    setUsed(new Set());
    setPicks({});
    setThkPickState(null);
    setXmasPickState(null);
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(PICK_KEY);
    localStorage.removeItem(THK_KEY);
    localStorage.removeItem(XMAS_KEY);
  };

  const weekNums = Object.keys(weeks).map(Number).sort((a, b) => a - b);
  const currentWeekGames: Game[] = weeks[selectedWeek] ?? [];
  const availableTeams = teams.filter(t => !used.has(t.team));
  const usedTeams = teams.filter(t => used.has(t.team));

  // Holiday game slices (derived from week data)
  const thkGames  = useMemo(() => (weeks[12] ?? []).filter(g => getGameTags(g.date).isThanksgiving), [weeks]);
  const xmasGames = useMemo(() => (weeks[16] ?? []).filter(g => getGameTags(g.date).isChristmas),    [weeks]);
  const thkTeams  = useMemo(() => new Set(thkGames.flatMap(g => [g.home, g.away])),  [thkGames]);
  const xmasTeams = useMemo(() => new Set(xmasGames.flatMap(g => [g.home, g.away])), [xmasGames]);

  // Grid columns: insert THK before W12, XMAS before W16
  type Column = number | 'thk' | 'xmas';
  const gridColumns = useMemo<Column[]>(() => {
    const cols: Column[] = [];
    for (const wk of weekNums) {
      if (wk === 12 && thkGames.length > 0)  cols.push('thk');
      if (wk === 16 && xmasGames.length > 0) cols.push('xmas');
      cols.push(wk);
    }
    return cols;
  }, [weekNums, thkGames.length, xmasGames.length]);

  // Helper: get a team's entry for a holiday game
  function getHolidayEntry(team: string, holidayGames: Game[]) {
    const game = holidayGames.find(g => g.home === team || g.away === team);
    if (!game) return null;
    const isHome = game.home === team;
    return {
      wp: isHome ? game.home_wp : game.away_wp,
      label: isHome ? game.home_label : game.away_label,
      opp: isHome ? game.away : game.home,
      isHome,
    };
  }

  const holidayPickCount = (thkPick ? 1 : 0) + (xmasPick ? 1 : 0);
  const totalPicks = Object.keys(picks).length + holidayPickCount;

  const navBtn = (active: boolean) => ({
    background: active ? PANEL : 'transparent',
    border: `1px solid ${active ? BORDER : 'transparent'}`,
    borderRadius: 8, padding: '7px 14px', color: active ? FG : MUTED,
    cursor: 'pointer', fontSize: '0.75rem', fontWeight: active ? 700 : 400,
  } as React.CSSProperties);

  return (
    <div style={{ ...themeVars, background: BG, minHeight: '100vh', padding: '32px 24px', color: FG } as React.CSSProperties}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>

        {/* Header */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: '0.65rem', color: MUTED, letterSpacing: '0.12em', marginBottom: 6 }}>
            CIRCA SURVIVOR · 2026 NFL SEASON
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
            <div>
              <h1 style={{ fontSize: '1.9rem', fontWeight: 800, fontFamily: 'Nunito', margin: 0 }}>Survivor Helper</h1>
              <p style={{ color: MUTED, margin: '6px 0 0', fontSize: '0.8rem' }}>
                Win probabilities from Walters power ratings. Mark teams used, set your weekly picks. Saved in your browser.
              </p>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span style={{ fontSize: '0.72rem', color: MUTED }}>
                {availableTeams.length} teams remaining · {totalPicks} picks
                {holidayPickCount > 0 && <span style={{ color: YELLOW }}> ({holidayPickCount} holiday)</span>}
              </span>
              <button
                onClick={toggleTheme}
                title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
                style={{
                  background: 'transparent', border: `1px solid ${BORDER}`,
                  borderRadius: 6, padding: '5px 10px', color: MUTED,
                  cursor: 'pointer', fontSize: '0.85rem', lineHeight: 1,
                }}
              >
                {dark ? '☀️' : '🌙'}
              </button>
              <a
                href="/circa-survivor-playbook.pdf"
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 5,
                  background: 'transparent', border: `1px solid ${BORDER}`,
                  borderRadius: 6, padding: '5px 10px', color: MUTED,
                  cursor: 'pointer', fontSize: '0.7rem', textDecoration: 'none',
                }}
              >
                Strategy Guide PDF
              </a>
              <button onClick={clearAll} style={{ background: 'transparent', border: `1px solid ${BORDER}`, borderRadius: 6, padding: '5px 10px', color: MUTED, cursor: 'pointer', fontSize: '0.7rem' }}>
                Reset
              </button>
            </div>
          </div>
        </div>

        {/* View toggle */}
        <div style={{ display: 'flex', gap: 6, marginBottom: 20, flexWrap: 'wrap' }}>
          <button style={navBtn(view === 'weekly')} onClick={() => setView('weekly')}>WEEKLY PICKS</button>
          <button style={navBtn(view === 'grid')} onClick={() => setView('grid')}>TEAM GRID</button>
          <button style={navBtn(view === 'paths')} onClick={() => setView('paths')}>OPTIMAL PATHS</button>
          <button style={navBtn(view === 'strategy')} onClick={() => setView('strategy')}>STRATEGY</button>
          <div style={{ width: 1, background: BORDER, margin: '0 4px', alignSelf: 'stretch' }} />
          <button style={navBtn(view === 'my-paths')} onClick={() => setView('my-paths')}>MY PATHS</button>
          <button style={navBtn(view === 'simulator')} onClick={() => setView('simulator')}>SIMULATOR</button>
          <button style={navBtn(view === 'multi-entry')} onClick={() => setView('multi-entry')}>MULTI-ENTRY</button>
        </div>

        {loading && <div style={{ textAlign: 'center', padding: 60, color: MUTED }}>Loading schedule...</div>}

        {/* WEEKLY VIEW */}
        {!loading && view === 'weekly' && (
          <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 20 }}>

            {/* Week selector sidebar */}
            <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 12, padding: 12, alignSelf: 'start' }}>
              <div style={{ fontSize: '0.6rem', color: MUTED, letterSpacing: '0.08em', marginBottom: 10 }}>SELECT WEEK</div>
              {weekNums.map(wk => {
                const pick = picks[wk];
                const games: Game[] = weeks[wk] ?? [];
                const firstDate = games[0]?.date ?? '';
                const isThkWeek  = wk === 12 && thkGames.length > 0;
                const isXmasWeek = wk === 16 && xmasGames.length > 0;
                return (
                  <button
                    key={wk}
                    onClick={() => setSelectedWeek(wk)}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      width: '100%', background: selectedWeek === wk ? 'var(--c-rowsel)' : 'transparent',
                      border: 'none', borderRadius: 6, padding: '6px 8px', cursor: 'pointer',
                      color: FG, fontSize: '0.75rem', marginBottom: 2,
                    }}
                  >
                    <span style={{ fontWeight: selectedWeek === wk ? 700 : 400 }}>
                      Wk {wk}
                      {isThkWeek  && <span style={{ color: YELLOW, marginLeft: 3 }}>🦃</span>}
                      {isXmasWeek && <span style={{ color: RED, marginLeft: 3 }}>🎄</span>}
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      {/* Holiday pick badge */}
                      {isThkWeek  && thkPick  && <img src={getLogo(thkPick)}  alt={thkPick}  style={{ width: 13, height: 13 }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />}
                      {isXmasWeek && xmasPick && <img src={getLogo(xmasPick)} alt={xmasPick} style={{ width: 13, height: 13 }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />}
                      {pick && (
                        <img src={getLogo(pick)} alt={pick} style={{ width: 16, height: 16 }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />
                      )}
                      {(() => {
                        const hz = getWeekHazard(wk, games);
                        if (hz === 'trap') return <span style={{ fontSize: '0.55rem', color: RED }}>⚠</span>;
                        if (hz === 'thin') return <span style={{ fontSize: '0.55rem', color: YELLOW }}>⚡</span>;
                        if (hz === 'holiday') return <span style={{ fontSize: '0.55rem' }}>🏈</span>;
                        return null;
                      })()}
                      <span style={{ fontSize: '0.6rem', color: MUTED }}>{firstDate.slice(5, 10)}</span>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Week games */}
            <div>
              <div style={{ marginBottom: 14 }}>
                <div style={{ fontWeight: 700, fontFamily: 'Nunito', fontSize: '1rem' }}>
                  Week {selectedWeek}
                  {currentWeekGames[0]?.date && (
                    <span style={{ color: MUTED, fontWeight: 400, fontSize: '0.8rem', marginLeft: 10 }}>
                      {new Date(currentWeekGames[0].date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </span>
                  )}
                </div>
                {picks[selectedWeek] && (
                  <div style={{ fontSize: '0.72rem', color: EMERALD, marginTop: 4 }}>
                    Regular pick: <strong>{picks[selectedWeek]}</strong>
                  </div>
                )}
                {selectedWeek === 12 && thkPick && (
                  <div style={{ fontSize: '0.72rem', color: YELLOW, marginTop: 2 }}>
                    🦃 Thanksgiving pick: <strong>{thkPick}</strong>
                  </div>
                )}
                {selectedWeek === 16 && xmasPick && (
                  <div style={{ fontSize: '0.72rem', color: RED, marginTop: 2 }}>
                    🎄 Christmas pick: <strong>{xmasPick}</strong>
                  </div>
                )}
              </div>

              {/* Thanksgiving mandatory pick section */}
              {selectedWeek === 12 && thkGames.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10,
                    padding: '8px 14px', background: YELLOW + '10',
                    border: `1px solid ${YELLOW}40`, borderRadius: 8,
                  }}>
                    <span style={{ fontSize: '1rem' }}>🦃</span>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '0.8rem', color: YELLOW }}>Thanksgiving Day — Mandatory Pick</div>
                      <div style={{ fontSize: '0.68rem', color: MUTED }}>Pick one team from the 3 Thursday games. This is a separate pick from your regular Week 12 selection.</div>
                    </div>
                    {thkPick && (
                      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6, background: YELLOW + '20', border: `1px solid ${YELLOW}`, borderRadius: 6, padding: '4px 10px' }}>
                        <img src={getLogo(thkPick)} alt={thkPick} style={{ width: 18, height: 18 }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />
                        <span style={{ fontSize: '0.72rem', fontWeight: 700, color: YELLOW }}>{thkPick}</span>
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'grid', gap: 8 }}>
                    {thkGames.map((g, i) => (
                      <HolidayGameCard
                        key={i} game={g}
                        currentPick={thkPick} onPick={team => setHolidayPick('thk', team)}
                        used={used} accentColor={YELLOW}
                      />
                    ))}
                  </div>
                  <div style={{ height: 1, background: BORDER, margin: '20px 0' }} />
                  <div style={{ fontSize: '0.65rem', color: MUTED, marginBottom: 10, letterSpacing: '0.06em', fontWeight: 700 }}>
                    REGULAR WEEK 12 PICK (all games)
                  </div>
                </div>
              )}

              {/* Christmas mandatory pick section */}
              {selectedWeek === 16 && xmasGames.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10,
                    padding: '8px 14px', background: RED + '10',
                    border: `1px solid ${RED}40`, borderRadius: 8,
                  }}>
                    <span style={{ fontSize: '1rem' }}>🎄</span>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '0.8rem', color: RED }}>Christmas Day — Mandatory Pick</div>
                      <div style={{ fontSize: '0.68rem', color: MUTED }}>Pick one team from the 3 Christmas games. This is a separate pick from your regular Week 16 selection.</div>
                    </div>
                    {xmasPick && (
                      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6, background: RED + '20', border: `1px solid ${RED}`, borderRadius: 6, padding: '4px 10px' }}>
                        <img src={getLogo(xmasPick)} alt={xmasPick} style={{ width: 18, height: 18 }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />
                        <span style={{ fontSize: '0.72rem', fontWeight: 700, color: RED }}>{xmasPick}</span>
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'grid', gap: 8 }}>
                    {xmasGames.map((g, i) => (
                      <HolidayGameCard
                        key={i} game={g}
                        currentPick={xmasPick} onPick={team => setHolidayPick('xmas', team)}
                        used={used} accentColor={RED}
                      />
                    ))}
                  </div>
                  <div style={{ height: 1, background: BORDER, margin: '20px 0' }} />
                  <div style={{ fontSize: '0.65rem', color: MUTED, marginBottom: 10, letterSpacing: '0.06em', fontWeight: 700 }}>
                    REGULAR WEEK 16 PICK (all games)
                  </div>
                </div>
              )}

              {/* Regular week games */}
              <div style={{ display: 'grid', gap: 8 }}>
                {currentWeekGames.map((g, i) => {
                  const awayUsed = used.has(g.away) && picks[selectedWeek] !== g.away;
                  const homeUsed = used.has(g.home) && picks[selectedWeek] !== g.home;
                  const awayPicked = picks[selectedWeek] === g.away;
                  const homePicked = picks[selectedWeek] === g.home;
                  const tags = getGameTags(g.date);

                  return (
                    <div
                      key={i}
                      style={{
                        background: PANEL,
                        border: `1px solid ${awayPicked || homePicked ? EMERALD + '80' : BORDER}`,
                        borderRadius: 10, padding: '12px 16px',
                        opacity: (awayUsed && homeUsed) ? 0.4 : 1,
                      }}
                    >
                      {/* Market odds line */}
                      {(() => {
                        const o = odds[`${g.away}:${g.home}`];
                        if (!o) return null;
                        return (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, fontSize: '0.62rem', color: MUTED }}>
                            <span style={{ fontWeight: 700, color: BLUE }}>{o.details}</span>
                            <span>O/U {o.over_under ?? '—'}</span>
                            <span>|</span>
                            <span>Away ML <span style={{ fontWeight: 700, color: o.away_ml > 0 ? EMERALD : FG }}>{o.away_ml > 0 ? '+' : ''}{o.away_ml}</span></span>
                            <span>Home ML <span style={{ fontWeight: 700, color: o.home_ml > 0 ? EMERALD : FG }}>{o.home_ml > 0 ? '+' : ''}{o.home_ml}</span></span>
                            {o.event_id && (
                              <button
                                onClick={() => navigate(`/matchup/${o.event_id}`)}
                                style={{ marginLeft: 'auto', background: BLUE + '18', border: `1px solid ${BLUE}55`, color: BLUE, borderRadius: 4, padding: '2px 8px', cursor: 'pointer', fontSize: '0.6rem', fontWeight: 700, letterSpacing: '0.05em' }}
                              >
                                VIEW MATCHUP →
                              </button>
                            )}
                          </div>
                        );
                      })()}
                      {/* Special game tags */}
                      {(tags.isThanksgiving || tags.isChristmas || tags.isTNF || tags.isMNF || tags.isOpener) && (
                        <div style={{ display: 'flex', gap: 6, marginBottom: 8 }}>
                          {tags.isOpener      && <span style={{ fontSize: '0.6rem', fontWeight: 700, background: EMERALD + '20', color: EMERALD, borderRadius: 4, padding: '2px 7px', letterSpacing: '0.06em' }}>NFL OPENER</span>}
                          {tags.isTNF         && <span style={{ fontSize: '0.6rem', fontWeight: 700, background: ORANGE + '20', color: ORANGE, borderRadius: 4, padding: '2px 7px', letterSpacing: '0.06em' }}>TNF 🏈</span>}
                          {tags.isMNF         && <span style={{ fontSize: '0.6rem', fontWeight: 700, background: BLUE + '20', color: BLUE, borderRadius: 4, padding: '2px 7px', letterSpacing: '0.06em' }}>MNF</span>}
                          {tags.isThanksgiving && <span style={{ fontSize: '0.6rem', fontWeight: 700, background: YELLOW + '20', color: YELLOW, borderRadius: 4, padding: '2px 7px', letterSpacing: '0.06em' }}>THANKSGIVING 🦃</span>}
                          {tags.isChristmas   && <span style={{ fontSize: '0.6rem', fontWeight: 700, background: RED + '20', color: RED, borderRadius: 4, padding: '2px 7px', letterSpacing: '0.06em' }}>CHRISTMAS 🎄</span>}
                        </div>
                      )}
                      {/* Game row */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>

                        {/* Away team */}
                        <button
                          onClick={() => !awayUsed && setPick(selectedWeek, g.away)}
                          disabled={awayUsed}
                          style={{
                            flex: 1, background: awayPicked ? 'oklch(69.6% .17 162.48 / .15)' : 'transparent',
                            border: `1px solid ${awayPicked ? EMERALD : 'transparent'}`,
                            borderRadius: 8, padding: '8px 12px', cursor: awayUsed ? 'default' : 'pointer',
                            textAlign: 'left',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <img src={getLogo(g.away)} alt={g.away} style={{ width: 28, height: 28, opacity: awayUsed ? 0.35 : 1 }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />
                            <div>
                              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: awayUsed ? MUTED : FG, fontFamily: 'Nunito' }}>
                                {g.away} {awayUsed && !awayPicked ? <span style={{ fontSize: '0.6rem', color: RED }}>USED</span> : ''}
                                {awayPicked && <span style={{ fontSize: '0.6rem', color: EMERALD, marginLeft: 4 }}>✓ PICK</span>}
                              </div>
                              <div style={{ fontSize: '0.65rem', color: MUTED }}>{g.away_name}</div>
                              <WpBar wp={g.away_wp} label={g.away_label} />
                            </div>
                          </div>
                        </button>

                        {/* @ divider */}
                        <div style={{ padding: '0 12px', color: MUTED, fontSize: '0.8rem', flexShrink: 0 }}>@</div>

                        {/* Home team */}
                        <button
                          onClick={() => !homeUsed && setPick(selectedWeek, g.home)}
                          disabled={homeUsed}
                          style={{
                            flex: 1, background: homePicked ? 'oklch(69.6% .17 162.48 / .15)' : 'transparent',
                            border: `1px solid ${homePicked ? EMERALD : 'transparent'}`,
                            borderRadius: 8, padding: '8px 12px', cursor: homeUsed ? 'default' : 'pointer',
                            textAlign: 'left',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <img src={getLogo(g.home)} alt={g.home} style={{ width: 28, height: 28, opacity: homeUsed ? 0.35 : 1 }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />
                            <div>
                              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: homeUsed ? MUTED : FG, fontFamily: 'Nunito' }}>
                                {g.home} {homeUsed && !homePicked ? <span style={{ fontSize: '0.6rem', color: RED }}>USED</span> : ''}
                                {homePicked && <span style={{ fontSize: '0.6rem', color: EMERALD, marginLeft: 4 }}>✓ PICK</span>}
                              </div>
                              <div style={{ fontSize: '0.65rem', color: MUTED }}>{g.home_name}</div>
                              <WpBar wp={g.home_wp} label={g.home_label} />
                            </div>
                          </div>
                        </button>

                        {/* Best pick badge */}
                        <div style={{ flexShrink: 0, padding: '0 8px', textAlign: 'center', minWidth: 64 }}>
                          {(() => {
                            const best = g.home_wp >= g.away_wp
                              ? { team: g.home, wp: g.home_wp, label: g.home_label }
                              : { team: g.away, wp: g.away_wp, label: g.away_label };
                            const bestUsed = used.has(best.team) && picks[selectedWeek] !== best.team;
                            return (
                              <span style={{ fontSize: '0.6rem', fontWeight: 700, letterSpacing: '0.05em', color: LABEL_COLOR[best.label] ?? MUTED, opacity: bestUsed ? 0.4 : 1 }}>
                                {best.label}
                              </span>
                            );
                          })()}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* TEAM GRID VIEW */}
        {!loading && view === 'grid' && (
          <div>
            <div style={{ fontSize: '0.65rem', color: MUTED, marginBottom: 10 }}>
              Click a team to toggle used/available. Each cell shows win probability for that week.{' '}
              <span style={{ color: YELLOW }}>🦃 THK</span> and <span style={{ color: RED }}>🎄 XMAS</span> are mandatory holiday picks — separate from the regular weekly pick.
            </div>

            {/* Path overlay selector */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.6rem', color: MUTED, fontWeight: 700, letterSpacing: '0.08em' }}>PATH OVERLAY:</span>
              <button
                onClick={() => setSelectedPathId(null)}
                style={{
                  fontSize: '0.65rem', fontWeight: 700, padding: '4px 10px', borderRadius: 6, cursor: 'pointer',
                  background: !selectedPathId ? 'var(--c-btnsel)' : 'transparent',
                  border: `1px solid ${!selectedPathId ? BORDER : 'transparent'}`,
                  color: !selectedPathId ? FG : MUTED,
                }}
              >OFF</button>
              {paths.map(p => (
                <button
                  key={p.id}
                  onClick={() => setSelectedPathId(selectedPathId === p.id ? null : p.id)}
                  style={{
                    fontSize: '0.65rem', fontWeight: 700, padding: '4px 10px', borderRadius: 6, cursor: 'pointer',
                    background: selectedPathId === p.id ? p.color + '22' : 'transparent',
                    border: `1px solid ${selectedPathId === p.id ? p.color : 'transparent'}`,
                    color: selectedPathId === p.id ? p.color : MUTED,
                  }}
                >{p.name}</button>
              ))}
            </div>

            {/* Odds toggle */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <button
                onClick={() => setOddsMode(o => !o)}
                title="Toggle odds glow overlay"
                style={{
                  fontSize: '0.65rem', fontWeight: 700, padding: '4px 10px', borderRadius: 6, cursor: 'pointer',
                  background: oddsMode ? BLUE + '22' : 'transparent',
                  border: `1px solid ${oddsMode ? BLUE : MUTED + '66'}`,
                  color: oddsMode ? BLUE : MUTED,
                }}
              >ODDS</button>
              {oddsMode && Object.keys(odds).length === 0 && (
                <span style={{ fontSize: '0.6rem', color: YELLOW }}>⚡ Loading odds...</span>
              )}
              {oddsMode && <span style={{ fontSize: '0.58rem', color: MUTED }}>Green glow = model edge · Red glow = market edge</span>}
            </div>

            {/* Available teams */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ fontSize: '0.65rem', color: EMERALD, letterSpacing: '0.1em', fontWeight: 700, marginBottom: 10 }}>
                AVAILABLE ({availableTeams.length})
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ borderCollapse: 'collapse', fontSize: '0.72rem', minWidth: 1000, border: `1px solid ${BORDER}`, borderRadius: 8 }}>
                  <thead>
                    <tr style={{ borderBottom: `1px solid ${BORDER}` }}>
                      <th style={{ padding: '6px 10px', textAlign: 'left', color: MUTED, fontWeight: 600, fontSize: '0.6rem', position: 'sticky', left: 0, background: BG, minWidth: 140, borderRight: `1px solid ${BORDER}` }}>TEAM</th>
                      {gridColumns.map(col => {
                        if (col === 'thk') return (
                          <th key="thk" style={{ padding: '6px 4px', fontWeight: 800, fontSize: '0.55rem', minWidth: 44, textAlign: 'center', borderRight: `1px solid ${BORDER}`, background: YELLOW + '12', color: YELLOW, letterSpacing: '0.04em' }}>
                            🦃<br/>THK
                          </th>
                        );
                        if (col === 'xmas') return (
                          <th key="xmas" style={{ padding: '6px 4px', fontWeight: 800, fontSize: '0.55rem', minWidth: 44, textAlign: 'center', borderRight: `1px solid ${BORDER}`, background: RED + '10', color: RED, letterSpacing: '0.04em' }}>
                            🎄<br/>XMAS
                          </th>
                        );
                        const wk = col as number;
                        const tags = (weeks[wk] ?? []).map(g => getGameTags(g.date));
                        const hasTNF = tags.some(t => t.isTNF);
                        return (
                          <th
                            key={wk}
                            style={{ padding: '6px 6px', color: selectedWeek === wk ? FG : MUTED, fontWeight: selectedWeek === wk ? 700 : 600, fontSize: '0.55rem', minWidth: 42, cursor: 'pointer', textAlign: 'center', borderRight: `1px solid ${BORDER}` }}
                            onClick={() => { setSelectedWeek(wk); setView('weekly'); }}
                          >
                            W{wk}{hasTNF ? '🏈' : ''}
                          </th>
                        );
                      })}
                    </tr>
                    {/* Path line row */}
                    {activePath && (
                      <tr style={{ background: activePath.color + '0D', borderBottom: `1px solid ${BORDER}` }}>
                        <td style={{ padding: '4px 10px', position: 'sticky', left: 0, background: activePath.color + '15', fontSize: '0.55rem', fontWeight: 800, color: activePath.color, letterSpacing: '0.06em', whiteSpace: 'nowrap', borderRight: `1px solid ${BORDER}` }}>
                          ── {activePath.name}
                        </td>
                        {gridColumns.map(col => {
                          if (col === 'thk') return (
                            <td key="thk" style={{ padding: '3px 2px', textAlign: 'center', borderRight: `1px solid ${BORDER}`, background: YELLOW + '08' }}>
                              <span style={{ fontSize: '0.5rem', color: MUTED }}>sep.</span>
                            </td>
                          );
                          if (col === 'xmas') return (
                            <td key="xmas" style={{ padding: '3px 2px', textAlign: 'center', borderRight: `1px solid ${BORDER}`, background: RED + '06' }}>
                              <span style={{ fontSize: '0.5rem', color: MUTED }}>sep.</span>
                            </td>
                          );
                          const wk = col as number;
                          const pick = activePath.picks[wk];
                          const pathColor = activePath.color;
                          return (
                            <td key={wk} style={{ padding: '3px 2px', textAlign: 'center', position: 'relative', borderRight: `1px solid ${BORDER}` }}>
                              <div style={{ position: 'absolute', top: '50%', left: 0, right: 0, height: 2, background: pathColor + '50', zIndex: 0 }} />
                              {pick ? (
                                <button
                                  onClick={() => setPick(wk, pick.team)}
                                  style={{ position: 'relative', zIndex: 1, background: pathColor + '25', border: `1px solid ${pathColor}`, borderRadius: 4, padding: '2px 4px', cursor: 'pointer', minWidth: 36 }}
                                >
                                  <img src={getLogo(pick.team)} alt={pick.team} style={{ width: 16, height: 16, display: 'block', margin: '0 auto 1px' }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />
                                  <div style={{ fontSize: '0.5rem', fontWeight: 800, color: pathColor, lineHeight: 1 }}>{Math.round(pick.wp * 100)}%</div>
                                </button>
                              ) : (
                                <span style={{ position: 'relative', zIndex: 1, fontSize: '0.5rem', color: MUTED }}>—</span>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    )}
                  </thead>
                  <tbody>
                    {availableTeams.map(t => (
                      <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
                        <td style={{ padding: '7px 10px', position: 'sticky', left: 0, background: PANEL, borderRight: `1px solid ${BORDER}` }}>
                          <button onClick={() => toggleUsed(t.team)} style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, padding: 0 }}>
                            <img src={getLogo(t.team)} alt={t.team} style={{ width: 20, height: 20 }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />
                            <div style={{ textAlign: 'left' }}>
                              <div style={{ fontWeight: 700, color: FG, fontFamily: 'Nunito' }}>{t.team}</div>
                              <div style={{ fontSize: '0.6rem', color: TIER_COLOR[t.tier] ?? MUTED }}>{t.tier}</div>
                            </div>
                          </button>
                        </td>
                        {gridColumns.map(col => {
                          // ── Thanksgiving column ──────────────────────────────
                          if (col === 'thk') {
                            const entry = getHolidayEntry(t.team, thkGames);
                            if (!entry) return (
                              <td key="thk" style={{ padding: '7px 4px', textAlign: 'center', borderRight: `1px solid ${BORDER}`, background: YELLOW + '06', color: MUTED, fontSize: '0.55rem' }}>—</td>
                            );
                            const isPick = thkPick === t.team;
                            const isBlocked = used.has(t.team) && !isPick;
                            const color = LABEL_COLOR[entry.label] ?? MUTED;
                            return (
                              <td key="thk" style={{ padding: '4px 3px', textAlign: 'center', borderRight: `1px solid ${BORDER}`, background: YELLOW + '08', outline: isPick ? `2px solid ${YELLOW}` : 'none', outlineOffset: -2 }}>
                                <button
                                  onClick={() => !isBlocked && setHolidayPick('thk', t.team)}
                                  style={{ background: isPick ? YELLOW + '22' : 'transparent', border: `1px solid ${isPick ? YELLOW : 'transparent'}`, borderRadius: 4, padding: '3px 4px', cursor: isBlocked ? 'default' : 'pointer', width: '100%', opacity: isBlocked ? 0.3 : 1 }}
                                >
                                  <div style={{ fontSize: '0.65rem', fontWeight: 700, color }}>{Math.round(entry.wp * 100)}%</div>
                                  <div style={{ fontSize: '0.55rem', color: MUTED }}>{entry.isHome ? '' : '@'}{entry.opp}</div>
                                </button>
                              </td>
                            );
                          }
                          // ── Christmas column ─────────────────────────────────
                          if (col === 'xmas') {
                            const entry = getHolidayEntry(t.team, xmasGames);
                            if (!entry) return (
                              <td key="xmas" style={{ padding: '7px 4px', textAlign: 'center', borderRight: `1px solid ${BORDER}`, background: RED + '04', color: MUTED, fontSize: '0.55rem' }}>—</td>
                            );
                            const isPick = xmasPick === t.team;
                            const isBlocked = used.has(t.team) && !isPick;
                            const color = LABEL_COLOR[entry.label] ?? MUTED;
                            return (
                              <td key="xmas" style={{ padding: '4px 3px', textAlign: 'center', borderRight: `1px solid ${BORDER}`, background: RED + '06', outline: isPick ? `2px solid ${RED}` : 'none', outlineOffset: -2 }}>
                                <button
                                  onClick={() => !isBlocked && setHolidayPick('xmas', t.team)}
                                  style={{ background: isPick ? RED + '22' : 'transparent', border: `1px solid ${isPick ? RED : 'transparent'}`, borderRadius: 4, padding: '3px 4px', cursor: isBlocked ? 'default' : 'pointer', width: '100%', opacity: isBlocked ? 0.3 : 1 }}
                                >
                                  <div style={{ fontSize: '0.65rem', fontWeight: 700, color }}>{Math.round(entry.wp * 100)}%</div>
                                  <div style={{ fontSize: '0.55rem', color: MUTED }}>{entry.isHome ? '' : '@'}{entry.opp}</div>
                                </button>
                              </td>
                            );
                          }
                          // ── Regular week column ──────────────────────────────
                          const wk = col as number;
                          const entry = t.schedule.find(s => s.week === wk);
                          const isPick = picks[wk] === t.team;
                          const isPathPick = activePath?.picks[wk]?.team === t.team;
                          if (!entry) {
                            return <td key={wk} style={{ padding: '7px 6px', textAlign: 'center', color: MUTED, fontSize: '0.6rem', borderRight: `1px solid ${BORDER}` }}>BYE</td>;
                          }
                          const color = LABEL_COLOR[entry.label] ?? MUTED;
                          const oddsEntry = getOddsEntry(t.team, entry.opp, entry.home);
                          const mktWp    = oddsEntry ? (entry.home ? oddsEntry.home_implied : oddsEntry.away_implied) : null;
                          const edge     = mktWp !== null ? Math.round((entry.wp - mktWp) * 100) : null;
                          const edgeColor = edge === null ? MUTED : edge >= 3 ? EMERALD : edge <= -3 ? RED : MUTED;

                          // Mode A: market label color
                          const mktLabel = mktWp !== null
                            ? mktWp >= 0.72 ? 'GREAT' : mktWp >= 0.60 ? 'GOOD' : mktWp >= 0.50 ? 'LEAN' : mktWp >= 0.40 ? 'TOUGH' : 'TRAP'
                            : null;
                          const mktColor = mktLabel ? (LABEL_COLOR[mktLabel] ?? MUTED) : MUTED;

                          // Odds glow background
                          const glowBg = (oddsMode && edge !== null && edge !== 0)
                            ? edge > 0
                              ? `oklch(69.6% .17 162.48 / ${Math.min(Math.abs(edge) / 22, 0.45).toFixed(2)})`
                              : `oklch(63.2% .204 25.331 / ${Math.min(Math.abs(edge) / 22, 0.45).toFixed(2)})`
                            : undefined;

                          return (
                            <td key={wk} style={{ padding: '4px 3px', textAlign: 'center', borderRight: `1px solid ${BORDER}`, outline: isPathPick ? `2px solid ${activePath!.color}` : 'none', outlineOffset: -2, background: glowBg }}>
                              <button
                                onClick={() => setPick(wk, t.team)}
                                style={{
                                  background: isPick ? color + '25' : 'transparent',
                                  border: `1px solid ${isPick ? color : 'transparent'}`,
                                  borderRadius: 4, padding: '3px 4px', cursor: 'pointer', width: '100%',
                                }}
                              >
                                <>
                                  <div style={{ fontSize: '0.65rem', fontWeight: 700, color }}>{Math.round(entry.wp * 100)}%</div>
                                  <div style={{ fontSize: '0.55rem', color: MUTED }}>{entry.home ? '' : '@'}{entry.opp}</div>
                                  {oddsMode && edge !== null && (
                                    <div style={{ fontSize: '0.5rem', fontWeight: 700, color: edgeColor }}>{edge >= 0 ? '+' : ''}{edge}</div>
                                  )}
                                </>
                              </button>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Used teams */}
            {usedTeams.length > 0 && (
              <div>
                <div style={{ fontSize: '0.65rem', color: RED, letterSpacing: '0.1em', fontWeight: 700, marginBottom: 10 }}>
                  USED ({usedTeams.length})
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {usedTeams.map(t => (
                    <button
                      key={t.team}
                      onClick={() => toggleUsed(t.team)}
                      style={{ display: 'flex', alignItems: 'center', gap: 6, background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 8, padding: '6px 10px', cursor: 'pointer', opacity: 0.5 }}
                    >
                      <img src={getLogo(t.team)} alt={t.team} style={{ width: 18, height: 18, filter: 'grayscale(100%)' }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />
                      <span style={{ fontSize: '0.72rem', color: MUTED }}>{t.team}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* PATHS VIEW */}
        {!loading && view === 'paths' && (
          <PathsView paths={paths} weeks={weeks} picks={picks} setPick={setPick} used={used}
            thkPick={thkPick} xmasPick={xmasPick} thkGames={thkGames} xmasGames={xmasGames}
            setHolidayPick={setHolidayPick}
          />
        )}

        {/* STRATEGY VIEW */}
        {!loading && view === 'strategy' && (
          <SurvivorStrategy teams={teams} weeks={weeks} used={used} />
        )}

        {/* MY PATHS VIEW */}
        {!loading && view === 'my-paths' && (
          <SurvivorPathBuilder
            weeks={weeks}
            customPaths={customPaths}
            onPathsChange={handleCustomPathsChange}
            thkGames={thkGames}
            xmasGames={xmasGames}
          />
        )}

        {/* SIMULATOR VIEW */}
        {!loading && view === 'simulator' && (
          <SurvivorSimulator
            weeks={weeks}
            userPicks={picks}
            algorithmicPaths={paths}
            customPaths={customPaths}
          />
        )}

        {/* MULTI-ENTRY VIEW */}
        {!loading && view === 'multi-entry' && (
          <SurvivorMultiEntry weeks={weeks} />
        )}

        {/* Disclaimer */}
        <div style={{ marginTop: 32, fontSize: '0.65rem', color: MUTED, lineHeight: 1.6 }}>
          Win probabilities derived from Walters power ratings + 2.5 pt home field advantage. Not affiliated with Circa Sports.
          Schedule from ESPN. Picks saved locally in your browser only.
        </div>

      </div>
    </div>
  );
}

// ── Optimal Paths View ───────────────────────────────────────────────────────

function PathsView({
  paths, weeks, picks, setPick, used,
  thkPick, xmasPick, thkGames, xmasGames, setHolidayPick,
}: {
  paths: OptimalPath[];
  weeks: Record<number, Game[]>;
  picks: Record<number, string>;
  setPick: (week: number, team: string) => void;
  used: Set<string>;
  thkPick: string | null;
  xmasPick: string | null;
  thkGames: Game[];
  xmasGames: Game[];
  setHolidayPick: (type: 'thk' | 'xmas', team: string) => void;
}) {
  const weekNums = Object.keys(weeks).map(Number).sort((a, b) => a - b);

  // Build path timeline columns including holiday slots
  type PCol = number | 'thk' | 'xmas';
  const pathCols: PCol[] = [];
  for (const wk of weekNums) {
    if (wk === 12 && thkGames.length > 0)  pathCols.push('thk');
    if (wk === 16 && xmasGames.length > 0) pathCols.push('xmas');
    pathCols.push(wk);
  }

  const weekTags: Record<number, GameTags[]> = {};
  for (const wk of weekNums) {
    weekTags[wk] = (weeks[wk] ?? []).map(g => getGameTags(g.date));
  }
  const weekHasTag = (wk: number, key: keyof GameTags) =>
    (weekTags[wk] ?? []).some(t => t[key]);

  const survivalProb = (path: OptimalPath) => {
    const vals = Object.values(path.picks).map(p => p.wp);
    return vals.reduce((acc, v) => acc * v, 1);
  };

  // Best holiday pick suggestion (highest WP among non-used teams)
  function bestHolidayPick(games: Game[], usedSet: Set<string>, currentPick: string | null) {
    let best: { team: string; wp: number; label: string } | null = null;
    for (const g of games) {
      for (const [team, wp, label] of [[g.home, g.home_wp, g.home_label], [g.away, g.away_wp, g.away_label]] as [string, number, string][]) {
        if (!usedSet.has(team) || team === currentPick) {
          if (!best || wp > best.wp) best = { team, wp, label };
        }
      }
    }
    return best;
  }

  return (
    <div>
      <div style={{ fontSize: '0.65rem', color: MUTED, marginBottom: 16, lineHeight: 1.6 }}>
        Four algorithmic paths through the 2026 season. Each path picks one team per week without repeating.
        Click any pick to set it as your actual pick for that week.{' '}
        <span style={{ color: YELLOW }}>🦃 THK</span> and <span style={{ color: RED }}>🎄 XMAS</span> are mandatory holiday picks tracked separately.
      </div>

      {/* Holiday pick summary bar */}
      {(thkGames.length > 0 || xmasGames.length > 0) && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
          {thkGames.length > 0 && (() => {
            const sugg = bestHolidayPick(thkGames, used, thkPick);
            return (
              <div style={{ background: YELLOW + '10', border: `1px solid ${YELLOW}40`, borderRadius: 10, padding: '10px 14px', flex: 1, minWidth: 220 }}>
                <div style={{ fontSize: '0.6rem', fontWeight: 800, color: YELLOW, letterSpacing: '0.08em', marginBottom: 6 }}>🦃 THANKSGIVING PICK (MANDATORY)</div>
                {thkPick ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <img src={getLogo(thkPick)} alt={thkPick} style={{ width: 24, height: 24 }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />
                    <span style={{ fontWeight: 700, color: YELLOW }}>{thkPick}</span>
                    <span style={{ fontSize: '0.6rem', color: MUTED }}>selected</span>
                  </div>
                ) : sugg ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: '0.68rem', color: MUTED }}>Suggested:</span>
                    <button
                      onClick={() => setHolidayPick('thk', sugg.team)}
                      style={{ display: 'flex', alignItems: 'center', gap: 6, background: YELLOW + '20', border: `1px solid ${YELLOW}`, borderRadius: 6, padding: '3px 8px', cursor: 'pointer' }}
                    >
                      <img src={getLogo(sugg.team)} alt={sugg.team} style={{ width: 16, height: 16 }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />
                      <span style={{ fontSize: '0.7rem', fontWeight: 700, color: YELLOW }}>{sugg.team}</span>
                      <span style={{ fontSize: '0.6rem', color: LABEL_COLOR[sugg.label] ?? MUTED }}>{Math.round(sugg.wp * 100)}%</span>
                    </button>
                  </div>
                ) : (
                  <div style={{ fontSize: '0.68rem', color: MUTED }}>No teams available — all Thanksgiving teams used</div>
                )}
              </div>
            );
          })()}
          {xmasGames.length > 0 && (() => {
            const sugg = bestHolidayPick(xmasGames, used, xmasPick);
            return (
              <div style={{ background: RED + '08', border: `1px solid ${RED}35`, borderRadius: 10, padding: '10px 14px', flex: 1, minWidth: 220 }}>
                <div style={{ fontSize: '0.6rem', fontWeight: 800, color: RED, letterSpacing: '0.08em', marginBottom: 6 }}>🎄 CHRISTMAS PICK (MANDATORY)</div>
                {xmasPick ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <img src={getLogo(xmasPick)} alt={xmasPick} style={{ width: 24, height: 24 }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />
                    <span style={{ fontWeight: 700, color: RED }}>{xmasPick}</span>
                    <span style={{ fontSize: '0.6rem', color: MUTED }}>selected</span>
                  </div>
                ) : sugg ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: '0.68rem', color: MUTED }}>Suggested:</span>
                    <button
                      onClick={() => setHolidayPick('xmas', sugg.team)}
                      style={{ display: 'flex', alignItems: 'center', gap: 6, background: RED + '20', border: `1px solid ${RED}`, borderRadius: 6, padding: '3px 8px', cursor: 'pointer' }}
                    >
                      <img src={getLogo(sugg.team)} alt={sugg.team} style={{ width: 16, height: 16 }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />
                      <span style={{ fontSize: '0.7rem', fontWeight: 700, color: RED }}>{sugg.team}</span>
                      <span style={{ fontSize: '0.6rem', color: LABEL_COLOR[sugg.label] ?? MUTED }}>{Math.round(sugg.wp * 100)}%</span>
                    </button>
                  </div>
                ) : (
                  <div style={{ fontSize: '0.68rem', color: MUTED }}>No teams available — all Christmas teams used</div>
                )}
              </div>
            );
          })()}
        </div>
      )}

      {paths.map(path => {
        const survP = survivalProb(path);
        return (
          <div key={path.id} style={{ marginBottom: 28 }}>
            {/* Path header */}
            <div style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
              background: PANEL, border: `1px solid ${path.color}40`,
              borderLeft: `3px solid ${path.color}`,
              borderRadius: '8px 8px 0 0', padding: '12px 16px',
            }}>
              <div>
                <span style={{ fontWeight: 800, fontSize: '0.85rem', color: path.color, fontFamily: 'Nunito', letterSpacing: '0.05em' }}>
                  {path.name}
                </span>
                <div style={{ fontSize: '0.68rem', color: MUTED, marginTop: 2 }}>{path.desc}</div>
              </div>
              <div style={{ textAlign: 'right', flexShrink: 0 }}>
                <div style={{ fontSize: '0.6rem', color: MUTED }}>SURVIVAL PROB</div>
                <div style={{ fontWeight: 800, fontSize: '1rem', color: path.color, fontFamily: 'Nunito' }}>
                  {(survP * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            {/* Scrollable pick timeline */}
            <div style={{ overflowX: 'auto', background: 'var(--c-pathbg)', border: `1px solid ${path.color}25`, borderTop: 'none', borderRadius: '0 0 8px 8px' }}>
              <div style={{ display: 'flex', minWidth: pathCols.length * 72 + 'px' }}>
                {pathCols.map((col, idx) => {
                  const isLast = idx === pathCols.length - 1;

                  // ── Thanksgiving column in path timeline ─────────────────
                  if (col === 'thk') {
                    const isPick = !!thkPick;
                    return (
                      <div key="thk" style={{ flex: '0 0 72px', minWidth: 72, borderRight: isLast ? 'none' : `1px solid ${BORDER}` }}>
                        <div style={{ textAlign: 'center', padding: '6px 4px 4px', borderBottom: `1px solid ${BORDER}`, background: YELLOW + '15' }}>
                          <div style={{ fontSize: '0.55rem', fontWeight: 700, color: YELLOW }}>🦃 THK</div>
                        </div>
                        <div style={{ position: 'relative', height: 2, background: YELLOW + '25' }} />
                        <div style={{ padding: '8px 4px', textAlign: 'center' }}>
                          {thkPick ? (
                            <>
                              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 4 }}>
                                <img src={getLogo(thkPick)} alt={thkPick} style={{ width: 24, height: 24 }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />
                              </div>
                              <div style={{ fontSize: '0.6rem', fontWeight: 700, color: YELLOW }}>{thkPick}</div>
                              <div style={{ fontSize: '0.5rem', color: EMERALD, fontWeight: 700 }}>✓ SET</div>
                            </>
                          ) : (
                            <div style={{ fontSize: '0.55rem', color: YELLOW, opacity: 0.6, padding: '6px 0' }}>needed</div>
                          )}
                        </div>
                      </div>
                    );
                  }

                  // ── Christmas column in path timeline ────────────────────
                  if (col === 'xmas') {
                    return (
                      <div key="xmas" style={{ flex: '0 0 72px', minWidth: 72, borderRight: isLast ? 'none' : `1px solid ${BORDER}` }}>
                        <div style={{ textAlign: 'center', padding: '6px 4px 4px', borderBottom: `1px solid ${BORDER}`, background: RED + '12' }}>
                          <div style={{ fontSize: '0.55rem', fontWeight: 700, color: RED }}>🎄 XMAS</div>
                        </div>
                        <div style={{ position: 'relative', height: 2, background: RED + '20' }} />
                        <div style={{ padding: '8px 4px', textAlign: 'center' }}>
                          {xmasPick ? (
                            <>
                              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 4 }}>
                                <img src={getLogo(xmasPick)} alt={xmasPick} style={{ width: 24, height: 24 }} onError={e => { (e.target as HTMLImageElement).style.display='none'; }} />
                              </div>
                              <div style={{ fontSize: '0.6rem', fontWeight: 700, color: RED }}>{xmasPick}</div>
                              <div style={{ fontSize: '0.5rem', color: EMERALD, fontWeight: 700 }}>✓ SET</div>
                            </>
                          ) : (
                            <div style={{ fontSize: '0.55rem', color: RED, opacity: 0.6, padding: '6px 0' }}>needed</div>
                          )}
                        </div>
                      </div>
                    );
                  }

                  // ── Regular week column in path timeline ─────────────────
                  const wk = col as number;
                  const pick = path.picks[wk];
                  const isMyPick = picks[wk] === pick?.team;
                  const isUsed = pick && used.has(pick.team) && !isMyPick;
                  const color = pick ? (LABEL_COLOR[pick.label] ?? MUTED) : MUTED;
                  const hasTNF = weekHasTag(wk, 'isTNF');

                  return (
                    <div
                      key={wk}
                      style={{ flex: '0 0 72px', minWidth: 72, borderRight: isLast ? 'none' : `1px solid ${BORDER}` }}
                    >
                      {/* Week label */}
                      <div style={{ textAlign: 'center', padding: '6px 4px 4px', borderBottom: `1px solid ${BORDER}` }}>
                        <div style={{ fontSize: '0.55rem', fontWeight: 700, color: MUTED }}>
                          WK{wk}{hasTNF ? ' 🏈' : ''}
                        </div>
                      </div>

                      {/* Connecting line segment */}
                      <div style={{ position: 'relative', height: 2, background: path.color + '35' }}>
                        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, ${path.color}60, ${path.color}60)` }} />
                      </div>

                      {/* Pick cell */}
                      <button
                        onClick={() => pick && setPick(wk, pick.team)}
                        disabled={!pick}
                        style={{
                          width: '100%', background: isMyPick ? path.color + '20' : 'transparent',
                          border: 'none', borderBottom: isMyPick ? `2px solid ${path.color}` : '2px solid transparent',
                          padding: '8px 4px', cursor: pick ? 'pointer' : 'default',
                          opacity: isUsed ? 0.4 : 1,
                        }}
                      >
                        {pick ? (
                          <>
                            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 4 }}>
                              <img
                                src={getLogo(pick.team)}
                                alt={pick.team}
                                style={{ width: 24, height: 24, opacity: isUsed ? 0.4 : 1 }}
                                onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                              />
                            </div>
                            <div style={{ fontSize: '0.6rem', fontWeight: 700, color: isUsed ? MUTED : FG, textAlign: 'center' }}>{pick.team}</div>
                            <div style={{ fontSize: '0.6rem', fontWeight: 700, color, textAlign: 'center' }}>{Math.round(pick.wp * 100)}%</div>
                            <div style={{ fontSize: '0.5rem', color: MUTED, textAlign: 'center' }}>vs {pick.opp}</div>
                            {isMyPick && <div style={{ fontSize: '0.5rem', color: path.color, textAlign: 'center', fontWeight: 700 }}>✓ PICK</div>}
                            {isUsed  && <div style={{ fontSize: '0.5rem', color: RED, textAlign: 'center' }}>USED</div>}
                          </>
                        ) : (
                          <div style={{ fontSize: '0.55rem', color: MUTED, textAlign: 'center', padding: '8px 0' }}>BYE</div>
                        )}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        );
      })}

      <div style={{ marginTop: 8, fontSize: '0.65rem', color: MUTED, lineHeight: 1.6 }}>
        Survival probability = product of all weekly win probabilities. Path algorithms are greedy — not globally optimal.
        Holiday picks (THK/XMAS) are mandatory separate picks not included in path survival probability.
      </div>
    </div>
  );
}

export default Survivor;
