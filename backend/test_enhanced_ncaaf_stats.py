"""Test NCAAF scraper with all 15 new stats"""
from scrapers.teamrankings_ncaaf_scraper import TeamRankingsNCAAFScraper
import json

print("Testing enhanced NCAAF scraper with 15 new stats...")
print("=" * 80)

scrap = TeamRankingsNCAAFScraper()

# Force fresh scraping (not cached)
print("\nFetching fresh stats for all NCAAF teams...")
stats = scrap.fetch_all_team_stats(force_refresh=True)

print(f"\nTotal teams fetched: {len(stats)}")

# Check Texas Tech for all the new stats
texas_tech = stats.get('Texas Tech', {})

if texas_tech:
    print("\n" + "=" * 80)
    print("TEXAS TECH RED RAIDERS - Enhanced Stats Report")
    print("=" * 80)

    print("\n[BASIC STATS]")
    print(f"  Record: {texas_tech.get('wins')}-{texas_tech.get('losses')}")
    print(f"  PPG: {texas_tech.get('pts_per_game')}")
    print(f"  Opp PPG: {texas_tech.get('pts_allowed')}")

    print("\n[BETTING TRENDS]")
    print(f"  ATS: {texas_tech.get('ats_wins')}-{texas_tech.get('ats_losses')}-{texas_tech.get('ats_pushes')}")
    print(f"  O/U: {texas_tech.get('ou_overs')}-{texas_tech.get('ou_unders')}-{texas_tech.get('ou_pushes')}")

    print("\n[NEW EFFICIENCY STATS]")
    print(f"  Yards per play: {texas_tech.get('yards_per_play')}")
    print(f"  Opp yards per play: {texas_tech.get('opponent_yards_per_play')}")
    print(f"  Completion %: {texas_tech.get('completion_pct')}")
    print(f"  Opp completion %: {texas_tech.get('opponent_completion_pct')}")
    print(f"  4th down %: {texas_tech.get('fourth_down_conversion_pct')}")

    print("\n[NEW TURNOVER & SCORING STATS]")
    print(f"  Interceptions/game: {texas_tech.get('interceptions_per_game')}")
    print(f"  Fumbles lost/game: {texas_tech.get('fumbles_lost_per_game')}")
    print(f"  Offensive TDs/game: {texas_tech.get('offensive_touchdowns_per_game')}")
    print(f"  Passing TDs/game: {texas_tech.get('passing_touchdowns_per_game')}")
    print(f"  Rushing TDs/game: {texas_tech.get('rushing_touchdowns_per_game')}")

    print("\n[NEW MISC STATS]")
    print(f"  QB sacked/game: {texas_tech.get('qb_sacked_per_game')}")
    print(f"  Penalty yards/game: {texas_tech.get('penalty_yards_per_game')}")
    print(f"  Plays/game: {texas_tech.get('plays_per_game')}")
    print(f"  First downs/game: {texas_tech.get('first_downs_per_game')}")
    print(f"  Time of possession: {texas_tech.get('time_of_possession')}")

    # Count how many new stats are populated
    new_stats = [
        'yards_per_play', 'opponent_yards_per_play', 'completion_pct',
        'opponent_completion_pct', 'fourth_down_conversion_pct',
        'interceptions_per_game', 'fumbles_lost_per_game',
        'offensive_touchdowns_per_game', 'passing_touchdowns_per_game',
        'rushing_touchdowns_per_game', 'qb_sacked_per_game',
        'penalty_yards_per_game', 'plays_per_game', 'first_downs_per_game',
        'time_of_possession'
    ]

    populated = sum(1 for stat in new_stats if texas_tech.get(stat) is not None)

    print("\n" + "=" * 80)
    print(f"NEW STATS POPULATED: {populated}/{len(new_stats)}")

    if populated == len(new_stats):
        print("[OK] All 15 new stats successfully scraped!")
    else:
        print(f"[WARNING] Missing {len(new_stats) - populated} stats")
        missing = [s for s in new_stats if texas_tech.get(s) is None]
        print(f"Missing: {missing}")
else:
    print("[ERROR] Texas Tech not found in scraped data!")

print("\nDone!")
