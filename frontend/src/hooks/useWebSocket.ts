/**
 * WebSocket Hook for Real-Time Game Updates
 * Connects to backend WebSocket and provides live data
 */

import { useEffect, useState, useRef, useCallback } from 'react';
import { LiveGame } from '../types';

interface WebSocketMessage {
  type: string;
  timestamp: string;
  count?: number;
  games?: any[];
}

interface UseWebSocketReturn {
  games: LiveGame[];
  connected: boolean;
  lastUpdate: Date | null;
  error: string | null;
}

const WEBSOCKET_URL = import.meta.env.PROD
  ? 'wss://max-ev-sports.com/ws/live-odds'
  : 'ws://localhost:8000/ws/live-odds';

const RECONNECT_DELAY = 3000; // 3 seconds
const PING_INTERVAL = 25000; // 25 seconds (send ping to keep alive)

export const useWebSocket = (): UseWebSocketReturn => {
  const [games, setGames] = useState<LiveGame[]>([]);
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const pingIntervalRef = useRef<number | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const connect = useCallback(() => {
    try {
      console.log('🔌 Connecting to WebSocket...', WEBSOCKET_URL);
      const ws = new WebSocket(WEBSOCKET_URL);

      ws.onopen = () => {
        console.log('✅ WebSocket Connected');
        setConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;

        // Start ping interval to keep connection alive
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
        }
        pingIntervalRef.current = window.setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, PING_INTERVAL);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (message.type === 'games_update' && message.games) {
            setGames(message.games as LiveGame[]);
            setLastUpdate(new Date());
            console.log(`📊 Received ${message.games.length} games via WebSocket`);
          } else if (message.type === 'ping' || message.type === 'pong') {
            // Keep alive message, no action needed
            console.log('💓 Keep-alive:', message.type);
          }
        } catch (err) {
          console.error('❌ Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('❌ WebSocket Error:', event);
        setError('Connection error');
        setConnected(false);
      };

      ws.onclose = (event) => {
        console.log('🔌 WebSocket Disconnected', event.code, event.reason);
        setConnected(false);

        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }

        // Attempt reconnect with exponential backoff
        const delay = Math.min(RECONNECT_DELAY * Math.pow(1.5, reconnectAttemptsRef.current), 30000);
        reconnectAttemptsRef.current += 1;

        console.log(`🔄 Reconnecting in ${delay / 1000}s... (attempt ${reconnectAttemptsRef.current})`);

        reconnectTimeoutRef.current = window.setTimeout(() => {
          connect();
        }, delay);
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('❌ Failed to create WebSocket:', err);
      setError('Failed to connect');

      // Retry connection
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect();
      }, RECONNECT_DELAY);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    // Connect on mount
    connect();

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    games,
    connected,
    lastUpdate,
    error,
  };
};

export default useWebSocket;
