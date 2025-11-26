/**
 * Hedge Alert Service - Polls for hedge opportunities and triggers toast notifications
 */

import { HedgeAlertData } from '../components/HedgeAlertModal';
import { getApiUrl } from '../config';

export interface HedgeToastData {
  id: string;
  title: string;
  message: string;
  alert: HedgeAlertData;
  timestamp: string;
}

class HedgeAlertService {
  private pollingInterval: number | null = null;
  private lastAlertId: string | null = null;
  private onNewAlertCallback: ((alert: HedgeToastData) => void) | null = null;

  /**
   * Start polling for hedge alerts
   * @param userId User ID to poll alerts for
   * @param intervalMs Polling interval in milliseconds (default: 10000 = 10 seconds)
   * @param onNewAlert Callback function to execute when new alert is detected
   */
  startPolling(
    userId: string,
    intervalMs: number = 10000,
    onNewAlert: (alert: HedgeToastData) => void
  ) {
    this.onNewAlertCallback = onNewAlert;

    // Initial fetch
    this.checkForNewAlerts(userId);

    // Set up polling
    this.pollingInterval = window.setInterval(() => {
      this.checkForNewAlerts(userId);
    }, intervalMs);

    console.log(`[HedgeAlertService] Started polling for user ${userId} every ${intervalMs}ms`);
  }

  /**
   * Stop polling for hedge alerts
   */
  stopPolling() {
    if (this.pollingInterval !== null) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
      console.log('[HedgeAlertService] Stopped polling');
    }
  }

  /**
   * Check for new hedge alerts
   */
  private async checkForNewAlerts(userId: string) {
    try {
      const response = await fetch(
        getApiUrl(`alerts/all?user_id=${userId}`)
      );

      if (!response.ok) {
        console.error('[HedgeAlertService] Failed to fetch alerts:', response.statusText);
        return;
      }

      const data = await response.json();
      const alerts = data.alerts || [];

      // Filter for hedge opportunity alerts
      const hedgeAlerts = alerts.filter((a: any) => a.alert_type === 'hedge_opportunity');

      if (hedgeAlerts.length === 0) {
        return;
      }

      // Get the most recent hedge alert
      const latestAlert = hedgeAlerts[0]; // Assuming alerts are sorted by timestamp DESC

      // Check if this is a new alert (different from last one we saw)
      if (latestAlert.id !== this.lastAlertId) {
        this.lastAlertId = latestAlert.id;

        // Parse the metadata (contains hedge details)
        const metadata = typeof latestAlert.metadata === 'string'
          ? JSON.parse(latestAlert.metadata)
          : latestAlert.metadata;

        // Create toast data
        const toastData: HedgeToastData = {
          id: latestAlert.id,
          title: '🔒 Hedge Opportunity!',
          message: `${metadata.home_team} vs ${metadata.away_team}: Lock in $${metadata.profit.guaranteed.toFixed(2)} profit (${metadata.profit.roi_percent.toFixed(1)}% ROI)`,
          alert: {
            alert_id: latestAlert.id,
            user_id: latestAlert.user_id,
            game_id: metadata.game_id,
            sport: metadata.sport,
            home_team: metadata.home_team,
            away_team: metadata.away_team,
            original_bet: metadata.original_bet,
            hedge_bet: metadata.hedge_bet,
            profit: metadata.profit,
            timestamp: metadata.timestamp,
            message: metadata.message
          },
          timestamp: latestAlert.timestamp
        };

        // Trigger callback
        if (this.onNewAlertCallback) {
          this.onNewAlertCallback(toastData);
        }

        console.log('[HedgeAlertService] New hedge alert detected:', toastData);
      }
    } catch (error) {
      console.error('[HedgeAlertService] Error checking for alerts:', error);
    }
  }

  /**
   * Manually fetch the latest hedge alert
   */
  async getLatestHedgeAlert(userId: string): Promise<HedgeToastData | null> {
    try {
      const response = await fetch(
        getApiUrl(`alerts/all?user_id=${userId}`)
      );

      if (!response.ok) {
        return null;
      }

      const data = await response.json();
      const alerts = data.alerts || [];

      // Filter for hedge opportunity alerts
      const hedgeAlerts = alerts.filter((a: any) => a.alert_type === 'hedge_opportunity');

      if (hedgeAlerts.length === 0) {
        return null;
      }

      const latestAlert = hedgeAlerts[0];
      const metadata = typeof latestAlert.metadata === 'string'
        ? JSON.parse(latestAlert.metadata)
        : latestAlert.metadata;

      return {
        id: latestAlert.id,
        title: '🔒 Hedge Opportunity!',
        message: `${metadata.home_team} vs ${metadata.away_team}: Lock in $${metadata.profit.guaranteed.toFixed(2)} profit`,
        alert: {
          alert_id: latestAlert.id,
          user_id: latestAlert.user_id,
          game_id: metadata.game_id,
          sport: metadata.sport,
          home_team: metadata.home_team,
          away_team: metadata.away_team,
          original_bet: metadata.original_bet,
          hedge_bet: metadata.hedge_bet,
          profit: metadata.profit,
          timestamp: metadata.timestamp,
          message: metadata.message
        },
        timestamp: latestAlert.timestamp
      };
    } catch (error) {
      console.error('[HedgeAlertService] Error fetching latest alert:', error);
      return null;
    }
  }
}

// Export singleton instance
export const hedgeAlertService = new HedgeAlertService();
