import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';

// Interfaces
interface BestPlay {
  id: string;
  sport: string;
  game_id: string;
  game_time: string;
  home_team: string;
  away_team: string;
  bet_type: string;
  market: string;
  market_line: number;
  model_prediction: number;
  model_name: string;
  model_confidence: number;
  edge: number;
  edge_percentage: number;
  recommendation: string;
  kelly_fraction: number;
  suggested_bet_size: string;
  probability: number;
  implied_probability?: number;
  is_pregame?: boolean;
  projection_type?: string;
  features_used: Record<string, any>;
  model_performance: Record<string, any>;
  consensus: {
    models_agree: number;
    models_total: number;
    strength: string;
  };
  score: number;
}

interface EdgeScannerResponse {
  total_plays: number;
  filters: {
    sport: string;
    min_edge: number;
    min_confidence: number;
    projection_type?: string;
  };
  plays: BestPlay[];
  generated_at: string;
}

interface SportInfo {
  id: string;
  name: string;
  models: number;
  active: boolean;
}

interface AvailableSportsResponse {
  sports: SportInfo[];
  total_models?: number;
}

type SortField = 'edge' | 'confidence' | 'kelly' | 'game_time' | 'consensus';
type SortDirection = 'asc' | 'desc';

// Tooltip Component
const Tooltip = ({ children, text }: { children: React.ReactNode; text: string }) => {
  const [show, setShow] = useState(false);

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
      >
        {children}
      </div>
      {show && (
        <div className="absolute z-[9999] top-full left-1/2 transform -translate-x-1/2 mt-2 px-3 py-2 bg-slate-900 border-2 border-blue-500 rounded-lg shadow-2xl whitespace-nowrap text-sm text-white min-w-max">
          {text}
          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-[-1px]">
            <div className="border-8 border-transparent border-b-blue-500"></div>
          </div>
        </div>
      )}
    </div>
  );
};

