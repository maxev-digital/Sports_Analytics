/**
 * TierGate — Restricts inline content based on subscription tier.
 *
 * Tiers: free | member | pro | admin
 * One paid plan: Pro ($99/year). Member = free signup.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getUserTier, canAccessRoute, AccessTier } from '../lib/accessMap';
import { logger } from '../utils/logger';

// Feature → minimum tier required
const FEATURE_ACCESS: Record<string, AccessTier> = {
  // Free
  odds_display:         'free',
  game_info:            'free',
  live_games:           'free',
  performance_charts:   'free',

  // Member
  bet_tracker:          'member',
  alerts_page:          'member',

  // Pro
  model_predictions:    'pro',
  best_plays:           'pro',
  edge_scanner:         'pro',
  predictions:          'pro',
  player_props:         'pro',
  props_page:           'pro',
  advanced_analytics:   'pro',
  arbitrage:            'pro',
  steam_moves:          'pro',
  max_ev_edges:         'pro',
  props_ml_edges:       'pro',
  model_performance:    'pro',
  predictions_database: 'pro',
  dfs_crusher:          'pro',
  browser_extension:    'pro',
  desktop_client:       'pro',
  api_access:           'pro',
  custom_models:        'pro',
};

export function hasFeatureAccess(subscriptionTier: string, feature: string): boolean {
  const required = FEATURE_ACCESS[feature];
  if (!required) return true;
  const userTier = getUserTier(true, subscriptionTier, null);
  return canAccessRoute(userTier, required);
}

export function getMinimumTier(feature: string): AccessTier {
  return FEATURE_ACCESS[feature] ?? 'free';
}

interface TierGateProps {
  feature: keyof typeof FEATURE_ACCESS;
  children: React.ReactNode;
  upgradeMessage?: string;
  showBlurredPreview?: boolean;
  fallback?: React.ReactNode;
  inline?: boolean;
}

export function TierGate({
  feature,
  children,
  upgradeMessage,
  showBlurredPreview = true,
  fallback,
  inline = false,
}: TierGateProps) {
  const { isAuthenticated, subscriptionTier, role } = useAuth();
  const navigate = useNavigate();

  if (role === 'admin') return <>{children}</>;

  const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  logger.info('TierGate:', { feature, isDev, subscriptionTier, isAuthenticated });
  if (isDev) return <>{children}</>;

  const required = FEATURE_ACCESS[feature];
  const userTier = getUserTier(isAuthenticated, subscriptionTier, role);
  const hasAccess = !required || canAccessRoute(userTier, required);

  if (hasAccess) return <>{children}</>;
  if (fallback) return <>{fallback}</>;

  const minTier = getMinimumTier(feature);
  const label = minTier === 'member' ? 'Free Account' : 'Pro ($99/yr)';
  const defaultMessage = upgradeMessage || `Requires ${label}`;

  if (inline) {
    return (
      <span
        className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-700/50 rounded text-slate-400 text-sm cursor-pointer hover:bg-slate-600/50 transition-colors"
        onClick={() => navigate('/pricing')}
        title="Click to upgrade"
      >
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
        <span className="blur-sm select-none">***</span>
      </span>
    );
  }

  if (showBlurredPreview) {
    return (
      <div className="relative">
        <div className="blur-md pointer-events-none select-none opacity-50">{children}</div>
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm rounded-lg">
          <div className="text-center p-6 max-w-sm">
            <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">
              {minTier === 'member' ? 'Free Account Required' : 'Pro Feature'}
            </h3>
            <p className="text-slate-300 text-sm mb-4">{defaultMessage}</p>
            <button
              onClick={() => navigate(minTier === 'member' ? '/signup' : '/pricing')}
              className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-medium rounded-lg transition-all shadow-lg hover:shadow-xl"
            >
              {minTier === 'member' ? 'Sign Up Free' : isAuthenticated ? 'Upgrade to Pro' : 'View Plans'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-slate-800/50 rounded-lg border border-slate-700 text-center">
      <p className="text-slate-400 text-sm mb-3">{defaultMessage}</p>
      <button
        onClick={() => navigate('/pricing')}
        className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded transition-colors"
      >
        Upgrade
      </button>
    </div>
  );
}

export function useFeatureAccess(feature: keyof typeof FEATURE_ACCESS): boolean {
  const { isAuthenticated, subscriptionTier, role } = useAuth();
  if (role === 'admin') return true;
  const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  if (isDev) return true;
  const required = FEATURE_ACCESS[feature];
  if (!required) return true;
  const userTier = getUserTier(isAuthenticated, subscriptionTier, role);
  return canAccessRoute(userTier, required);
}

export function withTierGate<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  feature: keyof typeof FEATURE_ACCESS,
  upgradeMessage?: string,
) {
  return function TierGatedComponent(props: P) {
    return (
      <TierGate feature={feature} upgradeMessage={upgradeMessage}>
        <WrappedComponent {...props} />
      </TierGate>
    );
  };
}

export default TierGate;
