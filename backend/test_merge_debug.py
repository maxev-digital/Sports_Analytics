from scrapers.teamrankings_ncaaf_scraper import TeamRankingsNCAAFScraper
import time

scrap = TeamRankingsNCAAFScraper()

print("=" * 60)
print("Step 1: Scraping PPG...")
ppg = scrap.scrape_stat_page('points-per-game')
print(f"PPG has {len(ppg)} teams")
print(f"Texas Tech PPG: {ppg.get('Texas Tech', 'NOT FOUND')}")
time.sleep(1)

print("\n" + "=" * 60)
print("Step 2: Scraping OPP PPG...")
opp_ppg = scrap.scrape_stat_page('opponent-points-per-game')
print(f"OPP PPG has {len(opp_ppg)} teams")
print(f"Texas Tech OPP PPG: {opp_ppg.get('Texas Tech', 'NOT FOUND')}")
time.sleep(1)

print("\n" + "=" * 60)
print("Step 3: Scraping Point Diff...")
point_diff = scrap.scrape_stat_page('average-scoring-margin')
print(f"Point Diff has {len(point_diff)} teams")
print(f"Texas Tech Point Diff: {point_diff.get('Texas Tech', 'NOT FOUND')}")
time.sleep(1)

print("\n" + "=" * 60)
print("Step 4: Scraping ATS trends...")
ats_trends = scrap.scrape_ats_trends()
print(f"ATS trends has {len(ats_trends)} teams")
print(f"Texas Tech in ATS: {ats_trends.get('Texas Tech', 'NOT FOUND')}")
time.sleep(1)

print("\n" + "=" * 60)
print("Step 5: Scraping O/U trends...")
ou_trends = scrap.scrape_ou_trends()
print(f"O/U trends has {len(ou_trends)} teams")
print(f"Texas Tech in O/U: {ou_trends.get('Texas Tech', 'NOT FOUND')}")

print("\n" + "=" * 60)
print("Step 6: Building all_teams set...")
all_teams = set(ppg.keys()) | set(opp_ppg.keys()) | set(point_diff.keys())
print(f"All teams: {len(all_teams)} teams")
print(f"Texas Tech in all_teams: {'Texas Tech' in all_teams}")
print(f"Sample teams: {list(all_teams)[:5]}")

print("\n" + "=" * 60)
print("Step 7: Simulating merge for Texas Tech...")
if 'Texas Tech' in all_teams:
    ats_data = ats_trends.get('Texas Tech', {})
    ou_data = ou_trends.get('Texas Tech', {})

    print(f"ats_data for Texas Tech: {ats_data}")
    print(f"ou_data for Texas Tech: {ou_data}")

    print(f"\nExtracting values:")
    print(f"  ats_wins: {ats_data.get('ats_wins')}")
    print(f"  ats_losses: {ats_data.get('ats_losses')}")
    print(f"  ats_pushes: {ats_data.get('ats_pushes')}")
    print(f"  ou_overs: {ou_data.get('ou_overs')}")
    print(f"  ou_unders: {ou_data.get('ou_unders')}")
    print(f"  ou_pushes: {ou_data.get('ou_pushes')}")
else:
    print("Texas Tech NOT in all_teams!")
