"""
Aggregate Player Season Stats from Existing Box Scores
Uses the 15,530 box scores we already have in player_props_results table

NO API CALLS - uses existing data only
"""

import sqlite3
from datetime import date
from collections import defaultdict
import json
import os

def aggregate_player_stats(db_path: str = "data/player_props.db"):
    """
    Calculate season averages from existing box score data
    """
    print(f"\n{'='*70}")
    print("AGGREGATING PLAYER STATS FROM EXISTING BOX SCORES")
    print(f"{'='*70}\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all box scores
    print("[1/3] Loading box scores from database...")
    cursor.execute("""
        SELECT date, player_id, player_name, team, prop_type, actual_value
        FROM player_props_results
        ORDER BY date, player_id
    """)

    results = cursor.fetchall()
    print(f"  [OK] Loaded {len(results)} box scores\n")

    # Aggregate by player
    print("[2/3] Calculating player season averages...")
    player_stats = defaultdict(lambda: {
        'team': None,
        'games': set(),
        'points': [],
        'rebounds': [],
        'assists': [],
        'threes': [],
        'blocks': [],
        'steals': []
    })

    for date_str, player_id, player_name, team, prop_type, actual_value in results:
        stats = player_stats[player_id]
        stats['player_name'] = player_name
        stats['team'] = team
        stats['games'].add(date_str)

        # Map prop_type to stat category
        if prop_type == 'points':
            stats['points'].append(actual_value)
        elif prop_type == 'rebounds':
            stats['rebounds'].append(actual_value)
        elif prop_type == 'assists':
            stats['assists'].append(actual_value)
        elif prop_type == 'threes':
            stats['threes'].append(actual_value)
        elif prop_type == 'blocks':
            stats['blocks'].append(actual_value)
        elif prop_type == 'steals':
            stats['steals'].append(actual_value)

    print(f"  [OK] Calculated stats for {len(player_stats)} players\n")

    # Calculate averages and save to database
    print("[3/3] Saving to player_stats_cache...")

    saved_count = 0
    for player_id, stats in player_stats.items():
        games_played = len(stats['games'])

        if games_played == 0:
            continue

        # Calculate averages
        ppg = sum(stats['points']) / len(stats['points']) if stats['points'] else 0
        rpg = sum(stats['rebounds']) / len(stats['rebounds']) if stats['rebounds'] else 0
        apg = sum(stats['assists']) / len(stats['assists']) if stats['assists'] else 0
        fg3m = sum(stats['threes']) / len(stats['threes']) if stats['threes'] else 0
        bpg = sum(stats['blocks']) / len(stats['blocks']) if stats['blocks'] else 0
        spg = sum(stats['steals']) / len(stats['steals']) if stats['steals'] else 0

        # Last 10 games (if we have enough data)
        last_10_ppg = sum(stats['points'][-10:]) / len(stats['points'][-10:]) if stats['points'] else ppg
        last_10_rpg = sum(stats['rebounds'][-10:]) / len(stats['rebounds'][-10:]) if stats['rebounds'] else rpg
        last_10_apg = sum(stats['assists'][-10:]) / len(stats['assists'][-10:]) if stats['assists'] else apg

        # Determine trend (last 10 vs season)
        if last_10_ppg > ppg * 1.1:
            trend = 'UP'
        elif last_10_ppg < ppg * 0.9:
            trend = 'DOWN'
        else:
            trend = 'STABLE'

        # Save to database
        cursor.execute("""
            INSERT OR REPLACE INTO player_stats_cache
            (player_id, player_name, team, date, games_played, minutes_per_game,
             points_per_game, rebounds_per_game, assists_per_game, fg3_per_game,
             blocks_per_game, steals_per_game, fg_pct, last_10_ppg, last_10_rpg,
             last_10_apg, trend_direction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            player_id,
            stats['player_name'],
            stats['team'],
            date.today().isoformat(),
            games_played,
            0,  # minutes_per_game - not available from props
            ppg,
            rpg,
            apg,
            fg3m,
            bpg,
            spg,
            0,  # fg_pct - not available from props
            last_10_ppg,
            last_10_rpg,
            last_10_apg,
            trend
        ))

        saved_count += 1

    conn.commit()

    print(f"  [OK] Saved {saved_count} players\n")

    # Export JSON backup
    print("[BACKUP] Exporting to JSON...")

    backup_data = {}
    cursor.execute("SELECT * FROM player_stats_cache")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    for row in rows:
        player_id = row[1]  # player_id column
        backup_data[player_id] = dict(zip(columns, row))

    backup_path = "D:/backend/data/backups/player_stats_cache.json"
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)

    with open(backup_path, 'w') as f:
        json.dump({
            'generated_date': date.today().isoformat(),
            'total_players': len(backup_data),
            'source': 'Aggregated from player_props_results box scores',
            'date_range': 'Oct 29 - Nov 12, 2025',
            'players': backup_data
        }, f, indent=2)

    file_size = os.path.getsize(backup_path) / 1024
    print(f"  [OK] Backup saved to {backup_path}")
    print(f"  File size: {file_size:.1f} KB\n")

    conn.close()

    # Summary
    print(f"{'='*70}")
    print("COMPLETE")
    print(f"{'='*70}")
    print(f"Players: {saved_count}")
    print(f"Database: D:/backend/data/player_props.db")
    print(f"Backup: {backup_path}")
    print(f"{'='*70}\n")

    return saved_count


if __name__ == "__main__":
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/player_props.db"
    count = aggregate_player_stats(db_path)

    print(f"[SUCCESS] Aggregated stats for {count} players from existing box scores!")
    print(f"\nNO API CALLS NEEDED - used data we already had!")