export function MaxEvEdges() {
  const [plays, setPlays] = useState<BestPlay[]>([]);
  const [availableSports, setAvailableSports] = useState<SportInfo[]>([]);
  const [totalModels, setTotalModels] = useState<number>(0);
  const [selectedSport, setSelectedSport] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [minEdge, setMinEdge] = useState(2.0);
  const [minConfidence, setMinConfidence] = useState(0.60);
  const [sortField, setSortField] = useState<SortField>('edge');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [searchQuery, setSearchQuery] = useState('');
  const [showingMockData, setShowingMockData] = useState(false);

  const sports = [
    { key: 'all', name: 'ALL', emoji: '🎯' },
    { key: 'nba', name: 'NBA', emoji: '🏀' },
    { key: 'ncaab', name: 'NCAAB', emoji: '🏀' },
    { key: 'nfl', name: 'NFL', emoji: '🏈' },
    { key: 'nhl', name: 'NHL', emoji: '🏒' },
    { key: 'mlb', name: 'MLB', emoji: '⚾' },
    { key: 'ncaaf', name: 'NCAAF', emoji: '🏈' },
  ];

  // Fetch available sports
  useEffect(() => {
    const fetchSports = async () => {
      try {
        const response = await fetch(getApiUrl('edge-scanner/sports'));
        const data: AvailableSportsResponse = await response.json();
        setAvailableSports(data.sports);
        setTotalModels(data.total_models || 60);
      } catch (error) {
        console.error('Error fetching sports:', error);
      }
    };
    fetchSports();
  }, []);

  // Fetch best plays
  useEffect(() => {
    const fetchBestPlays = async () => {
      try {
        setLoading(true);
        const params = new URLSearchParams({
          min_edge: minEdge.toString(),
          min_confidence: minConfidence.toString(),
          limit: '50',
          projection_type: 'pregame' // Only show pregame projections on this page
        });

        if (selectedSport !== 'all') {
          params.append('sport', selectedSport.toLowerCase());
        }

        const response = await fetch(getApiUrl(`edge-scanner/best-plays?${params.toString()}`));
        const data: EdgeScannerResponse = await response.json();
        setPlays(data.plays);

        // Detect if showing mock data (games from Nov 8, 2025)
        const isMock = data.plays.some(p => p.game_time.includes('2025-11-08'));
        setShowingMockData(isMock);

        setLoading(false);
      } catch (error) {
        console.error('Error fetching best plays:', error);
        setLoading(false);
      }
    };

    fetchBestPlays();
    const interval = setInterval(fetchBestPlays, 30000); // Auto-refresh every 30s
    return () => clearInterval(interval);
  }, [selectedSport, minEdge, minConfidence]);

  // Filter and sort plays
  const filteredPlays = plays
    .filter(play => {
      const matchesSearch =
        play.home_team.toLowerCase().includes(searchQuery.toLowerCase()) ||
        play.away_team.toLowerCase().includes(searchQuery.toLowerCase()) ||
        play.model_name.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesSearch;
    })
    .sort((a, b) => {
      let aVal: number, bVal: number;

      switch (sortField) {
        case 'edge':
          aVal = Math.abs(a.edge);
          bVal = Math.abs(b.edge);
          break;
        case 'confidence':
          aVal = a.model_confidence;
          bVal = b.model_confidence;
          break;
        case 'kelly':
          aVal = a.kelly_fraction;
          bVal = b.kelly_fraction;
          break;
        case 'game_time':
          aVal = new Date(a.game_time).getTime();
          bVal = new Date(b.game_time).getTime();
          break;
        case 'consensus':
          aVal = a.consensus.models_agree / a.consensus.models_total;
          bVal = b.consensus.models_agree / b.consensus.models_total;
          break;
        default:
          return 0;
      }

      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    });

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  // Sort indicator
  const SortIndicator = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null;
    return <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>;
  };

  // Format game time
  const formatGameTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMinutes = Math.floor((date.getTime() - now.getTime()) / 60000);

    if (diffMinutes < 60) {
      return `${diffMinutes}m`;
    } else if (diffMinutes < 1440) {
      return `${Math.floor(diffMinutes / 60)}h ${diffMinutes % 60}m`;
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
    }
  };

  // Consensus badge
  const ConsensusBadge = ({ consensus }: { consensus: { models_agree: number; models_total: number; strength: string } }) => {
    const configs: Record<string, { color: string }> = {
      STRONG: { color: 'text-emerald-400 bg-emerald-900/40 border-emerald-600' },
      MODERATE: { color: 'text-yellow-400 bg-yellow-900/40 border-yellow-600' },
      WEAK: { color: 'text-red-400 bg-red-900/40 border-red-600' }
    };
    const config = configs[consensus.strength] || configs.MODERATE;

    return (
      <span className={`px-2 py-1 rounded border text-xs font-semibold ${config.color}`}>
        {consensus.models_agree}/{consensus.models_total}
      </span>
    );
  };

  // Loading skeleton
  const LoadingSkeleton = () => (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black p-4" style={{ fontFamily: 'Rubik, sans-serif' }}>
      <div className="w-full mx-auto">
        <div className="mb-4 animate-pulse">
          <div className="h-10 w-96 bg-slate-700 rounded mb-2"></div>
          <div className="h-6 w-64 bg-slate-800 rounded"></div>
        </div>
        <div className="flex gap-4 mb-2">
          <div className="flex flex-col gap-2">
            {[...Array(7)].map((_, i) => (
              <div key={i} className="h-9 w-24 bg-slate-800 rounded animate-pulse"></div>
            ))}
          </div>
          <div className="flex-1">
            <div className="h-16 bg-slate-800/50 border border-slate-700 rounded-lg mb-3 animate-pulse"></div>
            <div className="bg-slate-900 border-2 border-slate-700 rounded-lg p-4">
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-16 bg-slate-800 rounded animate-pulse"></div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return <LoadingSkeleton />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black p-4" style={{ fontFamily: 'Rubik, sans-serif' }}>
      <div className="w-full mx-auto">
        {/* Header */}
        <div className="mb-4">
          <h1 className="text-4xl font-bold italic text-slate-100 mb-2" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>MAX EV MODEL EDGES</h1>
          <p className="text-slate-400 text-base">
            Live betting opportunities across <span className="text-blue-400 font-semibold">{totalModels} trained ML models</span> • Auto-refresh every 30s
          </p>
        </div>

        {/* Mock Data Banner */}
        {showingMockData && (
          <div className="mb-4 bg-yellow-900/40 border-2 border-yellow-600 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="text-2xl">ℹ️</div>
              <div className="flex-1">
                <div className="text-yellow-300 font-semibold mb-1">Demo Data (No Live Games)</div>
                <div className="text-yellow-200/80 text-sm">
                  Showing example predictions from {totalModels} trained models. Live predictions will appear when games are in progress.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Sport Tabs & Content */}
        <div className="flex gap-4 mb-2">
          {/* Sport Tabs - Vertical */}
          <div className="flex flex-col gap-2">
            {sports.map((sport) => {
              const sportInfo = availableSports.find(s => s.id === sport.key);
              const isActive = sportInfo?.active ?? true;

              return (
                <button
                  key={sport.key}
                  onClick={() => setSelectedSport(sport.key)}
                  disabled={!isActive && sport.key !== 'all'}
                  className={`px-3 py-1.5 text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-2 ${
                    selectedSport === sport.key
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                      : isActive || sport.key === 'all'
                      ? 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
                      : 'bg-slate-900 text-slate-600 border border-slate-800 cursor-not-allowed'
                  }`}
                >
                  <span className="text-sm">{sport.emoji}</span>
                  {sport.name}
                  {sportInfo && sport.key !== 'all' && (
                    <span className="text-xs opacity-70">({sportInfo.models})</span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Main Content */}
          <div className="flex-1">
            {/* Search and Filters */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-3 mb-3">
              <div className="flex gap-3 items-center flex-wrap">
                <input
                  type="text"
                  placeholder="Search teams or models..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1 min-w-[200px] px-3 py-1.5 bg-slate-900 border border-slate-600 rounded text-white text-sm"
                />
                <div className="flex gap-2 items-center">
                  <label className="text-slate-400 text-xs">Min Edge:</label>
                  <input
                    type="number"
                    value={minEdge}
                    onChange={(e) => setMinEdge(parseFloat(e.target.value))}
                    step="0.5"
                    min="0"
                    className="w-16 px-2 py-1 bg-slate-900 border border-slate-600 rounded text-white text-sm"
                  />
                </div>
                <div className="flex gap-2 items-center">
                  <label className="text-slate-400 text-xs">Min Confidence:</label>
                  <input
                    type="number"
                    value={minConfidence}
                    onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
                    step="0.05"
                    min="0"
                    max="1"
                    className="w-16 px-2 py-1 bg-slate-900 border border-slate-600 rounded text-white text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Plays Table */}
            {filteredPlays.length === 0 ? (
              <div className="bg-slate-900 border-2 border-slate-700 shadow-2xl rounded-lg p-12 text-center">
                <div className="text-6xl mb-4">🔍</div>
                <h3 className="text-2xl font-bold text-white mb-2">No plays found</h3>
                <p className="text-slate-400 text-lg mb-4">
                  {searchQuery ? (
                    <>No plays match your search query "{searchQuery}"</>
                  ) : (
                    <>No plays meet your current filter criteria</>
                  )}
                </p>
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setMinEdge(2.0);
                    setMinConfidence(0.60);
                  }}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded"
                >
                  Reset Filters
                </button>
              </div>
            ) : (
              <div className="bg-slate-900 border-2 border-slate-700 shadow-2xl rounded-lg overflow-visible">
                {/* Mobile scroll hint */}
                <div className="md:hidden bg-blue-900/40 border-b-2 border-blue-600 px-4 py-2 text-center">
                  <span className="text-blue-300 text-xs font-semibold">← Scroll horizontally to see all columns →</span>
                </div>
                <div className="overflow-x-auto overflow-y-visible">
                  <table className="w-full border-collapse min-w-[1400px]">
                    <thead className="bg-slate-800">
                      <tr>
                        <th className="text-left py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          <Tooltip text="Game matchup and start time">
                            <span className="cursor-help">Game</span>
                          </Tooltip>
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          Sport
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          <Tooltip text="Market type (Spreads, Totals, Moneyline)">
                            <span className="cursor-help">Bet Type</span>
                          </Tooltip>
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          <Tooltip text="Market line from sportsbook">
                            <span className="cursor-help">Line</span>
                          </Tooltip>
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          <Tooltip text="Model's predicted value">
                            <span className="cursor-help">Prediction</span>
                          </Tooltip>
                        </th>
                        <th
                          className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600 cursor-pointer hover:bg-slate-700 transition-colors"
                          onClick={() => toggleSort('edge')}
                        >
                          <Tooltip text="Your edge over the bookmaker in points/probability">
                            <span className="cursor-pointer">
                              Edge <SortIndicator field="edge" />
                            </span>
                          </Tooltip>
                        </th>
                        <th
                          className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600 cursor-pointer hover:bg-slate-700 transition-colors"
                          onClick={() => toggleSort('confidence')}
                        >
                          <Tooltip text="Model confidence (0-1)">
                            <span className="cursor-pointer">
                              Confidence <SortIndicator field="confidence" />
                            </span>
                          </Tooltip>
                        </th>
                        <th
                          className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600 cursor-pointer hover:bg-slate-700 transition-colors"
                          onClick={() => toggleSort('kelly')}
                        >
                          <Tooltip text="Recommended bet size using Kelly Criterion">
                            <span className="cursor-pointer">
                              Kelly <SortIndicator field="kelly" />
                            </span>
                          </Tooltip>
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          <Tooltip text="ML model used for prediction">
                            <span className="cursor-help">Model</span>
                          </Tooltip>
                        </th>
                        <th
                          className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-b-2 border-slate-600 cursor-pointer hover:bg-slate-700 transition-colors"
                          onClick={() => toggleSort('consensus')}
                        >
                          <Tooltip text="How many models agree on this play">
                            <span className="cursor-pointer">
                              Consensus <SortIndicator field="consensus" />
                            </span>
                          </Tooltip>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredPlays.map((play, idx) => {
                        return (
                          <tr
                            key={play.id}
                            className={`hover:bg-slate-800/70 hover:shadow-lg hover:scale-[1.01] transition-all duration-200 ${
                              idx < filteredPlays.length - 1 ? 'border-b border-slate-700' : ''
                            }`}
                          >
                            <td className="py-3 px-3 border-r border-slate-600">
                              <div className="text-white font-semibold text-sm">
                                {play.away_team} @ {play.home_team}
                              </div>
                              <div className="text-slate-400 text-xs mt-0.5">
                                {formatGameTime(play.game_time)}
                              </div>
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              <span className="px-2 py-0.5 bg-slate-700 text-slate-300 text-xs rounded font-semibold">
                                {play.sport}
                              </span>
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              <span className="text-slate-300 text-sm">{play.bet_type}</span>
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              <div className="text-white font-semibold text-base">
                                {play.market_line > 0 ? '+' : ''}{play.market_line}
                              </div>
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              <div className="text-blue-400 font-semibold text-base">
                                {play.model_prediction.toFixed(1)}
                              </div>
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              <div className="text-green-400 font-bold text-lg">
                                {play.edge > 0 ? '+' : ''}{play.edge.toFixed(1)}
                              </div>
                              <div className="text-green-300 text-xs">
                                ({play.edge_percentage.toFixed(1)}%)
                              </div>
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              <div className="text-white font-semibold text-base">
                                {(play.model_confidence * 100).toFixed(0)}%
                              </div>
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              <div className="text-amber-400 font-bold text-base">
                                {(play.kelly_fraction * 100).toFixed(1)}%
                              </div>
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              <span className="text-slate-300 text-xs">{play.model_name}</span>
                            </td>
                            <td className="py-3 px-3 text-center">
                              <ConsensusBadge consensus={play.consensus} />
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Stats Footer */}
            <div className="mt-4 text-center text-slate-500 text-base">
              Showing {filteredPlays.length} plays
              {selectedSport !== 'all' && ` for ${sports.find(s => s.key === selectedSport)?.name}`}
              {plays.length > 0 && ` • Updated ${new Date().toLocaleTimeString()}`}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
