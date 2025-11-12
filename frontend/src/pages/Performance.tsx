import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface PerformanceSummary {
  overall: {
    total_predictions: number;
    wins: number;
    losses: number;
    unknown: number;
    win_rate: number;
    profit_loss: number;
    roi: number;
  };
  by_bet_type: Array<{
    bet_type: string;
    count: number;
    wins: number;
    losses: number;
    win_rate: number;
    profit_loss: number;
    roi: number;
  }>;
  by_sport: Array<{
    sport: string;
    count: number;
    wins: number;
    losses: number;
    win_rate: number;
    profit_loss: number;
    roi: number;
  }>;
  by_confidence: Array<{
    confidence: string;
    count: number;
    wins: number;
    losses: number;
    win_rate: number;
    profit_loss: number;
    roi: number;
  }>;
}

interface Prediction {
  prediction_id: string;
  game_date: string;
  sport: string;
  away_team: string;
  home_team: string;
  away_score: number | null;
  home_score: number | null;
  bet_type: string;
  recommendation: string;
  confidence: string;
  market_total: number | null;
  predicted_total: number | null;
  actual_total: number | null;
  result: string;
  profit_loss: number;
  edge_accuracy: number | null;
}

export default function Performance() {
  const [summary, setSummary] = useState<PerformanceSummary | null>(null);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [chartData, setChartData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [days, setDays] = useState(30);
  const [betTypeFilter, setBetTypeFilter] = useState<string>('');
  const [sportFilter, setSportFilter] = useState<string>('');
  const [resultFilter, setResultFilter] = useState<string>('');

  useEffect(() => {
    fetchData();
  }, [days, betTypeFilter, sportFilter]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch summary
      const summaryParams = new URLSearchParams({ days: days.toString() });
      if (betTypeFilter) summaryParams.append('bet_type', betTypeFilter);
      if (sportFilter) summaryParams.append('sport', sportFilter);

      const summaryRes = await fetch(`/api/performance/summary?${summaryParams}`);
      const summaryData = await summaryRes.json();
      setSummary(summaryData);

      // Fetch recent predictions
      const predParams = new URLSearchParams({ limit: '100' });
      if (betTypeFilter) predParams.append('bet_type', betTypeFilter);
      if (sportFilter) predParams.append('sport', sportFilter);
      if (resultFilter) predParams.append('result', resultFilter);

      const predRes = await fetch(`/api/performance/recent-predictions?${predParams}`);
      const predData = await predRes.json();
      setPredictions(predData.predictions || []);

      // Fetch chart data
      const chartRes = await fetch(`/api/performance/chart-data?days=${days}`);
      const chartDataRes = await chartRes.json();
      setChartData(chartDataRes.chart_data || []);
    } catch (error) {
      console.error('Error fetching performance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return value >= 0 ? `+$${value.toFixed(2)}` : `-$${Math.abs(value).toFixed(2)}`;
  };

  const getROIColor = (roi: number) => {
    if (roi >= 5) return 'text-green-400';
    if (roi > 0) return 'text-green-300';
    if (roi > -5) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getResultBadge = (result: string) => {
    const badges = {
      WIN: 'bg-green-600 text-white',
      LOSS: 'bg-red-600 text-white',
      UNKNOWN: 'bg-gray-600 text-white'
    };
    return badges[result as keyof typeof badges] || 'bg-gray-600';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading performance data...</div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">No performance data available</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Model Performance</h1>
          <p className="text-slate-300">Historical prediction results with complete win/loss tracking</p>
          <p className="text-slate-400 text-sm mt-2">All profits calculated on $100 flat bets</p>
        </div>

        {/* Filters */}
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-white text-sm mb-2 block">Time Period</label>
              <select
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600"
              >
                <option value={7}>Last 7 Days</option>
                <option value={30}>Last 30 Days</option>
                <option value={90}>Last 90 Days</option>
                <option value={0}>All Time</option>
              </select>
            </div>
            <div>
              <label className="text-white text-sm mb-2 block">Bet Type</label>
              <select
                value={betTypeFilter}
                onChange={(e) => setBetTypeFilter(e.target.value)}
                className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600"
              >
                <option value="">All Bet Types</option>
                <option value="totals">Totals</option>
                <option value="spreads">Spreads</option>
                <option value="moneyline">Moneyline</option>
              </select>
            </div>
            <div>
              <label className="text-white text-sm mb-2 block">Sport</label>
              <select
                value={sportFilter}
                onChange={(e) => setSportFilter(e.target.value)}
                className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600"
              >
                <option value="">All Sports</option>
                <option value="NBA">NBA</option>
                <option value="NFL">NFL</option>
                <option value="NHL">NHL</option>
                <option value="NCAAB">NCAAB</option>
                <option value="NCAAF">NCAAF</option>
              </select>
            </div>
            <div>
              <label className="text-white text-sm mb-2 block">Result</label>
              <select
                value={resultFilter}
                onChange={(e) => { setResultFilter(e.target.value); fetchData(); }}
                className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600"
              >
                <option value="">All Results</option>
                <option value="WIN">Wins Only</option>
                <option value="LOSS">Losses Only</option>
              </select>
            </div>
          </div>
        </div>

        {/* Overall Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-blue-600 via-blue-700 to-blue-900 rounded-xl p-6 border-4 border-blue-500">
            <div className="text-blue-200 text-sm mb-1">Total Predictions</div>
            <div className="text-white text-3xl font-bold">{summary.overall.total_predictions}</div>
          </div>
          <div className="bg-gradient-to-br from-green-600 via-green-700 to-green-900 rounded-xl p-6 border-4 border-green-500">
            <div className="text-green-200 text-sm mb-1">Win Rate</div>
            <div className="text-white text-3xl font-bold">{summary.overall.win_rate.toFixed(1)}%</div>
            <div className="text-green-200 text-xs mt-1">{summary.overall.wins}W - {summary.overall.losses}L</div>
          </div>
          <div className={`bg-gradient-to-br ${summary.overall.profit_loss >= 0 ? 'from-green-600 via-green-700 to-green-900' : 'from-red-600 via-red-700 to-red-900'} rounded-xl p-6 border-4 ${summary.overall.profit_loss >= 0 ? 'border-green-500' : 'border-red-500'}`}>
            <div className={`${summary.overall.profit_loss >= 0 ? 'text-green-200' : 'text-red-200'} text-sm mb-1`}>Total Profit/Loss</div>
            <div className="text-white text-3xl font-bold">{formatCurrency(summary.overall.profit_loss)}</div>
          </div>
          <div className={`bg-gradient-to-br ${summary.overall.roi >= 0 ? 'from-purple-600 via-purple-700 to-purple-900' : 'from-red-600 via-red-700 to-red-900'} rounded-xl p-6 border-4 ${summary.overall.roi >= 0 ? 'border-purple-500' : 'border-red-500'}`}>
            <div className={`${summary.overall.roi >= 0 ? 'text-purple-200' : 'text-red-200'} text-sm mb-1`}>ROI</div>
            <div className="text-white text-3xl font-bold">{summary.overall.roi >= 0 ? '+' : ''}{summary.overall.roi.toFixed(2)}%</div>
          </div>
        </div>

        {/* By Bet Type */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <h2 className="text-2xl font-bold text-white mb-4">Performance by Bet Type</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {summary.by_bet_type.map((bt) => (
              <div key={bt.bet_type} className={`bg-gradient-to-br ${bt.roi >= 5 ? 'from-green-700 via-green-800 to-green-900 border-green-600' : bt.roi > 0 ? 'from-blue-700 via-blue-800 to-blue-900 border-blue-600' : 'from-red-700 via-red-800 to-red-900 border-red-600'} rounded-lg p-4 border-4`}>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-white font-bold text-lg">{bt.bet_type}</h3>
                  <span className={`text-2xl font-bold ${getROIColor(bt.roi)}`}>
                    {bt.roi >= 0 ? '+' : ''}{bt.roi.toFixed(1)}%
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between text-white/90">
                    <span>Predictions:</span>
                    <span className="font-semibold">{bt.count}</span>
                  </div>
                  <div className="flex justify-between text-white/90">
                    <span>Win Rate:</span>
                    <span className="font-semibold">{bt.win_rate.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between text-white/90">
                    <span>Record:</span>
                    <span className="font-semibold">{bt.wins}W - {bt.losses}L</span>
                  </div>
                  <div className="flex justify-between text-white font-bold">
                    <span>Profit:</span>
                    <span>{formatCurrency(bt.profit_loss)}</span>
                  </div>
                </div>
                {bt.roi >= 5 && (
                  <div className="mt-3 bg-green-500/20 border border-green-400 rounded px-2 py-1 text-center">
                    <span className="text-green-300 text-xs font-bold">✅ PROFITABLE SYSTEM</span>
                  </div>
                )}
                {bt.roi < -10 && (
                  <div className="mt-3 bg-red-500/20 border border-red-400 rounded px-2 py-1 text-center">
                    <span className="text-red-300 text-xs font-bold">❌ NEEDS IMPROVEMENT</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Cumulative P/L Chart */}
        {chartData.length > 0 && (
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <h2 className="text-2xl font-bold text-white mb-4">Cumulative Profit/Loss</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis dataKey="date" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" tickFormatter={(value) => `$${value}`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="cumulative_profit"
                  stroke="#10b981"
                  strokeWidth={3}
                  name="Cumulative P/L"
                  dot={{ fill: '#10b981', r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* By Sport */}
        {summary.by_sport.length > 0 && (
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <h2 className="text-2xl font-bold text-white mb-4">Performance by Sport</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-white">
                <thead>
                  <tr className="border-b border-slate-600">
                    <th className="text-left py-3 px-4">Sport</th>
                    <th className="text-right py-3 px-4">Predictions</th>
                    <th className="text-right py-3 px-4">Record</th>
                    <th className="text-right py-3 px-4">Win Rate</th>
                    <th className="text-right py-3 px-4">Profit/Loss</th>
                    <th className="text-right py-3 px-4">ROI</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.by_sport.map((sport) => (
                    <tr key={sport.sport} className="border-b border-slate-700 hover:bg-slate-700/30">
                      <td className="py-3 px-4 font-semibold">{sport.sport}</td>
                      <td className="text-right py-3 px-4">{sport.count}</td>
                      <td className="text-right py-3 px-4">{sport.wins}W - {sport.losses}L</td>
                      <td className="text-right py-3 px-4">{sport.win_rate.toFixed(1)}%</td>
                      <td className={`text-right py-3 px-4 font-bold ${sport.profit_loss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {formatCurrency(sport.profit_loss)}
                      </td>
                      <td className={`text-right py-3 px-4 font-bold ${getROIColor(sport.roi)}`}>
                        {sport.roi >= 0 ? '+' : ''}{sport.roi.toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Recent Predictions */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <h2 className="text-2xl font-bold text-white mb-4">Recent Predictions</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-white text-sm">
              <thead>
                <tr className="border-b border-slate-600">
                  <th className="text-left py-3 px-2">Date</th>
                  <th className="text-left py-3 px-2">Sport</th>
                  <th className="text-left py-3 px-2">Game</th>
                  <th className="text-left py-3 px-2">Bet Type</th>
                  <th className="text-left py-3 px-2">Pick</th>
                  <th className="text-center py-3 px-2">Result</th>
                  <th className="text-right py-3 px-2">P/L</th>
                </tr>
              </thead>
              <tbody>
                {predictions.slice(0, 50).map((pred, idx) => (
                  <tr key={idx} className="border-b border-slate-700 hover:bg-slate-700/30">
                    <td className="py-3 px-2 whitespace-nowrap">{pred.game_date}</td>
                    <td className="py-3 px-2">
                      <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded">
                        {pred.sport}
                      </span>
                    </td>
                    <td className="py-3 px-2">
                      <div className="text-xs">
                        <div>{pred.away_team} @ {pred.home_team}</div>
                        {pred.away_score !== null && pred.home_score !== null && (
                          <div className="text-slate-400">Final: {pred.away_score} - {pred.home_score}</div>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-2">
                      <span className="bg-slate-700 text-white text-xs px-2 py-1 rounded">
                        {pred.bet_type}
                      </span>
                    </td>
                    <td className="py-3 px-2 font-semibold">{pred.recommendation}</td>
                    <td className="py-3 px-2 text-center">
                      <span className={`${getResultBadge(pred.result)} text-xs px-2 py-1 rounded font-bold`}>
                        {pred.result}
                      </span>
                    </td>
                    <td className={`text-right py-3 px-2 font-bold ${pred.profit_loss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatCurrency(pred.profit_loss)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}
