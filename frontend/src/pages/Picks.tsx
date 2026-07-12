import { useState, useEffect, useCallback } from 'react';
import { TrendingUp, Target, Clock, BarChart3, RefreshCw, ChevronDown, Info } from 'lucide-react';
import '../styles/analytics.css';
import { getApiUrl } from '../config';
import { PickDetailCard, EnrichedPick } from '../components/PickDetailCard';

// ── Design tokens ────────────────────────────────────────────────────────────
const EMERALD    = 'oklch(69.6% .17 162.48)';
const BRAND_RED  = 'oklch(63.7% .237 25.331)';
const BLUE       = 'oklch(62.3% .214 259.815)';
const YELLOW     = 'oklch(79.5% .184 86.047)';
const MUTED_FG   = 'oklch(70.8% 0 0)';
const BORDER     = 'oklch(100% 0 0 / .1)';
const BORDER_STR = 'oklch(100% 0 0 / .18)';

// ── Types ────────────────────────────────────────────────────────────────────
interface Prediction {
  id: number;
  created_at_cst: string;
  sport: string;
  home_team: string;
  away_team: string;
  game_time_cst: string | null;
  pick_side: string;
  pick_type: string;
  our_probability: number;
  market_odds: number;
  market_implied_prob: number;
  edge_pct: number;
  detector: string;
  confidence_tier: string | null;
  status: string;
  result: string | null;
  pl_units: number | null;
  sonnet_narrative: string | null;
  game_id: string | null;
  total_line: number | null;
}

interface Stats {
  total_all_time: number;
  today: number;
  last_7_days: number;
  graded_30d: {
    total: number;
    wins: number;
    losses: number;
    pushes: number;
    win_rate_pct: number;
    total_pl_units: number;
  };
  avg_edge_pending_7d: number;
  generated_at: string;
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function fmtOdds(odds: number): string {
  return odds >= 0 ? `+${odds}` : `${odds}`;
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

function getPickLabel(p: Prediction): string {
  const side = p.pick_side.toUpperCase().replace('_COVER', ' COVER');
  if (p.pick_type === 'ml') return `${side} ML`;
  if (p.pick_type === 'total') {
    const line = p.total_line != null ? ` ${p.total_line}` : '';
    return `${side}${line}`;
  }
  if (p.pick_type === 'spread') return `${side}`;
  return `${side} ${p.pick_type.toUpperCase()}`;
}

function getConfColor(tier: string | null): string {
  if (tier === 'high') return EMERALD;
  if (tier === 'medium') return YELLOW;
  if (tier === 'low') return BRAND_RED;
  return MUTED_FG;
}

function getSportColor(sport: string): string {
  const map: Record<string, string> = {
    mlb: BRAND_RED,
    wnba: BLUE,
    tennis_atp: YELLOW,
    tennis_wta: YELLOW,
    soccer_mls: EMERALD,
    soccer_epl: EMERALD,
    nfl: BLUE,
    ncaaf: YELLOW,
    nba: EMERALD,
  };
  return map[sport] ?? MUTED_FG;
}

function getSportLabel(sport: string): string {
  const map: Record<string, string> = {
    mlb: 'MLB',
    wnba: 'WNBA',
    tennis_atp: 'ATP',
    tennis_wta: 'WTA',
    soccer_mls: 'MLS',
    soccer_epl: 'EPL',
    nfl: 'NFL',
    ncaaf: 'NCAAF',
    nba: 'NBA',
  };
  return map[sport] ?? sport.toUpperCase();
}

// ── Badge ────────────────────────────────────────────────────────────────────
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

// ── ResultBadge ───────────────────────────────────────────────────────────────
function ResultBadge({ result }: { result: string | null }) {
  if (!result) return null;
  let color = MUTED_FG;
  if (result === 'win') color = EMERALD;
  else if (result === 'loss') color = BRAND_RED;
  else if (result === 'push') color = YELLOW;
  const label = result.toUpperCase();
  return <Badge color={color} label={label} />;
}

// ── StatCard ──────────────────────────────────────────────────────────────────
function StatCard({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="stat-card" style={{ minWidth: 0 }}>
      <div style={{
        fontSize: '0.65rem',
        fontWeight: 700,
        color: MUTED_FG,
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
        marginBottom: 6,
      }}>
        {label}
      </div>
      <div className="stat-value" style={{ color: color ?? 'oklch(98.5% 0 0)', fontSize: '1.45rem' }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: '0.68rem', color: MUTED_FG, marginTop: 4 }}>
          {sub}
        </div>
      )}
    </div>
  );
}

