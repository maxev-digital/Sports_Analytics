# Multi-Sport Player Props System

**Complete ML-powered player props prediction system for all major sports**

## 🏆 Supported Sports

- **NBA** - Points, Rebounds, Assists, Threes, PRA, Blocks, Steals
- **NFL** - Pass Yards/TDs, Rush Yards/TDs, Receptions, Receiving Yards
- **NHL** - Goals, Assists, Points, Shots on Goal
- **NCAAB** - Points, Rebounds, Assists, Threes
- **NCAAF** - Pass Yards/TDs, Rush Yards/TDs, Receptions, Receiving Yards
- **MLB** - Coming soon (Hits, Home Runs, RBIs, Strikeouts)

## 📋 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DAILY WORKFLOW                            │
│  run_daily_props_workflow_multi_sport.py                    │
└────────┬────────────────────────────────────────────────────┘
         │
         ├── 1. SCRAPING (The Odds API)
         │   └── multi_sport_props_scraper.py
         │       ├── Fetches props for all sports
         │       ├── Stores in player_props_lines table
         │       └── Cost: ~50 API calls per run
         │
         ├── 2. PREDICTIONS (ML Models)
         │   └── multi_sport_predictor.py
         │       ├── Loads sport-specific models
         │       ├── Engineers features (multi_sport_features.py)
         │       ├── Generates predictions with edges
         │       └── Stores in player_props_predictions table
         │
         └── 3. GRADING (Results Tracking)
             └── results_tracker.py
                 ├── Fetches game results
                 ├── Grades previous predictions
                 └── Updates result/actual_value columns
```

## 🚀 Quick Start

### 1. Setup Database Schema

```bash
cd /root/sporttrader
python backend/database/setup_player_props_schema.py
```

This creates 6 tables:
- `player_props_lines` - Market lines from bookmakers
- `player_props_predictions` - ML predictions with edges
- `player_stats_cache` - Player statistics cache
- `team_stats_cache` - Team statistics cache
- `props_results` - Game results for grading
- `model_performance_tracking` - Model performance metrics

### 2. Run Complete Workflow

**Single Sport:**
```bash
python backend/run_daily_props_workflow_multi_sport.py --sports nba
```

**Multiple Sports:**
```bash
python backend/run_daily_props_workflow_multi_sport.py --sports nba,nfl,nhl
```

**All Sports:**
```bash
python backend/run_daily_props_workflow_multi_sport.py --sports all
```

**Skip Scraping (use existing data):**
```bash
python backend/run_daily_props_workflow_multi_sport.py --sports nba --skip-scrape
```

### 3. Schedule Daily Runs (Cron)

Add to crontab:
```bash
# Run at 10 AM daily for all sports
0 10 * * * cd /root/sporttrader && python backend/run_daily_props_workflow_multi_sport.py --sports all >> logs/daily_props.log 2>&1

# Run NBA only at 11 AM
0 11 * * * cd /root/sporttrader && python backend/run_daily_props_workflow_multi_sport.py --sports nba >> logs/nba_props.log 2>&1
```

## 📊 Data Flow

### Step 1: Scraping
```python
# Scrapes from The Odds API
from scrapers.props.multi_sport_props_scraper import MultiSportPropsScraper

scraper = MultiSportPropsScraper()
await scraper.run(sports=['nba', 'nfl'])
```

**Output:** `player_props_lines` table populated with today's lines

### Step 2: Predictions
```python
# Generates ML predictions
from ml.predictions.multi_sport_predictor import MultiSportPropsPredictor

predictor = MultiSportPropsPredictor()
predictor.run(sports=['nba', 'nfl'])
```

**Output:** `player_props_predictions` table with predictions and edges

### Step 3: Grading
```python
# Grades previous predictions
from scrapers.props.results_tracker import ResultsTracker

