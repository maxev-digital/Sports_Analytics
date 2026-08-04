import { useState } from 'react';
import { ChevronDown, TrendingUp, TrendingDown, Minus, AlertCircle, Activity } from 'lucide-react';

// ── Design tokens (match Picks.tsx) ─────────────────────────────────────────
const EMERALD    = 'oklch(69.6% .17 162.48)';
const BRAND_RED  = 'oklch(63.7% .237 25.331)';
const BLUE       = 'oklch(62.3% .214 259.815)';
const YELLOW     = 'oklch(79.5% .184 86.047)';
const MUTED_FG   = 'oklch(70.8% 0 0)';
const BORDER     = 'oklch(100% 0 0 / .1)';
const BORDER_STR = 'oklch(100% 0 0 / .18)';
const CARD_BG    = 'oklch(20% 0 0)';
const SECTION_BG = 'oklch(17% 0 0)';

// ── Types ────────────────────────────────────────────────────────────────────
export interface TeamRating {
  team: string;
  sport: string;
  power_rating: number | null;
  dvoa_total: number | null;
  dvoa_offense: number | null;
  dvoa_defense: number | null;
  sp_rating: number | null;
  sp_offense: number | null;
  sp_defense: number | null;
  wins: number;
  losses: number;
  point_diff_avg: number | null;
}

export interface LineSnapshot {
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  spread_home: number | null;
  total_line: number | null;
  home_ml: number | null;
  away_ml: number | null;
  books_sampled: number | null;
  snapshot_label: string | null;
  snapshot_at: string | null;
  id?: string;
}

export interface H2HGame {
  season: number;
  week: number | null;
  game_date: string;
  home_team: string;
  away_team: string;
  home_score: number | null;
  away_score: number | null;
  spread_close: number | null;
  home_covered: boolean | null;
  total_close: number | null;
  total_went_over: boolean | null;
}

export interface ATSSplit {
  team: string;
  role: string;
  games: number;
  covers: number;
  cover_pct: number;
  from_season: number;
  to_season: number;
}

export interface InjuryEntry {
  player_name: string;
  team: string;
  position: string | null;
  status: string | null;
  injury_type: string | null;
  description: string | null;
}

export interface EnrichedPick {
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
  home_rating: TeamRating | null;
  away_rating: TeamRating | null;
  line_snapshots: LineSnapshot[];
  h2h: H2HGame[];
  home_ats: ATSSplit | null;
  away_ats: ATSSplit | null;
  home_injuries: InjuryEntry[];
  away_injuries: InjuryEntry[];
  features?: Record<string, number | string> | null;
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function fmtOdds(odds: number): string {
  return odds >= 0 ? `+${odds}` : `${odds}`;
}

function fmtSpread(n: number): string {
  return n > 0 ? `+${n}` : `${n}`;
}

function fmtDate(ts: string | null): string {
  if (!ts) return '—';
  const d = new Date(ts);
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
}

function fmtTime(ts: string | null): string {
  if (!ts) return '—';
  const d = new Date(ts);
  return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: 'America/Chicago' }) + ' CST';
}

function fmtPct(n: number | null | undefined, decimals = 1): string {
  if (n == null) return '—';
  return `${n.toFixed(decimals)}%`;
}

function fmtRating(n: number | null | undefined, decimals = 1, sign = true): string {
  if (n == null) return '—';
  if (sign && n > 0) return `+${n.toFixed(decimals)}`;
  return n.toFixed(decimals);
}

function getSportColor(sport: string): string {
  const map: Record<string, string> = {
    mlb: EMERALD,
    wnba: BRAND_RED,
    tennis: YELLOW,
    soccer: BLUE,
    nfl: BLUE,
    ncaaf: YELLOW,
  };
  return map[sport.toLowerCase()] ?? MUTED_FG;
}

function getSportLabel(sport: string): string {
  const map: Record<string, string> = {
    mlb: 'MLB', wnba: 'WNBA', tennis: 'Tennis', soccer: 'Soccer',
    nfl: 'NFL', ncaaf: 'NCAAF',
  };
  return map[sport.toLowerCase()] ?? sport.toUpperCase();
}

