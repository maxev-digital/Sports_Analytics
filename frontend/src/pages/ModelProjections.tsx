import { useState, useEffect, useCallback } from 'react';
import { Brain, RefreshCw, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';
import '../styles/analytics.css';
import { getApiUrl } from '../config';

// ── Design tokens ─────────────────────────────────────────────────────────────
const EMERALD    = 'oklch(69.6% .17 162.48)';
const BRAND_RED  = 'oklch(63.7% .237 25.331)';
const BLUE       = 'oklch(62.3% .214 259.815)';
const YELLOW     = 'oklch(79.5% .184 86.047)';
const PURPLE     = 'oklch(65% .18 290)';
const MUTED_FG   = 'oklch(70.8% 0 0)';
const BORDER     = 'oklch(100% 0 0 / .1)';
const BORDER_STR = 'oklch(100% 0 0 / .18)';
const BG_HEADER  = 'oklch(22% 0 0)';
const BG_ROW_ALT = 'oklch(19% 0 0 / 0.5)';

// ── Types ─────────────────────────────────────────────────────────────────────
interface Projection {
  id: number;
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  game_date: string | null;
  proj_home_score: number | null;
  proj_away_score: number | null;
  proj_total: number | null;
  proj_spread: number | null;
  market_total: number | null;
  market_spread: number | null;
  data_completeness: number | null;
  model_confidence: string | null;
  projection_notes: string | null;
  metrics: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
const SPORT_LABELS: Record<string, string> = {
  MLB: 'MLB', NFL: 'NFL', CFB: 'CFB', NBA: 'NBA',
  NHL: 'NHL', NCAAB: 'NCAAB', ncaaf: 'CFB', nfl: 'NFL',
  mlb: 'MLB', nba: 'NBA', nhl: 'NHL', ncaab: 'NCAAB',
};
const SPORT_COLORS: Record<string, string> = {
  MLB: BRAND_RED, mlb: BRAND_RED,
  NFL: BLUE,      nfl: BLUE,
  CFB: YELLOW,    ncaaf: YELLOW,
  NBA: EMERALD,   nba: EMERALD,
  NHL: BLUE,      nhl: BLUE,
  NCAAB: PURPLE,  ncaab: PURPLE,
};

function sportLabel(s: string)  { return SPORT_LABELS[s] ?? s.toUpperCase(); }
function sportColor(s: string)  { return SPORT_COLORS[s] ?? MUTED_FG; }

function fmtScore(v: number | null)  { return v != null ? v.toFixed(1) : '—'; }
function fmtSpread(v: number | null) {
  if (v == null) return '—';
  if (v === 0)   return 'PK';
  return v > 0 ? `+${v.toFixed(1)}` : v.toFixed(1);
}

// ── Metric labels for expanded detail ─────────────────────────────────────────
const METRIC_LABELS: Record<string, string> = {
  home_starter: 'Home SP',      away_starter: 'Away SP',
  home_xfip: 'Home xFIP',       away_xfip: 'Away xFIP',
  home_era_xfip_gap: 'ERA−xFIP (H)', away_era_xfip_gap: 'ERA−xFIP (A)',
  home_k_rate: 'K% (H)',         away_k_rate: 'K% (A)',
  home_lineup_woba: 'wOBA (H)',  away_lineup_woba: 'wOBA (A)',
  park_factor: 'Park Factor',    wind_mph: 'Wind mph',
  wind_direction: 'Wind Dir',    wind_factor: 'Wind Factor',
  proj_f5_total: 'F5 Total',
  home_sp_plus: 'SP+ (H)',       away_sp_plus: 'SP+ (A)',
  sp_plus_gap: 'SP+ Gap',
  home_ypp_matchup: 'YPP Edge (H)', away_ypp_matchup: 'YPP Edge (A)',
  home_momentum_score: 'Momentum (H)', away_momentum_score: 'Momentum (A)',
  schedule_spot_delta: 'Sched Spot',
  home_epa_off: 'EPA Off (H)',   away_epa_off: 'EPA Off (A)',
  home_epa_def: 'EPA Def (H)',   away_epa_def: 'EPA Def (A)',
  weather_temp_f: 'Temp °F',     weather_wind_mph: 'Wind mph',
  weather_impact_score: 'Weather Adj',
};
const SKIP_METRICS = new Set(['data_notes']);

// ── Components ────────────────────────────────────────────────────────────────
function SportBadge({ sport }: { sport: string }) {
  const color = sportColor(sport);
  return (
    <span style={{
      padding: '1px 7px',
      borderRadius: 12,
      fontSize: '0.62rem',
      fontWeight: 700,
      letterSpacing: '0.08em',
      textTransform: 'uppercase' as const,
      background: `color-mix(in oklch, ${color} 18%, transparent)`,
      color,
      border: `1px solid color-mix(in oklch, ${color} 35%, transparent)`,
      whiteSpace: 'nowrap' as const,
    }}>{sportLabel(sport)}</span>
  );
}

function FilterPill({ label, active, color, onClick }: {
  label: string; active: boolean; color?: string; onClick: () => void;
}) {
  const c = color ?? MUTED_FG;
  return (
    <button onClick={onClick} style={{
      padding: '4px 12px', borderRadius: 20, fontSize: '0.68rem',
      fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' as const,
      cursor: 'pointer',
      border: `1px solid ${active ? `color-mix(in oklch, ${c} 60%, transparent)` : `color-mix(in oklch, ${c} 25%, transparent)`}`,
      background: active ? `color-mix(in oklch, ${c} 22%, transparent)` : 'transparent',
      color: active ? c : MUTED_FG, transition: 'all 0.15s', fontFamily: 'var(--d3-font)',
    }}>{label}</button>
  );
}

// ── Expandable detail row ─────────────────────────────────────────────────────
function DetailRow({ proj }: { proj: Projection }) {
  const entries = Object.entries(proj.metrics).filter(
    ([k]) => !SKIP_METRICS.has(k) && METRIC_LABELS[k]
  );
  const notes = proj.metrics['data_notes'] as string | undefined;

  return (
    <tr>
      <td colSpan={8} style={{ padding: 0 }}>
        <div style={{
          padding: '12px 16px 14px',
          background: 'oklch(17% 0 0 / 0.6)',
          borderBottom: `1px solid ${BORDER_STR}`,
        }}>
          {proj.projection_notes && (
            <p style={{
              fontSize: '0.76rem', color: 'oklch(82% 0 0)', lineHeight: 1.65,
              margin: '0 0 10px', borderLeft: `2px solid ${BLUE}`, paddingLeft: 10,
            }}>
              {proj.projection_notes}
            </p>
          )}
          {entries.length > 0 && (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(155px, 1fr))',
              gap: '5px 16px',
              marginTop: proj.projection_notes ? 8 : 0,
            }}>
              {entries.map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <span style={{ fontSize: '0.67rem', color: MUTED_FG }}>{METRIC_LABELS[k]}</span>
                  <span style={{ fontSize: '0.67rem', fontWeight: 700, color: 'oklch(88% 0 0)' }}>
                    {typeof v === 'boolean'
                      ? (v ? 'Yes' : 'No')
                      : typeof v === 'number'
                        ? (Number.isInteger(v) ? String(v) : v.toFixed(3))
                        : String(v)}
                  </span>
                </div>
              ))}
            </div>
          )}
          {notes && (
            <p style={{ fontSize: '0.7rem', color: MUTED_FG, fontStyle: 'italic', margin: '8px 0 0' }}>
              {notes}
            </p>
          )}
        </div>
      </td>
    </tr>
  );
}

