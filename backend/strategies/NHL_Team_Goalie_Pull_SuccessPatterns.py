# analyze_teams.py
df = pd.read_csv('nhl_goalie_pulls_2023_2024_full.csv')

team_stats = df.groupby('team').agg(
    pulls=('game_id', 'nunique'),
    success_rate=('outcome', lambda x: (x == 'tie_game').mean()),
    avg_time=('game_time', lambda x: pd.to_datetime(x, format='%M:%S').mean().strftime('%M:%S'))
).round(3)

team_stats['+EV'] = (team_stats['success_rate'] * 3.5 - 1).round(3)  # Rough +EV
team_stats = team_stats.sort_values('pulls', ascending=False)

print(team_stats.head(10))
team_stats.to_csv('team_goalie_pull_patterns.csv')