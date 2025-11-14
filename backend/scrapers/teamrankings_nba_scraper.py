"""
TeamRankings.com NBA Scraper - Free, reliable NBA team statistics

Scrapes:
- Points per game (offensive)
- Points allowed per game (defensive)
- Point differential (net rating proxy)
- Win/loss records
- Team rankings

URL: https://www.teamrankings.com/nba/stat/points-per-game
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

class TeamRankingsNBAScraper:
    """Scraper for TeamRankings.com NBA statistics"""

    BASE_URL = "https://www.teamrankings.com/nba"

    # Cache file location
    CACHE_FILE = "backend/data/raw/nba/teamrankings_cache.json"
    CACHE_DURATION = timedelta(hours=6)  # Refresh every 6 hours

    # Team name mapping: Full name -> TeamRankings abbreviated name
    TEAM_NAME_MAP = {
        'Atlanta Hawks': 'Atlanta',
        'Boston Celtics': 'Boston',
        'Brooklyn Nets': 'Brooklyn',
        'Charlotte Hornets': 'Charlotte',
        'Chicago Bulls': 'Chicago',
        'Cleveland Cavaliers': 'Cleveland',
        'Dallas Mavericks': 'Dallas',
        'Denver Nuggets': 'Denver',
        'Detroit Pistons': 'Detroit',
        'Golden State Warriors': 'Golden State',
        'Houston Rockets': 'Houston',
        'Indiana Pacers': 'Indiana',
        'Los Angeles Clippers': 'LA Clippers',
        'LA Clippers': 'LA Clippers',
        'Los Angeles Lakers': 'LA Lakers',
        'LA Lakers': 'LA Lakers',
        'Memphis Grizzlies': 'Memphis',
        'Miami Heat': 'Miami',
        'Milwaukee Bucks': 'Milwaukee',
        'Minnesota Timberwolves': 'Minnesota',
        'New Orleans Pelicans': 'New Orleans',
        'New York Knicks': 'New York',
        'Oklahoma City Thunder': 'Okla City',
        'Orlando Magic': 'Orlando',
        'Philadelphia 76ers': 'Philadelphia',
        'Phoenix Suns': 'Phoenix',
        'Portland Trail Blazers': 'Portland',
        'Sacramento Kings': 'Sacramento',
        'San Antonio Spurs': 'San Antonio',
        'Toronto Raptors': 'Toronto',
        'Utah Jazz': 'Utah',
        'Washington Wizards': 'Washington',
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
                        logger.info(f"Loaded TeamRankings cache from {cache_time}")
                        return cache.get('data', {})
        except Exception as e:
            logger.warning(f"Could not load cache: {e}")
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
            logger.info(f"Saved TeamRankings cache to {self.CACHE_FILE}")
        except Exception as e:
            logger.error(f"Could not save cache: {e}")

    def scrape_stat_page(self, stat_name: str) -> Dict[str, Dict]:
        """
        Scrape a single stat page from TeamRankings

        Args:
            stat_name: URL slug (e.g., 'points-per-game', 'opponent-points-per-game')

        Returns:
            Dict mapping team name -> {'value': float, 'rank': int}
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

                # Column 0: Rank
                rank_text = cols[0].text.strip()
                try:
                    rank = int(rank_text)
                except ValueError:
                    rank = None

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
                    stats[team_name] = {
                        'value': float(stat_value),
                        'rank': rank
                    }
                except ValueError:
                    logger.warning(f"Could not parse stat value: {stat_value}")

            logger.info(f"Scraped {len(stats)} teams from {stat_name}")
            return stats

        except Exception as e:
            logger.error(f"Error scraping {stat_name}: {e}")
            return {}

    def fetch_all_team_stats(self, force_refresh: bool = False) -> Dict[str, Dict]:
        """
        Fetch all NBA team statistics from TeamRankings

        Args:
            force_refresh: Bypass cache and fetch fresh data

        Returns:
            Dict mapping team name -> stats dict
            {
                'Los Angeles Lakers': {
                    'pts_per_game': 118.5,
                    'pts_allowed': 110.2,
                    'point_diff': 8.3,
                    'wins': 42,
                    'losses': 30,
                    'win_pct': 0.583
                },
                ...
            }
        """
        # Check cache first
        if not force_refresh and self.cache:
            logger.info("Using cached TeamRankings data")
            return self.cache

        logger.info("Fetching fresh NBA stats from TeamRankings.com...")

        # Scrape each stat page (basic stats)
        ppg = self.scrape_stat_page('points-per-game')
        time.sleep(1)  # Be polite to server

        opp_ppg = self.scrape_stat_page('opponent-points-per-game')
        time.sleep(1)

        point_diff = self.scrape_stat_page('average-scoring-margin')
        time.sleep(1)

        wins = self.scrape_stat_page('wins')
        time.sleep(1)

        losses = self.scrape_stat_page('losses')
        time.sleep(1)

        # NEW: Advanced stats for ML
        pace = self.scrape_stat_page('possessions-per-game')
        time.sleep(1)

        off_rebounds = self.scrape_stat_page('offensive-rebounds-per-game')
        time.sleep(1)

        def_rebounds = self.scrape_stat_page('defensive-rebounds-per-game')
        time.sleep(1)

        assists = self.scrape_stat_page('assists-per-game')
        time.sleep(1)

        turnovers = self.scrape_stat_page('turnovers-per-game')
        time.sleep(1)

        steals = self.scrape_stat_page('steals-per-game')
        time.sleep(1)

        blocks = self.scrape_stat_page('blocks-per-game')
        time.sleep(1)

        ts_pct = self.scrape_stat_page('true-shooting-percentage')
        time.sleep(1)

        fouls = self.scrape_stat_page('personal-fouls-per-game')
        time.sleep(1)

        paint_pts = self.scrape_stat_page('points-in-paint-per-game')
        time.sleep(1)

        # Shooting percentages
        fg_pct = self.scrape_stat_page('field-goal-pct')
        time.sleep(1)

        fg3_pct = self.scrape_stat_page('three-point-pct')
        time.sleep(1)

        ft_pct = self.scrape_stat_page('free-throw-pct')
        time.sleep(1)

        # Combine all stats
        all_teams = set(ppg.keys()) | set(opp_ppg.keys()) | set(point_diff.keys())

        team_stats = {}
        for team in all_teams:
            # Extract values and ranks
            ppg_data = ppg.get(team, {'value': 110.0, 'rank': None})
            opp_ppg_data = opp_ppg.get(team, {'value': 110.0, 'rank': None})
            point_diff_data = point_diff.get(team, {'value': 0.0, 'rank': None})
            wins_data = wins.get(team, {'value': 0, 'rank': None})
            losses_data = losses.get(team, {'value': 0, 'rank': None})
            pace_data = pace.get(team, {'value': 100.0, 'rank': None})
            off_reb_data = off_rebounds.get(team, {'value': 10.0, 'rank': None})
            def_reb_data = def_rebounds.get(team, {'value': 35.0, 'rank': None})
            assists_data = assists.get(team, {'value': 25.0, 'rank': None})
            turnovers_data = turnovers.get(team, {'value': 14.0, 'rank': None})
            steals_data = steals.get(team, {'value': 7.5, 'rank': None})
            blocks_data = blocks.get(team, {'value': 5.0, 'rank': None})
            ts_pct_data = ts_pct.get(team, {'value': 57.0, 'rank': None})
            fouls_data = fouls.get(team, {'value': 20.0, 'rank': None})
            paint_pts_data = paint_pts.get(team, {'value': 50.0, 'rank': None})
            fg_pct_data = fg_pct.get(team, {'value': 45.0, 'rank': None})
            fg3_pct_data = fg3_pct.get(team, {'value': 35.0, 'rank': None})
            ft_pct_data = ft_pct.get(team, {'value': 75.0, 'rank': None})

            w = wins_data.get('value', 0)
            l = losses_data.get('value', 0)
            games_played = w + l

            ppg_val = ppg_data.get('value', 110.0)
            opp_ppg_val = opp_ppg_data.get('value', 110.0)
            pace_val = pace_data.get('value', 100.0)
            assists_val = assists_data.get('value', 25.0)
            turnovers_val = turnovers_data.get('value', 14.0)

            team_stats[team] = {
                'team_name': team,
                # Basic stats
                'pts_per_game': ppg_val,
                'pts_allowed': opp_ppg_val,
                'point_diff': point_diff_data.get('value', 0.0),
                'wins': int(w),
                'losses': int(l),
                'games_played': int(games_played),
                'win_pct': round(w / games_played, 3) if games_played > 0 else 0.0,
                # Advanced stats (NEW for ML)
                'pace': pace_val,  # Possessions per game - CRITICAL for totals
                'offensive_rebounds': off_reb_data.get('value', 10.0),
                'defensive_rebounds': def_reb_data.get('value', 35.0),
                'total_rebounds': off_reb_data.get('value', 10.0) + def_reb_data.get('value', 35.0),
                'assists': assists_val,
                'turnovers': turnovers_val,
                'steals': steals_data.get('value', 7.5),
                'blocks': blocks_data.get('value', 5.0),
                'true_shooting_pct': ts_pct_data.get('value', 57.0),  # True shooting %
                'personal_fouls': fouls_data.get('value', 20.0),
                'points_in_paint': paint_pts_data.get('value', 50.0),
                # Shooting percentages as decimals (not percentages) for frontend compatibility
                'fg_pct': fg_pct_data.get('value', 45.0) / 100.0,  # Convert 45.0 to 0.45
                'fg3_pct': fg3_pct_data.get('value', 35.0) / 100.0,  # Convert 35.0 to 0.35
                'ft_pct': ft_pct_data.get('value', 75.0) / 100.0,  # Convert 75.0 to 0.75
                # Calculated stats
                'net_rating': point_diff_data.get('value', 0.0),
                'off_rating': ppg_val,  # Simplified
                'def_rating': opp_ppg_val,  # Simplified
                'assist_turnover_ratio': round(assists_val / turnovers_val, 2) if turnovers_val > 0 else 0.0,
                # RANKS (NEW!)
                'pts_per_game_rank': ppg_data.get('rank'),
                'pts_allowed_rank': opp_ppg_data.get('rank'),
                'point_diff_rank': point_diff_data.get('rank'),
                'pace_rank': pace_data.get('rank'),
                'off_rating_rank': ppg_data.get('rank'),  # Same as PPG rank
                'def_rating_rank': opp_ppg_data.get('rank'),  # Same as opp PPG rank
                'net_rating_rank': point_diff_data.get('rank'),  # Same as point diff rank
                'assists_rank': assists_data.get('rank'),
                'turnovers_rank': turnovers_data.get('rank'),
                'steals_rank': steals_data.get('rank'),
                'blocks_rank': blocks_data.get('rank'),
                'ts_pct_rank': ts_pct_data.get('rank'),
                'fg_pct_rank': fg_pct_data.get('rank'),
                'fg3_pct_rank': fg3_pct_data.get('rank'),
                'ft_pct_rank': ft_pct_data.get('rank'),
                'source': 'teamrankings',
                'last_updated': datetime.now().isoformat()
            }

        # Save to cache
        self._save_cache(team_stats)
        self.cache = team_stats

        logger.info(f"Fetched stats for {len(team_stats)} NBA teams from TeamRankings")
        return team_stats

    def get_team_stats(self, team_name: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get stats for a specific team

        Args:
            team_name: Full team name (e.g., 'Los Angeles Lakers', 'Lakers')
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

        # Try partial match (e.g., "Lakers" matches "LA Lakers")
        for full_name, stats in all_stats.items():
            if team_name.lower() in full_name.lower() or full_name.lower() in team_name.lower():
                return stats

        logger.warning(f"Team not found in TeamRankings data: {team_name}")
        return None

    def refresh_cache(self):
        """Force refresh the cache"""
        logger.info("Force refreshing TeamRankings cache...")
        self.fetch_all_team_stats(force_refresh=True)


# Standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    scraper = TeamRankingsNBAScraper()

    # Test: Fetch all teams
    print("\n=== Fetching All NBA Teams ===")
    all_stats = scraper.fetch_all_team_stats(force_refresh=True)
    print(f"Fetched {len(all_stats)} teams")

    # Test: Get specific team
    print("\n=== Los Angeles Lakers ===")
    lakers = scraper.get_team_stats("Los Angeles Lakers")
    if lakers:
        print(f"PPG: {lakers['pts_per_game']}")
        print(f"Opp PPG: {lakers['pts_allowed']}")
        print(f"Point Diff: {lakers['point_diff']}")
        print(f"Record: {lakers['wins']}-{lakers['losses']}")
        print(f"Win %: {lakers['win_pct']:.1%}")

    # Test: Get team by partial name
    print("\n=== Celtics (partial match) ===")
    celtics = scraper.get_team_stats("Celtics")
    if celtics:
        print(f"Full name: {celtics['team_name']}")
        print(f"PPG: {celtics['pts_per_game']}")
        print(f"Point Diff: {celtics['point_diff']}")
