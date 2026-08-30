import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

interface AgentContextValue {
  isOpen: boolean;
  unreadCount: number;
  panelWidth: number;
  openWidget: () => void;
  closeWidget: () => void;
  clearUnread: () => void;
  incrementUnread: (n?: number) => void;
  setPanelWidth: (w: number) => void;
}

const AgentContext = createContext<AgentContextValue | null>(null);

const PANEL_DEFAULT_WIDTH = 320;
const PANEL_MIN_WIDTH = 280;
const PANEL_MAX_WIDTH = 700;

export function AgentProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [panelWidth, setPanelWidthState] = useState(PANEL_DEFAULT_WIDTH);

  const setPanelWidth = useCallback((w: number) => {
    setPanelWidthState(Math.min(PANEL_MAX_WIDTH, Math.max(PANEL_MIN_WIDTH, w)));
  }, []);

  const openWidget = useCallback(() => {
    setIsOpen(true);
    setUnreadCount(0);
  }, []);

  const closeWidget = useCallback(() => setIsOpen(false), []);
  const clearUnread = useCallback(() => setUnreadCount(0), []);
  const incrementUnread = useCallback((n = 1) => {
    setUnreadCount(prev => prev + n);
  }, []);

  return (
    <AgentContext.Provider value={{ isOpen, unreadCount, panelWidth, openWidget, closeWidget, clearUnread, incrementUnread, setPanelWidth }}>
      {children}
    </AgentContext.Provider>
  );
}

export function useAgentContext(): AgentContextValue {
  const ctx = useContext(AgentContext);
  if (!ctx) throw new Error('useAgentContext must be used inside AgentProvider');
  return ctx;
}
