/**
 * F5 Edge Engine — TypeScript Interfaces
 */

export interface F5Play {
  type: string;
  book: string;
  tier: number;
  unit: number;
  signal: string;
  expected_hit: string;
  historical_roi: string;
  needs_f5_odds: boolean;
  fav_side?: string;
}

export interface F5Game {
  away_team: string;
  home_team: string;
  venue: string;
  away_pitcher: string;
  home_pitcher: string;
  away_era: number | null;
  home_era: number | null;
  era_diff: number | null;
  hp_umpire: string | null;
  temp: string | null;
  wind: string | null;
  commence: string;
  game_pk: number;
}

export interface F5GameWithPlays {
  game: F5Game;
  plays: F5Play[];
  odds: Record<string, unknown>;
  has_plays?: boolean;
}

export interface SignalStats {
  name: string;
  description: string;
  bets: number;
  wins: number;
  win_rate: number;
  roi: number;
  pl: number;
  p_value: number | null;
  status: 'proven' | 'promising' | 'disproved';
}

export interface DailyResult {
  date: string;
  pl: number;
  bets: number;
  wins: number;
}

export interface VenueEdge {
  venue: string;
  games: number;
  under_pct: number;
  under_roi: number;
  over_pct: number;
  over_roi: number;
  tie_pct: number;
  fav_pct: number;
  fav_roi: number;
}

export interface UmpireEdge {
  name: string;
  games: number;
  tie_rate: number;
  avg_f5: number;
}
