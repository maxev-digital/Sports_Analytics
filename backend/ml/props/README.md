# Player Props ML System + DFS Crusher

**Complete 7-Model Architecture for Player Props Predictions**

Version: 1.0
Status: ✅ In Development
Database: `ml/predictions.db` (unified with team totals)

---

## 📊 System Overview

This system mirrors the Team Totals ML architecture (BULLETPROOF ARCHITECTURE) but for player props.

**Key Features:**
- **7 Models:** XGBoost, LightGBM, Random Forest, Linear, PyTorch TabularNet, CatBoost, Neural Ensemble
- **70 Features:** Comprehensive player, team, opponent, and game context features
- **Unified Database:** All data stored in `ml/predictions.db` alongside team totals
- **DFS Crusher:** Correlated combos engine for PrizePicks/Underdog
- **Daily Automation:** Cron job at 10:30 AM CST

---

## 🏗️ Architecture

```
backend/ml/props/
├── __init__.py
├── enhanced_feature_engineering.py  ✅ 70 features extraction
├── trainer.py                        ⏳ Train 7 models
├── predictor.py                      ⏳ Daily prediction generation
├── schemas.py                        ⏳ Pydantic models
├── correlation_engine.py             ⏳ DFS combos engine
├── combo_generator.py                ⏳ Correlation matrix
├── setup_unified_schema.py           ✅ Database schema
└── models/                           📁 7 trained models
    ├── xgb_props.pkl
    ├── lgb_props.pkl
    ├── random_forest_props.pkl
    ├── pytorch_tabular_props.pt
    ├── catboost_props.cbm
    └── neural_ensemble_weighter_props.pt
```

---

## 📊 Database Schema

**Tables in `ml/predictions.db`:**

### 1. player_props_predictions
ML predictions with 7-model breakdown
```sql
- prediction_date, player_name, team, opponent
- prop_type, market_line, predicted_value
- edge, edge_pct, confidence_level, recommendation
- xgboost_pred, lightgbm_pred, rf_pred, linear_pred, pytorch_pred, catboost_pred, ensemble_pred
- result, actual_value, graded_at
```

### 2. correlated_combos
DFS PrizePicks/Underdog combos
```sql
- combo_id, sport, players, props, lines, directions
- true_probability, prize_picks_payout, expected_value_percent
- demon_goblin_score, display_edge, display_confidence
```

### 3. player_stats_cache
Player statistics (season + recent form)
```sql
- player_name, team, sport, season
- ppg, rpg, apg, fg%, 3pt%, ft%, mpg, usage_rate
- off_rating, def_rating, PER, ts%, last_10 stats
```

### 4. team_stats_cache
Team statistics
```sql
- team, sport, season
- off_rating, def_rating, pace, assists, turnovers, steals, blocks
```

### 5. props_results
Historical results for grading
```sql
- game_date, player_name, prop_type, actual_value
```

---

## 🎯 Feature Engineering (70 Features)

### Category Breakdown:

1. **Player Season Stats (15)**
   - PPG, RPG, APG, FG%, 3PT%, FT%
   - MPG, Usage Rate
   - Offensive/Defensive Ratings
   - Turnover Rate, Assist Rate, Rebound Rate
   - PER, True Shooting %

2. **Player Recent Form (10)**
   - Last 10 games PPG/RPG/APG
   - Recent trends (vs season avg)
   - Consistency score
   - Peak performance rate
   - Slump indicator

3. **Player vs Opponent History (8)**
   - Career vs opponent stats
   - Last 3 games vs opponent
   - Matchup advantage score
   - Head-to-head over rate
   - Position-based opponent stats

4. **Team Context (12)**
   - Team offensive/defensive ratings
   - Team pace, assist rate
   - Player's share of team scoring
   - Injury impact
   - Win/loss streaks
   - Rest days, back-to-back
   - Home/away

5. **Opponent Defense Ratings (10)**
   - Opponent defensive rating
   - Opponent pace
   - PPG/RPG/APG allowed
   - 3PT% allowed
   - Rim protection (blocks)
   - Perimeter defense (steals)
   - Turnover forced rate

