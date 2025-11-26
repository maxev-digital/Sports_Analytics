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

            # Parse each table (AFC and NFC conferences)
            # Each table has 4 tbody elements (one per division)
            for table in tables:
                tbody_elements = table.find_all('tbody')

                # Process each division's tbody
                for tbody in tbody_elements:
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

    def scrape_ats_trends(self) -> Dict[str, Dict]:
        """
        Scrape ATS (Against The Spread) trends from TeamRankings
        Scrapes overall, home, and away ATS records from separate pages

        Returns:
            Dict mapping team name -> ATS data:
            {
                'Buffalo': {
                    'ats_wins': 8,
                    'ats_losses': 2,
                    'ats_pushes': 0,
                    'home_ats_wins': 5,
                    'home_ats_losses': 1,
                    'home_ats_pushes': 0,
                    'away_ats_wins': 3,
                    'away_ats_losses': 1,
                    'away_ats_pushes': 0
                },
                ...
            }
        """
        # Scrape overall ATS
        ats_data = self._scrape_ats_page(f"{self.BASE_URL}/trends/ats_trends/", 'overall')

        # Scrape home ATS
        time.sleep(1)
        home_ats = self._scrape_ats_page(f"{self.BASE_URL}/trends/ats_trends/?sc=is_home", 'home')

        # Scrape away ATS
        time.sleep(1)
        away_ats = self._scrape_ats_page(f"{self.BASE_URL}/trends/ats_trends/?sc=is_away", 'away')

        # Merge home/away data into overall
        for team, data in ats_data.items():
            if team in home_ats:
                data['home_ats_wins'] = home_ats[team]['ats_wins']
                data['home_ats_losses'] = home_ats[team]['ats_losses']
                data['home_ats_pushes'] = home_ats[team]['ats_pushes']
            if team in away_ats:
                data['away_ats_wins'] = away_ats[team]['ats_wins']
                data['away_ats_losses'] = away_ats[team]['ats_losses']
                data['away_ats_pushes'] = away_ats[team]['ats_pushes']

        logger.info(f"Scraped ATS trends (overall + home/away) for {len(ats_data)} teams")
        return ats_data

    def _scrape_ats_page(self, url: str, record_type: str) -> Dict[str, Dict]:
        """Helper to scrape a single ATS page (overall, home, or away)"""
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
        Scrapes overall, home, and away O/U records from separate pages

        Returns:
            Dict mapping team name -> O/U data:
            {
                'Buffalo': {
                    'ou_overs': 7,
                    'ou_unders': 3,
                    'ou_pushes': 0,
                    'home_ou_overs': 4,
                    'home_ou_unders': 2,
                    'home_ou_pushes': 0,
                    'away_ou_overs': 3,
                    'away_ou_unders': 1,
                    'away_ou_pushes': 0
                },
                ...
            }
        """
        # Scrape overall O/U
        ou_data = self._scrape_ou_page(f"{self.BASE_URL}/trends/ou_trends/", 'overall')

        # Scrape home O/U
        time.sleep(1)
        home_ou = self._scrape_ou_page(f"{self.BASE_URL}/trends/ou_trends/?sc=is_home", 'home')

        # Scrape away O/U
        time.sleep(1)
        away_ou = self._scrape_ou_page(f"{self.BASE_URL}/trends/ou_trends/?sc=is_away", 'away')

        # Merge home/away data into overall
        for team, data in ou_data.items():
            if team in home_ou:
                data['home_ou_overs'] = home_ou[team]['ou_overs']
                data['home_ou_unders'] = home_ou[team]['ou_unders']
                data['home_ou_pushes'] = home_ou[team]['ou_pushes']
            if team in away_ou:
                data['away_ou_overs'] = away_ou[team]['ou_overs']
                data['away_ou_unders'] = away_ou[team]['ou_unders']
                data['away_ou_pushes'] = away_ou[team]['ou_pushes']

        logger.info(f"Scraped O/U trends (overall + home/away) for {len(ou_data)} teams")
        return ou_data

    def _scrape_ou_page(self, url: str, record_type: str) -> Dict[str, Dict]:
        """Helper to scrape a single O/U page (overall, home, or away)"""
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

        # === NEW: PHASE 1 - EFFICIENCY METRICS (6 stats) ===
        yards_per_play = self.scrape_stat_page('yards-per-play')
        time.sleep(1)

        opp_yards_per_play = self.scrape_stat_page('opponent-yards-per-play')
        time.sleep(1)

        completion_pct = self.scrape_stat_page('completion-pct')
        time.sleep(1)

        opp_completion_pct = self.scrape_stat_page('opponent-completion-pct')
        time.sleep(1)

        fourth_down_pct = self.scrape_stat_page('fourth-down-conversion-pct')
        time.sleep(1)

        opp_fourth_down_pct = self.scrape_stat_page('opponent-fourth-down-conversion-pct')
        time.sleep(1)

        # === NEW: PHASE 2 - TURNOVERS & SCORING (5 stats) ===
        interceptions_caught = self.scrape_stat_page('interceptions-per-game')
        time.sleep(1)

        interceptions_thrown = self.scrape_stat_page('interceptions-thrown-per-game')
        time.sleep(1)

        fumbles_lost = self.scrape_stat_page('fumbles-lost-per-game')
        time.sleep(1)

        offensive_tds = self.scrape_stat_page('offensive-touchdowns-per-game')
        time.sleep(1)

        defensive_tds = self.scrape_stat_page('defensive-touchdowns-per-game')
        time.sleep(1)

        # === NEW: PHASE 3 - PASSING DETAILS (6 stats) ===
        pass_attempts = self.scrape_stat_page('pass-attempts-per-game')
        time.sleep(1)

        opp_pass_attempts = self.scrape_stat_page('opponent-pass-attempts-per-game')
        time.sleep(1)

        passing_tds = self.scrape_stat_page('passing-touchdowns-per-game')
        time.sleep(1)

        opp_passing_tds = self.scrape_stat_page('opponent-passing-touchdowns-per-game')
        time.sleep(1)

        qb_sacked = self.scrape_stat_page('qb-sacked-per-game')
        time.sleep(1)

        touchdowns_total = self.scrape_stat_page('touchdowns-per-game')
        time.sleep(1)

        # === NEW: PHASE 4 - RUSHING DETAILS (4 stats) ===
        rush_attempts = self.scrape_stat_page('rushing-attempts-per-game')
        time.sleep(1)

        opp_rush_attempts = self.scrape_stat_page('opponent-rushing-attempts-per-game')
        time.sleep(1)

        rushing_tds = self.scrape_stat_page('rushing-touchdowns-per-game')
        time.sleep(1)

        opp_rushing_tds = self.scrape_stat_page('opponent-rushing-touchdowns-per-game')
        time.sleep(1)

        # === NEW: PHASE 5 - MISCELLANEOUS (5 stats) ===
        two_point_pct = self.scrape_stat_page('two-point-conversion-pct')
        time.sleep(1)

        penalty_yards = self.scrape_stat_page('penalty-yards-per-game')
        time.sleep(1)

        plays_per_game = self.scrape_stat_page('plays-per-game')
        time.sleep(1)

        opp_plays_per_game = self.scrape_stat_page('opponent-plays-per-game')
        time.sleep(1)

        opp_first_downs = self.scrape_stat_page('opponent-first-downs-per-game')
        time.sleep(1)

        # === NEW: PHASE 6 - BETTING TRENDS (ATS & O/U) ===
        ats_trends = self.scrape_ats_trends()
        time.sleep(1)

        ou_trends = self.scrape_ou_trends()
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

                # === NEW: EFFICIENCY METRICS (Phase 1) ===
                'yards_per_play': yards_per_play.get(team, 5.5),
                'opponent_yards_per_play': opp_yards_per_play.get(team, 5.5),
                'completion_pct': completion_pct.get(team, 62.0),
                'opponent_completion_pct': opp_completion_pct.get(team, 62.0),
                'fourth_down_conversion_pct': fourth_down_pct.get(team, 50.0),
                'opponent_fourth_down_conversion_pct': opp_fourth_down_pct.get(team, 50.0),

                # === NEW: TURNOVERS & SCORING (Phase 2) ===
                'interceptions_per_game': interceptions_caught.get(team, 0.7),
                'interceptions_thrown_per_game': interceptions_thrown.get(team, 0.7),
                'fumbles_lost_per_game': fumbles_lost.get(team, 0.5),
                'offensive_touchdowns_per_game': offensive_tds.get(team, 2.5),
                'defensive_touchdowns_per_game': defensive_tds.get(team, 0.2),

                # === NEW: PASSING DETAILS (Phase 3) ===
                'pass_attempts_per_game': pass_attempts.get(team, 35.0),
                'opponent_pass_attempts_per_game': opp_pass_attempts.get(team, 35.0),
                'passing_touchdowns_per_game': passing_tds.get(team, 1.5),
                'opponent_passing_touchdowns_per_game': opp_passing_tds.get(team, 1.5),
                'qb_sacked_per_game': qb_sacked.get(team, 2.0),
                'touchdowns_per_game': touchdowns_total.get(team, 2.5),

                # === NEW: RUSHING DETAILS (Phase 4) ===
                'rushing_attempts_per_game': rush_attempts.get(team, 25.0),
                'opponent_rushing_attempts_per_game': opp_rush_attempts.get(team, 25.0),
                'rushing_touchdowns_per_game': rushing_tds.get(team, 1.0),
                'opponent_rushing_touchdowns_per_game': opp_rushing_tds.get(team, 1.0),

                # === NEW: MISCELLANEOUS (Phase 5) ===
                'two_point_conversion_pct': two_point_pct.get(team, 50.0),
                'penalty_yards_per_game': penalty_yards.get(team, 50.0),
                'plays_per_game': plays_per_game.get(team, 65.0),
                'opponent_plays_per_game': opp_plays_per_game.get(team, 65.0),
                'opponent_first_downs_per_game': opp_first_downs.get(team, 20.0),

                # === NEW: BETTING TRENDS (Phase 6) ===
                # Overall ATS
                'ats_wins': ats_trends.get(team, {}).get('ats_wins'),
                'ats_losses': ats_trends.get(team, {}).get('ats_losses'),
                'ats_pushes': ats_trends.get(team, {}).get('ats_pushes'),
                # Home/Away ATS splits
                'home_ats_wins': ats_trends.get(team, {}).get('home_ats_wins'),
                'home_ats_losses': ats_trends.get(team, {}).get('home_ats_losses'),
                'home_ats_pushes': ats_trends.get(team, {}).get('home_ats_pushes'),
                'away_ats_wins': ats_trends.get(team, {}).get('away_ats_wins'),
                'away_ats_losses': ats_trends.get(team, {}).get('away_ats_losses'),
                'away_ats_pushes': ats_trends.get(team, {}).get('away_ats_pushes'),
                # Overall O/U
                'ou_overs': ou_trends.get(team, {}).get('ou_overs'),
                'ou_unders': ou_trends.get(team, {}).get('ou_unders'),
                'ou_pushes': ou_trends.get(team, {}).get('ou_pushes'),
                # Home/Away O/U splits
                'home_ou_overs': ou_trends.get(team, {}).get('home_ou_overs'),
                'home_ou_unders': ou_trends.get(team, {}).get('home_ou_unders'),
                'home_ou_pushes': ou_trends.get(team, {}).get('home_ou_pushes'),
                'away_ou_overs': ou_trends.get(team, {}).get('away_ou_overs'),
                'away_ou_unders': ou_trends.get(team, {}).get('away_ou_unders'),
                'away_ou_pushes': ou_trends.get(team, {}).get('away_ou_pushes'),
                # Last 5/10 trends - will be added from odds database if available
                'ats_last_5': None,  # Populated by NFLBettingTrendsCalculator
                'ats_last_10': None,  # Populated by NFLBettingTrendsCalculator
                'ou_last_5': None,  # Populated by NFLBettingTrendsCalculator
                'ou_last_10': None,  # Populated by NFLBettingTrendsCalculator

                'source': 'teamrankings',
                'last_updated': datetime.now().isoformat()
            }

        # Calculate rankings for each stat
        self._calculate_rankings(team_stats)

        # Save to cache
        self._save_cache(team_stats)
        self.cache = team_stats

        logger.info(f"Fetched stats for {len(team_stats)} NFL teams from TeamRankings")
        return team_stats

    def _calculate_rankings(self, team_stats: Dict[str, Dict]):
        """
        Calculate rankings for all stats

        Higher is better (rank 1 = best):
        - points_per_game (offensive)
        - passing_yards_per_game
        - rushing_yards_per_game
        - first_downs_per_game
        - third_down_conversion_pct
        - red_zone_scoring_pct
        - sacks_per_game
        - turnover_differential

        Lower is better (rank 1 = best):
        - points_allowed_per_game (defensive)
        - yards_allowed_per_game
        - opponent_passing_yards_per_game
        - opponent_rushing_yards_per_game
        - opponent_third_down_conversion_pct
        - opponent_red_zone_scoring_pct
        - penalties_per_game
        """
        if not team_stats:
            return

        # Offensive stats (higher is better)
        offensive_stats = [
            ('pts_per_game', 'points_per_game_rank'),
            ('passing_yards_per_game', 'passing_yards_per_game_rank'),
            ('rushing_yards_per_game', 'rushing_yards_per_game_rank'),
            ('first_downs_per_game', 'first_downs_rank'),
            ('third_down_conversion_pct', 'third_down_pct_rank'),
            ('red_zone_scoring_pct', 'red_zone_pct_rank'),
            ('sacks_per_game', 'sacks_rank'),
            ('turnover_diff', 'turnover_differential_rank'),
            ('yards_per_game', 'total_yards_per_game_rank'),
            # NEW: Efficiency rankings
            ('yards_per_play', 'yards_per_play_rank'),
            ('completion_pct', 'completion_pct_rank'),
            ('fourth_down_conversion_pct', 'fourth_down_conversion_pct_rank'),
            # NEW: Turnover & scoring rankings
            ('interceptions_per_game', 'interceptions_per_game_rank'),
            ('offensive_touchdowns_per_game', 'offensive_touchdowns_per_game_rank'),
            ('defensive_touchdowns_per_game', 'defensive_touchdowns_per_game_rank'),
            # NEW: Passing rankings
            ('passing_touchdowns_per_game', 'passing_touchdowns_per_game_rank'),
            ('touchdowns_per_game', 'touchdowns_per_game_rank'),
            # NEW: Rushing rankings
            ('rushing_touchdowns_per_game', 'rushing_touchdowns_per_game_rank'),
            # NEW: Misc rankings
            ('two_point_conversion_pct', 'two_point_conversion_pct_rank'),
            ('plays_per_game', 'plays_per_game_rank'),
        ]

        # Defensive stats (lower is better)
        defensive_stats = [
            ('pts_allowed', 'points_allowed_per_game_rank'),
            ('yards_allowed', 'yards_allowed_per_game_rank'),
            ('opponent_passing_yards_per_game', 'passing_yards_allowed_rank'),
            ('opponent_rushing_yards_per_game', 'rushing_yards_allowed_rank'),
            ('opponent_third_down_conversion_pct', 'opponent_third_down_pct_rank'),
            ('opponent_red_zone_scoring_pct', 'opponent_red_zone_pct_rank'),
            ('penalties_per_game', 'penalties_rank'),
            # NEW: Efficiency defense rankings (lower = better)
            ('opponent_yards_per_play', 'opponent_yards_per_play_rank'),
            ('opponent_completion_pct', 'opponent_completion_pct_rank'),
            ('opponent_fourth_down_conversion_pct', 'opponent_fourth_down_conversion_pct_rank'),
            # NEW: Turnover defense rankings (lower = better for giving up)
            ('interceptions_thrown_per_game', 'interceptions_thrown_per_game_rank'),
            ('fumbles_lost_per_game', 'fumbles_lost_per_game_rank'),
            ('opponent_passing_touchdowns_per_game', 'opponent_passing_touchdowns_per_game_rank'),
            ('opponent_rushing_touchdowns_per_game', 'opponent_rushing_touchdowns_per_game_rank'),
            ('qb_sacked_per_game', 'qb_sacked_per_game_rank'),
            # NEW: Misc defense rankings (lower = better)
            ('penalty_yards_per_game', 'penalty_yards_per_game_rank'),
            ('opponent_plays_per_game', 'opponent_plays_per_game_rank'),
            ('opponent_first_downs_per_game', 'opponent_first_downs_per_game_rank'),
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

        logger.info(f"Calculated rankings for {len(team_stats)} NFL teams")

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

    def merge_betting_trends_from_db(self, team_stats: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Merge last 5/10 game trends from odds database into team stats

        Args:
            team_stats: Team stats dict from TeamRankings

        Returns:
            Updated team stats with last 5/10 trends merged in
        """
        try:
            from scrapers.nfl_betting_trends_calculator import NFLBettingTrendsCalculator

            calculator = NFLBettingTrendsCalculator()
            db_trends = calculator.calculate_team_trends(lookback_days=120)

            if not db_trends:
                logger.warning("No betting trends calculated from odds database")
                return team_stats

            # Merge last 5/10 trends into team stats
            for team_name, stats in team_stats.items():
                # Try to find matching team in db_trends
                db_team_data = None

                # Try exact match first
                if team_name in db_trends:
                    db_team_data = db_trends[team_name]
                else:
                    # Try finding by partial match (e.g., "Kansas City" vs "Kansas City Chiefs")
                    for db_team in db_trends.keys():
                        if team_name in db_team or db_team in team_name:
                            db_team_data = db_trends[db_team]
                            break

                if db_team_data:
                    # Merge last 5/10 trends
                    stats['ats_last_5'] = db_team_data.get('ats_last_5')
                    stats['ats_last_10'] = db_team_data.get('ats_last_10')
                    stats['ou_last_5'] = db_team_data.get('ou_last_5')
                    stats['ou_last_10'] = db_team_data.get('ou_last_10')
                    logger.debug(f"Merged trends for {team_name} from odds DB")

            logger.info(f"Merged betting trends from odds database for {len(team_stats)} teams")
            return team_stats

        except ImportError:
            logger.warning("NFLBettingTrendsCalculator not available, skipping last 5/10 trends")
            return team_stats
        except Exception as e:
            logger.error(f"Error merging betting trends from database: {e}")
            return team_stats


# Standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    scraper = TeamRankingsNFLScraper()

    # Test: Fetch all teams
    print("\n=== Fetching All NFL Teams ===")
    all_stats = scraper.fetch_all_team_stats(force_refresh=True)
    print(f"Fetched {len(all_stats)} teams")

    # Test: Merge betting trends from DB (if available)
    print("\n=== Merging Betting Trends from Odds DB ===")
    all_stats = scraper.merge_betting_trends_from_db(all_stats)

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

        if chiefs.get('ats_last_5'):
            print(f"ATS Last 5: {chiefs['ats_last_5']}")
        if chiefs.get('ou_last_5'):
            print(f"O/U Last 5: {chiefs['ou_last_5']}")

    # Test: Get team by partial name
    print("\n=== Cowboys (partial match) ===")
    cowboys = scraper.get_team_stats("Cowboys")
    if cowboys:
        print(f"Full name: {cowboys['team_name']}")
        print(f"PPG: {cowboys['pts_per_game']}")
        print(f"Point Diff: {cowboys['point_diff']}")
