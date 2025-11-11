/**
 * Global Alert Monitor
 * Monitors for new alerts across all pages and triggers toast notifications
 * Runs in background regardless of which page user is on
 */

import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiUrl } from '../config';
import { useToast } from './Toast';
import { useSoundEffect } from '../hooks/useSoundEffect';

interface AlertsData {
  arbitrage: { count: number };
  steam_moves: { count: number };
  middles: { count: number };
  sharp_money: { count: number };
  schedule_fatigue: { count: number };
}

interface GlobalAlertMonitorProps {
  enabled?: boolean;
  pollInterval?: number; // milliseconds
}

export function GlobalAlertMonitor({
  enabled = true,
  pollInterval = 10000 // 10 seconds
}: GlobalAlertMonitorProps) {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const previousCountRef = useRef({
    arbitrage: -1,
    steam: -1,
    middles: -1,
    sharpMoney: -1,
    scheduleFatigue: -1
  });
  const isInitialLoadRef = useRef(true);

  // Sound effects
  const playArbitrageSound = useSoundEffect('alert-bell.mp3', 0.7);
  const playMiddleSound = useSoundEffect('alert-bell.mp3', 0.6);
  const playSteamMoveSound = useSoundEffect('alert-bell.mp3', 0.7);

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
          const newAlerts = data.arbitrage.count - previousCountRef.current.arbitrage;
          playArbitrageSound();
          showToast(
            `🚨 ${newAlerts} NEW ARBITRAGE OPPORTUNIT${newAlerts > 1 ? 'IES' : 'Y'} - Risk-Free Profit!`,
            'success',
            () => navigate('/alerts', { state: { category: 'pregame', tab: 'arbitrage' } })
          );
        }
        previousCountRef.current.arbitrage = data.arbitrage.count;

        // Check for new middle alerts
        if (data.middles.count > previousCountRef.current.middles && previousCountRef.current.middles >= 0) {
          const newAlerts = data.middles.count - previousCountRef.current.middles;
          playMiddleSound();
          showToast(
            `🎯 ${newAlerts} NEW MIDDLE${newAlerts > 1 ? 'S' : ''} - Win Both Sides!`,
            'success',
            () => navigate('/alerts', { state: { category: 'pregame', tab: 'lines' } })
          );
        }
        previousCountRef.current.middles = data.middles.count;

        // Check for new steam move alerts
        if (data.steam_moves.count > previousCountRef.current.steam && previousCountRef.current.steam >= 0) {
          const newAlerts = data.steam_moves.count - previousCountRef.current.steam;
          playSteamMoveSound();
          showToast(
            `⚡ ${newAlerts} NEW STEAM MOVE${newAlerts > 1 ? 'S' : ''} - Sharp Money Alert!`,
            'warning',
            () => navigate('/alerts', { state: { category: 'pregame', tab: 'steam' } })
          );
        }
        previousCountRef.current.steam = data.steam_moves.count;

        // Check for new sharp money alerts
        if (data.sharp_money.count > previousCountRef.current.sharpMoney && previousCountRef.current.sharpMoney >= 0) {
          const newAlerts = data.sharp_money.count - previousCountRef.current.sharpMoney;
          playSteamMoveSound();
          showToast(
            `💰 ${newAlerts} NEW SHARP MONEY ALERT${newAlerts > 1 ? 'S' : ''} - Pro Bettors Active!`,
            'info',
            () => navigate('/alerts', { state: { category: 'pregame', tab: 'sharp-money' } })
          );
        }
        previousCountRef.current.sharpMoney = data.sharp_money.count;

        // Check for new schedule fatigue alerts
        if (data.schedule_fatigue.count > previousCountRef.current.scheduleFatigue && previousCountRef.current.scheduleFatigue >= 0) {
          const newAlerts = data.schedule_fatigue.count - previousCountRef.current.scheduleFatigue;
          playSteamMoveSound();
          showToast(
            `😴 ${newAlerts} NEW SCHEDULE FATIGUE ALERT${newAlerts > 1 ? 'S' : ''} - Rest Advantage Detected!`,
            'warning',
            () => navigate('/alerts', { state: { category: 'pregame', tab: 'fatigue' } })
          );
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
  }, [enabled, pollInterval, playArbitrageSound, playMiddleSound, playSteamMoveSound, showToast, navigate]);

  // This component doesn't render anything
  return null;
}
