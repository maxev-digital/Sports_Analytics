/**
 * Statcast Leaders — MLB expected stats from Baseball Savant.
 * Shows xwOBA, xBA, xSLG, barrel%, hard-hit%, exit velocity leaders.
 */
import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, ScatterChart, Scatter, ZAxis,
} from 'recharts';
import '../styles/analytics.css';
import { getApiUrl } from '../config';

const EMERALD   = 'oklch(69.6% .17 162.48)';
const BRAND_RED = 'oklch(63.7% .237 25.331)';
const BLUE      = 'oklch(62.3% .214 259.815)';
const YELLOW    = 'oklch(79.5% .184 86.047)';
const MUTED_FG  = 'oklch(70.8% 0 0)';
const BORDER    = 'oklch(100% 0 0 / .1)';
const SIDEBAR_BG = 'oklch(20.5% 0 0)';

type View = 'batting' | 'pitching';
type Stat = 'xwOBA' | 'xBA' | 'xSLG' | 'xwOBADiff';

const STAT_OPTIONS: { key: Stat; label: string; description: string }[] = [
  { key: 'xwOBA',     label: 'xwOBA',      description: 'Expected weighted on-base average — best single measure of hitting quality' },
  { key: 'xBA',       label: 'xBA',        description: 'Expected batting average based on exit velocity and launch angle' },
  { key: 'xSLG',      label: 'xSLG',       description: 'Expected slugging based on contact quality' },
  { key: 'xwOBADiff', label: 'xwOBA Diff',  description: 'Difference between actual and expected — positive = lucky, negative = unlucky' },
];

interface BatterRow {
  name: string;
  team: string;
  pa: number;
  ba: number;
  xBA: number;
  xBADiff: number;
  slg: number;
  xSLG: number;
  xSLGDiff: number;
  woba: number;
  xwOBA: number;
  xwOBADiff: number;
}

function DarkTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '10px 14px', fontSize: '0.78rem' }}>
      {label && <p style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700, marginBottom: 4 }}>{label}</p>}
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color || MUTED_FG, margin: '2px 0' }}>
          {p.name}: <strong>{typeof p.value === 'number' ? p.value.toFixed(3) : p.value}</strong>
        </p>
      ))}
    </div>
  );
}

