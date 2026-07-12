import { useState, useEffect, useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, ReferenceLine,
} from 'recharts';
import '../styles/analytics.css';
import { getApiUrl } from '../config';

type Sport = 'mlb' | 'nba' | 'wnba' | 'nfl' | 'nhl' | 'ncaab' | 'ncaaf';
type SortDir = 'asc' | 'desc';

interface TeamRow {
  rank: number;
  team: string;
  abbr: string;
  logo: string;
  color: string;
  division: string;
  wins: number;
  losses: number;
  ties: number;
  pct: number;
  gamesBehind: number;
  pointsFor: number;
  pointsAgainst: number;
  differential: number;
  homeRecord: string;
  awayRecord: string;
  streak: string;
  last10: string;
}

const SPORTS: { key: Sport; label: string }[] = [
  { key: 'mlb',   label: 'MLB' },
  { key: 'nba',   label: 'NBA' },
  { key: 'wnba',  label: 'WNBA' },
  { key: 'nfl',   label: 'NFL' },
  { key: 'nhl',   label: 'NHL' },
  { key: 'ncaab', label: 'NCAAB' },
  { key: 'ncaaf', label: 'NCAAF' },
];

const SPORT_LABELS: Record<Sport, { pts: string; pa: string }> = {
  mlb:   { pts: 'R/G',   pa: 'RA/G' },
  nba:   { pts: 'PPG',   pa: 'OPP PPG' },
  wnba:  { pts: 'PPG',   pa: 'OPP PPG' },
  nfl:   { pts: 'PF/G',  pa: 'PA/G' },
  nhl:   { pts: 'GF/G',  pa: 'GA/G' },
  ncaab: { pts: 'PPG',   pa: 'OPP PPG' },
  ncaaf: { pts: 'PF/G',  pa: 'PA/G' },
};

type SortKey = keyof TeamRow;

const BRAND_RED  = 'oklch(63.7% .237 25.331)';
const EMERALD    = 'oklch(69.6% .17 162.48)';
const MUTED_FG   = 'oklch(70.8% 0 0)';
const CARD_BG    = 'oklch(24% 0 0)';
const SIDEBAR_BG = 'oklch(20.5% 0 0)';
const BORDER     = 'oklch(100% 0 0 / .1)';

// Custom dark tooltip for Recharts
function DarkTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '10px 14px', fontSize: '0.78rem' }}>
      <p style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700, marginBottom: 4 }}>{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color || MUTED_FG, margin: '2px 0' }}>
          {p.name}: <strong>{typeof p.value === 'number' ? p.value.toFixed(2) : p.value}</strong>
        </p>
      ))}
    </div>
  );
}

function colorDiff(val: number) {
  if (val > 0.5)  return 'val-pos';
  if (val < -0.5) return 'val-neg';
  return 'val-neutral';
}

function colorPct(val: number) {
  if (val > 0.55) return 'val-pos';
  if (val < 0.45) return 'val-neg';
  return 'val-neutral';
}

function streakColor(s: string) {
  return s.startsWith('W') ? EMERALD : 'oklch(63.7% .237 25.331)';
}

