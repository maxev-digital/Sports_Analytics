"""
NBA STATS SCRAPER - ESPN API Integration
Fetches real player stats from ESPN (FREE, no API key required)
Simple and reliable alternative to BallDontLie
"""

import requests
import sqlite3
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NBAStatsScraperESPN:
    """Scrape NBA stats from ESPN API (FREE)"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.rate_limit_delay = 0.5

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with rate limiting"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            time.sleep(self.rate_limit_delay)
            return response.json()
        except Exception as e:
            logger.error(f"ESPN API request failed: {e}")
            return None

    def get_all_teams(self) -> List[Dict]:
        """Fetch all NBA teams"""
        logger.info("Fetching NBA teams from ESPN...")
        data = self._make_request("teams", {"limit": 100})
        if data and "sports" in data:
            leagues = data["sports"][0]["leagues"][0]
            if "teams" in leagues:
                return [t["team"] for t in leagues["teams"]]
        return []

    def get_team_roster(self, team_id: str) -> List[Dict]:
        """Fetch team roster with stats"""
        data = self._make_request(f"teams/{team_id}/roster")
        if data and "athletes" in data:
            return data["athletes"]
        return []

    def parse_player_stats(self, athlete: Dict) -> Optional[Dict]:
        """Parse player stats from ESPN data"""
        try:
            # Get player info
            player_name = athlete.get("displayName", athlete.get("fullName", ""))
            if not player_name:
                return None

            # Get statistics
            stats = athlete.get("statistics", {})
            if not stats:
                return None

            # Parse season averages
            splits = stats.get("splits", {})
            categories = splits.get("categories", [])

            # Build stats dict
            stats_dict = {}
            for category in categories:
                cat_name = category.get("name", "")
                cat_stats = category.get("stats", [])
                for stat in cat_stats:
                    stat_name = stat.get("name", "")
                    stat_value = stat.get("value", 0)
                    stats_dict[stat_name] = stat_value

            # Extract key stats
            ppg = float(stats_dict.get("avgPoints", stats_dict.get("points", 0)))
            rpg = float(stats_dict.get("avgRebounds", stats_dict.get("totalRebounds", 0)))
            apg = float(stats_dict.get("avgAssists", stats_dict.get("assists", 0)))
            spg = float(stats_dict.get("avgSteals", stats_dict.get("steals", 0)))
            bpg = float(stats_dict.get("avgBlocks", stats_dict.get("blocks", 0)))
            tpg = float(stats_dict.get("avgTurnovers", stats_dict.get("turnovers", 0)))
            fg_pct = float(stats_dict.get("fieldGoalPct", 0))
            fg3_pct = float(stats_dict.get("threePointFieldGoalPct", 0))
            ft_pct = float(stats_dict.get("freeThrowPct", 0))
            games = int(stats_dict.get("gamesPlayed", 0))
            minutes = str(stats_dict.get("avgMinutes", "0"))

            if games == 0:
                return None

            # Calculate derived stats
            pts_rebs = ppg + rpg
            pts_asts = ppg + apg
            rebs_asts = rpg + apg
            pts_rebs_asts = ppg + rpg + apg
            fantasy_score = ppg + (rpg * 1.2) + (apg * 1.5) + (spg * 3) + (bpg * 3)

            return {
                "player_name": player_name,
                "ppg": ppg,
                "rpg": rpg,
                "apg": apg,
                "spg": spg,
                "bpg": bpg,
                "tpg": tpg,
                "fg_pct": fg_pct,
                "fg3_pct": fg3_pct,
                "ft_pct": ft_pct,
                "games_played": games,
                "min": minutes,
                "pts_rebs": pts_rebs,
                "pts_asts": pts_asts,
                "rebs_asts": rebs_asts,
                "pts_rebs_asts": pts_rebs_asts,
                "fantasy_score": fantasy_score
            }

        except Exception as e:
            logger.error(f"Error parsing player stats: {e}")
            return None

    def create_database_tables(self):
        """Create NBA stats tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_stats_cache (
                player_name TEXT PRIMARY KEY,
                team TEXT,
                ppg REAL,
                rpg REAL,
                apg REAL,
                spg REAL,
                bpg REAL,
                tpg REAL,
                fg_pct REAL,
                fg3_pct REAL,
                ft_pct REAL,
                games_played INTEGER,
                min TEXT,
                ppg_l10 REAL,
                rpg_l10 REAL,
                apg_l10 REAL,
                spg_l10 REAL,
                bpg_l10 REAL,
                pts_rebs REAL,
                pts_asts REAL,
                rebs_asts REAL,
                pts_rebs_asts REAL,
                fantasy_score REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        logger.info("NBA database tables created/verified")

    def save_player_stats(self, team_abbr: str, player_stats: Dict):
        """Save player stats to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Use season stats for last_10 as well (ESPN doesn't provide L10 easily)
        cursor.execute("""
            INSERT OR REPLACE INTO player_stats_cache (
                player_name, team, ppg, rpg, apg, spg, bpg, tpg,
                fg_pct, fg3_pct, ft_pct, games_played, min,
                ppg_l10, rpg_l10, apg_l10, spg_l10, bpg_l10,
                pts_rebs, pts_asts, rebs_asts, pts_rebs_asts,
                fantasy_score, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            player_stats["player_name"], team_abbr,
            player_stats["ppg"], player_stats["rpg"], player_stats["apg"],
            player_stats["spg"], player_stats["bpg"], player_stats["tpg"],
            player_stats["fg_pct"], player_stats["fg3_pct"], player_stats["ft_pct"],
            player_stats["games_played"], player_stats["min"],
            player_stats["ppg"], player_stats["rpg"], player_stats["apg"],
            player_stats["spg"], player_stats["bpg"],
            player_stats["pts_rebs"], player_stats["pts_asts"],
            player_stats["rebs_asts"], player_stats["pts_rebs_asts"],
            player_stats["fantasy_score"]
        ))

        conn.commit()
        conn.close()

    def scrape_all_nba_stats(self):
        """Main function to scrape all NBA stats from ESPN"""
        logger.info("Starting NBA stats scrape from ESPN...")
        start_time = time.time()

        # Create tables first
        self.create_database_tables()

        # Get all teams
        teams = self.get_all_teams()
        if not teams:
            logger.error("Failed to fetch NBA teams")
            return {
                "players_updated": 0,
                "players_failed": 0,
                "teams_processed": 0,
                "elapsed_seconds": 0
            }

        logger.info(f"Found {len(teams)} NBA teams")

        players_updated = 0
        players_failed = 0

        for team in teams:
            try:
                team_id = team.get("id")
                team_abbr = team.get("abbreviation", "")
                team_name = team.get("displayName", "")

                logger.info(f"Processing {team_name} ({team_abbr})...")

                # Get roster
                roster = self.get_team_roster(team_id)

                for athlete in roster:
                    try:
                        player_stats = self.parse_player_stats(athlete)
                        if player_stats:
                            self.save_player_stats(team_abbr, player_stats)
                            players_updated += 1
                        else:
                            players_failed += 1
                    except Exception as e:
                        logger.error(f"Error processing player: {e}")
                        players_failed += 1

                logger.info(f"  {team_name}: {players_updated} total players so far")

            except Exception as e:
                logger.error(f"Error processing team {team_name}: {e}")
                continue

        elapsed = time.time() - start_time
        logger.info(f"[SUCCESS] NBA stats scrape complete in {elapsed:.1f}s")
        logger.info(f"  Players updated: {players_updated}")
        logger.info(f"  Players failed: {players_failed}")
        logger.info(f"  Teams processed: {len(teams)}")

        return {
            "players_updated": players_updated,
            "players_failed": players_failed,
            "teams_processed": len(teams),
            "elapsed_seconds": elapsed
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape NBA stats from ESPN API")
    parser.add_argument("--db", default="../predictions.db", help="Path to predictions database")
    args = parser.parse_args()

    scraper = NBAStatsScraperESPN(args.db)
    result = scraper.scrape_all_nba_stats()

    print("\n" + "="*50)
    print("NBA STATS SCRAPER (ESPN) - RESULTS")
    print("="*50)
    print(f"Players updated: {result['players_updated']}")
    print(f"Players failed: {result['players_failed']}")
    print(f"Teams processed: {result['teams_processed']}")
    print(f"Time elapsed: {result['elapsed_seconds']:.1f}s")
    print("="*50)
