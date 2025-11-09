"""
TeamRankings.com MLB Scraper - Free, reliable MLB team statistics

Scrapes:
- Runs per game (offensive)
- Runs allowed per game (defensive)
- Run differential (net rating proxy)
- Win/loss records
- Batting average
- ERA (pitching)

URL: https://www.teamrankings.com/mlb/stat/runs-per-game
"""

import requests
from bs4 import BeautifulSoup
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class TeamRankingsMLBScraper:
    """Scraper for TeamRankings.com MLB statistics"""

    BASE_URL = "https://www.teamrankings.com/mlb"

    # Cache file location
    CACHE_FILE = "backend/data/raw/mlb/teamrankings_cache.json"
    CACHE_DURATION = timedelta(hours=6)  # Refresh every 6 hours

    # Team name mapping: Full name -> TeamRankings abbreviated name
    TEAM_NAME_MAP = {
        'Arizona Diamondbacks': 'Arizona',
        'Atlanta Braves': 'Atlanta',
        'Baltimore Orioles': 'Baltimore',
        'Boston Red Sox': 'Boston',
        'Chicago Cubs': 'Chi Cubs',
        'Chicago White Sox': 'Chi White Sox',
        'Cincinnati Reds': 'Cincinnati',
        'Cleveland Guardians': 'Cleveland',
        'Cleveland Indians': 'Cleveland',  # Legacy name
        'Colorado Rockies': 'Colorado',
        'Detroit Tigers': 'Detroit',
        'Houston Astros': 'Houston',
        'Kansas City Royals': 'Kansas City',
        'Los Angeles Angels': 'LA Angels',
        'LA Angels': 'LA Angels',
        'Los Angeles Dodgers': 'LA Dodgers',
        'LA Dodgers': 'LA Dodgers',
        'Miami Marlins': 'Miami',
        'Milwaukee Brewers': 'Milwaukee',
        'Minnesota Twins': 'Minnesota',
        'New York Mets': 'NY Mets',
        'NY Mets': 'NY Mets',
        'New York Yankees': 'NY Yankees',
        'NY Yankees': 'NY Yankees',
        'Oakland Athletics': 'Oakland',
        'Philadelphia Phillies': 'Philadelphia',
        'Pittsburgh Pirates': 'Pittsburgh',
        'San Diego Padres': 'San Diego',
        'San Francisco Giants': 'San Francisco',
        'Seattle Mariners': 'Seattle',
        'St. Louis Cardinals': 'St Louis',
        'Tampa Bay Rays': 'Tampa Bay',
        'Texas Rangers': 'Texas',
        'Toronto Blue Jays': 'Toronto',
        'Washington Nationals': 'Washington',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.teamrankings.com/'
        })
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load cached data from file"""
        try:
            if os.path.exists(self.CACHE_FILE):
                with open(self.CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                    cache_time = datetime.fromisoformat(cache.get('timestamp', '2000-01-01'))
                    if datetime.now() - cache_time < self.CACHE_DURATION:
                        logger.info(f"Loaded TeamRankings MLB cache from {cache_time}")
                        return cache.get('data', {})
        except Exception as e:
            logger.warning(f"Could not load MLB cache: {e}")
        return {}

    def _save_cache(self, data: Dict):
        """Save data to cache file"""
        try:
            os.makedirs(os.path.dirname(self.CACHE_FILE), exist_ok=True)
            cache = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(cache, f, indent=2)
            logger.info(f"Saved TeamRankings MLB cache to {self.CACHE_FILE}")
        except Exception as e:
            logger.error(f"Could not save MLB cache: {e}")

    def scrape_stat_page(self, stat_name: str) -> Dict[str, float]:
        """
        Scrape a single stat page from TeamRankings

        Args:
            stat_name: URL slug (e.g., 'runs-per-game', 'opponent-runs-per-game')

        Returns:
            Dict mapping team name -> stat value
        """
        url = f"{self.BASE_URL}/stat/{stat_name}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the stats table
            table = soup.find('table', {'class': 'datatable'})
            if not table:
                logger.error(f"Could not find stats table on {url}")
                return {}

            stats = {}

            # Parse table rows (skip header)
            for row in table.find('tbody').find_all('tr'):
                cols = row.find_all('td')
                if len(cols) < 3:
                    continue

                # Column 1: Team name
                team_link = cols[1].find('a')
                if not team_link:
                    continue
                team_name = team_link.text.strip()

                # Column 2: Stat value
                stat_value = cols[2].text.strip()
                try:
                    # Handle percentage values (remove % symbol)
                    if '%' in stat_value:
                        stat_value = stat_value.replace('%', '')
                    stats[team_name] = float(stat_value)
                except ValueError:
                    logger.warning(f"Could not parse stat value: {stat_value}")

            logger.info(f"Scraped {len(stats)} teams from {stat_name}")
            return stats

        except Exception as e:
            logger.error(f"Error scraping {stat_name}: {e}")
            return {}

    def fetch_all_team_stats(self, force_refresh: bool = False) -> Dict[str, Dict]:
        """
        Fetch all MLB team statistics from TeamRankings

        Args:
            force_refresh: Bypass cache and fetch fresh data

        Returns:
            Dict mapping team name -> stats dict
            {
                'LA Dodgers': {
                    'runs_per_game': 5.2,
                    'runs_allowed': 3.8,
                    'run_diff': 1.4,
                    'wins': 95,
                    'losses': 67,
                    'batting_avg': .265,
                    'era': 3.54
                },
                ...
            }
        """
        # Check cache first
        if not force_refresh and self.cache:
            logger.info("Using cached TeamRankings MLB data")
            return self.cache

        logger.info("Fetching fresh MLB stats from TeamRankings.com...")

        # Scrape each stat page
        runs_pg = self.scrape_stat_page('runs-per-game')
        time.sleep(1)  # Be polite to server

        runs_allowed = self.scrape_stat_page('opponent-runs-per-game')
        time.sleep(1)

        run_diff = self.scrape_stat_page('average-run-differential')
        time.sleep(1)

        batting_avg = self.scrape_stat_page('batting-average')
        time.sleep(1)

        era = self.scrape_stat_page('earned-run-average')
        time.sleep(1)

        # NEW: Advanced stats for ML
        home_runs = self.scrape_stat_page('home-runs-per-game')
        time.sleep(1)

        strikeouts = self.scrape_stat_page('strikeouts-per-game')
        time.sleep(1)

        walks = self.scrape_stat_page('walks-per-game')
        time.sleep(1)

        hits = self.scrape_stat_page('hits-per-game')
        time.sleep(1)

        errors = self.scrape_stat_page('errors-per-game')
        time.sleep(1)

        # Combine all stats
        all_teams = set(runs_pg.keys()) | set(runs_allowed.keys()) | set(run_diff.keys())

        team_stats = {}
        for team in all_teams:
            team_stats[team] = {
                'team_name': team,
                # Basic stats
                'runs_per_game': runs_pg.get(team, 4.5),
                'runs_allowed': runs_allowed.get(team, 4.5),
                'run_diff': run_diff.get(team, 0.0),
                'wins': 0,  # Would need separate scraping
                'losses': 0,
                'games_played': 0,
                'win_pct': 0.0,
                'batting_avg': batting_avg.get(team, 0.250),
                'era': era.get(team, 4.00),
                # Advanced stats (NEW for ML)
                'home_runs_per_game': home_runs.get(team, 1.0),  # Power hitting
                'strikeouts_per_game': strikeouts.get(team, 8.5),  # Pitching dominance
                'walks_per_game': walks.get(team, 3.0),  # Plate discipline/control
                'hits_per_game': hits.get(team, 8.5),  # Offensive consistency
                'errors_per_game': errors.get(team, 0.5),  # Defensive quality
                # Net rating approximation (run diff is close enough)
                'net_rating': run_diff.get(team, 0.0),
                'off_rating': runs_pg.get(team, 4.5),  # Simplified
                'def_rating': runs_allowed.get(team, 4.5),  # Simplified
                'source': 'teamrankings',
                'last_updated': datetime.now().isoformat()
            }

        # Save to cache
        self._save_cache(team_stats)
        self.cache = team_stats

        logger.info(f"Fetched stats for {len(team_stats)} MLB teams from TeamRankings")
        return team_stats

    def get_team_stats(self, team_name: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get stats for a specific team

        Args:
            team_name: Full team name (e.g., 'Los Angeles Dodgers', 'Dodgers')
            force_refresh: Bypass cache

        Returns:
            Team stats dict or None if not found
        """
        all_stats = self.fetch_all_team_stats(force_refresh=force_refresh)

        # Try mapping first
        mapped_name = self.TEAM_NAME_MAP.get(team_name)
        if mapped_name and mapped_name in all_stats:
            return all_stats[mapped_name]

        # Try exact match
        if team_name in all_stats:
            return all_stats[team_name]

        # Try partial match (e.g., "Dodgers" matches "LA Dodgers")
        for full_name, stats in all_stats.items():
            if team_name.lower() in full_name.lower() or full_name.lower() in team_name.lower():
                return stats

        logger.warning(f"Team not found in TeamRankings MLB data: {team_name}")
        return None

    def refresh_cache(self):
        """Force refresh the cache"""
        logger.info("Force refreshing TeamRankings MLB cache...")
        self.fetch_all_team_stats(force_refresh=True)


# Standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    scraper = TeamRankingsMLBScraper()

    # Test: Fetch all teams
    print("\n=== Fetching All MLB Teams ===")
    all_stats = scraper.fetch_all_team_stats(force_refresh=True)
    print(f"Fetched {len(all_stats)} teams")

    # Test: Get specific team
    print("\n=== Los Angeles Dodgers ===")
    dodgers = scraper.get_team_stats("Los Angeles Dodgers")
    if dodgers:
        print(f"Runs/Game: {dodgers['runs_per_game']}")
        print(f"Runs Allowed: {dodgers['runs_allowed']}")
        print(f"Run Diff: {dodgers['run_diff']}")
        print(f"Batting Avg: {dodgers['batting_avg']:.3f}")
        print(f"ERA: {dodgers['era']:.2f}")

    # Test: Get team by partial name
    print("\n=== Yankees (partial match) ===")
    yankees = scraper.get_team_stats("Yankees")
    if yankees:
        print(f"Full name: {yankees['team_name']}")
        print(f"Runs/Game: {yankees['runs_per_game']}")
        print(f"Run Diff: {yankees['run_diff']}")
