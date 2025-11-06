import { useState, useEffect } from 'react';
import { getUserBets } from '../utils/betTracking';
import { useAuth } from '../contexts/AuthContext';

interface BetTypePerformanceProps {
  sport: string; // 'NBA', 'NFL', 'NHL', etc.
}

interface BetTypeStats {
  betType: string;
  totalBets: number;
  wins: number;
  losses: number;
  pushes: number;
  totalStaked: number;
  totalProfit: number;
  winRate: number;
  roi: number;
  avgOdds: number;
}

export function BetTypePerformance({ sport }: BetTypePerformanceProps) {
  const { username } = useAuth();
  const [loading, setLoading] = useState(true);
  const [betTypeStats, setBetTypeStats] = useState<BetTypeStats[]>([]);

  useEffect(() => {
    if (!username) {
      setLoading(false);
      return;
    }

    const fetchBetTypePerformance = async () => {
      try {
        // Fetch all settled bets for the user
        const allBets = await getUserBets(username);

        // Filter by sport and settled status
        const sportBets = allBets.filter((bet: any) => {
          const betSport = bet.sport?.toUpperCase();
          const filterSport = sport.toUpperCase();

          // If "ALL", include all sports
          let sportMatch = filterSport === 'ALL';

          if (!sportMatch) {
            // Handle sport variations
            sportMatch =
              betSport === filterSport ||
              (filterSport === 'NBA' && betSport === 'BASKETBALL_NBA') ||
              (filterSport === 'NFL' && betSport === 'AMERICANFOOTBALL_NFL') ||
              (filterSport === 'NHL' && betSport === 'ICEHOCKEY_NHL') ||
              (filterSport === 'MLB' && betSport === 'BASEBALL_MLB') ||
              (filterSport === 'NCAAB' && betSport === 'BASKETBALL_NCAAB') ||
              (filterSport === 'NCAAF' && betSport === 'AMERICANFOOTBALL_NCAAF');
          }

          const isSettled = ['won', 'lost', 'push'].includes(bet.status);

          return sportMatch && isSettled;
        });

        // Group by bet type and calculate stats
        const betTypeMap = new Map<string, any[]>();

        sportBets.forEach((bet: any) => {
          const betType = bet.bet_type || 'unknown';
          if (!betTypeMap.has(betType)) {
            betTypeMap.set(betType, []);
          }
          betTypeMap.get(betType)!.push(bet);
        });

        // Calculate stats for each bet type
        const stats: BetTypeStats[] = [];

        betTypeMap.forEach((bets, betType) => {
          const wins = bets.filter(b => b.status === 'won').length;
          const losses = bets.filter(b => b.status === 'lost').length;
          const pushes = bets.filter(b => b.status === 'push').length;

          const totalStaked = bets.reduce((sum, b) => sum + (b.stake || 0), 0);

          // Calculate profit/loss
          let totalProfit = 0;
          bets.forEach(b => {
            if (b.status === 'won') {
              // American odds calculation
              const odds = b.odds || 0;
              const stake = b.stake || 0;
              if (odds > 0) {
                totalProfit += (stake * odds / 100);
              } else {
                totalProfit += (stake * 100 / Math.abs(odds));
              }
            } else if (b.status === 'lost') {
              totalProfit -= (b.stake || 0);
            }
            // Pushes return stake (0 profit/loss)
          });

          const winRate = bets.length > 0 ? (wins / (wins + losses)) * 100 : 0;
          const roi = totalStaked > 0 ? (totalProfit / totalStaked) * 100 : 0;

          // Calculate average odds
          const avgOdds = bets.length > 0
            ? bets.reduce((sum, b) => sum + (b.odds || 0), 0) / bets.length
            : 0;

          stats.push({
            betType,
            totalBets: bets.length,
            wins,
            losses,
            pushes,
            totalStaked,
            totalProfit,
            winRate,
            roi,
            avgOdds
          });
        });

        // Sort by total bets descending
        stats.sort((a, b) => b.totalBets - a.totalBets);

        setBetTypeStats(stats);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching bet type performance:', error);
        setLoading(false);
      }
    };

    fetchBetTypePerformance();
  }, [username, sport]);

  if (!username) {
    return (
      <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border-4 border-slate-700 rounded-lg p-8 text-center">
        <p className="text-slate-400 text-lg">
          Log in to view your bet type performance
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border-4 border-slate-700 rounded-lg p-8">
        <div className="text-center text-slate-400">Loading bet type performance...</div>
      </div>
    );
  }

  if (betTypeStats.length === 0) {
    return (
      <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border-4 border-slate-700 rounded-lg p-8 text-center">
        <p className="text-slate-400 text-lg">
          No settled {sport} bets yet. Start placing bets to track your performance!
        </p>
      </div>
    );
  }

  const formatBetType = (betType: string) => {
    const typeMap: Record<string, string> = {
      'spread': 'Spread',
      'total': 'Total',
      'moneyline': 'Moneyline',
      'prop': 'Player Props'
    };
    return typeMap[betType.toLowerCase()] || betType;
  };

  const getBetTypeIcon = (betType: string) => {
    const iconMap: Record<string, string> = {
      'spread': '📊',
      'total': '🎯',
      'moneyline': '💰',
      'prop': '👤'
    };
    return iconMap[betType.toLowerCase()] || '🎲';
  };

  return (
    <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border-4 border-blue-700 rounded-lg p-6">
      <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
        <span>📈</span>
        Your {sport === 'ALL' ? 'Overall' : sport} Performance by Bet Type
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {betTypeStats.map((stat) => (
          <div
            key={stat.betType}
            className="bg-slate-900 border-2 border-slate-700 rounded-lg p-5 hover:border-blue-600 transition-all"
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{getBetTypeIcon(stat.betType)}</span>
                <h3 className="text-lg font-bold text-white">
                  {formatBetType(stat.betType)}
                </h3>
              </div>
              <div className="text-sm text-slate-400">
                {stat.totalBets} bets
              </div>
            </div>

            {/* Win/Loss Record */}
            <div className="mb-3">
              <div className="text-sm text-slate-400 mb-1">Record</div>
              <div className="text-xl font-bold text-white">
                {stat.wins}W - {stat.losses}L
                {stat.pushes > 0 && ` - ${stat.pushes}P`}
              </div>
            </div>

            {/* Win Rate */}
            <div className="mb-3">
              <div className="text-sm text-slate-400 mb-1">Win Rate</div>
              <div className={`text-xl font-bold ${
                stat.winRate >= 55 ? 'text-green-400' :
                stat.winRate >= 50 ? 'text-blue-400' :
                'text-red-400'
              }`}>
                {stat.winRate.toFixed(1)}%
              </div>
            </div>

            {/* ROI */}
            <div className="mb-3">
              <div className="text-sm text-slate-400 mb-1">ROI</div>
              <div className={`text-xl font-bold ${
                stat.roi > 0 ? 'text-green-400' :
                stat.roi < 0 ? 'text-red-400' :
                'text-slate-400'
              }`}>
                {stat.roi > 0 ? '+' : ''}{stat.roi.toFixed(1)}%
              </div>
            </div>

            {/* Profit/Loss */}
            <div className="mb-3">
              <div className="text-sm text-slate-400 mb-1">Profit/Loss</div>
              <div className={`text-lg font-bold ${
                stat.totalProfit > 0 ? 'text-green-400' :
                stat.totalProfit < 0 ? 'text-red-400' :
                'text-slate-400'
              }`}>
                {stat.totalProfit > 0 ? '+' : ''}${stat.totalProfit.toFixed(2)}
              </div>
            </div>

            {/* Total Staked */}
            <div className="pt-3 border-t border-slate-700">
              <div className="text-xs text-slate-500">
                Total Staked: ${stat.totalStaked.toFixed(2)}
              </div>
              <div className="text-xs text-slate-500">
                Avg Odds: {stat.avgOdds > 0 ? '+' : ''}{stat.avgOdds.toFixed(0)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary Footer */}
      <div className="mt-6 pt-4 border-t border-slate-700">
        <div className="text-sm text-slate-400 text-center">
          <strong className="text-white">Total Bets:</strong> {betTypeStats.reduce((sum, s) => sum + s.totalBets, 0)} •
          <strong className="text-white"> Total Staked:</strong> ${betTypeStats.reduce((sum, s) => sum + s.totalStaked, 0).toFixed(2)} •
          <strong className={betTypeStats.reduce((sum, s) => sum + s.totalProfit, 0) > 0 ? 'text-green-400' : 'text-red-400'}>
            {' '}Net Profit: {betTypeStats.reduce((sum, s) => sum + s.totalProfit, 0) > 0 ? '+' : ''}
            ${betTypeStats.reduce((sum, s) => sum + s.totalProfit, 0).toFixed(2)}
          </strong>
        </div>
      </div>
    </div>
  );
}
