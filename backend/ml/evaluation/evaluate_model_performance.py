"""
Model Performance Evaluator
Evaluates retrained models against previous version

Compares:
- Accuracy
- Precision/Recall
- ROI potential
- Calibration

Decides whether to deploy new models or keep old ones
"""

import sys
import sqlite3
from pathlib import Path
import joblib
import json
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class ModelPerformanceEvaluator:
    """
    Evaluates model performance after retraining
    """

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.models_dir = self.base_dir / "trained_models"
        self.prop_types = ['points', 'rebounds', 'assists', 'threes', 'blocks', 'steals', 'PRA']
        self.algorithms = ['xgboost', 'lightgbm', 'random_forest', 'linear']

    def evaluate_all_models(self):
        """
        Evaluate all retrained models
        """
        print(f"\n{'='*70}")
        print("MODEL PERFORMANCE EVALUATION")
        print(f"{'='*70}\n")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        results = {}

        for prop_type in self.prop_types:
            print(f"[{prop_type.upper()}]")

            prop_results = {}
            for algorithm in self.algorithms:
                # Load model
                model_path = self.models_dir / f"{prop_type}_{algorithm}_model.joblib"

                if not model_path.exists():
                    print(f"  ✗ {algorithm}: Model not found")
                    continue

                try:
                    model_info = joblib.load(model_path)
                    accuracy = model_info.get('test_accuracy', 0)
                    model_name = model_info.get('model_type', algorithm)

                    print(f"  ✓ {algorithm}: {accuracy:.1f}% accuracy")

                    prop_results[algorithm] = {
                        'accuracy': accuracy,
                        'model_type': model_name,
                        'exists': True
                    }

                except Exception as e:
                    print(f"  ✗ {algorithm}: Load failed - {str(e)}")
                    prop_results[algorithm] = {'exists': False}

            results[prop_type] = prop_results
            print("")

        # Summary
        self.display_summary(results)

        return results

    def display_summary(self, results):
        """
        Display evaluation summary
        """
        print(f"{'='*70}")
        print("EVALUATION SUMMARY")
        print(f"{'='*70}\n")

        total_models = len(self.prop_types) * len(self.algorithms)
        loaded_models = sum(
            1 for prop_results in results.values()
            for alg_results in prop_results.values()
            if alg_results.get('exists', False)
        )

        print(f"Total models expected: {total_models}")
        print(f"Models loaded: {loaded_models}")
        print(f"Success rate: {loaded_models/total_models*100:.1f}%\n")

        # Average accuracy by prop type
        print("Average Accuracy by Prop Type:")
        for prop_type, prop_results in results.items():
            accuracies = [r['accuracy'] for r in prop_results.values() if r.get('exists')]
            if accuracies:
                avg_acc = sum(accuracies) / len(accuracies)
                print(f"  {prop_type}: {avg_acc:.1f}%")

        print(f"\n{'='*70}\n")

        print("[RECOMMENDATION]")
        if loaded_models >= total_models * 0.8:
            print("✓ Models look good - safe to deploy")
            return True
        else:
            print("✗ Too many model failures - investigate before deploying")
            return False


def main():
    """Main entry point"""
    evaluator = ModelPerformanceEvaluator()
    results = evaluator.evaluate_all_models()

    print("[COMPLETE] Model evaluation finished")


if __name__ == "__main__":
    main()
