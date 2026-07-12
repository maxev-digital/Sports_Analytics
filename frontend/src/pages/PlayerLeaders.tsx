import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  AreaChart, Area,
} from 'recharts';
import '../styles/analytics.css';
import { getApiUrl } from '../config';

// ── Design tokens ──────────────────────────────────────────────────────────
const BRAND_RED  = 'oklch(63.7% .237 25.331)';
const EMERALD    = 'oklch(69.6% .17 162.48)';
const BLUE       = 'oklch(62.3% .214 259.815)';
const YELLOW     = 'oklch(79.5% .184 86.047)';
const MUTED_FG   = 'oklch(70.8% 0 0)';
const SIDEBAR_BG = 'oklch(20.5% 0 0)';
const BORDER     = 'oklch(100% 0 0 / .1)';

const STAT_COLORS = [BRAND_RED, EMERALD, BLUE, YELLOW,
  'oklch(69% .18 290)', 'oklch(74% .17 205)', 'oklch(70% .15 47)'];

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

type Sport = 'mlb' | 'nba' | 'wnba' | 'nfl' | 'nhl';

const SPORTS: { key: Sport; label: string }[] = [
  { key: 'mlb',  label: 'MLB'  },
  { key: 'nba',  label: 'NBA'  },
  { key: 'wnba', label: 'WNBA' },
  { key: 'nfl',  label: 'NFL'  },
  { key: 'nhl',  label: 'NHL'  },
];

// ESPN stat categories per sport displayed in the grid
const STAT_DISPLAY: Record<Sport, number> = {
  mlb: 6, nba: 8, wnba: 6, nfl: 6, nhl: 5,
};

interface Leader {
  name: string;
  shortName: string;
  headshot: string;
  team: string;
  teamName: string;
  teamColor: string;
  value: number;
  displayValue: string;
}

interface Category {
  name: string;
  displayName: string;
  shortName: string;
  leaders: Leader[];
}

