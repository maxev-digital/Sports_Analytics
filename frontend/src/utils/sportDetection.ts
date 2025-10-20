/**
 * Sport Detection and Styling Utilities
 * Based on design system from DESIGN_SYSTEM.md
 */

export type SportType = 'NBA' | 'NFL' | 'NHL' | 'MLB' | 'NCAAF' | 'NCAAB' | 'SOCCER' | 'PGA' | 'TENNIS' | 'MMA';

/**
 * Detect sport from game data
 */
export function detectSport(game: any): SportType {
  const sport_key = game?.state?.sport_key || game?.sport_key || game?.sport || '';
  const sportKeyLower = sport_key.toLowerCase();

  if (sportKeyLower.includes('basketball_nba')) return 'NBA';
  if (sportKeyLower.includes('americanfootball_nfl')) return 'NFL';
  if (sportKeyLower.includes('americanfootball_ncaaf')) return 'NCAAF';
  if (sportKeyLower.includes('basketball_ncaab')) return 'NCAAB';
  if (sportKeyLower.includes('icehockey_nhl')) return 'NHL';
  if (sportKeyLower.includes('baseball_mlb')) return 'MLB';
  if (sportKeyLower.includes('soccer')) return 'SOCCER';
  if (sportKeyLower.includes('golf') || sportKeyLower.includes('pga')) return 'PGA';
  if (sportKeyLower.includes('tennis') || sportKeyLower.includes('atp') || sportKeyLower.includes('wta')) return 'TENNIS';
  if (sportKeyLower.includes('mma') || sportKeyLower.includes('ufc') || sportKeyLower.includes('boxing')) return 'MMA';

  return 'NBA'; // default
}

/**
 * Microsoft Fluent Emoji CDN URLs
 */
export const sportEmojis: Record<SportType, string> = {
  'NBA': 'https://em-content.zobj.net/source/microsoft-teams/363/basketball_1f3c0.png',
  'NFL': 'https://em-content.zobj.net/source/microsoft-teams/363/american-football_1f3c8.png',
  'NHL': 'https://em-content.zobj.net/source/microsoft-teams/363/ice-hockey_1f3d2.png',
  'MLB': 'https://em-content.zobj.net/source/microsoft-teams/363/baseball_26be.png',
  'NCAAF': 'https://em-content.zobj.net/source/microsoft-teams/363/american-football_1f3c8.png',
  'NCAAB': 'https://em-content.zobj.net/source/microsoft-teams/363/basketball_1f3c0.png',
  'SOCCER': 'https://em-content.zobj.net/source/microsoft-teams/363/soccer-ball_26bd.png',
  'PGA': 'https://em-content.zobj.net/source/microsoft-teams/363/flag-in-hole_26f3.png',
  'TENNIS': 'https://em-content.zobj.net/source/microsoft-teams/363/tennis_1f3be.png',
  'MMA': 'https://em-content.zobj.net/source/microsoft-teams/363/boxing-glove_1f94a.png'
};

/**
 * UI Emoji icons
 */
export const uiEmojis = {
  target: 'https://em-content.zobj.net/source/microsoft-teams/363/direct-hit_1f3af.png',
  fire: 'https://em-content.zobj.net/source/microsoft-teams/363/fire_1f525.png',
  chart: 'https://em-content.zobj.net/source/microsoft-teams/363/chart-increasing_1f4c8.png',
  lightning: 'https://em-content.zobj.net/source/microsoft-teams/363/high-voltage_26a1.png',
  search: 'https://em-content.zobj.net/source/microsoft-teams/363/magnifying-glass-tilted-left_1f50d.png',
  book: 'https://em-content.zobj.net/source/microsoft-teams/363/books_1f4da.png',
  graduation: 'https://em-content.zobj.net/source/microsoft-teams/363/graduation-cap_1f393.png',
  rocket: 'https://em-content.zobj.net/source/microsoft-teams/363/rocket_1f680.png',
  dollar: 'https://em-content.zobj.net/source/microsoft-teams/363/money-bag_1f4b0.png',
  gear: 'https://em-content.zobj.net/source/microsoft-teams/363/gear_2699-fe0f.png'
};

/**
 * Get sport emoji URL
 */
export function getSportEmoji(sport: SportType): string {
  return sportEmojis[sport] || sportEmojis['NBA'];
}

/**
 * Sport-specific styling configurations
 */
export interface SportStyle {
  gradientFrom: string;
  gradientTo: string;
  borderColor: string;
  glowColor: string;
}

export const sportStyles: Record<SportType, SportStyle> = {
  'NBA': {
    gradientFrom: 'from-blue-900',
    gradientTo: 'to-slate-800',
    borderColor: 'border-blue-500',
    glowColor: 'rgba(59, 130, 246, 0.3)'
  },
  'NFL': {
    gradientFrom: 'from-green-900',
    gradientTo: 'to-slate-800',
    borderColor: 'border-green-500',
    glowColor: 'rgba(34, 197, 94, 0.3)'
  },
  'NHL': {
    gradientFrom: 'from-orange-900',
    gradientTo: 'to-slate-800',
    borderColor: 'border-orange-500',
    glowColor: 'rgba(249, 115, 22, 0.3)'
  },
  'MLB': {
    gradientFrom: 'from-purple-900',
    gradientTo: 'to-slate-800',
    borderColor: 'border-purple-500',
    glowColor: 'rgba(168, 85, 247, 0.3)'
  },
  'NCAAF': {
    gradientFrom: 'from-red-900',
    gradientTo: 'to-slate-800',
    borderColor: 'border-red-500',
    glowColor: 'rgba(239, 68, 68, 0.3)'
  },
  'NCAAB': {
    gradientFrom: 'from-indigo-900',
    gradientTo: 'to-slate-800',
    borderColor: 'border-indigo-500',
    glowColor: 'rgba(99, 102, 241, 0.3)'
  },
  'SOCCER': {
    gradientFrom: 'from-cyan-900',
    gradientTo: 'to-slate-800',
    borderColor: 'border-cyan-500',
    glowColor: 'rgba(6, 182, 212, 0.3)'
  },
  'PGA': {
    gradientFrom: 'from-lime-900',
    gradientTo: 'to-slate-800',
    borderColor: 'border-lime-500',
    glowColor: 'rgba(132, 204, 22, 0.3)'
  },
  'TENNIS': {
    gradientFrom: 'from-yellow-900',
    gradientTo: 'to-slate-800',
    borderColor: 'border-yellow-500',
    glowColor: 'rgba(234, 179, 8, 0.3)'
  },
  'MMA': {
    gradientFrom: 'from-rose-900',
    gradientTo: 'to-slate-800',
    borderColor: 'border-rose-500',
    glowColor: 'rgba(244, 63, 94, 0.3)'
  }
};

/**
 * Get sport styling classes
 */
export function getSportStyle(sport: SportType): SportStyle {
  return sportStyles[sport] || sportStyles['NBA'];
}

/**
 * Get full gradient class string for Tailwind
 */
export function getSportGradientClasses(sport: SportType): string {
  const style = getSportStyle(sport);
  return `bg-gradient-to-br ${style.gradientFrom} ${style.gradientTo}`;
}

/**
 * Get border class for sport
 */
export function getSportBorderClass(sport: SportType): string {
  return getSportStyle(sport).borderColor;
}

/**
 * Get glow color for hover effects
 */
export function getSportGlowColor(sport: SportType): string {
  return getSportStyle(sport).glowColor;
}
