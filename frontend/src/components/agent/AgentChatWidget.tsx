import { useCallback } from 'react';
import { useAgentContext } from '../../contexts/AgentContext';
import { useAuth } from '../../contexts/AuthContext';
import { useAgentChat } from '../../hooks/useAgentChat';
import { ChatPanel } from './ChatPanel';

// Width of the always-visible blue divider strip
const DIVIDER_W = 22;

export function AgentChatWidget() {
  const { isOpen, openWidget, closeWidget, panelWidth, setPanelWidth } = useAgentContext();
  const { token, isAuthenticated, loading: authLoading } = useAuth();
  const chatState = useAgentChat(isOpen, token);
  const { mode, setMode } = chatState;

  // Anchor-based drag: startX + startWidth are captured once on mousedown.
  // Each mousemove computes new width relative to the original position,
  // avoiding the stale-closure bug that plagued the delta approach.
  const handleDragStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = panelWidth;

    const onMove = (ev: MouseEvent) => {
      // Dragging LEFT increases width; dragging RIGHT decreases it
      const newWidth = startWidth + (startX - ev.clientX);
      setPanelWidth(newWidth);
    };

    const onUp = () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }, [panelWidth, setPanelWidth]);

  const handleDividerMouseDown = useCallback((e: React.MouseEvent) => {
    if (isOpen) {
      handleDragStart(e);
    } else {
      openWidget();
    }
  }, [isOpen, handleDragStart, openWidget]);

  return (
    <>
      {/*
        Always-visible blue divider.
        - Panel closed → sits at right: 0, cursor pointer, click opens panel
        - Panel open   → sits at right: panelWidth, cursor col-resize, drag resizes
        Transitions in sync with the panel slide (both 300ms ease-in-out).
      */}
      <div
        className="fixed top-20 bottom-0 z-50 bg-gradient-to-b from-blue-800 via-blue-600 to-blue-800 hover:from-blue-600 hover:via-blue-400 hover:to-blue-600 flex flex-col items-center justify-center gap-3 transition-[right] duration-300 ease-in-out shadow-[-3px_0_12px_rgba(37,99,235,0.5)]"
        style={{
          width: DIVIDER_W,
          right: isOpen ? panelWidth : 0,
          cursor: isOpen ? 'col-resize' : 'pointer',
        }}
        onMouseDown={handleDividerMouseDown}
        title={isOpen ? 'Drag to resize' : 'Open MAX EV Analyst'}
        role="button"
        aria-label={isOpen ? 'Resize analyst panel' : 'Open analyst panel'}
      >
        {/* MAX AI label — rotated to read top-to-bottom in the vertical bar */}
        <div
          style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)', userSelect: 'none' }}
          className="flex flex-col items-center leading-none"
        >
          <span className="text-white font-black tracking-widest" style={{ fontSize: '0.6rem', letterSpacing: '0.18em' }}>MAX</span>
          <span className="text-blue-200 font-black tracking-widest" style={{ fontSize: '0.6rem', letterSpacing: '0.18em' }}>AI</span>
        </div>

        {/* Chevron — points left (open) / right (closed) */}
        <svg
          className={`w-3.5 h-3.5 text-blue-200 transition-transform duration-300 ${isOpen ? '' : 'rotate-180'}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
        </svg>
      </div>

      {/*
        Side panel.
        Always mounted so the CSS slide transition plays.
        translate-x-full when closed keeps it off-screen without unmounting.
      */}
      <div
        className={`fixed right-0 top-20 h-[calc(100vh-5rem)] z-40 bg-slate-900 shadow-2xl shadow-black/60 flex flex-col overflow-hidden transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full pointer-events-none'
        }`}
        style={{ width: panelWidth }}
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
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {authLoading ? (
          <div className="flex items-center justify-center flex-grow">
            <div className="w-5 h-5 rounded-full border-2 border-blue-400 border-t-transparent animate-spin" />
          </div>
        ) : isAuthenticated && token ? (
          <ChatPanel mode={mode} onModeChange={setMode} chatState={chatState} token={token} />
        ) : (
          <div className="flex flex-col items-center justify-center flex-grow gap-4 px-6 text-center">
            <div className="w-12 h-12 rounded-full bg-blue-900/50 flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
            </div>
            <div>
              <p className="text-white font-bold text-sm mb-1">Sign in to access the analyst</p>
              <p className="text-slate-400 text-xs">MAX EV Analyst is available to registered members.</p>
            </div>
            <a
              href="#/login"
              className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-500 text-white text-sm font-bold rounded-lg transition-colors text-center"
            >
              Sign In
            </a>
          </div>
        )}
      </div>
    </>
  );
}
