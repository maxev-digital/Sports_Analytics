export type TendencyLabel = 'OVER_HEAVY' | 'UNDER_HEAVY' | 'HOME_FRIENDLY' | 'NEUTRAL';

export interface RefereeSummary {
  name: string;
  games: number;
  avg_total: number | null;
  over_rate: number | null;
  under_rate: number | null;
  home_cover_pct: number | null;
  tendency: TendencyLabel;
  // Environment stats (from nfl_games)
  ot_rate?: number | null;
  dome_pct?: number | null;
  primetime_pct?: number | null;
  avg_temp?: number | null;
  avg_wind?: number | null;
  div_game_pct?: number | null;
  // Penalty stats (from nfl_referee_penalties — null until scraper runs)
  flags_per_game?: number | null;
  yards_per_game?: number | null;
  home_bias?: number | null;
}

export interface RefereeSeasonSplit {
  season: number;
  games: number;
  avg_total: number | null;
  over_rate: number | null;
  under_rate: number | null;
  home_cover_pct: number | null;
}

export interface RefereeProfile {
  name: string;
  summary: RefereeSummary;
  season_splits: RefereeSeasonSplit[];
}

export interface RefereeListResponse {
  count: number;
  referees: RefereeSummary[];
}

export type ColumnGroup = 'betting' | 'penalties' | 'environment';
