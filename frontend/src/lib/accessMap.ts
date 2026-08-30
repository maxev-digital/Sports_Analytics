/**
 * accessMap.ts — Single source of truth for route access tiers.
 *
 * Tiers (3 only):
 *   free   — no account needed
 *   member — free signup required
 *   pro    — $99/year subscription
 *   admin  — admin role only
 */

export type AccessTier = 'free' | 'member' | 'pro' | 'admin';

// Legacy paid tier names that map to 'pro'
const PRO_TIERS = new Set([
  'pro', 'elite', 'elitepro', 'professional', 'semipro', 'will_the_thrill',
]);

export function getUserTier(
  isAuthenticated: boolean,
  subscriptionTier: string,
  role: string | null,
): AccessTier {
  if (role === 'admin') return 'admin';
  if (!isAuthenticated) return 'free';
  if (PRO_TIERS.has(subscriptionTier)) return 'pro';
  return 'member';
}

const TIER_RANK: Record<AccessTier, number> = {
  free: 0, member: 1, pro: 2, admin: 3,
};

export function canAccessRoute(userTier: AccessTier, requiredTier: AccessTier): boolean {
  return TIER_RANK[userTier] >= TIER_RANK[requiredTier];
}

// Route → minimum tier required
export const ROUTE_TIERS: Record<string, AccessTier> = {
  // ── Free ──────────────────────────────────────────────────────────────
  '/':                'free',
  '/live-games':      'free',
  '/odds':            'free',
  '/alerts':          'free',
  '/todays-plays':    'free',
  '/picks':           'free',
  '/accuracy':        'free',
  '/power-rankings':  'free',
  '/team-rankings':   'free',
  '/track-record':    'free',
  '/system-overview': 'free',
  '/system-nfl':      'free',

  // ── Member (free signup) ───────────────────────────────────────────────
  '/survivor':          'member',
  '/confidence-pool':   'member',
  '/matchup-lab':       'member',
  '/trends':            'member',
  '/nfl-trends':        'member',
  '/cfb-ratings':       'member',
  '/mlb-team-stats':    'member',
  '/nfl-team-stats':    'member',
  '/recap':             'member',
  '/data-points':       'member',
  '/model-research':    'member',
  '/line-movement':     'member',
  '/madden-ratings':    'member',
  '/statcast':          'member',
  '/betting-rankings':  'member',
  '/open-bets':         'member',
  '/settings':          'member',

  // ── Pro ($99/year) ────────────────────────────────────────────────────
  '/model-projections':    'pro',
  '/model-performance':    'pro',
  '/predictions-database': 'pro',
  '/f5-edge':              'pro',
  '/max-ev-edges':         'pro',
  '/advanced-metrics':     'pro',
  '/player-leaders':       'pro',
  '/referee-trends':       'pro',
  '/injury-impact':        'pro',
  '/injury-heatmap':       'pro',
  '/tools':                'pro',
  '/kalshi':               'pro',
  '/analytics':            'pro',
  '/props':                'pro',

  // ── Admin ─────────────────────────────────────────────────────────────
  '/system-health':    'admin',
  '/admin-dashboard':  'admin',
};

export function getRouteTier(path: string): AccessTier {
  return ROUTE_TIERS[path] ?? 'free';
}
