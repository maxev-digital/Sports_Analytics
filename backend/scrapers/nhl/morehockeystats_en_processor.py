"""
MoreHockeyStats Empty Net Data Processor
Integrates empty net statistics with MoneyPuck team data

Data Source: MoreHockeyStats.com (Free download)
Attribution: "Empty net data courtesy of MoreHockeyStats.com"

This adds critical late-game features to NHL models:
- Empty net goals for/against
- EN success rate (when pulling goalie)
- EN defense rate (preventing EN goals when opponent pulls)
"""

import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MoreHockeyStatsENProcessor:
    """Process empty net statistics from MoreHockeyStats.com"""

    # Team name mapping from full names to MoneyPuck abbreviations
    TEAM_NAME_MAP = {
        'ANAHEIM DUCKS': 'ana',
        'ARIZONA COYOTES': 'ari',
        'BOSTON BRUINS': 'bos',
        'BUFFALO SABRES': 'buf',
        'CALGARY FLAMES': 'cgy',
        'CAROLINA HURRICANES': 'car',
        'CHICAGO BLACKHAWKS': 'chi',
        'COLORADO AVALANCHE': 'col',
        'COLUMBUS BLUE JACKETS': 'cbj',
        'DALLAS STARS': 'dal',
        'DETROIT RED WINGS': 'det',
        'EDMONTON OILERS': 'edm',
        'FLORIDA PANTHERS': 'fla',
        'LOS ANGELES KINGS': 'lak',
        'MINNESOTA WILD': 'min',
        'MONTREAL CANADIENS': 'mtl',
        'NASHVILLE PREDATORS': 'nsh',
        'NEW JERSEY DEVILS': 'njd',
        'NEW YORK ISLANDERS': 'nyi',
        'NEW YORK RANGERS': 'nyr',
        'OTTAWA SENATORS': 'ott',
        'PHILADELPHIA FLYERS': 'phi',
        'PITTSBURGH PENGUINS': 'pit',
        'SAN JOSE SHARKS': 'sjs',
        'SEATTLE KRAKEN': 'sea',
        'ST. LOUIS BLUES': 'stl',
        'TAMPA BAY LIGHTNING': 'tbl',
        'TORONTO MAPLE LEAFS': 'tor',
        'VANCOUVER CANUCKS': 'van',
        'VEGAS GOLDEN KNIGHTS': 'vgk',
        'WASHINGTON CAPITALS': 'wsh',
        'WINNIPEG JETS': 'wpg',
        'UTAH MAMMOTH': 'uta',  # New team 2024-25
        'UTAH HOCKEY CLUB': 'uta',  # Alternate name
    }

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / "data" / "raw" / "nhl"
        self.moneypuck_dir = self.data_dir / "moneypuck"

    def load_en_data(self, file_path: str) -> pd.DataFrame:
        """
        Load empty net data from CSV

        Args:
            file_path: Path to MoreHockeyStats EN CSV file

        Returns:
            DataFrame with processed EN stats
        """
        logger.info(f"Loading empty net data from {file_path}")

        df = pd.read_csv(file_path)

        # Show raw data structure
        logger.info(f"Loaded {len(df)} teams")
        logger.info(f"Columns: {df.columns.tolist()}")

        # Normalize team names to lowercase abbreviations
        df['team'] = df['Team'].str.upper().map(self.TEAM_NAME_MAP)

        # Check for unmapped teams
        unmapped = df[df['team'].isna()]['Team'].unique()
        if len(unmapped) > 0:
            logger.warning(f"Unmapped teams: {unmapped}")

        # Drop unmapped teams
        df = df.dropna(subset=['team'])

        # Rename columns for clarity
        df = df.rename(columns={
            'Scored': 'en_goals_for',
            'Allowed': 'en_goals_against',
            'Count': 'en_situations',
            'Succ. rate': 'en_success_rate'
        })

        # Select only needed columns
        df = df[['team', 'en_goals_for', 'en_goals_against', 'en_situations', 'en_success_rate']]

        logger.info(f"Processed {len(df)} teams with EN data")

        return df

    def merge_with_moneypuck(self, en_df: pd.DataFrame, season: str = "20232024") -> pd.DataFrame:
        """
        Merge empty net data with MoneyPuck team stats

        Args:
            en_df: Empty net DataFrame
            season: Season string (e.g., "20232024")

        Returns:
            Combined DataFrame with both datasets
        """
        logger.info(f"Merging EN data with MoneyPuck stats for {season}")

        # Load MoneyPuck processed data
        moneypuck_file = self.moneypuck_dir / "team_stats_processed_for_ml.csv"

        if not moneypuck_file.exists():
            logger.error(f"MoneyPuck data not found: {moneypuck_file}")
            return pd.DataFrame()

        moneypuck_df = pd.read_csv(moneypuck_file)

        # Debug: Show available seasons before filtering
        logger.info(f"Available seasons: {moneypuck_df['season'].unique()}")
        logger.info(f"Looking for season: {season}")
        logger.info(f"Season column dtype: {moneypuck_df['season'].dtype}")

        # Filter to requested season (strip whitespace in case of formatting issues)
        moneypuck_df['season'] = moneypuck_df['season'].astype(str).str.strip()
        season_clean = str(season).strip()
        moneypuck_df = moneypuck_df[moneypuck_df['season'] == season_clean].copy()

        if moneypuck_df.empty:
            logger.error(f"No MoneyPuck data for season {season_clean}")
            logger.error(f"Available: {sorted(moneypuck_df['season'].unique())}")
            return pd.DataFrame()

        logger.info(f"Loaded {len(moneypuck_df)} teams from MoneyPuck")

        # Merge on team
        merged = moneypuck_df.merge(en_df, on='team', how='left')

        # Fill missing EN data with 0 (teams with no EN situations)
        en_columns = ['en_goals_for', 'en_goals_against', 'en_situations', 'en_success_rate']
        merged[en_columns] = merged[en_columns].fillna(0)

        # Calculate per-game EN features
        merged['en_goals_for_per_game'] = merged['en_goals_for'] / merged['games_played']
        merged['en_goals_against_per_game'] = merged['en_goals_against'] / merged['games_played']
        merged['en_situations_per_game'] = merged['en_situations'] / merged['games_played']

        # Calculate EN differential (net advantage)
        merged['en_differential'] = merged['en_goals_for'] - merged['en_goals_against']
        merged['en_differential_per_game'] = merged['en_differential'] / merged['games_played']

        # Calculate EN defense rate (how well team prevents EN goals when opponent pulls goalie)
        # Higher is better (scored more than allowed)
        merged['en_net_rating'] = merged['en_success_rate']

        logger.info(f"Merged dataset: {len(merged)} teams with {len(merged.columns)} features")

        # Show summary statistics
        logger.info("\n=== Empty Net Statistics Summary ===")
        logger.info(f"Total EN goals scored: {merged['en_goals_for'].sum():.0f}")
        logger.info(f"Total EN goals allowed: {merged['en_goals_against'].sum():.0f}")
        logger.info(f"Avg EN goals per team: {merged['en_goals_for'].mean():.2f} for, {merged['en_goals_against'].mean():.2f} against")
        logger.info(f"Teams with positive EN differential: {(merged['en_differential'] > 0).sum()}")
        logger.info(f"Teams with negative EN differential: {(merged['en_differential'] < 0).sum()}")

        # Show top/bottom teams
        logger.info("\n=== Top 5 Teams (EN Success Rate) ===")
        top5 = merged.nlargest(5, 'en_success_rate')[['team', 'en_goals_for', 'en_goals_against', 'en_success_rate']]
        for _, row in top5.iterrows():
            logger.info(f"  {row['team'].upper()}: {row['en_goals_for']:.0f}F / {row['en_goals_against']:.0f}A ({row['en_success_rate']:.1%})")

        logger.info("\n=== Bottom 5 Teams (EN Success Rate) ===")
        bottom5 = merged.nsmallest(5, 'en_success_rate')[['team', 'en_goals_for', 'en_goals_against', 'en_success_rate']]
        for _, row in bottom5.iterrows():
            logger.info(f"  {row['team'].upper()}: {row['en_goals_for']:.0f}F / {row['en_goals_against']:.0f}A ({row['en_success_rate']:.1%})")

        return merged

    def save_combined_data(self, df: pd.DataFrame, output_path: str = None):
        """Save combined dataset"""
        if output_path is None:
            output_path = self.moneypuck_dir / "team_stats_with_empty_net.csv"

        df.to_csv(output_path, index=False)
        logger.info(f"\n✅ Saved combined data to: {output_path}")
        logger.info(f"   Total features: {len(df.columns)}")


