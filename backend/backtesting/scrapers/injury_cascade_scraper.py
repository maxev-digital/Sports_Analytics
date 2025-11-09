"""
Injury Cascade Props Strategy - Data Scraper & Backtest Engine

Strategy: When a star player exits mid-game, bet role player props to go over

This scraper:
1. Identifies games where team's leading scorer played <30 minutes (early exit)
2. Tracks substitute player performance in that game
3. Compares to their season averages
4. Calculates which prop types (PTS/REB/AST) are most profitable

Data Sources:
- NBA: balldontlie.io API (free)
- Stats: Player game logs and season averages
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os
from dotenv import load_dotenv


class InjuryCascadeScraper:
    """Scrapes NBA injury cascade opportunities"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize scraper

        Args:
            api_key: Optional API key (balldontlie.io is free, no key needed)
        """
        self.base_url = "https://api.balldontlie.io/v1"
        self.api_key = api_key
        self.session = requests.Session()

        # Rate limiting - be conservative to avoid 429 errors
        self.requests_per_minute = 30  # Reduced from 60 to be safe
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting"""
        min_interval = 60 / self.requests_per_minute
        elapsed = time.time() - self.last_request_time

        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: dict = None, retry_count: int = 0) -> dict:
        """Make API request with rate limiting and retry logic"""
        self._rate_limit()

        url = f"{self.base_url}/{endpoint}"
        headers = {}

        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        try:
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429 and retry_count < 3:
                # Rate limited - wait and retry with exponential backoff
                wait_time = (retry_count + 1) * 30  # 30, 60, 90 seconds
                print(f"[RATE LIMIT] Waiting {wait_time}s before retry {retry_count + 1}/3...")
                time.sleep(wait_time)
                return self._make_request(endpoint, params, retry_count + 1)
            else:
                print(f"[ERROR] API request failed: {e}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] API request failed: {e}")
            return None

    def get_season_games(self, season: int, team_id: Optional[int] = None) -> List[Dict]:
        """
        Get all games for a season

        Args:
            season: Season year (e.g., 2023 for 2023-24 season)
            team_id: Optional filter by team

        Returns:
            List of game dicts
        """
        print(f"Fetching games for {season}-{season+1} season...")

        games = []
        cursor = None
        page_num = 1

        while True:
            params = {
                'seasons[]': [season],
                'per_page': 100
            }

            if cursor:
                params['cursor'] = cursor

            if team_id:
                params['team_ids[]'] = [team_id]

            data = self._make_request('games', params)

            if not data or 'data' not in data:
                break

            games.extend(data['data'])

            # Check if more pages (cursor-based pagination)
            if 'meta' in data and 'next_cursor' in data['meta'] and data['meta']['next_cursor']:
                cursor = data['meta']['next_cursor']
                page_num += 1
                print(f"  Fetched page {page_num} (cursor: {cursor})...")
            else:
                break  # No more pages

        print(f"  Total games: {len(games)}")
        return games

    def get_player_season_stats(self, season: int, player_id: int) -> Optional[Dict]:
        """Get player's season averages"""
        params = {
            'seasons[]': [season],
            'player_ids[]': [player_id],
            'per_page': 100
        }

        data = self._make_request('season_averages', params)

        if data and 'data' in data and len(data['data']) > 0:
            return data['data'][0]

        return None

    def get_game_stats(self, game_id: int) -> List[Dict]:
        """Get all player stats for a specific game"""
        params = {
            'game_ids[]': [game_id],
            'per_page': 100
        }

        data = self._make_request('stats', params)

        if data and 'data' in data:
            return data['data']

        return []

    def get_team_roster(self, team_id: int, season: int) -> List[Dict]:
        """Get team's roster for season"""
        # Get season averages for all players on team
        params = {
            'seasons[]': [season],
            'per_page': 100
        }

        all_stats = []
        page = 1

        while True:
            params['page'] = page
            data = self._make_request('season_averages', params)

            if not data or 'data' not in data:
                break

            all_stats.extend(data['data'])

            if page >= data['meta']['total_pages']:
                break

            page += 1

        # Filter to team and sort by PPG
        team_players = [
            p for p in all_stats
            if p.get('player', {}).get('team_id') == team_id
        ]

        team_players.sort(key=lambda x: x.get('pts', 0), reverse=True)

        return team_players

    def identify_star_exits(self, season: int, min_ppg: float = 15.0,
                           max_minutes: int = 30) -> List[Dict]:
        """
        Identify games where star player exited early

        Args:
            season: Season year
            min_ppg: Minimum PPG to qualify as "star" (default 15+)
            max_minutes: Max minutes to qualify as "early exit" (default <30)

        Returns:
            List of opportunities
        """
        print(f"\n{'='*80}")
        print(f"IDENTIFYING INJURY CASCADE OPPORTUNITIES")
        print(f"Season: {season}-{season+1}")
        print(f"Star threshold: {min_ppg}+ PPG")
        print(f"Early exit threshold: <{max_minutes} minutes")
        print(f"{'='*80}\n")

        opportunities = []

        # Get all games
        games = self.get_season_games(season)

        print(f"\nAnalyzing {len(games)} games...\n")

        for idx, game in enumerate(games, 1):
            if idx % 50 == 0:
                print(f"  Processed {idx}/{len(games)} games...")

            game_id = game['id']
            game_date = game['date']
            home_team = game['home_team']['full_name']
            away_team = game['visitor_team']['full_name']

            # Get player stats for this game
            game_stats = self.get_game_stats(game_id)

            if not game_stats:
                continue

            # Check each team for star player early exit
            for team_id in [game['home_team']['id'], game['visitor_team']['id']]:
                team_stats = [s for s in game_stats if s['player']['team_id'] == team_id]

                if not team_stats:
                    continue

                # Find team's leading scorer (season averages)
                leading_scorers = self.get_team_roster(team_id, season)

                if not leading_scorers:
                    continue

                # Check if leading scorer played <30 minutes (injured/ejected)
                star = leading_scorers[0]
                star_ppg = star.get('pts', 0)

                if star_ppg < min_ppg:
                    continue  # Not a star player

                # Find star's game stats
                star_game_stats = [
                    s for s in team_stats
                    if s['player']['id'] == star['player']['id']
                ]

                if not star_game_stats:
                    continue

                star_minutes = star_game_stats[0].get('min', '0')

                # Parse minutes (format: "MM:SS" or "MM")
                try:
                    if ':' in str(star_minutes):
                        minutes_played = int(star_minutes.split(':')[0])
                    else:
                        minutes_played = int(star_minutes) if star_minutes else 0
                except:
                    minutes_played = 0

                if minutes_played >= max_minutes:
                    continue  # Star played full game

                # OPPORTUNITY FOUND - Star exited early!
                print(f"\n[OPPORTUNITY] {star['player']['first_name']} {star['player']['last_name']} "
                      f"({star_ppg:.1f} PPG) played only {minutes_played} min")
                print(f"  Game: {away_team} @ {home_team} on {game_date}")

                # Identify substitute players (non-starters who played 20+ min)
                substitutes = [
                    s for s in team_stats
                    if s['player']['id'] != star['player']['id']
                    and s.get('min', '0:00') != '0:00'
                ]

                for sub_stats in substitutes:
                    try:
                        sub_min = sub_stats.get('min', '0')
                        if ':' in str(sub_min):
                            sub_minutes = int(sub_min.split(':')[0])
                        else:
                            sub_minutes = int(sub_min) if sub_min else 0
                    except:
                        sub_minutes = 0

                    if sub_minutes < 15:  # Only track subs who played meaningful minutes
                        continue

                    # Get substitute's season averages
                    sub_player_id = sub_stats['player']['id']
                    sub_season_avg = self.get_player_season_stats(season, sub_player_id)

                    if not sub_season_avg:
                        continue

                    # Calculate performance vs average
                    game_pts = sub_stats.get('pts', 0)
                    game_reb = sub_stats.get('reb', 0)
                    game_ast = sub_stats.get('ast', 0)

                    avg_pts = sub_season_avg.get('pts', 0)
                    avg_reb = sub_season_avg.get('reb', 0)
                    avg_ast = sub_season_avg.get('ast', 0)

                    # Record opportunity
                    opportunity = {
                        'game_id': game_id,
                        'game_date': game_date,
                        'season': season,
                        'home_team': home_team,
                        'away_team': away_team,
                        'affected_team_id': team_id,
                        'star_player_name': f"{star['player']['first_name']} {star['player']['last_name']}",
                        'star_ppg': star_ppg,
                        'star_minutes_played': minutes_played,
                        'sub_player_id': sub_player_id,
                        'sub_player_name': f"{sub_stats['player']['first_name']} {sub_stats['player']['last_name']}",
                        'sub_minutes_played': sub_minutes,
                        'sub_pts_game': game_pts,
                        'sub_pts_avg': avg_pts,
                        'sub_pts_over': game_pts > avg_pts,
                        'sub_reb_game': game_reb,
                        'sub_reb_avg': avg_reb,
                        'sub_reb_over': game_reb > avg_reb,
                        'sub_ast_game': game_ast,
                        'sub_ast_avg': avg_ast,
                        'sub_ast_over': game_ast > avg_ast,
                    }

                    opportunities.append(opportunity)

                    print(f"  Substitute: {opportunity['sub_player_name']} ({sub_minutes} min)")
                    print(f"    PTS: {game_pts} vs {avg_pts:.1f} avg ({'OVER' if game_pts > avg_pts else 'UNDER'})")
                    print(f"    REB: {game_reb} vs {avg_reb:.1f} avg ({'OVER' if game_reb > avg_reb else 'UNDER'})")
                    print(f"    AST: {game_ast} vs {avg_ast:.1f} avg ({'OVER' if game_ast > avg_ast else 'UNDER'})")

        print(f"\n{'='*80}")
        print(f"FOUND {len(opportunities)} INJURY CASCADE OPPORTUNITIES")
        print(f"{'='*80}\n")

        return opportunities

    def calculate_results(self, opportunities: List[Dict]) -> Dict:
        """
        Calculate backtest results

        Args:
            opportunities: List of opportunity dicts

        Returns:
            Backtest results dict
        """
        if not opportunities:
            return {
                'total_opportunities': 0,
                'bets_placed': 0,
                'pts_over': {
                    'wins': 0,
                    'losses': 0,
                    'win_rate': 0.0,
                    'roi': 0.0
                },
                'reb_over': {
                    'wins': 0,
                    'losses': 0,
                    'win_rate': 0.0,
                    'roi': 0.0
                },
                'ast_over': {
                    'wins': 0,
                    'losses': 0,
                    'win_rate': 0.0,
                    'roi': 0.0
                },
                'best_prop_type': 'N/A',
                'best_win_rate': 0.0,
                'best_roi': 0.0
            }

        # Count prop type wins
        pts_over_wins = sum(1 for o in opportunities if o['sub_pts_over'])
        pts_over_losses = sum(1 for o in opportunities if not o['sub_pts_over'])

        reb_over_wins = sum(1 for o in opportunities if o['sub_reb_over'])
        reb_over_losses = sum(1 for o in opportunities if not o['sub_reb_over'])

        ast_over_wins = sum(1 for o in opportunities if o['sub_ast_over'])
        ast_over_losses = sum(1 for o in opportunities if not o['sub_ast_over'])

        # Calculate win rates
        pts_win_rate = (pts_over_wins / len(opportunities) * 100) if opportunities else 0
        reb_win_rate = (reb_over_wins / len(opportunities) * 100) if opportunities else 0
        ast_win_rate = (ast_over_wins / len(opportunities) * 100) if opportunities else 0

        # Calculate ROI at -110 odds
        profit_per_win = 90.91
        loss_per_bet = 100

        pts_profit = (pts_over_wins * profit_per_win) - (pts_over_losses * loss_per_bet)
        pts_roi = (pts_profit / (len(opportunities) * 100) * 100) if opportunities else 0

        reb_profit = (reb_over_wins * profit_per_win) - (reb_over_losses * loss_per_bet)
        reb_roi = (reb_profit / (len(opportunities) * 100) * 100) if opportunities else 0

        ast_profit = (ast_over_wins * profit_per_win) - (ast_over_losses * loss_per_bet)
        ast_roi = (ast_profit / (len(opportunities) * 100) * 100) if opportunities else 0

        # Find best prop type
        best_prop = max(
            [('PTS', pts_win_rate, pts_roi), ('REB', reb_win_rate, reb_roi), ('AST', ast_win_rate, ast_roi)],
            key=lambda x: x[1]
        )

        results = {
            'total_opportunities': len(opportunities),
            'bets_placed': len(opportunities),
            'pts_over': {
                'wins': pts_over_wins,
                'losses': pts_over_losses,
                'win_rate': round(pts_win_rate, 1),
                'roi': round(pts_roi, 1)
            },
            'reb_over': {
                'wins': reb_over_wins,
                'losses': reb_over_losses,
                'win_rate': round(reb_win_rate, 1),
                'roi': round(reb_roi, 1)
            },
            'ast_over': {
                'wins': ast_over_wins,
                'losses': ast_over_losses,
                'win_rate': round(ast_win_rate, 1),
                'roi': round(ast_roi, 1)
            },
            'best_prop_type': best_prop[0],
            'best_win_rate': round(best_prop[1], 1),
            'best_roi': round(best_prop[2], 1)
        }

        return results

    def save_opportunities(self, opportunities: List[Dict], filename: str):
        """Save opportunities to CSV"""
        if not opportunities:
            print("[WARNING] No opportunities to save")
            return

        df = pd.DataFrame(opportunities)
        df.to_csv(filename, index=False)
        print(f"[SAVED] Opportunities saved to: {filename}")

    def print_results(self, results: Dict):
        """Print results summary"""
        print(f"\n{'='*80}")
        print(f"INJURY CASCADE PROPS - BACKTEST RESULTS")
        print(f"{'='*80}\n")

        print(f"Total Opportunities: {results['total_opportunities']}")
        print(f"Bets Placed: {results['bets_placed']}\n")

        print("POINTS OVER PROP:")
        print(f"  Wins: {results['pts_over']['wins']}")
        print(f"  Losses: {results['pts_over']['losses']}")
        print(f"  Win Rate: {results['pts_over']['win_rate']}%")
        print(f"  ROI: {results['pts_over']['roi']:+.1f}%\n")

        print("REBOUNDS OVER PROP:")
        print(f"  Wins: {results['reb_over']['wins']}")
        print(f"  Losses: {results['reb_over']['losses']}")
        print(f"  Win Rate: {results['reb_over']['win_rate']}%")
        print(f"  ROI: {results['reb_over']['roi']:+.1f}%\n")

        print("ASSISTS OVER PROP:")
        print(f"  Wins: {results['ast_over']['wins']}")
        print(f"  Losses: {results['ast_over']['losses']}")
        print(f"  Win Rate: {results['ast_over']['win_rate']}%")
        print(f"  ROI: {results['ast_over']['roi']:+.1f}%\n")

        print(f"BEST PROP TYPE: {results['best_prop_type']}")
        print(f"  Win Rate: {results['best_win_rate']}%")
        print(f"  ROI: {results['best_roi']:+.1f}%")

        print(f"\n{'='*80}\n")


