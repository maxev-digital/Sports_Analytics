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
import { MetaTags } from '../components/MetaTags';

export interface GameResult {
  id: string;
  sport: string;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  total_points: number;
  margin: number;
  winner: string;
  commence_time: string;
  betting: { spread_result: string; total_result: string };
  our_evaluation: {
    lean_level: string;
    lean_side: string | null;
    lean_market: string | null;
    unit_rec: number;
    game_script: string | null;
    eval_result: string | null;
  } | null;
  our_predictions: Array<{
    pick_side: string;
    pick_type: string;
    edge_pct: number;
    confidence_tier: string;
    pred_result: string | null;
    sonnet_narrative: string | null;
  }>;
  external_picks: Array<{
    source: string;
    pick_side: string;
    pick_type: string;
    line: number;
    units: number;
    pick_result: string | null;
    actual_score: string | null;
  }>;
}

const ACTIVE_SPORTS: Array<{ key: string; label: string; emoji: string; weekly?: boolean }> = [
  { key: 'americanfootball_nfl',   label: 'NFL',  emoji: '🏈', weekly: true },
  { key: 'americanfootball_ncaaf', label: 'CFB',  emoji: '🏈', weekly: true },
  { key: 'baseball_mlb',           label: 'MLB',  emoji: '⚾' },
  { key: 'basketball_nba',         label: 'NBA',  emoji: '🏀' },
  { key: 'icehockey_nhl',          label: 'NHL',  emoji: '🏒' },
  { key: 'basketball_ncaab',       label: 'NCAAB',emoji: '🏀', weekly: true },
];

/** Weekly sports (NFL/CFB/NCAAB): show the current week only.
 *  NFL week = Thursday → Monday. Look back 5 days from anchor to catch
 *  Thursday/Friday games, look ahead 4 days to catch Monday Night but
 *  stop before next Thursday.
 *  Daily sports (MLB/NBA/NHL): show only games starting today (local date). */
function filterByWindow(games: LiveGame[], weekly: boolean): LiveGame[] {
  const now = Date.now();
  if (weekly) {
    const DAY = 24 * 60 * 60 * 1000;
    // Find the earliest upcoming game to anchor the week
    const upcoming = games
      .map(g => new Date(g.state.commence_time).getTime())
      .filter(t => t >= now - DAY) // include games from last 24h
      .sort((a, b) => a - b);
    if (!upcoming.length) {
      // No upcoming — show games from last 7 days
      return games.filter(g => {
        const t = new Date(g.state.commence_time).getTime();
        return t >= now - 7 * DAY;
      });
    }
    const anchor = upcoming[0];
    // 5 days back catches Thu/Fri kickoffs from earlier in the week
    // 4 days forward catches Sunday→Monday but stops before next Thursday
    const windowStart = anchor - 5 * DAY;
    const windowEnd = anchor + 4 * DAY;
    return games.filter(g => {
      const t = new Date(g.state.commence_time).getTime();
      return t >= windowStart && t <= windowEnd;
    });
  }
  // Daily: same calendar day in local time
  const todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);
  const todayEnd = new Date();
  todayEnd.setHours(23, 59, 59, 999);
  return games.filter(g => {
    const t = new Date(g.state.commence_time).getTime();
    return t >= todayStart.getTime() && t <= todayEnd.getTime();
  });
}

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

const POLL_INTERVAL = 60 * 1000; // 1 minute during games for live scores

