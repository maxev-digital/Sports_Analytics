"""
Verify All Trained Models Load Correctly

Checks that all 36 trained models (.joblib files) can be loaded
and basic predictions can be made.
"""

import joblib
from pathlib import Path
import numpy as np

def verify_models():
    """Verify all models load and can make predictions"""

    models_dir = Path(__file__).parent / "models"

    if not models_dir.exists():
        print(f"[X] Models directory not found: {models_dir}")
        return False

    print("=" * 60)
    print("VERIFYING ALL TRAINED MODELS")
    print("=" * 60)

    sports = ['nhl', 'ncaab', 'nba']
    bet_types = ['totals', 'spreads', 'moneyline']
    model_types = ['random_forest', 'xgboost', 'lightgbm']

    # Add linear/logistic for respective bet types
    regression_models = {
        'totals': 'linear_regression',
        'spreads': 'linear_regression',
        'moneyline': 'logistic_regression'
    }

    total_models = 0
    loaded_models = 0
    failed_models = []

    for sport in sports:
        print(f"\n{sport.upper()} Models:")
        print("-" * 40)

        for bet_type in bet_types:
            # Test ensemble models
            for model_type in model_types:
                model_name = f"{sport}_{model_type}_{bet_type}_latest.joblib"
                model_path = models_dir / model_name

                total_models += 1

                if not model_path.exists():
                    print(f"  [X] {model_name} - NOT FOUND")
                    failed_models.append(model_name)
                    continue

                try:
                    model = joblib.load(model_path)

                    # Verify we can make a prediction
                    # Use appropriate feature count
                    if sport == 'nhl':
                        n_features = {'totals': 24, 'spreads': 29, 'moneyline': 34}
                    elif sport == 'ncaab':
                        n_features = {'totals': 25, 'spreads': 27, 'moneyline': 34}
                    else:  # nba
                        n_features = {'totals': 32, 'spreads': 38, 'moneyline': 42}

                    sample_features = np.zeros((1, n_features[bet_type]))

                    if bet_type == 'moneyline':
                        # Classification model - has predict_proba
                        pred = model.predict(sample_features)
                        proba = model.predict_proba(sample_features)
                        print(f"  [OK] {model_name} (pred={pred[0]}, proba={proba[0][1]:.3f})")
                    else:
                        # Regression model
                        pred = model.predict(sample_features)
                        print(f"  [OK] {model_name} (pred={pred[0]:.2f})")

                    loaded_models += 1

                except Exception as e:
                    print(f"  [X] {model_name} - ERROR: {e}")
                    failed_models.append(model_name)

            # Test linear/logistic model
            regression_type = regression_models[bet_type]
            model_name = f"{sport}_{regression_type}_{bet_type}_latest.joblib"
            model_path = models_dir / model_name

            total_models += 1

            if not model_path.exists():
                print(f"  [X] {model_name} - NOT FOUND")
                failed_models.append(model_name)
                continue

            try:
                model = joblib.load(model_path)

                # Get feature count
                if sport == 'nhl':
                    n_features = {'totals': 24, 'spreads': 29, 'moneyline': 34}
                elif sport == 'ncaab':
                    n_features = {'totals': 25, 'spreads': 27, 'moneyline': 34}
                else:  # nba
                    n_features = {'totals': 32, 'spreads': 38, 'moneyline': 42}

                sample_features = np.zeros((1, n_features[bet_type]))

                if bet_type == 'moneyline':
                    pred = model.predict(sample_features)
                    proba = model.predict_proba(sample_features)
                    print(f"  [OK] {model_name} (pred={pred[0]}, proba={proba[0][1]:.3f})")
                else:
                    pred = model.predict(sample_features)
                    print(f"  [OK] {model_name} (pred={pred[0]:.2f})")

                loaded_models += 1

            except Exception as e:
                print(f"  [X] {model_name} - ERROR: {e}")
                failed_models.append(model_name)

    # Verify metadata files
    print("\n" + "=" * 60)
    print("VERIFYING METADATA FILES")
    print("=" * 60)

    for sport in sports:
        for bet_type in bet_types:
            metadata_name = f"{sport}_{bet_type}_metadata_latest.joblib"
            metadata_path = models_dir / metadata_name

            if not metadata_path.exists():
                print(f"  [X] {metadata_name} - NOT FOUND")
                failed_models.append(metadata_name)
                continue

            try:
                metadata = joblib.load(metadata_path)

                # Check required fields
                assert 'feature_names' in metadata
                assert 'training_date' in metadata
                assert 'training_stats' in metadata

                print(f"  [OK] {metadata_name}")
                print(f"      Training date: {metadata['training_date']}")
                print(f"      Features: {len(metadata['feature_names'])}")
                print(f"      Models: {', '.join(metadata['training_stats'].keys())}")

            except Exception as e:
                print(f"  [X] {metadata_name} - ERROR: {e}")
                failed_models.append(metadata_name)

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Total models expected: 36")
    print(f"Models loaded successfully: {loaded_models}/36")
    print(f"Success rate: {loaded_models/36*100:.1f}%")

    if failed_models:
        print(f"\n[X] FAILED ({len(failed_models)}):")
        for model in failed_models:
            print(f"  - {model}")
        return False
    else:
        print("\n[OK] ALL MODELS VERIFIED SUCCESSFULLY!")
        return True


if __name__ == "__main__":
    success = verify_models()
    exit(0 if success else 1)
