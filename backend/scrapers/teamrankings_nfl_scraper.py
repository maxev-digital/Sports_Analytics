"""
TeamRankings.com NFL Scraper - Free, reliable NFL team statistics

Scrapes:
- Points per game (offensive)
- Points allowed per game (defensive)
- Point differential (net rating proxy)
- Win/loss records
- Total yards, yards allowed
- Turnovers, turnover differential

URL: https://www.teamrankings.com/nfl/stat/points-per-game
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

class TeamRankingsNFLScraper:
    """Scraper for TeamRankings.com NFL statistics"""

    BASE_URL = "https://www.teamrankings.com/nfl"

    # Cache file location
    CACHE_FILE = "backend/data/raw/nfl/teamrankings_cache.json"
    CACHE_DURATION = timedelta(hours=6)  # Refresh every 6 hours

    # Team name mapping: Full name -> TeamRankings abbreviated name
    TEAM_NAME_MAP = {
        'Arizona Cardinals': 'Arizona',
        'Atlanta Falcons': 'Atlanta',
        'Baltimore Ravens': 'Baltimore',
        'Buffalo Bills': 'Buffalo',
        'Carolina Panthers': 'Carolina',
        'Chicago Bears': 'Chicago',
        'Cincinnati Bengals': 'Cincinnati',
        'Cleveland Browns': 'Cleveland',
        'Dallas Cowboys': 'Dallas',
        'Denver Broncos': 'Denver',
        'Detroit Lions': 'Detroit',
        'Green Bay Packers': 'Green Bay',
        'Houston Texans': 'Houston',
        'Indianapolis Colts': 'Indianapolis',
        'Jacksonville Jaguars': 'Jacksonville',
        'Kansas City Chiefs': 'Kansas City',
        'Las Vegas Raiders': 'Las Vegas',
        'LA Raiders': 'Las Vegas',
        'Los Angeles Chargers': 'LA Chargers',
        'LA Chargers': 'LA Chargers',
        'Los Angeles Rams': 'LA Rams',
        'LA Rams': 'LA Rams',
        'Miami Dolphins': 'Miami',
        'Minnesota Vikings': 'Minnesota',
        'New England Patriots': 'New England',
        'New Orleans Saints': 'New Orleans',
        'New York Giants': 'NY Giants',
        'NY Giants': 'NY Giants',
        'New York Jets': 'NY Jets',
        'NY Jets': 'NY Jets',
        'Philadelphia Eagles': 'Philadelphia',
        'Pittsburgh Steelers': 'Pittsburgh',
        'San Francisco 49ers': 'San Francisco',
        'Seattle Seahawks': 'Seattle',
        'Tampa Bay Buccaneers': 'Tampa Bay',
        'Tennessee Titans': 'Tennessee',
        'Washington Commanders': 'Washington',
        'Washington Football Team': 'Washington',  # Legacy name
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
                        logger.info(f"Loaded TeamRankings NFL cache from {cache_time}")
                        return cache.get('data', {})
        except Exception as e:
            logger.warning(f"Could not load NFL cache: {e}")
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
            logger.info(f"Saved TeamRankings NFL cache to {self.CACHE_FILE}")
        except Exception as e:
            logger.error(f"Could not save NFL cache: {e}")

    def scrape_stat_page(self, stat_name: str) -> Dict[str, float]:
        """
        Scrape a single stat page from TeamRankings

        Args:
            stat_name: URL slug (e.g., 'points-per-game', 'opponent-points-per-game')

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

    def scrape_standings(self) -> Dict[str, Dict]:
        """
        Scrape NFL standings page for W-L records

        Returns:
            Dict mapping team name -> {'wins': int, 'losses': int}
        """
        try:
            import re
            url = f"{self.BASE_URL}/standings/"
            logger.info(f"Scraping standings from {url}")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find ALL standings tables (class 'tr-table') - one per division
            tables = soup.find_all('table', {'class': 'tr-table'})
            if not tables:
                logger.error("Could not find standings tables")
                return {}

            records = {}

            # Parse each table (AFC East, AFC West, NFC East, etc.)
            for table in tables:
                tbody = table.find('tbody') if table.find('tbody') else table
                for row in tbody.find_all('tr'):
                    cols = row.find_all('td')
                    if len(cols) < 2:
                        continue

                    # Get all text from the row to find team name and record
                    row_text = ' '.join([c.text.strip() for c in cols])

                    # Skip division headers
                    if any(div in row_text for div in ['AFC East', 'AFC West', 'AFC North', 'AFC South', 'NFC East', 'NFC West', 'NFC North', 'NFC South']):
                        continue

                    # Extract team name (first column)
                    team_name = cols[0].text.strip()
                    if not team_name:
                        continue

                    # Find W-L record in format "8-2" or "10-1" anywhere in the row
                    record_match = re.search(r'(\d+)-(\d+)', row_text)
                    if record_match:
                        wins = int(record_match.group(1))
                        losses = int(record_match.group(2))
                        records[team_name] = {'wins': wins, 'losses': losses}

            logger.info(f"Scraped records for {len(records)} teams from standings")
            return records

        except Exception as e:
            logger.error(f"Error scraping standings: {e}")
            return {}

    def fetch_all_team_stats(self, force_refresh: bool = False) -> Dict[str, Dict]:
        """
        Fetch all NFL team statistics from TeamRankings

        Args:
            force_refresh: Bypass cache and fetch fresh data

        Returns:
            Dict mapping team name -> stats dict
            {
                'Kansas City': {
                    'pts_per_game': 28.5,
                    'pts_allowed': 19.2,
                    'point_diff': 9.3,
                    'wins': 9,
                    'losses': 1,
                    'yards_per_game': 385.2,
                    'yards_allowed': 312.5,
                    'turnover_diff': 8
                },
                ...
            }
        """
        # Check cache first
        if not force_refresh and self.cache:
            logger.info("Using cached TeamRankings NFL data")
            return self.cache

        logger.info("Fetching fresh NFL stats from TeamRankings.com...")

        # Scrape each stat page
        ppg = self.scrape_stat_page('points-per-game')
        time.sleep(1)  # Be polite to server

        opp_ppg = self.scrape_stat_page('opponent-points-per-game')
        time.sleep(1)

        point_diff = self.scrape_stat_page('average-scoring-margin')
        time.sleep(1)

        yards_per_game = self.scrape_stat_page('yards-per-game')
        time.sleep(1)

        yards_allowed = self.scrape_stat_page('opponent-yards-per-game')
        time.sleep(1)

        turnovers_lost = self.scrape_stat_page('turnovers-lost-per-game')
        time.sleep(1)

        turnovers_gained = self.scrape_stat_page('takeaways-per-game')
        time.sleep(1)

        # Get W-L records from standings page (wins/losses pages don't exist)
        records = self.scrape_standings()
        wins = {team: record['wins'] for team, record in records.items()}
        losses = {team: record['losses'] for team, record in records.items()}
        time.sleep(1)

        # NEW: Advanced stats for ML
        third_down_pct = self.scrape_stat_page('third-down-conversion-pct')
        time.sleep(1)

        opp_third_down_pct = self.scrape_stat_page('opponent-third-down-conversion-pct')
        time.sleep(1)

        red_zone_pct = self.scrape_stat_page('red-zone-scoring-pct')
        time.sleep(1)

        opp_red_zone_pct = self.scrape_stat_page('opponent-red-zone-scoring-pct')
        time.sleep(1)

        passing_yards = self.scrape_stat_page('passing-yards-per-game')
        time.sleep(1)

        rushing_yards = self.scrape_stat_page('rushing-yards-per-game')
        time.sleep(1)

        opp_passing_yards = self.scrape_stat_page('opponent-passing-yards-per-game')
        time.sleep(1)

        opp_rushing_yards = self.scrape_stat_page('opponent-rushing-yards-per-game')
        time.sleep(1)

        sacks = self.scrape_stat_page('sacks-per-game')
        time.sleep(1)

        penalties = self.scrape_stat_page('penalties-per-game')
        time.sleep(1)

        first_downs = self.scrape_stat_page('first-downs-per-game')
        time.sleep(1)

        # Combine all stats
        all_teams = set(ppg.keys()) | set(opp_ppg.keys()) | set(point_diff.keys())

        team_stats = {}
        for team in all_teams:
            w = wins.get(team, 0)
            l = losses.get(team, 0)
            games_played = w + l

            turnovers_l = turnovers_lost.get(team, 0)
            turnovers_g = turnovers_gained.get(team, 0)
            turnover_diff = turnovers_g - turnovers_l

            team_stats[team] = {
                'team_name': team,
                # Basic stats
                'pts_per_game': ppg.get(team, 20.0),
                'pts_allowed': opp_ppg.get(team, 20.0),
                'point_diff': point_diff.get(team, 0.0),
                'wins': int(w),
                'losses': int(l),
                'games_played': int(games_played),
                'win_pct': round(w / games_played, 3) if games_played > 0 else 0.0,
                'yards_per_game': yards_per_game.get(team, 320.0),
                'yards_allowed': yards_allowed.get(team, 320.0),
                'turnovers_lost': turnovers_l,
                'turnovers_gained': turnovers_g,
                'turnover_diff': turnover_diff,
                # Advanced stats (NEW for ML)
                'third_down_conversion_pct': third_down_pct.get(team, 40.0),  # CRITICAL for drives
                'opponent_third_down_conversion_pct': opp_third_down_pct.get(team, 40.0),
                'red_zone_scoring_pct': red_zone_pct.get(team, 55.0),  # CRITICAL for scoring
                'opponent_red_zone_scoring_pct': opp_red_zone_pct.get(team, 55.0),
                'passing_yards_per_game': passing_yards.get(team, 220.0),
                'rushing_yards_per_game': rushing_yards.get(team, 100.0),
                'opponent_passing_yards_per_game': opp_passing_yards.get(team, 220.0),
                'opponent_rushing_yards_per_game': opp_rushing_yards.get(team, 100.0),
                'sacks_per_game': sacks.get(team, 2.5),
                'penalties_per_game': penalties.get(team, 6.0),
                'first_downs_per_game': first_downs.get(team, 20.0),
                # Net rating approximation (point diff is close enough)
                'net_rating': point_diff.get(team, 0.0),
                'off_rating': ppg.get(team, 20.0),  # Simplified
                'def_rating': opp_ppg.get(team, 20.0),  # Simplified
                'source': 'teamrankings',
                'last_updated': datetime.now().isoformat()
            }

        # Save to cache
        self._save_cache(team_stats)
        self.cache = team_stats

        logger.info(f"Fetched stats for {len(team_stats)} NFL teams from TeamRankings")
        return team_stats

    def get_team_stats(self, team_name: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get stats for a specific team

        Args:
            team_name: Full team name (e.g., 'Kansas City Chiefs', 'Chiefs')
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

        # Try partial match (e.g., "Chiefs" matches "Kansas City")
        for full_name, stats in all_stats.items():
            if team_name.lower() in full_name.lower() or full_name.lower() in team_name.lower():
                return stats

        logger.warning(f"Team not found in TeamRankings NFL data: {team_name}")
        return None

    def refresh_cache(self):
        """Force refresh the cache"""
        logger.info("Force refreshing TeamRankings NFL cache...")
        self.fetch_all_team_stats(force_refresh=True)


# Standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    scraper = TeamRankingsNFLScraper()

    # Test: Fetch all teams
    print("\n=== Fetching All NFL Teams ===")
    all_stats = scraper.fetch_all_team_stats(force_refresh=True)
    print(f"Fetched {len(all_stats)} teams")

    # Test: Get specific team
    print("\n=== Kansas City Chiefs ===")
    chiefs = scraper.get_team_stats("Kansas City Chiefs")
    if chiefs:
        print(f"PPG: {chiefs['pts_per_game']}")
        print(f"Opp PPG: {chiefs['pts_allowed']}")
        print(f"Point Diff: {chiefs['point_diff']}")
        print(f"Record: {chiefs['wins']}-{chiefs['losses']}")
        print(f"Win %: {chiefs['win_pct']:.1%}")
        print(f"Yards/Game: {chiefs['yards_per_game']}")
        print(f"Turnover Diff: {chiefs['turnover_diff']:+.1f}")

    # Test: Get team by partial name
    print("\n=== Cowboys (partial match) ===")
    cowboys = scraper.get_team_stats("Cowboys")
    if cowboys:
        print(f"Full name: {cowboys['team_name']}")
        print(f"PPG: {cowboys['pts_per_game']}")
        print(f"Point Diff: {cowboys['point_diff']}")
