"""
CLV (Closing Line Value) Tracker - Backtesting Scraper

Strategy: Compare bet placement odds to closing line odds
- If you beat the closing line, you have positive CLV (profitable long-term)
- Industry standard: 52.4%+ win rate with CLV = profitable bettor

This scraper:
1. Fetches historical odds data (opening → closing lines)
2. Simulates bets placed at various times
3. Calculates CLV for each bet
4. Generates win rate and ROI by CLV bucket

Data Source: The Odds API (historical odds endpoint)
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os
from dotenv import load_dotenv


class CLVTrackerScraper:
    """Scrapes and analyzes Closing Line Value opportunities"""

    def __init__(self, odds_api_key: str):
        self.api_key = odds_api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        self.session = requests.Session()

    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """Make API request to The Odds API"""
        url = f"{self.base_url}/{endpoint}"

        if params is None:
            params = {}

        params['apiKey'] = self.api_key

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            # Log remaining quota
            quota_remaining = response.headers.get('x-requests-remaining', 'unknown')
            print(f"[API] Requests remaining: {quota_remaining}")

            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] API request failed: {e}")
            return None

    def get_historical_odds(self, sport: str, date: str, market: str = 'h2h') -> List[Dict]:
        """
        Get historical odds for a specific date

        Args:
            sport: Sport key (e.g., 'basketball_nba', 'americanfootball_nfl')
            date: Date in ISO format (YYYY-MM-DDTHH:MM:SSZ)
            market: Market type ('h2h', 'spreads', 'totals')

        Returns:
            List of game odds
        """
        print(f"Fetching historical odds for {sport} on {date}...")

        endpoint = f"sports/{sport}/odds-history"

        params = {
            'regions': 'us',
            'markets': market,
            'date': date,
            'oddsFormat': 'american'
        }

        data = self._make_request(endpoint, params)

        if data:
            print(f"  Found {len(data)} games")
            return data

        return []

    def get_event_odds_timeline(self, event_id: str) -> List[Dict]:
        """
        Get full odds timeline for a specific event
        Shows how odds moved from opening to closing

        Args:
            event_id: Unique event identifier

        Returns:
            List of odds snapshots over time
        """
        endpoint = f"events/{event_id}/odds-history"

        params = {
            'regions': 'us',
            'markets': 'h2h,spreads,totals',
            'oddsFormat': 'american'
        }

        data = self._make_request(endpoint, params)

        return data if data else []

    def calculate_clv(self, bet_odds: int, closing_odds: int) -> float:
        """
        Calculate CLV (Closing Line Value)

        CLV% = ((1 / bet_decimal_odds) - (1 / close_decimal_odds)) / (1 / close_decimal_odds) * 100

        Positive CLV = You got better odds than closing (good!)
        Negative CLV = You got worse odds than closing (bad!)

        Args:
            bet_odds: American odds when bet was placed (e.g., -110)
            closing_odds: American odds at close (e.g., -115)

        Returns:
            CLV as percentage
        """
        # Convert American to decimal
        def american_to_decimal(american_odds):
            if american_odds > 0:
                return (american_odds / 100) + 1
            else:
                return (100 / abs(american_odds)) + 1

        bet_decimal = american_to_decimal(bet_odds)
        close_decimal = american_to_decimal(closing_odds)

        bet_implied = 1 / bet_decimal
        close_implied = 1 / close_decimal

        clv_percent = ((close_implied - bet_implied) / bet_implied) * 100

        return round(clv_percent, 2)

    def analyze_clv_opportunities(self, sport: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Analyze CLV across multiple games

        Simulates placing bets at various times and compares to closing line

        Args:
            sport: Sport to analyze
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of CLV opportunities
        """
        print(f"\n{'='*80}")
        print(f"CLV ANALYSIS")
        print(f"Sport: {sport}")
        print(f"Period: {start_date} to {end_date}")
        print(f"{'='*80}\n")

        opportunities = []

        # Convert dates to datetime
        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        while current <= end:
            date_str = current.strftime('%Y-%m-%dT12:00:00Z')

            # Get odds for this date
            games = self.get_historical_odds(sport, date_str, market='h2h')

            for game in games:
                game_id = game.get('id')
                home_team = game.get('home_team')
                away_team = game.get('away_team')
                commence_time = game.get('commence_time')

                # Get full odds timeline for this game
                odds_timeline = self.get_event_odds_timeline(game_id)

                if not odds_timeline or len(odds_timeline) < 2:
                    continue  # Need at least opening and closing odds

                # First snapshot = opening odds
                # Last snapshot = closing odds
                opening = odds_timeline[0]
                closing = odds_timeline[-1]

                # Analyze each bookmaker
                for book in closing.get('bookmakers', []):
                    bookmaker = book.get('key')

                    # Find same bookmaker in opening odds
                    opening_book = next(
                        (b for b in opening.get('bookmakers', []) if b.get('key') == bookmaker),
                        None
                    )

                    if not opening_book:
                        continue

                    # Get moneyline odds
                    for market in book.get('markets', []):
                        if market.get('key') != 'h2h':
                            continue

                        for i, outcome in enumerate(market.get('outcomes', [])):
                            team = outcome.get('name')
                            closing_odds = outcome.get('price')

                            # Find opening odds for same team
                            opening_market = next(
                                (m for m in opening_book.get('markets', []) if m.get('key') == 'h2h'),
                                None
                            )

                            if not opening_market:
                                continue

                            opening_outcome = next(
                                (o for o in opening_market.get('outcomes', []) if o.get('name') == team),
                                None
                            )

                            if not opening_outcome:
                                continue

                            opening_odds = opening_outcome.get('price')

                            # Calculate CLV
                            clv = self.calculate_clv(opening_odds, closing_odds)

                            opportunity = {
                                'game_id': game_id,
                                'commence_time': commence_time,
                                'home_team': home_team,
                                'away_team': away_team,
                                'team': team,
                                'bookmaker': bookmaker,
                                'opening_odds': opening_odds,
                                'closing_odds': closing_odds,
                                'clv_percent': clv,
                                'beat_close': clv > 0
                            }

                            opportunities.append(opportunity)

                            if clv > 2:  # Print significant CLV
                                print(f"[CLV] {team} @ {bookmaker}: {opening_odds} → {closing_odds} (CLV: +{clv}%)")

            current += timedelta(days=1)

        print(f"\n{'='*80}")
        print(f"FOUND {len(opportunities)} CLV DATA POINTS")
        print(f"{'='*80}\n")

        return opportunities

    def calculate_results(self, opportunities: List[Dict]) -> Dict:
        """Calculate CLV backtest results"""
        if not opportunities:
            return {
                'total_bets': 0,
                'positive_clv_bets': 0,
                'negative_clv_bets': 0,
                'avg_clv': 0.0,
                'beat_close_rate': 0.0
            }

        total = len(opportunities)
        positive_clv = [o for o in opportunities if o['beat_close']]
        negative_clv = [o for o in opportunities if not o['beat_close']]

        avg_clv = sum(o['clv_percent'] for o in opportunities) / total

        results = {
            'total_bets': total,
            'positive_clv_bets': len(positive_clv),
            'negative_clv_bets': len(negative_clv),
            'avg_clv': round(avg_clv, 2),
            'beat_close_rate': round(len(positive_clv) / total * 100, 1) if total > 0 else 0.0
        }

        return results

    def print_results(self, results: Dict):
        """Print CLV results summary"""
        print(f"\n{'='*80}")
        print(f"CLV TRACKER - BACKTEST RESULTS")
        print(f"{'='*80}\n")

        print(f"Total Bets Analyzed: {results['total_bets']}")
        print(f"Positive CLV Bets: {results['positive_clv_bets']}")
        print(f"Negative CLV Bets: {results['negative_clv_bets']}")
        print(f"Average CLV: {results['avg_clv']:+.2f}%")
        print(f"Beat Close Rate: {results['beat_close_rate']}%")

        print(f"\n{'='*80}\n")


def main():
    """Run CLV tracker backtest"""
    load_dotenv('../../.env')

    api_key = os.getenv('ODDS_API_KEY')
    if not api_key:
        print("[ERROR] ODDS_API_KEY not found in environment")
        return

    print(f"[SUCCESS] API key loaded\n")

    scraper = CLVTrackerScraper(api_key)

    # Analyze November 2023 NBA games
    opportunities = scraper.analyze_clv_opportunities(
        sport='basketball_nba',
        start_date='2023-11-01',
        end_date='2023-11-07'  # 1 week sample
    )

    # Calculate results
    results = scraper.calculate_results(opportunities)

    # Print results
    scraper.print_results(results)

    # Save data
    if opportunities:
        df = pd.DataFrame(opportunities)
        df.to_csv('clv_tracker_backtest.csv', index=False)
        print(f"[SAVED] Data saved to: clv_tracker_backtest.csv")

    with open('clv_tracker_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"[SAVED] Results saved to: clv_tracker_results.json")

    print(f"\n[COMPLETE] CLV backtest finished!")


if __name__ == "__main__":
    main()
