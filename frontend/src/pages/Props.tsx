import { useEffect, useState } from 'react';
import { OddsMetricsDashboard } from '../components/OddsMetricsDashboard';
import { BetTypePerformance } from '../components/BetTypePerformance';
import { getApiUrl } from '../config';
import { TierGate } from '../components/TierGate';

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

// ML Props API Response (simpler structure)
interface MLPlayerProp {
  player_name: string;
  team: string;
  opponent: string;
  home_away: string;
  prop_type: string;
  market_line: number;
  predicted_value: number;
  edge: number;
  edge_pct: number;
  recommendation: 'OVER' | 'UNDER';
  confidence: number;
  over_odds: number | null;
  under_odds: number | null;
  bookmaker: string;
  models_used: string[];
  date: string;
}

interface MLPropsResponse {
  date: string;
  time_generated: string;
  total_props_analyzed: number;
  props_with_edge: number;
  min_edge_pct: number;
  props: MLPlayerProp[];
}

interface GroupedProp {
  player_name: string;
  prop_type: string;
  line: number;
  game: string;
  home_team: string;
  away_team: string;
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

interface CorrelatedCombo {
  combo_id: string;
  sport: string;
  num_legs: number;
  props: Array<{
    player_name: string;
    prop_type: string;
    line: number;
    direction: string;
    display_line: string;
  }>;
  payout_multiplier: string;
  edge: number;
  display_edge: string;
  confidence: string;
  confidence_color: string;
  recommendation: string;
  score: number;
  display_score: string;
  is_demon_mode: boolean;
  is_goblin_mode: boolean;
}

interface CombosResponse {
  combos: CorrelatedCombo[];
  count: number;
  stats: {
    total_combos: number;
    demon_mode: number;
    goblin_mode: number;
    normal: number;
  };
}

export function Props() {
  const [viewMode, setViewMode] = useState<'all' | 'edges' | 'crusher'>('all');
  const [selectedSport, setSelectedSport] = useState<string>('nba');
  const [props, setProps] = useState<PlayerProp[]>([]);
  const [groupedProps, setGroupedProps] = useState<GroupedProp[]>([]);
  const [edgeProps, setEdgeProps] = useState<MLPropsResponse | null>(null);
  const [combos, setCombos] = useState<CombosResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPropType, setSelectedPropType] = useState<string>('all');
  const [minEdge, setMinEdge] = useState<number>(5.0);
  const [minLegs, setMinLegs] = useState<number>(2);
  const [maxLegs, setMaxLegs] = useState<number>(6);
  const [demonModeOnly, setDemonModeOnly] = useState<boolean>(false);

  const sports = [
    { key: 'nba', name: 'NBA', emoji: '🏀' },
    { key: 'nfl', name: 'NFL', emoji: '🏈' },
    { key: 'nhl', name: 'NHL', emoji: '🏒' },
    { key: 'mlb', name: 'MLB', emoji: '⚾' },
    { key: 'ncaab', name: 'NCAAB', emoji: '🏀' },
    { key: 'ncaaf', name: 'NCAAF', emoji: '🏈' }
  ];

