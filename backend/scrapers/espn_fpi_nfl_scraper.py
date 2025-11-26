"""
ESPN FPI NFL Scraper
Scrapes opponent-adjusted efficiency ratings from ESPN FPI page
"""
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import logging
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)

class ESPNFPINFLScraper:
    """Scrapes NFL FPI ratings from ESPN"""

    def __init__(self):
        self.base_url = "https://www.espn.com/nfl/fpi"
        self.cache_file = "backend/data/raw/nfl/espn_fpi_cache.json"
        self.cache_duration_hours = 6

    def _load_cache(self) -> Optional[Dict]:
        """Load cached FPI data if available and fresh"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)

                # Check if cache is fresh (< 6 hours old)
                cache_time = datetime.fromisoformat(cache['timestamp'])
                age_hours = (datetime.now() - cache_time).total_seconds() / 3600

                if age_hours < self.cache_duration_hours:
                    logger.info(f"Loaded ESPN FPI cache from {cache['timestamp']}")
                    return cache['data']
                else:
                    logger.info(f"ESPN FPI cache is {age_hours:.1f} hours old, refreshing...")
        except Exception as e:
            logger.warning(f"Could not load ESPN FPI cache: {e}")

        return None

    def _save_cache(self, data: Dict):
        """Save FPI data to cache file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            cache = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
            logger.info(f"Saved ESPN FPI cache to {self.cache_file}")
        except Exception as e:
            logger.error(f"Could not save ESPN FPI cache: {e}")

    def _normalize_team_name(self, espn_name: str) -> str:
        """Convert ESPN team names to database format"""
        # ESPN uses full names like "Kansas City Chiefs"
        # Database uses short names like "Kansas City"

        # Handle special cases first
        special_cases = {
            'New York Giants': 'NY Giants',
            'New York Jets': 'NY Jets',
            'Los Angeles Rams': 'LA Rams',
            'Los Angeles Chargers': 'LA Chargers',
            'San Francisco 49ers': 'San Francisco',
            'Tampa Bay Buccaneers': 'Tampa Bay',
            'New England Patriots': 'New England'
        }

        if espn_name in special_cases:
            return special_cases[espn_name]

        # Strip mascot from end
        mascots = [
            'Texans', 'Bills', 'Ravens', 'Steelers', 'Bengals', 'Browns', 'Colts',
            'Jaguars', 'Titans', 'Chiefs', 'Broncos', 'Chargers', 'Raiders',
            'Cowboys', 'Eagles', 'Giants', 'Commanders', 'Bears', 'Lions',
            'Packers', 'Vikings', 'Falcons', 'Panthers', 'Saints', 'Buccaneers',
            '49ers', 'Cardinals', 'Rams', 'Seahawks', 'Patriots', 'Dolphins', 'Jets'
        ]

        for mascot in mascots:
            if espn_name.endswith(mascot):
                return espn_name.replace(mascot, '').strip()

        return espn_name

    def fetch_fpi_ratings(self, force_refresh: bool = False) -> Dict[str, Dict]:
        """
        Fetch FPI ratings for all NFL teams

        Returns:
            Dict mapping team name -> FPI data
            {
                'Kansas City': {
                    'fpi_rating': 7.3,
                    'fpi_offensive': 2.5,
                    'fpi_defensive': 3.8,
                    'fpi_special_teams': 1.0,
                    'fpi_sos': 0.2,
                    'fpi_remaining_sos': -0.5,
                    'fpi_avg_win_prob': 0.65,
                    'fpi_rank': 1
                },
                ...
            }
        """
        # Check cache first
        if not force_refresh:
            cached_data = self._load_cache()
            if cached_data:
                return cached_data

        logger.info("Fetching fresh ESPN FPI ratings...")

        try:
            # Fetch page with realistic headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(self.base_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the FPI table
            # ESPN uses a table with class "Table" or similar
            table = soup.find('table') or soup.find('div', class_='Table')

            if not table:
                logger.error("Could not find FPI table on ESPN page")
                return {}

            fpi_data = {}
            rank = 1

            # Parse table rows
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header row
                cells = row.find_all('td')
                if len(cells) < 8:
                    continue

                try:
                    # Extract team name (usually in first column)
                    team_cell = cells[0]
                    team_link = team_cell.find('a')
                    if team_link:
                        team_name = team_link.text.strip()
                    else:
                        team_name = team_cell.text.strip()

                    # Normalize team name to database format
                    normalized_name = self._normalize_team_name(team_name)

                    # Extract FPI metrics
                    # Column order: Rank, Team, Record, FPI, OFF, DEF, ST, SOS, REM_SOS, AVGWP
                    fpi_data[normalized_name] = {
                        'fpi_rating': self._parse_float(cells[3].text),
                        'fpi_offensive': self._parse_float(cells[4].text),
                        'fpi_defensive': self._parse_float(cells[5].text),
                        'fpi_special_teams': self._parse_float(cells[6].text),
                        'fpi_sos': self._parse_float(cells[7].text),
                        'fpi_remaining_sos': self._parse_float(cells[8].text) if len(cells) > 8 else None,
                        'fpi_avg_win_prob': self._parse_float(cells[9].text) if len(cells) > 9 else None,
                        'fpi_rank': rank
                    }

                    rank += 1

                except Exception as e:
                    logger.warning(f"Error parsing FPI row: {e}")
                    continue

            if fpi_data:
                logger.info(f"Scraped FPI ratings for {len(fpi_data)} teams")
                self._save_cache(fpi_data)
            else:
                logger.error("No FPI data scraped!")

            return fpi_data

        except Exception as e:
            logger.error(f"Error fetching ESPN FPI: {e}")
            return {}

    def _parse_float(self, text: str) -> Optional[float]:
        """Parse float from text, handling various formats"""
        try:
            # Remove any non-numeric characters except . and -
            cleaned = ''.join(c for c in text if c.isdigit() or c in '.-')
            return float(cleaned) if cleaned and cleaned != '-' else None
        except:
            return None

    def get_team_fpi(self, team_name: str) -> Optional[Dict]:
        """Get FPI ratings for a specific team"""
        all_data = self.fetch_fpi_ratings()
        return all_data.get(team_name)


if __name__ == '__main__':
    # Test the scraper
    logging.basicConfig(level=logging.INFO)

    scraper = ESPNFPINFLScraper()
    fpi_data = scraper.fetch_fpi_ratings(force_refresh=True)

    if fpi_data:
        print(f"\n✅ Successfully scraped FPI for {len(fpi_data)} teams")
        print("\nSample data (Kansas City):")
        kc_data = fpi_data.get('Kansas City', {})
        for key, value in kc_data.items():
            print(f"  {key}: {value}")

        print("\nAll teams:")
        for team in sorted(fpi_data.keys()):
            fpi = fpi_data[team].get('fpi_rating')
            rank = fpi_data[team].get('fpi_rank')
            print(f"  #{rank:2} {team:20} FPI: {fpi}")
    else:
        print("\n❌ Failed to scrape FPI data")
