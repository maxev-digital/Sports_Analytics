#!/usr/bin/env python3
"""
Pull NBA pace + efficiency ratings from ESPN stats API (free).
Computes pace proxy, ORtg proxy, and net differential.
Outputs: nba_efficiency_2024_25.json
"""
import json
import time
import urllib.request
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent

# ESPN team ID → abbreviation map
TEAMS = {
    1: 'ATL', 2: 'BOS', 17: 'BKN', 30: 'CHA', 4: 'CHI',
    5: 'CLE', 6: 'DAL', 7: 'DEN', 8: 'DET', 9: 'GS',
    10: 'HOU', 11: 'IND', 12: 'LAC', 13: 'LAL', 29: 'MEM',
    14: 'MIA', 15: 'MIL', 16: 'MIN', 3: 'NO', 18: 'NY',
    25: 'OKC', 19: 'ORL', 20: 'PHI', 21: 'PHX', 22: 'POR',
    23: 'SAC', 24: 'SA', 28: 'TOR', 26: 'UTA', 27: 'WSH',
}

TEAM_NAMES = {
    'ATL': 'Atlanta Hawks', 'BOS': 'Boston Celtics', 'BKN': 'Brooklyn Nets',
    'CHA': 'Charlotte Hornets', 'CHI': 'Chicago Bulls', 'CLE': 'Cleveland Cavaliers',
    'DAL': 'Dallas Mavericks', 'DEN': 'Denver Nuggets', 'DET': 'Detroit Pistons',
    'GS': 'Golden State Warriors', 'HOU': 'Houston Rockets', 'IND': 'Indiana Pacers',
    'LAC': 'LA Clippers', 'LAL': 'Los Angeles Lakers', 'MEM': 'Memphis Grizzlies',
    'MIA': 'Miami Heat', 'MIL': 'Milwaukee Bucks', 'MIN': 'Minnesota Timberwolves',
    'NO': 'New Orleans Pelicans', 'NY': 'New York Knicks', 'OKC': 'Oklahoma City Thunder',
    'ORL': 'Orlando Magic', 'PHI': 'Philadelphia 76ers', 'PHX': 'Phoenix Suns',
    'POR': 'Portland Trail Blazers', 'SAC': 'Sacramento Kings', 'SA': 'San Antonio Spurs',
    'TOR': 'Toronto Raptors', 'UTA': 'Utah Jazz', 'WSH': 'Washington Wizards',
}

BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def get_team_stats(team_id, season=2025):
    url = f"{BASE}/teams/{team_id}/statistics?season={season}"
    data = fetch(url)
    cats = data.get('results', {}).get('stats', {}).get('categories', [])
    stats = {}
    for cat in cats:
        for s in cat['stats']:
            stats[s['name']] = s['value']
    return stats


def get_team_record(team_id):
    url = f"{BASE}/teams/{team_id}"
    data = fetch(url)
    record = data.get('team', {}).get('record', {})
    items = record.get('items', [])
    for item in items:
        if item.get('type') == 'total':
            stats = {s['name']: s['value'] for s in item.get('stats', [])}
            return {
                'wins': int(stats.get('wins', 0)),
                'losses': int(stats.get('losses', 0)),
                'pct': float(stats.get('winPercent', 0)),
                'streak': stats.get('streak', ''),
            }
    return {'wins': 0, 'losses': 0, 'pct': 0.0, 'streak': ''}


def compute_pace_proxy(stats):
    """
    Pace proxy (possessions per game):
    Pace ≈ FGA + 0.44 * FTA - OReb + TOV
    """
    fga = stats.get('avgFieldGoalsAttempted', 0)
    fta = stats.get('avgFreeThrowsAttempted', 0)
    or_ = stats.get('avgOffensiveRebounds', 0)
    tov = stats.get('avgTurnovers', 0)
    return round(fga + 0.44 * fta - or_ + tov, 1)


def main():
    results = []
    print("Pulling NBA team stats from ESPN...")

    for team_id, abbr in sorted(TEAMS.items(), key=lambda x: x[1]):
        try:
            stats = get_team_stats(team_id)
            record = get_team_record(team_id)

            ppg = stats.get('avgPoints', 0)
            pace = compute_pace_proxy(stats)
            ortg = round((ppg / pace) * 100, 1) if pace > 0 else None

            results.append({
                'team': abbr,
                'team_name': TEAM_NAMES.get(abbr, abbr),
                'espn_id': team_id,
                'wins': record['wins'],
                'losses': record['losses'],
                'win_pct': round(record['pct'], 3),
                'ppg': round(ppg, 1),
                'pace': pace,
                'ortg_proxy': ortg,
                'fg_pct': round(stats.get('fieldGoalPct', 0), 1),
                'three_pct': round(stats.get('threePointPct', 0), 1),
                'three_rate': round(stats.get('avgThreePointFieldGoalsAttempted', 0) / stats.get('avgFieldGoalsAttempted', 1) * 100, 1),
                'ft_pct': round(stats.get('freeThrowPct', 0), 1),
                'reb': round(stats.get('avgRebounds', 0), 1),
                'ast': round(stats.get('avgAssists', 0), 1),
                'tov': round(stats.get('avgTurnovers', 0), 1),
                'ast_to': round(stats.get('assistTurnoverRatio', 0), 2),
                'blk': round(stats.get('avgBlocks', 0), 1),
                'stl': round(stats.get('avgSteals', 0), 1),
                'games': int(stats.get('gamesPlayed', 0)),
            })
            print(f"  {abbr}: PPG={ppg:.1f} Pace={pace} ORtg={ortg}")
            time.sleep(0.4)
        except Exception as e:
            print(f"  {abbr}: FAILED — {e}")

    # Sort by ORtg proxy descending
    results.sort(key=lambda x: x.get('ortg_proxy') or 0, reverse=True)

    # Compute league average pace for reference
    avg_pace = sum(r['pace'] for r in results) / len(results)
    avg_ppg = sum(r['ppg'] for r in results) / len(results)

    output = {
        'season': '2024-25',
        'teams': results,
        'meta': {
            'avg_pace': round(avg_pace, 1),
            'avg_ppg': round(avg_ppg, 1),
            'note': 'Pace proxy = FGA + 0.44*FTA - OR + TOV. ORtg proxy = PPG/Pace*100. No opponent data available from free ESPN API.',
        }
    }

    out = OUTPUT_DIR / 'nba_efficiency_2024_25.json'
    with open(out, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved {len(results)} teams → {out.name}")

    print(f"\nLeague avg pace: {avg_pace:.1f} | avg PPG: {avg_ppg:.1f}")
    print("\nTop 5 by ORtg proxy:")
    for t in results[:5]:
        print(f"  {t['team']:4s} ORtg={t['ortg_proxy']} Pace={t['pace']} PPG={t['ppg']}")
    print("\nBottom 5:")
    for t in results[-5:]:
        print(f"  {t['team']:4s} ORtg={t['ortg_proxy']} Pace={t['pace']} PPG={t['ppg']}")


if __name__ == "__main__":
    main()
