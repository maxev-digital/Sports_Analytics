/**
 * Survivor Helper — shared UI utilities.
 * Logo helper, OKLCH color tokens, and WP color scale.
 * Imported by all Survivor sub-components to avoid duplication.
 */

export const LOGO_MAP: Record<string, string> = {
  ARI: 'ari', ATL: 'atl', BAL: 'bal', BUF: 'buf', CAR: 'car', CHI: 'chi',
  CIN: 'cin', CLE: 'cle', DAL: 'dal', DEN: 'den', DET: 'det', GB:  'gb',
  HOU: 'hou', IND: 'ind', JAX: 'jax', KC:  'kc',  LAC: 'lac', LAR: 'lar',
  LV:  'lv',  MIA: 'mia', MIN: 'min', NE:  'ne',  NO:  'no',  NYG: 'nyg',
  NYJ: 'nyj', PHI: 'phi', PIT: 'pit', SEA: 'sea', SF:  'sf',  TB:  'tb',
  TEN: 'ten', WSH: 'wsh',
};

export const logo = (abbr: string): string =>
  `https://a.espncdn.com/i/teamlogos/nfl/500/${LOGO_MAP[abbr] ?? abbr.toLowerCase()}.png`;

/**
 * Convert an oklch(x% y z) color string to oklch(x% y z / alpha).
 * Fixes the invalid CSS produced by concatenating hex digits onto OKLCH colors.
 */
export const withAlpha = (oklchColor: string, alpha: number): string =>
  oklchColor.replace(')', ` / ${alpha})`);

/** OKLCH semantic color palette — synced with tailwind.config survivor tokens. */
export const COLORS = {
  EMERALD: 'oklch(69.6% .17 162.48)',
  RED:     'oklch(63.2% .204 25.331)',
  YELLOW:  'oklch(79.5% .184 86.047)',
  BLUE:    'oklch(62.3% .214 259.815)',
  ORANGE:  'oklch(72% .19 50)',
  PURPLE:  'oklch(70% .18 290)',
} as const;

export type NflColor = (typeof COLORS)[keyof typeof COLORS];

/** Win probability → OKLCH color (matches ev-* tailwind tokens). */
export const wpColor = (wp: number): string =>
  wp >= 0.73 ? COLORS.EMERALD
  : wp >= 0.58 ? COLORS.BLUE
  : wp >= 0.45 ? COLORS.YELLOW
  : COLORS.RED;

/** WP label string → display color. */
export const WP_LABEL_COLOR: Record<string, string> = {
  GREAT: COLORS.EMERALD,
  GOOD:  'oklch(70% .15 150)',
  LEAN:  COLORS.YELLOW,
  TOUGH: 'oklch(70% .15 30)',
  TRAP:  COLORS.RED,
};
