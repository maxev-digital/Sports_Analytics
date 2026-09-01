/**
 * SurvivorPathBuilder — "MY PATHS" tab for the Survivor Helper.
 * Grid mode: team × week matrix with sortable headers and separate THK/XMAS columns.
 * Sidebar mode: week-by-week game picker.
 */
import { useState, useMemo } from 'react';
import { CUSTOM_PATH_COLORS, type SurvivorGame, type SurvivorPick, type CustomPath } from './survivorAlgo';

const EMERALD = 'oklch(69.6% .17 162.48)';
const RED     = 'oklch(63.2% .204 25.331)';
const YELLOW  = 'oklch(79.5% .184 86.047)';
const BLUE    = 'oklch(62.3% .214 259.815)';
const MUTED   = 'var(--c-muted)';
const PANEL   = 'var(--c-panel)';
const BORDER  = 'var(--c-border)';
const FG      = 'var(--c-fg)';

const LABEL_COLOR: Record<string, string> = {
  GREAT: EMERALD, GOOD: 'oklch(70% .15 150)',
  LEAN: YELLOW, TOUGH: 'oklch(70% .15 30)', TRAP: RED,
};

const LOGO_MAP: Record<string, string> = {
  ARI:'ari',ATL:'atl',BAL:'bal',BUF:'buf',CAR:'car',CHI:'chi',CIN:'cin',CLE:'cle',
  DAL:'dal',DEN:'den',DET:'det',GB:'gb',HOU:'hou',IND:'ind',JAX:'jax',KC:'kc',
  LAC:'lac',LAR:'lar',LV:'lv',MIA:'mia',MIN:'min',NE:'ne',NO:'no',NYG:'nyg',
  NYJ:'nyj',PHI:'phi',PIT:'pit',SEA:'sea',SF:'sf',TB:'tb',TEN:'ten',WSH:'wsh',
};
const logo = (abbr: string) =>
  `https://a.espncdn.com/i/teamlogos/nfl/500/${LOGO_MAP[abbr] ?? abbr.toLowerCase()}.png`;

const wpColor = (wp: number) =>
  wp >= 0.73 ? EMERALD : wp >= 0.58 ? BLUE : wp >= 0.45 ? YELLOW : RED;

type HolidaySlot = 'thk' | 'xmas';
type GridCol = number | HolidaySlot;

interface BuildingState {
  name: string;
  color: string;
  picks: Record<number, SurvivorPick>;
  thkPick: SurvivorPick | null;
  xmasPick: SurvivorPick | null;
  editingId: string | null;
}

interface Props {
  weeks: Record<number, SurvivorGame[]>;
  customPaths: CustomPath[];
  onPathsChange: (paths: CustomPath[]) => void;
  thkGames?: SurvivorGame[];
  xmasGames?: SurvivorGame[];
}

