import { useState, useEffect, useRef } from 'react';
import { LiveGame } from '../types';
import { GameCard } from '../components/GameCard';
import { LiveGamesTicker } from '../components/LiveGamesTicker';
import { sportEmojis } from '../utils/sportDetection';
import { getApiUrl } from '../config';
import { useAlertMonitoring } from '../hooks/useAlertMonitoring';
import { useAuth } from '../contexts/AuthContext';

export function LiveGames() {
  const { username } = useAuth();
  const [games, setGames] = useState<LiveGame[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSport, setSelectedSport] = useState<string>('live');

  // Real-time alert monitoring
  const alertMonitoring = useAlertMonitoring(games);
  const [pinnedGames, setPinnedGames] = useState<Set<string>>(() => {
    // Load pinned games from localStorage on mount
    const saved = localStorage.getItem('pinnedGames');
    return saved ? new Set(JSON.parse(saved)) : new Set();
  });
  const gameRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  useEffect(() => {
    fetchGames();
    const interval = setInterval(fetchGames, 15000); // PERF FIX: Reduced from 5s to 15s (70% fewer requests)
    return () => clearInterval(interval);
  }, []);

  // Save pinned games to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('pinnedGames', JSON.stringify(Array.from(pinnedGames)));
  }, [pinnedGames]);

  const togglePin = (gameId: string) => {
    setPinnedGames(prev => {
      const newSet = new Set(prev);
      if (newSet.has(gameId)) {
        newSet.delete(gameId);
      } else {
        newSet.add(gameId);
      }
      return newSet;
    });
  };

  const fetchGames = async () => {
    try {
      const userId = username || 'default';
      const url = getApiUrl(`games?user_id=${userId}`);
      console.log('🔄 Fetching games from:', url);
      const response = await fetch(url);
      console.log('✅ Response received:', response.status, response.statusText);

      if (!response.ok) {
        console.error('❌ Response not OK:', response.status);
        setLoading(false);
        return;
      }

      const data = await response.json();
      console.log('📊 Fetched games:', data);
      console.log('📊 Number of games:', data.length);
      if (data.length > 0) {
        console.log('📊 First game structure:', data[0]);
      }
      setGames(data);
      setLoading(false);
    } catch (error) {
      console.error('❌ Error fetching games:', error);
      console.error('❌ Error details:', error instanceof Error ? error.message : String(error));
      setLoading(false);
    }
  };

  const sports = [
    { key: 'live', label: 'All Games', emoji: null },
    { key: 'nfl', label: 'NFL', filter: 'americanfootball_nfl', emoji: sportEmojis.NFL },
    { key: 'ncaaf', label: 'NCAAF', filter: 'americanfootball_ncaaf', emoji: sportEmojis.NCAAF },
    { key: 'nba', label: 'NBA', filter: 'basketball_nba', emoji: sportEmojis.NBA },
    { key: 'ncaab', label: 'NCAAB', filter: 'basketball_ncaab', emoji: sportEmojis.NCAAB },
    { key: 'nhl', label: 'NHL', filter: 'icehockey_nhl', emoji: sportEmojis.NHL },
    { key: 'mlb', label: 'MLB', filter: 'baseball_mlb', emoji: sportEmojis.MLB },
    { key: 'pga', label: 'PGA', filter: 'golf_pga', emoji: sportEmojis.PGA },
    { key: 'atp', label: 'ATP', filter: 'tennis_atp', emoji: sportEmojis.TENNIS },
    { key: 'wta', label: 'WTA', filter: 'tennis_wta', emoji: sportEmojis.TENNIS },
    { key: 'mma', label: 'MMA', filter: 'mma_mixed_martial_arts', emoji: sportEmojis.MMA },
    { key: 'wnba', label: 'WNBA', filter: 'basketball_wnba', emoji: sportEmojis.NBA },
    { key: 'nascar', label: 'NASCAR', filter: 'motorsport_nascar', emoji: null },
  ];

  const filteredGames = selectedSport === 'live'
    ? games  // Show all games when "All Games" is selected
    : games.filter(game => {
        const sport = sports.find(s => s.key === selectedSport);
        return sport && game.state.sport_key.includes(sport.filter);
      });

  // Check if current selection is tennis (ATP or WTA)
  const isTennisSelected = selectedSport === 'atp' || selectedSport === 'wta' ||
    (selectedSport === 'all' && filteredGames.some(g => g.state.sport_key.includes('tennis')));

  // Group tennis games by tournament
  const groupTennisByTournament = (games: LiveGame[]) => {
    const grouped: Record<string, LiveGame[]> = {};
    games.forEach(game => {
      const tournament = game.state.tournament || 'Other Matches';
      if (!grouped[tournament]) {
        grouped[tournament] = [];
      }
      grouped[tournament].push(game);
    });

    // Sort each tournament group: live games first, then by commence_time
    Object.keys(grouped).forEach(tournament => {
      grouped[tournament].sort((a, b) => {
        if (a.state.status === 'live' && b.state.status !== 'live') return -1;
        if (a.state.status !== 'live' && b.state.status === 'live') return 1;
        return new Date(a.state.commence_time).getTime() - new Date(b.state.commence_time).getTime();
      });
    });

    return grouped;
  };

  // Sort helper: pinned games first, then by status
  const sortByPinned = (games: LiveGame[]) => {
    return [...games].sort((a, b) => {
      const aPinned = pinnedGames.has(a.state.id);
      const bPinned = pinnedGames.has(b.state.id);
      if (aPinned && !bPinned) return -1;
      if (!aPinned && bPinned) return 1;
      return 0; // Keep original order if both pinned or both unpinned
    });
  };

  const liveGames = sortByPinned(filteredGames.filter(g => g.state.status === 'live'));
  const upcomingGames = sortByPinned(filteredGames.filter(g => g.state.status === 'upcoming'));

  console.log('🎮 Selected sport:', selectedSport);
  console.log('🎮 Total games:', games.length);
  console.log('🎮 Filtered games:', filteredGames.length);
  console.log('🎮 Live games:', liveGames.length);
  console.log('🎮 Upcoming games:', upcomingGames.length);

  // Scroll to game when ticker item is clicked
  const handleGameClick = (gameId: string) => {
    const element = gameRefs.current[gameId];
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  // For tennis, group by tournament and sort each tournament's games
  const tennisGames = filteredGames.filter(g => g.state.sport_key.includes('tennis'));
  const tennisByTournament = groupTennisByTournament(tennisGames);
  // Sort games within each tournament by pinned status
  Object.keys(tennisByTournament).forEach(tournament => {
    tennisByTournament[tournament] = sortByPinned(tennisByTournament[tournament]);
  });
  const isShowingOnlyTennis = (selectedSport === 'atp' || selectedSport === 'wta') && tennisGames.length > 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl text-slate-300">Loading games...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black">
      {/* Sport Filter Tabs */}
      <div className="sticky top-0 z-10 bg-gradient-to-br from-red-900 via-red-950 to-black border-b border-red-800">
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
        {/* Live Games Ticker */}
        <LiveGamesTicker games={filteredGames} onGameClick={handleGameClick} />

        {/* Tennis Tournament View */}
        {isShowingOnlyTennis && Object.keys(tennisByTournament).length > 0 ? (
          <div>
            {Object.entries(tennisByTournament).map(([tournament, tournamentGames]) => (
              <div key={tournament} className="mb-8">
                {/* Tournament Header */}
                <div className="flex items-center gap-3 mb-4">
                  <img
                    src="https://em-content.zobj.net/source/microsoft-teams/363/tennis_1f3be.png"
                    alt="Tennis"
                    className="w-8 h-8"
                    style={{ imageRendering: 'crisp-edges' }}
                  />
                  <h2 className="text-2xl font-bold text-slate-100">{tournament}</h2>
                  <span className="text-sm text-slate-400">({tournamentGames.length} matches)</span>
                  {tournamentGames.some(g => g.state.status === 'live') && (
                    <div className="flex items-center gap-1.5 ml-2">
                      <div className="w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse"></div>
                      <span className="text-xs text-red-400 font-semibold">LIVE</span>
                    </div>
                  )}
                </div>

                {/* Tournament Matches */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {tournamentGames.map((game) => (
                    <GameCard
                      key={game.state.id}
                      game={game}
                      isPinned={pinnedGames.has(game.state.id)}
                      onTogglePin={togglePin}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <>
            {/* Live Games Section (Non-Tennis) */}
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
                    <div key={game.state.id} ref={(el) => {gameRefs.current[game.state.id] = el}}>
                      <GameCard
                        game={game}
                        isPinned={pinnedGames.has(game.state.id)}
                        onTogglePin={togglePin}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Upcoming Games Section (Non-Tennis) */}
            {upcomingGames.length > 0 && (
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <h2 className="text-2xl font-bold text-slate-100">Upcoming Games</h2>
                  <span className="text-sm text-slate-400">({upcomingGames.length})</span>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {upcomingGames.map((game) => (
                    <GameCard
                      key={game.state.id}
                      game={game}
                      isPinned={pinnedGames.has(game.state.id)}
                      onTogglePin={togglePin}
                    />
                  ))}
                </div>
              </div>
            )}
          </>
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
