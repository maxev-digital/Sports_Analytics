import { useEffect, useState } from 'react';

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
  const [selectedSport, setSelectedSport] = useState<string>('nba');
  const [props, setProps] = useState<PlayerProp[]>([]);
  const [groupedProps, setGroupedProps] = useState<GroupedProp[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPropType, setSelectedPropType] = useState<string>('all');

  const sports = [
    { key: 'nba', name: 'NBA', icon: 'https://cdn.ssref.net/req/202410311/tlogo/bbr/NBA.png' },
    { key: 'nfl', name: 'NFL', icon: 'https://cdn.ssref.net/req/202410311/tlogo/pfr/NFL.png' },
    { key: 'nhl', name: 'NHL', icon: 'https://cdn.ssref.net/req/202410311/tlogo/hr/NHL.png' },
    { key: 'mlb', name: 'MLB', icon: 'https://cdn.ssref.net/req/202410311/tlogo/br/MLB.png' }
  ];

  // Fetch props data
  useEffect(() => {
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
  }, [selectedSport]);

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

  // Get player headshot URL
  const getPlayerHeadshot = (playerName: string) => {
    // This would need a proper player ID mapping in production
    // For now, return a placeholder
    return `https://via.placeholder.com/48x48.png?text=${playerName.charAt(0)}`;
  };

  const allBookmakers = Array.from(
    new Set(props.map(p => p.bookmaker))
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-3">Player Props</h1>
          <p className="text-lg text-slate-400">
            Compare player prop odds across multiple sportsbooks
          </p>
        </div>

        {/* Sport Selector */}
        <div className="mb-6">
          <div className="flex gap-3">
            {sports.map((sport) => (
              <button
                key={sport.key}
                onClick={() => setSelectedSport(sport.key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition-all ${
                  selectedSport === sport.key
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                <img src={sport.icon} alt={sport.name} className="w-6 h-6 object-contain" />
                {sport.name}
              </button>
            ))}
          </div>
        </div>

        {/* Filters */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Search Player
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by player name..."
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Prop Type
              </label>
              <select
                value={selectedPropType}
                onChange={(e) => setSelectedPropType(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
              >
                <option value="all">All Props</option>
                {propTypes.map((type) => (
                  <option key={type} value={type}>
                    {formatPropType(type)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Props Table */}
        {loading ? (
          <div className="text-center text-white text-xl py-12">
            Loading props...
          </div>
        ) : filteredProps.length === 0 ? (
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-12 text-center">
            <div className="text-slate-400 text-lg mb-2">No props available</div>
            <div className="text-slate-500 text-sm">
              {searchQuery ? 'Try adjusting your search filters' : 'Check back later for updated props'}
            </div>
          </div>
        ) : (
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-900/80 sticky top-0">
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-4 px-4 text-slate-300 font-semibold">Player</th>
                    <th className="text-left py-4 px-4 text-slate-300 font-semibold">Prop</th>
                    <th className="text-center py-4 px-4 text-slate-300 font-semibold">Line</th>
                    <th className="text-left py-4 px-4 text-slate-300 font-semibold">Game</th>
                    {allBookmakers.slice(0, 4).map((bookmaker) => (
                      <th key={bookmaker} className="text-center py-4 px-4 text-slate-300 font-semibold min-w-[120px]">
                        {bookmaker}
                      </th>
                    ))}
                    <th className="text-center py-4 px-4 text-slate-300 font-semibold">Best</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredProps.map((prop, idx) => (
                    <tr
                      key={idx}
                      className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors"
                    >
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-3">
                          <img
                            src={getPlayerHeadshot(prop.player_name)}
                            alt={prop.player_name}
                            className="w-10 h-10 rounded-full bg-slate-700"
                            onError={(e) => {
                              e.currentTarget.src = `https://via.placeholder.com/40x40.png?text=${prop.player_name.charAt(0)}`;
                            }}
                          />
                          <span className="text-white font-semibold">{prop.player_name}</span>
                        </div>
                      </td>
                      <td className="py-4 px-4 text-slate-300">
                        {formatPropType(prop.prop_type)}
                      </td>
                      <td className="py-4 px-4 text-center">
                        <span className="text-white font-bold text-lg">{prop.line}</span>
                      </td>
                      <td className="py-4 px-4">
                        <div className="text-slate-300 text-sm">{prop.game}</div>
                        <div className="text-slate-500 text-xs">
                          {new Date(prop.commence_time).toLocaleString()}
                        </div>
                      </td>
                      {allBookmakers.slice(0, 4).map((bookmaker) => (
                        <td key={bookmaker} className="py-4 px-4">
                          <div className="flex flex-col gap-1">
                            {prop.bookmakers[bookmaker]?.over && (
                              <div className={`text-center px-2 py-1 rounded-lg text-sm font-semibold ${
                                prop.best_over?.bookmaker === bookmaker
                                  ? 'bg-green-900/50 text-green-400 border border-green-700'
                                  : 'bg-slate-700/50 text-slate-300'
                              }`}>
                                O {formatOdds(prop.bookmakers[bookmaker].over!)}
                              </div>
                            )}
                            {prop.bookmakers[bookmaker]?.under && (
                              <div className={`text-center px-2 py-1 rounded-lg text-sm font-semibold ${
                                prop.best_under?.bookmaker === bookmaker
                                  ? 'bg-blue-900/50 text-blue-400 border border-blue-700'
                                  : 'bg-slate-700/50 text-slate-300'
                              }`}>
                                U {formatOdds(prop.bookmakers[bookmaker].under!)}
                              </div>
                            )}
                          </div>
                        </td>
                      ))}
                      <td className="py-4 px-4">
                        <div className="flex flex-col gap-1">
                          {prop.best_over && (
                            <div className="text-center px-2 py-1 rounded-lg text-sm font-bold bg-green-900/50 text-green-400 border border-green-700">
                              O {formatOdds(prop.best_over.odds)}
                            </div>
                          )}
                          {prop.best_under && (
                            <div className="text-center px-2 py-1 rounded-lg text-sm font-bold bg-blue-900/50 text-blue-400 border border-blue-700">
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
      </div>
    </div>
  );
}
