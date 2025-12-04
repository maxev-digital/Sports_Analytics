#!/usr/bin/env python3
"""
Multi-Sport Player Props Prediction Workflow
Generates predictions for NBA, NHL, and NFL
"""

import sys
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from ml.props.predictor import PropsPredictor

def run_multi_sport_predictions():
    """Generate predictions for all sports"""
    
    sports = ['nba', 'nhl', 'nfl']
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\n{'='*80}")
    print(f"MULTI-SPORT PLAYER PROPS PREDICTIONS - {today}")
    print(f"{'='*80}\n")
    
    results = {}
    
    for sport in sports:
        print(f"\n[{sport.upper()}] Starting predictions...")
        try:
            predictor = PropsPredictor(sport=sport)
            result = predictor.generate_all_props_edges()
            results[sport] = result
            print(f"[{sport.upper()}] ✅ Predictions generated successfully")
        except Exception as e:
            logger.error(f"[{sport.upper()}] ❌ Error: {e}")
            results[sport] = {'error': str(e)}
    
    print(f"\n{'='*80}")
    print(f"MULTI-SPORT PREDICTIONS COMPLETE")
    print(f"{'='*80}\n")
    
    for sport, result in results.items():
        if 'error' in result:
            print(f"  [{sport.upper()}] FAILED: {result['error']}")
        else:
            print(f"  [{sport.upper()}] SUCCESS")
    
    return results

if __name__ == "__main__":
    run_multi_sport_predictions()
