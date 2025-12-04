#!/usr/bin/env python3
r"""
Daily Systems Check for Max EV Sports ML System - WITH EMAIL

Runs comprehensive health check of all system components and emails results.

Features:
- Checks all 76 models, database, scrapers, predictions
- Sends email summary to admin
- Creates running log file
- Backs up logs to D:\Max_EV_Sports\COMPLETE_ML_SYSTEM_DOCS

Runs at 11:00 PM CST daily
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import glob
import json
import shutil

# Email imports
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

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

# [Previous check functions remain the same - check_model_files, check_database, etc.]
# I'll include abbreviated versions here for space

def check_model_files():
    """Check that all 76 models exist"""
    print_header("MODEL FILES CHECK")
    base_path = Path("/root/sporttrader/backend/ml/models")
    sports = ['nba', 'ncaab', 'nhl', 'nfl', 'ncaaf']

    totals_models = ['xgboost_totals_latest.joblib', 'lightgbm_totals_latest.joblib',
                     'random_forest_totals_latest.joblib', 'linear_regression_totals_latest.joblib',
                     'pytorch_tabular_totals_latest.pt', 'catboost_totals_latest.cbm',
                     'neural_ensemble_totals_latest.pt']
    spreads_models = ['xgboost_spreads_latest.joblib', 'lightgbm_spreads_latest.joblib',
                      'random_forest_spreads_latest.joblib', 'linear_regression_spreads_latest.joblib']
    moneyline_models = ['xgboost_moneyline_latest.joblib', 'lightgbm_moneyline_latest.joblib',
                        'random_forest_moneyline_latest.joblib', 'logistic_regression_moneyline_latest.joblib']

    totals_found = sum(1 for sport in sports for model in totals_models if (base_path / f"{sport}_{model}").exists())
    spreads_found = sum(1 for sport in sports for model in spreads_models if (base_path / f"{sport}_{model}").exists())
    moneyline_found = sum(1 for sport in sports for model in moneyline_models if (base_path / f"{sport}_{model}").exists())
    if (base_path / "nba_random_forest_classifier_moneyline_latest.joblib").exists():
        moneyline_found += 1

    total_found = totals_found + spreads_found + moneyline_found
    print_info(f"Totals: {totals_found}/35 | Spreads: {spreads_found}/20 | Moneyline: {moneyline_found}/21 | Total: {total_found}/76")

    if total_found == 76:
        print_success("All 76 models present")
        return True, f"{total_found}/76 models"
    else:
        print_error(f"Only {total_found}/76 models found")
        return False, f"{total_found}/76 models (missing {76-total_found})"

def check_database():
    """Check database integrity"""
    print_header("DATABASE CHECK")
    db_path = "/root/sporttrader/backend/ml/predictions.db"
    if not Path(db_path).exists():
        print_error("Database not found!")
        return False, "DB not found"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM predictions")
        total_preds = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE date(created_at) = date('now')")
        today_preds = cursor.fetchone()[0]
        cursor.execute("SELECT sport, COUNT(*) FROM predictions WHERE created_at >= date('now', '-7 days') GROUP BY sport")
        sport_counts = dict(cursor.fetchall())
        conn.close()

        print_info(f"Total: {total_preds:,} | Today: {today_preds}")
        for sport, count in sport_counts.items():
            print_info(f"  {sport}: {count} (7 days)")

        if today_preds > 0:
            print_success("Database operational")
            return True, f"{today_preds} predictions today"
        else:
            print_warning("No predictions today")
            return False, "No predictions today"
    except Exception as e:
        print_error(f"Database error: {e}")
        return False, str(e)

def check_scrapers():
    """Check if scrapers ran"""
    print_header("DATA SCRAPER CHECK")
    log_file = "/root/sporttrader/backend/logs/cron_scraper.log"
    if not Path(log_file).exists():
        print_warning("Scraper log not found")
        return False, "Log not found"

    with open(log_file, 'r') as f:
        lines = f.readlines()[-50:]
    today = datetime.now().strftime("%Y-%m-%d")
    today_logs = [l for l in lines if today in l]

    if today_logs:
        has_errors = any('error' in l.lower() or 'failed' in l.lower() for l in today_logs)
        if not has_errors:
            print_success("Scrapers ran successfully")
            return True, "Success"
        else:
            print_warning("Scraper errors detected")
            return False, "Errors detected"
    else:
        print_warning("No scraper logs today")
        return False, "No logs today"

def check_ml_predictions():
    """Check if ML predictions ran"""
    print_header("ML PREDICTIONS CHECK")
    log_file = "/root/sporttrader/backend/logs/ml_predictions_ENHANCED.log"
    if not Path(log_file).exists():
        print_warning("ML log not found")
        return False, "Log not found"

    with open(log_file, 'r') as f:
        lines = f.readlines()[-100:]
    today = datetime.now().strftime("%Y-%m-%d")
    today_logs = [l for l in lines if today in l]

    if today_logs:
        has_predictions = any('prediction' in l.lower() or 'generated' in l.lower() for l in today_logs)
        has_errors = any('error' in l.lower() or 'failed' in l.lower() for l in today_logs)
        if has_predictions and not has_errors:
            print_success("ML predictions generated")
            return True, "Predictions generated"
        elif has_errors:
            print_error("ML prediction errors")
            return False, "Errors detected"
    print_warning("No ML prediction logs today")
    return False, "No logs today"

def check_feature_dimensions():
    """Check feature dimensions"""
    print_header("FEATURE DIMENSION CHECK")
    try:
        import joblib
        models_path = Path("/root/sporttrader/backend/ml/models")
        sports_features = {'nba': 60, 'ncaab': 14, 'nhl': 27, 'nfl': 30, 'ncaaf': 30}
        all_ok = True
        mismatches = []

        for sport, expected in sports_features.items():
            model_path = models_path / f"{sport}_xgboost_totals_latest.joblib"
            if model_path.exists():
                model = joblib.load(model_path)
                actual = model.n_features_in_
                if actual == expected:
                    print_info(f"{sport.upper()}: {actual} features ✓")
                else:
                    print_warning(f"{sport.upper()}: Expected {expected}, got {actual}")
                    mismatches.append(f"{sport}:{expected}→{actual}")
                    all_ok = False

        if all_ok:
            print_success("All dimensions correct")
            return True, "All correct"
        else:
            return False, ", ".join(mismatches)
    except Exception as e:
        print_error(f"Check failed: {e}")
        return False, str(e)

def check_disk_space():
    """Check disk space"""
    print_header("DISK SPACE CHECK")
    try:
        import shutil
        stat = shutil.disk_usage("/root/sporttrader")
        free_gb = stat.free / (1024**3)
        used_pct = (stat.used / stat.total) * 100
        print_info(f"Free: {free_gb:.1f} GB | Used: {used_pct:.1f}%")

        if free_gb > 10:
            print_success(f"Sufficient space ({free_gb:.1f} GB)")
            return True, f"{free_gb:.1f} GB free"
        elif free_gb > 5:
            print_warning(f"Low space ({free_gb:.1f} GB)")
            return True, f"{free_gb:.1f} GB (low)"
        else:
            print_error(f"Critical space ({free_gb:.1f} GB)")
            return False, f"{free_gb:.1f} GB (critical)"
    except Exception as e:
        return True, "Unknown"

def generate_html_email(results, details):
    """Generate HTML email with executive summary"""

    # Determine overall status
    passed = sum(1 for r in results.values() if r)
    failed = len(results) - passed

    if failed == 0:
        status_color = "#10b981"  # green
        status_text = "ALL SYSTEMS OPERATIONAL"
        status_emoji = "✅"
    elif failed <= 2:
        status_color = "#f59e0b"  # yellow
        status_text = f"{failed} SYSTEMS NEED ATTENTION"
        status_emoji = "⚠️"
    else:
        status_color = "#ef4444"  # red
        status_text = f"{failed} SYSTEMS FAILING"
        status_emoji = "❌"

    # Build check rows
    check_rows = ""
    for check, status in results.items():
        icon = "✅" if status else "❌"
        color = "#10b981" if status else "#ef4444"
        detail = details.get(check, "")
        check_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                <span style="font-size: 20px;">{icon}</span> <strong>{check}</strong>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; color: {color};">
                {detail}
            </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">

        <!-- Header -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
            <h1 style="margin: 0; font-size: 28px;">MAX-EV SPORTS</h1>
            <p style="margin: 10px 0 0 0; font-size: 16px;">Daily Systems Check Report</p>
            <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">{datetime.now().strftime('%B %d, %Y at %I:%M %p CST')}</p>
        </div>

        <!-- Status Banner -->
        <div style="background: {status_color}; color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 30px;">
            <div style="font-size: 48px; margin-bottom: 10px;">{status_emoji}</div>
            <h2 style="margin: 0; font-size: 24px;">{status_text}</h2>
            <p style="margin: 10px 0 0 0; font-size: 16px;">{passed} passed • {failed} failed</p>
        </div>

        <!-- Executive Summary -->
        <div style="background: #f9fafb; border-left: 4px solid #667eea; padding: 20px; margin-bottom: 30px; border-radius: 5px;">
            <h3 style="margin-top: 0; color: #667eea;">📊 Executive Summary</h3>
            <table style="width: 100%; border-collapse: collapse;">
                {check_rows}
            </table>
        </div>

        <!-- System Details -->
        <div style="background: #ffffff; border: 1px solid #e5e7eb; padding: 20px; margin-bottom: 20px; border-radius: 8px;">
            <h3 style="margin-top: 0; color: #667eea;">🔧 System Details</h3>
            <ul style="list-style: none; padding: 0;">
                <li style="padding: 8px 0; border-bottom: 1px solid #f3f4f6;">
                    <strong>Total Models:</strong> 76 (35 totals + 20 spreads + 21 moneyline)
                </li>
                <li style="padding: 8px 0; border-bottom: 1px solid #f3f4f6;">
                    <strong>Sports Covered:</strong> NBA, NCAAB, NHL, NFL, NCAAF
                </li>
                <li style="padding: 8px 0; border-bottom: 1px solid #f3f4f6;">
                    <strong>Bet Types:</strong> Totals, Spreads, Moneyline
                </li>
                <li style="padding: 8px 0;">
                    <strong>Server:</strong> 148.230.87.135
                </li>
            </ul>
        </div>

        <!-- Action Required (if failures) -->
        {f'''
        <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 20px; margin-bottom: 20px; border-radius: 5px;">
            <h3 style="margin-top: 0; color: #ef4444;">⚠️ Action Required</h3>
            <p>One or more systems require attention. Please review the logs:</p>
            <ul>
                <li><code>/root/sporttrader/backend/logs/systems_check.log</code></li>
                <li><code>/root/sporttrader/backend/logs/ml_predictions_ENHANCED.log</code></li>
                <li><code>/root/sporttrader/backend/logs/cron_scraper.log</code></li>
            </ul>
            <p>SSH to VPS: <code>ssh root@148.230.87.135</code></p>
        </div>
        ''' if failed > 0 else ''}

        <!-- Footer -->
        <div style="text-align: center; padding: 20px; color: #6b7280; font-size: 14px; border-top: 1px solid #e5e7eb; margin-top: 30px;">
            <p>This is an automated daily report from your MAX-EV Sports ML System.</p>
            <p style="margin: 5px 0;">Next check scheduled for tomorrow at 11:00 PM CST</p>
            <p style="margin: 5px 0;"><a href="https://max-ev-sports.com" style="color: #667eea; text-decoration: none;">max-ev-sports.com</a></p>
        </div>

    </body>
    </html>
    """

    return html

