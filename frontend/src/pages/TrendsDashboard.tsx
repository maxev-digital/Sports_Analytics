/**
 * Team Trends Dashboard — Who's hot, who's cold across all sports.
 * Shows PPG trends, point differentials, streak analysis.
 */
import { useState, useEffect } from 'react';
import { Flame, Snowflake } from 'lucide-react';
import '../styles/analytics.css';
import { getApiUrl } from '../config';

const EMERALD   = 'oklch(69.6% .17 162.48)';
const BRAND_RED = 'oklch(63.7% .237 25.331)';
const MUTED_FG  = 'oklch(70.8% 0 0)';
const BORDER    = 'oklch(100% 0 0 / .1)';

// Hex fallbacks for SVG fills (oklch not supported in SVG attributes)
const HEX_GREEN  = '#4ade80';
const HEX_RED    = '#ef4444';
const HEX_MUTED  = '#9ca3af';
const HEX_FG     = '#f3f4f6';

type Sport = 'mlb' | 'nfl' | 'nba' | 'wnba' | 'nhl';
const SPORTS: { key: Sport; label: string }[] = [
  { key: 'mlb',  label: 'MLB' },
  { key: 'nfl',  label: 'NFL' },
  { key: 'nba',  label: 'NBA' },
  { key: 'wnba', label: 'WNBA' },
  { key: 'nhl',  label: 'NHL' },
];