export function TeamRankings() {
  const [sport, setSport]       = useState<Sport>('mlb');
  const [teams, setTeams]       = useState<TeamRow[]>([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState('');
  const [sortKey, setSortKey]   = useState<SortKey>('rank');
  const [sortDir, setSortDir]   = useState<SortDir>('asc');
  const [division, setDivision] = useState('ALL');
  const [view, setView]         = useState<'table' | 'chart'>('table');

  const labels = SPORT_LABELS[sport];

  useEffect(() => {
    setLoading(true);
    setError('');
    setDivision('ALL');
    setSortKey('rank');
    setSortDir('asc');

    fetch(getApiUrl(`analytics-data/standings/${sport}`))
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(data => {
        setTeams(data.teams || []);
        setLoading(false);
      })
      .catch(err => {
        setError('Could not load standings.');
        setLoading(false);
        console.error(err);
      });
  }, [sport]);

  const divisions = useMemo(() => {
    const divs = Array.from(new Set(teams.map(t => t.division).filter(Boolean)));
    return ['ALL', ...divs];
  }, [teams]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  };

  const sorted = useMemo(() => {
    let rows = division === 'ALL' ? [...teams] : teams.filter(t => t.division === division);
    rows.sort((a, b) => {
      const av = a[sortKey] as number | string;
      const bv = b[sortKey] as number | string;
      if (typeof av === 'number' && typeof bv === 'number')
        return sortDir === 'asc' ? av - bv : bv - av;
      return sortDir === 'asc'
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
    return rows;
  }, [teams, division, sortKey, sortDir]);

  // Top 10 for chart by differential
  const chartData = useMemo(() =>
    [...teams].sort((a, b) => b.differential - a.differential).slice(0, 15)
  , [teams]);

  const arrow = (key: SortKey) => (
    <span className={`sort-arrow${sortKey === key ? ' active' : ''}`}>
      {sortKey === key ? (sortDir === 'asc' ? ' ▲' : ' ▼') : ' ↕'}
    </span>
  );

  const thClass = (key: SortKey) => sortKey === key ? 'sorted' : '';

  const bestRecord = sorted.length > 0 ? `${sorted[0].wins}-${sorted[0].losses}` : '—';
  const bestDiff   = teams.length > 0 ? Math.max(...teams.map(t => t.differential)) : 0;
  const bestAbbr   = teams.find(t => t.differential === bestDiff)?.abbr ?? '—';
  const topTeam    = sorted[0]?.abbr ?? '—';

  return (
    <div className="analytics-page">

      {/* Header */}
      <div className="analytics-header">
        <h1>Team Rankings</h1>
        <p className="subtitle">Live standings, scoring differentials, and home/away splits</p>
        <div className="sport-tabs">
          {SPORTS.map(s => (
            <button
              key={s.key}
              className={`sport-tab${sport === s.key ? ' active' : ''}`}
              onClick={() => setSport(s.key)}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Filter bar */}
      <div className="filter-bar">
        <span className="filter-label">Division</span>
        {divisions.map(d => (
          <button
            key={d}
            className={`filter-pill${division === d ? ' active' : ''}`}
            onClick={() => setDivision(d)}
          >
            {d}
          </button>
        ))}

        {/* View toggle */}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
          <button
            className={`filter-pill${view === 'table' ? ' active' : ''}`}
            onClick={() => setView('table')}
          >
            Table
          </button>
          <button
            className={`filter-pill${view === 'chart' ? ' active' : ''}`}
            onClick={() => setView('chart')}
          >
            Chart
          </button>
        </div>
      </div>

      <div className="analytics-content">

        {/* Stat summary cards */}
        <div className="stat-cards">
          {[
            { val: topTeam,     label: '#1 ' + (division === 'ALL' ? 'Overall' : division) },
            { val: bestRecord,  label: 'Best Record' },
            { val: bestAbbr,    label: 'Best Differential' },
            { val: String(sorted.length), label: 'Teams' },
          ].map(c => (
            <div key={c.label} className="stat-card">
              <div className="stat-value">{c.val}</div>
              <div className="stat-label">{c.label}</div>
            </div>
          ))}
        </div>

        {/* Loading / error states */}
        {loading && (
          <div className="data-table-wrap" style={{ padding: '40px 0' }}>
            <div className="empty-state">
              <div className="skeleton" style={{ width: 200, margin: '0 auto 12px' }} />
              <div className="skeleton" style={{ width: 140, margin: '0 auto', height: 10 }} />
            </div>
          </div>
        )}

        {!loading && error && (
          <div className="data-table-wrap">
            <div className="empty-state">
              <h3>Data Unavailable</h3>
              <p>{error}</p>
            </div>
          </div>
        )}

        {/* CHART VIEW */}
        {!loading && !error && view === 'chart' && chartData.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* Run/Point Differential Bar Chart */}
            <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
              <p className="section-title" style={{ marginBottom: 16 }}>Scoring Differential — Top 15</p>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={BORDER} vertical={false} />
                  <XAxis
                    dataKey="abbr"
                    tick={{ fill: MUTED_FG, fontSize: 11, fontFamily: 'Nunito' }}
                    axisLine={{ stroke: BORDER }}
                    tickLine={false}
                    angle={-45}
                    textAnchor="end"
                    interval={0}
                  />
                  <YAxis
                    tick={{ fill: MUTED_FG, fontSize: 11, fontFamily: 'Nunito' }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={v => v > 0 ? `+${v}` : String(v)}
                  />
                  <Tooltip content={<DarkTooltip />} />
                  <ReferenceLine y={0} stroke={BORDER} strokeDasharray="4 4" />
                  <Bar dataKey="differential" name="Differential" radius={[3, 3, 0, 0]}>
                    {chartData.map(entry => (
                      <Cell
                        key={entry.abbr}
                        fill={entry.differential >= 0 ? EMERALD : BRAND_RED}
                        fillOpacity={0.85}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Win % Bar Chart */}
            <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
              <p className="section-title" style={{ marginBottom: 16 }}>Win Percentage — All Teams</p>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart
                  data={[...teams].sort((a, b) => b.pct - a.pct)}
                  margin={{ top: 4, right: 16, left: 0, bottom: 60 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={BORDER} vertical={false} />
                  <XAxis
                    dataKey="abbr"
                    tick={{ fill: MUTED_FG, fontSize: 11, fontFamily: 'Nunito' }}
                    axisLine={{ stroke: BORDER }}
                    tickLine={false}
                    angle={-45}
                    textAnchor="end"
                    interval={0}
                  />
                  <YAxis
                    domain={[0, 1]}
                    tick={{ fill: MUTED_FG, fontSize: 11, fontFamily: 'Nunito' }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={v => `${(v * 100).toFixed(0)}%`}
                  />
                  <Tooltip content={<DarkTooltip />} formatter={(v: number) => `${(v * 100).toFixed(1)}%`} />
                  <ReferenceLine y={0.5} stroke={BORDER} strokeDasharray="4 4" />
                  <Bar dataKey="pct" name="Win %" radius={[3, 3, 0, 0]}>
                    {[...teams].sort((a, b) => b.pct - a.pct).map(entry => (
                      <Cell
                        key={entry.abbr}
                        fill={entry.pct >= 0.5 ? EMERALD : BRAND_RED}
                        fillOpacity={0.85}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

          </div>
        )}

        {/* TABLE VIEW */}
        {!loading && !error && view === 'table' && (
          <div className="data-table-wrap">
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th onClick={() => toggleSort('rank')} className={thClass('rank')} style={{ width: 44 }}>#</th>
                    <th onClick={() => toggleSort('team')} className={thClass('team')} style={{ textAlign: 'left' }}>TEAM {arrow('team')}</th>
                    <th onClick={() => toggleSort('wins')} className={thClass('wins')}>W {arrow('wins')}</th>
                    <th onClick={() => toggleSort('losses')} className={thClass('losses')}>L {arrow('losses')}</th>
                    <th onClick={() => toggleSort('pct')} className={thClass('pct')}>PCT {arrow('pct')}</th>
                    <th onClick={() => toggleSort('gamesBehind')} className={thClass('gamesBehind')}>GB {arrow('gamesBehind')}</th>
                    <th onClick={() => toggleSort('pointsFor')} className={thClass('pointsFor')}>{labels.pts} {arrow('pointsFor')}</th>
                    <th onClick={() => toggleSort('pointsAgainst')} className={thClass('pointsAgainst')}>{labels.pa} {arrow('pointsAgainst')}</th>
                    <th onClick={() => toggleSort('differential')} className={thClass('differential')}>DIFF {arrow('differential')}</th>
                    <th>HOME</th>
                    <th>AWAY</th>
                    <th onClick={() => toggleSort('streak')} className={thClass('streak')}>STK {arrow('streak')}</th>
                    <th>L10</th>
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((row, i) => (
                    <tr key={row.team}>
                      <td>
                        <span className={`rank-badge${i < 5 ? ' top5' : ''}`}>{row.rank}</span>
                      </td>
                      <td>
                        <div className="team-cell">
                          {row.logo && (
                            <img
                              src={row.logo}
                              alt={row.abbr}
                              style={{ width: 22, height: 22, objectFit: 'contain', flexShrink: 0 }}
                              onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                            />
                          )}
                          <span className="team-abbr">{row.abbr}</span>
                          <span className="team-name">{row.team}</span>
                          {row.division && (
                            <span className="team-record">{row.division}</span>
                          )}
                        </div>
                      </td>
                      <td style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700 }}>{row.wins}</td>
                      <td>{row.losses}</td>
                      <td className={colorPct(row.pct)}>{row.pct.toFixed(3)}</td>
                      <td>{row.gamesBehind === 0 ? '—' : row.gamesBehind}</td>
                      <td>{row.pointsFor > 0 ? row.pointsFor.toFixed(2) : '—'}</td>
                      <td>{row.pointsAgainst > 0 ? row.pointsAgainst.toFixed(2) : '—'}</td>
                      <td className={colorDiff(row.differential)}>
                        {row.differential > 0 ? `+${row.differential.toFixed(2)}` : row.differential.toFixed(2)}
                      </td>
                      <td style={{ fontSize: '0.78rem' }}>{row.homeRecord || '—'}</td>
                      <td style={{ fontSize: '0.78rem' }}>{row.awayRecord || '—'}</td>
                      <td style={{ fontWeight: 700, color: streakColor(row.streak) }}>
                        {row.streak || '—'}
                      </td>
                      <td style={{ fontSize: '0.78rem' }}>{row.last10 || '—'}</td>
                    </tr>
                  ))}
                  {sorted.length === 0 && (
                    <tr>
                      <td colSpan={13} style={{ textAlign: 'center', padding: '40px', color: MUTED_FG }}>
                        No standings data available for {sport.toUpperCase()}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <p className="data-note">
          Updates every 5 minutes.
        </p>
      </div>
    </div>
  );
}
