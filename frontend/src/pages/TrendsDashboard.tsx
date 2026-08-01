/**
 * Team Trends Dashboard — Who's hot, who's cold across all sports.
 * Shows PPG trends, point differentials, streak analysis.
 */
import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, ReferenceLine,
} from 'recharts';
import { TrendingUp, TrendingDown, Flame, Snowflake } from 'lucide-react';
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
  { key: 'mlb',  label: 'MLB' },
  { key: 'nfl',  label: 'NFL' },
  { key: 'nba',  label: 'NBA' },
  { key: 'wnba', label: 'WNBA' },
  { key: 'nhl',  label: 'NHL' },
];

type SortBy = 'diff' | 'ppg' | 'papg' | 'pct' | 'streak';

interface TeamData {
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
  homeRecord: string;
  roadRecord: string;
}

function DarkTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '10px 14px', fontSize: '0.78rem' }}>
      {label && <p style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700, marginBottom: 4 }}>{label}</p>}
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color || MUTED_FG, margin: '2px 0' }}>
          {p.name}: <strong>{typeof p.value === 'number' ? p.value.toFixed(1) : p.value}</strong>
        </p>
      ))}
    </div>
  );
}

function streakNum(s: string): number {
  if (!s) return 0;
  const n = parseInt(s.replace(/\D/g, ''), 10) || 0;
  return s.startsWith('W') ? n : -n;
}

