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

interface Influencer {
  username: string;
  email: string;
  full_name: string;
  social_media_handle: string;
  platform: string;
  follower_count: number;
  referral_code: string;
  status: string;
  created_at: string;
  earnings: {
    total_referrals: number;
    active_subscribers: number;
    total_revenue: number;
    influencer_commission: number;
    pending_payout: number;
  };
}

export function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<'feedback' | 'chats' | 'influencers'>('feedback');
  const [feedback, setFeedback] = useState<FeedbackEntry[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [replyMessage, setReplyMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedFeedback, setSelectedFeedback] = useState<FeedbackEntry | null>(null);
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [adminResponse, setAdminResponse] = useState('');
  const [sendingResponse, setSendingResponse] = useState(false);
  const [influencers, setInfluencers] = useState<Influencer[]>([]);
  const [selectedInfluencer, setSelectedInfluencer] = useState<Influencer | null>(null);
  const [influencerModalOpen, setInfluencerModalOpen] = useState(false);

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
      } else if (activeTab === 'chats') {
        await loadConversations();
      } else if (activeTab === 'influencers') {
        await loadInfluencers();
      }
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const loadFeedback = async () => {
    try {
      const response = await fetch(getApiUrl(`feedback/all?token=${adminToken}`));
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
      const response = await fetch(getApiUrl(`chat/conversations?token=${adminToken}`));
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

  const loadInfluencers = async () => {
    try {
      const response = await fetch(getApiUrl('influencer/admin/all'), {
        headers: {
          'Authorization': `Bearer ${adminToken}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setInfluencers(data.influencers || []);
      }
    } catch (error) {
      console.error('Error loading influencers:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateInfluencerStatus = async (username: string, status: string) => {
    try {
      const response = await fetch(getApiUrl('influencer/admin/status'), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${adminToken}`,
        },
        body: JSON.stringify({ username, status }),
      });

      if (response.ok) {
        await loadInfluencers();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error updating influencer status:', error);
      return false;
    }
  };

  const loadConversation = async (username: string) => {
    try {
      const response = await fetch(getApiUrl(`chat/conversation/${username}?token=${adminToken}`));
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
      const response = await fetch(getApiUrl(`chat/admin/send?token=${adminToken}`), {
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
          <p className="text-slate-400">Monitor feedback, live chats, and manage influencers</p>
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
          <button
            onClick={() => setActiveTab('influencers')}
            className={`px-6 py-3 rounded-lg font-semibold transition-all ${
              activeTab === 'influencers'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Influencers {influencers.length > 0 && (
              <span className="ml-2 bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
                {influencers.length}
              </span>
            )}
          </button>
        </div>

        {/* Content */}
        {activeTab === 'influencers' ? (
          /* Influencers List */
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <h2 className="text-2xl font-bold text-white mb-6">Influencer Management</h2>
            {influencers.length === 0 ? (
              <p className="text-slate-400">No influencers registered yet</p>
            ) : (
              <div className="space-y-4">
                {influencers.map((influencer) => (
                  <div
                    key={influencer.username}
                    onClick={() => {
                      setSelectedInfluencer(influencer);
                      setInfluencerModalOpen(true);
                    }}
                    className="bg-slate-700 border border-slate-600 rounded-lg p-4 cursor-pointer hover:bg-slate-600 hover:border-blue-500 transition-all"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <span className="font-semibold text-white text-lg">{influencer.full_name}</span>
                        <span className="text-slate-400 text-sm ml-2">@{influencer.username}</span>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        influencer.status === 'active'
                          ? 'bg-green-900 text-green-300'
                          : influencer.status === 'paused'
                          ? 'bg-yellow-900 text-yellow-300'
                          : 'bg-red-900 text-red-300'
                      }`}>
                        {influencer.status.toUpperCase()}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                      <div>
                        <p className="text-slate-500 text-xs">Platform</p>
                        <p className="text-white font-semibold">{influencer.platform}</p>
                      </div>
                      <div>
                        <p className="text-slate-500 text-xs">Followers</p>
                        <p className="text-white font-semibold">{influencer.follower_count.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-slate-500 text-xs">Referral Code</p>
                        <p className="text-blue-400 font-mono font-semibold">{influencer.referral_code}</p>
                      </div>
                      <div>
                        <p className="text-slate-500 text-xs">Total Referrals</p>
                        <p className="text-white font-semibold">{influencer.earnings.total_referrals}</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4 pt-3 border-t border-slate-600">
                      <div>
                        <p className="text-slate-500 text-xs">Active Subs</p>
                        <p className="text-green-400 font-semibold">{influencer.earnings.active_subscribers}</p>
                      </div>
                      <div>
                        <p className="text-slate-500 text-xs">Commission</p>
                        <p className="text-green-400 font-semibold">${influencer.earnings.influencer_commission.toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-slate-500 text-xs">Pending Payout</p>
                        <p className="text-yellow-400 font-semibold">${influencer.earnings.pending_payout.toFixed(2)}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Influencer Detail Modal */}
            {influencerModalOpen && selectedInfluencer && (
              <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
                <div className="bg-slate-800 border border-slate-700 rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
                  {/* Header */}
                  <div className="p-6 border-b border-slate-700">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-2xl font-bold text-white mb-2">{selectedInfluencer.full_name}</h3>
                        <p className="text-slate-400">@{selectedInfluencer.username}</p>
                        <div className="flex gap-2 mt-3">
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            selectedInfluencer.status === 'active'
                              ? 'bg-green-900 text-green-300'
                              : selectedInfluencer.status === 'paused'
                              ? 'bg-yellow-900 text-yellow-300'
                              : 'bg-red-900 text-red-300'
                          }`}>
                            {selectedInfluencer.status.toUpperCase()}
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => setInfluencerModalOpen(false)}
                        className="text-slate-400 hover:text-white text-2xl"
                      >
                        ×
                      </button>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="p-6 space-y-6">
                    {/* Contact Info */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-slate-400 text-sm">Email:</label>
                        <p className="text-white">{selectedInfluencer.email}</p>
                      </div>
                      <div>
                        <label className="text-slate-400 text-sm">Social Media:</label>
                        <p className="text-white">{selectedInfluencer.social_media_handle}</p>
                      </div>
                      <div>
                        <label className="text-slate-400 text-sm">Platform:</label>
                        <p className="text-white">{selectedInfluencer.platform}</p>
                      </div>
                      <div>
                        <label className="text-slate-400 text-sm">Followers:</label>
                        <p className="text-white">{selectedInfluencer.follower_count.toLocaleString()}</p>
                      </div>
                    </div>

                    {/* Referral Code */}
                    <div>
                      <label className="text-slate-400 text-sm block mb-2">Referral Code:</label>
                      <p className="text-blue-400 font-mono text-xl font-bold bg-slate-900 p-3 rounded border border-slate-700">
                        {selectedInfluencer.referral_code}
                      </p>
                    </div>

                    {/* Earnings Stats */}
                    <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
                      <h4 className="text-white font-semibold mb-3">Performance Metrics</h4>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        <div>
                          <p className="text-slate-400 text-xs">Total Referrals</p>
                          <p className="text-white text-2xl font-bold">{selectedInfluencer.earnings.total_referrals}</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs">Active Subscribers</p>
                          <p className="text-green-400 text-2xl font-bold">{selectedInfluencer.earnings.active_subscribers}</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs">Total Revenue Generated</p>
                          <p className="text-blue-400 text-2xl font-bold">${selectedInfluencer.earnings.total_revenue.toFixed(2)}</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs">Commission Earned</p>
                          <p className="text-green-400 text-2xl font-bold">${selectedInfluencer.earnings.influencer_commission.toFixed(2)}</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs">Pending Payout</p>
                          <p className="text-yellow-400 text-2xl font-bold">${selectedInfluencer.earnings.pending_payout.toFixed(2)}</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs">Conversion Rate</p>
                          <p className="text-white text-2xl font-bold">
                            {selectedInfluencer.earnings.total_referrals > 0
                              ? ((selectedInfluencer.earnings.active_subscribers / selectedInfluencer.earnings.total_referrals) * 100).toFixed(1)
                              : 0}%
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Joined Date */}
                    <div>
                      <label className="text-slate-400 text-sm">Joined:</label>
                      <p className="text-white">{new Date(selectedInfluencer.created_at).toLocaleString()}</p>
                    </div>

                    {/* Status Management */}
                    <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
                      <h4 className="text-white font-semibold mb-3">Status Management</h4>
                      <div className="flex gap-3">
                        <button
                          onClick={async () => {
                            const success = await updateInfluencerStatus(selectedInfluencer.username, 'active');
                            if (success) {
                              alert('Status updated to Active');
                              setInfluencerModalOpen(false);
                            } else {
                              alert('Failed to update status');
                            }
                          }}
                          className={`flex-1 py-2 px-4 rounded font-semibold transition-all ${
                            selectedInfluencer.status === 'active'
                              ? 'bg-green-700 text-white cursor-not-allowed'
                              : 'bg-green-600 hover:bg-green-700 text-white'
                          }`}
                          disabled={selectedInfluencer.status === 'active'}
                        >
                          Set Active
                        </button>
                        <button
                          onClick={async () => {
                            const success = await updateInfluencerStatus(selectedInfluencer.username, 'paused');
                            if (success) {
                              alert('Status updated to Paused');
                              setInfluencerModalOpen(false);
                            } else {
                              alert('Failed to update status');
                            }
                          }}
                          className={`flex-1 py-2 px-4 rounded font-semibold transition-all ${
                            selectedInfluencer.status === 'paused'
                              ? 'bg-yellow-700 text-white cursor-not-allowed'
                              : 'bg-yellow-600 hover:bg-yellow-700 text-white'
                          }`}
                          disabled={selectedInfluencer.status === 'paused'}
                        >
                          Pause
                        </button>
                        <button
                          onClick={async () => {
                            if (confirm('Are you sure you want to suspend this influencer?')) {
                              const success = await updateInfluencerStatus(selectedInfluencer.username, 'suspended');
                              if (success) {
                                alert('Status updated to Suspended');
                                setInfluencerModalOpen(false);
                              } else {
                                alert('Failed to update status');
                              }
                            }
                          }}
                          className={`flex-1 py-2 px-4 rounded font-semibold transition-all ${
                            selectedInfluencer.status === 'suspended'
                              ? 'bg-red-700 text-white cursor-not-allowed'
                              : 'bg-red-600 hover:bg-red-700 text-white'
                          }`}
                          disabled={selectedInfluencer.status === 'suspended'}
                        >
                          Suspend
                        </button>
                      </div>
                      <p className="text-slate-400 text-xs mt-3">
                        Active: Can generate new referrals | Paused: Temporarily inactive | Suspended: Account disabled
                      </p>
                    </div>
                  </div>

                  {/* Footer */}
                  <div className="p-6 border-t border-slate-700">
                    <button
                      onClick={() => setInfluencerModalOpen(false)}
                      className="w-full px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded"
                    >
                      Close
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : activeTab === 'chats' ? (
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
                  <div
                    key={item.id}
                    onClick={() => {
                      setSelectedFeedback(item);
                      setFeedbackModalOpen(true);
                    }}
                    className="bg-slate-700 border border-slate-600 rounded-lg p-4 cursor-pointer hover:bg-slate-600 hover:border-blue-500 transition-all"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <span className="font-semibold text-white">{item.username}</span>
                        <span className="text-slate-400 text-sm ml-2">on {item.page}</span>
                      </div>
                      <div className="flex gap-2 items-center">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          item.status === 'resolved'
                            ? 'bg-green-900 text-green-300'
                            : item.status === 'in-progress'
                            ? 'bg-yellow-900 text-yellow-300'
                            : 'bg-slate-900 text-slate-300'
                        }`}>
                          {item.status}
                        </span>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          item.type === 'bug'
                            ? 'bg-red-900 text-red-300'
                            : item.type === 'feature'
                            ? 'bg-blue-900 text-blue-300'
                            : 'bg-purple-900 text-purple-300'
                        }`}>
                          {item.type}
                        </span>
                      </div>
                    </div>
                    <p className="text-slate-300 mb-2 line-clamp-2">{item.comment}</p>
                    <p className="text-slate-500 text-xs">
                      {new Date(item.timestamp).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {/* Feedback Detail Modal */}
            {feedbackModalOpen && selectedFeedback && (
              <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
                <div className="bg-slate-800 border border-slate-700 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                  {/* Header */}
                  <div className="p-6 border-b border-slate-700">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-2xl font-bold text-white mb-2">Feedback Details</h3>
                        <div className="flex gap-2 mb-2">
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            selectedFeedback.type === 'bug'
                              ? 'bg-red-900 text-red-300'
                              : selectedFeedback.type === 'feature'
                              ? 'bg-blue-900 text-blue-300'
                              : 'bg-purple-900 text-purple-300'
                          }`}>
                            {selectedFeedback.type}
                          </span>
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            selectedFeedback.status === 'resolved'
                              ? 'bg-green-900 text-green-300'
                              : selectedFeedback.status === 'in-progress'
                              ? 'bg-yellow-900 text-yellow-300'
                              : 'bg-slate-900 text-slate-300'
                          }`}>
                            {selectedFeedback.status}
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => setFeedbackModalOpen(false)}
                        className="text-slate-400 hover:text-white text-2xl"
                      >
                        ×
                      </button>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="p-6 space-y-4">
                    <div>
                      <label className="text-slate-400 text-sm">From:</label>
                      <p className="text-white font-semibold">{selectedFeedback.username}</p>
                    </div>

                    <div>
                      <label className="text-slate-400 text-sm">Page:</label>
                      <p className="text-white">{selectedFeedback.page}</p>
                    </div>

                    <div>
                      <label className="text-slate-400 text-sm">Submitted:</label>
                      <p className="text-white">{new Date(selectedFeedback.timestamp).toLocaleString()}</p>
                    </div>

                    <div>
                      <label className="text-slate-400 text-sm">Comment:</label>
                      <p className="text-white bg-slate-900 p-4 rounded border border-slate-700 whitespace-pre-wrap">
                        {selectedFeedback.comment}
                      </p>
                    </div>

                    {selectedFeedback.admin_notes && (
                      <div>
                        <label className="text-slate-400 text-sm">Admin Notes:</label>
                        <p className="text-slate-300 bg-slate-900 p-4 rounded border border-slate-700 whitespace-pre-wrap">
                          {selectedFeedback.admin_notes}
                        </p>
                      </div>
                    )}

                    <div>
                      <label className="text-slate-400 text-sm block mb-2">Feedback ID:</label>
                      <p className="text-slate-500 text-xs font-mono">{selectedFeedback.id}</p>
                    </div>
                  </div>

                  {/* Admin Response Section */}
                  <div className="p-6 border-t border-slate-700 bg-slate-900">
                    <label className="text-slate-300 font-semibold block mb-3">
                      Send Response to User
                    </label>
                    <textarea
                      value={adminResponse}
                      onChange={(e) => setAdminResponse(e.target.value)}
                      placeholder="Type your response to thank the user or ask for more details..."
                      rows={4}
                      className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 resize-none mb-3"
                    />
                    <div className="flex gap-3">
                      <button
                        onClick={async () => {
                          if (!adminResponse.trim()) return;
                          setSendingResponse(true);
                          try {
                            const response = await fetch(getApiUrl(`feedback/${selectedFeedback.id}/respond`), {
                              method: 'POST',
                              headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${adminToken}`,
                              },
                              body: JSON.stringify({
                                response: adminResponse,
                              }),
                            });

                            if (response.ok) {
                              alert('Response sent successfully!');
                              setAdminResponse('');
                              setFeedbackModalOpen(false);
                              await loadFeedback();
                            } else {
                              alert('Failed to send response');
                            }
                          } catch (error) {
                            console.error('Error sending response:', error);
                            alert('Failed to send response');
                          } finally {
                            setSendingResponse(false);
                          }
                        }}
                        disabled={!adminResponse.trim() || sendingResponse}
                        className={`flex-1 py-2 px-4 rounded font-semibold transition-all ${
                          !adminResponse.trim() || sendingResponse
                            ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
                            : 'bg-green-600 hover:bg-green-700 text-white'
                        }`}
                      >
                        {sendingResponse ? 'Sending...' : 'Send Response'}
                      </button>
                      <button
                        onClick={() => {
                          setAdminResponse('');
                          setFeedbackModalOpen(false);
                        }}
                        className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded"
                      >
                        Close
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
