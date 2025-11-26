/**
 * Hedge Alert Monitor
 * Monitors bet positions and triggers alerts when hedge opportunities are detected
 * Polls backend every 10 seconds for new hedge_opportunity alerts
 */

import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { hedgeAlertService, HedgeToastData } from '../services/hedgeAlertService';
import { HedgeAlertToast } from './HedgeAlertToast';
import { HedgeAlertModal, HedgeAlertData } from './HedgeAlertModal';

interface HedgeAlertMonitorProps {
  enabled?: boolean;
  pollInterval?: number; // milliseconds (default: 10000 = 10 seconds)
}

export function HedgeAlertMonitor({
  enabled = true,
  pollInterval = 10000
}: HedgeAlertMonitorProps) {
  const { username } = useAuth();
  const [currentToast, setCurrentToast] = useState<HedgeToastData | null>(null);
  const [modalAlert, setModalAlert] = useState<HedgeAlertData | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    if (!enabled || !username) {
      console.log('[HEDGE ALERT MONITOR] Disabled - not enabled or no user');
      return;
    }

    console.log(`[HEDGE ALERT MONITOR] Active - monitoring hedge opportunities for user: ${username}`);

    // Callback when new hedge alert is detected
    const handleNewHedgeAlert = (toast: HedgeToastData) => {
      console.log('[HEDGE ALERT MONITOR] 🔒 New hedge opportunity detected!', toast);
      setCurrentToast(toast);
    };

    // Start polling for hedge alerts
    hedgeAlertService.startPolling(
      username,
      pollInterval,
      handleNewHedgeAlert
    );

    // Cleanup on unmount
    return () => {
      console.log('[HEDGE ALERT MONITOR] Stopping polling');
      hedgeAlertService.stopPolling();
    };
  }, [enabled, username, pollInterval]);

  // Handle toast click - open modal
  const handleToastClick = () => {
    if (currentToast) {
      setModalAlert(currentToast.alert);
      setIsModalOpen(true);
    }
  };

  // Handle toast dismiss
  const handleToastDismiss = () => {
    setCurrentToast(null);
  };

  // Handle modal close
  const handleModalClose = () => {
    setIsModalOpen(false);
  };

  // Handle place hedge action
  const handlePlaceHedge = async (alertData: HedgeAlertData) => {
    console.log('[HEDGE ALERT MONITOR] User placing hedge bet:', alertData);
    // TODO: Open bet slip or external link to bookmaker
    // For now, just show browser alert
    window.alert(`Hedge bet: ${alertData.hedge_bet.side} $${alertData.hedge_bet.stake.toFixed(2)} at ${alertData.hedge_bet.odds > 0 ? '+' : ''}${alertData.hedge_bet.odds} on ${alertData.hedge_bet.bookmaker}`);
  };

  // Handle dismiss action
  const handleDismissAlert = async (alert: HedgeAlertData) => {
    console.log('[HEDGE ALERT MONITOR] User dismissed hedge alert:', alert.alert_id);
    // TODO: Mark alert as dismissed in backend
    setCurrentToast(null);
    setIsModalOpen(false);
  };

  return (
    <>
      {/* Toast notification - top-right corner */}
      {currentToast && (
        <HedgeAlertToast
          toast={currentToast}
          onClick={handleToastClick}
          onDismiss={handleToastDismiss}
        />
      )}

      {/* Modal - full details */}
      <HedgeAlertModal
        alert={modalAlert}
        isOpen={isModalOpen}
        onClose={handleModalClose}
        onPlaceHedge={handlePlaceHedge}
        onDismiss={handleDismissAlert}
      />
    </>
  );
}
