import { useState, useEffect } from 'react';

interface MetricCardProps {
  icon: string;
  label: string;
  value: string | number;
  subValue?: string;
  trend?: 'up' | 'down' | 'neutral';
  color?: 'green' | 'blue' | 'purple' | 'yellow' | 'red' | 'slate';
  onClick?: () => void;
}

function MetricCard({ icon, label, value, subValue, trend, color = 'blue', onClick }: MetricCardProps) {
  const colorClasses = {
    green: 'from-green-800/60 via-green-700/50 to-green-800/60 border-green-500/60 hover:border-green-400/80',
    blue: 'from-blue-800/60 via-blue-700/50 to-blue-800/60 border-blue-500/60 hover:border-blue-400/80',
    purple: 'from-purple-800/60 via-purple-700/50 to-purple-800/60 border-purple-500/60 hover:border-purple-400/80',
    yellow: 'from-yellow-800/60 via-yellow-700/50 to-yellow-800/60 border-yellow-500/60 hover:border-yellow-400/80',
    red: 'from-red-800/60 via-red-700/50 to-red-800/60 border-red-500/60 hover:border-red-400/80',
    slate: 'from-slate-800/60 via-slate-700/50 to-slate-800/60 border-slate-500/60 hover:border-slate-400/80'
  };

  const trendIcons = {
    up: '↗',
    down: '↘',
    neutral: '→'
  };

  const trendColors = {
    up: 'text-green-400',
    down: 'text-red-400',
    neutral: 'text-slate-400'
  };

  return (
    <div
      onClick={onClick}
      className={`
        bg-gradient-to-br ${colorClasses[color]}
        border p-1.5
        transition-all duration-200 hover:scale-102 hover:shadow-md
        ${onClick ? 'cursor-pointer' : ''}
        animate-fade-in
      `}
    >
      <div className="flex items-start justify-between mb-0.5">
        <span className="text-sm">{icon}</span>
        {trend && (
          <span className={`text-xs font-bold ${trendColors[trend]}`}>
            {trendIcons[trend]}
          </span>
        )}
      </div>
      <div className="text-lg font-bold text-slate-100 leading-tight">
        {value}
      </div>
      <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide leading-tight">
        {label}
      </div>
      {subValue && (
        <div className="text-[9px] text-slate-500 mt-0.5 font-medium leading-tight">
          {subValue}
        </div>
      )}
    </div>
  );
}

interface MetricsData {
  userMetrics: {
    winRate: number;
    totalUnits: number;
    roi: number;
    activeBets: number;
    weekPL: number;
    winStreak: number;
  };
  systemMetrics: {
    liveGames: number;
    alertsToday: number;
    highConfidence: number;
    alertWinRate: number;
    arbOpportunities: number;
    valueBets: number;
  };
}

