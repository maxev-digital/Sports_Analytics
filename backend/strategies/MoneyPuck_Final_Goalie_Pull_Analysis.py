"""
NHL Goalie Pull Analysis - Moneypuck Data 2023-24
Track REAL outcomes: goals scored, success rates, timing
"""

import pandas as pd
import requests
import zipfile
import io

print("=" * 80)
print("MONEYPUCK GOALIE PULL ANALYSIS - 2023-24 SEASON")
print("=" * 80)

# Download Moneypuck data
print("\nDownloading data...")
url = "https://peter-tanner.com/moneypuck/downloads/shots_2023.zip"
response = requests.get(url, timeout=120)

with zipfile.ZipFile(io.BytesIO(response.content)) as z:
    csv_filename = z.namelist()[0]
    with z.open(csv_filename) as f:
        df = pd.read_csv(f, low_memory=False)

print(f"Loaded {len(df):,} shots")

# Filter for empty net situations
df_empty_net = df[df['shotOnEmptyNet'] == 1].copy()
print(f"Empty net shots: {len(df_empty_net):,}")

# Determine which team pulled goalie
df_empty_net['pullingTeam'] = df_empty_net.apply(
    lambda row: row['awayTeamCode'] if row['homeEmptyNet'] == 1 else row['homeTeamCode'],
    axis=1
)

df_empty_net['opposingTeam'] = df_empty_net.apply(
    lambda row: row['homeTeamCode'] if row['homeEmptyNet'] == 1 else row['awayTeamCode'],
    axis=1
)

# Get score when pull happened
df_empty_net['pullingTeamScore'] = df_empty_net.apply(
    lambda row: row['awayTeamGoals'] if row['homeEmptyNet'] == 1 else row['homeTeamGoals'],
    axis=1
)

df_empty_net['opposingTeamScore'] = df_empty_net.apply(
    lambda row: row['homeTeamGoals'] if row['homeEmptyNet'] == 1 else row['awayTeamGoals'],
    axis=1
)

df_empty_net['scoreDifferential'] = df_empty_net['opposingTeamScore'] - df_empty_net['pullingTeamScore']

# Get timing info
if 'time' in df.columns:
    df_empty_net['pullTime'] = df_empty_net['time']
elif 'gameSeconds' in df.columns:
    df_empty_net['pullTime'] = df_empty_net['gameSeconds']

# Get period
df_empty_net['period'] = df_empty_net['period'] if 'period' in df.columns else 3

# Analyze outcomes per game
print("\n" + "=" * 80)
print("ANALYZING GOALIE PULL OUTCOMES PER GAME")
print("=" * 80)

game_pulls = []

for game_id, game_data in df_empty_net.groupby('game_id'):
    # Get first empty net shot (when pull happened)
    first_pull = game_data.iloc[0]

    pulling_team = first_pull['pullingTeam']
    pull_score_diff = first_pull['scoreDifferential']

    # Get all subsequent shots in this game (from full dataframe)
    game_shots = df[df['game_id'] == game_id].copy()
    game_shots = game_shots.sort_values('shotID')

    # Find shots after the pull
    first_pull_shot_id = first_pull['shotID']
    shots_after_pull = game_shots[game_shots['shotID'] >= first_pull_shot_id]

    # Track goals scored after pull
    goals_after_pull = shots_after_pull[shots_after_pull['goal'] == 1]

    goals_by_pulling_team = 0
    goals_by_opponent = 0

    for _, goal_shot in goals_after_pull.iterrows():
        scoring_team = goal_shot['homeTeamCode'] if goal_shot['isHomeTeam'] == 1 else goal_shot['awayTeamCode']

        if scoring_team == pulling_team:
            goals_by_pulling_team += 1
        else:
            goals_by_opponent += 1

    # Determine outcome
    if goals_by_pulling_team > 0 and goals_by_opponent > 0:
        outcome = 'both_scored'
    elif goals_by_pulling_team > 0:
        outcome = 'pulling_team_scored'
    elif goals_by_opponent > 0:
        outcome = 'opponent_scored'
    else:
        outcome = 'no_goal'

    game_pulls.append({
        'game_id': game_id,
        'pulling_team': pulling_team,
        'score_differential': pull_score_diff,
        'period': first_pull['period'],
        'goals_by_pulling_team': goals_by_pulling_team,
        'goals_by_opponent': goals_by_opponent,
        'total_goals_after_pull': goals_by_pulling_team + goals_by_opponent,
        'outcome': outcome,
        'pulling_team_tied_game': goals_by_pulling_team >= pull_score_diff
    })

# Create summary dataframe
pulls_df = pd.DataFrame(game_pulls)

print(f"\nAnalyzed {len(pulls_df)} goalie pull situations")

# Save to CSV
output_file = 'moneypuck_goalie_pulls_2023_2024_FINAL.csv'
pulls_df.to_csv(output_file, index=False)
print(f"Saved to: {output_file}")

# STATISTICS
print("\n" + "=" * 80)
print("GOALIE PULL STATISTICS - 2023-24 SEASON")
print("=" * 80)

print(f"\nTotal goalie pulls: {len(pulls_df)}")

print(f"\nSCORE DIFFERENTIAL:")
print(pulls_df['score_differential'].value_counts().sort_index())

print(f"\nGOALS SCORED AFTER PULL:")
print(f"At least 1 goal: {(pulls_df['total_goals_after_pull'] > 0).sum()} ({(pulls_df['total_goals_after_pull'] > 0).sum()/len(pulls_df)*100:.1f}%)")
print(f"No goals: {(pulls_df['total_goals_after_pull'] == 0).sum()} ({(pulls_df['total_goals_after_pull'] == 0).sum()/len(pulls_df)*100:.1f}%)")

print(f"\nPULLING TEAM SCORED:")
print(f"Yes: {(pulls_df['goals_by_pulling_team'] > 0).sum()} ({(pulls_df['goals_by_pulling_team'] > 0).sum()/len(pulls_df)*100:.1f}%)")
print(f"No: {(pulls_df['goals_by_pulling_team'] == 0).sum()} ({(pulls_df['goals_by_pulling_team'] == 0).sum()/len(pulls_df)*100:.1f}%)")

print(f"\nOPPONENT SCORED:")
print(f"Yes: {(pulls_df['goals_by_opponent'] > 0).sum()} ({(pulls_df['goals_by_opponent'] > 0).sum()/len(pulls_df)*100:.1f}%)")
print(f"No: {(pulls_df['goals_by_opponent'] == 0).sum()} ({(pulls_df['goals_by_opponent'] == 0).sum()/len(pulls_df)*100:.1f}%)")

print(f"\nPULLING TEAM TIED GAME:")
print(f"Yes: {pulls_df['pulling_team_tied_game'].sum()} ({pulls_df['pulling_team_tied_game'].sum()/len(pulls_df)*100:.1f}%)")
print(f"No: {(~pulls_df['pulling_team_tied_game']).sum()} ({(~pulls_df['pulling_team_tied_game']).sum()/len(pulls_df)*100:.1f}%)")

print(f"\nOUTCOME BREAKDOWN:")
print(pulls_df['outcome'].value_counts())

print(f"\nAVERAGE GOALS ADDED TO TOTAL:")
print(f"Mean: {pulls_df['total_goals_after_pull'].mean():.2f}")
print(f"Median: {pulls_df['total_goals_after_pull'].median():.0f}")

print(f"\nTOP 10 TEAMS BY GOALIE PULLS:")
print(pulls_df['pulling_team'].value_counts().head(10))

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE!")
print("=" * 80)
