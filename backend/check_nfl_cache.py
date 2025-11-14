"""Check NFL cache data"""
import json
import sys

cache_file = sys.argv[1] if len(sys.argv) > 1 else "backend/backend/data/raw/nfl/teamrankings_cache.json"

with open(cache_file) as f:
    cache = json.load(f)

data = cache['data']
print(f"Total teams: {len(data)}")

# Check teams with records
teams_with_records = {team: (stats['wins'], stats['losses'])
                      for team, stats in data.items()
                      if stats.get('wins') is not None}
print(f"Teams with records: {len(teams_with_records)}")

# Check teams with ranks
teams_with_ppg_rank = {team: stats.get('points_per_game_rank')
                       for team, stats in data.items()
                       if stats.get('points_per_game_rank') is not None}
print(f"Teams with PPG rank: {len(teams_with_ppg_rank)}")

# Sample team analysis
patriots = data.get('New England', {})
print(f"\nPatriots:")
print(f"  Record: {patriots.get('wins')}-{patriots.get('losses')}")
print(f"  PPG: {patriots.get('pts_per_game')}")
print(f"  PPG Rank: {patriots.get('points_per_game_rank')}")
print(f"  All keys: {len(patriots.keys())}")
print(f"  Rank keys: {[k for k in patriots.keys() if 'rank' in k]}")
