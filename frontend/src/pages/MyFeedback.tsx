import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';
import { useAuth } from '../contexts/AuthContext';

interface FeedbackItem {
  id: string;
  username: string;
  type: string;
  comment: string;
  page: string;
  timestamp: string;
  status: string;
  admin_notes: string;
  admin_response?: string;
  admin_response_date?: string;
  response_viewed?: boolean;
}

export function MyFeedback() {
  const { username, token } = useAuth();
  const [feedback, setFeedback] = useState<FeedbackItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFeedback, setSelectedFeedback] = useState<FeedbackItem | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    loadMyFeedback();
  }, []);

  const loadMyFeedback = async () => {
    try {
      const response = await fetch(getApiUrl(`feedback/my-feedback`), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

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

  const markAsViewed = async (feedbackId: string) => {
    try {
      await fetch(getApiUrl(`feedback/${feedbackId}/mark-viewed`), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      // Refresh feedback list
      await loadMyFeedback();
    } catch (error) {
      console.error('Error marking as viewed:', error);
    }
  };

  const openFeedback = async (item: FeedbackItem) => {
    setSelectedFeedback(item);
    setModalOpen(true);

    // Mark as viewed if it has an unviewed response
    if (item.admin_response && !item.response_viewed) {
      await markAsViewed(item.id);
    }
  };

  const unreadCount = feedback.filter(
    (f) => f.admin_response && !f.response_viewed
  ).length;

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-12 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="text-white text-xl">Loading your feedback...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">My Feedback</h1>
          <p className="text-slate-400">
            View your submitted feedback and admin responses
          </p>
          {unreadCount > 0 && (
            <div className="mt-4 bg-blue-900/30 border border-blue-700 rounded-lg p-4">
              <p className="text-blue-300">
                🔔 You have {unreadCount} new response{unreadCount > 1 ? 's' : ''} from the admin!
              </p>
            </div>
          )}
        </div>

        {/* Feedback List */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          {feedback.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-slate-400 text-lg mb-4">No feedback submitted yet</p>
              <p className="text-slate-500 text-sm">
                Use the feedback button to share bugs, feature requests, or comments
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {feedback.map((item) => (
                <div
                  key={item.id}
                  onClick={() => openFeedback(item)}
                  className={`relative bg-slate-700 border rounded-lg p-4 cursor-pointer hover:bg-slate-600 hover:border-blue-500 transition-all ${
                    item.admin_response && !item.response_viewed
                      ? 'border-blue-500 shadow-lg shadow-blue-500/30'
                      : 'border-slate-600'
                  }`}
                >
                  {/* New Response Badge */}
                  {item.admin_response && !item.response_viewed && (
                    <div className="absolute top-2 right-2 bg-blue-600 text-white text-xs font-bold px-3 py-1 rounded-full animate-pulse">
                      NEW RESPONSE
                    </div>
                  )}

                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <span className="text-slate-400 text-sm">
                        {new Date(item.timestamp).toLocaleDateString()} at{' '}
                        {new Date(item.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="flex gap-2 items-center">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          item.status === 'responded'
                            ? 'bg-green-900 text-green-300'
                            : 'bg-slate-900 text-slate-300'
                        }`}
                      >
                        {item.status === 'responded' ? 'Admin Responded' : 'Pending'}
                      </span>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          item.type === 'bug'
                            ? 'bg-red-900 text-red-300'
                            : item.type === 'feature'
                            ? 'bg-blue-900 text-blue-300'
                            : 'bg-purple-900 text-purple-300'
                        }`}
                      >
                        {item.type}
                      </span>
                    </div>
                  </div>

                  <p className="text-slate-300 mb-2 line-clamp-2">{item.comment}</p>

                  {item.admin_response && (
                    <div className="mt-3 bg-green-900/20 border border-green-700/50 rounded p-3">
                      <p className="text-green-400 text-sm font-semibold mb-1">
                        ✓ Admin Response:
                      </p>
                      <p className="text-slate-300 text-sm line-clamp-2">
                        {item.admin_response}
                      </p>
                    </div>
                  )}

                  <p className="text-slate-500 text-xs mt-2">
                    Submitted from: {item.page}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detail Modal */}
        {modalOpen && selectedFeedback && (
          <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
            <div className="bg-slate-800 border border-slate-700 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              {/* Header */}
              <div className="p-6 border-b border-slate-700">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-2xl font-bold text-white mb-2">Feedback Details</h3>
                    <div className="flex gap-2 mb-2">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          selectedFeedback.type === 'bug'
                            ? 'bg-red-900 text-red-300'
                            : selectedFeedback.type === 'feature'
                            ? 'bg-blue-900 text-blue-300'
                            : 'bg-purple-900 text-purple-300'
                        }`}
                      >
                        {selectedFeedback.type}
                      </span>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          selectedFeedback.status === 'responded'
                            ? 'bg-green-900 text-green-300'
                            : 'bg-slate-900 text-slate-300'
                        }`}
                      >
                        {selectedFeedback.status === 'responded' ? 'Admin Responded' : 'Pending'}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => setModalOpen(false)}
                    className="text-slate-400 hover:text-white text-2xl"
                  >
                    ×
                  </button>
                </div>
              </div>

              {/* Content */}
              <div className="p-6 space-y-4">
                <div>
                  <label className="text-slate-400 text-sm">Submitted:</label>
                  <p className="text-white">
                    {new Date(selectedFeedback.timestamp).toLocaleString()}
                  </p>
                </div>

                <div>
                  <label className="text-slate-400 text-sm">Page:</label>
                  <p className="text-white">{selectedFeedback.page}</p>
                </div>

                <div>
                  <label className="text-slate-400 text-sm">Your Feedback:</label>
                  <p className="text-white bg-slate-900 p-4 rounded border border-slate-700 whitespace-pre-wrap">
                    {selectedFeedback.comment}
                  </p>
                </div>

                {selectedFeedback.admin_response && (
                  <div>
                    <label className="text-green-400 text-sm font-semibold">
                      Admin Response:
                    </label>
                    <p className="text-white bg-green-900/20 border border-green-700 p-4 rounded whitespace-pre-wrap mt-2">
                      {selectedFeedback.admin_response}
                    </p>
                    <p className="text-slate-500 text-xs mt-2">
                      Responded on:{' '}
                      {selectedFeedback.admin_response_date &&
                        new Date(selectedFeedback.admin_response_date).toLocaleString()}
                    </p>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="p-6 border-t border-slate-700">
                <button
                  onClick={() => setModalOpen(false)}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
