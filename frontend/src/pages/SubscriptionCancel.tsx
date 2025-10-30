import React from 'react';
import { useNavigate } from 'react-router-dom';

const SubscriptionCancel: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4">
      <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-orange-500 rounded-lg p-8 max-w-md w-full text-center">
        <div className="text-7xl mb-4">❌</div>

        <h1 className="text-3xl font-bold text-white mb-4">
          Checkout Cancelled
        </h1>

        <p className="text-slate-300 mb-6">
          Your subscription checkout was cancelled. No charges were made to your account.
        </p>

        <p className="text-slate-400 text-sm mb-8">
          If you experienced any issues during checkout or have questions about our pricing plans, please don't hesitate to contact our support team.
        </p>

        <div className="flex gap-3">
          <button
            onClick={() => navigate('/pricing')}
            className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-6 py-3 rounded-lg font-semibold transition-all"
          >
            View Pricing
          </button>

          <button
            onClick={() => navigate('/dashboard')}
            className="flex-1 bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-700 hover:to-slate-800 text-white px-6 py-3 rounded-lg font-semibold transition-all"
          >
            Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionCancel;
