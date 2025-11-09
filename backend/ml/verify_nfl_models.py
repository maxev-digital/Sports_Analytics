"""Quick verification for NFL models"""
import joblib
import numpy as np
from pathlib import Path

models_dir = Path(__file__).parent / "models"

print("=" * 60)
print("VERIFYING NFL MODELS")
print("=" * 60)

bet_types = ['totals', 'spreads', 'moneyline']
model_types = ['random_forest', 'xgboost', 'lightgbm']
n_features = {'totals': 21, 'spreads': 25, 'moneyline': 29}

total_verified = 0

for bet_type in bet_types:
    print(f"\n{bet_type.upper()}:")

    # Test ensemble models
    for model_type in model_types:
        model_name = f"nfl_{model_type}_{bet_type}_latest.joblib"
        model_path = models_dir / model_name

        model = joblib.load(model_path)
        sample = np.zeros((1, n_features[bet_type]))
        pred = model.predict(sample)

        if bet_type == 'moneyline':
            proba = model.predict_proba(sample)
            print(f"  [OK] {model_name} (pred={pred[0]}, proba={proba[0][1]:.3f})")
        else:
            print(f"  [OK] {model_name} (pred={pred[0]:.2f})")

        total_verified += 1

    # Test linear/logistic
    if bet_type == 'moneyline':
        model_name = f"nfl_logistic_regression_{bet_type}_latest.joblib"
    else:
        model_name = f"nfl_linear_regression_{bet_type}_latest.joblib"

    model_path = models_dir / model_name
    model = joblib.load(model_path)
    sample = np.zeros((1, n_features[bet_type]))
    pred = model.predict(sample)

    if bet_type == 'moneyline':
        proba = model.predict_proba(sample)
        print(f"  [OK] {model_name} (pred={pred[0]}, proba={proba[0][1]:.3f})")
    else:
        print(f"  [OK] {model_name} (pred={pred[0]:.2f})")

    total_verified += 1

print("\n" + "=" * 60)
print(f"NFL MODELS VERIFIED: {total_verified}/12")
print("=" * 60)
