/**
 * Line Movement — Live odds board + movement history charts.
 * Shows current lines from line_snapshots and movement over time.
 */
import { useState, useEffect, useCallback } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { TrendingUp, TrendingDown, Minus, RefreshCw } from 'lucide-react';
import '../styles/analytics.css';
import { getApiUrl } from '../config';

const EMERALD   = 'oklch(69.6% .17 162.48)';
const BRAND_RED = 'oklch(63.7% .237 25.331)';
const BLUE      = 'oklch(62.3% .214 259.815)';
const YELLOW    = 'oklch(79.5% .184 86.047)';
const MUTED_FG  = 'oklch(70.8% 0 0)';
const BORDER    = 'oklch(100% 0 0 / .1)';
const CARD_BG   = 'oklch(24% 0 0)';

const SPORT_LABELS: Record<string, string> = {
  baseball_mlb: 'MLB', basketball_wnba: 'WNBA',
  americanfootball_nfl: 'NFL', americanfootball_ncaaf: 'NCAAF',
  basketball_nba: 'NBA', basketball_ncaab: 'NCAAB',
  icehockey_nhl: 'NHL', mma_mixed_martial_arts: 'MMA',
};

interface LineSnapshot {
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  game_time: string;
  spread_home: number | null;
  total_line: number | null;
  home_ml: number | null;
  away_ml: number | null;
  snapshot_at: string;
}

interface GameMovement {
  snapshots: LineSnapshot[];
  movement: Record<string, { open: number; current: number; delta: number }>;
}

function fmtOdds(n: number | null): string {
  if (n == null) return '—';
  return n >= 0 ? `+${n}` : `${n}`;
}

function fmtSpread(n: number | null): string {
  if (n == null) return '—';
  return n >= 0 ? `+${n}` : `${n}`;
}

function MovementArrow({ delta }: { delta: number | null | undefined }) {
  if (!delta) return <Minus size={12} style={{ color: MUTED_FG }} />;
  if (delta > 0) return <TrendingUp size={12} style={{ color: EMERALD }} />;
  return <TrendingDown size={12} style={{ color: BRAND_RED }} />;
}

