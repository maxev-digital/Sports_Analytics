import { useState, useEffect } from 'react';

interface SportPrediction {
  sport: string;
  game_id: string;
  game_date: string;
  home_team: string;
  away_team: string;
  predicted_total: number;
  market_total: number | null;
  total_edge: number | null;
  total_recommendation: string | null;
  total_confidence: string;
  predicted_spread: number;
  market_spread: number | null;
  spread_edge: number | null;
  spread_recommendation: string | null;
  spread_confidence: string;
  home_win_prob: number;
  away_win_prob: number;
  ml_recommendation: string | null;
  ml_confidence: string;
}

interface SportPerformance {
  sport: string;
  total_plays: number;
  wins: number;
  losses: number;
  pushes: number;
  pending: number;
  completed: number;
  win_rate: number;
  total_profit: number;
  avg_edge: number;
  avg_roi: number;
}

export function MultiSport() {
  const [activeTab, setActiveTab] = useState<'nba' | 'nhl' | 'nfl' | 'mlb'>('nba');
  const [predictions, setPredictions] = useState<SportPrediction[]>([]);
  const [sportPerformance, setSportPerformance] = useState<Record<string, SportPerformance>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch sport performance data
    fetch('http://localhost:8001/api/plays/performance/by-sport')
      .then(res => res.json())
      .then(data => {
        setSportPerformance(data.sports || {});
      })
      .catch(err => console.error('Error fetching sport performance:', err));

    // Mock data for demonstration
    const mockPredictions: SportPrediction[] = [
      {
        sport: 'NBA',
        game_id: 'nba_20250117_bos_lal',
        game_date: '2025-01-17T19:30:00',
        home_team: 'Lakers',
        away_team: 'Celtics',
        predicted_total: 228.3,
        market_total: 225.5,
        total_edge: 2.8,
        total_recommendation: 'OVER',
        total_confidence: 'MEDIUM',
        predicted_spread: -1.2,
        market_spread: -2.5,
        spread_edge: 1.3,
        spread_recommendation: 'AWAY',
        spread_confidence: 'LOW',
        home_win_prob: 0.547,
        away_win_prob: 0.453,
        ml_recommendation: 'HOME',
        ml_confidence: 'MEDIUM'
      },
      {
        sport: 'NHL',
        game_id: 'nhl_20250117_bos_tor',
        game_date: '2025-01-17T19:00:00',
        home_team: 'Maple Leafs',
        away_team: 'Bruins',
        predicted_total: 6.2,
        market_total: 6.5,
        total_edge: 0.3,
        total_recommendation: 'UNDER',
        total_confidence: 'LOW',
        predicted_spread: -0.3,
        market_spread: -0.5,
        spread_edge: 0.2,
        spread_recommendation: null,
        spread_confidence: 'LOW',
        home_win_prob: 0.512,
        away_win_prob: 0.488,
        ml_recommendation: null,
        ml_confidence: 'LOW'
      },
      {
        sport: 'NFL',
        game_id: 'nfl_20250119_kc_buf',
        game_date: '2025-01-19T15:30:00',
        home_team: 'Bills',
        away_team: 'Chiefs',
        predicted_total: 51.2,
        market_total: 48.5,
        total_edge: 2.7,
        total_recommendation: 'OVER',
        total_confidence: 'MEDIUM',
        predicted_spread: 2.8,
        market_spread: 1.5,
        spread_edge: 1.3,
        spread_recommendation: 'HOME',
        spread_confidence: 'LOW',
        home_win_prob: 0.605,
        away_win_prob: 0.395,
        ml_recommendation: 'HOME',
        ml_confidence: 'MEDIUM'
      },
      {
        sport: 'MLB',
        game_id: 'mlb_20250415_nyy_bos',
        game_date: '2025-04-15T19:10:00',
        home_team: 'Red Sox',
        away_team: 'Yankees',
        predicted_total: 8.8,
        market_total: 9.0,
        total_edge: 0.2,
        total_recommendation: null,
        total_confidence: 'LOW',
        predicted_spread: 0.5,
        market_spread: 0.5,
        spread_edge: 0.0,
        spread_recommendation: null,
        spread_confidence: 'LOW',
        home_win_prob: 0.520,
        away_win_prob: 0.480,
        ml_recommendation: null,
        ml_confidence: 'LOW'
      }
    ];

    setPredictions(mockPredictions);
    setLoading(false);
  }, []);

  const filteredPredictions = predictions.filter(p =>
    p.sport.toLowerCase() === activeTab
  );

  const getConfidenceBadge = (confidence: string) => {
    const styles = {
      HIGH: 'bg-green-600 text-white border-green-700',
      MEDIUM: 'bg-blue-600 text-white border-blue-700',
      LOW: 'bg-slate-600 text-white border-slate-700'
    };
    return styles[confidence as keyof typeof styles] || styles.LOW;
  };

  const getSportEmoji = (sport: string) => {
    switch(sport.toLowerCase()) {
      case 'nba':
        return '🏀';
      case 'nhl':
        return '🏒';
      case 'nfl':
        return '🏈';
      case 'mlb':
        return '⚾';
      default:
        return '🏀';
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black flex items-center justify-center">
        <div className="text-slate-400 text-lg">Loading predictions...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-100 mb-2">Multi-Sport Predictions</h1>
          <p className="text-slate-400">AI-powered betting analysis across NBA, NHL, NFL, and MLB</p>
        </div>

        {/* Sport Tabs */}
        <div className="flex gap-3 mb-6 overflow-x-auto pb-2">
          {(['nba', 'nhl', 'nfl', 'mlb'] as const).map((sport) => (
            <button
              key={sport}
              onClick={() => setActiveTab(sport)}
              className={`px-6 py-3 rounded border-2 font-bold transition-all whitespace-nowrap flex items-center gap-2 ${
                activeTab === sport
                  ? 'bg-blue-600 text-white border-blue-700 shadow-lg'
                  : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700 hover:border-slate-600'
              }`}
            >
              <span className="text-lg">{getSportEmoji(sport)}</span>
              {sport.toUpperCase()}
              <span className="text-sm opacity-75">
                ({predictions.filter(p => p.sport.toLowerCase() === sport).length})
              </span>
            </button>
          ))}
        </div>

        {/* Predictions Grid */}
        <div className="grid gap-6">
          {filteredPredictions.length === 0 ? (
            <div className="bg-slate-800 rounded border-2 border-slate-700 p-12 text-center">
              <div className="text-6xl mb-4 opacity-50">{getSportEmoji(activeTab)}</div>
              <h3 className="text-xl font-semibold text-slate-300 mb-2">
                No {activeTab.toUpperCase()} Games Available
              </h3>
              <p className="text-slate-500">
                Check back soon for upcoming predictions
              </p>
            </div>
          ) : (
            filteredPredictions.map((pred) => (
              <div
                key={pred.game_id}
                className="bg-slate-800 rounded border-2 border-slate-700 p-6 hover:border-blue-600 transition-all"
              >
                {/* Game Header */}
                <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-700">
                  <div>
                    <div className="text-2xl font-bold text-slate-100 mb-1">
                      {pred.away_team} @ {pred.home_team}
                    </div>
                    <div className="text-sm text-slate-400 flex items-center gap-2">
                      <span>{getSportEmoji(pred.sport)}</span>
                      {pred.sport} • {formatDate(pred.game_date)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-slate-400 mb-1">Win Probability</div>
                    <div className="flex gap-3">
                      <div className="text-center">
                        <div className="text-xs text-slate-500">{pred.away_team}</div>
                        <div className="text-lg font-bold text-slate-200">
                          {(pred.away_win_prob * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div className="text-slate-600">vs</div>
                      <div className="text-center">
                        <div className="text-xs text-slate-500">{pred.home_team}</div>
                        <div className="text-lg font-bold text-slate-200">
                          {(pred.home_win_prob * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Predictions Grid */}
                <div className="grid md:grid-cols-3 gap-4">
                  {/* Total */}
                  <div className="bg-slate-900 rounded border-2 border-slate-700 p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-bold text-slate-300 uppercase tracking-wide">Total</h4>
                      <span className={`px-3 py-1 rounded text-xs font-bold border-2 ${getConfidenceBadge(pred.total_confidence)}`}>
                        {pred.total_confidence}
                      </span>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-slate-400 text-sm">Predicted:</span>
                        <span className="text-slate-100 font-bold">{pred.predicted_total.toFixed(1)}</span>
                      </div>
                      {pred.market_total && (
                        <>
                          <div className="flex justify-between">
                            <span className="text-slate-400 text-sm">Market:</span>
                            <span className="text-slate-100 font-bold">{pred.market_total.toFixed(1)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400 text-sm">Edge:</span>
                            <span className="text-blue-400 font-bold">{pred.total_edge?.toFixed(1)}</span>
                          </div>
                          {pred.total_recommendation && (
                            <div className="mt-3 pt-3 border-t-2 border-slate-700">
                              <div className={`text-center py-2 rounded border-2 font-bold ${
                                pred.total_recommendation === 'OVER'
                                  ? 'bg-green-600 text-white border-green-700'
                                  : 'bg-red-600 text-white border-red-700'
                              }`}>
                                {pred.total_recommendation}
                              </div>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>

                  {/* Spread */}
                  <div className="bg-slate-900 rounded border-2 border-slate-700 p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-bold text-slate-300 uppercase tracking-wide">Spread</h4>
                      <span className={`px-3 py-1 rounded text-xs font-bold border-2 ${getConfidenceBadge(pred.spread_confidence)}`}>
                        {pred.spread_confidence}
                      </span>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-slate-400 text-sm">Predicted:</span>
                        <span className="text-slate-100 font-bold">
                          {pred.predicted_spread > 0 ? '+' : ''}{pred.predicted_spread.toFixed(1)}
                        </span>
                      </div>
                      {pred.market_spread && (
                        <>
                          <div className="flex justify-between">
                            <span className="text-slate-400 text-sm">Market:</span>
                            <span className="text-slate-100 font-bold">
                              {pred.market_spread > 0 ? '+' : ''}{pred.market_spread.toFixed(1)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400 text-sm">Edge:</span>
                            <span className="text-blue-400 font-bold">{pred.spread_edge?.toFixed(1)}</span>
                          </div>
                          {pred.spread_recommendation && (
                            <div className="mt-3 pt-3 border-t-2 border-slate-700">
                              <div className="text-center py-2 rounded border-2 font-bold bg-blue-600 text-white border-blue-700">
                                {pred.spread_recommendation === 'HOME' ? pred.home_team : pred.away_team}
                              </div>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>

                  {/* Moneyline */}
                  <div className="bg-slate-900 rounded border-2 border-slate-700 p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-bold text-slate-300 uppercase tracking-wide">Moneyline</h4>
                      <span className={`px-3 py-1 rounded text-xs font-bold border-2 ${getConfidenceBadge(pred.ml_confidence)}`}>
                        {pred.ml_confidence}
                      </span>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-slate-400 text-sm">{pred.home_team}:</span>
                        <span className="text-slate-100 font-bold">
                          {(pred.home_win_prob * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400 text-sm">{pred.away_team}:</span>
                        <span className="text-slate-100 font-bold">
                          {(pred.away_win_prob * 100).toFixed(1)}%
                        </span>
                      </div>
                      {pred.ml_recommendation && (
                        <div className="mt-3 pt-3 border-t-2 border-slate-700">
                          <div className="text-center py-2 rounded border-2 font-bold bg-green-600 text-white border-green-700">
                            {pred.ml_recommendation === 'HOME' ? pred.home_team : pred.away_team}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Stats Summary */}
        <div className="mt-8 grid md:grid-cols-4 gap-4">
          <div className="bg-slate-800 rounded border-2 border-slate-700 p-4">
            <div className="text-sm text-slate-400 mb-1 font-semibold">Total Games</div>
            <div className="text-3xl font-bold text-white">{predictions.length}</div>
          </div>
          <div className="bg-slate-800 rounded border-2 border-green-700 p-4">
            <div className="text-sm text-slate-400 mb-1 font-semibold">High Confidence</div>
            <div className="text-3xl font-bold text-green-500">
              {predictions.filter(p =>
                p.total_confidence === 'HIGH' ||
                p.spread_confidence === 'HIGH' ||
                p.ml_confidence === 'HIGH'
              ).length}
            </div>
          </div>
          <div className="bg-slate-800 rounded border-2 border-blue-700 p-4">
            <div className="text-sm text-slate-400 mb-1 font-semibold">Medium Confidence</div>
            <div className="text-3xl font-bold text-blue-500">
              {predictions.filter(p =>
                p.total_confidence === 'MEDIUM' ||
                p.spread_confidence === 'MEDIUM' ||
                p.ml_confidence === 'MEDIUM'
              ).length}
            </div>
          </div>
          <div className="bg-slate-800 rounded border-2 border-slate-700 p-4">
            <div className="text-sm text-slate-400 mb-1 font-semibold">Sports Covered</div>
            <div className="text-3xl font-bold text-white">
              {new Set(predictions.map(p => p.sport)).size}
            </div>
          </div>
        </div>

        {/* Sport Performance Dashboard */}
        <div className="mt-8">
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-slate-100 mb-1">Historical Performance by Sport</h2>
            <p className="text-slate-400">Track record separated by sport with transparent results</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {(['NBA', 'NHL', 'NFL', 'MLB'] as const).map((sport) => {
              const perf = sportPerformance[sport];
              const hasPerfData = perf && perf.total_plays > 0;

              return (
                <div key={sport} className="bg-slate-800 rounded border-2 border-slate-700 p-6 hover:border-blue-600 transition-all">
                  {/* Sport Header */}
                  <div className="flex items-center gap-3 mb-4 pb-3 border-b-2 border-slate-700">
                    <span className="text-2xl">{getSportEmoji(sport.toLowerCase())}</span>
                    <h3 className="text-xl font-bold text-white">{sport}</h3>
                  </div>

                  {hasPerfData ? (
                    <>
                      {/* Record */}
                      <div className="mb-4">
                        <div className="text-sm text-slate-400 mb-1 font-semibold uppercase tracking-wide">Record</div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-2xl font-bold text-green-400">{perf.wins}</span>
                          <span className="text-slate-500">-</span>
                          <span className="text-2xl font-bold text-red-400">{perf.losses}</span>
                          {perf.pushes > 0 && (
                            <>
                              <span className="text-slate-500">-</span>
                              <span className="text-2xl font-bold text-slate-400">{perf.pushes}</span>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Win Rate */}
                      <div className="mb-4">
                        <div className="text-sm text-slate-400 mb-1 font-semibold uppercase tracking-wide">Win Rate</div>
                        <div className={`text-3xl font-bold ${
                          perf.win_rate >= 55 ? 'text-green-400' :
                          perf.win_rate >= 52 ? 'text-blue-400' :
                          'text-slate-400'
                        }`}>
                          {perf.win_rate.toFixed(1)}%
                        </div>
                        <div className="w-full bg-slate-700 rounded-full h-2 mt-2">
                          <div
                            className={`h-2 rounded-full transition-all ${
                              perf.win_rate >= 55 ? 'bg-green-600' :
                              perf.win_rate >= 52 ? 'bg-blue-600' :
                              'bg-slate-600'
                            }`}
                            style={{ width: `${Math.min(perf.win_rate, 100)}%` }}
                          />
                        </div>
                      </div>

                      {/* Total Profit */}
                      <div className="mb-4">
                        <div className="text-sm text-slate-400 mb-1 font-semibold uppercase tracking-wide">Total Profit</div>
                        <div className={`text-2xl font-bold ${
                          perf.total_profit > 0 ? 'text-green-400' :
                          perf.total_profit < 0 ? 'text-red-400' :
                          'text-slate-400'
                        }`}>
                          {perf.total_profit > 0 ? '+' : ''}{perf.total_profit.toFixed(2)} units
                        </div>
                      </div>

                      {/* Stats */}
                      <div className="pt-3 border-t-2 border-slate-700 space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Avg Edge:</span>
                          <span className="text-white font-bold">{perf.avg_edge.toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Avg ROI:</span>
                          <span className="text-white font-bold">{perf.avg_roi.toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Total Plays:</span>
                          <span className="text-white font-bold">{perf.total_plays}</span>
                        </div>
                        {perf.pending > 0 && (
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-400">Pending:</span>
                            <span className="text-yellow-400 font-bold">{perf.pending}</span>
                          </div>
                        )}
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-8">
                      <div className="text-slate-500 text-sm mb-2">No historical data yet</div>
                      <div className="text-slate-600 text-xs">Results will appear after plays are logged</div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