  // UNIFIED: Fetch props with edges from /api/ui/props-edges for ALL modes
  useEffect(() => {
    const fetchEdgeProps = async () => {
      setLoading(true);
      try {
        // Unified UI endpoint with all filters
        const params = new URLSearchParams({
          sport: selectedSport,
          min_edge: minEdge.toString(),
          view_mode: viewMode
        });

        const response = await fetch(getApiUrl(`ui/props-edges?${params.toString()}`));
        if (response.ok) {
          const rawData = await response.json();
          // Handle both old format {props: []} and new format {edges: []}
          const data: MLPropsResponse = {
            date: rawData.date || rawData.generated_at,
            time_generated: rawData.generated_at || new Date().toISOString(),
            total_props_analyzed: rawData.total || 0,
            props_with_edge: rawData.total || 0,
            min_edge_pct: rawData.filters?.min_edge || minEdge,
            props: rawData.edges || rawData.props || []
          };
          setEdgeProps(data);
        }
      } catch (error) {
        console.error('Error fetching edge props:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchEdgeProps();
    const interval = setInterval(fetchEdgeProps, 120000); // Refresh every 2 minutes

    return () => clearInterval(interval);
  }, [selectedSport, viewMode, minEdge]);

  // Fetch correlated combos for DFS Crusher mode
  useEffect(() => {
    if (viewMode !== 'crusher') return;

    const fetchCombos = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({
          sport: selectedSport,
          min_legs: minLegs.toString(),
          max_legs: maxLegs.toString(),
          demon_mode_only: demonModeOnly.toString(),
          limit: '50'
        });

        const response = await fetch(getApiUrl(`ui/dfs-combos?${params.toString()}`));
        if (response.ok) {
          const data: CombosResponse = await response.json();
          setCombos(data);
        }
      } catch (error) {
        console.error('Error fetching combos:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCombos();
    const interval = setInterval(fetchCombos, 180000); // Refresh every 3 minutes

    return () => clearInterval(interval);
  }, [selectedSport, viewMode, minLegs, maxLegs, demonModeOnly]);



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
          home_team: prop.home_team,
          away_team: prop.away_team,
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

  // Filter props - use edgeProps directly for both modes
  const filteredPropsFromAPI = (edgeProps?.props || []).filter((prop) => {
    const matchesSearch = prop.player_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesPropType = selectedPropType === 'all' || prop.prop_type === selectedPropType;
    return matchesSearch && matchesPropType;
  });

  // Keep old groupedProps for backwards compatibility (not used anymore)
  const filteredProps = groupedProps.filter((prop) => {
    const matchesSearch = prop.player_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesPropType = selectedPropType === 'all' || prop.prop_type === selectedPropType;
    return matchesSearch && matchesPropType;
  });

  // Get unique prop types for filter
  const propTypes = Array.from(new Set((edgeProps?.props || []).map(p => p.prop_type)));

  // Format prop type for display
  const formatPropType = (type: string) => {
    return type.replace('player_', '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  // Format odds display
  const formatOdds = (odds: number) => {
    return odds > 0 ? `+${odds}` : `${odds}`;
  };

  // Extract team abbreviation from full team name
  const getTeamAbbrev = (teamName: string): string => {
    // Common team name mappings for abbreviations
    const abbrevMap: { [key: string]: string } = {
      // NBA
      'Los Angeles Lakers': 'LAL',
      'Los Angeles Clippers': 'LAC',
      'Golden State Warriors': 'GSW',
      'Phoenix Suns': 'PHX',
      'Sacramento Kings': 'SAC',
      'Dallas Mavericks': 'DAL',
      'Houston Rockets': 'HOU',
      'Memphis Grizzlies': 'MEM',
      'New Orleans Pelicans': 'NOP',
      'San Antonio Spurs': 'SAS',
      'Denver Nuggets': 'DEN',
      'Minnesota Timberwolves': 'MIN',
      'Oklahoma City Thunder': 'OKC',
      'Portland Trail Blazers': 'POR',
      'Utah Jazz': 'UTA',
      'Boston Celtics': 'BOS',
      'Brooklyn Nets': 'BKN',
      'New York Knicks': 'NYK',
      'Philadelphia 76ers': 'PHI',
      'Toronto Raptors': 'TOR',
      'Chicago Bulls': 'CHI',
      'Cleveland Cavaliers': 'CLE',
      'Detroit Pistons': 'DET',
      'Indiana Pacers': 'IND',
      'Milwaukee Bucks': 'MIL',
      'Atlanta Hawks': 'ATL',
      'Charlotte Hornets': 'CHA',
      'Miami Heat': 'MIA',
      'Orlando Magic': 'ORL',
      'Washington Wizards': 'WAS',
      // NFL
      'Arizona Cardinals': 'ARI',
      'Atlanta Falcons': 'ATL',
      'Baltimore Ravens': 'BAL',
      'Buffalo Bills': 'BUF',
      'Carolina Panthers': 'CAR',
      'Chicago Bears': 'CHI',
      'Cincinnati Bengals': 'CIN',
      'Cleveland Browns': 'CLE',
      'Dallas Cowboys': 'DAL',
      'Denver Broncos': 'DEN',
      'Detroit Lions': 'DET',
      'Green Bay Packers': 'GB',
      'Houston Texans': 'HOU',
      'Indianapolis Colts': 'IND',
      'Jacksonville Jaguars': 'JAX',
      'Kansas City Chiefs': 'KC',
      'Las Vegas Raiders': 'LV',
      'Los Angeles Chargers': 'LAC',
      'Los Angeles Rams': 'LAR',
      'Miami Dolphins': 'MIA',
      'Minnesota Vikings': 'MIN',
      'New England Patriots': 'NE',
      'New Orleans Saints': 'NO',
      'New York Giants': 'NYG',
      'New York Jets': 'NYJ',
      'Philadelphia Eagles': 'PHI',
      'Pittsburgh Steelers': 'PIT',
      'San Francisco 49ers': 'SF',
      'Seattle Seahawks': 'SEA',
      'Tampa Bay Buccaneers': 'TB',
      'Tennessee Titans': 'TEN',
      'Washington Commanders': 'WAS',
    };

    // Check if we have a direct mapping
    if (abbrevMap[teamName]) {
      return abbrevMap[teamName];
    }

    // Fallback: create abbreviation from first letters of each word
    const words = teamName.split(' ').filter(word =>
      !['the', 'of', 'and'].includes(word.toLowerCase())
    );
    if (words.length >= 2) {
      // Take first letter of last word and first letter(s) of first word
      const lastWord = words[words.length - 1];
      const firstWord = words[0];
      return (firstWord.substring(0, 2) + lastWord[0]).toUpperCase();
    }

    // Ultimate fallback: first 3 letters
    return teamName.substring(0, 3).toUpperCase();
  };


  const allBookmakers = Array.from(
    new Set(props.map(p => p.bookmaker))
  );

  return (
    <TierGate feature="props_ml_edges">
      <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black p-4" style={{ fontFamily: 'Rubik, sans-serif' }}>
        <div className="w-full mx-auto">
        {/* Header with Prop Type Selector and View Mode */}
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold italic text-slate-100 mb-2" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>PLAYER PROPS</h1>
            <p className="text-slate-400 text-lg">
              {viewMode === 'all'
                ? 'Compare player prop odds across multiple sportsbooks'
                : 'Advanced projections with edge analysis and betting recommendations'}
            </p>
            {viewMode === 'edges' && selectedSport !== 'nba' && (
              <div className="mt-2 bg-amber-900/20 border border-amber-700 p-2 text-amber-400 text-lg">
                ⚠️ Edge analysis is currently only available for NBA. Select NBA to view advanced props.
              </div>
            )}
          </div>

          <div className="flex gap-2">
            {/* Prop Type Selector */}
            {viewMode === 'all' && (
              <div className="flex gap-1 bg-slate-900 p-1 border border-white rounded-lg">
                <button
                  onClick={() => setSelectedPropType('all')}
                  className={`px-4 py-1.5 text-lg font-semibold transition-all ${
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
                    className={`px-4 py-1.5 text-lg font-semibold transition-all whitespace-nowrap ${
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
            <div className="flex gap-1 bg-slate-900 p-1 border border-white rounded-lg">
              <button
                onClick={() => setViewMode('all')}
                className={`px-4 py-1.5 text-lg font-semibold transition-all ${
                  viewMode === 'all'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                All Props
              </button>
              <button
                onClick={() => setViewMode('edges')}
                className={`px-4 py-1.5 text-lg font-semibold transition-all ${
                  viewMode === 'edges'
                    ? 'bg-green-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                🎯 Edges
              </button>
              <button
                onClick={() => setViewMode('crusher')}
                className={`px-4 py-1.5 text-lg font-semibold transition-all ${
                  viewMode === 'crusher'
                    ? 'bg-purple-600 text-white shadow-md shadow-purple-600/50'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                🔥 PrizePicks Crusher
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
                className={`px-3 py-1.5 text-lg font-semibold whitespace-nowrap transition-all flex items-center gap-2 ${
                  selectedSport === sport.key
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
                }`}
              >
                <span className="text-lg">{sport.emoji}</span>
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
            className="w-full bg-slate-900 border border-white px-2 py-1.5 text-white text-lg placeholder-slate-500 focus:outline-none focus:border-blue-400"
          />
        </div>

        {/* RENDER: PrizePicks Crusher View */}
        {viewMode === 'crusher' ? (
          <>
            {/* Combo Filters */}
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-4 mb-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center gap-4">
                  <label className="text-lg font-medium text-slate-300">Min Legs:</label>
                  <input
                    type="number"
                    value={minLegs}
                    onChange={(e) => setMinLegs(parseInt(e.target.value) || 2)}
                    className="bg-slate-900 border border-white rounded-lg px-4 py-2 text-white w-20 focus:outline-none focus:border-purple-400"
                    min="2"
                    max="6"
                  />
                </div>
                <div className="flex items-center gap-4">
                  <label className="text-lg font-medium text-slate-300">Max Legs:</label>
                  <input
                    type="number"
                    value={maxLegs}
                    onChange={(e) => setMaxLegs(parseInt(e.target.value) || 6)}
                    className="bg-slate-900 border border-white rounded-lg px-4 py-2 text-white w-20 focus:outline-none focus:border-purple-400"
                    min="2"
                    max="6"
                  />
                </div>
                <div className="flex items-center gap-4">
                  <label className="text-lg font-medium text-slate-300">
                    <input
                      type="checkbox"
                      checked={demonModeOnly}
                      onChange={(e) => setDemonModeOnly(e.target.checked)}
                      className="mr-2 w-5 h-5 accent-purple-600"
                    />
                    🔥 Demon Mode Only
                  </label>
                </div>
              </div>
            </div>

            {loading ? (
              <div className="text-center text-white text-3xl py-12">
                Loading correlated combos...
              </div>
            ) : !combos || combos.combos.length === 0 ? (
              <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-12 text-center">
                <div className="text-slate-400 text-xl mb-2">No combos found</div>
                <div className="text-slate-500 text-lg">
                  Try adjusting filters or check back when predictions are generated
                </div>
              </div>
            ) : (
              <>
                {/* Stats Summary */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-gradient-to-br from-purple-800 via-slate-900 to-black border border-purple-600 rounded-xl p-4">
                    <div className="text-purple-400 text-lg font-medium mb-1">Total Combos</div>
                    <div className="text-white text-4xl font-bold">{combos.stats.total_combos}</div>
                  </div>
                  <div className="bg-gradient-to-br from-red-800 via-slate-900 to-black border border-red-600 rounded-xl p-4">
                    <div className="text-red-400 text-lg font-medium mb-1">🔥 Demon Mode</div>
                    <div className="text-white text-4xl font-bold">{combos.stats.demon_mode}</div>
                  </div>
                  <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-4">
                    <div className="text-slate-400 text-lg font-medium mb-1">Normal</div>
                    <div className="text-white text-4xl font-bold">{combos.stats.normal}</div>
                  </div>
                  <div className="bg-gradient-to-br from-purple-800 via-slate-900 to-black border border-purple-600 rounded-xl p-4">
                    <div className="text-purple-400 text-lg font-medium mb-1">👺 Goblin Mode</div>
                    <div className="text-white text-4xl font-bold">{combos.stats.goblin_mode}</div>
                  </div>
                </div>

                {/* Combos Grid */}
                <div className="space-y-4">
                  {combos.combos.map((combo) => (
                    <div
                      key={combo.combo_id}
                      className={`bg-gradient-to-br from-slate-800 via-slate-900 to-black border-2 rounded-xl overflow-hidden shadow-xl ${
                        combo.is_demon_mode
                          ? 'border-red-600 shadow-red-600/30'
                          : combo.is_goblin_mode
                          ? 'border-purple-600 shadow-purple-600/30'
                          : 'border-white'
                      }`}
                    >
                      {/* Combo Header */}
                      <div className={`px-6 py-4 border-b-2 ${
                        combo.is_demon_mode
                          ? 'bg-red-900/20 border-red-600'
                          : combo.is_goblin_mode
                          ? 'bg-purple-900/20 border-purple-600'
                          : 'bg-slate-800/50 border-slate-700'
                      }`}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            {combo.is_demon_mode && (
                              <span className="bg-red-600 text-white px-3 py-1 rounded-lg font-bold text-lg shadow-lg shadow-red-600/50">
                                🔥 DEMON MODE
                              </span>
                            )}
                            {combo.is_goblin_mode && (
                              <span className="bg-purple-600 text-white px-3 py-1 rounded-lg font-bold text-lg shadow-lg shadow-purple-600/50">
                                👺 GOBLIN MODE
                              </span>
                            )}
                            <div>
                              <div className="text-white font-bold text-2xl">
                                {combo.num_legs}-Leg Combo
                              </div>
                              <div className="text-slate-400 text-lg">
                                {combo.payout_multiplier} Payout
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-green-400 font-bold text-3xl">
                              {combo.display_edge}
                            </div>
                            <div className={`text-lg font-semibold ${combo.confidence_color}`}>
                              {combo.confidence} • Score: {combo.display_score}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Props in Combo */}
                      <div className="p-6">
                        <div className="space-y-3">
                          {combo.props.map((prop, idx) => (
                            <div
                              key={idx}
                              className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 hover:bg-slate-800/70 transition-colors"
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <div className="text-white font-bold text-xl">
                                    {prop.player_name}
                                  </div>
                                  <div className="text-slate-400 text-lg">
                                    {prop.prop_type}
                                  </div>
                                </div>
                                <div className="text-center px-6">
                                  <div className={`font-bold text-2xl ${
                                    prop.direction === 'OVER' ? 'text-green-400' : 'text-blue-400'
                                  }`}>
                                    {prop.direction}
                                  </div>
                                  <div className="text-white text-xl font-semibold">
                                    {prop.display_line}
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Add to Bet Slip Button */}
                        <button
                          className={`w-full mt-4 py-3 rounded-lg font-bold text-xl transition-all ${
                            combo.is_demon_mode
                              ? 'bg-red-600 hover:bg-red-700 text-white shadow-lg shadow-red-600/50'
                              : 'bg-purple-600 hover:bg-purple-700 text-white shadow-lg shadow-purple-600/50'
                          }`}
                        >
                          📋 Add Combo to Bet Slip
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Last Updated */}
                <div className="mt-6 text-center text-slate-500 text-lg">
                  Showing {combos.count} of {combos.stats.total_combos} combos
                </div>
              </>
            )}
          </>
        ) : viewMode === 'edges' ? (
          <>
            {/* Edge Filter */}
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-4">
                <label className="text-lg font-medium text-slate-300">Minimum Edge %:</label>
                <input
                  type="number"
                  value={minEdge}
                  onChange={(e) => setMinEdge(parseFloat(e.target.value) || 5.0)}
                  className="bg-slate-900 border border-white rounded-lg px-4 py-2 text-white w-24 focus:outline-none focus:border-blue-400"
                  min="0"
                  max="50"
                  step="0.5"
                />
                <span className="text-slate-500 text-lg">Show props with at least {minEdge}% edge</span>
              </div>
            </div>

            {loading ? (
              <div className="text-center text-white text-3xl py-12">
                Loading edge analysis...
              </div>
            ) : !edgeProps || edgeProps.props.length === 0 ? (
              <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-12 text-center">
                <div className="text-slate-400 text-xl mb-2">No props with edges found</div>
                <div className="text-slate-500 text-lg">
                  Try lowering the minimum edge threshold or check back later
                </div>
              </div>
            ) : (
              <>
                {/* Stats Summary */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-4">
                    <div className="text-blue-400 text-lg font-medium mb-1">Total Props Analyzed</div>
                    <div className="text-white text-4xl font-bold">{edgeProps.total_props_analyzed}</div>
                  </div>
                  <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-4">
                    <div className="text-green-400 text-lg font-medium mb-1">Props with Edge</div>
                    <div className="text-white text-4xl font-bold">{edgeProps.props_with_edge}</div>
                  </div>
                  <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-4">
                    <div className="text-yellow-400 text-lg font-medium mb-1">Min Edge</div>
                    <div className="text-white text-4xl font-bold">{edgeProps.min_edge_pct}%</div>
                  </div>
                  <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-4">
                    <div className="text-purple-400 text-lg font-medium mb-1">Unique Players</div>
                    <div className="text-white text-4xl font-bold">{new Set(edgeProps.props.map(p => p.player_name)).size}</div>
                  </div>
                </div>

                {/* Props with Edges - Table View */}
                <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl overflow-hidden shadow-2xl">
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                      <thead className="bg-slate-800">
                        <tr>
                          <th className="text-left py-3 px-4 text-slate-300 font-bold text-lg uppercase tracking-wider border-r border-b-2 border-slate-600">
                            Player
                          </th>
                          <th className="text-left py-3 px-4 text-slate-300 font-bold text-lg uppercase tracking-wider border-r border-b-2 border-slate-600">
                            Matchup
                          </th>
                          <th className="text-left py-3 px-4 text-slate-300 font-bold text-lg uppercase tracking-wider border-r border-b-2 border-slate-600">
                            Prop Type
                          </th>
                          <th className="text-center py-3 px-4 text-slate-300 font-bold text-lg uppercase tracking-wider border-r border-b-2 border-slate-600">
                            Market Line
                          </th>
                          <th className="text-center py-3 px-4 text-slate-300 font-bold text-lg uppercase tracking-wider border-r border-b-2 border-slate-600">
                            ML Prediction
                          </th>
                          <th className="text-center py-3 px-4 text-slate-300 font-bold text-lg uppercase tracking-wider border-r border-b-2 border-slate-600">
                            Edge
                          </th>
                          <th className="text-center py-3 px-4 text-slate-300 font-bold text-lg uppercase tracking-wider border-r border-b-2 border-slate-600">
                            Recommendation
                          </th>
                          <th className="text-center py-3 px-4 text-slate-300 font-bold text-lg uppercase tracking-wider border-r border-b-2 border-slate-600">
                            Confidence
                          </th>
                          <th className="text-center py-3 px-4 text-slate-300 font-bold text-lg uppercase tracking-wider border-b-2 border-slate-600">
                            Best Odds
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {edgeProps.props.filter((prop, idx, self) =>
                          // Remove duplicates: keep only first occurrence of each player+prop+line combo
                          idx === self.findIndex((p) =>
                            p.player_name === prop.player_name &&
                            p.prop_type === prop.prop_type &&
                            p.market_line === prop.market_line
                          )
                        ).map((prop, idx) => (
                          <tr
                            key={`${prop.player_name}-${prop.prop_type}-${prop.market_line}`}
                            className={`hover:bg-slate-800/50 transition-colors ${
                              idx < edgeProps.props.length - 1 ? 'border-b border-slate-700' : ''
                            }`}
                          >
                            <td className="py-3 px-4 border-r border-slate-600">
                              <div className="text-white font-semibold">{prop.player_name}</div>
                              <div className="text-slate-500 text-lg">{prop.team}</div>
                            </td>
                            <td className="py-3 px-4 border-r border-slate-600">
                              <div className="text-slate-300 text-lg">vs {prop.opponent}</div>
                              <div className="text-slate-500 text-lg">{prop.home_away}</div>
                            </td>
                            <td className="py-3 px-4 border-r border-slate-600">
                              <span className="text-slate-300 font-medium">{formatPropType(prop.prop_type)}</span>
                            </td>
                            <td className="py-3 px-4 text-center border-r border-slate-600">
                              <span className="text-white font-bold text-xl">{prop.market_line}</span>
                            </td>
                            <td className="py-3 px-4 text-center border-r border-slate-600">
                              <span className="text-blue-400 font-bold text-xl">
                                {prop.predicted_value ? prop.predicted_value.toFixed(1) : 'N/A'}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-center border-r border-slate-600">
                              <div className={`font-bold text-xl ${Math.abs(prop.edge_pct || 0) >= 10 ? 'text-green-400' : 'text-yellow-400'}`}>
                                {prop.edge_pct ? Math.abs(prop.edge_pct).toFixed(1) : '0.0'}%
                              </div>
                              <div className="text-slate-400 text-sm">
                                ({prop.edge ? Math.abs(prop.edge).toFixed(1) : '0.0'} pts)
                              </div>
                            </td>
                            <td className="py-3 px-4 text-center border-r border-slate-600">
                              <div className={`inline-block px-3 py-1 rounded-lg font-bold text-lg ${
                                prop.edge_pct >= 10
                                  ? 'bg-green-900/50 text-green-400 border border-green-700'
                                  : 'bg-yellow-900/50 text-yellow-400 border border-yellow-700'
                              }`}>
                                {prop.recommendation}
                              </div>
                            </td>
                            <td className="py-3 px-4 text-center border-r border-slate-600">
                              <div className={`font-semibold text-lg ${
                                prop.confidence && prop.confidence >= 70 ? 'text-green-400' :
                                prop.confidence && prop.confidence >= 50 ? 'text-yellow-400' : 'text-slate-400'
                              }`}>
                                {prop.confidence ? prop.confidence.toFixed(0) : 'N/A'}%
                              </div>
                            </td>
                            <td className="py-3 px-4 text-center">
                              <div className="space-y-1">
                                {prop.over_odds && (
                                  <div className={`text-lg font-semibold px-2 py-1 rounded ${
                                    prop.recommendation === 'OVER'
                                      ? 'bg-green-900/40 text-green-400'
                                      : 'text-slate-400'
                                  }`}>
                                    O {formatOdds(prop.over_odds)}
                                  </div>
                                )}
                                {prop.under_odds && (
                                  <div className={`text-lg font-semibold px-2 py-1 rounded ${
                                    prop.recommendation === 'UNDER'
                                      ? 'bg-blue-900/40 text-blue-400'
                                      : 'text-slate-400'
                                  }`}>
                                    U {formatOdds(prop.under_odds)}
                                  </div>
                                )}
                                <div className="text-slate-500 text-[9px]">{prop.bookmaker}</div>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Last Updated */}
                <div className="mt-6 text-center text-slate-500 text-lg">
                  Last updated: {edgeProps.time_generated}
                </div>
              </>
            )}
          </>
        ) : (
          /* RENDER: Basic Props Table View */
          <>
            {/* Props Table */}
            {loading ? (
              <div className="text-center text-white text-3xl py-12">
                Loading props...
              </div>
            ) : filteredPropsFromAPI.length === 0 ? (
          <div className="bg-slate-800/50 border border-slate-700 p-12 text-center">
            <div className="text-slate-400 text-xl mb-2">No props available</div>
            <div className="text-slate-500 text-lg">
              {searchQuery ? 'Try adjusting your search filters' : 'Check back later for updated props'}
            </div>
          </div>
        ) : (
          <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl overflow-hidden shadow-2xl">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead className="bg-slate-800">
                  <tr>
                    <th className="text-left py-2 px-1 text-slate-300 font-bold text-lg uppercase tracking-wider border-r border-b-2 border-slate-600 w-[100px]">
                      Player
                    </th>
                    <th className="text-left py-2 px-1 text-slate-300 font-bold text-lg uppercase tracking-wider border-r border-b-2 border-slate-600 w-[90px]">
                      Prop
                    </th>
                    <th className="text-center py-2 px-1 text-slate-300 font-bold text-lg uppercase tracking-wider border-r border-b-2 border-slate-600 w-[50px]">
                      Line
                    </th>
                    <th className="text-left py-2 px-1 text-slate-300 font-bold text-lg uppercase tracking-wider border-r border-b-2 border-slate-600 w-[110px]">
                      Matchup
                    </th>
                    <th className="text-center py-2 px-1 text-slate-300 font-bold text-lg uppercase tracking-wider border-r border-b-2 border-slate-600 w-[80px]">
                      Odds
                    </th>
                    <th className="text-center py-2 px-1 text-slate-300 font-bold text-lg uppercase tracking-wider border-b-2 border-slate-600 w-[80px]">
                      Book
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPropsFromAPI.map((prop, idx) => (
                    <tr
                      key={idx}
                      className={`hover:bg-slate-800/30 transition-colors ${
                        idx < filteredPropsFromAPI.length - 1 ? 'border-b border-slate-700' : ''
                      }`}
                    >
                      <td className="py-0.5 px-1 border-r border-slate-600 w-[100px]">
                        <div className="flex flex-col">
                          <span className="text-white font-semibold text-lg truncate block">{prop.player_name}</span>
                          <span className="text-slate-500 text-[9px] truncate">
                            {prop.team}
                          </span>
                        </div>
                      </td>
                      <td className="py-0.5 px-1 border-r border-slate-600 w-[90px]">
                        <span className="text-slate-300 text-lg truncate block">{formatPropType(prop.prop_type)}</span>
                      </td>
                      <td className="py-0.5 px-1 text-center border-r border-slate-600 w-[50px]">
                        <span className="text-white font-bold text-lg">{prop.market_line}</span>
                      </td>
                      <td className="py-0.5 px-1 border-r border-slate-600 w-[110px]">
                        <div className="text-slate-300 text-[10px] truncate">vs {prop.opponent}</div>
                        <div className="text-slate-500 text-[9px] truncate">
                          {prop.home_away}
                        </div>
                      </td>
                      <td className="py-0.5 px-1 text-center border-r border-slate-700">
                        <div className="space-y-0.5">
                          {prop.over_odds && (
                            <div className="text-center px-1 py-0.5 text-lg font-semibold text-slate-300">
                              O {formatOdds(prop.over_odds)}
                            </div>
                          )}
                          {prop.under_odds && (
                            <div className="text-center px-1 py-0.5 text-lg font-semibold text-slate-300">
                              U {formatOdds(prop.under_odds)}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="py-0.5 px-1 text-center">
                        <div className="text-slate-400 text-[9px]">{prop.bookmaker}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

            {/* Stats Footer */}
            <div className="mt-6 text-center text-slate-500 text-lg">
              Showing {filteredPropsFromAPI.length} props across multiple sportsbooks
            </div>
          </>
        )}

          </div>
        </div>
      </div>
    </div>
    </TierGate>
  );
}
