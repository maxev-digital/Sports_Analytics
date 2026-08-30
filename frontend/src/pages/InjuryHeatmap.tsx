import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';
import '../styles/analytics.css';

const OFF_COLS = ['QB', 'OL', 'WR', 'RB'] as const;
const DEF_COLS = ['DL', 'LB', 'DB'] as const;
type Col = typeof OFF_COLS[number] | typeof DEF_COLS[number];

const BRAND_RED = 'oklch(63.7% .237 25.331)';
const ORANGE    = 'oklch(70.5% .213 47.604)';
const YELLOW    = 'oklch(79.5% .184 86.047)';
const MUTED_FG  = 'oklch(70.8% 0 0)';
const BORDER    = 'oklch(100% 0 0 / .1)';
const BLUE      = 'oklch(62.3% .214 259.815)';
const EMERALD   = 'oklch(69.6% .17 162.48)';

interface PlayerEntry {
  name: string;
  pos: string;
  group: string;
  status: string;
  comment: string;
}

interface GroupData {
  count: number;
  weight: number;
  players: PlayerEntry[];
}

interface TeamRow {
  team: string;
  team_name: string;
  groups: Record<Col, GroupData>;
  off_total: number;
  def_total: number;
  total_weight: number;
  players: PlayerEntry[];
}

interface HeatmapData {
  teams: TeamRow[];
  built_at: number;
}

function getLogo(abbr: string): string {
  const map: Record<string, string> = {
    ARI:'ari',ATL:'atl',BAL:'bal',BUF:'buf',CAR:'car',CHI:'chi',CIN:'cin',CLE:'cle',
    DAL:'dal',DEN:'den',DET:'det',GB:'gb',HOU:'hou',IND:'ind',JAX:'jax',KC:'kc',
    LAC:'lac',LAR:'lar',LV:'lv',MIA:'mia',MIN:'min',NE:'ne',NO:'no',NYG:'nyg',
    NYJ:'nyj',PHI:'phi',PIT:'pit',SEA:'sea',SF:'sf',TB:'tb',TEN:'ten',WSH:'wsh',
  };
  return `https://a.espncdn.com/i/teamlogos/nfl/500/${map[abbr] ?? abbr.toLowerCase()}.png`;
}

function nickname(teamName: string): string {
  return teamName.split(' ').slice(-1)[0];
}

function weightColor(val: number, high: number, mid: number): string {
  if (val > high) return BRAND_RED;
  if (val > mid)  return ORANGE;
  if (val > 0)    return YELLOW;
  return MUTED_FG;
}

function StatusBadge({ status }: { status: string }) {
  const s: Record<string, React.CSSProperties> = {
    Out:          { background: 'rgba(239,68,68,0.15)',  color: BRAND_RED, border: '1px solid rgba(239,68,68,0.3)' },
    Doubtful:     { background: 'rgba(249,115,22,0.15)', color: ORANGE,    border: '1px solid rgba(249,115,22,0.3)' },
    Questionable: { background: 'rgba(234,179,8,0.15)',  color: YELLOW,    border: '1px solid rgba(234,179,8,0.3)' },
    Probable:     { background: 'rgba(255,255,255,0.05)', color: MUTED_FG, border: `1px solid ${BORDER}` },
  };
  return (
    <span style={{
      fontSize: '0.6rem', padding: '1px 5px', borderRadius: 3,
      fontWeight: 700, flexShrink: 0, fontFamily: 'var(--d3-font)',
      ...(s[status] ?? { color: MUTED_FG }),
    }}>
      {status}
    </span>
  );
}

