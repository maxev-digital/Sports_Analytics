import { useState, useRef, useEffect } from 'react';
import { AgentMode, useAgentChat } from '../../hooks/useAgentChat';
import { ChatMessage, TypingIndicator } from './ChatMessage';
import { ProactivePicks } from './ProactivePicks';
import { BetTracker } from './BetTracker';

interface ChatPanelProps {
  mode: AgentMode;
  onModeChange: (mode: AgentMode) => void;
  chatState: ReturnType<typeof useAgentChat>;
  token: string | null;
}

const SUGGESTED_QUESTIONS = [
  "What should I bet tonight?",
  "Analyze my pending bets",
  "Break down tonight's MLB slate",
  "Any high-confidence picks right now?",
  "How am I doing this month?",
];

export function ChatPanel({ mode, onModeChange, chatState, token }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const { messages, picks, loadingChat, loadingPicks, error, sendMessage, fetchPicks, clearHistory, picksFetched } = chatState;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loadingChat]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || loadingChat) return;
    setInput('');
    sendMessage(text);
    if (mode !== 'chat') onModeChange('chat');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Mode Toggle */}
      <div className="flex border-b border-slate-700 bg-slate-800/50">
        {([
          { key: 'picks', label: 'Top Picks' },
          { key: 'chat',  label: 'Ask Analyst' },
          { key: 'bets',  label: 'My Bets' },
        ] as { key: AgentMode; label: string }[]).map(({ key, label }) => (
          <button
            key={key}
            onClick={() => onModeChange(key)}
            className={`flex-1 py-2.5 text-xs font-semibold transition-colors ${
              mode === key
                ? 'text-blue-400 border-b-2 border-blue-400 bg-slate-800'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {mode === 'picks' ? (
          <ProactivePicks
            picks={picks}
            loading={loadingPicks}
            error={error}
            onFetchPicks={fetchPicks}
            picksFetched={picksFetched}
          />
        ) : mode === 'bets' ? (
          <BetTracker token={token} />
        ) : (
          <div className="p-3">
            {messages.length === 0 && (
              <div className="py-4">
                <div className="mb-4 text-center">
                  <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-blue-600/20 mb-2">
                    <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  <p className="text-sm font-medium text-slate-300">MAX EV Handicapper</p>
                  <p className="text-xs text-slate-500 mt-0.5">Powered by 60 ML models + your bet history</p>
                </div>
                <div className="flex flex-col gap-1.5">
                  {SUGGESTED_QUESTIONS.map(q => (
                    <button
                      key={q}
                      onClick={() => sendMessage(q)}
                      className="text-left text-xs text-slate-300 bg-slate-700/50 hover:bg-slate-700 border border-slate-600/40 rounded-lg px-3 py-2 transition-colors flex items-center gap-2"
                    >
                      <svg className="w-3 h-3 text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((msg, i) => (
              <ChatMessage key={i} message={msg} />
            ))}
            {loadingChat && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Footer: input + clear */}
      {mode === 'chat' && (
        <div className="border-t border-slate-700 p-3 space-y-1.5">
          <div className="flex gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me to handicap a game, analyze your bets, or find tonight's best plays..."
              rows={2}
              disabled={loadingChat}
              className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 resize-none focus:outline-none focus:border-blue-500 disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loadingChat}
              className="px-3 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg transition-colors self-end"
              title="Send"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
          {messages.length > 0 && (
            <button
              onClick={clearHistory}
              className="text-xs text-slate-600 hover:text-slate-400 transition-colors"
            >
              Clear chat history
            </button>
          )}
        </div>
      )}
    </div>
  );
}
