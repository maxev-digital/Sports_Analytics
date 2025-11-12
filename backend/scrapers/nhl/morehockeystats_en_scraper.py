"""
MoreHockeyStats.com Empty Net Scraper
Scrapes current season empty net statistics for all 32 NHL teams

Data Source: https://morehockeystats.com/teams/en
Attribution: "Empty net data courtesy of MoreHockeyStats.com"
"""

import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MoreHockeyStatsENScraper:
    """Scrape empty net statistics from MoreHockeyStats.com"""

    # Team name mapping from MoreHockeyStats display names to NHL API abbreviations
    TEAM_NAME_MAP = {
        'ANAHEIM': 'ana',
        'ARIZONA': 'ari',
        'UTAH': 'uta',
        'BOSTON': 'bos',
        'BUFFALO': 'buf',
        'CALGARY': 'cgy',
        'CAROLINA': 'car',
        'CHICAGO': 'chi',
        'COLORADO': 'col',
        'COLUMBUS': 'cbj',
        'DALLAS': 'dal',
        'DETROIT': 'det',
        'EDMONTON': 'edm',
        'FLORIDA': 'fla',
        'LOS ANGELES': 'lak',
        'MINNESOTA': 'min',
        'MONTREAL': 'mtl',
        'NASHVILLE': 'nsh',
        'NEW JERSEY': 'njd',
        'NY ISLANDERS': 'nyi',
        'NY RANGERS': 'nyr',
        'OTTAWA': 'ott',
        'PHILADELPHIA': 'phi',
        'PITTSBURGH': 'pit',
        'SAN JOSE': 'sjs',
        'SEATTLE': 'sea',
        'ST. LOUIS': 'stl',
        'ST LOUIS': 'stl',
        'TAMPA BAY': 'tbl',
        'TORONTO': 'tor',
        'VANCOUVER': 'van',
        'VEGAS': 'vgk',
        'WASHINGTON': 'wsh',
        'WINNIPEG': 'wpg',
    }

    def __init__(self):
        self.url = "https://morehockeystats.com/teams/en"
        self.data_dir = Path(__file__).parent.parent.parent / "data" / "raw" / "nhl"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver with headless options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def scrape_empty_net_stats(self) -> pd.DataFrame:
        """
        Scrape empty net statistics from MoreHockeyStats.com

        Returns:
            DataFrame with columns: team, en_goals_for, en_goals_against,
                                   en_differential, en_situations, en_success_rate
        """
        logger.info(f"Scraping empty net data from {self.url}")

        driver = None
        try:
            driver = self.setup_driver()
            driver.get(self.url)

            # Wait for table to load
            logger.info("Waiting for table to load...")
            wait = WebDriverWait(driver, 20)
            table = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )

            # Give extra time for JavaScript to populate data
            time.sleep(3)

            logger.info("Table loaded, parsing data...")

            # Parse table rows
            rows = table.find_elements(By.TAG_NAME, "tr")
            logger.info(f"Found {len(rows)} rows")

            data = []
            header_row = None

            for i, row in enumerate(rows):
                cells = row.find_elements(By.TAG_NAME, "th") + row.find_elements(By.TAG_NAME, "td")
                cell_text = [cell.text.strip() for cell in cells]

                # First row with data is header
                if i == 0 or 'Team' in cell_text:
                    header_row = cell_text
                    logger.info(f"Header: {header_row}")
                    continue

                if len(cell_text) >= 4:  # Need at least team name and some stats
                    data.append(cell_text)

            logger.info(f"Extracted {len(data)} team rows")

            if not data:
                logger.error("No data extracted from table")
                return pd.DataFrame()

            # Create DataFrame
            # Expected columns: Team, Scored (EN goals for), Allowed (EN goals against),
            #                   Count (situations), Succ. rate
            df = pd.DataFrame(data)

            # Set proper column names based on what we find
            if len(df.columns) >= 5:
                df.columns = ['Team', 'en_goals_for', 'en_goals_against', 'en_situations', 'en_success_rate'] + list(df.columns[5:])
            else:
                logger.error(f"Unexpected number of columns: {len(df.columns)}")
                logger.error(f"Sample row: {data[0] if data else 'None'}")
                return pd.DataFrame()

            # Clean and convert data types
            df['en_goals_for'] = pd.to_numeric(df['en_goals_for'], errors='coerce')
            df['en_goals_against'] = pd.to_numeric(df['en_goals_against'], errors='coerce')
            df['en_situations'] = pd.to_numeric(df['en_situations'], errors='coerce')

            # Convert success rate (might be "45.5%" format)
            df['en_success_rate'] = df['en_success_rate'].str.rstrip('%').astype(float) / 100.0

            # Map team names to abbreviations
            df['team_abbr'] = df['Team'].str.upper().apply(self._map_team_name)

            # Check for unmapped teams
            unmapped = df[df['team_abbr'].isna()]['Team'].unique()
            if len(unmapped) > 0:
                logger.warning(f"Unmapped teams: {unmapped}")

            # Drop unmapped teams
            df = df.dropna(subset=['team_abbr'])

            # Calculate differential
            df['en_differential'] = df['en_goals_for'] - df['en_goals_against']

            # Select final columns
            df = df[['team_abbr', 'Team', 'en_goals_for', 'en_goals_against',
                     'en_differential', 'en_situations', 'en_success_rate']]

            logger.info(f"Successfully scraped {len(df)} teams")
            logger.info(f"\nSample data:\n{df.head()}")

            return df

        except Exception as e:
            logger.error(f"Error scraping empty net data: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()

        finally:
            if driver:
                driver.quit()

    def _map_team_name(self, team_name: str) -> str:
        """Map MoreHockeyStats team name to NHL API abbreviation"""
        team_upper = team_name.upper()

        # Try exact match first
        if team_upper in self.TEAM_NAME_MAP:
            return self.TEAM_NAME_MAP[team_upper]

        # Try partial match
        for key, abbr in self.TEAM_NAME_MAP.items():
            if key in team_upper:
                return abbr

        return None

    def save_to_csv(self, df: pd.DataFrame, filename: str = None):
        """Save scraped data to CSV"""
        if df.empty:
            logger.error("No data to save")
            return None

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"empty_net_stats_{timestamp}.csv"

        output_path = self.data_dir / filename
        df.to_csv(output_path, index=False)
        logger.info(f"Saved empty net data to: {output_path}")

        return output_path

    def save_to_latest(self, df: pd.DataFrame):
        """Save as 'latest' file for easy loading"""
        if df.empty:
            return None

        latest_path = self.data_dir / "empty_net_stats_latest.csv"
        df.to_csv(latest_path, index=False)
        logger.info(f"Saved latest empty net data to: {latest_path}")

        return latest_path


def main():
    """Main scraper execution"""
    logger.info("=" * 60)
    logger.info("MOREHOCKEYSTATS.COM EMPTY NET SCRAPER")
    logger.info("Attribution: Empty net data courtesy of MoreHockeyStats.com")
    logger.info("=" * 60)

    scraper = MoreHockeyStatsENScraper()

    # Scrape data
    df = scraper.scrape_empty_net_stats()

    if df.empty:
        logger.error("Failed to scrape empty net data")
        return

    # Save with timestamp
    scraper.save_to_csv(df)

    # Save as latest
    scraper.save_to_latest(df)

    # Display summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Teams scraped: {len(df)}")
    logger.info(f"Total EN goals scored: {df['en_goals_for'].sum():.0f}")
    logger.info(f"Total EN goals allowed: {df['en_goals_against'].sum():.0f}")
    logger.info(f"Avg EN goals per team: {df['en_goals_for'].mean():.2f} for, {df['en_goals_against'].mean():.2f} against")

    # Top 5 teams by differential
    logger.info("\n=== Top 5 Teams (EN Differential) ===")
    top5 = df.nlargest(5, 'en_differential')[['Team', 'en_goals_for', 'en_goals_against', 'en_differential']]
    for _, row in top5.iterrows():
        logger.info(f"  {row['Team']}: {row['en_goals_for']:.0f}F / {row['en_goals_against']:.0f}A ({row['en_differential']:+.0f})")

    # Bottom 5 teams
    logger.info("\n=== Bottom 5 Teams (EN Differential) ===")
    bottom5 = df.nsmallest(5, 'en_differential')[['Team', 'en_goals_for', 'en_goals_against', 'en_differential']]
    for _, row in bottom5.iterrows():
        logger.info(f"  {row['Team']}: {row['en_goals_for']:.0f}F / {row['en_goals_against']:.0f}A ({row['en_differential']:+.0f})")

    logger.info("\n" + "=" * 60)
    logger.info("✅ SUCCESS!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
