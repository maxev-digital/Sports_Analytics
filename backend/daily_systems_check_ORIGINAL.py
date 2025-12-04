#!/usr/bin/env python3
"""
Daily Systems Check for Max EV Sports ML System

Runs comprehensive health check of all system components:
- ML models (76 total across 3 bet types)
- Data scrapers and pipelines
- Database integrity
- Prediction generation
- Feature dimension validation
- Log file analysis

Designed to run at 11:00 PM CST (after all daily operations)
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import glob
import json

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"   {text}")

def check_model_files():
    """Check that all 76 models exist"""
    print_header("MODEL FILES CHECK")

    base_path = Path("/root/sporttrader/backend/ml/models")

    # Expected models
    sports = ['nba', 'ncaab', 'nhl', 'nfl', 'ncaaf']

    # Totals models (7 per sport = 35)
    totals_models = [
        'xgboost_totals_latest.joblib',
        'lightgbm_totals_latest.joblib',
        'random_forest_totals_latest.joblib',
        'linear_regression_totals_latest.joblib',
        'pytorch_tabular_totals_latest.pt',
        'catboost_totals_latest.cbm',
        'neural_ensemble_totals_latest.pt'
    ]

    # Spreads models (4 per sport = 20)
    spreads_models = [
        'xgboost_spreads_latest.joblib',
        'lightgbm_spreads_latest.joblib',
        'random_forest_spreads_latest.joblib',
        'linear_regression_spreads_latest.joblib'
    ]

    # Moneyline models (4 per sport = 20, NBA has extra)
    moneyline_models = [
        'xgboost_moneyline_latest.joblib',
        'lightgbm_moneyline_latest.joblib',
        'random_forest_moneyline_latest.joblib',
        'logistic_regression_moneyline_latest.joblib'
    ]

    totals_found = 0
    spreads_found = 0
    moneyline_found = 0
    missing = []

    # Check totals
    for sport in sports:
        for model in totals_models:
            path = base_path / f"{sport}_{model}"
            if path.exists():
                totals_found += 1
            else:
                missing.append(f"{sport}_{model}")

    # Check spreads
    for sport in sports:
        for model in spreads_models:
            path = base_path / f"{sport}_{model}"
            if path.exists():
                spreads_found += 1
            else:
                missing.append(f"{sport}_{model}")

    # Check moneyline
    for sport in sports:
        for model in moneyline_models:
            path = base_path / f"{sport}_{model}"
            if path.exists():
                moneyline_found += 1
            else:
                missing.append(f"{sport}_{model}")

    # Also check for NBA's extra classifier
    nba_classifier = base_path / "nba_random_forest_classifier_moneyline_latest.joblib"
    if nba_classifier.exists():
        moneyline_found += 1

    total_found = totals_found + spreads_found + moneyline_found

    print_info(f"Totals Models: {totals_found}/35")
    print_info(f"Spreads Models: {spreads_found}/20")
    print_info(f"Moneyline Models: {moneyline_found}/21")
    print_info(f"Total: {total_found}/76")

    if total_found == 76:
        print_success("All 76 models present")
    elif total_found >= 70:
        print_warning(f"Missing {76-total_found} models")
        for m in missing[:5]:
            print_info(f"  Missing: {m}")
    else:
        print_error(f"Only {total_found}/76 models found")
        for m in missing[:10]:
            print_info(f"  Missing: {m}")

    return total_found == 76

def check_database():
    """Check database integrity and recent predictions"""
    print_header("DATABASE CHECK")

    db_path = "/root/sporttrader/backend/ml/predictions.db"

    if not Path(db_path).exists():
        print_error("Database not found!")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Total predictions
        cursor.execute("SELECT COUNT(*) FROM predictions")
        total_preds = cursor.fetchone()[0]
        print_info(f"Total predictions in DB: {total_preds:,}")

        # Recent predictions (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) FROM predictions
            WHERE created_at >= date('now', '-7 days')
        """)
        recent_preds = cursor.fetchone()[0]
        print_info(f"Predictions (last 7 days): {recent_preds}")

        # Today's predictions
        cursor.execute("""
            SELECT COUNT(*) FROM predictions
            WHERE date(created_at) = date('now')
        """)
        today_preds = cursor.fetchone()[0]
        print_info(f"Predictions today: {today_preds}")

        # Check for NULL predicted_values (indicates failure)
        cursor.execute("""
            SELECT COUNT(*) FROM predictions
            WHERE predicted_value IS NULL
            AND created_at >= date('now', '-7 days')
        """)
        null_preds = cursor.fetchone()[0]

        if null_preds > 0:
            print_warning(f"{null_preds} predictions with NULL values (last 7 days)")
        else:
            print_success("No NULL prediction values")

        # Predictions by sport (last 7 days)
        print_info("\nPredictions by sport (last 7 days):")
        cursor.execute("""
            SELECT sport, COUNT(*) FROM predictions
            WHERE created_at >= date('now', '-7 days')
            GROUP BY sport
            ORDER BY COUNT(*) DESC
        """)
        for sport, count in cursor.fetchall():
            print_info(f"  {sport}: {count}")

        conn.close()

        if today_preds > 0:
            print_success("Database operational with recent predictions")
            return True
        else:
            print_warning("No predictions generated today")
            return False

    except Exception as e:
        print_error(f"Database check failed: {e}")
        return False

