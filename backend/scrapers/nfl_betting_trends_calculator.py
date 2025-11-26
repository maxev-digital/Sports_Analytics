"""
NFL Betting Trends Calculator
Calculates ATS and Over/Under trends from Odds API historical data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class NFLBettingTrendsCalculator:
    """Calculates betting trends from historical odds archive database"""

    def __init__(self, db_path: str = None):
        # Use existing odds archive database
        if db_path is None:
            db_path = 'backend/data/odds_archive/odds_history.db'

        if not os.path.exists(db_path):
            logger.warning(f"Odds archive database not found at {db_path}")
            self.db_path = None
        else:
            self.db_path = db_path
            logger.info(f"Using odds archive database: {db_path}")

        self.sport = 'americanfootball_nfl'

    def calculate_team_trends(self, lookback_days: int = 365) -> Dict[str, Dict]:
        """
        Calculate ATS and O/U trends for all NFL teams

        Args:
            lookback_days: How many days back to analyze

        Returns:
            Dict mapping team name -> trends data:
            {
                'Kansas City Chiefs': {
                    'ats_record': {'wins': 8, 'losses': 5, 'pushes': 0},
                    'ats_win_pct': 0.615,
                    'ats_home': {'wins': 5, 'losses': 2, 'pushes': 0},
                    'ats_away': {'wins': 3, 'losses': 3, 'pushes': 0},
                    'ats_last_5': [1, 1, 0, 1, 0],  # 1=win, 0=loss, -1=push
                    'ats_last_10': [1, 1, 0, 1, 0, 1, 1, 0, 0, 1],
                    'ou_record': {'overs': 7, 'unders': 6, 'pushes': 0},
                    'ou_win_pct': 0.538,  # % of overs
                    'ou_home': {'overs': 4, 'unders': 3, 'pushes': 0},
                    'ou_away': {'overs': 3, 'unders': 3, 'pushes': 0},
                    'ou_last_5': [1, 0, 1, 1, 0],  # 1=over, 0=under, -1=push
                    'ou_last_10': [1, 0, 1, 1, 0, 0, 1, 1, 0, 1],
                    'games_analyzed': 13,
                    'last_updated': '2024-11-20'
                }
            }
        """
        logger.info(f"Calculating NFL betting trends (last {lookback_days} days)...")

        # Fetch completed games with scores (timezone-aware for API comparison)
        from datetime import timezone
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        completed_games = self._fetch_completed_games(cutoff_date)

        if not completed_games:
            logger.warning("No completed games found!")
            return {}

        logger.info(f"Analyzing {len(completed_games)} completed games...")

        # Calculate trends for each team
        team_trends = self._calculate_trends_from_games(completed_games)

        logger.info(f"Calculated trends for {len(team_trends)} teams")
        return team_trends

    def _fetch_completed_games(self, cutoff_date: datetime) -> List[Dict]:
        """Fetch completed NFL games from odds archive database"""
        if not self.db_path:
            logger.error("No odds archive database available")
            return []

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Query: Join pregame odds with game results
            # Tables: game_odds_pregame (odds), game_results (final scores)
            query = """
            SELECT
                o.game_id,
                o.sport_key,
                o.home_team,
                o.away_team,
                o.commence_time,
                o.home_spread,
                o.total_over_under,
                r.home_score,
                r.away_score,
                r.completed
            FROM game_odds_pregame o
            LEFT JOIN game_results r ON o.game_id = r.game_id
            WHERE o.sport_key = ?
                AND r.completed = 1
                AND o.commence_time >= ?
                AND o.snapshot_type = 'closing'
            ORDER BY o.commence_time DESC
            """

            cursor.execute(query, (self.sport, cutoff_date.isoformat()))
            rows = cursor.fetchall()

            completed = []
            for row in rows:
                game_data = {
                    'id': row['game_id'],
                    'sport_key': row['sport_key'],
                    'home_team': row['home_team'],
                    'away_team': row['away_team'],
                    'commence_time': row['commence_time'],
                    'home_spread': row['home_spread'],
                    'total': row['total_over_under'],
                    'home_score': row['home_score'],
                    'away_score': row['away_score'],
                    'completed': True
                }
                completed.append(game_data)

            conn.close()
            logger.info(f"Found {len(completed)} completed games from odds archive")
            return completed

        except Exception as e:
            logger.error(f"Error querying odds archive: {e}", exc_info=True)
            return []

    def _calculate_trends_from_games(self, games: List[Dict]) -> Dict[str, Dict]:
        """Calculate ATS and O/U trends from completed games"""
        team_games = defaultdict(list)
        team_trends = {}

        # Group games by team
        for game in games:
            game_data = self._extract_game_data(game)
            if not game_data:
                continue

            home_team = game_data['home_team']
            away_team = game_data['away_team']

            # Add game from home team's perspective
            home_game = {
                'date': game_data['date'],
                'is_home': True,
                'team_score': game_data['home_score'],
                'opponent_score': game_data['away_score'],
                'spread': game_data['spread'],  # Home spread
                'total': game_data['total']
            }
            team_games[home_team].append(home_game)

            # Add game from away team's perspective
            away_game = {
                'date': game_data['date'],
                'is_home': False,
                'team_score': game_data['away_score'],
                'opponent_score': game_data['home_score'],
                'spread': -game_data['spread'],  # Flip spread for away team
                'total': game_data['total']
            }
            team_games[away_team].append(away_game)

        # Calculate trends for each team
        for team_name, games_list in team_games.items():
            # Sort by date (newest first)
            games_list.sort(key=lambda g: g['date'], reverse=True)

            trends = {
                'ats_record': {'wins': 0, 'losses': 0, 'pushes': 0},
                'ats_home': {'wins': 0, 'losses': 0, 'pushes': 0},
                'ats_away': {'wins': 0, 'losses': 0, 'pushes': 0},
                'ats_last_5': [],
                'ats_last_10': [],
                'ou_record': {'overs': 0, 'unders': 0, 'pushes': 0},
                'ou_home': {'overs': 0, 'unders': 0, 'pushes': 0},
                'ou_away': {'overs': 0, 'unders': 0, 'pushes': 0},
                'ou_last_5': [],
                'ou_last_10': [],
                'games_analyzed': len(games_list),
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            }

            # Process each game
            for idx, game_data in enumerate(games_list):
                # Calculate ATS result
                ats_result = self._calculate_ats(
                    game_data['team_score'],
                    game_data['opponent_score'],
                    game_data['spread'],
                    game_data['is_home']
                )

                # Calculate O/U result
                ou_result = self._calculate_ou(
                    game_data['team_score'],
                    game_data['opponent_score'],
                    game_data['total']
                )

                # Update overall records
                self._update_record(trends['ats_record'], ats_result)
                self._update_record(trends['ou_record'], ou_result, is_ou=True)

                # Update home/away splits
                split_key = 'ats_home' if game_data['is_home'] else 'ats_away'
                self._update_record(trends[split_key], ats_result)

                ou_split_key = 'ou_home' if game_data['is_home'] else 'ou_away'
                self._update_record(trends[ou_split_key], ou_result, is_ou=True)

                # Track last 5 and 10 games
                if idx < 5:
                    trends['ats_last_5'].append(ats_result)
                    trends['ou_last_5'].append(ou_result)
                if idx < 10:
                    trends['ats_last_10'].append(ats_result)
                    trends['ou_last_10'].append(ou_result)

            # Calculate win percentages
            ats_total = trends['ats_record']['wins'] + trends['ats_record']['losses']
            trends['ats_win_pct'] = trends['ats_record']['wins'] / ats_total if ats_total > 0 else 0

            ou_total = trends['ou_record']['overs'] + trends['ou_record']['unders']
            trends['ou_win_pct'] = trends['ou_record']['overs'] / ou_total if ou_total > 0 else 0

            team_trends[team_name] = trends

        return team_trends

    def _extract_game_data(self, game: Dict) -> Optional[Dict]:
        """Extract relevant data from a game (already formatted from database)"""
        try:
            # Data is already in the right format from database query
            home_score = game.get('home_score')
            away_score = game.get('away_score')
            spread = game.get('home_spread')
            total = game.get('total')

            # Validate required fields
            if home_score is None or away_score is None:
                return None
            if spread is None or total is None:
                return None

            return {
                'date': game.get('commence_time'),
                'home_team': game.get('home_team'),
                'away_team': game.get('away_team'),
                'home_score': home_score,
                'away_score': away_score,
                'spread': spread,
                'total': total
            }

        except Exception as e:
            logger.debug(f"Error extracting game data: {e}")
            return None

    def _calculate_ats(self, team_score: int, opponent_score: int,
                       spread: float, is_home: bool) -> int:
        """
        Calculate ATS result
        Returns: 1 (win), 0 (loss), -1 (push)
        """
        # Adjust spread based on perspective
        effective_spread = spread if is_home else -spread

        # Calculate cover margin
        actual_margin = team_score - opponent_score
        cover_margin = actual_margin + effective_spread

        if abs(cover_margin) < 0.5:  # Push
            return -1
        elif cover_margin > 0:  # Win
            return 1
        else:  # Loss
            return 0

    def _calculate_ou(self, team_score: int, opponent_score: int, total: float) -> int:
        """
        Calculate Over/Under result
        Returns: 1 (over), 0 (under), -1 (push)
        """
        actual_total = team_score + opponent_score

        if abs(actual_total - total) < 0.5:  # Push
            return -1
        elif actual_total > total:  # Over
            return 1
        else:  # Under
            return 0

    def _update_record(self, record: Dict, result: int, is_ou: bool = False):
        """Update win-loss-push record based on result"""
        if result == 1:
            key = 'overs' if is_ou else 'wins'
            record[key] += 1
        elif result == 0:
            key = 'unders' if is_ou else 'losses'
            record[key] += 1
        else:  # Push
            record['pushes'] += 1


if __name__ == '__main__':
    # Test the calculator
    logging.basicConfig(level=logging.INFO)

    calculator = NFLBettingTrendsCalculator()
    trends = calculator.calculate_team_trends(lookback_days=120)

    if trends:
        print(f"\n[OK] Calculated trends for {len(trends)} teams\n")

        # Show sample data
        sample_teams = list(trends.keys())[:3]
        for team in sample_teams:
            data = trends[team]
            print(f"{team}:")
            print(f"  ATS: {data['ats_record']['wins']}-{data['ats_record']['losses']}-{data['ats_record']['pushes']} ({data['ats_win_pct']:.1%})")
            print(f"  O/U: {data['ou_record']['overs']}-{data['ou_record']['unders']}-{data['ou_record']['pushes']} ({data['ou_win_pct']:.1%})")
            print(f"  Games analyzed: {data['games_analyzed']}")
            print()
    else:
        print("\n[NO] Failed to calculate trends")
