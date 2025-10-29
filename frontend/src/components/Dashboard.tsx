import { useState, useEffect, useRef } from 'react';
import { LiveGame } from '../types';
import { GameCard } from './GameCard';
import { sportEmojis } from '../utils/sportDetection';
import { useWebSocket } from '../hooks/useWebSocket';

type Sport = 'NBA' | 'NHL' | 'NCAAF' | 'NFL' | 'MLB' | 'ALL';

export function Dashboard() {
  // Use WebSocket for real-time updates instead of polling
  // Pass 'default' as user_id to enable per-user bookmaker filtering
  const { games: wsGames, connected: wsConnected, lastUpdate: wsLastUpdate, error: wsError } = useWebSocket('default');

  const [games, setGames] = useState<LiveGame[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [selectedSport, setSelectedSport] = useState<Sport>('ALL');
  const [soundEnabled, setSoundEnabled] = useState(true);
  const alertedGamesRef = useRef<Set<string>>(new Set());
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Initialize audio and speech synthesis
  useEffect(() => {
    // Create audio element with your custom audio file
    // Place your audio file in the public folder and reference it like this:
    // For example: public/alert-bell.mp3
    const audio = new Audio('/alert-bell.mp3');
    audioRef.current = audio;

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  // Function to speak announcement using Web Speech API
  const speakAlert = (game: LiveGame) => {
    if (!('speechSynthesis' in window)) {
      console.log('Speech synthesis not supported');
      return;
    }

    const { away_team, home_team } = game.state;
    const { recommendation, strength_factor, edge } = game.projection;

    // Create announcement text
    const strengthPercent = strength_factor ? Math.round(strength_factor) : 0;
    const edgePoints = edge ? Math.abs(edge).toFixed(1) : '0';

    const announcement = `Alert! Strong ${recommendation?.toLowerCase()} opportunity detected. ` +
      `${away_team.name} at ${home_team.name}. ` +
      `Bet ${recommendation?.toLowerCase()} with ${strengthPercent} percent confidence. ` +
      `Edge of ${edgePoints} points.`;

    // Create speech utterance
    const utterance = new SpeechSynthesisUtterance(announcement);
    utterance.rate = 1.1; // Slightly faster than normal
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // Play beep first, then speak
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(err => console.log('Audio play failed:', err));

      // Delay speech slightly to let beep play
      setTimeout(() => {
        window.speechSynthesis.speak(utterance);
      }, 200);
    } else {
      window.speechSynthesis.speak(utterance);
    }
  };

  // Check for new strong recommendations and play alert
  useEffect(() => {
    if (!soundEnabled || loading) return;

    games.forEach(game => {
      const gameId = game.state.id;
      const strength = game.projection.strength_factor;
      const hasRecommendation = game.projection.recommendation && strength !== null && strength !== undefined;

      // Check if game has strong recommendation (>50%) and hasn't been alerted yet
      if (hasRecommendation && strength > 50 && !alertedGamesRef.current.has(gameId)) {
        alertedGamesRef.current.add(gameId);

        // Play voice announcement
        speakAlert(game);

        // Log the alert
        console.log(`🔔 ALERT: Strong bet detected for ${game.state.away_team.name} vs ${game.state.home_team.name}`);
        console.log(`   Recommendation: ${game.projection.recommendation} with ${strength.toFixed(1)}% strength`);
      }

      // Clean up alerted games that no longer meet criteria
      if (!hasRecommendation || strength <= 50) {
        alertedGamesRef.current.delete(gameId);
      }
    });
  }, [games, soundEnabled, loading]);

  // Update games from WebSocket
  useEffect(() => {
    if (wsGames.length > 0) {
      setGames(wsGames);
      setLoading(false);
    }

    if (wsLastUpdate) {
      setLastUpdate(wsLastUpdate);
    }

    if (wsError) {
      setError(wsError);
    } else {
      setError(null);
    }
  }, [wsGames, wsLastUpdate, wsError]);

  // Helper function to get sport from game
  const getSport = (game: LiveGame): Sport => {
    if (game.state.sport_key.includes('basketball_nba')) return 'NBA';
    if (game.state.sport_key.includes('icehockey')) return 'NHL';
    if (game.state.sport_key.includes('americanfootball_ncaaf')) return 'NCAAF';
    if (game.state.sport_key.includes('americanfootball_nfl')) return 'NFL';
    if (game.state.sport_key.includes('baseball_mlb')) return 'MLB';
    return 'NBA';
  };

  // Separate games by sport
  const ncaafGames = games.filter(g => getSport(g) === 'NCAAF');
  const nbaGames = games.filter(g => getSport(g) === 'NBA');
  const nhlGames = games.filter(g => getSport(g) === 'NHL');
  const nflGames = games.filter(g => getSport(g) === 'NFL');
  const mlbGames = games.filter(g => getSport(g) === 'MLB');

  // Filter games by selected sport
  const filteredGames = selectedSport === 'ALL' ? games : games.filter(g => getSport(g) === selectedSport);

  // Separate filtered games by status
  const liveGames = filteredGames.filter(g => g.state.status === 'live');
  const upcomingGames = filteredGames.filter(g => g.state.status === 'upcoming');
  const completedGames = filteredGames.filter(g => g.state.status === 'completed');

  // Sort upcoming by commence time
  upcomingGames.sort((a, b) =>
    new Date(a.state.commence_time).getTime() - new Date(b.state.commence_time).getTime()
  );

  // Get league emoji (no copyrighted logos)
  const getLeagueEmoji = (sport: Sport) => {
    switch(sport) {
      case 'NBA':
        return '🏀';
      case 'NHL':
        return '🏒';
      case 'NCAAF':
        return '🏈';
      case 'NFL':
        return '🏈';
      case 'MLB':
        return '⚾';
      default:
        return '🏀';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-bold text-white mb-2">Loading NBA Games...</div>
          <div className="text-slate-400">Fetching live data</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-4">
      {/* Header with League Logo */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex items-center justify-between mb-4">
          {selectedSport !== 'ALL' && (
            <div className="flex items-center gap-4">
              <div className="text-5xl">
                {getLeagueEmoji(selectedSport)}
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white">{selectedSport} Games</h1>
                <div className="flex items-center gap-3">
                  <p className="text-slate-400 text-sm">
                    Last updated: {lastUpdate.toLocaleTimeString()}
                  </p>
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                    <span className={`text-xs font-semibold ${wsConnected ? 'text-green-400' : 'text-red-400'}`}>
                      {wsConnected ? 'LIVE' : 'Disconnected'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
          {selectedSport === 'ALL' && (
            <div>
              <h1 className="text-3xl font-bold text-white mb-1">Live Betting Dashboard</h1>
              <div className="flex items-center gap-3">
                <p className="text-slate-400 text-sm">
                  Last updated: {lastUpdate.toLocaleTimeString()}
                </p>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                  <span className={`text-xs font-semibold ${wsConnected ? 'text-green-400' : 'text-red-400'}`}>
                    {wsConnected ? 'LIVE' : 'Disconnected'}
                  </span>
                </div>
              </div>
            </div>
          )}
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSoundEnabled(!soundEnabled)}
              className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                soundEnabled
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
              title={soundEnabled ? 'Sound alerts enabled' : 'Sound alerts disabled'}
            >
              {soundEnabled ? '🔔 Sound ON' : '🔕 Sound OFF'}
            </button>
            <div className="text-right">
              <div className="text-sm text-slate-400">Total Games</div>
              <div className="text-3xl font-bold text-white">{filteredGames.length}</div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          <button
            onClick={() => setSelectedSport('ALL')}
            className={`px-4 py-2 rounded-lg font-semibold whitespace-nowrap transition-colors ${
              selectedSport === 'ALL'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            All Sports ({games.length})
          </button>
          <button
            onClick={() => setSelectedSport('NBA')}
            className={`px-4 py-2 rounded-lg font-semibold whitespace-nowrap transition-colors flex items-center gap-2 ${
              selectedSport === 'NBA'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <img src={sportEmojis.NBA} alt="NBA" className="w-4 h-4" style={{ imageRendering: 'crisp-edges' }} />
            NBA ({nbaGames.length})
          </button>
          <button
            onClick={() => setSelectedSport('NHL')}
            className={`px-4 py-2 rounded-lg font-semibold whitespace-nowrap transition-colors flex items-center gap-2 ${
              selectedSport === 'NHL'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <img src={sportEmojis.NHL} alt="NHL" className="w-4 h-4" style={{ imageRendering: 'crisp-edges' }} />
            NHL ({nhlGames.length})
          </button>
          <button
            onClick={() => setSelectedSport('NCAAF')}
            className={`px-4 py-2 rounded-lg font-semibold whitespace-nowrap transition-colors flex items-center gap-2 ${
              selectedSport === 'NCAAF'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <img src={sportEmojis.NCAAF} alt="NCAAF" className="w-4 h-4" style={{ imageRendering: 'crisp-edges' }} />
            NCAAF ({ncaafGames.length})
          </button>
          <button
            onClick={() => setSelectedSport('NFL')}
            className={`px-4 py-2 rounded-lg font-semibold whitespace-nowrap transition-colors flex items-center gap-2 ${
              selectedSport === 'NFL'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <img src={sportEmojis.NFL} alt="NFL" className="w-4 h-4" style={{ imageRendering: 'crisp-edges' }} />
            NFL ({nflGames.length})
          </button>
          <button
            onClick={() => setSelectedSport('MLB')}
            className={`px-4 py-2 rounded-lg font-semibold whitespace-nowrap transition-colors flex items-center gap-2 ${
              selectedSport === 'MLB'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <img src={sportEmojis.MLB} alt="MLB" className="w-4 h-4" style={{ imageRendering: 'crisp-edges' }} />
            MLB ({mlbGames.length})
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="max-w-7xl mx-auto mb-6">
          <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded">
            <strong className="font-bold">Error: </strong>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Live Games */}
      {liveGames.length > 0 && (
        <div className="max-w-7xl mx-auto mb-8">
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center">
            <span className="w-3 h-3 bg-red-600 rounded-full mr-2 animate-pulse"></span>
            Live Games ({liveGames.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {liveGames.map(game => (
              <GameCard key={game.state.id} game={game} />
            ))}
          </div>
        </div>
      )}

      {/* Upcoming Games */}
      {upcomingGames.length > 0 && (
        <div className="max-w-7xl mx-auto mb-8">
          <h2 className="text-2xl font-bold text-white mb-4">
            Upcoming Games ({upcomingGames.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {upcomingGames.map(game => (
              <GameCard key={game.state.id} game={game} />
            ))}
          </div>
        </div>
      )}

      {/* Completed Games */}
      {completedGames.length > 0 && (
        <div className="max-w-7xl mx-auto mb-8">
          <h2 className="text-2xl font-bold text-white mb-4">
            Completed Games ({completedGames.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {completedGames.map(game => (
              <GameCard key={game.state.id} game={game} />
            ))}
          </div>
        </div>
      )}

      {/* No Games */}
      {filteredGames.length === 0 && !loading && (
        <div className="max-w-7xl mx-auto text-center py-12">
          <div className="text-xl text-slate-400">
            {selectedSport === 'ALL' ? 'No games available' : `No ${selectedSport} games available`}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="max-w-7xl mx-auto mt-12 text-center text-sm text-slate-500">
        <p className="flex items-center justify-center gap-2">
          <span className={`inline-block w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          {wsConnected ? 'Real-time updates via WebSocket (3s refresh)' : 'Disconnected - Reconnecting...'}
        </p>
        <p className="mt-1">Powered by Odds API</p>
      </div>
    </div>
  );
}
