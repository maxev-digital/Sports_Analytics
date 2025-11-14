"""
Automated Daily Predictions Generator
CREATED: 2025-11-09

Generates and logs predictions for all upcoming games automatically.
This feeds data to the autonomous learning system.

Run daily via cron:
    0 10 * * * cd /root/sporttrader/backend && source venv/bin/activate && python3 automated_daily_predictions.py >> logs/daily_predictions.log 2>&1
"""

import sys
import os
import logging
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import argparse

# Add backend to path
sys.path.append(str(Path(__file__).parent))

# Setup logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'daily_predictions_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutomatedPredictionGenerator:
    """Generates predictions for all upcoming games and logs them automatically"""

    def __init__(self, sport: str):
        self.sport = sport.lower()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Paths
        project_root = Path(__file__).parent.parent if Path(__file__).parent.name == 'backend' else Path(__file__).parent
        self.tracking_dir = project_root / "backend" / "data" / "tracking"
        self.tracking_dir.mkdir(parents=True, exist_ok=True)

        self.predictions_log = self.tracking_dir / "predictions_log.csv"

        logger.info(f"=" * 80)
        logger.info(f"AUTOMATED DAILY PREDICTIONS - {sport.upper()}")
        logger.info(f"Timestamp: {self.timestamp}")
        logger.info(f"=" * 80)

    def fetch_upcoming_games(self) -> List[Dict]:
        """Fetch all upcoming games for next 7 days"""
        logger.info("Fetching upcoming games...")

        if self.sport == 'nba':
            return self._fetch_nba_games()
        elif self.sport == 'ncaab':
            return self._fetch_ncaab_games()
        else:
            logger.warning(f"Sport {self.sport} not yet supported")
            return []

    def _fetch_nba_games(self) -> List[Dict]:
        """Fetch NBA games from SportsDataIO or ESPN"""
        import requests

        games = []
        today = datetime.now()

        # Check next 7 days
        for days_ahead in range(7):
            date = today + timedelta(days=days_ahead)
            date_str = date.strftime('%Y%m%d')

            try:
                url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_str}"
                response = requests.get(url, timeout=10)

                if response.status_code != 200:
                    continue

                data = response.json()

                if 'events' not in data:
                    continue

                for event in data['events']:
                    # Only get games that haven't started yet
                    status = event.get('status', {}).get('type', {}).get('state', '')
                    if status not in ['pre', 'scheduled']:
                        continue

                    competitions = event.get('competitions', [])
                    if not competitions:
                        continue

                    comp = competitions[0]
                    competitors = comp.get('competitors', [])

                    if len(competitors) != 2:
                        continue

                    home_team = None
                    away_team = None

                    for team in competitors:
                        team_name = team.get('team', {}).get('displayName', '')
                        if team.get('homeAway') == 'home':
                            home_team = team_name
                        else:
                            away_team = team_name

                    if home_team and away_team:
                        game_date = date.strftime('%Y-%m-%d')
                        game_time = event.get('date', '')

                        games.append({
                            'game_date': game_date,
                            'game_time': game_time,
                            'home_team': home_team,
                            'away_team': away_team,
                            'sport': 'nba'
                        })

                        logger.info(f"  Found: {away_team} @ {home_team} on {game_date}")

            except Exception as e:
                logger.error(f"Error fetching games for {date_str}: {e}")
                continue

        return games

    def _fetch_ncaab_games(self) -> List[Dict]:
        """Fetch NCAAB games from ESPN"""
        import requests

        games = []
        today = datetime.now()

        # Check next 7 days
        for days_ahead in range(7):
            date = today + timedelta(days=days_ahead)
            date_str = date.strftime('%Y%m%d')

            try:
                url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={date_str}"
                response = requests.get(url, timeout=10)

                if response.status_code != 200:
                    continue

                data = response.json()

                if 'events' not in data:
                    continue

                for event in data['events']:
                    # Only get games that haven't started yet
                    status = event.get('status', {}).get('type', {}).get('state', '')
                    if status not in ['pre', 'scheduled']:
                        continue

                    competitions = event.get('competitions', [])
                    if not competitions:
                        continue

                    comp = competitions[0]
                    competitors = comp.get('competitors', [])

                    if len(competitors) != 2:
                        continue

                    home_team = None
                    away_team = None

                    for team in competitors:
                        team_name = team.get('team', {}).get('displayName', '')
                        if team.get('homeAway') == 'home':
                            home_team = team_name
                        else:
                            away_team = team_name

                    if home_team and away_team:
                        game_date = date.strftime('%Y-%m-%d')
                        game_time = event.get('date', '')

                        games.append({
                            'game_date': game_date,
                            'game_time': game_time,
                            'home_team': home_team,
                            'away_team': away_team,
                            'sport': 'ncaab'
                        })

                        logger.info(f"  Found: {away_team} @ {home_team} on {game_date}")

            except Exception as e:
                logger.error(f"Error fetching games for {date_str}: {e}")
                continue

        return games

    def generate_predictions(self, games: List[Dict]) -> pd.DataFrame:
        """Generate predictions for all games using ML models"""
        logger.info(f"Generating predictions for {len(games)} games...")

        predictions = []

        for game in games:
            try:
                # Use the models router to generate predictions
                # This calls the same models that Edge Lab uses
                prediction = self._predict_game(game)

                if prediction:
                    predictions.append(prediction)
                    logger.info(f"  ✓ {game['away_team']} @ {game['home_team']}: {prediction['predicted_total']:.1f}")

            except Exception as e:
                logger.error(f"Error predicting {game['away_team']} @ {game['home_team']}: {e}")
                continue

        return pd.DataFrame(predictions)

    def _predict_game(self, game: Dict) -> Dict:
        """Generate prediction for a single game"""
        # Import model loaders
        if game['sport'] == 'nba':
            from models.random_forest_totals import get_nba_random_forest_model
            model = get_nba_random_forest_model()
        elif game['sport'] == 'ncaab':
            from models.ncaab.random_forest_totals import get_ncaab_random_forest_model
            model = get_ncaab_random_forest_model()
        else:
            return None

        # Fetch team stats (you'll need to implement this based on your stats sources)
        game_data = self._fetch_team_stats(game)

        if not game_data:
            logger.warning(f"Could not fetch stats for {game['away_team']} @ {game['home_team']}")
            return None

        # Generate prediction (without market total initially)
        result = model.predict(game_data)

        # Fetch market total from odds API
        market_total = self._fetch_market_total(game)

        if market_total:
            # Regenerate with market total for edge calculation
            result = model.predict(game_data, market_total)

        # Format prediction
        prediction = {
            'prediction_id': f"{game['sport'].upper()}_{game['game_date'].replace('-', '')}_{game['away_team'].replace(' ', '_')}_{game['home_team'].replace(' ', '_')}",
            'date_predicted': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'game_date': game['game_date'],
            'game_time': game['game_time'],
            'away_team': game['away_team'],
            'home_team': game['home_team'],
            'predicted_total': result['prediction']['total'],
            'market_total': market_total if market_total else 0.0,
            'edge': result.get('market_analysis', {}).get('edge', 0.0),
            'recommendation': result.get('market_analysis', {}).get('recommendation', 'PASS'),
            'confidence': result['prediction'].get('confidence', 0.0),
            'bet_placed': 'NO'  # Automated predictions don't place bets
        }

        return prediction

    def _fetch_team_stats(self, game: Dict) -> Dict:
        """Fetch team statistics (placeholder - implement based on your data sources)"""
        # TODO: Implement actual stats fetching from your data sources
        # For now, return basic structure
        return {
            'home_team': game['home_team'],
            'away_team': game['away_team'],
            'home_stats': {},
            'away_stats': {}
        }

    def _fetch_market_total(self, game: Dict) -> float:
        """Fetch market total from odds API (placeholder)"""
        # TODO: Implement odds API fetching
        # For now, return None
        return None

    def log_predictions(self, predictions_df: pd.DataFrame):
        """Log predictions to tracking file"""
        logger.info("Logging predictions...")

        if predictions_df.empty:
            logger.warning("No predictions to log")
            return

        # Load existing log or create new
        if self.predictions_log.exists():
            existing = pd.read_csv(self.predictions_log)

            # Remove duplicates (don't re-log same game)
            existing_ids = set(existing['prediction_id'].values)
            new_preds = predictions_df[~predictions_df['prediction_id'].isin(existing_ids)]

            if new_preds.empty:
                logger.info("All predictions already logged")
                return

            # Append new predictions
            combined = pd.concat([existing, new_preds], ignore_index=True)
        else:
            combined = predictions_df
            new_preds = predictions_df

        # Save
        combined.to_csv(self.predictions_log, index=False)

        logger.info(f"✓ Logged {len(new_preds)} new predictions")
        logger.info(f"✓ Total predictions tracked: {len(combined)}")

    def run(self):
        """Run the full automated prediction pipeline"""
        try:
            # Step 1: Fetch upcoming games
            games = self.fetch_upcoming_games()

            if not games:
                logger.warning("No upcoming games found")
                return True

            logger.info(f"Found {len(games)} upcoming games")

            # Step 2: Generate predictions
            predictions_df = self.generate_predictions(games)

            if predictions_df.empty:
                logger.warning("No predictions generated")
                return True

            # Step 3: Log predictions
            self.log_predictions(predictions_df)

            logger.info("✓ Automated prediction generation complete")
            return True

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            return False


def main():
    parser = argparse.ArgumentParser(description='Automated Daily Predictions Generator')
    parser.add_argument('--sport', required=True, choices=['nba', 'ncaab', 'nfl', 'ncaaf', 'nhl'],
                       help='Sport to generate predictions for')

    args = parser.parse_args()

    generator = AutomatedPredictionGenerator(sport=args.sport)
    success = generator.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
