/**
 * Volatility Arbitrage Alert Service
 *
 * Polls backend for hedge trigger alerts and dispatches events
 * for the ToastAlertContainer to display
 */

import { ToastAlertData } from '../components/ToastAlert';

let shownAlerts = new Set<string>();
let pollingInterval: NodeJS.Timeout | null = null;

/**
 * Poll backend for new hedge trigger alerts
 */
export async function pollVolatilityAlerts(userId: string): Promise<void> {
  try {
    const response = await fetch(`/api/volatility/alerts?user_id=${userId}`);

    if (!response.ok) {
      console.error('Failed to fetch volatility alerts:', response.statusText);
      return;
    }

    const data = await response.json();

    if (data.alerts && Array.isArray(data.alerts) && data.alerts.length > 0) {
      // Filter out already shown alerts
      const newAlerts = data.alerts.filter(
        (alert: any) => !shownAlerts.has(alert.id)
      );

      // Dispatch custom events for new alerts
      newAlerts.forEach((alert: any) => {
        // Transform backend alert to ToastAlertData format
        const toastAlert: ToastAlertData = {
          id: alert.id,
          position_id: alert.position_id,
          game_id: alert.game_id,
          type: 'hedge_trigger',
          priority: 'high',
          title: 'Hedge Opportunity Available!',
          message: `${alert.hedge_team} has hit your trigger price of +${alert.trigger_price}`,
          game: {
            home_team: alert.home_team,
            away_team: alert.away_team,
            quarter: alert.current_quarter,
            score: alert.current_score
          },
          hedge_opportunity: {
            team: alert.hedge_team,
            odds: alert.hedge_odds,
            locked_profit: alert.locked_profit,
            recommended_stake: alert.recommended_stake
          },
          timestamp: alert.timestamp || new Date().toISOString(),
          expires_in: alert.expires_in || 300, // 5 minutes default
          persistent: true,
          sound: true
        };

        // Dispatch event
        window.dispatchEvent(
          new CustomEvent('volatility-hedge-alert', {
            detail: toastAlert
          })
        );

        // Mark as shown
        shownAlerts.add(alert.id);
      });

      console.log(`[Volatility Alerts] Dispatched ${newAlerts.length} new alerts`);
    }
  } catch (error) {
    console.error('Error polling volatility alerts:', error);
  }
}

/**
 * Start polling for volatility alerts
 */
export function startVolatilityAlertPolling(userId: string, intervalMs: number = 30000): void {
  // Stop existing polling if any
  stopVolatilityAlertPolling();

  console.log(`[Volatility Alerts] Starting polling every ${intervalMs / 1000}s for user ${userId}`);

  // Initial check
  pollVolatilityAlerts(userId);

  // Start interval
  pollingInterval = setInterval(() => {
    pollVolatilityAlerts(userId);
  }, intervalMs);
}

/**
 * Stop polling for volatility alerts
 */
export function stopVolatilityAlertPolling(): void {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
    console.log('[Volatility Alerts] Stopped polling');
  }
}

/**
 * Clear shown alerts cache (useful for testing or resetting state)
 */
export function clearShownAlerts(): void {
  shownAlerts.clear();
  console.log('[Volatility Alerts] Cleared shown alerts cache');
}

/**
 * Manually dismiss an alert (prevents it from being shown again)
 */
export function dismissAlert(alertId: string): void {
  shownAlerts.add(alertId);
}
