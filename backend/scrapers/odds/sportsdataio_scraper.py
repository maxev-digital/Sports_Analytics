#!/usr/bin/env python3
"""
Sports Data IO Scraper
Collects betting lines for NBA and NCAA Basketball
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SportsDataIOScraper:
    """Sports Data IO - Professional sports data API"""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('SPORTSDATAIO_API_KEY')
        self.base_url = 'https://api.sportsdata.io/v3'

        if not self.api_key:
            raise ValueError("SPORTSDATAIO_API_KEY not found in .env file")

    def get_nba_odds(self, date=None, days_ahead=7):
        """
        Get NBA odds for specified date range

        Args:
            date: Start date (YYYY-MM-DD format). Defaults to today.
            days_ahead: Number of days ahead to fetch (default 7)

        Returns:
            DataFrame with odds data
        """
        if date is None:
            date = datetime.now()
        else:
            date = datetime.strptime(date, '%Y-%m-%d')

        print(f"Fetching NBA odds from Sports Data IO...")

        all_odds = []

        # Fetch odds for each day
        for day_offset in range(days_ahead + 1):
            fetch_date = date + timedelta(days=day_offset)
            date_str = fetch_date.strftime('%Y-%m-%d')

            url = f'{self.base_url}/nba/odds/json/GameOddsByDate/{date_str}'

            try:
                response = requests.get(url, params={'key': self.api_key}, timeout=10)

                if response.status_code != 200:
                    print(f"  [{date_str}] Error: HTTP {response.status_code}")
                    continue

                games = response.json()

                if not games:
                    print(f"  [{date_str}] No games scheduled")
                    continue

                print(f"  [{date_str}] Found {len(games)} games")

                # Parse odds data from each game
                for game in games:
                    game_id = game['GameId']
                    home_team = game['HomeTeamName']
                    away_team = game['AwayTeamName']
                    commence_time = game['DateTime']
                    status = game.get('Status', 'Scheduled')

                    # Extract pregame odds from each sportsbook
                    for odd in game.get('PregameOdds', []):
                        sportsbook = odd['Sportsbook']

                        # Only process odds with Over/Under data
                        if odd.get('OverUnder') is not None:
                            all_odds.append({
                                'game_id': game_id,
                                'home_team': home_team,
                                'away_team': away_team,
                                'commence_time': commence_time,
                                'game_status': status,
                                'sportsbook': sportsbook,
                                'total_line': odd.get('OverUnder'),
                                'over_price': odd.get('OverPayout'),
                                'under_price': odd.get('UnderPayout'),
                                'home_spread': odd.get('HomePointSpread'),
                                'away_spread': odd.get('AwayPointSpread'),
                                'home_spread_price': odd.get('HomePointSpreadPayout'),
                                'away_spread_price': odd.get('AwayPointSpreadPayout'),
                                'home_moneyline': odd.get('HomeMoneyLine'),
                                'away_moneyline': odd.get('AwayMoneyLine'),
                                'odds_updated': odd.get('Updated'),
                                'timestamp': datetime.now().isoformat(),
                                'market_type': 'pregame'
                            })

                    # Extract live odds if available
                    for odd in game.get('LiveOdds', []):
                        sportsbook = odd['Sportsbook']

                        if odd.get('OverUnder') is not None:
                            all_odds.append({
                                'game_id': game_id,
                                'home_team': home_team,
                                'away_team': away_team,
                                'commence_time': commence_time,
                                'game_status': status,
                                'sportsbook': sportsbook,
                                'total_line': odd.get('OverUnder'),
                                'over_price': odd.get('OverPayout'),
                                'under_price': odd.get('UnderPayout'),
                                'home_spread': odd.get('HomePointSpread'),
                                'away_spread': odd.get('AwayPointSpread'),
                                'home_spread_price': odd.get('HomePointSpreadPayout'),
                                'away_spread_price': odd.get('AwayPointSpreadPayout'),
                                'home_moneyline': odd.get('HomeMoneyLine'),
                                'away_moneyline': odd.get('AwayMoneyLine'),
                                'odds_updated': odd.get('Updated'),
                                'timestamp': datetime.now().isoformat(),
                                'market_type': 'live'
                            })

            except Exception as e:
                print(f"  [{date_str}] Error: {str(e)}")
                continue

        df = pd.DataFrame(all_odds)

        if not df.empty:
            # Convert timestamps
            df['commence_time'] = pd.to_datetime(df['commence_time'])
            df['odds_updated'] = pd.to_datetime(df['odds_updated'])

            print(f"\nTotal games: {df['game_id'].nunique()}")
            print(f"Total odds entries: {len(df)}")
            print(f"Sportsbooks: {df['sportsbook'].unique().tolist()}")

        return df

    def get_ncaab_odds(self, date=None, days_ahead=7):
        """
        Get NCAA Basketball odds for specified date range

        Args:
            date: Start date (YYYY-MM-DD format). Defaults to today.
            days_ahead: Number of days ahead to fetch (default 7)

        Returns:
            DataFrame with odds data
        """
        if date is None:
            date = datetime.now()
        else:
            date = datetime.strptime(date, '%Y-%m-%d')

        print(f"Fetching NCAA Basketball odds from Sports Data IO...")

        all_odds = []

        # Fetch odds for each day
        for day_offset in range(days_ahead + 1):
            fetch_date = date + timedelta(days=day_offset)
            date_str = fetch_date.strftime('%Y-%m-%d')

            url = f'{self.base_url}/cbb/odds/json/GameOddsByDate/{date_str}'

            try:
                response = requests.get(url, params={'key': self.api_key}, timeout=10)

                if response.status_code != 200:
                    print(f"  [{date_str}] Error: HTTP {response.status_code}")
                    continue

                games = response.json()

                if not games:
                    print(f"  [{date_str}] No games scheduled")
                    continue

                print(f"  [{date_str}] Found {len(games)} games")

                # Parse odds data from each game
                for game in games:
                    game_id = game['GameId']
                    home_team = game['HomeTeamName']
                    away_team = game['AwayTeamName']
                    commence_time = game['DateTime']
                    status = game.get('Status', 'Scheduled')

                    # Extract pregame odds from each sportsbook
                    for odd in game.get('PregameOdds', []):
                        sportsbook = odd['Sportsbook']

                        if odd.get('OverUnder') is not None:
                            all_odds.append({
                                'game_id': game_id,
                                'home_team': home_team,
                                'away_team': away_team,
                                'commence_time': commence_time,
                                'game_status': status,
                                'sportsbook': sportsbook,
                                'total_line': odd.get('OverUnder'),
                                'over_price': odd.get('OverPayout'),
                                'under_price': odd.get('UnderPayout'),
                                'home_spread': odd.get('HomePointSpread'),
                                'away_spread': odd.get('AwayPointSpread'),
                                'home_spread_price': odd.get('HomePointSpreadPayout'),
                                'away_spread_price': odd.get('AwayPointSpreadPayout'),
                                'home_moneyline': odd.get('HomeMoneyLine'),
                                'away_moneyline': odd.get('AwayMoneyLine'),
                                'odds_updated': odd.get('Updated'),
                                'timestamp': datetime.now().isoformat(),
                                'market_type': 'pregame'
                            })

            except Exception as e:
                print(f"  [{date_str}] Error: {str(e)}")
                continue

        df = pd.DataFrame(all_odds)

        if not df.empty:
            # Convert timestamps
            df['commence_time'] = pd.to_datetime(df['commence_time'])
            df['odds_updated'] = pd.to_datetime(df['odds_updated'])

            print(f"\nTotal games: {df['game_id'].nunique()}")
            print(f"Total odds entries: {len(df)}")
            print(f"Sportsbooks: {df['sportsbook'].unique().tolist()}")

        return df

    def get_consensus_total(self, game_id, df):
        """Calculate consensus total across sportsbooks (pregame only)"""
        game_odds = df[(df['game_id'] == game_id) & (df['market_type'] == 'pregame')]

        if game_odds.empty:
            return None

        # Get most common line
        consensus = game_odds['total_line'].mode()

        if len(consensus) > 0:
            return float(consensus.iloc[0])
        else:
            return float(game_odds['total_line'].mean())

    def save_odds(self, sport, date=None, days_ahead=7):
        """
        Scrape and save odds

        Args:
            sport: 'NBA' or 'NCAAB'
            date: Start date (YYYY-MM-DD format). Defaults to today.
            days_ahead: Number of days ahead to fetch
        """
        if sport.upper() == 'NBA':
            odds_df = self.get_nba_odds(date=date, days_ahead=days_ahead)
        elif sport.upper() == 'NCAAB':
            odds_df = self.get_ncaab_odds(date=date, days_ahead=days_ahead)
        else:
            raise ValueError(f"Unknown sport: {sport}")

        if odds_df.empty:
            print(f"WARNING: No {sport} odds to save")
            return None

        # Create output directory
        output_dir = 'backend/data/raw/odds'
        os.makedirs(output_dir, exist_ok=True)

        # Save to CSV with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{output_dir}/{sport.lower()}_odds_{timestamp}.csv'
        odds_df.to_csv(filename, index=False)

        print(f"Saved: {filename}")

        # Also save as latest
        latest_file = f'{output_dir}/{sport.lower()}_odds_latest.csv'
        odds_df.to_csv(latest_file, index=False)
        print(f"Saved: {latest_file}")

        return odds_df


if __name__ == "__main__":
    print("="*60)
    print("SPORTS DATA IO SCRAPER")
    print("="*60)

    try:
        scraper = SportsDataIOScraper()

        # Get NBA odds for next 14 days
        print("\nNBA ODDS:")
        nba_odds = scraper.save_odds('NBA', days_ahead=14)

        if nba_odds is not None and not nba_odds.empty:
            print("\nSample games:")
            for game_id in nba_odds['game_id'].unique()[:3]:
                game = nba_odds[nba_odds['game_id'] == game_id].iloc[0]
                consensus = scraper.get_consensus_total(game_id, nba_odds)
                num_books = len(nba_odds[(nba_odds['game_id'] == game_id) &
                                        (nba_odds['market_type'] == 'pregame')]['sportsbook'].unique())
                print(f"  {game['away_team']} @ {game['home_team']}")
                print(f"    Consensus Total: {consensus} ({num_books} books)")

        print("\nCOMPLETE")

    except ValueError as e:
        print(f"\nERROR: {str(e)}")
        print("\nAdd your Sports Data IO API key to .env:")
        print("SPORTSDATAIO_API_KEY=your_key_here")
