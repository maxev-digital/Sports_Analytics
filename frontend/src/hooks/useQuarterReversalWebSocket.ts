/**
 * WebSocket Hook for Quarter Reversal Alerts
 * Connects to backend WebSocket and provides real-time quarter reversal opportunities
 */

import { useEffect, useState, useRef, useCallback } from 'react';

interface BetRecommendation {
  rank: number;
  label: string;
  odds: string;
  decimal_odds: number;
  probability: number;
  expected_value: number;
  bet_type: string;
  variance: number;
  score: number;
  kelly_size?: number;
  kelly_pct?: number;
  full_kelly_pct?: number;
  context?: string;
}

interface QuarterReversalOpportunity {
  game_id: string;
  matchup: string;
  strategy: 'Q1-Q2_to_Q3' | 'Q2-Q3_to_Q4' | 'Q3-Q4_to_OT' | 'COMBO' | 'HEDGE';
  hot_team: string;
  reversal_team: string;
  quarter: string;
  trigger: string;
  reversal_prob: string;
  expected_roi: string;
  alert_level: 'HIGH' | 'MEDIUM' | 'CRITICAL';
  reasoning: string;
  recommendations: BetRecommendation[];
  total_options: number;
  timestamp: string;
}

interface WebSocketMessage {
  type: string;
  timestamp: string;
  count?: number;
  opportunities?: QuarterReversalOpportunity[];
}

interface UseQuarterReversalWebSocketReturn {
  opportunities: QuarterReversalOpportunity[];
  connected: boolean;
  lastUpdate: Date | null;
  error: string | null;
}

const RECONNECT_DELAY = 3000; // 3 seconds
const PING_INTERVAL = 25000; // 25 seconds

export const useQuarterReversalWebSocket = (userId: string = 'default'): UseQuarterReversalWebSocketReturn => {
  const [opportunities, setOpportunities] = useState<QuarterReversalOpportunity[]>([]);
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const pingIntervalRef = useRef<number | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const connect = useCallback(() => {
    // Build WebSocket URL with user_id query parameter
    const baseUrl = import.meta.env.PROD
      ? 'wss://max-ev-sports.com/ws/live-odds'
      : 'ws://localhost:8000/ws/live-odds';
    const websocketUrl = `${baseUrl}?user_id=${userId}`;

    try {
      console.log('🔌 Connecting to Quarter Reversal WebSocket...', websocketUrl);
      const ws = new WebSocket(websocketUrl);

      ws.onopen = () => {
        console.log('✅ Quarter Reversal WebSocket Connected');
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

          // Handle quarter reversal updates
          if (message.type === 'quarter_reversal_update' && message.opportunities) {
            console.log(`🔄 Received ${message.opportunities.length} quarter reversal opportunities`);
            setOpportunities(message.opportunities);
            setLastUpdate(new Date());
          } else if (message.type === 'quarter_reversal_batch' && message.opportunities) {
            console.log(`📦 Received batch of ${message.opportunities.length} quarter reversal opportunities`);
            setOpportunities(message.opportunities);
            setLastUpdate(new Date());
          } else if (message.type === 'ping' || message.type === 'pong') {
            // Keep alive message, no action needed
            console.log('💓 Quarter Reversal Keep-alive:', message.type);
          }
        } catch (err) {
          console.error('❌ Error parsing Quarter Reversal WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('❌ Quarter Reversal WebSocket Error:', event);
        setError('Connection error');
        setConnected(false);
      };

      ws.onclose = (event) => {
        console.log('🔌 Quarter Reversal WebSocket Disconnected', event.code, event.reason);
        setConnected(false);

        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }

        // Attempt reconnect with exponential backoff
        const delay = Math.min(RECONNECT_DELAY * Math.pow(1.5, reconnectAttemptsRef.current), 30000);
        reconnectAttemptsRef.current += 1;

        console.log(`🔄 Reconnecting Quarter Reversal WebSocket in ${delay / 1000}s... (attempt ${reconnectAttemptsRef.current})`);

        reconnectTimeoutRef.current = window.setTimeout(() => {
          connect();
        }, delay);
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('❌ Failed to create Quarter Reversal WebSocket:', err);
      setError('Failed to connect');

      // Retry connection
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect();
      }, RECONNECT_DELAY);
    }
  }, [userId]);

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
  }, [connect, disconnect, userId]);

  return {
    opportunities,
    connected,
    lastUpdate,
    error,
  };
};

export default useQuarterReversalWebSocket;
