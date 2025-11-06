import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getApiUrl } from '../config';

interface MetricsData {
  userMetrics: {
    winRate: number;
    totalUnits: number;
    roi: number;
    activeBets: number;
  };
}

export function OddsMetricsDashboard() {
  const { username } = useAuth();
  const [metrics, setMetrics] = useState<MetricsData>({
    userMetrics: {
      winRate: 0,
      totalUnits: 0,
      roi: 0,
      activeBets: 0
    }
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [username]);

  const fetchMetrics = async () => {
    try {
      // Fetch user betting metrics from real endpoint
      let userData = null;
      if (username) {
        const userResponse = await fetch(getApiUrl(`bets/user/${username}/stats`)).catch(() => null);
        userData = userResponse?.ok ? await userResponse.json().catch(() => null) : null;
      }

      // Calculate total units from profit (assuming $100 per unit)
      const totalUnits = userData ? (userData.net_profit_loss / 100) : 0;

      setMetrics({
        userMetrics: {
          winRate: userData?.win_rate || 0,
          totalUnits: totalUnits,
          roi: userData?.roi_percent || 0,
          activeBets: userData?.settled_bets || 0
        }
      });
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-20 bg-slate-800/50 border border-slate-700 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Users Results Section - Matches Strategy Results Page */}
      <div className="mb-3">
        <h2 className="text-sm font-bold text-blue-300 mb-2">Users Results</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
          {/* Win Rate */}
          <div className="bg-gradient-to-br from-green-900/50 to-green-800/30 border border-green-700 rounded-lg p-1.5">
            <div className="text-green-400 text-xs font-semibold mb-0">Win Rate</div>
            <div className="text-white text-3xl font-bold leading-tight">
              {metrics.userMetrics.winRate > 0 ? `${metrics.userMetrics.winRate.toFixed(1)}%` : '--'}
            </div>
            <div className="text-green-300 text-xs mt-0">
              {metrics.userMetrics.winRate > 0 ? 'From graded bets' : 'No graded bets yet'}
            </div>
          </div>

          {/* ROI */}
          <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border border-blue-700 rounded-lg p-1.5">
            <div className="text-blue-400 text-xs font-semibold mb-0">ROI</div>
            <div className="text-white text-3xl font-bold leading-tight">
              {metrics.userMetrics.roi !== 0 ? `${metrics.userMetrics.roi >= 0 ? '+' : ''}${metrics.userMetrics.roi.toFixed(1)}%` : '--'}
            </div>
            <div className="text-blue-300 text-xs mt-0">From My Bets</div>
          </div>

          {/* Total Bets */}
          <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border border-purple-700 rounded-lg p-1.5">
            <div className="text-purple-400 text-xs font-semibold mb-0">Total Bets</div>
            <div className="text-white text-3xl font-bold leading-tight">
              {metrics.userMetrics.activeBets || '--'}
            </div>
            <div className="text-purple-300 text-xs mt-0">Graded</div>
          </div>

          {/* Total Profit */}
          <div className="bg-gradient-to-br from-amber-900/50 to-amber-800/30 border border-amber-700 rounded-lg p-1.5">
            <div className="text-amber-400 text-xs font-semibold mb-0">Total Profit</div>
            <div className="text-white text-3xl font-bold leading-tight">
              {metrics.userMetrics.totalUnits !== 0
                ? `${metrics.userMetrics.totalUnits >= 0 ? '+' : ''}$${(metrics.userMetrics.totalUnits * 100).toFixed(0)}`
                : '--'}
            </div>
            <div className="text-amber-300 text-xs mt-0">
              {metrics.userMetrics.totalUnits !== 0
                ? `${metrics.userMetrics.totalUnits >= 0 ? '+' : ''}${metrics.userMetrics.totalUnits.toFixed(1)}u`
                : 'Place bets to track'}
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fade-in {
          animation: fade-in 0.5s ease-out;
        }
      `}</style>
    </div>
  );
}
