import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { B2BAlertToast, B2BAlertData } from '../components/B2BAlertToast';
import { LiveGame } from '../types';

interface B2BAlertContextType {
  showB2BAlert: (alert: B2BAlertData) => void;
  dismissAlert: (id: string) => void;
  checkGamesForB2B: (games: LiveGame[]) => void;
  activeAlerts: B2BAlertData[];
  dismissedAlerts: Set<string>; // Track dismissed alerts to not show again
}

const B2BAlertContext = createContext<B2BAlertContextType | undefined>(undefined);

export function useB2BAlert() {
  const context = useContext(B2BAlertContext);
  if (!context) {
    throw new Error('useB2BAlert must be used within B2BAlertProvider');
  }
  return context;
}

export function B2BAlertProvider({ children }: { children: ReactNode }) {
  const [alerts, setAlerts] = useState<B2BAlertData[]>([]);
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(() => {
    // Load dismissed alerts from sessionStorage (reset each session)
    const saved = sessionStorage.getItem('dismissedB2BAlerts');
    return saved ? new Set(JSON.parse(saved)) : new Set();
  });

  // Save dismissed alerts to sessionStorage
  useEffect(() => {
    sessionStorage.setItem('dismissedB2BAlerts', JSON.stringify([...dismissedAlerts]));
  }, [dismissedAlerts]);

  // Show a new B2B alert
  const showB2BAlert = useCallback((alert: B2BAlertData) => {
    // Don't show if already dismissed
    if (dismissedAlerts.has(alert.id)) {
      return;
    }

    setAlerts(prev => {
      // Check if alert already exists
      if (prev.some(a => a.id === alert.id)) {
        return prev;
      }

      // Limit to max 3 B2B alerts at once
      const updated = [...prev, alert];
      if (updated.length > 3) {
        return updated.slice(-3);
      }
      return updated;
    });
  }, [dismissedAlerts]);

  // Dismiss a specific alert
  const dismissAlert = useCallback((id: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== id));
    setDismissedAlerts(prev => new Set([...prev, id]));
  }, []);

  // Check games for B2B situations and show alerts
  const checkGamesForB2B = useCallback((games: LiveGame[]) => {
    games.forEach(game => {
      // Only check NBA, NHL, NCAAB
      const sportKey = game.state?.sport_key || '';
      if (!sportKey.includes('nba') && !sportKey.includes('nhl') && !sportKey.includes('ncaab')) {
        return;
      }

      // Check if there's a fatigue edge (rest differential >= 2)
      if (game.fatigue_edge && game.rest_differential && game.rest_differential >= 2) {
        const alertId = `b2b-${game.state.id}`;

        // Don't show if already dismissed
        if (dismissedAlerts.has(alertId)) {
          return;
        }

        const alertData: B2BAlertData = {
          id: alertId,
          sport: sportKey,
          homeTeam: game.state.home_team.name,
          awayTeam: game.state.away_team.name,
          homeRestDays: game.home_rest_days || 0,
          awayRestDays: game.away_rest_days || 0,
          restDifferential: game.rest_differential,
          fatigueEdge: game.fatigue_edge as 'HOME' | 'AWAY',
          edgePoints: game.fatigue_edge_points || 0,
          timestamp: Date.now(),
        };

        showB2BAlert(alertData);
      }
    });
  }, [dismissedAlerts, showB2BAlert]);

  return (
    <B2BAlertContext.Provider value={{ showB2BAlert, dismissAlert, checkGamesForB2B, activeAlerts: alerts, dismissedAlerts }}>
      {children}

      {/* Render B2B toast notifications */}
      <div className="fixed bottom-0 right-0 z-50 pointer-events-none">
        <div className="relative">
          {alerts.map((alert, index) => (
            <div key={alert.id} className="pointer-events-auto">
              <B2BAlertToast
                alert={alert}
                onDismiss={() => dismissAlert(alert.id)}
                position={index}
              />
            </div>
          ))}
        </div>
      </div>
    </B2BAlertContext.Provider>
  );
}
