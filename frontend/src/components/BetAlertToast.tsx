import { useState, useEffect } from 'react';
import { StrategyAlert } from '../types';

interface BetAlertToastProps {
  alert: StrategyAlert;
  onDismiss: () => void;
  position: number; // 0 = bottom, 1 = second from bottom, etc.
}

export function BetAlertToast({ alert, onDismiss, position }: BetAlertToastProps) {
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [isExiting, setIsExiting] = useState(false);

  // Update timer every second
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeElapsed(prev => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Auto-dismiss based on urgency
  useEffect(() => {
    let dismissTime: number;

    switch (alert.urgency || alert.confidence) {
      case 'CRITICAL':
        dismissTime = 60000; // 60 seconds for critical alerts
        break;
      case 'HIGH':
        dismissTime = 45000; // 45 seconds for high urgency
        break;
      case 'MEDIUM':
        dismissTime = 30000; // 30 seconds for medium
        break;
      default:
        dismissTime = 20000; // 20 seconds for low
    }

    const timer = setTimeout(() => {
      handleDismiss();
    }, dismissTime);

    return () => clearTimeout(timer);
  }, [alert.urgency, alert.confidence]);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(onDismiss, 300); // Wait for exit animation
  };

  // Format time elapsed as MM:SS
  const formatTimeElapsed = () => {
    const minutes = Math.floor(timeElapsed / 60);
    const seconds = timeElapsed % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // Confidence level styling
  const getConfidenceStyles = () => {
    const conf = alert.urgency || alert.confidence;
    switch (conf) {
      case 'CRITICAL':
        return {
          bg: 'bg-gradient-to-br from-red-600 via-red-700 to-red-900',
          border: 'border-red-500',
          glow: 'shadow-2xl shadow-red-500/50',
          pulse: 'animate-pulse',
          emoji: '🚨',
          timerColor: 'text-red-200'
        };
      case 'HIGH':
        return {
          bg: 'bg-gradient-to-br from-orange-600 via-orange-700 to-orange-900',
          border: 'border-orange-500',
          glow: 'shadow-xl shadow-orange-500/40',
          pulse: '',
          emoji: '🔥',
          timerColor: 'text-orange-200'
        };
      case 'MEDIUM':
        return {
          bg: 'bg-gradient-to-br from-yellow-600 via-yellow-700 to-yellow-900',
          border: 'border-yellow-500',
          glow: 'shadow-lg shadow-yellow-500/30',
          pulse: '',
          emoji: '⚡',
          timerColor: 'text-yellow-200'
        };
      default:
        return {
          bg: 'bg-gradient-to-br from-blue-600 via-blue-700 to-blue-900',
          border: 'border-blue-500',
          glow: 'shadow-lg shadow-blue-500/30',
          pulse: '',
          emoji: '💡',
          timerColor: 'text-blue-200'
        };
    }
  };

  const styles = getConfidenceStyles();

  // Calculate bottom position based on index (stack them up)
  const bottomPosition = position * 180 + 16; // 180px per notification + 16px base

  return (
    <div
      className={`
        ${styles.bg} ${styles.border} ${styles.glow} ${styles.pulse}
        fixed right-4 z-50 w-96 border-4 rounded-xl overflow-hidden
        transition-all duration-300 ease-out
        ${isExiting ? 'opacity-0 translate-x-full' : 'opacity-100 translate-x-0'}
      `}
      style={{ bottom: `${bottomPosition}px` }}
    >
      {/* Header - Strategy Name & Timer */}
      <div className="flex items-center justify-between bg-black/30 px-4 py-2 border-b-2 border-white/20">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{styles.emoji}</span>
          <div>
            <div className="font-bold text-white text-sm">{alert.strategy_name}</div>
            <div className="text-xs text-white/70 uppercase">{alert.confidence} Confidence</div>
          </div>
        </div>

        {/* Time Decay Counter */}
        <div className="text-right">
          <div className={`font-mono font-bold text-lg ${styles.timerColor}`}>
            {formatTimeElapsed()}
          </div>
          <div className="text-xs text-white/60">Age</div>
        </div>
      </div>

      {/* Alert Body */}
      <div className="p-4 space-y-3">
        {/* Trigger */}
        <div className="bg-black/40 rounded-lg p-3 border border-white/20">
          <div className="text-xs font-semibold text-white/70 mb-1">TRIGGER</div>
          <div className="text-sm text-white font-medium leading-tight">
            {alert.trigger}
          </div>
        </div>

        {/* Recommendation */}
        <div className="bg-black/40 rounded-lg p-3 border border-white/20">
          <div className="text-xs font-semibold text-white/70 mb-1">RECOMMENDATION</div>
          <div className="text-sm text-white font-bold">
            {alert.recommendation}
          </div>
        </div>

        {/* Bet Options - Books */}
        {alert.bet_options && alert.bet_options.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs font-semibold text-white/70">BOOKS & ODDS</div>
            {alert.bet_options.slice(0, 3).map((option, idx) => (
              <div
                key={idx}
                className="bg-black/40 rounded-lg p-2 border border-white/20 flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <div className="text-white font-semibold text-sm">
                    {option.bookmaker_title || option.bookmaker}
                  </div>
                  <div className="text-white/70 text-xs">{option.label}</div>
                </div>
                <div className="text-white font-bold text-sm">
                  {typeof option.odds === 'number'
                    ? (option.odds > 0 ? `+${Math.round(option.odds)}` : Math.round(option.odds))
                    : option.odds}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Stats Row */}
        <div className="grid grid-cols-3 gap-2 pt-2 border-t border-white/20">
          <div className="text-center">
            <div className="text-white font-bold text-lg">+{alert.edge_percentage.toFixed(1)}%</div>
            <div className="text-white/60 text-xs font-semibold">Edge</div>
          </div>
          <div className="text-center">
            <div className="text-white font-bold text-lg">+{alert.expected_roi.toFixed(1)}%</div>
            <div className="text-white/60 text-xs font-semibold">ROI</div>
          </div>
          <div className="text-center">
            <div className="text-white font-bold text-lg">{alert.stake_recommendation.toFixed(1)}u</div>
            <div className="text-white/60 text-xs font-semibold">Stake</div>
          </div>
        </div>

        {/* Win Probability */}
        <div className="bg-black/40 rounded-lg p-2 border border-white/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-white/70">Win Probability</span>
            <span className="text-white font-bold">{(alert.win_probability * 100).toFixed(1)}%</span>
          </div>
          <div className="w-full bg-white/20 rounded-full h-2 mt-1">
            <div
              className="bg-green-400 h-2 rounded-full transition-all duration-500"
              style={{ width: `${alert.win_probability * 100}%` }}
            />
          </div>
        </div>

        {/* Expiration Warning */}
        {alert.expires_in && alert.expires_in < 300 && (
          <div className="bg-red-500/20 border border-red-400 rounded-lg p-2 text-center">
            <div className="text-red-200 text-xs font-bold">
              ⏱️ Expires in {Math.floor(alert.expires_in / 60)}:{(alert.expires_in % 60).toString().padStart(2, '0')}
            </div>
          </div>
        )}
      </div>

      {/* Close Button */}
      <button
        onClick={handleDismiss}
        className="absolute top-2 right-2 text-white/60 hover:text-white transition-colors text-xl font-bold w-6 h-6 flex items-center justify-center"
      >
        ×
      </button>
    </div>
  );
}
