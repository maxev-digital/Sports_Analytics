import { useAgentContext } from '../../contexts/AgentContext';
import { useAuth } from '../../contexts/AuthContext';
import { useAgentChat } from '../../hooks/useAgentChat';
import { ChatPanel } from './ChatPanel';

export function AgentChatWidget() {
  const { isOpen, openWidget, closeWidget } = useAgentContext();
  const { token } = useAuth();
  const chatState = useAgentChat(isOpen, token);
  const { mode, setMode } = chatState;

  return (
    <>
      {/*
        Side panel — always mounted so the CSS slide transition plays.
        Positioned below the sticky nav (top-20 = 80px = nav h-20).
        translate-x-full when closed so it's off-screen but still in the DOM.
      */}
      <div
        className={`fixed right-0 top-20 h-[calc(100vh-5rem)] w-80 z-40 bg-slate-900 border-l border-slate-700 shadow-2xl shadow-black/60 flex flex-col overflow-hidden transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full pointer-events-none'
        }`}
      >
        {/* Panel header */}
        <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-blue-900/80 to-slate-900 border-b border-slate-700 flex-shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
            <span className="font-bold text-white text-sm">MAX EV Analyst</span>
          </div>
          <button
            onClick={closeWidget}
            className="text-slate-400 hover:text-white transition-colors p-0.5"
            title="Collapse panel"
          >
            {/* Chevron-right — indicates collapsing toward the right */}
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        <ChatPanel mode={mode} onModeChange={setMode} chatState={chatState} />
      </div>

      {/*
        Vertical tab trigger — visible when panel is collapsed.
        Fades out and slides right as the panel opens.
      */}
      <button
        onClick={openWidget}
        className={`fixed right-0 top-1/2 -translate-y-1/2 z-50 flex flex-col items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-2 py-5 rounded-l-xl shadow-lg shadow-blue-500/30 transition-all duration-300 ${
          isOpen ? 'opacity-0 pointer-events-none' : 'opacity-100'
        }`}
        title="Open MAX EV Analyst"
      >
        {/* Brain / analyst icon */}
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
          />
        </svg>
        {/* Chevron-left indicating panel opens to the left */}
        <svg className="w-3 h-3 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
      </button>
    </>
  );
}
