import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import '../styles/analytics.css';

const API_BASE = import.meta.env.DEV ? 'http://localhost:8889/api/f5' : '/api/f5';

// ── Design tokens — matches analytics.css oklch system ───────────────────
const CARD     = 'oklch(24% 0 0)';
const MUTED    = 'oklch(26.9% 0 0)';
const SIDEBAR  = 'oklch(20.5% 0 0)';
const BORDER   = 'oklch(100% 0 0 / .1)';
const FG       = 'oklch(98.5% 0 0)';
const MUTED_FG = 'oklch(70.8% 0 0)';
const BLUE     = 'oklch(62.3% .214 259.815)';
const EMERALD  = 'oklch(69.6% .17 162.48)';
const RED_ACC  = 'oklch(63.7% .237 25.331)';
const YELLOW   = 'oklch(79.5% .184 86.047)';

// ── Types ─────────────────────────────────────────────────────────────────

interface TeamData {
  abbr: string; name: string; full_name: string; logo: string;
  color: string; alt_color: string; rating: number | null;
  tier: string | null; rank: number | null; record: string | null;
}
interface Injury { name: string; position: string; status: string; detail: string; }
interface GameResult {
  event_id: string; week: number | null; date: string;
  at_vs: string; opponent: string; result: string;
}
interface TeamRecord { overall?: string; home?: string; road?: string; }
interface TeamStats {
  season?: number;
  pts_per_game?: number; pts_allowed_pg?: number;
  rush_yds_pg?: number; rush_ypa?: number;
  pass_yds_pg?: number; total_yds_pg?: number;
  fumbles_lost?: number; total_points?: number;
}
interface MatchupData {
  event_id: string; short_name: string; date: string; week: number | null;
  tv: string; neutral_site: boolean;
  venue: { name: string; city: string; state: string; indoor: boolean; grass: boolean; };
  home: TeamData; away: TeamData;
  odds: { spread: number | null; over_under: number | null; details: string;
          away_ml: number | null; home_ml: number | null;
          away_implied: number | null; home_implied: number | null; };
  espn_wp: { home: number | null; away: number | null; };
  model_wp: { home: number | null; away: number | null; };
  edge: { home: number | null; away: number | null; };
  injuries: { home: Injury[]; away: Injury[]; };
  home_record?: TeamRecord; away_record?: TeamRecord;
  home_last5?: GameResult[]; away_last5?: GameResult[];
  home_stats?: TeamStats; away_stats?: TeamStats;
}
interface Angle {
  name: string; label: string; fired: boolean;
  lean_level: string; lean_side: string | null; lean_market: string | null;
  reasoning: string; signals_cited: string[];
}
interface AnalysisData {
  event_id: string; home_team: string; away_team: string; source: string;
  generated_at: string; cached: boolean;
  angles: Angle[];
  convergence: {
    convergence_count: number; consensus_lean: string;
    consensus_side: string | null; consensus_market: string | null;
    dissent_flag: boolean; convergence_note: string;
  };
  verdict: {
    lean_level: string; lean_side: string | null; lean_market: string | null;
    unit_rec: number; game_script: string;
    signals_used: string[]; confidence_note: string;
  };
}

// ── Constants ─────────────────────────────────────────────────────────────

const LEAN_COLOR: Record<string, string> = {
  strong_lean:    EMERALD,
  favorable_lean: BLUE,
  slight_lean:    YELLOW,
  no_edge:        MUTED_FG,
};
const LEAN_LABEL: Record<string, string> = {
  strong_lean:    'STRONG LEAN',
  favorable_lean: 'FAVORABLE LEAN',
  slight_lean:    'SLIGHT LEAN',
  no_edge:        'NO EDGE',
};
const STATUS_COLOR: Record<string, string> = {
  Out: RED_ACC, Doubtful: 'oklch(70.5% .213 47.604)', Questionable: YELLOW, IR: RED_ACC,
};

