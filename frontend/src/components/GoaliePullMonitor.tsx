/**
 * Goalie Pull Monitor
 * Monitors NHL games via backend API and triggers alerts for goalie pull opportunities
 * Backend handles all logic including 1-4 goal deficits with appropriate timing
 */

import { useEffect, useRef } from 'react';
import { getApiUrl } from '../config';
import { useBetAlertNotification } from '../contexts/BetAlertNotificationContext';
import { StrategyAlert } from '../types';

interface GoaliePullMonitorProps {
  enabled?: boolean;
  pollInterval?: number; // milliseconds
}

export function GoaliePullMonitor({
  enabled = true,
  pollInterval = 3000 // 3 seconds
}: GoaliePullMonitorProps) {
  const { showBetAlert } = useBetAlertNotification();
  const alertedGamesRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!enabled) {
      console.log('[GOALIE PULL MONITOR] Disabled - not on eligible page');
      return;
    }

    console.log('[GOALIE PULL MONITOR] Active and monitoring...');

    const checkForGoaliePulls = async () => {
      try {
        // Fetch goalie pull opportunities from backend
        // Backend handles all deficit levels (1-4 goals) with appropriate timing
        const response = await fetch(getApiUrl('goalie-pull-opportunities'));
        if (!response.ok) return;

        const data = await response.json();
        const opportunities = data.opportunities || [];

        if (opportunities.length > 0) {
          console.log(`[GOALIE PULL MONITOR] Found ${opportunities.length} goalie pull opportunity(ies)`);
        }

        // Process each opportunity from backend
        for (const opp of opportunities) {
          const alertKey = `${opp.game_id}-goalie-pull`;

          // Skip if already alerted
          if (alertedGamesRef.current.has(alertKey)) {
            continue;
          }

          console.log(`[GOALIE PULL MONITOR] 🥅 Goalie Pull Alert: ${opp.away_team} @ ${opp.home_team}`);
          console.log(`  Trailing: ${opp.trailing_team} by ${opp.score_diff} goal(s)`);
          console.log(`  Time: ${opp.time_remaining} in period ${opp.period}`);
          console.log(`  Recommendation: ${opp.recommendation || 'N/A'}`);

          // Convert to strategy alert format
          const alert: StrategyAlert = {
            strategy_id: `goalie-pull-${opp.game_id}`,
            strategy_name: 'Goalie Pull',
            game_id: opp.game_id,
            home_team: opp.home_team,
            away_team: opp.away_team,
            sport: 'icehockey_nhl',
            confidence: 'HIGH',
            trigger: `${opp.trailing_team} down ${opp.score_diff} with ${opp.time_remaining} left`,
            recommendation: opp.recommendation || `Goalie pull imminent. ${opp.trailing_team} expected to pull goalie.`,
            edge_percentage: 8.0,
            expected_roi: 0.12,
            win_probability: 0.58,
            stake_recommendation: 100,
            bet_options: [],
            reasoning: `Empty net statistics: Trailing team ${opp.trailing_team_en_stats?.en_success_rate?.toFixed(1) || 'N/A'}% success rate, Leading team ${opp.leading_team_en_stats?.en_success_rate?.toFixed(1) || 'N/A'}% when opponent pulls.`,
            urgency: 'CRITICAL',
            expires_in: 120,
            sound_alert: true,
            timestamp: new Date().toISOString()
          };

          // Show alert
          showBetAlert(alert);
          alertedGamesRef.current.add(alertKey);

          console.log(`[GOALIE PULL MONITOR] ✅ Alert shown for ${opp.away_team} @ ${opp.home_team}`);
        }
      } catch (error) {
        console.error('[GOALIE PULL MONITOR] Error:', error);
      }
    };

    // Initial check
    checkForGoaliePulls();

    // Set up polling
    const interval = setInterval(checkForGoaliePulls, pollInterval);

    return () => clearInterval(interval);
  }, [enabled, pollInterval, showBetAlert]);

  // This component doesn't render anything
  return null;
}
