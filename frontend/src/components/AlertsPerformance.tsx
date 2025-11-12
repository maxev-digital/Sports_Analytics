import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';

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
  result: string;
  profit_loss: number;
}

export function AlertsPerformance() {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(25);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    fetchRecentPredictions();
  }, [currentPage]);

  const fetchRecentPredictions = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch more than we need to enable proper pagination
      const url = `${getApiUrl('performance/recent-predictions')}?limit=500`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error('Failed to fetch predictions');
      }

      const data = await response.json();
      const allPredictions = data.predictions || [];

      // Calculate pagination
      const total = Math.ceil(allPredictions.length / pageSize);
      setTotalPages(total);

      // Get current page slice
      const startIdx = (currentPage - 1) * pageSize;
      const endIdx = startIdx + pageSize;
      setPredictions(allPredictions.slice(startIdx, endIdx));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error fetching predictions:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}$${value.toFixed(2)}`;
  };

  // Round to nearest 0.5 (so -9.7 becomes -9.5, -10.3 becomes -10.5)
  const roundToHalf = (num: number): number => {
    return Math.round(num * 2) / 2;
  };

  const formatBettingLine = (betType: string, marketTotal: number | null) => {
    if (marketTotal === null) return '-';

    if (betType === 'TOTALS') {
      const rounded = roundToHalf(marketTotal);
      return `O/U ${rounded % 1 === 0 ? rounded.toFixed(0) : rounded.toFixed(1)}`;
    } else if (betType === 'SPREADS') {
      const rounded = roundToHalf(marketTotal);
      const sign = rounded >= 0 ? '+' : '';
      return `${sign}${rounded % 1 === 0 ? rounded.toFixed(0) : rounded.toFixed(1)}`;
    } else if (betType === 'MONEYLINE') {
      // Convert probability to American odds
      if (marketTotal > 0 && marketTotal < 1) {
        const odds = marketTotal >= 0.5
          ? Math.round(-100 * marketTotal / (1 - marketTotal))
          : Math.round(100 * (1 - marketTotal) / marketTotal);
        return odds >= 0 ? `+${odds}` : `${odds}`;
      }
      return marketTotal.toFixed(0);
    }
    return marketTotal.toFixed(1);
  };

  // Get team name for spread/moneyline recommendations
  const getTeamForRecommendation = (recommendation: string, homeTeam: string, awayTeam: string, betType: string): string => {
    if (betType === 'TOTALS') {
      return recommendation; // OVER/UNDER
    }

    // For SPREADS and MONEYLINE, replace HOME/AWAY with actual team names
    if (recommendation === 'HOME') {
      return homeTeam;
    } else if (recommendation === 'AWAY') {
      return awayTeam;
    }

    return recommendation; // Fallback
  };

  const getResultBadge = (result: string) => {
    if (result === 'WIN') return 'bg-green-600 text-white';
    if (result === 'LOSS') return 'bg-red-600 text-white';
    return 'bg-gray-600 text-white';
  };

  const getSportBadge = (sport: string) => {
    if (sport === 'NBA' || sport === 'NCAAB') return 'bg-orange-600';
    if (sport === 'NFL' || sport === 'NCAAF') return 'bg-green-600';
    if (sport === 'NHL') return 'bg-blue-600';
    return 'bg-purple-600';
  };

  if (loading) {
    return (
      <div className="bg-slate-900 border-2 border-slate-700 rounded-lg p-8">
        <div className="text-white text-center">Loading alerts performance...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-900 border-2 border-red-700 rounded-lg p-8">
        <div className="text-red-400 text-center">Error: {error}</div>
      </div>
    );
  }

  if (predictions.length === 0) {
    return (
      <div className="bg-slate-900 border-2 border-slate-700 rounded-lg p-8">
        <div className="text-slate-400 text-center">No prediction results available yet</div>
      </div>
    );
  }

  // Format date to MM/DD/YYYY
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`;
  };

  // Calculate overall win/loss stats for current page
  const completedBets = predictions.filter(p => p.result !== 'UNKNOWN');
  const wins = predictions.filter(p => p.result === 'WIN').length;
  const losses = predictions.filter(p => p.result === 'LOSS').length;
  const winRate = completedBets.length > 0 ? ((wins / completedBets.length) * 100).toFixed(1) : '0.0';
  const totalPL = predictions.reduce((sum, p) => sum + p.profit_loss, 0);

  return (
    <div className="bg-slate-900 border-4 border-slate-700 rounded-lg p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-4xl font-bold text-white">📊 Alerts Performance</h2>
        <div className="text-right">
          <div className="text-2xl font-bold text-white">{wins}W - {losses}L</div>
          <div className={`text-xl font-bold ${winRate >= '55' ? 'text-green-400' : winRate >= '50' ? 'text-yellow-400' : 'text-red-400'}`}>
            {winRate}% Win Rate
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-white">
          <thead>
            <tr className="border-b-4 border-slate-600">
              <th className="text-left py-4 px-3 text-base font-bold">Date</th>
              <th className="text-left py-4 px-3 text-base font-bold">Sport</th>
              <th className="text-left py-4 px-3 text-base font-bold">Game</th>
              <th className="text-left py-4 px-3 text-base font-bold">Type</th>
              <th className="text-left py-4 px-3 text-base font-bold">Pick</th>
              <th className="text-center py-4 px-3 text-base font-bold">Line</th>
              <th className="text-center py-4 px-3 text-base font-bold">Conf</th>
              <th className="text-right py-4 px-3 text-base font-bold">Score</th>
              <th className="text-center py-4 px-3 text-base font-bold">Result</th>
              <th className="text-right py-4 px-3 text-base font-bold">P/L</th>
            </tr>
          </thead>
          <tbody>
            {predictions.map((pred) => (
              <tr key={pred.prediction_id} className="border-b border-slate-700 hover:bg-slate-800/50">
                <td className="py-4 px-3 whitespace-nowrap text-slate-300 text-base">
                  {formatDate(pred.game_date)}
                </td>
                <td className="py-4 px-3">
                  <span className={`${getSportBadge(pred.sport)} text-white text-sm px-3 py-1 rounded font-bold`}>
                    {pred.sport}
                  </span>
                </td>
                <td className="py-4 px-3">
                  <div className="text-sm">
                    <div className="font-bold">{pred.away_team} @</div>
                    <div className="font-bold">{pred.home_team}</div>
                  </div>
                </td>
                <td className="py-4 px-3">
                  <span className="bg-slate-700 text-slate-200 text-sm px-3 py-1 rounded font-bold">
                    {pred.bet_type}
                  </span>
                </td>
                <td className="py-4 px-3 font-bold text-white text-sm">
                  {getTeamForRecommendation(pred.recommendation, pred.home_team, pred.away_team, pred.bet_type)}
                </td>
                <td className="text-center py-4 px-3">
                  <span className="text-yellow-400 font-bold text-base">
                    {formatBettingLine(pred.bet_type, pred.market_total)}
                  </span>
                </td>
                <td className="text-center py-4 px-3">
                  <span className={`px-3 py-1 rounded text-sm font-bold ${
                    pred.confidence === 'HIGH' ? 'bg-green-700 text-white' :
                    pred.confidence === 'MEDIUM' ? 'bg-yellow-700 text-white' :
                    'bg-slate-600 text-slate-300'
                  }`}>
                    {pred.confidence}
                  </span>
                </td>
                <td className="text-right py-4 px-3 text-base text-slate-300">
                  {pred.away_score !== null && pred.home_score !== null ? (
                    <div className="font-bold">
                      <div>{pred.away_score}</div>
                      <div>{pred.home_score}</div>
                    </div>
                  ) : (
                    <span className="text-slate-500">-</span>
                  )}
                </td>
                <td className="text-center py-4 px-3">
                  <span className={`${getResultBadge(pred.result)} text-sm px-3 py-2 rounded font-bold`}>
                    {pred.result}
                  </span>
                </td>
                <td className={`text-right py-4 px-3 font-bold text-lg ${
                  pred.profit_loss >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {formatCurrency(pred.profit_loss)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="mt-6 pt-6 border-t-4 border-slate-700">
        <div className="flex items-center justify-between text-base mb-6">
          <div className="text-slate-400 text-lg font-bold">
            Showing page {currentPage} of {totalPages} ({predictions.length} results)
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <span className="text-slate-400 text-lg">Page P/L:</span>
              <span className={`font-bold text-2xl ${
                totalPL >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {formatCurrency(totalPL)}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-slate-400 text-lg">Page Record:</span>
              <span className="font-bold text-white text-2xl">
                {wins}W - {losses}L ({winRate}%)
              </span>
            </div>
          </div>
        </div>

        {/* Pagination Buttons */}
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => setCurrentPage(1)}
            disabled={currentPage === 1}
            className={`px-5 py-3 border-2 text-base font-bold ${
              currentPage === 1
                ? 'bg-slate-800 text-slate-600 border-slate-700 cursor-not-allowed'
                : 'bg-slate-900 text-white border-slate-600 hover:border-blue-500'
            }`}
          >
            « First
          </button>
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
            className={`px-5 py-3 border-2 text-base font-bold ${
              currentPage === 1
                ? 'bg-slate-800 text-slate-600 border-slate-700 cursor-not-allowed'
                : 'bg-slate-900 text-white border-slate-600 hover:border-blue-500'
            }`}
          >
            ‹ Prev
          </button>

          {/* Page numbers */}
          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
            let pageNum;
            if (totalPages <= 5) {
              pageNum = i + 1;
            } else if (currentPage <= 3) {
              pageNum = i + 1;
            } else if (currentPage >= totalPages - 2) {
              pageNum = totalPages - 4 + i;
            } else {
              pageNum = currentPage - 2 + i;
            }

            return (
              <button
                key={pageNum}
                onClick={() => setCurrentPage(pageNum)}
                className={`px-5 py-3 border-2 text-base font-bold ${
                  currentPage === pageNum
                    ? 'bg-blue-600 text-white border-blue-500'
                    : 'bg-slate-900 text-white border-slate-600 hover:border-blue-500'
                }`}
              >
                {pageNum}
              </button>
            );
          })}

          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
            className={`px-5 py-3 border-2 text-base font-bold ${
              currentPage === totalPages
                ? 'bg-slate-800 text-slate-600 border-slate-700 cursor-not-allowed'
                : 'bg-slate-900 text-white border-slate-600 hover:border-blue-500'
            }`}
          >
            Next ›
          </button>
          <button
            onClick={() => setCurrentPage(totalPages)}
            disabled={currentPage === totalPages}
            className={`px-5 py-3 border-2 text-base font-bold ${
              currentPage === totalPages
                ? 'bg-slate-800 text-slate-600 border-slate-700 cursor-not-allowed'
                : 'bg-slate-900 text-white border-slate-600 hover:border-blue-500'
            }`}
          >
            Last »
          </button>
        </div>
      </div>
    </div>
  );
}
