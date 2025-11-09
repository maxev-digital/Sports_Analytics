# extract_goalie_pulls.py
import requests
import pandas as pd
import time
from datetime import datetime
import json
import sys

# === CONFIG ===
SEASON = "20232024"
START_DATE = "2023-10-10"
END_DATE = "2024-04-18"
OUTPUT_FILE = "nhl_goalie_pulls_2023_2024_full.csv"

# === STEP 1: Get all game IDs ===
def get_game_ids():
    from datetime import datetime, timedelta

    game_ids = []
    start = datetime.strptime(START_DATE, "%Y-%m-%d")
    end = datetime.strptime(END_DATE, "%Y-%m-%d")
    current = start
    total_days = (end - start).days + 1

    print(f"Fetching schedules from {START_DATE} to {END_DATE}... ({total_days} days)", flush=True)

    game_types_seen = set()
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        url = f"https://api-web.nhle.com/v1/schedule/{date_str}"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and response.text.strip():
                try:
                    data = response.json()
                    for week in data.get('gameWeek', []):
                        for game in week.get('games', []):
                            game_type = game.get('gameType')
                            game_types_seen.add(game_type)
                            # Only include regular season games (gameType = 2)
                            if game_type == 2:
                                game_ids.append(game['id'])
                except json.JSONDecodeError:
                    # Skip if JSON is invalid
                    pass
            time.sleep(0.05)  # Rate limit
        except Exception as e:
            # Continue on error
            pass

        current += timedelta(days=1)

    print(f"\nGame types found: {sorted(game_types_seen)}", flush=True)
    return game_ids

# === STEP 2: Extract pulls from PBP ===
def extract_pulls_from_game(game_id):
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return []
        data = response.json()
    except Exception as e:
        return []

    pulls = []
    try:
        for play in data.get('plays', []):
            try:
                event = play.get('typeDescKey', '')
                if event in ['goalie-pulled', 'goalie-change']:
                    team = play.get('team', {}).get('abbrev', 'UNKNOWN')
                    period = play.get('period', 3)
                    game_time = play.get('timeInPeriod', '00:00')
                    wall_time = play.get('timeStamp', '')
                    home_score = play.get('homeScore', 0)
                    away_score = play.get('awayScore', 0)
                    trailing = 'home' if home_score < away_score else 'away'
                    score_at_pull = f"{min(home_score, away_score)}-{max(home_score, away_score)}"
                    trailing_goals = abs(home_score - away_score)
                    outcome = 'tie_game' if 'goal' in str(play.get('result', {})) else 'no_tie'

                    pulls.append({
                        'game_id': game_id,
                        'date': data.get('gameDate', ''),
                        'team': team,
                        'period': period,
                        'game_time': game_time,
                        'wall_time': wall_time,
                        'score_at_pull': score_at_pull,
                        'trailing_goals': trailing_goals,
                        'outcome': outcome
                    })
            except Exception:
                # Skip this play if there's an error
                continue
    except Exception:
        pass

    return pulls

# === MAIN ===
if __name__ == "__main__":
    print("=" * 80, flush=True)
    print("NHL GOALIE PULL DATA SCRAPER - 2023-24 SEASON", flush=True)
    print("=" * 80, flush=True)
    print("\nFetching game IDs...", flush=True)
    game_ids = get_game_ids()
    print(f"\nFound {len(game_ids)} games", flush=True)
    print("\nStarting game processing...", flush=True)

    all_pulls = []
    for i, gid in enumerate(game_ids, 1):
        if i % 50 == 0 or i == 1:
            print(f"\nProcessing game {i}/{len(game_ids)} ({i/len(game_ids)*100:.1f}%)", flush=True)
        pulls = extract_pulls_from_game(gid)
        if pulls:
            print(f"  Game {gid}: Found {len(pulls)} goalie pull(s)", flush=True)
        all_pulls.extend(pulls)
        time.sleep(0.2)  # Rate limit

    print("\n" + "=" * 80, flush=True)
    print("SCRAPING COMPLETE!", flush=True)
    print("=" * 80, flush=True)

    df = pd.DataFrame(all_pulls)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSUCCESS: {len(df)} goalie pulls saved to {OUTPUT_FILE}", flush=True)
    print("\nDistribution by trailing goals:", flush=True)
    print(df['trailing_goals'].value_counts(), flush=True)