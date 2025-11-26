from scrapers.teamrankings_ncaaf_scraper import TeamRankingsNCAAFScraper

scrap = TeamRankingsNCAAFScraper()

print("=" * 60)
print("Testing fetch_all_team_stats(force_refresh=True)...")
stats = scrap.fetch_all_team_stats(force_refresh=True)
print(f"Returned {len(stats)} teams total")
texas_tech = stats.get("Texas Tech", {})
print(f"Texas Tech ATS: {texas_tech.get('ats_wins')}-{texas_tech.get('ats_losses')}-{texas_tech.get('ats_pushes')}")
print(f"Texas Tech O/U: {texas_tech.get('ou_overs')}-{texas_tech.get('ou_unders')}-{texas_tech.get('ou_pushes')}")
print(f"Texas Tech PPG: {texas_tech.get('pts_per_game')}")
