# NHL Goalie Pull Data Scraper v2 - Tracks ALL outcomes after goalie pull
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import json
import sys

# === CONFIG ===
SEASON = "20232024"
START_DATE = "2023-10-10"
END_DATE = "2024-06-25"
OUTPUT_FILE = "nhl_goalie_pulls_v2_2023_2024.csv"

# === STEP 1: Get all game IDs ===
def get_game_ids():
    game_ids = []
    start = datetime.strptime(START_DATE, "%Y-%m-%d")
    end = datetime.strptime(END_DATE, "%Y-%m-%d")
    current = start

    print(f"Fetching schedules from {START_DATE} to {END_DATE}...", flush=True)

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        url = f"https://api-web.nhle.com/v1/schedule/{date_str}"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and response.text.strip():
                data = response.json()
                for week in data.get('gameWeek', []):
                    for game in week.get('games', []):
                        if game.get('gameType') in [2, 3]:  # Regular + Playoffs
                            game_ids.append(game['id'])
            time.sleep(0.03)
        except Exception:
            pass

        current += timedelta(days=1)

    # Deduplicate
    unique_game_ids = list(set(game_ids))
    print(f"Found {len(unique_game_ids)} unique games", flush=True)
    return unique_game_ids


# === STEP 2: Extract goalie pulls and track outcomes ===
def extract_pulls_from_game(game_id):
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return []
        data = response.json()
    except Exception:
        return []

    pulls = []
    try:
        plays = data.get('plays', [])
        home_team = data.get('homeTeam', {}).get('abbrev', 'UNK')
        away_team = data.get('awayTeam', {}).get('abbrev', 'UNK')
        home_team_id = data.get('homeTeam', {}).get('id')
        away_team_id = data.get('awayTeam', {}).get('id')

        # Track which teams have pulled goalie (to avoid duplicates)
        pulls_tracked = set()

        for i, play in enumerate(plays):
            if play.get('typeDescKey') not in ['goal', 'shot-on-goal', 'missed-shot']:
                continue

            details = play.get('details', {})
            goalie_id = details.get('goalieInNetId')

            # Empty net detected (goalie pulled)
            if goalie_id is None or goalie_id == 0:
                period = play.get('periodDescriptor', {}).get('number', 3)
                time_in_period = play.get('timeInPeriod', '00:00')
                home_score = details.get('homeScore', 0)
                away_score = details.get('awayScore', 0)

                # Determine which team pulled (trailing team)
                if home_score < away_score:
                    trailing_team = home_team
                    trailing_team_id = home_team_id
                    score_diff = away_score - home_score
                elif away_score < home_score:
                    trailing_team = away_team
                    trailing_team_id = away_team_id
                    score_diff = home_score - away_score
                else:
                    # Tied game - can't determine who pulled
                    continue

                # Check if we've already tracked this team's pull
                pull_key = f"{game_id}_{trailing_team}_{period}"
                if pull_key in pulls_tracked:
                    continue

                pulls_tracked.add(pull_key)

                # Calculate time remaining
                try:
                    time_parts = time_in_period.split(':')
                    minutes = int(time_parts[0])
                    seconds = int(time_parts[1])
                    time_remaining_seconds = (20 - minutes) * 60 + (60 - seconds)
                except:
                    time_remaining_seconds = 120

                # NOW: Track what happens AFTER the pull
                goal_after_pull = False
                goal_by_trailing = False
                goal_by_opponent = False
                time_to_goal = None
                final_home_score = home_score
                final_away_score = away_score

                # Look at all subsequent plays
                for j in range(i, len(plays)):
                    next_play = plays[j]
                    next_event = next_play.get('typeDescKey')
                    next_details = next_play.get('details', {})

                    # Check if goal scored
                    if next_event == 'goal':
                        goal_after_pull = True
                        final_home_score = next_details.get('homeScore', home_score)
                        final_away_score = next_details.get('awayScore', away_score)

                        scoring_team_id = next_details.get('eventOwnerTeamId')

                        if scoring_team_id == trailing_team_id:
                            goal_by_trailing = True
                        else:
                            goal_by_opponent = True

                        # Calculate time to goal
                        try:
                            next_time = next_play.get('timeInPeriod', '00:00')
                            next_parts = next_time.split(':')
                            next_minutes = int(next_parts[0])
                            next_seconds = int(next_parts[1])
                            next_time_remaining = (20 - next_minutes) * 60 + (60 - next_seconds)
                            time_to_goal = time_remaining_seconds - next_time_remaining
                        except:
                            time_to_goal = None

                        break  # Only care about first goal after pull

                    # Check for period end or game end
                    if next_event in ['period-end', 'game-end']:
                        break

                # Determine outcome
                if goal_by_trailing and goal_by_opponent:
                    outcome = 'both_scored'
                elif goal_by_trailing:
                    outcome = 'trailing_scored'
                elif goal_by_opponent:
                    outcome = 'opponent_scored'
                else:
                    outcome = 'no_goal'

                pulls.append({
                    'game_id': game_id,
                    'date': data.get('gameDate', ''),
                    'team': trailing_team,
                    'period': period,
                    'pull_time': time_in_period,
                    'time_remaining_seconds': time_remaining_seconds,
                    'score_differential': score_diff,
                    'home_score_at_pull': home_score,
                    'away_score_at_pull': away_score,
                    'goal_scored_after': goal_after_pull,
                    'goal_by_trailing_team': goal_by_trailing,
                    'goal_by_opponent': goal_by_opponent,
                    'time_to_goal_seconds': time_to_goal,
                    'outcome': outcome,
                    'final_home_score': final_home_score,
                    'final_away_score': final_away_score,
                    'total_goals_added': (final_home_score + final_away_score) - (home_score + away_score)
                })

    except Exception as e:
        pass

    return pulls