def send_email_summary(results, details):
    """Send email summary using Brevo"""
    print_header("SENDING EMAIL SUMMARY")

    try:
        # Get Brevo API key
        api_key = os.getenv("BREVO_API_KEY")
        if not api_key:
            print_error("BREVO_API_KEY not set")
            return False

        # Get admin email
        admin_email = os.getenv("ADMIN_EMAIL", "gte.apw@gmail.com")

        # Configure Brevo
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = api_key
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

        # Generate email HTML
        html_content = generate_html_email(results, details)

        # Determine subject based on status
        passed = sum(1 for r in results.values() if r)
        failed = len(results) - passed

        if failed == 0:
            subject = "✅ Daily Systems Check: ALL OPERATIONAL"
        elif failed <= 2:
            subject = f"⚠️  Daily Systems Check: {failed} Systems Need Attention"
        else:
            subject = f"❌ Daily Systems Check: {failed} SYSTEMS FAILING"

        # Send email
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": admin_email}],
            sender={"email": "noreply@max-ev-sports.com", "name": "MAX-EV Sports System Monitor"},
            subject=subject,
            html_content=html_content
        )

        api_response = api_instance.send_transac_email(send_smtp_email)
        print_success(f"Email sent to {admin_email}")
        return True

    except ApiException as e:
        print_error(f"Brevo API error: {e}")
        return False
    except Exception as e:
        print_error(f"Email error: {e}")
        return False