// ── Table row ─────────────────────────────────────────────────────────────────
function ProjectionRow({ proj, index }: { proj: Projection; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const hasDetail = Object.keys(proj.metrics).length > 0 || !!proj.projection_notes;
  const rowBg = index % 2 === 1 ? BG_ROW_ALT : 'transparent';

  const tdBase: React.CSSProperties = {
    padding: '10px 12px',
    borderBottom: `1px solid ${BORDER}`,
    verticalAlign: 'middle',
    background: rowBg,
  };

  return (
    <>
      <tr style={{ cursor: hasDetail ? 'pointer' : 'default' }}
          onClick={() => hasDetail && setExpanded(e => !e)}>

        {/* Sport */}
        <td style={{ ...tdBase, width: 64 }}>
          <SportBadge sport={proj.sport} />
        </td>

        {/* Matchup */}
        <td style={{ ...tdBase, minWidth: 180 }}>
          <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'oklch(96% 0 0)' }}>
            {proj.away_team}
          </div>
          <div style={{ fontSize: '0.72rem', color: MUTED_FG, marginTop: 1 }}>
            @ {proj.home_team}
          </div>
        </td>

        {/* Away proj */}
        <td style={{ ...tdBase, textAlign: 'center', width: 80 }}>
          <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'oklch(94% 0 0)' }}>
            {fmtScore(proj.proj_away_score)}
          </div>
          <div style={{ fontSize: '0.58rem', color: MUTED_FG, marginTop: 1 }}>AWAY</div>
        </td>

        {/* Home proj */}
        <td style={{ ...tdBase, textAlign: 'center', width: 80 }}>
          <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'oklch(94% 0 0)' }}>
            {fmtScore(proj.proj_home_score)}
          </div>
          <div style={{ fontSize: '0.58rem', color: MUTED_FG, marginTop: 1 }}>HOME</div>
        </td>

        {/* Proj total */}
        <td style={{ ...tdBase, textAlign: 'center', width: 80 }}>
          <div style={{ fontSize: '1.05rem', fontWeight: 800, color: EMERALD }}>
            {fmtScore(proj.proj_total)}
          </div>
          <div style={{ fontSize: '0.58rem', color: MUTED_FG, marginTop: 1 }}>TOTAL</div>
        </td>

        {/* Proj spread */}
        <td style={{ ...tdBase, textAlign: 'center', width: 80 }}>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: YELLOW }}>
            {fmtSpread(proj.proj_spread)}
          </div>
          <div style={{ fontSize: '0.58rem', color: MUTED_FG, marginTop: 1 }}>SPREAD</div>
        </td>

        {/* Morning line (market line at build time) */}
        <td style={{ ...tdBase, textAlign: 'center', width: 110 }}>
          {proj.market_total != null ? (
            <div style={{ fontSize: '0.9rem', fontWeight: 800, color: PURPLE }}>
              {proj.market_total.toFixed(1)}
            </div>
          ) : (
            <div style={{ fontSize: '0.9rem', fontWeight: 800, color: MUTED_FG }}>—</div>
          )}
          {proj.market_spread != null && (
            <div style={{ fontSize: '0.67rem', color: MUTED_FG, marginTop: 1 }}>
              {fmtSpread(proj.market_spread)}
            </div>
          )}
          <div style={{ fontSize: '0.55rem', color: MUTED_FG, marginTop: 1, letterSpacing: '0.05em' }}>MORNING LINE</div>
        </td>

        {/* Expand toggle */}
        <td style={{ ...tdBase, textAlign: 'center', width: 40 }}>
          {hasDetail && (
            <span style={{ color: BLUE }}>
              {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </span>
          )}
        </td>
      </tr>

      {expanded && <DetailRow proj={proj} />}
    </>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export function ModelProjections() {
  const [projections, setProjections] = useState<Projection[]>([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState('');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [filterSport, setFilterSport] = useState('all');

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(getApiUrl('projections/today'));
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setProjections(data.projections ?? []);
      setLastUpdated(new Date());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load projections');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const sports   = Array.from(new Set(projections.map(p => p.sport))).sort();
  const filtered = filterSport === 'all'
    ? projections
    : projections.filter(p => p.sport === filterSport);

  const highConf = projections.filter(p => p.model_confidence === 'HIGH').length;
  const medConf  = projections.filter(p => p.model_confidence === 'MEDIUM').length;

  const thStyle: React.CSSProperties = {
    padding: '9px 12px',
    fontSize: '0.62rem',
    fontWeight: 700,
    color: MUTED_FG,
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    textAlign: 'left' as const,
    background: BG_HEADER,
    borderBottom: `1px solid ${BORDER_STR}`,
    whiteSpace: 'nowrap' as const,
  };

  return (
    <div className="analytics-page">
      {/* Header */}
      <div className="analytics-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
          <div>
            <h1 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Brain size={20} style={{ color: BLUE }} />
              MODEL PROJECTIONS
            </h1>
            <p className="subtitle">
              {lastUpdated
                ? `Updated ${lastUpdated.toLocaleTimeString()} — statistical game-state projections used as evidence by the handicapping agent`
                : 'Loading projections...'}
            </p>
          </div>
          <button
            onClick={fetchAll}
            disabled={loading}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '6px 14px', background: 'transparent',
              border: `1px solid ${BORDER_STR}`, borderRadius: 6,
              color: MUTED_FG, fontSize: '0.75rem', fontWeight: 700,
              cursor: loading ? 'not-allowed' : 'pointer',
              fontFamily: 'var(--d3-font)', opacity: loading ? 0.5 : 1,
            }}
          >
            <RefreshCw size={13} style={{ animation: loading ? 'mev-spin 1s linear infinite' : 'none' }} />
            Refresh
          </button>
        </div>
      </div>

      <div className="analytics-content">
        {/* Callout */}
        <div style={{
          display: 'flex', alignItems: 'flex-start', gap: 10,
          padding: '9px 13px', marginBottom: 18, borderRadius: 6,
          border: `1px solid color-mix(in oklch, ${BLUE} 28%, transparent)`,
          background: `color-mix(in oklch, ${BLUE} 5%, transparent)`,
        }}>
          <AlertCircle size={13} style={{ color: BLUE, flexShrink: 0, marginTop: 2 }} />
          <p style={{ fontSize: '0.73rem', color: MUTED_FG, lineHeight: 1.55, margin: 0 }}>
            <strong style={{ color: 'oklch(88% 0 0)' }}>Model outputs</strong> — statistical projections of scores, totals, and matchup metrics.
            One evidence layer read by the handicapping agent before making picks.
            Actual recommendations are on <strong style={{ color: 'oklch(88% 0 0)' }}>Today's Plays</strong>. Runs 7:00 AM CST.
          </p>
        </div>

        {/* Stat bar */}
        <div className="stat-cards" style={{ marginBottom: 20 }}>
          {[
            { label: "Today's Games",    value: projections.length, sub: 'projections built',    color: BLUE },
            { label: 'High Confidence',  value: highConf,           sub: 'complete data',        color: EMERALD },
            { label: 'Medium Conf',      value: medConf,            sub: 'partial data',         color: YELLOW },
            { label: 'Sports Live',      value: sports.length,      sub: 'MLB · CFB · NFL',      color: 'oklch(94% 0 0)' },
          ].map(s => (
            <div key={s.label} className="stat-card" style={{ minWidth: 0 }}>
              <div style={{ fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6 }}>{s.label}</div>
              <div className="stat-value" style={{ color: s.color, fontSize: '1.45rem' }}>{loading ? '—' : s.value}</div>
              <div style={{ fontSize: '0.68rem', color: MUTED_FG, marginTop: 4 }}>{s.sub}</div>
            </div>
          ))}
        </div>

        {/* Sport filter */}
        {!loading && sports.length > 1 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.62rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', minWidth: 44 }}>Sport</span>
            <FilterPill label="All" active={filterSport === 'all'} onClick={() => setFilterSport('all')} />
            {sports.map(s => (
              <FilterPill key={s} label={sportLabel(s)} active={filterSport === s}
                color={sportColor(s)} onClick={() => setFilterSport(filterSport === s ? 'all' : s)} />
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{
            padding: '10px 14px', marginBottom: 14,
            background: `color-mix(in oklch, ${BRAND_RED} 12%, transparent)`,
            border: `1px solid color-mix(in oklch, ${BRAND_RED} 40%, transparent)`,
            borderRadius: 6, color: BRAND_RED, fontSize: '0.82rem', fontWeight: 600,
          }}>{error}</div>
        )}

        {/* Loading */}
        {loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {[...Array(6)].map((_, i) => <div key={i} className="skeleton" style={{ height: 52 }} />)}
          </div>
        )}

        {/* Empty */}
        {!loading && filtered.length === 0 && (
          <div className="empty-state">
            <h3>No Projections Yet Today</h3>
            <p>Projection builders run at 7:00 AM CST. Check back after that window.</p>
          </div>
        )}

        {/* Table */}
        {!loading && filtered.length > 0 && (
          <div className="data-table-wrap" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'auto' }}>
                <thead>
                  <tr>
                    <th style={thStyle}>Sport</th>
                    <th style={thStyle}>Matchup</th>
                    <th style={{ ...thStyle, textAlign: 'center' }}>Proj Away</th>
                    <th style={{ ...thStyle, textAlign: 'center' }}>Proj Home</th>
                    <th style={{ ...thStyle, textAlign: 'center' }}>Total</th>
                    <th style={{ ...thStyle, textAlign: 'center' }}>Spread</th>
                    <th style={{ ...thStyle, textAlign: 'center' }}>Morning Line</th>
                    <th style={{ ...thStyle, textAlign: 'center' }}></th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((p, i) => (
                    <ProjectionRow key={p.id} proj={p} index={i} />
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ padding: '8px 14px', borderTop: `1px solid ${BORDER}`, fontSize: '0.65rem', color: MUTED_FG }}>
              Click any row to expand projection signals · {filtered.length} game{filtered.length !== 1 ? 's' : ''}
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes mev-spin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
