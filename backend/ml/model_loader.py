"""
Model Loader Utility

Centralized loader for all 60 trained ML models across 5 sports.
Handles model loading, validation, and ensemble predictions.

Usage:
    from backend.ml.model_loader import ModelLoader

    loader = ModelLoader()

    # Load single model
    model = loader.load_model('nba', 'totals', 'random_forest')

    # Load all models for ensemble
    models = loader.load_all_models('nba', 'totals')

    # Get ensemble prediction
    prediction = loader.get_ensemble_prediction('nba', 'totals', features)
"""

import joblib
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple

logger = logging.getLogger(__name__)


class ModelLoader:
    """Load and manage ML models for sports betting predictions"""

    # Supported sports
    SPORTS = ['nhl', 'ncaab', 'nba', 'nfl', 'ncaaf']

    # Bet types
    BET_TYPES = ['totals', 'spreads', 'moneyline']

    # Model algorithms
    ALGORITHMS = ['random_forest', 'xgboost', 'lightgbm']

    # Additional algorithms for specific bet types
    REGRESSION_ALGORITHMS = ALGORITHMS + ['linear_regression']
    CLASSIFICATION_ALGORITHMS = ALGORITHMS + ['logistic_regression']

    # Feature counts by sport and bet type
    FEATURE_COUNTS = {
        'nhl': {'totals': 24, 'spreads': 29, 'moneyline': 34},
        'ncaab': {'totals': 25, 'spreads': 27, 'moneyline': 34},
        'nba': {'totals': 32, 'spreads': 38, 'moneyline': 42},
        'nfl': {'totals': 21, 'spreads': 25, 'moneyline': 29},
        'ncaaf': {'totals': 24, 'spreads': 29, 'moneyline': 33},
    }

    def __init__(self, models_dir: Path = None):
        """
        Initialize model loader

        Args:
            models_dir: Directory containing .joblib model files
        """
        if models_dir is None:
            models_dir = Path(__file__).parent / "models"

        self.models_dir = models_dir
        self._model_cache = {}  # Cache loaded models

        if not self.models_dir.exists():
            raise FileNotFoundError(f"Models directory not found: {self.models_dir}")

        logger.info(f"ModelLoader initialized with models_dir: {self.models_dir}")

    def load_model(self, sport: str, bet_type: str, algorithm: str):
        """
        Load a single trained model

        Args:
            sport: 'nhl', 'ncaab', 'nba', 'nfl', or 'ncaaf'
            bet_type: 'totals', 'spreads', or 'moneyline'
            algorithm: 'random_forest', 'xgboost', 'lightgbm', 'linear_regression', or 'logistic_regression'

        Returns:
            Loaded scikit-learn/xgboost/lightgbm model

        Raises:
            ValueError: If invalid sport, bet_type, or algorithm
            FileNotFoundError: If model file doesn't exist
        """
        # Validate inputs
        if sport not in self.SPORTS:
            raise ValueError(f"Invalid sport: {sport}. Must be one of {self.SPORTS}")

        if bet_type not in self.BET_TYPES:
            raise ValueError(f"Invalid bet_type: {bet_type}. Must be one of {self.BET_TYPES}")

        # Check if algorithm is valid for bet type
        if bet_type == 'moneyline':
            valid_algorithms = self.CLASSIFICATION_ALGORITHMS
        else:
            valid_algorithms = self.REGRESSION_ALGORITHMS

        if algorithm not in valid_algorithms:
            raise ValueError(f"Invalid algorithm: {algorithm} for {bet_type}. Must be one of {valid_algorithms}")

        # Check cache first
        cache_key = f"{sport}_{algorithm}_{bet_type}"
        if cache_key in self._model_cache:
            logger.debug(f"Loaded {cache_key} from cache")
            return self._model_cache[cache_key]

        # Load from file
        model_filename = f"{sport}_{algorithm}_{bet_type}_latest.joblib"
        model_path = self.models_dir / model_filename

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        try:
            model = joblib.load(model_path)
            self._model_cache[cache_key] = model
            logger.info(f"Loaded model: {model_filename}")
            return model
        except Exception as e:
            logger.error(f"Error loading model {model_filename}: {e}")
            raise

    def load_all_models(self, sport: str, bet_type: str) -> Dict[str, any]:
        """
        Load all 4 models for a sport/bet_type combination (for ensemble)

        Args:
            sport: 'nhl', 'ncaab', 'nba', 'nfl', or 'ncaaf'
            bet_type: 'totals', 'spreads', or 'moneyline'

        Returns:
            Dictionary of {algorithm: model}
        """
        if bet_type == 'moneyline':
            algorithms = self.CLASSIFICATION_ALGORITHMS
        else:
            algorithms = self.REGRESSION_ALGORITHMS

        models = {}
        for algorithm in algorithms:
            try:
                models[algorithm] = self.load_model(sport, bet_type, algorithm)
            except FileNotFoundError:
                logger.warning(f"Model not found: {sport}_{algorithm}_{bet_type}")

        return models

    def load_metadata(self, sport: str, bet_type: str) -> Dict:
        """
        Load metadata for a sport/bet_type combination

        Args:
            sport: 'nhl', 'ncaab', 'nba', 'nfl', or 'ncaaf'
            bet_type: 'totals', 'spreads', or 'moneyline'

        Returns:
            Dictionary with training stats, feature names, etc.
        """
        metadata_filename = f"{sport}_{bet_type}_metadata_latest.joblib"
        metadata_path = self.models_dir / metadata_filename

        if not metadata_path.exists():
            logger.warning(f"Metadata file not found: {metadata_path}")
            return {}

        try:
            metadata = joblib.load(metadata_path)
            logger.info(f"Loaded metadata: {metadata_filename}")
            return metadata
        except Exception as e:
            logger.error(f"Error loading metadata {metadata_filename}: {e}")
            return {}

    def get_best_model(self, sport: str, bet_type: str) -> Tuple[str, any]:
        """
        Get the best performing model for a sport/bet_type

        Based on documented performance benchmarks:
        - Random Forest is best for most categories
        - XGBoost for NBA moneyline
        - LightGBM for NFL moneyline

        Args:
            sport: 'nhl', 'ncaab', 'nba', 'nfl', or 'ncaaf'
            bet_type: 'totals', 'spreads', or 'moneyline'

        Returns:
            Tuple of (algorithm_name, loaded_model)
        """
        # Best model mappings (from performance benchmarks)
        best_models = {
            'nhl': {
                'totals': 'linear_regression',
                'spreads': 'random_forest',
                'moneyline': 'random_forest'
            },
            'ncaab': {
                'totals': 'random_forest',
                'spreads': 'random_forest',
                'moneyline': 'random_forest'
            },
            'nba': {
                'totals': 'random_forest',
                'spreads': 'random_forest',
                'moneyline': 'xgboost'
            },
            'nfl': {
                'totals': 'random_forest',
                'spreads': 'random_forest',
                'moneyline': 'lightgbm'
            },
            'ncaaf': {
                'totals': 'linear_regression',
                'spreads': 'random_forest',
                'moneyline': 'random_forest'
            }
        }

        algorithm = best_models[sport][bet_type]
        model = self.load_model(sport, bet_type, algorithm)

        return algorithm, model

    def get_ensemble_prediction(
        self,
        sport: str,
        bet_type: str,
        features: np.ndarray,
        method: str = 'mean'
    ) -> Dict:
        """
        Get ensemble prediction from all 4 models

        Args:
            sport: 'nhl', 'ncaab', 'nba', 'nfl', or 'ncaaf'
            bet_type: 'totals', 'spreads', or 'moneyline'
            features: Feature matrix (n_samples, n_features)
            method: 'mean' (average all), 'median', or 'weighted' (by R²)

        Returns:
            Dictionary with:
                - prediction: Ensemble prediction
                - individual_predictions: Dict of {algorithm: prediction}
                - std: Standard deviation of predictions
                - agreement: Percentage of models agreeing (for classification)
        """
        models = self.load_all_models(sport, bet_type)

        if not models:
            raise ValueError(f"No models found for {sport} {bet_type}")

        # Validate feature count
        expected_features = self.FEATURE_COUNTS[sport][bet_type]
        if features.shape[1] != expected_features:
            raise ValueError(
                f"Expected {expected_features} features for {sport} {bet_type}, "
                f"got {features.shape[1]}"
            )

        predictions = {}
        probabilities = {}

        # Get predictions from each model
        for algorithm, model in models.items():
            pred = model.predict(features)
            predictions[algorithm] = pred[0]

            # For classification, also get probabilities
            if bet_type == 'moneyline' and hasattr(model, 'predict_proba'):
                proba = model.predict_proba(features)
                probabilities[algorithm] = proba[0][1]  # Probability of class 1 (home win)

        # Compute ensemble prediction
        pred_values = np.array(list(predictions.values()))

        # Filter out extreme outliers using IQR method (more robust than std dev)
        if len(pred_values) > 2:
            q1 = np.percentile(pred_values, 25)
            q3 = np.percentile(pred_values, 75)
            iqr = q3 - q1

            # Filter out values > 3 * IQR from Q1/Q3 (very conservative)
            lower_bound = q1 - 3 * iqr
            upper_bound = q3 + 3 * iqr

            mask = (pred_values >= lower_bound) & (pred_values <= upper_bound)
            filtered_values = pred_values[mask]

            # Only use filtered values if we didn't filter out everything
            if len(filtered_values) > 0:
                pred_values = filtered_values
                logger.debug(f"Filtered ensemble from {len(pred_values)} to {len(filtered_values)} predictions")

        if method == 'mean':
            ensemble_pred = np.mean(pred_values)
        elif method == 'median':
            ensemble_pred = np.median(pred_values)
        elif method == 'weighted':
            # Weight by R² from metadata (TODO: implement)
            ensemble_pred = np.mean(pred_values)  # Fallback to mean for now
        else:
            raise ValueError(f"Unknown ensemble method: {method}")

        result = {
            'prediction': ensemble_pred,
            'individual_predictions': predictions,
            'std': np.std(pred_values),
            'min': np.min(pred_values),
            'max': np.max(pred_values)
        }

        # For classification, add agreement metrics
        if bet_type == 'moneyline':
            # Count how many models agree on prediction
            pred_classes = [1 if p > 0.5 else 0 for p in pred_values]
            agreement = np.mean(pred_classes)  # Percentage predicting class 1

            result['agreement'] = agreement
            result['ensemble_probability'] = np.mean(list(probabilities.values()))
            result['individual_probabilities'] = probabilities

        return result

    def validate_features(self, sport: str, bet_type: str, features: np.ndarray) -> bool:
        """
        Validate that features have correct shape

        Args:
            sport: 'nhl', 'ncaab', 'nba', 'nfl', or 'ncaaf'
            bet_type: 'totals', 'spreads', or 'moneyline'
            features: Feature matrix to validate

        Returns:
            True if valid, raises ValueError otherwise
        """
        expected_features = self.FEATURE_COUNTS[sport][bet_type]

        if features.ndim != 2:
            raise ValueError(f"Features must be 2D array, got {features.ndim}D")

        if features.shape[1] != expected_features:
            raise ValueError(
                f"Expected {expected_features} features for {sport} {bet_type}, "
                f"got {features.shape[1]}"
            )

        return True

    def get_all_sports_models(self, bet_type: str) -> Dict[str, Dict]:
        """
        Load best model for each sport for a given bet type

        Args:
            bet_type: 'totals', 'spreads', or 'moneyline'

        Returns:
            Dictionary of {sport: {'algorithm': name, 'model': model}}
        """
        models = {}

        for sport in self.SPORTS:
            try:
                algorithm, model = self.get_best_model(sport, bet_type)
                models[sport] = {
                    'algorithm': algorithm,
                    'model': model
                }
            except Exception as e:
                logger.warning(f"Could not load {sport} {bet_type}: {e}")

        return models

    def clear_cache(self):
        """Clear the model cache (useful for testing/development)"""
        self._model_cache = {}
        logger.info("Model cache cleared")


