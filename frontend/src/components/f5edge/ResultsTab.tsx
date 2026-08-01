/**
 * F5 Edge Engine — Results Tab
 * Shows backtested signal performance for the current season.
 */
import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts';
import { Badge } from './Badge';
import { EMERALD, BRAND_RED, BLUE, YELLOW, MUTED_FG, BORDER, FG, plColor, fmtPct } from './tokens';

interface SignalResult {
  signal: string;
  tier: string;
  type: string;
  bets: number;
  wins: number;
  win_rate: number;
  pl: number;
  roi: number;
  season: number;
  period: string;
}

interface BacktestData {
  signals: SignalResult[];
  games: number;
  ties: number;
  season: number;
}

const SIDEBAR_BG = 'oklch(20.5% 0 0)';

function DarkTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '10px 14px', fontSize: '0.78rem' }}>
      {label && <p style={{ color: FG, fontWeight: 700, marginBottom: 4 }}>{label}</p>}
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color || MUTED_FG, margin: '2px 0' }}>
          {p.name}: <strong>{typeof p.value === 'number' ? (p.dataKey === 'roi' ? p.value.toFixed(1) + '%' : '$' + p.value.toLocaleString()) : p.value}</strong>
        </p>
      ))}
    </div>
  );
}

function tierColor(tier: string): string {
  if (tier === 'STRONG') return EMERALD;
  if (tier === 'GOOD') return BLUE;
  return YELLOW;
}

function typeLabel(type: string): string {
  const map: Record<string, string> = {
    tie: 'TIE', under: 'UNDER', fav_ml: 'FAV ML', sgp: 'PARLAY',
  };
  return map[type] ?? type.toUpperCase();
}

