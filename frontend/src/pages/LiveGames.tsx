import { useState, useEffect } from 'react';
import { LiveGame } from '../types';
import { GameCard } from '../components/GameCard';
import { sportEmojis } from '../utils/sportDetection';

export function LiveGames() {
  const [games, setGames] = useState<LiveGame[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSport, setSelectedSport] = useState<string>('all');

  useEffect(() => {
    fetchGames();
    const interval = setInterval(fetchGames, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchGames = async () => {
    try {
      const response = await fetch('/api/games');
      const data = await response.json();
      setGames(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching games:', error);
      setLoading(false);
    }
  };

  const sports = [
    { key: 'all', label: 'All Sports', logo: null, emoji: null },
    { key: 'nfl', label: 'NFL', filter: 'americanfootball_nfl', logo: 'https://a.espncdn.com/i/teamlogos/leagues/500/nfl.png', emoji: sportEmojis.NFL },
    { key: 'ncaaf', label: 'NCAAF', filter: 'americanfootball_ncaaf', logo: 'https://a.espncdn.com/i/teamlogos/leagues/500/ncaa.png', emoji: sportEmojis.NCAAF },
    { key: 'nba', label: 'NBA', filter: 'basketball_nba', logo: 'https://a.espncdn.com/i/teamlogos/leagues/500/nba.png', emoji: sportEmojis.NBA },
    { key: 'ncaab', label: 'NCAAB', filter: 'basketball_ncaab', logo: 'https://a.espncdn.com/i/teamlogos/leagues/500/ncaa.png', emoji: sportEmojis.NCAAB },
    { key: 'nhl', label: 'NHL', filter: 'icehockey_nhl', logo: 'https://a.espncdn.com/i/teamlogos/leagues/500/nhl.png', emoji: sportEmojis.NHL },
    { key: 'mlb', label: 'MLB', filter: 'baseball_mlb', logo: 'https://a.espncdn.com/i/teamlogos/leagues/500/mlb.png', emoji: sportEmojis.MLB },
    { key: 'pga', label: 'PGA', filter: 'golf_pga', logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/leagues/500/pga.png', emoji: sportEmojis.PGA },
    { key: 'atp', label: 'ATP', filter: 'tennis_atp', logo: 'https://a.espncdn.com/i/teamlogos/leagues/500/atp.png', emoji: sportEmojis.TENNIS },
    { key: 'wta', label: 'WTA', filter: 'tennis_wta', logo: 'https://a.espncdn.com/i/teamlogos/leagues/500/wta.png', emoji: sportEmojis.TENNIS },
    { key: 'mma', label: 'MMA', filter: 'mma_mixed_martial_arts', logo: 'https://a.espncdn.com/i/teamlogos/leagues/500/ufc.png', emoji: sportEmojis.MMA },
    { key: 'wnba', label: 'WNBA', filter: 'basketball_wnba', logo: 'https://a.espncdn.com/i/teamlogos/leagues/500/wnba.png', emoji: sportEmojis.NBA },
    { key: 'nascar', label: 'NASCAR', filter: 'motorsport_nascar', logo: 'https://a.espncdn.com/i/teamlogos/leagues/500/nascar.png', emoji: null },
  ];

  const filteredGames = selectedSport === 'all'
    ? games
    : games.filter(game => {
        const sport = sports.find(s => s.key === selectedSport);
        return sport && game.state.sport_key.includes(sport.filter);
      });

  const liveGames = filteredGames.filter(g => g.state.status === 'live');
  const upcomingGames = filteredGames.filter(g => g.state.status === 'upcoming');

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl text-slate-300">Loading games...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)' }}>
      {/* Sport Filter Tabs */}
      <div className="sticky top-0 z-10 bg-slate-900/95 backdrop-blur-sm border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex gap-2 overflow-x-auto scrollbar-hide">
            {sports.map(sport => (
              <button
                key={sport.key}
                onClick={() => setSelectedSport(sport.key)}
                className={`px-3 py-2 rounded-lg text-sm font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
                  selectedSport === sport.key
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {sport.emoji && (
                  <img
                    src={sport.emoji}
                    alt={sport.label}
                    className="w-4 h-4"
                    style={{ imageRendering: 'crisp-edges' }}
                  />
                )}
                {sport.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Live Games Section */}
        {liveGames.length > 0 && (
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                <h2 className="text-2xl font-bold text-slate-100">Live Games</h2>
              </div>
              <span className="text-sm text-slate-400">({liveGames.length})</span>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {liveGames.map((game) => (
                <GameCard key={game.state.id} game={game} />
              ))}
            </div>
          </div>
        )}

        {/* Upcoming Games Section */}
        {upcomingGames.length > 0 && (
          <div>
            <div className="flex items-center gap-3 mb-4">
              <h2 className="text-2xl font-bold text-slate-100">Upcoming Games</h2>
              <span className="text-sm text-slate-400">({upcomingGames.length})</span>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {upcomingGames.map((game) => (
                <GameCard key={game.state.id} game={game} />
              ))}
            </div>
          </div>
        )}

        {/* No Games Message */}
        {filteredGames.length === 0 && (
          <div className="text-center py-20">
            {(() => {
              const currentSport = sports.find(s => s.key === selectedSport);
              const emojiUrl = currentSport?.emoji || sportEmojis.NBA;
              return (
                <img
                  src={emojiUrl}
                  alt="No games"
                  className="w-16 h-16 mx-auto mb-4"
                  style={{ imageRendering: 'crisp-edges' }}
                />
              );
            })()}
            <h3 className="text-xl font-semibold text-slate-300 mb-2">
              No {selectedSport !== 'all' ? sports.find(s => s.key === selectedSport)?.label : ''} games available
            </h3>
            <p className="text-slate-400">Check back later for more games</p>
          </div>
        )}
      </div>
    </div>
  );
}
