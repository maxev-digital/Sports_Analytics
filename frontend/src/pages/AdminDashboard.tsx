import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';

interface FeedbackEntry {
  id: string;
  username: string;
  type: string;
  comment: string;
  page: string;
  timestamp: string;
  status: string;
  admin_notes: string;
}

interface Conversation {
  username: string;
  message_count: number;
  last_message: any;
  last_message_at: string;
  unread_count: number;
}

interface ChatMessage {
  id: string;
  sender: string;
  message: string;
  timestamp: string;
}

export function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<'feedback' | 'chats'>('chats');
  const [feedback, setFeedback] = useState<FeedbackEntry[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [replyMessage, setReplyMessage] = useState('');
  const [loading, setLoading] = useState(true);

  const adminToken = localStorage.getItem('auth_token');

  useEffect(() => {
    loadData();
    // Poll for updates every 5 seconds
    const interval = setInterval(() => {
      loadData();
    }, 5000);
    return () => clearInterval(interval);
  }, [activeTab]);

  const loadData = async () => {
    try {
      if (activeTab === 'feedback') {
        await loadFeedback();
      } else {
        await loadConversations();
      }
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const loadFeedback = async () => {
    try {
      const response = await fetch(`${getApiUrl()}/api/feedback/all?token=${adminToken}`);
      if (response.ok) {
        const data = await response.json();
        setFeedback(data.feedback || []);
      }
    } catch (error) {
      console.error('Error loading feedback:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadConversations = async () => {
    try {
      const response = await fetch(`${getApiUrl()}/api/chat/conversations?token=${adminToken}`);
      if (response.ok) {
        const data = await response.json();
        setConversations(data.conversations || []);
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadConversation = async (username: string) => {
    try {
      const response = await fetch(`${getApiUrl()}/api/chat/conversation/${username}?token=${adminToken}`);
      if (response.ok) {
        const data = await response.json();
        setChatMessages(data.messages || []);
        setSelectedConversation(username);
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  };

  const sendAdminReply = async () => {
    if (!replyMessage.trim() || !selectedConversation) return;

    try {
      const response = await fetch(`${getApiUrl()}/api/chat/admin/send?token=${adminToken}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: selectedConversation,
          message: replyMessage,
        }),
      });

      if (response.ok) {
        setReplyMessage('');
        await loadConversation(selectedConversation);
        await loadConversations();
      }
    } catch (error) {
      console.error('Error sending reply:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Admin Dashboard</h1>
          <p className="text-slate-400">Monitor feedback and live chats</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('chats')}
            className={`px-6 py-3 rounded-lg font-semibold transition-all ${
              activeTab === 'chats'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Live Chats {conversations.filter(c => c.unread_count > 0).length > 0 && (
              <span className="ml-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                {conversations.filter(c => c.unread_count > 0).length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('feedback')}
            className={`px-6 py-3 rounded-lg font-semibold transition-all ${
              activeTab === 'feedback'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Feedback
          </button>
        </div>

        {/* Content */}
        {activeTab === 'chats' ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Conversations List */}
            <div className="lg:col-span-1 bg-slate-800 border border-slate-700 rounded-lg p-4">
              <h2 className="text-xl font-bold text-white mb-4">Conversations</h2>
              <div className="space-y-2">
                {conversations.length === 0 ? (
                  <p className="text-slate-400 text-sm">No conversations yet</p>
                ) : (
                  conversations.map((conv) => (
                    <button
                      key={conv.username}
                      onClick={() => loadConversation(conv.username)}
                      className={`w-full text-left p-3 rounded-lg transition-all ${
                        selectedConversation === conv.username
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-semibold">{conv.username}</p>
                          <p className="text-xs opacity-75">{conv.message_count} messages</p>
                        </div>
                        {conv.unread_count > 0 && (
                          <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                            {conv.unread_count}
                          </span>
                        )}
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>

            {/* Chat Window */}
            <div className="lg:col-span-2 bg-slate-800 border border-slate-700 rounded-lg flex flex-col" style={{ height: '600px' }}>
              {selectedConversation ? (
                <>
                  {/* Header */}
                  <div className="p-4 border-b border-slate-700">
                    <h2 className="text-xl font-bold text-white">Chat with {selectedConversation}</h2>
                  </div>

                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-3">
                    {chatMessages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex ${msg.sender === 'admin' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[80%] rounded-lg px-4 py-2 ${
                            msg.sender === 'admin'
                              ? 'bg-green-600 text-white'
                              : 'bg-slate-700 text-slate-100'
                          }`}
                        >
                          <p className="text-sm">{msg.message}</p>
                          <p className="text-xs opacity-75 mt-1">
                            {new Date(msg.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Reply Input */}
                  <div className="p-4 border-t border-slate-700">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={replyMessage}
                        onChange={(e) => setReplyMessage(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && sendAdminReply()}
                        placeholder="Type your reply..."
                        className="flex-1 bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
                      />
                      <button
                        onClick={sendAdminReply}
                        disabled={!replyMessage.trim()}
                        className={`px-6 py-2 rounded font-semibold transition-all ${
                          replyMessage.trim()
                            ? 'bg-green-600 hover:bg-green-700 text-white'
                            : 'bg-slate-600 text-slate-400 cursor-not-allowed'
                        }`}
                      >
                        Send
                      </button>
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex items-center justify-center h-full text-slate-400">
                  Select a conversation to view messages
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Feedback List */
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <h2 className="text-2xl font-bold text-white mb-6">User Feedback</h2>
            {feedback.length === 0 ? (
              <p className="text-slate-400">No feedback yet</p>
            ) : (
              <div className="space-y-4">
                {feedback.map((item) => (
                  <div key={item.id} className="bg-slate-700 border border-slate-600 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <span className="font-semibold text-white">{item.username}</span>
                        <span className="text-slate-400 text-sm ml-2">on {item.page}</span>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        item.type === 'bug'
                          ? 'bg-red-900 text-red-300'
                          : item.type === 'feature'
                          ? 'bg-blue-900 text-blue-300'
                          : 'bg-green-900 text-green-300'
                      }`}>
                        {item.type}
                      </span>
                    </div>
                    <p className="text-slate-300 mb-2">{item.comment}</p>
                    <p className="text-slate-500 text-xs">
                      {new Date(item.timestamp).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
