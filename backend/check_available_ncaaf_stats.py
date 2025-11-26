"""
Check what stats are available on TeamRankings for NCAAF
"""
import requests
from bs4 import BeautifulSoup

# Stats we want to check for (based on NFL implementation)
potential_stats = [
    # Already scraping these:
    'points-per-game',
    'opponent-points-per-game',
    'average-scoring-margin',
    'yards-per-game',
    'opponent-yards-per-game',
    'third-down-conversion-pct',
    'red-zone-scoring-pct',
    'passing-yards-per-game',
    'rushing-yards-per-game',
    'sacks-per-game',
    'takeaways-per-game',

    # Additional stats to check:
    'yards-per-play',
    'opponent-yards-per-play',
    'completion-percentage',
    'opponent-completion-percentage',
    'fourth-down-conversion-pct',
    'interceptions-per-game',
    'fumbles-lost-per-game',
    'offensive-touchdowns-per-game',
    'passing-touchdowns-per-game',
    'rushing-touchdowns-per-game',
    'qb-sacked-per-game',
    'penalty-yards-per-game',
    'plays-per-game',
    'first-downs-per-game',
    'time-of-possession',
]

base_url = "https://www.teamrankings.com/college-football/stat/"

print("Checking NCAAF stat availability on TeamRankings...\n")
print("=" * 80)

available = []
not_available = []

for stat in potential_stats:
    url = f"{base_url}{stat}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            available.append(stat)
            print(f"[OK] {stat}")
        else:
            not_available.append(stat)
            print(f"[NO] {stat} (status: {response.status_code})")
    except Exception as e:
        not_available.append(stat)
        print(f"[NO] {stat} (error: {str(e)[:50]})")

print("\n" + "=" * 80)
print(f"\nSummary:")
print(f"Available: {len(available)}/{len(potential_stats)}")
print(f"Not available: {len(not_available)}/{len(potential_stats)}")

print("\n" + "=" * 80)
print("NEW stats to add (not currently scraped):")
new_stats = [s for s in available if s not in [
    'points-per-game',
    'opponent-points-per-game',
    'average-scoring-margin',
    'yards-per-game',
    'opponent-yards-per-game',
    'third-down-conversion-pct',
    'red-zone-scoring-pct',
    'passing-yards-per-game',
    'rushing-yards-per-game',
    'sacks-per-game',
    'takeaways-per-game',
]]
for stat in new_stats:
    print(f"  - {stat}")
