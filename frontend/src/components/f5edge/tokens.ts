/**
 * F5 Edge Engine — Design Tokens
 * Matches the analytics.css oklch palette exactly.
 */

export const EMERALD   = 'oklch(69.6% .17 162.48)';
export const BRAND_RED = 'oklch(63.7% .237 25.331)';
export const BLUE      = 'oklch(62.3% .214 259.815)';
export const YELLOW    = 'oklch(79.5% .184 86.047)';
export const MUTED_FG  = 'oklch(70.8% 0 0)';
export const FG        = 'oklch(98.5% 0 0)';
export const BORDER    = 'oklch(100% 0 0 / .1)';
export const CARD_BG   = 'oklch(24% 0 0)';

export const TIER_COLORS: Record<string, string> = {
  STRONG:   EMERALD,
  GOOD:     BLUE,
  STANDARD: YELLOW,
  PASS:     MUTED_FG,
};

export function tierColor(tier: number): string {
  if (tier === 1) return EMERALD;
  if (tier === 2) return BLUE;
  return YELLOW;
}

export function tierLabel(tier: number): string {
  if (tier === 1) return 'STRONG';
  if (tier === 2) return 'GOOD';
  return 'STANDARD';
}

export function plColor(value: number): string {
  if (value > 0) return EMERALD;
  if (value < 0) return BRAND_RED;
  return MUTED_FG;
}

export function fmtOdds(odds: number): string {
  return odds >= 0 ? `+${odds}` : `${odds}`;
}

export function fmtPl(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}$${Math.abs(value).toFixed(0)}`;
}

export function fmtPct(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
}
