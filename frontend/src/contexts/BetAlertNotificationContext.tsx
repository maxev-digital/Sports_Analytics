import { createContext, useContext, useState, useCallback, ReactNode, useEffect } from 'react';
import { StrategyAlert } from '../types';
import { BetAlertToast } from '../components/BetAlertToast';

interface BetAlertNotification extends StrategyAlert {
  id: string;
  showTime: number; // When it was shown
}

interface BetAlertNotificationContextType {
  showBetAlert: (alert: StrategyAlert) => void;
  dismissAlert: (id: string) => void;
  activeAlerts: BetAlertNotification[];
  isAudioMuted: boolean;
  toggleAudioMute: () => void;
}

const BetAlertNotificationContext = createContext<BetAlertNotificationContextType | undefined>(undefined);

export function useBetAlertNotification() {
  const context = useContext(BetAlertNotificationContext);
  if (!context) {
    throw new Error('useBetAlertNotification must be used within BetAlertNotificationProvider');
  }
  return context;
}

export function BetAlertNotificationProvider({ children }: { children: ReactNode }) {
  const [alerts, setAlerts] = useState<BetAlertNotification[]>([]);

  // Audio mute state - load from localStorage
  const [isAudioMuted, setIsAudioMuted] = useState<boolean>(() => {
    const saved = localStorage.getItem('betAlertAudioMuted');
    return saved === 'true';
  });

  // Save audio mute preference to localStorage
  useEffect(() => {
    localStorage.setItem('betAlertAudioMuted', isAudioMuted.toString());
  }, [isAudioMuted]);

  // Toggle audio mute
  const toggleAudioMute = useCallback(() => {
    setIsAudioMuted(prev => !prev);
  }, []);

  // Show a new bet alert notification
  const showBetAlert = useCallback((alert: StrategyAlert) => {
    const id = `${alert.strategy_id}-${Date.now()}`;
    const notification: BetAlertNotification = {
      ...alert,
      id,
      showTime: Date.now()
    };

    setAlerts(prev => {
      // Limit to max 5 active notifications
      const updated = [...prev, notification];
      if (updated.length > 5) {
        return updated.slice(-5); // Keep only the latest 5
      }
      return updated;
    });

    // Play audio alert if enabled and not muted
    if (alert.sound_alert && !isAudioMuted) {
      playAlertSound(alert.confidence);
    }
  }, [isAudioMuted]);

  // Dismiss a specific alert
  const dismissAlert = useCallback((id: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== id));
  }, []);

  // Play sound based on confidence level
  const playAlertSound = (confidence: string) => {
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      // Different tones for different confidence levels
      const frequency = confidence === 'CRITICAL' ? 1400 : confidence === 'HIGH' ? 1000 : 800;
      oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
      oscillator.type = 'sine';

      gainNode.gain.setValueAtTime(0.4, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.4);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.4);

      // Triple beep for CRITICAL alerts
      if (confidence === 'CRITICAL') {
        setTimeout(() => {
          const osc2 = audioContext.createOscillator();
          const gain2 = audioContext.createGain();
          osc2.connect(gain2);
          gain2.connect(audioContext.destination);
          osc2.frequency.setValueAtTime(1400, audioContext.currentTime);
          osc2.type = 'sine';
          gain2.gain.setValueAtTime(0.4, audioContext.currentTime);
          gain2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.4);
          osc2.start(audioContext.currentTime);
          osc2.stop(audioContext.currentTime + 0.4);
        }, 500);

        setTimeout(() => {
          const osc3 = audioContext.createOscillator();
          const gain3 = audioContext.createGain();
          osc3.connect(gain3);
          gain3.connect(audioContext.destination);
          osc3.frequency.setValueAtTime(1400, audioContext.currentTime);
          osc3.type = 'sine';
          gain3.gain.setValueAtTime(0.4, audioContext.currentTime);
          gain3.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.4);
          osc3.start(audioContext.currentTime);
          osc3.stop(audioContext.currentTime + 0.4);
        }, 1000);
      }
    } catch (error) {
      console.error('Failed to play alert sound:', error);
    }
  };

  return (
    <BetAlertNotificationContext.Provider value={{ showBetAlert, dismissAlert, activeAlerts: alerts, isAudioMuted, toggleAudioMute }}>
      {children}

      {/* Render toast notifications - stacked from bottom */}
      <div className="fixed bottom-0 right-0 z-50 pointer-events-none">
        <div className="relative">
          {alerts.map((alert, index) => (
            <div key={alert.id} className="pointer-events-auto">
              <BetAlertToast
                alert={alert}
                onDismiss={() => dismissAlert(alert.id)}
                position={index}
              />
            </div>
          ))}
        </div>
      </div>
    </BetAlertNotificationContext.Provider>
  );
}