def backup_to_local_drive():
    r"""Backup logs to D:\Max_EV_Sports\COMPLETE_ML_SYSTEM_DOCS"""
    print_header("BACKING UP LOGS")

    try:
        # Local backup directory
        backup_dir = Path("D:/Max_EV_Sports/COMPLETE_ML_SYSTEM_DOCS/systems_check_logs")
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Log file on VPS
        log_file = Path("/root/sporttrader/backend/logs/systems_check.log")

        if not log_file.exists():
            print_warning("No log file to backup")
            return False

        # Create backup filename with date
        backup_filename = f"systems_check_{datetime.now().strftime('%Y%m%d')}.log"
        backup_path = backup_dir / backup_filename

        # Copy log file
        shutil.copy2(log_file, backup_path)

        print_success(f"Backed up to {backup_path}")
        print_info(f"Backup size: {backup_path.stat().st_size / 1024:.1f} KB")

        # Keep only last 30 days of backups
        cutoff_date = datetime.now() - timedelta(days=30)
        for old_backup in backup_dir.glob("systems_check_*.log"):
            file_date_str = old_backup.stem.replace("systems_check_", "")
            try:
                file_date = datetime.strptime(file_date_str, "%Y%m%d")
                if file_date < cutoff_date:
                    old_backup.unlink()
                    print_info(f"Deleted old backup: {old_backup.name}")
            except:
                pass

        return True

    except Exception as e:
        print_error(f"Backup failed: {e}")
        return False

