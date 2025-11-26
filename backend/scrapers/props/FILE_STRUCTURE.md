# Player Props ML - File Structure and Verification Guide

**Last Updated:** November 14, 2025

This document shows where all files will be located as we progress through the 8-week implementation plan.

---

## CURRENT FILE STRUCTURE (Week 2)

```
C:\Users\nashr\backend\scrapers\props\
├── README.md                          # Status overview (YOU ARE HERE)
├── IMPLEMENTATION_PLAN.md             # Full 8-week roadmap
├── FILE_STRUCTURE.md                  # This file - verification guide
├── balldontlie_client.py              # ✅ WORKING - NBA player stats API
├── results_tracker.py                 # ✅ WORKING - Grades props with real stats
└── daily_props_scraper.py             # ✅ WORKING - Fetches props lines

D:\backend\data\
├── player_props.db                    # ✅ SQLite database (176 graded props)
├── raw\
│   └── props\
│       ├── nba_props_lines\           # Daily props lines
│       └── player_stats\              # Cached player stats
├── predictions\
│   └── props\                         # (Will store daily predictions - Week 7)
└── models\
    └── props\                         # (Will store trained models - Week 5)

C:\Users\nashr\
└── PROPS_IMPLEMENTATION_STATUS.md     # ✅ Current status tracker
```

---

## VERIFICATION COMMANDS

### Check Database Status
```bash
# Count graded props
sqlite3 D:\backend\data\player_props.db "SELECT COUNT(*) as graded_props FROM player_props_results;"

# Count by date
sqlite3 D:\backend\data\player_props.db "SELECT date, COUNT(*) as count FROM player_props_results GROUP BY date ORDER BY date DESC LIMIT 10;"

# Check latest graded props
sqlite3 D:\backend\data\player_props.db "SELECT player_name, prop_type, market_line, actual_value, result FROM player_props_results ORDER BY date DESC LIMIT 20;"
```

### Check BallDontLie API
```bash
# Test API connection
python -c "from backend.scrapers.props.balldontlie_client import BallDontLieClient; client = BallDontLieClient(); print(client.get_player_by_name('LeBron James'))"
```

### Check Files
```bash
# List props scraper files
ls -la backend/scrapers/props/

# Check database size
ls -lh D:/backend/data/player_props.db
```

---

## PROGRESS MILESTONES

### Week 1-2: Data Infrastructure (CURRENT)
- [x] Database schema created
- [x] BallDontLie API client integrated
- [x] Daily props scraper built
- [x] Results tracker built and tested
- [x] 176 props graded (as of 2025-11-13)
- [ ] 1000+ props graded (BLOCKER for Week 3)

**Verification:**
```bash
sqlite3 D:\backend\data\player_props.db "SELECT COUNT(*) FROM player_props_results;"
# Should show 176+ and growing daily
```

### Week 3-4: Feature Engineering (NOT STARTED)
**Files that will be created:**
```
backend/scrapers/props/
├── feature_engineer.py                # NBA props feature extraction (50+ features)
├── matchup_analyzer.py                # Opponent defensive stats
└── trends_analyzer.py                 # Recent form, splits, streaks
```

**Verification when built:**
```bash
# Test feature extraction
python backend/scrapers/props/feature_engineer.py --test
```

### Week 5-6: ML Model Training (NOT STARTED)
**Files that will be created:**
```
backend/models/props/
├── nba_props_trainer.py               # Train XGBoost, LightGBM, RF models
├── points_model.pkl                   # Trained points model
├── rebounds_model.pkl                 # Trained rebounds model
├── assists_model.pkl                  # Trained assists model
├── threes_model.pkl                   # Trained threes model
├── blocks_model.pkl                   # Trained blocks model
├── steals_model.pkl                   # Trained steals model
└── ensemble_model.pkl                 # Ensemble of all models
```

**Verification when built:**
```bash
# Check model files exist
ls -la backend/models/props/*.pkl

# Test model prediction
python backend/models/props/nba_props_trainer.py --predict --player "Giannis Antetokounmpo" --prop "points"
```

### Week 7-8: Production Integration (NOT STARTED)
**Files that will be created:**
```
backend/
├── run_daily_props_workflow.py        # Daily prediction workflow
└── routes/
    └── props_predictions.py           # API endpoint for daily predictions

frontend/src/pages/
└── PropsPerformance.tsx               # Props performance dashboard (ALREADY EXISTS)
```

**Verification when built:**
```bash
# Run daily workflow
python backend/run_daily_props_workflow.py

# Check predictions generated
ls -la D:/backend/data/predictions/props/nba_props_*.csv

# Test API endpoint
curl http://localhost:8000/api/props-predictions/today
```

---

## QUICK VERIFICATION SCRIPT

Save this as `verify_props_progress.py`:

