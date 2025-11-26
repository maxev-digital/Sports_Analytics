/**
 * Quarter Strategy Alert Monitor
 * Monitors Quarter Reversal and Cold Team Bounce-Back alerts via WebSocket
 * Triggers toast notifications when new alerts are detected
 */

import { useEffect, useRef } from 'react';
import { useQuarterReversalWebSocket } from '../hooks/useQuarterReversalWebSocket';
import { useBetAlertNotification } from '../contexts/BetAlertNotificationContext';
import { StrategyAlert } from '../types';
import { getBookmaker } from '../utils/bookmakers';

interface QuarterStrategyAlertMonitorProps {
  enabled?: boolean;
}

export function QuarterStrategyAlertMonitor({ enabled = true }: QuarterStrategyAlertMonitorProps) {
  const { opportunities, coldTeamOpportunities, connected } = useQuarterReversalWebSocket('default');
  const { showBetAlert } = useBetAlertNotification();

  // Track previously seen alerts to avoid duplicates
  const seenQRAlerts = useRef<Set<string>>(new Set());
  const seenCTAlerts = useRef<Set<string>>(new Set());

  // Alert queue to show one at a time
  const alertQueueRef = useRef<StrategyAlert[]>([]);
  const isProcessingQueueRef = useRef(false);

  // Queue processor - shows alerts one at a time with delay
  const processAlertQueue = async () => {
    if (isProcessingQueueRef.current || alertQueueRef.current.length === 0) return;

    isProcessingQueueRef.current = true;

    while (alertQueueRef.current.length > 0) {
      const alert = alertQueueRef.current.shift();
      if (alert) {
        showBetAlert(alert);
        // Wait 15 seconds before showing next alert
        await new Promise(resolve => setTimeout(resolve, 15000));
      }
    }

    isProcessingQueueRef.current = false;
  };

  // Add alert to queue
  const queueAlert = (alert: StrategyAlert) => {
    alertQueueRef.current.push(alert);
    processAlertQueue();
  };

  // Monitor Quarter Reversal opportunities
  useEffect(() => {
    if (!enabled || !connected) return;

    opportunities.forEach(opp => {
      const alertKey = `${opp.game_id}-${opp.strategy}-${opp.quarter}`;

      // Only trigger toast for new alerts
      if (!seenQRAlerts.current.has(alertKey)) {
        seenQRAlerts.current.add(alertKey);

        console.log('🔄 New Quarter Reversal Alert:', opp.matchup, opp.trigger);

        const strategyAlert = convertQuarterReversalToStrategyAlert(opp);
        queueAlert(strategyAlert);
      }
    });
  }, [opportunities, enabled, connected]);

  // Monitor Cold Team Bounce-Back opportunities
  useEffect(() => {
    if (!enabled || !connected) return;

    coldTeamOpportunities.forEach(opp => {
      const alertKey = `${opp.game_id}-${opp.strategy}-${opp.quarter}`;

      // Only trigger toast for new alerts
      if (!seenCTAlerts.current.has(alertKey)) {
        seenCTAlerts.current.add(alertKey);

        console.log('❄️ New Cold Team Alert:', opp.matchup, opp.trigger);

        const strategyAlert = convertColdTeamToStrategyAlert(opp);
        queueAlert(strategyAlert);
      }
    });
  }, [coldTeamOpportunities, enabled, connected]);

  // This component doesn't render anything
  return null;
}

// ========== ALERT CONVERTERS ==========

function convertQuarterReversalToStrategyAlert(opp: any): StrategyAlert {
  const bestRec = opp.recommendations?.[0];
  const bookInfo = bestRec ? getBookmaker(bestRec.bookmaker) : null;

  // Determine urgency based on strategy type
  let urgency: 'CRITICAL' | 'HIGH' | 'MEDIUM' = 'HIGH';
  if (opp.strategy?.includes('OT') || opp.alert_level === 'CRITICAL') {
    urgency = 'CRITICAL';
  } else if (opp.alert_level === 'MEDIUM') {
    urgency = 'MEDIUM';
  }

  return {
    strategy_id: `quarter-reversal-${opp.game_id}-${opp.quarter}-${Date.now()}`,
    strategy_name: 'Quarter Reversal',
    game_id: opp.game_id,
    home_team: opp.home_team,
    away_team: opp.away_team,
    sport: 'basketball_nba',
    confidence: opp.alert_level || 'HIGH',
    trigger: opp.trigger,
    recommendation: `Bet ${opp.reversal_team} to win ${opp.quarter}. Look for spreads at -115 or better, or moneylines up to +160.`,
    edge_percentage: bestRec?.ev_percent || 8.0,
    expected_roi: parseFloat(opp.expected_roi?.replace(/[^0-9.-]/g, '') || '26.56'),
    win_probability: opp.confidence || 0.5625,
    stake_recommendation: bestRec?.kelly_size || 100,
    bet_options: opp.recommendations?.slice(0, 3).map((rec: any, idx: number) => {
      const book = getBookmaker(rec.bookmaker);
      return {
        label: rec.label || rec.side,
        market_type: rec.bet_type === 'spread' ? 'spreads' : rec.bet_type === 'moneyline' ? 'h2h' : 'totals',
        bet_side: rec.side,
        line: rec.line,
        odds: rec.price,
        bookmaker: rec.bookmaker,
        bookmaker_title: book.name,
        bookmaker_logo: book.logo,
        probability: rec.probability || 0.5625,
        expected_value: rec.ev_percent || 0
      };
    }) || [],
    reasoning: opp.reasoning,
    urgency: urgency,
    expires_in: 600, // 10 minutes (typical quarter length)
    sound_alert: true,
    timestamp: opp.timestamp || new Date().toISOString()
  };
}

function convertColdTeamToStrategyAlert(opp: any): StrategyAlert {
  const bestRec = opp.recommendations?.[0];
  const bookInfo = bestRec ? getBookmaker(bestRec.bookmaker) : null;

  return {
    strategy_id: `cold-team-${opp.game_id}-${opp.quarter}-${Date.now()}`,
    strategy_name: 'Cold Team Bounce-Back',
    game_id: opp.game_id,
    home_team: opp.home_team,
    away_team: opp.away_team,
    sport: 'basketball_nba',
    confidence: opp.alert_level || 'HIGH',
    trigger: opp.trigger,
    recommendation: `Bet ${opp.cold_team} to win Q4. Desperation play - 64% win rate. Target spreads at -115 or better, or moneylines up to +160.`,
    edge_percentage: bestRec?.ev_percent || 12.0,
    expected_roi: parseFloat(opp.expected_roi?.replace(/[^0-9.-]/g, '') || '43.93'),
    win_probability: opp.confidence || 0.6397,
    stake_recommendation: bestRec?.kelly_size || 100,
    bet_options: opp.recommendations?.slice(0, 3).map((rec: any, idx: number) => {
      const book = getBookmaker(rec.bookmaker);
      return {
        label: rec.label || rec.side,
        market_type: rec.bet_type === 'spread' ? 'spreads' : rec.bet_type === 'moneyline' ? 'h2h' : 'totals',
        bet_side: rec.side,
        line: rec.line,
        odds: rec.price,
        bookmaker: rec.bookmaker,
        bookmaker_title: book.name,
        bookmaker_logo: book.logo,
        probability: rec.probability || 0.6397,
        expected_value: rec.ev_percent || 0
      };
    }) || [],
    reasoning: opp.reasoning,
    urgency: 'HIGH',
    expires_in: 600, // 10 minutes (Q4 length)
    sound_alert: true,
    timestamp: opp.timestamp || new Date().toISOString()
  };
}