function derivePickDisplay(pick: EnrichedPick): { label: string; sublabel: string } {
  const latest = pick.line_snapshots[pick.line_snapshots.length - 1];
  const earliest = pick.line_snapshots[0];
  const snap = latest ?? earliest;

  if (pick.pick_type === 'totals' || pick.pick_type === 'total') {
    const dir = pick.pick_side === 'over' ? 'OVER' : 'UNDER';
    const num = pick.total_line ?? snap?.total_line;
    return { label: `${dir} ${num ?? '?'}`, sublabel: 'Totals' };
  }

  if (pick.pick_type === 'h2h' || pick.pick_type === 'moneyline') {
    const team = pick.pick_side === 'home' ? pick.home_team : pick.away_team;
    return { label: team.toUpperCase(), sublabel: 'Moneyline' };
  }

  // Spread
  const team = pick.pick_side === 'home' ? pick.home_team : pick.away_team;
  if (snap?.spread_home != null) {
    const raw = pick.pick_side === 'home' ? snap.spread_home : -snap.spread_home;
    return { label: `${team.toUpperCase()} ${fmtSpread(raw)}`, sublabel: 'ATS' };
  }
  return { label: team.toUpperCase(), sublabel: 'Spread' };
}

function confidenceColor(tier: string | null): string {
  if (!tier) return MUTED_FG;
  const t = tier.toLowerCase();
  if (t === 'high') return EMERALD;
  if (t === 'medium') return YELLOW;
  return MUTED_FG;
}

function atsColor(pct: number): string {
  if (pct >= 58) return EMERALD;
  if (pct <= 42) return BRAND_RED;
  return YELLOW;
}

function injuryStatusColor(status: string | null): string {
  if (!status) return MUTED_FG;
  const s = status.toLowerCase();
  if (s.includes('out') || s.includes('ir')) return BRAND_RED;
  if (s.includes('questionable')) return YELLOW;
  if (s.includes('doubtful')) return '#ff8c42';
  return MUTED_FG;
}

// ── Accordion section ────────────────────────────────────────────────────────
interface AccordionProps {
  title: string;
  badge?: string;
  badgeColor?: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  disabled?: boolean;
  disabledLabel?: string;
}

