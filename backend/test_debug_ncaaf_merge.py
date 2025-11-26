from scrapers.teamrankings_ncaaf_scraper import TeamRankingsNCAAFScraper

scrap = TeamRankingsNCAAFScraper()

# Test individual scraping methods
print("=" * 60)
print("Testing scrape_ats_trends()...")
ats_trends = scrap.scrape_ats_trends()
print(f"Returned {len(ats_trends)} teams with ATS data")
print(f"Texas Tech in ats_trends: {ats_trends.get('Texas Tech', 'NOT FOUND')}")
print(f"Sample keys: {list(ats_trends.keys())[:5]}")

print("\n" + "=" * 60)
print("Testing scrape_ou_trends()...")
ou_trends = scrap.scrape_ou_trends()
print(f"Returned {len(ou_trends)} teams with O/U data")
print(f"Texas Tech in ou_trends: {ou_trends.get('Texas Tech', 'NOT FOUND')}")
print(f"Sample keys: {list(ou_trends.keys())[:5]}")

print("\n" + "=" * 60)
print("Testing fetch_all_team_stats()...")
stats = scrap.fetch_all_team_stats()
print(f"Returned {len(stats)} teams total")
texas_tech = stats.get("Texas Tech", {})
print(f"Texas Tech ATS: {texas_tech.get('ats_wins')}-{texas_tech.get('ats_losses')}-{texas_tech.get('ats_pushes')}")
print(f"Texas Tech O/U: {texas_tech.get('ou_overs')}-{texas_tech.get('ou_unders')}-{texas_tech.get('ou_pushes')}")
print(f"Texas Tech PPG: {texas_tech.get('pts_per_game')}")
