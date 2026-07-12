import { useState, useEffect, useCallback } from 'react';
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis,
  CartesianGrid, Tooltip, ResponsiveContainer,
  Cell, ReferenceLine,
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

// ── Types ──────────────────────────────────────────────────────────────────
interface Pick {
  sport: string;
  home_team: string;
  away_team: string;
  game_time_cst: string | null;
  pick_side: string;        // 'home'|'away'|'over'|'under'
  pick_type: string;        // 'ml'|'spread'|'total'
  our_probability: number;
  market_odds: number;      // american odds e.g. -110, +150
  market_implied_prob: number;
  edge_pct: number;
  detector: string;
  confidence_tier: string | null;  // 'high'|'medium'|'low'
  sonnet_narrative: string | null;
  features: Record<string, number> | null;
}

// ── Helper functions ───────────────────────────────────────────────────────
function fmtOdds(odds: number): string {
  return odds >= 0 ? `+${odds}` : `${odds}`;
}

function fmtEdge(edge: number): string {
  return `+${edge.toFixed(1)}%`;
}

function fmtProb(prob: number): string {
  return `${(prob * 100).toFixed(1)}%`;
}

function fmtGameTime(ts: string | null): string {
  if (!ts) return 'TBD';
  try {
    const dt = new Date(ts);
    if (isNaN(dt.getTime())) return ts;
    const now = new Date();
    const isToday = dt.toDateString() === now.toDateString();
    const time = dt.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
    if (isToday) return `Today ${time} CST`;
    const date = dt.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    return `${date} ${time} CST`;
  } catch {
    return ts;
  }
}

function getConfColor(tier: string | null): string {
  if (tier === 'high')   return EMERALD;
  if (tier === 'medium') return YELLOW;
  if (tier === 'low')    return BRAND_RED;
  return MUTED_FG;
}

function getSportColor(sport: string): string {
  const map: Record<string, string> = {
    mlb: BRAND_RED, wnba: BLUE, nfl: BLUE, ncaaf: YELLOW,
    nba: EMERALD, tennis_atp: YELLOW, tennis_wta: YELLOW,
    soccer_mls: EMERALD, soccer_epl: EMERALD,
  };
  return map[sport] ?? MUTED_FG;
}

function getPickLabel(p: Pick): string {
  if (p.pick_type === 'total') return p.pick_side.toUpperCase();
  const team = p.pick_side === 'home' ? p.home_team : p.away_team;
  const short = team.split(' ').pop() ?? team;
  if (p.pick_type === 'ml')     return `${short} ML`;
  if (p.pick_type === 'spread') return `${short} SPREAD`;
  return `${short} ${p.pick_type.toUpperCase()}`;
}

// ── Scatter tooltip ────────────────────────────────────────────────────────
function ScatterTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const p: Pick = payload[0].payload.pick;
  return (
    <div style={{
      background: 'oklch(24% 0 0)',
      border: `1px solid oklch(100% 0 0 / .18)`,
      borderRadius: 6,
      padding: '10px 14px',
      fontSize: '0.8rem',
      color: 'oklch(98.5% 0 0)',
      maxWidth: 280,
      lineHeight: 1.5,
    }}>
      <div style={{ fontWeight: 800, marginBottom: 3 }}>
        {p.away_team} @ {p.home_team}
      </div>
      <div style={{ color: MUTED_FG, fontSize: '0.73rem', marginBottom: 8 }}>
        {fmtGameTime(p.game_time_cst)}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <span>
          <span style={{ color: MUTED_FG }}>Pick: </span>
          <strong>{getPickLabel(p)}</strong>
        </span>
        <span>
          <span style={{ color: MUTED_FG }}>Type: </span>
          {p.pick_type.toUpperCase()}
        </span>
        <span>
          <span style={{ color: EMERALD }}>Edge: </span>
          <strong style={{ color: EMERALD }}>{fmtEdge(p.edge_pct)}</strong>
        </span>
        <span>
          <span style={{ color: MUTED_FG }}>Our Prob: </span>
          {fmtProb(p.our_probability)}
        </span>
        <span>
          <span style={{ color: MUTED_FG }}>Market: </span>
          {fmtOdds(p.market_odds)}
        </span>
        {p.sonnet_narrative && (
          <div style={{
            marginTop: 6,
            paddingTop: 6,
            borderTop: `1px solid oklch(100% 0 0 / .1)`,
            color: MUTED_FG,
            fontStyle: 'italic',
            fontSize: '0.75rem',
          }}>
            {p.sonnet_narrative.length > 140
              ? p.sonnet_narrative.slice(0, 137) + '...'
              : p.sonnet_narrative}
          </div>
        )}
      </div>
    </div>
  );
}

