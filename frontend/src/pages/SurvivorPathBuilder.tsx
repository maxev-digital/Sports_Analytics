/**
 * SurvivorPathBuilder — "MY PATHS" tab for the Survivor Helper.
 * Grid mode: team × week matrix with sortable headers and separate THK/XMAS columns.
 * Sidebar mode: week-by-week game picker.
 */
import { useState, useMemo } from 'react';
import { CUSTOM_PATH_COLORS, type SurvivorGame, type SurvivorPick, type CustomPath } from './survivorAlgo';
import { logo, wpColor, COLORS, WP_LABEL_COLOR, withAlpha } from './survivorUtils';

const { EMERALD, RED, YELLOW, BLUE } = COLORS;

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

  const gridCols = useMemo<GridCol[]>(() => {
    const cols: GridCol[] = [];
    for (const wk of weekNums) {
      if (wk === 12 && thkGames.length > 0)  cols.push('thk');
      if (wk === 16 && xmasGames.length > 0) cols.push('xmas');
      cols.push(wk);
    }
    return cols;
  }, [weekNums, thkGames.length, xmasGames.length]);

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

  const allTeams = useMemo(() => Object.keys(teamWeekMap).sort(), [teamWeekMap]);

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
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-[0.7rem] font-extrabold text-fg tracking-[0.06em]">MY CUSTOM PATHS</div>
            <div className="text-[0.62rem] text-muted mt-0.5">
              Build season-long pick sequences including Thanksgiving and Christmas picks.
            </div>
          </div>
          <button
            onClick={startNew}
            className="text-[0.7rem] font-extrabold py-2 px-4 rounded-md cursor-pointer shrink-0"
            style={{ background: withAlpha(BLUE, 0.13), border: `1px solid ${BLUE}`, color: BLUE }}
          >
            + NEW PATH
          </button>
        </div>

        {customPaths.length === 0 && (
          <div className="text-center py-12 px-6 bg-panel border border-ev-border border-dashed rounded-[10px] text-[0.72rem] text-muted">
            No custom paths yet. Click <strong className="text-fg">+ NEW PATH</strong> to build your first season-long pick sequence.
          </div>
        )}

        <div className="grid gap-3">
          {customPaths.map(path => {
            const sp = survivalProbPath(path);
            const pickCount = Object.keys(path.picks).length
              + (path.thkPick ? 1 : 0) + (path.xmasPick ? 1 : 0);
            return (
              <div
                key={path.id}
                className="rounded-lg py-[14px] px-4"
                style={{
                  background: 'var(--c-panel)',
                  border: `1px solid ${withAlpha(path.color, 0.25)}`,
                  borderLeft: `3px solid ${path.color}`,
                }}
              >
                <div className="flex items-start justify-between mb-[10px]">
                  <div>
                    <div className="font-extrabold text-[0.85rem] font-[Nunito]" style={{ color: path.color }}>
                      {path.name}
                    </div>
                    <div className="text-[0.62rem] text-muted mt-0.5">
                      {pickCount} / {totalSlots} slots picked · joint survival {(sp * 100).toFixed(2)}%
                    </div>
                  </div>
                  <div className="flex gap-1.5 shrink-0 ml-3">
                    <button
                      onClick={() => startEdit(path)}
                      className="text-[0.62rem] font-bold py-1 px-[10px] rounded-[5px] cursor-pointer bg-transparent text-muted border border-ev-border"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => deletePath(path.id)}
                      className="text-[0.62rem] font-bold py-1 px-[10px] rounded-[5px] cursor-pointer bg-transparent"
                      style={{ border: `1px solid ${withAlpha(RED, 0.31)}`, color: RED }}
                    >
                      Delete
                    </button>
                  </div>
                </div>

                {/* Pick timeline — bordered table */}
                <div className="overflow-x-auto mt-1">
                  <table className="border-collapse" style={{ minWidth: 'max-content' }}>
                    <thead>
                      <tr>
                        {weekNums.map(wk => {
                          const isThkWk  = wk === 12 && thkGames.length > 0;
                          const isXmasWk = wk === 16 && xmasGames.length > 0;
                          return (
                            <>
                              {isThkWk && (
                                <th
                                  key="thk-h"
                                  className="py-[5px] px-1.5 text-center min-w-[64px] text-[0.6rem] font-extrabold"
                                  style={{ border: `1px solid ${withAlpha(YELLOW, 0.31)}`, background: withAlpha(YELLOW, 0.09), color: YELLOW }}
                                >
                                  🦃 THK
                                </th>
                              )}
                              {isXmasWk && (
                                <th
                                  key="xmas-h"
                                  className="py-[5px] px-1.5 text-center min-w-[64px] text-[0.6rem] font-extrabold"
                                  style={{ border: `1px solid ${withAlpha(RED, 0.25)}`, background: withAlpha(RED, 0.07), color: RED }}
                                >
                                  🎄 XMS
                                </th>
                              )}
                              <th
                                key={wk}
                                className="py-[5px] px-2 text-center min-w-[64px] text-[0.6rem] font-bold"
                                style={{
                                  border: '1px solid var(--c-border)',
                                  background: path.picks[wk] ? withAlpha(path.color, 0.08) : 'transparent',
                                  color: path.picks[wk] ? path.color : 'var(--c-muted)',
                                }}
                              >
                                WK{wk}
                              </th>
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
                                  <td
                                    key="thk-b"
                                    className="py-2 px-1.5 text-center align-middle"
                                    style={{
                                      border: `1px solid ${withAlpha(YELLOW, 0.31)}`,
                                      background: p ? withAlpha(YELLOW, 0.06) : 'transparent',
                                    }}
                                  >
                                    {p ? (
                                      <>
                                        <img src={logo(p.team)} alt={p.team} className="w-[30px] h-[30px] block mx-auto mb-1" onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                                        <div className="text-[0.65rem] font-extrabold" style={{ color: YELLOW }}>{p.team}</div>
                                        <div className="text-[0.6rem] text-muted">{Math.round(p.wp * 100)}%</div>
                                      </>
                                    ) : (
                                      <span className="text-[0.6rem] text-muted">—</span>
                                    )}
                                  </td>
                                );
                              })()}
                              {isXmasWk && (() => {
                                const p = path.xmasPick;
                                return (
                                  <td
                                    key="xmas-b"
                                    className="py-2 px-1.5 text-center align-middle"
                                    style={{
                                      border: `1px solid ${withAlpha(RED, 0.25)}`,
                                      background: p ? withAlpha(RED, 0.05) : 'transparent',
                                    }}
                                  >
                                    {p ? (
                                      <>
                                        <img src={logo(p.team)} alt={p.team} className="w-[30px] h-[30px] block mx-auto mb-1" onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                                        <div className="text-[0.65rem] font-extrabold" style={{ color: RED }}>{p.team}</div>
                                        <div className="text-[0.6rem] text-muted">{Math.round(p.wp * 100)}%</div>
                                      </>
                                    ) : (
                                      <span className="text-[0.6rem] text-muted">—</span>
                                    )}
                                  </td>
                                );
                              })()}
                              {(() => {
                                const p = path.picks[wk];
                                return (
                                  <td
                                    key={wk}
                                    className="py-2 px-1.5 text-center align-middle"
                                    style={{
                                      border: '1px solid var(--c-border)',
                                      background: p ? withAlpha(path.color, 0.06) : 'transparent',
                                    }}
                                  >
                                    {p ? (
                                      <>
                                        <img src={logo(p.team)} alt={p.team} className="w-[30px] h-[30px] block mx-auto mb-1" onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                                        <div className="text-[0.65rem] font-extrabold text-fg">{p.team}</div>
                                        <div className="text-[0.6rem] font-bold" style={{ color: WP_LABEL_COLOR[p.label] ?? 'var(--c-muted)' }}>
                                          {Math.round(p.wp * 100)}%
                                        </div>
                                      </>
                                    ) : (
                                      <span className="text-[0.6rem] text-muted">—</span>
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
    <div className="flex flex-col gap-[10px] mb-4">
      <div className="flex items-center gap-[10px] flex-wrap">
        <input
          value={nameInput}
          onChange={e => setNameInput(e.target.value)}
          placeholder="Path name (e.g. My Circa Entry)"
          className="flex-1 min-w-[200px] py-2 px-3 rounded-md text-[0.82rem] font-bold font-[Nunito] bg-panel border border-ev-border text-fg"
        />
        <div className="flex gap-[5px] items-center">
          {CUSTOM_PATH_COLORS.map((c, i) => (
            <button
              key={i}
              onClick={() => setBuilding(b => b ? { ...b, color: c } : b)}
              className="w-5 h-5 rounded-full cursor-pointer"
              style={{
                background: c,
                border: building.color === c ? '3px solid var(--c-fg)' : '2px solid transparent',
              }}
            />
          ))}
        </div>
        <div className="flex bg-track rounded-md p-[2px]">
          {(['grid', 'sidebar'] as const).map(mode => (
            <button
              key={mode}
              onClick={() => setBuilderMode(mode)}
              className="py-[5px] px-[11px] rounded-[5px] cursor-pointer text-[0.65rem] font-bold"
              style={{
                background: builderMode === mode ? 'var(--c-panel)' : 'transparent',
                border: builderMode === mode ? '1px solid var(--c-border)' : '1px solid transparent',
                color: builderMode === mode ? 'var(--c-fg)' : 'var(--c-muted)',
              }}
            >
              {mode === 'grid' ? 'GRID' : 'SIDEBAR'}
            </button>
          ))}
        </div>
        <button
          onClick={cancelBuild}
          className="text-[0.68rem] font-bold py-[7px] px-3 rounded-md cursor-pointer bg-transparent border border-ev-border text-muted"
        >
          Cancel
        </button>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex-1 h-1 bg-track rounded-sm overflow-hidden">
          <div
            className="h-full rounded-sm transition-[width] duration-200 ease-in-out"
            style={{ background: building.color, width: `${(totalPicked / totalSlots) * 100}%` }}
          />
        </div>
        <div className="text-[0.62rem] text-muted whitespace-nowrap">
          {totalPicked}/{totalSlots} slots · joint survival{' '}
          <span className="font-bold" style={{ color: building.color }}>
            {(survivalProb(building) * 100).toFixed(2)}%
          </span>
        </div>
      </div>
    </div>
  );

  const SaveBanner = allFilled ? (
    <div
      className="flex items-center justify-between flex-wrap gap-3 rounded-[10px] py-[14px] px-5 mb-4"
      style={{
        background: withAlpha(building.color, 0.09),
        border: `1.5px solid ${building.color}`,
      }}
    >
      <div>
        <div className="font-extrabold text-[0.85rem] font-[Nunito]" style={{ color: building.color }}>
          ✓ All {totalSlots} slots picked
        </div>
        <div className="text-[0.62rem] text-muted mt-0.5">
          Joint survival: <strong style={{ color: building.color }}>{(survivalProb(building) * 100).toFixed(2)}%</strong>
          {!nameInput.trim() && <span className="ml-2" style={{ color: YELLOW }}>← enter a name to save</span>}
        </div>
      </div>
      <button
        onClick={savePath}
        disabled={!canSave}
        className="text-[0.78rem] font-extrabold py-[10px] px-6 rounded-lg"
        style={{
          cursor: canSave ? 'pointer' : 'default',
          background: canSave ? building.color : 'var(--c-muted)',
          border: `1px solid ${canSave ? building.color : 'var(--c-muted)'}`,
          color: canSave ? 'oklch(98% 0 0)' : 'var(--c-muted)',
        }}
      >
        Save Path
      </button>
    </div>
  ) : null;

  // ── GRID MODE ──────────────────────────────────────────────────────────────
  if (builderMode === 'grid') {
    return (
      <div>
        {BuilderHeader}
        {SaveBanner}

        <div className="bg-panel border border-ev-border rounded-[10px] overflow-hidden">
          <div className="overflow-x-auto overflow-y-auto max-h-[70vh]">
            <table className="border-collapse text-[0.68rem]" style={{ minWidth: 'max-content' }}>
              <thead>
                <tr>
                  <th
                    className="sticky left-0 top-0 z-[4] bg-panel border-r border-ev-border border-b border-ev-border py-2 px-3 text-left text-[0.58rem] text-muted font-bold tracking-[0.06em] min-w-[90px]"
                  >
                    TEAM
                  </th>

                  {gridCols.map(col => {
                    const isTHK    = col === 'thk';
                    const isXMAS   = col === 'xmas';
                    const isHoliday = isTHK || isXMAS;
                    const isActive  = sortState?.col === col;
                    const indicator = isActive ? (sortState!.dir === 'desc' ? ' ▼' : ' ▲') : '';
                    const accent    = isTHK ? YELLOW : isXMAS ? RED : undefined;

                    let colPick: SurvivorPick | null = null;
                    if (isTHK)       colPick = building.thkPick;
                    else if (isXMAS) colPick = building.xmasPick;
                    else             colPick = building.picks[col as number] ?? null;

                    return (
                      <th
                        key={String(col)}
                        onClick={() => cycleSort(col)}
                        className="sticky top-0 z-[3] py-1.5 px-1 text-center text-[0.58rem] font-bold tracking-[0.04em] min-w-[58px] cursor-pointer select-none"
                        style={{
                          background: colPick
                            ? (isHoliday ? withAlpha(accent ?? YELLOW, 0.14) : withAlpha(building.color, 0.13))
                            : isActive ? 'var(--c-rowsel)' : isHoliday ? withAlpha(accent ?? YELLOW, 0.06) : 'var(--c-panel)',
                          borderBottom: `2px solid ${colPick ? (accent ?? building.color) : isActive ? 'var(--c-fg)' : 'var(--c-border)'}`,
                          borderRight: `1px solid ${isHoliday ? withAlpha(accent ?? YELLOW, 0.31) : 'var(--c-border)'}`,
                          color: colPick ? (accent ?? building.color) : isActive ? 'var(--c-fg)' : 'var(--c-muted)',
                        }}
                      >
                        <div>{isTHK ? `🦃THK${indicator}` : isXMAS ? `🎄XMS${indicator}` : `WK${col}${indicator}`}</div>
                        {colPick && (
                          <img
                            src={logo(colPick.team)} alt={colPick.team}
                            className="w-[18px] h-[18px] mx-auto mt-0.5 block"
                            onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                          />
                        )}
                      </th>
                    );
                  })}
                </tr>
              </thead>

              <tbody>
                {sortedTeams.map((team, rowIdx) => {
                  const isUsed = usedInPath.has(team);
                  const pickedSlot = building.thkPick?.team === team ? 'THK'
                    : building.xmasPick?.team === team ? 'XMAS'
                    : Object.entries(building.picks).find(([, p]) => p.team === team)?.[0];

                  return (
                    <tr
                      key={team}
                      className={isUsed ? 'opacity-50' : ''}
                      style={{ background: rowIdx % 2 === 0 ? 'transparent' : 'var(--c-rowsel)' }}
                    >
                      <td
                        className="sticky left-0 z-[2] border-r border-ev-border py-1 px-[10px] whitespace-nowrap"
                        style={{ background: rowIdx % 2 === 0 ? 'var(--c-panel)' : 'var(--c-pathbg, var(--c-panel))' }}
                      >
                        <div className="flex items-center gap-[7px]">
                          <img
                            src={logo(team)} alt={team}
                            className="w-[22px] h-[22px] shrink-0"
                            style={{ filter: isUsed ? 'grayscale(80%)' : 'none' }}
                            onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                          />
                          <div>
                            <div className="font-bold text-[0.72rem]" style={{ color: isUsed ? 'var(--c-muted)' : 'var(--c-fg)' }}>
                              {team}
                            </div>
                            {isUsed && pickedSlot && (
                              <div className="text-[0.5rem] font-bold" style={{ color: building.color }}>
                                {pickedSlot} ✓
                              </div>
                            )}
                          </div>
                        </div>
                      </td>

                      {gridCols.map(col => {
                        const isTHK  = col === 'thk';
                        const isXMAS = col === 'xmas';
                        const accent = isTHK ? YELLOW : isXMAS ? RED : undefined;

                        let game: { wp: number; opp: string; home: boolean; label: string } | undefined;
                        let isPicked = false;
                        let isBlocked = false;

                        if (isTHK) {
                          game = thkMap[team];
                          isPicked = building.thkPick?.team === team;
                          isBlocked = isUsed && !isPicked;
                        } else if (isXMAS) {
                          game = xmasMap[team];
                          isPicked = building.xmasPick?.team === team;
                          isBlocked = isUsed && !isPicked;
                        } else {
                          game = teamWeekMap[team]?.[col as number];
                          isPicked = building.picks[col as number]?.team === team;
                          isBlocked = isUsed && !isPicked;
                        }

                        const activeAccent = accent ?? building.color;

                        if (!game) {
                          return (
                            <td key={String(col)} className="p-0 text-center border-r border-ev-border">
                              <div className="py-[10px] px-1 text-[0.5rem] text-muted">—</div>
                            </td>
                          );
                        }

                        const wpCol = wpColor(game.wp);

                        return (
                          <td
                            key={String(col)}
                            className="p-0 text-center"
                            style={{
                              borderRight: `1px solid ${(isTHK || isXMAS) ? withAlpha(accent ?? YELLOW, 0.25) : 'var(--c-border)'}`,
                              background: isPicked ? withAlpha(activeAccent, 0.14) : isTHK ? withAlpha(YELLOW, 0.04) : isXMAS ? withAlpha(RED, 0.03) : 'transparent',
                              borderBottom: isPicked ? `2px solid ${activeAccent}` : '2px solid transparent',
                            }}
                          >
                            <button
                              onClick={() => {
                                if (isBlocked) return;
                                if (isTHK)       pickHoliday('thk',  team, game!.wp, game!.opp, game!.home, game!.label);
                                else if (isXMAS) pickHoliday('xmas', team, game!.wp, game!.opp, game!.home, game!.label);
                                else             pickTeam(col as number, team, game!.wp, game!.opp, game!.home, game!.label);
                              }}
                              disabled={isBlocked}
                              title={`${team} vs ${game.opp} · ${Math.round(game.wp * 100)}% · ${game.label}`}
                              className="w-full h-full py-1.5 px-1 flex flex-col items-center gap-0.5"
                              style={{
                                background: 'transparent',
                                border: 'none',
                                cursor: isBlocked ? 'default' : 'pointer',
                              }}
                            >
                              {isPicked && <div className="text-[0.45rem] font-extrabold leading-none" style={{ color: activeAccent }}>✓</div>}
                              <div className="text-[0.65rem] font-bold" style={{ color: isPicked ? activeAccent : wpCol }}>
                                {Math.round(game.wp * 100)}%
                              </div>
                              <div className="text-[0.45rem] text-muted">
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

        <div className="flex gap-4 mt-[10px] flex-wrap text-[0.6rem] text-muted">
          {[['73%+', EMERALD, 'GREAT'], ['58–72%', BLUE, 'GOOD'], ['45–57%', YELLOW, 'LEAN'], ['<45%', RED, 'TOUGH']].map(([range, color, label]) => (
            <div key={String(label)} className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-[2px]" style={{ background: color as string }} />
              <span>{range} — {label}</span>
            </div>
          ))}
          <span className="ml-2">· Click to pick · Click again to deselect · Click week header to sort</span>
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

      <div className="grid gap-4" style={{ gridTemplateColumns: '160px 1fr' }}>
        {/* Week sidebar */}
        <div className="bg-panel border border-ev-border rounded-[10px] p-[10px] self-start">
          <div className="text-[0.58rem] text-muted tracking-[0.08em] mb-2">SELECT WEEK</div>
          {allSidebarWeeks.map(slot => {
            const isTHK    = slot === 'thk';
            const isXMAS   = slot === 'xmas';
            const slotAccent = isTHK ? YELLOW : isXMAS ? RED : building.color;
            const slotPick: SurvivorPick | null =
              isTHK  ? building.thkPick  :
              isXMAS ? building.xmasPick :
              building.picks[slot as number] ?? null;
            const isActive = activeWeek === slot;
            return (
              <button
                key={String(slot)}
                onClick={() => setActiveWeek(slot)}
                className="flex items-center justify-between w-full rounded-[5px] py-[5px] px-[7px] cursor-pointer text-fg text-[0.7rem] mb-0.5"
                style={{
                  background: isActive ? withAlpha(slotAccent, 0.09) : 'transparent',
                  border: `1px solid ${isActive ? slotAccent : 'transparent'}`,
                }}
              >
                <span
                  style={{
                    fontWeight: isActive ? 700 : 400,
                    color: isTHK ? YELLOW : isXMAS ? RED : 'var(--c-fg)',
                  }}
                >
                  {isTHK ? '🦃 THK' : isXMAS ? '🎄 XMS' : `Wk ${slot}`}
                </span>
                {slotPick && (
                  <img
                    src={logo(slotPick.team)} alt={slotPick.team}
                    className="w-4 h-4"
                    onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                  />
                )}
              </button>
            );
          })}
        </div>

        {/* Game picker */}
        <div>
          <div className="font-bold font-[Nunito] text-[0.95rem] text-fg mb-3">
            {activeWeek === 'thk' ? '🦃 Thanksgiving Pick' : activeWeek === 'xmas' ? '🎄 Christmas Pick' : `Week ${activeWeek}`}
            {isHolidayActive && (
              <span className="text-[0.65rem] font-normal ml-2" style={{ color: activeAccent }}>mandatory separate pick</span>
            )}
            {currentPick && (
              <span className="text-[0.68rem] font-normal ml-[10px]" style={{ color: activeAccent }}>
                ✓ {currentPick.team} selected
              </span>
            )}
          </div>
          <div className="grid gap-2">
            {currentGames.map((g, i) => {
              const sides = [
                { team: g.home, wp: g.home_wp, opp: g.away, home: true,  label: g.home_label },
                { team: g.away, wp: g.away_wp, opp: g.home, home: false, label: g.away_label },
              ];
              return (
                <div
                  key={i}
                  className="bg-panel rounded-lg py-[10px] px-[14px]"
                  style={{
                    border: `1px solid ${(currentPick?.team === g.home || currentPick?.team === g.away) ? withAlpha(activeAccent, 0.44) : 'var(--c-border)'}`,
                  }}
                >
                  <div className="flex items-center">
                    {sides.map((side, si) => {
                      const isPick = currentPick?.team === side.team;
                      const isUsed = usedInPath.has(side.team) && !isPick;
                      const col    = WP_LABEL_COLOR[side.label] ?? 'var(--c-muted)';
                      return (
                        <button
                          key={si}
                          onClick={() => {
                            if (isUsed) return;
                            if (activeWeek === 'thk')       pickHoliday('thk',  side.team, side.wp, side.opp, side.home, side.label);
                            else if (activeWeek === 'xmas') pickHoliday('xmas', side.team, side.wp, side.opp, side.home, side.label);
                            else                            pickTeam(activeWeek as number, side.team, side.wp, side.opp, side.home, side.label);
                          }}
                          disabled={isUsed}
                          className="flex-1 rounded-md py-2 px-[10px]"
                          style={{
                            background: isPick ? withAlpha(activeAccent, 0.09) : 'transparent',
                            border: `1px solid ${isPick ? activeAccent : 'transparent'}`,
                            cursor: isUsed ? 'default' : 'pointer',
                            textAlign: si === 0 ? 'left' : 'right',
                            opacity: isUsed ? 0.35 : 1,
                          }}
                        >
                          <div
                            className="flex items-center gap-2"
                            style={{ flexDirection: si === 0 ? 'row' : 'row-reverse' }}
                          >
                            <img
                              src={logo(side.team)} alt={side.team}
                              className="w-7 h-7 shrink-0"
                              onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                            />
                            <div>
                              <div className="font-bold text-[0.82rem] text-fg font-[Nunito]">
                                {side.team}
                                {isPick && <span className="text-[0.55rem] ml-1" style={{ color: activeAccent }}>✓</span>}
                                {isUsed && <span className="text-[0.52rem] ml-1" style={{ color: RED }}>USED</span>}
                              </div>
                              <div className="text-[0.6rem] font-bold" style={{ color: col }}>
                                {Math.round(side.wp * 100)}% · {side.label}
                              </div>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                    <div className="px-2 text-muted text-[0.75rem] shrink-0">@</div>
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
