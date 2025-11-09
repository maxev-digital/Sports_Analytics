"""Import NCAA Men's Basketball 2023-24 season"""
from data_sources.espn_client import ESPNClient

client = ESPNClient()

print("\n" + "="*60)
print("IMPORTING NCAA BASKETBALL 2023-24 SEASON")
print("="*60)
print("This may take 5-10 minutes...")
print("="*60 + "\n")

try:
    # Import 2023-24 NCAAB season
    # ESPN uses 'mens-college-basketball' for the sport
    games = client.import_season(
        season=2024,  # 2023-24 season
        sport='mens-college-basketball',
        save_to_db=True
    )

    print("\n" + "="*60)
    print(f"TOTAL NCAA BASKETBALL GAMES IMPORTED: {len(games)}")
    print("="*60)

except Exception as e:
    print(f"\n[ERROR] Failed to import NCAA Basketball: {e}")
    print("\nNote: ESPN client may need to be modified to support NCAA Basketball.")
    print("Check data_sources/espn_client.py for sport URL mappings.")
