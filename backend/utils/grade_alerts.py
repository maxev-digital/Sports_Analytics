"""
Alert Grading System
Grades betting alerts (arbitrage, middle, steam moves) against actual game results
Calculates WIN/LOSS/PUSH outcomes and profit/loss

Runs daily after games complete to populate alerts_results_log.csv
"""

import sys
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File paths
BASE_DIR = Path(__file__).parent.parent
ALERTS_LOG = BASE_DIR / "data" / "tracking" / "alerts_log.csv"
RESULTS_LOG = BASE_DIR / "data" / "tracking" / "alerts_results_log.csv"
PERFORMANCE_SUMMARY = BASE_DIR / "data" / "tracking" / "alerts_performance_summary.csv"

# Odds API configuration
import os
ODDS_API_KEY = os.getenv('ODDS_API_KEY', '1da2e5df04ef63dd4d9f7645829dbf20')
ODDS_API_BASE = "https://api.the-odds-api.com/v4"


class AlertGrader:
    """Grades betting alerts and tracks performance"""

    def __init__(self):
        self.results_cache = {}  # Cache game results to avoid duplicate API calls

    def fetch_game_results(self, sport: str, days_back: int = 3) -> Dict:
        """
        Fetch completed game scores from Odds API

        Args:
            sport: Sport key (basketball_nba, icehockey_nhl, etc.)
            days_back: How many days back to fetch results

        Returns:
            Dict mapping game_id to scores
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)

            # Format dates for API
            date_from = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            date_to = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')

            url = f"{ODDS_API_BASE}/sports/{sport}/scores/"
            params = {
                'apiKey': ODDS_API_KEY,
                'daysFrom': days_back,
                'dateFormat': 'iso'
            }

            logger.info(f"Fetching {sport} results from past {days_back} days...")
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                results = {}

                for game in data:
                    if game.get('completed'):
                        game_id = game['id']
                        scores = game.get('scores', [])

                        if len(scores) >= 2:
                            # Extract home and away scores
                            home_team = None
                            away_team = None
                            home_score = None
                            away_score = None

                            for score in scores:
                                if score.get('name'):
                                    if 'home' in str(score).lower() or score == scores[0]:
                                        home_team = score['name']
                                        home_score = score.get('score')
                                    else:
                                        away_team = score['name']
                                        away_score = score.get('score')

                            results[game_id] = {
                                'home_team': home_team,
                                'away_team': away_team,
                                'home_score': home_score,
                                'away_score': away_score,
                                'completed': True
                            }

                logger.info(f"Fetched {len(results)} completed {sport} games")
                return results
            else:
                logger.error(f"API error {response.status_code}: {response.text}")
                return {}

        except Exception as e:
            logger.error(f"Error fetching results for {sport}: {e}")
            return {}

    def grade_middle_alert(self, alert: pd.Series, actual_total: float) -> Dict:
        """
        Grade a middle betting alert

        Args:
            alert: Alert row from alerts_log
            actual_total: Actual game total

        Returns:
            Dict with outcome and profit_loss
        """
        try:
            details = json.loads(alert['strategy_details'])
            low_line = float(details['low_line'])
            high_line = float(details['high_line'])

            # Middle betting: Win if result lands between the two lines
            if low_line < actual_total < high_line:
                # WIN BOTH SIDES - Middle hit!
                # Calculate profit from both bets
                odds_low = details['odds_low']
                odds_high = details['odds_high']

                # Convert American odds to decimal
                if odds_low < 0:
                    decimal_low = 1 + (100 / abs(odds_low))
                else:
                    decimal_low = 1 + (odds_low / 100)

                if odds_high < 0:
                    decimal_high = 1 + (100 / abs(odds_high))
                else:
                    decimal_high = 1 + (odds_high / 100)

                # Profit from $100 on each side
                profit = (decimal_low - 1) * 100 + (decimal_high - 1) * 100

                return {
                    'outcome': 'WIN_BOTH',
                    'profit_loss': profit,
                    'actual_total': actual_total
                }

            elif actual_total == low_line or actual_total == high_line:
                # PUSH one side, win or lose the other
                return {
                    'outcome': 'PUSH_ONE',
                    'profit_loss': 0.0,  # Typically break even
                    'actual_total': actual_total
                }

            elif actual_total < low_line:
                # Lost the OVER bet, won the UNDER bet
                # Net result depends on odds
                return {
                    'outcome': 'LOSE_ONE',
                    'profit_loss': -9.1,  # Typical juice loss
                    'actual_total': actual_total
                }

            else:  # actual_total > high_line
                # Won the OVER bet, lost the UNDER bet
                return {
                    'outcome': 'LOSE_ONE',
                    'profit_loss': -9.1,  # Typical juice loss
                    'actual_total': actual_total
                }

        except Exception as e:
            logger.error(f"Error grading middle alert: {e}")
            return {'outcome': 'ERROR', 'profit_loss': 0.0}

    def grade_arbitrage_alert(self, alert: pd.Series, home_score: int, away_score: int) -> Dict:
        """
        Grade an arbitrage alert
        Arbitrage guarantees profit regardless of outcome
        """
        try:
            details = json.loads(alert['strategy_details'])
            guaranteed_profit = details.get('guaranteed_profit', 0)

            # Arbitrage always wins (risk-free)
            return {
                'outcome': 'WIN',
                'profit_loss': guaranteed_profit,
                'home_score': home_score,
                'away_score': away_score
            }

        except Exception as e:
            logger.error(f"Error grading arbitrage alert: {e}")
            return {'outcome': 'ERROR', 'profit_loss': 0.0}

    def grade_steam_move_alert(self, alert: pd.Series, home_score: int, away_score: int, actual_total: float) -> Dict:
        """
        Grade a steam move alert
        Steam moves are line movements - grade based on final result
        """
        try:
            details = json.loads(alert['strategy_details'])
            market_type = details['market_type']
            side = details['side']
            new_line = float(details['new_line'])

            if market_type == 'totals':
                # Grade OVER/UNDER
                if side == 'over':
                    if actual_total > new_line:
                        return {'outcome': 'WIN', 'profit_loss': 90.91, 'actual_total': actual_total}
                    elif actual_total == new_line:
                        return {'outcome': 'PUSH', 'profit_loss': 0.0, 'actual_total': actual_total}
                    else:
                        return {'outcome': 'LOSS', 'profit_loss': -100.0, 'actual_total': actual_total}
                else:  # under
                    if actual_total < new_line:
                        return {'outcome': 'WIN', 'profit_loss': 90.91, 'actual_total': actual_total}
                    elif actual_total == new_line:
                        return {'outcome': 'PUSH', 'profit_loss': 0.0, 'actual_total': actual_total}
                    else:
                        return {'outcome': 'LOSS', 'profit_loss': -100.0, 'actual_total': actual_total}

            elif market_type == 'spreads':
                # Grade spread bet
                margin = home_score - away_score

                if side == 'favorite':
                    # Favorite must win by more than the spread
                    if margin > new_line:
                        return {'outcome': 'WIN', 'profit_loss': 90.91}
                    elif margin == new_line:
                        return {'outcome': 'PUSH', 'profit_loss': 0.0}
                    else:
                        return {'outcome': 'LOSS', 'profit_loss': -100.0}
                else:
                    # Underdog covers if they lose by less than spread
                    if margin < new_line:
                        return {'outcome': 'WIN', 'profit_loss': 90.91}
                    elif margin == new_line:
                        return {'outcome': 'PUSH', 'profit_loss': 0.0}
                    else:
                        return {'outcome': 'LOSS', 'profit_loss': -100.0}

            return {'outcome': 'UNKNOWN', 'profit_loss': 0.0}

        except Exception as e:
            logger.error(f"Error grading steam move alert: {e}")
            return {'outcome': 'ERROR', 'profit_loss': 0.0}

    def grade_alerts(self, days_back: int = 3):
        """
        Main grading function - grades all ungraded alerts

        Args:
            days_back: How many days back to check for completed games
        """
        logger.info(f"\n{'='*70}")
        logger.info("ALERT GRADING SYSTEM")
        logger.info(f"{'='*70}\n")

        # Load alerts log
        if not ALERTS_LOG.exists():
            logger.error(f"Alerts log not found: {ALERTS_LOG}")
            return

        df_alerts = pd.read_csv(ALERTS_LOG)
        logger.info(f"Loaded {len(df_alerts)} total alerts")

        # Load existing results log
        if RESULTS_LOG.exists():
            df_results = pd.read_csv(RESULTS_LOG)
            graded_alert_ids = set(df_results['alert_id'].values)
        else:
            df_results = pd.DataFrame(columns=[
                'alert_id', 'alert_type', 'game_id', 'away_score', 'home_score',
                'actual_total', 'actual_result', 'recommended_side', 'outcome',
                'profit_loss', 'graded_at', 'grading_method', 'notes'
            ])
            graded_alert_ids = set()

        logger.info(f"Already graded: {len(graded_alert_ids)} alerts")

        # Filter to ungraded alerts from recent days
        df_ungraded = df_alerts[~df_alerts['alert_id'].isin(graded_alert_ids)]
        df_ungraded = df_ungraded[df_ungraded['status'] == 'pending']

        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days_back)
        df_ungraded['date_generated'] = pd.to_datetime(df_ungraded['date_generated'])
        df_ungraded = df_ungraded[df_ungraded['date_generated'] >= cutoff_date]

        logger.info(f"Ungraded alerts from past {days_back} days: {len(df_ungraded)}")

        if len(df_ungraded) == 0:
            logger.info("No alerts to grade")
            return

        # Fetch game results for each sport
        sports = df_ungraded['sport'].unique()
        for sport in sports:
            self.results_cache[sport] = self.fetch_game_results(sport, days_back)

        # Grade each alert
        graded_count = 0
        new_results = []

        for idx, alert in df_ungraded.iterrows():
            game_id = alert['game_id']
            sport = alert['sport']
            alert_type = alert['alert_type']

            # Check if game is completed
            if sport not in self.results_cache or game_id not in self.results_cache[sport]:
                continue  # Game not completed yet

            game_result = self.results_cache[sport][game_id]
            home_score = game_result['home_score']
            away_score = game_result['away_score']

            if home_score is None or away_score is None:
                continue

            actual_total = home_score + away_score

            # Grade based on alert type
            if alert_type == 'middle':
                grade_result = self.grade_middle_alert(alert, actual_total)
            elif alert_type == 'arbitrage':
                grade_result = self.grade_arbitrage_alert(alert, home_score, away_score)
            elif alert_type == 'steam_move':
                grade_result = self.grade_steam_move_alert(alert, home_score, away_score, actual_total)
            else:
                continue

            # Record result
            new_results.append({
                'alert_id': alert['alert_id'],
                'alert_type': alert_type,
                'game_id': game_id,
                'away_score': away_score,
                'home_score': home_score,
                'actual_total': actual_total,
                'actual_result': f"{away_score}-{home_score}",
                'recommended_side': alert.get('recommended_side', ''),
                'outcome': grade_result['outcome'],
                'profit_loss': grade_result['profit_loss'],
                'graded_at': datetime.now().isoformat(),
                'grading_method': 'odds_api_scores',
                'notes': ''
            })

            graded_count += 1

            if graded_count % 100 == 0:
                logger.info(f"Graded {graded_count} alerts...")

        # Append new results
        if new_results:
            df_new = pd.DataFrame(new_results)
            df_results = pd.concat([df_results, df_new], ignore_index=True)
            df_results.to_csv(RESULTS_LOG, index=False)

            logger.info(f"\n✅ Graded {graded_count} alerts")
            logger.info(f"📁 Saved to: {RESULTS_LOG}")

            # Update performance summary
            self.update_performance_summary(df_results)
        else:
            logger.info("No new alerts to grade")

    def update_performance_summary(self, df_results: pd.DataFrame):
        """Calculate and save performance summary by alert type"""

        summary_rows = []

        for alert_type in ['middle', 'arbitrage', 'steam_move']:
            df_type = df_results[df_results['alert_type'] == alert_type]

            if len(df_type) == 0:
                continue

            total_alerts = len(df_type)
            wins = len(df_type[df_type['outcome'].str.contains('WIN', na=False)])
            losses = len(df_type[df_type['outcome'] == 'LOSS'])
            pushes = len(df_type[df_type['outcome'] == 'PUSH'])

            # Win rate (exclude pushes)
            decisive = wins + losses
            win_rate = (wins / decisive * 100) if decisive > 0 else 0.0

            # Calculate ROI
            total_profit = df_type['profit_loss'].sum()
            avg_bet = 100  # Assume $100 per bet
            roi = (total_profit / (total_alerts * avg_bet) * 100) if total_alerts > 0 else 0.0

            # Average odds
            avg_odds = df_type['profit_loss'].mean()

            summary_rows.append({
                'alert_type': alert_type.upper(),
                'total_alerts': total_alerts,
                'settled_alerts': decisive + pushes,
                'pending_alerts': 0,
                'wins': wins,
                'losses': losses,
                'pushes': pushes,
                'win_rate': round(win_rate, 2),
                'roi': round(roi, 2),
                'total_profit': round(total_profit, 2),
                'avg_odds': round(avg_odds, 2),
                'last_updated': datetime.now().isoformat()
            })

        if summary_rows:
            df_summary = pd.DataFrame(summary_rows)
            df_summary.to_csv(PERFORMANCE_SUMMARY, index=False)
            logger.info(f"📊 Updated performance summary: {PERFORMANCE_SUMMARY}")

            # Print summary
            logger.info("\n" + "="*70)
            logger.info("ALERT PERFORMANCE SUMMARY")
            logger.info("="*70)
            for _, row in df_summary.iterrows():
                logger.info(f"\n{row['alert_type']}:")
                logger.info(f"  Win Rate: {row['win_rate']}% ({row['wins']}W-{row['losses']}L-{row['pushes']}P)")
                logger.info(f"  ROI: {row['roi']}%")
                logger.info(f"  Total Profit: ${row['total_profit']:.2f}")


def main():
    """Run alert grading"""
    grader = AlertGrader()
    grader.grade_alerts(days_back=7)  # Grade past week


if __name__ == '__main__':
    main()
