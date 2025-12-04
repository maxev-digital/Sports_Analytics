"""
NHL STATS SCRAPER - MoneyPuck API Integration
Fetches real player and team stats for hockey props using MoneyPuck (FREE, reliable)
MoneyPuck provides comprehensive NHL data without requiring API keys
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

class NHLStatsScraperMoneyPuck:
    """Scrape NHL stats from MoneyPuck API (FREE, no key required)"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.base_url = "http://moneypuck.com/moneypuck/playerData/seasonSummary"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.rate_limit_delay = 0.3

        # Team abbreviation mapping
        self.team_mapping = {
            "ANA": "Anaheim Ducks", "ARI": "Arizona Coyotes", "BOS": "Boston Bruins",
            "BUF": "Buffalo Sabres", "CAR": "Carolina Hurricanes", "CBJ": "Columbus Blue Jackets",
            "CGY": "Calgary Flames", "CHI": "Chicago Blackhawks", "COL": "Colorado Avalanche",
            "DAL": "Dallas Stars", "DET": "Detroit Red Wings", "EDM": "Edmonton Oilers",
            "FLA": "Florida Panthers", "L.A": "Los Angeles Kings", "MIN": "Minnesota Wild",
            "MTL": "Montreal Canadiens", "N.J": "New Jersey Devils", "NSH": "Nashville Predators",
            "NYI": "New York Islanders", "NYR": "New York Rangers", "OTT": "Ottawa Senators",
            "PHI": "Philadelphia Flyers", "PIT": "Pittsburgh Penguins", "S.J": "San Jose Sharks",
            "SEA": "Seattle Kraken", "STL": "St. Louis Blues", "T.B": "Tampa Bay Lightning",
            "TOR": "Toronto Maple Leafs", "VAN": "Vancouver Canucks", "VGK": "Vegas Golden Knights",
            "WPG": "Winnipeg Jets", "WSH": "Washington Capitals", "UTA": "Utah Hockey Club"
        }

    def _make_request(self, endpoint: str, season: str = "2024") -> Optional[List[Dict]]:
        """
        Make API request to MoneyPuck
        Season format: "2024" for 2024-25 season
        Endpoints: "skaters" or "goalies"
        """
        try:
            # MoneyPuck endpoint: individual player stats
            url = f"{self.base_url}/{season}/regular/{endpoint}.csv"
            logger.info(f"Fetching from: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            # Parse CSV response
            import csv
            from io import StringIO

            csv_data = StringIO(response.text)
            reader = csv.DictReader(csv_data)
            players = list(reader)

            time.sleep(self.rate_limit_delay)
            return players

        except Exception as e:
            logger.error(f"MoneyPuck API request failed: {e}")
            return None

    def create_database_tables(self):
        """Create NHL stats tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Skaters table
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

        # Goalies table
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

        # Team stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nhl_team_stats_cache (
                team_name TEXT PRIMARY KEY,
                abbreviation TEXT,
                conference TEXT,
                division TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        logger.info("NHL database tables created/verified")

    def parse_skater_stats(self, player_data: Dict) -> Dict:
        """Parse skater stats from MoneyPuck data"""
        try:
            games = int(float(player_data.get("games_played", 1)))
            if games == 0:
                games = 1

            goals = int(float(player_data.get("I_F_goals", 0)))
            assists = int(float(player_data.get("I_F_primaryAssists", 0))) + int(float(player_data.get("I_F_secondaryAssists", 0)))
            shots = int(float(player_data.get("I_F_shotsOnGoal", 0)))

            return {
                "goals_pg": goals / games,
                "assists_pg": assists / games,
                "points_pg": (goals + assists) / games,
                "shots_pg": shots / games,
                "pim_pg": float(player_data.get("penalityMinutes", 0)) / games,
                "powerplay_goals": int(float(player_data.get("I_F_goals_powerPlay", 0))),
                "powerplay_points": int(float(player_data.get("I_F_points_powerPlay", 0))),
                "shooting_pct": float(player_data.get("I_F_shootingPct", 0)),
                "plus_minus": int(float(player_data.get("I_F_plusMinus", 0))),
                "games_played": games,
                "toi_per_game": str(int(float(player_data.get("icetime", 0)) / games / 60)) + ":00"
            }
        except Exception as e:
            logger.error(f"Error parsing skater stats: {e}")
            return None

    def parse_goalie_stats(self, player_data: Dict) -> Dict:
        """Parse goalie stats from MoneyPuck data"""
        try:
            games = int(float(player_data.get("games_played", 1)))
            if games == 0:
                games = 1

            saves = int(float(player_data.get("shotsOnGoalAgainst", 0))) - int(float(player_data.get("goalsAgainst", 0)))

            return {
                "saves_pg": saves / games,
                "goals_against_pg": float(player_data.get("goalsAgainst", 0)) / games,
                "save_pct": float(player_data.get("savedShotsOnGoalPct", 0)),
                "gaa": float(player_data.get("goalsAgainst", 0)) / games,
                "wins": int(float(player_data.get("wins", 0))),
                "losses": int(float(player_data.get("losses", 0))),
                "ot_losses": int(float(player_data.get("ot", 0))),
                "shutouts": int(float(player_data.get("shutouts", 0))),
                "games_played": games,
                "games_started": games  # MoneyPuck doesn't distinguish
            }
        except Exception as e:
            logger.error(f"Error parsing goalie stats: {e}")
            return None

    def save_skater_stats(self, player_name: str, team: str, stats: Dict):
        """Save skater stats to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

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

    def scrape_all_nhl_stats(self, season: str = "2024"):
        """Main function to scrape all NHL stats from MoneyPuck"""
        logger.info("Starting NHL stats scrape from MoneyPuck...")
        start_time = time.time()

        # Create tables first
        self.create_database_tables()

        skaters_updated = 0
        goalies_updated = 0
        players_failed = 0
        teams_processed = set()

        # Get skaters data
        logger.info("Fetching skaters...")
        skaters_data = self._make_request("skaters", season)
        if skaters_data:
            logger.info(f"Found {len(skaters_data)} skaters from MoneyPuck")
            for player_data in skaters_data:
                try:
                    player_name = player_data.get("name", "").strip()
                    if not player_name:
                        continue

                    team_abbr = player_data.get("team", "")
                    team_name = self.team_mapping.get(team_abbr, team_abbr)
                    teams_processed.add(team_name)

                    games_played = int(float(player_data.get("games_played", 0)))
                    if games_played < 1:
                        continue

                    stats = self.parse_skater_stats(player_data)
                    if stats:
                        self.save_skater_stats(player_name, team_name, stats)
                        skaters_updated += 1
                    else:
                        players_failed += 1

                except Exception as e:
                    logger.error(f"Error processing skater {player_name}: {e}")
                    players_failed += 1
                    continue
        else:
            logger.error("Failed to fetch skaters data from MoneyPuck")

        # Get goalies data
        logger.info("Fetching goalies...")
        goalies_data = self._make_request("goalies", season)
        if goalies_data:
            logger.info(f"Found {len(goalies_data)} goalies from MoneyPuck")
            for player_data in goalies_data:
                try:
                    player_name = player_data.get("name", "").strip()
                    if not player_name:
                        continue

                    team_abbr = player_data.get("team", "")
                    team_name = self.team_mapping.get(team_abbr, team_abbr)
                    teams_processed.add(team_name)

                    games_played = int(float(player_data.get("games_played", 0)))
                    if games_played < 1:
                        continue

                    stats = self.parse_goalie_stats(player_data)
                    if stats:
                        self.save_goalie_stats(player_name, team_name, stats)
                        goalies_updated += 1
                    else:
                        players_failed += 1

                except Exception as e:
                    logger.error(f"Error processing goalie {player_name}: {e}")
                    players_failed += 1
                    continue
        else:
            logger.error("Failed to fetch goalies data from MoneyPuck")

        elapsed = time.time() - start_time
        logger.info(f"[SUCCESS] NHL stats scrape complete in {elapsed:.1f}s")
        logger.info(f"  Skaters updated: {skaters_updated}")
        logger.info(f"  Goalies updated: {goalies_updated}")
        logger.info(f"  Players failed: {players_failed}")
        logger.info(f"  Teams updated: {len(teams_processed)}")

        return {
            "skaters_updated": skaters_updated,
            "goalies_updated": goalies_updated,
            "players_failed": players_failed,
            "teams_updated": len(teams_processed),
            "elapsed_seconds": elapsed
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape NHL stats from MoneyPuck API")
    parser.add_argument("--db", default="../predictions.db", help="Path to predictions database")
    parser.add_argument("--season", default="2024", help="Season (2024 for 2024-25)")
    args = parser.parse_args()

    scraper = NHLStatsScraperMoneyPuck(args.db)
    result = scraper.scrape_all_nhl_stats(args.season)

    print("\n" + "="*50)
    print("NHL STATS SCRAPER (MoneyPuck) - RESULTS")
    print("="*50)
    print(f"Skaters updated: {result['skaters_updated']}")
    print(f"Goalies updated: {result['goalies_updated']}")
    print(f"Players failed: {result['players_failed']}")
    print(f"Teams updated: {result['teams_updated']}")
    print(f"Time elapsed: {result['elapsed_seconds']:.1f}s")
    print("="*50)
