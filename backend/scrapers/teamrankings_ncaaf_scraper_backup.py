"""
TeamRankings.com NCAAF Scraper - Free, reliable college football team statistics

Scrapes:
- Points per game (offensive)
- Points allowed per game (defensive)
- Point differential (net rating proxy)
- Win/loss records
- Total yards, yards allowed
- Turnovers

URL: https://www.teamrankings.com/college-football/stat/points-per-game
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

class TeamRankingsNCAAFScraper:
    """Scraper for TeamRankings.com NCAAF (College Football) statistics"""

    BASE_URL = "https://www.teamrankings.com/college-football"

    # Cache file location
    CACHE_FILE = "backend/data/raw/ncaaf/teamrankings_cache.json"
    CACHE_DURATION = timedelta(hours=6)  # Refresh every 6 hours

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
                        logger.info(f"Loaded TeamRankings NCAAF cache from {cache_time}")
                        return cache.get('data', {})
        except Exception as e:
            logger.warning(f"Could not load NCAAF cache: {e}")
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
            logger.info(f"Saved TeamRankings NCAAF cache to {self.CACHE_FILE}")
        except Exception as e:
            logger.error(f"Could not save NCAAF cache: {e}")

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
        Scrape NCAAF standings page for W-L records

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

            # Find ALL standings tables (class 'tr-table') - one per conference
            tables = soup.find_all('table', {'class': 'tr-table'})
            if not tables:
                logger.error("Could not find standings tables")
                return {}

            records = {}

            # Parse each table (conferences)
            # Each table may have multiple tbody elements
            for table in tables:
                tbody_elements = table.find_all('tbody')

                # Process each tbody (could be multiple per conference table)
                for tbody in tbody_elements:
                    for row in tbody.find_all('tr'):
                        cols = row.find_all('td')
                        if len(cols) < 3:
                            continue

                        # Get all text from the row
                        row_text = ' '.join([c.text.strip() for c in cols])

                        # Skip conference headers
                        if 'Conference' in row_text:
                            continue

                        # Extract team name from column 2
                        # Column 0 is ranking, column 1 is a stat, column 2 is team name
                        # Structure: <div class="table-team-logo-text"><a>Team Name</a><small>(record)</small></div>
                        text_wrapper = cols[2].find('div', {'class': 'table-team-logo-text'})
                        if not text_wrapper:
                            logger.debug(f"No text wrapper found in column 2")
                            continue

                        team_link = text_wrapper.find('a')
                        if not team_link:
                            logger.debug(f"No link found in text wrapper")
                            continue

                        team_name = team_link.text.strip()
                        if not team_name:
                            logger.debug(f"Empty team name from link")
                            continue

                        # Find W-L record in format "9-0" or "10-2" anywhere in the row
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

    def scrape_ats_trends(self) -> Dict[str, Dict]:
        """
        Scrape ATS (Against The Spread) trends from TeamRankings
        Scrapes overall ATS records (no home/away splits to avoid complications)

        Returns:
            Dict mapping team name -> ATS data:
            {
                'Alabama': {
                    'ats_wins': 8,
                    'ats_losses': 2,
                    'ats_pushes': 0
                },
                ...
            }
        """
        # Scrape overall ATS only (no home/away splits)
        ats_data = self._scrape_ats_page(f"{self.BASE_URL}/trends/ats_trends/", 'overall')
        logger.info(f"Scraped ATS trends for {len(ats_data)} NCAAF teams")
        return ats_data

    def _scrape_ats_page(self, url: str, record_type: str) -> Dict[str, Dict]:
        """Helper to scrape a single ATS page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the stats table
            table = soup.find('table', {'class': 'datatable'})
            if not table:
                logger.error(f"Could not find ATS trends table on {url}")
                return {}

            ats_data = {}

            # Parse table rows (skip header)
            for row in table.find('tbody').find_all('tr'):
                cols = row.find_all('td')
                if len(cols) < 2:
                    continue

                # Column 0: Team name
                team_link = cols[0].find('a')
                if not team_link:
                    continue
                team_name = team_link.text.strip()

                # Column 1: ATS Record (format: "W-L-P")
                ats_record = cols[1].text.strip()
                try:
                    parts = ats_record.split('-')
                    if len(parts) == 3:
                        ats_data[team_name] = {
                            'ats_wins': int(parts[0]),
                            'ats_losses': int(parts[1]),
                            'ats_pushes': int(parts[2])
                        }
                except (ValueError, IndexError) as e:
                    logger.warning(f"Could not parse {record_type} ATS record for {team_name}: {ats_record}")

            logger.info(f"Scraped {record_type} ATS trends for {len(ats_data)} teams")
            return ats_data

        except Exception as e:
            logger.error(f"Error scraping {record_type} ATS trends: {e}")
            return {}

    def scrape_ou_trends(self) -> Dict[str, Dict]:
        """
        Scrape O/U (Over/Under) trends from TeamRankings
        Scrapes overall O/U records (no home/away splits to avoid complications)

        Returns:
            Dict mapping team name -> O/U data:
            {
                'Alabama': {
                    'ou_overs': 7,
                    'ou_unders': 3,
                    'ou_pushes': 0
                },
                ...
            }
        """
        # Scrape overall O/U only (no home/away splits)
        ou_data = self._scrape_ou_page(f"{self.BASE_URL}/trends/ou_trends/", 'overall')
        logger.info(f"Scraped O/U trends for {len(ou_data)} NCAAF teams")
        return ou_data

    def _scrape_ou_page(self, url: str, record_type: str) -> Dict[str, Dict]:
        """Helper to scrape a single O/U page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the stats table
            table = soup.find('table', {'class': 'datatable'})
            if not table:
                logger.error(f"Could not find O/U trends table on {url}")
                return {}

            ou_data = {}

            # Parse table rows (skip header)
            for row in table.find('tbody').find_all('tr'):
                cols = row.find_all('td')
                if len(cols) < 2:
                    continue

                # Column 0: Team name
                team_link = cols[0].find('a')
                if not team_link:
                    continue
                team_name = team_link.text.strip()

                # Column 1: O/U Record (format: "O-U-P")
                ou_record = cols[1].text.strip()
                try:
                    parts = ou_record.split('-')
                    if len(parts) == 3:
                        ou_data[team_name] = {
                            'ou_overs': int(parts[0]),
                            'ou_unders': int(parts[1]),
                            'ou_pushes': int(parts[2])
                        }
                except (ValueError, IndexError) as e:
                    logger.warning(f"Could not parse {record_type} O/U record for {team_name}: {ou_record}")

            logger.info(f"Scraped {record_type} O/U trends for {len(ou_data)} teams")
            return ou_data

        except Exception as e:
            logger.error(f"Error scraping {record_type} O/U trends: {e}")
            return {}

    def fetch_all_team_stats(self, force_refresh: bool = False) -> Dict[str, Dict]:
        """
        Fetch all NCAAF team statistics from TeamRankings

        Args:
            force_refresh: Bypass cache and fetch fresh data

        Returns:
            Dict mapping team name -> stats dict
            {
                'Alabama': {
                    'pts_per_game': 35.2,
                    'pts_allowed': 18.5,
                    'point_diff': 16.7,
                    'wins': 10,
                    'losses': 2,
                    'yards_per_game': 425.8,
                    'yards_allowed': 298.3,
                    'ats_wins': 8,
                    'ats_losses': 2,
                    'ats_pushes': 0,
                    'ou_overs': 7,
                    'ou_unders': 3,
                    'ou_pushes': 0
                },
                ...
            }
        """
        # Check cache first
        if not force_refresh and self.cache:
            logger.info("Using cached TeamRankings NCAAF data")
            return self.cache

        logger.info("Fetching fresh NCAAF stats from TeamRankings.com...")

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

        # NEW: Advanced stats for ML
        third_down_pct = self.scrape_stat_page('third-down-conversion-pct')
        time.sleep(1)

        red_zone_pct = self.scrape_stat_page('red-zone-scoring-pct')
        time.sleep(1)

        passing_yards = self.scrape_stat_page('passing-yards-per-game')
        time.sleep(1)

        rushing_yards = self.scrape_stat_page('rushing-yards-per-game')
        time.sleep(1)

        sacks = self.scrape_stat_page('sacks-per-game')
        time.sleep(1)

        takeaways = self.scrape_stat_page('takeaways-per-game')
        time.sleep(1)

        # Get W-L records from standings page
        records = self.scrape_standings()
        time.sleep(1)

        # NEW: Scrape betting trends (ATS and O/U)
        ats_trends = self.scrape_ats_trends()
        time.sleep(1)

        ou_trends = self.scrape_ou_trends()
        time.sleep(1)

        # Combine all stats
        all_teams = set(ppg.keys()) | set(opp_ppg.keys()) | set(point_diff.keys())

        team_stats = {}
        for team in all_teams:
            # Get W-L record for this team
            w = records.get(team, {}).get('wins', 0)
            l = records.get(team, {}).get('losses', 0)
            games_played = w + l

            # Get betting trends for this team
            ats_data = ats_trends.get(team, {})
            ou_data = ou_trends.get(team, {})

            team_stats[team] = {
                'team_name': team,
                # Basic stats
                'pts_per_game': ppg.get(team, 25.0),
                'pts_allowed': opp_ppg.get(team, 25.0),
                'point_diff': point_diff.get(team, 0.0),
                'wins': int(w),
                'losses': int(l),
                'games_played': int(games_played),
                'win_pct': round(w / games_played, 3) if games_played > 0 else 0.0,
                'yards_per_game': yards_per_game.get(team, 350.0),
                'yards_allowed': yards_allowed.get(team, 350.0),
                # Advanced stats (NEW for ML)
                'third_down_conversion_pct': third_down_pct.get(team, 40.0),  # Drive efficiency
                'red_zone_scoring_pct': red_zone_pct.get(team, 55.0),  # RZ efficiency
                'passing_yards_per_game': passing_yards.get(team, 220.0),
                'rushing_yards_per_game': rushing_yards.get(team, 130.0),
                'sacks_per_game': sacks.get(team, 2.0),
                'takeaways_per_game': takeaways.get(team, 1.5),
                # Net rating approximation (point diff is close enough)
                'net_rating': point_diff.get(team, 0.0),
                'off_rating': ppg.get(team, 25.0),  # Simplified
                'def_rating': opp_ppg.get(team, 25.0),  # Simplified
                # Betting trends (NEW)
                'ats_wins': ats_data.get('ats_wins'),
                'ats_losses': ats_data.get('ats_losses'),
                'ats_pushes': ats_data.get('ats_pushes'),
                'ou_overs': ou_data.get('ou_overs'),
                'ou_unders': ou_data.get('ou_unders'),
                'ou_pushes': ou_data.get('ou_pushes'),
                'source': 'teamrankings',
                'last_updated': datetime.now().isoformat()
            }

        # Calculate rankings for each stat
        self._calculate_rankings(team_stats)

        # Save to cache
        self._save_cache(team_stats)
        self.cache = team_stats

        logger.info(f"Fetched stats for {len(team_stats)} NCAAF teams from TeamRankings")
        return team_stats

    def _calculate_rankings(self, team_stats: Dict[str, Dict]):
        """
        Calculate rankings for all stats

        Higher is better (rank 1 = best):
        - points_per_game (offensive)
        - passing_yards_per_game
        - rushing_yards_per_game
        - third_down_conversion_pct
        - red_zone_scoring_pct
        - sacks_per_game
        - takeaways_per_game

        Lower is better (rank 1 = best):
        - points_allowed_per_game (defensive)
        - yards_allowed_per_game
        """
        if not team_stats:
            return

        # Offensive stats (higher is better)
        offensive_stats = [
            ('pts_per_game', 'points_per_game_rank'),
            ('passing_yards_per_game', 'passing_yards_per_game_rank'),
            ('rushing_yards_per_game', 'rushing_yards_per_game_rank'),
            ('third_down_conversion_pct', 'third_down_pct_rank'),
            ('red_zone_scoring_pct', 'red_zone_pct_rank'),
            ('sacks_per_game', 'sacks_rank'),
            ('takeaways_per_game', 'takeaways_rank'),
            ('yards_per_game', 'total_yards_per_game_rank'),
        ]

        # Defensive stats (lower is better)
        defensive_stats = [
            ('pts_allowed', 'points_allowed_per_game_rank'),
            ('yards_allowed', 'yards_allowed_per_game_rank'),
        ]

        # Calculate ranks for offensive stats (higher = better)
        for stat_key, rank_key in offensive_stats:
            teams_with_stat = [(team, stats[stat_key]) for team, stats in team_stats.items() if stat_key in stats]
            # Sort descending (highest value = rank 1)
            teams_with_stat.sort(key=lambda x: x[1], reverse=True)
            for rank, (team, _) in enumerate(teams_with_stat, start=1):
                team_stats[team][rank_key] = rank

        # Calculate ranks for defensive stats (lower = better)
        for stat_key, rank_key in defensive_stats:
            teams_with_stat = [(team, stats[stat_key]) for team, stats in team_stats.items() if stat_key in stats]
            # Sort ascending (lowest value = rank 1)
            teams_with_stat.sort(key=lambda x: x[1])
            for rank, (team, _) in enumerate(teams_with_stat, start=1):
                team_stats[team][rank_key] = rank

        logger.info(f"Calculated rankings for {len(team_stats)} NCAAF teams")

    def get_team_stats(self, team_name: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get stats for a specific team

        Args:
            team_name: Full team name (e.g., 'Alabama Crimson Tide', 'Ohio State Buckeyes')
            force_refresh: Bypass cache

        Returns:
            Team stats dict or None if not found
        """
        all_stats = self.fetch_all_team_stats(force_refresh=force_refresh)

        # Try exact match
        if team_name in all_stats:
            return all_stats[team_name]

        # Try fuzzy match - find best match by counting matching words
        # This handles cases like "Ohio State Buckeyes" -> "Ohio St"
        team_name_lower = team_name.lower()
        team_words = set(team_name_lower.split())

        # Handle common abbreviations
        if 'state' in team_words:
            team_words.add('st')
        if 'st' in team_words:
            team_words.add('state')

        best_match = None
        best_score = 0
        best_name = None

        for full_name, stats in all_stats.items():
            full_name_lower = full_name.lower()
            full_words = set(full_name_lower.split())

            # Handle abbreviations in scraped data too
            if 'st' in full_words:
                full_words.add('state')

            # Calculate match score (number of common words)
            common_words = team_words & full_words
            score = len(common_words)

            # Bonus for matching more words from the TeamRankings name
            # Prefer "Ohio St" (2 words matched) over "Ohio" (1 word matched)
            teamrankings_words = set(full_name_lower.split())
            score += len(common_words & teamrankings_words) * 0.1

            # Bonus for exact substring match
            if full_name_lower in team_name_lower:
                score += 0.5

            if score > best_score:
                best_score = score
                best_match = stats
                best_name = full_name

        # Only return if we have a reasonable match (at least 1 word in common)
        if best_match and best_score >= 1:
            logger.debug(f"Matched '{team_name}' -> '{best_name}' (score: {best_score:.2f})")
            return best_match

        logger.warning(f"Team not found in TeamRankings NCAAF data: {team_name}")
        return None

    def refresh_cache(self):
        """Force refresh the cache"""
        logger.info("Force refreshing TeamRankings NCAAF cache...")
        self.fetch_all_team_stats(force_refresh=True)


# Standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    scraper = TeamRankingsNCAAFScraper()

    # Test: Fetch all teams
    print("\n=== Fetching All NCAAF Teams ===")
    all_stats = scraper.fetch_all_team_stats(force_refresh=True)
    print(f"Fetched {len(all_stats)} teams")

    # Test: Get specific team
    print("\n=== Alabama ===")
    bama = scraper.get_team_stats("Alabama")
    if bama:
        print(f"PPG: {bama['pts_per_game']}")
        print(f"Opp PPG: {bama['pts_allowed']}")
        print(f"Point Diff: {bama['point_diff']}")
        print(f"Yards/Game: {bama['yards_per_game']}")

    # Test: Get another team
    print("\n=== Ohio State ===")
    osu = scraper.get_team_stats("Ohio State")
    if osu:
        print(f"PPG: {osu['pts_per_game']}")
        print(f"Point Diff: {osu['point_diff']}")