// ── PendingPickCard ───────────────────────────────────────────────────────────
function PendingPickCard({ pick }: { pick: Prediction }) {
  const confColor  = getConfColor(pick.confidence_tier);
  const sportColor = getSportColor(pick.sport);
  const pickLabel  = getPickLabel(pick);

  return (
    <div className="data-table-wrap" style={{ padding: 0, overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '10px 14px 8px',
        borderBottom: `1px solid ${BORDER}`,
        flexWrap: 'wrap',
      }}>
        <Badge color={sportColor} label={getSportLabel(pick.sport)} />
        <span style={{ fontSize: '0.88rem', fontWeight: 800, color: 'oklch(98.5% 0 0)', flex: 1, minWidth: 0 }}>
          {pick.away_team} @ {pick.home_team}
        </span>
        <span style={{ fontSize: '0.72rem', color: MUTED_FG, display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0 }}>
          <Clock size={11} />
          {fmtGameTime(pick.game_time_cst)}
        </span>
      </div>

      {/* Body */}
      <div style={{ padding: '10px 14px 8px' }}>
        <div style={{ marginBottom: 8 }}>
          <span style={{ fontSize: '0.72rem', color: MUTED_FG }}>Pick: </span>
          <span style={{ fontSize: '1rem', fontWeight: 800, color: confColor, letterSpacing: '0.03em' }}>
            {pickLabel}
          </span>
          <span style={{ fontSize: '0.82rem', color: 'oklch(98.5% 0 0)', fontWeight: 600, marginLeft: 6 }}>
            at {fmtOdds(pick.market_odds)}
          </span>
          <span style={{ marginLeft: 10, fontSize: '0.82rem', fontWeight: 700, color: EMERALD }}>
            Edge: +{pick.edge_pct.toFixed(1)}%
          </span>
        </div>
        {pick.sonnet_narrative && (
          <div style={{
            fontSize: '0.76rem',
            color: MUTED_FG,
            fontStyle: 'italic',
            lineHeight: 1.5,
            borderLeft: `2px solid ${BORDER_STR}`,
            paddingLeft: 8,
            marginBottom: 8,
          }}>
            {pick.sonnet_narrative.length > 160
              ? pick.sonnet_narrative.slice(0, 157) + '...'
              : pick.sonnet_narrative}
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '6px 14px 10px',
        flexWrap: 'wrap',
      }}>
        {pick.confidence_tier && (
          <span style={{ fontSize: '0.7rem', color: MUTED_FG }}>
            Confidence: <span style={{ color: confColor, fontWeight: 700 }}>{pick.confidence_tier}</span>
          </span>
        )}
        <span style={{ fontSize: '0.7rem', color: MUTED_FG }}>|</span>
        <span style={{ fontSize: '0.7rem', color: MUTED_FG }}>
          Detector: <span style={{ color: 'oklch(85% 0 0)', fontWeight: 600 }}>{pick.detector}</span>
        </span>
        <span style={{ fontSize: '0.7rem', color: MUTED_FG }}>|</span>
        <span style={{ fontSize: '0.7rem', color: MUTED_FG }}>
          Our Prob: <span style={{ color: 'oklch(85% 0 0)', fontWeight: 600 }}>
            {(pick.our_probability * 100).toFixed(1)}%
          </span>
        </span>
      </div>
    </div>
  );
}

