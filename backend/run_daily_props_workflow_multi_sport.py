"""
Daily Multi-Sport Player Props Workflow
========================================
Complete end-to-end workflow for all sports player props

This script orchestrates:
1. Scraping player props from The Odds API (all sports)
2. Generating ML predictions with edge analysis
3. Storing predictions in unified database
4. Grading previous predictions with results

Usage:
    python backend/run_daily_props_workflow_multi_sport.py --sports nba
    python backend/run_daily_props_workflow_multi_sport.py --sports all
    python backend/run_daily_props_workflow_multi_sport.py --sports nba,nfl,nhl --skip-scrape

Schedule with cron (runs daily at 10 AM):
    0 10 * * * cd /root/sporttrader && python backend/run_daily_props_workflow_multi_sport.py --sports all
"""

import sys
import argparse
import asyncio
from pathlib import Path
from datetime import datetime
import subprocess

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


class DailyPropsWorkflow:
    """Orchestrates the complete daily props workflow"""

    def __init__(self, sports: list, db_path: str = "data/player_props.db", skip_scrape: bool = False):
        self.sports = sports
        self.db_path = db_path
        self.skip_scrape = skip_scrape
        self.results = {
            'scraping': {},
            'predictions': {},
            'grading': {}
        }

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    async def run_scraping(self):
        """Step 1: Scrape player props from The Odds API"""
        if self.skip_scrape:
            self.log("SKIPPING scraping (--skip-scrape flag)")
            return

        self.log("=" * 70)
        self.log("STEP 1: SCRAPING PLAYER PROPS")
        self.log("=" * 70)

        try:
            # Import and run scraper
            from scrapers.props.multi_sport_props_scraper import MultiSportPropsScraper

            scraper = MultiSportPropsScraper(db_path=self.db_path)
            result = await scraper.run(sports=self.sports)

            self.results['scraping'] = result
            self.log(f"Scraping complete: {result['props']} props scraped using {result['api_calls']} API calls")

            return result

        except Exception as e:
            self.log(f"Scraping failed: {e}", "ERROR")
            self.results['scraping'] = {'error': str(e)}
            return None

    def run_predictions(self):
        """Step 2: Generate ML predictions"""
        self.log("=" * 70)
        self.log("STEP 2: GENERATING ML PREDICTIONS")
        self.log("=" * 70)

        try:
            from ml.predictions.multi_sport_predictor import MultiSportPropsPredictor

            predictor = MultiSportPropsPredictor(db_path=self.db_path)
            results = predictor.run(sports=self.sports)

            total_predictions = sum(r['predictions'] for r in results)
            self.log(f"Predictions complete: {total_predictions} predictions generated")

            self.results['predictions'] = {
                'total': total_predictions,
                'by_sport': {r['sport']: r['predictions'] for r in results}
            }

            return results

        except Exception as e:
            self.log(f"Predictions failed: {e}", "ERROR")
            self.results['predictions'] = {'error': str(e)}
            return None

    def run_grading(self):
        """Step 3: Grade previous predictions with results"""
        self.log("=" * 70)
        self.log("STEP 3: GRADING PREVIOUS PREDICTIONS")
        self.log("=" * 70)

        try:
            # Import results tracker
            from scrapers.props.results_tracker import ResultsTracker

            tracker = ResultsTracker(db_path=self.db_path)

            # Fetch results for each sport
            total_graded = 0
            for sport in self.sports:
                try:
                    graded = tracker.grade_predictions(sport=sport)
                    self.log(f"Graded {graded} {sport.upper()} predictions")
                    total_graded += graded
                except Exception as e:
                    self.log(f"Grading failed for {sport}: {e}", "WARN")

            self.log(f"Grading complete: {total_graded} predictions graded")

            self.results['grading'] = {'total': total_graded}
            return total_graded

        except Exception as e:
            self.log(f"Grading failed: {e}", "ERROR")
            self.results['grading'] = {'error': str(e)}
            return None

    def generate_summary(self):
        """Generate workflow summary"""
        self.log("=" * 70)
        self.log("WORKFLOW SUMMARY")
        self.log("=" * 70)

        # Scraping summary
        scraping = self.results.get('scraping', {})
        if 'error' in scraping:
            self.log(f"Scraping: FAILED - {scraping['error']}", "ERROR")
        elif scraping:
            self.log(f"Scraping: {scraping.get('props', 0)} props, {scraping.get('api_calls', 0)} API calls")
        else:
            self.log("Scraping: SKIPPED")

        # Predictions summary
        predictions = self.results.get('predictions', {})
        if 'error' in predictions:
            self.log(f"Predictions: FAILED - {predictions['error']}", "ERROR")
        elif predictions:
            self.log(f"Predictions: {predictions.get('total', 0)} total")
            for sport, count in predictions.get('by_sport', {}).items():
                self.log(f"  - {sport.upper()}: {count}")
        else:
            self.log("Predictions: NO DATA")

        # Grading summary
        grading = self.results.get('grading', {})
        if 'error' in grading:
            self.log(f"Grading: FAILED - {grading['error']}", "ERROR")
        elif grading:
            self.log(f"Grading: {grading.get('total', 0)} predictions graded")
        else:
            self.log("Grading: NO DATA")

        self.log("=" * 70)

    async def run(self):
        """Run complete workflow"""
        start_time = datetime.now()

        self.log("=" * 70)
        self.log("DAILY MULTI-SPORT PLAYER PROPS WORKFLOW")
        self.log("=" * 70)
        self.log(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"Sports: {', '.join(self.sports)}")
        self.log(f"Database: {self.db_path}")
        self.log("")

        # Step 1: Scrape props
        await self.run_scraping()

        # Step 2: Generate predictions
        self.run_predictions()

        # Step 3: Grade previous predictions
        self.run_grading()

        # Generate summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        self.generate_summary()
        self.log(f"Workflow completed in {duration:.1f} seconds")
        self.log("")

        return self.results


