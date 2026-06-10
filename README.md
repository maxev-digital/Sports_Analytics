# MAX EV Sports

Real-time sports analytics platform for identifying and tracking value across major US sportsbooks. Built solo as a first major Python/ML project.

## What It Does

Monitors six sharp sportsbooks in real-time, runs ML ensemble predictions across four sports, and surfaces edge opportunities based on line movement and model output. Originally included an automated trading layer for Kalshi prediction markets — that module is archived as Kalshi/prediction markets changed the economics of the approach mid-build.

## Stack

**Backend:** Python 3, FastAPI, SQLite  
**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Recharts, Electron  
**ML:** XGBoost, LightGBM, Random Forest (ensemble)  
**Infrastructure:** Linux VPS, systemd services, Nginx, cron

## Architecture

```
React/Electron Frontend (TypeScript)
        ↓
FastAPI Backend (Python, port 8000)
        ↓
Real-Time Services (systemd, always-on)
  ├── Sharp Totals Logger     — polls 6 books every 10 seconds
  ├── Sharp Value Trader      — scans for mispriced lines hourly
  ├── ML Predictions API      — serves model output via FastAPI
  └── Kalshi Bot (archived)  — automated trade execution
        ↓
Scheduled Tasks (cron)
  ├── ML Predictions          — daily 6 AM regeneration
  ├── Strategy Alerts         — situational edge detection (daily 10 AM)
  ├── Game Results Scraper    — daily outcome collection
  └── Model Grading           — accuracy and ROI calculation post-game
        ↓
SQLite Databases
  ├── predictions.db          — ML model output and accuracy tracking
  ├── sharp_totals_history.db — historical book line movement
  ├── sharp_value_trades.db   — value trade log
  ├── positions.db            — open/settled position tracking
  ├── strategy_alerts.db      — situational opportunity log
  └── odds_history.db         — full historical odds archive
```

## Data Sources

| Source | Purpose | Volume |
|--------|---------|--------|
| The Odds API | Live odds from 6 sharp books | ~26k calls/day |
| Kalshi API | Prediction market data + trade execution (archived) | Real-time |
| BallDontLie API | NBA player statistics for prop modeling | Daily |
| ESPN / CBS RSS | Sports news, injuries, briefings | Every 4 hours |

**Sharp books tracked:** Pinnacle, Circa, BetOnline, Bookmaker, DraftKings, Bovada

**Sports covered:** NBA, NHL, NCAAB, NFL

## ML Pipeline

Three models run in ensemble for each prediction type:

- **XGBoost** — gradient boosting, primary model for totals and spreads
- **LightGBM** — fast boosting alternative, used for player props
- **Random Forest** — ensemble baseline, improves robustness on small samples

**Features:** historical game stats, rest days, home/away, injury context, line movement velocity, revenge/letdown situational flags

**Output per prediction:** probability vs market line, edge percentage, Kelly criterion bet sizing, confidence score

**Grading:** outcome comparison runs nightly, accuracy and ROI tracked by sport, model, and bet type

## Frontend Pages

| Page | Description |
|------|-------------|
| Home | Daily briefing — news, injuries, trending stories |
| Markets | Live value opportunities with ML prediction overlay |
| Positions | Full trade history with P&L |
| Analytics | Win rate, ROI, model performance over time |
| Props | Player prop predictions (partial) |
| Tools | Kelly calculator, edge analysis utilities |

## What I'd Do Differently

This was my first large Python project. A few things I'd change with what I know now:

- **PostgreSQL instead of SQLite** — multiple always-on services writing to the same SQLite files created contention. PostgreSQL with connection pooling is the right call at this data volume.
- **Separate the ML training pipeline** — training and serving are mixed in the same codebase. A proper feature store and scheduled retraining job would be cleaner.
- **Start with one sport** — building NBA, NHL, NCAAB, and NFL simultaneously from day one spread the model training data too thin early on. Better to nail one sport's prediction pipeline before expanding.
- **The Kalshi layer** — prediction markets emerged mid-build and changed the arbitrage economics significantly. If restarting today I'd build the analytics layer only and treat execution as a separate, later problem.

## Status

Archived. The core analytics pipeline (line movement tracking, ML predictions, strategy alerts) works. The Kalshi automated trading module is preserved but not active. This repo is kept as a portfolio reference for the data pipeline and ML architecture.
