# BULLETPROOF PLAYER PROPS - ML MODELS & DATA REFERENCE

## Complete Documentation of All Models, Features, and Data Points

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Supported Prop Types](#supported-prop-types)
3. [7-Model Ensemble](#7-model-ensemble)
4. [70 Features Complete Reference](#70-features-complete-reference)
5. [Feature Categories Deep Dive](#feature-categories-deep-dive)
6. [Data Sources](#data-sources)
7. [Prediction Output Fields](#prediction-output-fields)
8. [API Endpoints](#api-endpoints)

---

## Architecture Overview

The Player Props ML system mirrors the main Max EV Edge models exactly:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BULLETPROOF PROPS PIPELINE                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────────┐    ┌──────────────────┐   │
│  │ Props Lines │───▶│ 70 Features     │───▶│ 7-Model Ensemble │   │
│  │ (Database)  │    │ Extraction      │    │                  │   │
│  └─────────────┘    └─────────────────┘    └────────┬─────────┘   │
│                                                      │             │
│                                                      ▼             │
│                      ┌───────────────────────────────────────┐    │
│                      │        PREDICTION OUTPUT              │    │
│                      ├───────────────────────────────────────┤    │
│                      │ - predicted_value                     │    │
│                      │ - edge (vs market line)               │    │
│                      │ - over_probability / under_probability │    │
│                      │ - confidence (0-100)                  │    │
│                      │ - recommendation (OVER/UNDER/NO_PLAY) │    │
│                      │ - kelly_fraction                      │    │
│                      └───────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Supported Prop Types

### NBA Props
| Prop Type | Description | Typical Lines |
|-----------|-------------|---------------|
| `points` | Total points scored | 15.5 - 35.5 |
| `rebounds` | Total rebounds | 3.5 - 12.5 |
| `assists` | Total assists | 2.5 - 12.5 |
| `steals` | Total steals | 0.5 - 2.5 |
| `blocks` | Total blocks | 0.5 - 3.5 |
| `threes` | Three-pointers made | 0.5 - 5.5 |
| `pts_rebs` | Points + Rebounds | 20.5 - 45.5 |
| `pts_asts` | Points + Assists | 20.5 - 45.5 |
| `rebs_asts` | Rebounds + Assists | 6.5 - 20.5 |
| `pts_rebs_asts` | Points + Rebounds + Assists | 25.5 - 55.5 |
| `turnovers` | Total turnovers | 1.5 - 4.5 |
| `fantasy_score` | DFS fantasy points | 25.5 - 60.5 |

### NHL Props
| Prop Type | Description | Typical Lines |
|-----------|-------------|---------------|
| `goals` | Goals scored | 0.5 - 1.5 |
| `assists` | Assists | 0.5 - 1.5 |
| `points` | Goals + Assists | 0.5 - 2.5 |
| `shots_on_goal` | Shots on goal | 2.5 - 5.5 |
| `power_play_points` | PP points | 0.5 |
| `saves` | Goalie saves | 22.5 - 32.5 |
| `goals_against` | Goals allowed | 2.5 - 3.5 |

### NFL Props
| Prop Type | Description | Typical Lines |
|-----------|-------------|---------------|
| `passing_yards` | QB passing yards | 200.5 - 300.5 |
| `passing_tds` | Passing touchdowns | 1.5 - 2.5 |
| `rushing_yards` | Rushing yards | 40.5 - 100.5 |
| `receiving_yards` | Receiving yards | 40.5 - 100.5 |
| `receptions` | Total receptions | 3.5 - 7.5 |
| `touchdowns` | Total touchdowns | 0.5 - 1.5 |

---

## 7-Model Ensemble

### Model Architecture

| # | Model | Type | Weight | Description |
|---|-------|------|--------|-------------|
| 1 | **XGBoost** | Gradient Boosting | 20% | Extreme Gradient Boosting - Handles non-linear relationships |
| 2 | **LightGBM** | Gradient Boosting | 20% | Light Gradient Boosting - Fast, handles large datasets |
| 3 | **CatBoost** | Gradient Boosting | 15% | Categorical Boosting - Good with categorical features |
| 4 | **Random Forest** | Ensemble Trees | 15% | Robust, reduces overfitting via bagging |
| 5 | **Linear/Ridge** | Linear Regression | 10% | Baseline model, interpretable coefficients |
| 6 | **PyTorch Tabular** | Neural Network | 20% | Deep learning for tabular data |
| 7 | **Neural Ensemble** | Meta-learner | N/A | Learns optimal weights from model outputs |

### Model Files
```
ml/props/models/
├── xgb_props.pkl              # XGBoost model
├── lgb_props.pkl              # LightGBM model
├── catboost_props.cbm         # CatBoost model
├── random_forest_props.pkl    # Random Forest model
├── linear_props.pkl           # Linear/Ridge model
├── pytorch_tabular_props.pt   # PyTorch neural network
├── neural_ensemble_weighter_props.pt  # Ensemble weighter
└── ensemble_weights.json      # Trained ensemble weights
```

### Ensemble Prediction Formula

```python
predicted_value = Σ(model_prediction[i] * weight[i]) / Σ(weight[i])

# Default weights (if not trained):
weights = {
    'xgb': 0.20,
    'lgb': 0.20,
    'catboost': 0.15,
    'random_forest': 0.15,
    'linear': 0.10,
    'pytorch_tabular': 0.20
}
```

---

## 70 Features Complete Reference

### Summary Table

| Category | Count | Features |
|----------|-------|----------|
| Player Stats | 28 | Season averages, recent form, splits, trends, advanced |
| Matchup | 22 | Opponent defense, pace, historical vs opponent |
| Context | 15 | Rest, venue, game importance, team context |
| Market | 5 | Line analysis, implied probabilities |
| **TOTAL** | **70** | |

---

## Feature Categories Deep Dive

### 1. PLAYER STATS FEATURES (28 Features)

#### Season Averages (5 features)

| Feature | Data Source | Description |
|---------|-------------|-------------|
| `season_avg` | BallDontLie API / Props DB | Player's season average for this prop type |
| `season_mins` | BallDontLie API | Average minutes per game this season |
| `season_games_played` | BallDontLie API | Total games played this season |
| `season_std` | Calculated | Standard deviation of performance this season |
| `season_per_minute` | Calculated | `season_avg / season_mins` - Rate stat per minute |

#### Recent Form - Last 5 Games (5 features)

| Feature | Data Source | Description |
|---------|-------------|-------------|
| `last_5_avg` | Props DB Results | Average of last 5 games for this prop type |
| `last_5_mins` | Props DB Results | Average minutes in last 5 games |
| `last_5_std` | Calculated | Standard deviation of last 5 games |
| `last_5_over_pct` | Calculated | % of last 5 games over current market line |
| `last_5_per_minute` | Calculated | `last_5_avg / last_5_mins` |

#### Recent Form - Last 10 Games (5 features)

| Feature | Data Source | Description |
|---------|-------------|-------------|
| `last_10_avg` | Props DB Results | Average of last 10 games for this prop type |
| `last_10_mins` | Props DB Results | Average minutes in last 10 games |
| `last_10_std` | Calculated | Standard deviation of last 10 games |
| `last_10_over_pct` | Calculated | % of last 10 games over current market line |
| `last_10_per_minute` | Calculated | `last_10_avg / last_10_mins` |

#### Trends (5 features)

| Feature | Data Source | Description |
|---------|-------------|-------------|
| `last_3_avg` | Props DB Results | Average of last 3 games |
| `trend_l3_vs_l10` | Calculated | `last_3_avg - last_10_avg` (recent momentum) |
| `trend_l5_vs_season` | Calculated | `last_5_avg - season_avg` |
| `mins_trend_5g` | Calculated | Change in minutes from 5th most recent to most recent game |
| `hot_streak_indicator` | Calculated | 1.0 if `trend_l3_vs_l10 > 0`, else 0.0 |

#### Splits (4 features)

| Feature | Data Source | Description |
|---------|-------------|-------------|
| `home_avg` | Props DB Results | Average in home games |
| `away_avg` | Props DB Results | Average in away games |
| `home_away_diff` | Calculated | `home_avg - away_avg` |
| `day_night_preference` | Future Enhancement | Day vs night game performance (currently 0.0) |

#### Advanced (4 features)

| Feature | Data Source | Description |
|---------|-------------|-------------|
| `consistency_score` | Calculated | `1 / (1 + coefficient_of_variation)` - Higher = more consistent |
| `ceiling_games_pct` | Calculated | % of last 5 games at or above 90th percentile |
| `floor_games_pct` | Calculated | % of last 5 games at or below 10th percentile |
| `hit_rate_at_current_line` | Props DB Results | Historical % over current market line |

---

### 2. MATCHUP FEATURES (22 Features)

#### Opponent Team Stats (6 features)

| Feature | Data Source | Description |
|---------|-------------|-------------|
| `opp_pace` | Team Stats API | Opponent's pace rating (possessions/game) |
| `opp_def_rating` | Team Stats API | Opponent's defensive rating (points allowed/100 poss) |
| `opp_off_rating` | Team Stats API | Opponent's offensive rating |
| `opp_win_pct` | Team Stats API | Opponent's win percentage |
| `opp_recent_form_10g` | Team Stats API | Opponent's win % in last 10 games |
| `opp_home_away_record` | Team Stats API | Opponent's road win % (if away) |

#### Opponent vs Prop Type (6 features)

| Feature | Data Source | Description |
|---------|-------------|-------------|
| `opp_def_rank_vs_prop` | Defense Rankings | Opponent's rank defending this prop type (1-30) |
| `opp_def_rate_vs_prop` | Defense Rankings | Opponent's rate stat defending this prop type |
| `opp_allowed_per_game_prop` | Defense Rankings | Avg of this stat type allowed by opponent |
| `opp_vs_position_rank` | Defense Rankings | Opponent's rank vs player's position |
| `opp_recent_vs_prop_trend` | Defense Rankings | Trend in opponent's defense vs prop type |
| `opp_pts_allowed_variance` | Defense Rankings | Variance in opponent's defensive performance |

#### Historical vs Opponent (5 features)

| Feature | Data Source | Description |
|---------|-------------|-------------|
| `vs_opp_avg` | Props DB Results | Player's average vs this opponent |
| `vs_opp_games` | Props DB Results | Number of games vs this opponent |
| `vs_opp_over_pct` | Props DB Results | % over line vs this opponent |
| `vs_opp_last_game` | Props DB Results | Player's stat in last game vs opponent |
| `vs_opp_career_hit_rate` | Props DB Results | Career hit rate at this line vs opponent |

#### Matchup Composite (5 features)

| Feature | Data Source | Description |
|---------|-------------|-------------|
| `matchup_difficulty` | Calculated | Composite difficulty score (0-1) |
| `pace_differential` | Calculated | `team_pace - opp_pace` |
| `implied_team_total` | Odds API | Team's implied total from betting odds |
| `game_total_line` | Odds API | Game total line from sportsbooks |
| `spread_absolute` | Odds API | Absolute value of point spread |

**Matchup Difficulty Formula:**
```python
matchup_difficulty = (
    (opp_def_rating / 120.0) * 0.4 +
    (opp_win_pct) * 0.3 +
    ((30 - opp_def_rank_vs_prop) / 30.0) * 0.3
)
```

---

### 3. CONTEXT FEATURES (15 Features)

#### Rest and Schedule (5 features)

| Feature | Data Source | Description |
|---------|-------------|-------------|
| `rest_days` | Schedule API | Days since player's last game |
| `is_back_to_back` | Calculated | 1.0 if `rest_days == 0`, else 0.0 |
| `opp_rest_days` | Schedule API | Opponent's days of rest |
| `rest_advantage` | Calculated | `rest_days - opp_rest_days` |
| `games_in_last_7` | Schedule API | Number of games played in last 7 days |

#### Venue and Travel (4 features)

| Feature | Data Source | Description |
|---------|-------------|-------------|
| `is_home` | Props DB | 1.0 if home game, 0.0 if away |
| `travel_distance` | Calculated | Miles traveled for away game |
| `altitude_factor` | Static Lookup | 1.0 for Denver/Utah (high altitude), else 0.0 |
| `timezone_shift` | Calculated | Time zones crossed for away game |

#### Game Importance (3 features)

| Feature | Data Source | Description |
|---------|-------------|-------------|
| `days_into_season` | Calculated | Days since season start (Oct 22, 2024) |
| `season_month` | Calculated | Month of season (1-12 adjusted) |
| `playoff_implications` | Future Enhancement | Playoff relevance score (currently 0.5) |

#### Team Context (3 features)

| Feature | Data Source | Description |
|---------|-------------|-------------|
| `teammate_injury_boost` | Injury Reports | Usage boost from injured teammates |
| `primetime_game` | Schedule API | 1.0 if nationally televised |
| `division_rivalry` | Static Lookup | 1.0 if teams in same division |

---

### 4. MARKET FEATURES (5 Features)

| Feature | Data Source | Description |
|---------|-------------|-------------|
| `line_vs_season_avg` | Calculated | `market_line - season_avg` (how line compares to season) |
| `line_vs_last_10_avg` | Calculated | `market_line - last_10_avg` |
| `line_pct_of_season` | Calculated | `market_line / season_avg` (line as % of average) |
| `implied_over_prob` | Odds API | Implied probability of over (from vig) |
| `value_indicator` | Calculated | `last_10_avg - market_line` (raw edge signal) |

---

## Data Sources

### Primary Data Sources

| Source | Data Type | Update Frequency |
|--------|-----------|------------------|
| **BallDontLie API** | Player stats, game logs | Real-time |
| **The Odds API** | Lines, odds, totals | Every 15 min |
| **Props DB (player_props.db)** | Historical results | After each game |
| **Predictions DB (predictions.db)** | ML predictions | Daily at 10:30 AM |

### Database Schema

#### player_props_lines (Input)
```sql
CREATE TABLE player_props_lines (
    id INTEGER PRIMARY KEY,
    date TEXT,
    player_name TEXT,
    team TEXT,
    opponent TEXT,
    home_away TEXT,
    prop_type TEXT,
    market_line REAL,
    sportsbook TEXT,
    game_id TEXT
);
```

#### player_props_results (Training Data)
```sql
CREATE TABLE player_props_results (
    id INTEGER PRIMARY KEY,
    game_date TEXT,
    player_name TEXT,
    team TEXT,
    opponent TEXT,
    home_away TEXT,
    prop_type TEXT,
    market_line REAL,
    actual_value REAL,
    result TEXT  -- WIN, LOSS, PUSH
);
```

#### player_prop_predictions (Output)
```sql
CREATE TABLE player_prop_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_date TEXT NOT NULL,
    player_name TEXT NOT NULL,
    team TEXT,
    opponent TEXT,
    prop_type TEXT NOT NULL,
    market_line REAL NOT NULL,
    predicted_value REAL NOT NULL,
    edge REAL NOT NULL,
    over_probability REAL,
    under_probability REAL,
    confidence REAL,
    recommendation TEXT,
    kelly_fraction REAL,
    sportsbook TEXT,
    game_id TEXT,
    model_predictions TEXT,
    generated_at TEXT,
    result TEXT,
    actual_value REAL,
    graded_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Prediction Output Fields

### Core Prediction Fields

| Field | Type | Description |
|-------|------|-------------|
| `player_name` | string | Player's full name |
| `team` | string | Player's team abbreviation |
| `opponent` | string | Opponent team abbreviation |
| `prop_type` | string | Type of prop (points, rebounds, etc.) |
| `market_line` | float | Current sportsbook line |
| `predicted_value` | float | Model's predicted stat value |
| `edge` | float | `predicted_value - market_line` |
| `over_probability` | float | Probability of OVER (0-100) |
| `under_probability` | float | Probability of UNDER (0-100) |
| `confidence` | float | Prediction confidence (0-100) |
| `recommendation` | string | OVER, UNDER, or NO_PLAY |
| `kelly_fraction` | float | Recommended bet size (0-0.25) |

### Display Fields (Pre-computed for Frontend)

| Field | Format | Example |
|-------|--------|---------|
| `display_edge` | `{edge:+.1f}` | "+3.2" |
| `display_confidence` | `{confidence:.0f}%` | "72%" |
| `display_over_prob` | `{over_prob:.1f}%` | "65.3%" |
| `display_under_prob` | `{under_prob:.1f}%` | "34.7%" |
| `display_recommendation` | string | "OVER" |

---

## API Endpoints

### Sacred /api/ui/ Endpoints

| Endpoint | Description | Returns |
|----------|-------------|---------|
| `GET /api/ui/props-edges` | Today's ML edges | edges[], total, date, filters |
| `GET /api/ui/props-performance` | Model performance metrics | summary, by_prop_type, by_confidence |
| `GET /api/ui/props-historical` | Historical predictions | predictions[], history[], total |
| `GET /api/ui/props-health` | System health check | status, props_system, timestamp |

### Query Parameters

#### /api/ui/props-edges
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `sport` | string | null | Filter by sport |
| `prop_type` | string | null | Filter by prop type |
| `min_confidence` | int | 55 | Minimum confidence threshold |
| `min_edge` | float | 1.0 | Minimum edge threshold |
| `limit` | int | 50 | Max results to return |

#### /api/ui/props-performance
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `days` | int | 30 | Lookback period in days |
| `sport` | string | null | Filter by sport |
| `prop_type` | string | null | Filter by prop type |

---

## Confidence Calculation

```python
def calculate_confidence(edge, std_dev, consistency, recent_form, hit_rate):
    # Base confidence from edge size (0-30 points)
    edge_confidence = min(30, abs(edge) * 5)

    # Consistency bonus (0-25 points)
    consistency_bonus = consistency * 25

    # Historical hit rate bonus (0-25 points)
    hit_rate_bonus = (hit_rate - 0.4) * 50 if hit_rate > 0.4 else 0

    # Recent form bonus (-10 to +20 points)
    form_bonus = min(20, max(-10, recent_form * 3))

    # Total (capped 30-95)
    total = 50 + edge_confidence + consistency_bonus + hit_rate_bonus + form_bonus
    return max(30, min(95, total))
```

---

## Kelly Criterion Formula

```python
def kelly_criterion(prob, odds=-110):
    # Convert American odds to decimal
    if odds < 0:
        decimal_odds = 1 + (100 / abs(odds))  # -110 → 1.909
    else:
        decimal_odds = 1 + (odds / 100)

    # Kelly formula: (bp - q) / b
    b = decimal_odds - 1  # 0.909 for -110
    p = prob  # e.g., 0.65
    q = 1 - p  # 0.35

    kelly = (b * p - q) / b

    # Use 25% fractional Kelly for safety
    return max(0, min(0.25, kelly * 0.25))
```

---

## Cron Schedule

```bash
# BULLETPROOF: Player Props ML Predictions - 10:30 AM CST
30 10 * * * cd /root/sporttrader/backend && source venv/bin/activate && \
    python3 -c "from ml.props.predictor import generate_all_props_edges; generate_all_props_edges()" \
    >> logs/props_predictions.log 2>&1
```

---

## File Structure

```
backend/ml/props/
├── __init__.py
├── enhanced_feature_engineering.py   # 70 features extraction
├── predictor.py                      # 7-model ensemble predictor
├── trainer.py                        # Model training script
├── ARCHITECTURE_DO_NOT_TOUCH.md      # Defense documentation
├── PROPS_MODELS_DATA_REFERENCE.md    # This file
└── models/
    ├── __init__.py
    ├── xgb_props.pkl
    ├── lgb_props.pkl
    ├── catboost_props.cbm
    ├── random_forest_props.pkl
    ├── linear_props.pkl
    ├── pytorch_tabular_props.pt
    ├── neural_ensemble_weighter_props.pt
    └── ensemble_weights.json
```

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-29 | 1.0 | Initial bulletproof architecture |

---

**IMPORTANT: This documentation is BULLETPROOF. Do not modify without explicit approval.**
