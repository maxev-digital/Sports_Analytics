import { useState, useCallback, useEffect, useRef } from 'react';
import { getApiUrl } from '../config';
import { logger } from '../utils/logger';

export type AgentMode = 'picks' | 'chat';

export interface AgentMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface PickCard {
  id: number;
  sport: string;
  home_team: string;
  away_team: string;
  pick_side: string | null;
  pick_type: string | null;
  edge_pct: number;
  confidence_tier: string;
  market_odds: number;
  ml_confidence_pct: number;
  kelly_units: number;
  detector: string;
  narrative: string;
  total_line: number | null;
  game_time_cst: string | null;
}

const HISTORY_KEY = 'agent_chat_history';
const HISTORY_TTL_MS = 24 * 60 * 60 * 1000;

function loadHistory(): AgentMessage[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    if (!raw) return [];
    const { messages, savedAt } = JSON.parse(raw) as { messages: AgentMessage[]; savedAt: number };
    if (Date.now() - savedAt > HISTORY_TTL_MS) return [];
    return messages.map(m => ({ ...m, timestamp: new Date(m.timestamp) }));
  } catch {
    return [];
  }
}

function saveHistory(messages: AgentMessage[]) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify({ messages, savedAt: Date.now() }));
  } catch {
    // ignore storage errors
  }
}

export function useAgentChat() {
  const [mode, setMode] = useState<AgentMode>('picks');
  const [messages, setMessages] = useState<AgentMessage[]>(() => loadHistory());
  const [picks, setPicks] = useState<PickCard[]>([]);
  const [loadingChat, setLoadingChat] = useState(false);
  const [loadingPicks, setLoadingPicks] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const picksFetchedRef = useRef(false);

  useEffect(() => {
    saveHistory(messages);
  }, [messages]);

  const fetchPicks = useCallback(async (sport?: string) => {
    setLoadingPicks(true);
    setError(null);
    try {
      const resp = await fetch(getApiUrl('agent/picks'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sport: sport ?? null, limit: 5 }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json() as { picks: PickCard[]; count: number };
      setPicks(data.picks);
      picksFetchedRef.current = true;
    } catch (err) {
      logger.error('fetchPicks error:', err);
      setError('Could not load picks. Please try again.');
    } finally {
      setLoadingPicks(false);
    }
  }, []);

  const sendMessage = useCallback(async (text: string) => {
    const userMsg: AgentMessage = { role: 'user', content: text, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setLoadingChat(true);
    setError(null);

    // Streaming: add a placeholder assistant message and fill it token by token
    const assistantMsg: AgentMessage = { role: 'assistant', content: '', timestamp: new Date() };
    setMessages(prev => [...prev, assistantMsg]);

    try {
      const history = messages.slice(-8).map(m => ({ role: m.role, content: m.content }));
      const resp = await fetch(getApiUrl('agent/chat/stream'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history }),
      });

      if (!resp.ok || !resp.body) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        for (const line of chunk.split('\n')) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data: ')) continue;
          const payload = trimmed.slice(6);
          if (payload === '[DONE]') break;
          try {
            const parsed = JSON.parse(payload) as { text: string };
            accumulated += parsed.text;
            setMessages(prev => {
              const copy = [...prev];
              const last = copy[copy.length - 1];
              if (last?.role === 'assistant') {
                copy[copy.length - 1] = { ...last, content: accumulated };
              }
              return copy;
            });
          } catch {
            // ignore malformed SSE chunks
          }
        }
      }
    } catch (err) {
      logger.error('sendMessage error:', err);
      setError('Failed to get a response. Please try again.');
      setMessages(prev => prev.slice(0, -2)); // remove user + empty assistant
    } finally {
      setLoadingChat(false);
    }
  }, [messages]);

  const clearHistory = useCallback(() => {
    setMessages([]);
    localStorage.removeItem(HISTORY_KEY);
  }, []);

  return {
    mode, setMode,
    messages,
    picks,
    loadingChat,
    loadingPicks,
    error,
    fetchPicks,
    sendMessage,
    clearHistory,
    picksFetched: picksFetchedRef.current,
  };
}
