import React, { useState, useEffect, useCallback } from 'react';
import { X, Trophy } from 'lucide-react';
import { getBookmaker } from '../utils/bookmakers';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from 'recharts';

interface BetExample {
  bookmaker: string;
  label: string;
  odds: string;
}

interface AlertBetOption {
  bookmaker: string;
  label: string;
  odds: string;
  stake?: string;
}

interface PricingToast {
  id: string;
  type: 'recap' | 'counter' | 'edge' | 'scarcity' | 'cta' | 'chart' | 'middle' | 'arbitrage' | 'goalie';
  label: string;
  title: string;
  subtitle?: string;
  emoji: string;
  valueColor: string;
  delay: number;
  duration: number;
  betExample?: BetExample;
  // For alert-style toasts (middle, arb, goalie)
  alertBets?: AlertBetOption[];
  alertInfo?: {
    sport: string;
    matchup: string;
    trigger?: string;
  };
  bookCardColor?: string; // e.g. 'green', 'red', 'yellow'
  chartData?: { period: string; units: number }[];
  cta?: {
    text: string;
    action: () => void;
  };
}

// Units won data for chart (Jan 1, 2025 - Nov 28, 2025) - realistic variance
const unitsWonData = [
  { period: 'Jan', units: 22 },
  { period: 'Feb', units: 38 },
  { period: 'Mar', units: 31 },  // down month
  { period: 'Apr', units: 58 },
  { period: 'May', units: 72 },
  { period: 'Jun', units: 65 },  // slight pullback
  { period: 'Jul', units: 94 },
  { period: 'Aug', units: 112 },
  { period: 'Sep', units: 105 }, // down month
  { period: 'Oct', units: 148 },
  { period: 'Nov', units: 187 },
];

interface PricingToastSequenceProps {
  enabled?: boolean;
  onUpgradeClick?: () => void;
}

// Yesterday's performance data (would come from API in production)
const getYesterdayStats = () => ({
  wins: 11,
  losses: 3,
  units: 14.7,
  topEdge: 11.4,
  topPlay: 'Celtics 1H -3.5',
  membersViewed: 41,
  ytdUnits: 187,
  memberCount: 847,
});