export function InjuryHeatmap() {
  const [data, setData]             = useState<HeatmapData | null>(null);
  const [loading, setLoading]       = useState(true);
  const [expanding, setExpanding]   = useState<string | null>(null);
  const [sortBy, setSortBy]         = useState<Col | 'off' | 'def' | 'total'>('total');
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = (refresh = false) => {
    setLoading(true);
    fetch(getApiUrl(`f5/injury-heatmap${refresh ? '?refresh=true' : ''}`))
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); setRefreshing(false); })
      .catch(() => { setLoading(false); setRefreshing(false); });
  };

  useEffect(() => { fetchData(); }, []);

  const sorted = (data?.teams ?? []).slice().sort((a, b) => {
    if (sortBy === 'total') return b.total_weight - a.total_weight;
    if (sortBy === 'off')   return b.off_total - a.off_total;
    if (sortBy === 'def')   return b.def_total - a.def_total;
    return (b.groups[sortBy as Col]?.weight ?? 0) - (a.groups[sortBy as Col]?.weight ?? 0);
  });

  // Normalize cell backgrounds against dataset max — same approach as /trends heatmap
  const maxCellWeight = Math.max(
    ...sorted.flatMap(t => [...OFF_COLS, ...DEF_COLS].map(c => t.groups[c]?.weight ?? 0)),
    1,
  );
  const cellBg = (weight: number) => {
    if (weight === 0) return 'transparent';
    const norm = weight / maxCellWeight;
    return `rgba(239,68,68,${(norm * 0.55).toFixed(2)})`;
  };

  const builtAt = data?.built_at
    ? new Date(data.built_at * 1000).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
    : null;

  // Exact same th style as /trends heatmap
  const thStyle = (col: string, extra?: React.CSSProperties): React.CSSProperties => ({
    padding: '6px 10px',
    textAlign: 'center',
    fontSize: '0.6rem',
    fontWeight: 700,
    letterSpacing: '0.1em',
    color: sortBy === col ? EMERALD : MUTED_FG,
    cursor: 'pointer',
    userSelect: 'none',
    whiteSpace: 'nowrap',
    borderBottom: `1px solid ${BORDER}`,
    fontFamily: 'var(--d3-font)',
    ...extra,
  });

  // Exact same data cell style as /trends heatmap
  const cell: React.CSSProperties = {
    padding: '5px 10px',
    textAlign: 'center',
    fontFamily: 'var(--d3-mono)',
    fontWeight: 600,
    fontSize: '0.75rem',
    color: 'var(--foreground)',
  };

  return (
    <div className="analytics-page">

      {/* Header — matches analytics-header exactly */}
      <div className="analytics-header">
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 3 }}>
              NFL 2026 · Live
            </div>
            <h1>Injury Heat Map</h1>
            <p className="subtitle">
              Per-team injury load by position group · Out=3, Doubtful=2, Questionable=1 · Click any row to expand
              {builtAt && <span style={{ marginLeft: 8, opacity: 0.6 }}>· Built {builtAt}</span>}
            </p>
          </div>
          <button
            onClick={() => { setRefreshing(true); fetchData(true); }}
            disabled={refreshing || loading}
            style={{
              padding: '6px 14px', borderRadius: 4, fontSize: '0.72rem', fontWeight: 700,
              fontFamily: 'var(--d3-font)', background: 'transparent',
              border: `1px solid ${BORDER}`, color: MUTED_FG,
              cursor: 'pointer', transition: 'all 0.15s',
              opacity: refreshing || loading ? 0.4 : 1,
              marginTop: 4,
            }}
          >
            {refreshing ? 'Refreshing…' : '↻ Refresh'}
          </button>
        </div>
      </div>

      {/* Filter bar — matches filter-bar exactly */}
      <div className="filter-bar">
        <span className="filter-label">SORT BY</span>
        {([
          ['total', 'TOTAL WT'],
          ['off',   'OFF TOT'],
          ['def',   'DEF TOT'],
          ['QB', 'QB'], ['OL', 'OL'], ['WR', 'WR'],
          ['RB', 'RB'], ['DL', 'DL'], ['LB', 'LB'], ['DB', 'DB'],
        ] as [Col | 'off' | 'def' | 'total', string][]).map(([key, label]) => (
          <button key={key} className={`filter-pill ${sortBy === key ? 'active' : ''}`} onClick={() => setSortBy(key)}>
            {label}
          </button>
        ))}
        <span style={{ marginLeft: 'auto', fontSize: '0.72rem', color: MUTED_FG }}>{sorted.length} teams</span>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '8px 24px', flexWrap: 'wrap', borderBottom: `1px solid ${BORDER}` }}>
        <span style={{ fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.08em', textTransform: 'uppercase' }}>Severity:</span>
        {[
          { bg: `rgba(239,68,68,${(0.15).toFixed(2)})`, label: 'Light (Q)' },
          { bg: `rgba(239,68,68,${(0.30).toFixed(2)})`, label: 'Moderate' },
          { bg: `rgba(239,68,68,${(0.45).toFixed(2)})`, label: 'Heavy' },
          { bg: `rgba(239,68,68,${(0.55).toFixed(2)})`, label: 'Rash' },
        ].map(l => (
          <div key={l.label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 14, height: 14, borderRadius: 2, background: l.bg, border: '1px solid rgba(255,255,255,0.08)' }} />
            <span style={{ fontSize: '0.72rem', color: MUTED_FG }}>{l.label}</span>
          </div>
        ))}
      </div>

      <div style={{ padding: '16px 24px 24px' }}>
        {loading ? (
          <div className="data-table-wrap" style={{ padding: 56, textAlign: 'center' }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%',
              border: `2px solid ${BRAND_RED}`, borderTopColor: 'transparent',
              animation: 'spin 0.8s linear infinite', margin: '0 auto 12px',
            }} />
            <div style={{ color: MUTED_FG, fontSize: '0.83rem' }}>Building heatmap — fetching all 32 teams from ESPN…</div>
            <div style={{ color: MUTED_FG, fontSize: '0.72rem', marginTop: 6, opacity: 0.6 }}>First load ~60s · Cached 6 hours</div>
          </div>
        ) : (
          <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
              <thead>
                {/* Section labels */}
                <tr>
                  <th style={{ ...thStyle(''), cursor: 'default', textAlign: 'left' }} />
                  <th colSpan={OFF_COLS.length + 1} style={{ ...thStyle(''), color: BLUE, borderBottom: `1px solid ${BLUE}40`, cursor: 'default' }}>
                    OFFENSE
                  </th>
                  <th colSpan={DEF_COLS.length + 1} style={{ ...thStyle(''), color: BRAND_RED, borderBottom: `1px solid ${BRAND_RED}40`, borderLeft: `1px solid ${BORDER}`, cursor: 'default' }}>
                    DEFENSE
                  </th>
                  <th style={{ ...thStyle(''), cursor: 'default', borderLeft: `1px solid ${BORDER}` }} />
                </tr>
                {/* Column headers */}
                <tr>
                  <th style={{ ...thStyle(''), textAlign: 'left', cursor: 'default', color: MUTED_FG }}>TEAM</th>
                  {OFF_COLS.map(col => (
                    <th key={col} style={thStyle(col)} onClick={() => setSortBy(col)}>{col}</th>
                  ))}
                  <th style={thStyle('off', { borderLeft: `1px solid ${BORDER}` })} onClick={() => setSortBy('off')}>TOT</th>
                  {DEF_COLS.map((col, ci) => (
                    <th key={col} style={thStyle(col, ci === 0 ? { borderLeft: `1px solid ${BORDER}` } : undefined)} onClick={() => setSortBy(col)}>{col}</th>
                  ))}
                  <th style={thStyle('def', { borderLeft: `1px solid ${BORDER}` })} onClick={() => setSortBy('def')}>TOT</th>
                  <th style={thStyle('total', { borderLeft: `1px solid ${BORDER}`, color: sortBy === 'total' ? EMERALD : 'var(--foreground)' })} onClick={() => setSortBy('total')}>WT ↕</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((team, idx) => {
                  const isOpen = expanding === team.team;
                  const evenBg = idx % 2 === 0 ? 'transparent' : 'oklch(100% 0 0 / .02)';
                  const rowBg  = isOpen ? 'var(--muted)' : evenBg;
                  return (
                    <>
                      <tr
                        key={team.team}
                        onClick={() => setExpanding(isOpen ? null : team.team)}
                        style={{ borderBottom: `1px solid ${BORDER}`, cursor: 'pointer', background: rowBg, transition: 'background 0.15s' }}
                        onMouseEnter={e => { e.currentTarget.style.background = 'var(--muted)'; }}
                        onMouseLeave={e => { e.currentTarget.style.background = rowBg; }}
                      >
                        {/* Team cell — matches /trends exactly: logo 15px + abbr bold + nickname muted */}
                        <td style={{ padding: '5px 10px', whiteSpace: 'nowrap' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <img
                              src={getLogo(team.team)} alt=""
                              style={{ width: 15, height: 15, objectFit: 'contain' }}
                              onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                            />
                            <span style={{ fontWeight: 700, color: 'var(--foreground)', fontSize: '0.78rem' }}>{team.team}</span>
                            <span style={{ color: MUTED_FG, fontSize: '0.6rem', fontFamily: 'var(--d3-mono)' }}>{nickname(team.team_name)}</span>
                          </div>
                        </td>

                        {/* Offense position cells */}
                        {OFF_COLS.map(col => {
                          const g = team.groups[col] ?? { count: 0, weight: 0 };
                          return (
                            <td key={col} style={{ ...cell, background: cellBg(g.weight) }}>
                              {g.count > 0 ? g.count : ''}
                            </td>
                          );
                        })}

                        {/* Offense total */}
                        <td style={{ ...cell, borderLeft: `1px solid ${BORDER}`, color: weightColor(team.off_total, 5, 2), fontWeight: 700 }}>
                          {team.off_total > 0 ? team.off_total : '—'}
                        </td>

                        {/* Defense position cells */}
                        {DEF_COLS.map((col, ci) => {
                          const g = team.groups[col] ?? { count: 0, weight: 0 };
                          return (
                            <td key={col} style={{ ...cell, background: cellBg(g.weight), borderLeft: ci === 0 ? `1px solid ${BORDER}` : undefined }}>
                              {g.count > 0 ? g.count : ''}
                            </td>
                          );
                        })}

                        {/* Defense total */}
                        <td style={{ ...cell, borderLeft: `1px solid ${BORDER}`, color: weightColor(team.def_total, 5, 2), fontWeight: 700 }}>
                          {team.def_total > 0 ? team.def_total : '—'}
                        </td>

                        {/* Total weight */}
                        <td style={{ ...cell, borderLeft: `1px solid ${BORDER}`, color: weightColor(team.total_weight, 15, 6), fontWeight: 700 }}>
                          {team.total_weight > 0 ? team.total_weight : '—'}
                        </td>
                      </tr>

                      {/* Expanded player detail */}
                      {isOpen && (
                        <tr key={`${team.team}-detail`}>
                          <td
                            colSpan={OFF_COLS.length + DEF_COLS.length + 4}
                            style={{ padding: '12px 18px', background: 'var(--muted)', borderBottom: `1px solid ${BORDER}` }}
                          >
                            <div style={{ fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>
                              {team.team_name} · {team.players.filter(p => p.status !== 'Probable').length} significant injuries
                            </div>
                            <div style={{ display: 'grid', gap: 4, gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' }}>
                              {team.players
                                .filter(p => p.status !== 'Probable')
                                .sort((a, b) => {
                                  const w: Record<string, number> = { Out: 3, Doubtful: 2, Questionable: 1 };
                                  return (w[b.status] ?? 0) - (w[a.status] ?? 0);
                                })
                                .map((p, i) => (
                                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '2px 0' }}>
                                    <span style={{ color: MUTED_FG, fontSize: '0.65rem', width: 24, textAlign: 'right', flexShrink: 0, fontFamily: 'var(--d3-mono)' }}>{p.pos}</span>
                                    <span style={{ color: 'var(--foreground)', fontSize: '0.78rem', fontWeight: 600, width: 130, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flexShrink: 0 }}>{p.name}</span>
                                    <StatusBadge status={p.status} />
                                    {p.comment && (
                                      <span style={{ color: MUTED_FG, fontSize: '0.7rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.comment.slice(0, 55)}</span>
                                    )}
                                  </div>
                                ))}
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        <p className="data-note">
          Source: ESPN sports.core.api.espn.com · Weight: Out=3, Doubtful=2, Questionable=1 · Click any team row to expand
        </p>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

export default InjuryHeatmap;
