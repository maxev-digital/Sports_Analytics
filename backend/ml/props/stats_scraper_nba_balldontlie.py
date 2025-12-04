"""
NBA STATS SCRAPER - BallDontLie API Integration
Fetches real player and team stats to populate player_stats_cache and team_stats_cache
Requires BallDontLie API key (paid tier for full access)
"""

import requests
import sqlite3
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NBAStatsScraperBallDontLie:
    """Scrape NBA stats from BallDontLie API v1"""

    def __init__(self, db_path: str, api_key: Optional[str] = None):
        self.db_path = Path(db_path)
        self.api_key = api_key or os.getenv("BALLDONTLIE_API_KEY")

        if not self.api_key:
            raise ValueError("BallDontLie API key required. Set BALLDONTLIE_API_KEY env var or pass as parameter")

        self.base_url = "https://api.balldontlie.io/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': self.api_key,
            'Accept': 'application/json'
        })
        self.rate_limit_delay = 1.2  # Conservative rate limiting (60 req/min max)
        self.max_retries = 3

    def _make_request(self, endpoint: str, params: Dict = None, retry_count: int = 0) -> Optional[Dict]:
        """Make API request with rate limiting and exponential backoff"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            time.sleep(self.rate_limit_delay)
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                if retry_count < self.max_retries:
                    wait_time = (2 ** retry_count) * 2  # Exponential backoff: 2, 4, 8 seconds
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry {retry_count + 1}/{self.max_retries}")
                    time.sleep(wait_time)
                    return self._make_request(endpoint, params, retry_count + 1)
                else:
                    logger.error(f"Rate limit exceeded after {self.max_retries} retries")
                    return None
            else:
                logger.error(f"HTTP {e.response.status_code} for {endpoint}: {e}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {endpoint}: {e}")
            return None

    def get_all_players(self, per_page: int = 100) -> List[Dict]:
        """Fetch all active NBA players with pagination"""
        logger.info("Fetching all NBA players from BallDontLie...")

        all_players = []
        cursor = None

        while True:
            params = {
                "per_page": per_page,
                "active": "true"  # Only active players
            }
            if cursor:
                params["cursor"] = cursor

            data = self._make_request("players", params=params)
            if not data or "data" not in data:
                break

            players = data["data"]
            all_players.extend(players)

            # Check for next page
            cursor = data.get("meta", {}).get("next_cursor")
            if not cursor:
                break

            logger.info(f"Fetched {len(all_players)} players so far...")

        logger.info(f"Found {len(all_players)} total active NBA players")
        return all_players

    def get_player_season_averages(self, player_id: int, season: str = "2025") -> Optional[Dict]:
        """
        Fetch player season averages
        Season: "2024" for 2024-25 season (BallDontLie uses just the start year)
        """
        params = {
            "season": season
        }

        # BallDontLie v1 uses different endpoint structure
        try:
            url = f"{self.base_url}/stats"
            params_with_player = {
                **params,
                "player_ids[]": [player_id],
                "per_page": 100
            }

            response = self.session.get(url, params=params_with_player, timeout=15)
            response.raise_for_status()
            time.sleep(self.rate_limit_delay)

            data = response.json()
            if data and "data" in data and len(data["data"]) > 0:
                # Calculate averages from stats
                return self._calculate_season_averages(data["data"])
            return None
        except Exception as e:
            logger.error(f"Failed to get season averages for player {player_id}: {e}")
            return None

    def _calculate_season_averages(self, stats_list: List[Dict]) -> Dict:
        """Calculate season averages from game stats"""
        if not stats_list:
            return {}

        total_games = len(stats_list)
        if total_games == 0:
            return {}

        # Sum up all stats
        totals = {
            "pts": 0, "reb": 0, "ast": 0, "stl": 0, "blk": 0,
            "turnover": 0, "fg_pct": 0, "fg3_pct": 0, "ft_pct": 0
        }
        total_minutes = 0

        for game in stats_list:
            for key in totals.keys():
                totals[key] += float(game.get(key, 0) or 0)

            # Handle minutes specially (comes as "MM:SS" string)
            min_str = game.get("min", "0:00") or "0:00"
            if isinstance(min_str, str) and ":" in min_str:
                parts = min_str.split(":")
                total_minutes += int(parts[0]) + (int(parts[1]) / 60 if len(parts) > 1 else 0)
            else:
                total_minutes += float(min_str or 0)

        # Calculate averages
        avg_minutes = total_minutes / total_games if total_games > 0 else 0
        return {
            "pts": totals["pts"] / total_games,
            "reb": totals["reb"] / total_games,
            "ast": totals["ast"] / total_games,
            "stl": totals["stl"] / total_games,
            "blk": totals["blk"] / total_games,
            "turnover": totals["turnover"] / total_games,
            "fg_pct": totals["fg_pct"] / total_games,
            "fg3_pct": totals["fg3_pct"] / total_games,
            "ft_pct": totals["ft_pct"] / total_games,
            "min": str(int(avg_minutes)),
            "games_played": total_games
        }

    def get_player_last_n_games(self, player_id: int, n: int = 10) -> List[Dict]:
        """Fetch player's last N game stats"""
        today = datetime.now()
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        params = {
            "player_ids[]": player_id,
            "start_date": start_date,
            "end_date": end_date,
            "per_page": n
        }

        data = self._make_request("stats", params=params)
        if data and "data" in data:
            return data["data"][:n]
        return []

    def calculate_last_n_averages(self, games: List[Dict]) -> Dict:
        """Calculate averages from last N games"""
        if not games:
            return {}

        total_pts = sum(g.get("pts", 0) or 0 for g in games)
        total_reb = sum(g.get("reb", 0) or 0 for g in games)
        total_ast = sum(g.get("ast", 0) or 0 for g in games)
        total_stl = sum(g.get("stl", 0) or 0 for g in games)
        total_blk = sum(g.get("blk", 0) or 0 for g in games)
        n = len(games)

        return {
            "ppg": total_pts / n if n > 0 else 0.0,
            "rpg": total_reb / n if n > 0 else 0.0,
            "apg": total_ast / n if n > 0 else 0.0,
            "spg": total_stl / n if n > 0 else 0.0,
            "bpg": total_blk / n if n > 0 else 0.0
        }

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_stats_cache (
                team_name TEXT PRIMARY KEY,
                abbreviation TEXT,
                conference TEXT,
                division TEXT,
                offensive_rating REAL,
                defensive_rating REAL,
                pace REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        logger.info("NBA database tables created/verified")

    def save_player_stats(self, player_name: str, team_abbr: str, season_stats: Dict, last_10_stats: Dict):
        """Save comprehensive player stats to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate derived stats
        ppg = season_stats.get("pts", 0) or 0
        rpg = season_stats.get("reb", 0) or 0
        apg = season_stats.get("ast", 0) or 0

        pts_rebs = ppg + rpg
        pts_asts = ppg + apg
        rebs_asts = rpg + apg
        pts_rebs_asts = ppg + rpg + apg

        # Simple fantasy score calculation
        fantasy_score = ppg + (rpg * 1.2) + (apg * 1.5) + (season_stats.get("stl", 0) or 0) * 3 + (season_stats.get("blk", 0) or 0) * 3

        cursor.execute("""
            INSERT OR REPLACE INTO player_stats_cache (
                player_name, team, ppg, rpg, apg, spg, bpg, tpg,
                fg_pct, fg3_pct, ft_pct, games_played, min,
                ppg_l10, rpg_l10, apg_l10, spg_l10, bpg_l10,
                pts_rebs, pts_asts, rebs_asts, pts_rebs_asts,
                fantasy_score, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            player_name, team_abbr,
            ppg, rpg, apg,
            season_stats.get("stl", 0) or 0,
            season_stats.get("blk", 0) or 0,
            season_stats.get("turnover", 0) or 0,
            season_stats.get("fg_pct", 0) or 0,
            season_stats.get("fg3_pct", 0) or 0,
            season_stats.get("ft_pct", 0) or 0,
            season_stats.get("games_played", 0) or 0,
            season_stats.get("min", "0") or "0",
            last_10_stats.get("ppg", ppg),
            last_10_stats.get("rpg", rpg),
            last_10_stats.get("apg", apg),
            last_10_stats.get("spg", season_stats.get("stl", 0) or 0),
            last_10_stats.get("bpg", season_stats.get("blk", 0) or 0),
            pts_rebs, pts_asts, rebs_asts, pts_rebs_asts,
            fantasy_score
        ))

        conn.commit()
        conn.close()

    def scrape_all_nba_stats(self, season: str = "2025"):
        """Main function to scrape all NBA stats"""
        logger.info("Starting NBA stats scrape from BallDontLie...")
        start_time = time.time()

        # Create tables first
        self.create_database_tables()

        # Get all players (only active ones)
        all_players = self.get_all_players()
        if not all_players:
            logger.error("Failed to fetch players")
            return {
                "players_updated": 0,
                "players_failed": 0,
                "elapsed_seconds": 0
            }

        # Filter to only players with teams (active roster)
        players = [p for p in all_players if p.get("team", {}).get("abbreviation") not in ["FA", None, ""]]
        logger.info(f"Filtering to {len(players)} active players (from {len(all_players)} total)")

        players_updated = 0
        players_failed = 0
        players_skipped = 0

        for i, player in enumerate(players, 1):
            try:
                player_id = player.get("id")
                player_name = f"{player.get('first_name', '')} {player.get('last_name', '')}".strip()
                team_abbr = player.get("team", {}).get("abbreviation", "")

                if not player_name or not team_abbr:
                    players_skipped += 1
                    continue

                # Get season stats
                season_stats = self.get_player_season_averages(player_id, season)
                if not season_stats or season_stats.get("games_played", 0) < 1:
                    players_skipped += 1
                    continue

                # For last 10, use same as season for now (simplify API calls)
                last_10_stats = {
                    "ppg": season_stats.get("pts", 0),
                    "rpg": season_stats.get("reb", 0),
                    "apg": season_stats.get("ast", 0),
                    "spg": season_stats.get("stl", 0),
                    "bpg": season_stats.get("blk", 0)
                }

                # Save to database
                self.save_player_stats(player_name, team_abbr, season_stats, last_10_stats)
                players_updated += 1

                if i % 25 == 0:
                    logger.info(f"Progress: {i}/{len(players)} processed, {players_updated} updated, {players_skipped} skipped")

            except Exception as e:
                logger.error(f"Error processing {player_name}: {e}")
                players_failed += 1
                continue

        elapsed = time.time() - start_time
        logger.info(f"[SUCCESS] NBA stats scrape complete in {elapsed:.1f}s")
        logger.info(f"  Players updated: {players_updated}")
        logger.info(f"  Players skipped (no stats): {players_skipped}")
        logger.info(f"  Players failed: {players_failed}")

        return {
            "players_updated": players_updated,
            "players_failed": players_failed,
            "elapsed_seconds": elapsed
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape NBA stats from BallDontLie API")
    parser.add_argument("--db", default="../predictions.db", help="Path to predictions database")
    parser.add_argument("--season", type=int, default=2024, help="Season (2024 for 2024-25)")
    parser.add_argument("--api-key", help="BallDontLie API key (or set BALLDONTLIE_API_KEY env var)")
    args = parser.parse_args()

    try:
        scraper = NBAStatsScraperBallDontLie(args.db, args.api_key)
        result = scraper.scrape_all_nba_stats(args.season)

        print("\n" + "="*50)
        print("NBA STATS SCRAPER (BallDontLie) - RESULTS")
        print("="*50)
        print(f"Players updated: {result['players_updated']}")
        print(f"Players failed: {result['players_failed']}")
        print(f"Time elapsed: {result['elapsed_seconds']:.1f}s")
        print("="*50)
    except ValueError as e:
        print(f"\n[ERROR] {e}")
        print("Please set BALLDONTLIE_API_KEY environment variable or use --api-key flag")
