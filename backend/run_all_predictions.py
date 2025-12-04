#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path

scripts = [
    "predict_nba_totals.py",
    "predict_nba_spreads.py",
    "predict_nba_moneyline.py",
    "predict_nhl_totals.py",
    "predict_nhl_spreads.py",
    "predict_nhl_moneyline.py",
    "predict_nfl_totals.py",
    "predict_nfl_spreads.py",
    "predict_nfl_moneyline.py",
    "predict_ncaaf_totals.py",
    "predict_ncaaf_spreads.py",
    "predict_ncaaf_moneyline.py",
    "predict_ncaab_totals.py",
]

print("RUNNING ALL PREDICTIONS")
print("="*60)
success = 0
failed = []

for script in scripts:
    print(f"Running {script}...")
    try:
        result = subprocess.run(
            [sys.executable, script],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            success += 1
            print(result.stdout)
        else:
            failed.append(script)
            print(f"FAILED: {result.stderr}")
    except Exception as e:
        failed.append(script)
        print(f"ERROR: {e}")

print(f"Success: {success}/{len(scripts)}")
if failed:
    print(f"Failed: {failed}")