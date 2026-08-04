import { useState, useEffect, useCallback, useMemo } from 'react';
import { getApiUrl } from '../config';
import { SurvivorStrategy, computeFutureValue, findHolidayDoubles, getWeekHazard } from './SurvivorStrategy';

// ── Semantic color tokens (theme-agnostic) ────────────────────────────────────
// These resolve to CSS custom properties set on the root wrapper div.
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

type View = 'grid' | 'weekly' | 'paths' | 'strategy';

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
  const weeksByRef = weeks; // captured for FV calc inside contrarian path
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
      id: 'conservative',
      name: 'CONSERVATIVE',
      desc: 'Avoids burning GREAT matchups early — saves them for tough stretches',
      color: YELLOW,
      picks: buildPath((c, wk) => {
        if (wk <= 7 && c.label === 'GREAT') return c.wp * 0.82;
        return c.wp;
      }),
    },
    {
      id: 'contrarian',
      name: 'CONTRARIAN',
      desc: 'Avoids high-future-value teams early — the sharp field will hoard them, so use them later',
      color: ORANGE,
      picks: buildPath((c, wk) => {
        // Penalize teams with high FV in early weeks — the sharp Circa crowd will be saving them.
        // Using a high-FV team early burns an asset the field will be hoarding; creates poor leverage.
        const fv = computeFutureValue(c.team, wk, weeksByRef);
        if (wk <= 7 && fv >= 6) return c.wp * 0.78;
        if (wk <= 5 && fv >= 4) return c.wp * 0.86;
        return c.wp;
      }),
    },
  ];
}

const STORAGE_KEY  = 'survivor_2026_used';
const PICK_KEY     = 'survivor_2026_picks';
const THEME_KEY    = 'survivor_theme';

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

