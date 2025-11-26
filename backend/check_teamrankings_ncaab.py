"""Check what stats TeamRankings has for NCAAB"""
import requests

# Key stats for totals betting
totals_focused_stats = [
    # PACE & TEMPO (critical for totals)
    'possessions-per-game',
    'seconds-per-possession',
    'average-possession-length',

    # SCORING & EFFICIENCY
    'points-per-game',
    'opponent-points-per-game',
    'effective-field-goal-pct',
    'opponent-effective-field-goal-pct',
    'offensive-efficiency',
    'defensive-efficiency',

    # SHOOTING VOLUME (impacts totals)
    'field-goal-attempts-per-game',
    'three-point-attempts-per-game',
    'free-throw-attempts-per-game',

    # SHOOTING EFFICIENCY
    'field-goal-pct',
    'three-point-pct',
    'two-point-pct',
    'free-throw-pct',

    # REBOUNDING (2nd chance points)
    'offensive-rebounds-per-game',
    'defensive-rebounds-per-game',
    'total-rebounds-per-game',

    # TURNOVERS (impact pace)
    'turnovers-per-game',
    'opponent-turnovers-per-game',
    'turnover-pct',

    # BETTING TRENDS
    'ats-win-pct',
    'over-under-record',
]

base_url = "https://www.teamrankings.com/ncaa-basketball/stat/"

print("Checking TeamRankings NCAAB stats availability...")
print("=" * 80)

available = []
not_available = []

for stat in totals_focused_stats:
    url = f"{base_url}{stat}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            available.append(stat)
            print(f"[OK] {stat}")
        else:
            not_available.append(stat)
            print(f"[NO] {stat}")
    except Exception as e:
        not_available.append(stat)
        print(f"[NO] {stat}")

print("\n" + "=" * 80)
print(f"\nSUMMARY:")
print(f"Available: {len(available)}/{len(totals_focused_stats)}")

print("\n" + "=" * 80)
print("AVAILABLE STATS FOR NCAAB:")
for stat in available:
    print(f"  - {stat}")