// ── Mini horizontal bar chart for one stat category ───────────────────────
function StatLeaderCard({ cat, color }: { cat: Category; color: string }) {
  const top8 = cat.leaders.slice(0, 8);

  return (
    <div className="data-table-wrap" style={{ padding: '16px' }}>
      <p className="section-title" style={{ marginBottom: 12, color }}>{cat.displayName}</p>

      {/* Small bar chart */}
      <ResponsiveContainer width="100%" height={180}>
        <BarChart
          data={top8}
          layout="vertical"
          margin={{ top: 0, right: 40, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={BORDER} horizontal={false} />
          <XAxis
            type="number"
            domain={[0, 'dataMax']}
            tick={{ fill: MUTED_FG, fontSize: 10, fontFamily: 'Nunito' }}
            axisLine={{ stroke: BORDER }}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="shortName"
            width={80}
            tick={{ fill: 'oklch(98.5% 0 0)', fontSize: 10, fontFamily: 'Nunito', fontWeight: 600 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<DarkTooltip />} />
          <Bar dataKey="value" name={cat.shortName} radius={[0, 3, 3, 0]} fill={color} fillOpacity={0.85}>
            {top8.map((_, i) => (
              <Cell key={i} fill={color} fillOpacity={1 - i * 0.07} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Compact leader list */}
      <div style={{ marginTop: 10 }}>
        {cat.leaders.slice(0, 5).map((p, i) => (
          <div key={p.name} style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '5px 0',
            borderBottom: i < 4 ? `1px solid ${BORDER}` : 'none',
          }}>
            <span style={{
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              width: 20, height: 20, borderRadius: 3, fontSize: '0.65rem', fontWeight: 800,
              flexShrink: 0,
              background: i === 0 ? color : 'oklch(26.9% 0 0)',
              color: i === 0 ? '#fff' : MUTED_FG,
            }}>{i + 1}</span>

            {p.headshot && (
              <img
                src={p.headshot}
                alt={p.shortName}
                style={{ width: 24, height: 24, borderRadius: '50%', objectFit: 'cover', flexShrink: 0, background: 'oklch(26.9% 0 0)' }}
                onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
              />
            )}

            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'oklch(98.5% 0 0)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {p.name}
              </div>
              <div style={{ fontSize: '0.68rem', color: MUTED_FG }}>{p.team}</div>
            </div>

            <div style={{ fontSize: '1rem', fontWeight: 800, color, flexShrink: 0 }}>
              {p.displayValue}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── NBA player leaders from NBA.com ────────────────────────────────────────
function NBAPlayerLeaders() {
  const [stat, setStat] = useState('PTS');
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const stats = [
    { key: 'PTS', label: 'Points' }, { key: 'REB', label: 'Rebounds' },
    { key: 'AST', label: 'Assists' }, { key: 'STL', label: 'Steals' },
    { key: 'BLK', label: 'Blocks' }, { key: 'FG_PCT', label: 'FG%' },
    { key: 'FG3_PCT', label: '3P%' }, { key: 'FT_PCT', label: 'FT%' },
  ];

  useEffect(() => {
    setLoading(true); setError('');
    fetch(getApiUrl(`analytics-data/nba/player-leaders?stat=${stat}&limit=25`))
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(d => { setData(d.players || []); setLoading(false); })
      .catch(() => { setError('NBA.com player data unavailable'); setLoading(false); });
  }, [stat]);

  const top10 = data.slice(0, 10);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      <div className="filter-bar" style={{ paddingLeft: 0, background: 'transparent', border: 'none' }}>
        <span className="filter-label">Stat</span>
        {stats.map(s => (
          <button key={s.key} className={`filter-pill${stat === s.key ? ' active' : ''}`} onClick={() => setStat(s.key)}>
            {s.label}
          </button>
        ))}
      </div>

      {loading && <div className="skeleton" style={{ height: 300, borderRadius: 8 }} />}
      {error && <div className="empty-state"><p>{error}</p></div>}

      {!loading && !error && top10.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Chart */}
          <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
            <p className="section-title" style={{ marginBottom: 16 }}>{stats.find(s => s.key === stat)?.label} Leaders — Top 10</p>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={top10} margin={{ top: 4, right: 16, left: 0, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={BORDER} vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fill: MUTED_FG, fontSize: 10, fontFamily: 'Nunito' }}
                  axisLine={{ stroke: BORDER }}
                  tickLine={false}
                  angle={-40}
                  textAnchor="end"
                  interval={0}
                />
                <YAxis tick={{ fill: MUTED_FG, fontSize: 11, fontFamily: 'Nunito' }} axisLine={false} tickLine={false} />
                <Tooltip content={<DarkTooltip />} />
                <Bar dataKey="value" name={stat} radius={[3,3,0,0]}>
                  {top10.map((_, i) => (
                    <Cell key={i} fill={i < 3 ? BRAND_RED : i < 6 ? EMERALD : BLUE} fillOpacity={0.85} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Radar — top 5 players compared across all key stats */}
          {(() => {
            const top5 = data.slice(0, 5);
            if (top5.length < 2) return null;
            const DIMS = [
              { key: 'pts', label: 'PTS' }, { key: 'reb', label: 'REB' },
              { key: 'ast', label: 'AST' }, { key: 'stl', label: 'STL' },
              { key: 'blk', label: 'BLK' },
            ];
            const maxes: Record<string, number> = {};
            DIMS.forEach(d => {
              maxes[d.key] = Math.max(...data.map((p: any) => p[d.key] ?? 0)) || 1;
            });
            const radarData = DIMS.map(d => {
              const row: any = { stat: d.label };
              top5.forEach((p: any, i: number) => {
                row[`p${i}`] = Math.round(((p[d.key] ?? 0) / maxes[d.key]) * 100);
              });
              return row;
            });
            const RADAR_COLORS = [BRAND_RED, EMERALD, BLUE, YELLOW, 'oklch(69% .18 290)'];
            return (
              <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
                <p className="section-title" style={{ marginBottom: 4 }}>Player Profile Radar — Top 5 (normalized)</p>
                <p style={{ fontSize: '0.75rem', color: MUTED_FG, marginBottom: 12 }}>Each axis = % of top player in dataset for that category. Larger web = more complete player. A player who fills all 5 axes is an elite two-way contributor.</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
                  {top5.map((p: any, i: number) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem' }}>
                      <div style={{ width: 10, height: 10, borderRadius: 2, background: RADAR_COLORS[i], flexShrink: 0 }} />
                      <span style={{ color: 'oklch(98.5% 0 0)', fontWeight: 600 }}>{p.name?.split(' ').slice(-1)[0] ?? p.name}</span>
                    </div>
                  ))}
                </div>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={radarData} margin={{ top: 10, right: 30, left: 30, bottom: 10 }}>
                    <PolarGrid stroke={BORDER} />
                    <PolarAngleAxis dataKey="stat" tick={{ fill: MUTED_FG, fontSize: 12, fontFamily: 'Nunito', fontWeight: 700 }} />
                    {top5.map((_: any, i: number) => (
                      <Radar key={i} name={top5[i].name} dataKey={`p${i}`} stroke={RADAR_COLORS[i]} fill={RADAR_COLORS[i]} fillOpacity={0.1} strokeWidth={2} />
                    ))}
                    <Tooltip content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      return <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '8px 12px', fontSize: '0.78rem' }}>
                        {payload.map((p: any, i: number) => <p key={i} style={{ color: p.color, margin: '2px 0' }}>{top5[i]?.name}: <strong>{p.value}/100</strong></p>)}
                      </div>;
                    }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            );
          })()}

          {/* AreaChart — stat falloff from rank 1 → 10 */}
          <div className="data-table-wrap" style={{ padding: '20px 16px' }}>
            <p className="section-title" style={{ marginBottom: 4 }}>{stats.find(s => s.key === stat)?.label} Falloff — Rank 1 to {top10.length}</p>
            <p style={{ fontSize: '0.75rem', color: MUTED_FG, marginBottom: 12 }}>Steep drop after rank 3-4 = stat is concentrated in a few players (fade middle of leaderboard in props). Gradual slope = many players are close in value.</p>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={top10.map((p: any, i: number) => ({ rank: i + 1, value: p.value, name: p.name }))} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
                <defs>
                  <linearGradient id="statFalloff" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor={BRAND_RED} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={BRAND_RED} stopOpacity={0.03} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={BORDER} vertical={false} />
                <XAxis dataKey="rank" tick={{ fill: MUTED_FG, fontSize: 11, fontFamily: 'Nunito' }} axisLine={{ stroke: BORDER }} tickLine={false} label={{ value: 'Rank', position: 'insideBottom', offset: -2, fill: MUTED_FG, fontSize: 10 }} />
                <YAxis tick={{ fill: MUTED_FG, fontSize: 11, fontFamily: 'Nunito' }} axisLine={{ stroke: BORDER }} tickLine={false} domain={['auto', 'auto']} />
                <Tooltip content={({ active, payload }) => {
                  if (!active || !payload?.length) return null;
                  const d = payload[0]?.payload;
                  return <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '8px 12px', fontSize: '0.78rem' }}>
                    <p style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700 }}>#{d?.rank} {d?.name}</p>
                    <p style={{ color: BRAND_RED }}>{stat}: <strong>{d?.value?.toFixed(1)}</strong></p>
                  </div>;
                }} />
                <Area type="monotone" dataKey="value" name={stat} stroke={BRAND_RED} fill="url(#statFalloff)" strokeWidth={2} dot={{ fill: BRAND_RED, r: 3 }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Full table */}
          <div className="data-table-wrap">
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ width: 44 }}>#</th>
                    <th style={{ textAlign: 'left' }}>PLAYER</th>
                    <th>TEAM</th><th>GP</th><th>MIN</th>
                    <th style={{ color: BRAND_RED }}>{stat}</th>
                    <th>PTS</th><th>REB</th><th>AST</th>
                    <th>STL</th><th>BLK</th>
                    <th>FG%</th><th>3P%</th><th>FT%</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((p, i) => (
                    <tr key={p.name}>
                      <td><span className={`rank-badge${i < 3 ? ' top5' : ''}`}>{p.rank}</span></td>
                      <td><div className="team-cell"><span className="team-name">{p.name}</span></div></td>
                      <td>{p.team}</td>
                      <td>{p.gp}</td>
                      <td>{p.min?.toFixed(1)}</td>
                      <td style={{ color: BRAND_RED, fontWeight: 800 }}>{p.value?.toFixed(1)}</td>
                      <td>{p.pts?.toFixed(1)}</td>
                      <td>{p.reb?.toFixed(1)}</td>
                      <td>{p.ast?.toFixed(1)}</td>
                      <td>{p.stl?.toFixed(1)}</td>
                      <td>{p.blk?.toFixed(1)}</td>
                      <td>{p.fgPct ? (p.fgPct * 100).toFixed(1) + '%' : '—'}</td>
                      <td>{p.fg3Pct ? (p.fg3Pct * 100).toFixed(1) + '%' : '—'}</td>
                      <td>{p.ftPct ? (p.ftPct * 100).toFixed(1) + '%' : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── ESPN Leaders Grid ──────────────────────────────────────────────────────
function ESPNLeaders({ sport }: { sport: Sport }) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const count = STAT_DISPLAY[sport];

  useEffect(() => {
    setLoading(true); setError('');
    fetch(getApiUrl(`analytics-data/leaders/${sport}?limit=15`))
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(d => { setCategories(d.categories || []); setLoading(false); })
      .catch(() => { setError(`Leaders unavailable for ${sport.toUpperCase()}`); setLoading(false); });
  }, [sport]);

  if (loading) return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="skeleton" style={{ height: 320, borderRadius: 8 }} />
      ))}
    </div>
  );

  if (error) return <div className="empty-state"><h3>Unavailable</h3><p>{error}</p></div>;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
      {categories.slice(0, count).map((cat, i) => (
        <StatLeaderCard key={cat.name} cat={cat} color={STAT_COLORS[i % STAT_COLORS.length]} />
      ))}
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

export function PlayerLeaders() {
  const [sport, setSport] = useState<Sport>('mlb');

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1>Player Leaders</h1>
        <p className="subtitle">Season stat leaders across all major sports</p>
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

      <div className="analytics-content">
        {sport === 'nba' ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className="filter-bar" style={{ paddingLeft: 0, background: 'transparent', border: 'none' }}>
              <span className="filter-label" style={{ fontSize: '0.7rem' }}>Enhanced player-level data available for this sport</span>
            </div>
            <NBAPlayerLeaders />
          </div>
        ) : (
          <ESPNLeaders sport={sport} />
        )}
      </div>
    </div>
  );
}
