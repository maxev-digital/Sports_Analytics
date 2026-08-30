import { useState, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getApiUrl } from '../config';
import { logger } from '../utils/logger';

export type AgentMode = 'picks' | 'chat' | 'bets';

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
const PICK_POLL_INTERVAL_MS = 5 * 60 * 1000;

function loadHistory(): AgentMessage[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (
      typeof parsed !== 'object' || parsed === null ||
      !('messages' in parsed) || !('savedAt' in parsed)
    ) return [];
    const { messages, savedAt } = parsed as { messages: AgentMessage[]; savedAt: number };
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

function buildHeaders(token: string | null): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

export function useAgentChat(isOpen: boolean = true, token: string | null = null) {
  const [mode, setMode] = useState<AgentMode>('picks');
  const [messages, setMessages] = useState<AgentMessage[]>(() => loadHistory());
  const [loadingChat, setLoadingChat] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);

  // React Query for picks — polls in background when panel is collapsed
  const {
    data: picks = [],
    isFetching: loadingPicks,
    isFetched: picksFetched,
    refetch: refetchPicks,
    error: picksQueryError,
  } = useQuery({
    queryKey: ['agent-picks', token] as const,
    queryFn: async () => {
      const resp = await fetch(getApiUrl('v1/agent/picks'), {
        method: 'POST',
        headers: buildHeaders(token),
        body: JSON.stringify({ sport: null, limit: 5 }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json() as { picks: PickCard[]; count: number };
      return data.picks;
    },
    enabled: !!token,
    staleTime: PICK_POLL_INTERVAL_MS,
    refetchInterval: isOpen ? false : PICK_POLL_INTERVAL_MS,
  });

  const fetchPicks = useCallback(() => {
    refetchPicks().catch(err => logger.error('fetchPicks error:', err));
  }, [refetchPicks]);

  const sendMessage = useCallback(async (text: string) => {
    const userMsg: AgentMessage = { role: 'user', content: text, timestamp: new Date() };
    const assistantMsg: AgentMessage = { role: 'assistant', content: '', timestamp: new Date() };

    setMessages(prev => [...prev, userMsg, assistantMsg]);
    setLoadingChat(true);
    setChatError(null);

    let accumulated = '';
    let succeeded = false;

    try {
      const history = messages.slice(-8).map(m => ({ role: m.role, content: m.content }));
      const resp = await fetch(getApiUrl('v1/agent/chat/stream'), {
        method: 'POST',
        headers: buildHeaders(token),
        body: JSON.stringify({ message: text, history }),
      });

      if (!resp.ok || !resp.body) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();

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
      succeeded = true;
    } catch (err) {
      logger.error('sendMessage error:', err);
      setChatError('Failed to get a response. Please try again.');
      setMessages(prev => prev.slice(0, -2)); // remove user + empty assistant
    } finally {
      setLoadingChat(false);
      if (succeeded) {
        // Persist the complete exchange — no useEffect needed
        saveHistory([
          ...messages,
          userMsg,
          { ...assistantMsg, content: accumulated },
        ]);
      }
    }
  }, [messages, token]);

  const clearHistory = useCallback(() => {
    setMessages([]);
    localStorage.removeItem(HISTORY_KEY);
  }, []);

  // Sync mode to picks tab when panel opens and picks are already loaded
  useEffect(() => {
    if (isOpen && picksFetched && picks.length > 0 && messages.length === 0) {
      setMode('picks');
    }
  }, [isOpen]);

  const error = chatError ?? (picksQueryError ? 'Could not load picks. Please try again.' : null);

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
    picksFetched,
  };
}