export function Statcast() {
  const [view, setView] = useState<View>('batting');
  const [stat, setStat] = useState<Stat>('xwOBA');
  const [players, setPlayers] = useState<BatterRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [minPA, setMinPA] = useState(200);

  useEffect(() => {
    setLoading(true);
    const endpoint = view === 'batting'
      ? `analytics-data/statcast/batting?season=2026&min_pa=${minPA}`
      : `analytics-data/statcast/pitching?season=2026&min_pa=${minPA}`;

    fetch(getApiUrl(endpoint))
      .then(r => r.json())
      .then(d => {
        const list = d.players ?? d ?? [];
        const qualified = list.filter((p: BatterRow) => p.pa >= minPA);
        setPlayers(qualified);
      })
      .catch(() => setPlayers([]))
      .finally(() => setLoading(false));
  }, [view, minPA]);

  const sorted = [...players].sort((a, b) => {
    const av = (a as any)[stat] ?? 0;
    const bv = (b as any)[stat] ?? 0;
    return stat === 'xwOBADiff' ? av - bv : bv - av;  // Diff: most unlucky first (negative)
  });

  const top20 = stat === 'xwOBADiff'
    ? [...sorted.slice(0, 10), ...sorted.slice(-10).reverse()]  // Most unlucky + most lucky
    : sorted.slice(0, 20);

  const selectedStat = STAT_OPTIONS.find(s => s.key === stat);

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1>Statcast Leaders</h1>
        <p className="subtitle">MLB expected stats from Baseball Savant — contact quality metrics that predict future performance</p>

        <div className="sport-tabs" style={{ marginTop: 12 }}>
          <button className={`sport-tab ${view === 'batting' ? 'active' : ''}`} onClick={() => setView('batting')}>
            BATTING
          </button>
          <button className={`sport-tab ${view === 'pitching' ? 'active' : ''}`} onClick={() => setView('pitching')}>
            PITCHING
          </button>
        </div>
      </div>

      {/* Stat selector + filter */}
      <div className="filter-bar">
        <span className="filter-label">METRIC</span>
        {STAT_OPTIONS.map(s => (
          <button
            key={s.key}
            className={`filter-pill ${stat === s.key ? 'active' : ''}`}
            onClick={() => setStat(s.key)}
          >
            {s.label}
          </button>
        ))}
        <span className="filter-label" style={{ marginLeft: 16 }}>MIN PA</span>
        <select
          className="filter-select"
          value={minPA}
          onChange={e => setMinPA(Number(e.target.value))}
        >
          <option value={100}>100</option>
          <option value={200}>200</option>
          <option value={300}>300</option>
          <option value={400}>400</option>
        </select>
        <span style={{ marginLeft: 'auto', fontSize: '0.72rem', color: MUTED_FG }}>
          {players.length} qualified players
        </span>
      </div>

      <div style={{ padding: '16px 24px', maxWidth: 1200 }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: MUTED_FG }}>Loading Statcast data...</div>
        ) : (
          <>
            {/* Description */}
            {selectedStat && (
              <div style={{ fontSize: '0.78rem', color: MUTED_FG, marginBottom: 16 }}>
                {selectedStat.description}
              </div>
            )}

            {/* Bar chart — top 20 */}
            <div className="data-table-wrap" style={{ padding: '14px 18px', marginBottom: 16 }}>
              <div style={{ fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
                {stat === 'xwOBADiff' ? 'MOST UNLUCKY (negative) vs MOST LUCKY (positive)' : `TOP 20 — ${selectedStat?.label}`}
              </div>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={top20} layout="vertical" margin={{ top: 4, right: 24, left: 0, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="oklch(100% 0 0 / .05)" />
                  <XAxis type="number" tick={{ fill: MUTED_FG, fontSize: 10, fontFamily: 'var(--d3-mono)' }} tickLine={false} axisLine={false} />
                  <YAxis type="category" dataKey="name" width={130} tick={{ fill: 'oklch(98.5% 0 0)', fontSize: 11, fontFamily: 'Nunito' }} tickLine={false} axisLine={false} />
                  <Tooltip content={<DarkTooltip />} />
                  {stat === 'xwOBADiff' ? (
                    <Bar dataKey={stat} radius={[0, 4, 4, 0]}>
                      {top20.map((p, i) => (
                        <Cell key={i} fill={(p as any)[stat] >= 0 ? EMERALD : BRAND_RED} />
                      ))}
                    </Bar>
                  ) : (
                    <Bar dataKey={stat} fill={EMERALD} radius={[0, 4, 4, 0]} />
                  )}
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Data table */}
            <StatcastTable players={sorted} stat={stat} />

            {/* Scatter: actual vs expected */}
            {stat !== 'xwOBADiff' && (
              <div className="data-table-wrap" style={{ padding: '14px 18px', marginTop: 16 }}>
                <div style={{ fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
                  ACTUAL vs EXPECTED — dots above the line are over-performing
                </div>
                <ResponsiveContainer width="100%" height={350}>
                  <ScatterChart margin={{ top: 10, right: 24, left: 0, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="oklch(100% 0 0 / .05)" />
                    <XAxis type="number" dataKey={`x${stat.slice(1)}`} name={`Expected (${stat})`}
                      tick={{ fill: MUTED_FG, fontSize: 10, fontFamily: 'var(--d3-mono)' }} tickLine={false}
                      label={{ value: stat, position: 'bottom', fill: MUTED_FG, fontSize: 11 }} />
                    <YAxis type="number" dataKey={stat === 'xBA' ? 'ba' : stat === 'xSLG' ? 'slg' : 'woba'}
                      name="Actual" tick={{ fill: MUTED_FG, fontSize: 10, fontFamily: 'var(--d3-mono)' }} tickLine={false}
                      label={{ value: 'Actual', angle: -90, position: 'insideLeft', fill: MUTED_FG, fontSize: 11 }} />
                    <ZAxis range={[30, 30]} />
                    <Tooltip content={<DarkTooltip />} />
                    <Scatter data={sorted.map(p => ({
                      ...p,
                      [`x${stat.slice(1)}`]: (p as any)[stat],
                    }))} fill={BLUE} />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function StatcastTable({ players, stat }: { players: BatterRow[]; stat: Stat }) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
        <thead>
          <tr>
            {['#', 'Player', 'Team', 'PA', 'BA', 'xBA', 'SLG', 'xSLG', 'wOBA', 'xwOBA', 'Diff'].map(h => (
              <th key={h} style={{
                padding: '8px 10px', textAlign: h === 'Player' || h === 'Team' ? 'left' : 'right',
                fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG,
                letterSpacing: '0.1em', textTransform: 'uppercase',
                borderBottom: `1px solid ${BORDER}`,
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {players.slice(0, 50).map((p, i) => (
            <tr key={p.name + i} style={{ borderBottom: `1px solid ${BORDER}` }}>
              <td style={{ padding: '6px 10px', textAlign: 'right', color: MUTED_FG, fontFamily: 'var(--d3-mono)', fontSize: '0.72rem' }}>{i + 1}</td>
              <td style={{ padding: '6px 10px', fontWeight: 600, color: 'var(--foreground)' }}>{p.name}</td>
              <td style={{ padding: '6px 10px', color: MUTED_FG }}>{p.team || '—'}</td>
              <td style={{ padding: '6px 10px', textAlign: 'right', color: MUTED_FG, fontFamily: 'var(--d3-mono)' }}>{p.pa}</td>
              <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: 'var(--foreground)' }}>{p.ba?.toFixed(3)}</td>
              <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: EMERALD }}>{p.xBA?.toFixed(3)}</td>
              <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: 'var(--foreground)' }}>{p.slg?.toFixed(3)}</td>
              <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: EMERALD }}>{p.xSLG?.toFixed(3)}</td>
              <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: 'var(--foreground)' }}>{p.woba?.toFixed(3)}</td>
              <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: BLUE, fontWeight: 700 }}>{p.xwOBA?.toFixed(3)}</td>
              <td style={{
                padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', fontWeight: 700,
                color: p.xwOBADiff > 0 ? EMERALD : p.xwOBADiff < -0.02 ? BRAND_RED : MUTED_FG,
              }}>
                {p.xwOBADiff > 0 ? '+' : ''}{p.xwOBADiff?.toFixed(3)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Statcast;
