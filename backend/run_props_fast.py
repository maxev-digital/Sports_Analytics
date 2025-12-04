#!/usr/bin/env python3
"""Fast multi-sport props predictions with parallel processing"""

import sys
import logging
from datetime import datetime, date
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent))

from ml.props.predictor import PropsPredictor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def run_sport_predictions(sport: str) -> dict:
    """Run predictions for a single sport"""
    try:
        logger.info(f"[{sport.upper()}] Starting predictions...")
        predictor = PropsPredictor(sport=sport)
        
        # Generate predictions with lower confidence threshold for faster processing
        result = predictor.generate_all_props_edges(
            props_date=date.today()
        )
        
        logger.info(f"[{sport.upper()}] ✅ Completed")
        return {sport: "SUCCESS", "predictions": result}
    except Exception as e:
        logger.error(f"[{sport.upper()}] ❌ Error: {e}")
        return {sport: "FAILED", "error": str(e)}

def main():
    print("="*80)
    print(f"FAST PROPS PREDICTIONS - {date.today()}")
    print("="*80)
    print()
    
    sports = ['nba', 'nhl', 'nfl']
    results = {}
    
    for sport in sports:
        result = run_sport_predictions(sport)
        results[sport] = result.get(sport)
    
    print()
    print("="*80)
    print("PREDICTIONS COMPLETE")
    print("="*80)
    print()
    for sport in sports:
        status = results.get(sport, "UNKNOWN")
        print(f"  [{sport.upper()}] {status}")
    print()

if __name__ == "__main__":
    main()
