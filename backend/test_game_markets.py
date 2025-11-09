from scrapers.sportsdataio_client import SportsDataIOClient
import json

client = SportsDataIOClient()
data = client._make_request('v3/nba/odds/json/BettingMarketsByGameID/22647')

# Find main game markets
spread_markets = [m for m in data if m['BettingBetType'] == 'Spread' and m['BettingPeriodType'] == 'Full-Game']
moneyline_markets = [m for m in data if m['BettingBetType'] == 'Moneyline' and m['BettingPeriodType'] == 'Full-Game']
total_markets = [m for m in data if m['BettingMarketType'] == 'Game Line' and 'Total' in m['Name'] if m.get('Name')] if any(m.get('Name') for m in data) else []

print("=" * 80)
print("SPREAD MARKET")
print("=" * 80)
if spread_markets:
    m = spread_markets[0]
    print(f"Available sportsbooks: {[s['Name'] for s in m['AvailableSportsbooks']]}")
    print(f"\nAll outcomes by sportsbook:")
    for outcome in m['BettingOutcomes']:
        print(f"  {outcome['SportsBook']['Name']:15} {outcome['Participant']:30} {outcome['Value']:>6} @ {outcome['PayoutAmerican']:>4}")

print("\n" + "=" * 80)
print("MONEYLINE MARKET")
print("=" * 80)
if moneyline_markets:
    m = moneyline_markets[0]
    print(f"Available sportsbooks: {[s['Name'] for s in m['AvailableSportsbooks']]}")
    print(f"\nAll outcomes by sportsbook:")
    for outcome in m['BettingOutcomes']:
        print(f"  {outcome['SportsBook']['Name']:15} {outcome['Participant']:30} @ {outcome['PayoutAmerican']:>4}")

# Try to find total market
print("\n" + "=" * 80)
print("LOOKING FOR TOTAL MARKET")
print("=" * 80)
total_markets = [m for m in data if m['BettingBetType'] == 'Both Teams Total Points' and m['BettingPeriodType'] == 'Full-Game' and len(m['AvailableSportsbooks']) > 1]
if total_markets:
    m = total_markets[0]
    print(f"Market Type: {m['BettingMarketType']}")
    print(f"Bet Type: {m['BettingBetType']}")
    print(f"Available sportsbooks: {[s['Name'] for s in m['AvailableSportsbooks']]}")
    print(f"\nSample outcomes (first 10):")
    for outcome in m['BettingOutcomes'][:10]:
        print(f"  {outcome['SportsBook']['Name']:15} {outcome['BettingOutcomeType']:6} {outcome['Value']:>6} @ {outcome['PayoutAmerican']:>4}")
