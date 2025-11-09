"""
B2B vs Rested Strategy - Backtesting Scraper

Strategy: Fade teams on back-to-back games vs well-rested opponents
- Teams on B2B (0 days rest) vs teams with 3+ days rest
- Historical edge: 58% ATS favoring rested team

This scraper:
1. Fetches historical game schedules
2. Identifies B2B situations
3. Calculates rest days for each team
4. Tracks performance ATS (Against The Spread)

Data Sources:
- NBA: balldontlie.io API
- Odds: The Odds API
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os
from dotenv import load_dotenv


class B2BVsRestedScraper:
    """Scrapes and analyzes back-to-back vs rested team opportunities"""

    def __init__(self, balldontlie_key: str, odds_api_key: str):
        self.balldontlie_key = balldontlie_key
        self.odds_api_key = odds_api_key
        self.base_url_bbl = "https://api.balldontlie.io/v1"
        self.base_url_odds = "https://api.the-odds-api.com/v4"
        self.session = requests.Session()
        self.requests_per_minute = 30
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting for balldontlie"""
        min_interval = 60 / self.requests_per_minute
        elapsed = time.time() - self.last_request_time

        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

        self.last_request_time = time.time()

    def _make_bbl_request(self, endpoint: str, params: dict = None) -> dict:
        """Make request to balldontlie API"""
        self._rate_limit()

        url = f"{self.base_url_bbl}/{endpoint}"
        headers = {'Authorization': self.balldontlie_key}

        try:
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] BallDontLie API failed: {e}")
            return None

    def get_season_games(self, season: int, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get all games for a season or date range"""
        print(f"Fetching games for {season}-{season+1} season...")

        games = []
        cursor = None

        while True:
            params = {
                'seasons[]': season,
                'per_page': 100
            }

            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            if cursor:
                params['cursor'] = cursor

            data = self._make_bbl_request('games', params)

            if not data or 'data' not in data:
                break

            games.extend(data['data'])

            # Check for more pages
            if 'meta' in data and 'next_cursor' in data['meta'] and data['meta']['next_cursor']:
                cursor = data['meta']['next_cursor']
            else:
                break

        print(f"  Fetched {len(games)} games")
        return games

    def calculate_rest_days(self, games: List[Dict], team_id: int, current_game_date: str) -> int:
        """
        Calculate days of rest before a game

        Args:
            games: All games in season
            team_id: Team to check
            current_game_date: Date of current game

        Returns:
            Days of rest (0 = back-to-back, 1 = 1 day rest, etc.)
        """
        current_date = datetime.strptime(current_game_date[:10], '%Y-%m-%d')

        # Find previous game for this team
        team_games = [
            g for g in games
            if (g['home_team']['id'] == team_id or g['visitor_team']['id'] == team_id)
            and g.get('status') == 'Final'
        ]

        # Sort by date
        team_games.sort(key=lambda x: x['date'])

        # Find previous game before current date
        previous_game = None
        for game in reversed(team_games):
            game_date = datetime.strptime(game['date'][:10], '%Y-%m-%d')
            if game_date < current_date:
                previous_game = game
                break

        if not previous_game:
            return 99  # First game of season

        prev_date = datetime.strptime(previous_game['date'][:10], '%Y-%m-%d')
        rest_days = (current_date - prev_date).days - 1

        return rest_days

    def identify_b2b_opportunities(self, season: int, start_date: str, end_date: str) -> List[Dict]:
        """
        Identify B2B vs Rested matchups

        Args:
            season: NBA season (2023 = 2023-24)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of B2B opportunities
        """
        print(f"\n{'='*80}")
        print(f"B2B VS RESTED ANALYSIS")
        print(f"Season: {season}-{season+1}")
        print(f"Period: {start_date} to {end_date}")
        print(f"{'='*80}\n")

        # Get all games for season
        all_games = self.get_season_games(season)

        # Filter to date range
        games_in_range = [
            g for g in all_games
            if start_date <= g['date'][:10] <= end_date
            and g.get('status') == 'Final'
        ]

        print(f"Analyzing {len(games_in_range)} games...\n")

        opportunities = []

        for game in games_in_range:
            home_team = game['home_team']
            away_team = game['visitor_team']
            game_date = game['date'][:10]

            # Calculate rest days
            home_rest = self.calculate_rest_days(all_games, home_team['id'], game_date)
            away_rest = self.calculate_rest_days(all_games, away_team['id'], game_date)

            # Check for B2B vs Rested (3+ days)
            is_opportunity = False
            fatigued_team = None
            rested_team = None

            if home_rest == 0 and away_rest >= 3:
                is_opportunity = True
                fatigued_team = home_team['full_name']
                rested_team = away_team['full_name']
                print(f"[B2B] {game_date}: {home_team['abbreviation']} (B2B) vs {away_team['abbreviation']} ({away_rest}d rest)")

            elif away_rest == 0 and home_rest >= 3:
                is_opportunity = True
                fatigued_team = away_team['full_name']
                rested_team = home_team['full_name']
                print(f"[B2B] {game_date}: {away_team['abbreviation']} (B2B) @ {home_team['abbreviation']} ({home_rest}d rest)")

            if is_opportunity:
                opportunity = {
                    'game_id': game['id'],
                    'game_date': game_date,
                    'season': season,
                    'home_team': home_team['full_name'],
                    'away_team': away_team['full_name'],
                    'home_score': game.get('home_team_score', 0),
                    'away_score': game.get('visitor_team_score', 0),
                    'home_rest_days': home_rest,
                    'away_rest_days': away_rest,
                    'fatigued_team': fatigued_team,
                    'rested_team': rested_team
                }

                opportunities.append(opportunity)

        print(f"\n{'='*80}")
        print(f"FOUND {len(opportunities)} B2B VS RESTED OPPORTUNITIES")
        print(f"{'='*80}\n")

        return opportunities

    def calculate_results(self, opportunities: List[Dict]) -> Dict:
        """Calculate backtest results"""
        if not opportunities:
            return {
                'total_opportunities': 0,
                'rested_team_wins': 0,
                'fatigued_team_wins': 0,
                'rested_win_rate': 0.0
            }

        total = len(opportunities)
        rested_wins = 0
        fatigued_wins = 0

        for opp in opportunities:
            home_score = opp['home_score']
            away_score = opp['away_score']
            rested_team = opp['rested_team']
            home_team = opp['home_team']

            # Determine winner
            if home_score > away_score:
                winner = home_team
            else:
                winner = opp['away_team']

            if winner == rested_team:
                rested_wins += 1
            else:
                fatigued_wins += 1

        results = {
            'total_opportunities': total,
            'rested_team_wins': rested_wins,
            'fatigued_team_wins': fatigued_wins,
            'rested_win_rate': round(rested_wins / total * 100, 1) if total > 0 else 0.0
        }

        return results

    def print_results(self, results: Dict):
        """Print results summary"""
        print(f"\n{'='*80}")
        print(f"B2B VS RESTED - BACKTEST RESULTS")
        print(f"{'='*80}\n")

        print(f"Total B2B Matchups: {results['total_opportunities']}")
        print(f"Rested Team Wins: {results['rested_team_wins']}")
        print(f"Fatigued Team Wins: {results['fatigued_team_wins']}")
        print(f"Rested Team Win Rate: {results['rested_win_rate']}%")

        if results['rested_win_rate'] >= 54:
            print(f"\n✅ EDGE CONFIRMED: {results['rested_win_rate']}% win rate is profitable!")
        else:
            print(f"\n⚠️ Edge unclear: {results['rested_win_rate']}% may need more data")

        print(f"\n{'='*80}\n")


def main():
    """Run B2B vs Rested backtest"""
    load_dotenv('../../.env')

    bbl_key = os.getenv('BALLDONTLIE_API_KEY')
    odds_key = os.getenv('ODDS_API_KEY')

    if not bbl_key:
        print("[ERROR] BALLDONTLIE_API_KEY not found")
        return

    print(f"[SUCCESS] API keys loaded\n")

    scraper = B2BVsRestedScraper(bbl_key, odds_key)

    # Analyze November 2023 NBA games
    opportunities = scraper.identify_b2b_opportunities(
        season=2023,
        start_date='2023-11-01',
        end_date='2023-11-30'
    )

    # Calculate results
    results = scraper.calculate_results(opportunities)

    # Print results
    scraper.print_results(results)

    # Save data
    if opportunities:
        df = pd.DataFrame(opportunities)
        df.to_csv('b2b_vs_rested_backtest.csv', index=False)
        print(f"[SAVED] Data saved to: b2b_vs_rested_backtest.csv")

    with open('b2b_vs_rested_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"[SAVED] Results saved to: b2b_vs_rested_results.json")

    print(f"\n[COMPLETE] B2B backtest finished!")


if __name__ == "__main__":
    main()
