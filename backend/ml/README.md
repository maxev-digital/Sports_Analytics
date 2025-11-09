# ML Training Infrastructure

Complete machine learning training pipeline for MAX-EV-SPORTS prediction models.

## Quick Start

### 1. Install Dependencies
```bash
pip install scikit-learn pandas numpy xgboost lightgbm scipy joblib httpx
```

### 2. Train NHL Models
```bash
python -m backend.ml.training.train_nhl_models
```

### 3. Verify Models Created
```bash
ls backend/ml/models/nhl_*.joblib
```

## Training Process

1. **Data Loading**: Fetches historical games from NHL API
2. **Feature Engineering**: Creates 24-34 feature matrices
3. **Model Training**: Trains Random Forest, XGBoost, LightGBM, Linear/Logistic
4. **Evaluation**: MAE, RMSE, R² for regression; Accuracy, ROC-AUC for classification
5. **Saving**: Models saved as .joblib files with metadata

## Output Files

- `nhl_random_forest_totals_latest.joblib`
- `nhl_xgboost_totals_latest.joblib`
- `nhl_lightgbm_totals_latest.joblib`
- `nhl_linear_regression_totals_latest.joblib`
- (Plus 8 more for spreads/moneyline)
- `nhl_totals_metadata_latest.joblib` (performance stats)

See full documentation in this file for details.
