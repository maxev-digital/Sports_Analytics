# Regression to Mean Basketball Totals Strategy

## Folder Structure

```
regression_to_mean/
├── __init__.py                    # Package initialization
├── README.md                      # This file
├── strategy.py                    # Core strategy logic
│
├── models/                        # Model-related code
│   ├── __init__.py
│   ├── quantile_trainer.py       # XGBoost quantile regression training
│   ├── predictor.py              # Prediction interface
│   └── feature_engineering.py    # Feature calculation utilities
│
├── monitors/                      # Live monitoring services
│   ├── __init__.py
│   ├── live_monitor.py           # Main live monitoring service
│   ├── odds_fetcher.py           # Fetch live odds from APIs
│   └── game_tracker.py           # Track game state and context
│
├── utils/                         # Helper utilities
│   ├── __init__.py
│   ├── kelly_calculator.py       # Kelly criterion calculations
│   ├── z_score.py                # Z-score statistical functions
│   └── notifications.py          # Discord/SMS/Email alerts
│
├── docs/                          # Documentation
│   ├── strategy_guide.md         # Full strategy documentation
│   ├── quickstart.md             # Quick start guide
│   ├── api_reference.md          # API endpoint docs
│   └── examples.md               # Usage examples
│
└── tests/                         # Unit tests
    ├── __init__.py
    ├── test_strategy.py
    ├── test_predictions.py
    └── test_kelly_sizing.py
```

## Quick Start

```python
from backend.strategies.regression_to_mean import RegressionToMeanStrategy

# Initialize strategy
strategy = RegressionToMeanStrategy(
    model_path="backend/ml/models/ncaab_quantile_mean_latest.json",
    z_score_threshold=2.0,
    min_confidence=0.60,
    min_edge=3.0
)

# Analyze a game
alerts = strategy.analyze_game(
    game_features={...},
    live_totals={"DraftKings": 164.5, "FanDuel": 165.0},
    pregame_total=158.5
)
```

## Components

### strategy.py
Core strategy logic - prediction, z-score calculation, alert generation

### models/
- **quantile_trainer.py**: Train XGBoost models with confidence intervals
- **predictor.py**: Load models and generate predictions
- **feature_engineering.py**: Calculate 40+ features from team stats

### monitors/
- **live_monitor.py**: Continuous monitoring of all live games
- **odds_fetcher.py**: Fetch live totals from The Odds API
- **game_tracker.py**: Track game context (quarter, score, time)

### utils/
- **kelly_calculator.py**: Optimal bet sizing
- **z_score.py**: Statistical deviation calculations
- **notifications.py**: Alert delivery (Discord, SMS, Email)

## Development

Add new files to appropriate subfolder as strategy evolves:
- New model types → `models/`
- New monitoring features → `monitors/`
- New utilities → `utils/`
- Documentation → `docs/`
- Tests → `tests/`

## Version History

- **v1.0.0** (2025-11-07): Initial implementation
  - XGBoost quantile regression
  - Live monitoring service
  - API endpoints
  - Kelly criterion sizing