def load_model(sport: str, bet_type: str, algorithm: str):
    """
    Convenience function to load a single model

    Args:
        sport: 'nhl', 'ncaab', 'nba', 'nfl', or 'ncaaf'
        bet_type: 'totals', 'spreads', or 'moneyline'
        algorithm: Model algorithm name

    Returns:
        Loaded model
    """
    loader = ModelLoader()
    return loader.load_model(sport, bet_type, algorithm)


def load_best_model(sport: str, bet_type: str):
    """
    Convenience function to load the best model for a sport/bet_type

    Args:
        sport: 'nhl', 'ncaab', 'nba', 'nfl', or 'ncaaf'
        bet_type: 'totals', 'spreads', or 'moneyline'

    Returns:
        Tuple of (algorithm_name, loaded_model)
    """
    loader = ModelLoader()
    return loader.get_best_model(sport, bet_type)


def get_ensemble_prediction(sport: str, bet_type: str, features: np.ndarray):
    """
    Convenience function to get ensemble prediction

    Args:
        sport: 'nhl', 'ncaab', 'nba', 'nfl', or 'ncaaf'
        bet_type: 'totals', 'spreads', or 'moneyline'
        features: Feature matrix (n_samples, n_features)

    Returns:
        Dictionary with ensemble prediction and statistics
    """
    loader = ModelLoader()
    return loader.get_ensemble_prediction(sport, bet_type, features)


