import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

interface AgentContextValue {
  isOpen: boolean;
  unreadCount: number;
  openWidget: () => void;
  closeWidget: () => void;
  clearUnread: () => void;
  incrementUnread: (n?: number) => void;
}

const AgentContext = createContext<AgentContextValue | null>(null);

export function AgentProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

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
    <AgentContext.Provider value={{ isOpen, unreadCount, openWidget, closeWidget, clearUnread, incrementUnread }}>
      {children}
    </AgentContext.Provider>
  );
}

export function useAgentContext(): AgentContextValue {
  const ctx = useContext(AgentContext);
  if (!ctx) throw new Error('useAgentContext must be used inside AgentProvider');
  return ctx;
}
