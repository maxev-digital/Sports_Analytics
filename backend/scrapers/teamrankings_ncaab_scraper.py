"""
TeamRankings.com NCAAB Scraper - Free, reliable college basketball team statistics

Scrapes season baseline stats for NCAAB totals betting:
- Pace metrics (possessions/game, seconds/possession)
- Scoring efficiency (points/game, offensive/defensive efficiency)
- Shooting percentages (FG%, 3PT%, FT%, eFG%)
- Shooting volume (attempts per game)
- Rebounds, turnovers
- ATS & O/U betting trends

URL: https://www.teamrankings.com/ncaa-basketball/stat/[stat-name]
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

class TeamRankingsNCAABScraper:
    """Scraper for TeamRankings.com NCAAB (College Basketball) statistics"""

    BASE_URL = "https://www.teamrankings.com/ncaa-basketball"

    # Cache file location
    CACHE_FILE = "backend/data/raw/ncaab/teamrankings_cache.json"
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
                        logger.info(f"Loaded TeamRankings NCAAB cache from {cache_time}")
                        return cache.get('data', {})
        except Exception as e:
            logger.warning(f"Could not load NCAAB cache: {e}")
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
            logger.info(f"Saved TeamRankings NCAAB cache to {self.CACHE_FILE}")
        except Exception as e:
            logger.error(f"Could not save NCAAB cache: {e}")

    def scrape_stat_page(self, stat_name: str) -> Dict[str, float]:
        """
        Scrape a single stat page from TeamRankings

        Args:
            stat_name: URL slug (e.g., 'points-per-game', 'possessions-per-game')

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
            tbody = table.find('tbody')
            if not tbody:
                logger.error(f"Could not find tbody on {url}")
                return {}

            for row in tbody.find_all('tr'):
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
                    logger.warning(f"Could not parse stat value: {stat_value} for {team_name}")

            logger.info(f"Scraped {len(stats)} teams from {stat_name}")
            return stats

        except Exception as e:
            logger.error(f"Error scraping {stat_name}: {e}")
            return {}

    def scrape_ats_trends(self) -> Dict[str, Dict]:
        """
        Scrape ATS (Against The Spread) records from TeamRankings

        Returns:
            Dict mapping team name -> {'ats_wins': int, 'ats_losses': int, 'ats_pushes': int}
        """
        try:
            url = f"{self.BASE_URL}/stat/ats-record"
            logger.info(f"Scraping ATS records from {url}")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the ATS trends table
            table = soup.find('table', {'class': 'datatable'})
            if not table:
                logger.error("Could not find ATS trends table")
                return {}

            ats_data = {}

            for row in table.find('tbody').find_all('tr'):
                cols = row.find_all('td')
                if len(cols) < 3:
                    continue

                # Column 1: Team name
                team_link = cols[1].find('a')
                if not team_link:
                    continue
                team_name = team_link.text.strip()

                # Column 2: ATS record (e.g., "10-5-0" or "10-5")
                ats_record = cols[2].text.strip()

                # Parse W-L-P format
                parts = ats_record.split('-')
                if len(parts) >= 2:
                    try:
                        wins = int(parts[0])
                        losses = int(parts[1])
                        pushes = int(parts[2]) if len(parts) > 2 else 0

                        ats_data[team_name] = {
                            'ats_wins': wins,
                            'ats_losses': losses,
                            'ats_pushes': pushes
                        }
                    except ValueError:
                        logger.warning(f"Could not parse ATS record: {ats_record}")

            logger.info(f"Scraped ATS trends for {len(ats_data)} teams")
            return ats_data

        except Exception as e:
            logger.error(f"Error scraping ATS trends: {e}")
            return {}

    def scrape_ou_trends(self) -> Dict[str, Dict]:
        """
        Scrape O/U (Over/Under) records from TeamRankings

        Returns:
            Dict mapping team name -> {'ou_overs': int, 'ou_unders': int, 'ou_pushes': int}
        """
        try:
            url = f"{self.BASE_URL}/stat/over-under-record"
            logger.info(f"Scraping O/U records from {url}")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the O/U trends table
            table = soup.find('table', {'class': 'datatable'})
            if not table:
                logger.error("Could not find O/U trends table")
                return {}

            ou_data = {}

            for row in table.find('tbody').find_all('tr'):
                cols = row.find_all('td')
                if len(cols) < 3:
                    continue

                # Column 1: Team name
                team_link = cols[1].find('a')
                if not team_link:
                    continue
                team_name = team_link.text.strip()

                # Column 2: O/U record (e.g., "8-7-0" or "8-7")
                ou_record = cols[2].text.strip()

                # Parse O-U-P format
                parts = ou_record.split('-')
                if len(parts) >= 2:
                    try:
                        overs = int(parts[0])
                        unders = int(parts[1])
                        pushes = int(parts[2]) if len(parts) > 2 else 0

                        ou_data[team_name] = {
                            'ou_overs': overs,
                            'ou_unders': unders,
                            'ou_pushes': pushes
                        }
                    except ValueError:
                        logger.warning(f"Could not parse O/U record: {ou_record}")

            logger.info(f"Scraped O/U trends for {len(ou_data)} teams")
            return ou_data

        except Exception as e:
            logger.error(f"Error scraping O/U trends: {e}")
            return {}

    def fetch_all_team_stats(self) -> Dict[str, Dict]:
        """
        Fetch all NCAAB team statistics for totals betting

        Returns:
            Dict mapping team name -> stats dict with all metrics
        """
        # Check cache first
        if self.cache and 'teams' in self.cache:
            logger.info("Returning cached NCAAB stats")
            return self.cache['teams']

        logger.info("Fetching fresh NCAAB stats from TeamRankings...")

        # === PACE & TEMPO (critical for totals) ===
        possessions = self.scrape_stat_page('possessions-per-game')
        time.sleep(1)

        seconds_per_poss = self.scrape_stat_page('seconds-per-possession')
        time.sleep(1)

        # === SCORING & EFFICIENCY ===
        points_per_game = self.scrape_stat_page('points-per-game')
        time.sleep(1)

        opp_points_per_game = self.scrape_stat_page('opponent-points-per-game')
        time.sleep(1)

        offensive_efficiency = self.scrape_stat_page('offensive-efficiency')
        time.sleep(1)

        defensive_efficiency = self.scrape_stat_page('defensive-efficiency')
        time.sleep(1)

        effective_fg_pct = self.scrape_stat_page('effective-field-goal-pct')
        time.sleep(1)

        opp_effective_fg_pct = self.scrape_stat_page('opponent-effective-field-goal-pct')
        time.sleep(1)

        # === SHOOTING VOLUME (impacts totals) ===
        fg_attempts = self.scrape_stat_page('field-goal-attempts-per-game')
        time.sleep(1)

        three_pt_attempts = self.scrape_stat_page('three-point-attempts-per-game')
        time.sleep(1)

        ft_attempts = self.scrape_stat_page('free-throw-attempts-per-game')
        time.sleep(1)

        # === SHOOTING EFFICIENCY ===
        fg_pct = self.scrape_stat_page('field-goal-pct')
        time.sleep(1)

        three_pt_pct = self.scrape_stat_page('three-point-pct')
        time.sleep(1)

        two_pt_pct = self.scrape_stat_page('two-point-pct')
        time.sleep(1)

        ft_pct = self.scrape_stat_page('free-throw-pct')
        time.sleep(1)

        # === REBOUNDING (2nd chance points) ===
        off_rebounds = self.scrape_stat_page('offensive-rebounds-per-game')
        time.sleep(1)

        def_rebounds = self.scrape_stat_page('defensive-rebounds-per-game')
        time.sleep(1)

        total_rebounds = self.scrape_stat_page('total-rebounds-per-game')
        time.sleep(1)

        # === TURNOVERS (impact pace) ===
        turnovers = self.scrape_stat_page('turnovers-per-game')
        time.sleep(1)

        opp_turnovers = self.scrape_stat_page('opponent-turnovers-per-game')
        time.sleep(1)

        turnover_pct = self.scrape_stat_page('turnover-pct')
        time.sleep(1)

        # === BETTING TRENDS ===
        ats_trends = self.scrape_ats_trends()
        time.sleep(1)

        ou_trends = self.scrape_ou_trends()
        time.sleep(1)

        # Combine all stats by team
        all_teams = set()
        for stat_dict in [possessions, points_per_game, fg_pct]:
            all_teams.update(stat_dict.keys())

        team_stats = {}
        for team in all_teams:
            # Get ATS/OU trends
            ats = ats_trends.get(team, {})
            ou = ou_trends.get(team, {})

            team_stats[team] = {
                # PACE & TEMPO
                'possessions_per_game': possessions.get(team),
                'seconds_per_possession': seconds_per_poss.get(team),

                # SCORING & EFFICIENCY
                'points_per_game': points_per_game.get(team),
                'opponent_points_per_game': opp_points_per_game.get(team),
                'offensive_efficiency': offensive_efficiency.get(team),
                'defensive_efficiency': defensive_efficiency.get(team),
                'effective_field_goal_pct': effective_fg_pct.get(team),
                'opponent_effective_field_goal_pct': opp_effective_fg_pct.get(team),

                # SHOOTING VOLUME
                'field_goal_attempts_per_game': fg_attempts.get(team),
                'three_point_attempts_per_game': three_pt_attempts.get(team),
                'free_throw_attempts_per_game': ft_attempts.get(team),

                # SHOOTING EFFICIENCY
                'field_goal_pct': fg_pct.get(team),
                'three_point_pct': three_pt_pct.get(team),
                'two_point_pct': two_pt_pct.get(team),
                'free_throw_pct': ft_pct.get(team),

                # REBOUNDING
                'offensive_rebounds_per_game': off_rebounds.get(team),
                'defensive_rebounds_per_game': def_rebounds.get(team),
                'total_rebounds_per_game': total_rebounds.get(team),

                # TURNOVERS
                'turnovers_per_game': turnovers.get(team),
                'opponent_turnovers_per_game': opp_turnovers.get(team),
                'turnover_pct': turnover_pct.get(team),

                # BETTING TRENDS
                'ats_wins': ats.get('ats_wins'),
                'ats_losses': ats.get('ats_losses'),
                'ats_pushes': ats.get('ats_pushes'),
                'ou_overs': ou.get('ou_overs'),
                'ou_unders': ou.get('ou_unders'),
                'ou_pushes': ou.get('ou_pushes'),
            }

        logger.info(f"Fetched stats for {len(team_stats)} NCAAB teams")

        # Save to cache
        cache_data = {'teams': team_stats}
        self._save_cache(cache_data)
        self.cache = cache_data

        return team_stats


