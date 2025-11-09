# Run this in Python
import requests
import pandas as pd

def get_all_pulls():
    pulls = []
    page = 1
    while True:
        url = f"https://api-web.nhle.com/v1/gamecenter/all/play-by-play"
        params = {'season': '20232024', 'page': page, 'per_page': 100}
        data = requests.get(url, params=params).json()
        for game in data.get('games', []):
            for play in game.get('plays', []):
                if play.get('typeDescKey') in ['goalie-pulled', 'goalie-change']:
                    pulls.append({
                        'game_id': game['id'],
                        'date': game['gameDate'],
                        'team': play['team']['abbrev'],
                        'period': play['period'],
                        'game_time': play['timeInPeriod'],
                        'score_at_pull': f"{play['homeScore']}-{play['awayScore']}",
                        'trailing_goals': abs(play['homeScore'] - play['awayScore']),
                        'outcome': 'tie_game' if 'goal' in play.get('result', {}) else 'no_tie'
                    })
        if page >= data.get('totalPages', 1):
            break
        page += 1
    return pd.DataFrame(pulls)

df = get_all_pulls()
df.to_csv('nhl_goalie_pulls_2023_2024_FULL.csv', index=False)
print(f"Full pulls: {len(df)}")