tracker = ResultsTracker()
tracker.grade_predictions(sport='nba')
```

**Output:** Updates `result` and `actual_value` in predictions table

## 🎯 API Endpoints

### Get Today's Props with Edges

**Endpoint:** `GET /api/ui/props-edges`

**Parameters:**
- `sport` - Sport filter (nba, nfl, nhl, etc.)
- `prop_type` - Prop type filter (points, rebounds, etc.)
- `min_confidence` - Minimum confidence (default: 0.55)
- `min_edge` - Minimum edge % (default: 1.0)
- `view_mode` - "edges" or "all"
- `limit` - Max results (default: 50)

**Example:**
```bash
curl "http://localhost:8000/api/ui/props-edges?sport=nba&min_edge=5&view_mode=edges"
```

**Response:**
```json
{
  "props": [
    {
      "player_name": "LeBron James",
      "team": "Los Angeles Lakers",
      "opponent": "Boston Celtics",
      "prop_type": "points",
      "market_line": 25.5,
      "predicted_value": 28.2,
      "edge": 2.7,
      "edge_pct": 10.6,
      "confidence": 0.72,
      "recommendation": "OVER",
      "over_odds": -110,
      "under_odds": -110
    }
  ],
  "total_props_analyzed": 50,
  "props_with_edge": 12,
  "date": "2025-11-30"
}
```

### Get Model Performance

**Endpoint:** `GET /api/ui/props-performance`

**Parameters:**
- `days` - Days to analyze (default: 30)
- `sport` - Sport filter
- `prop_type` - Prop type filter

**Example:**
```bash
curl "http://localhost:8000/api/ui/props-performance?sport=nba&days=30"
```

## 🧠 Machine Learning Models

### Current Models (NBA Only)

Located in: `backend/ml/trained_models/`

```
nba_points_model.joblib
nba_rebounds_model.joblib
nba_assists_model.joblib
nba_threes_model.joblib
nba_PRA_model.joblib
```

### Feature Engineering

**22 Features for NBA:**

**Player Stats (8 features):**
- season_avg, last_10_avg, usage_rate, minutes_per_game
- home_avg, away_avg, vs_opponent_avg, fg_pct

**Opponent Matchup (8 features):**
- opp_defensive_rating, opp_pace, opp_assists, opp_turnovers
- opp_steals, opp_blocks, opp_rebounds, opp_points_allowed

**Market Context (6 features):**
- market_line, line_vs_avg_diff, line_vs_l10_diff
- prop_weight, is_home, matchup_factor

### Training New Models

**For NBA:**
```bash
cd backend/ml/models
python nba_props_trainer_fast.py
```

**For Other Sports:**
Models need to be trained with historical data. Template:
```python
from ml.feature_engineering.multi_sport_features import get_feature_engineer
from sklearn.ensemble import RandomForestRegressor