type SortBy = 'diff' | 'ppg' | 'papg' | 'pct' | 'streak';
type VizMode = 'list' | 'heatmap';

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
  const [vizMode, setVizMode] = useState<VizMode>('heatmap');

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

          {/* Point differential viz — 3-way toggle */}
          <div className="data-table-wrap" style={{ padding: '14px 18px', marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 12 }}>
              <span style={{ fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', flex: 1 }}>
                POINT DIFFERENTIAL PER GAME
              </span>
              <div style={{ display: 'flex', gap: 4 }}>
                {([['list', 'RANKED'], ['heatmap', 'HEAT MAP']] as [VizMode, string][]).map(([mode, label]) => (
                  <button
                    key={mode}
                    onClick={() => setVizMode(mode)}
                    style={{
                      fontSize: '0.6rem', fontWeight: 700, letterSpacing: '0.08em',
                      padding: '3px 8px', borderRadius: 4, border: 'none', cursor: 'pointer',
                      background: vizMode === mode ? 'oklch(62.3% .214 259.815)' : 'rgba(255,255,255,0.06)',
                      color: vizMode === mode ? '#fff' : MUTED_FG,
                      transition: 'background 0.15s',
                    }}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
            {vizMode === 'list'    && <DiffRanking teams={sorted} />}
            {vizMode === 'heatmap' && <HeatMap teams={sorted} />}
          </div>

          {/* Full table */}
          <TrendsTable teams={sorted} />
        </div>
      )}
    </div>
  );
}

function DiffRanking({ teams }: { teams: TeamData[] }) {
  const maxAbs = Math.max(...teams.map(t => Math.abs(t.diff)), 1);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {teams.map((t, i) => {
        const pct = (Math.abs(t.diff) / maxAbs) * 100;
        const isPos = t.diff >= 0;
        const streakColor = t.streak.startsWith('W') ? EMERALD : t.streak.startsWith('L') ? BRAND_RED : MUTED_FG;
        const barColor = isPos ? EMERALD : BRAND_RED;

        return (
          <div
            key={t.abbr}
            style={{
              display: 'grid',
              gridTemplateColumns: '24px 20px 52px 1fr 52px 44px',
              alignItems: 'center',
              gap: 8,
              padding: '3px 0',
              borderBottom: i < teams.length - 1 ? `1px solid ${BORDER}` : 'none',
            }}
          >
            {/* rank */}
            <span style={{ fontSize: '0.68rem', color: MUTED_FG, textAlign: 'right', fontFamily: 'var(--d3-mono)' }}>
              {i + 1}
            </span>

            {/* logo */}
            <img src={t.logo} alt="" style={{ width: 18, height: 18, objectFit: 'contain' }} />

            {/* abbr + record */}
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.8rem', color: 'var(--foreground)', lineHeight: 1.1 }}>{t.abbr}</div>
              <div style={{ fontSize: '0.62rem', color: MUTED_FG, fontFamily: 'var(--d3-mono)' }}>{t.wins}-{t.losses}</div>
            </div>

            {/* diverging bar */}
            <div style={{ display: 'flex', alignItems: 'center', height: 20 }}>
              {/* negative (left) side */}
              <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end', height: '100%', alignItems: 'center' }}>
                {!isPos && (
                  <div style={{
                    width: `${pct}%`,
                    height: 10,
                    background: `linear-gradient(to left, ${BRAND_RED}, oklch(63.7% .237 25.331 / .4))`,
                    borderRadius: '3px 0 0 3px',
                  }} />
                )}
              </div>
              {/* center line */}
              <div style={{ width: 1, height: 16, background: 'rgba(255,255,255,0.18)', flexShrink: 0 }} />
              {/* positive (right) side */}
              <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-start', height: '100%', alignItems: 'center' }}>
                {isPos && (
                  <div style={{
                    width: `${pct}%`,
                    height: 10,
                    background: `linear-gradient(to right, ${EMERALD}, oklch(69.6% .17 162.48 / .4))`,
                    borderRadius: '0 3px 3px 0',
                  }} />
                )}
              </div>
            </div>

            {/* diff */}
            <div style={{
              textAlign: 'right',
              fontFamily: 'var(--d3-mono)',
              fontWeight: 700,
              fontSize: '0.78rem',
              color: barColor,
            }}>
              {isPos ? '+' : ''}{t.diff.toFixed(1)}
            </div>

            {/* streak badge */}
            <div style={{
              textAlign: 'center',
              fontFamily: 'var(--d3-mono)',
              fontWeight: 700,
              fontSize: '0.68rem',
              color: streakColor,
              background: `${streakColor}18`,
              border: `1px solid ${streakColor}40`,
              borderRadius: 4,
              padding: '1px 4px',
            }}>
              {t.streak}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Option B: CSS diverging ranked list ──────────────────────────────────────
function SvgBars({ teams }: { teams: TeamData[] }) {
  const ROW_H = 24;
  const TOP   = 2;
  const IW    = 800;
  const LBL_W = 52;   // left label area
  const VAL_W = 72;   // right value + streak area
  const CHART  = IW - LBL_W - VAL_W;  // 676
  const CX     = LBL_W + CHART / 2;   // center x
  const MAX_B  = CHART / 2;           // max bar width in each direction
  const IH     = teams.length * ROW_H + TOP * 2;
  const maxAbs = Math.max(...teams.map(t => Math.abs(t.diff)), 1);

  return (
    <svg width="100%" viewBox={`0 0 ${IW} ${IH}`} style={{ display: 'block' }}>
      <defs>
        <linearGradient id="sg-green" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={HEX_GREEN} />
          <stop offset="100%" stopColor={HEX_GREEN} stopOpacity={0.2} />
        </linearGradient>
        <linearGradient id="sg-red" x1="100%" y1="0%" x2="0%" y2="0%">
          <stop offset="0%" stopColor={HEX_RED} />
          <stop offset="100%" stopColor={HEX_RED} stopOpacity={0.2} />
        </linearGradient>
      </defs>

      {teams.map((t, i) => {
        const y    = TOP + i * ROW_H;
        const cy   = y + ROW_H / 2;
        const bH   = 11;
        const bY   = cy - bH / 2;
        const isP  = t.diff >= 0;
        const bW   = (Math.abs(t.diff) / maxAbs) * MAX_B;
        const sc   = t.streak.startsWith('W') ? HEX_GREEN : t.streak.startsWith('L') ? HEX_RED : HEX_MUTED;

        return (
          <g key={t.abbr}>
            {i > 0 && <line x1={0} y1={y} x2={IW} y2={y} stroke="rgba(255,255,255,0.05)" strokeWidth={0.5} />}

            {/* team abbr */}
            <text x={LBL_W - 8} y={cy} textAnchor="end" dominantBaseline="central"
              fill={HEX_FG} fontSize={11} fontWeight="700" fontFamily="Nunito, sans-serif">
              {t.abbr}
            </text>

            {/* bar */}
            {isP
              ? <rect x={CX} y={bY} width={bW} height={bH} rx={2} fill="url(#sg-green)" />
              : <rect x={CX - bW} y={bY} width={bW} height={bH} rx={2} fill="url(#sg-red)" />
            }

            {/* center spine */}
            <line x1={CX} y1={y + 3} x2={CX} y2={y + ROW_H - 3}
              stroke="rgba(255,255,255,0.2)" strokeWidth={0.75} />

            {/* diff value */}
            <text x={IW - VAL_W + 6} y={cy} textAnchor="start" dominantBaseline="central"
              fill={isP ? HEX_GREEN : HEX_RED} fontSize={10} fontWeight="700" fontFamily="monospace">
              {isP ? '+' : ''}{t.diff.toFixed(1)}
            </text>

            {/* streak */}
            <text x={IW - 6} y={cy} textAnchor="end" dominantBaseline="central"
              fill={sc} fontSize={9} fontFamily="monospace" fontWeight="700">
              {t.streak}
            </text>
          </g>
        );
      })}

      {/* zero line cap at top/bottom */}
      <line x1={CX} y1={TOP} x2={CX} y2={IH - TOP}
        stroke="rgba(255,255,255,0.12)" strokeWidth={1} strokeDasharray="3 3" />
    </svg>
  );
}

// ── Option C: Bloomberg heat-map grid ────────────────────────────────────────
function HeatMap({ teams }: { teams: TeamData[] }) {
  type ColDef = { key: keyof TeamData; label: string; dir: 'high' | 'low' | 'div'; fmt: (v: number) => string };
  const cols: ColDef[] = [
    { key: 'ppg',  label: 'PPG',  dir: 'high', fmt: v => v.toFixed(1) },
    { key: 'papg', label: 'PAPG', dir: 'low',  fmt: v => v.toFixed(1) },
    { key: 'diff', label: 'DIFF', dir: 'div',  fmt: v => (v > 0 ? '+' : '') + v.toFixed(1) },
    { key: 'pct',  label: 'W%',   dir: 'high', fmt: v => v.toFixed(3) },
  ];

  const ranges = Object.fromEntries(cols.map(c => {
    const vals = teams.map(t => t[c.key] as number);
    return [c.key, { min: Math.min(...vals), max: Math.max(...vals) }];
  }));

  function cellBg(key: string, val: number, dir: 'high' | 'low' | 'div'): string {
    const { min, max } = ranges[key];
    if (max === min) return 'transparent';
    const norm = (val - min) / (max - min);
    if (dir === 'high') return `rgba(74,222,128,${(norm * 0.5).toFixed(2)})`;
    if (dir === 'low')  return `rgba(74,222,128,${((1 - norm) * 0.5).toFixed(2)})`;
    if (val >= 0) return `rgba(74,222,128,${((val / (max || 1)) * 0.55).toFixed(2)})`;
    return `rgba(239,68,68,${((Math.abs(val) / (Math.abs(min) || 1)) * 0.55).toFixed(2)})`;
  }

  const cell: React.CSSProperties = {
    padding: '5px 10px', textAlign: 'center' as const,
    fontFamily: 'var(--d3-mono)', fontWeight: 600, fontSize: '0.75rem',
    color: 'var(--foreground)',
  };
  const th: React.CSSProperties = {
    padding: '6px 10px', textAlign: 'center' as const,
    fontSize: '0.6rem', fontWeight: 700, color: MUTED_FG,
    letterSpacing: '0.1em', borderBottom: `1px solid ${BORDER}`,
  };

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead>
          <tr>
            <th style={{ ...th, textAlign: 'left' }}>TEAM</th>
            {cols.map(c => <th key={c.key} style={th}>{c.label}</th>)}
            <th style={th}>STREAK</th>
            <th style={th}>L10</th>
            <th style={{ ...th, textAlign: 'left' }}>HOME</th>
            <th style={{ ...th, textAlign: 'left' }}>ROAD</th>
          </tr>
        </thead>
        <tbody>
          {teams.map(t => {
            const sc = t.streak.startsWith('W') ? HEX_GREEN : t.streak.startsWith('L') ? HEX_RED : HEX_MUTED;
            const sn = Math.abs(streakNum(t.streak));
            const sBg = t.streak.startsWith('W')
              ? `rgba(74,222,128,${Math.min(sn / 10, 1) * 0.45})`
              : t.streak.startsWith('L')
              ? `rgba(239,68,68,${Math.min(sn / 10, 1) * 0.45})`
              : 'transparent';

            return (
              <tr key={t.abbr} style={{ borderBottom: `1px solid ${BORDER}` }}>
                <td style={{ padding: '5px 10px', whiteSpace: 'nowrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <img src={t.logo} alt="" style={{ width: 15, height: 15, objectFit: 'contain' }} />
                    <span style={{ fontWeight: 700, color: 'var(--foreground)', fontSize: '0.78rem' }}>{t.abbr}</span>
                    <span style={{ color: MUTED_FG, fontSize: '0.6rem', fontFamily: 'var(--d3-mono)' }}>{t.wins}-{t.losses}</span>
                  </div>
                </td>
                {cols.map(c => {
                  const val = t[c.key] as number;
                  return (
                    <td key={c.key} style={{ ...cell, background: cellBg(c.key as string, val, c.dir) }}>
                      {c.fmt(val)}
                    </td>
                  );
                })}
                <td style={{ ...cell, background: sBg, color: sc, fontWeight: 700 }}>{t.streak}</td>
                <td style={{ ...cell, color: MUTED_FG }}>{t.last10}</td>
                <td style={{ padding: '5px 10px', fontFamily: 'var(--d3-mono)', fontSize: '0.75rem', color: MUTED_FG }}>{t.homeRecord}</td>
                <td style={{ padding: '5px 10px', fontFamily: 'var(--d3-mono)', fontSize: '0.75rem', color: MUTED_FG }}>{t.roadRecord}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
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
