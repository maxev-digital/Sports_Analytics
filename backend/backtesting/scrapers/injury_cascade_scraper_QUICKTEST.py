"""
Injury Cascade Props Strategy - QUICK TEST VERSION
Tests scraper with limited data (November 2023 only - ~100 games)
Should complete in ~10 minutes

Once verified, use injury_cascade_scraper.py for full season backtest
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os
from dotenv import load_dotenv


class InjuryCascadeScraperQuickTest:
    """Quick test version - only fetches November 2023 games"""

    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://api.balldontlie.io/v1"
        self.api_key = api_key
        self.session = requests.Session()
        self.requests_per_minute = 30
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
            headers['Authorization'] = self.api_key

        try:
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429 and retry_count < 3:
                wait_time = (retry_count + 1) * 30
                print(f"[RATE LIMIT] Waiting {wait_time}s before retry {retry_count + 1}/3...")
                time.sleep(wait_time)
                return self._make_request(endpoint, params, retry_count + 1)
            else:
                print(f"[ERROR] API request failed: {e}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] API request failed: {e}")
            return None

    def get_november_games(self) -> List[Dict]:
        """Get only November 2023 games for quick testing"""
        print(f"Fetching November-December 2023 games (2 MONTH TEST)...")

        games = []
        cursor = None
        page_num = 1

        # November 1 - December 31, 2023
        params = {
            'seasons[]': [2023],
            'start_date': '2023-11-01',
            'end_date': '2023-12-31',
            'per_page': 100
        }

        while True:
            if cursor:
                params['cursor'] = cursor

            data = self._make_request('games', params)

            if not data or 'data' not in data:
                break

            games.extend(data['data'])

            if 'meta' in data and 'next_cursor' in data['meta'] and data['meta']['next_cursor']:
                cursor = data['meta']['next_cursor']
                page_num += 1
                print(f"  Fetched page {page_num}...")
            else:
                break

        print(f"  Total games: {len(games)}")
        return games

    def get_player_season_stats(self, season: int, player_id: int) -> Optional[Dict]:
        """Get player's season averages"""
        params = {
            'season': season,
            'player_id': player_id
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

    def get_team_top_scorer_from_game(self, team_stats: List[Dict], season: int) -> Optional[Dict]:
        """
        Find team's likely star player from this game's participants
        Fetches season averages for each player and returns the top scorer
        """
        player_averages = []

        for player_stat in team_stats:
            player_id = player_stat['player']['id']
            season_avg = self.get_player_season_stats(season, player_id)

            if season_avg and season_avg.get('pts', 0) > 0:
                # Add game stat reference
                season_avg['game_stat'] = player_stat
                player_averages.append(season_avg)

        if not player_averages:
            return None

        # Sort by season PPG descending
        player_averages.sort(key=lambda x: x.get('pts', 0), reverse=True)

        return player_averages[0]

    def identify_star_exits(self, games: List[Dict], min_ppg: float = 15.0,
                           max_minutes: int = 30) -> List[Dict]:
        """Identify games where star player exited early"""
        print(f"\n{'='*80}")
        print(f"IDENTIFYING INJURY CASCADE OPPORTUNITIES (2 MONTH TEST)")
        print(f"Test Period: November-December 2023")
        print(f"Star threshold: {min_ppg}+ PPG")
        print(f"Early exit threshold: <{max_minutes} minutes")
        print(f"{'='*80}\n")

        opportunities = []
        season = 2023

        print(f"\nAnalyzing {len(games)} games...\n")

        for idx, game in enumerate(games, 1):
            if idx % 10 == 0:
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

                # Find team's top scorer from this game's roster
                star = self.get_team_top_scorer_from_game(team_stats, season)

                if not star:
                    continue

                star_ppg = star.get('pts', 0)

                if star_ppg < min_ppg:
                    continue

                # Get star's game stats (stored in star dict)
                star_game_stat = star.get('game_stat')

                if not star_game_stat:
                    continue

                star_minutes = star_game_stat.get('min', '0')

                # Parse minutes
                try:
                    if ':' in str(star_minutes):
                        minutes_played = int(star_minutes.split(':')[0])
                    else:
                        minutes_played = int(star_minutes) if star_minutes else 0
                except:
                    minutes_played = 0

                if minutes_played >= max_minutes:
                    continue

                # OPPORTUNITY FOUND!
                star_player_info = star_game_stat['player']
                print(f"\n[OPPORTUNITY] {star_player_info['first_name']} {star_player_info['last_name']} "
                      f"({star_ppg:.1f} PPG) played only {minutes_played} min")
                print(f"  Game: {away_team} @ {home_team} on {game_date}")

                # Identify substitutes
                substitutes = [
                    s for s in team_stats
                    if s['player']['id'] != star_player_info['id']
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

                    if sub_minutes < 15:
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
                        'star_player_name': f"{star_player_info['first_name']} {star_player_info['last_name']}",
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
        """Calculate backtest results"""
        if not opportunities:
            return {
                'total_opportunities': 0,
                'bets_placed': 0,
                'pts_over': {'wins': 0, 'losses': 0, 'win_rate': 0.0, 'roi': 0.0},
                'reb_over': {'wins': 0, 'losses': 0, 'win_rate': 0.0, 'roi': 0.0},
                'ast_over': {'wins': 0, 'losses': 0, 'win_rate': 0.0, 'roi': 0.0},
                'best_prop_type': 'N/A',
                'best_win_rate': 0.0,
                'best_roi': 0.0
            }

        # Count wins
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

    def print_results(self, results: Dict):
        """Print results summary"""
        print(f"\n{'='*80}")
        print(f"INJURY CASCADE PROPS - QUICK TEST RESULTS")
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
    """Run quick test"""
    load_dotenv('../../.env')

    api_key = os.getenv('BALLDONTLIE_API_KEY')
    if not api_key:
        print("[ERROR] BALLDONTLIE_API_KEY not found in environment")
        return

    print(f"[SUCCESS] API key loaded\n")

    scraper = InjuryCascadeScraperQuickTest(api_key=api_key)

    # Get November 2023 games only
    games = scraper.get_november_games()

    # Identify opportunities
    opportunities = scraper.identify_star_exits(
        games=games,
        min_ppg=15.0,
        max_minutes=30
    )

    # Calculate results
    results = scraper.calculate_results(opportunities)

    # Print results
    scraper.print_results(results)

    # Save data
    if opportunities:
        df = pd.DataFrame(opportunities)
        df.to_csv('injury_cascade_QUICKTEST.csv', index=False)
        print(f"[SAVED] Data saved to: injury_cascade_QUICKTEST.csv")

    with open('injury_cascade_QUICKTEST_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"[SAVED] Results saved to: injury_cascade_QUICKTEST_results.json")

    print(f"\n[COMPLETE] Quick test finished!")
    print(f"[NEXT STEP] If results look good, run full season backtest with injury_cascade_scraper.py")


if __name__ == "__main__":
    main()
