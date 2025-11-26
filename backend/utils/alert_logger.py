"""
Alert Logging Utility
Handles CSV logging for all system alerts and their outcomes
"""
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Literal
import logging

logger = logging.getLogger(__name__)

# CSV file paths
TRACKING_DIR = Path(__file__).parent.parent / "data" / "tracking"
ALERTS_LOG = TRACKING_DIR / "alerts_log.csv"
ALERTS_RESULTS_LOG = TRACKING_DIR / "alerts_results_log.csv"
ALERTS_PERFORMANCE_SUMMARY = TRACKING_DIR / "alerts_performance_summary.csv"

# Ensure tracking directory exists
TRACKING_DIR.mkdir(parents=True, exist_ok=True)


def log_alert(alert_data: Dict) -> bool:
    """
    Log a new alert to alerts_log.csv
    Called when alert is generated

    Args:
        alert_data: Dictionary containing alert information

    Returns:
        bool: True if logged successfully, False otherwise
    """
    try:
        # Extract fields from alert_data
        alert_id = alert_data.get('id', alert_data.get('alert_id', ''))
        alert_type = alert_data.get('alert_type', '')

        # Get game information
        game = alert_data.get('game', {})
        game_id = alert_data.get('game_id', game.get('id', ''))
        sport = alert_data.get('sport', game.get('sport_key', ''))
        away_team = alert_data.get('away_team', game.get('away_team', ''))
        home_team = alert_data.get('home_team', game.get('home_team', ''))

        # Get timing information
        generated_at = alert_data.get('generated_at', datetime.now().isoformat())
        timestamp = alert_data.get('timestamp', generated_at)
        date_generated = timestamp.split('T')[0] if 'T' in timestamp else timestamp[:10]

        game_date = alert_data.get('game_date', game.get('commence_time', ''))
        if 'T' in game_date:
            game_date = game_date.split('T')[0]

        game_time = alert_data.get('game_time', '')
        if not game_time and game.get('commence_time'):
            game_time = game.get('commence_time').split('T')[1][:8] if 'T' in game.get('commence_time') else ''

        # Get betting information
        market_type = alert_data.get('market_type', alert_data.get('market', ''))
        recommended_side = alert_data.get('recommended_side', alert_data.get('recommendation', ''))
        recommended_odds = alert_data.get('recommended_odds', alert_data.get('odds', ''))
        recommended_bookmaker = alert_data.get('recommended_bookmaker', alert_data.get('bookmaker', ''))

        # Get analysis metrics
        confidence = alert_data.get('confidence', '')
        edge_percent = alert_data.get('edge_percent', alert_data.get('edge', 0))
        profit_potential = alert_data.get('profit_potential', alert_data.get('ev', 0))

        # Get status and metadata
        status = alert_data.get('status', 'pending')
        strategy_details = json.dumps(alert_data.get('strategy_details', {}))
        notes = alert_data.get('notes', alert_data.get('message', ''))

        # Prepare row data
        row = [
            alert_id,
            alert_type,
            date_generated,
            timestamp,
            game_id,
            sport,
            away_team,
            home_team,
            game_date,
            game_time,
            market_type,
            recommended_side,
            recommended_odds,
            recommended_bookmaker,
            confidence,
            edge_percent,
            profit_potential,
            status,
            strategy_details,
            notes
        ]

        # Check if file exists and has header
        file_exists = ALERTS_LOG.exists()

        # Write to CSV
        with open(ALERTS_LOG, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header if file is new
            if not file_exists:
                writer.writerow([
                    'alert_id', 'alert_type', 'date_generated', 'timestamp', 'game_id', 'sport',
                    'away_team', 'home_team', 'game_date', 'game_time', 'market_type',
                    'recommended_side', 'recommended_odds', 'recommended_bookmaker', 'confidence',
                    'edge_percent', 'profit_potential', 'status', 'strategy_details', 'notes'
                ])

            writer.writerow(row)

        logger.info(f"✅ Logged alert {alert_id} ({alert_type}) to CSV")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to log alert to CSV: {str(e)}")
        return False


def log_alert_result(
    alert_id: str,
    alert_type: str,
    game_id: str,
    outcome: Literal['won', 'lost', 'push'],
    actual_result: Dict,
    recommended_side: str,
    profit_loss: float = 0.0,
    grading_method: str = 'auto',
    notes: str = ''
) -> bool:
    """
    Log graded result to alerts_results_log.csv
    Called when alert is settled

    Args:
        alert_id: Unique alert identifier
        alert_type: Type of alert (arbitrage, steam_move, etc.)
        game_id: Game identifier
        outcome: 'won', 'lost', or 'push'
        actual_result: Dictionary with game result data
        recommended_side: What was recommended
        profit_loss: Profit/loss amount (units)
        grading_method: 'auto' or 'manual'
        notes: Additional notes about grading

    Returns:
        bool: True if logged successfully, False otherwise
    """
    try:
        # Extract actual game results
        away_score = actual_result.get('away_score', '')
        home_score = actual_result.get('home_score', '')
        actual_total = actual_result.get('actual_total', '')
        if not actual_total and away_score and home_score:
            actual_total = int(away_score) + int(home_score)

        actual_outcome = actual_result.get('actual_outcome', '')

        # Get current timestamp
        graded_at = datetime.now().isoformat()

        # Prepare row data
        row = [
            alert_id,
            alert_type,
            game_id,
            away_score,
            home_score,
            actual_total,
            actual_outcome,
            recommended_side,
            outcome,
            profit_loss,
            graded_at,
            grading_method,
            notes
        ]

        # Check if file exists and has header
        file_exists = ALERTS_RESULTS_LOG.exists()

        # Write to CSV
        with open(ALERTS_RESULTS_LOG, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header if file is new
            if not file_exists:
                writer.writerow([
                    'alert_id', 'alert_type', 'game_id', 'away_score', 'home_score',
                    'actual_total', 'actual_result', 'recommended_side', 'outcome',
                    'profit_loss', 'graded_at', 'grading_method', 'notes'
                ])

            writer.writerow(row)

        logger.info(f"✅ Logged result for alert {alert_id}: {outcome.upper()}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to log alert result to CSV: {str(e)}")
        return False


def grade_alert(
    alert_type: str,
    recommended_side: str,
    recommended_odds: float,
    actual_result: Dict,
    market_type: str = ''
) -> tuple[Literal['won', 'lost', 'push'], float, str]:
    """
    Determine if alert won, lost, or pushed
    Based on recommended_side vs actual game outcome

    Args:
        alert_type: Type of alert
        recommended_side: What was recommended (e.g., "OVER 220.5", "NNG @ +180")
        recommended_odds: Odds for the recommendation
        actual_result: Dictionary with game result data
        market_type: Market type (totals, spreads, moneyline, etc.)

    Returns:
        tuple: (outcome, profit_loss, notes)
    """
    try:
        away_score = int(actual_result.get('away_score', 0))
        home_score = int(actual_result.get('home_score', 0))
        actual_total = away_score + home_score

        # Parse recommended side
        rec_upper = recommended_side.upper()

        # ARBITRAGE - Always wins (by definition)
        if alert_type == 'arbitrage':
            # Calculate guaranteed profit
            profit = calculate_arb_profit(recommended_odds)
            return ('won', profit, 'Arbitrage guarantee')

        # GOALIE PULL / EMPTY NET ALERTS
        if alert_type == 'goalie_pull':
            en_goal_scored = actual_result.get('en_goal_scored', False)
            goalie_pulled = actual_result.get('goalie_pulled', False)

            if not goalie_pulled:
                return ('push', 0.0, 'Goalie not pulled - void bet')

            # NNG (No Next Goal)
            if 'NNG' in rec_upper or 'NO NEXT GOAL' in rec_upper:
                if not en_goal_scored:
                    profit = calculate_profit(recommended_odds, 1.0)
                    return ('won', profit, 'No EN goal scored')
                else:
                    return ('lost', -1.0, 'EN goal scored')

            # OVER (expect EN goal)
            elif 'OVER' in rec_upper:
                if en_goal_scored:
                    profit = calculate_profit(recommended_odds, 1.0)
                    return ('won', profit, 'EN goal scored')
                else:
                    return ('lost', -1.0, 'No EN goal scored')

            # UNDER (expect no EN goal)
            elif 'UNDER' in rec_upper:
                if not en_goal_scored:
                    profit = calculate_profit(recommended_odds, 1.0)
                    return ('won', profit, 'No EN goal scored')
                else:
                    return ('lost', -1.0, 'EN goal scored')

        # TOTALS (OVER/UNDER)
        if 'OVER' in rec_upper or 'UNDER' in rec_upper:
            # Extract the line
            line = extract_number_from_recommendation(recommended_side)

            if line is None:
                return ('push', 0.0, 'Could not parse line')

            if 'OVER' in rec_upper:
                if actual_total > line:
                    profit = calculate_profit(recommended_odds, 1.0)
                    return ('won', profit, f'Actual total {actual_total} > {line}')
                elif actual_total == line:
                    return ('push', 0.0, f'Actual total {actual_total} = {line}')
                else:
                    return ('lost', -1.0, f'Actual total {actual_total} < {line}')

            elif 'UNDER' in rec_upper:
                if actual_total < line:
                    profit = calculate_profit(recommended_odds, 1.0)
                    return ('won', profit, f'Actual total {actual_total} < {line}')
                elif actual_total == line:
                    return ('push', 0.0, f'Actual total {actual_total} = {line}')
                else:
                    return ('lost', -1.0, f'Actual total {actual_total} > {line}')

        # SPREAD
        if 'SPREAD' in market_type.upper() or any(team in rec_upper for team in ['@', 'VS']):
            # Parse spread
            spread = extract_number_from_recommendation(recommended_side)
            if spread is None:
                return ('push', 0.0, 'Could not parse spread')

            # Determine which team was recommended
            # This is simplified - real implementation would need team name matching
            home_covered = (home_score + spread) > away_score

            if home_covered:
                profit = calculate_profit(recommended_odds, 1.0)
                return ('won', profit, f'Spread covered')
            else:
                return ('lost', -1.0, f'Spread not covered')

        # MIDDLE - Special case
        if alert_type == 'middle':
            middle_hit = actual_result.get('middle_hit', False)
            if middle_hit:
                profit = calculate_middle_profit(recommended_odds)
                return ('won', profit, 'Middle hit!')
            else:
                # Check which side lost
                return ('push', 0.0, 'Middle missed - broke even')

        # STEAM MOVE - Regular bet grading
        if alert_type == 'steam_move':
            # Grade like normal bet based on market type
            # This would use same logic as TOTALS/SPREAD above
            pass

        # Default - unable to grade
        return ('push', 0.0, 'Unable to determine outcome')

    except Exception as e:
        logger.error(f"Error grading alert: {str(e)}")
        return ('push', 0.0, f'Grading error: {str(e)}')


def calculate_profit(odds: float, stake: float = 1.0) -> float:
    """
    Calculate profit from winning bet

    Args:
        odds: American odds (e.g., -110, +150)
        stake: Bet amount (default 1 unit)

    Returns:
        float: Profit amount
    """
    try:
        odds_num = float(odds)

        if odds_num > 0:
            # Positive odds (e.g., +150 = win 1.5 units on 1 unit stake)
            return stake * (odds_num / 100)
        else:
            # Negative odds (e.g., -110 = win 0.909 units on 1 unit stake)
            return stake * (100 / abs(odds_num))
    except:
        return 0.0


def calculate_arb_profit(odds_list: List[float]) -> float:
    """
    Calculate guaranteed profit from arbitrage

    Args:
        odds_list: List of odds for both sides

    Returns:
        float: Guaranteed profit percentage
    """
    # Simplified - real implementation would calculate proper arb stakes
    return 0.02  # ~2% typical arb profit


def calculate_middle_profit(odds_list: List[float]) -> float:
    """
    Calculate profit from hitting middle

    Args:
        odds_list: List of odds for both sides

    Returns:
        float: Profit from both bets winning
    """
    # Simplified - real implementation would calculate actual middle profit
    return 1.8  # Example: both sides win


def extract_number_from_recommendation(rec: str) -> Optional[float]:
    """
    Extract numerical value from recommendation string

    Examples:
        "OVER 220.5" -> 220.5
        "Lakers -3.5" -> -3.5
        "UNDER 48.5" -> 48.5

    Args:
        rec: Recommendation string

    Returns:
        float or None: Extracted number
    """
    import re

    # Look for decimal number with optional negative sign
    match = re.search(r'[-+]?\d+\.?\d*', rec)
    if match:
        try:
            return float(match.group())
        except:
            return None
    return None


def get_pending_alerts() -> List[Dict]:
    """
    Get all pending alerts from alerts_log.csv

    Returns:
        List of alert dictionaries
    """
    try:
        pending = []

        if not ALERTS_LOG.exists():
            return pending

        with open(ALERTS_LOG, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('status', '').lower() == 'pending':
                    pending.append(row)

        return pending

    except Exception as e:
        logger.error(f"Error reading pending alerts: {str(e)}")
        return []


def update_alert_status(alert_id: str, new_status: str) -> bool:
    """
    Update the status of an alert in alerts_log.csv

    Args:
        alert_id: Alert ID to update
        new_status: New status ('pending', 'won', 'lost', 'push')

    Returns:
        bool: True if updated successfully
    """
    try:
        if not ALERTS_LOG.exists():
            return False

        # Read all rows
        rows = []
        with open(ALERTS_LOG, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if row['alert_id'] == alert_id:
                    row['status'] = new_status
                rows.append(row)

        # Write back
        with open(ALERTS_LOG, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        logger.info(f"Updated alert {alert_id} status to {new_status}")
        return True

    except Exception as e:
        logger.error(f"Error updating alert status: {str(e)}")
        return False


if __name__ == "__main__":
    # Test logging
    test_alert = {
        'id': 'test_123',
        'alert_type': 'steam_move',
        'game_id': 'nba_lal_gsw',
        'sport': 'basketball_nba',
        'away_team': 'Los Angeles Lakers',
        'home_team': 'Golden State Warriors',
        'game_date': '2025-11-15',
        'game_time': '19:00:00',
        'market_type': 'totals',
        'recommended_side': 'OVER 220.5',
        'recommended_odds': -110,
        'recommended_bookmaker': 'fanduel',
        'confidence': 'HIGH',
        'edge_percent': 5.2,
        'profit_potential': 12.3,
        'generated_at': '2025-11-15T18:30:00',
        'timestamp': '2025-11-15T18:30:00',
        'status': 'pending',
        'notes': 'Heavy sharp action on OVER'
    }

    print("Testing alert logger...")
    result = log_alert(test_alert)
    print(f"Log alert result: {result}")

    # Test grading
    test_result = {
        'away_score': 115,
        'home_score': 108,
        'actual_total': 223
    }

    outcome, profit, notes = grade_alert(
        'steam_move',
        'OVER 220.5',
        -110,
        test_result,
        'totals'
    )

    print(f"Grading result: {outcome}, Profit: {profit}, Notes: {notes}")

    # Test logging result
    result = log_alert_result(
        'test_123',
        'steam_move',
        'nba_lal_gsw',
        outcome,
        test_result,
        'OVER 220.5',
        profit,
        'auto',
        notes
    )

    print(f"Log result: {result}")
