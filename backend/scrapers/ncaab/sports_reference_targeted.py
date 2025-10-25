#!/usr/bin/env python3
"""
Targeted Sports-Reference Scraper
Only scrapes dates where we have closing lines to maximize efficiency
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import os

def scrape_targeted():
    """Scrape only dates where we have closing line data"""

    print("="*70)
    print("TARGETED SPORTS-REFERENCE SCRAPER")
    print("="*70)

    # Load closing lines to get dates
    closing_file = "backend/data/historical/closing_vs_actual_2024_20251011_104312.csv"
    closing_df = pd.read_csv(closing_file)

    unique_dates = sorted(closing_df['Date'].unique())
    print(f"\n Closing lines cover {len(unique_dates)} unique dates")
    print(f" Date range: {unique_dates[0]} to {unique_dates[-1]}")

    base_url = "https://www.sports-reference.com/cbb/boxscores/index.cgi"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    all_games = []

    for i, date_str in enumerate(unique_dates):
        date = datetime.strptime(date_str, '%Y-%m-%d')

        # Try this date and +/- 1 day for flexible matching
        for offset in [0, -1, 1]:
            target_date = date + timedelta(days=offset)

            params = {
                'month': target_date.month,
                'day': target_date.day,
                'year': target_date.year
            }

            try:
                response = requests.get(base_url, params=params, headers=headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')
                summaries = soup.find_all('div', class_='game_summary')

                for summary in summaries:
                    game = parse_game(summary, target_date)
                    if game:
                        all_games.append(game)

                if len(summaries) > 0:
                    print(f"   {target_date.strftime('%Y-%m-%d')}: {len(summaries)} games")

                time.sleep(0.5)  # Be nice to server

            except Exception as e:
                pass  # Skip errors

        if (i+1) % 10 == 0:
            print(f"\n Progress: {i+1}/{len(unique_dates)} dates, {len(all_games)} games\n")

    # Convert to DataFrame
    df = pd.DataFrame(all_games)

    # Remove duplicates (from flexible date matching)
    df = df.drop_duplicates(subset=['Date', 'Home_Team', 'Away_Team'])

    print(f"\n TOTAL: {len(df)} unique games scraped")

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"backend/data/historical/sports_ref_targeted_{timestamp}.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False)

    print(f" Saved: {output_file}")
    print("="*70)

    return df, output_file


def parse_game(summary, date):
    """Parse a single game"""
    try:
        winner_div = summary.find('tr', class_='winner')
        loser_div = summary.find('tr', class_='loser')

        if not winner_div or not loser_div:
            return None

        winner_team = winner_div.find('a').text.strip()
        winner_score_td = winner_div.find('td', class_='right')
        winner_score = int(winner_score_td.text.strip()) if winner_score_td else None

        loser_team = loser_div.find('a').text.strip()
        loser_score_td = loser_div.find('td', class_='right')
        loser_score = int(loser_score_td.text.strip()) if loser_score_td else None

        if winner_score is None or loser_score is None:
            return None

        # Determine home/away
        table = summary.find('table')
        rows = table.find_all('tr')
        first_team_link = rows[0].find('a')
        first_is_winner = first_team_link and first_team_link.text.strip() == winner_team

        if first_is_winner:
            away_team, away_score = winner_team, winner_score
            home_team, home_score = loser_team, loser_score
        else:
            away_team, away_score = loser_team, loser_score
            home_team, home_score = winner_team, winner_score

        return {
            'Date': date.strftime('%Y-%m-%d'),
            'Home_Team': home_team,
            'Away_Team': away_team,
            'Home_Score': home_score,
            'Away_Score': away_score,
            'Actual_Total': away_score + home_score
        }
    except:
        return None


if __name__ == "__main__":
    import sys
    df, output_file = scrape_targeted()
    sys.exit(0 if df is not None and len(df) > 0 else 1)
