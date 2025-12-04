#!/usr/bin/env python3
"""
Populate DFS Crusher cache from correlated_combos table
Converts top combos into platform-ready format for DFS Crusher page
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict

# Database and output paths
PREDICTIONS_DB = Path(__file__).parent.parent / 'predictions.db'
CACHE_DIR = Path(__file__).parent / 'cache'
OUTPUT_FILE = CACHE_DIR / 'dfs_crusher_latest.json'

# Platform configurations
PLATFORMS = {
    'PrizePicks': {
        'logo': 'prizepicks',
        'gradient': 'from-amber-600 via-orange-700 to-red-800 border-amber-500',
        'payout_2leg': '3x',
        'payout_3leg': '5x',
        'payout_4leg': '10x'
    },
    'Underdog': {
        'logo': 'underdog',
        'gradient': 'from-purple-600 via-pink-700 to-red-800 border-purple-500',
        'payout_2leg': '3x',
        'payout_3leg': '6x',
        'payout_4leg': '10x'
    },
    'Fliff': {
        'logo': 'fliff',
        'gradient': 'from-red-700 via-rose-800 to-black border-red-600',
        'payout_2leg': '3x',
        'payout_3leg': '5x',
        'payout_4leg': '9x'
    },
    'Sleeper': {
        'logo': 'sleeper',
        'gradient': 'from-indigo-600 via-blue-700 to-cyan-800 border-indigo-500',
        'payout_2leg': '3x',
        'payout_3leg': '5x',
        'payout_4leg': '10x'
    },
    'ParlayPlay': {
        'logo': 'parlayplay',
        'gradient': 'from-green-600 via-emerald-700 to-teal-800 border-green-500',
        'payout_2leg': '3x',
        'payout_3leg': '6x',
        'payout_4leg': '11x'
    }
}


def get_top_combos(limit_per_legs: int = 2) -> List[Dict]:
    """Get top correlated combos by demon score, grouped by leg count"""
    conn = sqlite3.connect(str(PREDICTIONS_DB))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get top combos for each leg count (2, 3, 4)
    all_combos = []

    for num_legs in [2, 3, 4]:
        cursor.execute("""
            SELECT
                combo_id,
                sport,
                players,
                props,
                lines,
                directions,
                true_probability,
                prize_picks_payout,
                expected_value_percent,
                demon_goblin_score
            FROM correlated_combos
            WHERE sport = 'nba'
            ORDER BY demon_goblin_score DESC
            LIMIT ?
        """, (limit_per_legs,))

        combos = cursor.fetchall()
        all_combos.extend(combos)

    conn.close()
    return all_combos


def parse_combo_data(combo: Dict) -> Dict:
    """Parse JSON fields from combo row"""
    try:
        return {
            'combo_id': combo['combo_id'],
            'sport': combo['sport'],
            'players': json.loads(combo['players']) if isinstance(combo['players'], str) else combo['players'],
            'props': json.loads(combo['props']) if isinstance(combo['props'], str) else combo['props'],
            'lines': json.loads(combo['lines']) if isinstance(combo['lines'], str) else combo['lines'],
            'directions': json.loads(combo['directions']) if isinstance(combo['directions'], str) else combo['directions'],
            'true_probability': combo['true_probability'],
            'payout': combo['prize_picks_payout'],
            'ev_percent': combo['expected_value_percent'],
            'demon_score': combo['demon_goblin_score']
        }
    except Exception as e:
        print(f"Error parsing combo {combo['combo_id']}: {e}")
        return None


def format_combo_for_platform(combo_data: Dict, platform_name: str) -> Dict:
    """Format combo data for DFS Crusher display"""
    platform_config = PLATFORMS[platform_name]

    num_legs = len(combo_data['players'])

    # Build the best play string
    play_parts = []
    for i in range(num_legs):
        player = combo_data['players'][i]
        prop = combo_data['props'][i].replace('_', ' ').title()
        line = combo_data['lines'][i]
        direction = combo_data['directions'][i]

        play_parts.append(f"{player} {prop} {direction}")

    best_play = " + ".join(play_parts)

    # Get payout for this leg count
    payout_key = f'payout_{num_legs}leg'
    payout = platform_config.get(payout_key, f"{combo_data['payout']}x")

    # Format win rate (convert from decimal to percentage)
    true_win_rate = f"{combo_data['true_probability'] * 100:.1f}%"

    # Format EV
    ev = f"+{combo_data['ev_percent']:.1f}%"

    # Demon score (higher is better)
    demon_score = round(combo_data['demon_score'], 2)

    # Entries today = total combos for this platform
    entries_today = 1760  # From our generated combos

    return {
        'site': platform_name,
        'logo': platform_config['logo'],
        'gradient': platform_config['gradient'],
        'bestPlay': best_play,
        'trueWinRate': true_win_rate,
        'payout': payout,
        'ev': ev,
        'demonScore': demon_score,
        'entriesToday': entries_today
    }


def generate_dfs_crusher_cache():
    """Generate DFS Crusher cache file from correlated combos"""
    print("=" * 70)
    print("GENERATING DFS CRUSHER CACHE")
    print("=" * 70)

    # Ensure cache directory exists
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Get top combos
    print(f"\n[1/3] Fetching top combos from database...")
    top_combos = get_top_combos(limit_per_legs=2)
    print(f"  Found {len(top_combos)} top combos")

    if not top_combos:
        print("  No combos found - creating empty cache")
        cache_data = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_demons": 0,
            "plays": []
        }
    else:
        # Parse combo data
        print(f"\n[2/3] Parsing combo data...")
        parsed_combos = []
        for combo in top_combos:
            parsed = parse_combo_data(combo)
            if parsed:
                parsed_combos.append(parsed)
        print(f"  Parsed {len(parsed_combos)} combos successfully")

        # Assign each combo to a platform
        print(f"\n[3/3] Formatting for platforms...")
        plays = []
        platform_names = list(PLATFORMS.keys())

        for i, combo_data in enumerate(parsed_combos):
            # Assign to platform (rotate through platforms)
            platform_name = platform_names[i % len(platform_names)]

            play = format_combo_for_platform(combo_data, platform_name)
            plays.append(play)

            print(f"  [{i+1}/{len(parsed_combos)}] {platform_name}: Score {play['demonScore']}")

        # Count demons (score >= 15)
        total_demons = sum(1 for p in plays if p['demonScore'] >= 15)

        # Sort by demon score (highest first)
        plays.sort(key=lambda x: x['demonScore'], reverse=True)

        cache_data = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_demons": total_demons,
            "plays": plays
        }

    # Write to cache file
    print(f"\n[WRITING] Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(cache_data, f, indent=2)

    print(f"\n" + "=" * 70)
    print(f"DFS CRUSHER CACHE GENERATED")
    print("=" * 70)
    print(f"Total Plays: {len(cache_data['plays'])}")
    print(f"Demon Plays (score >= 15): {cache_data['total_demons']}")
    print(f"Cache File: {OUTPUT_FILE}")
    print(f"Generated: {cache_data['generated_at']}")

    if cache_data['plays']:
        print(f"\nTop 3 Plays:")
        for i, play in enumerate(cache_data['plays'][:3], 1):
            print(f"  {i}. {play['site']}: {play['demonScore']} - {play['ev']} EV - {play['trueWinRate']} Win Rate")

    return cache_data


if __name__ == "__main__":
    generate_dfs_crusher_cache()
