"""
Automated Regression to Mean Alert Runner
CREATED: 2025-11-09

Automatically monitors live games and logs regression to mean alerts.
This feeds the autonomous learning system.

Run every 5 minutes during game time via cron:
    */5 18-23 * * * cd /root/sporttrader/backend && source venv/bin/activate && python3 run_regression_alerts.py --sport nba >> logs/regression_alerts.log 2>&1
"""

import sys
import os
import logging
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from pathlib import Path
import argparse

# Add backend to path
sys.path.append(str(Path(__file__).parent))

# Setup logging
log_dir = Path("backend/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'regression_alerts_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RegressionAlertRunner:
    """Runs regression to mean analysis for all live games automatically"""

    def __init__(self, sport: str):
        self.sport = sport.lower()

        # Load parameters for this sport
        params_file = Path(f"backend/strategies/regression_to_mean/{sport}_params.json")
        if params_file.exists():
            import json
            with open(params_file, 'r') as f:
                params = json.load(f)
                self.z_score_threshold = params.get('z_score_threshold', 2.0)
                self.min_edge = params.get('min_edge', 3.0)
                self.min_confidence = params.get('min_confidence', 0.60)
        else:
            # Default parameters
            self.z_score_threshold = 2.0
            self.min_edge = 3.0
            self.min_confidence = 0.60

        # Setup tracking
        tracking_dir = Path("backend/data/tracking/regression")
        tracking_dir.mkdir(parents=True, exist_ok=True)
        self.alerts_log = tracking_dir / f"{sport}_regression_alerts.csv"

        # Initialize log file
        if not self.alerts_log.exists():
            df = pd.DataFrame(columns=[
                'alert_id', 'timestamp', 'game_date', 'game_id',
                'quarter', 'time_remaining', 'home_team', 'away_team',
                'home_score', 'away_score', 'current_total',
                'predicted_total', 'live_total', 'z_score', 'edge',
                'confidence', 'recommendation'
            ])
            df.to_csv(self.alerts_log, index=False)

    def fetch_live_games(self) -> list:
        """Fetch all live games for the sport"""
        logger.info(f"Fetching live {self.sport.upper()} games...")

        if self.sport == 'nba':
            return self._fetch_nba_live_games()
        elif self.sport == 'ncaab':
            return self._fetch_ncaab_live_games()
        else:
            return []

    def _fetch_nba_live_games(self) -> list:
        """Fetch live NBA games from ESPN"""
        try:
            today = datetime.now().strftime('%Y%m%d')
            url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today}"

            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return []

            data = response.json()
            live_games = []

            for event in data.get('events', []):
                status = event.get('status', {})
                state = status.get('type', {}).get('state', '')

                # Only in-progress games
                if state != 'in':
                    continue

                comp = event.get('competitions', [{}])[0]
                competitors = comp.get('competitors', [])

                if len(competitors) != 2:
                    continue

                # Extract game info
                home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                away = next((c for c in competitors if c.get('homeAway') == 'away'), None)

                if not home or not away:
                    continue

                # Get live odds if available
                odds = comp.get('odds', [])
                live_total = None
                if odds and len(odds) > 0:
                    live_total = odds[0].get('overUnder')

                game = {
                    'game_id': event.get('id', ''),
                    'game_date': datetime.now().strftime('%Y-%m-%d'),
                    'home_team': home.get('team', {}).get('displayName', ''),
                    'away_team': away.get('team', {}).get('displayName', ''),
                    'home_score': int(home.get('score', 0)),
                    'away_score': int(away.get('score', 0)),
                    'quarter': int(status.get('period', 1)),
                    'time_remaining': status.get('displayClock', '0:00'),
                    'live_total': live_total
                }

                live_games.append(game)
                logger.info(f"  Found: {game['away_team']} @ {game['home_team']} - Q{game['quarter']} {game['time_remaining']}")

            return live_games

        except Exception as e:
            logger.error(f"Error fetching NBA live games: {e}")
            return []

    def _fetch_ncaab_live_games(self) -> list:
        """Fetch live NCAAB games from ESPN"""
        try:
            today = datetime.now().strftime('%Y%m%d')
            url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={today}"

            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return []

            data = response.json()
            live_games = []

            for event in data.get('events', []):
                status = event.get('status', {})
                state = status.get('type', {}).get('state', '')

                # Only in-progress games
                if state != 'in':
                    continue

                comp = event.get('competitions', [{}])[0]
                competitors = comp.get('competitors', [])

                if len(competitors) != 2:
                    continue

                home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                away = next((c for c in competitors if c.get('homeAway') == 'away'), None)

                if not home or not away:
                    continue

                # Get live odds if available
                odds = comp.get('odds', [])
                live_total = None
                if odds and len(odds) > 0:
                    live_total = odds[0].get('overUnder')

                game = {
                    'game_id': event.get('id', ''),
                    'game_date': datetime.now().strftime('%Y-%m-%d'),
                    'home_team': home.get('team', {}).get('displayName', ''),
                    'away_team': away.get('team', {}).get('displayName', ''),
                    'home_score': int(home.get('score', 0)),
                    'away_score': int(away.get('score', 0)),
                    'quarter': int(status.get('period', 1)),
                    'time_remaining': status.get('displayClock', '0:00'),
                    'live_total': live_total
                }

                live_games.append(game)
                logger.info(f"  Found: {game['away_team']} @ {game['home_team']} - {game['quarter']}H {game['time_remaining']}")

            return live_games

        except Exception as e:
            logger.error(f"Error fetching NCAAB live games: {e}")
            return []

    def get_model_prediction(self, game: dict) -> float:
        """
        Get model prediction for game total

        In production, this would:
        1. Load ML models for the sport
        2. Generate prediction based on current game state
        3. Return predicted total

        For now, using simplified placeholder
        """
        # Simplified: use current scoring rate
        current_total = game['home_score'] + game['away_score']

        # Estimate based on quarter/half
        if self.sport == 'nba':
            quarters_played = game['quarter'] - 1
            if quarters_played > 0:
                avg_per_quarter = current_total / quarters_played
                predicted_total = avg_per_quarter * 4
            else:
                predicted_total = 220.0  # League average
        else:  # NCAAB
            halves_played = game['quarter'] - 1
            if halves_played > 0:
                avg_per_half = current_total / halves_played
                predicted_total = avg_per_half * 2
            else:
                predicted_total = 140.0  # NCAA average

        return predicted_total

    def analyze_game(self, game: dict) -> dict:
        """Analyze a single game for regression opportunities"""
        try:
            # Need live total to analyze
            if not game.get('live_total'):
                return None

            # Get model prediction
            predicted_total = self.get_model_prediction(game)
            live_total = float(game['live_total'])

            # Calculate deviation
            deviation = predicted_total - live_total

            # Calculate z-score (simplified - use 10 point std dev)
            std_dev = 10.0  # Typical game volatility
            z_score = abs(deviation) / std_dev

            # Check if meets thresholds
            edge = abs(deviation)

            if z_score < self.z_score_threshold:
                return None

            if edge < self.min_edge:
                return None

            # Determine recommendation
            if deviation > 0:
                recommendation = 'OVER'
            else:
                recommendation = 'UNDER'

            # Calculate confidence (simplified)
            confidence = min(0.95, 0.50 + (z_score - self.z_score_threshold) * 0.1)

            if confidence < self.min_confidence:
                return None

            # Create alert
            alert = {
                'alert_id': f"{game['game_id']}_{datetime.now().strftime('%H%M%S')}",
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'game_date': game['game_date'],
                'game_id': game['game_id'],
                'quarter': game['quarter'],
                'time_remaining': game['time_remaining'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'home_score': game['home_score'],
                'away_score': game['away_score'],
                'current_total': game['home_score'] + game['away_score'],
                'predicted_total': predicted_total,
                'live_total': live_total,
                'z_score': z_score,
                'edge': edge,
                'confidence': confidence,
                'recommendation': recommendation
            }

            logger.info(f"  ALERT: {recommendation} {live_total}")
            logger.info(f"    Predicted: {predicted_total:.1f} | Z-Score: {z_score:.2f}")
            logger.info(f"    Edge: {edge:.1f} pts | Confidence: {confidence:.1%}")

            return alert

        except Exception as e:
            logger.error(f"Error analyzing game {game['game_id']}: {e}")
            return None

    def log_alert(self, alert: dict):
        """Log alert to tracking file"""
        if not alert:
            return

        # Load existing log
        existing = pd.read_csv(self.alerts_log)

        # Append new alert
        new_row = pd.DataFrame([alert])
        combined = pd.concat([existing, new_row], ignore_index=True)

        # Save
        combined.to_csv(self.alerts_log, index=False)

    def run(self):
        """Run regression analysis for all live games"""
        logger.info("=" * 80)
        logger.info(f"REGRESSION ALERT RUNNER - {self.sport.upper()}")
        logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        logger.info(f"Parameters: Z-Score={self.z_score_threshold:.1f}, MinEdge={self.min_edge:.1f}, MinConf={self.min_confidence:.1%}")
        logger.info("=" * 80)

        # Fetch live games
        live_games = self.fetch_live_games()

        if not live_games:
            logger.info("No live games found")
            return True

        logger.info(f"Found {len(live_games)} live games")

        # Analyze each game
        alerts = []
        for game in live_games:
            alert = self.analyze_game(game)
            if alert:
                self.log_alert(alert)
                alerts.append(alert)

        if alerts:
            logger.info(f"✅ Generated {len(alerts)} regression alerts")
        else:
            logger.info("No alerts met criteria")

        return True


def main():
    parser = argparse.ArgumentParser(description='Automated Regression to Mean Alert Runner')
    parser.add_argument('--sport', required=True, choices=['nba', 'ncaab'],
                       help='Sport to run regression alerts for')

    args = parser.parse_args()

    runner = RegressionAlertRunner(sport=args.sport)
    success = runner.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