// ── Sub-components ─────────────────────────────────────────────────────────

function WpDonut({ home, away, label }: { home: number | null; away: number | null; label: string }) {
  if (home === null) return <div style={{ color: MUTED_FG, fontSize: 12 }}>—</div>;
  const pct = Math.round(home * 100);
  const r = 34; const circ = 2 * Math.PI * r;
  const dash = (home * circ).toFixed(1);
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ fontSize: 10, color: MUTED_FG, marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.07em', fontWeight: 700 }}>{label}</div>
      <svg width="84" height="84" viewBox="0 0 84 84">
        <circle cx="42" cy="42" r={r} fill="none" stroke={MUTED} strokeWidth="7" />
        <circle cx="42" cy="42" r={r} fill="none" stroke={BLUE} strokeWidth="7"
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
          transform="rotate(-90 42 42)" />
        <text x="42" y="42" textAnchor="middle" dominantBaseline="central"
          fill={FG} fontSize="13" fontWeight="800">{pct}%</text>
      </svg>
      <div style={{ fontSize: 10, color: MUTED_FG, marginTop: 2 }}>
        Away {Math.round((away ?? 0) * 100)}%
      </div>
    </div>
  );
}

function AngleCard({ angle }: { angle: Angle }) {
  const [open, setOpen] = useState(false);
  const color = LEAN_COLOR[angle.lean_level] ?? MUTED_FG;
  const label = LEAN_LABEL[angle.lean_level] ?? angle.lean_level.toUpperCase();
  const sideLabel = angle.lean_side
    ? `→ ${angle.lean_side.toUpperCase()} ${(angle.lean_market ?? '').toUpperCase()}`
    : '';

  return (
    <div style={{
      background: SIDEBAR, border: `1px solid ${color}33`,
      borderRadius: 4, padding: '12px 14px', cursor: 'pointer',
    }} onClick={() => setOpen(o => !o)}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ color: MUTED_FG, fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>
            {angle.label}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ background: color + '22', color, fontSize: 10, fontWeight: 800, padding: '2px 8px', borderRadius: 3, letterSpacing: '0.06em' }}>
              {label}
            </span>
            {sideLabel && <span style={{ color: MUTED_FG, fontSize: 11 }}>{sideLabel}</span>}
          </div>
        </div>
        <div style={{ color: MUTED_FG, fontSize: 14 }}>{open ? '▲' : '▼'}</div>
      </div>
      {open && (
        <div style={{ marginTop: 10, borderTop: `1px solid ${BORDER}`, paddingTop: 10 }}>
          <p style={{ color: MUTED_FG, fontSize: 12, lineHeight: 1.6, margin: '0 0 8px' }}>
            {angle.reasoning || (angle.fired ? 'No reasoning provided.' : 'Trigger conditions not met for this game.')}
          </p>
          {angle.signals_cited.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
              {angle.signals_cited.map((s, i) => (
                <span key={i} style={{ background: MUTED, color: MUTED_FG, fontSize: 10, padding: '2px 6px', borderRadius: 3 }}>
                  {s}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ConvergenceBar({ convergence }: { convergence: AnalysisData['convergence'] }) {
  const total = 4;
  const pct = convergence.convergence_count / total;
  const color = LEAN_COLOR[convergence.consensus_lean] ?? MUTED_FG;
  const label = LEAN_LABEL[convergence.consensus_lean] ?? 'NO EDGE';
  const side = convergence.consensus_side ? convergence.consensus_side.toUpperCase() : '';
  const mkt  = convergence.consensus_market ? convergence.consensus_market.toUpperCase() : '';

  return (
    <div style={{ background: CARD, border: `1px solid ${color}44`, borderRadius: 4, padding: '16px 18px' }}>
      <div className="section-title" style={{ marginBottom: 10 }}>Convergence Verdict</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
        <span style={{ background: color + '22', color, fontSize: 12, fontWeight: 800, padding: '3px 12px', borderRadius: 3, letterSpacing: '0.05em' }}>
          {label}
        </span>
        {side && <span style={{ color: FG, fontSize: 12, fontWeight: 700 }}>{side} {mkt}</span>}
        {convergence.dissent_flag && (
          <span style={{ background: YELLOW + '22', color: YELLOW, fontSize: 10, padding: '2px 7px', borderRadius: 3, fontWeight: 700 }}>SPLIT</span>
        )}
      </div>
      <div style={{ background: MUTED, borderRadius: 2, height: 5, marginBottom: 8 }}>
        <div style={{ background: color, height: 5, borderRadius: 2, width: `${Math.round(pct * 100)}%`, transition: 'width 0.6s ease' }} />
      </div>
      <div style={{ color: MUTED_FG, fontSize: 11, lineHeight: 1.5 }}>
        {convergence.convergence_note}
      </div>
    </div>
  );
}

function InjuryList({ injuries }: { injuries: Injury[] }) {
  if (!injuries.length) return (
    <div style={{ color: MUTED_FG, fontSize: 11, padding: '6px 0', opacity: 0.6 }}>No reported injuries</div>
  );
  return (
    <div>
      {injuries.slice(0, 8).map((inj, i) => (
        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: `1px solid ${BORDER}` }}>
          <div>
            <span style={{ color: FG, fontSize: 12, fontWeight: 700 }}>{inj.name}</span>
            <span style={{ color: MUTED_FG, fontSize: 10, marginLeft: 6 }}>{inj.position}</span>
          </div>
          <span style={{ color: STATUS_COLOR[inj.status] ?? MUTED_FG, fontSize: 10, fontWeight: 800, letterSpacing: '0.05em' }}>
            {inj.status}
          </span>
        </div>
      ))}
    </div>
  );
}

function Last5Games({ games, abbr }: { games: GameResult[]; abbr: string }) {
  if (!games.length) return <div style={{ color: MUTED_FG, fontSize: 11, opacity: 0.6 }}>No game history</div>;
  return (
    <div>
      <div className="section-title" style={{ marginBottom: 6 }}>{abbr} — Last {games.length}</div>
      <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
        {games.map((g, i) => {
          const win  = g.result === 'W';
          const loss = g.result === 'L';
          const bg   = win ? EMERALD + '22' : loss ? RED_ACC + '22' : MUTED;
          const fg   = win ? EMERALD : loss ? RED_ACC : MUTED_FG;
          return (
            <div key={i} style={{ background: bg, border: `1px solid ${fg}44`, borderRadius: 3, padding: '4px 8px', minWidth: 52, textAlign: 'center' }}>
              <div style={{ color: fg, fontSize: 11, fontWeight: 800 }}>{g.result}</div>
              <div style={{ color: MUTED_FG, fontSize: 10 }}>{g.at_vs} {g.opponent}</div>
              {g.week && <div style={{ color: MUTED_FG, fontSize: 9, opacity: 0.7 }}>Wk {g.week}</div>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StatBar({ label, homeVal, awayVal, higher = 'home' }:
  { label: string; homeVal?: number; awayVal?: number; higher?: 'home' | 'away' | 'neither' }) {
  if (homeVal == null && awayVal == null) return null;
  const h = homeVal ?? 0;
  const a = awayVal ?? 0;
  const total = h + a || 1;
  const homePct = (h / total) * 100;
  const homeWins = higher === 'home' ? h > a : higher === 'away' ? h < a : false;
  const awayWins = higher === 'home' ? a > h : higher === 'away' ? a < h : false;
  const homeColor = homeWins ? EMERALD : awayWins ? RED_ACC : BLUE;
  const awayColor = awayWins ? EMERALD : homeWins ? RED_ACC : BLUE;

  return (
    <div style={{ marginBottom: 11 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3, alignItems: 'center' }}>
        <span style={{ color: awayColor, fontSize: 13, fontWeight: 800 }}>{awayVal != null ? awayVal : '—'}</span>
        <span style={{ color: MUTED_FG, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em', fontWeight: 700 }}>{label}</span>
        <span style={{ color: homeColor, fontSize: 13, fontWeight: 800 }}>{homeVal != null ? homeVal : '—'}</span>
      </div>
      <div style={{ background: MUTED, borderRadius: 2, height: 3, overflow: 'hidden', display: 'flex' }}>
        <div style={{ width: `${100 - homePct}%`, background: awayColor + '88' }} />
        <div style={{ width: `${homePct}%`, background: homeColor + '88' }} />
      </div>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────

export function MatchupDetail() {
  const { eventId } = useParams<{ eventId: string }>();
  const navigate    = useNavigate();

  const [matchup, setMatchup]   = useState<MatchupData | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [loadingM, setLoadingM] = useState(true);
  const [loadingA, setLoadingA] = useState(false);
  const [errorM, setErrorM]     = useState<string | null>(null);
  const [scriptOpen, setScriptOpen] = useState(false);

  useEffect(() => {
    if (!eventId) return;
    setLoadingM(true);
    fetch(`${API_BASE}/matchup/${eventId}`)
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(d => { setMatchup(d); setErrorM(null); })
      .catch(() => setErrorM('Could not load matchup data.'))
      .finally(() => setLoadingM(false));
  }, [eventId]);

  function loadAnalysis() {
    if (!eventId || loadingA || analysis) return;
    setLoadingA(true);
    fetch(`${API_BASE}/matchup/${eventId}/analysis`)
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(d => setAnalysis(d))
      .catch(() => {})
      .finally(() => setLoadingA(false));
  }

  if (loadingM) return (
    <div className="analytics-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', color: MUTED_FG, fontSize: 14 }}>
      Loading matchup…
    </div>
  );

  if (errorM || !matchup) return (
    <div className="analytics-page" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: 12 }}>
      <div style={{ color: RED_ACC, fontSize: 14 }}>{errorM ?? 'Matchup not found.'}</div>
      <button onClick={() => navigate(-1)} style={{ color: BLUE, background: 'none', border: 'none', cursor: 'pointer', fontSize: 13 }}>← Back</button>
    </div>
  );

  const { home, away, odds, espn_wp, model_wp, edge, venue, injuries } = matchup;
  const hStats = matchup.home_stats ?? {};
  const aStats = matchup.away_stats ?? {};
  const hRec   = matchup.home_record ?? {};
  const aRec   = matchup.away_record ?? {};

  const gameDate = matchup.date
    ? new Date(matchup.date).toLocaleDateString('en-US', {
        weekday: 'short', month: 'short', day: 'numeric',
        hour: 'numeric', minute: '2-digit', timeZoneName: 'short',
      })
    : '—';

  const spreadLabel = odds.spread != null
    ? `${home.abbr} ${odds.spread > 0 ? '+' : ''}${odds.spread} / ${away.abbr} ${odds.spread > 0 ? '-' : '+'}${Math.abs(odds.spread)}`
    : odds.details || '—';
  const mlLabel = (ml: number | null) => ml == null ? '—' : ml > 0 ? `+${ml}` : `${ml}`;
  const edgeColor = (e: number | null) => !e ? MUTED_FG : e > 0 ? EMERALD : RED_ACC;

  const hPassYds = hStats.total_yds_pg && hStats.rush_yds_pg
    ? Math.round((hStats.total_yds_pg - hStats.rush_yds_pg) * 10) / 10 : undefined;
  const aPassYds = aStats.total_yds_pg && aStats.rush_yds_pg
    ? Math.round((aStats.total_yds_pg - aStats.rush_yds_pg) * 10) / 10 : undefined;

  const statsSeason = hStats.season ?? aStats.season;
  const hasStats = Object.keys(hStats).length > 1 || Object.keys(aStats).length > 1;
  const hasLast5 = (matchup.home_last5?.length ?? 0) > 0 || (matchup.away_last5?.length ?? 0) > 0;

  return (
    <div className="analytics-page">

      {/* ── Header bar ─────────────────────────────────────────────────── */}
      <div className="analytics-header">
        <button onClick={() => navigate(-1)} style={{ color: MUTED_FG, background: 'none', border: 'none', cursor: 'pointer', fontSize: 12, marginBottom: 10, display: 'flex', alignItems: 'center', gap: 4, fontFamily: 'inherit', fontWeight: 600 }}>
          ← Back
        </button>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16, paddingBottom: 20 }}>

          {/* Away */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 160 }}>
            <img src={away.logo} alt={away.abbr} style={{ width: 52, height: 52, objectFit: 'contain' }} onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
            <div>
              <div style={{ color: MUTED_FG, fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Away</div>
              <div style={{ color: FG, fontSize: 20, fontWeight: 800, letterSpacing: '-0.02em' }}>{away.name}</div>
              <div style={{ color: MUTED_FG, fontSize: 13, fontWeight: 700 }}>{aRec.overall ?? '—'}</div>
              {away.rating != null && (
                <div style={{ color: MUTED_FG, fontSize: 10, fontWeight: 600 }}>
                  Rtg {away.rating.toFixed(1)}{away.rank ? ` · #${away.rank}` : ''}{away.tier ? ` · ${away.tier}` : ''}
                </div>
              )}
            </div>
          </div>

          {/* Game info */}
          <div style={{ textAlign: 'center', flex: '0 0 auto' }}>
            {matchup.week && <div style={{ color: MUTED_FG, fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', marginBottom: 4 }}>NFL WEEK {matchup.week}</div>}
            <div style={{ color: BLUE, fontSize: 20, fontWeight: 800, letterSpacing: '0.06em' }}>@</div>
            <div style={{ color: MUTED_FG, fontSize: 11, fontWeight: 600, marginTop: 4 }}>{gameDate}</div>
            {matchup.tv && <div style={{ color: MUTED_FG, fontSize: 10, marginTop: 2 }}>📺 {matchup.tv}</div>}
            <div style={{ color: MUTED_FG, fontSize: 10, marginTop: 3, opacity: 0.7 }}>
              {venue.name ? `${venue.name} · ${venue.city}, ${venue.state}` : ''}
              {venue.indoor ? ' · Dome' : venue.grass ? ' · Grass' : ' · Turf'}
            </div>
            {matchup.neutral_site && <div style={{ color: YELLOW, fontSize: 10, marginTop: 2, fontWeight: 700 }}>Neutral Site</div>}
          </div>

          {/* Home */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 160, justifyContent: 'flex-end' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ color: MUTED_FG, fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Home</div>
              <div style={{ color: FG, fontSize: 20, fontWeight: 800, letterSpacing: '-0.02em' }}>{home.name}</div>
              <div style={{ color: MUTED_FG, fontSize: 13, fontWeight: 700 }}>{hRec.overall ?? '—'}</div>
              {home.rating != null && (
                <div style={{ color: MUTED_FG, fontSize: 10, fontWeight: 600 }}>
                  Rtg {home.rating.toFixed(1)}{home.rank ? ` · #${home.rank}` : ''}{home.tier ? ` · ${home.tier}` : ''}
                </div>
              )}
            </div>
            <img src={home.logo} alt={home.abbr} style={{ width: 52, height: 52, objectFit: 'contain' }} onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
          </div>
        </div>
      </div>

      {/* ── Content area ───────────────────────────────────────────────── */}
      <div className="analytics-content">

        {/* Team Stats Comparison */}
        {hasStats && (
          <div className="data-table-wrap mb">
            <div style={{ padding: '14px 18px 6px', borderBottom: `1px solid ${BORDER}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div className="section-title">
                  Team Stats{statsSeason ? ` — ${statsSeason} Season` : ''}
                </div>
                <div style={{ display: 'flex', gap: 24, marginRight: 4 }}>
                  <div style={{ color: MUTED_FG, fontSize: 10, fontWeight: 700, textAlign: 'center' }}>{away.abbr}<br /><span style={{ opacity: 0.6 }}>Away</span></div>
                  <div style={{ color: MUTED_FG, fontSize: 10, fontWeight: 700, textAlign: 'center' }}>{home.abbr}<br /><span style={{ opacity: 0.6 }}>Home</span></div>
                </div>
              </div>
            </div>
            <div style={{ padding: '16px 18px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 36px' }}>
                <div>
                  <StatBar label="Pts / Game"     homeVal={hStats.pts_per_game}   awayVal={aStats.pts_per_game}   />
                  <StatBar label="Pts Allowed / G" homeVal={hStats.pts_allowed_pg} awayVal={aStats.pts_allowed_pg} higher="neither" />
                  <StatBar label="Total Yds / G"  homeVal={hStats.total_yds_pg}   awayVal={aStats.total_yds_pg}   />
                </div>
                <div>
                  <StatBar label="Rush Yds / G"   homeVal={hStats.rush_yds_pg}    awayVal={aStats.rush_yds_pg}    />
                  <StatBar label="Pass Yds / G"   homeVal={hPassYds}              awayVal={aPassYds}              />
                  <StatBar label="Rush YPA"       homeVal={hStats.rush_ypa}       awayVal={aStats.rush_ypa}       />
                </div>
              </div>
              <div style={{ display: 'flex', gap: 12, marginTop: 8, opacity: 0.7 }}>
                <span style={{ color: EMERALD, fontSize: 10 }}>■ Better</span>
                <span style={{ color: RED_ACC, fontSize: 10 }}>■ Worse</span>
                <span style={{ color: BLUE, fontSize: 10 }}>■ Even</span>
              </div>
            </div>
          </div>
        )}

        {/* Recent Form — Last 5 Games */}
        {hasLast5 && (
          <div className="data-table-wrap mb">
            <div style={{ padding: '14px 18px', borderBottom: `1px solid ${BORDER}` }}>
              <div className="section-title">Recent Form — 2025 Season</div>
            </div>
            <div style={{ padding: '14px 18px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
              <Last5Games games={matchup.away_last5 ?? []} abbr={away.abbr} />
              <Last5Games games={matchup.home_last5 ?? []} abbr={home.abbr} />
            </div>
          </div>
        )}

        {/* 3-column layout */}
        <div style={{ display: 'grid', gridTemplateColumns: '210px 1fr 210px', gap: 14 }}>

          {/* Left — WP + Odds + Edge + Power */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>

            <Panel label="Win Probability">
              <div style={{ display: 'flex', justifyContent: 'space-around', padding: '8px 0' }}>
                <WpDonut home={model_wp.away} away={model_wp.home} label={away.abbr} />
                <WpDonut home={model_wp.home} away={model_wp.away} label={home.abbr} />
              </div>
              <div style={{ fontSize: 10, color: MUTED_FG, textAlign: 'center', marginTop: 4, opacity: 0.7 }}>Model WP (Walters)</div>
              {espn_wp.home != null && (
                <div style={{ fontSize: 10, color: MUTED_FG, textAlign: 'center', marginTop: 2, opacity: 0.6 }}>
                  ESPN: {away.abbr} {Math.round((espn_wp.away ?? 0) * 100)}% / {home.abbr} {Math.round(espn_wp.home * 100)}%
                </div>
              )}
            </Panel>

            <Panel label="Lines">
              <Row label="Spread"    value={spreadLabel} />
              <Row label="Total O/U" value={odds.over_under != null ? `${odds.over_under}` : '—'} />
              <Row label={`${away.abbr} ML`} value={mlLabel(odds.away_ml)} />
              <Row label={`${home.abbr} ML`} value={mlLabel(odds.home_ml)} />
              {odds.away_implied != null && (
                <>
                  <div style={{ borderTop: `1px solid ${BORDER}`, margin: '8px 0' }} />
                  <Row label={`${away.abbr} implied`} value={`${Math.round(odds.away_implied * 100)}%`} />
                  <Row label={`${home.abbr} implied`} value={`${Math.round(odds.home_implied! * 100)}%`} />
                </>
              )}
            </Panel>

            {(edge.home !== null || edge.away !== null) && (
              <Panel label="Model Edge">
                <Row label={away.abbr} value={edge.away != null ? `${edge.away > 0 ? '+' : ''}${edge.away}%` : '—'} valueColor={edgeColor(edge.away)} />
                <Row label={home.abbr} value={edge.home != null ? `${edge.home > 0 ? '+' : ''}${edge.home}%` : '—'} valueColor={edgeColor(edge.home)} />
                <div style={{ color: MUTED_FG, fontSize: 10, marginTop: 8, lineHeight: 1.4, opacity: 0.7 }}>
                  Model WP − vig-free implied. Positive = undervalued by market.
                </div>
              </Panel>
            )}

            {(home.rating != null || away.rating != null) && (
              <Panel label="Power Ratings">
                {[{ team: away, label: 'Away' }, { team: home, label: 'Home' }].map(({ team, label }) => (
                  <div key={team.abbr} style={{ marginBottom: 10 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: MUTED_FG, fontSize: 12, fontWeight: 700 }}>
                        {team.abbr} <span style={{ color: MUTED_FG, fontSize: 10, opacity: 0.6 }}>({label})</span>
                      </span>
                      <span style={{ color: FG, fontSize: 13, fontWeight: 800 }}>{team.rating?.toFixed(1) ?? '—'}</span>
                    </div>
                    {team.tier && (
                      <div style={{ color: BLUE, fontSize: 10, fontWeight: 700, textAlign: 'right', marginTop: 1 }}>
                        {team.tier.toUpperCase()}{team.rank ? ` · #${team.rank}` : ''}
                      </div>
                    )}
                  </div>
                ))}
                <div style={{ color: MUTED_FG, fontSize: 10, opacity: 0.6 }}>Max EV Walters power index</div>
              </Panel>
            )}
          </div>

          {/* Center — Angles + Convergence + Verdict */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <Panel label="Handicapper Angles">
              {!analysis && !loadingA ? (
                <div style={{ textAlign: 'center', padding: '20px 0' }}>
                  <div style={{ color: MUTED_FG, fontSize: 12, marginBottom: 14, lineHeight: 1.6 }}>
                    Run 4-angle AI analysis — Matchup, Sharp Money, Situational, Totals — evaluated independently then converged.
                  </div>
                  <button
                    onClick={loadAnalysis}
                    style={{ padding: '9px 24px', background: `linear-gradient(135deg, ${BLUE}, oklch(52% .22 290))`, color: '#fff', fontWeight: 800, fontSize: 12, borderRadius: 4, border: 'none', cursor: 'pointer', letterSpacing: '0.05em', fontFamily: 'inherit' }}
                  >
                    RUN ANALYSIS
                  </button>
                </div>
              ) : loadingA ? (
                <div style={{ textAlign: 'center', padding: '28px 0', color: MUTED_FG, fontSize: 12 }}>
                  <div style={{ marginBottom: 6 }}>Running angle evaluations…</div>
                  <div style={{ fontSize: 10, opacity: 0.6 }}>Matchup · Sharp · Situational · Totals — ~15s</div>
                </div>
              ) : analysis ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {analysis.angles.map(angle => <AngleCard key={angle.name} angle={angle} />)}
                </div>
              ) : null}
            </Panel>

            {analysis && <ConvergenceBar convergence={analysis.convergence} />}

            {analysis?.verdict && (
              <Panel label="Verdict">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <span style={{ background: (LEAN_COLOR[analysis.verdict.lean_level] ?? MUTED_FG) + '22', color: LEAN_COLOR[analysis.verdict.lean_level] ?? MUTED_FG, fontSize: 10, fontWeight: 800, padding: '2px 10px', borderRadius: 3, letterSpacing: '0.06em' }}>
                    {LEAN_LABEL[analysis.verdict.lean_level] ?? analysis.verdict.lean_level}
                  </span>
                  {analysis.verdict.lean_side && (
                    <span style={{ color: FG, fontSize: 13, fontWeight: 700 }}>{analysis.verdict.lean_side}</span>
                  )}
                  {analysis.verdict.unit_rec > 0 && (
                    <span style={{ color: EMERALD, fontSize: 11, fontWeight: 800 }}>{analysis.verdict.unit_rec}u</span>
                  )}
                </div>
                {analysis.verdict.confidence_note && (
                  <div style={{ color: MUTED_FG, fontSize: 11, marginTop: 8, fontStyle: 'italic' }}>
                    {analysis.verdict.confidence_note}
                  </div>
                )}
              </Panel>
            )}
          </div>

          {/* Right — Injuries + Records */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <Panel label={`${away.name} Injuries`}>
              <InjuryList injuries={injuries.away} />
            </Panel>
            <Panel label={`${home.name} Injuries`}>
              <InjuryList injuries={injuries.home} />
            </Panel>

            {(Object.keys(hRec).length > 0 || Object.keys(aRec).length > 0) && (
              <Panel label="Records">
                <div style={{ marginBottom: 10 }}>
                  <div style={{ color: BLUE, fontSize: 10, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>{away.abbr} (Away)</div>
                  <Row label="Overall" value={aRec.overall ?? '—'} />
                  <Row label="Home"    value={aRec.home    ?? '—'} />
                  <Row label="Road"    value={aRec.road    ?? '—'} />
                </div>
                <div>
                  <div style={{ color: BLUE, fontSize: 10, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>{home.abbr} (Home)</div>
                  <Row label="Overall" value={hRec.overall ?? '—'} />
                  <Row label="Home"    value={hRec.home    ?? '—'} />
                  <Row label="Road"    value={hRec.road    ?? '—'} />
                </div>
              </Panel>
            )}
          </div>
        </div>

        {/* Game Script — full width */}
        {analysis?.verdict?.game_script && (
          <div className="data-table-wrap" style={{ marginTop: 14, overflow: 'hidden' }}>
            <button
              onClick={() => setScriptOpen(o => !o)}
              style={{ width: '100%', padding: '16px 18px', background: 'none', border: 'none', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontFamily: 'inherit' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span className="section-title" style={{ marginBottom: 0 }}>Game Script</span>
                <span style={{ background: BLUE + '22', color: BLUE, fontSize: 10, padding: '2px 7px', borderRadius: 3, fontWeight: 800 }}>AI</span>
                <span style={{ color: MUTED_FG, fontSize: 11 }}>{analysis.source === 'db' ? 'Cached' : 'Live'}</span>
              </div>
              <span style={{ color: MUTED_FG, fontSize: 14 }}>{scriptOpen ? '▲' : '▼'}</span>
            </button>
            {scriptOpen && (
              <div style={{ padding: '0 18px 20px', borderTop: `1px solid ${BORDER}` }}>
                <div style={{ paddingTop: 16, color: MUTED_FG, fontSize: 13, lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
                  {analysis.verdict.game_script}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Utility ────────────────────────────────────────────────────────────────

function Panel({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="data-table-wrap" style={{ padding: '14px 16px' }}>
      <div className="section-title" style={{ marginBottom: 12 }}>{label}</div>
      {children}
    </div>
  );
}

function Row({ label, value, valueColor }: { label: string; value: string; valueColor?: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: `1px solid ${BORDER}` }}>
      <span style={{ color: MUTED_FG, fontSize: 12 }}>{label}</span>
      <span style={{ color: valueColor ?? FG, fontSize: 12, fontWeight: 700 }}>{value}</span>
    </div>
  );
}
