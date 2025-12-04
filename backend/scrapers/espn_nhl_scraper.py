"""
ESPN.com NHL Scraper - NHL team statistics

Scrapes comprehensive NHL team stats from ESPN including:
- Goals per game (offensive)
- Goals allowed per game (defensive)
- Goal differential
- Power play stats
- Penalty kill stats
- Shooting percentage
- Save percentage
- Faceoff percentage

Data Source: https://www.espn.com/nhl/stats/team
"""

import requests
from bs4 import BeautifulSoup
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class ESPNNHLScraper:
    """Scraper for ESPN.com NHL statistics"""

    BASE_URL = "https://www.espn.com/nhl/stats/team"

    # Cache file location
    CACHE_DIR = Path("backend/data/raw/nhl")
    CACHE_FILE = CACHE_DIR / "espn_cache.json"
    CACHE_DURATION = timedelta(hours=6)  # Refresh every 6 hours

    # Team name mapping: Full name -> ESPN abbreviated name
    TEAM_NAME_MAP = {
        'Anaheim Ducks': 'Anaheim',
        'Arizona Coyotes': 'Arizona',
        'Utah Hockey Club': 'Utah',
        'Boston Bruins': 'Boston',
        'Buffalo Sabres': 'Buffalo',
        'Calgary Flames': 'Calgary',
        'Carolina Hurricanes': 'Carolina',
        'Chicago Blackhawks': 'Chicago',
        'Colorado Avalanche': 'Colorado',
        'Columbus Blue Jackets': 'Columbus',
        'Dallas Stars': 'Dallas',
        'Detroit Red Wings': 'Detroit',
        'Edmonton Oilers': 'Edmonton',
        'Florida Panthers': 'Florida',
        'Los Angeles Kings': 'Los Angeles',
        'LA Kings': 'Los Angeles',
        'Minnesota Wild': 'Minnesota',
        'Montréal Canadiens': 'Montreal',
        'Montreal Canadiens': 'Montreal',
        'Nashville Predators': 'Nashville',
        'New Jersey Devils': 'New Jersey',
        'New York Islanders': 'NY Islanders',
        'NY Islanders': 'NY Islanders',
        'New York Rangers': 'NY Rangers',
        'NY Rangers': 'NY Rangers',
        'Ottawa Senators': 'Ottawa',
        'Philadelphia Flyers': 'Philadelphia',
        'Pittsburgh Penguins': 'Pittsburgh',
        'San Jose Sharks': 'San Jose',
        'Seattle Kraken': 'Seattle',
        'St. Louis Blues': 'St Louis',
        'St Louis Blues': 'St Louis',
        'Tampa Bay Lightning': 'Tampa Bay',
        'Toronto Maple Leafs': 'Toronto',
        'Vancouver Canucks': 'Vancouver',
        'Vegas Golden Knights': 'Vegas',
        'Washington Capitals': 'Washington',
        'Winnipeg Jets': 'Winnipeg',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.cache = self._load_cache()

        # Ensure cache directory exists
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _load_cache(self) -> Dict:
        """Load cached data from file"""
        try:
            if self.CACHE_FILE.exists():
                with open(self.CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                    cache_time = datetime.fromisoformat(cache.get('timestamp', '2000-01-01'))
                    if datetime.now() - cache_time < self.CACHE_DURATION:
                        logger.info(f"Loaded ESPN NHL cache from {cache_time}")
                        return cache.get('data', {})
        except Exception as e:
            logger.warning(f"Could not load NHL cache: {e}")
        return {}

    def _save_cache(self, data: Dict):
        """Save data to cache file"""
        try:
            cache = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(cache, f, indent=2)
            logger.info(f"Saved ESPN NHL cache to {self.CACHE_FILE}")
        except Exception as e:
            logger.error(f"Could not save NHL cache: {e}")

    def scrape_team_stats(self, stat_category: str = "_/stat/scoring") -> Dict[str, Dict]:
        """
        Scrape team stats from ESPN for a specific category

        Categories:
        - _/stat/scoring: Goals, goals against
        - _/stat/special-teams: Power play, penalty kill
        - _/stat/miscellaneous: Shots, faceoffs, etc.
        """
        url = f"{self.BASE_URL}/{stat_category}"

        try:
            logger.info(f"Scraping {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            teams_data = {}

            # Find the stats table
            table = soup.find('table', {'class': 'Table'})
            if not table:
                logger.warning(f"No table found for {stat_category}")
                return teams_data

            # Parse header to get stat names
            headers = []
            thead = table.find('thead')
            if thead:
                for th in thead.find_all('th'):
                    headers.append(th.get_text(strip=True))

            # Parse rows
            tbody = table.find('tbody')
            if tbody:
                for row in tbody.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) < 2:
                        continue

                    # First cell is team name
                    team_name = cells[0].get_text(strip=True)

                    # Normalize team name
                    normalized_name = self._normalize_team_name(team_name)
                    if not normalized_name:
                        continue

                    # Extract stats
                    stats = {}
                    for i, cell in enumerate(cells[1:], 1):
                        if i < len(headers):
                            stat_name = headers[i].lower().replace(' ', '_')
                            try:
                                stat_value = float(cell.get_text(strip=True))
                                stats[stat_name] = stat_value
                            except ValueError:
                                stats[stat_name] = cell.get_text(strip=True)

                    teams_data[normalized_name] = stats

            logger.info(f"Scraped stats for {len(teams_data)} teams from {stat_category}")
            return teams_data

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {}

    def _normalize_team_name(self, team_name: str) -> Optional[str]:
        """Normalize team name to match our standard format"""
        # Remove rank numbers and extra spaces
        team_name = team_name.strip()
        for rank_str in [str(i) for i in range(1, 33)]:
            if team_name.startswith(rank_str):
                team_name = team_name[len(rank_str):].strip()
                break

        # Check direct mapping
        for full_name, short_name in self.TEAM_NAME_MAP.items():
            if team_name.lower() in full_name.lower() or full_name.lower() in team_name.lower():
                return full_name

        return team_name if team_name else None

    def fetch_all_stats(self) -> Dict[str, Dict]:
        """Fetch all NHL team statistics from ESPN"""

        # Check cache first
        if self.cache:
            logger.info("Using cached NHL data")
            return self.cache

        logger.info("Fetching fresh NHL data from ESPN")
        all_teams = {}

        # Scrape different stat categories
        categories = {
            '_/stat/scoring': ['goals_per_game', 'goals_against', 'goal_differential'],
            '_/stat/special-teams': ['power_play_pct', 'penalty_kill_pct'],
            '_/stat/miscellaneous': ['shots_per_game', 'shooting_pct', 'save_pct', 'faceoff_win_pct']
        }

        for category, expected_stats in categories.items():
            time.sleep(1)  # Rate limiting
            stats = self.scrape_team_stats(category)

            # Merge stats into all_teams
            for team, team_stats in stats.items():
                if team not in all_teams:
                    all_teams[team] = {}
                all_teams[team].update(team_stats)

        # Save to cache
        if all_teams:
            self._save_cache(all_teams)

        logger.info(f"Fetched stats for {len(all_teams)} NHL teams from ESPN")
        return all_teams

    def get_team_stats(self, team_name: str) -> Optional[Dict]:
        """Get stats for a specific team"""
        all_stats = self.fetch_all_stats()

        # Try exact match first
        if team_name in all_stats:
            return all_stats[team_name]

        # Try normalized matching
        for cached_team, stats in all_stats.items():
            if team_name.lower() in cached_team.lower() or cached_team.lower() in team_name.lower():
                return stats

        logger.warning(f"No stats found for team: {team_name}")
        return None


if __name__ == "__main__":
    # Test the scraper
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    scraper = ESPNNHLScraper()
    stats = scraper.fetch_all_stats()

    print(f"\nScraped stats for {len(stats)} teams:")
    for team, team_stats in list(stats.items())[:3]:
        print(f"\n{team}:")
        for stat, value in team_stats.items():
            print(f"  {stat}: {value}")