// ── GradedPickRow ─────────────────────────────────────────────────────────────
function GradedPickRow({ pick }: { pick: Prediction }) {
  const sportColor = getSportColor(pick.sport);
  const pickLabel  = getPickLabel(pick);
  const plColor    = pick.pl_units != null
    ? pick.pl_units > 0 ? EMERALD : pick.pl_units < 0 ? BRAND_RED : YELLOW
    : MUTED_FG;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      padding: '10px 14px',
      borderBottom: `1px solid ${BORDER}`,
      flexWrap: 'wrap',
    }}>
      {/* Sport + matchup */}
      <div style={{ flex: 1, minWidth: 180 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
          <Badge color={sportColor} label={getSportLabel(pick.sport)} />
          <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'oklch(98.5% 0 0)' }}>
            {pick.away_team} @ {pick.home_team}
          </span>
        </div>
        <div style={{ fontSize: '0.7rem', color: MUTED_FG }}>
          {fmtGameTime(pick.game_time_cst)}
        </div>
      </div>

      {/* Pick */}
      <div style={{ minWidth: 120 }}>
        <div style={{ fontSize: '0.82rem', fontWeight: 700, color: getConfColor(pick.confidence_tier) }}>
          {pickLabel}
        </div>
        <div style={{ fontSize: '0.7rem', color: MUTED_FG }}>
          {fmtOdds(pick.market_odds)} &bull; Edge: +{pick.edge_pct.toFixed(1)}%
        </div>
      </div>

      {/* Result */}
      <div style={{ minWidth: 60, textAlign: 'center' }}>
        <ResultBadge result={pick.result} />
      </div>

      {/* P/L */}
      <div style={{ minWidth: 70, textAlign: 'right' }}>
        {pick.pl_units != null ? (
          <span style={{ fontSize: '0.88rem', fontWeight: 800, color: plColor }}>
            {pick.pl_units > 0 ? '+' : ''}{pick.pl_units.toFixed(2)}u
          </span>
        ) : (
          <span style={{ color: MUTED_FG, fontSize: '0.8rem' }}>—</span>
        )}
      </div>
    </div>
  );
}

// ── FilterBar ─────────────────────────────────────────────────────────────────
type FilterPillProps = {
  label: string;
  active: boolean;
  color?: string;
  onClick: () => void;
};
function FilterPill({ label, active, color, onClick }: FilterPillProps) {
  const c = color ?? MUTED_FG;
  return (
    <button
      onClick={onClick}
      style={{
        padding: '4px 12px',
        borderRadius: 20,
        fontSize: '0.68rem',
        fontWeight: 700,
        letterSpacing: '0.08em',
        textTransform: 'uppercase' as const,
        cursor: 'pointer',
        border: `1px solid ${active
          ? `color-mix(in oklch, ${c} 60%, transparent)`
          : `color-mix(in oklch, ${c} 25%, transparent)`}`,
        background: active
          ? `color-mix(in oklch, ${c} 22%, transparent)`
          : 'transparent',
        color: active ? c : MUTED_FG,
        transition: 'all 0.15s',
        fontFamily: 'var(--d3-font)',
      }}
    >
      {label}
    </button>
  );
}

