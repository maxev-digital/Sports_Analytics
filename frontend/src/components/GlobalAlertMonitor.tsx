/**
 * Global Alert Monitor
 * Monitors for new alerts across all pages and triggers RICH bet alert notifications
 * Uses BetAlertToast system for detailed notifications with bookmaker icons
 */

import { useEffect, useRef } from 'react';
import { getApiUrl } from '../config';
import { useBetAlertNotification } from '../contexts/BetAlertNotificationContext';
import { StrategyAlert } from '../types';
import { getBookmaker, formatOdds, getMarketLabel } from '../utils/bookmakers';

interface AlertsData {
  arbitrage: { count: number; alerts: any[] };
  steam_moves: { count: number; alerts: any[] };
  middles: { count: number; alerts: any[] };
}

interface GlobalAlertMonitorProps {
  enabled?: boolean;
  pollInterval?: number; // milliseconds
}

export function GlobalAlertMonitor({
  enabled = true,
  pollInterval = 10000 // 10 seconds
}: GlobalAlertMonitorProps) {
  const { showBetAlert } = useBetAlertNotification();
  const previousCountRef = useRef({
    arbitrage: -1,
    steam: -1,
    middles: -1
  });
  const isInitialLoadRef = useRef(true);
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
        // Wait 10 seconds before showing next alert
        // This gives audio chain time to complete and user time to read/act
        await new Promise(resolve => setTimeout(resolve, 10000));
      }
    }

    isProcessingQueueRef.current = false;
  };

  // Add alerts to queue instead of showing immediately
  const queueAlert = (alert: StrategyAlert) => {
    alertQueueRef.current.push(alert);
    processAlertQueue();
  };

  useEffect(() => {
    if (!enabled) return;

    const checkForAlerts = async () => {
      try {
        const response = await fetch(getApiUrl('alerts/all?user_id=default'));
        if (!response.ok) return;

        const data: AlertsData = await response.json();

        // Skip initial load
        if (isInitialLoadRef.current) {
          previousCountRef.current.arbitrage = data.arbitrage.count;
          previousCountRef.current.steam = data.steam_moves.count;
          previousCountRef.current.middles = data.middles.count;
          isInitialLoadRef.current = false;
          return;
        }

        // Collect all new alerts into queue
        const newAlertsToQueue: StrategyAlert[] = [];

        // Check for new arbitrage alerts
        if (data.arbitrage.count > previousCountRef.current.arbitrage && previousCountRef.current.arbitrage >= 0) {
          const newAlerts = data.arbitrage.alerts.slice(previousCountRef.current.arbitrage);
          newAlerts.forEach(alert => newAlertsToQueue.push(convertArbitrageToStrategyAlert(alert)));
        }
        previousCountRef.current.arbitrage = data.arbitrage.count;

        // Check for new middle alerts
        if (data.middles.count > previousCountRef.current.middles && previousCountRef.current.middles >= 0) {
          const newAlerts = data.middles.alerts.slice(previousCountRef.current.middles);
          newAlerts.forEach(alert => newAlertsToQueue.push(convertMiddleToStrategyAlert(alert)));
        }
        previousCountRef.current.middles = data.middles.count;

        // Check for new steam move alerts
        if (data.steam_moves.count > previousCountRef.current.steam && previousCountRef.current.steam >= 0) {
          const newAlerts = data.steam_moves.alerts.slice(previousCountRef.current.steam);
          newAlerts.forEach(alert => newAlertsToQueue.push(convertSteamMoveToStrategyAlert(alert)));
        }
        previousCountRef.current.steam = data.steam_moves.count;

        // Queue all new alerts (will be shown one at a time with 3s delay)
        newAlertsToQueue.forEach(alert => queueAlert(alert));

      } catch (error) {
        console.error('[GLOBAL ALERT MONITOR] Error fetching alerts:', error);
      }
    };

    // Initial check
    checkForAlerts();

    // Set up polling interval
    const intervalId = setInterval(checkForAlerts, pollInterval);

    return () => clearInterval(intervalId);
  }, [enabled, pollInterval, showBetAlert]);

  // This component doesn't render anything
  return null;
}

// ========== ALERT CONVERTERS ==========

function convertArbitrageToStrategyAlert(alert: any): StrategyAlert {
  const book1 = getBookmaker(alert.book_a || alert.bookmaker_a || '');
  const book2 = getBookmaker(alert.book_b || alert.bookmaker_b || '');

  return {
    strategy_id: `arbitrage-${alert.game_id}-${Date.now()}`,
    strategy_name: 'Arbitrage Opportunity',
    game_id: alert.game_id,
    home_team: alert.home_team,
    away_team: alert.away_team,
    sport: alert.sport || alert.sport_key,
    confidence: 'HIGH',
    trigger: `Risk-free profit detected across ${book1.name} and ${book2.name}`,
    recommendation: `Place both sides - guaranteed profit regardless of outcome`,
    edge_percentage: alert.profit_percent || 0,
    expected_roi: alert.profit_percent || 0,
    win_probability: 1.0, // 100% - it's arbitrage
    stake_recommendation: alert.total_stake || 100,
    bet_options: [
      {
        label: `${alert.side_a || 'Side A'}`,
        market_type: alert.market_type || 'h2h',
        bet_side: alert.side_a || 'Side A',
        odds: alert.odds_a || 0,
        bookmaker: alert.book_a || '',
        bookmaker_title: book1.name,
        bookmaker_logo: book1.logo,
        probability: 0.5,
        expected_value: alert.profit_percent / 2 || 0
      },
      {
        label: `${alert.side_b || 'Side B'}`,
        market_type: alert.market_type || 'h2h',
        bet_side: alert.side_b || 'Side B',
        odds: alert.odds_b || 0,
        bookmaker: alert.book_b || '',
        bookmaker_title: book2.name,
        bookmaker_logo: book2.logo,
        probability: 0.5,
        expected_value: alert.profit_percent / 2 || 0
      }
    ],
    reasoning: `Arbitrage opportunity found - bet both sides and lock in ${formatOdds(alert.profit_percent || 0)}% guaranteed profit`,
    urgency: 'CRITICAL',
    expires_in: alert.expires_in || 300,
    sound_alert: true,
    timestamp: alert.timestamp || new Date().toISOString()
  };
}