function AccordionSection({ title, badge, badgeColor, children, defaultOpen = false, disabled = false, disabledLabel }: AccordionProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div style={{ borderTop: `1px solid ${BORDER}` }}>
      <button
        onClick={() => !disabled && setOpen(o => !o)}
        disabled={disabled}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.75rem 1.25rem',
          background: 'transparent',
          border: 'none',
          cursor: disabled ? 'default' : 'pointer',
          color: disabled ? MUTED_FG : 'oklch(90% 0 0)',
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <span style={{ fontSize: '0.7rem', letterSpacing: '0.08em', fontWeight: 700 }}>{title}</span>
          {badge && (
            <span style={{
              fontSize: '0.6rem', fontWeight: 700, letterSpacing: '0.06em',
              padding: '0.15rem 0.45rem', borderRadius: 3,
              background: badgeColor ? `${badgeColor}20` : `${MUTED_FG}20`,
              color: badgeColor ?? MUTED_FG,
              border: `1px solid ${badgeColor ? `${badgeColor}40` : `${MUTED_FG}40`}`,
            }}>
              {badge}
            </span>
          )}
          {disabled && disabledLabel && (
            <span style={{ fontSize: '0.6rem', color: MUTED_FG, fontStyle: 'italic' }}>{disabledLabel}</span>
          )}
        </span>
        {!disabled && (
          <ChevronDown size={14} style={{ transform: open ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform .2s ease', color: MUTED_FG }} />
        )}
      </button>
      <div style={{ maxHeight: open ? '2000px' : '0', overflow: 'hidden', transition: 'max-height .35s ease' }}>
        <div style={{ padding: '0 1.25rem 1.25rem' }}>
          {children}
        </div>
      </div>
    </div>
  );
}

// ── Stat row helper ──────────────────────────────────────────────────────────
function StatRow({ label, homeVal, awayVal, homeColor, awayColor, higherBetter = true }: {
  label: string;
  homeVal: string;
  awayVal: string;
  homeColor?: string;
  awayColor?: string;
  higherBetter?: boolean;
}) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '0.5rem', alignItems: 'center', padding: '0.3rem 0' }}>
      <span style={{ color: homeColor ?? 'oklch(88% 0 0)', fontWeight: 600, fontSize: '0.82rem' }}>{homeVal}</span>
      <span style={{ color: MUTED_FG, fontSize: '0.65rem', textAlign: 'center', letterSpacing: '0.06em', whiteSpace: 'nowrap' }}>{label}</span>
      <span style={{ color: awayColor ?? 'oklch(88% 0 0)', fontWeight: 600, fontSize: '0.82rem', textAlign: 'right' }}>{awayVal}</span>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export function PickDetailCard({ pick }: { pick: EnrichedPick }) {
  const [narrativeExpanded, setNarrativeExpanded] = useState(false);
  const sportColor = getSportColor(pick.sport);
  const { label: pickLabel, sublabel: pickSublabel } = derivePickDisplay(pick);
  const latestSnap = pick.line_snapshots[pick.line_snapshots.length - 1];
  const openSnap = pick.line_snapshots[0];
  const hasSpreads = latestSnap?.spread_home != null;

  const lineChanged = openSnap && latestSnap && openSnap.id !== latestSnap.id &&
    (openSnap.spread_home !== latestSnap.spread_home || openSnap.home_ml !== latestSnap.home_ml);

  const narrative = pick.sonnet_narrative ?? '';
  const narrativeTruncated = narrative.length > 500;
  const displayedNarrative = narrativeExpanded || !narrativeTruncated ? narrative : narrative.slice(0, 500) + '…';

  const hasRatings = pick.home_rating || pick.away_rating;
  const hasH2H = pick.h2h && pick.h2h.length > 0;
  const hasATS = pick.home_ats || pick.away_ats;
  const hasInjuries = pick.home_injuries.length > 0 || pick.away_injuries.length > 0;
  const featureEntries = pick.features ? Object.entries(pick.features) : [];
  const hasFeatures = featureEntries.length > 0;

  return (
    <div style={{
      background: CARD_BG,
      border: `1px solid ${BORDER_STR}`,
      borderRadius: 8,
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
    }}>

      {/* ── Sport color stripe ─────────────────────────────────────────── */}
      <div style={{ height: 3, background: sportColor }} />

      {/* ── Header: matchup info ──────────────────────────────────────── */}
      <div style={{ padding: '1rem 1.25rem 0.75rem', borderBottom: `1px solid ${BORDER}` }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{
              fontSize: '0.6rem', fontWeight: 800, letterSpacing: '0.1em',
              padding: '0.2rem 0.55rem', borderRadius: 3,
              background: `${sportColor}18`,
              color: sportColor,
              border: `1px solid ${sportColor}35`,
            }}>
              {getSportLabel(pick.sport)}
            </span>
            <span style={{ fontSize: '0.75rem', color: 'oklch(88% 0 0)', fontWeight: 600 }}>
              {pick.away_team} <span style={{ color: MUTED_FG }}>@</span> {pick.home_team}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontSize: '0.72rem', color: MUTED_FG }}>{fmtDate(pick.game_time_cst)}</span>
            <span style={{ fontSize: '0.72rem', color: MUTED_FG }}>{fmtTime(pick.game_time_cst)}</span>
          </div>
        </div>
      </div>

      {/* ── THE PICK callout ──────────────────────────────────────────── */}
      <div style={{
        padding: '1.25rem',
        background: `${sportColor}08`,
        borderBottom: `1px solid ${BORDER}`,
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
      }}>
        <div>
          <div style={{ fontSize: '0.6rem', color: MUTED_FG, letterSpacing: '0.1em', fontWeight: 700, marginBottom: '0.3rem' }}>
            OUR PICK — {pickSublabel.toUpperCase()}
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'oklch(95% 0 0)', letterSpacing: '-0.01em', lineHeight: 1 }}>
            {pickLabel}
          </div>
          {latestSnap?.spread_home != null && pick.pick_type !== 'h2h' && (
            <div style={{ marginTop: '0.35rem', fontSize: '0.7rem', color: MUTED_FG }}>
              Line: {pick.home_team.split(' ').pop()} {fmtSpread(latestSnap.spread_home)}
              {latestSnap.total_line ? ` · Total ${latestSnap.total_line}` : ''}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'flex-end' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.6rem', color: MUTED_FG, letterSpacing: '0.08em', marginBottom: '0.2rem' }}>ODDS</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'oklch(90% 0 0)' }}>{fmtOdds(pick.market_odds)}</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.6rem', color: MUTED_FG, letterSpacing: '0.08em', marginBottom: '0.2rem' }}>EDGE</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: pick.edge_pct >= 4 ? EMERALD : pick.edge_pct >= 2.5 ? YELLOW : MUTED_FG }}>
              +{pick.edge_pct.toFixed(2)}%
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.6rem', color: MUTED_FG, letterSpacing: '0.08em', marginBottom: '0.2rem' }}>CONF</div>
            <div style={{
              fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.06em',
              color: confidenceColor(pick.confidence_tier),
              textTransform: 'uppercase',
            }}>
              {pick.confidence_tier ?? 'LOW'}
            </div>
          </div>
        </div>
      </div>

      {/* ── Game Script (narrative) ───────────────────────────────────── */}
      {narrative && (
        <div style={{ padding: '1.25rem', borderBottom: `1px solid ${BORDER}` }}>
          <div style={{ fontSize: '0.6rem', fontWeight: 700, letterSpacing: '0.1em', color: MUTED_FG, marginBottom: '0.75rem' }}>
            GAME SCRIPT — EXPERT ANALYSIS
          </div>
          <div style={{ fontSize: '0.85rem', lineHeight: 1.75, color: 'oklch(88% 0 0)', whiteSpace: 'pre-line' }}>
            {displayedNarrative}
          </div>
          {narrativeTruncated && (
            <button
              onClick={() => setNarrativeExpanded(e => !e)}
              style={{
                marginTop: '0.75rem',
                background: 'transparent',
                border: `1px solid ${BORDER_STR}`,
                borderRadius: 4,
                color: sportColor,
                fontSize: '0.72rem',
                fontWeight: 600,
                cursor: 'pointer',
                padding: '0.35rem 0.85rem',
                letterSpacing: '0.04em',
              }}
            >
              {narrativeExpanded ? 'Show Less' : 'Read Full Analysis'}
            </button>
          )}
        </div>
      )}

      {/* ── Model Summary bar ────────────────────────────────────────── */}
      <div style={{ padding: '0.85rem 1.25rem', borderBottom: `1px solid ${BORDER}`, display: 'flex', flexWrap: 'wrap', gap: '1.5rem' }}>
        <div>
          <span style={{ fontSize: '0.6rem', color: MUTED_FG, letterSpacing: '0.08em' }}>OUR PROB </span>
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: BLUE }}>{fmtPct(pick.our_probability * 100)}</span>
        </div>
        <div>
          <span style={{ fontSize: '0.6rem', color: MUTED_FG, letterSpacing: '0.08em' }}>MKT IMPLIED </span>
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'oklch(88% 0 0)' }}>{fmtPct(pick.market_implied_prob * 100)}</span>
        </div>
        <div>
          <span style={{ fontSize: '0.6rem', color: MUTED_FG, letterSpacing: '0.08em' }}>EDGE </span>
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: EMERALD }}>+{pick.edge_pct.toFixed(2)}%</span>
        </div>
        <div>
          <span style={{ fontSize: '0.6rem', color: MUTED_FG, letterSpacing: '0.08em' }}>MODEL </span>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'oklch(80% 0 0)' }}>
            {pick.detector.replace('rule_', '').replace('_', ' ').toUpperCase()}
          </span>
        </div>
        {pick.home_rating && (
          <div>
            <span style={{ fontSize: '0.6rem', color: MUTED_FG, letterSpacing: '0.08em' }}>SIGNAL LAYERS </span>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: YELLOW }}>Power Ratings + Multibook Vig</span>
          </div>
        )}
      </div>

      {/* ══ ACCORDION SECTIONS ══════════════════════════════════════════ */}

      {/* Market Data & Line Movement */}
      <AccordionSection
        title="MARKET DATA & LINE MOVEMENT"
        badge={lineChanged ? 'MOVED' : 'STABLE'}
        badgeColor={lineChanged ? YELLOW : EMERALD}
      >
        {pick.line_snapshots.length === 0 ? (
          <p style={{ fontSize: '0.78rem', color: MUTED_FG }}>No line snapshots available yet. Tracker runs 3x daily.</p>
        ) : (
          <>
            {/* Opening vs current comparison */}
            {openSnap && latestSnap && openSnap.id !== latestSnap.id && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                {[{ label: 'OPEN', snap: openSnap }, { label: 'CURRENT', snap: latestSnap }].map(({ label, snap }) => (
                  <div key={label} style={{
                    background: SECTION_BG, borderRadius: 6, padding: '0.75rem',
                    border: `1px solid ${BORDER}`,
                  }}>
                    <div style={{ fontSize: '0.6rem', color: MUTED_FG, letterSpacing: '0.08em', marginBottom: '0.5rem' }}>{label}</div>
                    {snap.spread_home != null && (
                      <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'oklch(88% 0 0)', marginBottom: '0.2rem' }}>
                        {pick.home_team.split(' ').pop()} {fmtSpread(snap.spread_home)} / {pick.away_team.split(' ').pop()} {fmtSpread(-snap.spread_home)}
                      </div>
                    )}
                    {snap.total_line != null && (
                      <div style={{ fontSize: '0.75rem', color: MUTED_FG }}>Total: {snap.total_line}</div>
                    )}
                    {snap.home_ml != null && (
                      <div style={{ fontSize: '0.75rem', color: MUTED_FG }}>
                        ML: {fmtOdds(snap.home_ml)} / {fmtOdds(snap.away_ml ?? 0)}
                      </div>
                    )}
                    {snap.books_sampled != null && (
                      <div style={{ fontSize: '0.65rem', color: MUTED_FG, marginTop: '0.25rem' }}>{snap.books_sampled} books</div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Snapshot table */}
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.76rem' }}>
                <thead>
                  <tr>
                    {['Snapshot', 'Spread', 'Total', 'Home ML', 'Away ML', 'Books'].map(h => (
                      <th key={h} style={{
                        textAlign: 'left', padding: '0.3rem 0.5rem',
                        fontSize: '0.6rem', letterSpacing: '0.07em', color: MUTED_FG,
                        borderBottom: `1px solid ${BORDER}`,
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {pick.line_snapshots.map((s, i) => (
                    <tr key={i} style={{ borderBottom: `1px solid ${BORDER}` }}>
                      <td style={{ padding: '0.35rem 0.5rem', color: MUTED_FG }}>{s.snapshot_label ?? s.snapshot_at?.slice(5, 16) ?? '—'}</td>
                      <td style={{ padding: '0.35rem 0.5rem', color: 'oklch(88% 0 0)', fontWeight: 600 }}>
                        {s.spread_home != null ? `${pick.home_team.split(' ').pop()} ${fmtSpread(s.spread_home)}` : '—'}
                      </td>
                      <td style={{ padding: '0.35rem 0.5rem', color: 'oklch(88% 0 0)' }}>{s.total_line ?? '—'}</td>
                      <td style={{ padding: '0.35rem 0.5rem', color: 'oklch(88% 0 0)' }}>{s.home_ml != null ? fmtOdds(s.home_ml) : '—'}</td>
                      <td style={{ padding: '0.35rem 0.5rem', color: 'oklch(88% 0 0)' }}>{s.away_ml != null ? fmtOdds(s.away_ml) : '—'}</td>
                      <td style={{ padding: '0.35rem 0.5rem', color: MUTED_FG }}>{s.books_sampled ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Line movement summary */}
            {lineChanged && openSnap && latestSnap && (
              <div style={{ marginTop: '0.85rem', padding: '0.6rem 0.85rem', background: `${YELLOW}10`, borderRadius: 5, border: `1px solid ${YELLOW}25` }}>
                <div style={{ fontSize: '0.7rem', color: YELLOW, fontWeight: 600 }}>
                  Line Movement Detected
                </div>
                {openSnap.spread_home !== latestSnap.spread_home && (
                  <div style={{ fontSize: '0.72rem', color: MUTED_FG, marginTop: '0.2rem' }}>
                    Spread shifted: {fmtSpread(openSnap.spread_home ?? 0)} → {fmtSpread(latestSnap.spread_home ?? 0)}
                    {(latestSnap.spread_home ?? 0) < (openSnap.spread_home ?? 0)
                      ? ' (home team getting more action / sharps on home)'
                      : ' (away team getting more action / sharps on away)'}
                  </div>
                )}
                {openSnap.home_ml !== latestSnap.home_ml && openSnap.spread_home === latestSnap.spread_home && (
                  <div style={{ fontSize: '0.72rem', color: MUTED_FG, marginTop: '0.2rem' }}>
                    Juice drift: {fmtOdds(openSnap.home_ml ?? 0)}/{fmtOdds(openSnap.away_ml ?? 0)} → {fmtOdds(latestSnap.home_ml ?? 0)}/{fmtOdds(latestSnap.away_ml ?? 0)}
                    — public money shading toward {(latestSnap.home_ml ?? 0) < (openSnap.home_ml ?? 0) ? pick.home_team : pick.away_team}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </AccordionSection>

      {/* Power Ratings */}
      <AccordionSection
        title="POWER RATINGS"
        badge={hasRatings ? (pick.sport === 'nfl' ? 'DVOA' : 'SP+') : undefined}
        badgeColor={BLUE}
        disabled={!hasRatings}
        disabledLabel="Ratings not yet loaded"
      >
        {hasRatings && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '0', marginBottom: '0.5rem' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'oklch(88% 0 0)' }}>{pick.home_team}</div>
              <div style={{ width: 80 }} />
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'oklch(88% 0 0)', textAlign: 'right' }}>{pick.away_team}</div>
            </div>
            <div style={{ marginBottom: '0.25rem', fontSize: '0.6rem', color: MUTED_FG, letterSpacing: '0.06em' }}>
              HOME · {pick.home_rating?.wins ?? 0}-{pick.home_rating?.losses ?? 0} &nbsp;|&nbsp; AWAY · {pick.away_rating?.wins ?? 0}-{pick.away_rating?.losses ?? 0}
            </div>
            <div style={{ borderTop: `1px solid ${BORDER}`, marginTop: '0.6rem', paddingTop: '0.6rem' }}>
              {pick.sport === 'nfl' && (
                <>
                  <StatRow
                    label="POWER RTG"
                    homeVal={fmtRating(pick.home_rating?.power_rating)}
                    awayVal={fmtRating(pick.away_rating?.power_rating)}
                  />
                  <StatRow label="DVOA TOTAL" homeVal={fmtPct(pick.home_rating?.dvoa_total)} awayVal={fmtPct(pick.away_rating?.dvoa_total)} />
                  <StatRow label="OFF DVOA"   homeVal={fmtPct(pick.home_rating?.dvoa_offense)} awayVal={fmtPct(pick.away_rating?.dvoa_offense)} />
                  <StatRow label="DEF DVOA"   homeVal={fmtPct(pick.home_rating?.dvoa_defense)} awayVal={fmtPct(pick.away_rating?.dvoa_defense)} />
                  <StatRow label="PT DIFF/G"  homeVal={fmtRating(pick.home_rating?.point_diff_avg, 1)} awayVal={fmtRating(pick.away_rating?.point_diff_avg, 1)} />
                </>
              )}
              {pick.sport === 'ncaaf' && (
                <>
                  <StatRow label="SP+ RTG"    homeVal={fmtRating(pick.home_rating?.sp_rating)}  awayVal={fmtRating(pick.away_rating?.sp_rating)} />
                  <StatRow label="SP+ OFF"    homeVal={fmtRating(pick.home_rating?.sp_offense)} awayVal={fmtRating(pick.away_rating?.sp_offense)} />
                  <StatRow label="SP+ DEF"    homeVal={fmtRating(pick.home_rating?.sp_defense)} awayVal={fmtRating(pick.away_rating?.sp_defense)} />
                  <StatRow label="POWER RTG"  homeVal={fmtRating(pick.home_rating?.power_rating)} awayVal={fmtRating(pick.away_rating?.power_rating)} />
                </>
              )}
            </div>
            <div style={{ marginTop: '0.75rem', fontSize: '0.68rem', color: MUTED_FG, fontStyle: 'italic' }}>
              {pick.sport === 'nfl'
                ? 'DVOA: Defense-adjusted Value Over Average. Positive offense = above avg; negative defense = elite (fewer points allowed).'
                : 'SP+: Bill Connelly predictive model. Higher = stronger team.'}
            </div>
          </>
        )}
      </AccordionSection>

      {/* Historical ATS */}
      <AccordionSection
        title="HISTORICAL ATS SPLITS"
        badge={hasATS ? 'SINCE 2022' : undefined}
        badgeColor={YELLOW}
        disabled={!hasATS}
        disabledLabel={!['nfl', 'ncaaf'].includes(pick.sport) ? 'NFL/NCAAF historical data only' : 'No ATS data found'}
      >
        {hasATS && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem', marginBottom: '0.85rem' }}>
              {[pick.home_ats, pick.away_ats].filter(Boolean).map(ats => ats && (
                <div key={ats.role} style={{
                  background: SECTION_BG, borderRadius: 6, padding: '0.85rem',
                  border: `1px solid ${BORDER}`,
                }}>
                  <div style={{ fontSize: '0.6rem', color: MUTED_FG, letterSpacing: '0.08em', marginBottom: '0.4rem' }}>
                    {ats.role === 'home' ? 'AT HOME' : 'AS AWAY'} · {ats.from_season}–{ats.to_season}
                  </div>
                  <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'oklch(88% 0 0)', marginBottom: '0.4rem' }}>
                    {ats.team}
                  </div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: atsColor(ats.cover_pct) }}>
                    {ats.cover_pct}%
                  </div>
                  <div style={{ fontSize: '0.68rem', color: MUTED_FG, marginTop: '0.2rem' }}>
                    {ats.covers}/{ats.games} covers
                  </div>
                  {pick.pick_side === ats.role && (
                    <div style={{ marginTop: '0.4rem', fontSize: '0.65rem', color: sportColor, fontWeight: 600 }}>
                      ← OUR PICK SIDE
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div style={{ fontSize: '0.68rem', color: MUTED_FG, fontStyle: 'italic' }}>
              ATS cover rate since 2022 regular season. Push games excluded from calculation.
            </div>
          </>
        )}
      </AccordionSection>

      {/* Head to Head */}
      <AccordionSection
        title="HEAD TO HEAD"
        badge={hasH2H ? `LAST ${pick.h2h.length}` : undefined}
        badgeColor={MUTED_FG}
        disabled={!hasH2H}
        disabledLabel={!['nfl', 'ncaaf'].includes(pick.sport) ? 'NFL/NCAAF historical database only' : 'No H2H history found'}
      >
        {hasH2H && (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.74rem' }}>
              <thead>
                <tr>
                  {['Date', 'Site', 'Result', 'Spread', 'Cover', 'Total', 'O/U'].map(h => (
                    <th key={h} style={{
                      textAlign: 'left', padding: '0.3rem 0.5rem',
                      fontSize: '0.6rem', letterSpacing: '0.07em', color: MUTED_FG,
                      borderBottom: `1px solid ${BORDER}`, whiteSpace: 'nowrap',
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pick.h2h.map((g, i) => {
                  const homeWon = (g.home_score ?? 0) > (g.away_score ?? 0);
                  const winner = homeWon ? g.home_team.split(' ').pop() : g.away_team.split(' ').pop();
                  const score = g.home_score != null ? `${g.home_score}-${g.away_score}` : '—';
                  const coverTeam = g.home_covered ? g.home_team.split(' ').pop() : g.away_team.split(' ').pop();
                  return (
                    <tr key={i} style={{ borderBottom: `1px solid ${BORDER}` }}>
                      <td style={{ padding: '0.35rem 0.5rem', color: MUTED_FG, whiteSpace: 'nowrap' }}>
                        {g.game_date} {g.week ? `W${g.week}` : ''}
                      </td>
                      <td style={{ padding: '0.35rem 0.5rem', color: MUTED_FG, whiteSpace: 'nowrap' }}>
                        {g.home_team.split(' ').pop()}
                      </td>
                      <td style={{ padding: '0.35rem 0.5rem', fontWeight: 600, color: 'oklch(88% 0 0)', whiteSpace: 'nowrap' }}>
                        {winner} {score}
                      </td>
                      <td style={{ padding: '0.35rem 0.5rem', color: MUTED_FG }}>
                        {g.spread_close != null ? `${g.home_team.split(' ').pop()} ${fmtSpread(g.spread_close)}` : '—'}
                      </td>
                      <td style={{ padding: '0.35rem 0.5rem', whiteSpace: 'nowrap' }}>
                        <span style={{
                          fontSize: '0.65rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: 3,
                          background: g.home_covered == null ? `${MUTED_FG}15` : `${EMERALD}15`,
                          color: g.home_covered == null ? MUTED_FG : EMERALD,
                        }}>
                          {g.home_covered == null ? '—' : `${coverTeam} -${g.spread_close != null ? Math.abs(g.spread_close) : '?'}`}
                        </span>
                      </td>
                      <td style={{ padding: '0.35rem 0.5rem', color: MUTED_FG }}>{g.total_close ?? '—'}</td>
                      <td style={{ padding: '0.35rem 0.5rem' }}>
                        {g.total_went_over == null ? (
                          <span style={{ color: MUTED_FG }}>—</span>
                        ) : (
                          <span style={{
                            fontSize: '0.65rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: 3,
                            background: g.total_went_over ? `${BRAND_RED}15` : `${BLUE}15`,
                            color: g.total_went_over ? BRAND_RED : BLUE,
                          }}>
                            {g.total_went_over ? 'OVER' : 'UNDER'}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </AccordionSection>

      {/* Injury Report */}
      <AccordionSection
        title="INJURY REPORT"
        badge={hasInjuries ? `${pick.home_injuries.length + pick.away_injuries.length} LISTED` : undefined}
        badgeColor={pick.home_injuries.length + pick.away_injuries.length > 0 ? BRAND_RED : MUTED_FG}
        disabled={!hasInjuries}
        disabledLabel="No injuries listed"
      >
        {hasInjuries && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            {[
              { team: pick.home_team, label: 'HOME', injuries: pick.home_injuries },
              { team: pick.away_team, label: 'AWAY', injuries: pick.away_injuries },
            ].map(({ team, label, injuries }) => (
              <div key={label}>
                <div style={{ fontSize: '0.6rem', color: MUTED_FG, letterSpacing: '0.08em', marginBottom: '0.5rem' }}>
                  {team} ({label})
                </div>
                {injuries.length === 0 ? (
                  <div style={{ fontSize: '0.72rem', color: MUTED_FG, fontStyle: 'italic' }}>None listed</div>
                ) : (
                  injuries.map((inj, i) => (
                    <div key={i} style={{
                      display: 'flex', alignItems: 'flex-start', gap: '0.5rem',
                      padding: '0.35rem 0', borderBottom: i < injuries.length - 1 ? `1px solid ${BORDER}` : 'none',
                    }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '0.76rem', fontWeight: 600, color: 'oklch(88% 0 0)' }}>
                          {inj.player_name}
                          {inj.position && (
                            <span style={{ fontSize: '0.65rem', color: MUTED_FG, fontWeight: 400, marginLeft: '0.4rem' }}>
                              {inj.position}
                            </span>
                          )}
                        </div>
                        {inj.injury_type && (
                          <div style={{ fontSize: '0.68rem', color: MUTED_FG }}>{inj.injury_type}</div>
                        )}
                      </div>
                      <span style={{
                        fontSize: '0.6rem', fontWeight: 700, letterSpacing: '0.05em',
                        padding: '0.15rem 0.4rem', borderRadius: 3,
                        color: injuryStatusColor(inj.status),
                        background: `${injuryStatusColor(inj.status)}18`,
                        border: `1px solid ${injuryStatusColor(inj.status)}35`,
                        whiteSpace: 'nowrap',
                      }}>
                        {inj.status ?? 'GTD'}
                      </span>
                    </div>
                  ))
                )}
              </div>
            ))}
          </div>
        )}
      </AccordionSection>

      {/* Model Signals — raw feature vector */}
      <AccordionSection
        title="MODEL SIGNALS"
        badge={hasFeatures ? `${featureEntries.length} FACTORS` : undefined}
        badgeColor={BLUE}
        disabled={!hasFeatures}
        disabledLabel="No feature data"
      >
        {hasFeatures && (
          <>
            <div style={{ fontSize: '0.68rem', color: MUTED_FG, fontStyle: 'italic', marginBottom: '0.75rem' }}>
              Raw model inputs that drove this pick. These are the quantitative signals evaluated by the edge engine.
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem' }}>
              {featureEntries.map(([k, v]) => {
                const label = k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                const isPercent = k.includes('pct') || k.includes('prob') || k.includes('rate') || k.includes('edge');
                const isBool = v === 0 || v === 1;
                let display = '';
                if (isBool) display = v === 1 ? 'Yes' : 'No';
                else if (isPercent) display = `${(Number(v) * (Math.abs(Number(v)) <= 1 ? 100 : 1)).toFixed(1)}%`;
                else display = typeof v === 'number' ? Number(v).toFixed(3) : String(v);
                return (
                  <div key={k} style={{
                    background: SECTION_BG,
                    borderRadius: 5,
                    padding: '0.45rem 0.65rem',
                    border: `1px solid ${BORDER}`,
                  }}>
                    <div style={{ fontSize: '0.6rem', color: MUTED_FG, letterSpacing: '0.04em', marginBottom: '0.2rem' }}>
                      {label}
                    </div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'oklch(88% 0 0)' }}>
                      {display}
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </AccordionSection>

      {/* Coaching Matchup — Phase 5 placeholder */}
      <AccordionSection
        title="COACHING MATCHUP"
        disabled={true}
        disabledLabel="Phase 5 — Expert Agent (coming soon)"
      >
        <div />
      </AccordionSection>

    </div>
  );
}
