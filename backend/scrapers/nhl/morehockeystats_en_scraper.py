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
        'NEW YORK ISLANDERS': 'nyi',
        'NY ISLANDERS': 'nyi',
        'NEW YORK RANGERS': 'nyr',
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
        self.url_with = "https://morehockeystats.com/teams/en"  # WITH empty net (offensive)
        # Try multiple possible URL patterns for the AGAINST tab
        self.url_against_options = [
            "https://morehockeystats.com/teams/en#against",  # Hash fragment
            "https://morehockeystats.com/teams/en?tab=against",  # Tab parameter
            "https://morehockeystats.com/teams/en?view=against",  # View parameter
            "https://morehockeystats.com/teams/en?withagainst=1",  # Binary flag
            "https://morehockeystats.com/teams/en?mode=against",  # Mode parameter
        ]
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

    def scrape_tab_data(self, driver, wait, tab_name: str) -> pd.DataFrame:
        """
        Scrape data from the currently displayed tab

        Args:
            driver: Selenium webdriver
            wait: WebDriverWait instance
            tab_name: Name of the tab being scraped (for logging)

        Returns:
            DataFrame with tab data
        """
        logger.info(f"Scraping '{tab_name}' tab...")

        # Wait for table to load
        table = wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        # Give extra time for JavaScript to populate data
        time.sleep(3)

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

        logger.info(f"Extracted {len(data)} team rows from '{tab_name}' tab")

        if not data:
            logger.error(f"No data extracted from '{tab_name}' tab")
            return pd.DataFrame()

        # Create DataFrame
        # Expected columns: Team, Scored, Allowed, Count, Succ. rate
        df = pd.DataFrame(data)

        # Set proper column names based on what we find
        if len(df.columns) >= 5:
            df.columns = ['Team', 'scored', 'allowed', 'situations', 'succ_rate'] + list(df.columns[5:])
        else:
            logger.error(f"Unexpected number of columns in '{tab_name}': {len(df.columns)}")
            logger.error(f"Sample row: {data[0] if data else 'None'}")
            return pd.DataFrame()

        # Clean and convert data types
        df['scored'] = pd.to_numeric(df['scored'], errors='coerce')
        df['allowed'] = pd.to_numeric(df['allowed'], errors='coerce')
        df['situations'] = pd.to_numeric(df['situations'], errors='coerce')

        # Map team names to abbreviations
        df['team_abbr'] = df['Team'].str.upper().apply(self._map_team_name)

        # Check for unmapped teams
        unmapped = df[df['team_abbr'].isna()]['Team'].unique()
        if len(unmapped) > 0:
            logger.warning(f"Unmapped teams in '{tab_name}': {unmapped}")

        # Drop unmapped teams
        df = df.dropna(subset=['team_abbr'])

        # Keep only needed columns
        df = df[['team_abbr', 'Team', 'scored', 'allowed', 'situations']]

        return df

    def scrape_empty_net_stats(self) -> pd.DataFrame:
        """
        Scrape BOTH empty net tabs from MoreHockeyStats.com:
        1. Playing WITH empty net (offensive situations)
        2. Playing AGAINST empty net (defensive situations)

        Returns:
            DataFrame with combined empty net statistics
        """
        logger.info(f"Scraping empty net data from {self.url_with}")

        driver = None
        try:
            driver = self.setup_driver()
            wait = WebDriverWait(driver, 20)

            # ========== TAB 1: Playing WITH Empty Net (Offensive) ==========
            logger.info("=" * 60)
            logger.info("SCRAPING TAB 1: Playing WITH Empty Net")
            logger.info("=" * 60)

            driver.get(self.url_with)
            time.sleep(3)  # Wait for page to load

            with_en_df = self.scrape_tab_data(driver, wait, "Playing WITH Empty Net")

            if with_en_df.empty:
                logger.error("Failed to scrape 'Playing WITH Empty Net' tab")
                return pd.DataFrame()

            # ========== TAB 2: Playing AGAINST Empty Net (Defensive) ==========
            logger.info("\n" + "=" * 60)
            logger.info("SCRAPING TAB 2: Playing AGAINST Empty Net")
            logger.info("=" * 60)

            # Navigate directly to the AGAINST tab URL
            logger.info(f"Navigating to: {self.url_against}")
            driver.get(self.url_against)
            time.sleep(3)  # Wait for page to load

            # Scrape the AGAINST tab
            against_en_df = self.scrape_tab_data(driver, wait, "Playing AGAINST Empty Net")

            # VALIDATION: Ensure the data actually changed
            if not against_en_df.empty and not with_en_df.empty:
                # Compare first team's data to ensure it's different
                first_team_with = with_en_df.iloc[0]
                first_team_against = against_en_df.iloc[0]

                if (first_team_with['scored'] == first_team_against['scored'] and
                    first_team_with['allowed'] == first_team_against['allowed'] and
                    first_team_with['situations'] == first_team_against['situations']):
                    logger.error("⚠️ DATA VALIDATION FAILED: Both tabs have identical data!")
                    logger.error(f"WITH tab first row: {first_team_with[['Team', 'scored', 'allowed', 'situations']].to_dict()}")
                    logger.error(f"AGAINST tab first row: {first_team_against[['Team', 'scored', 'allowed', 'situations']].to_dict()}")
                    logger.warning("Tab switch did not work - data was duplicated")
                    # Save screenshot for debugging
                    try:
                        driver.save_screenshot(str(self.data_dir / "debug_duplicate_data.png"))
                        logger.info(f"Saved debug screenshot to: {self.data_dir / 'debug_duplicate_data.png'}")
                    except:
                        pass
                    return self._format_single_tab_data(with_en_df)
                else:
                    logger.info("✅ Data validation passed - tabs have different data")

            if against_en_df.empty:
                logger.error("Failed to scrape 'Playing AGAINST Empty Net' tab")
                logger.warning("Will return only offensive EN data")
                return self._format_single_tab_data(with_en_df)

            # Now rename both dataframes
            # Rename offensive data
            with_en_df = with_en_df.rename(columns={
                'scored': 'en_goals_for_offensive',      # Goals scored when WE pulled goalie
                'allowed': 'en_goals_against_offensive',  # Goals allowed when WE pulled goalie
                'situations': 'en_situations_offensive'   # Times WE pulled goalie
            })

            # Rename defensive data
            against_en_df = against_en_df.rename(columns={
                'scored': 'en_goals_for_defensive',      # Goals scored when OPPONENT pulled goalie
                'allowed': 'en_goals_against_defensive',  # Goals allowed when OPPONENT pulled goalie
                'situations': 'en_situations_defensive'   # Times OPPONENT pulled goalie
            })

            # ========== MERGE BOTH TABS ==========
            logger.info("\n" + "=" * 60)
            logger.info("MERGING BOTH TABS")
            logger.info("=" * 60)

            merged = with_en_df.merge(
                against_en_df[['team_abbr', 'en_goals_for_defensive', 'en_goals_against_defensive', 'en_situations_defensive']],
                on='team_abbr',
                how='outer'
            )

            # Fill any missing values with 0
            numeric_cols = ['en_goals_for_offensive', 'en_goals_against_offensive', 'en_situations_offensive',
                          'en_goals_for_defensive', 'en_goals_against_defensive', 'en_situations_defensive']
            merged[numeric_cols] = merged[numeric_cols].fillna(0)

            # Calculate combined totals
            merged['en_goals_for'] = merged['en_goals_for_offensive'] + merged['en_goals_for_defensive']
            merged['en_goals_against'] = merged['en_goals_against_offensive'] + merged['en_goals_against_defensive']
            merged['en_situations'] = merged['en_situations_offensive'] + merged['en_situations_defensive']
            merged['en_differential'] = merged['en_goals_for'] - merged['en_goals_against']

            # Calculate success rate (combined)
            merged['en_success_rate'] = (merged['en_goals_for'] / merged['en_situations']).fillna(0)

            # Reorder columns
            merged = merged[['team_abbr', 'Team',
                           'en_goals_for', 'en_goals_against', 'en_differential',
                           'en_situations', 'en_success_rate',
                           'en_goals_for_offensive', 'en_goals_against_offensive', 'en_situations_offensive',
                           'en_goals_for_defensive', 'en_goals_against_defensive', 'en_situations_defensive']]

            logger.info(f"Successfully merged data for {len(merged)} teams")
            logger.info(f"\nSample merged data:\n{merged.head()}")

            return merged

        except Exception as e:
            logger.error(f"Error scraping empty net data: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()

        finally:
            if driver:
                driver.quit()

    def _format_single_tab_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Format single tab data (fallback when only one tab is available)

        Args:
            df: DataFrame with 'scored', 'allowed', 'situations' columns (NOT renamed yet)

        Returns:
            DataFrame formatted with combined columns
        """
        # First rename offensive columns
        df = df.rename(columns={
            'scored': 'en_goals_for_offensive',
            'allowed': 'en_goals_against_offensive',
            'situations': 'en_situations_offensive'
        })

        # Calculate combined stats (same as offensive when defensive is missing)
        df['en_goals_for'] = df['en_goals_for_offensive']
        df['en_goals_against'] = df['en_goals_against_offensive']
        df['en_situations'] = df['en_situations_offensive']
        df['en_differential'] = df['en_goals_for'] - df['en_goals_against']
        df['en_success_rate'] = (df['en_goals_for'] / df['en_situations']).fillna(0)

        # Add defensive columns as zeros
        df['en_goals_for_defensive'] = 0
        df['en_goals_against_defensive'] = 0
        df['en_situations_defensive'] = 0

        # Reorder columns
        df = df[['team_abbr', 'Team',
                'en_goals_for', 'en_goals_against', 'en_differential',
                'en_situations', 'en_success_rate',
                'en_goals_for_offensive', 'en_goals_against_offensive', 'en_situations_offensive',
                'en_goals_for_defensive', 'en_goals_against_defensive', 'en_situations_defensive']]

        return df

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