export function LineMovement() {
  const [games, setGames] = useState<LineSnapshot[]>([]);
  const [selectedGame, setSelectedGame] = useState<string | null>(null);
  const [gameDetail, setGameDetail] = useState<GameMovement | null>(null);
  const [sportFilter, setSportFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchGames = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(getApiUrl('line-movement'));
      const d = await r.json();
      setGames(d.games ?? []);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { fetchGames(); }, [fetchGames]);

  const fetchDetail = useCallback(async (gameId: string) => {
    setDetailLoading(true);
    setSelectedGame(gameId);
    try {
      const r = await fetch(getApiUrl(`line-movement/${gameId}`));
      setGameDetail(await r.json());
    } catch { /* ignore */ }
    setDetailLoading(false);
  }, []);

  const sports = [...new Set(games.map(g => g.sport))].sort();
  const filtered = sportFilter === 'all' ? games : games.filter(g => g.sport === sportFilter);

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1>Line Movement</h1>
            <p className="subtitle">
              Live odds board — track spread, total, and moneyline movement across all sports
            </p>
          </div>
          <button onClick={fetchGames} disabled={loading} style={{
            display: 'flex', alignItems: 'center', gap: 6, padding: '6px 14px',
            borderRadius: 6, background: 'var(--muted)', border: `1px solid ${BORDER}`,
            color: 'var(--foreground)', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer',
          }}>
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            REFRESH
          </button>
        </div>

        <div className="sport-tabs" style={{ marginTop: 12 }}>
          <button
            className={`sport-tab ${sportFilter === 'all' ? 'active' : ''}`}
            onClick={() => setSportFilter('all')}
          >
            ALL ({games.length})
          </button>
          {sports.map(s => (
            <button
              key={s}
              className={`sport-tab ${sportFilter === s ? 'active' : ''}`}
              onClick={() => setSportFilter(s)}
            >
              {SPORT_LABELS[s] ?? s.toUpperCase()} ({games.filter(g => g.sport === s).length})
            </button>
          ))}
        </div>
      </div>

      <div style={{ padding: '16px 24px', display: 'flex', gap: 16 }}>
        {/* Games list */}
        <div style={{ flex: 1, maxWidth: 700 }}>
          <OddsTable games={filtered} selectedId={selectedGame} onSelect={fetchDetail} />
        </div>

        {/* Detail panel */}
        <div style={{ flex: 1, minWidth: 300 }}>
          {selectedGame && gameDetail ? (
            <MovementDetail data={gameDetail} loading={detailLoading} />
          ) : (
            <div style={{
              background: CARD_BG, border: `1px solid ${BORDER}`, borderRadius: 6,
              padding: 40, textAlign: 'center', color: MUTED_FG, fontSize: '0.85rem',
            }}>
              Select a game to see line movement history
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function OddsTable({ games, selectedId, onSelect }: {
  games: LineSnapshot[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
        <thead>
          <tr>
            {['Game', 'Sport', 'Spread', 'Total', 'Home ML', 'Away ML'].map(h => (
              <th key={h} style={{
                padding: '8px 10px', textAlign: h === 'Game' ? 'left' : 'right',
                fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG,
                letterSpacing: '0.1em', textTransform: 'uppercase',
                borderBottom: `1px solid ${BORDER}`,
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {games.map(g => (
            <tr
              key={g.game_id}
              onClick={() => onSelect(g.game_id)}
              style={{
                borderBottom: `1px solid ${BORDER}`,
                cursor: 'pointer',
                background: selectedId === g.game_id ? 'oklch(26% 0 0)' : 'transparent',
              }}
            >
              <td style={{ padding: '8px 10px', fontWeight: 600, color: 'var(--foreground)' }}>
                {g.away_team} @ {g.home_team}
              </td>
              <td style={{ padding: '8px 10px', textAlign: 'right', color: MUTED_FG, fontSize: '0.7rem' }}>
                {SPORT_LABELS[g.sport] ?? g.sport}
              </td>
              <td style={{ padding: '8px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: 'var(--foreground)' }}>
                {fmtSpread(g.spread_home)}
              </td>
              <td style={{ padding: '8px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: BLUE }}>
                {g.total_line ?? '—'}
              </td>
              <td style={{ padding: '8px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: g.home_ml && g.home_ml < 0 ? EMERALD : MUTED_FG }}>
                {fmtOdds(g.home_ml)}
              </td>
              <td style={{ padding: '8px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', color: g.away_ml && g.away_ml < 0 ? EMERALD : MUTED_FG }}>
                {fmtOdds(g.away_ml)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {games.length === 0 && (
        <div style={{ padding: 24, textAlign: 'center', color: MUTED_FG }}>No games found</div>
      )}
    </div>
  );
}

function MovementDetail({ data, loading }: { data: GameMovement; loading: boolean }) {
  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: MUTED_FG }}>Loading...</div>;

  const snaps = data.snapshots ?? [];
  const movement = data.movement ?? {};
  const hasMovement = Object.keys(movement).length > 0;

  if (snaps.length === 0) {
    return (
      <div style={{
        background: CARD_BG, border: `1px solid ${BORDER}`, borderRadius: 6,
        padding: 24, color: MUTED_FG, fontSize: '0.85rem',
      }}>
        No snapshot history for this game yet.
      </div>
    );
  }

  const game = snaps[0];
  const chartData = snaps.map(s => ({
    time: new Date(s.snapshot_at).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }),
    spread: s.spread_home,
    total: s.total_line,
    homeML: s.home_ml,
    awayML: s.away_ml,
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Game header */}
      <div className="data-table-wrap" style={{ padding: '14px 18px' }}>
        <div style={{ fontWeight: 800, fontSize: '0.95rem', color: 'var(--foreground)', marginBottom: 4 }}>
          {game.away_team} @ {game.home_team}
        </div>
        <div style={{ fontSize: '0.72rem', color: MUTED_FG }}>
          {SPORT_LABELS[game.sport] ?? game.sport} — {snaps.length} snapshot{snaps.length > 1 ? 's' : ''}
        </div>
      </div>

      {/* Movement summary */}
      {hasMovement && (
        <div className="data-table-wrap" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
            Line Movement
          </div>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            {Object.entries(movement).map(([field, m]) => (
              <div key={field} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <MovementArrow delta={m.delta} />
                <span style={{ fontSize: '0.72rem', color: MUTED_FG }}>
                  {field.replace('_', ' ')}:
                </span>
                <span style={{ fontSize: '0.78rem', fontWeight: 700, fontFamily: 'var(--d3-mono)', color: 'var(--foreground)' }}>
                  {m.open} → {m.current}
                </span>
                <span style={{
                  fontSize: '0.68rem', fontWeight: 700, fontFamily: 'var(--d3-mono)',
                  color: m.delta > 0 ? EMERALD : BRAND_RED,
                }}>
                  ({m.delta > 0 ? '+' : ''}{m.delta})
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chart */}
      {snaps.length > 1 && (
        <>
          <ChartCard title="Spread" dataKey="spread" data={chartData} color={EMERALD} />
          <ChartCard title="Total" dataKey="total" data={chartData} color={BLUE} />
          <ChartCard title="Home ML" dataKey="homeML" data={chartData} color={YELLOW} />
        </>
      )}

      {snaps.length === 1 && (
        <div className="data-table-wrap" style={{ padding: '14px 18px' }}>
          <div style={{ fontSize: '0.78rem', color: MUTED_FG }}>
            Only 1 snapshot captured. Charts appear when multiple snapshots are available
            (line tracker runs periodically to capture movement).
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 12 }}>
            <StatBox label="Spread" value={fmtSpread(game.spread_home)} />
            <StatBox label="Total" value={game.total_line?.toString() ?? '—'} color={BLUE} />
            <StatBox label="Home ML" value={fmtOdds(game.home_ml)} />
            <StatBox label="Away ML" value={fmtOdds(game.away_ml)} />
          </div>
        </div>
      )}
    </div>
  );
}

function ChartCard({ title, dataKey, data, color }: {
  title: string; dataKey: string; data: any[]; color: string;
}) {
  return (
    <div className="data-table-wrap" style={{ padding: '14px 18px' }}>
      <div style={{ fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
        {title}
      </div>
      <ResponsiveContainer width="100%" height={120}>
        <AreaChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={`grad-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="oklch(100% 0 0 / .05)" />
          <XAxis dataKey="time" tick={{ fill: MUTED_FG, fontSize: 9 }} tickLine={false} axisLine={false} />
          <YAxis domain={['auto', 'auto']} tick={{ fill: MUTED_FG, fontSize: 10, fontFamily: 'var(--d3-mono)' }} tickLine={false} axisLine={false} width={40} />
          <Tooltip
            contentStyle={{ background: 'oklch(20% 0 0)', border: `1px solid ${BORDER}`, borderRadius: 6, fontSize: '0.75rem' }}
            labelStyle={{ color: MUTED_FG }}
          />
          <Area type="monotone" dataKey={dataKey} stroke={color} fill={`url(#grad-${dataKey})`} strokeWidth={2} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function StatBox({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{ background: 'oklch(22% 0 0)', borderRadius: 6, padding: '8px 12px' }}>
      <div style={{ fontSize: '0.62rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase' }}>{label}</div>
      <div style={{ fontSize: '1.1rem', fontWeight: 800, fontFamily: 'var(--d3-mono)', color: color ?? 'var(--foreground)', marginTop: 2 }}>{value}</div>
    </div>
  );
}

export default LineMovement;