// ── PickCard ───────────────────────────────────────────────────────────────
interface PickCardProps {
  pick: Pick;
  idx: number;
  expanded: boolean;
  onToggle: () => void;
}

function PickCard({ pick, idx, expanded, onToggle }: PickCardProps) {
  const confColor  = getConfColor(pick.confidence_tier);
  const sportColor = getSportColor(pick.sport);
  const features   = pick.features ? Object.entries(pick.features) : [];

  function Badge({ color, label }: { color: string; label: string }) {
    return (
      <span style={{
        padding: '2px 9px',
        borderRadius: 20,
        fontSize: '0.67rem',
        fontWeight: 700,
        letterSpacing: '0.08em',
        textTransform: 'uppercase' as const,
        background: `color-mix(in oklch, ${color} 18%, transparent)`,
        color,
        border: `1px solid color-mix(in oklch, ${color} 40%, transparent)`,
      }}>{label}</span>
    );
  }

  return (
    <div
      className="data-table-wrap"
      style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}
    >
      {/* Badges row */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
        <Badge color={sportColor} label={pick.sport} />
        <Badge color={MUTED_FG} label={pick.pick_type} />
        {pick.confidence_tier && (
          <Badge color={confColor} label={pick.confidence_tier} />
        )}
      </div>

      {/* Matchup */}
      <div>
        <div style={{ fontSize: '1rem', fontWeight: 800, color: 'oklch(98.5% 0 0)', letterSpacing: '-0.01em' }}>
          {pick.away_team} @ {pick.home_team}
        </div>
        <div style={{ fontSize: '0.76rem', color: MUTED_FG, marginTop: 2 }}>
          {fmtGameTime(pick.game_time_cst)}
        </div>
      </div>

      {/* Pick label */}
      <div style={{
        fontSize: '1.25rem',
        fontWeight: 800,
        color: confColor,
        letterSpacing: '0.03em',
      }}>
        {getPickLabel(pick)}
      </div>

      {/* Stats row */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: '0.82rem', fontWeight: 700, color: EMERALD }}>
          Edge: {fmtEdge(pick.edge_pct)}
        </span>
        <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'oklch(98.5% 0 0)' }}>
          Our Prob: {fmtProb(pick.our_probability)}
        </span>
        <span style={{ fontSize: '0.82rem', fontWeight: 600, color: MUTED_FG }}>
          Market: {fmtOdds(pick.market_odds)}
        </span>
      </div>

      {/* Detector */}
      <div style={{ fontSize: '0.71rem', color: MUTED_FG }}>
        Detector: {pick.detector}
      </div>

      {/* Sonnet narrative */}
      {pick.sonnet_narrative && (
        <div style={{
          fontSize: '0.79rem',
          color: MUTED_FG,
          fontStyle: 'italic',
          lineHeight: 1.55,
          borderLeft: `2px solid oklch(100% 0 0 / .12)`,
          paddingLeft: 10,
        }}>
          {pick.sonnet_narrative}
        </div>
      )}

      {/* Features accordion */}
      {features.length > 0 && (
        <div>
          <button
            onClick={onToggle}
            style={{
              background: 'none',
              border: 'none',
              color: MUTED_FG,
              fontSize: '0.7rem',
              fontWeight: 700,
              cursor: 'pointer',
              padding: '4px 0',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              display: 'flex',
              alignItems: 'center',
              gap: 5,
            }}
          >
            <span>{expanded ? '▲' : '▼'}</span>
            {expanded ? 'Hide Features' : 'Show Features'}
          </button>
          {expanded && (
            <table
              className="data-table"
              style={{ marginTop: 6, fontSize: '0.76rem' }}
            >
              <thead>
                <tr>
                  <th style={{ textAlign: 'left' }}>Feature</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {features.map(([k, v]) => (
                  <tr key={k}>
                    <td style={{ fontWeight: 600, color: 'oklch(98.5% 0 0)' }}>{k}</td>
                    <td style={{ textAlign: 'right' }}>
                      {typeof v === 'number' ? v.toFixed(3) : String(v)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────
export function MaxEvEdges() {
  const [sport, setSport]                   = useState<string>('mlb');
  const [picks, setPicks]                   = useState<Pick[]>([]);
  const [health, setHealth]                 = useState<any>(null);
  const [loading, setLoading]               = useState(true);
  const [error, setError]                   = useState('');
  const [viewMode, setViewMode]             = useState<'cards' | 'table'>('cards');
  const [minEdge, setMinEdge]               = useState(3);
  const [pickTypeFilter, setPickTypeFilter] = useState<'all' | 'ml' | 'spread' | 'total'>('all');
  const [confidenceFilter, setConfFilter]   = useState<'all' | 'high' | 'medium' | 'low'>('all');
  const [liveMode, setLiveMode]             = useState(false);
  const [lastUpdated, setLastUpdated]       = useState<Date | null>(null);
  const [source, setSource]                 = useState('database');
  const [expandedCards, setExpandedCards]   = useState<Set<number>>(new Set());
  const [healthExpanded, setHealthExpanded] = useState(false);
  const [sortField, setSortField]           = useState('edge_pct');
  const [sortDir, setSortDir]               = useState<'asc' | 'desc'>('desc');
  const [sportCounts, setSportCounts]       = useState<Record<string, number>>({});

  // ── Data fetching ────────────────────────────────────────────────────────
  const fetchHealth = useCallback(async () => {
    try {
      const res = await fetch(getApiUrl('v2/edges/health'));
      if (res.ok) setHealth(await res.json());
    } catch {}
  }, []);

  const fetchPicks = useCallback(async (live: boolean) => {
    setLoading(true);
    setError('');
    try {
      const ep = live ? 'v2/edges/live' : 'v2/edges/today';
      const q  = new URLSearchParams({ sport, min_edge: String(minEdge) });
      const res = await fetch(getApiUrl(`${ep}?${q}`));
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const list: Pick[] = data.picks || [];
      setPicks(list);
      setSource(data.source || (live ? 'live' : 'database'));
      setLastUpdated(new Date());
      setSportCounts(prev => ({ ...prev, [sport]: list.length }));
    } catch (e: any) {
      setError(e.message || 'Failed to load picks');
      setPicks([]);
    } finally {
      setLoading(false);
    }
  }, [sport, minEdge]);

  useEffect(() => { fetchHealth(); }, [fetchHealth]);

  // Re-fetch when sport, minEdge, or liveMode changes
  useEffect(() => { fetchPicks(liveMode); }, [liveMode, fetchPicks]);

  // Auto-refresh every 60s when live
  useEffect(() => {
    if (!liveMode) return;
    const id = setInterval(() => fetchPicks(true), 60_000);
    return () => clearInterval(id);
  }, [liveMode, fetchPicks]);

  // ── Derived state ────────────────────────────────────────────────────────
  const filteredPicks = picks.filter(p => {
    if (pickTypeFilter !== 'all' && p.pick_type !== pickTypeFilter) return false;
    if (confidenceFilter !== 'all' && p.confidence_tier !== confidenceFilter) return false;
    return true;
  });

  const sortedPicks = [...filteredPicks].sort((a, b) => {
    const av = (a as any)[sortField] ?? 0;
    const bv = (b as any)[sortField] ?? 0;
    const cmp = typeof av === 'string' ? av.localeCompare(bv) : (av as number) - (bv as number);
    return sortDir === 'desc' ? -cmp : cmp;
  });

  const scatterData = filteredPicks.map((p, i) => ({
    x: p.edge_pct,
    y: p.our_probability,
    pick: p,
    idx: i,
  }));

  const healthStatus = (health?.overall_status as string | undefined) || 'unknown';
  const healthColor  = healthStatus === 'healthy' ? EMERALD
    : healthStatus === 'warning' ? YELLOW : BRAND_RED;

  // ── Handlers ─────────────────────────────────────────────────────────────
  const toggleSort = (f: string) => {
    if (sortField === f) setSortDir(prev => prev === 'asc' ? 'desc' : 'asc');
    else { setSortField(f); setSortDir('desc'); }
  };

  const toggleCard = (idx: number) => {
    setExpandedCards(prev => {
      const next = new Set(prev);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });
  };

  // ── Sub-components ────────────────────────────────────────────────────────
  function SortArrow({ f }: { f: string }) {
    const active = sortField === f;
    return (
      <span className={`sort-arrow ${active ? 'active' : ''}`}>
        {active ? (sortDir === 'desc' ? '↓' : '↑') : '↕'}
      </span>
    );
  }

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="analytics-page">
      {/* ── 1. Header ───────────────────────────────────────────────────── */}
      <div className="analytics-header">
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: 10,
        }}>
          {/* Title / subtitle */}
          <div>
            <h1>MAX-EV EDGE ENGINE</h1>
            <p className="subtitle">
              {lastUpdated
                ? `Updated ${lastUpdated.toLocaleTimeString()} · Source: ${source}`
                : 'Loading...'}
            </p>
          </div>

          {/* Health + count */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0, paddingTop: 4 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: healthColor,
                display: 'inline-block',
                boxShadow: `0 0 6px ${healthColor}`,
              }} />
              <span style={{
                fontSize: '0.72rem',
                fontWeight: 700,
                color: healthColor,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
              }}>
                {healthStatus}
              </span>
            </div>
            {health?.total_picks_today != null && (
              <span style={{ fontSize: '0.72rem', color: MUTED_FG, fontWeight: 600 }}>
                {health.total_picks_today} picks today
              </span>
            )}
          </div>
        </div>

        {/* ── 2. Sport tabs ──────────────────────────────────────────────── */}
        <div className="sport-tabs">
          {(['mlb', 'wnba', 'tennis_atp', 'tennis_wta', 'nba', 'nfl', 'ncaaf']).map(s => (
            <button
              key={s}
              className={`sport-tab ${sport === s ? 'active' : ''}`}
              onClick={() => setSport(s)}
            >
              {s === 'tennis_atp' ? 'ATP' : s === 'tennis_wta' ? 'WTA' : s.toUpperCase()}
              {sportCounts[s] != null && sportCounts[s] > 0
                ? ` (${sportCounts[s]})`
                : ''}
            </button>
          ))}
        </div>
      </div>

      {/* ── 3. Filter bar ───────────────────────────────────────────────── */}
      <div className="filter-bar">
        <span className="filter-label">View:</span>
        <button
          className={`filter-pill ${viewMode === 'cards' ? 'active' : ''}`}
          onClick={() => setViewMode('cards')}
        >Cards</button>
        <button
          className={`filter-pill ${viewMode === 'table' ? 'active' : ''}`}
          onClick={() => setViewMode('table')}
        >Table</button>

        <span style={{ width: 1, height: 18, background: BORDER, margin: '0 4px', flexShrink: 0 }} />

        <span className="filter-label">Type:</span>
        {(['all', 'ml', 'spread', 'total'] as const).map(t => (
          <button
            key={t}
            className={`filter-pill ${pickTypeFilter === t ? 'active' : ''}`}
            onClick={() => setPickTypeFilter(t)}
          >
            {t === 'all' ? 'All' : t.toUpperCase()}
          </button>
        ))}

        <span style={{ width: 1, height: 18, background: BORDER, margin: '0 4px', flexShrink: 0 }} />

        <span className="filter-label">Confidence:</span>
        {(['all', 'high', 'medium', 'low'] as const).map(c => (
          <button
            key={c}
            className={`filter-pill ${confidenceFilter === c ? 'active' : ''}`}
            onClick={() => setConfFilter(c)}
          >
            {c === 'all' ? 'All' : c.charAt(0).toUpperCase() + c.slice(1)}
          </button>
        ))}

        <span style={{ width: 1, height: 18, background: BORDER, margin: '0 4px', flexShrink: 0 }} />

        <span className="filter-label">Min Edge %:</span>
        <input
          type="number"
          value={minEdge}
          onChange={e => setMinEdge(Number(e.target.value))}
          step={0.5}
          min={0}
          max={20}
          style={{
            width: 60,
            padding: '3px 8px',
            background: 'var(--muted)',
            border: `1px solid ${BORDER}`,
            borderRadius: 4,
            color: 'oklch(98.5% 0 0)',
            fontSize: '0.8rem',
            fontWeight: 600,
            fontFamily: 'var(--d3-font)',
            outline: 'none',
          }}
        />

        {/* Live mode button — right-aligned */}
        <div style={{ marginLeft: 'auto' }}>
          <button
            onClick={() => setLiveMode(m => !m)}
            className={`filter-pill ${liveMode ? 'active' : ''}`}
            style={liveMode
              ? { display: 'flex', alignItems: 'center', gap: 6 }
              : { display: 'flex', alignItems: 'center', gap: 6 }
            }
          >
            {liveMode && (
              <span style={{
                width: 7,
                height: 7,
                borderRadius: '50%',
                background: '#fff',
                display: 'inline-block',
                animation: 'mev-pulse 1.2s ease-in-out infinite',
              }} />
            )}
            {liveMode ? 'LIVE' : 'Live Mode'}
          </button>
        </div>
      </div>

      {/* ── Content ─────────────────────────────────────────────────────── */}
      <div className="analytics-content">
        {/* Error banner */}
        {error && (
          <div style={{
            padding: '10px 14px',
            marginBottom: 16,
            background: `color-mix(in oklch, ${BRAND_RED} 12%, transparent)`,
            border: `1px solid color-mix(in oklch, ${BRAND_RED} 40%, transparent)`,
            borderRadius: 6,
            color: BRAND_RED,
            fontSize: '0.82rem',
            fontWeight: 600,
          }}>
            {error}
          </div>
        )}

        {/* Loading skeletons */}
        {loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {[...Array(4)].map((_, i) => (
              <div key={i} className="skeleton" style={{ height: 90 }} />
            ))}
          </div>
        )}

        {!loading && (
          <>
            {/* ── 4. Scatter plot ─────────────────────────────────────── */}
            {filteredPicks.length > 0 && (
              <div
                className="data-table-wrap"
                style={{ marginBottom: 20, padding: '16px 20px 20px', overflow: 'visible' }}
              >
                <div className="section-title">
                  Edge vs Probability — All Today's Picks
                </div>
                <ResponsiveContainer width="100%" height={300}>
                  <ScatterChart margin={{ top: 10, right: 24, bottom: 28, left: 16 }}>
                    <CartesianGrid
                      stroke={BORDER}
                      strokeDasharray="3 3"
                    />
                    <XAxis
                      type="number"
                      dataKey="x"
                      name="Edge %"
                      domain={[0, 'auto']}
                      tick={{ fill: MUTED_FG, fontSize: 11 }}
                      tickLine={false}
                      axisLine={{ stroke: BORDER }}
                      label={{
                        value: 'Edge %',
                        position: 'insideBottom',
                        offset: -14,
                        fill: MUTED_FG,
                        fontSize: 11,
                      }}
                    />
                    <YAxis
                      type="number"
                      dataKey="y"
                      name="Our Probability"
                      domain={[0.45, 0.75]}
                      tickFormatter={v => `${(v * 100).toFixed(0)}%`}
                      tick={{ fill: MUTED_FG, fontSize: 11 }}
                      tickLine={false}
                      axisLine={{ stroke: BORDER }}
                      label={{
                        value: 'Our Probability',
                        angle: -90,
                        position: 'insideLeft',
                        offset: 10,
                        fill: MUTED_FG,
                        fontSize: 11,
                      }}
                    />
                    <ZAxis range={[60, 60]} />
                    <Tooltip content={<ScatterTooltip />} />
                    <ReferenceLine
                      x={minEdge}
                      stroke={MUTED_FG}
                      strokeDasharray="4 3"
                      strokeOpacity={0.6}
                      label={{ value: `${minEdge}% min`, fill: MUTED_FG, fontSize: 10, position: 'insideTopRight' }}
                    />
                    <ReferenceLine
                      y={0.526}
                      stroke={YELLOW}
                      strokeDasharray="4 3"
                      strokeOpacity={0.7}
                      label={{ value: 'Breakeven', fill: YELLOW, fontSize: 10, position: 'insideTopLeft' }}
                    />
                    <Scatter data={scatterData}>
                      {scatterData.map((entry, i) => (
                        <Cell
                          key={i}
                          fill={getConfColor(entry.pick.confidence_tier)}
                          fillOpacity={0.85}
                        />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
                <p className="data-note">
                  Dot color = confidence tier (green = high, yellow = medium, red = low).
                  Upper-right quadrant (high edge + high prob) = strongest picks.
                </p>
              </div>
            )}

            {/* ── 5. Picks display ───────────────────────────────────── */}
            {filteredPicks.length === 0 ? (
              /* ── 6. Empty state ─────────────────────────────────────── */
              <div className="empty-state">
                <h3>No Edges Found</h3>
                <p>
                  No edges above {minEdge}% found for today's {sport.toUpperCase()} games.
                </p>
                {!liveMode && (
                  <button
                    className="filter-pill active"
                    onClick={() => setLiveMode(true)}
                    style={{ marginTop: 16, cursor: 'pointer' }}
                  >
                    Switch to Live Mode
                  </button>
                )}
              </div>

            ) : viewMode === 'cards' ? (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
                gap: 14,
                marginBottom: 20,
              }}>
                {filteredPicks.map((pick, idx) => (
                  <PickCard
                    key={`${pick.away_team}-${pick.home_team}-${pick.pick_type}-${pick.pick_side}-${idx}`}
                    pick={pick}
                    idx={idx}
                    expanded={expandedCards.has(idx)}
                    onToggle={() => toggleCard(idx)}
                  />
                ))}
              </div>

            ) : (
              <div className="data-table-wrap" style={{ marginBottom: 20 }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left', cursor: 'pointer' }} onClick={() => toggleSort('home_team')}>
                        Matchup <SortArrow f="home_team" />
                      </th>
                      <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('pick_side')}>
                        Pick <SortArrow f="pick_side" />
                      </th>
                      <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('pick_type')}>
                        Type <SortArrow f="pick_type" />
                      </th>
                      <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('edge_pct')}>
                        Edge % <SortArrow f="edge_pct" />
                      </th>
                      <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('our_probability')}>
                        Our Prob <SortArrow f="our_probability" />
                      </th>
                      <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('market_odds')}>
                        Market Odds <SortArrow f="market_odds" />
                      </th>
                      <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('confidence_tier')}>
                        Confidence <SortArrow f="confidence_tier" />
                      </th>
                      <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('detector')}>
                        Detector <SortArrow f="detector" />
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedPicks.map((pick, idx) => {
                      const confColor = getConfColor(pick.confidence_tier);
                      return (
                        <tr key={idx}>
                          <td style={{ fontWeight: 700, color: 'oklch(98.5% 0 0)' }}>
                            {pick.away_team} @ {pick.home_team}
                            <div style={{
                              fontSize: '0.72rem',
                              color: MUTED_FG,
                              fontWeight: 500,
                              marginTop: 2,
                            }}>
                              {fmtGameTime(pick.game_time_cst)}
                            </div>
                          </td>
                          <td style={{ fontWeight: 700, color: confColor, textAlign: 'right' }}>
                            {getPickLabel(pick)}
                          </td>
                          <td style={{ textTransform: 'uppercase' }}>{pick.pick_type}</td>
                          <td style={{ fontWeight: 700, color: EMERALD }}>
                            {fmtEdge(pick.edge_pct)}
                          </td>
                          <td>{fmtProb(pick.our_probability)}</td>
                          <td>{fmtOdds(pick.market_odds)}</td>
                          <td>
                            {pick.confidence_tier ? (
                              <span style={{
                                color: confColor,
                                fontWeight: 700,
                                textTransform: 'uppercase',
                                fontSize: '0.72rem',
                                letterSpacing: '0.06em',
                              }}>
                                {pick.confidence_tier}
                              </span>
                            ) : (
                              <span style={{ color: MUTED_FG }}>—</span>
                            )}
                          </td>
                          <td style={{ fontSize: '0.76rem' }}>{pick.detector}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* ── 7. System health accordion ──────────────────────────── */}
            <div className="data-table-wrap">
              <button
                onClick={() => setHealthExpanded(e => !e)}
                style={{
                  width: '100%',
                  padding: '14px 18px',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  color: 'oklch(98.5% 0 0)',
                  fontFamily: 'var(--d3-font)',
                }}
              >
                <span className="section-title" style={{ margin: 0 }}>
                  System Health — Agent Reports
                </span>
                <span style={{ color: MUTED_FG, fontSize: '0.8rem' }}>
                  {healthExpanded ? '▲' : '▼'}
                </span>
              </button>

              {healthExpanded && (
                <div style={{
                  padding: '0 18px 20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 18,
                  borderTop: `1px solid ${BORDER}`,
                }}>
                  {/* Ingestion per sport */}
                  {health?.ingestion && Object.keys(health.ingestion).length > 0 && (
                    <div style={{ marginTop: 14 }}>
                      <div className="section-title">Ingestion Status</div>
                      <div className="data-table-wrap">
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th style={{ textAlign: 'left' }}>Sport</th>
                              <th>Records</th>
                              <th>Valid %</th>
                              <th>Flags</th>
                            </tr>
                          </thead>
                          <tbody>
                            {Object.entries(health.ingestion).map(([s, info]: [string, any]) => (
                              <tr key={s}>
                                <td style={{
                                  fontWeight: 700,
                                  color: 'oklch(98.5% 0 0)',
                                  textTransform: 'uppercase',
                                }}>
                                  {s}
                                </td>
                                <td>{info.records_fetched ?? '—'}</td>
                                <td>
                                  {info.valid_pct != null
                                    ? `${(info.valid_pct as number).toFixed(1)}%`
                                    : '—'}
                                </td>
                                <td style={{
                                  color: (info.flags?.length ?? 0) > 0 ? YELLOW : MUTED_FG,
                                  fontSize: '0.75rem',
                                }}>
                                  {info.flags?.join(', ') || 'None'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Last Opus reflection */}
                  {health?.last_reflection && (
                    <div>
                      <div className="section-title">Last Reflection</div>
                      <p style={{
                        color: MUTED_FG,
                        fontSize: '0.82rem',
                        fontStyle: 'italic',
                        lineHeight: 1.6,
                        margin: 0,
                      }}>
                        {health.last_reflection}
                      </p>
                    </div>
                  )}

                  {/* Action items */}
                  {Array.isArray(health?.action_items) && health.action_items.length > 0 && (
                    <div>
                      <div className="section-title">Action Items</div>
                      <ul style={{
                        listStyle: 'none',
                        padding: 0,
                        margin: 0,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 7,
                      }}>
                        {(health.action_items as string[]).map((item, i) => (
                          <li key={i} style={{
                            display: 'flex',
                            gap: 8,
                            fontSize: '0.82rem',
                            color: MUTED_FG,
                            alignItems: 'flex-start',
                          }}>
                            <span style={{ color: YELLOW, fontWeight: 700, flexShrink: 0, marginTop: 1 }}>
                              •
                            </span>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {!health && (
                    <p className="data-note" style={{ marginTop: 14 }}>
                      Health data unavailable.
                    </p>
                  )}
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Keyframes for live-mode pulse dot */}
      <style>{`
        @keyframes mev-pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50%       { opacity: 0.45; transform: scale(0.8); }
        }
      `}</style>
    </div>
  );
}
