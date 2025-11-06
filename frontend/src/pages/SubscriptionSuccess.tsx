import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const SubscriptionSuccess: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const [countdown, setCountdown] = useState(5);
  const { refreshSubscription, username } = useAuth();
  const [verifying, setVerifying] = useState(true);

  useEffect(() => {
    const verifyAndActivate = async () => {
      if (!sessionId || !username) {
        console.error('Missing session ID or username');
        setVerifying(false);
        return;
      }

      try {
        // Call backend to verify checkout and update subscription
        const response = await fetch('/api/subscription/verify-checkout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            user_id: username
          })
        });

        if (response.ok) {
          const data = await response.json();
          console.log('Subscription verified:', data);
        }
      } catch (error) {
        console.error('Error verifying checkout:', error);
      }

      // Retry subscription refresh up to 5 times to ensure it's updated
      let retries = 5;
      let subscriptionUpdated = false;

      while (retries > 0 && !subscriptionUpdated) {
        await refreshSubscription();

        // Wait 1 second between retries
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Check if subscription tier has been updated (not 'free' or 'trial')
        const currentTier = localStorage.getItem('subscription_tier');
        if (currentTier && currentTier !== 'free' && currentTier !== 'trial') {
          subscriptionUpdated = true;
          console.log('✅ Subscription successfully updated to:', currentTier);

          // Track successful purchase for X Ads conversion
          if (typeof (window as any).twq !== 'undefined') {
            // Determine purchase value based on tier
            const tierPrices: Record<string, number> = {
              'beta': 9.99,
              'starter': 29,
              'semipro': 49,
              'professional': 75,
              'elite': 129,
              'elitepro': 229
            };
            const purchaseValue = tierPrices[currentTier] || 0;

            (window as any).twq('event', 'tw-p3o73-oebxl', {
              value: purchaseValue.toString(),
              currency: 'USD',
              num_items: '1',
              content_name: currentTier
            });
            console.log('✅ X Ads Purchase event tracked:', purchaseValue, currentTier);
          }
        } else {
          retries--;
          console.log(`⏳ Waiting for subscription update... ${retries} retries left`);
        }
      }

      setVerifying(false);

      // Countdown redirect to dashboard
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            navigate('/dashboard');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(timer);
    };

    verifyAndActivate();
  }, [navigate, refreshSubscription, sessionId, username]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4">
      <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-green-500 rounded-lg p-8 max-w-md w-full text-center">
        <div className="text-7xl mb-4">✅</div>

        <h1 className="text-3xl font-bold text-white mb-4">
          Payment Successful!
        </h1>

        {verifying ? (
          <p className="text-slate-300 mb-6">
            Activating your subscription... Please wait.
          </p>
        ) : (
          <p className="text-slate-300 mb-6">
            Thank you for subscribing to MAX-EV Sports! Your account has been upgraded and you now have access to all premium features.
          </p>
        )}

        {sessionId && (
          <div className="bg-slate-800 border border-slate-700 rounded p-3 mb-6">
            <p className="text-xs text-slate-400">Session ID:</p>
            <p className="text-xs text-slate-300 font-mono break-all">{sessionId}</p>
          </div>
        )}

        <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4 mb-6">
          <p className="text-blue-300 text-sm">
            Redirecting to dashboard in <span className="font-bold text-white">{countdown}</span> seconds...
          </p>
        </div>

        <button
          onClick={() => navigate('/dashboard')}
          className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-6 py-3 rounded-lg font-semibold transition-all"
        >
          Go to Dashboard Now
        </button>
      </div>
    </div>
  );
};

export default SubscriptionSuccess;
