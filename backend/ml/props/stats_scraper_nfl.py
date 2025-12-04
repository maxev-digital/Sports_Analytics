"""
NFL STATS SCRAPER - ESPN API Integration
Fetches real player and team stats for NFL props
"""

import requests
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NFLStatsScraper:
    """Scrape NFL stats from ESPN API (FREE)"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.rate_limit_delay = 0.5  # Conservative rate limiting
        self.current_season = "2026"  # 2025 = 2024-25 NFL season

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with rate limiting"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            time.sleep(self.rate_limit_delay)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {endpoint}: {e}")
            return None

    def get_all_teams(self) -> List[Dict]:
        """Fetch all NFL teams"""
        logger.info("Fetching all NFL teams...")
        data = self._make_request("teams")
        if data and data.get("sports"):
            teams = []
            for sport in data["sports"]:
                if sport.get("leagues"):
                    for league in sport["leagues"]:
                        if league.get("teams"):
                            teams.extend(league["teams"])
            logger.info(f"Found {len(teams)} NFL teams")
            return teams
        return []

    def get_team_roster(self, team_id: str) -> List[Dict]:
        """Fetch team roster"""
        data = self._make_request(f"teams/{team_id}/roster")
        if data and data.get("athletes"):
            return data["athletes"]
        return []

    def get_player_stats(self, player_id: str) -> Optional[Dict]:
        """Fetch player season stats"""
        data = self._make_request(f"athletes/{player_id}/statistics")
        if data and data.get("statistics"):
            # Get current season stats
            for stat_group in data["statistics"]:
                if stat_group.get("displayName") == "seasonStats":
                    return stat_group
        return None

    def calculate_qb_stats(self, stats: Dict) -> Dict:
        """Calculate QB stats from ESPN data"""
        stats_dict = {}

        # Parse stats array
        if "stats" in stats:
            stat_map = {}
            labels = stats.get("labels", [])
            values = stats.get("stats", [])

            for label, value in zip(labels, values):
                stat_map[label] = value

            # Extract QB stats
            stats_dict = {
                "passing_yards_pg": float(stat_map.get("passingYards", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "passing_tds_pg": float(stat_map.get("passingTouchdowns", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "passing_ints_pg": float(stat_map.get("interceptions", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "completions_pg": float(stat_map.get("completions", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "attempts_pg": float(stat_map.get("passingAttempts", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "completion_pct": float(stat_map.get("completionPercentage", 0)),
                "rushing_yards_pg": float(stat_map.get("rushingYards", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "rushing_tds_pg": float(stat_map.get("rushingTouchdowns", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "games_played": int(stat_map.get("gamesPlayed", 0))
            }

        return stats_dict

    def calculate_rb_stats(self, stats: Dict) -> Dict:
        """Calculate RB stats from ESPN data"""
        stats_dict = {}

        if "stats" in stats:
            stat_map = {}
            labels = stats.get("labels", [])
            values = stats.get("stats", [])

            for label, value in zip(labels, values):
                stat_map[label] = value

            stats_dict = {
                "rushing_yards_pg": float(stat_map.get("rushingYards", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "rushing_tds_pg": float(stat_map.get("rushingTouchdowns", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "rushing_attempts_pg": float(stat_map.get("rushingAttempts", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "yards_per_carry": float(stat_map.get("yardsPerRushAttempt", 0)),
                "receiving_yards_pg": float(stat_map.get("receivingYards", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "receiving_tds_pg": float(stat_map.get("receivingTouchdowns", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "receptions_pg": float(stat_map.get("receptions", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "targets_pg": float(stat_map.get("receivingTargets", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "games_played": int(stat_map.get("gamesPlayed", 0))
            }

        return stats_dict

    def calculate_wr_te_stats(self, stats: Dict) -> Dict:
        """Calculate WR/TE stats from ESPN data"""
        stats_dict = {}

        if "stats" in stats:
            stat_map = {}
            labels = stats.get("labels", [])
            values = stats.get("stats", [])

            for label, value in zip(labels, values):
                stat_map[label] = value

            stats_dict = {
                "receiving_yards_pg": float(stat_map.get("receivingYards", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "receiving_tds_pg": float(stat_map.get("receivingTouchdowns", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "receptions_pg": float(stat_map.get("receptions", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "targets_pg": float(stat_map.get("receivingTargets", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "yards_per_reception": float(stat_map.get("yardsPerReception", 0)),
                "rushing_yards_pg": float(stat_map.get("rushingYards", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "rushing_tds_pg": float(stat_map.get("rushingTouchdowns", 0)) / max(float(stat_map.get("gamesPlayed", 1)), 1),
                "games_played": int(stat_map.get("gamesPlayed", 0))
            }

        return stats_dict

    def save_qb_stats(self, player_name: str, team: str, stats: Dict):
        """Save QB stats to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nfl_qb_stats_cache (
                player_name TEXT PRIMARY KEY,
                team TEXT,
                passing_yards_pg REAL,
                passing_tds_pg REAL,
                passing_ints_pg REAL,
                completions_pg REAL,
                attempts_pg REAL,
                completion_pct REAL,
                rushing_yards_pg REAL,
                rushing_tds_pg REAL,
                games_played INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            INSERT OR REPLACE INTO nfl_qb_stats_cache (
                player_name, team, passing_yards_pg, passing_tds_pg, passing_ints_pg,
                completions_pg, attempts_pg, completion_pct,
                rushing_yards_pg, rushing_tds_pg, games_played, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            player_name, team,
            stats.get("passing_yards_pg", 0), stats.get("passing_tds_pg", 0), stats.get("passing_ints_pg", 0),
            stats.get("completions_pg", 0), stats.get("attempts_pg", 0), stats.get("completion_pct", 0),
            stats.get("rushing_yards_pg", 0), stats.get("rushing_tds_pg", 0), stats.get("games_played", 0)
        ))

        conn.commit()
        conn.close()

    def save_rb_stats(self, player_name: str, team: str, stats: Dict):
        """Save RB stats to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nfl_rb_stats_cache (
                player_name TEXT PRIMARY KEY,
                team TEXT,
                rushing_yards_pg REAL,
                rushing_tds_pg REAL,
                rushing_attempts_pg REAL,
                yards_per_carry REAL,
                receiving_yards_pg REAL,
                receiving_tds_pg REAL,
                receptions_pg REAL,
                targets_pg REAL,
                games_played INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            INSERT OR REPLACE INTO nfl_rb_stats_cache (
                player_name, team, rushing_yards_pg, rushing_tds_pg, rushing_attempts_pg,
                yards_per_carry, receiving_yards_pg, receiving_tds_pg,
                receptions_pg, targets_pg, games_played, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            player_name, team,
            stats.get("rushing_yards_pg", 0), stats.get("rushing_tds_pg", 0), stats.get("rushing_attempts_pg", 0),
            stats.get("yards_per_carry", 0), stats.get("receiving_yards_pg", 0), stats.get("receiving_tds_pg", 0),
            stats.get("receptions_pg", 0), stats.get("targets_pg", 0), stats.get("games_played", 0)
        ))

        conn.commit()
        conn.close()

    def save_wr_te_stats(self, player_name: str, team: str, position: str, stats: Dict):
        """Save WR/TE stats to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nfl_receiver_stats_cache (
                player_name TEXT PRIMARY KEY,
                team TEXT,
                position TEXT,
                receiving_yards_pg REAL,
                receiving_tds_pg REAL,
                receptions_pg REAL,
                targets_pg REAL,
                yards_per_reception REAL,
                rushing_yards_pg REAL,
                rushing_tds_pg REAL,
                games_played INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            INSERT OR REPLACE INTO nfl_receiver_stats_cache (
                player_name, team, position, receiving_yards_pg, receiving_tds_pg,
                receptions_pg, targets_pg, yards_per_reception,
                rushing_yards_pg, rushing_tds_pg, games_played, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            player_name, team, position,
            stats.get("receiving_yards_pg", 0), stats.get("receiving_tds_pg", 0),
            stats.get("receptions_pg", 0), stats.get("targets_pg", 0), stats.get("yards_per_reception", 0),
            stats.get("rushing_yards_pg", 0), stats.get("rushing_tds_pg", 0), stats.get("games_played", 0)
        ))

        conn.commit()
        conn.close()

    def save_team_stats(self, team_name: str, team_data: Dict):
        """Save team stats to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nfl_team_stats_cache (
                team_name TEXT PRIMARY KEY,
                abbreviation TEXT,
                conference TEXT,
                division TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        team_info = team_data.get("team", {})
        cursor.execute("""
            INSERT OR REPLACE INTO nfl_team_stats_cache (
                team_name, abbreviation, conference, division, last_updated
            ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            team_info.get("displayName", team_name),
            team_info.get("abbreviation", ""),
            team_info.get("groups", {}).get("name", ""),
            team_info.get("groups", {}).get("parent", {}).get("name", "")
        ))

        conn.commit()
        conn.close()

    def scrape_all_nfl_stats(self):
        """Main function to scrape all NFL stats"""
        logger.info("Starting NFL stats scrape...")
        start_time = time.time()

        # Get all teams
        teams = self.get_all_teams()
        logger.info(f"Found {len(teams)} NFL teams")

        qbs_updated = 0
        rbs_updated = 0
        receivers_updated = 0
        players_failed = 0
        teams_processed = 0

        for team_data in teams:
            team_info = team_data.get("team", {})
            team_id = team_info.get("id")
            team_name = team_info.get("displayName", "Unknown")
            team_abbr = team_info.get("abbreviation", "")

            logger.info(f"Processing {team_name}...")

            # Save team stats
            self.save_team_stats(team_name, team_data)
            teams_processed += 1

            # Get roster
            roster = self.get_team_roster(team_id)

            for athlete_data in roster:
                athlete = athlete_data.get("athlete", {})
                player_id = athlete.get("id")
                player_name = athlete.get("displayName", "Unknown")
                position = athlete.get("position", {}).get("abbreviation", "")

                # Only process offensive skill positions
                if position not in ["QB", "RB", "WR", "TE"]:
                    continue

                try:
                    # Get player stats
                    stats = self.get_player_stats(player_id)
                    if not stats:
                        players_failed += 1
                        continue

                    # Process based on position
                    if position == "QB":
                        qb_stats = self.calculate_qb_stats(stats)
                        if qb_stats:
                            self.save_qb_stats(player_name, team_abbr, qb_stats)
                            qbs_updated += 1

                    elif position == "RB":
                        rb_stats = self.calculate_rb_stats(stats)
                        if rb_stats:
                            self.save_rb_stats(player_name, team_abbr, rb_stats)
                            rbs_updated += 1

                    elif position in ["WR", "TE"]:
                        wr_stats = self.calculate_wr_te_stats(stats)
                        if wr_stats:
                            self.save_wr_te_stats(player_name, team_abbr, position, wr_stats)
                            receivers_updated += 1

                except Exception as e:
                    logger.error(f"Error processing {player_name}: {e}")
                    players_failed += 1
                    continue

            logger.info(f"  {team_name}: QBs={qbs_updated}, RBs={rbs_updated}, WR/TE={receivers_updated}")

        elapsed = time.time() - start_time
        logger.info(f"[SUCCESS] NFL stats scrape complete in {elapsed:.1f}s")
        logger.info(f"  QBs updated: {qbs_updated}")
        logger.info(f"  RBs updated: {rbs_updated}")
        logger.info(f"  WR/TE updated: {receivers_updated}")
        logger.info(f"  Players failed: {players_failed}")
        logger.info(f"  Teams updated: {teams_processed}")

        return {
            "qbs_updated": qbs_updated,
            "rbs_updated": rbs_updated,
            "receivers_updated": receivers_updated,
            "players_failed": players_failed,
            "teams_updated": teams_processed,
            "elapsed_seconds": elapsed
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape NFL stats from ESPN API")
    parser.add_argument("--db", default="../predictions.db", help="Path to predictions database")
    args = parser.parse_args()

    scraper = NFLStatsScraper(args.db)
    result = scraper.scrape_all_nfl_stats()

    print("\n" + "="*50)
    print("NFL STATS SCRAPER - RESULTS")
    print("="*50)
    print(f"QBs updated: {result['qbs_updated']}")
    print(f"RBs updated: {result['rbs_updated']}")
    print(f"WR/TE updated: {result['receivers_updated']}")
    print(f"Players failed: {result['players_failed']}")
    print(f"Teams updated: {result['teams_updated']}")
    print(f"Time elapsed: {result['elapsed_seconds']:.1f}s")
    print("="*50)
