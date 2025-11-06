import { useEffect, useState } from 'react';
import { OddsMetricsDashboard } from '../components/OddsMetricsDashboard';
import { BetTypePerformance } from '../components/BetTypePerformance';

interface PlayerProp {
  event_id: string;
  home_team: string;
  away_team: string;
  commence_time: string;
  player_name: string;
  prop_type: string;
  line: number;
  odds: number;
  bookmaker: string;
  last_update: string;
}

// Advanced Props with Edges interfaces
interface BookmakerOdds {
  bookmaker: string;
  over_odds: number | null;
  under_odds: number | null;
}

interface PlayerPropOdds {
  player_name: string;
  prop_type: string;
  line: number;
  bookmakers: BookmakerOdds[];
  best_over_odds: number | null;
  best_under_odds: number | null;
  best_over_book: string | null;
  best_under_book: string | null;
}

interface ProjectionFactors {
  baseline: number;
  recent_avg: number;
  trend: string;
  matchup_adjustment: number;
  pace_adjustment: number;
  total_adjustment: number;
}

interface PlayerPropProjection {
  prop_type: string;
  projection: number;
  confidence: string;
  confidence_score: number;
  factors: ProjectionFactors;
  reasoning: string;
}

interface PlayerPropEdge {
  edge: number;
  edge_pct: number;
  recommendation: string | null;
  bet_strength: string | null;
}

interface PlayerPropWithEdge {
  player_name: string;
  team: string;
  opponent: string | null;
  game_time: string;
  prop_type: string;
  market_odds: PlayerPropOdds;
  projection: PlayerPropProjection;
  edge: PlayerPropEdge;
}

interface PlayerPropsGame {
  event_id: string;
  sport_key: string;
  home_team: string;
  away_team: string;
  commence_time: string;
  props: PlayerPropWithEdge[];
}

interface PlayerPropsResponse {
  games: PlayerPropsGame[];
  total_props: number;
  total_strong_bets: number;
  total_moderate_bets: number;
  last_updated: string;
}

interface GroupedProp {
  player_name: string;
  prop_type: string;
  line: number;
  game: string;
  commence_time: string;
  bookmakers: {
    [bookmaker: string]: {
      over?: number;
      under?: number;
    };
  };
  best_over?: { bookmaker: string; odds: number };
  best_under?: { bookmaker: string; odds: number };
}

