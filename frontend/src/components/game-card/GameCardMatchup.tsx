import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LiveGame } from '../../types';
import { detectSport, getSportBorderClass } from '../../utils/sportDetection';
import { formatTeamName } from '../../utils/teamNames';

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

interface Props {
  game: LiveGame;
}

export function GameCardMatchup({ game }: Props) {
  const navigate = useNavigate();
  const { state, odds: rawOdds } = game;
  const sport = detectSport(game);
  const borderClass = getSportBorderClass(sport);

  const [matchup, setMatchup] = useState<MatchupData | null>(null);
  const [f5Id, setF5Id]       = useState<string | null>(null);

  // Only NFL has F5 matchup data right now
  const supportsF5 = sport === 'NFL' || sport === 'NCAAF';

  useEffect(() => {
    if (!supportsF5) return;
    const home = formatTeamName(state.home_team.name, state.sport_key);
    const away = formatTeamName(state.away_team.name, state.sport_key);
    fetch(`${F5_BASE}/matchup-lookup?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.event_id) setF5Id(d.event_id); })
      .catch(() => {});
  }, [state.home_team.name, state.away_team.name, supportsF5]);

  useEffect(() => {
    if (!f5Id) return;
    fetch(`${F5_BASE}/matchup/${f5Id}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d && !d.detail) setMatchup(d); })
      .catch(() => {});
  }, [f5Id]);

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

  // Top injuries — one per team (highest severity first)
  const SEVERITY = ['Out', 'Injured Reserve', 'Doubtful', 'Questionable'];
  const topInjury = (list: Injury[]) =>
    [...list].sort((a, b) => SEVERITY.indexOf(a.status) - SEVERITY.indexOf(b.status))[0] ?? null;

  const homeInjury = matchup ? topInjury(matchup.injuries.home) : null;
  const awayInjury = matchup ? topInjury(matchup.injuries.away) : null;

  const homeName = matchup?.home.full_name ?? formatTeamName(state.home_team.name, state.sport_key);
  const awayName = matchup?.away.full_name ?? formatTeamName(state.away_team.name, state.sport_key);
  const homeLogo = matchup?.home.logo ?? null;
  const awayLogo = matchup?.away.logo ?? null;

  return (
    <div className={`bg-slate-800 rounded-lg border-2 ${borderClass} hover:shadow-lg transition-shadow overflow-hidden`}>

      {/* ── Header ── */}
      <div className="flex items-center justify-between px-3 py-2 bg-slate-900/60 border-b border-slate-700">
        <div className="text-xs text-slate-400 font-medium">{gameDate} · {gameTime} CST</div>
        <div className="flex items-center gap-2">
          {matchup?.week && (
            <span className="text-xs text-slate-500">Wk {matchup.week}</span>
          )}
          {matchup?.venue?.name && (
            <span className="text-xs text-slate-500 hidden sm:inline truncate max-w-[120px]">
              {matchup.venue.name}
            </span>
          )}
        </div>
      </div>

      <div className="p-3 space-y-3">

        {/* ── Teams ── */}
        <div className="flex items-center justify-between gap-2">
          {/* Away */}
          <div className="flex items-center gap-2 flex-1 min-w-0">
            {awayLogo
              ? <img src={awayLogo} alt="" className="w-8 h-8 object-contain flex-shrink-0" onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
              : <div className="w-8 h-8 rounded-full bg-slate-700 flex-shrink-0" />
            }
            <div className="min-w-0">
              <div className="text-sm font-bold text-white truncate">{awayName}</div>
              {matchup?.away && (
                <div className={`text-xs font-semibold ${TIER_COLORS[matchup.away.tier ?? ''] ?? 'text-slate-400'}`}>
                  #{matchup.away.rank} · {matchup.away.tier}
                </div>
              )}
            </div>
          </div>

          <div className="text-slate-500 font-bold text-sm px-1 flex-shrink-0">@</div>

          {/* Home */}
          <div className="flex items-center gap-2 flex-1 min-w-0 justify-end">
            <div className="min-w-0 text-right">
              <div className="text-sm font-bold text-white truncate">{homeName}</div>
              {matchup?.home && (
                <div className={`text-xs font-semibold ${TIER_COLORS[matchup.home.tier ?? ''] ?? 'text-slate-400'}`}>
                  #{matchup.home.rank} · {matchup.home.tier}
                </div>
              )}
            </div>
            {homeLogo
              ? <img src={homeLogo} alt="" className="w-8 h-8 object-contain flex-shrink-0" onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
              : <div className="w-8 h-8 rounded-full bg-slate-700 flex-shrink-0" />
            }
          </div>
        </div>

        {/* ── Consensus Odds ── */}
        <div className="grid grid-cols-3 gap-1 text-center">
          <div className="bg-slate-900/60 rounded p-1.5">
            <div className="text-xs text-slate-500 uppercase tracking-wide mb-0.5">Spread</div>
            <div className="text-sm font-bold text-white">
              {consensusSpread != null ? `${matchup?.home.abbr ?? 'HM'} ${fmtSpread(consensusSpread)}` : '—'}
            </div>
          </div>
          <div className="bg-slate-900/60 rounded p-1.5">
            <div className="text-xs text-slate-500 uppercase tracking-wide mb-0.5">O/U</div>
            <div className="text-sm font-bold text-white">
              {consensusOU != null ? consensusOU.toFixed(1) : '—'}
            </div>
          </div>
          <div className="bg-slate-900/60 rounded p-1.5">
            <div className="text-xs text-slate-500 uppercase tracking-wide mb-0.5">ML</div>
            <div className="text-xs font-bold text-white">
              {fmtOdds(consensusAwayMl)} / {fmtOdds(consensusHomeMl)}
            </div>
          </div>
        </div>

        {/* ── Model Win Probability ── */}
        {homeWp != null && awayWp != null && (
          <div>
            <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
              <span>{matchup?.away.abbr} {(awayWp * 100).toFixed(0)}%</span>
              <span className="uppercase tracking-widest text-slate-600 text-[10px]">Model WP</span>
              <span>{(homeWp * 100).toFixed(0)}% {matchup?.home.abbr}</span>
            </div>
            <div className="h-2 rounded-full overflow-hidden bg-slate-700 flex">
              <div
                className="h-full bg-blue-500 transition-all"
                style={{ width: `${awayWp * 100}%` }}
              />
              <div
                className="h-full bg-emerald-500 transition-all"
                style={{ width: `${homeWp * 100}%` }}
              />
            </div>
            {homeEdge != null && (
              <div className="text-xs text-center mt-1">
                <span className={`font-bold ${homeEdge > 0 ? 'text-emerald-400' : 'text-blue-400'}`}>
                  {homeEdge > 0 ? `${matchup?.home.abbr} +${homeEdge.toFixed(1)}%` : `${matchup?.away.abbr} +${Math.abs(homeEdge).toFixed(1)}%`}
                </span>
                <span className="text-slate-500"> edge vs market</span>
              </div>
            )}
          </div>
        )}

        {/* ── Injuries ── */}
        {(homeInjury || awayInjury) && (
          <div className="space-y-1 pt-1 border-t border-slate-700">
            {awayInjury && (
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${INJURY_DOT[awayInjury.status] ?? 'bg-slate-500'}`} />
                <span className="font-medium text-slate-300">{matchup?.away.abbr}:</span>
                <span className="truncate">{awayInjury.name} ({awayInjury.position}) · {awayInjury.status}</span>
              </div>
            )}
            {homeInjury && (
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${INJURY_DOT[homeInjury.status] ?? 'bg-slate-500'}`} />
                <span className="font-medium text-slate-300">{matchup?.home.abbr}:</span>
                <span className="truncate">{homeInjury.name} ({homeInjury.position}) · {homeInjury.status}</span>
              </div>
            )}
          </div>
        )}

        {/* ── Footer ── */}
        <div className="flex items-center justify-between pt-1 border-t border-slate-700">
          <div className="text-xs text-slate-600">
            {rawOdds.length} books · consensus line
          </div>
          <button
            onClick={() => navigate(`/matchup/${f5Id ?? state.id}`)}
            className="text-xs px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white transition-colors font-semibold"
          >
            Full Matchup →
          </button>
        </div>
      </div>
    </div>
  );
}
