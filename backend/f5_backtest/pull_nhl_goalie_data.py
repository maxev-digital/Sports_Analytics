#!/usr/bin/env python3
"""
Pull NHL team + goalie stats from the official NHL stats API (free).
Outputs: nhl_goalie_rankings_2024_25.json
"""
import json
import time
import urllib.request
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent
BASE = "https://api.nhle.com/stats/rest/en"
SEASON = "20242025"

TEAM_NAMES = {
    'ANA': 'Anaheim Ducks', 'ARI': 'Arizona Coyotes', 'BOS': 'Boston Bruins',
    'BUF': 'Buffalo Sabres', 'CGY': 'Calgary Flames', 'CAR': 'Carolina Hurricanes',
    'CHI': 'Chicago Blackhawks', 'COL': 'Colorado Avalanche', 'CBJ': 'Columbus Blue Jackets',
    'DAL': 'Dallas Stars', 'DET': 'Detroit Red Wings', 'EDM': 'Edmonton Oilers',
    'FLA': 'Florida Panthers', 'LAK': 'Los Angeles Kings', 'MIN': 'Minnesota Wild',
    'MTL': 'Montreal Canadiens', 'NSH': 'Nashville Predators', 'NJD': 'New Jersey Devils',
    'NYI': 'New York Islanders', 'NYR': 'New York Rangers', 'OTT': 'Ottawa Senators',
    'PHI': 'Philadelphia Flyers', 'PIT': 'Pittsburgh Penguins', 'SEA': 'Seattle Kraken',
    'SJS': 'San Jose Sharks', 'STL': 'St. Louis Blues', 'TBL': 'Tampa Bay Lightning',
    'TOR': 'Toronto Maple Leafs', 'UTA': 'Utah Hockey Club', 'VAN': 'Vancouver Canucks',
    'VGK': 'Vegas Golden Knights', 'WSH': 'Washington Capitals', 'WPG': 'Winnipeg Jets',
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def pull_team_stats():
    url = f"{BASE}/team/summary?cayenneExp=seasonId={SEASON}%20and%20gameTypeId=2&sort=points&dir=DESC&limit=40"
    d = fetch(url)
    teams = {}
    for t in d.get('data', []):
        abbr = None
        # Get abbrev from teamFullName → match to our map
        full = t.get('teamFullName', '')
        for a, name in TEAM_NAMES.items():
            if name == full:
                abbr = a
                break
        if not abbr:
            continue
        teams[abbr] = {
            'team': abbr,
            'team_name': full,
            'games': t.get('gamesPlayed', 0),
            'wins': t.get('wins', 0),
            'losses': t.get('losses', 0),
            'ot_losses': t.get('otLosses', 0),
            'points': t.get('points', 0),
            'point_pct': round(t.get('pointPct', 0), 3),
            'gf_pg': round(t.get('goalsForPerGame', 0), 2),
            'ga_pg': round(t.get('goalsAgainstPerGame', 0), 2),
            'net_goals': round(t.get('goalsForPerGame', 0) - t.get('goalsAgainstPerGame', 0), 2),
            'sf_pg': round(t.get('shotsForPerGame', 0), 1),
            'sa_pg': round(t.get('shotsAgainstPerGame', 0), 1),
            'pp_pct': round(t.get('powerPlayPct', 0) * 100, 1),
            'pk_pct': round(t.get('penaltyKillPct', 0) * 100, 1),
            'shutouts': t.get('teamShutouts', 0),
            'faceoff_pct': round(t.get('faceoffWinPct', 0) * 100, 1),
        }
    print(f"Team stats: {len(teams)} teams")
    return teams


def pull_goalie_stats():
    # Get all goalies with 20+ GP
    url = f"{BASE}/goalie/summary?cayenneExp=seasonId={SEASON}%20and%20gameTypeId=2%20and%20gamesPlayed%3E=20&sort=savePct&dir=DESC&limit=100"
    d = fetch(url)
    goalies = []
    for g in d.get('data', []):
        gp = g.get('gamesPlayed', 0)
        gs = g.get('gamesStarted', 0)
        if gp < 10:
            continue
        toi_sec = g.get('timeOnIce', 0)
        toi_min = round(toi_sec / 60, 0)
        goalies.append({
            'name': g.get('goalieFullName', ''),
            'teams': g.get('teamAbbrevs', ''),
            'gp': gp,
            'gs': gs,
            'wins': g.get('wins', 0),
            'losses': g.get('losses', 0),
            'sv_pct': round(g.get('savePct', 0), 4),
            'gaa': round(g.get('goalsAgainstAverage', 0), 2),
            'shutouts': g.get('shutouts', 0),
            'saves': g.get('saves', 0),
            'shots_against': g.get('shotsAgainst', 0),
        })
    print(f"Goalies (10+ GP): {len(goalies)}")
    return goalies


def assign_primary_goalies(goalies, teams):
    """Assign each team its primary goalie (most starts)."""
    # Group by team
    from collections import defaultdict
    team_goalies = defaultdict(list)
    for g in goalies:
        team_str = g['teams']
        # Handle multi-team goalies (take last team if traded)
        parts = [t.strip() for t in team_str.split(',')]
        primary_team = parts[-1]  # Last team listed
        team_goalies[primary_team].append(g)

    # Sort by games started descending, pick top 2
    for abbr, team_data in teams.items():
        starters = sorted(team_goalies.get(abbr, []), key=lambda x: -x['gs'])
        team_data['starter'] = starters[0] if starters else None
        team_data['backup'] = starters[1] if len(starters) > 1 else None

    return teams


def pull_home_away_splits():
    """Pull home vs away goalie stats."""
    splits = {}
    for situation in ['home', 'away']:
        url = f"{BASE}/goalie/summary?cayenneExp=seasonId={SEASON}%20and%20gameTypeId=2%20and%20gamesStarted%3E=10%20and%20homeRoad=%27{situation.upper()}%27&limit=100"
        try:
            d = fetch(url)
            for g in d.get('data', []):
                name = g.get('goalieFullName', '')
                if name not in splits:
                    splits[name] = {}
                splits[name][situation] = {
                    'sv_pct': round(g.get('savePct', 0), 4),
                    'gaa': round(g.get('goalsAgainstAverage', 0), 2),
                    'gs': g.get('gamesStarted', 0),
                }
        except Exception as e:
            print(f"  Home/away split failed: {e}")
    return splits


def main():
    print("Pulling NHL team stats...")
    teams = pull_team_stats()

    print("Pulling NHL goalie stats...")
    goalies = pull_goalie_stats()

    print("Pulling home/away splits...")
    try:
        splits = pull_home_away_splits()
    except Exception:
        splits = {}

    # Attach splits to goalies
    for g in goalies:
        g_splits = splits.get(g['name'], {})
        g['home_sv_pct'] = g_splits.get('home', {}).get('sv_pct')
        g['away_sv_pct'] = g_splits.get('away', {}).get('sv_pct')
        g['home_gaa'] = g_splits.get('home', {}).get('gaa')
        g['away_gaa'] = g_splits.get('away', {}).get('gaa')

    # Assign primary goalies to teams
    teams = assign_primary_goalies(goalies, teams)

    # Sort teams by point pct
    teams_list = sorted(teams.values(), key=lambda x: -x['point_pct'])

    output = {
        'season': '2024-25',
        'teams': teams_list,
        'goalies': sorted(goalies, key=lambda x: -x['sv_pct']),
    }

    out = OUTPUT_DIR / 'nhl_goalie_rankings_2024_25.json'
    with open(out, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved {len(teams_list)} teams, {len(goalies)} goalies → {out.name}")

    print("\nTop 5 Teams (points%):")
    for t in teams_list[:5]:
        s = t.get('starter') or {}
        print(f"  {t['team']:3s} {t['point_pct']:.3f} | GF/GA: {t['gf_pg']}/{t['ga_pg']} | PP:{t['pp_pct']}% PK:{t['pk_pct']}% | Starter: {s.get('name','?')} {s.get('sv_pct','?')} SV%")

    print("\nTop 10 Goalies (SV%):")
    for g in goalies[:10]:
        print(f"  {g['name']:25s} {g['sv_pct']:.4f} SV% {g['gaa']:.2f} GAA {g['gs']} GS {g['shutouts']} SO | {g['teams']}")


if __name__ == "__main__":
    main()
