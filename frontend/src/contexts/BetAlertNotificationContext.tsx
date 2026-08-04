import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { StrategyAlert } from '../types';

interface BetAlertNotification extends StrategyAlert {
  id: string;
  showTime: number;
}

interface BetAlertNotificationContextType {
  showBetAlert: (alert: StrategyAlert) => void;
  dismissAlert: (id: string) => void;
  alerts: BetAlertNotification[];
  isAudioMuted: boolean;
  toggleAudioMute: () => void;
}

const BetAlertNotificationContext = createContext<BetAlertNotificationContextType | null>(null);

export function useBetAlertNotification(): BetAlertNotificationContextType {
  const ctx = useContext(BetAlertNotificationContext);
  if (!ctx) throw new Error('useBetAlertNotification must be used within BetAlertNotificationProvider');
  return ctx;
}

export function BetAlertNotificationProvider({ children }: { children: ReactNode }) {
  const [alerts, setAlerts] = useState<BetAlertNotification[]>([]);
  const [isAudioMuted, setIsAudioMuted] = useState(false);

  // Toasts disabled for MVP — stub keeps the context API intact
  const showBetAlert = useCallback((_alert: StrategyAlert) => {
    // no-op: toasts disabled
  }, []);

  const dismissAlert = useCallback((id: string) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
  }, []);

  const toggleAudioMute = useCallback(() => {
    setIsAudioMuted(prev => !prev);
  }, []);

  return (
    <BetAlertNotificationContext.Provider
      value={{ showBetAlert, dismissAlert, alerts, isAudioMuted, toggleAudioMute }}
    >
      {children}
    </BetAlertNotificationContext.Provider>
  );
}