6. **Game Context (8)**
   - Game total over/under
   - Spread
   - Primetime game indicator
   - Days since last game
   - Game importance
   - Weather/altitude (outdoor sports)
   - Time of season

7. **Matchup Differentials (7)**
   - Pace differential
   - Efficiency vs defense
   - Usage rate expected change
   - Scoring/rebounding/assist opportunity differentials
   - Pace-adjusted expectation

**Total: 70 features ✅**

---

## 🤖 Model Architecture

### Base Models (6):

1. **XGBoost**
   - n_estimators=200, learning_rate=0.05, max_depth=6
   - File: `models/xgb_props.pkl`

2. **LightGBM**
   - n_estimators=200, learning_rate=0.05, num_leaves=31
   - File: `models/lgb_props.pkl`

3. **Random Forest**
   - n_estimators=100, max_depth=10
   - File: `models/random_forest_props.pkl`

4. **Linear Regression**
   - Baseline model (in-memory only)

5. **PyTorch TabularNet**
   - 6-layer deep neural network
   - Input(70) → Dense(256) → Dense(512) → Dense(256) → Dense(128) → Dense(64) → Output(1)
   - BatchNorm + ReLU + Dropout(0.3)
   - File: `models/pytorch_tabular_props.pt`

6. **CatBoost**
   - iterations=200, learning_rate=0.05, depth=6
   - File: `models/catboost_props.cbm`

### Meta-Learner (1):

7. **Neural Ensemble Weighter**
   - Combines 6 base model predictions
   - Input: 12 values (6 predictions + 6 recent accuracies)
   - Output: 6 weights (sum to 1)
   - File: `models/neural_ensemble_weighter_props.pt`

---

## 🚀 Usage

### Setup Database
```bash
python ml/props/setup_unified_schema.py
```

### Test Feature Engineering
```bash
python ml/props/enhanced_feature_engineering.py
```

### Train Models
```bash
python ml/props/trainer.py --sport nba --prop-types points rebounds assists
```

### Generate Daily Predictions
```bash
python -c "from ml.props.predictor import generate_all_props_edges; generate_all_props_edges()"
```

### Cron Job (10:30 AM CST daily)
```bash
30 16 * * * cd /root/sporttrader/backend && source venv/bin/activate && python -c "from ml.props.predictor import generate_all_props_edges; generate_all_props_edges()" >> logs/props_predictions.log 2>&1
```

---

## 📈 DFS Crusher Features

**Correlated Combos Engine** - Runs automatically after predictions

### Correlation Types:
- Same-player multi-stat (Points + Assists)
- Teammate combos (Luka + Kyrie)
- Pace-based correlations (High-pace game players)
- QB + WR combos (NFL)
- Pitcher K's + Game Under (MLB)

### Demon/Goblin Detection:
- **Demon Line:** PrizePicks line ≥ 1.0 higher than model prediction
- **Goblin Line:** PrizePicks line ≤ 1.0 lower than model prediction

### Endpoints:
- `GET /api/ui/props-edges` - Single props with edges
- `GET /api/ui/props-correlations` - Correlated combos

---

## ✅ Completed Features

- [x] Directory structure
- [x] Database schema (5 tables)
- [x] Enhanced feature engineering (70 features)
- [ ] 7-model trainer
- [ ] Daily predictor
- [ ] Correlation engine
- [ ] Frontend integration
- [ ] Cron automation

---

## 📝 Next Steps

1. **Build trainer.py** - Train all 7 models
2. **Build predictor.py** - Generate daily edges
3. **Build correlation_engine.py** - DFS combos
4. **Update Props.tsx** - Add PrizePicks Crusher tab
5. **Deploy to VPS** - Setup cron jobs

---

**Status:** Phase 1B Complete (Feature Engineering)
**Last Updated:** December 2, 2025
**Author:** Max EV Sports ML Team