def main():
    """Test the NCAAB scraper"""
    logging.basicConfig(level=logging.INFO)

    scraper = TeamRankingsNCAABScraper()

    print("\n" + "="*80)
    print("NCAAB TeamRankings Scraper Test")
    print("="*80)

    # Test full fetch
    all_stats = scraper.fetch_all_team_stats()

    # Show sample team
    if all_stats:
        # Try to find a prominent team
        sample_teams = ['Duke', 'North Carolina', 'Kansas', 'Kentucky', 'Gonzaga']
        sample_team = None
        for team in sample_teams:
            if team in all_stats:
                sample_team = team
                break

        if not sample_team:
            sample_team = list(all_stats.keys())[0]

        print(f"\n{sample_team} Season Stats (TeamRankings):")
        print("="*80)
        stats = all_stats[sample_team]

        print("\nPACE & TEMPO:")
        print(f"  Possessions/game: {stats.get('possessions_per_game')}")
        print(f"  Seconds/possession: {stats.get('seconds_per_possession')}")

        print("\nSCORING:")
        print(f"  Points/game: {stats.get('points_per_game')}")
        print(f"  Opp Points/game: {stats.get('opponent_points_per_game')}")
        print(f"  Offensive Efficiency: {stats.get('offensive_efficiency')}")
        print(f"  Defensive Efficiency: {stats.get('defensive_efficiency')}")

        print("\nSHOOTING:")
        print(f"  FG%: {stats.get('field_goal_pct')}")
        print(f"  3PT%: {stats.get('three_point_pct')}")
        print(f"  FT%: {stats.get('free_throw_pct')}")
        print(f"  eFG%: {stats.get('effective_field_goal_pct')}")

        print("\nVOLUME:")
        print(f"  FG attempts/game: {stats.get('field_goal_attempts_per_game')}")
        print(f"  3PT attempts/game: {stats.get('three_point_attempts_per_game')}")
        print(f"  FT attempts/game: {stats.get('free_throw_attempts_per_game')}")

        print("\nREBOUNDS & TURNOVERS:")
        print(f"  Off rebounds/game: {stats.get('offensive_rebounds_per_game')}")
        print(f"  Def rebounds/game: {stats.get('defensive_rebounds_per_game')}")
        print(f"  Turnovers/game: {stats.get('turnovers_per_game')}")
        print(f"  Turnover %: {stats.get('turnover_pct')}")

        print("\nBETTING TRENDS:")
        print(f"  ATS: {stats.get('ats_wins')}-{stats.get('ats_losses')}-{stats.get('ats_pushes')}")
        print(f"  O/U: {stats.get('ou_overs')}-{stats.get('ou_unders')}-{stats.get('ou_pushes')}")

        print("\n" + "="*80)
        print(f"Total teams scraped: {len(all_stats)}")


if __name__ == "__main__":
    main()
