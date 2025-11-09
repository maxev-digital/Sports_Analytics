"""Quick profitability simulation runner"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from analysis.regression_profitability_simulator import RegressionProfitabilitySimulator

# Run simulation with 1.5 sigma threshold
simulator = RegressionProfitabilitySimulator(
    std_deviation=17.08,
    threshold_sigma=1.5
)

results = simulator.run_simulation(games_limit=300)

print("\n" + "="*80)
print("SIMULATION COMPLETE")
print("="*80)