def main():
    """Run injury cascade backtest"""
    # Load environment variables - try multiple paths
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if not os.path.exists(env_path):
        # Try from current working directory
        env_path = os.path.join(os.getcwd(), 'backend', '.env')
        if not os.path.exists(env_path):
            env_path = os.path.join(os.getcwd(), '.env')

    load_dotenv(env_path)

    # Get API key
    api_key = os.getenv('BALLDONTLIE_API_KEY')
    if not api_key:
        print("[WARNING] BALLDONTLIE_API_KEY not found in environment variables")
        print(f"Tried loading from: {env_path}")
        print("The scraper may not work without an API key")
    else:
        print(f"[SUCCESS] API key loaded from environment")

    scraper = InjuryCascadeScraper(api_key=api_key)

    # Run for 2023-24 season
    season = 2023

    # Identify opportunities
    opportunities = scraper.identify_star_exits(
        season=season,
        min_ppg=15.0,  # Star = 15+ PPG
        max_minutes=30  # Early exit = <30 minutes
    )

    # Calculate results
    results = scraper.calculate_results(opportunities)

    # Print results
    scraper.print_results(results)

    # Save data
    scraper.save_opportunities(
        opportunities,
        f'injury_cascade_opportunities_{season}_{season+1}.csv'
    )

    # Save results summary
    with open(f'injury_cascade_results_{season}_{season+1}.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"[COMPLETE] Backtest finished for {season}-{season+1} season")


if __name__ == "__main__":
    main()
