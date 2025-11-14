"""
Historical Props Data Backfill
Rapidly build training dataset by fetching historical props and grading them

Strategy:
1. Get historical NBA games from BallDontLie (last 30-60 days)
2. For each game, fetch player stats
3. Simulate props lines based on season averages
4. Grade props with actual game outcomes
5. Store in database for ML training

This gives us 1,000s of training samples in hours instead of weeks.
"""

import sys
import sqlite3
import asyncio
import numpy as np
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import time

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.props.balldontlie_client import BallDontLieClient


class HistoricalPropsBackfill:
    """
    Backfills historical props data for ML training
    """

    def __init__(self, db_path: str = "data/player_props.db"):
        self.db_path = db_path
        self.stats_client = BallDontLieClient()
        self.current_season = 2024  # 2024-25 season

    def backfill_last_n_days(self, days: int = 30, min_minutes: float = 20.0):
        """
        Backfill props data for the last N days

        Args:
            days: Number of days to backfill
            min_minutes: Minimum minutes played to include player
        """
        print(f"\n{'='*70}")
        print(f"HISTORICAL PROPS BACKFILL - LAST {days} DAYS")
        print(f"{'='*70}\n")

        start_date = date.today() - timedelta(days=days)
        end_date = date.today() - timedelta(days=1)  # Yesterday

        print(f"Period: {start_date} to {end_date}")
        print(f"Min minutes filter: {min_minutes}")
        print()

        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Statistics
        total_props_created = 0
        total_props_graded = 0
        total_games_processed = 0
        errors = 0

        # Get all NBA games in date range
        print(f"[1/3] Fetching NBA games from BallDontLie...")

        current_date = start_date
        all_game_ids = []

        while current_date <= end_date:
            try:
                # BallDontLie games endpoint with date filter
                games = self.stats_client.get_games_by_date(current_date)

                if games:
                    game_ids = [g['id'] for g in games]
                    all_game_ids.extend(game_ids)
                    print(f"  {current_date}: Found {len(games)} games")

                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                print(f"  [ERROR] Failed to fetch games for {current_date}: {e}")
                errors += 1

            current_date += timedelta(days=1)

        print(f"  [OK] Found {len(all_game_ids)} total games\n")

        # Process each game
        print(f"[2/3] Processing games and generating props...")

        for i, game_id in enumerate(all_game_ids, 1):
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(all_game_ids)} games ({i/len(all_game_ids)*100:.1f}%)")

            try:
                # Get game details and player stats
                game_stats = self.stats_client.get_game_stats(game_id)

                if not game_stats:
                    print(f"  [WARN] No stats for game {game_id}")
                    continue

                if i <= 3:  # Debug first few games
                    print(f"  [DEBUG] Game {game_id}: {len(game_stats.get('data', []))} player stats")

                # Process all players in the game
                player_stats_list = game_stats.get('data', [])

                if not player_stats_list:
                    continue

                # Get game info from first player's stats (all players have same game info)
                first_player = player_stats_list[0]
                game_info = first_player.get('game', {})
                game_date_str = game_info.get('date', '')[:10]

                if not game_date_str:
                    continue

                game_date = datetime.fromisoformat(game_date_str).date()
                home_team = game_info.get('home_team', {}).get('abbreviation', 'UNK')
                away_team = game_info.get('visitor_team', {}).get('abbreviation', 'UNK')

                for player_stat in player_stats_list:
                    # Filter by minutes played
                    minutes = player_stat.get('min', '0')

                    # Convert minutes string to float (format: "32:15" or "32")
                    try:
                        if ':' in str(minutes):
                            mins_parts = str(minutes).split(':')
                            minutes_float = float(mins_parts[0]) + float(mins_parts[1]) / 60
                        else:
                            minutes_float = float(minutes) if minutes else 0.0
                    except:
                        minutes_float = 0.0

                    if minutes_float < min_minutes:
                        continue

                    # Extract player info
                    player_info = player_stat.get('player', {})
                    player_id = player_info.get('id')
                    player_name = f"{player_info.get('first_name', '')} {player_info.get('last_name', '')}".strip()
                    player_team = player_stat.get('team', {}).get('abbreviation', 'UNK')

                    if not player_name or not player_id:
                        continue

                    # Determine home/away
                    is_home = player_team == home_team
                    opponent = away_team if is_home else home_team
                    home_away = "HOME" if is_home else "AWAY"

                    # Generate props for each stat type
                    prop_types = {
                        'points': player_stat.get('pts', 0),
                        'rebounds': player_stat.get('reb', 0),
                        'assists': player_stat.get('ast', 0),
                        'threes': player_stat.get('fg3m', 0),
                        'blocks': player_stat.get('blk', 0),
                        'steals': player_stat.get('stl', 0)
                    }

                    # Add PRA
                    prop_types['PRA'] = (
                        player_stat.get('pts', 0) +
                        player_stat.get('reb', 0) +
                        player_stat.get('ast', 0)
                    )

                    # Get season average for line estimation
                    season_avg = self.stats_client.get_player_season_averages(
                        player_id, self.current_season
                    )

                    for prop_type, actual_value in prop_types.items():
                        if actual_value == 0:
                            continue  # Skip if player didn't record this stat

                        # Estimate market line from season average
                        if season_avg:
                            if prop_type == 'PRA':
                                market_line = (
                                    season_avg.get('pts', 0) +
                                    season_avg.get('reb', 0) +
                                    season_avg.get('ast', 0)
                                )
                            else:
                                stat_key = {
                                    'points': 'pts',
                                    'rebounds': 'reb',
                                    'assists': 'ast',
                                    'threes': 'fg3m',
                                    'blocks': 'blk',
                                    'steals': 'stl'
                                }.get(prop_type, prop_type)
                                market_line = season_avg.get(stat_key, 0)
                                if market_line == 0:
                                    # No season avg - add random variance to actual value
                                    market_line = actual_value + np.random.uniform(-2.5, 2.5)
                        else:
                            # No season avg - add random variance to actual value
                            # This creates realistic lines that can hit over or under
                            market_line = actual_value + np.random.uniform(-2.5, 2.5)

                        # Round to .5 (typical props lines)
                        market_line = round(market_line * 2) / 2

                        if market_line <= 0:
                            continue

                        # Store props line
                        try:
                            cursor.execute("""
                                INSERT OR IGNORE INTO player_props_lines
                                (date, game_id, player_id, player_name, team, opponent,
                                 home_away, prop_type, market_line, over_odds, under_odds, bookmaker)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                game_date,
                                str(game_id),
                                str(player_id),
                                player_name,
                                player_team,
                                opponent,
                                home_away,
                                prop_type,
                                market_line,
                                -110,  # Standard odds
                                -110,
                                "HISTORICAL_BACKFILL"
                            ))
                            total_props_created += cursor.rowcount

                        except Exception as e:
                            print(f"  [ERROR] Failed to store line: {e}")
                            errors += 1

                        # Store result
                        try:
                            hit = actual_value > market_line
                            difference = actual_value - market_line

                            cursor.execute("""
                                INSERT OR IGNORE INTO player_props_results
                                (date, player_id, player_name, team, opponent, prop_type,
                                 market_line, actual_value, hit, difference)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                game_date,
                                str(player_id),
                                player_name,
                                player_team,
                                opponent,
                                prop_type,
                                market_line,
                                actual_value,
                                hit,
                                difference
                            ))
                            total_props_graded += cursor.rowcount

                        except Exception as e:
                            print(f"  [ERROR] Failed to store result: {e}")
                            errors += 1

                total_games_processed += 1
                conn.commit()  # Commit after each game

            except Exception as e:
                print(f"  [ERROR] Failed to process game {game_id}: {e}")
                errors += 1

            # Rate limiting
            time.sleep(0.3)

        # Summary
        print(f"\n[3/3] Summary statistics...")

        cursor.execute("SELECT COUNT(*) FROM player_props_lines WHERE bookmaker = 'HISTORICAL_BACKFILL'")
        total_lines = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM player_props_results")
        total_results = cursor.fetchone()[0]

        cursor.execute("""
            SELECT prop_type, COUNT(*),
                   SUM(CASE WHEN hit = 1 THEN 1 ELSE 0 END) as hits
            FROM player_props_results
            GROUP BY prop_type
        """)
        prop_breakdown = cursor.fetchall()

        conn.close()

        print(f"\n{'='*70}")
        print(f"BACKFILL COMPLETE")
        print(f"{'='*70}")
        print(f"Games processed: {total_games_processed}")
        print(f"Props lines created: {total_lines}")
        print(f"Props results graded: {total_results}")
        print(f"Errors: {errors}")
        print(f"\nBreakdown by prop type:")
        for prop_type, count, hits in prop_breakdown:
            hit_rate = (hits / count * 100) if count > 0 else 0
            print(f"  {prop_type}: {count} props ({hit_rate:.1f}% hit rate)")
        print(f"{'='*70}\n")

        return {
            'games_processed': total_games_processed,
            'props_created': total_lines,
            'props_graded': total_results,
            'errors': errors
        }


def main():
    """
    Main entry point - backfill last 30 days
    """
    import argparse

    parser = argparse.ArgumentParser(description='Backfill historical props data')
    parser.add_argument('--days', type=int, default=30, help='Number of days to backfill (default: 30)')
    parser.add_argument('--min-minutes', type=float, default=20.0, help='Minimum minutes played (default: 20.0)')

    args = parser.parse_args()

    backfiller = HistoricalPropsBackfill()
    result = backfiller.backfill_last_n_days(
        days=args.days,
        min_minutes=args.min_minutes
    )

    print(f"\n[SUCCESS] Backfill successful!")
    print(f"[DATA] Database now has {result['props_graded']} graded props for training")
    print(f"\n[BACKUP] Run backup script to save this data:")
    print(f"   python backup_props_data.py\n")


if __name__ == "__main__":
    main()
