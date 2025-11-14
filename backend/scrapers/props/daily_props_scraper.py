"""
Daily Props Lines Scraper
Fetches NBA player props from The Odds API and stores in database
Run daily at 8am CST to capture opening lines

Usage:
    python backend/scrapers/props/daily_props_scraper.py
"""
import sys
import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime, date
import os

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from player_props_client import PlayerPropsClient


class DailyPropsLineScraper:
    """
    Scrapes player props odds and stores opening lines for ML training
    """

    def __init__(self, db_path: str = "data/player_props.db"):
        self.db_path = db_path
        self.client = PlayerPropsClient()

    async def scrape_nba_props(self):
        """
        Fetch all NBA player props for today and store in database
        """
        print("=" * 70)
        print("NBA PLAYER PROPS - DAILY LINES SCRAPER")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Database: {self.db_path}")
        print()

        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Fetch NBA games from The Odds API
        print("[1/4] Fetching NBA games...")
        try:
            import httpx
            url = f"{self.client.base_url}/sports/basketball_nba/events"

            async with httpx.AsyncClient(timeout=30.0) as http_client:
                response = await http_client.get(url, params={
                    "apiKey": os.getenv("ODDS_API_KEY"),
                    "dateFormat": "iso"
                })
                response.raise_for_status()
                games = response.json()

            print(f"  [OK] Found {len(games)} NBA games")

        except Exception as e:
            print(f"  [ERROR] Failed to fetch games: {e}")
            conn.close()
            return

        # Fetch props for all games
        print(f"\n[2/4] Fetching props for {len(games)} games...")
        try:
            nba_props = await self.client.fetch_all_game_props(games)
            print(f"  [OK] Fetched props for {len(nba_props)} games")
        except Exception as e:
            print(f"  [ERROR] Failed to fetch props: {e}")
            conn.close()
            return

        # Parse and store props
        print("\n[3/4] Parsing props data...")
        stored_count = 0
        error_count = 0
        today = date.today()

        for game_id, game_props in nba_props.items():
            # Extract game info
            home_team = game_props.get('home_team', '')
            away_team = game_props.get('away_team', '')
            props_by_market = game_props.get('props_by_market', {})

            for market_key, props_list in props_by_market.items():
                # Convert market key to prop type
                prop_type = self._convert_market_key(market_key)

                # props_list is a list of player props
                for prop_data in props_list:
                    try:
                        # Extract player name and line
                        player_name = prop_data.get("player_name", "")
                        market_line = prop_data.get("line", 0.0)

                        if not player_name:
                            continue

                        # Get bookmakers odds
                        bookmakers_dict = prop_data.get("bookmakers", {})
                        if not bookmakers_dict:
                            continue

                        # Find best over and under odds across all bookmakers
                        best_over_odds = -110  # Default
                        best_under_odds = -110
                        best_bookmaker = "UNKNOWN"

                        for bookmaker_name, odds in bookmakers_dict.items():
                            over_odds = odds.get("over", -110)
                            under_odds = odds.get("under", -110)

                            if over_odds > best_over_odds:
                                best_over_odds = over_odds
                                best_bookmaker = bookmaker_name
                            if under_odds > best_under_odds:
                                best_under_odds = under_odds

                        # Determine team and opponent (simple heuristic - improve later)
                        team = home_team  # Assume home for now
                        opponent = away_team
                        home_away = "HOME"
                        player_id = f"{player_name.replace(' ', '_')}_{team}"  # Simple ID

                        # Store in database
                        cursor.execute("""
                            INSERT OR REPLACE INTO player_props_lines
                            (date, game_id, player_id, player_name, team, opponent,
                             home_away, prop_type, market_line, over_odds, under_odds, bookmaker)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            today,
                            game_id,
                            player_id,
                            player_name,
                            team,
                            opponent,
                            home_away,
                            prop_type,
                            market_line,
                            best_over_odds,
                            best_under_odds,
                            best_bookmaker
                        ))

                        stored_count += 1

                    except Exception as e:
                        error_count += 1
                        print(f"  [ERROR] Failed to store {player_name} {prop_type}: {e}")

        # Commit to database
        conn.commit()

        print(f"  [OK] Parsed {stored_count + error_count} props")
        if error_count > 0:
            print(f"  [WARN] {error_count} errors encountered")

        # Summary statistics
        print("\n[4/4] Summary statistics...")

        # Count by prop type
        cursor.execute("""
            SELECT prop_type, COUNT(*)
            FROM player_props_lines
            WHERE date = ?
            GROUP BY prop_type
        """, (today,))

        prop_counts = cursor.fetchall()
        print(f"  Props stored today ({today}):")
        total_props = 0
        for prop_type, count in prop_counts:
            print(f"    - {prop_type}: {count}")
            total_props += count

        # Total records in database
        cursor.execute("SELECT COUNT(*) FROM player_props_lines")
        total_all_time = cursor.fetchone()[0]

        conn.close()

        print(f"\n  Total props today: {total_props}")
        print(f"  Total props all-time: {total_all_time}")

        print("\n" + "=" * 70)
        print("[SUCCESS] Daily props lines scrape complete!")
        print("=" * 70)

        return {
            "date": str(today),
            "props_stored": stored_count,
            "errors": error_count,
            "total_all_time": total_all_time
        }

    def _convert_market_key(self, market_key: str) -> str:
        """
        Convert The Odds API market key to our prop type
        """
        mapping = {
            "player_points": "points",
            "player_rebounds": "rebounds",
            "player_assists": "assists",
            "player_threes": "threes",
            "player_blocks": "blocks",
            "player_steals": "steals",
            "player_points_rebounds_assists": "PRA"
        }
        return mapping.get(market_key, market_key)


async def main():
    """
    Main entry point for daily scraper
    """
    scraper = DailyPropsLineScraper()
    result = await scraper.scrape_nba_props()

    if result:
        print(f"\nScrape completed successfully!")
        print(f"Stored: {result['props_stored']} props")
        print(f"Errors: {result['errors']}")
        print(f"Database now has: {result['total_all_time']} total props")

    # Backup recommendation
    print("\n" + "=" * 70)
    print("REMINDER: Run backup script to save this data!")
    print("  python backup_props_data.py")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