async def main():
    parser = argparse.ArgumentParser(
        description='Run daily multi-sport player props workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python backend/run_daily_props_workflow_multi_sport.py --sports nba
  python backend/run_daily_props_workflow_multi_sport.py --sports all
  python backend/run_daily_props_workflow_multi_sport.py --sports nba,nfl,nhl
  python backend/run_daily_props_workflow_multi_sport.py --sports nba --skip-scrape
        """
    )

    parser.add_argument(
        '--sports',
        type=str,
        default='nba',
        help='Sports to process (comma-separated: nba,nhl,nfl,ncaab,ncaaf or "all")'
    )

    parser.add_argument(
        '--db',
        type=str,
        default='data/player_props.db',
        help='Database path (default: data/player_props.db)'
    )

    parser.add_argument(
        '--skip-scrape',
        action='store_true',
        help='Skip scraping step (use existing props data)'
    )

    args = parser.parse_args()

    # Parse sports list
    if args.sports.lower() == 'all':
        sports = ['nba', 'nfl', 'nhl', 'ncaab', 'ncaaf']
    else:
        sports = [s.strip().lower() for s in args.sports.split(',')]

    # Validate sports
    valid_sports = ['nba', 'nfl', 'nhl', 'ncaab', 'ncaaf', 'mlb']
    for sport in sports:
        if sport not in valid_sports:
            print(f"ERROR: Invalid sport '{sport}'. Valid options: {', '.join(valid_sports)}")
            sys.exit(1)

    # Run workflow
    workflow = DailyPropsWorkflow(
        sports=sports,
        db_path=args.db,
        skip_scrape=args.skip_scrape
    )

    try:
        results = await workflow.run()

        # Exit with error if critical failures
        if 'error' in results.get('predictions', {}):
            print("\n[ERROR] Workflow failed - predictions error")
            sys.exit(1)

        print("\n[SUCCESS] Workflow completed successfully")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Workflow cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
