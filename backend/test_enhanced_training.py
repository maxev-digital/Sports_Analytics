import sys
import numpy as np
from pathlib import Path
sys.path.append('/root/sporttrader/backend')

from ml.training.enhanced_multi_model_trainer import EnhancedMultiModelTrainer

# Generate synthetic test data
print("Generating test data...")
X_train = np.random.randn(1000, 42)  # 1000 samples, 42 features (current)
y_train = np.random.randn(1000) * 10 + 220  # Target ~220

print("Testing enhanced multi-model trainer...")
trainer = EnhancedMultiModelTrainer(sport='test', bet_type='totals')
models = trainer.train_all_models(X_train, y_train)

print(f"SUCCESS: Trained {len(models)} models")
for name in models.keys():
    print(f"  ✓ {name}")

