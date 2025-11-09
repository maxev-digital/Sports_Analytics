#!/usr/bin/env python3
"""
TeamRankings URL Discovery Script

Tests which stat URLs exist on TeamRankings.com for each sport.
This helps us know exactly what data we can scrape before updating scrapers.

Usage:
    python discover_teamrankings_stats.py
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, List

# Common stat URL patterns to test
NBA_STATS_TO_TEST = [
    'points-per-game',
    'opponent-points-per-game',
    'average-scoring-margin',
    'pace',
    'possessions-per-game',
    'offensive-rebounds-per-game',
    'defensive-rebounds-per-game',
    'rebounds-per-game',
    'assists-per-game',
    'turnovers-per-game',
    'steals-per-game',
    'blocks-per-game',
    'field-goal-percentage',
    'three-point-percentage',
    'free-throw-percentage',
    'effective-field-goal-percentage',
    'true-shooting-percentage',
    'personal-fouls-per-game',
    'fast-break-points-per-game',
    'points-in-paint-per-game',
]

NFL_STATS_TO_TEST = [
    'points-per-game',
    'opponent-points-per-game',
    'average-scoring-margin',
    'yards-per-game',
    'opponent-yards-per-game',
    'third-down-conversion-pct',
    'opponent-third-down-conversion-pct',
    'red-zone-scoring-pct',
    'opponent-red-zone-scoring-pct',
    'sacks-per-game',
    'opponent-sacks-per-game',
    'time-of-possession',
    'passing-yards-per-game',
    'rushing-yards-per-game',
    'opponent-passing-yards-per-game',
    'opponent-rushing-yards-per-game',
    'penalties-per-game',
    'takeaways-per-game',
    'turnovers-lost-per-game',
    'turnover-margin',
    'first-downs-per-game',
]

MLB_STATS_TO_TEST = [
    'runs-per-game',
    'opponent-runs-per-game',
    'average-run-differential',
    'batting-average',
    'earned-run-average',
    'home-runs-per-game',
    'strikeouts-per-game',
    'walks-per-game',
    'on-base-percentage',
    'slugging-percentage',
    'ops',
    'whip',
    'hits-per-game',
    'errors-per-game',
]

NCAAF_STATS_TO_TEST = [
    'points-per-game',
    'opponent-points-per-game',
    'average-scoring-margin',
    'yards-per-game',
    'opponent-yards-per-game',
    'third-down-conversion-pct',
    'red-zone-scoring-pct',
    'sacks-per-game',
    'time-of-possession',
    'passing-yards-per-game',
    'rushing-yards-per-game',
    'turnovers-per-game',
    'takeaways-per-game',
]


def test_stat_url(sport: str, stat_name: str) -> Dict:
    """
    Test if a stat URL exists and is scrapable

    Returns:
        Dict with status, sample_value, team_count
    """
    url = f"https://www.teamrankings.com/{sport}/stat/{stat_name}"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            return {'status': 'NOT_FOUND', 'url': url}

        if response.status_code != 200:
            return {'status': 'ERROR', 'code': response.status_code, 'url': url}

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the stats table
        table = soup.find('table', {'class': 'datatable'})
        if not table:
            return {'status': 'NO_TABLE', 'url': url}

        # Count teams
        rows = table.find('tbody').find_all('tr')
        team_count = len(rows)

        # Get sample value from first row
        if rows:
            cols = rows[0].find_all('td')
            if len(cols) >= 3:
                sample_team = cols[1].text.strip()
                sample_value = cols[2].text.strip()

                return {
                    'status': 'SUCCESS',
                    'url': url,
                    'team_count': team_count,
                    'sample_team': sample_team,
                    'sample_value': sample_value
                }

        return {'status': 'PARSE_ERROR', 'url': url}

    except Exception as e:
        return {'status': 'EXCEPTION', 'error': str(e), 'url': url}


def discover_stats(sport: str, stats_to_test: List[str]):
    """Discover which stats are available for a sport"""
    print(f"\n{'='*80}")
    print(f"Discovering {sport.upper()} Stats")
    print(f"{'='*80}\n")

    found = []
    not_found = []
    errors = []

    for i, stat_name in enumerate(stats_to_test, 1):
        print(f"[{i}/{len(stats_to_test)}] Testing: {stat_name}...", end=' ')

        result = test_stat_url(sport, stat_name)

        if result['status'] == 'SUCCESS':
            print(f"[OK] FOUND ({result['team_count']} teams, sample: {result['sample_value']})")
            found.append(stat_name)
        elif result['status'] == 'NOT_FOUND':
            print(f"[X] 404")
            not_found.append(stat_name)
        else:
            print(f"[!] {result['status']}")
            errors.append((stat_name, result))

        time.sleep(0.5)  # Be polite to server

    # Summary
    print(f"\n{'-'*80}")
    print(f"Summary for {sport.upper()}:")
    print(f"  [OK] Found: {len(found)}/{len(stats_to_test)}")
    print(f"  [X] Not Found: {len(not_found)}")
    print(f"  [!] Errors: {len(errors)}")
    print(f"{'-'*80}\n")

    if found:
        print("[OK] Available Stats:")
        for stat in found:
            print(f"  - {stat}")

    if not_found:
        print(f"\n[X] Not Available:")
        for stat in not_found[:10]:  # Show first 10
            print(f"  - {stat}")
        if len(not_found) > 10:
            print(f"  ... and {len(not_found) - 10} more")

    return found


if __name__ == "__main__":
    print("\n" + "="*80)
    print("TeamRankings.com Stat URL Discovery")
    print("="*80)

    # Discover NBA stats
    nba_found = discover_stats('nba', NBA_STATS_TO_TEST)

    # Discover NFL stats
    nfl_found = discover_stats('nfl', NFL_STATS_TO_TEST)

    # Discover NCAAF stats
    ncaaf_found = discover_stats('college-football', NCAAF_STATS_TO_TEST)

    # Discover MLB stats
    mlb_found = discover_stats('mlb', MLB_STATS_TO_TEST)

    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"NBA: {len(nba_found)} stats available")
    print(f"NFL: {len(nfl_found)} stats available")
    print(f"NCAAF: {len(ncaaf_found)} stats available")
    print(f"MLB: {len(mlb_found)} stats available")
    print(f"\nTotal: {len(nba_found) + len(nfl_found) + len(ncaaf_found) + len(mlb_found)} stats")
    print("="*80 + "\n")
