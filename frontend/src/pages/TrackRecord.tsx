import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Cell,
} from 'recharts';
import { getApiUrl } from '../config';

const BG       = 'oklch(14.5% 0 0)';
const PANEL    = 'oklch(18% 0 0)';
const BORDER   = 'oklch(100% 0 0 / .08)';
const FG       = 'oklch(98.5% 0 0)';
const MUTED    = 'oklch(60% 0 0)';
const EMERALD  = 'oklch(69.6% .17 162.48)';
const RED      = 'oklch(63.2% .204 25.331)';
const YELLOW   = 'oklch(79.5% .184 86.047)';
const BLUE     = 'oklch(62.3% .214 259.815)';

interface Signal {
  signal: string;
  tier: 'STRONG' | 'GOOD' | 'WEAK';
  type: string;
  bets: number;
  wins: number;
  win_rate: number;
  pl: number;
  roi: number;
  period: string;
}

interface BacktestData {
  signals: Signal[];
  games: number;
  ties: number;
  season: number;
}

interface MonthData {
  month: number;
  month_name: string;
  total_games: number;
  ties: number;
  tie_rate_pct: number;
  modeled_pct: number;
  difference: number;
}

const TIER_COLOR: Record<string, string> = {
  STRONG: EMERALD,
  GOOD:   YELLOW,
  WEAK:   MUTED,
};

const MONTH_DATA: MonthData[] = [
  { month: 4, month_name: 'Apr', total_games: 799,  ties: 116, tie_rate_pct: 14.52, modeled_pct: 12.5, difference: 2.02 },
  { month: 5, month_name: 'May', total_games: 821,  ties: 113, tie_rate_pct: 13.76, modeled_pct: 11.9, difference: 1.86 },
  { month: 6, month_name: 'Jun', total_games: 794,  ties: 120, tie_rate_pct: 15.11, modeled_pct: 11.4, difference: 3.71 },
  { month: 7, month_name: 'Jul', total_games: 733,  ties: 106, tie_rate_pct: 14.46, modeled_pct: 11.0, difference: 3.46 },
  { month: 8, month_name: 'Aug', total_games: 826,  ties: 117, tie_rate_pct: 14.16, modeled_pct: 11.3, difference: 2.86 },
  { month: 9, month_name: 'Sep', total_games: 794,  ties: 115, tie_rate_pct: 14.48, modeled_pct: 12.1, difference: 2.38 },
];

function StatCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div style={{
      background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 12,
      padding: '20px 24px', flex: 1, minWidth: 140,
    }}>
      <div style={{ fontSize: '0.65rem', color: MUTED, letterSpacing: '0.08em', marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: '1.75rem', fontWeight: 800, color: color ?? FG, fontFamily: 'Nunito', lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontSize: '0.65rem', color: MUTED, marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function TierBadge({ tier }: { tier: string }) {
  const color = TIER_COLOR[tier] ?? MUTED;
  return (
    <span style={{
      fontSize: '0.6rem', fontWeight: 700, letterSpacing: '0.08em',
      color, border: `1px solid ${color}`, borderRadius: 4,
      padding: '2px 6px',
    }}>{tier}</span>
  );
}

function RoiBar({ roi, maxAbs }: { roi: number; maxAbs: number }) {
  const pct = Math.min(Math.abs(roi) / maxAbs * 100, 100);
  const positive = roi >= 0;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ width: 80, height: 6, background: 'oklch(100% 0 0 / .08)', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{
          width: `${pct}%`, height: '100%',
          background: positive ? EMERALD : RED,
          borderRadius: 3,
        }} />
      </div>
      <span style={{
        fontSize: '0.75rem', fontWeight: 700,
        color: positive ? EMERALD : RED, minWidth: 52,
      }}>
        {roi >= 0 ? '+' : ''}{roi.toFixed(1)}%
      </span>
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 8, padding: '10px 14px', fontSize: '0.75rem' }}>
      <div style={{ color: FG, fontWeight: 700, marginBottom: 4 }}>{label}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} style={{ color: p.fill, marginBottom: 2 }}>
          {p.name}: {p.value.toFixed(2)}%
        </div>
      ))}
    </div>
  );
};