export const PricingToastSequence: React.FC<PricingToastSequenceProps> = ({
  enabled = true,
  onUpgradeClick,
}) => {
  const [activeToasts, setActiveToasts] = useState<PricingToast[]>([]);
  const [shownIds, setShownIds] = useState<Set<string>>(new Set());
  const stats = getYesterdayStats();

  // Define the toast sequence - styled like ModelPerformance summary cards
  const toastSequence: PricingToast[] = [
    // 1. Last 30 Days Performance Recap
    {
      id: 'recap',
      type: 'recap',
      label: 'Last 30 Days',
      title: '142W - 65L',
      subtitle: '68% Win Rate',
      emoji: '🔥',
      valueColor: 'text-green-400',
      delay: 500,
      duration: 6500, // All visible at 4.5s, this fades at 7s
      betExample: {
        bookmaker: 'fanduel',
        label: 'Celtics -4.5 (Won ✓)',
        odds: '-110',
      },
    },
    // 2. Units Won Chart
    {
      id: 'chart',
      type: 'chart',
      label: '189 Units Won Last 60 Days',
      title: '+189 units',
      subtitle: '189 units · $18,900 profit · 9.2% ROI',
      emoji: '📊',
      valueColor: 'text-green-400',
      delay: 1000,
      duration: 7000, // Fades at 8s
      chartData: unitsWonData,
    },
    // 3. Live P/L Counter
    {
      id: 'counter',
      type: 'counter',
      label: 'Season Results',
      title: `+${stats.ytdUnits} units`,
      subtitle: '2025 season profit',
      emoji: '📈',
      valueColor: 'text-blue-400',
      delay: 1500,
      duration: 7500, // Fades at 9s
      betExample: {
        bookmaker: 'draftkings',
        label: 'Thunder ML (Won ✓)',
        odds: '+145',
      },
    },
    // 4. Single Monster Edge
    {
      id: 'edge',
      type: 'edge',
      label: 'Top Edge Found',
      title: `+${stats.topEdge}%`,
      subtitle: stats.topPlay,
      emoji: '🎯',
      valueColor: 'text-orange-400',
      delay: 2000,
      duration: 8000, // Fades at 10s
      betExample: {
        bookmaker: 'fanduel',
        label: 'Celtics 1H -3.5',
        odds: '-105',
      },
    },
    // 5. Scarcity + Proof
    {
      id: 'scarcity',
      type: 'scarcity',
      label: 'Members Only',
      title: 'High-value play',
      subtitle: `Only ${stats.membersViewed} members have seen this`,
      emoji: '🔒',
      valueColor: 'text-purple-400',
      delay: 2500,
      duration: 8500, // Fades at 11s
      betExample: {
        bookmaker: 'betmgm',
        label: 'Lakers +7.5',
        odds: '-108',
      },
    },
    // 6. NHL Middle Opportunity
    {
      id: 'middle',
      type: 'middle',
      label: 'MIDDLE OPPORTUNITY',
      title: '+2.8% ROI',
      subtitle: 'Bet both sides - chance to win both!',
      emoji: '⚡',
      valueColor: 'text-green-400',
      delay: 3000,
      duration: 9000, // Fades at 12s
      bookCardColor: 'green',
      alertInfo: {
        sport: 'NHL',
        matchup: 'Bruins @ Rangers',
        trigger: '1.5pt spread gap detected',
      },
      alertBets: [
        { bookmaker: 'draftkings', label: 'Bruins +1.5', odds: '-115', stake: '$550' },
        { bookmaker: 'fanduel', label: 'Rangers -1.5', odds: '+135', stake: '$450' },
      ],
    },
    // 7. Arbitrage Alert
    {
      id: 'arbitrage',
      type: 'arbitrage',
      label: 'ARBITRAGE FOUND',
      title: '+1.4% Profit',
      subtitle: 'Risk-free guaranteed profit',
      emoji: '🚨',
      valueColor: 'text-red-400',
      delay: 3500,
      duration: 9500, // Fades at 13s
      bookCardColor: 'red',
      alertInfo: {
        sport: 'NBA',
        matchup: 'Lakers @ Celtics',
        trigger: 'Moneyline mispricing',
      },
      alertBets: [
        { bookmaker: 'betmgm', label: 'Lakers ML', odds: '+185', stake: '$370' },
        { bookmaker: 'caesars', label: 'Celtics ML', odds: '-170', stake: '$630' },
      ],
    },
    // 8. Goalie Pull Opportunity
    {
      id: 'goalie',
      type: 'goalie',
      label: 'GOALIE PULL ALERT',
      title: '🥅 Empty Net',
      subtitle: '3rd period - trailing by 1',
      emoji: '🏒',
      valueColor: 'text-yellow-400',
      delay: 4000,
      duration: 10000, // Fades at 14s
      bookCardColor: 'yellow',
      alertInfo: {
        sport: 'NHL',
        matchup: 'Maple Leafs @ Oilers',
        trigger: '5 min left, goalie likely to pull',
      },
      alertBets: [
        { bookmaker: 'draftkings', label: 'Over 5.5 Goals', odds: '+125' },
      ],
    },
    // 9. One-Click Win CTA - Stays until clicked
    {
      id: 'cta',
      type: 'cta',
      label: 'Limited Offer',
      title: '260W - 159L',
      subtitle: '62% Win Rate - Join now!',
      emoji: '⚡',
      valueColor: 'text-green-400',
      delay: 4500,
      duration: 0, // Stays forever until user clicks signup
      betExample: {
        bookmaker: 'draftkings',
        label: 'Best Value Edge',
        odds: '+142',
      },
      cta: {
        text: 'Give Me Free Access',
        action: () => onUpgradeClick?.(),
      },
    },
  ];

  // Show toast
  const showToast = useCallback((toast: PricingToast) => {
    if (shownIds.has(toast.id)) return;

    setShownIds(prev => new Set(prev).add(toast.id));
    setActiveToasts(prev => [...prev, toast]);

    if (toast.duration > 0) {
      setTimeout(() => {
        dismissToast(toast.id);
      }, toast.duration);
    }
  }, [shownIds]);

  // Dismiss toast
  const dismissToast = (id: string) => {
    setActiveToasts(prev => prev.filter(t => t.id !== id));
  };

  // Schedule toasts on mount
  useEffect(() => {
    if (!enabled) return;

    const timeouts: NodeJS.Timeout[] = [];

    toastSequence.forEach(toast => {
      const timeout = setTimeout(() => {
        showToast(toast);
      }, toast.delay);
      timeouts.push(timeout);
    });

    return () => {
      timeouts.forEach(clearTimeout);
    };
  }, [enabled, showToast]);

  // Play sound based on toast type
  const playSound = (type: string) => {
    const soundMap: Record<string, string> = {
      recap: '/victory.mp3',
      counter: '/level-up.mp3',
      edge: '/notification.mp3',
      scarcity: '/notification.mp3',
      cta: '/success-chime.mp3',
      middle: '/notification.mp3',
      arbitrage: '/victory.mp3',
      goalie: '/notification.mp3',
      chart: '/level-up.mp3',
    };
    const soundUrl = soundMap[type];
    if (soundUrl) {
      const audio = new Audio(soundUrl);
      audio.volume = 0.5;
      audio.play().catch(() => {});
    }
  };

  // Get book card color class based on alert type
  const getBookCardColor = (color?: string) => {
    switch (color) {
      case 'green':
        return 'bg-green-600/80 border-white hover:bg-green-500/90';
      case 'red':
        return 'bg-red-600/80 border-white hover:bg-red-500/90';
      case 'yellow':
        return 'bg-yellow-600/80 border-white hover:bg-yellow-500/90';
      case 'blue':
        return 'bg-blue-600/80 border-white hover:bg-blue-500/90';
      case 'purple':
        return 'bg-purple-600/80 border-white hover:bg-purple-500/90';
      default:
        return 'bg-slate-700/80 border-slate-600 hover:bg-slate-600/90';
    }
  };

  // Get sport badge color
  const getSportBadge = (sport: string) => {
    switch (sport.toUpperCase()) {
      case 'NBA':
        return { color: 'bg-orange-500', label: 'NBA' };
      case 'NFL':
        return { color: 'bg-green-600', label: 'NFL' };
      case 'NHL':
        return { color: 'bg-blue-500', label: 'NHL' };
      case 'NCAAB':
        return { color: 'bg-purple-500', label: 'NCAAB' };
      default:
        return { color: 'bg-gray-500', label: sport };
    }
  };

  // Play sound when toast appears
  useEffect(() => {
    if (activeToasts.length > 0) {
      const latestToast = activeToasts[activeToasts.length - 1];
      playSound(latestToast.type);
    }
  }, [activeToasts.length]);

  if (!enabled || activeToasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col-reverse gap-3 max-h-screen overflow-y-auto pb-4">
      {activeToasts.map((toast, index) => {
        const bookInfo = toast.betExample ? getBookmaker(toast.betExample.bookmaker) : null;

        return (
          <div
            key={toast.id}
            className={`
              bg-gradient-to-br from-slate-800 via-slate-900 to-black
              border-2 border-white rounded-xl
              overflow-hidden w-80
              transition-all duration-300 ease-out
              ${index === 0 ? 'animate-slide-in-right' : ''}
            `}
            style={{
              animationDelay: `${index * 100}ms`,
            }}
          >
            {/* Header - Like ModelPerformance card headers */}
            <div className="px-4 pt-4 pb-2">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{toast.emoji}</span>
                  <div>
                    <div className="text-slate-400 text-sm font-medium">{toast.label}</div>
                    <div className={`text-xl font-bold ${toast.valueColor}`}>{toast.title}</div>
                  </div>
                </div>
                <button
                  onClick={() => dismissToast(toast.id)}
                  className="text-slate-500 hover:text-white transition-colors p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              {toast.subtitle && (
                <div className="text-slate-400 text-sm mt-1 ml-9">{toast.subtitle}</div>
              )}
            </div>

            {/* Chart for chart type toast */}
            {toast.type === 'chart' && toast.chartData && (
              <div className="px-4 pb-3">
                <div className="bg-gradient-to-br from-black via-gray-900 to-slate-900 border border-slate-700 rounded-lg p-3">
                  <ResponsiveContainer width="100%" height={100}>
                    <LineChart data={toast.chartData}>
                      <XAxis
                        dataKey="period"
                        stroke="#94a3b8"
                        tick={{ fontSize: 10 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        stroke="#94a3b8"
                        tick={{ fontSize: 10 }}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={(value) => `${value}u`}
                        width={35}
                      />
                      <Line
                        type="monotone"
                        dataKey="units"
                        stroke="#10b981"
                        strokeWidth={2}
                        dot={{ r: 3, fill: '#10b981' }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Bet Example with Book Logo - Colored Gradient based on toast type */}
            {toast.betExample && bookInfo && (
              <div className="px-4 pb-3">
                <div className={`rounded-lg p-2 border-2 flex items-center justify-between transition-all ${
                  toast.type === 'recap' ? 'bg-gradient-to-r from-green-600/80 to-green-700/80 border-green-400' :
                  toast.type === 'counter' ? 'bg-gradient-to-r from-blue-600/80 to-blue-700/80 border-blue-400' :
                  toast.type === 'edge' ? 'bg-gradient-to-r from-orange-600/80 to-orange-700/80 border-orange-400' :
                  toast.type === 'scarcity' ? 'bg-gradient-to-r from-purple-600/80 to-purple-700/80 border-purple-400' :
                  toast.type === 'cta' ? 'bg-gradient-to-r from-green-600/80 to-green-700/80 border-green-400' :
                  'bg-slate-900/50 border-slate-700'
                }`}>
                  <div className="flex items-center gap-2">
                    <img
                      src={bookInfo.logo}
                      alt={bookInfo.name}
                      className="w-6 h-6 rounded bg-white p-0.5"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                    <div>
                      <div className="text-white font-semibold text-sm">{bookInfo.name}</div>
                      <div className="text-white/80 text-sm">{toast.betExample.label}</div>
                    </div>
                  </div>
                  <div className="text-white font-bold text-sm">{toast.betExample.odds}</div>
                </div>
              </div>
            )}

            {/* Stats Row for Edge toast */}
            {toast.type === 'edge' && (
              <div className="px-4 pb-3">
                <div className="grid grid-cols-3 gap-2 border-t border-slate-700 pt-3">
                  <div className="text-center">
                    <div className="text-orange-400 font-bold text-base">+{stats.topEdge}%</div>
                    <div className="text-slate-400 text-sm">Edge</div>
                  </div>
                  <div className="text-center">
                    <div className="text-green-400 font-bold text-base">+8.2%</div>
                    <div className="text-slate-400 text-sm">ROI</div>
                  </div>
                  <div className="text-center">
                    <div className="text-blue-400 font-bold text-base">1.5u</div>
                    <div className="text-slate-400 text-sm">Stake</div>
                  </div>
                </div>
              </div>
            )}

            {/* Alert-style toasts (Middle, Arbitrage, Goalie) */}
            {(toast.type === 'middle' || toast.type === 'arbitrage' || toast.type === 'goalie') && (
              <div className="px-4 pb-3 space-y-2">
                {/* Sport Badge + Matchup */}
                {toast.alertInfo && (
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-bold text-white ${getSportBadge(toast.alertInfo.sport).color}`}>
                      {getSportBadge(toast.alertInfo.sport).label}
                    </span>
                    <span className="text-white text-sm font-semibold">{toast.alertInfo.matchup}</span>
                  </div>
                )}

                {/* Trigger Info */}
                {toast.alertInfo?.trigger && (
                  <div className="bg-black/40 rounded-lg p-2 border border-white/20">
                    <div className="text-xs text-slate-400 font-semibold">TRIGGER</div>
                    <div className="text-sm text-white">{toast.alertInfo.trigger}</div>
                  </div>
                )}

                {/* Book Cards with Colored Backgrounds */}
                {toast.alertBets && toast.alertBets.map((bet, idx) => {
                  const betBookInfo = getBookmaker(bet.bookmaker);
                  return (
                    <div
                      key={idx}
                      className={`rounded-lg p-2 border-2 flex items-center justify-between transition-all cursor-pointer ${getBookCardColor(toast.bookCardColor)}`}
                    >
                      <div className="flex items-center gap-2">
                        {betBookInfo && (
                          <img
                            src={betBookInfo.logo}
                            alt={betBookInfo.name}
                            className="w-6 h-6 rounded"
                            onError={(e) => {
                              (e.target as HTMLImageElement).style.display = 'none';
                            }}
                          />
                        )}
                        <div>
                          <div className="text-white font-semibold text-sm">{betBookInfo?.name || bet.bookmaker}</div>
                          <div className="text-white/80 text-xs">{bet.label}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-white font-bold text-sm">{bet.odds}</div>
                        {bet.stake && <div className="text-white/70 text-xs">{bet.stake}</div>}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* CTA Button */}
            {toast.cta && (
              <div className="px-4 pb-4">
                <button
                  onClick={toast.cta.action}
                  className="
                    w-full py-3 px-4
                    bg-gradient-to-r from-blue-600 to-blue-700
                    border border-blue-500
                    text-white font-bold
                    rounded-lg
                    hover:from-blue-500 hover:to-blue-600 transition-all
                    flex items-center justify-center gap-2
                  "
                >
                  <Trophy className="w-5 h-5" />
                  {toast.cta.text}
                </button>
              </div>
            )}
          </div>
        );
      })}

      <style>{`
        @keyframes slide-in-right {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        .animate-slide-in-right {
          animation: slide-in-right 0.4s ease-out forwards;
        }
        @keyframes pulse-border {
          0%, 100% {
            border-color: rgba(255, 255, 255, 0.4);
            box-shadow: 0 0 5px rgba(255, 255, 255, 0.2);
          }
          50% {
            border-color: rgba(255, 255, 255, 1);
            box-shadow: 0 0 20px rgba(255, 255, 255, 0.6), 0 0 40px rgba(255, 255, 255, 0.3);
          }
        }
        .animate-pulse-border {
          animation: pulse-border 2s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
};

export default PricingToastSequence;
