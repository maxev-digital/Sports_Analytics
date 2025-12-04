"""
PERFORMANCE TRACKER - PHASE 5
Calculates performance stats for props predictions and combos
100% pre-calculated backend - frontend is dumb reader
"""
import sqlite3
import logging
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "ml" / "predictions.db"


class PerformanceTracker:
    """Calculates and tracks performance metrics for props predictions"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH

    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # ============================================================================
    # MAIN PERFORMANCE CALCULATION
    # ============================================================================

    def calculate_performance(
        self,
        sport: Optional[str] = None,
        prop_type: Optional[str] = None,
        model: Optional[str] = None,
        days: int = 30,
        unit_size: float = 100.0,
        bankroll: float = 10000.0
    ) -> Dict:
        """
        Calculate comprehensive performance stats

        Returns EVERYTHING frontend needs in single call (bulletproof pattern)
        """
        conn = self.get_db_connection()

        try:
            # Calculate date range
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            # Build filters
            filters = {
                'sport': sport or 'all',
                'prop_type': prop_type or 'all',
                'model': model or 'all',
                'days': days
            }

            # Get graded predictions (those with actual results)
            graded_preds = self._get_graded_predictions(
                conn, start_date, end_date, sport, prop_type, model
            )

            if not graded_preds:
                return self._empty_response(filters)

            # Calculate overall summary
            summary = self._calculate_summary(graded_preds, unit_size, bankroll)

            # Calculate breakdowns
            by_confidence = self._calculate_by_confidence(graded_preds, unit_size)
            by_prop_type = self._calculate_by_prop_type(graded_preds, unit_size)
            by_sport = self._calculate_by_sport(graded_preds, unit_size)
            by_model = self._calculate_by_model(graded_preds, unit_size)

            # Calculate time series history
            history = self._calculate_history(graded_preds, unit_size, days)

            # Get recent predictions
            predictions = self._get_recent_predictions(
                conn, start_date, end_date, sport, prop_type, model, limit=50
            )

            return {
                'summary': summary,
                'by_confidence': by_confidence,
                'by_prop_type': by_prop_type,
                'by_sport': by_sport,
                'by_model': by_model,
                'history': history,
                'predictions': predictions,
                'predictions_total': len(graded_preds),
                'filters': filters,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error calculating performance: {e}", exc_info=True)
            return self._empty_response(filters, error=str(e))
        finally:
            conn.close()

    # ============================================================================
    # HELPER FUNCTIONS
    # ============================================================================

    def _get_graded_predictions(
        self, conn, start_date, end_date, sport=None, prop_type=None, model=None
    ) -> List[Dict]:
        """Get predictions that have been graded (have actual results)"""
        cursor = conn.cursor()

        # Build query
        where_clauses = [
            "pred.prediction_date >= ?",
            "pred.prediction_date <= ?",
            "res.actual_value IS NOT NULL",  # Must have result
            "pred.recommendation != 'NO_PLAY'"  # Don't include NO_PLAY
        ]
        params = [start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")]

        if sport:
            where_clauses.append("pred.sport = ?")
            params.append(sport)

        if prop_type:
            where_clauses.append("pred.prop_type = ?")
            params.append(prop_type)

        if model:
            where_clauses.append("pred.model = ?")
            params.append(model)

        where_sql = " AND ".join(where_clauses)

        query = f"""
            SELECT
                pred.id,
                pred.prediction_date,
                pred.player_name,
                pred.team,
                pred.opponent,
                pred.sport,
                pred.prop_type,
                pred.market_line,
                pred.predicted_value,
                pred.recommendation,
                pred.confidence,
                pred.edge_pct,
                pred.model_type as model,
                res.actual_value
            FROM player_props_predictions pred
            JOIN props_results res ON (
                pred.player_name = res.player_name AND
                pred.prop_type = res.prop_type AND
                pred.prediction_date = res.game_date
            )
            WHERE {where_sql}
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert to list of dicts and determine win/loss
        predictions = []
        for row in rows:
            result = self._determine_result(
                row['recommendation'],
                row['market_line'],
                row['actual_value']
            )

            predictions.append({
                'id': row['id'],
                'prediction_date': row['prediction_date'],
                'player_name': row['player_name'],
                'team': row['team'],
                'opponent': row['opponent'],
                'sport': row['sport'],
                'prop_type': row['prop_type'],
                'market_line': row['market_line'],
                'predicted_value': row['predicted_value'],
                'actual_value': row['actual_value'],
                'recommendation': row['recommendation'],
                'confidence': row['confidence'],
                'edge_pct': row['edge_pct'],
                'model': row['model'] or 'ensemble',
                'result': result,
                'profit_loss': 1.0 if result == 'WIN' else -1.1  # -110 odds
            })

        return predictions

    def _determine_result(self, recommendation: str, line: float, actual: float) -> str:
        """Determine if prediction was WIN, LOSS, or PUSH"""
        if actual == line:
            return 'PUSH'
        elif recommendation == 'OVER' and actual > line:
            return 'WIN'
        elif recommendation == 'UNDER' and actual < line:
            return 'WIN'
        else:
            return 'LOSS'

    def _calculate_summary(self, predictions: List[Dict], unit_size: float, bankroll: float) -> Dict:
        """Calculate overall summary statistics"""
        total = len(predictions)
        wins = sum(1 for p in predictions if p['result'] == 'WIN')
        losses = sum(1 for p in predictions if p['result'] == 'LOSS')
        pushes = sum(1 for p in predictions if p['result'] == 'PUSH')

        win_rate = wins / total if total > 0 else 0.0

        # Calculate units won/lost
        units_won = sum(p['profit_loss'] for p in predictions)

        # Calculate ROI (units won / total units risked)
        roi = (units_won / total) if total > 0 else 0.0

        # Calculate average edge
        avg_edge = sum(p['edge_pct'] for p in predictions) / total if total > 0 else 0.0

        return {
            'total_predictions': total,
            'wins': wins,
            'losses': losses,
            'pushes': pushes,
            'win_rate': win_rate,
            'roi': roi,
            'avg_edge': avg_edge,
            'units_won': units_won,
            'pnl_dollars': units_won * unit_size,
            'current_bankroll': bankroll + (units_won * unit_size)
        }

    def _calculate_by_confidence(self, predictions: List[Dict], unit_size: float) -> Dict:
        """Break down performance by confidence level"""
        by_conf = defaultdict(lambda: {'total': 0, 'wins': 0, 'units_won': 0.0})

        for pred in predictions:
            # Categorize confidence
            conf = pred['confidence'] if pred['confidence'] else 0.0
            if conf >= 0.7:
                conf_level = 'HIGH'
            elif conf >= 0.5:
                conf_level = 'MEDIUM'
            else:
                conf_level = 'LOW'

            by_conf[conf_level]['total'] += 1
            if pred['result'] == 'WIN':
                by_conf[conf_level]['wins'] += 1
            by_conf[conf_level]['units_won'] += pred['profit_loss']

        # Calculate rates
        result = {}
        for conf_level, stats in by_conf.items():
            result[conf_level] = {
                'total': stats['total'],
                'wins': stats['wins'],
                'win_rate': stats['wins'] / stats['total'] if stats['total'] > 0 else 0.0,
                'roi': stats['units_won'] / stats['total'] if stats['total'] > 0 else 0.0
            }

        return result

    def _calculate_by_prop_type(self, predictions: List[Dict], unit_size: float) -> Dict:
        """Break down performance by prop type"""
        by_prop = defaultdict(lambda: {'total': 0, 'wins': 0, 'units_won': 0.0})

        for pred in predictions:
            prop_type = pred['prop_type']
            by_prop[prop_type]['total'] += 1
            if pred['result'] == 'WIN':
                by_prop[prop_type]['wins'] += 1
            by_prop[prop_type]['units_won'] += pred['profit_loss']

        # Calculate rates
        result = {}
        for prop_type, stats in by_prop.items():
            result[prop_type] = {
                'total': stats['total'],
                'wins': stats['wins'],
                'win_rate': stats['wins'] / stats['total'] if stats['total'] > 0 else 0.0,
                'roi': stats['units_won'] / stats['total'] if stats['total'] > 0 else 0.0
            }

        return result

    def _calculate_by_sport(self, predictions: List[Dict], unit_size: float) -> Dict:
        """Break down performance by sport"""
        by_sport = defaultdict(lambda: {'total': 0, 'wins': 0, 'units_won': 0.0})

        for pred in predictions:
            sport = pred['sport']
            by_sport[sport]['total'] += 1
            if pred['result'] == 'WIN':
                by_sport[sport]['wins'] += 1
            by_sport[sport]['units_won'] += pred['profit_loss']

        # Calculate rates
        result = {}
        for sport, stats in by_sport.items():
            result[sport] = {
                'total': stats['total'],
                'wins': stats['wins'],
                'win_rate': stats['wins'] / stats['total'] if stats['total'] > 0 else 0.0,
                'roi': stats['units_won'] / stats['total'] if stats['total'] > 0 else 0.0
            }

        return result

    def _calculate_by_model(self, predictions: List[Dict], unit_size: float) -> Dict:
        """Break down performance by model"""
        by_model = defaultdict(lambda: {'total': 0, 'wins': 0, 'units_won': 0.0})

        for pred in predictions:
            model = pred['model']
            by_model[model]['total'] += 1
            if pred['result'] == 'WIN':
                by_model[model]['wins'] += 1
            by_model[model]['units_won'] += pred['profit_loss']

        # Calculate rates
        result = {}
        for model, stats in by_model.items():
            result[model] = {
                'total': stats['total'],
                'wins': stats['wins'],
                'win_rate': stats['wins'] / stats['total'] if stats['total'] > 0 else 0.0,
                'roi': stats['units_won'] / stats['total'] if stats['total'] > 0 else 0.0
            }

        return result

    def _calculate_history(self, predictions: List[Dict], unit_size: float, days: int) -> List[Dict]:
        """Calculate daily time series for charts"""
        # Group by date
        by_date = defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0, 'units_won': 0.0})

        for pred in predictions:
            date_str = pred['prediction_date']
            by_date[date_str]['total'] += 1
            if pred['result'] == 'WIN':
                by_date[date_str]['wins'] += 1
            elif pred['result'] == 'LOSS':
                by_date[date_str]['losses'] += 1
            by_date[date_str]['units_won'] += pred['profit_loss']

        # Convert to list and sort
        history = []
        for date_str in sorted(by_date.keys()):
            stats = by_date[date_str]
            history.append({
                'period': date_str,
                'predictions': stats['total'],
                'wins': stats['wins'],
                'losses': stats['losses'],
                'win_rate': stats['wins'] / stats['total'] if stats['total'] > 0 else 0.0,
                'daily_win_rate': stats['wins'] / stats['total'] if stats['total'] > 0 else 0.0,
                'roi': stats['units_won'] / stats['total'] if stats['total'] > 0 else 0.0,
                'units_won': stats['units_won']
            })

        return history

    def _get_recent_predictions(
        self, conn, start_date, end_date, sport=None, prop_type=None, model=None, limit=50
    ) -> List[Dict]:
        """Get recent predictions for table display"""
        cursor = conn.cursor()

        # Build query (same as graded predictions)
        where_clauses = [
            "pred.prediction_date >= ?",
            "pred.prediction_date <= ?",
            "res.actual_value IS NOT NULL",
            "pred.recommendation != 'NO_PLAY'"
        ]
        params = [start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")]

        if sport:
            where_clauses.append("pred.sport = ?")
            params.append(sport)

        if prop_type:
            where_clauses.append("pred.prop_type = ?")
            params.append(prop_type)

        if model:
            where_clauses.append("pred.model = ?")
            params.append(model)

        where_sql = " AND ".join(where_clauses)
        params.append(limit)

        query = f"""
            SELECT
                pred.prediction_date,
                pred.prediction_date as game_date,
                pred.player_name,
                pred.team,
                pred.opponent,
                pred.sport,
                pred.prop_type,
                pred.market_line,
                pred.predicted_value,
                pred.recommendation,
                pred.confidence,
                pred.edge_pct,
                pred.model_type as model,
                res.actual_value
            FROM player_props_predictions pred
            JOIN props_results res ON (
                pred.player_name = res.player_name AND
                pred.prop_type = res.prop_type AND
                pred.prediction_date = res.game_date
            )
            WHERE {where_sql}
            ORDER BY pred.prediction_date DESC
            LIMIT ?
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        predictions = []
        for row in rows:
            result = self._determine_result(
                row['recommendation'],
                row['market_line'],
                row['actual_value']
            )

            predictions.append({
                'prediction_date': row['prediction_date'],
                'game_date': row['game_date'],
                'player_name': row['player_name'],
                'team': row['team'],
                'opponent': row['opponent'],
                'sport': row['sport'],
                'prop_type': row['prop_type'],
                'market_line': row['market_line'],
                'predicted_value': row['predicted_value'],
                'actual_value': row['actual_value'],
                'recommendation': row['recommendation'],
                'confidence': row['confidence'] or 0.0,
                'edge_pct': row['edge_pct'] or 0.0,
                'model': row['model'] or 'ensemble',
                'result': result,
                'profit_loss': 1.0 if result == 'WIN' else -1.1
            })

        return predictions

    def _empty_response(self, filters: Dict, error: Optional[str] = None) -> Dict:
        """Return empty response structure"""
        return {
            'summary': {
                'total_predictions': 0,
                'wins': 0,
                'losses': 0,
                'pushes': 0,
                'win_rate': 0.0,
                'roi': 0.0,
                'avg_edge': 0.0,
                'units_won': 0.0,
                'pnl_dollars': 0.0
            },
            'by_confidence': {},
            'by_prop_type': {},
            'by_sport': {},
            'by_model': {},
            'history': [],
            'predictions': [],
            'predictions_total': 0,
            'filters': filters,
            'generated_at': datetime.utcnow().isoformat(),
            'error': error
        }
