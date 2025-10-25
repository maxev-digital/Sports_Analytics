# Data Storage Guide

This document outlines where and how all betting data is stored in the system.

## Directory Structure

```
C:\Users\nashr\backend\data\
├── raw/                          # Raw scraped data (unprocessed)
│   ├── nba/                      # NBA team stats from official API
│   ├── ncaab/                    # NCAA Basketball (KenPom data)
│   └── odds/                     # Betting odds from The Odds API
│
├── historical/                   # Historical game data
│   └── h2h/                      # Head-to-head matchup history
│       ├── nba/                  # NBA H2H data (JSON files)
│       ├── nhl/                  # NHL H2H data
│       ├── nfl/                  # NFL H2H data
│       └── mlb/                  # MLB H2H data
│
├── predictions/                  # Generated predictions
│   ├── nba_predictions_latest.csv
│   ├── ncaab_predictions_latest.csv
│   └── [dated prediction files]
│
├── tracking/                     # Performance tracking
│   ├── predictions_log.csv      # All logged predictions
│   ├── results_log.csv          # Actual game results
│   └── performance_summary.csv  # Historical ROI/Win rates
│
├── processed/                    # Processed/cleaned data
│   └── nba/                      # Processed NBA stats
│
├── backtesting/                  # Historical backtest results
│   └── [backtest result files]
│
├── analysis/                     # Analysis outputs
│   └── [various analysis files]
│
└── team_name_mapping.json        # Team name standardization

```

## Data Types and Formats

### 1. Head-to-Head (H2H) Data
**Location**: `backend/data/historical/h2h/{sport}/`

**Format**: JSON files named `teamA_vs_teamB.json` (alphabetically sorted)

**Structure**:
```json
{
  "sport": "nba",
  "team1": "LAL",
  "team2": "BOS",
  "last_updated": "2025-01-15T10:30:00",
  "total_games": 15,
  "games": [
    {
      "date": "2024-12-15",
      "season": 2024,
      "home_team": "LAL",
      "away_team": "BOS",
      "home_score": 110,
      "away_score": 105,
      "total": 215,
      "spread": 5,
      "playoff": false
    }
  ]
}
```

**Usage**:
- Matchup History Strategy analyzes these files
- Auto-cached for 7 days
- Used for revenge game detection and trend analysis

### 2. Raw Team Stats
**Location**: `backend/data/raw/nba/nba_team_stats_YYYY-MM-DD.csv`

**Format**: CSV with columns:
- team_name, pace, off_rating, def_rating, net_rating
- fg_pct, three_pt_pct, ft_pct, reb_per_game
- ast_per_game, tov_per_game, etc.

**Refresh**: Daily via `nba_api_stats.py`

### 3. Betting Odds
**Location**: `backend/data/raw/odds/`

**Format**: JSON files from The Odds API

**Refresh**: Real-time (10-second intervals during games)

### 4. Predictions
**Location**: `backend/data/predictions/`

**Format**: CSV with columns:
- game_id, date, home_team, away_team
- predicted_total, market_total, edge
- confidence, recommendation, bet_decision

**Usage**: Uploaded to Google Sheets for tracking

### 5. Performance Tracking
**Location**: `backend/data/tracking/`

**Files**:
- `predictions_log.csv`: Every prediction made
- `results_log.csv`: Actual game outcomes
- `performance_summary.csv`: ROI, win rate, units won/lost

**Usage**: Track model performance over time

## Data Flows

### Flow 1: Daily Prediction Generation (NBA)
```
1. Scrape team stats → backend/data/raw/nba/
2. Fetch odds → backend/data/raw/odds/
3. Generate predictions → backend/data/predictions/
4. Log predictions → backend/data/tracking/predictions_log.csv
5. Upload to Google Sheets
```

### Flow 2: H2H Analysis
```
1. Scrape H2H history → backend/data/historical/h2h/{sport}/
2. Load cached data (if < 7 days old)
3. Apply Matchup History Strategy
4. Generate H2H-based recommendations
```

### Flow 3: Performance Tracking
```
1. Game completes
2. Record result → backend/data/tracking/results_log.csv
3. Calculate W/L/P → Update performance_summary.csv
4. Generate reports
```

## Caching Strategy

### H2H Data
- **Cache Duration**: 7 days
- **Rationale**: Historical data doesn't change frequently
- **Refresh Trigger**: Manual refresh or age > 7 days

### Team Stats
- **Cache Duration**: 24 hours
- **Rationale**: Stats update daily
- **Refresh Trigger**: Daily at 9 AM

### Odds Data
- **Cache Duration**: None (real-time)
- **Rationale**: Odds change constantly
- **Refresh Trigger**: Every 10 seconds during games

## Storage Limits and Cleanup

### Current Storage Usage
- **H2H Data**: ~1-2 MB per sport (100-200 matchups)
- **Raw Stats**: ~5 MB per season
- **Predictions**: ~10 MB per season
- **Tracking**: ~20 MB per season

### Cleanup Schedule
- **H2H**: Keep all (historical value)
- **Raw Stats**: Keep current season + 2 years
- **Predictions**: Archive after season ends
- **Tracking**: Keep all (performance history)

## Database Future (PostgreSQL)

**Planned Migration**:
Currently using flat files (JSON/CSV) for simplicity and rapid development.

**Future state** (when scaling):
- H2H data → `h2h_games` table
- Predictions → `predictions` table
- Performance → `performance_tracking` table

**Benefits**:
- Faster queries
- Better relationships
- Concurrent access
- Easier analytics

**Migration Timeline**: After validating strategies (3-6 months)

## Accessing Data

### From Python
```python
# Load H2H data
from scrapers.h2h.head_to_head_scraper import HeadToHeadScraper

scraper = HeadToHeadScraper()
data = scraper.load_h2h_data('nba', 'lal', 'bos')

# Load predictions
import pandas as pd
predictions = pd.read_csv('backend/data/predictions/nba_predictions_latest.csv')
```

### From API
```bash
# H2H endpoint (coming soon)
GET /api/h2h/{sport}/{team1}/{team2}

# Predictions endpoint
GET /api/predictions/latest
```

## Backup Strategy

**Currently**: Git + local backups

**Recommended**:
1. Daily backup to cloud (AWS S3 or Google Cloud Storage)
2. Keep 30-day rolling backups
3. Monthly archival backups

## Security Considerations

- **Sensitive**: API keys in `.env` (not committed to git)
- **Public**: Prediction data (can be shared)
- **Private**: Performance tracking (competitive advantage)
- **Logs**: Exclude from git (`.gitignore`)
