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
  sharp_money: { count: number; alerts: any[] };
  schedule_fatigue: { count: number; alerts: any[] };
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
    middles: -1,
    sharpMoney: -1,
    scheduleFatigue: -1
  });
  const isInitialLoadRef = useRef(true);

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
          previousCountRef.current.sharpMoney = data.sharp_money.count;
          previousCountRef.current.scheduleFatigue = data.schedule_fatigue.count;
          isInitialLoadRef.current = false;
          return;
        }

        // Check for new arbitrage alerts
        if (data.arbitrage.count > previousCountRef.current.arbitrage && previousCountRef.current.arbitrage >= 0) {
          const newAlerts = data.arbitrage.alerts.slice(previousCountRef.current.arbitrage);
          newAlerts.forEach(alert => showBetAlert(convertArbitrageToStrategyAlert(alert)));
        }
        previousCountRef.current.arbitrage = data.arbitrage.count;

        // Check for new middle alerts
        if (data.middles.count > previousCountRef.current.middles && previousCountRef.current.middles >= 0) {
          const newAlerts = data.middles.alerts.slice(previousCountRef.current.middles);
          newAlerts.forEach(alert => showBetAlert(convertMiddleToStrategyAlert(alert)));
        }
        previousCountRef.current.middles = data.middles.count;

        // Check for new steam move alerts
        if (data.steam_moves.count > previousCountRef.current.steam && previousCountRef.current.steam >= 0) {
          const newAlerts = data.steam_moves.alerts.slice(previousCountRef.current.steam);
          newAlerts.forEach(alert => showBetAlert(convertSteamMoveToStrategyAlert(alert)));
        }
        previousCountRef.current.steam = data.steam_moves.count;

        // Check for new sharp money alerts
        if (data.sharp_money.count > previousCountRef.current.sharpMoney && previousCountRef.current.sharpMoney >= 0) {
          const newAlerts = data.sharp_money.alerts.slice(previousCountRef.current.sharpMoney);
          newAlerts.forEach(alert => showBetAlert(convertSharpMoneyToStrategyAlert(alert)));
        }
        previousCountRef.current.sharpMoney = data.sharp_money.count;

        // Check for new schedule fatigue alerts
        if (data.schedule_fatigue.count > previousCountRef.current.scheduleFatigue && previousCountRef.current.scheduleFatigue >= 0) {
          const newAlerts = data.schedule_fatigue.alerts.slice(previousCountRef.current.scheduleFatigue);
          newAlerts.forEach(alert => showBetAlert(convertScheduleFatigueToStrategyAlert(alert)));
        }
        previousCountRef.current.scheduleFatigue = data.schedule_fatigue.count;

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
  const books = alert.books_moved || [];
  const bookInfo = books.length > 0 ? getBookmaker(books[0]) : getBookmaker('draftkings');

  return {
    strategy_id: `steam-${alert.game_id}-${Date.now()}`,
    strategy_name: 'Steam Move Detected',
    game_id: alert.game_id,
    home_team: alert.home_team,
    away_team: alert.away_team,
    sport: alert.sport || alert.sport_key,
    confidence: alert.consensus_percent > 80 ? 'HIGH' : 'MEDIUM',
    trigger: `Sharp money caused ${Math.abs(alert.movement || 0).toFixed(1)} point line movement`,
    recommendation: `Follow the sharp money on ${alert.side || 'this side'}`,
    edge_percentage: Math.min(alert.consensus_percent / 10 || 5, 10),
    expected_roi: Math.min(alert.consensus_percent / 8 || 6, 12),
    win_probability: alert.consensus_percent / 100 || 0.6,
    stake_recommendation: 1.5,
    bet_options: [
      {
        label: `${alert.side || 'Side'} ${alert.new_line || ''}`,
        market_type: alert.market_type || 'spreads',
        bet_side: alert.side || 'Side',
        line: alert.new_line,
        odds: -110,
        bookmaker: books[0] || 'draftkings',
        bookmaker_title: bookInfo.name,
        bookmaker_logo: bookInfo.logo,
        probability: alert.consensus_percent / 100 || 0.6,
        expected_value: alert.consensus_percent / 10 || 5
      }
    ],
    reasoning: `${books.length} books moved in sync - clear sharp action detected`,
    urgency: 'HIGH',
    expires_in: 300,
    sound_alert: true,
    timestamp: alert.timestamp || new Date().toISOString()
  };
}

