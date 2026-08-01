/**
 * Power Rankings — Composite team rankings across all sports.
 * Combines win%, point differential, and recent form into a single score.
 */
import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
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

type Sport = 'mlb' | 'nfl' | 'nba' | 'wnba' | 'nhl';
const SPORTS: { key: Sport; label: string }[] = [
  { key: 'mlb', label: 'MLB' }, { key: 'nfl', label: 'NFL' },
  { key: 'nba', label: 'NBA' }, { key: 'wnba', label: 'WNBA' },
  { key: 'nhl', label: 'NHL' },
];

interface TeamRank {
  rank: number;
  team: string;
  abbr: string;
  logo: string;
  wins: number;
  losses: number;
  pct: number;
  ppg: number;
  papg: number;
  diff: number;
  streak: string;
  last10: string;
  powerScore: number;
  tier: 'elite' | 'contender' | 'average' | 'below' | 'bottom';
}

function computeRankings(teams: any[]): TeamRank[] {
  if (!teams.length) return [];

  const maxDiff = Math.max(...teams.map(t => Math.abs(t.diff)), 1);
  const maxPct = Math.max(...teams.map(t => t.pct), 0.001);

  const ranked = teams.map(t => {
    const pctScore = (t.pct / maxPct) * 40;
    const diffScore = ((t.diff + maxDiff) / (2 * maxDiff)) * 35;
    const l10 = t.last10 ? parseInt(t.last10.split('-')[0], 10) : 5;
    const formScore = (l10 / 10) * 25;
    const powerScore = Math.round(pctScore + diffScore + formScore);

    return { ...t, powerScore };
  });

  ranked.sort((a, b) => b.powerScore - a.powerScore);

  return ranked.map((t, i) => {
    const pct = (i + 1) / ranked.length;
    const tier = pct <= 0.15 ? 'elite' : pct <= 0.35 ? 'contender' : pct <= 0.65 ? 'average' : pct <= 0.85 ? 'below' : 'bottom';
    return { ...t, rank: i + 1, tier };
  });
}

const TIER_COLORS: Record<string, string> = {
  elite: EMERALD, contender: BLUE, average: YELLOW, below: MUTED_FG, bottom: BRAND_RED,
};

const TIER_LABELS: Record<string, string> = {
  elite: 'ELITE', contender: 'CONTENDER', average: 'AVERAGE', below: 'BELOW AVG', bottom: 'BOTTOM',
};

function DarkTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '10px 14px', fontSize: '0.78rem' }}>
      {label && <p style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700, marginBottom: 4 }}>{label}</p>}
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color || MUTED_FG, margin: '2px 0' }}>
          {p.name}: <strong>{p.value}</strong>
        </p>
      ))}
    </div>
  );
}

export function PowerRankings() {
  const [sport, setSport] = useState<Sport>('mlb');
  const [rankings, setRankings] = useState<TeamRank[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(getApiUrl(`analytics-data/team-scoring/${sport}`))
      .then(r => r.json())
      .then(d => setRankings(computeRankings(d.teams ?? [])))
      .catch(() => setRankings([]))
      .finally(() => setLoading(false));
  }, [sport]);

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1>Power Rankings</h1>
        <p className="subtitle">Composite rankings: 40% win rate + 35% point differential + 25% recent form (last 10)</p>
        <div className="sport-tabs" style={{ marginTop: 12 }}>
          {SPORTS.map(s => (
            <button key={s.key} className={`sport-tab ${sport === s.key ? 'active' : ''}`} onClick={() => setSport(s.key)}>
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: MUTED_FG }}>Loading...</div>
      ) : (
        <div style={{ padding: '16px 24px', maxWidth: 1200 }}>
          {/* Power Score bar chart */}
          <div className="data-table-wrap" style={{ padding: '14px 18px', marginBottom: 16 }}>
            <div style={{ fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
              POWER SCORE (0-100)
            </div>
            <ResponsiveContainer width="100%" height={Math.max(300, rankings.length * 22)}>
              <BarChart data={rankings} layout="vertical" margin={{ top: 4, right: 24, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="oklch(100% 0 0 / .05)" />
                <XAxis type="number" domain={[0, 100]} tick={{ fill: MUTED_FG, fontSize: 10, fontFamily: 'var(--d3-mono)' }} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="abbr" width={45} tick={{ fill: 'oklch(98.5% 0 0)', fontSize: 11, fontFamily: 'Nunito', fontWeight: 600 }} tickLine={false} axisLine={false} />
                <Tooltip content={<DarkTooltip />} />
                <Bar dataKey="powerScore" name="Power Score" radius={[0, 4, 4, 0]}>
                  {rankings.map((t, i) => (
                    <Cell key={i} fill={TIER_COLORS[t.tier]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Rankings table */}
          <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
              <thead>
                <tr>
                  {['#', 'Team', 'Score', 'Tier', 'W-L', 'PCT', 'PPG', 'PAPG', 'Diff', 'Streak', 'L10'].map(h => (
                    <th key={h} style={{
                      padding: '8px 10px', textAlign: h === 'Team' || h === 'Tier' ? 'left' : 'right',
                      fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG,
                      letterSpacing: '0.1em', textTransform: 'uppercase',
                      borderBottom: `1px solid ${BORDER}`,
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rankings.map(t => (
                  <tr key={t.abbr} style={{ borderBottom: `1px solid ${BORDER}` }}>
                    <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', fontWeight: 700, color: t.rank <= 3 ? EMERALD : MUTED_FG }}>{t.rank}</td>
                    <td style={{ padding: '6px 10px', display: 'flex', alignItems: 'center', gap: 8 }}>
                      <img src={t.logo} alt="" style={{ width: 20, height: 20 }} />
                      <span style={{ fontWeight: 600, color: 'var(--foreground)' }}>{t.team}</span>
                    </td>
                    <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', fontWeight: 800, color: TIER_COLORS[t.tier], fontSize: '0.9rem' }}>{t.powerScore}</td>
                    <td style={{ padding: '6px 10px' }}>
                      <span style={{
                        padding: '2px 8px', borderRadius: 20, fontSize: '0.62rem', fontWeight: 700,
                        letterSpacing: '0.08em', textTransform: 'uppercase',
                        background: `color-mix(in oklch, ${TIER_COLORS[t.tier]} 18%, transparent)`,
                        color: TIER_COLORS[t.tier],
                        border: `1px solid color-mix(in oklch, ${TIER_COLORS[t.tier]} 40%, transparent)`,
                      }}>
                        {TIER_LABELS[t.tier]}
                      </span>
                    </td>
                    <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: 'var(--foreground)' }}>{t.wins}-{t.losses}</td>
                    <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: 'var(--foreground)', fontWeight: 700 }}>{t.pct.toFixed(3)}</td>
                    <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: EMERALD }}>{t.ppg.toFixed(1)}</td>
                    <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: BRAND_RED }}>{t.papg.toFixed(1)}</td>
                    <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', fontWeight: 700, color: t.diff > 0 ? EMERALD : BRAND_RED }}>
                      {t.diff > 0 ? '+' : ''}{t.diff.toFixed(1)}
                    </td>
                    <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', fontWeight: 700, color: t.streak.startsWith('W') ? EMERALD : BRAND_RED }}>{t.streak}</td>
                    <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: MUTED_FG }}>{t.last10}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default PowerRankings;
