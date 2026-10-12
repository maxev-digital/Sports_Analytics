import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LiveGame } from '../../types';
import { detectSport, getSportBorderClass, getSportStyle } from '../../utils/sportDetection';
import { formatTeamName } from '../../utils/teamNames';
import { getTeamLogoUrl } from '../../utils/teamLogos';
import { getNflAbbr, getNflRating, NFL_POWER_RATINGS } from '../../utils/nflData';
import { getCfbRating } from '../../utils/cfbData';
import type { GameResult } from '../../pages/LiveGames';

const F5_BASE = import.meta.env.DEV ? 'http://localhost:8889/api/f5' : '/api/f5';

interface TeamData {
  abbr: string;
  full_name: string;
  logo: string;
  rating: number | null;
  tier: string | null;
  rank: number | null;
}

interface Injury {
  name: string;
  position: string;
  status: string;
}

interface MatchupData {
  event_id: string;
  short_name: string;
  week: number | null;
  tv: string;
  venue: { name: string; city: string; state: string; indoor: boolean };
  home: TeamData;
  away: TeamData;
  odds: {
    spread: number | null;
    over_under: number | null;
    away_ml: number | null;
    home_ml: number | null;
    away_implied: number | null;
    home_implied: number | null;
  };
  model_wp: { home: number | null; away: number | null };
  edge: { home: number | null; away: number | null };
  injuries: { home: Injury[]; away: Injury[] };
}

const TIER_COLORS: Record<string, string> = {
  ELITE:      'text-yellow-400',
  CONTENDER:  'text-blue-400',
  AVERAGE:    'text-slate-400',
  REBUILDING: 'text-red-400',
};

const INJURY_DOT: Record<string, string> = {
  Out:             'bg-red-500',
  'Injured Reserve': 'bg-red-600',
  Questionable:    'bg-yellow-500',
  Doubtful:        'bg-orange-500',
};

