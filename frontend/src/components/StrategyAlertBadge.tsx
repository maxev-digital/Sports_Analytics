import { useState, useEffect } from 'react';
import { StrategyAlert } from '../types';

interface StrategyAlertBadgeProps {
  alerts: StrategyAlert[];
  onAlertClick?: (alert: StrategyAlert) => void;
}

export function StrategyAlertBadge({ alerts, onAlertClick }: StrategyAlertBadgeProps) {
  const [selectedAlertIndex, setSelectedAlertIndex] = useState(0);
  const [soundPlayed, setSoundPlayed] = useState<Set<string>>(new Set());

  if (!alerts || alerts.length === 0) {
    return null;
  }

  const currentAlert = alerts[selectedAlertIndex];

  // Auto-rotate through alerts every 5 seconds
  useEffect(() => {
    if (alerts.length > 1) {
      const interval = setInterval(() => {
        setSelectedAlertIndex((prev) => (prev + 1) % alerts.length);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [alerts.length]);

  // Play audio alert for CRITICAL/HIGH confidence alerts (once per alert)
  useEffect(() => {
    if (currentAlert.sound_alert && !soundPlayed.has(currentAlert.strategy_id)) {
      playAlertSound(currentAlert.confidence);
      setSoundPlayed((prev) => new Set(prev).add(currentAlert.strategy_id));
    }
  }, [currentAlert, soundPlayed]);

  const playAlertSound = (confidence: string) => {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    // Different tones for different confidence levels
    const frequency = confidence === 'CRITICAL' ? 1200 : confidence === 'HIGH' ? 900 : 700;
    oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
    oscillator.type = 'sine';

    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentiallyRampToValueAtTime(0.01, audioContext.currentTime + 0.3);

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.3);

    // Double beep for CRITICAL
    if (confidence === 'CRITICAL') {
      setTimeout(() => {
        const osc2 = audioContext.createOscillator();
        const gain2 = audioContext.createGain();
        osc2.connect(gain2);
        gain2.connect(audioContext.destination);
        osc2.frequency.setValueAtTime(1200, audioContext.currentTime);
        osc2.type = 'sine';
        gain2.gain.setValueAtTime(0.3, audioContext.currentTime);
        gain2.gain.exponentiallyRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
        osc2.start(audioContext.currentTime);
        osc2.stop(audioContext.currentTime + 0.3);
      }, 400);
    }
  };

  // Confidence level styling
  const getConfidenceStyles = (confidence: string) => {
    switch (confidence) {
      case 'CRITICAL':
        return {
          bg: 'bg-gradient-to-r from-red-600 via-red-700 to-red-800',
          border: 'border-red-500',
          text: 'text-red-100',
          glow: 'shadow-lg shadow-red-500/50',
          animation: 'animate-pulse',
          emoji: '🚨'
        };
      case 'HIGH':
        return {
          bg: 'bg-gradient-to-r from-orange-600 via-orange-700 to-orange-800',
          border: 'border-orange-500',
          text: 'text-orange-100',
          glow: 'shadow-lg shadow-orange-500/50',
          animation: '',
          emoji: '🔥'
        };
      case 'MEDIUM':
        return {
          bg: 'bg-gradient-to-r from-yellow-600 via-yellow-700 to-yellow-800',
          border: 'border-yellow-500',
          text: 'text-yellow-100',
          glow: 'shadow-md shadow-yellow-500/30',
          animation: '',
          emoji: '⚡'
        };
      default:
        return {
          bg: 'bg-gradient-to-r from-blue-600 via-blue-700 to-blue-800',
          border: 'border-blue-500',
          text: 'text-blue-100',
          glow: 'shadow-md shadow-blue-500/30',
          animation: '',
          emoji: '💡'
        };
    }
  };

  const styles = getConfidenceStyles(currentAlert.confidence);

  return (
    <div className="strategy-alerts-container mb-3">
      {/* Alert Badge - Compact summary */}
      <div
        className={`${styles.bg} ${styles.border} ${styles.glow} ${styles.animation} border-2 rounded-lg p-3 cursor-pointer transition-all hover:scale-105`}
        onClick={() => onAlertClick?.(currentAlert)}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{styles.emoji}</span>
            <div>
              <div className={`font-bold text-sm ${styles.text}`}>
                {currentAlert.strategy_name}
              </div>
              <div className="text-xs text-white/80">
                {currentAlert.confidence} CONFIDENCE
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="font-bold text-lg text-white">
              +{currentAlert.edge_percentage.toFixed(1)}%
            </div>
            <div className="text-xs text-white/80">Edge</div>
          </div>
        </div>

        {/* Trigger */}
        <div className="text-sm text-white/90 mb-2 line-clamp-2">
          {currentAlert.trigger}
        </div>

        {/* Stats Row */}
        <div className="flex items-center justify-between text-xs text-white/80 border-t border-white/20 pt-2">
          <div>
            <span className="font-semibold">ROI:</span> +{currentAlert.expected_roi.toFixed(1)}%
          </div>
          <div>
            <span className="font-semibold">Win:</span> {(currentAlert.win_probability * 100).toFixed(1)}%
          </div>
          <div>
            <span className="font-semibold">Stake:</span> {currentAlert.stake_recommendation.toFixed(1)}u
          </div>
        </div>

        {/* Multiple alerts indicator */}
        {alerts.length > 1 && (
          <div className="flex items-center justify-center gap-1 mt-2 pt-2 border-t border-white/20">
            {alerts.map((_, idx) => (
              <div
                key={idx}
                className={`w-2 h-2 rounded-full transition-all cursor-pointer ${
                  idx === selectedAlertIndex ? 'bg-white scale-125' : 'bg-white/40 hover:bg-white/60'
                }`}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedAlertIndex(idx);
                }}
              />
            ))}
          </div>
        )}

        {/* Expiration countdown for urgent alerts */}
        {currentAlert.expires_in && currentAlert.expires_in < 300 && (
          <div className="mt-2 pt-2 border-t border-white/20 text-center">
            <div className="text-xs font-bold text-white/90">
              ⏱️ Expires in {Math.floor(currentAlert.expires_in / 60)}:{(currentAlert.expires_in % 60).toString().padStart(2, '0')}
            </div>
          </div>
        )}
      </div>

      {/* Click to expand - Shows detailed recommendations */}
      <div className="text-center mt-1">
        <button className="text-xs text-slate-400 hover:text-slate-300 transition">
          Click for bet recommendations →
        </button>
      </div>
    </div>
  );
}
