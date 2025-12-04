import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { sportEmojis, uiEmojis } from '../utils/sportDetection';

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

interface PropTypeStats {
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
    roi: number;
  };
}

interface ModelStats {
  [key: string]: {
    total: number;
    wins: number;
    win_rate: number;
    roi: number;
  };
}

interface PerformanceOverview {
  summary: PerformanceSummary;
  by_confidence: ConfidenceStats;
  by_prop_type: PropTypeStats;
  by_sport: SportStats;
  by_model: ModelStats;
  filters: {
    sport: string;
    prop_type: string;
    model: string;
    days: number;
  };
  generated_at: string;
}

interface HistoryPeriod {
  period: string;
  predictions: number;
  wins: number;
  losses: number;
  win_rate: number;
  daily_win_rate: number;
  roi: number;
  units_won: number;
}

interface Prediction {
  prediction_date: string;
  game_date: string;
  player_name: string;
  team: string;
  opponent: string;
  prop_type: string;
  market_line: number;
  predicted_value: number;
  actual_value: number | null;
  edge_pct: number;
  recommendation: string;
  confidence: number;
  result: string;
  sport: string;
  model: string;
  profit_loss: number;
}

export function PropsPerformance() {
  const [overview, setOverview] = useState<PerformanceOverview | null>(null);
  const [history, setHistory] = useState<HistoryPeriod[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [predictionsTotal, setPredictionsTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedSport, setSelectedSport] = useState('all');
  const [selectedPropType, setSelectedPropType] = useState('all');
  const [selectedModel, setSelectedModel] = useState('all');
  const [days, setDays] = useState(30);
  const [unitSize, setUnitSize] = useState(100);
  const [startingBankroll, setStartingBankroll] = useState(10000);

  const sports = [
    { key: 'all', name: 'All Sports', emoji: uiEmojis.target },
    { key: 'nba', name: 'NBA', emoji: sportEmojis.NBA },
    { key: 'ncaab', name: 'NCAAB', emoji: sportEmojis.NCAAB },
    { key: 'nfl', name: 'NFL', emoji: sportEmojis.NFL },
    { key: 'nhl', name: 'NHL', emoji: sportEmojis.NHL },
    { key: 'ncaaf', name: 'NCAAF', emoji: sportEmojis.NCAAF },
  ];

  const propTypes = [
    { key: 'all', name: 'All Props' },
    { key: 'points', name: 'Points' },
    { key: 'rebounds', name: 'Rebounds' },
    { key: 'assists', name: 'Assists' },
    { key: 'threes', name: '3-Pointers' },
    { key: 'blocks', name: 'Blocks' },
    { key: 'steals', name: 'Steals' },
    { key: 'PRA', name: 'PRA' },
  ];

  useEffect(() => {
    fetchData();
  }, [selectedSport, selectedPropType, selectedModel, days]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        days: days.toString(),
        limit: '50',
        unit_size: unitSize.toString(),
        bankroll: startingBankroll.toString()
      });
      if (selectedSport !== 'all') params.append('sport', selectedSport);
      if (selectedPropType !== 'all') params.append('prop_type', selectedPropType);
      if (selectedModel !== 'all') params.append('model', selectedModel);

      // BULLETPROOF: Single /api/ui/props-performance call returns everything
      const response = await fetch(getApiUrl(`props-performance?${params.toString()}`));
      const data = await response.json();

      // Backend returns all data pre-calculated
      setOverview(data);
      setHistory(data.history || []);
      setPredictions(data.predictions || []);
      setPredictionsTotal(data.predictions_total || 0);

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
    <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-slate-900 p-6" style={{ fontFamily: 'Rubik, sans-serif' }}>
      <div className="max-w-7xl mx-auto">
        <div className="h-12 w-96 bg-slate-700 rounded animate-pulse mb-2"></div>
        <div className="h-6 w-64 bg-slate-800 rounded animate-pulse mb-8"></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-slate-800 rounded-xl animate-pulse"></div>
          ))}
        </div>
      </div>
    </div>
  );

  if (loading && !overview) {
    return <LoadingSkeleton />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-slate-900 p-6" style={{ fontFamily: 'Rubik, sans-serif' }}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-5xl font-bold italic text-slate-100 mb-2" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>
            PLAYER PROPS PERFORMANCE
          </h1>
          <p className="text-slate-400 text-lg">
            Track player prop prediction accuracy across all sports & prop types
          </p>
        </div>

        {/* Filters */}
        <div className="bg-gradient-to-br from-slate-700 via-slate-800 to-slate-900 border border-white rounded-xl p-4 mb-6">
          <div className="flex gap-4 items-center flex-wrap">
            <div>
              <label className="text-slate-400 text-sm block mb-1">Sport:</label>
              <select
                value={selectedSport}
                onChange={(e) => setSelectedSport(e.target.value)}
                className="px-3 py-2 bg-slate-800 border border-slate-600 hover:border-white transition-all rounded text-white"
              >
                {sports.map(sport => (
                  <option key={sport.key} value={sport.key}>{sport.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-slate-400 text-sm block mb-1">Prop Type:</label>
              <select
                value={selectedPropType}
                onChange={(e) => setSelectedPropType(e.target.value)}
                className="px-3 py-2 bg-slate-800 border border-slate-600 hover:border-white transition-all rounded text-white"
              >
                {propTypes.map(pt => (
                  <option key={pt.key} value={pt.key}>{pt.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-slate-400 text-sm block mb-1">Model:</label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="px-3 py-2 bg-slate-800 border border-slate-600 hover:border-white transition-all rounded text-white"
              >
                <option value="all">All Models</option>
                <option value="ensemble">Ensemble</option>
                <option value="xgboost">XGBoost</option>
                <option value="lightgbm">LightGBM</option>
                <option value="random_forest">Random Forest</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 text-sm block mb-1">Time Range:</label>
              <select
                value={days}
                onChange={(e) => setDays(parseInt(e.target.value))}
                className="px-3 py-2 bg-slate-800 border border-slate-600 hover:border-white transition-all rounded text-white"
              >
                <option value="1">Yesterday</option>
                <option value="7">Last 7 Days</option>
                <option value="30">Last 30 Days</option>
                <option value="60">Last 60 Days</option>
                <option value="90">Last 90 Days</option>
                <option value="365">All Time</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 text-sm block mb-1">Unit Size:</label>
              <select
                value={unitSize}
                onChange={(e) => setUnitSize(parseInt(e.target.value))}
                className="px-3 py-2 bg-slate-800 border border-slate-600 hover:border-white transition-all rounded text-white"
              >
                <option value="25">$25</option>
                <option value="50">$50</option>
                <option value="100">$100</option>
                <option value="200">$200</option>
                <option value="300">$300</option>
                <option value="500">$500</option>
                <option value="1000">$1,000</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 text-sm block mb-1">Starting Bankroll:</label>
              <input
                type="number"
                value={startingBankroll}
                onChange={(e) => setStartingBankroll(parseInt(e.target.value) || 0)}
                className="px-3 py-2 bg-slate-800 border border-slate-600 hover:border-white transition-all rounded text-white w-32"
                placeholder="10000"
                step="1000"
                min="0"
              />
            </div>
          </div>
        </div>

        {/* Summary Cards */}
        {overview && overview.summary && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
            <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
              <div className="text-slate-400 text-sm mb-1">Win Rate</div>
              <div className="text-3xl font-bold text-blue-400">{formatPercent(overview.summary.win_rate)}</div>
              <div className="text-slate-500 text-xs mt-2">{overview.summary.wins}W - {overview.summary.losses}L</div>
            </div>

            <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
              <div className="text-slate-400 text-sm mb-1">ROI</div>
              <div className={`text-3xl font-bold ${overview.summary.roi >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {overview.summary.roi >= 0 ? '+' : ''}{overview.summary.roi.toFixed(1)}%
              </div>
              <div className="text-slate-500 text-xs mt-2">{overview.summary.units_won.toFixed(2)} units</div>
            </div>

            <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
              <div className="text-slate-400 text-sm mb-1">Profit/Loss (${unitSize})</div>
              <div className={`text-3xl font-bold ${overview.summary.units_won >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {overview.summary.units_won >= 0 ? '+' : ''}${(overview.summary.units_won * unitSize).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
              </div>
              <div className="text-slate-500 text-xs mt-2">Based on ${unitSize.toLocaleString()}/bet</div>
            </div>

            <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
              <div className="text-slate-400 text-sm mb-1">Predictions</div>
              <div className="text-3xl font-bold text-purple-400">{overview.summary.total_predictions}</div>
              <div className="text-slate-500 text-xs mt-2">{overview.summary.pushes} pushes</div>
            </div>

            <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
              <div className="text-slate-400 text-sm mb-1">Units Won</div>
              <div className="text-3xl font-bold text-orange-400">{overview.summary.units_won >= 0 ? '+' : ''}{overview.summary.units_won.toFixed(2)}</div>
              <div className="text-slate-500 text-xs mt-2">Avg Edge: {overview.summary.avg_edge.toFixed(1)}%</div>
            </div>
          </div>
        )}

        {/* Bankroll & Kelly Cards */}
        {overview && overview.summary && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            {/* Bankroll Status */}
            <div className="bg-gradient-to-br from-emerald-900 via-emerald-950 to-black border border-emerald-600 rounded-xl p-6">
              <div className="flex items-center gap-2 mb-3">
                <img src={uiEmojis.star} alt="Bankroll" className="w-6 h-6" />
                <h3 className="text-lg font-bold text-emerald-200">Bankroll Status</h3>
              </div>
              {(() => {
                const totalPL = overview.summary.units_won * unitSize;
                const currentBankroll = startingBankroll + totalPL;
                const percentChange = ((currentBankroll - startingBankroll) / startingBankroll) * 100;
                const unitsRemaining = Math.floor(currentBankroll / unitSize);

                return (
                  <div className="space-y-3">
                    <div>
                      <div className="text-xs text-emerald-400 mb-1">Current Bankroll</div>
                      <div className={`text-3xl font-bold ${currentBankroll >= startingBankroll ? 'text-green-300' : 'text-red-300'}`}>
                        ${currentBankroll.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-emerald-400">% Change</div>
                        <div className={`font-semibold ${percentChange >= 0 ? 'text-green-300' : 'text-red-300'}`}>
                          {percentChange >= 0 ? '+' : ''}{percentChange.toFixed(1)}%
                        </div>
                      </div>
                      <div>
                        <div className="text-emerald-400">Units Left</div>
                        <div className="font-semibold text-emerald-200">{unitsRemaining}</div>
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>

            {/* Kelly Criterion */}
            <div className="bg-gradient-to-br from-amber-900 via-amber-950 to-black border border-amber-600 rounded-xl p-6">
              <div className="flex items-center gap-2 mb-3">
                <img src={uiEmojis.lightning} alt="Kelly" className="w-6 h-6" />
                <h3 className="text-lg font-bold text-amber-200">Kelly Criterion Risk Levels</h3>
              </div>
              {(() => {
                const aggressivePercent = 0.05;
                const moderatePercent = 0.025;
                const conservativePercent = 0.0125;

                const aggressiveAmount = startingBankroll * aggressivePercent;
                const moderateAmount = startingBankroll * moderatePercent;
                const conservativeAmount = startingBankroll * conservativePercent;

                const recommendedBankrollConservative = unitSize / conservativePercent;
                const recommendedBankrollModerate = unitSize / moderatePercent;
                const recommendedBankrollAggressive = unitSize / aggressivePercent;

                const currentPercent = unitSize / startingBankroll;
                let closestLevel = 'moderate';
                if (Math.abs(currentPercent - conservativePercent) < Math.abs(currentPercent - moderatePercent)) {
                  closestLevel = 'conservative';
                }
                if (Math.abs(currentPercent - aggressivePercent) < Math.abs(currentPercent - moderatePercent) &&
                    Math.abs(currentPercent - aggressivePercent) < Math.abs(currentPercent - conservativePercent)) {
                  closestLevel = 'aggressive';
                }

                return (
                  <div className="space-y-3">
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div className={`bg-amber-950/50 rounded p-2 border-2 ${closestLevel === 'conservative' ? 'border-green-500' : 'border-transparent'}`}>
                        <div className="text-amber-400 font-semibold">Conservative</div>
                        <div className="font-bold text-amber-200 text-sm">${Math.round(conservativeAmount).toLocaleString()}</div>
                        <div className="text-amber-500 text-[10px] mb-1">1.25% Kelly</div>
                        <div className="text-[9px] text-amber-600 leading-tight">
                          Your ${unitSize}: needs ${Math.round(recommendedBankrollConservative).toLocaleString()} roll
                        </div>
                      </div>
                      <div className={`bg-amber-950/50 rounded p-2 border-2 ${closestLevel === 'moderate' ? 'border-blue-500' : 'border-transparent'}`}>
                        <div className="text-amber-400 font-semibold">Moderate</div>
                        <div className="font-bold text-amber-200 text-sm">${Math.round(moderateAmount).toLocaleString()}</div>
                        <div className="text-amber-500 text-[10px] mb-1">2.5% Kelly</div>
                        <div className="text-[9px] text-amber-600 leading-tight">
                          Your ${unitSize}: needs ${Math.round(recommendedBankrollModerate).toLocaleString()} roll
                        </div>
                      </div>
                      <div className={`bg-amber-950/50 rounded p-2 border-2 ${closestLevel === 'aggressive' ? 'border-red-500' : 'border-transparent'}`}>
                        <div className="text-amber-400 font-semibold">Aggressive</div>
                        <div className="font-bold text-amber-200 text-sm">${Math.round(aggressiveAmount).toLocaleString()}</div>
                        <div className="text-amber-500 text-[10px] mb-1">5% Kelly</div>
                        <div className="text-[9px] text-amber-600 leading-tight">
                          Your ${unitSize}: needs ${Math.round(recommendedBankrollAggressive).toLocaleString()} roll
                        </div>
                      </div>
                    </div>
                    <div className="text-[10px] text-amber-400 text-center pt-1">
                      Current: ${unitSize} unit = {((unitSize/startingBankroll)*100).toFixed(2)}% of bankroll
                      {closestLevel === 'conservative' && ' - Conservative approach'}
                      {closestLevel === 'moderate' && ' - Moderate risk'}
                      {closestLevel === 'aggressive' && ' - High risk'}
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>
        )}

        {/* Dynamic Analytics Cards */}
        {overview && overview.summary && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            {/* Break-Even Calculator */}
            <div className="bg-gradient-to-br from-blue-900 via-blue-950 to-black border border-blue-600 rounded-xl p-6">
              <div className="flex items-center gap-2 mb-3">
                <img src={uiEmojis.target} alt="Target" className="w-6 h-6" />
                <h3 className="text-lg font-bold text-blue-200">Break-Even Target</h3>
              </div>
              {(() => {
                const currentWins = overview.summary.wins;
                const currentLosses = overview.summary.losses;
                const currentTotal = currentWins + currentLosses;
                const breakEvenRate = 0.524;
                const neededWins = Math.ceil(currentTotal * breakEvenRate);
                const winsNeeded = neededWins - currentWins;
                const isBreakEven = overview.summary.units_won >= 0;

                return (
                  <div className="space-y-2">
                    <div className="text-2xl font-bold text-blue-300">
                      {isBreakEven ? 'Profitable!' : `${winsNeeded} more wins`}
                    </div>
                    <div className="text-sm text-blue-400">
                      {isBreakEven
                        ? `You're ${Math.abs(currentWins - neededWins)} wins above break-even`
                        : `Need ${neededWins} total wins (52.4%) to break even at -110 odds`
                      }
                    </div>
                  </div>
                );
              })()}
            </div>

            {/* Best Performing Period */}
            <div className="bg-gradient-to-br from-green-900 via-green-950 to-black border border-green-600 rounded-xl p-6">
              <div className="flex items-center gap-2 mb-3">
                <img src={uiEmojis.fire} alt="Fire" className="w-6 h-6" />
                <h3 className="text-lg font-bold text-green-200">Best Day</h3>
              </div>
              {(() => {
                if (history.length === 0) return <div className="text-green-400">No data yet</div>;
                const bestDay = history.reduce((best, current) =>
                  (current.wins - current.losses) > (best.wins - best.losses) ? current : best
                );
                const dayUnits = (bestDay.wins * 0.91) - bestDay.losses;
                return (
                  <div className="space-y-2">
                    <div className="text-2xl font-bold text-green-300">
                      +${(dayUnits * unitSize).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                    </div>
                    <div className="text-sm text-green-400">
                      {bestDay.period} - {bestDay.wins}W-{bestDay.losses}L ({(bestDay.daily_win_rate * 100).toFixed(1)}%)
                    </div>
                  </div>
                );
              })()}
            </div>

            {/* Projection Calculator */}
            <div className="bg-gradient-to-br from-purple-900 via-purple-950 to-black border border-purple-600 rounded-xl p-6">
              <div className="flex items-center gap-2 mb-3">
                <img src={uiEmojis.lightning} alt="Lightning" className="w-6 h-6" />
                <h3 className="text-lg font-bold text-purple-200">100-Bet Projection</h3>
              </div>
              {(() => {
                const avgProfitPerBet = overview.summary.total_predictions > 0
                  ? overview.summary.units_won / overview.summary.total_predictions
                  : 0;
                const projection100 = avgProfitPerBet * 100 * unitSize;
                const isPositive = projection100 >= 0;

                return (
                  <div className="space-y-2">
                    <div className={`text-2xl font-bold ${isPositive ? 'text-green-300' : 'text-red-300'}`}>
                      {isPositive ? '+' : ''}${projection100.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                    </div>
                    <div className="text-sm text-purple-400">
                      If current {(overview.summary.win_rate * 100).toFixed(1)}% win rate continues
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>
        )}

        {/* Performance Charts */}
        {history.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Win Rate Over Time */}
            <div className="bg-gradient-to-br from-black via-gray-900 to-slate-900 border border-white rounded-xl p-6">
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
            <div className="bg-gradient-to-br from-black via-gray-900 to-slate-900 border border-white rounded-xl p-6">
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

            {/* Profit/Loss Over Time */}
            <div className="bg-gradient-to-br from-black via-gray-900 to-slate-900 border border-white rounded-xl p-6">
              <h3 className="text-xl font-bold text-slate-100 mb-4">Profit/Loss (${unitSize.toLocaleString()} Bets)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={history.map(h => ({ ...h, profit_dollars: h.units_won * unitSize }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="period" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" tickFormatter={(value) => `$${value.toFixed(0)}`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                    formatter={(value: any) => `$${value.toFixed(2)}`}
                  />
                  <Line type="monotone" dataKey="profit_dollars" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Units Won Over Time */}
            <div className="bg-gradient-to-br from-black via-gray-900 to-slate-900 border border-white rounded-xl p-6">
              <h3 className="text-xl font-bold text-slate-100 mb-4">Units Won Over Time</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="period" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" tickFormatter={(value) => `${value.toFixed(1)}u`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                    formatter={(value: any) => `${value.toFixed(2)} units`}
                  />
                  <Line type="monotone" dataKey="units_won" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Performance by Prop Type */}
        {overview && overview.by_prop_type && Object.keys(overview.by_prop_type).length > 0 && (
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-slate-100 mb-4">Performance by Prop Type</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(overview.by_prop_type)
                .sort((a, b) => b[1].win_rate - a[1].win_rate)
                .map(([propType, stats]: [string, any]) => (
                  <div key={propType} className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
                    <div className="flex justify-between items-start mb-4">
                      <h3 className="text-lg font-bold text-slate-100 uppercase">{propType}</h3>
                      <div className="text-right">
                        <div className={`text-2xl font-bold ${stats.win_rate >= 0.55 ? 'text-green-400' : stats.win_rate >= 0.50 ? 'text-yellow-400' : 'text-red-400'}`}>
                          {formatPercent(stats.win_rate)}
                        </div>
                        <div className="text-xs text-slate-400">Win Rate</div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Record:</span>
                        <span className="text-slate-200 font-semibold">{stats.wins}W - {stats.total - stats.wins}L</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">ROI:</span>
                        <span className={`font-semibold ${stats.roi >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {stats.roi >= 0 ? '+' : ''}{stats.roi.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Performance by Confidence Level */}
        {overview && overview.by_confidence && Object.keys(overview.by_confidence).length > 0 && (
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-slate-100 mb-4">Performance by Confidence Level</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {Object.entries(overview.by_confidence).map(([level, stats]: [string, any]) => {
                const confidenceConfig = {
                  'high': { gradient: 'from-slate-800 via-slate-900 to-black border-white', icon: uiEmojis.fire },
                  'medium': { gradient: 'from-slate-800 via-slate-900 to-black border-white', icon: uiEmojis.lightning },
                  'low': { gradient: 'from-slate-800 via-slate-900 to-black border-white', icon: uiEmojis.star },
                };
                const config = confidenceConfig[level as keyof typeof confidenceConfig] || confidenceConfig.low;

                return (
                  <div key={level} className={`bg-gradient-to-br ${config.gradient} border rounded-xl p-6`}>
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex items-center gap-2">
                        <img src={config.icon} alt={level} className="w-8 h-8" />
                        <h3 className="text-lg font-bold text-slate-100 uppercase">{level}</h3>
                      </div>
                      <div className="text-right">
                        <div className={`text-2xl font-bold ${stats.win_rate >= 0.55 ? 'text-green-400' : stats.win_rate >= 0.50 ? 'text-yellow-400' : 'text-red-400'}`}>
                          {formatPercent(stats.win_rate)}
                        </div>
                        <div className="text-xs text-slate-400">Win Rate</div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Record:</span>
                        <span className="text-slate-200 font-semibold">{stats.wins}W - {stats.total - stats.wins}L</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">ROI:</span>
                        <span className={`font-semibold ${stats.roi >= 10 ? 'text-green-400' : stats.roi >= 0 ? 'text-yellow-400' : 'text-red-400'}`}>
                          {stats.roi > 0 ? '+' : ''}{stats.roi.toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Total Picks:</span>
                        <span className="text-slate-200 font-semibold">{stats.total}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Performance by Sport */}
        {overview && overview.by_sport && Object.keys(overview.by_sport).length > 0 && (
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-slate-100 mb-4">Performance by Sport</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(overview.by_sport)
                .sort((a, b) => b[1].win_rate - a[1].win_rate)
                .map(([sportKey, stats]: [string, any]) => {
                  const sportInfo = sports.find(s => s.key === sportKey) || { emoji: uiEmojis.target, name: sportKey.toUpperCase() };

                  return (
                    <div key={sportKey} className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center gap-2">
                          <img src={sportInfo.emoji} alt={sportInfo.name} className="w-10 h-10" />
                          <h3 className="text-lg font-bold text-slate-100">{sportInfo.name}</h3>
                        </div>
                        <div className="text-right">
                          <div className={`text-2xl font-bold ${stats.win_rate >= 0.55 ? 'text-green-400' : stats.win_rate >= 0.50 ? 'text-yellow-400' : 'text-red-400'}`}>
                            {formatPercent(stats.win_rate)}
                          </div>
                          <div className="text-xs text-slate-400">Win Rate</div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Record:</span>
                          <span className="text-slate-200 font-semibold">{stats.wins}W - {stats.total - stats.wins}L</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">ROI:</span>
                          <span className={`font-semibold ${stats.roi >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {stats.roi >= 0 ? '+' : ''}{stats.roi.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        )}

        {/* Performance by Model */}
        {overview && overview.by_model && Object.keys(overview.by_model).length > 0 && (
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-slate-100 mb-4">Performance by Model</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(overview.by_model)
                .sort((a, b) => b[1].win_rate - a[1].win_rate)
                .map(([model, stats]: [string, any]) => (
                  <div key={model} className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
                    <div className="flex justify-between items-start mb-4">
                      <h3 className="text-lg font-bold text-slate-100 uppercase">{model.replace('_', ' ')}</h3>
                      <div className="text-right">
                        <div className={`text-2xl font-bold ${stats.win_rate >= 0.55 ? 'text-green-400' : stats.win_rate >= 0.50 ? 'text-yellow-400' : 'text-red-400'}`}>
                          {formatPercent(stats.win_rate)}
                        </div>
                        <div className="text-xs text-slate-400">Win Rate</div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Record:</span>
                        <span className="text-slate-200 font-semibold">{stats.wins}W - {stats.total - stats.wins}L</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">ROI:</span>
                        <span className={`font-semibold ${stats.roi >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {stats.roi >= 0 ? '+' : ''}{stats.roi.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Recent Predictions Table */}
        {predictions.length > 0 && (
          <div className="bg-gradient-to-br from-black via-gray-900 to-slate-900 border border-white rounded-xl p-6 mb-8">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-2xl font-bold text-slate-100">Recent Predictions ({predictionsTotal} total)</h3>
              <div className="text-slate-400 text-sm">Showing last 50</div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-800/50 border-b border-slate-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-slate-300">Date</th>
                    <th className="px-4 py-3 text-left text-slate-300">Player</th>
                    <th className="px-4 py-3 text-left text-slate-300">Prop</th>
                    <th className="px-4 py-3 text-right text-slate-300">Line</th>
                    <th className="px-4 py-3 text-right text-slate-300">Pred</th>
                    <th className="px-4 py-3 text-right text-slate-300">Actual</th>
                    <th className="px-4 py-3 text-center text-slate-300">Pick</th>
                    <th className="px-4 py-3 text-center text-slate-300">Result</th>
                    <th className="px-4 py-3 text-right text-slate-300">P/L</th>
                  </tr>
                </thead>
                <tbody>
                  {predictions.map((pred, idx) => (
                    <tr key={`${pred.game_date}-${pred.player_name}-${pred.prop_type}`} className={`border-b border-slate-800 ${idx % 2 === 0 ? 'bg-slate-900/50' : 'bg-slate-800/30'}`}>
                      <td className="px-4 py-3 text-slate-400 whitespace-nowrap">{pred.game_date}</td>
                      <td className="px-4 py-3">
                        <div className="text-slate-200 font-medium">{pred.player_name}</div>
                        <div className="text-xs text-slate-500">{pred.team} vs {pred.opponent}</div>
                      </td>
                      <td className="px-4 py-3 text-slate-400 uppercase text-xs">{pred.prop_type}</td>
                      <td className="px-4 py-3 text-right text-slate-400">{pred.market_line?.toFixed(1)}</td>
                      <td className="px-4 py-3 text-right text-slate-300">{pred.predicted_value?.toFixed(1)}</td>
                      <td className="px-4 py-3 text-right font-semibold text-slate-200">
                        {pred.actual_value ? pred.actual_value.toFixed(1) : '-'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          pred.recommendation === 'OVER' ? 'bg-green-900/40 text-green-400 border border-green-700' :
                          'bg-red-900/40 text-red-400 border border-red-700'
                        }`}>
                          {pred.recommendation}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                          pred.result === 'WIN' ? 'bg-green-900/50 text-green-300' :
                          pred.result === 'LOSS' ? 'bg-red-900/50 text-red-300' :
                          'bg-slate-800 text-slate-400'
                        }`}>
                          {pred.result}
                        </span>
                      </td>
                      <td className={`px-4 py-3 text-right font-bold ${
                        pred.profit_loss > 0 ? 'text-green-400' : pred.profit_loss < 0 ? 'text-red-400' : 'text-slate-400'
                      }`}>
                        {pred.profit_loss > 0 ? '+' : ''}{pred.profit_loss?.toFixed(2)}u
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* No Data Message */}
        {overview && overview.summary && overview.summary.total_predictions === 0 && (
          <div className="bg-gradient-to-br from-yellow-700 via-yellow-800 to-yellow-900 border border-yellow-600 shadow-yellow-500/50 rounded-xl p-6 text-center">
            <div className="text-2xl mb-2">📊</div>
            <div className="text-yellow-300 font-semibold mb-2">No Performance Data Available</div>
            <div className="text-yellow-200/80 text-sm">
              Props performance tracking will begin once predictions are logged and results are recorded.
              Check back after games complete to see how the models performed.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