export function Props() {
  const [viewMode, setViewMode] = useState<'all' | 'edges'>('all');
  const [selectedSport, setSelectedSport] = useState<string>('nba');
  const [props, setProps] = useState<PlayerProp[]>([]);
  const [groupedProps, setGroupedProps] = useState<GroupedProp[]>([]);
  const [edgeProps, setEdgeProps] = useState<PlayerPropsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPropType, setSelectedPropType] = useState<string>('all');
  const [minEdge, setMinEdge] = useState<number>(5.0);

  const sports = [
    { key: 'nba', name: 'NBA', emoji: '🏀' },
    { key: 'nfl', name: 'NFL', emoji: '🏈' },
    { key: 'nhl', name: 'NHL', emoji: '🏒' },
    { key: 'mlb', name: 'MLB', emoji: '⚾' },
    { key: 'ncaab', name: 'NCAAB', emoji: '🏀' },
    { key: 'ncaaf', name: 'NCAAF', emoji: '🏈' }
  ];

  // Fetch props data (basic view)
  useEffect(() => {
    if (viewMode !== 'all') return;

    const fetchProps = async () => {
      setLoading(true);
      try {
        const response = await fetch(`/api/props/${selectedSport}`);
        if (response.ok) {
          const data = await response.json();
          setProps(data.props || []);
        }
      } catch (error) {
        console.error('Error fetching props:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchProps();
    const interval = setInterval(fetchProps, 60000); // Refresh every minute

    return () => clearInterval(interval);
  }, [selectedSport, viewMode]);

  // Fetch advanced props with edges (edges view)
  useEffect(() => {
    if (viewMode !== 'edges') return;
    if (selectedSport !== 'nba') return; // Only NBA supported for now

    const fetchEdgeProps = async () => {
      setLoading(true);
      try {
        const response = await fetch(`/api/player-props/nba/edges?min_edge_pct=${minEdge}`);
        if (response.ok) {
          const data: PlayerPropsResponse = await response.json();
          setEdgeProps(data);
        }
      } catch (error) {
        console.error('Error fetching edge props:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchEdgeProps();
    const interval = setInterval(fetchEdgeProps, 120000); // Refresh every 2 minutes (slower since this is more expensive)

    return () => clearInterval(interval);
  }, [selectedSport, viewMode, minEdge]);

  // Group props by player + prop type + line
  useEffect(() => {
    const grouped: { [key: string]: GroupedProp } = {};

    props.forEach((prop) => {
      const key = `${prop.player_name}-${prop.prop_type}-${prop.line}`;

      if (!grouped[key]) {
        grouped[key] = {
          player_name: prop.player_name,
          prop_type: prop.prop_type,
          line: prop.line,
          game: `${prop.away_team} @ ${prop.home_team}`,
          commence_time: prop.commence_time,
          bookmakers: {}
        };
      }

      // Determine if this is over or under
      const isOver = prop.odds > 0 || prop.player_name.includes('Over');
      const isUnder = prop.odds < 0 || prop.player_name.includes('Under');

      if (!grouped[key].bookmakers[prop.bookmaker]) {
        grouped[key].bookmakers[prop.bookmaker] = {};
      }

      if (isOver) {
        grouped[key].bookmakers[prop.bookmaker].over = prop.odds;
      } else if (isUnder) {
        grouped[key].bookmakers[prop.bookmaker].under = prop.odds;
      } else {
        // If we can't determine, assign based on odds value
        if (!grouped[key].bookmakers[prop.bookmaker].over) {
          grouped[key].bookmakers[prop.bookmaker].over = prop.odds;
        } else {
          grouped[key].bookmakers[prop.bookmaker].under = prop.odds;
        }
      }
    });

    // Calculate best odds for each prop
    Object.values(grouped).forEach((prop) => {
      let bestOverOdds = -Infinity;
      let bestOverBook = '';
      let bestUnderOdds = -Infinity;
      let bestUnderBook = '';

      Object.entries(prop.bookmakers).forEach(([bookmaker, odds]) => {
        if (odds.over && odds.over > bestOverOdds) {
          bestOverOdds = odds.over;
          bestOverBook = bookmaker;
        }
        if (odds.under && odds.under > bestUnderOdds) {
          bestUnderOdds = odds.under;
          bestUnderBook = bookmaker;
        }
      });

      if (bestOverBook) {
        prop.best_over = { bookmaker: bestOverBook, odds: bestOverOdds };
      }
      if (bestUnderBook) {
        prop.best_under = { bookmaker: bestUnderBook, odds: bestUnderOdds };
      }
    });

    setGroupedProps(Object.values(grouped));
  }, [props]);

  // Filter props
  const filteredProps = groupedProps.filter((prop) => {
    const matchesSearch = prop.player_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesPropType = selectedPropType === 'all' || prop.prop_type === selectedPropType;
    return matchesSearch && matchesPropType;
  });

  // Get unique prop types for filter
  const propTypes = Array.from(new Set(props.map(p => p.prop_type)));

  // Format prop type for display
  const formatPropType = (type: string) => {
    return type.replace('player_', '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  // Format odds display
  const formatOdds = (odds: number) => {
    return odds > 0 ? `+${odds}` : `${odds}`;
  };


  const allBookmakers = Array.from(
    new Set(props.map(p => p.bookmaker))
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black p-4" style={{ fontFamily: 'Rubik, sans-serif' }}>
      <div className="w-full mx-auto">
        {/* Header with Prop Type Selector and View Mode */}
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-100 mb-2">Player Props</h1>
            <p className="text-slate-400 text-sm">
              {viewMode === 'all'
                ? 'Compare player prop odds across multiple sportsbooks'
                : 'Advanced projections with edge analysis and betting recommendations'}
            </p>
            {viewMode === 'edges' && selectedSport !== 'nba' && (
              <div className="mt-2 bg-amber-900/20 border border-amber-700 p-2 text-amber-400 text-xs">
                ⚠️ Edge analysis is currently only available for NBA. Select NBA to view advanced props.
              </div>
            )}
          </div>

          <div className="flex gap-2">
            {/* Prop Type Selector */}
            {viewMode === 'all' && (
              <div className="flex gap-1 bg-slate-900 p-1 border border-slate-700">
                <button
                  onClick={() => setSelectedPropType('all')}
                  className={`px-4 py-1.5 text-xs font-semibold transition-all ${
                    selectedPropType === 'all'
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  All Props
                </button>
                {propTypes.slice(0, 5).map((type) => (
                  <button
                    key={type}
                    onClick={() => setSelectedPropType(type)}
                    className={`px-4 py-1.5 text-xs font-semibold transition-all whitespace-nowrap ${
                      selectedPropType === type
                        ? 'bg-blue-600 text-white shadow-md'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {formatPropType(type).split(' ').slice(0, 2).join(' ')}
                  </button>
                ))}
              </div>
            )}

            {/* View Mode Toggle */}
            <div className="flex gap-1 bg-slate-900 p-1 border border-slate-700">
              <button
                onClick={() => setViewMode('all')}
                className={`px-4 py-1.5 text-xs font-semibold transition-all ${
                  viewMode === 'all'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                All Props
              </button>
              <button
                onClick={() => setViewMode('edges')}
                className={`px-4 py-1.5 text-xs font-semibold transition-all ${
                  viewMode === 'edges'
                    ? 'bg-green-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                🎯 Edges
              </button>
            </div>
          </div>
        </div>

        {/* Sport Tabs & Metrics Dashboard - Side by Side */}
        <div className="flex gap-4 mb-2">
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

            {/* User Bet Type Performance Section */}
            <div className="mb-6">
              <BetTypePerformance sport={selectedSport.toUpperCase()} />
            </div>

        {/* Search Filter - Compact */}
        <div className="bg-slate-800/50 border border-slate-700 p-2 mb-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by player name..."
            className="w-full bg-slate-900 border border-slate-700 px-2 py-1.5 text-white text-xs placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* RENDER: Edge Props View */}
        {viewMode === 'edges' ? (
          <>
            {/* Edge Filter */}
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-4">
                <label className="text-sm font-medium text-slate-300">Minimum Edge %:</label>
                <input
                  type="number"
                  value={minEdge}
                  onChange={(e) => setMinEdge(parseFloat(e.target.value) || 5.0)}
                  className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white w-24 focus:outline-none focus:border-blue-500"
                  min="0"
                  max="50"
                  step="0.5"
                />
                <span className="text-slate-500 text-sm">Show props with at least {minEdge}% edge</span>
              </div>
            </div>

            {loading ? (
              <div className="text-center text-white text-xl py-12">
                Loading edge analysis...
              </div>
            ) : !edgeProps || edgeProps.total_props === 0 ? (
              <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-12 text-center">
                <div className="text-slate-400 text-lg mb-2">No props with edges found</div>
                <div className="text-slate-500 text-sm">
                  Try lowering the minimum edge threshold or check back later
                </div>
              </div>
            ) : (
              <>
                {/* Stats Summary */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border border-blue-700 rounded-lg p-4">
                    <div className="text-blue-400 text-sm font-medium mb-1">Total Props</div>
                    <div className="text-white text-3xl font-bold">{edgeProps.total_props}</div>
                  </div>
                  <div className="bg-gradient-to-br from-green-900/50 to-green-800/30 border border-green-700 rounded-lg p-4">
                    <div className="text-green-400 text-sm font-medium mb-1">Strong Bets</div>
                    <div className="text-white text-3xl font-bold">{edgeProps.total_strong_bets}</div>
                  </div>
                  <div className="bg-gradient-to-br from-yellow-900/50 to-yellow-800/30 border border-yellow-700 rounded-lg p-4">
                    <div className="text-yellow-400 text-sm font-medium mb-1">Moderate Bets</div>
                    <div className="text-white text-3xl font-bold">{edgeProps.total_moderate_bets}</div>
                  </div>
                  <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border border-purple-700 rounded-lg p-4">
                    <div className="text-purple-400 text-sm font-medium mb-1">Games Analyzed</div>
                    <div className="text-white text-3xl font-bold">{edgeProps.games.length}</div>
                  </div>
                </div>

                {/* Props with Edges */}
                <div className="space-y-6">
                  {edgeProps.games.map((game) => (
                    <div key={game.event_id} className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg overflow-hidden">
                      {/* Game Header */}
                      <div className="bg-slate-900/80 px-6 py-3 border-b border-slate-700">
                        <div className="flex items-center justify-between">
                          <div className="text-white font-bold text-lg">{game.away_team} @ {game.home_team}</div>
                          <div className="text-slate-400 text-sm">{new Date(game.commence_time).toLocaleString()}</div>
                        </div>
                      </div>

                      {/* Props */}
                      <div className="divide-y divide-slate-700/50">
                        {game.props.map((prop, idx) => (
                          <div key={idx} className="p-6 hover:bg-slate-700/20 transition-colors">
                            {/* Player Info */}
                            <div className="flex items-start justify-between mb-4">
                              <div>
                                <h3 className="text-white font-bold text-xl mb-1">{prop.player_name}</h3>
                                <div className="flex items-center gap-3 text-slate-400 text-sm">
                                  <span>{prop.team}</span>
                                  {prop.opponent && <span>vs {prop.opponent}</span>}
                                  <span>•</span>
                                  <span className="font-semibold text-white">{formatPropType(prop.prop_type)}</span>
                                </div>
                              </div>

                              {/* Recommendation Badge */}
                              {prop.edge.recommendation && (
                                <div className={`px-4 py-2 rounded-lg font-bold text-sm ${
                                  prop.edge.bet_strength === 'STRONG'
                                    ? 'bg-green-900/50 text-green-400 border-2 border-green-700 shadow-lg shadow-green-900/50'
                                    : prop.edge.bet_strength === 'MODERATE'
                                    ? 'bg-yellow-900/50 text-yellow-400 border-2 border-yellow-700'
                                    : 'bg-blue-900/50 text-blue-400 border-2 border-blue-700'
                                }`}>
                                  {prop.edge.bet_strength} {prop.edge.recommendation}
                                </div>
                              )}
                            </div>

                            {/* Key Stats Row */}
                            <div className="grid grid-cols-4 gap-4 mb-4">
                              <div className="bg-slate-900/50 rounded-lg p-3">
                                <div className="text-slate-500 text-xs mb-1">Market Line</div>
                                <div className="text-white font-bold text-2xl">{prop.market_odds.line}</div>
                              </div>
                              <div className="bg-slate-900/50 rounded-lg p-3">
                                <div className="text-slate-500 text-xs mb-1">Our Projection</div>
                                <div className="text-blue-400 font-bold text-2xl">{prop.projection.projection}</div>
                              </div>
                              <div className="bg-slate-900/50 rounded-lg p-3">
                                <div className="text-slate-500 text-xs mb-1">Edge</div>
                                <div className={`font-bold text-2xl ${prop.edge.edge > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                  {prop.edge.edge > 0 ? '+' : ''}{prop.edge.edge} ({prop.edge.edge_pct > 0 ? '+' : ''}{prop.edge.edge_pct.toFixed(1)}%)
                                </div>
                              </div>
                              <div className="bg-slate-900/50 rounded-lg p-3">
                                <div className="text-slate-500 text-xs mb-1">Confidence</div>
                                <div className={`font-bold text-xl ${
                                  prop.projection.confidence === 'HIGH' ? 'text-green-400' :
                                  prop.projection.confidence === 'MEDIUM' ? 'text-yellow-400' : 'text-slate-400'
                                }`}>
                                  {prop.projection.confidence} ({(prop.projection.confidence_score * 100).toFixed(0)}%)
                                </div>
                              </div>
                            </div>

                            {/* Projection Factors */}
                            <div className="bg-slate-900/30 rounded-lg p-4 mb-4">
                              <div className="text-slate-400 text-xs font-semibold mb-2 uppercase">Projection Breakdown</div>
                              <div className="grid grid-cols-3 gap-3 text-sm">
                                <div>
                                  <span className="text-slate-500">Baseline:</span>
                                  <span className="text-white ml-2 font-semibold">{prop.projection.factors.baseline}</span>
                                </div>
                                <div>
                                  <span className="text-slate-500">Recent Avg:</span>
                                  <span className="text-white ml-2 font-semibold">{prop.projection.factors.recent_avg}</span>
                                </div>
                                <div>
                                  <span className="text-slate-500">Trend:</span>
                                  <span className={`ml-2 font-semibold ${
                                    prop.projection.factors.trend === 'increasing' ? 'text-green-400' :
                                    prop.projection.factors.trend === 'decreasing' ? 'text-red-400' : 'text-slate-400'
                                  }`}>
                                    {prop.projection.factors.trend === 'increasing' ? '↗️ UP' :
                                     prop.projection.factors.trend === 'decreasing' ? '↘️ DOWN' : '→ STABLE'}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-slate-500">Matchup Adj:</span>
                                  <span className="text-white ml-2 font-semibold">
                                    {prop.projection.factors.matchup_adjustment > 0 ? '+' : ''}{prop.projection.factors.matchup_adjustment.toFixed(2)}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-slate-500">Pace Adj:</span>
                                  <span className="text-white ml-2 font-semibold">
                                    {prop.projection.factors.pace_adjustment > 0 ? '+' : ''}{prop.projection.factors.pace_adjustment.toFixed(2)}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-slate-500">Total Adj:</span>
                                  <span className="text-white ml-2 font-semibold">
                                    {prop.projection.factors.total_adjustment > 0 ? '+' : ''}{prop.projection.factors.total_adjustment.toFixed(2)}
                                  </span>
                                </div>
                              </div>
                            </div>

                            {/* Reasoning */}
                            <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-3 mb-4">
                              <div className="text-blue-400 text-xs font-semibold mb-1">💡 Analysis</div>
                              <div className="text-slate-300 text-sm">{prop.projection.reasoning}</div>
                            </div>

                            {/* Best Odds */}
                            <div className="flex items-center gap-3">
                              <div className="text-slate-500 text-sm font-medium">Best Odds:</div>
                              {prop.market_odds.best_over_odds && (
                                <div className="bg-green-900/30 border border-green-700 rounded-lg px-3 py-1">
                                  <span className="text-green-400 text-sm font-semibold">
                                    Over {formatOdds(prop.market_odds.best_over_odds)} @ {prop.market_odds.best_over_book}
                                  </span>
                                </div>
                              )}
                              {prop.market_odds.best_under_odds && (
                                <div className="bg-blue-900/30 border border-blue-700 rounded-lg px-3 py-1">
                                  <span className="text-blue-400 text-sm font-semibold">
                                    Under {formatOdds(prop.market_odds.best_under_odds)} @ {prop.market_odds.best_under_book}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Last Updated */}
                <div className="mt-6 text-center text-slate-500 text-sm">
                  Last updated: {new Date(edgeProps.last_updated).toLocaleString()}
                </div>
              </>
            )}
          </>
        ) : (
          /* RENDER: Basic Props Table View */
          <>
            {/* Props Table */}
            {loading ? (
              <div className="text-center text-white text-xl py-12">
                Loading props...
              </div>
            ) : filteredProps.length === 0 ? (
          <div className="bg-slate-800/50 border border-slate-700 p-12 text-center">
            <div className="text-slate-400 text-lg mb-2">No props available</div>
            <div className="text-slate-500 text-sm">
              {searchQuery ? 'Try adjusting your search filters' : 'Check back later for updated props'}
            </div>
          </div>
        ) : (
          <div className="bg-slate-900 overflow-hidden border-2 border-slate-700 shadow-2xl">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead className="bg-slate-800">
                  <tr>
                    <th className="text-left py-2 px-1 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600 w-[100px]">
                      Player
                    </th>
                    <th className="text-left py-2 px-1 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600 w-[90px]">
                      Prop
                    </th>
                    <th className="text-center py-2 px-1 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600 w-[50px]">
                      Line
                    </th>
                    <th className="text-left py-2 px-1 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600 w-[110px]">
                      Game
                    </th>
                    {allBookmakers.slice(0, 5).map((bookmaker, index) => (
                      <th key={bookmaker} className={`text-center py-2 px-1 text-slate-300 font-bold text-xs uppercase tracking-wider border-b-2 border-slate-600 w-[70px] ${
                        index < allBookmakers.slice(0, 5).length - 1 ? 'border-r border-slate-600' : ''
                      }`}>
                        {bookmaker}
                      </th>
                    ))}
                    <th className="text-center py-2 px-1 text-slate-300 font-bold text-xs uppercase tracking-wider border-b-2 border-slate-600 w-[70px]">
                      Best
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredProps.map((prop, idx) => (
                    <tr
                      key={idx}
                      className={`hover:bg-slate-800/30 transition-colors ${
                        idx < filteredProps.length - 1 ? 'border-b border-slate-700' : ''
                      }`}
                    >
                      <td className="py-0.5 px-1 border-r border-slate-600 w-[100px]">
                        <span className="text-white font-semibold text-xs truncate block">{prop.player_name}</span>
                      </td>
                      <td className="py-0.5 px-1 border-r border-slate-600 w-[90px]">
                        <span className="text-slate-300 text-xs truncate block">{formatPropType(prop.prop_type)}</span>
                      </td>
                      <td className="py-0.5 px-1 text-center border-r border-slate-600 w-[50px]">
                        <span className="text-white font-bold text-sm">{prop.line}</span>
                      </td>
                      <td className="py-0.5 px-1 border-r border-slate-600 w-[110px]">
                        <div className="text-slate-300 text-[10px] truncate">{prop.game}</div>
                        <div className="text-slate-500 text-[9px] truncate">
                          {new Date(prop.commence_time).toLocaleString()}
                        </div>
                      </td>
                      {allBookmakers.slice(0, 5).map((bookmaker, bookIndex) => (
                        <td key={bookmaker} className={`py-0.5 px-1 text-center ${
                          bookIndex < allBookmakers.slice(0, 5).length - 1 ? 'border-r border-slate-700' : ''
                        }`}>
                          <div className="space-y-0.5">
                            {prop.bookmakers[bookmaker]?.over && (
                              <div className={`text-center px-1 py-0.5 text-xs font-semibold ${
                                prop.best_over?.bookmaker === bookmaker
                                  ? 'bg-green-900/30 text-green-400'
                                  : 'text-slate-300'
                              }`}>
                                O {formatOdds(prop.bookmakers[bookmaker].over!)}
                              </div>
                            )}
                            {prop.bookmakers[bookmaker]?.under && (
                              <div className={`text-center px-1 py-0.5 text-xs font-semibold ${
                                prop.best_under?.bookmaker === bookmaker
                                  ? 'bg-blue-900/30 text-blue-400'
                                  : 'text-slate-300'
                              }`}>
                                U {formatOdds(prop.bookmakers[bookmaker].under!)}
                              </div>
                            )}
                          </div>
                        </td>
                      ))}
                      <td className="py-0.5 px-1">
                        <div className="space-y-0.5">
                          {prop.best_over && (
                            <div className="text-center px-1 py-0.5 text-xs font-bold bg-green-900/50 text-green-400">
                              O {formatOdds(prop.best_over.odds)}
                            </div>
                          )}
                          {prop.best_under && (
                            <div className="text-center px-1 py-0.5 text-xs font-bold bg-blue-900/50 text-blue-400">
                              U {formatOdds(prop.best_under.odds)}
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

            {/* Stats Footer */}
            <div className="mt-6 text-center text-slate-500 text-sm">
              Showing {filteredProps.length} props from {allBookmakers.length} sportsbooks
            </div>
          </>
        )}

          </div>
        </div>
      </div>
    </div>
  );
}