/** Compute median consensus line from all bookmaker odds */
function consensus(values: (number | null | undefined)[]): number | null {
  const valid = values.filter((v): v is number => v != null);
  if (!valid.length) return null;
  const sorted = [...valid].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

function fmtOdds(n: number | null): string {
  if (n == null) return '—';
  return n > 0 ? `+${n}` : String(n);
}

function fmtSpread(n: number | null): string {
  if (n == null) return '—';
  return n > 0 ? `+${n}` : String(n);
}

interface KalshiData {
  home: { mid: number | null; yes_ask: number | null; subtitle: string | null };
  away: { mid: number | null; yes_ask: number | null; subtitle: string | null };
}

interface AtsRecord {
  situation: string;
  games: number;
  ats_wins: number;
  ats_losses: number;
  ats_pct: number;
  ou_over: number;
  ou_under: number;
  over_pct: number;
}

interface Props {
  game: LiveGame;
  gameResult?: GameResult;
}

export function GameCardMatchup({ game, gameResult }: Props) {
  const navigate = useNavigate();
  const { state, odds: rawOdds } = game;
  const sport = detectSport(game);
  const borderClass = getSportBorderClass(sport);
  const sportStyle = getSportStyle(sport);

  const [matchup, setMatchup]       = useState<MatchupData | null>(null);
  const [f5Id, setF5Id]             = useState<string | null>(null);
  const [kalshi, setKalshi]         = useState<KalshiData | null>(null);
  const [homeLogoErr, setHomeLogoErr] = useState(false);
  const [awayLogoErr, setAwayLogoErr] = useState(false);
  const [scriptOpen, setScriptOpen]   = useState(false);
  const [homeAts, setHomeAts]       = useState<AtsRecord | null>(null);
  const [awayAts, setAwayAts]       = useState<AtsRecord | null>(null);
  const [homeInjuries, setHomeInjuries] = useState<Injury[]>([]);
  const [awayInjuries, setAwayInjuries] = useState<Injury[]>([]);

  // Only NFL has F5 matchup data right now
  const supportsF5 = sport === 'NFL' || sport === 'NCAAF';

  useEffect(() => {
    if (!supportsF5) return;
    const home = formatTeamName(state.home_team.name, state.sport_key);
    const away = formatTeamName(state.away_team.name, state.sport_key);
    const sportParam = sport === 'NCAAF' ? '&sport=ncaaf' : '';
    fetch(`${F5_BASE}/matchup-lookup?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}${sportParam}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.event_id) setF5Id(d.event_id); })
      .catch(() => {});
  }, [state.home_team.name, state.away_team.name, supportsF5]);

  useEffect(() => {
    if (!f5Id) return;
    const mSport = sport === 'NCAAF' ? '?sport=ncaaf' : '';
    fetch(`${F5_BASE}/matchup/${f5Id}${mSport}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d && !d.detail) setMatchup(d); })
      .catch(() => {});
  }, [f5Id]);

  // Injuries — NFL only, fetched directly from heatmap cache by team abbr
  useEffect(() => {
    if (sport !== 'NFL') return;
    const ha = getNflAbbr(state.home_team.name);
    const aa = getNflAbbr(state.away_team.name);
    if (ha) fetch(`${F5_BASE}/team-injuries?team=${ha}`).then(r => r.ok ? r.json() : null).then(d => { if (d) setHomeInjuries(d.players ?? []); }).catch(() => {});
    if (aa) fetch(`${F5_BASE}/team-injuries?team=${aa}`).then(r => r.ok ? r.json() : null).then(d => { if (d) setAwayInjuries(d.players ?? []); }).catch(() => {});
  }, [sport, state.home_team.name, state.away_team.name]);

  // ATS/OU records — NFL only, uses static abbr map (no matchup dependency)
  useEffect(() => {
    if (sport !== 'NFL') return;
    const homeAbbr = getNflAbbr(state.home_team.name) ?? matchup?.home.abbr;
    const awayAbbr = getNflAbbr(state.away_team.name) ?? matchup?.away.abbr;
    if (!homeAbbr || !awayAbbr) return;
    Promise.all([
      fetch(`${F5_BASE}/nfl/ats?team=${homeAbbr}&season=2025`).then(r => r.ok ? r.json() : null).catch(() => null),
      fetch(`${F5_BASE}/nfl/ats?team=${awayAbbr}&season=2025`).then(r => r.ok ? r.json() : null).catch(() => null),
    ]).then(([hData, aData]) => {
      setHomeAts(hData?.situations?.find((s: AtsRecord) => s.situation === 'overall') ?? null);
      setAwayAts(aData?.situations?.find((s: AtsRecord) => s.situation === 'overall') ?? null);
    });
  }, [sport, state.home_team.name, state.away_team.name]);

  // Kalshi market prices — public API, no auth needed
  useEffect(() => {
    const home = formatTeamName(state.home_team.name, state.sport_key);
    const away = formatTeamName(state.away_team.name, state.sport_key);
    fetch(`${F5_BASE}/kalshi-game?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}&sport_key=${encodeURIComponent(state.sport_key)}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.found) setKalshi({ home: d.home, away: d.away }); })
      .catch(() => {});
  }, [state.home_team.name, state.away_team.name, state.sport_key]);

  // Consensus odds — use F5 data if available, otherwise median across books
  const consensusSpread = matchup?.odds.spread
    ?? consensus(rawOdds.map(o => o.home_spread));
  const consensusOU = matchup?.odds.over_under
    ?? consensus(rawOdds.map(o => o.total));
  const consensusHomeMl = matchup?.odds.home_ml
    ?? consensus(rawOdds.map(o => o.home_ml));
  const consensusAwayMl = matchup?.odds.away_ml
    ?? consensus(rawOdds.map(o => o.away_ml));

  const gameTime = new Date(state.commence_time).toLocaleTimeString('en-US', {
    hour: 'numeric', minute: '2-digit', timeZone: 'America/Chicago',
  });
  const gameDate = new Date(state.commence_time).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', timeZone: 'America/Chicago',
  });

  const homeWp   = matchup?.model_wp.home ?? null;
  const awayWp   = matchup?.model_wp.away ?? null;
  const homeEdge = matchup?.edge.home ?? null;

  // Book-implied win probability from consensus ML (immediate, no F5 needed)
  function mlToImplied(ml: number): number {
    return ml < 0 ? (-ml) / (-ml + 100) : 100 / (ml + 100);
  }
  const bookHomeWp = consensusHomeMl != null ? mlToImplied(consensusHomeMl) : null;
  const bookAwayWp = consensusAwayMl != null ? mlToImplied(consensusAwayMl) : null;
  const displayHomeWp = homeWp ?? bookHomeWp;
  const displayAwayWp = awayWp ?? bookAwayWp;

  // Top injuries — use direct fetch (homeInjuries/awayInjuries), fall back to matchup if loaded
  const SEVERITY = ['Out', 'Injured Reserve', 'Doubtful', 'Questionable'];
  const topInjury = (list: Injury[]) =>
    [...list].sort((a, b) => SEVERITY.indexOf(a.status) - SEVERITY.indexOf(b.status))[0] ?? null;

  const effectiveHomeInj = homeInjuries.length ? homeInjuries : (matchup?.injuries.home ?? []);
  const effectiveAwayInj = awayInjuries.length ? awayInjuries : (matchup?.injuries.away ?? []);
  const homeInjury = topInjury(effectiveHomeInj);
  const awayInjury = topInjury(effectiveAwayInj);

  const homeName = matchup?.home.full_name ?? formatTeamName(state.home_team.name, state.sport_key);
  const awayName = matchup?.away.full_name ?? formatTeamName(state.away_team.name, state.sport_key);
  const homeLogo = matchup?.home.logo ?? getTeamLogoUrl(state.home_team.name, state.sport_key);
  const awayLogo = matchup?.away.logo ?? getTeamLogoUrl(state.away_team.name, state.sport_key);

  const SPORT_LABELS: Record<string, string> = {
    NFL: '🏈 NFL', NCAAF: '🏈 CFB', MLB: '⚾ MLB',
    NBA: '🏀 NBA', NHL: '🏒 NHL', NCAAB: '🏀 NCAAB',
  };

  // Initials fallback for missing logos
  const initials = (name: string) => name.split(' ').slice(-2).map(w => w[0]).join('').toUpperCase().slice(0, 3);

  // Derived abbrs — use static map first (no F5 required)
  const homeAbbr = matchup?.home.abbr ?? getNflAbbr(state.home_team.name) ?? initials(homeName);
  const awayAbbr = matchup?.away.abbr ?? getNflAbbr(state.away_team.name) ?? initials(awayName);

  const edgeSide = homeEdge != null
    ? homeEdge > 0
      ? { label: homeAbbr, val: homeEdge }
      : { label: awayAbbr, val: Math.abs(homeEdge) }
    : null;

  // Best book from rawOdds
  const bestOver  = rawOdds.find(o => o.is_best_over);
  const bestUnder = rawOdds.find(o => o.is_best_under);

  // Power ratings — use F5 matchup data if loaded, else static 2025 preseason ratings
  // Power ratings — NFL uses nflData, CFB uses cfbData, both fall back to matchup API
  const homeStaticNfl = getNflRating(state.home_team.name);
  const awayStaticNfl = getNflRating(state.away_team.name);
  const homeStaticCfb = sport === 'NCAAF' ? getCfbRating(formatTeamName(state.home_team.name, state.sport_key)) : null;
  const awayStaticCfb = sport === 'NCAAF' ? getCfbRating(formatTeamName(state.away_team.name, state.sport_key)) : null;
  const homeStaticRating = homeStaticNfl ?? homeStaticCfb;
  const awayStaticRating = awayStaticNfl ?? awayStaticCfb;
  const homeRating = matchup?.home.rating ?? homeStaticRating?.rating ?? null;
  const awayRating = matchup?.away.rating ?? awayStaticRating?.rating ?? null;
  const homeTier   = matchup?.home.tier   ?? homeStaticRating?.tier   ?? null;
  const awayTier   = matchup?.away.tier   ?? awayStaticRating?.tier   ?? null;
  const homeRank   = matchup?.home.rank   ?? homeStaticRating?.rank   ?? null;
  const awayRank   = matchup?.away.rank   ?? awayStaticRating?.rank   ?? null;
  const ratingGap  = homeRating != null && awayRating != null ? homeRating - awayRating : null;

  // Injury severity score: Out/IR=3, Doubtful=2, Questionable=1
  const injuryScore = (injuries: Injury[]) =>
    injuries.reduce((s, i) => s + (['Out', 'Injured Reserve'].includes(i.status) ? 3 : i.status === 'Doubtful' ? 2 : i.status === 'Questionable' ? 1 : 0), 0);
  const homeInjScore = injuryScore(effectiveHomeInj);
  const awayInjScore = injuryScore(effectiveAwayInj);

  // ATS record formatter
  const fmtAts = (r: AtsRecord | null) => r ? `${r.ats_wins}-${r.ats_losses} (${(r.ats_pct * 100).toFixed(0)}%)` : '—';
  const fmtOu  = (r: AtsRecord | null) => r ? `${r.ou_over}-${r.ou_under} (${(r.over_pct * 100).toFixed(0)}%)` : '—';

  return (
    <div
      className={`rounded-xl border ${borderClass} overflow-hidden flex flex-col`}
      style={{ background: 'linear-gradient(160deg, #0f172a 0%, #1e293b 100%)', boxShadow: `0 2px 16px ${sportStyle.glowColor}` }}
    >
      {/* ── Sport accent stripe ── */}
      <div className="h-1 w-full" style={{ background: sportStyle.glowColor.replace('0.3', '0.8') }} />

      {/* ── Header ── */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-700/60">
        <div className="flex items-center gap-2">
          <span
            className="text-[10px] font-extrabold tracking-widest px-2 py-0.5 rounded-full text-white"
            style={{ background: sportStyle.glowColor }}
          >
            {SPORT_LABELS[sport] ?? sport}
          </span>
          {matchup?.tv && (
            <span className="text-[10px] font-bold text-slate-400 bg-slate-800 border border-slate-600 px-1.5 py-0.5 rounded">
              📺 {matchup.tv}
            </span>
          )}
        </div>
        <div className="text-right">
          <div className="text-xs font-bold text-slate-200">{gameTime} CT</div>
          <div className="text-[10px] text-slate-500">{gameDate}</div>
        </div>
      </div>

      <div className="p-4 space-y-4 flex-1">

        {/* ── Teams ── */}
        <div className="flex items-center justify-between gap-3">
          {/* Away */}
          {/* Away */}
          <div className="flex flex-col items-center gap-1.5 flex-1 min-w-0">
            <div className="w-14 h-14 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center p-1.5 flex-shrink-0">
              {awayLogo && !awayLogoErr
                ? <img src={awayLogo} alt={awayName} className="w-full h-full object-contain" onError={() => setAwayLogoErr(true)} />
                : <span className="text-[11px] font-black text-slate-400">{initials(awayName)}</span>
              }
            </div>
            <div className="text-center min-w-0 w-full">
              <div className="text-sm font-extrabold text-white truncate leading-tight">{awayName}</div>
              {awayTier && (
                <div className={`text-[10px] font-semibold ${TIER_COLORS[awayTier] ?? 'text-slate-500'}`}>
                  {awayRank ? `#${awayRank} ` : ''}{awayTier}
                </div>
              )}
              {displayAwayWp != null && <div className="text-[11px] font-bold text-blue-400 mt-0.5">{(displayAwayWp * 100).toFixed(0)}%</div>}
            </div>
          </div>

          {/* VS separator / Score */}
          <div className="flex flex-col items-center gap-0.5 flex-shrink-0">
            {state.home_team.score != null && state.away_team.score != null ? (
              <>
                <div className="flex items-center gap-2">
                  <span className={`text-2xl font-black ${state.away_team.score > state.home_team.score ? 'text-white' : 'text-slate-500'}`}>{state.away_team.score}</span>
                  <span className="text-xs text-slate-600">-</span>
                  <span className={`text-2xl font-black ${state.home_team.score > state.away_team.score ? 'text-white' : 'text-slate-500'}`}>{state.home_team.score}</span>
                </div>
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                  state.status === 'final' ? 'bg-slate-700 text-slate-400' :
                  state.status === 'in_progress' ? 'bg-red-500/20 text-red-400 animate-pulse' :
                  'text-slate-600'
                }`}>
                  {state.status === 'final' ? 'FINAL' : state.status === 'in_progress' ? 'LIVE' : '@'}
                </span>
              </>
            ) : (
              <>
                <div className="text-xs font-black text-slate-500 tracking-widest">@</div>
                {matchup?.venue?.city && (
                  <div className="text-[9px] text-slate-600 text-center leading-tight">
                    {matchup.venue.indoor ? '🏟' : '🌤'} {matchup.venue.city}
                  </div>
                )}
              </>
            )}
            {matchup?.week && <div className="text-[9px] text-slate-600">Wk {matchup.week}</div>}
          </div>

          {/* Home */}
          <div className="flex flex-col items-center gap-1.5 flex-1 min-w-0">
            <div className="w-14 h-14 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center p-1.5 flex-shrink-0">
              {homeLogo && !homeLogoErr
                ? <img src={homeLogo} alt={homeName} className="w-full h-full object-contain" onError={() => setHomeLogoErr(true)} />
                : <span className="text-[11px] font-black text-slate-400">{initials(homeName)}</span>
              }
            </div>
            <div className="text-center min-w-0 w-full">
              <div className="text-sm font-extrabold text-white truncate leading-tight">{homeName}</div>
              {homeTier && (
                <div className={`text-[10px] font-semibold ${TIER_COLORS[homeTier] ?? 'text-slate-500'}`}>
                  {homeRank ? `#${homeRank} ` : ''}{homeTier}
                </div>
              )}
              {displayHomeWp != null && <div className="text-[11px] font-bold text-emerald-400 mt-0.5">{(displayHomeWp * 100).toFixed(0)}%</div>}
            </div>
          </div>
        </div>

        {/* ── Win probability bar — shows from book ML immediately ── */}
        {displayHomeWp != null && displayAwayWp != null && (
          <div className="space-y-1">
            <div className="flex justify-between text-[10px] text-slate-500 px-0.5">
              <span>{awayName.split(' ').pop()} {(displayAwayWp * 100).toFixed(0)}%</span>
              <span className="text-slate-600">{homeWp != null ? 'MODEL WP' : 'BOOK IMPLIED'}</span>
              <span>{(displayHomeWp * 100).toFixed(0)}% {homeName.split(' ').pop()}</span>
            </div>
            <div className="h-2 rounded-full overflow-hidden bg-slate-700/60 flex">
              <div className="h-full bg-blue-500/80 transition-all" style={{ width: `${displayAwayWp * 100}%` }} />
              <div className="h-full bg-emerald-500/80 transition-all" style={{ width: `${displayHomeWp * 100}%` }} />
            </div>
            {edgeSide && (
              <div className="flex justify-center pt-0.5">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${homeEdge! > 0 ? 'bg-emerald-500/15 text-emerald-400' : 'bg-blue-500/15 text-blue-400'}`}>
                  ⚡ {edgeSide.label} +{edgeSide.val.toFixed(1)}pp model edge
                </span>
              </div>
            )}
          </div>
        )}

        {/* ── Power Rating Bar ── */}
        {ratingGap != null && (
          <div className="border-t border-slate-700/50 pt-3 space-y-1">
            <div className="flex justify-between items-center text-[10px] text-slate-500 px-0.5">
              <span className="font-bold">{awayName.split(' ').pop()} {awayRating?.toFixed(1)}</span>
              <span className="tracking-widest">POWER RATINGS</span>
              <span className="font-bold">{homeRating?.toFixed(1)} {homeName.split(' ').pop()}</span>
            </div>
            <div className="h-1.5 rounded-full overflow-hidden bg-slate-700/60 flex">
              {(() => {
                // Normalize by shifting both ratings above zero (worst possible NFL rating ≈ -15)
                const MIN_OFFSET = -15;
                const awayNorm = (awayRating ?? 0) - MIN_OFFSET;
                const homeNorm = (homeRating ?? 0) - MIN_OFFSET;
                const total = awayNorm + homeNorm;
                if (total <= 0) return null;
                const awayPct = (awayNorm / total) * 100;
                const homePct = (homeNorm / total) * 100;
                return <>
                  <div className="h-full bg-blue-500/70" style={{ width: `${awayPct}%` }} />
                  <div className="h-full bg-emerald-500/70" style={{ width: `${homePct}%` }} />
                </>;
              })()}
            </div>
            {Math.abs(ratingGap) >= 2 && (
              <div className="text-center text-[9px] text-slate-500">
                {ratingGap > 0
                  ? `${homeAbbr} +${ratingGap.toFixed(1)} edge`
                  : `${awayAbbr} +${Math.abs(ratingGap).toFixed(1)} edge`}
              </div>
            )}
          </div>
        )}

        {/* ── Consensus Odds ── */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="bg-slate-800/80 rounded-lg p-2 border border-slate-700/50">
            <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">Spread</div>
            <div className="text-sm font-black text-white">
              {consensusSpread != null ? (
                consensusSpread < 0 ? `${homeAbbr} ${consensusSpread}` :
                consensusSpread > 0 ? `${awayAbbr} -${consensusSpread}` : 'PK'
              ) : '—'}
            </div>
          </div>
          <div className="bg-slate-800/80 rounded-lg p-2 border border-slate-700/50">
            <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">Total</div>
            <div className="text-sm font-black text-white">
              {consensusOU != null ? `o/u ${consensusOU.toFixed(1)}` : '—'}
            </div>
          </div>
          <div className="bg-slate-800/80 rounded-lg p-2 border border-slate-700/50">
            <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">ML</div>
            <div className="text-xs font-bold">
              <span className="text-blue-300">{fmtOdds(consensusAwayMl)}</span>
              <span className="text-slate-600 mx-0.5">/</span>
              <span className="text-emerald-300">{fmtOdds(consensusHomeMl)}</span>
            </div>
          </div>
        </div>

        {/* ── Best Book Highlight ── */}
        {(bestOver || bestUnder) && (
          <div className="grid grid-cols-2 gap-2">
            {bestOver && (
              <div className="bg-emerald-950/40 border border-emerald-700/40 rounded-lg px-2 py-1.5 text-center">
                <div className="text-[9px] text-emerald-500 uppercase tracking-widest mb-0.5">Best Over</div>
                <div className="text-xs font-black text-emerald-300">o{bestOver.total}</div>
                <div className="text-[9px] text-emerald-600">{bestOver.bookmaker} {bestOver.over_price > 0 ? `+${bestOver.over_price}` : bestOver.over_price}</div>
              </div>
            )}
            {bestUnder && (
              <div className="bg-blue-950/40 border border-blue-700/40 rounded-lg px-2 py-1.5 text-center">
                <div className="text-[9px] text-blue-500 uppercase tracking-widest mb-0.5">Best Under</div>
                <div className="text-xs font-black text-blue-300">u{bestUnder.total}</div>
                <div className="text-[9px] text-blue-600">{bestUnder.bookmaker} {bestUnder.under_price > 0 ? `+${bestUnder.under_price}` : bestUnder.under_price}</div>
              </div>
            )}
          </div>
        )}

        {/* ── Kalshi Market ── */}
        {kalshi && (kalshi.home.mid != null || kalshi.away.mid != null) && (() => {
          const hMid = kalshi.home.mid ?? 0;
          const aMid = kalshi.away.mid ?? 0;
          const total = hMid + aMid || 100;
          const hPct  = Math.round((hMid / total) * 100);
          const aPct  = 100 - hPct;
          // Edge vs book implied (if available)
          const hBookImplied = consensusHomeMl != null
            ? Math.round(consensusHomeMl < 0
                ? (-consensusHomeMl / (-consensusHomeMl + 100)) * 100
                : (100 / (consensusHomeMl + 100)) * 100)
            : null;
          const hEdge = hBookImplied != null ? hMid - hBookImplied : null;
          return (
            <div className="border-t border-slate-700/50 pt-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-extrabold tracking-widest text-slate-500 flex items-center gap-1">
                  <span className="inline-block w-3.5 h-3.5 rounded-sm bg-slate-700 text-white text-[8px] font-black flex items-center justify-center leading-none">K</span>
                  KALSHI
                </span>
                {hEdge != null && Math.abs(hEdge) >= 3 && (
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${hEdge > 0 ? 'text-emerald-400 bg-emerald-500/10' : 'text-blue-400 bg-blue-500/10'}`}>
                    {hEdge > 0
                      ? `${homeAbbr} +${hEdge}pp vs book`
                      : `${awayAbbr} +${Math.abs(hEdge)}pp vs book`}
                  </span>
                )}
              </div>
              {/* Price bar */}
              <div className="flex items-center gap-2">
                <div className="text-right flex-shrink-0 w-10">
                  <div className="text-xs font-black text-blue-300">{aMid}¢</div>
                  <div className="text-[9px] text-slate-600">{kalshi.away.subtitle ?? 'Away'}</div>
                </div>
                <div className="flex-1 h-4 rounded-full overflow-hidden bg-slate-700/60 flex relative">
                  <div className="h-full bg-blue-500/70 transition-all" style={{ width: `${aPct}%` }} />
                  <div className="h-full bg-emerald-500/70 transition-all" style={{ width: `${hPct}%` }} />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-[9px] font-black text-white/80 tracking-wider">{aPct}% | {hPct}%</span>
                  </div>
                </div>
                <div className="flex-shrink-0 w-10">
                  <div className="text-xs font-black text-emerald-300">{hMid}¢</div>
                  <div className="text-[9px] text-slate-600">{kalshi.home.subtitle ?? 'Home'}</div>
                </div>
              </div>
              <div className="text-[9px] text-slate-600 text-center">
                YES price in cents · $1 payout if team wins
              </div>
            </div>
          );
        })()}

        {/* ── ATS / O-U Records (NFL) ── */}
        {(homeAts || awayAts) && (
          <div className="border-t border-slate-700/50 pt-3 space-y-1.5">
            <div className="text-[10px] font-extrabold tracking-widest text-slate-500">2025 ATS / O-U</div>
            <div className="grid grid-cols-3 gap-1 text-center text-[10px]">
              <div className="text-left text-slate-600">Team</div>
              <div className="text-slate-600">ATS</div>
              <div className="text-slate-600">O/U</div>
              {/* Away row */}
              <div className="text-left font-bold text-blue-300">{awayAbbr}</div>
              <div className={awayAts && awayAts.ats_pct >= 0.55 ? 'text-emerald-400 font-bold' : awayAts && awayAts.ats_pct <= 0.40 ? 'text-red-400' : 'text-slate-300'}>
                {fmtAts(awayAts)}
              </div>
              <div className={awayAts && awayAts.over_pct >= 0.55 ? 'text-yellow-400 font-bold' : 'text-slate-300'}>
                {fmtOu(awayAts)}
              </div>
              {/* Home row */}
              <div className="text-left font-bold text-emerald-300">{homeAbbr}</div>
              <div className={homeAts && homeAts.ats_pct >= 0.55 ? 'text-emerald-400 font-bold' : homeAts && homeAts.ats_pct <= 0.40 ? 'text-red-400' : 'text-slate-300'}>
                {fmtAts(homeAts)}
              </div>
              <div className={homeAts && homeAts.over_pct >= 0.55 ? 'text-yellow-400 font-bold' : 'text-slate-300'}>
                {fmtOu(homeAts)}
              </div>
            </div>
          </div>
        )}

        {/* ── Injuries + Severity ── */}
        {(effectiveHomeInj.length > 0 || effectiveAwayInj.length > 0) && (
          <div className="space-y-1.5 border-t border-slate-700/50 pt-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-extrabold tracking-widest text-slate-500">INJURY REPORT</span>
              <div className="flex gap-2">
                {awayInjScore > 0 && (
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${awayInjScore >= 6 ? 'bg-red-500/20 text-red-400' : awayInjScore >= 3 ? 'bg-orange-500/20 text-orange-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                    {awayAbbr} {awayInjScore}pt
                  </span>
                )}
                {homeInjScore > 0 && (
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${homeInjScore >= 6 ? 'bg-red-500/20 text-red-400' : homeInjScore >= 3 ? 'bg-orange-500/20 text-orange-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                    {homeAbbr} {homeInjScore}pt
                  </span>
                )}
              </div>
            </div>
            {/* Away injuries — top 3 */}
            {effectiveAwayInj.slice(0, 3).map((inj, i) => (
              <div key={`away-${i}`} className="flex items-center gap-1.5 text-[11px] text-slate-400">
                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${INJURY_DOT[inj.status] ?? 'bg-slate-500'}`} />
                <span className="font-bold text-blue-300">{awayAbbr}</span>
                <span className="truncate">{inj.name} <span className="text-slate-600">·</span> {inj.position} <span className="text-slate-600">·</span> {inj.status}</span>
              </div>
            ))}
            {/* Home injuries — top 3 */}
            {effectiveHomeInj.slice(0, 3).map((inj, i) => (
              <div key={`home-${i}`} className="flex items-center gap-1.5 text-[11px] text-slate-400">
                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${INJURY_DOT[inj.status] ?? 'bg-slate-500'}`} />
                <span className="font-bold text-emerald-300">{homeAbbr}</span>
                <span className="truncate">{inj.name} <span className="text-slate-600">·</span> {inj.position} <span className="text-slate-600">·</span> {inj.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Post-Game Results (final games only) ── */}
      {state.status === 'final' && gameResult && (
        <div className="px-4 pb-3 space-y-3">
          {/* Betting Outcome */}
          <div className="border-t border-slate-700/50 pt-3 space-y-2">
            <div className="text-[10px] font-extrabold tracking-widest text-slate-500">GAME RESULT</div>
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-slate-800/80 rounded-lg p-2 text-center border border-slate-700/50">
                <div className="text-[9px] text-slate-500 uppercase mb-1">Spread</div>
                <div className="text-[11px] font-bold text-slate-200">{gameResult.betting.spread_result}</div>
              </div>
              <div className="bg-slate-800/80 rounded-lg p-2 text-center border border-slate-700/50">
                <div className="text-[9px] text-slate-500 uppercase mb-1">Total</div>
                <div className="text-[11px] font-bold text-slate-200">{gameResult.betting.total_result}</div>
              </div>
            </div>
          </div>

          {/* Our Evaluation */}
          {gameResult.our_evaluation && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-extrabold tracking-widest text-slate-500">MAX EV EVALUATION</span>
                {gameResult.our_evaluation.eval_result && (
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${
                    gameResult.our_evaluation.eval_result === 'win' ? 'bg-emerald-500/20 text-emerald-400' :
                    gameResult.our_evaluation.eval_result === 'loss' ? 'bg-red-500/20 text-red-400' :
                    'bg-yellow-500/20 text-yellow-400'
                  }`}>
                    {gameResult.our_evaluation.eval_result.toUpperCase()}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                  gameResult.our_evaluation.lean_level === 'strong_lean' ? 'bg-emerald-500/15 text-emerald-400' :
                  gameResult.our_evaluation.lean_level === 'favorable_lean' ? 'bg-blue-500/15 text-blue-400' :
                  gameResult.our_evaluation.lean_level === 'slight_lean' ? 'bg-yellow-500/15 text-yellow-400' :
                  'bg-slate-700 text-slate-400'
                }`}>
                  {gameResult.our_evaluation.lean_level.replace(/_/g, ' ').toUpperCase()}
                </span>
                {gameResult.our_evaluation.lean_side && (
                  <span className="text-[11px] text-slate-300 font-semibold">
                    {gameResult.our_evaluation.lean_side} {gameResult.our_evaluation.lean_market ? `(${gameResult.our_evaluation.lean_market})` : ''}
                  </span>
                )}
              </div>

              {/* Game Script (collapsible) */}
              {gameResult.our_evaluation.game_script && (
                <button
                  onClick={(e) => { e.stopPropagation(); setScriptOpen(o => !o); }}
                  className="w-full text-left"
                >
                  <div className="flex items-center justify-between text-[10px] text-slate-500 hover:text-slate-300 transition-colors">
                    <span className="flex items-center gap-1">
                      <span className="bg-blue-500/15 text-blue-400 px-1.5 py-0.5 rounded text-[9px] font-bold">AI</span>
                      Game Script
                    </span>
                    <span>{scriptOpen ? '▲' : '▼'}</span>
                  </div>
                  {scriptOpen && (
                    <div className="mt-2 text-[11px] text-slate-400 leading-relaxed bg-slate-800/60 rounded-lg p-3 border border-slate-700/40">
                      {gameResult.our_evaluation.game_script}
                    </div>
                  )}
                </button>
              )}
            </div>
          )}

          {/* External Picks (Spreitzer, etc.) */}
          {gameResult.external_picks.length > 0 && (
            <div className="space-y-1.5">
              <div className="text-[10px] font-extrabold tracking-widest text-slate-500">EXTERNAL PICKS</div>
              {gameResult.external_picks.map((pick, i) => (
                <div key={i} className="flex items-center justify-between bg-slate-800/60 rounded-lg px-3 py-2 border border-slate-700/40">
                  <div>
                    <span className="text-[10px] font-bold text-purple-400">{pick.source}</span>
                    <span className="text-[11px] text-slate-300 ml-2 font-semibold">{pick.pick_side}</span>
                    {pick.units > 0 && <span className="text-[10px] text-slate-500 ml-1">({pick.units}u)</span>}
                  </div>
                  {pick.pick_result && pick.pick_result !== 'pending' && (
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${
                      pick.pick_result === 'win' ? 'bg-emerald-500/20 text-emerald-400' :
                      pick.pick_result === 'loss' ? 'bg-red-500/20 text-red-400' :
                      'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {pick.pick_result.toUpperCase()}
                    </span>
                  )}
                  {(!pick.pick_result || pick.pick_result === 'pending') && (
                    <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-slate-700 text-slate-400">PENDING</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Footer ── */}
      <div className="flex items-center justify-between px-4 pb-3 pt-1 border-t border-slate-700/40">
        <div className="text-[10px] text-slate-600">{rawOdds.length} books · consensus</div>
        <button
          onClick={() => navigate(`/matchup/${f5Id ?? state.id}${sport === 'NCAAF' ? '?sport=ncaaf' : ''}`)}
          className="text-[11px] font-bold text-slate-400 hover:text-white transition-colors flex items-center gap-1"
        >
          Full Matchup <span className="text-slate-600">→</span>
        </button>
      </div>
    </div>
  );
}
