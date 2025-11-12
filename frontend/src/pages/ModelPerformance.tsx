import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface PerformanceSummary {
  total_predictions: number;
  wins: number;
  losses: number;
  pushes: number;
  win_rate: number;
  roi: number;
  avg_edge: number;
  units_won: number;
}

interface ConfidenceStats {
  [key: string]: {
    total: number;
    wins: number;
    win_rate: number;
    roi: number;
  };
}

interface SportStats {
  [key: string]: {
    total: number;
    wins: number;
    win_rate: number;
  };
}

interface ModelStats {
  [key: string]: {
    total: number;
    wins: number;
    win_rate: number;
  };
}

interface PerformanceOverview {
  summary: PerformanceSummary;
  by_confidence: ConfidenceStats;
  by_sport: SportStats;
  by_model: ModelStats;
  filters: {
    sport: string;
    model: string;
    bet_type: string;
    days: number;
  };
  generated_at: string;
}

interface HistoryPeriod {
  period: string;
  predictions: number;
  wins: number;
  win_rate: number;
  roi: number;
  units_won: number;
}

interface ModelInfo {
  name: string;
  description: string;
  markets: string[];
  strength: string;
  performance?: {
    predictions: number;
    win_rate: number;
    last_updated: string;
  };
}

export function ModelPerformance() {
  const [overview, setOverview] = useState<PerformanceOverview | null>(null);
  const [history, setHistory] = useState<HistoryPeriod[]>([]);
  const [modelsInfo, setModelsInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedSport, setSelectedSport] = useState('all');
  const [selectedModel, setSelectedModel] = useState('all');
  const [selectedBetType, setSelectedBetType] = useState('all');
  const [days, setDays] = useState(30);

  const sports = [
    { key: 'all', name: 'All Sports', emoji: '🎯' },
    { key: 'nba', name: 'NBA', emoji: '🏀' },
    { key: 'ncaab', name: 'NCAAB', emoji: '🏀' },
    { key: 'nfl', name: 'NFL', emoji: '🏈' },
    { key: 'nhl', name: 'NHL', emoji: '🏒' },
    { key: 'ncaaf', name: 'NCAAF', emoji: '🏈' },
  ];

  useEffect(() => {
    fetchData();
  }, [selectedSport, selectedModel, selectedBetType, days]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({ days: days.toString() });
      if (selectedSport !== 'all') params.append('sport', selectedSport);
      if (selectedModel !== 'all') params.append('model', selectedModel);
      if (selectedBetType !== 'all') params.append('bet_type', selectedBetType);

      // Fetch overview
      const overviewRes = await fetch(getApiUrl(`model-performance/overview?${params.toString()}`));
      const overviewData = await overviewRes.json();
      setOverview(overviewData);

      // Fetch history
      const historyRes = await fetch(getApiUrl(`model-performance/history?${params.toString()}`));
      const historyData = await historyRes.json();
      setHistory(historyData.history || []);

      // Fetch models info
      const modelsRes = await fetch(getApiUrl('model-performance/models'));
      const modelsData = await modelsRes.json();
      setModelsInfo(modelsData);

      setLoading(false);
    } catch (error) {
      console.error('Error fetching performance data:', error);
      setLoading(false);
    }
  };

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const LoadingSkeleton = () => (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black p-6" style={{ fontFamily: 'Rubik, sans-serif' }}>
      <div className="max-w-7xl mx-auto">
        <div className="h-12 w-96 bg-slate-700 rounded animate-pulse mb-2"></div>
        <div className="h-6 w-64 bg-slate-800 rounded animate-pulse mb-8"></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-slate-800 rounded-lg animate-pulse"></div>
          ))}
        </div>
      </div>
    </div>
  );

  if (loading && !overview) {
    return <LoadingSkeleton />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black p-6" style={{ fontFamily: 'Rubik, sans-serif' }}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-5xl font-bold italic text-slate-100 mb-2" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>
            ML MODEL PERFORMANCE
          </h1>
          <p className="text-slate-400 text-lg">
            Track prediction accuracy and improvement across all models & sports
          </p>
        </div>

        {/* Filters */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 mb-6">
          <div className="flex gap-4 items-center flex-wrap">
            <div>
              <label className="text-slate-400 text-sm block mb-1">Sport:</label>
              <select
                value={selectedSport}
                onChange={(e) => setSelectedSport(e.target.value)}
                className="px-3 py-2 bg-slate-900 border border-slate-600 rounded text-white"
              >
                {sports.map(sport => (
                  <option key={sport.key} value={sport.key}>{sport.emoji} {sport.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-slate-400 text-sm block mb-1">Model:</label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="px-3 py-2 bg-slate-900 border border-slate-600 rounded text-white"
              >
                <option value="all">All Models</option>
                <option value="ensemble">Ensemble</option>
                <option value="xgboost">XGBoost</option>
                <option value="random_forest">Random Forest</option>
                <option value="lightgbm">LightGBM</option>
                <option value="linear_regression">Linear Regression</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 text-sm block mb-1">Bet Type:</label>
              <select
                value={selectedBetType}
                onChange={(e) => setSelectedBetType(e.target.value)}
                className="px-3 py-2 bg-slate-900 border border-slate-600 rounded text-white"
              >
                <option value="all">All Types</option>
                <option value="totals">Totals</option>
                <option value="spreads">Spreads</option>
                <option value="moneyline">Moneyline</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 text-sm block mb-1">Time Range:</label>
              <select
                value={days}
                onChange={(e) => setDays(parseInt(e.target.value))}
                className="px-3 py-2 bg-slate-900 border border-slate-600 rounded text-white"
              >
                <option value="7">Last 7 Days</option>
                <option value="30">Last 30 Days</option>
                <option value="60">Last 60 Days</option>
                <option value="90">Last 90 Days</option>
                <option value="365">All Time</option>
              </select>
            </div>
          </div>
        </div>

        {/* Summary Cards */}
        {overview && overview.summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-gradient-to-br from-blue-900/40 to-blue-800/20 border-2 border-blue-600 rounded-lg p-6">
              <div className="text-slate-400 text-sm mb-1">Win Rate</div>
              <div className="text-4xl font-bold text-blue-400">{formatPercent(overview.summary.win_rate)}</div>
              <div className="text-slate-500 text-xs mt-2">{overview.summary.wins}W - {overview.summary.losses}L</div>
            </div>

            <div className="bg-gradient-to-br from-green-900/40 to-green-800/20 border-2 border-green-600 rounded-lg p-6">
              <div className="text-slate-400 text-sm mb-1">ROI</div>
              <div className={`text-4xl font-bold ${overview.summary.roi >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {overview.summary.roi >= 0 ? '+' : ''}{overview.summary.roi.toFixed(1)}%
              </div>
              <div className="text-slate-500 text-xs mt-2">{overview.summary.units_won.toFixed(2)} units</div>
            </div>

            <div className="bg-gradient-to-br from-purple-900/40 to-purple-800/20 border-2 border-purple-600 rounded-lg p-6">
              <div className="text-slate-400 text-sm mb-1">Predictions</div>
              <div className="text-4xl font-bold text-purple-400">{overview.summary.total_predictions}</div>
              <div className="text-slate-500 text-xs mt-2">{overview.summary.pushes} pushes</div>
            </div>

            <div className="bg-gradient-to-br from-amber-900/40 to-amber-800/20 border-2 border-amber-600 rounded-lg p-6">
              <div className="text-slate-400 text-sm mb-1">Avg Edge</div>
              <div className="text-4xl font-bold text-amber-400">+{overview.summary.avg_edge.toFixed(1)}</div>
              <div className="text-slate-500 text-xs mt-2">points/probability</div>
            </div>
          </div>
        )}

        {/* Performance Charts */}
        {history.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Win Rate Over Time */}
            <div className="bg-slate-900 border-2 border-slate-700 rounded-lg p-6">
              <h3 className="text-xl font-bold text-slate-100 mb-4">Win Rate Over Time</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="period" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" tickFormatter={(value) => `${(value * 100).toFixed(0)}%`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                    formatter={(value: any) => `${(value * 100).toFixed(1)}%`}
                  />
                  <Line type="monotone" dataKey="win_rate" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* ROI Over Time */}
            <div className="bg-slate-900 border-2 border-slate-700 rounded-lg p-6">
              <h3 className="text-xl font-bold text-slate-100 mb-4">ROI Over Time</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="period" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" tickFormatter={(value) => `${value.toFixed(0)}%`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                    formatter={(value: any) => `${value.toFixed(1)}%`}
                  />
                  <Line type="monotone" dataKey="roi" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Performance Breakdown Tables */}
        {overview && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* By Confidence */}
            {overview.by_confidence && Object.keys(overview.by_confidence).length > 0 && (
              <div className="bg-slate-900 border-2 border-slate-700 rounded-lg p-6">
                <h3 className="text-xl font-bold text-slate-100 mb-4">By Confidence Level</h3>
                <div className="space-y-3">
                  {Object.entries(overview.by_confidence).map(([level, stats]) => (
                    <div key={level} className="bg-slate-800/50 rounded p-3">
                      <div className="flex justify-between items-center mb-2">
                        <span className={`text-sm font-semibold uppercase ${
                          level === 'high' ? 'text-green-400' :
                          level === 'medium' ? 'text-yellow-400' : 'text-red-400'
                        }`}>{level}</span>
                        <span className="text-slate-300 font-bold">{formatPercent(stats.win_rate)}</span>
                      </div>
                      <div className="text-xs text-slate-500">
                        {stats.wins}/{stats.total} picks • ROI: {stats.roi.toFixed(1)}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* By Sport */}
            {overview.by_sport && Object.keys(overview.by_sport).length > 0 && (
              <div className="bg-slate-900 border-2 border-slate-700 rounded-lg p-6">
                <h3 className="text-xl font-bold text-slate-100 mb-4">By Sport</h3>
                <div className="space-y-3">
                  {Object.entries(overview.by_sport).sort((a, b) => b[1].win_rate - a[1].win_rate).map(([sport, stats]) => (
                    <div key={sport} className="bg-slate-800/50 rounded p-3">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-semibold uppercase text-slate-300">{sport}</span>
                        <span className="text-slate-300 font-bold">{formatPercent(stats.win_rate)}</span>
                      </div>
                      <div className="text-xs text-slate-500">
                        {stats.wins}/{stats.total} picks
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* By Model */}
            {overview.by_model && Object.keys(overview.by_model).length > 0 && (
              <div className="bg-slate-900 border-2 border-slate-700 rounded-lg p-6">
                <h3 className="text-xl font-bold text-slate-100 mb-4">By Model</h3>
                <div className="space-y-3">
                  {Object.entries(overview.by_model).sort((a, b) => b[1].win_rate - a[1].win_rate).map(([model, stats]) => (
                    <div key={model} className="bg-slate-800/50 rounded p-3">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-semibold text-slate-300">{model.replace('_', ' ').toUpperCase()}</span>
                        <span className="text-slate-300 font-bold">{formatPercent(stats.win_rate)}</span>
                      </div>
                      <div className="text-xs text-slate-500">
                        {stats.wins}/{stats.total} picks
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Model Information */}
        {modelsInfo && modelsInfo.models && (
          <div className="bg-slate-900 border-2 border-slate-700 rounded-lg p-6">
            <h3 className="text-2xl font-bold text-slate-100 mb-6">Model Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(modelsInfo.models.nba).map(([key, model]: [string, any]) => (
                <div key={key} className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                  <h4 className="text-lg font-semibold text-blue-400 mb-2">{model.name}</h4>
                  <p className="text-sm text-slate-400 mb-3">{model.description}</p>
                  <div className="text-xs text-slate-500 mb-2">
                    <strong className="text-slate-300">Strength:</strong> {model.strength}
                  </div>
                  <div className="text-xs text-slate-500">
                    <strong className="text-slate-300">Markets:</strong> {model.markets.join(', ')}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* No Data Message */}
        {overview && overview.summary && overview.summary.total_predictions === 0 && (
          <div className="bg-yellow-900/40 border-2 border-yellow-600 rounded-lg p-6 text-center">
            <div className="text-2xl mb-2">📊</div>
            <div className="text-yellow-300 font-semibold mb-2">No Performance Data Available</div>
            <div className="text-yellow-200/80 text-sm">
              Model performance tracking will begin once predictions are logged and results are recorded.
              Check back after games complete to see how the models performed.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