function convertSharpMoneyToStrategyAlert(alert: any): StrategyAlert {
  const books = alert.sharp_books_involved || [];
  const bookInfo = books.length > 0 ? getBookmaker(books[0]) : getBookmaker('draftkings');

  return {
    strategy_id: `sharp-${alert.game_id}-${Date.now()}`,
    strategy_name: 'Sharp Money Alert',
    game_id: alert.game_id,
    home_team: alert.home_team,
    away_team: alert.away_team,
    sport: alert.sport || alert.sport_key,
    confidence: alert.confidence_level as any || 'MEDIUM',
    trigger: alert.reasoning || 'Sharp action detected from professional bettors',
    recommendation: alert.recommendation || `Bet with the sharp money`,
    edge_percentage: alert.edge_percent || 5,
    expected_roi: (alert.edge_percent || 5) * 1.2,
    win_probability: 0.6,
    stake_recommendation: alert.confidence_level === 'HIGH' ? 2.0 : 1.5,
    bet_options: [
      {
        label: alert.recommendation || 'Sharp Play',
        market_type: alert.market_type || 'h2h',
        bet_side: alert.recommendation || '',
        line: alert.current_line,
        odds: -110,
        bookmaker: books[0] || 'draftkings',
        bookmaker_title: bookInfo.name,
        bookmaker_logo: bookInfo.logo,
        probability: 0.6,
        expected_value: alert.edge_percent || 5
      }
    ],
    reasoning: alert.reasoning || 'Professional bettors are taking this side',
    urgency: alert.confidence_level === 'HIGH' ? 'HIGH' : 'MEDIUM',
    expires_in: 300,
    sound_alert: true,
    timestamp: alert.timestamp || new Date().toISOString()
  };
}

function convertScheduleFatigueToStrategyAlert(alert: any): StrategyAlert {
  return {
    strategy_id: `fatigue-${alert.game_id}-${Date.now()}`,
    strategy_name: 'Schedule Fatigue',
    game_id: alert.game_id,
    home_team: alert.home_team,
    away_team: alert.away_team,
    sport: alert.sport || alert.sport_key,
    confidence: alert.confidence_level as any || 'MEDIUM',
    trigger: `${alert.favored_side === 'home' ? alert.home_team : alert.away_team} has rest advantage`,
    recommendation: `Bet ${alert.favored_side === 'home' ? alert.home_team : alert.away_team} (${alert.rest_differential} day rest edge)`,
    edge_percentage: alert.edge_percent || 5,
    expected_roi: (alert.edge_percent || 5) * 1.2,
    win_probability: 0.58,
    stake_recommendation: alert.confidence_level === 'HIGH' ? 2.0 : 1.5,
    bet_options: [
      {
        label: `${alert.favored_side === 'home' ? alert.home_team : alert.away_team} (Rest Advantage)`,
        market_type: 'spreads',
        bet_side: alert.favored_side || 'home',
        odds: -110,
        bookmaker: 'draftkings',
        bookmaker_title: 'DraftKings',
        bookmaker_logo: getBookmaker('draftkings').logo,
        probability: 0.58,
        expected_value: alert.edge_percent || 5
      }
    ],
    reasoning: alert.reasoning || `${alert.rest_differential} day rest differential creates fatigue edge`,
    urgency: alert.confidence_level === 'HIGH' ? 'HIGH' : 'MEDIUM',
    expires_in: 3600,
    sound_alert: true,
    timestamp: alert.timestamp || new Date().toISOString()
  };
}