```python
#!/usr/bin/env python3
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("D:/backend/data/player_props.db")

print("=" * 60)
print("PLAYER PROPS ML SYSTEM - PROGRESS CHECK")
print("=" * 60)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Check database
if DB_PATH.exists():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Count graded props
    cursor.execute("SELECT COUNT(*) FROM player_props_results")
    graded = cursor.fetchone()[0]

    # Count by prop type
    cursor.execute("SELECT prop_type, COUNT(*) FROM player_props_results GROUP BY prop_type")
    by_type = cursor.fetchall()

    # Latest date
    cursor.execute("SELECT MAX(date) FROM player_props_results")
    latest_date = cursor.fetchone()[0]

    conn.close()

    print(f"✅ Database: FOUND")
    print(f"📊 Total Graded Props: {graded}")
    print(f"📅 Latest Data: {latest_date}")
    print(f"\nBreakdown by Prop Type:")
    for prop_type, count in by_type:
        print(f"  - {prop_type}: {count}")

    # Progress to 1000
    progress_pct = (graded / 1000) * 100
    print(f"\n📈 Progress to 1000 props: {progress_pct:.1f}%")
    print(f"   Need {1000 - graded} more props")

    # Estimate
    if graded >= 176:
        days_since_start = 1  # Started 2025-11-13
        props_per_day = graded / days_since_start if days_since_start > 0 else 0
        days_to_1000 = (1000 - graded) / props_per_day if props_per_day > 0 else 0
        print(f"   Est. {days_to_1000:.0f} days to reach 1000 (at {props_per_day:.0f} props/day)")
else:
    print("❌ Database: NOT FOUND")

print()

# Check files
files_to_check = {
    "BallDontLie Client": "backend/scrapers/props/balldontlie_client.py",
    "Results Tracker": "backend/scrapers/props/results_tracker.py",
    "Daily Scraper": "backend/scrapers/props/daily_props_scraper.py",
    "Feature Engineer": "backend/scrapers/props/feature_engineer.py",
    "Model Trainer": "backend/models/props/nba_props_trainer.py",
    "Daily Workflow": "backend/run_daily_props_workflow.py",
}

print("File Status:")
for name, path in files_to_check.items():
    if Path(path).exists():
        print(f"  ✅ {name}")
    else:
        print(f"  ❌ {name} (not built yet)")

print()
print("=" * 60)
```

**Run it:**
```bash
python verify_props_progress.py
```

---

## EXPECTED OUTPUT AT EACH STAGE

### Week 2 (NOW):
```
✅ Database: FOUND
📊 Total Graded Props: 176
📅 Latest Data: 2025-11-13

Breakdown by Prop Type:
  - points: 60
  - rebounds: 30
  - assists: 28
  - threes: 25
  - blocks: 18
  - steals: 15

📈 Progress to 1000 props: 17.6%
   Need 824 more props
   Est. 5-10 days to reach 1000 (at 80-150 props/day)

File Status:
  ✅ BallDontLie Client
  ✅ Results Tracker
  ✅ Daily Scraper
  ❌ Feature Engineer (not built yet)
  ❌ Model Trainer (not built yet)
  ❌ Daily Workflow (not built yet)
```

### Week 4 (Feature Engineering Complete):
```
✅ Database: FOUND
📊 Total Graded Props: 1200
📅 Latest Data: 2025-11-28

File Status:
  ✅ BallDontLie Client
  ✅ Results Tracker
  ✅ Daily Scraper
  ✅ Feature Engineer
  ❌ Model Trainer (not built yet)
  ❌ Daily Workflow (not built yet)
```

### Week 6 (Models Trained):
```
✅ Database: FOUND
📊 Total Graded Props: 2000+
📅 Latest Data: 2025-12-12

File Status:
  ✅ BallDontLie Client
  ✅ Results Tracker
  ✅ Daily Scraper
  ✅ Feature Engineer
  ✅ Model Trainer
  ✅ 6 Trained Models (points, rebounds, assists, threes, blocks, steals)
  ❌ Daily Workflow (not built yet)
```

### Week 8 (LAUNCH):
```
✅ Database: FOUND
📊 Total Graded Props: 3000+
📅 Latest Data: 2025-12-26

File Status:
  ✅ BallDontLie Client
  ✅ Results Tracker
  ✅ Daily Scraper
  ✅ Feature Engineer
  ✅ Model Trainer
  ✅ 6 Trained Models
  ✅ Daily Workflow
  ✅ API Endpoints
  ✅ Frontend Dashboard
```

---

## SUMMARY

**Current Status:** Week 2 of 8 - Data Collection Phase
**Blocker:** Need 1000+ graded props before training models (currently 176)
**Next Milestone:** Reach 1000 props (est. 2-4 weeks)
**Files Location:** All props code in `backend/scrapers/props/`
**Database:** `D:\backend\data\player_props.db`

**To verify progress at any time:**
```bash
python verify_props_progress.py
```