export function OddsMetricsDashboard() {
  const [metrics, setMetrics] = useState<MetricsData>({
    userMetrics: {
      winRate: 0,
      totalUnits: 0,
      roi: 0,
      activeBets: 0,
      weekPL: 0,
      winStreak: 0
    },
    systemMetrics: {
      liveGames: 0,
      alertsToday: 0,
      highConfidence: 0,
      alertWinRate: 0,
      arbOpportunities: 0,
      valueBets: 0
    }
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      // Fetch user betting metrics (suppress 404 errors - endpoint may not exist yet)
      const userResponse = await fetch('/api/user/metrics').catch(() => null);
      const userData = userResponse?.ok ? await userResponse.json().catch(() => null) : null;

      // Fetch system/alerts metrics (suppress 404 errors - endpoint may not exist yet)
      const systemResponse = await fetch('/api/system/metrics').catch(() => null);
      const systemData = systemResponse?.ok ? await systemResponse.json().catch(() => null) : null;

      // Fetch current games for live count
      const gamesResponse = await fetch('/api/games').catch(() => null);
      const gamesData = gamesResponse?.ok ? await gamesResponse.json().catch(() => []) : [];

      // Fetch alerts for today (suppress 404 errors - endpoint may not exist yet)
      const alertsResponse = await fetch('/api/alerts').catch(() => null);
      const alertsData = alertsResponse?.ok ? await alertsResponse.json().catch(() => []) : [];

      setMetrics({
        userMetrics: {
          winRate: userData?.win_rate || 0,
          totalUnits: userData?.total_units || 0,
          roi: userData?.roi || 0,
          activeBets: userData?.active_bets || 0,
          weekPL: userData?.week_pl || 0,
          winStreak: userData?.win_streak || 0
        },
        systemMetrics: {
          liveGames: gamesData.filter((g: any) => g.state?.status === 'live').length || 0,
          alertsToday: alertsData.length || 0,
          highConfidence: alertsData.filter((a: any) => a.confidence === 'high').length || 0,
          alertWinRate: systemData?.alert_win_rate || 0,
          arbOpportunities: systemData?.arb_opportunities || 0,
          valueBets: systemData?.value_bets || 0
        }
      });
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const getWinRateColor = (rate: number): 'green' | 'yellow' | 'red' => {
    if (rate >= 55) return 'green';
    if (rate >= 50) return 'yellow';
    return 'red';
  };

  const getUnitsColor = (units: number): 'green' | 'red' | 'slate' => {
    if (units > 0) return 'green';
    if (units < 0) return 'red';
    return 'slate';
  };

  const getTrend = (value: number): 'up' | 'down' | 'neutral' => {
    if (value > 0) return 'up';
    if (value < 0) return 'down';
    return 'neutral';
  };

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="grid grid-cols-6 gap-1.5">
          {[...Array(12)].map((_, i) => (
            <div key={i} className="h-16 bg-slate-800/50 border border-slate-700"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* User Performance Metrics */}
      <div className="mb-1.5">
        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
          <span className="text-xs">📊</span> Your Performance
        </h3>
        <div className="grid grid-cols-6 gap-1.5">
          <MetricCard
            icon="🎯"
            label="Win Rate"
            value={`${metrics.userMetrics.winRate.toFixed(1)}%`}
            trend={metrics.userMetrics.winRate >= 52.4 ? 'up' : 'down'}
            color={getWinRateColor(metrics.userMetrics.winRate)}
          />
          <MetricCard
            icon="💰"
            label="Total Units"
            value={metrics.userMetrics.totalUnits >= 0 ? `+${metrics.userMetrics.totalUnits.toFixed(1)}` : metrics.userMetrics.totalUnits.toFixed(1)}
            trend={getTrend(metrics.userMetrics.totalUnits)}
            color={getUnitsColor(metrics.userMetrics.totalUnits)}
          />
          <MetricCard
            icon="📈"
            label="ROI"
            value={`${metrics.userMetrics.roi >= 0 ? '+' : ''}${metrics.userMetrics.roi.toFixed(1)}%`}
            trend={getTrend(metrics.userMetrics.roi)}
            color={metrics.userMetrics.roi > 0 ? 'green' : metrics.userMetrics.roi < 0 ? 'red' : 'slate'}
          />
          <MetricCard
            icon="🎲"
            label="Active Bets"
            value={metrics.userMetrics.activeBets}
            color="blue"
          />
          <MetricCard
            icon="📅"
            label="This Week"
            value={metrics.userMetrics.weekPL >= 0 ? `+${metrics.userMetrics.weekPL.toFixed(1)}u` : `${metrics.userMetrics.weekPL.toFixed(1)}u`}
            trend={getTrend(metrics.userMetrics.weekPL)}
            color={metrics.userMetrics.weekPL > 0 ? 'green' : metrics.userMetrics.weekPL < 0 ? 'red' : 'slate'}
          />
          <MetricCard
            icon={metrics.userMetrics.winStreak > 0 ? '🔥' : metrics.userMetrics.winStreak < 0 ? '❄️' : '➖'}
            label="Streak"
            value={`${Math.abs(metrics.userMetrics.winStreak)}${metrics.userMetrics.winStreak > 0 ? 'W' : metrics.userMetrics.winStreak < 0 ? 'L' : ''}`}
            color={metrics.userMetrics.winStreak > 0 ? 'green' : metrics.userMetrics.winStreak < 0 ? 'red' : 'slate'}
          />
        </div>
      </div>

      {/* System Alerts Metrics */}
      <div>
        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
          <span className="text-xs">⚡</span> System Activity
        </h3>
        <div className="grid grid-cols-6 gap-1.5">
          <MetricCard
            icon="🎮"
            label="Live Games"
            value={metrics.systemMetrics.liveGames}
            subValue="Being Tracked"
            color="purple"
          />
          <MetricCard
            icon="🔔"
            label="Alerts Today"
            value={metrics.systemMetrics.alertsToday}
            subValue="All Types"
            color="blue"
          />
          <MetricCard
            icon="⭐"
            label="High Confidence"
            value={metrics.systemMetrics.highConfidence}
            subValue="Premium Alerts"
            color="yellow"
          />
          <MetricCard
            icon="✅"
            label="Alert Win Rate"
            value={`${metrics.systemMetrics.alertWinRate.toFixed(1)}%`}
            trend={metrics.systemMetrics.alertWinRate >= 55 ? 'up' : 'neutral'}
            color={metrics.systemMetrics.alertWinRate >= 55 ? 'green' : 'slate'}
          />
          <MetricCard
            icon="⚡"
            label="Arb Opps"
            value={metrics.systemMetrics.arbOpportunities}
            subValue="Right Now"
            color="green"
          />
          <MetricCard
            icon="💎"
            label="Value Bets"
            value={metrics.systemMetrics.valueBets}
            subValue="+EV Found"
            color="purple"
          />
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
