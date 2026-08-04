import { useState, useRef, useEffect } from 'react';
import { AgentMode, useAgentChat } from '../../hooks/useAgentChat';
import { ChatMessage, TypingIndicator } from './ChatMessage';
import { ProactivePicks } from './ProactivePicks';

interface ChatPanelProps {
  mode: AgentMode;
  onModeChange: (mode: AgentMode) => void;
  chatState: ReturnType<typeof useAgentChat>;
}

const SUGGESTED_QUESTIONS = [
  "What's the best bet tonight?",
  "Any high-confidence OVER picks?",
  "Which sport has the most edge today?",
];

export function ChatPanel({ mode, onModeChange, chatState }: ChatPanelProps) {
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
        {(['picks', 'chat'] as AgentMode[]).map(m => (
          <button
            key={m}
            onClick={() => onModeChange(m)}
            className={`flex-1 py-2.5 text-sm font-semibold transition-colors capitalize ${
              mode === m
                ? 'text-blue-400 border-b-2 border-blue-400 bg-slate-800'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {m === 'picks' ? 'Top Picks' : 'Ask Analyst'}
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
        ) : (
          <div className="p-3">
            {messages.length === 0 && (
              <div className="py-6">
                <p className="text-center text-sm text-slate-400 mb-4">
                  Ask me anything about today's games or picks.
                </p>
                <div className="flex flex-col gap-2">
                  {SUGGESTED_QUESTIONS.map(q => (
                    <button
                      key={q}
                      onClick={() => sendMessage(q)}
                      className="text-left text-xs text-slate-300 bg-slate-700/50 hover:bg-slate-700 border border-slate-600/40 rounded-lg px-3 py-2 transition-colors"
                    >
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
              placeholder="Ask about tonight's games..."
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
