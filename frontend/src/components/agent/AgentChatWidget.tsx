import { useEffect } from 'react';
import { useAgentContext } from '../../contexts/AgentContext';
import { useAgentChat } from '../../hooks/useAgentChat';
import { ChatPanel } from './ChatPanel';

export function AgentChatWidget() {
  const { isOpen, unreadCount, openWidget, closeWidget } = useAgentContext();
  const chatState = useAgentChat();
  const { mode, setMode, fetchPicks } = chatState;

  // Poll for new picks every 5 minutes when widget is closed
  useEffect(() => {
    const interval = setInterval(() => {
      if (!isOpen) {
        fetchPicks();
      }
    }, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [isOpen, fetchPicks]);

  return (
    <>
      {/* Panel */}
      {isOpen && (
        <div className="fixed bottom-20 right-6 z-50 w-80 h-[520px] bg-slate-900 border border-slate-700 rounded-xl shadow-2xl shadow-black/60 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-blue-900/80 to-slate-900 border-b border-slate-700">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
              <span className="font-bold text-white text-sm">MAX EV Analyst</span>
            </div>
            <button
              onClick={closeWidget}
              className="text-slate-400 hover:text-white transition-colors"
              title="Close"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Chat panel */}
          <ChatPanel
            mode={mode}
            onModeChange={setMode}
            chatState={chatState}
          />
        </div>
      )}

      {/* Floating trigger button */}
      <button
        onClick={isOpen ? closeWidget : openWidget}
        className="fixed bottom-6 right-36 z-50 w-12 h-12 rounded-full bg-gradient-to-br from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 shadow-lg shadow-blue-500/30 transition-all hover:scale-110 flex items-center justify-center"
        title="MAX EV Analyst"
      >
        {isOpen ? (
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        )}
        {/* Unread badge */}
        {!isOpen && unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center font-bold">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>
    </>
  );
}