function convertMiddleToStrategyAlert(alert: any): StrategyAlert {
  const book1 = getBookmaker(alert.book_low || alert.bookmaker_low || '');
  const book2 = getBookmaker(alert.book_high || alert.bookmaker_high || '');

  return {
    strategy_id: `middle-${alert.game_id}-${Date.now()}`,
    strategy_name: 'Middle Opportunity',
    game_id: alert.game_id,
    home_team: alert.home_team,
    away_team: alert.away_team,
    sport: alert.sport || alert.sport_key,
    confidence: 'HIGH',
    trigger: `${alert.gap || 0} point gap detected - potential to win both sides`,
    recommendation: `Bet both sides of the middle - chance to win both or push one`,
    edge_percentage: alert.profit_percent || 0,
    expected_roi: alert.profit_percent || 0,
    win_probability: 0.15, // ~15% chance to hit middle
    stake_recommendation: 100,
    bet_options: [
      {
        label: `${alert.side_low || 'Low'} ${alert.low_line || ''}`,
        market_type: alert.market_type || 'totals',
        bet_side: alert.side_low || 'Low',
        line: alert.low_line,
        odds: alert.odds_low || 0,
        bookmaker: alert.book_low || '',
        bookmaker_title: book1.name,
        bookmaker_logo: book1.logo,
        probability: 0.5,
        expected_value: alert.profit_percent / 2 || 0
      },
      {
        label: `${alert.side_high || 'High'} ${alert.high_line || ''}`,
        market_type: alert.market_type || 'totals',
        bet_side: alert.side_high || 'High',
        line: alert.high_line,
        odds: alert.odds_high || 0,
        bookmaker: alert.book_high || '',
        bookmaker_title: book2.name,
        bookmaker_logo: book2.logo,
        probability: 0.5,
        expected_value: alert.profit_percent / 2 || 0
      }
    ],
    reasoning: `Middle opportunity with ${alert.gap || 0} point gap - potential to cash both tickets`,
    urgency: 'HIGH',
    expires_in: alert.expires_in || 300,
    sound_alert: true,
    timestamp: alert.timestamp || new Date().toISOString()
  };
}

function convertSteamMoveToStrategyAlert(alert: any): StrategyAlert {
  const movedBooks = alert.books_moved || [];
  const staleBooks = alert.books_not_moved || [];

  // Round movement to nearest 0.5 (lines only move in 0.5 or whole number increments)
  const movement = Math.abs(alert.movement || 0);
  const roundedMovement = Math.round(movement * 2) / 2; // Round to nearest 0.5

  // Determine which line to bet (the OLD line at stale books)
  const targetLine = alert.original_line || alert.best_stale_line || 0;
  const targetBook = alert.best_stale_book || (staleBooks.length > 0 ? staleBooks[0] : 'draftkings');
  const targetOdds = alert.best_stale_odds || -110;

  const bookInfo = getBookmaker(targetBook);

  return {
    strategy_id: `steam-${alert.game_id}-${Date.now()}`,
    strategy_name: 'Steam Move Detected',
    game_id: alert.game_id,
    home_team: alert.home_team,
    away_team: alert.away_team,
    sport: alert.sport || alert.sport_key,
    confidence: alert.consensus_percent > 80 ? 'HIGH' : 'MEDIUM',
    trigger: `${movedBooks.length} books moved ${roundedMovement} points - ${staleBooks.length} books still have stale numbers`,
    recommendation: staleBooks.length > 0
      ? `BET ${alert.side || 'the move'} at ${targetBook.toUpperCase()} before they adjust`
      : `BET ${alert.side || 'the move'} - all books moved, opportunity closing`,
    edge_percentage: Math.min(alert.consensus_percent / 10 || 5, 10),
    expected_roi: Math.min(alert.consensus_percent / 8 || 6, 12),
    win_probability: alert.consensus_percent / 100 || 0.65,
    stake_recommendation: staleBooks.length > 0 ? 2.0 : 1.0, // Higher stake if stale books exist
    bet_options: [
      {
        label: `${alert.side || 'Side'} ${targetLine || ''} (STALE NUMBER)`,
        market_type: alert.market_type || 'spreads',
        bet_side: alert.side || 'Side',
        line: targetLine,
        odds: targetOdds,
        bookmaker: targetBook,
        bookmaker_title: bookInfo.name,
        bookmaker_logo: bookInfo.logo,
        probability: alert.consensus_percent / 100 || 0.65,
        expected_value: roundedMovement * 2 // Value = how many points better you're getting
      }
    ],
    reasoning: staleBooks.length > 0
      ? `Steam move: ${movedBooks.length} books moved from ${alert.original_line} to ${alert.new_line}. Bet the OLD number at ${targetBook} before they catch up.`
      : `Steam move detected: ${movedBooks.length} books moved ${roundedMovement} pts in sync. All books adjusted - act fast.`,
    urgency: 'HIGH',
    expires_in: 180, // 3 minutes - steam moves expire quickly
    sound_alert: true,
    timestamp: alert.timestamp || new Date().toISOString()
  };
}

