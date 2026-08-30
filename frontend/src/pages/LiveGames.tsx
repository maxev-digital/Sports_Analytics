/**
 * Live Games — Game Cards screen
 * Fetches today's games from /api/games for active sports and renders
 * them using GameCardV2. No WebSocket dependency — REST polling only.
 */
import { useState, useEffect } from 'react';
import { GameCardMatchup } from '../components/game-card/GameCardMatchup';
import { LiveGame, GameOdds } from '../types';
import { getApiUrl } from '../config';
import { logger } from '../utils/logger';
import '../styles/analytics.css';

const ACTIVE_SPORTS: Array<{ key: string; label: string; emoji: string }> = [
  { key: 'americanfootball_nfl',   label: 'NFL',  emoji: '🏈' },
  { key: 'americanfootball_ncaaf', label: 'CFB',  emoji: '🏈' },
  { key: 'baseball_mlb',           label: 'MLB',  emoji: '⚾' },
  { key: 'basketball_nba',         label: 'NBA',  emoji: '🏀' },
  { key: 'icehockey_nhl',          label: 'NHL',  emoji: '🏒' },
  { key: 'basketball_ncaab',       label: 'NCAAB',emoji: '🏀' },
];

const EMPTY_PROJECTION = {
  current_total: 0,
  projected_final: 0,
  pregame_total: 0,
  current_live_total: null,
  line_movement: null,
  best_book_disparity: null,
  best_disparity_amount: null,
  edge: null,
  confidence: 'LOW' as const,
  recommendation: null,
  strength_factor: null,
};

function apiGameToLiveGame(apiGame: any): LiveGame {
  const odds: GameOdds[] = (apiGame.odds ?? []).map((o: any) => ({
    bookmaker:        o.bookmaker,
    total:            o.total ?? 0,
    over_price:       o.over_price ?? 0,
    under_price:      o.under_price ?? 0,
    is_best_over:     o.is_best_over ?? false,
    is_best_under:    o.is_best_under ?? false,
    latency_ms:       null,
    home_spread:      o.home_spread ?? null,
    away_spread:      o.away_spread ?? null,
    home_spread_price:o.home_spread_price ?? null,
    away_spread_price:o.away_spread_price ?? null,
    home_ml:          o.home_ml ?? null,
    away_ml:          o.away_ml ?? null,
  }));

  return {
    state: {
      id:             apiGame.state.id,
      sport_key:      apiGame.state.sport_key,
      home_team:      { name: apiGame.state.home_team.name, score: apiGame.state.home_team.score },
      away_team:      { name: apiGame.state.away_team.name, score: apiGame.state.away_team.score },
      commence_time:  apiGame.state.commence_time,
      status:         apiGame.state.status ?? 'upcoming',
      quarter:        null,
      time_remaining: null,
    },
    odds,
    projection:           EMPTY_PROJECTION,
    home_team_stats:      null,
    away_team_stats:      null,
    home_nfl_live_stats:  null,
    away_nfl_live_stats:  null,
    home_nfl_stats:       null,
    away_nfl_stats:       null,
    home_ncaaf_stats:     null,
    away_ncaaf_stats:     null,
    home_nhl_momentum:    null,
    away_nhl_momentum:    null,
    home_nhl_stats:       null,
    away_nhl_stats:       null,
    home_nba_momentum:    null,
    away_nba_momentum:    null,
    home_nfl_momentum:    null,
    away_nfl_momentum:    null,
    home_ncaaf_momentum:  null,
    away_ncaaf_momentum:  null,
    home_mlb_stats:       null,
    away_mlb_stats:       null,
    alternate_lines:      null,
  };
}

export function LiveGames() {
  const [activeSport, setActiveSport] = useState(ACTIVE_SPORTS[0].key);
  const [games, setGames]             = useState<LiveGame[]>([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch(getApiUrl(`games?user_id=default&sport_key=${activeSport}`))
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(data => {
        if (cancelled) return;
        const mapped = (data as any[]).map(apiGameToLiveGame);
        mapped.sort((a, b) =>
          new Date(a.state.commence_time).getTime() - new Date(b.state.commence_time).getTime()
        );
        setGames(mapped);
        logger.info(`[LiveGames] ${mapped.length} games for ${activeSport}`);
      })
      .catch(err => {
        if (!cancelled) setError(`Failed to load games (${err})`);
      })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [activeSport]);

  return (
    <div className="analytics-page p-4">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-slate-100 mb-1" style={{ letterSpacing: '-0.02em' }}>
          GAME CARDS
        </h1>
        <p className="text-slate-400 text-sm">Today's games with live odds across all books</p>
      </div>

      {/* Sport tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {ACTIVE_SPORTS.map(s => (
          <button
            key={s.key}
            onClick={() => setActiveSport(s.key)}
            className={`px-3 py-1.5 rounded text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
              activeSport === s.key
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
            }`}
          >
            <span>{s.emoji}</span> {s.label}
          </button>
        ))}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20 text-slate-400">
          Loading games...
        </div>
      )}

      {error && !loading && (
        <div className="flex items-center justify-center py-20 text-red-400">{error}</div>
      )}

      {!loading && !error && games.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 gap-3">
          <span className="text-4xl">📭</span>
          <p className="text-slate-400">No games scheduled for this sport today.</p>
        </div>
      )}

      {!loading && !error && games.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {games.map(game => (
            <GameCardMatchup
              key={game.state.id}
              game={game}
            />
          ))}
        </div>
      )}

      <div className="mt-4 text-xs text-slate-600 text-center">
        {games.length} games · odds cached 24h · data via The Odds API
      </div>
    </div>
  );
}