export function LiveGames() {
  const [activeSport, setActiveSport] = useState(ACTIVE_SPORTS[0].key);
  const [games, setGames]             = useState<LiveGame[]>([]);
  const [gameResults, setGameResults] = useState<Map<string, GameResult>>(new Map());
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [refreshing, setRefreshing]   = useState(false);

  const fetchGames = async (showLoader: boolean) => {
    if (showLoader) setLoading(true);
    else setRefreshing(true);
    setError(null);

    try {
      // Fetch games + scores + results in parallel
      const [gamesResp, scoresResp, resultsResp] = await Promise.all([
        fetch(getApiUrl(`games?user_id=default&sport_key=${activeSport}`)),
        fetch(getApiUrl(`f5/live-scores?sport=${activeSport}&days=3`)).catch(() => null),
        fetch(getApiUrl(`f5/game-results?sport=${activeSport}&days=3`)).catch(() => null),
      ]);

      if (!gamesResp.ok) throw new Error(String(gamesResp.status));
      const data = await gamesResp.json();
      const sport = ACTIVE_SPORTS.find(s => s.key === activeSport);
      const mapped = (data as any[]).map(apiGameToLiveGame);

      // Merge live scores into game state + inject completed games not in odds feed
      if (scoresResp && scoresResp.ok) {
        const scoresData = await scoresResp.json();
        const scoreMap = new Map<string, any>();
        for (const sg of scoresData.games ?? []) {
          const key = `${sg.away_team}|${sg.home_team}`.toLowerCase();
          scoreMap.set(key, sg);
        }
        const existingKeys = new Set(mapped.map(g => `${g.state.away_team.name}|${g.state.home_team.name}`.toLowerCase()));

        // Update existing games with scores
        for (const game of mapped) {
          const key = `${game.state.away_team.name}|${game.state.home_team.name}`.toLowerCase();
          const score = scoreMap.get(key);
          if (score) {
            if (score.home_score != null) game.state.home_team.score = score.home_score;
            if (score.away_score != null) game.state.away_team.score = score.away_score;
            if (score.status === 'final') game.state.status = 'final';
            else if (score.status === 'live') game.state.status = 'in_progress';
          }
        }

        // Inject completed/live games that the odds feed dropped
        for (const sg of scoresData.games ?? []) {
          const key = `${sg.away_team}|${sg.home_team}`.toLowerCase();
          if (!existingKeys.has(key) && (sg.status === 'final' || sg.status === 'live')) {
            mapped.push(apiGameToLiveGame({
              state: {
                id: sg.id,
                sport_key: sg.sport,
                home_team: { name: sg.home_team, score: sg.home_score },
                away_team: { name: sg.away_team, score: sg.away_score },
                commence_time: sg.commence_time,
                status: sg.status === 'final' ? 'final' : 'in_progress',
              },
              odds: [],
            }));
          }
        }
      }

      // Build game results map for post-game data (evaluations, picks, betting)
      if (resultsResp && resultsResp.ok) {
        const resultsData = await resultsResp.json();
        const rMap = new Map<string, GameResult>();
        for (const gr of resultsData.games ?? []) {
          const key = `${gr.away_team}|${gr.home_team}`.toLowerCase();
          rMap.set(key, gr);
        }
        setGameResults(rMap);
      }

      const filtered = filterByWindow(mapped, !!sport?.weekly);
      // Sort: live games first, then upcoming by time, then final
      filtered.sort((a, b) => {
        const statusOrder = (s: string) => s === 'in_progress' ? 0 : s === 'upcoming' || s === 'scheduled' ? 1 : 2;
        const so = statusOrder(a.state.status) - statusOrder(b.state.status);
        if (so !== 0) return so;
        return new Date(a.state.commence_time).getTime() - new Date(b.state.commence_time).getTime();
      });
      setGames(filtered);
      setLastRefresh(new Date());
      logger.info(`[LiveGames] ${filtered.length}/${mapped.length} games for ${activeSport}`);
    } catch (err) {
      setError(`Failed to load games (${err})`);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Initial load + sport change
  useEffect(() => {
    fetchGames(true);
  }, [activeSport]);

  // Auto-poll every 5 minutes
  useEffect(() => {
    const interval = setInterval(() => fetchGames(false), POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [activeSport]);

  return (
    <div className="analytics-page p-4">
      <MetaTags title="Matchups" description="Live game cards with real-time odds from 15+ sportsbooks, power ratings, injury reports, and ATS records for every game today." />
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-100 mb-1" style={{ letterSpacing: '-0.02em' }}>
            MATCHUPS
          </h1>
          <p className="text-slate-400 text-sm">Today's games with live odds across all books</p>
        </div>
        <button
          onClick={() => fetchGames(false)}
          disabled={refreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700 transition-all disabled:opacity-50"
        >
          <span className={refreshing ? 'animate-spin' : ''}>↻</span>
          {refreshing ? 'Refreshing...' : `Updated ${lastRefresh.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`}
        </button>
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
          {games.map(game => {
            const rKey = `${game.state.away_team.name}|${game.state.home_team.name}`.toLowerCase();
            return (
              <GameCardMatchup
                key={game.state.id}
                game={game}
                gameResult={gameResults.get(rKey)}
              />
            );
          })}
        </div>
      )}

      <div className="mt-4 text-xs text-slate-600 text-center">
        {games.length} games · auto-refreshes every 5 min · data via The Odds API
      </div>
    </div>
  );
}