def check_scrapers():
    """Check if scrapers ran successfully"""
    print_header("DATA SCRAPER CHECK")

    log_file = "/root/sporttrader/backend/logs/cron_scraper.log"

    if not Path(log_file).exists():
        print_error("Scraper log file not found")
        return False

    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()[-50:]  # Last 50 lines

        # Check for today's date
        today = datetime.now().strftime("%Y-%m-%d")
        today_logs = [l for l in lines if today in l]

        if today_logs:
            print_info(f"Found {len(today_logs)} log entries for today")

            # Check for success indicators
            success_keywords = ['success', 'complete', 'finished', 'done']
            error_keywords = ['error', 'failed', 'exception', 'traceback']

            has_success = any(any(kw in l.lower() for kw in success_keywords) for l in today_logs)
            has_errors = any(any(kw in l.lower() for kw in error_keywords) for l in today_logs)

            if has_success and not has_errors:
                print_success("Scrapers appear to have run successfully")
                return True
            elif has_errors:
                print_warning("Errors detected in scraper logs")
                error_lines = [l.strip() for l in today_logs if any(kw in l.lower() for kw in error_keywords)]
                for line in error_lines[:3]:
                    print_info(f"  {line[:80]}...")
                return False
            else:
                print_warning("Unable to determine scraper status")
                return True  # Assume OK if no explicit errors
        else:
            print_warning("No scraper logs found for today")
            return False

    except Exception as e:
        print_error(f"Failed to check scraper logs: {e}")
        return False

def check_ml_predictions():
    """Check if ML predictions ran successfully"""
    print_header("ML PREDICTIONS CHECK")

    log_file = "/root/sporttrader/backend/logs/ml_predictions_ENHANCED.log"

    if not Path(log_file).exists():
        print_error("ML predictions log file not found")
        return False

    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()[-100:]  # Last 100 lines

        today = datetime.now().strftime("%Y-%m-%d")
        today_logs = [l for l in lines if today in l]

        if today_logs:
            print_info(f"Found {len(today_logs)} log entries for today")

            # Check for prediction generation
            pred_keywords = ['prediction', 'generated', 'saved']
            error_keywords = ['error', 'failed', 'exception', 'traceback', 'feature shape mismatch']

            has_predictions = any(any(kw in l.lower() for kw in pred_keywords) for l in today_logs)
            has_errors = any(any(kw in l.lower() for kw in error_keywords) for l in today_logs)

            if has_predictions and not has_errors:
                print_success("ML predictions generated successfully")
                return True
            elif has_errors:
                print_error("Errors detected in ML prediction logs")
                error_lines = [l.strip() for l in today_logs if any(kw in l.lower() for kw in error_keywords)]
                for line in error_lines[:5]:
                    print_info(f"  {line[:100]}...")
                return False
            else:
                print_warning("ML prediction status unclear")
                return False
        else:
            print_warning("No ML prediction logs found for today")
            return False

    except Exception as e:
        print_error(f"Failed to check ML prediction logs: {e}")
        return False

