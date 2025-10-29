import { useState, useEffect } from 'react';
import { BookmakerLogo } from '../components/BookmakerLogo';

interface GameOdds {
  id: string;
  sport_key: string;
  home_team: string;
  away_team: string;
  home_score?: number;
  away_score?: number;
  commence_time: string;
  status: string;
  odds: Array<{
    bookmaker: string;
    total: number;
    over_price: number;
    under_price: number;
    home_spread: number;
    away_spread: number;
    home_spread_price: number;
    away_spread_price: number;
    home_ml: number;
    away_ml: number;
    is_best_over?: boolean;
    is_best_under?: boolean;
    latency_ms?: number;
  }>;
}

type SportKey = 'basketball_nba' | 'basketball_ncaab' | 'americanfootball_nfl' | 'americanfootball_ncaaf' | 'icehockey_nhl' | 'baseball_mlb';
type BetType = 'moneyline' | 'spread' | 'total';

export function Odds() {
  const [activeSport, setActiveSport] = useState<SportKey>('basketball_nba');
  const [activeBetType, setActiveBetType] = useState<BetType>('moneyline');
  const [games, setGames] = useState<GameOdds[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGames();
  }, [activeSport]);

  const fetchGames = async () => {
    setLoading(true);
    console.log('🎮 Loading games for sport:', activeSport);

    // Use mock data for testing (VPS is off)
    const mockGames = mockData[activeSport] || [];
    console.log('📊 Using mock data:', mockGames.length, 'games');
    setGames(mockGames);
    setLoading(false);

    /* Uncomment when VPS is back online:
    try {
      const response = await fetch(`/api/games`);
      if (!response.ok) throw new Error('API not available');

      const apiGames = await response.json();
      const transformedGames = apiGames.map((game: any) => ({
        id: game.state.id,
        sport_key: game.state.sport_key,
        home_team: game.state.home_team.name,
        away_team: game.state.away_team.name,
        home_score: game.state.home_team.score,
        away_score: game.state.away_team.score,
        commence_time: game.state.commence_time,
        status: game.state.status,
        odds: game.odds
      }));

      const filteredGames = transformedGames.filter((game: GameOdds) => game.sport_key === activeSport);
      filteredGames.sort((a, b) => new Date(a.commence_time).getTime() - new Date(b.commence_time).getTime());
      setGames(filteredGames);
    } catch (error) {
      console.error('API error, using mock data:', error);
      setGames(mockData[activeSport] || []);
    } finally {
      setLoading(false);
    }
    */
  };

  const getSportDisplayName = (sport: SportKey): string => {
    const sportNames = {
      'basketball_nba': 'NBA',
      'basketball_ncaab': 'NCAAB',
      'americanfootball_nfl': 'NFL',
      'americanfootball_ncaaf': 'NCAAF',
      'icehockey_nhl': 'NHL',
      'baseball_mlb': 'MLB'
    };
    return sportNames[sport] || 'NBA';
  };

  const getSportIcon = (sport: SportKey): string => {
    const sportIcons = {
      'basketball_nba': '🏀',
      'basketball_ncaab': '🏀',
      'americanfootball_nfl': '🏈',
      'americanfootball_ncaaf': '🏈',
      'icehockey_nhl': '🏒',
      'baseball_mlb': '⚾'
    };
    return sportIcons[sport] || '🏀';
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const today = new Date();
    const gameDate = new Date(dateStr);

    if (gameDate.toDateString() === today.toDateString()) {
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit'
      });
    }

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  const formatOdds = (price: number): string => {
    if (price > 0) return `+${price}`;
    return price.toString();
  };

  const getTimeUntilGame = (dateStr: string): string => {
    const now = new Date();
    const gameTime = new Date(dateStr);
    const diffMs = gameTime.getTime() - now.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 0) return 'LIVE';
    if (diffMins < 60) return `${diffMins}m`;
    if (diffHours < 24) return `${diffHours}h ${diffMins % 60}m`;
    return `${diffDays}d ${diffHours % 24}h`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black flex items-center justify-center">
        <div className="text-slate-400 text-lg">Loading odds...</div>
      </div>
    );
  }

  // Get all available bookmakers from the games
  const allBookmakers = Array.from(new Set(games.flatMap(game =>
    game.odds.map(odd => odd.bookmaker)
  ))).sort();

  // Select top 10 bookmakers for display
  const bookmakers = allBookmakers.slice(0, 10);

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black p-4">
      <div className="max-w-[1600px] mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-100 mb-2">Odds Comparison</h1>
          <p className="text-slate-400 text-sm">Real-time betting lines across top sportsbooks</p>
        </div>

        {/* Sport Tabs */}
        <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
          {(['basketball_nba', 'basketball_ncaab', 'americanfootball_nfl', 'americanfootball_ncaaf', 'icehockey_nhl', 'baseball_mlb'] as SportKey[]).map((sport) => (
            <button
              key={sport}
              onClick={() => setActiveSport(sport)}
              className={`px-4 py-2 rounded text-sm font-semibold whitespace-nowrap transition-all flex items-center gap-2 ${
                activeSport === sport
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              <span className="text-lg">{getSportIcon(sport)}</span>
              {getSportDisplayName(sport)}
            </button>
          ))}
        </div>

        {/* Bet Type Selector */}
        <div className="flex gap-2 mb-6 bg-slate-900 p-1 rounded-lg border border-slate-700 w-fit">
          <button
            onClick={() => setActiveBetType('moneyline')}
            className={`px-6 py-2 rounded-md text-sm font-semibold transition-all ${
              activeBetType === 'moneyline'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Moneyline
          </button>
          <button
            onClick={() => setActiveBetType('spread')}
            className={`px-6 py-2 rounded-md text-sm font-semibold transition-all ${
              activeBetType === 'spread'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Spread
          </button>
          <button
            onClick={() => setActiveBetType('total')}
            className={`px-6 py-2 rounded-md text-sm font-semibold transition-all ${
              activeBetType === 'total'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Total
          </button>
        </div>

        {/* Compact Odds Grid */}
        <div className="bg-slate-900 rounded-lg overflow-hidden border-2 border-slate-700 shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              {/* Header Row with Bookmaker Logos */}
              <thead className="bg-slate-800">
                <tr>
                  <th className="text-left py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider sticky left-0 bg-slate-800 z-10 min-w-[220px] border-r border-b-2 border-slate-600">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{getSportIcon(activeSport)}</span>
                      {getSportDisplayName(activeSport)} Games
                    </div>
                  </th>
                  {bookmakers.map((bookmaker, index) => (
                    <th key={bookmaker} className={`py-2 px-2 text-center min-w-[95px] border-b-2 border-slate-600 ${
                      index < bookmakers.length - 1 ? 'border-r border-slate-600' : ''
                    }`}>
                      <BookmakerLogo
                        bookmaker={bookmaker}
                        size="md"
                        showName={false}
                      />
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {games.map((game, gameIndex) => (
                  <tr
                    key={game.id}
                    className={`hover:bg-slate-800/30 transition-colors ${
                      game.status === 'live' ? 'bg-red-900/10' : ''
                    } ${gameIndex < games.length - 1 ? 'border-b border-slate-700' : ''}`}
                  >
                    {/* Game Info Column */}
                    <td className="py-2 px-3 sticky left-0 bg-slate-900/95 backdrop-blur-sm z-10 border-r border-slate-600">
                      <div className="flex flex-col">
                        {/* Time Badge */}
                        <div className="flex items-center gap-1.5 mb-1">
                          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                            game.status === 'live'
                              ? 'bg-red-600 text-white animate-pulse'
                              : 'bg-slate-700 text-slate-300'
                          }`}>
                            {game.status === 'live' ? 'LIVE' : getTimeUntilGame(game.commence_time)}
                          </span>
                          {game.status !== 'live' && (
                            <span className="text-[10px] text-slate-500">
                              {formatDate(game.commence_time)}
                            </span>
                          )}
                        </div>

                        {/* Teams */}
                        <div className="space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-slate-100">
                              {game.away_team}
                            </span>
                            {game.away_score !== undefined && (
                              <span className="text-xs font-bold text-blue-400 ml-2">
                                {game.away_score}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-slate-100">
                              {game.home_team}
                            </span>
                            {game.home_score !== undefined && (
                              <span className="text-xs font-bold text-blue-400 ml-2">
                                {game.home_score}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Bookmaker Odds Cells */}
                    {bookmakers.map((bookmaker, bookIndex) => {
                      const bookOdds = game.odds.find(o => o.bookmaker === bookmaker);

                      return (
                        <td key={bookmaker} className={`py-1.5 px-1.5 text-center ${
                          bookIndex < bookmakers.length - 1 ? 'border-r border-slate-700' : ''
                        }`}>
                          {bookOdds ? (
                            <div>
                              {/* Moneyline */}
                              {activeBetType === 'moneyline' && (
                                <div className="grid grid-cols-2 divide-x divide-slate-700">
                                  <div className="hover:bg-slate-800 transition-colors cursor-pointer px-1 py-1.5">
                                    <div className="text-base font-bold text-blue-300">
                                      {formatOdds(bookOdds.away_ml)}
                                    </div>
                                  </div>
                                  <div className="hover:bg-slate-800 transition-colors cursor-pointer px-1 py-1.5">
                                    <div className="text-base font-bold text-green-300">
                                      {formatOdds(bookOdds.home_ml)}
                                    </div>
                                  </div>
                                </div>
                              )}

                              {/* Spread */}
                              {activeBetType === 'spread' && (
                                <div className="grid grid-cols-2 divide-x divide-slate-700">
                                  <div className="hover:bg-slate-800 transition-colors cursor-pointer px-1 py-1.5">
                                    <div className="text-sm font-bold text-slate-100">
                                      {bookOdds.away_spread > 0 ? '+' : ''}{bookOdds.away_spread}
                                    </div>
                                    <div className="text-xs text-slate-400 mt-0.5">
                                      {formatOdds(bookOdds.away_spread_price)}
                                    </div>
                                  </div>
                                  <div className="hover:bg-slate-800 transition-colors cursor-pointer px-1 py-1.5">
                                    <div className="text-sm font-bold text-slate-100">
                                      {bookOdds.home_spread > 0 ? '+' : ''}{bookOdds.home_spread}
                                    </div>
                                    <div className="text-xs text-slate-400 mt-0.5">
                                      {formatOdds(bookOdds.home_spread_price)}
                                    </div>
                                  </div>
                                </div>
                              )}

                              {/* Total */}
                              {activeBetType === 'total' && (
                                <div className="grid grid-cols-2 divide-x divide-slate-700">
                                  <div className={`hover:bg-slate-800 transition-colors cursor-pointer px-1 py-1.5 ${
                                    bookOdds.is_best_over ? 'bg-green-900/30' : ''
                                  }`}>
                                    <div className={`text-[10px] ${bookOdds.is_best_over ? 'text-green-300 font-semibold' : 'text-slate-400'}`}>
                                      O {bookOdds.total}
                                    </div>
                                    <div className={`text-base font-bold mt-0.5 ${bookOdds.is_best_over ? 'text-green-200' : 'text-slate-100'}`}>
                                      {formatOdds(bookOdds.over_price)}
                                    </div>
                                  </div>
                                  <div className={`hover:bg-slate-800 transition-colors cursor-pointer px-1 py-1.5 ${
                                    bookOdds.is_best_under ? 'bg-red-900/30' : ''
                                  }`}>
                                    <div className={`text-[10px] ${bookOdds.is_best_under ? 'text-red-300 font-semibold' : 'text-slate-400'}`}>
                                      U {bookOdds.total}
                                    </div>
                                    <div className={`text-base font-bold mt-0.5 ${bookOdds.is_best_under ? 'text-red-200' : 'text-slate-100'}`}>
                                      {formatOdds(bookOdds.under_price)}
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          ) : (
                            <div className="text-slate-600 text-xs py-3">—</div>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Stats Footer */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-4 text-center">
            <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">Games</div>
            <div className="text-2xl font-bold text-white">{games.length}</div>
          </div>
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-4 text-center">
            <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">Sportsbooks</div>
            <div className="text-2xl font-bold text-green-400">{bookmakers.length}</div>
          </div>
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-4 text-center">
            <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">Live Now</div>
            <div className="text-2xl font-bold text-red-400">
              {games.filter(g => g.status === 'live').length}
            </div>
          </div>
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-4 text-center">
            <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">Total Lines</div>
            <div className="text-2xl font-bold text-blue-400">
              {games.reduce((sum, g) => sum + g.odds.length, 0)}
            </div>
          </div>
        </div>

        {/* Best Odds Legend */}
        {activeBetType === 'total' && (
          <div className="mt-4 text-xs text-slate-400 flex items-center gap-6 justify-center">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-600 rounded ring-2 ring-green-400"></div>
              <span>Best Over Odds</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-600 rounded ring-2 ring-red-400"></div>
              <span>Best Under Odds</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Mock data for development
const mockData: Record<SportKey, GameOdds[]> = {
  basketball_nba: [
    {
      id: 'nba_game_1',
      sport_key: 'basketball_nba',
      home_team: 'Los Angeles Lakers',
      away_team: 'Boston Celtics',
      commence_time: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(), // 2 hours from now
      status: 'upcoming',
      odds: [
        { bookmaker: 'DraftKings', total: 228.5, over_price: -105, under_price: -115, home_spread: -2.5, away_spread: 2.5, home_spread_price: -110, away_spread_price: -110, home_ml: -150, away_ml: 130, is_best_over: true },
        { bookmaker: 'FanDuel', total: 229.0, over_price: -108, under_price: -112, home_spread: -2.5, away_spread: 2.5, home_spread_price: -110, away_spread_price: -110, home_ml: -155, away_ml: 135 },
        { bookmaker: 'BetMGM', total: 228.0, over_price: -110, under_price: -110, home_spread: -3.0, away_spread: 3.0, home_spread_price: -115, away_spread_price: -105, home_ml: -145, away_ml: 125, is_best_under: true },
        { bookmaker: 'Caesars', total: 228.5, over_price: -107, under_price: -113, home_spread: -2.5, away_spread: 2.5, home_spread_price: -108, away_spread_price: -112, home_ml: -152, away_ml: 132 },
        { bookmaker: 'BetRivers', total: 229.0, over_price: -109, under_price: -111, home_spread: -3.0, away_spread: 3.0, home_spread_price: -110, away_spread_price: -110, home_ml: -148, away_ml: 128 },
        { bookmaker: 'PointsBet', total: 228.0, over_price: -112, under_price: -108, home_spread: -2.5, away_spread: 2.5, home_spread_price: -112, away_spread_price: -108, home_ml: -153, away_ml: 133 }
      ]
    },
    {
      id: 'nba_game_2',
      sport_key: 'basketball_nba',
      home_team: 'Golden State Warriors',
      away_team: 'Phoenix Suns',
      commence_time: new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString(), // 4 hours from now
      status: 'upcoming',
      odds: [
        { bookmaker: 'DraftKings', total: 232.5, over_price: -110, under_price: -110, home_spread: 3.5, away_spread: -3.5, home_spread_price: -110, away_spread_price: -110, home_ml: 145, away_ml: -165 },
        { bookmaker: 'FanDuel', total: 233.0, over_price: -108, under_price: -112, home_spread: 3.5, away_spread: -3.5, home_spread_price: -112, away_spread_price: -108, home_ml: 150, away_ml: -170, is_best_over: true },
        { bookmaker: 'BetMGM', total: 232.0, over_price: -115, under_price: -105, home_spread: 4.0, away_spread: -4.0, home_spread_price: -115, away_spread_price: -105, home_ml: 140, away_ml: -160, is_best_under: true },
        { bookmaker: 'Caesars', total: 232.5, over_price: -111, under_price: -109, home_spread: 3.5, away_spread: -3.5, home_spread_price: -110, away_spread_price: -110, home_ml: 148, away_ml: -168 },
        { bookmaker: 'BetRivers', total: 233.0, over_price: -110, under_price: -110, home_spread: 3.5, away_spread: -3.5, home_spread_price: -108, away_spread_price: -112, home_ml: 142, away_ml: -162 },
        { bookmaker: 'PointsBet', total: 232.0, over_price: -113, under_price: -107, home_spread: 4.0, away_spread: -4.0, home_spread_price: -110, away_spread_price: -110, home_ml: 146, away_ml: -166 }
      ]
    },
    {
      id: 'nba_game_3',
      sport_key: 'basketball_nba',
      home_team: 'Milwaukee Bucks',
      away_team: 'Philadelphia 76ers',
      home_score: 98,
      away_score: 92,
      commence_time: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(), // Started 1 hour ago
      status: 'live',
      odds: [
        { bookmaker: 'DraftKings', total: 225.5, over_price: -110, under_price: -110, home_spread: -4.5, away_spread: 4.5, home_spread_price: -110, away_spread_price: -110, home_ml: -180, away_ml: 155 },
        { bookmaker: 'FanDuel', total: 226.0, over_price: -108, under_price: -112, home_spread: -4.5, away_spread: 4.5, home_spread_price: -112, away_spread_price: -108, home_ml: -185, away_ml: 160 },
        { bookmaker: 'BetMGM', total: 225.0, over_price: -112, under_price: -108, home_spread: -5.0, away_spread: 5.0, home_spread_price: -115, away_spread_price: -105, home_ml: -175, away_ml: 150 },
        { bookmaker: 'Caesars', total: 225.5, over_price: -109, under_price: -111, home_spread: -4.5, away_spread: 4.5, home_spread_price: -110, away_spread_price: -110, home_ml: -182, away_ml: 157 },
        { bookmaker: 'BetRivers', total: 226.0, over_price: -110, under_price: -110, home_spread: -4.5, away_spread: 4.5, home_spread_price: -108, away_spread_price: -112, home_ml: -178, away_ml: 152 },
        { bookmaker: 'PointsBet', total: 225.0, over_price: -111, under_price: -109, home_spread: -5.0, away_spread: 5.0, home_spread_price: -110, away_spread_price: -110, home_ml: -180, away_ml: 155 }
      ]
    },
    {
      id: 'nba_game_4',
      sport_key: 'basketball_nba',
      home_team: 'Dallas Mavericks',
      away_team: 'Denver Nuggets',
      commence_time: new Date(Date.now() + 6 * 60 * 60 * 1000).toISOString(), // 6 hours from now
      status: 'upcoming',
      odds: [
        { bookmaker: 'DraftKings', total: 230.5, over_price: -112, under_price: -108, home_spread: 1.5, away_spread: -1.5, home_spread_price: -110, away_spread_price: -110, home_ml: -115, away_ml: -105 },
        { bookmaker: 'FanDuel', total: 231.0, over_price: -110, under_price: -110, home_spread: 1.5, away_spread: -1.5, home_spread_price: -108, away_spread_price: -112, home_ml: -118, away_ml: -102 },
        { bookmaker: 'BetMGM', total: 230.0, over_price: -115, under_price: -105, home_spread: 2.0, away_spread: -2.0, home_spread_price: -112, away_spread_price: -108, home_ml: -120, away_ml: 100, is_best_under: true },
        { bookmaker: 'Caesars', total: 230.5, over_price: -113, under_price: -107, home_spread: 1.5, away_spread: -1.5, home_spread_price: -110, away_spread_price: -110, home_ml: -116, away_ml: -104 },
        { bookmaker: 'BetRivers', total: 231.0, over_price: -110, under_price: -110, home_spread: 1.5, away_spread: -1.5, home_spread_price: -110, away_spread_price: -110, home_ml: -117, away_ml: -103 },
        { bookmaker: 'PointsBet', total: 230.5, over_price: -111, under_price: -109, home_spread: 2.0, away_spread: -2.0, home_spread_price: -110, away_spread_price: -110, home_ml: -119, away_ml: -101, is_best_over: true }
      ]
    }
  ],
  basketball_ncaab: [],
  americanfootball_nfl: [],
  americanfootball_ncaaf: [],
  icehockey_nhl: [],
  baseball_mlb: []
};