def get_available_models():
    """
    Get list of all available models

    Returns:
        List of model keys in format: "sport_algorithm_bettype"
    """
    loader = ModelLoader()
    models = []

    for sport in loader.SPORTS:
        for bet_type in loader.BET_TYPES:
            if bet_type == 'moneyline':
                algorithms = loader.CLASSIFICATION_ALGORITHMS
            else:
                algorithms = loader.REGRESSION_ALGORITHMS

            for algorithm in algorithms:
                model_key = f"{sport}_{algorithm}_{bet_type}"
                model_filename = f"{sport}_{algorithm}_{bet_type}_latest.joblib"
                model_path = loader.models_dir / model_filename

                if model_path.exists():
                    models.append(model_key)

    return models


if __name__ == "__main__":
    # Example usage
    import logging
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("MODEL LOADER DEMO")
    print("=" * 60)

    loader = ModelLoader()

    # Test 1: Load single model
    print("\n1. Loading NBA Random Forest Totals model:")
    model = loader.load_model('nba', 'totals', 'random_forest')
    print(f"   Model type: {type(model).__name__}")

    # Test 2: Load all models for ensemble
    print("\n2. Loading all NBA totals models:")
    models = loader.load_all_models('nba', 'totals')
    for algo, model in models.items():
        print(f"   {algo}: {type(model).__name__}")

    # Test 3: Get best model
    print("\n3. Getting best NBA totals model:")
    algo, model = loader.get_best_model('nba', 'totals')
    print(f"   Best algorithm: {algo}")
    print(f"   Model type: {type(model).__name__}")

    # Test 4: Ensemble prediction (dummy features)
    print("\n4. Testing ensemble prediction (dummy data):")
    features = np.zeros((1, 32))  # NBA totals has 32 features
    result = loader.get_ensemble_prediction('nba', 'totals', features)
    print(f"   Ensemble prediction: {result['prediction']:.2f}")
    print(f"   Std deviation: {result['std']:.2f}")
    print(f"   Individual predictions:")
    for algo, pred in result['individual_predictions'].items():
        print(f"     {algo}: {pred:.2f}")

    # Test 5: Load metadata
    print("\n5. Loading NBA totals metadata:")
    metadata = loader.load_metadata('nba', 'totals')
    if metadata:
        print(f"   Training samples: {metadata.get('n_train_samples', 'N/A')}")
        print(f"   Training date: {metadata.get('training_date', 'N/A')}")

    print("\n" + "=" * 60)
    print("MODEL LOADER DEMO COMPLETE")
    print("=" * 60)