function FilterBar({
  picks,
  sport, setSport,
  type, setType,
  conf, setConf,
}: {
  picks: Array<{ sport: string; pick_type: string; confidence_tier: string | null }>;
  sport: string; setSport: (v: string) => void;
  type: string;  setType:  (v: string) => void;
  conf: string;  setConf:  (v: string) => void;
}) {
  const sports = Array.from(new Set(picks.map(p => p.sport))).sort();
  const types  = Array.from(new Set(picks.map(p => p.pick_type))).sort();
  const confs  = ['high', 'medium', 'low'].filter(c =>
    picks.some(p => p.confidence_tier === c)
  );

  const sportColorMap: Record<string, string> = {
    mlb: BRAND_RED, wnba: BLUE,
    tennis_atp: YELLOW, tennis_wta: YELLOW,
    soccer_mls: EMERALD, soccer_epl: EMERALD,
    nfl: BLUE, ncaaf: YELLOW,
  };
  const typeColorMap: Record<string, string> = {
    ml: BLUE, total: EMERALD, spread: YELLOW, props: MUTED_FG,
  };
  const confColorMap: Record<string, string> = {
    high: EMERALD, medium: YELLOW, low: BRAND_RED,
  };

  return (
    <div style={{
      padding: '10px 0 14px',
      display: 'flex',
      flexDirection: 'column',
      gap: 8,
    }}>
      {/* Sport row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.62rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', minWidth: 52 }}>Sport</span>
        <FilterPill label="All" active={sport === 'all'} onClick={() => setSport('all')} />
        {sports.map(s => (
          <FilterPill
            key={s}
            label={getSportLabel(s)}
            active={sport === s}
            color={sportColorMap[s]}
            onClick={() => setSport(sport === s ? 'all' : s)}
          />
        ))}
      </div>
      {/* Type row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.62rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', minWidth: 52 }}>Type</span>
        <FilterPill label="All" active={type === 'all'} onClick={() => setType('all')} />
        {types.map(t => (
          <FilterPill
            key={t}
            label={t.toUpperCase()}
            active={type === t}
            color={typeColorMap[t]}
            onClick={() => setType(type === t ? 'all' : t)}
          />
        ))}
      </div>
      {/* Confidence row */}
      {confs.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.62rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', minWidth: 52 }}>Conf</span>
          <FilterPill label="All" active={conf === 'all'} onClick={() => setConf('all')} />
          {confs.map(c => (
            <FilterPill
              key={c}
              label={c.charAt(0).toUpperCase() + c.slice(1)}
              active={conf === c}
              color={confColorMap[c]}
              onClick={() => setConf(conf === c ? 'all' : c)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export function Picks() {
  const [stats, setStats]           = useState<Stats | null>(null);
  const [pending, setPending]       = useState<EnrichedPick[]>([]);
  const [graded, setGraded]         = useState<Prediction[]>([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState('');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [filterSport, setFilterSport] = useState('all');
  const [filterType,  setFilterType]  = useState('all');
  const [filterConf,  setFilterConf]  = useState('all');

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [statsRes, enrichedRes, gradedRes] = await Promise.all([
        fetch(getApiUrl('predictions/stats')),
        fetch(getApiUrl('predictions/enriched?status=pending')),
        fetch(getApiUrl('predictions/graded?days=7')),
      ]);

      if (statsRes.ok) {
        const d = await statsRes.json();
        setStats(d);
      }
      if (enrichedRes.ok) {
        const d = await enrichedRes.json();
        const sorted = (d.picks ?? []).slice().sort((a: EnrichedPick, b: EnrichedPick) => {
          const ta = a.game_time_cst ? new Date(a.game_time_cst).getTime() : Infinity;
          const tb = b.game_time_cst ? new Date(b.game_time_cst).getTime() : Infinity;
          return ta - tb;
        });
        setPending(sorted);
      }
      if (gradedRes.ok) {
        const d = await gradedRes.json();
        // Sort most recent first
        const sorted = (d.predictions ?? []).sort((a: Prediction, b: Prediction) =>
          new Date(b.created_at_cst).getTime() - new Date(a.created_at_cst).getTime()
        );
        setGraded(sorted.slice(0, 30));
      }
      setLastUpdated(new Date());
    } catch (e: any) {
      setError(e.message ?? 'Failed to load picks data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const filteredPending = pending.filter(p => {
    if (filterSport !== 'all' && p.sport !== filterSport) return false;
    if (filterType  !== 'all' && p.pick_type !== filterType)  return false;
    if (filterConf  !== 'all' && p.confidence_tier !== filterConf) return false;
    return true;
  });

  const winRate   = stats?.graded_30d?.win_rate_pct ?? null;
  const totalPL   = stats?.graded_30d?.total_pl_units ?? null;
  const plColor   = totalPL != null ? (totalPL >= 0 ? EMERALD : BRAND_RED) : MUTED_FG;
  const wrColor   = winRate != null ? (winRate >= 55 ? EMERALD : winRate >= 48 ? YELLOW : BRAND_RED) : MUTED_FG;

  return (
    <div className="analytics-page">
      {/* ── Header ────────────────────────────────────────────────────── */}
      <div className="analytics-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
          <div>
            <h1 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Target size={20} style={{ color: BRAND_RED }} />
              PICKS
            </h1>
            <p className="subtitle">
              {lastUpdated
                ? `Updated ${lastUpdated.toLocaleTimeString()} — today's pending picks and recent results`
                : 'Loading picks data...'}
            </p>
          </div>
          <button
            onClick={fetchAll}
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '6px 14px',
              background: 'transparent',
              border: `1px solid ${BORDER_STR}`,
              borderRadius: 6,
              color: MUTED_FG,
              fontSize: '0.75rem',
              fontWeight: 700,
              cursor: loading ? 'not-allowed' : 'pointer',
              fontFamily: 'var(--d3-font)',
              opacity: loading ? 0.5 : 1,
            }}
          >
            <RefreshCw size={13} style={{ animation: loading ? 'mev-spin 1s linear infinite' : 'none' }} />
            Refresh
          </button>
        </div>
      </div>

      {/* ── Content ───────────────────────────────────────────────────── */}
      <div className="analytics-content">
        {/* Error */}
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

        {/* ── 1. Stats bar ────────────────────────────────────────────── */}
        <div className="stat-cards" style={{ marginBottom: 24 }}>
          <StatCard
            label="Today's Picks"
            value={loading ? '—' : String(stats?.today ?? pending.length)}
            sub="pending predictions"
            color={BLUE}
          />
          <StatCard
            label="Last 7 Days"
            value={loading ? '—' : String(stats?.last_7_days ?? '—')}
            sub="predictions generated"
            color="oklch(98.5% 0 0)"
          />
          <StatCard
            label="30-Day Win Rate"
            value={loading ? '—' : winRate != null ? `${winRate.toFixed(1)}%` : '—'}
            sub={
              stats?.graded_30d
                ? `${stats.graded_30d.wins}W ${stats.graded_30d.losses}L ${stats.graded_30d.pushes}P`
                : 'graded picks'
            }
            color={wrColor}
          />
          <StatCard
            label="30-Day P/L"
            value={
              loading
                ? '—'
                : totalPL != null
                ? `${totalPL >= 0 ? '+' : ''}${totalPL.toFixed(2)}u`
                : '—'
            }
            sub="units profit/loss"
            color={plColor}
          />
        </div>

        {/* ── 2. Today's Picks ────────────────────────────────────────── */}
        <div style={{ marginBottom: 28 }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 4,
          }}>
            <TrendingUp size={15} style={{ color: EMERALD }} />
            <span style={{
              fontSize: '0.75rem',
              fontWeight: 800,
              color: MUTED_FG,
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
            }}>
              Today's Picks
            </span>
            {!loading && (
              <span style={{
                fontSize: '0.68rem',
                fontWeight: 700,
                color: BLUE,
                background: `color-mix(in oklch, ${BLUE} 14%, transparent)`,
                border: `1px solid color-mix(in oklch, ${BLUE} 35%, transparent)`,
                borderRadius: 10,
                padding: '1px 8px',
              }}>
                {filteredPending.length}{filteredPending.length !== pending.length ? ` / ${pending.length}` : ''} pending
              </span>
            )}
          </div>

          {/* Filter bar — shown once data is loaded */}
          {!loading && pending.length > 0 && (
            <FilterBar
              picks={pending}
              sport={filterSport} setSport={setFilterSport}
              type={filterType}   setType={setFilterType}
              conf={filterConf}   setConf={setFilterConf}
            />
          )}

          {loading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[...Array(3)].map((_, i) => (
                <div key={i} className="skeleton" style={{ height: 110 }} />
              ))}
            </div>
          )}

          {!loading && pending.length === 0 && (
            <div className="empty-state">
              <h3>No Pending Picks Today</h3>
              <p>Check back later — predictions are generated daily before game time.</p>
            </div>
          )}

          {!loading && filteredPending.length === 0 && pending.length > 0 && (
            <div className="empty-state">
              <h3>No Picks Match These Filters</h3>
              <p>Try adjusting the sport, type, or confidence filters above.</p>
            </div>
          )}

          {!loading && filteredPending.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {filteredPending.map((pick) => (
                <PickDetailCard key={pick.id} pick={pick} />
              ))}
            </div>
          )}
        </div>

        {/* ── 3. Recent Results ───────────────────────────────────────── */}
        <div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 12,
          }}>
            <BarChart3 size={15} style={{ color: YELLOW }} />
            <span style={{
              fontSize: '0.75rem',
              fontWeight: 800,
              color: MUTED_FG,
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
            }}>
              Recent Results
            </span>
            <span style={{
              fontSize: '0.68rem',
              color: MUTED_FG,
              fontWeight: 500,
            }}>
              Last 7 days
            </span>
          </div>

          {loading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {[...Array(5)].map((_, i) => (
                <div key={i} className="skeleton" style={{ height: 56 }} />
              ))}
            </div>
          )}

          {!loading && graded.length === 0 && (
            <div className="empty-state">
              <h3>No Graded Results Yet</h3>
              <p>Results appear here once games complete and picks are graded.</p>
            </div>
          )}

          {!loading && graded.length > 0 && (
            <div className="data-table-wrap" style={{ padding: 0, overflow: 'hidden' }}>
              {/* Table header */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '8px 14px',
                borderBottom: `1px solid ${BORDER_STR}`,
                background: 'oklch(22% 0 0)',
              }}>
                <div style={{ flex: 1, minWidth: 180, fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase' }}>Matchup</div>
                <div style={{ minWidth: 120, fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase' }}>Pick</div>
                <div style={{ minWidth: 60, textAlign: 'center', fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase' }}>Result</div>
                <div style={{ minWidth: 70, textAlign: 'right', fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase' }}>P/L</div>
              </div>
              {graded.map((pick) => (
                <GradedPickRow key={pick.id} pick={pick} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Methodology + Disclaimer ───────────────────────────────── */}
      <MethodologySection />

      <style>{`
        @keyframes mev-spin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        .mev-accordion-body {
          overflow: hidden;
          transition: max-height 0.3s ease, opacity 0.25s ease;
        }
      `}</style>
    </div>
  );
}

// ── MethodologySection ────────────────────────────────────────────────────────
function MethodologySection() {
  const [open, setOpen] = useState(false);

  const sectionStyle: React.CSSProperties = {
    marginTop: 28,
    border: `1px solid ${BORDER_STR}`,
    borderRadius: 8,
    overflow: 'hidden',
  };
  const headerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '11px 16px',
    cursor: 'pointer',
    background: 'oklch(22% 0 0)',
    userSelect: 'none' as const,
  };
  const bodyStyle: React.CSSProperties = {
    padding: open ? '18px 18px 20px' : '0 18px',
    maxHeight: open ? 2000 : 0,
    opacity: open ? 1 : 0,
    overflow: 'hidden',
    transition: 'max-height 0.35s ease, opacity 0.25s ease, padding 0.25s ease',
  };
  const h3: React.CSSProperties = {
    fontSize: '0.72rem',
    fontWeight: 800,
    color: 'oklch(90% 0 0)',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    marginBottom: 8,
    marginTop: 16,
  };
  const p: React.CSSProperties = {
    fontSize: '0.78rem',
    color: MUTED_FG,
    lineHeight: 1.65,
    marginBottom: 10,
  };
  const pill = (label: string, color: string) => (
    <span key={label} style={{
      display: 'inline-block',
      padding: '2px 9px',
      borderRadius: 12,
      fontSize: '0.67rem',
      fontWeight: 700,
      marginRight: 6,
      marginBottom: 4,
      background: `color-mix(in oklch, ${color} 15%, transparent)`,
      color,
      border: `1px solid color-mix(in oklch, ${color} 35%, transparent)`,
    }}>{label}</span>
  );

  return (
    <div style={sectionStyle}>
      <div style={headerStyle} onClick={() => setOpen(o => !o)}>
        <Info size={13} style={{ color: BLUE }} />
        <span style={{ fontSize: '0.72rem', fontWeight: 800, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', flex: 1 }}>
          How Picks Are Generated &amp; Edge Explained
        </span>
        <ChevronDown size={14} style={{ color: MUTED_FG, transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.25s' }} />
      </div>

      <div style={bodyStyle}>
        {/* How edges are calculated */}
        <div style={h3}>How Edge Is Calculated</div>
        <p style={p}>
          <strong style={{ color: 'oklch(90% 0 0)' }}>Edge %</strong> is the gap between our estimated fair probability and the probability implied by the market
          odds — after vig (the bookmaker's cut) is removed. A +5% edge means we believe the true
          probability of winning is 5 percentage points higher than what the odds reflect.
        </p>
        <p style={p}>
          We use three rule-based detectors to identify value:
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 12 }}>
          {[
            {
              label: 'Multibook Vig Removal',
              color: BLUE,
              text: 'Compares implied probabilities across all available books. When one book\'s line diverges from the consensus by ≥3%, the market is mispriced — we flag the side offering the better-than-consensus price. The consensus itself (vig-removed) is our fair value estimate.',
            },
            {
              label: 'Pitching Luck Regression (MLB)',
              color: BRAND_RED,
              text: 'ERA vs xERA (expected ERA based on quality of contact). Pitchers with ERA well below xERA have been lucky — regression toward the mean suggests more runs allowed going forward. Combined home + away gap drives an over/under lean on game totals.',
            },
            {
              label: 'Lineup xwOBA Regression (MLB)',
              color: YELLOW,
              text: 'Teams hitting the ball much harder than results show (xwOBA far above wOBA) are underperforming their true talent. When such a team is priced as a significant underdog (+150 or worse), there may be ML value.',
            },
          ].map(({ label, color, text }) => (
            <div key={label} style={{
              padding: '10px 12px',
              borderRadius: 6,
              border: `1px solid color-mix(in oklch, ${color} 25%, transparent)`,
              background: `color-mix(in oklch, ${color} 6%, transparent)`,
            }}>
              <div style={{ fontSize: '0.7rem', fontWeight: 800, color, marginBottom: 5, letterSpacing: '0.05em' }}>{label}</div>
              <div style={{ fontSize: '0.76rem', color: MUTED_FG, lineHeight: 1.6 }}>{text}</div>
            </div>
          ))}
        </div>

        {/* Confidence tiers */}
        <div style={h3}>Confidence Tiers</div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
          {[
            { tier: 'High', color: EMERALD, desc: 'Multiple corroborating signals (3+ books flagged, strong Statcast edge), edge ≥5%' },
            { tier: 'Medium', color: YELLOW, desc: 'Clear edge with moderate corroboration, edge 3–5%' },
            { tier: 'Low', color: BRAND_RED, desc: 'Single signal, thinner edge 1–3% — use as supplementary context only' },
          ].map(({ tier, color, desc }) => (
            <div key={tier} style={{ flex: '1 1 200px', padding: '8px 12px', borderRadius: 6, border: `1px solid ${BORDER}` }}>
              <div style={{ fontSize: '0.68rem', fontWeight: 800, color, marginBottom: 4, letterSpacing: '0.06em', textTransform: 'uppercase' }}>{tier}</div>
              <div style={{ fontSize: '0.72rem', color: MUTED_FG, lineHeight: 1.5 }}>{desc}</div>
            </div>
          ))}
        </div>

        {/* Disclaimer */}
        <div style={{
          marginTop: 16,
          padding: '12px 14px',
          borderRadius: 6,
          border: `1px solid color-mix(in oklch, ${BRAND_RED} 30%, transparent)`,
          background: `color-mix(in oklch, ${BRAND_RED} 6%, transparent)`,
        }}>
          <div style={{ fontSize: '0.68rem', fontWeight: 800, color: BRAND_RED, marginBottom: 6, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            Disclaimer — For Informational &amp; Entertainment Purposes Only
          </div>
          <p style={{ ...p, marginBottom: 4, fontSize: '0.73rem' }}>
            All picks and edge calculations generated by Max EV Sports are <strong style={{ color: 'oklch(90% 0 0)' }}>algorithmic outputs based on
            publicly available data</strong> and do not constitute financial, legal, or sports betting advice.
            Past performance does not guarantee future results. Sports betting involves substantial risk
            of loss.
          </p>
          <p style={{ ...p, marginBottom: 0, fontSize: '0.73rem' }}>
            Picks are generated for analytical and entertainment purposes only. Always gamble responsibly
            and within your means. If you or someone you know has a gambling problem, contact the
            National Problem Gambling Helpline at <strong style={{ color: 'oklch(90% 0 0)' }}>1-800-522-4700</strong>.
          </p>
        </div>
      </div>
    </div>
  );
}
