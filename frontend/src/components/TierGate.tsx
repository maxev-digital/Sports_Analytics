/**
 * TierGate Component
 *
 * Restricts content based on user's subscription tier.
 * Shows blurred content with upgrade prompt for non-qualifying users.
 *
 * Usage:
 * <TierGate feature="predictions">
 *   <PredictionContent />
 * </TierGate>
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

// Feature access mapping - defines which tiers can access each feature
// TIER STRUCTURE:
// - trial/free_trial: 14-day free trial (card required)
// - starter: Entry level paid tier - basic features
// - semipro: Gets model predictions access
// - professional: Gets player props page access
// - elite/elitepro: Everything including extension and desktop client

const FEATURE_ACCESS: Record<string, string[]> = {
  // Basic features - Available to ALL tiers (including trial)
  odds_display: ['trial', 'free_trial', 'starter', 'semipro', 'professional', 'elite', 'elitepro', 'will_the_thrill'],
  game_info: ['trial', 'free_trial', 'starter', 'semipro', 'professional', 'elite', 'elitepro', 'will_the_thrill'],
  bet_tracker: ['trial', 'free_trial', 'starter', 'semipro', 'professional', 'elite', 'elitepro', 'will_the_thrill'],
  performance_charts: ['trial', 'free_trial', 'starter', 'semipro', 'professional', 'elite', 'elitepro', 'will_the_thrill'],
  live_games: ['trial', 'free_trial', 'starter', 'semipro', 'professional', 'elite', 'elitepro', 'will_the_thrill'],

  // Model Predictions - Semi-Pro and above
  model_predictions: ['semipro', 'professional', 'elite', 'elitepro', 'will_the_thrill'],
  best_plays: ['semipro', 'professional', 'elite', 'elitepro', 'will_the_thrill'],
  edge_scanner: ['semipro', 'professional', 'elite', 'elitepro', 'will_the_thrill'],
  predictions: ['semipro', 'professional', 'elite', 'elitepro', 'will_the_thrill'],

  // Player Props - Professional and above
  player_props: ['professional', 'elite', 'elitepro', 'will_the_thrill'],
  props_page: ['professional', 'elite', 'elitepro', 'will_the_thrill'],

  // Advanced Analytics - Professional and above
  advanced_analytics: ['professional', 'elite', 'elitepro', 'will_the_thrill'],
  arbitrage: ['professional', 'elite', 'elitepro', 'will_the_thrill'],
  steam_moves: ['professional', 'elite', 'elitepro', 'will_the_thrill'],

  // Elite features - Elite and Elite Pro only
  max_ev_edges: ['semipro', 'professional', 'elite', 'elitepro', 'will_the_thrill'],
  alerts_page: ['semipro', 'professional', 'elite', 'elitepro', 'will_the_thrill'],
  props_ml_edges: ['professional', 'elite', 'elitepro', 'will_the_thrill'],
  model_performance: ['semipro', 'professional', 'elite', 'elitepro', 'will_the_thrill'],
  predictions_database: ['semipro', 'professional', 'elite', 'elitepro', 'will_the_thrill'],
  dfs_crusher: ['professional', 'elite', 'elitepro', 'will_the_thrill'],
  browser_extension: ['elite', 'elitepro', 'will_the_thrill'],
  desktop_client: ['elite', 'elitepro', 'will_the_thrill'],
  api_access: ['elite', 'elitepro', 'will_the_thrill'],
  custom_models: ['elite', 'elitepro', 'will_the_thrill'],
};

// Helper function to check access
export function hasFeatureAccess(tier: string, feature: string): boolean {
  const allowedTiers = FEATURE_ACCESS[feature];
  if (!allowedTiers) return true; // If feature not defined, allow access
  return allowedTiers.includes(tier.toLowerCase());
}

// Helper function to get minimum tier for a feature
export function getMinimumTier(feature: string): string {
  const allowedTiers = FEATURE_ACCESS[feature];
  if (!allowedTiers || allowedTiers.length === 0) return 'free';

  // Return the first non-free tier that has access
  const paidTiers = allowedTiers.filter(t => t !== 'free');
  if (paidTiers.length === 0) return 'free';

  // Priority order
  const tierOrder = ['trial', 'free_trial', 'starter', 'semipro', 'professional', 'elite', 'elitepro'];
  for (const tier of tierOrder) {
    if (paidTiers.includes(tier)) return tier;
  }
  return paidTiers[0];
}

interface TierGateProps {
  /** Feature key to check access for */
  feature: keyof typeof FEATURE_ACCESS;
  /** Content to show when user has access */
  children: React.ReactNode;
  /** Custom message for the upgrade prompt */
  upgradeMessage?: string;
  /** Show blurred preview of content (default: true) */
  showBlurredPreview?: boolean;
  /** Custom fallback content instead of default upgrade prompt */
  fallback?: React.ReactNode;
  /** Inline mode - doesn't add wrapper div (for inline content like spans) */
  inline?: boolean;
}

export function TierGate({
  feature,
  children,
  upgradeMessage,
  showBlurredPreview = true,
  fallback,
  inline = false
}: TierGateProps) {
  const { subscriptionTier, role, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Admins always have access
  if (role === 'admin') {
    return <>{children}</>;
  }

  // Development mode bypass
  const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  console.log('🔐 TierGate Debug:', {
    feature,
    hostname: window.location.hostname,
    isDev,
    subscriptionTier,
    role,
    isAuthenticated
  });

  if (isDev) {
    console.log('✅ TierGate: Dev mode bypass - showing content');
    return <>{children}</>;
  }

  // Check if user has access
  const hasAccess = hasFeatureAccess(subscriptionTier, feature);
  console.log('🔐 TierGate: hasAccess =', hasAccess, 'for feature', feature);

  if (hasAccess) {
    return <>{children}</>;
  }

  // Custom fallback if provided
  if (fallback) {
    return <>{fallback}</>;
  }

  // Default upgrade prompt
  const minTier = getMinimumTier(feature);
  const defaultMessage = upgradeMessage || `Upgrade to ${minTier.charAt(0).toUpperCase() + minTier.slice(1)} to unlock this feature`;

  // Inline mode for small content
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

  // Full blurred preview mode
  if (showBlurredPreview) {
    return (
      <div className="relative">
        {/* Blurred content preview */}
        <div className="blur-md pointer-events-none select-none opacity-50">
          {children}
        </div>

        {/* Upgrade overlay */}
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm rounded-lg">
          <div className="text-center p-6 max-w-sm">
            <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Premium Feature</h3>
            <p className="text-slate-300 text-sm mb-4">{defaultMessage}</p>
            <button
              onClick={() => navigate('/pricing')}
              className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-medium rounded-lg transition-all shadow-lg hover:shadow-xl"
            >
              {isAuthenticated ? 'Upgrade Now' : 'View Plans'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Simple non-blurred fallback
  return (
    <div className="p-6 bg-slate-800/50 rounded-lg border border-slate-700 text-center">
      <div className="w-10 h-10 mx-auto mb-3 rounded-full bg-slate-700 flex items-center justify-center">
        <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      </div>
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

/**
 * Hook to check feature access
 */
export function useFeatureAccess(feature: keyof typeof FEATURE_ACCESS): boolean {
  const { subscriptionTier, role } = useAuth();

  // Admins always have access
  if (role === 'admin') return true;

  // Dev mode bypass
  const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  if (isDev) return true;

  return hasFeatureAccess(subscriptionTier, feature);
}

/**
 * Higher-order component for wrapping entire pages
 */
export function withTierGate<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  feature: keyof typeof FEATURE_ACCESS,
  upgradeMessage?: string
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
