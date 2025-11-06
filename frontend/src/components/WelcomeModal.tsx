import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface WelcomeModalProps {
  username: string;
}

export function WelcomeModal({ username }: WelcomeModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user has seen welcome modal
    const hasSeenWelcome = localStorage.getItem(`welcome_seen_${username}`);

    if (!hasSeenWelcome) {
      setIsOpen(true);
    }
  }, [username]);

  const handleClose = () => {
    localStorage.setItem(`welcome_seen_${username}`, 'true');
    setIsOpen(false);
  };

  const handleSetupBankroll = () => {
    localStorage.setItem(`welcome_seen_${username}`, 'true');
    setIsOpen(false);
    navigate('/analytics', { state: { openBankroll: true } });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/90 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border-4 border-blue-600 rounded-lg max-w-2xl w-full p-8 shadow-2xl">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="text-6xl mb-4">🎯</div>
          <h2 className="text-4xl font-bold text-white mb-2">Welcome to Max EV Sports!</h2>
          <p className="text-lg text-slate-300">Let's get you set up for success</p>
        </div>

        {/* Features List */}
        <div className="space-y-4 mb-8">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
              <span className="text-2xl">💰</span>
              Set Up Your Bankroll
            </h3>
            <p className="text-slate-400 text-sm">
              Configure your total bankroll and individual bookmaker balances for Kelly Criterion bet sizing.
            </p>
          </div>

          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
              <span className="text-2xl">📊</span>
              Track Live Strategies
            </h3>
            <p className="text-slate-400 text-sm">
              16+ live betting strategies including arbitrage, steam moves, and momentum detection.
            </p>
          </div>

          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
              <span className="text-2xl">📈</span>
              Monitor Your Performance
            </h3>
            <p className="text-slate-400 text-sm">
              Track all bets with automatic grading and detailed analytics to measure your edge.
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={handleSetupBankroll}
            className="flex-1 px-6 py-4 bg-green-600 hover:bg-green-700 text-white font-bold text-lg rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <span className="text-2xl">💰</span>
            Set Up Bankroll Now
          </button>

          <button
            onClick={handleClose}
            className="flex-1 px-6 py-4 bg-slate-700 hover:bg-slate-600 text-white font-semibold text-lg rounded-lg transition-colors"
          >
            I'll Do This Later
          </button>
        </div>

        {/* Quick Tip */}
        <div className="mt-6 bg-blue-900/30 border border-blue-700 rounded-lg p-4">
          <p className="text-blue-200 text-sm text-center">
            <strong>💡 Tip:</strong> Setting up your bankroll enables Kelly Criterion recommendations for optimal bet sizing!
          </p>
        </div>
      </div>
    </div>
  );
}
