/**
 * Real-time Alert Monitoring Hook
 * Checks for matching alerts based on user preferences and game conditions
 */
import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/Toast';
import { useBetAlertNotification } from '../contexts/BetAlertNotificationContext';
import { getAlertPreferences } from '../api/alertPreferences';
import { getSystemById } from '../data/advancedSystems';
import { StrategyAlert } from '../types';

interface AlertTrigger {
  systemId: number;
  systemName: string;
  gameId: string;
  matchup: string;
  strength?: number;
  timestamp: number;
}

export function useAlertMonitoring(games: any[]) {
  const { username } = useAuth();
  const { showToast } = useToast();
  const { showBetAlert } = useBetAlertNotification();
  const [enabledSystems, setEnabledSystems] = useState<number[]>([]);
  const [lastCheck, setLastCheck] = useState<number>(Date.now());
  const shownAlerts = useRef<Set<string>>(new Set());

  // Load enabled systems every 30 seconds
  useEffect(() => {
    if (!username) return;

    const loadPreferences = async () => {
      try {
        const prefs = await getAlertPreferences(username);
        setEnabledSystems(prefs.enabled_systems);
      } catch (error) {
        console.error('Failed to load alert preferences:', error);
      }
    };

    loadPreferences();
    const interval = setInterval(loadPreferences, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, [username]);

  // Check for alert conditions in live games
  useEffect(() => {
    if (!username || enabledSystems.length === 0 || !games || games.length === 0) {
      return;
    }

    const checkForAlerts = () => {
      const now = Date.now();
      const newAlerts: AlertTrigger[] = [];

      games.forEach((game: any) => {
        // Only check live games
        if (game.status !== 'live') return;

        // Check if game has projection data with strength signal
        const projection = game.projection;
        if (!projection || !projection.strength_factor) return;

        // Check each enabled system
        enabledSystems.forEach((systemId) => {
          const system = getSystemById(systemId);
          if (!system) return;

          // Check if this system applies to this sport
          const sportMatches = system.sports.includes(game.sport_key) || system.sports.includes('multi-sport');
          if (!sportMatches) return;

          // Check system-specific conditions
          let shouldAlert = false;
          const alertKey = `${game.id}-${systemId}`;

          // System #1: Max EV Boost (NBA) - Check for regression signals
          if (systemId === 1 && projection.strength_factor >= 50) {
            shouldAlert = true;
          }

          // System #2: Max EV Boost (NCAAB) - Check for regression signals
          if (systemId === 2 && projection.strength_factor >= 50) {
            shouldAlert = true;
          }

          // System #6: Goalie Pull Alert (NHL) - Check for specific conditions
          if (systemId === 6 && game.sport_key === 'icehockey_nhl') {
            // This would check for goalie pull conditions from the backend
            // For now, we'll trigger on high strength signals
            if (projection.strength_factor >= 70) {
              shouldAlert = true;
            }
          }

          // System #14: Quarter Reversal Strategy
          if (systemId === 14 && projection.strength_factor >= 55) {
            shouldAlert = true;
          }

          // System #23: Halftime Tracker
          if (systemId === 23 && game.period && game.period.includes('Half')) {
            if (projection.strength_factor >= 50) {
              shouldAlert = true;
            }
          }

          // System #24: Momentum Detector
          if (systemId === 24 && projection.pace_differential) {
            if (Math.abs(projection.pace_differential) > 3 && projection.strength_factor >= 50) {
              shouldAlert = true;
            }
          }

          // System #25: Pace Mismatch Detector
          if (systemId === 25 && projection.pace_differential) {
            if (Math.abs(projection.pace_differential) > 5 && projection.strength_factor >= 50) {
              shouldAlert = true;
            }
          }

          // System #8: End-Game Unders
          if (systemId === 8 && game.period && game.period.includes('4th')) {
            const scoreDiff = Math.abs((game.home_score || 0) - (game.away_score || 0));
            if (scoreDiff > 15 && projection.recommendation === 'UNDER') {
              shouldAlert = true;
            }
          }

          // If alert should trigger and hasn't been shown yet
          if (shouldAlert && !shownAlerts.current.has(alertKey)) {
            newAlerts.push({
              systemId,
              systemName: system.name,
              gameId: game.id,
              matchup: `${game.away_team} @ ${game.home_team}`,
              strength: projection.strength_factor,
              timestamp: now
            });
            shownAlerts.current.add(alertKey);
          }
        });
      });

      // Show bet alert notifications for new alerts
      newAlerts.forEach((alertTrigger) => {
        // Find the game data for bet options
        const game = games.find(g => g.id === alertTrigger.gameId);

        // Create a full StrategyAlert object
        const strategyAlert: StrategyAlert = {
          strategy_id: alertTrigger.systemId.toString(),
          strategy_name: alertTrigger.systemName,
          confidence: alertTrigger.strength && alertTrigger.strength >= 70 ? 'CRITICAL' :
                      alertTrigger.strength && alertTrigger.strength >= 60 ? 'HIGH' :
                      alertTrigger.strength && alertTrigger.strength >= 50 ? 'MEDIUM' : 'LOW',
          trigger: `${alertTrigger.matchup} - Detected at ${new Date().toLocaleTimeString()}`,
          recommendation: game?.projection?.recommendation ?
            `Bet ${game.projection.recommendation} ${(game.projection.current_live_total || game.projection.current_total)?.toFixed?.(1) || game.projection.current_live_total || game.projection.current_total}` :
            'Check live odds for betting opportunity',
          edge_percentage: Number((game?.projection?.edge || alertTrigger.strength || 0).toFixed(1)),
          expected_roi: Number(((game?.projection?.edge || alertTrigger.strength || 0) * 1.2).toFixed(1)),
          win_probability: Number((0.5 + ((alertTrigger.strength || 50) - 50) / 100).toFixed(2)),
          stake_recommendation: Number((game?.projection?.unit_recommendation || 1.0).toFixed(1)),
          bet_options: game?.bookmakers?.slice(0, 3).map((book: any) => ({
            label: `${game.projection?.recommendation || 'OVER'} ${book.total?.toFixed?.(1) || book.total}`,
            market_type: 'totals',
            bet_side: game.projection?.recommendation || 'OVER',
            line: Number(book.total?.toFixed?.(1) || book.total),
            odds: Math.round(game.projection?.recommendation === 'OVER' ? book.over_price : book.under_price),
            bookmaker: book.bookmaker,
            bookmaker_title: book.bookmaker,
            probability: Number((0.5 + ((alertTrigger.strength || 50) - 50) / 100).toFixed(2)),
            expected_value: Number(((game?.projection?.edge || 0) / 100).toFixed(2)),
            kelly_size: Number((game?.projection?.unit_recommendation || 1.0).toFixed(1))
          })) || [],
          urgency: alertTrigger.strength && alertTrigger.strength >= 70 ? 'CRITICAL' :
                   alertTrigger.strength && alertTrigger.strength >= 60 ? 'HIGH' : 'MEDIUM',
          expires_in: 300, // 5 minutes default
          sound_alert: true,
          timestamp: new Date().toISOString()
        };

        // Show the enhanced bet alert notification
        showBetAlert(strategyAlert);

        // Also show simple toast for backwards compatibility
        const strengthText = alertTrigger.strength ? ` (${alertTrigger.strength.toFixed(1)}%)` : '';
        showToast(
          `🚨 ${alertTrigger.systemName}: ${alertTrigger.matchup}${strengthText}`,
          'info'
        );
      });

      setLastCheck(now);
    };

    // Check immediately, then every 15 seconds
    checkForAlerts();
    const interval = setInterval(checkForAlerts, 15000); // 15 seconds

    return () => clearInterval(interval);
  }, [username, enabledSystems, games, showToast]);

  // Clear shown alerts when games change significantly (new set of games)
  useEffect(() => {
    const gameIds = new Set(games.map(g => g.id));
    const alertKeys = Array.from(shownAlerts.current);

    // Remove alerts for games that are no longer in the list
    alertKeys.forEach(alertKey => {
      const gameId = alertKey.split('-')[0];
      if (!gameIds.has(gameId)) {
        shownAlerts.current.delete(alertKey);
      }
    });
  }, [games]);

  return {
    enabledSystemsCount: enabledSystems.length,
    lastCheck,
    isMonitoring: enabledSystems.length > 0 && username !== null
  };
}
