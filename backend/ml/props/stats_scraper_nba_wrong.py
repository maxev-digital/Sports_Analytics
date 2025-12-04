"""
NBA STATS SCRAPER V2 - BallDontLie API (FIXED)
Gets ONLY active 2024-25 season players with stats
"""

import requests
import sqlite3
import time
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NBAStatsScraperV2:
    """Scrape NBA stats from BallDontLie API - only active players"""

    def __init__(self, db_path: str, api_key: str = None):
        self.db_path = Path(db_path)
        self.base_url = "https://api.balldontlie.io/v1"

        # Get API key
        self.api_key = api_key or os.getenv('BALLDONTLIE_API_KEY')
        if not self.api_key:
            raise ValueError("BallDontLie API key required")

        self.session = requests.Session()
        self.session.headers.update({'Authorization': self.api_key})
        self.rate_limit_delay = 0.6

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with rate limiting"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            time.sleep(self.rate_limit_delay)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {endpoint}: {e}")
            return None

    def get_active_players_with_stats(self, season: int = 2024) -> List[Dict]:
        """
        Get ONLY players who have stats in the current season
        This filters out inactive/retired players
        """
        logger.info(f"Fetching active players for {season} season...")
        active_players = []

        # Strategy: Get season averages for all players, this automatically filters to active
        # BallDontLie returns empty for inactive players
        page = 1

        while page <= 50:  # Reasonable limit, ~500 active players max
            params = {
                "season": season,
                "per_page": 100,
                "page": page
            }

            data = self._make_request("season_averages", params=params)
            if not data or "data" not in data:
                break

            season_stats = data["data"]
            if not season_stats:
                break

            logger.info(f"  Page {page}: Found {len(season_stats)} players with stats")

            # For each stat line, we need to get player details
            for stat in season_stats:
                player_id = stat.get("player_id")
                if player_id and stat.get("games_played", 0) > 0:
                    active_players.append({
                        "player_id": player_id,
                        "season_stats": stat
                    })

            # Check pagination
            meta = data.get("meta", {})
            if page >= meta.get("total_pages", 1):
                break
            page += 1

        logger.info(f"Found {len(active_players)} active players with stats")
        return active_players

    def get_player_details(self, player_id: int) -> Optional[Dict]:
        """Get player info (name, team, etc)"""
        data = self._make_request(f"players/{player_id}")
        if data and "data" in data:
            return data["data"]
        return None

    def get_player_game_logs(self, player_id: int, season: int = 2024, limit: int = 10) -> List[Dict]:
        """Fetch player's recent game logs"""
        params = {
            "seasons[]": season,
            "player_ids[]": player_id,
            "per_page": limit
        }

        data = self._make_request("stats", params=params)
        if data and data.get("data"):
            return data["data"]
        return []

    def calculate_player_stats(self, season_avg: Dict, recent_games: List[Dict]) -> Dict:
        """Calculate comprehensive player stats"""

        stats = {
            "ppg": float(season_avg.get("pts", 0)),
            "rpg": float(season_avg.get("reb", 0)),
            "apg": float(season_avg.get("ast", 0)),
            "spg": float(season_avg.get("stl", 0)),
            "bpg": float(season_avg.get("blk", 0)),
            "tpg": float(season_avg.get("turnover", 0)),
            "fg_pct": float(season_avg.get("fg_pct", 0)),
            "fg3_pct": float(season_avg.get("fg3_pct", 0)),
            "ft_pct": float(season_avg.get("ft_pct", 0)),
            "games_played": int(season_avg.get("games_played", 0)),
            "min": season_avg.get("min", "0:00")
        }

        # Calculate last 10 games averages
        if recent_games:
            stats["ppg_l10"] = sum(g.get("pts", 0) for g in recent_games) / len(recent_games)
            stats["rpg_l10"] = sum(g.get("reb", 0) for g in recent_games) / len(recent_games)
            stats["apg_l10"] = sum(g.get("ast", 0) for g in recent_games) / len(recent_games)
            stats["spg_l10"] = sum(g.get("stl", 0) for g in recent_games) / len(recent_games)
            stats["bpg_l10"] = sum(g.get("blk", 0) for g in recent_games) / len(recent_games)
        else:
            stats["ppg_l10"] = stats["ppg"]
            stats["rpg_l10"] = stats["rpg"]
            stats["apg_l10"] = stats["apg"]
            stats["spg_l10"] = stats["spg"]
            stats["bpg_l10"] = stats["bpg"]

        # Derived stats for combo props
        stats["pts_rebs"] = stats["ppg"] + stats["rpg"]
        stats["pts_asts"] = stats["ppg"] + stats["apg"]
        stats["rebs_asts"] = stats["rpg"] + stats["apg"]
        stats["pts_rebs_asts"] = stats["ppg"] + stats["rpg"] + stats["apg"]
        stats["fantasy_score"] = (
            stats["ppg"] +
            stats["rpg"] * 1.2 +
            stats["apg"] * 1.5 +
            stats["spg"] * 3.0 +
            stats["bpg"] * 3.0 -
            stats["tpg"]
        )

        return stats

    def save_player_stats(self, player_name: str, team: str, stats: Dict):
        """Save player stats to database"""
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

        cursor.execute("""
            INSERT OR REPLACE INTO player_stats_cache (
                player_name, team, ppg, rpg, apg, spg, bpg, tpg,
                fg_pct, fg3_pct, ft_pct, games_played, min,
                ppg_l10, rpg_l10, apg_l10, spg_l10, bpg_l10,
                pts_rebs, pts_asts, rebs_asts, pts_rebs_asts, fantasy_score,
                last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            player_name, team,
            stats["ppg"], stats["rpg"], stats["apg"], stats["spg"], stats["bpg"], stats["tpg"],
            stats["fg_pct"], stats["fg3_pct"], stats["ft_pct"], stats["games_played"], stats["min"],
            stats["ppg_l10"], stats["rpg_l10"], stats["apg_l10"], stats["spg_l10"], stats["bpg_l10"],
            stats["pts_rebs"], stats["pts_asts"], stats["rebs_asts"], stats["pts_rebs_asts"], stats["fantasy_score"]
        ))

        conn.commit()
        conn.close()

    def save_team_stats(self, team_name: str, abbreviation: str, conference: str, division: str):
        """Save team stats to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_stats_cache (
                team_name TEXT PRIMARY KEY,
                abbreviation TEXT,
                conference TEXT,
                division TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            INSERT OR REPLACE INTO team_stats_cache (
                team_name, abbreviation, conference, division, last_updated
            ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (team_name, abbreviation, conference, division))

        conn.commit()
        conn.close()

    def scrape_all_nba_stats(self, season: int = 2024):
        """Main function to scrape all active NBA stats"""
        logger.info("Starting NBA stats scrape (BallDontLie API v2)...")
        start_time = time.time()

        # Get active players with stats
        active_players = self.get_active_players_with_stats(season)
        logger.info(f"Processing {len(active_players)} active players...")

        players_updated = 0
        players_failed = 0
        teams_seen = {}

        for idx, player_data in enumerate(active_players):
            player_id = player_data["player_id"]
            season_stats = player_data["season_stats"]

            try:
                # Get player details (name, team)
                player_info = self.get_player_details(player_id)
                if not player_info:
                    logger.warning(f"Could not get info for player ID {player_id}")
                    players_failed += 1
                    continue

                player_name = f"{player_info.get('first_name', '')} {player_info.get('last_name', '')}".strip()
                team = player_info.get("team", {})
                team_name = team.get("full_name", "Free Agent")
                team_abbr = team.get("abbreviation", "FA")

                # Skip free agents
                if team_abbr == "FA":
                    continue

                # Get recent game logs
                recent_games = self.get_player_game_logs(player_id, season, limit=10)

                # Calculate comprehensive stats
                stats = self.calculate_player_stats(season_stats, recent_games)

                # Save to database
                self.save_player_stats(player_name, team_abbr, stats)
                players_updated += 1

                # Track teams
                if team_name not in teams_seen:
                    teams_seen[team_name] = {
                        "abbreviation": team_abbr,
                        "conference": team.get("conference", ""),
                        "division": team.get("division", "")
                    }

                if (idx + 1) % 25 == 0:
                    logger.info(f"Processed {idx + 1}/{len(active_players)} ({players_updated} updated, {players_failed} failed)")

            except Exception as e:
                logger.error(f"Error processing player ID {player_id}: {e}")
                players_failed += 1
                continue

        # Save team stats
        logger.info("Saving team entries...")
        for team_name, team_data in teams_seen.items():
            self.save_team_stats(
                team_name,
                team_data["abbreviation"],
                team_data["conference"],
                team_data["division"]
            )

        elapsed = time.time() - start_time
        logger.info(f"[SUCCESS] NBA stats scrape complete in {elapsed:.1f}s")
        logger.info(f"  Players updated: {players_updated}")
        logger.info(f"  Players failed: {players_failed}")
        logger.info(f"  Teams updated: {len(teams_seen)}")

        return {
            "players_updated": players_updated,
            "players_failed": players_failed,
            "teams_updated": len(teams_seen),
            "elapsed_seconds": elapsed
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape NBA stats from BallDontLie API v2")
    parser.add_argument("--db", default="../predictions.db", help="Path to predictions database")
    parser.add_argument("--api-key", help="BallDontLie API key")
    parser.add_argument("--season", type=int, default=2024, help="Season year")
    args = parser.parse_args()

    scraper = NBAStatsScraperV2(args.db, args.api_key)
    result = scraper.scrape_all_nba_stats(args.season)

    print("\n" + "="*50)
    print("NBA STATS SCRAPER V2 - RESULTS")
    print("="*50)
    print(f"Players updated: {result['players_updated']}")
    print(f"Players failed: {result['players_failed']}")
    print(f"Teams updated: {result['teams_updated']}")
    print(f"Time elapsed: {result['elapsed_seconds']:.1f}s")
    print("="*50)
