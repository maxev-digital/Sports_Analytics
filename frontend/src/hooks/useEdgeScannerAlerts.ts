/**
 * Edge Scanner Live Projections Alert Hook
 *
 * Monitors the Edge Scanner API for high-value live betting projections
 * and triggers toast notifications via the existing BetAlertNotification system.
 */

import { useEffect, useRef } from 'react';
import { getApiUrl } from '../config';
import { useBetAlertNotification } from '../contexts/BetAlertNotificationContext';
import { StrategyAlert } from '../types';

interface BestPlay {
  id: string;
  sport: string;
  game_id: string;
  game_time: string;
  home_team: string;
  away_team: string;
  bet_type: string;
  market: string;
  market_line: number;
  model_prediction: number;
  model_name: string;
  model_confidence: number;
  edge: number;
  edge_percentage: number;
  recommendation: string;
  kelly_fraction: number;
  suggested_bet_size: string;
  probability: number;
  is_pregame?: boolean;
  projection_type?: string;
  consensus: {
    models_agree: number;
    models_total: number;
    strength: string;
  };
}

interface UseEdgeScannerAlertsOptions {
  enabled?: boolean;
  minEdge?: number;           // Minimum edge to trigger alert
  minConfidence?: number;     // Minimum model confidence
  pollInterval?: number;      // Polling frequency in ms
  sports?: string[];          // Filter by specific sports (optional)
}

export function useEdgeScannerAlerts(options: UseEdgeScannerAlertsOptions = {}) {
  const {
    enabled = true,
    minEdge = 3.5,              // Higher threshold for alerts
    minConfidence = 0.70,       // Higher confidence for quality alerts
    pollInterval = 20000,       // Poll every 20 seconds
    sports = []                 // Empty = all sports
  } = options;

  const { showBetAlert } = useBetAlertNotification();
  const seenAlertIds = useRef<Set<string>>(new Set());
  const isPolling = useRef(false);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    let intervalId: NodeJS.Timeout;

    const checkForLiveProjections = async () => {
      // Prevent concurrent requests
      if (isPolling.current) {
        return;
      }

      try {
        isPolling.current = true;

        // Build query parameters
        const params = new URLSearchParams({
          projection_type: 'live',               // Only live games
          min_edge: minEdge.toString(),
          min_confidence: minConfidence.toString(),
          limit: '20'
        });

        // Optionally filter by sport
        if (sports.length > 0) {
          params.append('sport', sports.join(','));
        }

        const response = await fetch(getApiUrl(`edge-scanner/best-plays?${params.toString()}`));

        if (!response.ok) {
          console.error('Failed to fetch live projections:', response.statusText);
          return;
        }

        const data = await response.json();
        const plays: BestPlay[] = data.plays || [];

        // Find new alerts we haven't seen yet
        const newAlerts = plays.filter(play => !seenAlertIds.current.has(play.id));

        // Convert each play to a StrategyAlert and show
        newAlerts.forEach(play => {
          seenAlertIds.current.add(play.id);

          const strategyAlert: StrategyAlert = convertPlayToAlert(play);

          // Show the alert
          showBetAlert(strategyAlert);

          // Log for debugging
          console.log('🤖 New Live ML Projection Alert:', {
            model: play.model_name,
            game: `${play.away_team} @ ${play.home_team}`,
            bet: play.recommendation,
            edge: `+${play.edge.toFixed(1)}`,
            confidence: `${(play.model_confidence * 100).toFixed(1)}%`,
            kelly: `${(play.kelly_fraction * 100).toFixed(1)}%`
          });
        });

      } catch (error) {
        console.error('Error checking for live projections:', error);
      } finally {
        isPolling.current = false;
      }
    };

    // Initial check
    checkForLiveProjections();

    // Set up polling
    intervalId = setInterval(checkForLiveProjections, pollInterval);

    // Cleanup
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [enabled, minEdge, minConfidence, pollInterval, sports.join(','), showBetAlert]);

  // Method to clear seen alerts (useful for testing)
  const resetSeenAlerts = () => {
    seenAlertIds.current.clear();
  };

  return {
    resetSeenAlerts,
    seenCount: seenAlertIds.current.size,
    isEnabled: enabled
  };
}

/**
 * Convert Edge Scanner BestPlay to StrategyAlert format
 */
function convertPlayToAlert(play: BestPlay): StrategyAlert {
  // Determine confidence level based on edge and model confidence
  const confidenceScore = (Math.abs(play.edge) / 10) * play.model_confidence;
  let confidence: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

  if (confidenceScore >= 0.5 || Math.abs(play.edge) >= 5) {
    confidence = 'CRITICAL';
  } else if (confidenceScore >= 0.35 || Math.abs(play.edge) >= 4) {
    confidence = 'HIGH';
  } else if (confidenceScore >= 0.25) {
    confidence = 'MEDIUM';
  } else {
    confidence = 'LOW';
  }

  // Format the strategy name
  const strategyName = `${play.sport} ${play.model_name} - ${play.bet_type}`;

  // Format the trigger message
  const trigger = `${play.away_team} @ ${play.home_team} - LIVE IN PROGRESS`;

  // Format recommendation with line
  const recommendation = `${play.recommendation} ${play.market_line}`;

  // Calculate expected ROI (simplified)
  const expectedROI = Math.abs(play.edge) * 1.5;

  // Estimate win probability from edge
  const winProbability = play.probability || (0.5 + (play.edge / 20));

  // Create bet options (simplified - in production would fetch real books)
  const betOptions = [{
    label: recommendation,
    market_type: play.bet_type.toLowerCase(),
    bet_side: play.recommendation,
    line: play.market_line,
    odds: convertProbabilityToAmericanOdds(winProbability),
    bookmaker: 'Edge Scanner',
    bookmaker_title: 'Best Available',
    probability: winProbability,
    expected_value: play.edge / 100,
    kelly_size: play.kelly_fraction
  }];

  return {
    strategy_id: `edge_scanner_${play.model_name}_${play.bet_type}`,
    strategy_name: strategyName,
    confidence,
    trigger,
    recommendation,
    edge_percentage: Math.abs(play.edge),
    expected_roi: expectedROI,
    win_probability: winProbability,
    stake_recommendation: play.kelly_fraction * 100,  // Convert to units
    bet_options: betOptions,
    urgency: confidence,
    expires_in: 180,  // 3 minutes for live alerts
    sound_alert: true,
    timestamp: new Date().toISOString()
  };
}

/**
 * Convert probability to American odds format
 */
function convertProbabilityToAmericanOdds(probability: number): number {
  if (probability >= 0.5) {
    return Math.round(-100 * probability / (1 - probability));
  } else {
    return Math.round(100 * (1 - probability) / probability);
  }
}

export default useEdgeScannerAlerts;
