"""
NHL Historical Data Loader

Fetches historical NHL game data for model training:
- Game results (scores, winners)
- Team statistics (season averages)
- Goalie statistics
- Advanced metrics (PDO, faceoffs, etc.)

Data Sources:
1. NHL Official API (api-web.nhle.com)
2. Local database (if already scraped)
3. CSV files in backend/data/historical/nhl/
"""

import httpx
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class NHLDataLoader:
    """Load and preprocess historical NHL data for model training"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = "https://api-web.nhle.com/v1"
        self.data_dir = Path(__file__).parent.parent.parent / "data" / "historical" / "nhl"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def fetch_season_games(self, season: str) -> pd.DataFrame:
        """
        Fetch all games for a season

        Args:
            season: Season string like "20232024"

        Returns:
            DataFrame with game results
        """
        logger.info(f"Fetching NHL season {season} games...")

        # Check if already cached locally
        cache_file = self.data_dir / f"games_{season}.csv"
        if cache_file.exists():
            logger.info(f"Loading cached data from {cache_file}")
            return pd.read_csv(cache_file)

        games = []

        try:
            # Fetch schedule from NHL API
            # Note: Actual API endpoints may vary, adjust as needed
            url = f"{self.base_url}/schedule/{season}"
            response = await self.client.get(url)
            response.raise_for_status()
            schedule_data = response.json()

            # Parse games from schedule
            for game_week in schedule_data.get('gameWeek', []):
                for game_date in game_week.get('games', []):
                    for game in game_date if isinstance(game_date, list) else [game_date]:
                        if game.get('gameState') == 'OFF':  # Final games only
                            games.append({
                                'game_id': game.get('id'),
                                'date': game.get('gameDate'),
                                'home_team': game.get('homeTeam', {}).get('abbrev'),
                                'away_team': game.get('awayTeam', {}).get('abbrev'),
                                'home_score': game.get('homeTeam', {}).get('score', 0),
                                'away_score': game.get('awayTeam', {}).get('score', 0),
                                'season': season
                            })

            # Convert to DataFrame
            df = pd.DataFrame(games)

            # Calculate outcomes
            df['home_win'] = (df['home_score'] > df['away_score']).astype(int)
            df['total'] = df['home_score'] + df['away_score']
            df['home_margin'] = df['home_score'] - df['away_score']

            # Cache the results
            df.to_csv(cache_file, index=False)
            logger.info(f"Saved {len(df)} games to {cache_file}")

            return df

        except Exception as e:
            logger.error(f"Error fetching season {season}: {e}")
            return pd.DataFrame()

    def load_enhanced_stats(self, season: str) -> pd.DataFrame:
        """
        Load enhanced team statistics from MoneyPuck + MoreHockeyStats

        UPGRADED 2025-11-11: Now uses REAL data instead of placeholders
        - MoneyPuck.com: xG, shot quality, possession metrics, REAL shots/faceoffs
        - MoreHockeyStats.com: Empty net statistics

        Args:
            season: Season string like "20232024"

        Returns:
            DataFrame with 54 enhanced features per team
        """
        enhanced_file = self.data_dir / "moneypuck" / "team_stats_with_empty_net.csv"

        if not enhanced_file.exists():
            logger.warning(f"Enhanced stats file not found: {enhanced_file}")
            logger.warning("Falling back to basic NHL API stats with placeholders")
            return pd.DataFrame()

        df = pd.read_csv(enhanced_file)

        # Convert season to int for filtering
        season_int = int(season)
        df_season = df[df['season'] == season_int].copy()

        if df_season.empty:
            logger.warning(f"No enhanced stats for season {season}")
            logger.info(f"Available seasons: {sorted(df['season'].unique())}")
            return pd.DataFrame()

        logger.info(f"✅ Loaded ENHANCED stats for {len(df_season)} teams ({len(df_season.columns)} features)")
        logger.info(f"   Includes: xG, shot quality, possession, empty net data")

        return df_season

    async def fetch_team_stats(self, season: str) -> pd.DataFrame:
        """
        Fetch team statistics for a season (FALLBACK METHOD)

        NOTE: This method uses placeholders for many stats.
        Prefer load_enhanced_stats() which has REAL data from MoneyPuck.

        Returns:
            DataFrame with team stats (GPG, GAPG, PP%, PK%, etc.)
        """
        logger.info(f"Fetching NHL team stats for {season}...")

        cache_file = self.data_dir / f"team_stats_{season}.csv"
        if cache_file.exists():
            return pd.read_csv(cache_file)

        team_stats = []

        try:
            # Fetch standings (includes basic stats)
            url = f"{self.base_url}/standings/{season}"
            response = await self.client.get(url)
            response.raise_for_status()
            standings = response.json()

            for team in standings.get('standings', []):
                team_abbr = team.get('teamAbbrev', {}).get('default', '').lower()
                games_played = team.get('gamesPlayed', 0)

                if games_played == 0:
                    continue

                team_stats.append({
                    'team': team_abbr,
                    'season': season,
                    'games_played': games_played,
                    'wins': team.get('wins', 0),
                    'losses': team.get('losses', 0),
                    'ot_losses': team.get('otLosses', 0),
                    'points': team.get('points', 0),
                    'goals_for': team.get('goalFor', 0),
                    'goals_against': team.get('goalAgainst', 0),
                    'goals_per_game': team.get('goalFor', 0) / games_played,
                    'goals_against_per_game': team.get('goalAgainst', 0) / games_played,
                    'win_pct': team.get('wins', 0) / games_played,
                    # PLACEHOLDERS (replaced by load_enhanced_stats()):
                    'shots_per_game': 30.0,  # Placeholder
                    'shots_against_per_game': 30.0,
                    'power_play_pct': 20.0,
                    'penalty_kill_pct': 80.0,
                    'faceoff_win_pct': 50.0,
                    'shooting_pct': 10.0,
                    'save_pct': 0.910,
                    'pdo': 100.0
                })

            df = pd.DataFrame(team_stats)
            df.to_csv(cache_file, index=False)
            logger.info(f"Saved team stats for {len(df)} teams")

            return df

        except Exception as e:
            logger.error(f"Error fetching team stats: {e}")
            return pd.DataFrame()

    def load_historical_data(self, seasons: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load historical data for multiple seasons

        Args:
            seasons: List of season strings like ["20222023", "20232024"]

        Returns:
            Tuple of (games_df, team_stats_df)
        """
        all_games = []
        all_stats = []

        for season in seasons:
            # Run async functions
            games = asyncio.run(self.fetch_season_games(season))
            stats = asyncio.run(self.fetch_team_stats(season))

            if not games.empty:
                all_games.append(games)
            if not stats.empty:
                all_stats.append(stats)

        games_df = pd.concat(all_games, ignore_index=True) if all_games else pd.DataFrame()
        stats_df = pd.concat(all_stats, ignore_index=True) if all_stats else pd.DataFrame()

        logger.info(f"Loaded {len(games_df)} games and {len(stats_df)} team-season records")

        return games_df, stats_df

    def prepare_training_data(self, games_df: pd.DataFrame, stats_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge games with team stats to create training dataset

        UPGRADED 2025-11-11: Attempts to use enhanced stats (xG, shot quality, etc.)
        Falls back to basic stats if enhanced not available.

        Returns:
            DataFrame ready for model training with features and targets
        """
        logger.info("Preparing training data...")

        training_data = []

        # Try to load enhanced stats for seasons in games_df
        seasons = games_df['season'].unique()
        enhanced_stats_dict = {}

        for season in seasons:
            enhanced = self.load_enhanced_stats(season)
            if not enhanced.empty:
                enhanced_stats_dict[season] = enhanced
                logger.info(f"✅ Using ENHANCED stats for {season}")
            else:
                logger.info(f"⚠️  Using basic stats for {season} (enhanced not available)")

        for _, game in games_df.iterrows():
            # Get team stats for this game's season
            season = game['season']
            home_team = game['home_team']
            away_team = game['away_team']

            # Try enhanced stats first, fall back to basic stats
            if season in enhanced_stats_dict:
                enhanced_df = enhanced_stats_dict[season]
                home_stats = enhanced_df[enhanced_df['team'] == home_team.lower()]
                away_stats = enhanced_df[enhanced_df['team'] == away_team.lower()]
            else:
                home_stats = stats_df[(stats_df['season'] == season) & (stats_df['team'] == home_team)]
                away_stats = stats_df[(stats_df['season'] == season) & (stats_df['team'] == away_team)]

            if home_stats.empty or away_stats.empty:
                continue

            # Create feature row
            row = {
                'game_id': game['game_id'],
                'date': game['date'],
                'season': season,

                # Home team features
                'home_team': home_team,
                'home_goals_per_game': home_stats.iloc[0]['goals_per_game'],
                'home_goals_against_per_game': home_stats.iloc[0]['goals_against_per_game'],
                'home_shots_per_game': home_stats.iloc[0]['shots_per_game'],
                'home_shots_against_per_game': home_stats.iloc[0]['shots_against_per_game'],
                'home_power_play_pct': home_stats.iloc[0]['power_play_pct'],
                'home_penalty_kill_pct': home_stats.iloc[0]['penalty_kill_pct'],
                'home_faceoff_win_pct': home_stats.iloc[0]['faceoff_win_pct'],
                'home_shooting_pct': home_stats.iloc[0]['shooting_pct'],
                'home_save_pct': home_stats.iloc[0]['save_pct'],
                'home_pdo': home_stats.iloc[0]['pdo'],
                'home_win_pct': home_stats.iloc[0]['win_pct'],

                # Away team features
                'away_team': away_team,
                'away_goals_per_game': away_stats.iloc[0]['goals_per_game'],
                'away_goals_against_per_game': away_stats.iloc[0]['goals_against_per_game'],
                'away_shots_per_game': away_stats.iloc[0]['shots_per_game'],
                'away_shots_against_per_game': away_stats.iloc[0]['shots_against_per_game'],
                'away_power_play_pct': away_stats.iloc[0]['power_play_pct'],
                'away_penalty_kill_pct': away_stats.iloc[0]['penalty_kill_pct'],
                'away_faceoff_win_pct': away_stats.iloc[0]['faceoff_win_pct'],
                'away_shooting_pct': away_stats.iloc[0]['shooting_pct'],
                'away_save_pct': away_stats.iloc[0]['save_pct'],
                'away_pdo': away_stats.iloc[0]['pdo'],
                'away_win_pct': away_stats.iloc[0]['win_pct'],

                # === ENHANCED FEATURES (2025-11-11) ===
                # Expected Goals
                'home_xgoals_per_game': home_stats.iloc[0].get('xgoals_per_game', home_stats.iloc[0]['goals_per_game']),
                'away_xgoals_per_game': away_stats.iloc[0].get('xgoals_per_game', away_stats.iloc[0]['goals_per_game']),
                'home_xgoals_against_per_game': home_stats.iloc[0].get('xgoals_against_per_game', home_stats.iloc[0]['goals_against_per_game']),
                'away_xgoals_against_per_game': away_stats.iloc[0].get('xgoals_against_per_game', away_stats.iloc[0]['goals_against_per_game']),
                'home_goals_above_expected': home_stats.iloc[0].get('goals_above_expected', 0),
                'away_goals_above_expected': away_stats.iloc[0].get('goals_above_expected', 0),

                # Shot Quality
                'home_hd_shooting_pct': home_stats.iloc[0].get('hd_shooting_pct', 25.0),
                'away_hd_shooting_pct': away_stats.iloc[0].get('hd_shooting_pct', 25.0),
                'home_hd_save_pct': home_stats.iloc[0].get('hd_save_pct', 0.70),
                'away_hd_save_pct': away_stats.iloc[0].get('hd_save_pct', 0.70),

                # Possession Metrics
                'home_corsi_for_pct': home_stats.iloc[0].get('corsi_for_pct', 50.0),
                'away_corsi_for_pct': away_stats.iloc[0].get('corsi_for_pct', 50.0),
                'home_fenwick_for_pct': home_stats.iloc[0].get('fenwick_for_pct', 50.0),
                'away_fenwick_for_pct': away_stats.iloc[0].get('fenwick_for_pct', 50.0),

                # Empty Net Stats
                'home_en_goals_for_per_game': home_stats.iloc[0].get('en_goals_for_per_game', 0),
                'away_en_goals_for_per_game': away_stats.iloc[0].get('en_goals_for_per_game', 0),
                'home_en_goals_against_per_game': home_stats.iloc[0].get('en_goals_against_per_game', 0),
                'away_en_goals_against_per_game': away_stats.iloc[0].get('en_goals_against_per_game', 0),
                'home_en_success_rate': home_stats.iloc[0].get('en_success_rate', 0),
                'away_en_success_rate': away_stats.iloc[0].get('en_success_rate', 0),

                # Target variables
                'home_score': game['home_score'],
                'away_score': game['away_score'],
                'total': game['total'],
                'home_margin': game['home_margin'],
                'home_win': game['home_win']
            }

            training_data.append(row)

        df = pd.DataFrame(training_data)
        logger.info(f"Created training dataset with {len(df)} games")

        return df

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


def load_nhl_training_data(seasons: List[str] = None) -> pd.DataFrame:
    """
    Convenience function to load NHL training data

    Args:
        seasons: List of seasons to load. Defaults to last 3 seasons.

    Returns:
        Training-ready DataFrame
    """
    if seasons is None:
        # Default to last 3 seasons
        current_year = datetime.now().year
        seasons = [
            f"{current_year-3}{current_year-2}",
            f"{current_year-2}{current_year-1}",
            f"{current_year-1}{current_year}"
        ]

    loader = NHLDataLoader()
    games_df, stats_df = loader.load_historical_data(seasons)

    # If no data from API, try sample data
    if games_df.empty:
        sample_file = loader.data_dir / "sample_training_data.csv"
        if sample_file.exists():
            logger.info(f"Using sample training data from {sample_file}")
            training_df = pd.read_csv(sample_file)
            return training_df
        else:
            logger.error("No data available from API or sample file")
            return pd.DataFrame()

    training_df = loader.prepare_training_data(games_df, stats_df)

    return training_df