# Load historical data
# Engineer features using sport-specific feature engineer
# Train model
# Save as {sport}_{prop_type}_model.joblib
```

## 📁 File Structure

```
backend/
├── ml/
│   ├── feature_engineering/
│   │   └── multi_sport_features.py      # Feature engineering for all sports
│   ├── predictions/
│   │   ├── multi_sport_predictor.py     # Unified predictor
│   │   └── daily_props_predictor_fast.py # NBA predictor (legacy)
│   └── trained_models/
│       ├── nba_points_model.joblib
│       ├── nba_rebounds_model.joblib
│       └── ...
├── scrapers/
│   └── props/
│       ├── multi_sport_props_scraper.py  # Scrapes all sports
│       ├── results_tracker.py            # Grades predictions
│       └── daily_props_scraper.py        # NBA scraper (legacy)
├── routes/
│   └── ui_props.py                       # API endpoints
├── database/
│   └── setup_player_props_schema.py      # Schema setup
└── run_daily_props_workflow_multi_sport.py  # Master workflow
```

## 🔧 Configuration

### Database

Default: `data/player_props.db`

Override with `--db` flag:
```bash
python backend/run_daily_props_workflow_multi_sport.py --db /path/to/custom.db
```

### The Odds API

Set in `.env`:
```bash
ODDS_API_KEY=your_api_key_here
```

**API Usage:**
- ~9 calls per NBA scrape
- ~4 calls per NFL scrape
- ~7 calls per NHL scrape
- ~16 calls per NCAAB scrape
- ~11 calls per NCAAF scrape

Total: ~47 calls for "all" sports

## 📈 Model Performance Tracking

View model performance:
```bash
curl "http://localhost:8000/api/ui/props-performance?sport=nba&days=30"
```

**Key Metrics:**
- Win Rate: % of correct predictions
- Units Won: Profit/loss at -110 odds
- ROI: Return on investment %
- By Prop Type: Performance broken down by prop
- By Confidence: Performance by confidence level

## 🐛 Troubleshooting

### No Predictions Generated

**Check 1: Models exist**
```bash
ls backend/ml/trained_models/*.joblib
```

**Check 2: Props data exists**
```bash
python3 -c "import sqlite3; conn = sqlite3.connect('data/player_props.db'); print(conn.execute('SELECT COUNT(*) FROM player_props_lines WHERE date = date()').fetchone())"
```

**Check 3: Feature engineering working**
```bash
python backend/ml/predictions/multi_sport_predictor.py --sports nba
```

### API Returning Empty Props

**Check 1: Database has today's data**
```sql
SELECT COUNT(*) FROM player_props_predictions
WHERE prediction_date = date('now');
```

**Check 2: Edge filters**
Lower the `min_edge` slider in the frontend

**Check 3: Sport filter**
Ensure the selected sport has models and data

### Scraper Failing

**Check 1: API Key valid**
```bash
echo $ODDS_API_KEY
```

**Check 2: API requests remaining**
Check logs for "x-requests-remaining" header

**Check 3: Network connectivity**
```bash
curl "https://api.the-odds-api.com/v4/sports?apiKey=$ODDS_API_KEY"
```

## 🚀 Deployment Steps

### 1. Deploy Fixed UI Endpoints to VPS

```bash
# Copy fixed version
scp backend/routes/ui_props_FIXED.py root@148.230.87.135:/root/sporttrader/backend/routes/ui_props.py

# Restart service
ssh root@148.230.87.135 "systemctl restart sporttrader"
```

### 2. Setup Database on VPS

```bash
ssh root@148.230.87.135
cd /root/sporttrader
python backend/database/setup_player_props_schema.py
```

### 3. Run Initial Scrape

```bash
python backend/run_daily_props_workflow_multi_sport.py --sports nba
```

### 4. Setup Cron Job

```bash
crontab -e

# Add:
0 10 * * * cd /root/sporttrader && python backend/run_daily_props_workflow_multi_sport.py --sports all >> logs/daily_props.log 2>&1
```

### 5. Verify in Frontend

Visit: `https://max-ev-sports.com/#/props`

Should see today's props with edges!

## 📝 Next Steps for Full Multi-Sport Support

### Immediate (NBA works now):
- ✅ Frontend displaying NBA props
- ✅ API endpoints working
- ✅ Daily workflow functional

### Short-term (train models for other sports):
1. Collect historical data for NFL, NHL, NCAAB, NCAAF
2. Train models using `multi_sport_features.py`
3. Save models as `{sport}_{prop_type}_model.joblib`
4. Run daily workflow with `--sports all`

### Long-term (full automation):
1. Automated model retraining (weekly)
2. Real-time odds tracking
3. Live in-game prop predictions
4. Advanced betting strategies (Kelly Criterion, etc.)

## 📞 Support

Issues? Check:
1. Logs: `logs/daily_props.log`
2. Database: `sqlite3 data/player_props.db`
3. API health: `/api/ui/props-health`

---

**Last Updated:** 2025-11-30
**Version:** 1.0.0 - Multi-Sport Foundation