export function TrendsDashboard() {
  const [sport, setSport] = useState<Sport>('mlb');
  const [teams, setTeams] = useState<TeamData[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<SortBy>('diff');

  useEffect(() => {
    setLoading(true);
    fetch(getApiUrl(`analytics-data/team-scoring/${sport}`))
      .then(r => r.json())
      .then(d => setTeams(d.teams ?? []))
      .catch(() => setTeams([]))
      .finally(() => setLoading(false));
  }, [sport]);

  const sorted = [...teams].sort((a, b) => {
    if (sortBy === 'diff') return b.diff - a.diff;
    if (sortBy === 'ppg') return b.ppg - a.ppg;
    if (sortBy === 'papg') return a.papg - b.papg;
    if (sortBy === 'pct') return b.pct - a.pct;
    if (sortBy === 'streak') return streakNum(b.streak) - streakNum(a.streak);
    return 0;
  });

  const hot = sorted.filter(t => t.diff > 0 && streakNum(t.streak) >= 2).slice(0, 5);
  const cold = sorted.filter(t => t.diff < 0 || streakNum(t.streak) <= -3).slice(-5).reverse();

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1>Team Trends</h1>
        <p className="subtitle">Who's hot, who's cold — scoring trends, differentials, and streaks across all sports</p>

        <div className="sport-tabs" style={{ marginTop: 12 }}>
          {SPORTS.map(s => (
            <button key={s.key} className={`sport-tab ${sport === s.key ? 'active' : ''}`} onClick={() => setSport(s.key)}>
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <div className="filter-bar">
        <span className="filter-label">SORT</span>
        {([
          ['diff', 'POINT DIFF'], ['ppg', 'SCORING'], ['papg', 'DEFENSE'],
          ['pct', 'WIN %'], ['streak', 'STREAK'],
        ] as [SortBy, string][]).map(([key, label]) => (
          <button key={key} className={`filter-pill ${sortBy === key ? 'active' : ''}`} onClick={() => setSortBy(key)}>
            {label}
          </button>
        ))}
        <span style={{ marginLeft: 'auto', fontSize: '0.72rem', color: MUTED_FG }}>
          {teams.length} teams
        </span>
      </div>

      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: MUTED_FG }}>Loading...</div>
      ) : (
        <div style={{ padding: '16px 24px', maxWidth: 1200 }}>
          {/* Hot & Cold cards */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <HotColdCard title="HOT" icon={<Flame size={14} />} teams={hot} color={EMERALD} />
            <HotColdCard title="COLD" icon={<Snowflake size={14} />} teams={cold} color={BRAND_RED} />
          </div>

          {/* Point differential bar chart */}
          <div className="data-table-wrap" style={{ padding: '14px 18px', marginBottom: 16 }}>
            <div style={{ fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
              POINT DIFFERENTIAL PER GAME
            </div>
            <ResponsiveContainer width="100%" height={Math.max(300, sorted.length * 22)}>
              <BarChart data={sorted} layout="vertical" margin={{ top: 4, right: 24, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="oklch(100% 0 0 / .05)" />
                <XAxis type="number" tick={{ fill: MUTED_FG, fontSize: 10, fontFamily: 'var(--d3-mono)' }} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="abbr" width={45} tick={{ fill: 'oklch(98.5% 0 0)', fontSize: 11, fontFamily: 'Nunito', fontWeight: 600 }} tickLine={false} axisLine={false} />
                <Tooltip content={<DarkTooltip />} />
                <ReferenceLine x={0} stroke={BORDER} />
                <Bar dataKey="diff" name="Pt Diff" radius={[0, 4, 4, 0]}>
                  {sorted.map((t, i) => (
                    <Cell key={i} fill={t.diff >= 0 ? EMERALD : BRAND_RED} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Full table */}
          <TrendsTable teams={sorted} />
        </div>
      )}
    </div>
  );
}

function HotColdCard({ title, icon, teams, color }: {
  title: string; icon: React.ReactNode; teams: TeamData[]; color: string;
}) {
  return (
    <div className="data-table-wrap" style={{ padding: '14px 18px', borderLeft: `3px solid ${color}` }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8, color, fontWeight: 700, fontSize: '0.75rem', letterSpacing: '0.1em' }}>
        {icon} {title}
      </div>
      {teams.length === 0 ? (
        <div style={{ color: MUTED_FG, fontSize: '0.78rem' }}>No qualifying teams</div>
      ) : (
        teams.map(t => (
          <div key={t.abbr} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0', fontSize: '0.78rem' }}>
            <img src={t.logo} alt="" style={{ width: 20, height: 20 }} />
            <span style={{ color: 'var(--foreground)', fontWeight: 600, flex: 1 }}>{t.team}</span>
            <span style={{ color, fontFamily: 'var(--d3-mono)', fontWeight: 700 }}>
              {t.diff > 0 ? '+' : ''}{t.diff.toFixed(1)}
            </span>
            <span style={{ color: MUTED_FG, fontFamily: 'var(--d3-mono)', fontSize: '0.72rem' }}>
              {t.streak}
            </span>
          </div>
        ))
      )}
    </div>
  );
}

function TrendsTable({ teams }: { teams: TeamData[] }) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
        <thead>
          <tr>
            {['Team', 'W', 'L', 'PCT', 'PPG', 'PAPG', 'DIFF', 'Streak', 'L10', 'Home', 'Road'].map(h => (
              <th key={h} style={{
                padding: '8px 10px', textAlign: h === 'Team' ? 'left' : 'right',
                fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG,
                letterSpacing: '0.1em', textTransform: 'uppercase',
                borderBottom: `1px solid ${BORDER}`,
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {teams.map(t => (
            <tr key={t.abbr} style={{ borderBottom: `1px solid ${BORDER}` }}>
              <td style={{ padding: '6px 10px', display: 'flex', alignItems: 'center', gap: 8 }}>
                <img src={t.logo} alt="" style={{ width: 18, height: 18 }} />
                <span style={{ fontWeight: 600, color: 'var(--foreground)' }}>{t.team}</span>
              </td>
              <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: 'var(--foreground)' }}>{t.wins}</td>
              <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: MUTED_FG }}>{t.losses}</td>
              <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: 'var(--foreground)', fontWeight: 700 }}>{t.pct.toFixed(3)}</td>
              <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: EMERALD }}>{t.ppg.toFixed(1)}</td>
              <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: BRAND_RED }}>{t.papg.toFixed(1)}</td>
              <td style={{
                padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', fontWeight: 700,
                color: t.diff > 0 ? EMERALD : t.diff < 0 ? BRAND_RED : MUTED_FG,
              }}>
                {t.diff > 0 ? '+' : ''}{t.diff.toFixed(1)}
              </td>
              <td style={{
                padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', fontWeight: 700,
                color: t.streak.startsWith('W') ? EMERALD : t.streak.startsWith('L') ? BRAND_RED : MUTED_FG,
              }}>
                {t.streak}
              </td>
              <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: MUTED_FG }}>{t.last10}</td>
              <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: MUTED_FG }}>{t.homeRecord}</td>
              <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: MUTED_FG }}>{t.roadRecord}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default TrendsDashboard;