def main():
    """Process empty net data and merge with MoneyPuck"""
    processor = MoreHockeyStatsENProcessor()

    logger.info("=" * 60)
    logger.info("PROCESSING EMPTY NET DATA FROM MOREHOCKEYSTATS.COM")
    logger.info("Attribution: Empty net data courtesy of MoreHockeyStats.com")
    logger.info("=" * 60)

    # Load EN data
    en_file = Path(__file__).parent.parent.parent / "backend" / "data" / "morehockeystats_empty_net_2023_2024.csv"

    if not en_file.exists():
        logger.error(f"Empty net CSV not found: {en_file}")
        logger.error("Please download from MoreHockeyStats.com and save to backend/backend/data/")
        return

    en_df = processor.load_en_data(str(en_file))

    # Merge with MoneyPuck data (2023-24 season)
    combined_df = processor.merge_with_moneypuck(en_df, season="20232024")

    if combined_df.empty:
        logger.error("Merge failed. Check that MoneyPuck data exists for 2023-24 season.")
        return

    # Save combined dataset
    processor.save_combined_data(combined_df)

    logger.info("=" * 60)
    logger.info("✅ SUCCESS!")
    logger.info("Empty net features added to MoneyPuck data")
    logger.info("=" * 60)
    logger.info("\nNEW FEATURES AVAILABLE:")
    logger.info("  ✅ en_goals_for_per_game - EN goals scored per game")
    logger.info("  ✅ en_goals_against_per_game - EN goals allowed per game")
    logger.info("  ✅ en_differential_per_game - Net EN advantage")
    logger.info("  ✅ en_success_rate - Success rate when pulling goalie")
    logger.info("  ✅ en_net_rating - Overall EN performance rating")
    logger.info("=" * 60)
    logger.info("\nUSE CASES:")
    logger.info("  1. Late-game total predictions (EN goals inflate scores)")
    logger.info("  2. Spread betting when teams trail (who scores EN goals?)")
    logger.info("  3. Live betting momentum (EN situations signal desperation)")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