export function SurvivorPathBuilder({ weeks, customPaths, onPathsChange, thkGames = [], xmasGames = [] }: Props) {
  const [building, setBuilding]       = useState<BuildingState | null>(null);
  const [activeWeek, setActiveWeek]   = useState<number | HolidaySlot>(1);
  const [nameInput, setNameInput]     = useState('');
  const [builderMode, setBuilderMode] = useState<'sidebar' | 'grid'>('grid');
  const [sortState, setSortState]     = useState<{ col: GridCol; dir: 'desc' | 'asc' } | null>(null);

  const weekNums = useMemo(
    () => Object.keys(weeks).map(Number).sort((a, b) => a - b),
    [weeks],
  );

  // Grid columns: insert THK before WK12, XMAS before WK16
  const gridCols = useMemo<GridCol[]>(() => {
    const cols: GridCol[] = [];
    for (const wk of weekNums) {
      if (wk === 12 && thkGames.length > 0)  cols.push('thk');
      if (wk === 16 && xmasGames.length > 0) cols.push('xmas');
      cols.push(wk);
    }
    return cols;
  }, [weekNums, thkGames.length, xmasGames.length]);

  // Build team → week lookup
  const teamWeekMap = useMemo(() => {
    const map: Record<string, Record<number, { wp: number; opp: string; home: boolean; label: string }>> = {};
    for (const [wkStr, games] of Object.entries(weeks)) {
      const wk = Number(wkStr);
      for (const g of games) {
        if (!map[g.home]) map[g.home] = {};
        if (!map[g.away]) map[g.away] = {};
        map[g.home][wk] = { wp: g.home_wp, opp: g.away, home: true,  label: g.home_label };
        map[g.away][wk] = { wp: g.away_wp, opp: g.home, home: false, label: g.away_label };
      }
    }
    return map;
  }, [weeks]);

  // Build team → holiday game lookup
  const thkMap = useMemo(() => {
    const m: Record<string, { wp: number; opp: string; home: boolean; label: string }> = {};
    for (const g of thkGames) {
      m[g.home] = { wp: g.home_wp, opp: g.away, home: true,  label: g.home_label };
      m[g.away] = { wp: g.away_wp, opp: g.home, home: false, label: g.away_label };
    }
    return m;
  }, [thkGames]);

  const xmasMap = useMemo(() => {
    const m: Record<string, { wp: number; opp: string; home: boolean; label: string }> = {};
    for (const g of xmasGames) {
      m[g.home] = { wp: g.home_wp, opp: g.away, home: true,  label: g.home_label };
      m[g.away] = { wp: g.away_wp, opp: g.home, home: false, label: g.away_label };
    }
    return m;
  }, [xmasGames]);

  // All teams sorted alphabetically (base order)
  const allTeams = useMemo(() => Object.keys(teamWeekMap).sort(), [teamWeekMap]);

  // Apply column sort
  const sortedTeams = useMemo(() => {
    if (!sortState) return allTeams;
    return [...allTeams].sort((a, b) => {
      let wpA: number, wpB: number;
      if (sortState.col === 'thk') {
        wpA = thkMap[a]?.wp ?? -1;
        wpB = thkMap[b]?.wp ?? -1;
      } else if (sortState.col === 'xmas') {
        wpA = xmasMap[a]?.wp ?? -1;
        wpB = xmasMap[b]?.wp ?? -1;
      } else {
        wpA = teamWeekMap[a]?.[sortState.col as number]?.wp ?? -1;
        wpB = teamWeekMap[b]?.[sortState.col as number]?.wp ?? -1;
      }
      return sortState.dir === 'desc' ? wpB - wpA : wpA - wpB;
    });
  }, [allTeams, sortState, teamWeekMap, thkMap, xmasMap]);

  const cycleSort = (col: GridCol) => {
    setSortState(prev => {
      if (!prev || prev.col !== col) return { col, dir: 'desc' };
      if (prev.dir === 'desc') return { col, dir: 'asc' };
      return null;
    });
  };

  // Teams used anywhere in the current path (regular + holiday)
  const usedInPath = useMemo(() => {
    if (!building) return new Set<string>();
    const s = new Set(Object.values(building.picks).map(p => p.team));
    if (building.thkPick)  s.add(building.thkPick.team);
    if (building.xmasPick) s.add(building.xmasPick.team);
    return s;
  }, [building]);

  const startNew = () => {
    const color = CUSTOM_PATH_COLORS[customPaths.length % CUSTOM_PATH_COLORS.length];
    setBuilding({ name: '', color, picks: {}, thkPick: null, xmasPick: null, editingId: null });
    setNameInput('');
    setActiveWeek(weekNums[0] ?? 1);
  };

  const startEdit = (path: CustomPath) => {
    setBuilding({
      name: path.name, color: path.color, picks: { ...path.picks },
      thkPick: path.thkPick ?? null, xmasPick: path.xmasPick ?? null,
      editingId: path.id,
    });
    setNameInput(path.name);
    setActiveWeek(weekNums[0] ?? 1);
  };

  const cancelBuild = () => setBuilding(null);

  const savePath = () => {
    if (!building || !nameInput.trim()) return;
    const base = {
      name: nameInput.trim(), color: building.color,
      picks: building.picks,
      thkPick:  building.thkPick  ?? undefined,
      xmasPick: building.xmasPick ?? undefined,
    };
    const updated = building.editingId
      ? customPaths.map(p => p.id === building.editingId ? { ...p, ...base } : p)
      : [...customPaths, { id: `custom-${Date.now()}`, createdAt: Date.now(), ...base }];
    onPathsChange(updated);
    setBuilding(null);
  };

  const deletePath = (id: string) => onPathsChange(customPaths.filter(p => p.id !== id));

  const pickTeam = (wk: number, team: string, wp: number, opp: string, home: boolean, label: string) => {
    if (!building) return;
    const prev = building.picks[wk];
    const next = prev?.team === team
      ? (() => { const p = { ...building.picks }; delete p[wk]; return p; })()
      : { ...building.picks, [wk]: { week: wk, team, wp, opp, home, label } };
    setBuilding({ ...building, picks: next });
  };

  const pickHoliday = (slot: HolidaySlot, team: string, wp: number, opp: string, home: boolean, label: string) => {
    if (!building) return;
    const key = slot === 'thk' ? 'thkPick' : 'xmasPick';
    const prev = building[key];
    setBuilding({ ...building, [key]: prev?.team === team ? null : { week: slot === 'thk' ? 12 : 16, team, wp, opp, home, label } });
  };

  const survivalProb = (b: BuildingState) => {
    let p = Object.values(b.picks).reduce((acc, pick) => acc * pick.wp, 1);
    if (b.thkPick)  p *= b.thkPick.wp;
    if (b.xmasPick) p *= b.xmasPick.wp;
    return p;
  };

  const survivalProbPath = (path: CustomPath) => {
    let p = Object.values(path.picks).reduce((acc, pick) => acc * pick.wp, 1);
    if (path.thkPick)  p *= path.thkPick.wp;
    if (path.xmasPick) p *= path.xmasPick.wp;
    return p;
  };

  const regularPickCount = building ? Object.keys(building.picks).length : 0;
  const holidayPickCount = building ? (building.thkPick ? 1 : 0) + (building.xmasPick ? 1 : 0) : 0;
  const totalPicked = regularPickCount + holidayPickCount;
  const totalSlots  = weekNums.length + (thkGames.length > 0 ? 1 : 0) + (xmasGames.length > 0 ? 1 : 0);
  const allFilled   = building ? totalPicked === totalSlots : false;
  const canSave     = !!nameInput.trim();

  // ── List view ──────────────────────────────────────────────────────────────
  if (!building) {
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: '0.7rem', fontWeight: 800, color: FG, letterSpacing: '0.06em' }}>MY CUSTOM PATHS</div>
            <div style={{ fontSize: '0.62rem', color: MUTED, marginTop: 2 }}>
              Build season-long pick sequences including Thanksgiving and Christmas picks.
            </div>
          </div>
          <button onClick={startNew} style={{
            fontSize: '0.7rem', fontWeight: 800, padding: '8px 16px', borderRadius: 6,
            cursor: 'pointer', background: BLUE + '22', border: `1px solid ${BLUE}`, color: BLUE, flexShrink: 0,
          }}>
            + NEW PATH
          </button>
        </div>

        {customPaths.length === 0 && (
          <div style={{
            textAlign: 'center', padding: '48px 24px',
            background: PANEL, border: `1px dashed ${BORDER}`, borderRadius: 10,
            fontSize: '0.72rem', color: MUTED,
          }}>
            No custom paths yet. Click <strong style={{ color: FG }}>+ NEW PATH</strong> to build your first season-long pick sequence.
          </div>
        )}

        <div style={{ display: 'grid', gap: 12 }}>
          {customPaths.map(path => {
            const sp = survivalProbPath(path);
            const pickCount = Object.keys(path.picks).length
              + (path.thkPick ? 1 : 0) + (path.xmasPick ? 1 : 0);
            return (
              <div key={path.id} style={{
                background: PANEL, border: `1px solid ${path.color}40`,
                borderLeft: `3px solid ${path.color}`, borderRadius: 8, padding: '14px 16px',
              }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 10 }}>
                  <div>
                    <div style={{ fontWeight: 800, fontSize: '0.85rem', color: path.color, fontFamily: 'Nunito' }}>
                      {path.name}
                    </div>
                    <div style={{ fontSize: '0.62rem', color: MUTED, marginTop: 2 }}>
                      {pickCount} / {totalSlots} slots picked · joint survival {(sp * 100).toFixed(2)}%
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 6, flexShrink: 0, marginLeft: 12 }}>
                    <button onClick={() => startEdit(path)} style={{
                      fontSize: '0.62rem', fontWeight: 700, padding: '4px 10px', borderRadius: 5,
                      cursor: 'pointer', background: 'transparent', border: `1px solid ${BORDER}`, color: MUTED,
                    }}>Edit</button>
                    <button onClick={() => deletePath(path.id)} style={{
                      fontSize: '0.62rem', fontWeight: 700, padding: '4px 10px', borderRadius: 5,
                      cursor: 'pointer', background: 'transparent', border: `1px solid ${RED}50`, color: RED,
                    }}>Delete</button>
                  </div>
                </div>

                {/* Pick timeline — bordered table */}
                <div style={{ overflowX: 'auto', marginTop: 4 }}>
                  <table style={{ borderCollapse: 'collapse', minWidth: 'max-content' }}>
                    <thead>
                      <tr>
                        {weekNums.map(wk => {
                          const isThkWk  = wk === 12 && thkGames.length > 0;
                          const isXmasWk = wk === 16 && xmasGames.length > 0;
                          return (
                            <>
                              {isThkWk && (
                                <th key="thk-h" style={{
                                  padding: '5px 6px', textAlign: 'center', minWidth: 64,
                                  border: `1px solid ${YELLOW}50`,
                                  background: YELLOW + '18',
                                  fontSize: '0.6rem', fontWeight: 800, color: YELLOW,
                                }}>🦃 THK</th>
                              )}
                              {isXmasWk && (
                                <th key="xmas-h" style={{
                                  padding: '5px 6px', textAlign: 'center', minWidth: 64,
                                  border: `1px solid ${RED}40`,
                                  background: RED + '12',
                                  fontSize: '0.6rem', fontWeight: 800, color: RED,
                                }}>🎄 XMS</th>
                              )}
                              <th key={wk} style={{
                                padding: '5px 8px', textAlign: 'center', minWidth: 64,
                                border: `1px solid ${BORDER}`,
                                background: path.picks[wk] ? path.color + '14' : 'transparent',
                                fontSize: '0.6rem', fontWeight: 700,
                                color: path.picks[wk] ? path.color : MUTED,
                              }}>WK{wk}</th>
                            </>
                          );
                        })}
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        {weekNums.map(wk => {
                          const isThkWk  = wk === 12 && thkGames.length > 0;
                          const isXmasWk = wk === 16 && xmasGames.length > 0;
                          return (
                            <>
                              {isThkWk && (() => {
                                const p = path.thkPick;
                                return (
                                  <td key="thk-b" style={{
                                    padding: '8px 6px', textAlign: 'center',
                                    border: `1px solid ${YELLOW}50`,
                                    background: p ? YELLOW + '10' : 'transparent',
                                    verticalAlign: 'middle',
                                  }}>
                                    {p ? (
                                      <>
                                        <img src={logo(p.team)} alt={p.team} style={{ width: 30, height: 30, display: 'block', margin: '0 auto 4px' }} onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                                        <div style={{ fontSize: '0.65rem', fontWeight: 800, color: YELLOW }}>{p.team}</div>
                                        <div style={{ fontSize: '0.6rem', color: MUTED }}>{Math.round(p.wp * 100)}%</div>
                                      </>
                                    ) : (
                                      <span style={{ fontSize: '0.6rem', color: MUTED }}>—</span>
                                    )}
                                  </td>
                                );
                              })()}
                              {isXmasWk && (() => {
                                const p = path.xmasPick;
                                return (
                                  <td key="xmas-b" style={{
                                    padding: '8px 6px', textAlign: 'center',
                                    border: `1px solid ${RED}40`,
                                    background: p ? RED + '08' : 'transparent',
                                    verticalAlign: 'middle',
                                  }}>
                                    {p ? (
                                      <>
                                        <img src={logo(p.team)} alt={p.team} style={{ width: 30, height: 30, display: 'block', margin: '0 auto 4px' }} onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                                        <div style={{ fontSize: '0.65rem', fontWeight: 800, color: RED }}>{p.team}</div>
                                        <div style={{ fontSize: '0.6rem', color: MUTED }}>{Math.round(p.wp * 100)}%</div>
                                      </>
                                    ) : (
                                      <span style={{ fontSize: '0.6rem', color: MUTED }}>—</span>
                                    )}
                                  </td>
                                );
                              })()}
                              {(() => {
                                const p = path.picks[wk];
                                return (
                                  <td key={wk} style={{
                                    padding: '8px 6px', textAlign: 'center',
                                    border: `1px solid ${BORDER}`,
                                    background: p ? path.color + '10' : 'transparent',
                                    verticalAlign: 'middle',
                                  }}>
                                    {p ? (
                                      <>
                                        <img src={logo(p.team)} alt={p.team} style={{ width: 30, height: 30, display: 'block', margin: '0 auto 4px' }} onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                                        <div style={{ fontSize: '0.65rem', fontWeight: 800, color: FG }}>{p.team}</div>
                                        <div style={{ fontSize: '0.6rem', color: LABEL_COLOR[p.label] ?? MUTED, fontWeight: 700 }}>{Math.round(p.wp * 100)}%</div>
                                      </>
                                    ) : (
                                      <span style={{ fontSize: '0.6rem', color: MUTED }}>—</span>
                                    )}
                                  </td>
                                );
                              })()}
                            </>
                          );
                        })}
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // ── Builder shared elements ────────────────────────────────────────────────
  const BuilderHeader = (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        <input
          value={nameInput}
          onChange={e => setNameInput(e.target.value)}
          placeholder="Path name (e.g. My Circa Entry)"
          style={{
            flex: 1, minWidth: 200, padding: '8px 12px', borderRadius: 6,
            background: PANEL, border: `1px solid ${BORDER}`, color: FG,
            fontSize: '0.82rem', fontWeight: 700, fontFamily: 'Nunito',
          }}
        />
        <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
          {CUSTOM_PATH_COLORS.map((c, i) => (
            <button key={i} onClick={() => setBuilding(b => b ? { ...b, color: c } : b)} style={{
              width: 20, height: 20, borderRadius: '50%', background: c, cursor: 'pointer',
              border: building.color === c ? `3px solid ${FG}` : '2px solid transparent',
            }} />
          ))}
        </div>
        <div style={{ display: 'flex', background: 'var(--c-track)', borderRadius: 6, padding: 2 }}>
          {(['grid', 'sidebar'] as const).map(mode => (
            <button key={mode} onClick={() => setBuilderMode(mode)} style={{
              padding: '5px 11px', borderRadius: 5, cursor: 'pointer', fontSize: '0.65rem', fontWeight: 700,
              background: builderMode === mode ? PANEL : 'transparent',
              border: builderMode === mode ? `1px solid ${BORDER}` : '1px solid transparent',
              color: builderMode === mode ? FG : MUTED,
            }}>
              {mode === 'grid' ? 'GRID' : 'SIDEBAR'}
            </button>
          ))}
        </div>
        <button onClick={cancelBuild} style={{
          fontSize: '0.68rem', fontWeight: 700, padding: '7px 12px', borderRadius: 6,
          cursor: 'pointer', background: 'transparent', border: `1px solid ${BORDER}`, color: MUTED,
        }}>Cancel</button>
      </div>

      {/* Progress bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ flex: 1, height: 4, background: 'var(--c-track)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{
            height: '100%', borderRadius: 2, background: building.color,
            width: `${(totalPicked / totalSlots) * 100}%`,
            transition: 'width 0.2s ease',
          }} />
        </div>
        <div style={{ fontSize: '0.62rem', color: MUTED, whiteSpace: 'nowrap' }}>
          {totalPicked}/{totalSlots} slots · joint survival{' '}
          <span style={{ color: building.color, fontWeight: 700 }}>
            {(survivalProb(building) * 100).toFixed(2)}%
          </span>
        </div>
      </div>
    </div>
  );

  const SaveBanner = allFilled ? (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12,
      background: building.color + '18', border: `1.5px solid ${building.color}`,
      borderRadius: 10, padding: '14px 20px', marginBottom: 16,
    }}>
      <div>
        <div style={{ fontWeight: 800, fontSize: '0.85rem', color: building.color, fontFamily: 'Nunito' }}>
          ✓ All {totalSlots} slots picked
        </div>
        <div style={{ fontSize: '0.62rem', color: MUTED, marginTop: 2 }}>
          Joint survival: <strong style={{ color: building.color }}>{(survivalProb(building) * 100).toFixed(2)}%</strong>
          {!nameInput.trim() && <span style={{ color: YELLOW, marginLeft: 8 }}>← enter a name to save</span>}
        </div>
      </div>
      <button onClick={savePath} disabled={!canSave} style={{
        fontSize: '0.78rem', fontWeight: 800, padding: '10px 24px', borderRadius: 8,
        cursor: canSave ? 'pointer' : 'default',
        background: canSave ? building.color : MUTED + '22',
        border: `1px solid ${canSave ? building.color : MUTED + '44'}`,
        color: canSave ? 'oklch(98% 0 0)' : MUTED,
      }}>Save Path</button>
    </div>
  ) : null;

  // ── GRID MODE ──────────────────────────────────────────────────────────────
  if (builderMode === 'grid') {
    return (
      <div>
        {BuilderHeader}
        {SaveBanner}

        <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 10, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: '70vh' }}>
            <table style={{ borderCollapse: 'collapse', fontSize: '0.68rem', minWidth: 'max-content' }}>
              <thead>
                <tr>
                  {/* Team header — sticky left + top */}
                  <th style={{
                    position: 'sticky', left: 0, top: 0, zIndex: 4,
                    background: PANEL, borderRight: `1px solid ${BORDER}`,
                    borderBottom: `1px solid ${BORDER}`,
                    padding: '8px 12px', textAlign: 'left',
                    fontSize: '0.58rem', color: MUTED, fontWeight: 700, letterSpacing: '0.06em',
                    minWidth: 90,
                  }}>TEAM</th>

                  {gridCols.map(col => {
                    const isHoliday = col === 'thk' || col === 'xmas';
                    const isTHK     = col === 'thk';
                    const isXMAS    = col === 'xmas';
                    const isActive  = sortState?.col === col;
                    const indicator = isActive ? (sortState!.dir === 'desc' ? ' ▼' : ' ▲') : '';
                    const accentCol = isTHK ? YELLOW : isXMAS ? RED : undefined;

                    // Current pick for this column
                    let colPick: SurvivorPick | null = null;
                    if (isTHK)        colPick = building.thkPick;
                    else if (isXMAS)  colPick = building.xmasPick;
                    else              colPick = building.picks[col as number] ?? null;

                    return (
                      <th key={String(col)}
                        onClick={() => cycleSort(col)}
                        style={{
                          position: 'sticky', top: 0, zIndex: 3,
                          background: colPick
                            ? (isHoliday ? (isTHK ? YELLOW : RED) + '25' : building.color + '22')
                            : isActive ? 'var(--c-rowsel)' : PANEL,
                          borderBottom: `2px solid ${colPick ? (accentCol ?? building.color) : isActive ? FG : BORDER}`,
                          borderRight: `1px solid ${isHoliday ? (accentCol + '50') : BORDER}`,
                          padding: '6px 4px', textAlign: 'center',
                          fontSize: '0.58rem',
                          color: colPick ? (accentCol ?? building.color) : isActive ? FG : MUTED,
                          fontWeight: 700, letterSpacing: '0.04em', minWidth: 58,
                          cursor: 'pointer', userSelect: 'none',
                          ...(isHoliday ? { background: colPick ? (isTHK ? YELLOW + '25' : RED + '20') : (isTHK ? YELLOW + '10' : RED + '08') } : {}),
                        }}
                      >
                        <div>
                          {isTHK ? `🦃THK${indicator}` : isXMAS ? `🎄XMS${indicator}` : `WK${col}${indicator}`}
                        </div>
                        {colPick && (
                          <img src={logo(colPick.team)} alt={colPick.team}
                            style={{ width: 18, height: 18, margin: '2px auto 0', display: 'block' }}
                            onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                        )}
                      </th>
                    );
                  })}
                </tr>
              </thead>

              <tbody>
                {sortedTeams.map((team, rowIdx) => {
                  const isUsed = usedInPath.has(team);
                  // Which slot is this team picked in?
                  const pickedSlot = building.thkPick?.team === team ? 'THK'
                    : building.xmasPick?.team === team ? 'XMAS'
                    : Object.entries(building.picks).find(([, p]) => p.team === team)?.[0];

                  return (
                    <tr key={team} style={{ background: rowIdx % 2 === 0 ? 'transparent' : 'var(--c-rowsel)', opacity: isUsed ? 0.5 : 1 }}>
                      {/* Team label — sticky left */}
                      <td style={{
                        position: 'sticky', left: 0, zIndex: 2,
                        background: rowIdx % 2 === 0 ? PANEL : 'var(--c-pathbg, var(--c-panel))',
                        borderRight: `1px solid ${BORDER}`, padding: '4px 10px', whiteSpace: 'nowrap',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                          <img src={logo(team)} alt={team}
                            style={{ width: 22, height: 22, flexShrink: 0, filter: isUsed ? 'grayscale(80%)' : 'none' }}
                            onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                          <div>
                            <div style={{ fontWeight: 700, fontSize: '0.72rem', color: isUsed ? MUTED : FG }}>{team}</div>
                            {isUsed && pickedSlot && (
                              <div style={{ fontSize: '0.5rem', color: building.color, fontWeight: 700 }}>
                                {pickedSlot} ✓
                              </div>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Column cells */}
                      {gridCols.map(col => {
                        const isTHK  = col === 'thk';
                        const isXMAS = col === 'xmas';
                        const accentCol = isTHK ? YELLOW : isXMAS ? RED : undefined;

                        let game: { wp: number; opp: string; home: boolean; label: string } | undefined;
                        let isPicked = false;
                        let isBlockedElsewhere = false;

                        if (isTHK) {
                          game = thkMap[team];
                          isPicked = building.thkPick?.team === team;
                          isBlockedElsewhere = isUsed && !isPicked;
                        } else if (isXMAS) {
                          game = xmasMap[team];
                          isPicked = building.xmasPick?.team === team;
                          isBlockedElsewhere = isUsed && !isPicked;
                        } else {
                          const wk = col as number;
                          game = teamWeekMap[team]?.[wk];
                          isPicked = building.picks[wk]?.team === team;
                          isBlockedElsewhere = isUsed && !isPicked;
                        }

                        const activeAccent = accentCol ?? building.color;

                        if (!game) {
                          return (
                            <td key={String(col)} style={{ padding: 0, textAlign: 'center', borderRight: `1px solid ${BORDER}` }}>
                              <div style={{ padding: '10px 4px', fontSize: '0.5rem', color: MUTED + '60' }}>—</div>
                            </td>
                          );
                        }

                        const col2 = wpColor(game.wp);

                        return (
                          <td key={String(col)} style={{
                            padding: 0, textAlign: 'center',
                            borderRight: `1px solid ${(isTHK || isXMAS) ? accentCol + '40' : BORDER}`,
                            background: isPicked ? activeAccent + '25' : (isTHK ? YELLOW + '06' : isXMAS ? RED + '05' : 'transparent'),
                            borderBottom: isPicked ? `2px solid ${activeAccent}` : '2px solid transparent',
                          }}>
                            <button
                              onClick={() => {
                                if (isBlockedElsewhere) return;
                                if (isTHK)       pickHoliday('thk',  team, game!.wp, game!.opp, game!.home, game!.label);
                                else if (isXMAS) pickHoliday('xmas', team, game!.wp, game!.opp, game!.home, game!.label);
                                else             pickTeam(col as number, team, game!.wp, game!.opp, game!.home, game!.label);
                              }}
                              disabled={isBlockedElsewhere}
                              title={`${team} vs ${game.opp} · ${Math.round(game.wp * 100)}% · ${game.label}`}
                              style={{
                                width: '100%', height: '100%', padding: '6px 4px',
                                background: 'transparent', border: 'none',
                                cursor: isBlockedElsewhere ? 'default' : 'pointer',
                                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
                              }}
                            >
                              {isPicked && <div style={{ fontSize: '0.45rem', color: activeAccent, fontWeight: 800, lineHeight: 1 }}>✓</div>}
                              <div style={{ fontSize: '0.65rem', fontWeight: 700, color: isPicked ? activeAccent : col2 }}>
                                {Math.round(game.wp * 100)}%
                              </div>
                              <div style={{ fontSize: '0.45rem', color: MUTED }}>
                                {game.home ? 'vs' : '@'}{game.opp}
                              </div>
                            </button>
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 16, marginTop: 10, flexWrap: 'wrap', fontSize: '0.6rem', color: MUTED }}>
          {[['73%+', EMERALD, 'GREAT'], ['58–72%', BLUE, 'GOOD'], ['45–57%', YELLOW, 'LEAN'], ['<45%', RED, 'TOUGH']].map(([range, color, label]) => (
            <div key={String(label)} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <div style={{ width: 8, height: 8, borderRadius: 2, background: color as string }} />
              <span>{range} — {label}</span>
            </div>
          ))}
          <span style={{ marginLeft: 8 }}>· Click to pick · Click again to deselect · Click week header to sort</span>
        </div>
      </div>
    );
  }

  // ── SIDEBAR MODE ───────────────────────────────────────────────────────────
  const allSidebarWeeks: (number | HolidaySlot)[] = [];
  for (const wk of weekNums) {
    if (wk === 12 && thkGames.length > 0)  allSidebarWeeks.push('thk');
    if (wk === 16 && xmasGames.length > 0) allSidebarWeeks.push('xmas');
    allSidebarWeeks.push(wk);
  }

  const currentGames: SurvivorGame[] =
    activeWeek === 'thk'  ? thkGames  :
    activeWeek === 'xmas' ? xmasGames :
    weeks[activeWeek as number] ?? [];

  const currentPick: SurvivorPick | null =
    activeWeek === 'thk'  ? building.thkPick  :
    activeWeek === 'xmas' ? building.xmasPick :
    building.picks[activeWeek as number] ?? null;

  const isHolidayActive = activeWeek === 'thk' || activeWeek === 'xmas';
  const activeAccent    = activeWeek === 'thk' ? YELLOW : activeWeek === 'xmas' ? RED : building.color;

  return (
    <div>
      {BuilderHeader}
      {SaveBanner}

      <div style={{ display: 'grid', gridTemplateColumns: '160px 1fr', gap: 16 }}>
        {/* Week sidebar */}
        <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 10, padding: 10, alignSelf: 'start' }}>
          <div style={{ fontSize: '0.58rem', color: MUTED, letterSpacing: '0.08em', marginBottom: 8 }}>SELECT WEEK</div>
          {allSidebarWeeks.map(slot => {
            const isTHK  = slot === 'thk';
            const isXMAS = slot === 'xmas';
            const slotAccent = isTHK ? YELLOW : isXMAS ? RED : building.color;
            const slotPick: SurvivorPick | null =
              isTHK  ? building.thkPick  :
              isXMAS ? building.xmasPick :
              building.picks[slot as number] ?? null;
            const isActive = activeWeek === slot;
            return (
              <button key={String(slot)} onClick={() => setActiveWeek(slot)} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                width: '100%', background: isActive ? slotAccent + '18' : 'transparent',
                border: `1px solid ${isActive ? slotAccent : 'transparent'}`,
                borderRadius: 5, padding: '5px 7px', cursor: 'pointer', color: FG,
                fontSize: '0.7rem', marginBottom: 2,
              }}>
                <span style={{ fontWeight: isActive ? 700 : 400, color: isTHK ? YELLOW : isXMAS ? RED : FG }}>
                  {isTHK ? '🦃 THK' : isXMAS ? '🎄 XMS' : `Wk ${slot}`}
                </span>
                {slotPick && (
                  <img src={logo(slotPick.team)} alt={slotPick.team}
                    style={{ width: 16, height: 16 }}
                    onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                )}
              </button>
            );
          })}
        </div>

        {/* Game picker */}
        <div>
          <div style={{ fontWeight: 700, fontFamily: 'Nunito', fontSize: '0.95rem', marginBottom: 12 }}>
            {activeWeek === 'thk' ? '🦃 Thanksgiving Pick' : activeWeek === 'xmas' ? '🎄 Christmas Pick' : `Week ${activeWeek}`}
            {isHolidayActive && (
              <span style={{ fontSize: '0.65rem', color: activeAccent, fontWeight: 400, marginLeft: 8 }}>mandatory separate pick</span>
            )}
            {currentPick && (
              <span style={{ fontSize: '0.68rem', color: activeAccent, fontWeight: 400, marginLeft: 10 }}>
                ✓ {currentPick.team} selected
              </span>
            )}
          </div>
          <div style={{ display: 'grid', gap: 8 }}>
            {currentGames.map((g, i) => {
              const sides = [
                { team: g.home, wp: g.home_wp, opp: g.away, home: true,  label: g.home_label },
                { team: g.away, wp: g.away_wp, opp: g.home, home: false, label: g.away_label },
              ];
              return (
                <div key={i} style={{
                  background: PANEL,
                  border: `1px solid ${(currentPick?.team === g.home || currentPick?.team === g.away) ? activeAccent + '70' : BORDER}`,
                  borderRadius: 8, padding: '10px 14px',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    {sides.map((side, si) => {
                      const isPick = currentPick?.team === side.team;
                      const isUsed = usedInPath.has(side.team) && !isPick;
                      const col    = LABEL_COLOR[side.label] ?? MUTED;
                      return (
                        <button key={si}
                          onClick={() => {
                            if (isUsed) return;
                            if (activeWeek === 'thk')       pickHoliday('thk',  side.team, side.wp, side.opp, side.home, side.label);
                            else if (activeWeek === 'xmas') pickHoliday('xmas', side.team, side.wp, side.opp, side.home, side.label);
                            else                            pickTeam(activeWeek as number, side.team, side.wp, side.opp, side.home, side.label);
                          }}
                          disabled={isUsed}
                          style={{
                            flex: 1, background: isPick ? activeAccent + '18' : 'transparent',
                            border: `1px solid ${isPick ? activeAccent : 'transparent'}`,
                            borderRadius: 6, padding: '8px 10px',
                            cursor: isUsed ? 'default' : 'pointer',
                            textAlign: si === 0 ? 'left' : 'right', opacity: isUsed ? 0.35 : 1,
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexDirection: si === 0 ? 'row' : 'row-reverse' }}>
                            <img src={logo(side.team)} alt={side.team} style={{ width: 28, height: 28, flexShrink: 0 }} onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                            <div>
                              <div style={{ fontWeight: 700, fontSize: '0.82rem', color: FG, fontFamily: 'Nunito' }}>
                                {side.team}
                                {isPick && <span style={{ fontSize: '0.55rem', color: activeAccent, marginLeft: 4 }}>✓</span>}
                                {isUsed && <span style={{ fontSize: '0.52rem', color: RED, marginLeft: 4 }}>USED</span>}
                              </div>
                              <div style={{ fontSize: '0.6rem', fontWeight: 700, color: col }}>
                                {Math.round(side.wp * 100)}% · {side.label}
                              </div>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                    <div style={{ padding: '0 8px', color: MUTED, fontSize: '0.75rem', flexShrink: 0 }}>@</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
