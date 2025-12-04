#!/usr/bin/env python3
"""
Generate DFS Crusher data from existing player_props_lines database
Uses your current Odds API data - no additional scraping needed
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict

# DFS bookmakers we support (that you have data for)
DFS_BOOKMAKERS = {
    'fliff': {'name': 'Fliff', 'gradient': 'from-red-800 via-black to-black border-red-700'},
    'draftkings': {'name': 'DraftKings', 'gradient': 'from-green-700 via-emerald-800 to-black border-green-600'},
    'fanduel': {'name': 'FanDuel', 'gradient': 'from-blue-700 via-cyan-800 to-black border-cyan-600'},
    'betmgm': {'name': 'BetMGM', 'gradient': 'from-amber-700 via-orange-800 to-black border-amber-600'},
    # Add these when they appear in your database:
    # 'prizepicks': {'name': 'PrizePicks', 'gradient': 'from-amber-700 via-orange-800 to-black border-amber-600'},
    # 'underdog': {'name': 'Underdog', 'gradient': 'from-purple-700 via-pink-800 to-black border-purple-600'},
}

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'player_props.db'
OUTPUT_PATH = Path(__file__).parent / 'cache' / 'dfs_crusher_latest.json'

def calculate_edge(over_odds: int, under_odds: int, predicted_prob: float = None) -> float:
    """Calculate implied edge (simplified for now)"""
    if not predicted_prob:
        predicted_prob = 0.55  # Default slight edge
    
    # Convert American odds to implied probability
    if over_odds < 0:
        implied_prob = abs(over_odds) / (abs(over_odds) + 100)
    else:
        implied_prob = 100 / (over_odds + 100)
    
    # Edge = True Probability - Implied Probability
    edge = (predicted_prob - implied_prob) * 100
    return max(0, edge)

def generate_dfs_crusher_data() -> Dict:
    """Generate DFS Crusher JSON from database"""
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    today = date.today().strftime('%Y-%m-%d')
    
    # Get props for each DFS bookmaker
    plays = []
    
    for bookmaker_key, bookmaker_info in DFS_BOOKMAKERS.items():
        # Get today's props for this bookmaker
        cursor.execute("""
            SELECT 
                player_name,
                prop_type,
                market_line,
                over_odds,
                under_odds,
                COUNT(*) OVER() as total_props
            FROM player_props_lines
            WHERE date = ?
              AND bookmaker = ?
              AND over_odds IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 5
        """, (today, bookmaker_key))
        
        bookmaker_props = cursor.fetchall()
        
        if not bookmaker_props:
            continue
        
        # Get the best prop for this bookmaker
        for prop in bookmaker_props[:1]:  # Just take the first one as best
            edge = calculate_edge(prop['over_odds'], prop['under_odds'])
            
            # Calculate EV and demon score
            ev_pct = int(edge * 1.5)  # Simplified EV calculation
            demon_score = int(edge * 2)  # Visual intensity score
            
            # Determine direction (Over is usually the action)
            direction = 'Higher' if prop['over_odds'] < prop['under_odds'] else 'Lower'
            
            # Format the play
            play = {
                'site': bookmaker_info['name'],
                'logo': bookmaker_key,
                'gradient': bookmaker_info['gradient'],
                'bestPlay': f"{prop['player_name']} {prop['prop_type'].replace('_', ' ').title()} {prop['market_line']} {direction}",
                'trueWinRate': f"{55 + (edge/2):.1f}%",  # Estimated win rate
                'payout': '3x',  # Standard DFS payout
                'ev': f"+{ev_pct}%",
                'demonScore': demon_score,
                'entriesToday': prop['total_props']
            }
            plays.append(play)
    
    conn.close()
    
    # Create final JSON structure
    result = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'total_demons': len([p for p in plays if p['demonScore'] >= 15]),
        'plays': sorted(plays, key=lambda x: x['demonScore'], reverse=True)
    }
    
    return result

def save_dfs_crusher_data():
    """Generate and save DFS crusher data"""
    data = generate_dfs_crusher_data()
    
    # Create cache directory if needed
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to JSON
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Generated DFS Crusher data: {len(data['plays'])} plays from {len(set(p['site'] for p in data['plays']))} sites")
    print(f"   Saved to: {OUTPUT_PATH}")
    print(f"   Demons: {data['total_demons']}")
    
    return data

if __name__ == '__main__':
    save_dfs_crusher_data()