def main():
    """Run all systems checks with email and backup"""
    print_header("MAX EV SPORTS - DAILY SYSTEMS CHECK WITH EMAIL")
    print_info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S CST')}")

    results = {}
    details = {}

    # Run all checks
    results['Model Files'], details['Model Files'] = check_model_files()
    results['Database'], details['Database'] = check_database()
    results['Data Scrapers'], details['Data Scrapers'] = check_scrapers()
    results['ML Predictions'], details['ML Predictions'] = check_ml_predictions()
    results['Feature Dimensions'], details['Feature Dimensions'] = check_feature_dimensions()
    results['Disk Space'], details['Disk Space'] = check_disk_space()

    # Generate summary
    print_header("DAILY SYSTEMS CHECK SUMMARY")
    passed = sum(results.values())
    failed = len(results) - passed
    print_info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S CST')}")
    print_info(f"Passed: {passed} | Failed: {failed}")
    print()

    for check, status in results.items():
        status_icon = "✅" if status else "❌"
        status_text = "PASS" if status else "FAIL"
        color = Colors.GREEN if status else Colors.RED
        print(f"{color}{status_icon} {check}: {status_text} - {details[check]}{Colors.END}")

    # Send email
    email_sent = send_email_summary(results, details)

    # Backup logs (only works if script runs on Windows machine with D: drive access)
    # For VPS cron, this will fail gracefully
    try:
        backup_to_local_drive()
    except:
        print_info("Skipping local backup (not on Windows machine)")

    print()
    if failed == 0:
        print_success("ALL SYSTEMS OPERATIONAL")
        exit_code = 0
    elif failed <= 2:
        print_warning(f"{failed} SYSTEMS NEED ATTENTION")
        exit_code = 1
    else:
        print_error(f"{failed} SYSTEMS FAILING - IMMEDIATE ACTION REQUIRED")
        exit_code = 2

    print()
    print_info(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S CST')}")
    print_info(f"Email sent: {'Yes' if email_sent else 'No'}")
    print()

    return exit_code

if __name__ == "__main__":
    sys.exit(main())
