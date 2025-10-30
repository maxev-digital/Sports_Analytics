import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface SubscriptionGuardProps {
  children: React.ReactNode;
}

export function SubscriptionGuard({ children }: SubscriptionGuardProps) {
  const { subscriptionTier, username, refreshSubscription } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    refreshSubscription();
  }, []);

  useEffect(() => {
    if (subscriptionTier === 'free' || subscriptionTier === 'trial') {
      console.log(`User ${username} has tier ${subscriptionTier} - redirecting to pricing`);
      navigate('/pricing', { replace: true });
    }
  }, [subscriptionTier, navigate, username]);

  if (subscriptionTier !== 'free' && subscriptionTier !== 'trial') {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
      <div className="text-white text-xl">Checking subscription...</div>
    </div>
  );
}