export function ResultsTab() {
  const [data, setData] = useState<BacktestData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Try fetching from API first, fall back to static data
    fetch('/api/f5/results')
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setData(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // Use hardcoded 2026 data if API not available
  const results: BacktestData = data ?? FALLBACK_DATA;
  const signals = results.signals.filter(s => s.bets > 0);
  const profitable = signals.filter(s => s.roi > 0);
  const totalPl = signals.reduce((sum, s) => sum + s.pl, 0);
  const totalBets = signals.reduce((sum, s) => sum + s.bets, 0);

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: MUTED_FG }}>Loading results...</div>;

  return (
    <div>
      {/* Summary stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 16 }}>
        <SummaryCard label="Total P&L" value={`$${totalPl.toLocaleString()}`} color={plColor(totalPl)} />
        <SummaryCard label="Total Bets" value={totalBets.toLocaleString()} />
        <SummaryCard label="Profitable Signals" value={`${profitable.length}/${signals.length}`} color={EMERALD} />
        <SummaryCard label="Games Analyzed" value={results.games.toLocaleString()} sub={results.season + ' First Half'} />
      </div>

      {/* ROI bar chart */}
      <div className="data-table-wrap" style={{ padding: '14px 18px', marginBottom: 16 }}>
        <div style={{ fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
          ROI BY SIGNAL — 2026 FIRST HALF
        </div>
        <ResponsiveContainer width="100%" height={signals.length * 36 + 20}>
          <BarChart data={signals} layout="vertical" margin={{ top: 4, right: 24, left: 0, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="oklch(100% 0 0 / .05)" />
            <XAxis type="number" tick={{ fill: MUTED_FG, fontSize: 10, fontFamily: 'var(--d3-mono)' }} tickLine={false} axisLine={false}
              tickFormatter={v => `${v}%`} />
            <YAxis type="category" dataKey="signal" width={220} tick={{ fill: FG, fontSize: 11, fontFamily: 'Nunito', fontWeight: 600 }} tickLine={false} axisLine={false} />
            <Tooltip content={<DarkTooltip />} />
            <Bar dataKey="roi" name="ROI" radius={[0, 4, 4, 0]}>
              {signals.map((s, i) => (
                <Cell key={i} fill={s.roi > 0 ? EMERALD : BRAND_RED} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Results table */}
      <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
          <thead>
            <tr>
              {['Signal', 'Tier', 'Type', 'Bets', 'Wins', 'Win %', 'P&L', 'ROI'].map(h => (
                <th key={h} style={{
                  padding: '8px 10px', textAlign: h === 'Signal' ? 'left' : 'right',
                  fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG,
                  letterSpacing: '0.1em', textTransform: 'uppercase',
                  borderBottom: `1px solid ${BORDER}`,
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {signals.map(s => (
              <tr key={s.signal} style={{ borderBottom: `1px solid ${BORDER}` }}>
                <td style={{ padding: '8px 10px', fontWeight: 600, color: FG }}>{s.signal}</td>
                <td style={{ padding: '8px 10px', textAlign: 'right' }}>
                  <Badge color={tierColor(s.tier)} label={s.tier} />
                </td>
                <td style={{ padding: '8px 10px', textAlign: 'right' }}>
                  <Badge color={BLUE} label={typeLabel(s.type)} />
                </td>
                <td style={{ padding: '8px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: MUTED_FG }}>{s.bets.toLocaleString()}</td>
                <td style={{ padding: '8px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: MUTED_FG }}>{s.wins.toLocaleString()}</td>
                <td style={{ padding: '8px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', fontWeight: 700, color: s.win_rate > 50 ? EMERALD : s.win_rate < 45 ? BRAND_RED : FG }}>{s.win_rate}%</td>
                <td style={{ padding: '8px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', fontWeight: 700, color: plColor(s.pl) }}>
                  {s.pl >= 0 ? '+' : ''}${Math.abs(s.pl).toLocaleString()}
                </td>
                <td style={{ padding: '8px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', fontWeight: 700, color: plColor(s.roi) }}>{fmtPct(s.roi)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SummaryCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="stat-card" style={{ minWidth: 0 }}>
      <div style={{ fontSize: '0.62rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6 }}>{label}</div>
      <div className="stat-value" style={{ color: color ?? FG, fontSize: '1.4rem' }}>{value}</div>
      {sub && <div style={{ fontSize: '0.65rem', color: MUTED_FG, marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <span>
      <span style={{ color: MUTED_FG }}>{label}: </span>
      <span style={{ color: color ?? FG, fontWeight: 700, fontFamily: 'var(--d3-mono)' }}>{value}</span>
    </span>
  );
}

// Fallback data from 2026 first-half backtest
const FALLBACK_DATA: BacktestData = {
  season: 2026,
  games: 1638,
  ties: 258,
  signals: [
    { signal: "F5 Tie (Ace vs Ace)", tier: "STRONG", type: "tie", bets: 164, wins: 37, win_rate: 22.6, pl: 3950, roi: 24.1, season: 2026, period: "First Half (Apr-Jul)" },
    { signal: "F5 Tie (Hi-Venue+ERA<4)", tier: "STRONG", type: "tie", bets: 55, wins: 17, win_rate: 30.9, pl: 3850, roi: 70.0, season: 2026, period: "First Half (Apr-Jul)" },
    { signal: "F5 Under (ERA<3.50)", tier: "STRONG", type: "under", bets: 164, wins: 120, win_rate: 73.2, pl: 6509, roi: 39.7, season: 2026, period: "First Half (Apr-Jul)" },
    { signal: "F5 Under (ERA<4.50)", tier: "GOOD", type: "under", bets: 471, wins: 287, win_rate: 60.9, pl: 7691, roi: 16.3, season: 2026, period: "First Half (Apr-Jul)" },
    { signal: "F5 Fav ML (diff>=1.5)", tier: "STRONG", type: "fav_ml", bets: 604, wins: 391, win_rate: 64.7, pl: 8777, roi: 14.5, season: 2026, period: "First Half (Apr-Jul)" },
    { signal: "F5 Fav ML (diff>=1.0)", tier: "GOOD", type: "fav_ml", bets: 279, wins: 125, win_rate: 44.8, pl: -5785, roi: -20.7, season: 2026, period: "First Half (Apr-Jul)" },
    { signal: "F5 Fav ML (diff>=1.5+hitter)", tier: "STRONG", type: "fav_ml", bets: 205, wins: 136, win_rate: 66.3, pl: 3562, roi: 17.4, season: 2026, period: "First Half (Apr-Jul)" },
    { signal: "F5 Tie+Under SGP", tier: "STRONG", type: "sgp", bets: 219, wins: 48, win_rate: 21.9, pl: 6525, roi: 119.2, season: 2026, period: "First Half (Apr-Jul)" },
    { signal: "F1 Tie+FG Under SGP", tier: "GOOD", type: "sgp", bets: 377, wins: 251, win_rate: 66.6, pl: 15675, roi: 166.3, season: 2026, period: "First Half (Apr-Jul)" },
  ],
};
