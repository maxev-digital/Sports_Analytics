import { useEffect, useState } from 'react';
import { OddsMetricsDashboard } from '../components/OddsMetricsDashboard';

interface HandicapperPick {
  id: string;
  sport: string;
  game_id: string;
  home_team: string;
  away_team: string;
  commence_time: string;
  pick_type: 'spread' | 'moneyline' | 'total';
  pick_side: string;
  pick_value: number | null;
  odds: number;
  bookmaker: string;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  handicapper: string;
  analysis: string;
  key_factors: string[];
  edge_percent: number | null;
  created_at: string;
}

interface HandicapperPicksResponse {
  picks: HandicapperPick[];
  total_picks: number;
  last_updated: string;
}

export function HandicapperPicks() {
  const [selectedSport, setSelectedSport] = useState<string>('nba');
  const [picks, setPicks] = useState<HandicapperPick[]>([]);
  const [loading, setLoading] = useState(true);

  const sports = [
    { key: 'nba', name: 'NBA', emoji: '🏀' },
    { key: 'nfl', name: 'NFL', emoji: '🏈' },
    { key: 'nhl', name: 'NHL', emoji: '🏒' },
    { key: 'mlb', name: 'MLB', emoji: '⚾' },
    { key: 'ncaab', name: 'NCAAB', emoji: '🏀' },
    { key: 'ncaaf', name: 'NCAAF', emoji: '🏈' }
  ];

  // Fetch handicapper picks
  useEffect(() => {
    const fetchPicks = async () => {
      setLoading(true);
      try {
        const response = await fetch(`/api/handicapper-picks/${selectedSport}`);
        if (response.ok) {
          const data: HandicapperPicksResponse = await response.json();
          setPicks(data.picks || []);
        }
      } catch (error) {
        console.error('Error fetching handicapper picks:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPicks();
    const interval = setInterval(fetchPicks, 300000); // Refresh every 5 minutes

    return () => clearInterval(interval);
  }, [selectedSport]);

  const formatPickType = (type: string) => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  const formatOdds = (odds: number) => {
    return odds > 0 ? `+${odds}` : `${odds}`;
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'HIGH':
        return 'from-green-800/60 via-green-700/50 to-green-800/60 border-green-500/60';
      case 'MEDIUM':
        return 'from-yellow-800/60 via-yellow-700/50 to-yellow-800/60 border-yellow-500/60';
      case 'LOW':
        return 'from-slate-800/60 via-slate-700/50 to-slate-800/60 border-slate-500/60';
      default:
        return 'from-slate-800/60 via-slate-700/50 to-slate-800/60 border-slate-500/60';
    }
  };

  const getConfidenceBadgeColor = (confidence: string) => {
    switch (confidence) {
      case 'HIGH':
        return 'bg-green-900/50 text-green-400 border-green-700';
      case 'MEDIUM':
        return 'bg-yellow-900/50 text-yellow-400 border-yellow-700';
      case 'LOW':
        return 'bg-slate-900/50 text-slate-400 border-slate-700';
      default:
        return 'bg-slate-900/50 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black p-4" style={{ fontFamily: 'Rubik, sans-serif' }}>
      <div className="w-full mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-100 mb-2">Handicapper Picks</h1>
          <p className="text-slate-400 text-sm">
            Expert analysis and betting recommendations from professional handicappers
          </p>
        </div>

        {/* Sport Tabs & Metrics Dashboard - Side by Side */}
        <div className="flex gap-4 mb-4">
          {/* Sport Tabs - Vertical */}
          <div className="flex flex-col gap-2">
            {sports.map((sport) => (
              <button
                key={sport.key}
                onClick={() => setSelectedSport(sport.key)}
                className={`px-3 py-1.5 text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-2 ${
                  selectedSport === sport.key
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
                }`}
              >
                <span className="text-sm">{sport.emoji}</span>
                {sport.name}
              </button>
            ))}
          </div>

          {/* Metrics Dashboard & Main Content */}
          <div className="flex-1">
            <OddsMetricsDashboard />

            {/* Picks Content */}
            {loading ? (
              <div className="text-center text-white text-xl py-12">
                Loading handicapper picks...
              </div>
            ) : picks.length === 0 ? (
              <div className="bg-slate-800/50 border border-slate-700 p-12 text-center mt-4">
                <div className="text-slate-400 text-lg mb-2">No picks available</div>
                <div className="text-slate-500 text-sm">
                  Check back later for today's handicapper picks
                </div>
              </div>
            ) : (
              <div className="mt-4 space-y-4">
                {picks.map((pick) => (
                  <div
                    key={pick.id}
                    className={`bg-gradient-to-br ${getConfidenceColor(pick.confidence)} border p-4 transition-all duration-200 hover:scale-[1.01] hover:shadow-lg`}
                  >
                    {/* Pick Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-white font-bold text-lg">
                            {pick.away_team} @ {pick.home_team}
                          </h3>
                          <span className={`px-2 py-0.5 text-xs font-bold border ${getConfidenceBadgeColor(pick.confidence)}`}>
                            {pick.confidence}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-sm text-slate-400">
                          <span>{new Date(pick.commence_time).toLocaleString()}</span>
                          <span>•</span>
                          <span className="text-slate-300 font-semibold">By {pick.handicapper}</span>
                        </div>
                      </div>

                      {/* Pick Summary Box */}
                      <div className="bg-slate-900/50 border border-slate-600 p-3 ml-4">
                        <div className="text-center">
                          <div className="text-xs text-slate-500 uppercase mb-1">The Pick</div>
                          <div className="text-white font-bold text-lg mb-1">
                            {pick.pick_side}
                            {pick.pick_value !== null && (
                              <span className="text-slate-400 ml-1">
                                {pick.pick_type === 'spread' ? (pick.pick_value > 0 ? `+${pick.pick_value}` : pick.pick_value) : pick.pick_value}
                              </span>
                            )}
                          </div>
                          <div className="text-slate-300 text-sm font-semibold">
                            {formatOdds(pick.odds)} @ {pick.bookmaker}
                          </div>
                          <div className="text-xs text-slate-500 mt-1">{formatPickType(pick.pick_type)}</div>
                        </div>
                      </div>
                    </div>

                    {/* Analysis Section */}
                    <div className="bg-slate-900/30 border border-slate-700/50 p-4 mb-3">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-blue-400 text-sm">📊</span>
                        <h4 className="text-blue-400 font-semibold text-sm uppercase tracking-wide">Analysis</h4>
                      </div>
                      <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-line">
                        {pick.analysis}
                      </p>
                    </div>

                    {/* Key Factors */}
                    {pick.key_factors && pick.key_factors.length > 0 && (
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-green-400 text-sm">✅</span>
                          <h4 className="text-green-400 font-semibold text-sm uppercase tracking-wide">Key Factors</h4>
                        </div>
                        <ul className="space-y-1">
                          {pick.key_factors.map((factor, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-slate-300 text-sm">
                              <span className="text-green-400 mt-0.5">•</span>
                              <span>{factor}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Edge Indicator */}
                    {pick.edge_percent !== null && pick.edge_percent > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-700/50">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-500">Projected Edge:</span>
                          <span className="text-green-400 font-bold text-sm">+{pick.edge_percent.toFixed(1)}%</span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {/* Footer Stats */}
                <div className="text-center text-slate-500 text-sm mt-6 pt-4 border-t border-slate-700">
                  Showing {picks.length} expert picks for {sports.find(s => s.key === selectedSport)?.name}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
