"""
Process MoreHockeyStats Empty Net CSV Data
Parses the manually downloaded CSV from morehockeystats.com
"""

import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ENCSVProcessor:
    """Process empty net data from CSV file"""

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
        'UTAH MAMMOTH': 'uta',
        'UTAH HOCKEY CLUB': 'uta',
    }

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.output_dir = Path(__file__).parent.parent.parent / "data" / "raw" / "nhl"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_csv(self) -> pd.DataFrame:
        """
        Process the EN_DATA.csv file with both tabs of data

        Returns:
            DataFrame with combined empty net statistics
        """
        logger.info(f"Processing CSV file: {self.csv_path}")

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split into AGAINST and WITH sections
        sections = content.split('With/Against')

        if len(sections) < 3:
            logger.error("Could not find both WITH and AGAINST sections")
            return pd.DataFrame()

        # Parse AGAINST section
        against_section = sections[1]
        against_lines = [line for line in against_section.split('\n') if line.strip()]

        # Find the data rows (after the header line with Team, Scored, Allowed, etc.)
        against_data = []
        in_data = False
        for line in against_lines:
            if 'Team\tScored\tAllowed' in line or 'Team	Scored	Allowed' in line:
                in_data = True
                continue
            if in_data and line.strip() and not any(x in line for x in ['Season', 'Stage', 'Empty net', 'Playoff', 'Schedule']):
                parts = line.split('\t')
                if len(parts) >= 4:
                    against_data.append(parts[:4])  # Team, Scored, Allowed, Count

        # Parse WITH section
        with_section = sections[2]
        with_lines = [line for line in with_section.split('\n') if line.strip()]

        with_data = []
        in_data = False
        for line in with_lines:
            if 'Team\tScored\tAllowed' in line or 'Team	Scored	Allowed' in line:
                in_data = True
                continue
            if in_data and line.strip() and not any(x in line for x in ['Season', 'Stage', 'Empty net', 'Playoff', 'Schedule']):
                parts = line.split('\t')
                if len(parts) >= 4:
                    with_data.append(parts[:4])  # Team, Scored, Allowed, Count

        logger.info(f"Found {len(against_data)} teams in AGAINST section")
        logger.info(f"Found {len(with_data)} teams in WITH section")

        # Create DataFrames
        against_df = pd.DataFrame(against_data, columns=['Team', 'scored_against', 'allowed_against', 'situations_against'])
        with_df = pd.DataFrame(with_data, columns=['Team', 'scored_with', 'allowed_with', 'situations_with'])

        # Convert to numeric
        for col in ['scored_against', 'allowed_against', 'situations_against']:
            against_df[col] = pd.to_numeric(against_df[col], errors='coerce')

        for col in ['scored_with', 'allowed_with', 'situations_with']:
            with_df[col] = pd.to_numeric(with_df[col], errors='coerce')

        # Map team names
        against_df['team_abbr'] = against_df['Team'].str.upper().map(self.TEAM_NAME_MAP)
        with_df['team_abbr'] = with_df['Team'].str.upper().map(self.TEAM_NAME_MAP)

        # Remove unmapped teams
        against_df = against_df.dropna(subset=['team_abbr'])
        with_df = with_df.dropna(subset=['team_abbr'])

        # Merge both datasets
        merged = against_df.merge(with_df[['team_abbr', 'scored_with', 'allowed_with', 'situations_with']],
                                 on='team_abbr', how='outer')

        # Fill NaN with 0
        numeric_cols = ['scored_against', 'allowed_against', 'situations_against',
                       'scored_with', 'allowed_with', 'situations_with']
        merged[numeric_cols] = merged[numeric_cols].fillna(0)

        # Rename to match our schema
        # AGAINST = defensive (opponent pulled goalie)
        # WITH = offensive (we pulled goalie)
        merged = merged.rename(columns={
            'scored_against': 'en_goals_for_defensive',      # Goals WE scored when opponent pulled goalie
            'allowed_against': 'en_goals_against_defensive',  # Goals opponent scored when they pulled goalie
            'situations_against': 'en_situations_defensive',
            'scored_with': 'en_goals_for_offensive',          # Goals WE scored when we pulled goalie
            'allowed_with': 'en_goals_against_offensive',     # Goals opponent scored when we pulled goalie
            'situations_with': 'en_situations_offensive'
        })

        # Calculate combined totals
        merged['en_goals_for'] = merged['en_goals_for_offensive'] + merged['en_goals_for_defensive']
        merged['en_goals_against'] = merged['en_goals_against_offensive'] + merged['en_goals_against_defensive']
        merged['en_situations'] = merged['en_situations_offensive'] + merged['en_situations_defensive']
        merged['en_differential'] = merged['en_goals_for'] - merged['en_goals_against']
        merged['en_success_rate'] = (merged['en_goals_for'] / merged['en_situations']).fillna(0)

        # Reorder columns
        merged = merged[['team_abbr', 'Team',
                       'en_goals_for', 'en_goals_against', 'en_differential',
                       'en_situations', 'en_success_rate',
                       'en_goals_for_offensive', 'en_goals_against_offensive', 'en_situations_offensive',
                       'en_goals_for_defensive', 'en_goals_against_defensive', 'en_situations_defensive']]

        logger.info(f"Successfully processed {len(merged)} teams")
        logger.info(f"\nSample data (Anaheim Ducks):")
        ducks = merged[merged['team_abbr'] == 'ana']
        if not ducks.empty:
            logger.info(f"Offensive: {ducks['en_goals_for_offensive'].values[0]}F/{ducks['en_goals_against_offensive'].values[0]}A in {ducks['en_situations_offensive'].values[0]} situations")
            logger.info(f"Defensive: {ducks['en_goals_for_defensive'].values[0]}F/{ducks['en_goals_against_defensive'].values[0]}A in {ducks['en_situations_defensive'].values[0]} situations")
            logger.info(f"Combined: {ducks['en_goals_for'].values[0]}F/{ducks['en_goals_against'].values[0]}A")

        return merged

    def save_to_csv(self, df: pd.DataFrame):
        """Save processed data to CSV"""
        if df.empty:
            logger.error("No data to save")
            return

        # Save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        timestamped_path = self.output_dir / f"empty_net_stats_{timestamp}.csv"
        df.to_csv(timestamped_path, index=False)
        logger.info(f"Saved timestamped data to: {timestamped_path}")

        # Save as latest
        latest_path = self.output_dir / "empty_net_stats_latest.csv"
        df.to_csv(latest_path, index=False)
        logger.info(f"Saved latest data to: {latest_path}")


def main():
    """Main processing function"""
    logger.info("=" * 60)
    logger.info("PROCESSING MOREHOCKEYSTATS EN_DATA.CSV")
    logger.info("=" * 60)

    # Path to the CSV file
    csv_path = Path("D:/backend/data/NHL Empty_Net_Data_Daily/EN_DATA.csv")

    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        logger.error("Please download the data from morehockeystats.com/teams/en")
        return

    processor = ENCSVProcessor(str(csv_path))
    df = processor.process_csv()

    if df.empty:
        logger.error("Failed to process CSV")
        return

    processor.save_to_csv(df)

    logger.info("\n" + "=" * 60)
    logger.info("✅ SUCCESS!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
