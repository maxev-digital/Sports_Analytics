import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface SubscriptionGuardProps {
  children: React.ReactNode;
}

export function SubscriptionGuard({ children }: SubscriptionGuardProps) {
  const { subscriptionTier, username, role, refreshSubscription } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    refreshSubscription();
  }, []);

  useEffect(() => {
    // Don't redirect if user is on subscription success page (they just paid!)
    if (location.pathname === '/subscription/success') {
      return;
    }

    // Admins bypass subscription checks
    if (role === 'admin') {
      console.log(`User ${username} is admin - bypassing subscription check`);
      return;
    }

    if (subscriptionTier === 'free' || subscriptionTier === 'trial') {
      console.log(`User ${username} has tier ${subscriptionTier} - redirecting to pricing`);
      navigate('/pricing', { replace: true });
    }
  }, [subscriptionTier, navigate, username, role, location.pathname]);

  // Allow access for admins OR paid users
  if (role === 'admin' || (subscriptionTier !== 'free' && subscriptionTier !== 'trial')) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
      <div className="text-white text-xl">Checking subscription...</div>
    </div>
  );
}
