"""
GRADING ENGINE - PHASE 4
Fetches actual game results and grades predictions and combos
"""
import sqlite3
import logging
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

# NBA API imports
try:
    from nba_api.stats.endpoints import playergamelog, leaguegamefinder
    from nba_api.stats.static import players, teams
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False
    logging.warning("nba_api not installed - grading will be limited")

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "ml" / "predictions.db"


class GradingEngine:
    """Grades predictions and combos against actual game results"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.nba_api_available = NBA_API_AVAILABLE

        if not self.nba_api_available:
            logger.warning("NBA API not available - install with: pip install nba_api")

    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # ============================================================================
    # FETCH GAME RESULTS
    # ============================================================================

    def fetch_player_game_stats(self, player_name: str, game_date: str, season: str = "2024-25") -> Optional[Dict]:
        """
        Fetch player stats for a specific game using NBA API

        Args:
            player_name: Player name (e.g., "LeBron James")
            game_date: Game date (YYYY-MM-DD)
            season: NBA season (e.g., "2024-25")

        Returns:
            Dict with player stats or None if not found
        """
        if not self.nba_api_available:
            logger.error("NBA API not available")
            return None

        try:
            # Find player ID
            all_players = players.get_players()
            player = next((p for p in all_players if p['full_name'].lower() == player_name.lower()), None)

            if not player:
                logger.warning(f"Player not found: {player_name}")
                return None

            player_id = player['id']

            # Fetch game log
            import time
            time.sleep(0.6)  # Rate limiting

            game_log = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=season,
                season_type_all_star='Regular Season'
            )

            games_df = game_log.get_data_frames()[0]

            # Convert game_date to match format (e.g., "DEC 02, 2024")
            target_date = datetime.strptime(game_date, "%Y-%m-%d")
            target_date_str = target_date.strftime("%b %d, %Y").upper()

            # Find the game on this date
            game = games_df[games_df['GAME_DATE'] == target_date_str]

            if game.empty:
                logger.warning(f"No game found for {player_name} on {game_date}")
                return None

            game_row = game.iloc[0]

            # Extract relevant stats
            stats = {
                'player_name': player_name,
                'game_date': game_date,
                'game_id': game_row['Game_ID'],
                'team': game_row['MATCHUP'].split()[0],
                'opponent': game_row['MATCHUP'].split()[-1],
                'points': float(game_row['PTS']),
                'rebounds': float(game_row['REB']),
                'assists': float(game_row['AST']),
                'steals': float(game_row['STL']),
                'blocks': float(game_row['BLK']),
                'turnovers': float(game_row['TOV']),
                'fg_made': float(game_row['FGM']),
                'fg_attempted': float(game_row['FGA']),
                'fg3_made': float(game_row['FG3M']),
                'fg3_attempted': float(game_row['FG3A']),
                'ft_made': float(game_row['FTM']),
                'ft_attempted': float(game_row['FTA']),
                'minutes': float(game_row['MIN']),
                'plus_minus': float(game_row['PLUS_MINUS']) if game_row['PLUS_MINUS'] else 0
            }

            logger.info(f"✅ Fetched stats for {player_name} on {game_date}: {stats['points']}p {stats['rebounds']}r {stats['assists']}a")
            return stats

        except Exception as e:
            logger.error(f"Error fetching stats for {player_name} on {game_date}: {e}")
            return None

    def store_game_results(self, stats: Dict, sport: str = "nba"):
        """Store game results in props_results table"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Map prop types to actual values
            prop_mappings = {
                'points': stats['points'],
                'rebounds': stats['rebounds'],
                'assists': stats['assists'],
                'steals': stats['steals'],
                'blocks': stats['blocks'],
                'turnovers': stats['turnovers'],
                'threes': stats['fg3_made'],
                'pts_rebs_asts': stats['points'] + stats['rebounds'] + stats['assists'],
                'pts_rebs': stats['points'] + stats['rebounds'],
                'pts_asts': stats['points'] + stats['assists'],
                'rebs_asts': stats['rebounds'] + stats['assists'],
            }

            # Insert each prop type
            for prop_type, actual_value in prop_mappings.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO props_results
                    (game_date, game_id, player_name, team, opponent, sport, prop_type, actual_value)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stats['game_date'],
                    stats['game_id'],
                    stats['player_name'],
                    stats['team'],
                    stats['opponent'],
                    sport,
                    prop_type,
                    actual_value
                ))

            conn.commit()
            logger.info(f"✅ Stored results for {stats['player_name']} on {stats['game_date']}")

        except Exception as e:
            logger.error(f"Error storing results: {e}")
            conn.rollback()
        finally:
            conn.close()

    # ============================================================================
    # GRADE PREDICTIONS
    # ============================================================================

    def grade_predictions_for_date(self, game_date: str, sport: str = "nba") -> Dict:
        """
        Grade all predictions for a specific date

        Args:
            game_date: Date to grade (YYYY-MM-DD)
            sport: Sport (nba, nfl, nhl)

        Returns:
            Dict with grading results
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Get all predictions for this date
            cursor.execute("""
                SELECT id, player_name, team, opponent, prop_type, market_line,
                       predicted_value, recommendation, confidence, edge_pct,
                       prediction_date
                FROM player_props_predictions
                WHERE prediction_date = ? AND sport = ?
            """, (game_date, sport))

            predictions = cursor.fetchall()
            logger.info(f"Found {len(predictions)} predictions to grade for {game_date}")

            results = {
                'total_predictions': len(predictions),
                'graded': 0,
                'correct': 0,
                'incorrect': 0,
                'no_result': 0,
                'predictions': []
            }

            # Check if we have actual results for this date
            cursor.execute("""
                SELECT DISTINCT player_name, prop_type, actual_value
                FROM props_results
                WHERE game_date = ? AND sport = ?
            """, (game_date, sport))

            actual_results = {}
            for row in cursor.fetchall():
                key = (row['player_name'], row['prop_type'])
                actual_results[key] = row['actual_value']

            if not actual_results:
                logger.warning(f"No actual results found for {game_date}. Fetch game data first.")
                return results

            # Grade each prediction
            for pred in predictions:
                key = (pred['player_name'], pred['prop_type'])

                if key not in actual_results:
                    results['no_result'] += 1
                    continue

                actual_value = actual_results[key]
                market_line = pred['market_line']
                recommendation = pred['recommendation']

                # Determine if prediction was correct
                is_correct = False
                if recommendation == 'OVER' and actual_value > market_line:
                    is_correct = True
                elif recommendation == 'UNDER' and actual_value < market_line:
                    is_correct = True
                elif recommendation == 'NO_PLAY':
                    continue  # Don't grade NO_PLAY

                if is_correct:
                    results['correct'] += 1
                else:
                    results['incorrect'] += 1

                results['graded'] += 1

                results['predictions'].append({
                    'player_name': pred['player_name'],
                    'prop_type': pred['prop_type'],
                    'market_line': market_line,
                    'predicted_value': pred['predicted_value'],
                    'actual_value': actual_value,
                    'recommendation': recommendation,
                    'result': 'WIN' if is_correct else 'LOSS',
                    'confidence': pred['confidence'],
                    'edge_pct': pred['edge_pct']
                })

            # Calculate win rate
            if results['graded'] > 0:
                win_rate = (results['correct'] / results['graded']) * 100
                logger.info(f"✅ Graded {results['graded']} predictions: {results['correct']} correct ({win_rate:.1f}% win rate)")

            return results

        except Exception as e:
            logger.error(f"Error grading predictions: {e}", exc_info=True)
            return {'error': str(e)}
        finally:
            conn.close()

    # ============================================================================
    # GRADE COMBOS
    # ============================================================================

    def grade_combos_for_date(self, game_date: str, sport: str = "nba") -> Dict:
        """
        Grade all combos for a specific date

        Args:
            game_date: Date to grade (YYYY-MM-DD)
            sport: Sport (nba, nfl, nhl)

        Returns:
            Dict with combo grading results
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Format date for combo_id (YYYYMMDD)
            date_str = game_date.replace("-", "")

            # Get all combos for this date
            cursor.execute("""
                SELECT combo_id, sport, players, props, lines, directions,
                       expected_value_percent, demon_goblin_score
                FROM correlated_combos
                WHERE combo_id LIKE ? AND sport = ?
            """, (f"%_{date_str}_%", sport))

            combos = cursor.fetchall()
            logger.info(f"Found {len(combos)} combos to grade for {game_date}")

            results = {
                'total_combos': len(combos),
                'graded': 0,
                'won': 0,
                'lost': 0,
                'no_result': 0,
                'combos': []
            }

            # Get actual results
            cursor.execute("""
                SELECT player_name, prop_type, actual_value
                FROM props_results
                WHERE game_date = ? AND sport = ?
            """, (game_date, sport))

            actual_results = {}
            for row in cursor.fetchall():
                key = (row['player_name'], row['prop_type'])
                actual_results[key] = row['actual_value']

            if not actual_results:
                logger.warning(f"No actual results found for {game_date}")
                return results

            # Grade each combo
            for combo in combos:
                players = json.loads(combo['players'])
                prop_types = json.loads(combo['props'])
                lines = json.loads(combo['lines'])
                directions = json.loads(combo['directions'])

                # Check if all legs hit
                all_legs_graded = True
                all_legs_hit = True
                leg_results = []

                for i in range(len(players)):
                    player_name = players[i]
                    prop_type = prop_types[i]
                    line = lines[i]
                    direction = directions[i]

                    key = (player_name, prop_type)

                    if key not in actual_results:
                        all_legs_graded = False
                        break

                    actual_value = actual_results[key]

                    # Check if this leg hit
                    leg_hit = False
                    if direction == 'OVER' and actual_value > line:
                        leg_hit = True
                    elif direction == 'UNDER' and actual_value < line:
                        leg_hit = True

                    leg_results.append({
                        'player': player_name,
                        'prop': prop_type,
                        'line': line,
                        'direction': direction,
                        'actual': actual_value,
                        'hit': leg_hit
                    })

                    if not leg_hit:
                        all_legs_hit = False

                if not all_legs_graded:
                    results['no_result'] += 1
                    continue

                # Combo result
                combo_won = all_legs_hit

                if combo_won:
                    results['won'] += 1
                else:
                    results['lost'] += 1

                results['graded'] += 1

                results['combos'].append({
                    'combo_id': combo['combo_id'],
                    'num_legs': len(players),
                    'result': 'WIN' if combo_won else 'LOSS',
                    'legs': leg_results,
                    'expected_value': combo['expected_value_percent'],
                    'demon_score': combo['demon_goblin_score']
                })

            # Calculate win rate
            if results['graded'] > 0:
                win_rate = (results['won'] / results['graded']) * 100
                logger.info(f"✅ Graded {results['graded']} combos: {results['won']} won ({win_rate:.1f}% win rate)")

            return results

        except Exception as e:
            logger.error(f"Error grading combos: {e}", exc_info=True)
            return {'error': str(e)}
        finally:
            conn.close()

    # ============================================================================
    # MAIN GRADING WORKFLOW
    # ============================================================================

    def grade_date(self, game_date: str, sport: str = "nba", fetch_results: bool = True) -> Dict:
        """
        Complete grading workflow for a date:
        1. Fetch game results (if requested)
        2. Grade predictions
        3. Grade combos

        Args:
            game_date: Date to grade (YYYY-MM-DD)
            sport: Sport (nba, nfl, nhl)
            fetch_results: Whether to fetch game results first

        Returns:
            Dict with complete grading results
        """
        logger.info(f"🎯 Starting grading for {game_date} ({sport})")

        # Step 1: Fetch game results if needed
        if fetch_results and self.nba_api_available:
            logger.info("📥 Fetching game results...")
            self.fetch_all_game_results_for_date(game_date, sport)

        # Step 2: Grade predictions
        logger.info("📊 Grading predictions...")
        pred_results = self.grade_predictions_for_date(game_date, sport)

        # Step 3: Grade combos
        logger.info("🔥 Grading combos...")
        combo_results = self.grade_combos_for_date(game_date, sport)

        return {
            'date': game_date,
            'sport': sport,
            'predictions': pred_results,
            'combos': combo_results
        }

    def fetch_all_game_results_for_date(self, game_date: str, sport: str = "nba"):
        """Fetch game results for all players who had predictions on this date"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Get unique players who had predictions
            cursor.execute("""
                SELECT DISTINCT player_name
                FROM player_props_predictions
                WHERE prediction_date = ? AND sport = ?
            """, (game_date, sport))

            players = [row['player_name'] for row in cursor.fetchall()]
            logger.info(f"Fetching results for {len(players)} players")

            for player_name in players:
                stats = self.fetch_player_game_stats(player_name, game_date)
                if stats:
                    self.store_game_results(stats, sport)

        except Exception as e:
            logger.error(f"Error fetching all game results: {e}")
        finally:
            conn.close()


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    grader = GradingEngine()

    if len(sys.argv) < 2:
        print("Usage: python grading_engine.py <date> [sport]")
        print("Example: python grading_engine.py 2025-12-01 nba")
        sys.exit(1)

    game_date = sys.argv[1]
    sport = sys.argv[2] if len(sys.argv) > 2 else "nba"

    print(f"\n{'='*70}")
    print(f"GRADING ENGINE - {game_date} ({sport.upper()})")
    print(f"{'='*70}\n")

    results = grader.grade_date(game_date, sport, fetch_results=True)

    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")
    print(f"\nPredictions:")
    print(f"  Total: {results['predictions']['total_predictions']}")
    print(f"  Graded: {results['predictions']['graded']}")
    print(f"  Correct: {results['predictions']['correct']}")
    print(f"  Incorrect: {results['predictions']['incorrect']}")
    if results['predictions']['graded'] > 0:
        wr = (results['predictions']['correct'] / results['predictions']['graded']) * 100
        print(f"  Win Rate: {wr:.1f}%")

    print(f"\nCombos:")
    print(f"  Total: {results['combos']['total_combos']}")
    print(f"  Graded: {results['combos']['graded']}")
    print(f"  Won: {results['combos']['won']}")
    print(f"  Lost: {results['combos']['lost']}")
    if results['combos']['graded'] > 0:
        wr = (results['combos']['won'] / results['combos']['graded']) * 100
        print(f"  Win Rate: {wr:.1f}%")
