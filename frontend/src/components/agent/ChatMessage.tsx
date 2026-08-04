import { AgentMessage } from '../../hooks/useAgentChat';

interface ChatMessageProps {
  message: AgentMessage;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold text-white flex-shrink-0 mr-2 mt-0.5">
          EV
        </div>
      )}
      <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm leading-relaxed ${
        isUser
          ? 'bg-blue-600 text-white rounded-tr-sm'
          : 'bg-slate-700 text-slate-100 rounded-tl-sm'
      }`}>
        <p className="whitespace-pre-wrap">{message.content}</p>
        <span className={`text-xs mt-1 block ${isUser ? 'text-blue-200' : 'text-slate-500'}`}>
          {message.timestamp.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex justify-start mb-3">
      <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold text-white flex-shrink-0 mr-2 mt-0.5">
        EV
      </div>
      <div className="bg-slate-700 rounded-xl rounded-tl-sm px-3 py-3">
        <div className="flex gap-1">
          <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}
