/**
 * Toast Alert Component
 *
 * High-priority persistent alerts for volatility arbitrage hedge triggers
 * Shows when opposite side hits target price for locked profit
 */

import { useState, useEffect } from 'react';
import { X, TrendingUp, DollarSign, Clock } from 'lucide-react';
import { startVolatilityAlertPolling, stopVolatilityAlertPolling } from '../services/volatilityAlertService';

export interface ToastAlertData {
  id: string;
  position_id: string;
  game_id: string;
  type: 'hedge_trigger' | 'position_closed' | 'info';
  priority: 'high' | 'medium' | 'low';
  title: string;
  message: string;

  // Hedge-specific data
  game?: {
    home_team: string;
    away_team: string;
    quarter: string;
    score: string;
  };
  hedge_opportunity?: {
    team: string;
    odds: number;
    locked_profit: number;
    recommended_stake: number;
  };

  timestamp: string;
  expires_in?: number; // seconds
  persistent?: boolean;
  sound?: boolean;
}

interface ToastAlertProps {
  alert: ToastAlertData;
  onDismiss: (id: string) => void;
  onAction: (alertId: string, action: 'view' | 'execute' | 'dismiss') => void;
}

export function ToastAlert({ alert, onDismiss, onAction }: ToastAlertProps) {
  const [timeLeft, setTimeLeft] = useState(alert.expires_in || 0);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    if (alert.expires_in) {
      const interval = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [alert.expires_in]);

  // Play sound on mount if enabled
  useEffect(() => {
    if (alert.sound && alert.type === 'hedge_trigger') {
      // Optional: Add sound effect
      const audio = new Audio('/sounds/notification.mp3');
      audio.volume = 0.5;
      audio.play().catch(() => {}); // Ignore if no sound file
    }
  }, [alert.sound, alert.type]);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => {
      onDismiss(alert.id);
    }, 300);
  };

  const handleAction = (action: 'view' | 'execute' | 'dismiss') => {
    onAction(alert.id, action);
    if (action === 'dismiss') {
      handleDismiss();
    }
  };

  // Priority-based styling
  const getPriorityColors = () => {
    switch (alert.priority) {
      case 'high':
        return {
          bg: 'bg-gradient-to-r from-green-600 to-emerald-600',
          border: 'border-green-400',
          glow: 'shadow-lg shadow-green-500/50'
        };
      case 'medium':
        return {
          bg: 'bg-gradient-to-r from-blue-600 to-indigo-600',
          border: 'border-blue-400',
          glow: 'shadow-lg shadow-blue-500/50'
        };
      default:
        return {
          bg: 'bg-gradient-to-r from-gray-600 to-gray-700',
          border: 'border-gray-400',
          glow: 'shadow-lg'
        };
    }
  };

  const colors = getPriorityColors();

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div
      className={`
        fixed bottom-6 right-6 z-50 w-96
        ${colors.bg} ${colors.border} border-2 rounded-lg
        ${colors.glow}
        ${isExiting ? 'animate-slide-out-right' : 'animate-slide-in-right'}
        ${alert.priority === 'high' ? 'animate-pulse-subtle' : ''}
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between p-4 border-b border-white/20">
        <div className="flex items-center gap-3">
          {alert.type === 'hedge_trigger' && (
            <div className="p-2 bg-white/20 rounded-lg">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
          )}
          <div>
            <h3 className="text-lg font-bold text-white">{alert.title}</h3>
            {alert.priority === 'high' && (
              <span className="text-xs text-emerald-200 font-semibold">
                URGENT - LOCKED PROFIT AVAILABLE
              </span>
            )}
          </div>
        </div>

        <button
          onClick={handleDismiss}
          className="text-white/70 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Body */}
      <div className="p-4 space-y-3">
        {/* Game Info */}
        {alert.game && (
          <div className="bg-black/20 rounded-lg p-3">
            <div className="text-white font-semibold text-sm">
              {alert.game.away_team} @ {alert.game.home_team}
            </div>
            <div className="text-white/70 text-xs mt-1">
              {alert.game.quarter} | {alert.game.score}
            </div>
          </div>
        )}

        {/* Message */}
        <p className="text-white/90 text-sm leading-relaxed">
          {alert.message}
        </p>

        {/* Hedge Opportunity Details */}
        {alert.hedge_opportunity && (
          <div className="bg-black/30 rounded-lg p-3 space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-white/70">Hedge Team:</span>
              <span className="text-white font-semibold">
                {alert.hedge_opportunity.team} {alert.hedge_opportunity.odds > 0 ? '+' : ''}
                {alert.hedge_opportunity.odds}
              </span>
            </div>

            <div className="flex items-center justify-between text-sm">
              <span className="text-white/70">Recommended Stake:</span>
              <span className="text-white font-semibold">
                ${alert.hedge_opportunity.recommended_stake.toFixed(2)}
              </span>
            </div>

            <div className="flex items-center justify-between text-lg border-t border-white/20 pt-2 mt-2">
              <span className="text-emerald-200 font-bold flex items-center gap-1">
                <DollarSign className="w-5 h-5" />
                LOCKED PROFIT:
              </span>
              <span className="text-emerald-300 font-bold">
                ${alert.hedge_opportunity.locked_profit.toFixed(2)}
              </span>
            </div>
          </div>
        )}

        {/* Time Remaining */}
        {timeLeft > 0 && (
          <div className="flex items-center gap-2 text-white/60 text-xs">
            <Clock className="w-4 h-4" />
            <span>Expires in: {formatTime(timeLeft)}</span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2 p-4 border-t border-white/20">
        {alert.type === 'hedge_trigger' && (
          <>
            <button
              onClick={() => handleAction('view')}
              className="flex-1 py-2 px-4 bg-white/20 hover:bg-white/30 text-white font-semibold rounded-lg transition-all"
            >
              View Details
            </button>
            <button
              onClick={() => handleAction('execute')}
              className="flex-1 py-2 px-4 bg-white hover:bg-emerald-50 text-green-700 font-bold rounded-lg transition-all shadow-lg"
            >
              Execute Hedge
            </button>
          </>
        )}

        {alert.type !== 'hedge_trigger' && (
          <button
            onClick={() => handleAction('dismiss')}
            className="flex-1 py-2 px-4 bg-white/20 hover:bg-white/30 text-white font-semibold rounded-lg transition-all"
          >
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Toast Alert Container
 * Manages multiple toast alerts
 */
export function ToastAlertContainer() {
  const [alerts, setAlerts] = useState<ToastAlertData[]>([]);

  // Listen for new alerts from volatilityAlertService
  useEffect(() => {
    // TODO: Get actual user_id from auth context
    const userId = 'USER_ID';

    // Handle incoming alerts
    const handleAlert = (event: CustomEvent) => {
      const newAlert = event.detail as ToastAlertData;
      setAlerts(prev => {
        // Avoid duplicates
        if (prev.some(a => a.id === newAlert.id)) {
          return prev;
        }
        return [...prev, newAlert];
      });
    };

    // Listen for volatility hedge alerts
    window.addEventListener('volatility-hedge-alert', handleAlert as EventListener);

    // Start polling for volatility alerts
    startVolatilityAlertPolling(userId, 30000);

    return () => {
      window.removeEventListener('volatility-hedge-alert', handleAlert as EventListener);
      stopVolatilityAlertPolling();
    };
  }, []);

  const handleDismiss = (id: string) => {
    setAlerts((prev) => prev.filter((alert) => alert.id !== id));
  };

  const handleAction = (alertId: string, action: 'view' | 'execute' | 'dismiss') => {
    const alert = alerts.find((a) => a.id === alertId);
    if (!alert) return;

    if (action === 'view') {
      // Open hedge alert modal
      window.dispatchEvent(new CustomEvent('open-hedge-modal', {
        detail: { positionId: alert.position_id }
      }));
    } else if (action === 'execute') {
      // Navigate to hedge execution
      window.location.href = `/volatility-positions?hedge=${alert.position_id}`;
    }

    // Dismiss after action
    if (action !== 'view') {
      handleDismiss(alertId);
    }
  };

  return (
    <div className="fixed bottom-0 right-0 z-50 pointer-events-none">
      <div className="space-y-4 p-6 pointer-events-auto">
        {alerts.map((alert) => (
          <ToastAlert
            key={alert.id}
            alert={alert}
            onDismiss={handleDismiss}
            onAction={handleAction}
          />
        ))}
      </div>
    </div>
  );
}

// Add animations to global CSS
const styles = `
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

@keyframes slide-out-right {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}

@keyframes pulse-subtle {
  0%, 100% {
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.5);
  }
  50% {
    box-shadow: 0 0 30px rgba(16, 185, 129, 0.7);
  }
}

.animate-slide-in-right {
  animation: slide-in-right 0.3s ease-out;
}

.animate-slide-out-right {
  animation: slide-out-right 0.3s ease-in;
}

.animate-pulse-subtle {
  animation: pulse-subtle 2s infinite;
}
`;

// Inject styles
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style');
  styleSheet.textContent = styles;
  document.head.appendChild(styleSheet);
}
