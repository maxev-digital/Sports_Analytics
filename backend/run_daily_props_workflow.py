"""
Daily NBA Props ML Workflow
Runs complete daily workflow for props predictions

Schedule:
- 8:00 AM CST: Scrape props lines
- 2:00 AM CST: Grade previous day's props
- 9:00 AM CST: Generate predictions
- Weekly: Retrain models (Mondays 4:00 AM)

Usage:
    python backend/run_daily_props_workflow.py --task morning
    python backend/run_daily_props_workflow.py --task night
    python backend/run_daily_props_workflow.py --task predictions
    python backend/run_daily_props_workflow.py --task retrain
"""

import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.props.daily_props_scraper import DailyPropsLineScraper
from scrapers.props.results_tracker import PropsResultsTracker
# Prediction and training imports will be added when models are ready


class DailyPropsWorkflow:
    """
    Orchestrates daily props ML workflow
    """

    def __init__(self):
        self.scraper = DailyPropsLineScraper()
        self.tracker = PropsResultsTracker()
        # Use D: drive database (production)
        self.db_path = "D:/backend/data/player_props.db"

    async def morning_workflow(self):
        """
        Morning workflow: Scrape today's props lines
        Run at 8:00 AM CST
        """
        print(f"\n{'='*70}")
        print(f"MORNING WORKFLOW - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")

        # 1. Scrape today's NBA props
        print("[1/3] Scraping NBA props lines...")
        try:
            result = await self.scraper.scrape_nba_props()
            print(f"  [OK] Scraped {result['props_stored']} props")
        except Exception as e:
            print(f"  [ERROR] Failed to scrape props: {e}")
            return

        # 2. Backup data
        print("\n[2/3] Backing up data...")
        try:
            import subprocess
            subprocess.run(['python', 'backup_props_data.py'], check=True)
            print(f"  [OK] Backup complete")
        except Exception as e:
            print(f"  [ERROR] Backup failed: {e}")

        # 3. Ready for predictions
        print(f"\n[3/3] Ready for predictions workflow")
        print(f"  Run: python backend/run_daily_props_workflow.py --task predictions")

        print(f"\n{'='*70}")
        print(f"[SUCCESS] Morning workflow complete!")
        print(f"{'='*70}\n")

    def night_workflow(self):
        """
        Night workflow: Grade previous day's props
        Run at 2:00 AM CST
        """
        print(f"\n{'='*70}")
        print(f"NIGHT WORKFLOW - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")

        # 1. Grade yesterday's props
        print("[1/2] Grading previous day's props...")
        yesterday = date.today() - timedelta(days=1)

        try:
            result = self.tracker.grade_previous_day_props(yesterday)
            print(f"  [OK] Graded {result['graded']} props")
            print(f"  [SKIP] {result['skipped']} (no game data)")
            print(f"  [ERROR] {result['errors']} errors")
        except Exception as e:
            print(f"  [ERROR] Failed to grade props: {e}")
            return

        # 2. Backup data
        print("\n[2/2] Backing up data...")
        try:
            import subprocess
            subprocess.run(['python', 'backup_props_data.py'], check=True)
            print(f"  [OK] Backup complete")
        except Exception as e:
            print(f"  [ERROR] Backup failed: {e}")

        print(f"\n{'='*70}")
        print(f"[SUCCESS] Night workflow complete!")
        print(f"{'='*70}\n")

    def predictions_workflow(self):
        """
        Predictions workflow: Generate ML predictions
        Run at 9:00 AM CST (after morning scrape)
        """
        print(f"\n{'='*70}")
        print(f"PREDICTIONS WORKFLOW - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")

        import sqlite3
        from ml.predictions.daily_props_predictor_fast import EnhancedPropsPredictor

        try:
            # Initialize predictor
            print("[1/4] Loading ML predictor...")
            predictor = EnhancedPropsPredictor(db_path=self.db_path)
            predictor.load_models()
            predictor.load_team_stats()
            print(f"  [OK] Loaded {len(predictor.models)} models\n")

            # Get today's date
            today = date.today().strftime('%Y-%m-%d')
            prediction_date = today

            # Connect to database
            print("[2/4] Loading today's props from database...")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get all props for today
            cursor.execute("""
                SELECT DISTINCT
                    player_id, player_name, team, opponent, home_away,
                    prop_type, market_line, over_odds, under_odds, bookmaker, date
                FROM player_props_lines
                WHERE date = ?
                ORDER BY player_name, prop_type
            """, (today,))

            props = cursor.fetchall()
            print(f"  [OK] Found {len(props)} props for {today}\n")

            if len(props) == 0:
                print(f"  [WARN] No props found for today. Run morning workflow first.")
                return

            # Generate predictions
            print("[3/4] Generating ML predictions...")
            predictions_saved = 0
            predictions_skipped = 0

            for prop in props:
                player_id, player_name, team, opponent, home_away, prop_type, market_line, over_odds, under_odds, bookmaker, game_date = prop

                # Generate prediction
                try:
                    features = predictor.extract_enhanced_features(
                        player_id=player_id,
                        player_name=player_name,
                        prop_type=prop_type,
                        market_line=market_line,
                        home_away=home_away,
                        opponent=opponent
                    )

                    # Find best model for this prop type
                    best_model_key = None
                    best_prediction = None
                    best_confidence = 0

                    for model_key in predictor.models.keys():
                        if model_key.startswith(prop_type):
                            model_data = predictor.models[model_key]
                            model = model_data['model']

                            # Create feature vector
                            feature_values = [features[f] for f in model_data['features']]
                            X = [feature_values]

                            # Predict
                            prediction = model.predict(X)[0]

                            # Use model's test accuracy as confidence proxy
                            confidence = model_data.get('test_accuracy', 50) / 100.0

                            if confidence > best_confidence:
                                best_confidence = confidence
                                best_prediction = prediction
                                best_model_key = model_key

                    if best_prediction is not None:
                        # Calculate edge
                        edge = best_prediction - market_line
                        edge_pct = (edge / market_line) * 100

                        # Determine recommendation
                        if edge > 0:
                            recommendation = 'OVER'
                        else:
                            recommendation = 'UNDER'

                        # Save to database
                        cursor.execute("""
                            INSERT OR REPLACE INTO player_props_predictions
                            (prediction_date, game_date, player_id, player_name, team, opponent,
                             prop_type, market_line, predicted_value, confidence, model_type,
                             edge_pct, recommendation)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            prediction_date, game_date, player_id, player_name, team, opponent,
                            prop_type, market_line, best_prediction, best_confidence, best_model_key,
                            edge_pct, recommendation
                        ))

                        predictions_saved += 1
                    else:
                        predictions_skipped += 1

                except Exception as e:
                    predictions_skipped += 1
                    if predictions_skipped <= 3:  # Only print first few errors
                        print(f"  [SKIP] {player_name} {prop_type}: {str(e)[:50]}")

            conn.commit()
            conn.close()

            print(f"\n  [OK] Saved {predictions_saved} predictions")
            print(f"  [SKIP] {predictions_skipped} props (no model or error)\n")

            # Backup
            print("[4/4] Backing up data...")
            try:
                import subprocess
                subprocess.run(['python', 'backup_props_data.py'], check=True)
                print(f"  [OK] Backup complete\n")
            except Exception as e:
                print(f"  [ERROR] Backup failed: {e}\n")

            print(f"{'='*70}")
            print(f"[SUCCESS] Predictions workflow complete!")
            print(f"  {predictions_saved} predictions ready for API")
            print(f"{'='*70}\n")

        except Exception as e:
            print(f"\n[ERROR] Predictions workflow failed: {e}")
            import traceback
            traceback.print_exc()
            print(f"\n{'='*70}\n")

    def retrain_workflow(self):
        """
        Retraining workflow: Retrain models weekly
        Run Mondays at 4:00 AM CST
        """
        print(f"\n{'='*70}")
        print(f"RETRAINING WORKFLOW - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")

        print("[INFO] Model retraining workflow")
        print("  Run:")
        print("  python backend/ml/models/nba_props_trainer.py --prop-type all")
        print()
        print("  This will:")
        print("  1. Load all graded props from database")
        print("  2. Extract features")
        print("  3. Train XGBoost, LightGBM, Random Forest")
        print("  4. Evaluate and save models")
        print("  5. Update predictions with new models")

        print(f"\n{'='*70}\n")


async def main():
    """
    Main entry point
    """
    parser = argparse.ArgumentParser(description='Run daily props ML workflow')
    parser.add_argument('--task', type=str, required=True,
                       choices=['morning', 'night', 'predictions', 'retrain', 'test'],
                       help='Workflow to run')

    args = parser.parse_args()

    workflow = DailyPropsWorkflow()

    if args.task == 'morning':
        await workflow.morning_workflow()

    elif args.task == 'night':
        workflow.night_workflow()

    elif args.task == 'predictions':
        workflow.predictions_workflow()

    elif args.task == 'retrain':
        workflow.retrain_workflow()

    elif args.task == 'test':
        print("\n[TEST] Running quick test of all workflows...")
        await workflow.morning_workflow()
        workflow.night_workflow()
        workflow.predictions_workflow()


if __name__ == "__main__":
    asyncio.run(main())