export function Survivor() {
  const [dark, setDark] = useState(() => localStorage.getItem(THEME_KEY) === 'dark');
  const [teams, setTeams] = useState<Team[]>([]);
  const [weeks, setWeeks] = useState<Record<number, Game[]>>({});
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<View>('weekly');
  const [selectedWeek, setSelectedWeek] = useState(1);
  const [used, setUsed] = useState<Set<string>>(loadUsed);
  const [picks, setPicks] = useState<Record<number, string>>(loadPicks);

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
      })
      .catch(() => setLoading(false));
  }, []);

  const paths = useMemo(() => computePaths(weeks), [weeks]);
  const [selectedPathId, setSelectedPathId] = useState<string | null>(null);
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

  const clearAll = () => {
    setUsed(new Set());
    setPicks({});
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(PICK_KEY);
  };

  const weekNums = Object.keys(weeks).map(Number).sort((a, b) => a - b);
  const currentWeekGames: Game[] = weeks[selectedWeek] ?? [];
  const availableTeams = teams.filter(t => !used.has(t.team));
  const usedTeams = teams.filter(t => used.has(t.team));

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
              <span style={{ fontSize: '0.72rem', color: MUTED }}>{availableTeams.length} teams remaining · {Object.keys(picks).length} weeks picked</span>
              {/* Theme toggle */}
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
        <div style={{ display: 'flex', gap: 6, marginBottom: 20 }}>
          <button style={navBtn(view === 'weekly')} onClick={() => setView('weekly')}>WEEKLY PICKS</button>
          <button style={navBtn(view === 'grid')} onClick={() => setView('grid')}>TEAM GRID</button>
          <button style={navBtn(view === 'paths')} onClick={() => setView('paths')}>OPTIMAL PATHS</button>
          <button style={navBtn(view === 'strategy')} onClick={() => setView('strategy')}>STRATEGY</button>
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
                    <span style={{ fontWeight: selectedWeek === wk ? 700 : 400 }}>Wk {wk}</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
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
                    Your pick: <strong>{picks[selectedWeek]}</strong>
                  </div>
                )}
              </div>

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
              Click a team to toggle used/available. Each cell shows win probability for that week. Green = GREAT, Yellow = LEAN, Red = TRAP.
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
                      <th style={{ padding: '6px 8px', color: MUTED, fontWeight: 600, fontSize: '0.6rem', minWidth: 52, borderRight: `1px solid ${BORDER}` }}>RTG</th>
                      <th style={{ padding: '6px 8px', color: BLUE, fontWeight: 700, fontSize: '0.6rem', minWidth: 44, borderRight: `1px solid ${BORDER}` }} title="Future Value Score">FV</th>
                      {weekNums.map(wk => {
                        const tags = (weeks[wk] ?? []).map(g => getGameTags(g.date));
                        const hasThanksgiving = tags.some(t => t.isThanksgiving);
                        const hasChristmas    = tags.some(t => t.isChristmas);
                        const hasTNF          = tags.some(t => t.isTNF);
                        return (
                          <th
                            key={wk}
                            style={{ padding: '6px 6px', color: selectedWeek === wk ? FG : MUTED, fontWeight: selectedWeek === wk ? 700 : 600, fontSize: '0.55rem', minWidth: 42, cursor: 'pointer', textAlign: 'center', borderRight: `1px solid ${BORDER}` }}
                            onClick={() => { setSelectedWeek(wk); setView('weekly'); }}
                          >
                            W{wk}{hasThanksgiving ? '🦃' : hasChristmas ? '🎄' : hasTNF ? '🏈' : ''}
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
                        <td style={{ padding: '4px 8px', textAlign: 'center', fontSize: '0.55rem', color: MUTED, borderRight: `1px solid ${BORDER}` }}>PATH</td>
                        {weekNums.map(wk => {
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
                        <td style={{ padding: '7px 8px', fontWeight: 700, color: t.rating >= 4 ? EMERALD : t.rating >= 0 ? YELLOW : RED, textAlign: 'center', borderRight: `1px solid ${BORDER}` }}>
                          {t.rating >= 0 ? '+' : ''}{t.rating.toFixed(1)}
                        </td>
                        <td style={{ padding: '7px 8px', textAlign: 'center', borderRight: `1px solid ${BORDER}` }}>
                          {(() => {
                            const fv = computeFutureValue(t.team, 0, weeks);
                            return (
                              <span style={{ fontSize: '0.7rem', fontWeight: 800, fontFamily: 'monospace',
                                color: fv >= 8 ? EMERALD : fv >= 4 ? BLUE : MUTED }}>
                                {fv}
                              </span>
                            );
                          })()}
                        </td>
                        {weekNums.map(wk => {
                          const entry = t.schedule.find(s => s.week === wk);
                          const isPick = picks[wk] === t.team;
                          const isPathPick = activePath?.picks[wk]?.team === t.team;
                          if (!entry) {
                            return <td key={wk} style={{ padding: '7px 6px', textAlign: 'center', color: MUTED, fontSize: '0.6rem', borderRight: `1px solid ${BORDER}` }}>BYE</td>;
                          }
                          const color = LABEL_COLOR[entry.label] ?? MUTED;
                          return (
                            <td key={wk} style={{ padding: '4px 3px', textAlign: 'center', borderRight: `1px solid ${BORDER}`, outline: isPathPick ? `2px solid ${activePath!.color}` : 'none', outlineOffset: -2 }}>
                              <button
                                onClick={() => setPick(wk, t.team)}
                                style={{
                                  background: isPick ? color + '25' : 'transparent',
                                  border: `1px solid ${isPick ? color : 'transparent'}`,
                                  borderRadius: 4, padding: '3px 4px', cursor: 'pointer', width: '100%',
                                }}
                              >
                                <div style={{ fontSize: '0.65rem', fontWeight: 700, color }}>{Math.round(entry.wp * 100)}%</div>
                                <div style={{ fontSize: '0.55rem', color: MUTED }}>{entry.home ? '' : '@'}{entry.opp}</div>
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
          <PathsView paths={paths} weeks={weeks} picks={picks} setPick={setPick} used={used} />
        )}

        {/* STRATEGY VIEW */}
        {!loading && view === 'strategy' && (
          <SurvivorStrategy teams={teams} weeks={weeks} used={used} />
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
}: {
  paths: OptimalPath[];
  weeks: Record<number, Game[]>;
  picks: Record<number, string>;
  setPick: (week: number, team: string) => void;
  used: Set<string>;
}) {
  const weekNums = Object.keys(weeks).map(Number).sort((a, b) => a - b);

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

  return (
    <div>
      <div style={{ fontSize: '0.65rem', color: MUTED, marginBottom: 16, lineHeight: 1.6 }}>
        Four algorithmic paths through the 2026 season. Each path picks one team per week without repeating.
        Click any pick to set it as your actual pick for that week. <span style={{ color: YELLOW }}>🦃 = Thanksgiving · 🎄 = Christmas · 🏈 = TNF</span>
      </div>

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
              <div style={{ display: 'flex', minWidth: weekNums.length * 72 + 'px' }}>
                {weekNums.map((wk, idx) => {
                  const pick = path.picks[wk];
                  const isMyPick = picks[wk] === pick?.team;
                  const isUsed = pick && used.has(pick.team) && !isMyPick;
                  const color = pick ? (LABEL_COLOR[pick.label] ?? MUTED) : MUTED;
                  const hasTNF = weekHasTag(wk, 'isTNF');
                  const hasThanksgiving = weekHasTag(wk, 'isThanksgiving');
                  const hasChristmas = weekHasTag(wk, 'isChristmas');
                  const isLast = idx === weekNums.length - 1;

                  return (
                    <div
                      key={wk}
                      style={{
                        flex: '0 0 72px', minWidth: 72,
                        borderRight: isLast ? 'none' : `1px solid ${BORDER}`,
                        padding: '0',
                      }}
                    >
                      {/* Week label */}
                      <div style={{
                        textAlign: 'center', padding: '6px 4px 4px',
                        borderBottom: `1px solid ${BORDER}`,
                        background: hasThanksgiving ? YELLOW + '15' : hasChristmas ? RED + '12' : 'transparent',
                      }}>
                        <div style={{ fontSize: '0.55rem', fontWeight: 700, color: MUTED }}>
                          WK{wk}
                          {hasThanksgiving && ' 🦃'}
                          {hasChristmas && ' 🎄'}
                          {hasTNF && !hasThanksgiving && !hasChristmas && ' 🏈'}
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
        FUTURE VALUE and CONSERVATIVE paths will diverge most from the public in weeks 1–7.
      </div>
    </div>
  );
}

export default Survivor;