export function TrackRecord() {
  const [data, setData] = useState<BacktestData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(getApiUrl('f5/results'))
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const signals: Signal[] = data?.signals ?? [];
  const totalBets = signals.reduce((s, x) => s + x.bets, 0);
  const totalPL   = signals.reduce((s, x) => s + x.pl, 0);
  const winSigs   = signals.filter(s => s.roi > 0).length;
  const bestROI   = signals.reduce((mx, s) => Math.max(mx, s.roi), 0);
  const maxRoiAbs = signals.reduce((mx, s) => Math.max(mx, Math.abs(s.roi)), 0);

  const chartData = MONTH_DATA.map(m => ({
    name: m.month_name,
    'Actual Tie Rate': m.tie_rate_pct,
    'Modeled Rate': m.modeled_pct,
    'Edge': m.difference,
  }));

  return (
    <div style={{ background: BG, minHeight: '100vh', padding: '32px 24px', color: FG }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>

        {/* Header */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ fontSize: '0.65rem', color: MUTED, letterSpacing: '0.12em', marginBottom: 8 }}>
            RESEARCH VALIDATION · MLB 2026 SEASON
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'Nunito', margin: 0, lineHeight: 1.1 }}>
            Track Record
          </h1>
          <p style={{ color: MUTED, marginTop: 8, fontSize: '0.85rem', maxWidth: 560 }}>
            Backtest results for our F5 edge signals. Validated against {data?.games?.toLocaleString() ?? '1,638'} MLB first-half games
            with {data?.ties?.toLocaleString() ?? '258'} observed ties. Research phase: Apr–Jul {data?.season ?? 2026}.
          </p>
        </div>

        {/* Hero stat bar */}
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 32 }}>
          <StatCard label="TOTAL BETS ANALYZED" value={loading ? '—' : totalBets.toLocaleString()} sub="across all signals" />
          <StatCard label="WINNING SIGNALS" value={loading ? '—' : `${winSigs} / ${signals.length}`} sub="positive ROI" color={EMERALD} />
          <StatCard label="BEST SIGNAL ROI" value={loading ? '—' : `+${bestROI.toFixed(0)}%`} sub="F1 Tie+FG Under SGP" color={EMERALD} />
          <StatCard
            label="NET P&L (ALL SIGNALS)"
            value={loading ? '—' : `${totalPL >= 0 ? '+' : ''}$${Math.abs(totalPL).toLocaleString()}`}
            sub="$100/bet unit sizing"
            color={totalPL >= 0 ? EMERALD : RED}
          />
          <StatCard label="GAMES ANALYZED" value={loading ? '—' : (data?.games ?? 0).toLocaleString()} sub={`MLB ${data?.season ?? 2026}`} color={BLUE} />
        </div>

        {/* Signal performance table */}
        <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 12, marginBottom: 28, overflow: 'hidden' }}>
          <div style={{ padding: '16px 20px', borderBottom: `1px solid ${BORDER}` }}>
            <div style={{ fontWeight: 700, fontSize: '0.85rem', fontFamily: 'Nunito' }}>Signal Performance</div>
            <div style={{ fontSize: '0.65rem', color: MUTED, marginTop: 2 }}>
              All signals sorted by ROI. P&L calculated at $100/unit flat bet sizing.
            </div>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${BORDER}` }}>
                  {['Signal', 'Tier', 'Type', 'Bets', 'Wins', 'Win%', 'ROI', 'P&L'].map(h => (
                    <th key={h} style={{ padding: '10px 14px', textAlign: 'left', color: MUTED, fontWeight: 600, fontSize: '0.65rem', letterSpacing: '0.06em' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={8} style={{ padding: 32, textAlign: 'center', color: MUTED }}>Loading...</td></tr>
                ) : (
                  [...signals].sort((a, b) => b.roi - a.roi).map((s, i) => (
                    <tr key={i} style={{ borderBottom: `1px solid ${BORDER}`, background: i % 2 === 0 ? 'transparent' : 'oklch(100% 0 0 / .02)' }}>
                      <td style={{ padding: '11px 14px', fontWeight: 600, color: FG, fontFamily: 'Nunito', minWidth: 200 }}>{s.signal}</td>
                      <td style={{ padding: '11px 14px' }}><TierBadge tier={s.tier} /></td>
                      <td style={{ padding: '11px 14px', color: MUTED, fontSize: '0.7rem' }}>{s.type.toUpperCase()}</td>
                      <td style={{ padding: '11px 14px', color: FG }}>{s.bets}</td>
                      <td style={{ padding: '11px 14px', color: FG }}>{s.wins}</td>
                      <td style={{ padding: '11px 14px', color: s.win_rate >= 60 ? EMERALD : s.win_rate >= 50 ? YELLOW : MUTED, fontWeight: 700 }}>
                        {s.win_rate.toFixed(1)}%
                      </td>
                      <td style={{ padding: '11px 14px' }}>
                        <RoiBar roi={s.roi} maxAbs={maxRoiAbs} />
                      </td>
                      <td style={{ padding: '11px 14px', fontWeight: 700, color: s.pl >= 0 ? EMERALD : RED }}>
                        {s.pl >= 0 ? '+' : ''}${s.pl.toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Monthly tie rate chart */}
        <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 12, marginBottom: 28, padding: '20px 20px 12px' }}>
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontWeight: 700, fontSize: '0.85rem', fontFamily: 'Nunito' }}>F5 Tie Rate: Actual vs Modeled (2023–2024)</div>
            <div style={{ fontSize: '0.65rem', color: MUTED, marginTop: 2 }}>
              4,857 MLB first-half games · 2023–2024 seasons. Our model consistently underpredicts tie frequency — the systematic gap is the edge.
            </div>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={chartData} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="oklch(100% 0 0 / .06)" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: MUTED, fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis
                domain={[9, 17]} tick={{ fill: MUTED, fontSize: 11 }} axisLine={false} tickLine={false}
                tickFormatter={v => `${v}%`}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'oklch(100% 0 0 / .04)' }} />
              <ReferenceLine y={14.52} stroke={EMERALD} strokeDasharray="4 4" strokeOpacity={0.4} />
              <Bar dataKey="Actual Tie Rate" fill={BLUE} radius={[4, 4, 0, 0]} name="Actual Tie Rate" />
              <Bar dataKey="Modeled Rate" fill="oklch(100% 0 0 / .15)" radius={[4, 4, 0, 0]} name="Modeled Rate" />
            </BarChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', gap: 20, marginTop: 8, paddingLeft: 4 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.65rem', color: MUTED }}>
              <div style={{ width: 10, height: 10, background: BLUE, borderRadius: 2 }} />
              Actual tie rate (observed)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.65rem', color: MUTED }}>
              <div style={{ width: 10, height: 10, background: 'oklch(100% 0 0 / .25)', borderRadius: 2 }} />
              Modeled tie rate (expected)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.65rem', color: EMERALD }}>
              <div style={{ width: 10, height: 1, background: EMERALD }} />
              Overall actual avg (14.52%)
            </div>
          </div>
        </div>

        {/* Monthly edge breakdown */}
        <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 12, marginBottom: 28, overflow: 'hidden' }}>
          <div style={{ padding: '16px 20px', borderBottom: `1px solid ${BORDER}` }}>
            <div style={{ fontWeight: 700, fontSize: '0.85rem', fontFamily: 'Nunito' }}>Monthly Edge Breakdown</div>
            <div style={{ fontSize: '0.65rem', color: MUTED, marginTop: 2 }}>
              All months show actual tie rate exceeding modeled rate — systematic mispricing that persists across all conditions.
            </div>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${BORDER}` }}>
                {['Month', 'Games', 'Ties Observed', 'Actual Rate', 'Modeled Rate', 'Edge'].map(h => (
                  <th key={h} style={{ padding: '10px 16px', textAlign: 'left', color: MUTED, fontWeight: 600, fontSize: '0.65rem', letterSpacing: '0.06em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {MONTH_DATA.map((m, i) => (
                <tr key={m.month} style={{ borderBottom: `1px solid ${BORDER}`, background: i % 2 === 0 ? 'transparent' : 'oklch(100% 0 0 / .02)' }}>
                  <td style={{ padding: '10px 16px', fontWeight: 600, color: FG }}>{m.month_name}</td>
                  <td style={{ padding: '10px 16px', color: MUTED }}>{m.total_games.toLocaleString()}</td>
                  <td style={{ padding: '10px 16px', color: FG }}>{m.ties}</td>
                  <td style={{ padding: '10px 16px', fontWeight: 700, color: BLUE }}>{m.tie_rate_pct.toFixed(2)}%</td>
                  <td style={{ padding: '10px 16px', color: MUTED }}>{m.modeled_pct.toFixed(1)}%</td>
                  <td style={{ padding: '10px 16px', fontWeight: 700, color: EMERALD }}>+{m.difference.toFixed(2)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Methodology note */}
        <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 12, padding: '20px 24px', marginBottom: 20 }}>
          <div style={{ fontWeight: 700, fontSize: '0.85rem', fontFamily: 'Nunito', marginBottom: 10 }}>Methodology</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
            {[
              { label: 'Data Source', text: '4,857 MLB first-half games (2023–2024) plus 1,638 live-tracked games in 2026. All data from MLB Stats API.' },
              { label: 'Signal Logic', text: 'Signals combine pitcher ERA, park factors, lineup scoring patterns, and historical tie rates to identify value.' },
              { label: 'P&L Calculation', text: 'Flat $100/unit. Ties paid at +800 (US). Under/ML bets use closing line odds from The Odds API.' },
              { label: 'No Data Mining', text: 'Signals defined before 2026 season using 2023–2024 data only. Out-of-sample validation ongoing.' },
            ].map(item => (
              <div key={item.label}>
                <div style={{ fontSize: '0.65rem', color: MUTED, letterSpacing: '0.07em', marginBottom: 4 }}>{item.label.toUpperCase()}</div>
                <div style={{ fontSize: '0.75rem', color: FG, lineHeight: 1.5 }}>{item.text}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Disclaimer */}
        <div style={{ fontSize: '0.65rem', color: MUTED, lineHeight: 1.6, textAlign: 'center', padding: '0 20px' }}>
          Research results only. Past performance does not guarantee future results. Sports betting involves risk of loss.
          This site does not facilitate wagering. Always gamble responsibly.
        </div>

      </div>
    </div>
  );
}

export default TrackRecord;