def check_kenpom():
    """Check if KenPom scraper ran"""
    print_header("KENPOM SCRAPER CHECK")

    log_file = "/root/sporttrader/backend/logs/kenpom_scraper.log"

    if not Path(log_file).exists():
        print_warning("KenPom log file not found")
        return True  # Not critical

    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()[-30:]

        today = datetime.now().strftime("%Y-%m-%d")
        today_logs = [l for l in lines if today in l]

        if today_logs:
            has_errors = any('error' in l.lower() or 'failed' in l.lower() for l in today_logs)

            if not has_errors:
                print_success("KenPom scraper ran successfully")
                return True
            else:
                print_warning("KenPom scraper encountered errors")
                return False
        else:
            print_info("No KenPom logs for today (may not run every day)")
            return True

    except Exception as e:
        print_warning(f"Could not check KenPom logs: {e}")
        return True

def check_feature_dimensions():
    """Check if feature dimensions are correctly aligned"""
    print_header("FEATURE DIMENSION CHECK")

    try:
        import joblib
        import numpy as np

        models_path = Path("/root/sporttrader/backend/ml/models")

        sports_features = {
            'nba': 60,
            'ncaab': 14,
            'nhl': 27,
            'nfl': 30,
            'ncaaf': 30
        }

        all_ok = True

        for sport, expected in sports_features.items():
            model_path = models_path / f"{sport}_xgboost_totals_latest.joblib"

            if model_path.exists():
                model = joblib.load(model_path)
                actual = model.n_features_in_

                if actual == expected:
                    print_info(f"{sport.upper()}: {actual} features ✓")
                else:
                    print_warning(f"{sport.upper()}: Expected {expected}, got {actual}")
                    all_ok = False
            else:
                print_warning(f"{sport.upper()}: Model not found")
                all_ok = False

        if all_ok:
            print_success("All feature dimensions correct")
        else:
            print_warning("Feature dimension mismatches detected")

        return all_ok

    except Exception as e:
        print_error(f"Feature dimension check failed: {e}")
        return False

def check_disk_space():
    """Check available disk space"""
    print_header("DISK SPACE CHECK")

    try:
        import shutil

        stat = shutil.disk_usage("/root/sporttrader")

        total_gb = stat.total / (1024**3)
        used_gb = stat.used / (1024**3)
        free_gb = stat.free / (1024**3)
        used_pct = (stat.used / stat.total) * 100

        print_info(f"Total: {total_gb:.1f} GB")
        print_info(f"Used: {used_gb:.1f} GB ({used_pct:.1f}%)")
        print_info(f"Free: {free_gb:.1f} GB")

        if free_gb > 10:
            print_success(f"Sufficient disk space ({free_gb:.1f} GB free)")
            return True
        elif free_gb > 5:
            print_warning(f"Low disk space ({free_gb:.1f} GB free)")
            return True
        else:
            print_error(f"Critical disk space ({free_gb:.1f} GB free)")
            return False

    except Exception as e:
        print_warning(f"Could not check disk space: {e}")
        return True

def generate_summary_report(results):
    """Generate final summary report"""
    print_header("DAILY SYSTEMS CHECK SUMMARY")

    total_checks = len(results)
    passed = sum(results.values())
    failed = total_checks - passed

    print_info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S CST')}")
    print_info(f"Total Checks: {total_checks}")
    print_info(f"Passed: {passed}")
    print_info(f"Failed: {failed}")
    print()

    for check, status in results.items():
        status_icon = "✅" if status else "❌"
        status_text = "PASS" if status else "FAIL"
        color = Colors.GREEN if status else Colors.RED
        print(f"{color}{status_icon} {check}: {status_text}{Colors.END}")

    print()

    if failed == 0:
        print_success("ALL SYSTEMS OPERATIONAL")
        return 0
    elif failed <= 2:
        print_warning(f"{failed} SYSTEMS NEED ATTENTION")
        return 1
    else:
        print_error(f"{failed} SYSTEMS FAILING - IMMEDIATE ACTION REQUIRED")
        return 2

def main():
    """Run all systems checks"""
    print_header("MAX EV SPORTS - DAILY SYSTEMS CHECK")
    print_info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S CST')}")

    results = {}

    # Run all checks
    results['Model Files'] = check_model_files()
    results['Database'] = check_database()
    results['Data Scrapers'] = check_scrapers()
    results['ML Predictions'] = check_ml_predictions()
    results['KenPom Scraper'] = check_kenpom()
    results['Feature Dimensions'] = check_feature_dimensions()
    results['Disk Space'] = check_disk_space()

    # Generate summary
    exit_code = generate_summary_report(results)

    print()
    print_info(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S CST')}")
    print()

    return exit_code

if __name__ == "__main__":
    sys.exit(main())
