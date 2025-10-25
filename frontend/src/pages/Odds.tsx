import { useState, useEffect } from 'react';

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

export function Odds() {
  const [activeSport, setActiveSport] = useState<SportKey>('basketball_nba');
  const [games, setGames] = useState<GameOdds[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGames();
  }, [activeSport]);

  const fetchGames = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/games`);
      const apiGames = await response.json();

      // Transform API data to match our interface
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

      // Filter games by selected sport and sort by time
      const filteredGames = transformedGames.filter((game: GameOdds) => game.sport_key === activeSport);
      filteredGames.sort((a, b) => new Date(a.commence_time).getTime() - new Date(b.commence_time).getTime());

      setGames(filteredGames);
    } catch (error) {
      console.error('Error fetching games:', error);
      setGames(mockData[activeSport] || []);
    } finally {
      setLoading(false);
    }
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

  const getSportLogo = (sport: SportKey): string => {
    const sportLogos = {
      'basketball_nba': 'https://a.espncdn.com/i/teamlogos/leagues/500/nba.png',
      'basketball_ncaab': 'https://a.espncdn.com/i/teamlogos/leagues/500/ncaab.png',
      'americanfootball_nfl': 'https://a.espncdn.com/i/teamlogos/leagues/500/nfl.png',
      'americanfootball_ncaaf': 'https://a.espncdn.com/i/teamlogos/leagues/500/ncaaf.png',
      'icehockey_nhl': 'https://a.espncdn.com/i/teamlogos/leagues/500/nhl.png',
      'baseball_mlb': 'https://a.espncdn.com/i/teamlogos/leagues/500/mlb.png'
    };
    return sportLogos[sport] || sportLogos.basketball_nba;
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

  // Select top 8 bookmakers for display (typical professional layout)
  const bookmakers = allBookmakers.slice(0, 8);

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-100 mb-2">Live Odds Grid</h1>
          <p className="text-slate-400 text-sm">Real-time odds comparison across sportsbooks</p>
        </div>

        {/* Sport Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto">
          {(['basketball_nba', 'basketball_ncaab', 'americanfootball_nfl', 'americanfootball_ncaaf', 'icehockey_nhl', 'baseball_mlb'] as SportKey[]).map((sport) => (
            <button
              key={sport}
              onClick={() => setActiveSport(sport)}
              className={`px-4 py-2 rounded text-sm font-semibold whitespace-nowrap transition-all flex items-center gap-2 ${
                activeSport === sport
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              <img src={getSportLogo(sport)} alt="" className="w-4 h-4" />
              {getSportDisplayName(sport)}
            </button>
          ))}
        </div>

        {/* Odds Grid */}
        <div className="bg-slate-900 rounded-lg overflow-hidden border border-slate-700">
          <div className="overflow-x-auto">
            <table className="w-full">
              {/* Header Row */}
              <thead className="bg-slate-800 border-b border-slate-600">
                <tr>
                  <th className="text-left py-3 px-4 text-slate-300 font-bold text-sm sticky left-0 bg-slate-800 z-10 min-w-64">
                    Game ({getSportDisplayName(activeSport)})
                  </th>
                  {bookmakers.map(bookmaker => (
                    <th key={bookmaker} className="py-3 px-2 text-center text-slate-300 font-bold text-xs min-w-48">
                      {bookmaker}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {/* Moneyline Section */}
                {games.map((game) => {
                  const gameBookmakers = bookmakers;
                  return (
                    <tr key={`${game.id}-ml`} className="border-b border-slate-700">
                      <td className="py-3 px-4 text-white font-semibold text-sm sticky left-0 bg-slate-900/80 backdrop-blur-sm">
                        <div className="flex flex-col">
                          <span className="text-xs text-slate-400 opacity-70">
                            {formatDate(game.commence_time)}
                          </span>
                          <div className="flex items-center justify-between mt-1">
                            <span className="text-slate-200">{game.away_team}</span>
                            <span className="text-slate-500 mx-2">vs</span>
                            <span className="text-slate-200">{game.home_team}</span>
                          </div>
                        </div>
                      </td>
                      {gameBookmakers.map(bookmaker => {
                        const bookOdds = game.odds.find(o => o.bookmaker === bookmaker);
                        return (
                          <td key={bookmaker} className="py-3 px-2 text-center">
                            {bookOdds ? (
                              <div className="grid grid-cols-2 gap-1">
                                <div className="bg-slate-700 rounded p-1 text-xs">
                                  <div className="text-blue-300 font-bold">
                                    {formatOdds(bookOdds.away_ml)}
                                  </div>
                                  <div className="text-slate-400 text-[10px]">AWAY</div>
                                </div>
                                <div className="bg-slate-700 rounded p-1 text-xs">
                                  <div className="text-green-300 font-bold">
                                    {formatOdds(bookOdds.home_ml)}
                                  </div>
                                  <div className="text-slate-400 text-[10px]">HOME</div>
                                </div>
                              </div>
                            ) : (
                              <div className="text-slate-600 text-xs">-</div>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}

                {/* Spread Section */}
                {games.map((game) => {
                  const gameBookmakers = bookmakers;
                  return (
                    <tr key={`${game.id}-spread`} className="border-b border-slate-700">
                      <td className="py-3 px-4 text-slate-400 font-semibold text-sm sticky left-0 bg-slate-900/80 backdrop-blur-sm">
                        Spread
                      </td>
                      {gameBookmakers.map(bookmaker => {
                        const bookOdds = game.odds.find(o => o.bookmaker === bookmaker);
                        return (
                          <td key={bookmaker} className="py-3 px-2 text-center">
                            {bookOdds ? (
                              <div className="grid grid-cols-2 gap-1">
                                <div className="bg-slate-600 rounded p-1 text-xs">
                                  <div className="text-slate-300 font-bold">
                                    {bookOdds.away_spread > 0 ? '+' : ''}{bookOdds.away_spread}
                                  </div>
                                  <div className="text-slate-400 text-[10px]">
                                    {formatOdds(bookOdds.away_spread_price)}
                                  </div>
                                </div>
                                <div className="bg-slate-600 rounded p-1 text-xs">
                                  <div className="text-slate-300 font-bold">
                                    {bookOdds.home_spread > 0 ? '+' : ''}{bookOdds.home_spread}
                                  </div>
                                  <div className="text-slate-400 text-[10px]">
                                    {formatOdds(bookOdds.home_spread_price)}
                                  </div>
                                </div>
                              </div>
                            ) : (
                              <div className="text-slate-600 text-xs">-</div>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}

                {/* Total Section */}
                {games.map((game, gameIndex) => {
                  const gameBookmakers = bookmakers;
                  return (
                    <tr key={`${game.id}-total`} className={`${gameIndex < games.length - 1 ? 'border-b border-slate-600' : ''}`}>
                      <td className="py-3 px-4 text-slate-400 font-semibold text-sm sticky left-0 bg-slate-900/80 backdrop-blur-sm">
                        Total
                      </td>
                      {gameBookmakers.map(bookmaker => {
                        const bookOdds = game.odds.find(o => o.bookmaker === bookmaker);
                        return (
                          <td key={bookmaker} className="py-3 px-2 text-center">
                            {bookOdds ? (
                              <div className="grid grid-cols-2 gap-1">
                                <div className={`rounded p-1 text-xs ${
                                  bookOdds.is_best_over ? 'bg-green-700 ring-1 ring-green-400' : 'bg-slate-600'
                                }`}>
                                  <div className="font-bold">
                                    {bookOdds.total}
                                  </div>
                                  <div className={`text-[10px] ${
                                    bookOdds.is_best_over ? 'text-green-200' : 'text-slate-400'
                                  }`}>
                                    {formatOdds(bookOdds.over_price)}
                                  </div>
                                </div>
                                <div className={`rounded p-1 text-xs ${
                                  bookOdds.is_best_under ? 'bg-red-700 ring-1 ring-red-400' : 'bg-slate-600'
                                }`}>
                                  <div className="font-bold">
                                    <span className={`text-[10px] ${
                                      bookOdds.is_best_under ? 'text-red-200' : 'text-slate-400'
                                    }`}>
                                      U
                                    </span>
                                  </div>
                                  <div className={`text-[10px] ${
                                    bookOdds.is_best_under ? 'text-red-200' : 'text-slate-400'
                                  }`}>
                                    {formatOdds(bookOdds.under_price)}
                                  </div>
                                </div>
                              </div>
                            ) : (
                              <div className="text-slate-600 text-xs">-</div>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer Stats */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800 rounded border border-slate-700 p-3 text-center">
            <div className="text-sm text-slate-400 mb-1">Games</div>
            <div className="text-lg font-bold text-white">{games.length}</div>
          </div>
          <div className="bg-slate-800 rounded border border-slate-700 p-3 text-center">
            <div className="text-sm text-slate-400 mb-1">Bookmakers</div>
            <div className="text-lg font-bold text-green-400">{bookmakers.length}</div>
          </div>
          <div className="bg-slate-800 rounded border border-slate-700 p-3 text-center">
            <div className="text-sm text-slate-400 mb-1">Live Games</div>
            <div className="text-lg font-bold text-red-400">
              {games.filter(g => g.status === 'live').length}
            </div>
          </div>
          <div className="bg-slate-800 rounded border border-slate-700 p-3 text-center">
            <div className="text-sm text-slate-400 mb-1">Total Lines</div>
            <div className="text-lg font-bold text-blue-400">
              {games.reduce((sum, g) => sum + g.odds.length, 0)}
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="mt-4 text-xs text-slate-500 flex items-center gap-4 justify-center">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-700 rounded"></div>
            <span>Best Over</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-700 rounded"></div>
            <span>Best Under</span>
          </div>
        </div>
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
      home_team: 'Lakers',
      away_team: 'Celtics',
      commence_time: '2025-01-17T19:30:00',
      status: 'upcoming',
      odds: [
        {
          bookmaker: 'DraftKings',
          total: 228.5,
          over_price: -105,
          under_price: -115,
          home_spread: -2.5,
          away_spread: 2.5,
          home_spread_price: -110,
          away_spread_price: -110,
          home_ml: 150,
          away_ml: -180,
          is_best_over: true,
          latency_ms: 1000
        },
        {
          bookmaker: 'FanDuel',
          total: 229.0,
          over_price: -108,
          under_price: -112,
          home_spread: -2.5,
          away_spread: 2.5,
          home_spread_price: -110,
          away_spread_price: -110,
          home_ml: 155,
          away_ml: -175,
          latency_ms: 1500
        },
        {
          bookmaker: 'BetMGM',
          total: 228.0,
          over_price: -106,
          under_price: -114,
          home_spread: -3.0,
          away_spread: 3.0,
          home_spread_price: -115,
          away_spread_price: -105,
          home_ml: 140,
          away_ml: -165,
          is_best_under: true,
          latency_ms: 3000
        }
      ]
    }
  ],
  basketball_ncaab: [],
  americanfootball_nfl: [],
  americanfootball_ncaaf: [],
  icehockey_nhl: [],
  baseball_mlb: []
};