# === MAIN ===
if __name__ == "__main__":
    print("=" * 80, flush=True)
    print("NHL GOALIE PULL SCRAPER V2 - Track ALL Outcomes", flush=True)
    print("=" * 80, flush=True)

    game_ids = get_game_ids()
    print(f"\nProcessing {len(game_ids)} games...\n", flush=True)

    all_pulls = []
    for i, gid in enumerate(game_ids, 1):
        if i % 100 == 0:
            print(f"Processing game {i}/{len(game_ids)} ({i/len(game_ids)*100:.1f}%)", flush=True)

        pulls = extract_pulls_from_game(gid)
        all_pulls.extend(pulls)
        time.sleep(0.15)

    print("\n" + "=" * 80, flush=True)
    print("SCRAPING COMPLETE!", flush=True)
    print("=" * 80, flush=True)

    if all_pulls:
        df = pd.DataFrame(all_pulls)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"\nSUCCESS: {len(df)} goalie pulls saved to {OUTPUT_FILE}", flush=True)

        print("\n" + "=" * 80, flush=True)
        print("OUTCOME ANALYSIS", flush=True)
        print("=" * 80, flush=True)

        print(f"\nTotal goalie pulls detected: {len(df)}", flush=True)
        print(f"\nGoals scored after pull: {df['goal_scored_after'].sum()} ({df['goal_scored_after'].sum()/len(df)*100:.1f}%)", flush=True)
        print(f"No goals after pull: {(~df['goal_scored_after']).sum()} ({(~df['goal_scored_after']).sum()/len(df)*100:.1f}%)", flush=True)

        print("\nOutcome breakdown:", flush=True)
        print(df['outcome'].value_counts(), flush=True)

        print("\nScore differential:", flush=True)
        print(df['score_differential'].value_counts().sort_index(), flush=True)

        print("\nAverage goals added to total:", flush=True)
        print(f"  Mean: {df['total_goals_added'].mean():.2f}", flush=True)
        print(f"  Median: {df['total_goals_added'].median():.2f}", flush=True)
    else:
        print("\nWARNING: No goalie pulls detected!", flush=True)
