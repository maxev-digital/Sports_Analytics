# BULLETPROOF PLAYER PROPS ARCHITECTURE
## DO NOT MODIFY WITHOUT EXPLICIT APPROVAL

This architecture is SACRED and mirrors the main model system exactly.

## Directory Structure (FINAL)
```
backend/
├── ml/
│   ├── props/
│   │   ├── __init__.py
│   │   ├── enhanced_feature_engineering.py  ← 70 features
│   │   ├── predictor.py                     ← generate_all_props_edges()
│   │   ├── trainer.py                       ← 7-model training
│   │   ├── models/
│   │   │   ├── xgb_props.pkl
│   │   │   ├── lgb_props.pkl
│   │   │   ├── catboost_props.cbm
│   │   │   ├── random_forest_props.pkl
│   │   │   ├── linear_props.pkl
│   │   │   ├── pytorch_tabular_props.pt
│   │   │   └── neural_ensemble_weighter_props.pt
│   │   └── backups/
│   └── predictions.db                       ← player_prop_predictions table
```

## Sacred API Endpoints (NEVER BREAK)
- `/api/ui/props-edges` - Today's ML-generated edges
- `/api/ui/props-performance` - Model performance metrics
- `/api/ui/props-historical` - Historical predictions
- `/api/ui/props-health` - System health check

## Daily Autonomous Schedule
- 3:00 AM CST: Grade previous day's props
- 10:30 AM CST: Generate new props predictions (90 mins after main models)

## 7-Model Ensemble (Identical to Main Models)
1. XGBoost
2. LightGBM
3. CatBoost
4. Random Forest
5. Linear/Ridge Regression
6. PyTorch Tabular Net
7. Neural Ensemble Weighter

## 70 Features (Within 68-72 Range)
- Player Stats: 28 features
- Matchup: 22 features
- Context: 15 features
- Market: 5 features

## FORBIDDEN Actions
❌ Direct database calls from frontend
❌ Calculations in frontend
❌ Endpoints outside /api/ui/*
❌ Renaming or simplifying any files
❌ Changing feature count outside 68-72 range

## Required Display Fields (Pre-computed by Backend)
- display_edge
- display_confidence
- display_recommendation
- display_win_rate
- display_units
- display_roi

THIS ARCHITECTURE IS PERMANENT.
NO DEVIATIONS ALLOWED.
