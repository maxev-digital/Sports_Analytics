from scrapers.sportsdataio_client import SportsDataIOClient
import json

client = SportsDataIOClient()
data = client.get_live_odds('NBA', '2025-11-06')

print(f'Total games: {len(data)}')
print()

for game in data:
    pregame_count = len(game.get('PregameOdds', []))
    live_count = len(game.get('LiveOdds', []))
    alt_count = len(game.get('AlternateMarketPregameOdds', []))

    print(f"{game['AwayTeamName']} @ {game['HomeTeamName']}")
    print(f"  PregameOdds: {pregame_count}, LiveOdds: {live_count}, AltMarket: {alt_count}")

    # If there are pregame odds, show a sample
    if pregame_count > 0:
        print("  Sample PregameOdds:")
        print(json.dumps(game['PregameOdds'][0], indent=4))
