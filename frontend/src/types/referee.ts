export type TendencyLabel = 'OVER_HEAVY' | 'UNDER_HEAVY' | 'HOME_FRIENDLY' | 'NEUTRAL';

export interface RefereeSummary {
  name: string;
  games: number;
  avg_total: number | null;
  over_rate: number | null;
  under_rate: number | null;
  home_cover_pct: number | null;
  tendency: TendencyLabel;
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
