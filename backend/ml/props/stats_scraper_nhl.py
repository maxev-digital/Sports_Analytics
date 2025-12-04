"""
NHL STATS SCRAPER - NHL API Integration
Fetches real player and team stats for hockey props
"""

import requests
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NHLStatsScraper:
    """Scrape NHL stats from official NHL API (FREE)"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.base_url = "https://statsapi.web.nhl.com/api/v1"
        self.session = requests.Session()
        self.rate_limit_delay = 0.5  # Conservative rate limiting

    def _make_request(self, endpoint: str) -> Optional[Dict]:
        """Make API request with rate limiting"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            time.sleep(self.rate_limit_delay)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None

    def get_all_teams(self) -> List[Dict]:
        """Fetch all NHL teams"""
        logger.info("Fetching all NHL teams...")
        data = self._make_request("teams")
        if data and data.get("teams"):
            return data["teams"]
        return []

    def get_team_roster(self, team_id: int) -> List[Dict]:
        """Fetch team roster"""
        data = self._make_request(f"teams/{team_id}/roster")
        if data and data.get("roster"):
            return data["roster"]
        return []

    def get_player_stats(self, player_id: int, season: str = "20252026") -> Optional[Dict]:
        """Fetch player season stats"""
        data = self._make_request(f"people/{player_id}/stats?stats=statsSingleSeason&season={season}")
        if data and data.get("stats") and data["stats"][0].get("splits"):
            return data["stats"][0]["splits"][0].get("stat")
        return None

    def get_goalie_stats(self, player_id: int, season: str = "20252026") -> Optional[Dict]:
        """Fetch goalie season stats"""
        data = self._make_request(f"people/{player_id}/stats?stats=statsSingleSeason&season={season}")
        if data and data.get("stats") and data["stats"][0].get("splits"):
            return data["stats"][0]["splits"][0].get("stat")
        return None

    def calculate_skater_stats(self, stats: Dict) -> Dict:
        """Calculate comprehensive skater stats"""
        games = stats.get("games", 1)

        return {
            "goals_pg": stats.get("goals", 0) / games if games > 0 else 0.0,
            "assists_pg": stats.get("assists", 0) / games if games > 0 else 0.0,
            "points_pg": stats.get("points", 0) / games if games > 0 else 0.0,
            "shots_pg": stats.get("shots", 0) / games if games > 0 else 0.0,
            "pim_pg": stats.get("pim", 0) / games if games > 0 else 0.0,
            "powerplay_goals": stats.get("powerPlayGoals", 0),
            "powerplay_points": stats.get("powerPlayPoints", 0),
            "shooting_pct": stats.get("shotPct", 0.0),
            "plus_minus": stats.get("plusMinus", 0),
            "games_played": games,
            "toi_per_game": stats.get("timeOnIcePerGame", "0:00")
        }

    def calculate_goalie_stats(self, stats: Dict) -> Dict:
        """Calculate comprehensive goalie stats"""
        games = stats.get("games", 1)

        return {
            "saves_pg": stats.get("saves", 0) / games if games > 0 else 0.0,
            "goals_against_pg": stats.get("goalsAgainst", 0) / games if games > 0 else 0.0,
            "save_pct": stats.get("savePercentage", 0.0),
            "gaa": stats.get("goalAgainstAverage", 0.0),
            "wins": stats.get("wins", 0),
            "losses": stats.get("losses", 0),
            "ot_losses": stats.get("ot", 0),
            "shutouts": stats.get("shutouts", 0),
            "games_played": games,
            "games_started": stats.get("gamesStarted", 0)
        }

    def save_skater_stats(self, player_name: str, team: str, stats: Dict):
        """Save skater stats to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nhl_skater_stats_cache (
                player_name TEXT PRIMARY KEY,
                team TEXT,
                goals_pg REAL,
                assists_pg REAL,
                points_pg REAL,
                shots_pg REAL,
                pim_pg REAL,
                powerplay_goals INTEGER,
                powerplay_points INTEGER,
                shooting_pct REAL,
                plus_minus INTEGER,
                games_played INTEGER,
                toi_per_game TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            INSERT OR REPLACE INTO nhl_skater_stats_cache (
                player_name, team, goals_pg, assists_pg, points_pg, shots_pg, pim_pg,
                powerplay_goals, powerplay_points, shooting_pct, plus_minus,
                games_played, toi_per_game, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            player_name, team,
            stats["goals_pg"], stats["assists_pg"], stats["points_pg"], stats["shots_pg"], stats["pim_pg"],
            stats["powerplay_goals"], stats["powerplay_points"], stats["shooting_pct"], stats["plus_minus"],
            stats["games_played"], stats["toi_per_game"]
        ))

        conn.commit()
        conn.close()

    def save_goalie_stats(self, player_name: str, team: str, stats: Dict):
        """Save goalie stats to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nhl_goalie_stats_cache (
                player_name TEXT PRIMARY KEY,
                team TEXT,
                saves_pg REAL,
                goals_against_pg REAL,
                save_pct REAL,
                gaa REAL,
                wins INTEGER,
                losses INTEGER,
                ot_losses INTEGER,
                shutouts INTEGER,
                games_played INTEGER,
                games_started INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            INSERT OR REPLACE INTO nhl_goalie_stats_cache (
                player_name, team, saves_pg, goals_against_pg, save_pct, gaa,
                wins, losses, ot_losses, shutouts, games_played, games_started, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            player_name, team,
            stats["saves_pg"], stats["goals_against_pg"], stats["save_pct"], stats["gaa"],
            stats["wins"], stats["losses"], stats["ot_losses"], stats["shutouts"],
            stats["games_played"], stats["games_started"]
        ))

        conn.commit()
        conn.close()

    def save_team_stats(self, team_name: str, team_data: Dict):
        """Save team stats to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nhl_team_stats_cache (
                team_name TEXT PRIMARY KEY,
                abbreviation TEXT,
                conference TEXT,
                division TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            INSERT OR REPLACE INTO nhl_team_stats_cache (
                team_name, abbreviation, conference, division, last_updated
            ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            team_name,
            team_data.get("abbreviation", ""),
            team_data.get("conference", {}).get("name", ""),
            team_data.get("division", {}).get("name", "")
        ))

        conn.commit()
        conn.close()

    def scrape_all_nhl_stats(self):
        """Main function to scrape all NHL stats"""
        logger.info("Starting NHL stats scrape...")
        start_time = time.time()

        # Get all teams
        teams = self.get_all_teams()
        logger.info(f"Found {len(teams)} NHL teams")

        skaters_updated = 0
        goalies_updated = 0
        players_failed = 0

        for team in teams:
            team_id = team["id"]
            team_name = team["name"]
            logger.info(f"Processing {team_name}...")

            # Save team stats
            self.save_team_stats(team_name, team)

            # Get roster
            roster = self.get_team_roster(team_id)

            for player_info in roster:
                person = player_info.get("person", {})
                player_id = person.get("id")
                player_name = person.get("fullName", "Unknown")
                position = player_info.get("position", {}).get("code", "")

                try:
                    if position == "G":
                        # Goalie stats
                        stats = self.get_goalie_stats(player_id)
                        if stats:
                            goalie_stats = self.calculate_goalie_stats(stats)
                            self.save_goalie_stats(player_name, team_name, goalie_stats)
                            goalies_updated += 1
                        else:
                            players_failed += 1
                    else:
                        # Skater stats
                        stats = self.get_player_stats(player_id)
                        if stats:
                            skater_stats = self.calculate_skater_stats(stats)
                            self.save_skater_stats(player_name, team_name, skater_stats)
                            skaters_updated += 1
                        else:
                            players_failed += 1

                except Exception as e:
                    logger.error(f"Error processing {player_name}: {e}")
                    players_failed += 1
                    continue

            logger.info(f"  {team_name}: {skaters_updated} skaters, {goalies_updated} goalies")

        elapsed = time.time() - start_time
        logger.info(f"[SUCCESS] NHL stats scrape complete in {elapsed:.1f}s")
        logger.info(f"  Skaters updated: {skaters_updated}")
        logger.info(f"  Goalies updated: {goalies_updated}")
        logger.info(f"  Players failed: {players_failed}")
        logger.info(f"  Teams updated: {len(teams)}")

        return {
            "skaters_updated": skaters_updated,
            "goalies_updated": goalies_updated,
            "players_failed": players_failed,
            "teams_updated": len(teams),
            "elapsed_seconds": elapsed
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape NHL stats from NHL API")
    parser.add_argument("--db", default="../predictions.db", help="Path to predictions database")
    args = parser.parse_args()

    scraper = NHLStatsScraper(args.db)
    result = scraper.scrape_all_nhl_stats()

    print("\n" + "="*50)
    print("NHL STATS SCRAPER - RESULTS")
    print("="*50)
    print(f"Skaters updated: {result['skaters_updated']}")
    print(f"Goalies updated: {result['goalies_updated']}")
    print(f"Players failed: {result['players_failed']}")
    print(f"Teams updated: {result['teams_updated']}")
    print(f"Time elapsed: {result['elapsed_seconds']:.1f}s")
    print("="*50)
