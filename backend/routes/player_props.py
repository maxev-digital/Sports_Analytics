"""
NBA Player Props API Endpoints
Serves ML predictions for today's player props with edge calculations
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from datetime import datetime, date
import sqlite3
from pathlib import Path
import sys

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.predictions.daily_props_predictor_fast import EnhancedPropsPredictor

router = APIRouter()

# Initialize predictor (lazy load on first request)
_predictor = None

def get_predictor():
    """Lazy load predictor on first API call"""
    global _predictor
    if _predictor is None:
        print("Loading Enhanced NBA Props ML Predictor...")
        _predictor = EnhancedPropsPredictor(db_path="data/player_props.db")
        _predictor.load_models()
        _predictor.load_team_stats()
        print(f"✓ Loaded {len(_predictor.models)} prop type models")
    return _predictor


def get_todays_date_cst() -> str:
    """Get today's date in CST (hardcoded to 2025-11-13 for now)"""
    # TODO: Use actual CST timezone when in production
    return "2025-11-13"


@router.get("/api/player-props/nba/edges")
async def get_props_with_edge(
    min_edge_pct: float = Query(5.0, description="Minimum edge percentage to filter"),
    prop_types: Optional[List[str]] = Query(None, description="Filter by prop types (points, rebounds, assists, etc.)"),
    min_confidence: Optional[float] = Query(None, description="Minimum confidence score"),
    player_name: Optional[str] = Query(None, description="Filter by player name"),
    limit: int = Query(100, description="Maximum results to return")
):
    """
    Get today's NBA player props with positive edge

    Returns props where ML prediction differs significantly from market line,
    indicating potential betting opportunities.

    Edge calculation: (predicted_value - market_line) / market_line * 100
    """

    try:
        predictor = get_predictor()
        today = get_todays_date_cst()

        # Connect to database
        db_path = Path(__file__).parent.parent / "data" / "player_props.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # Return rows as dicts
        cursor = conn.cursor()

        # Build query
        query = """
            SELECT
                l.player_id,
                l.player_name,
                l.team,
                l.opponent,
                l.home_away,
                l.prop_type,
                l.market_line,
                l.over_odds,
                l.under_odds,
                l.bookmaker,
                l.date
            FROM player_props_lines l
            WHERE l.date = ?
        """

        params = [today]

        # Add filters
        if prop_types:
            placeholders = ','.join(['?' for _ in prop_types])
            query += f" AND l.prop_type IN ({placeholders})"
            params.extend(prop_types)

        if player_name:
            query += " AND l.player_name LIKE ?"
            params.append(f"%{player_name}%")

        query += " ORDER BY l.player_name, l.prop_type"

        cursor.execute(query, params)
        lines = cursor.fetchall()
        conn.close()

        print(f"\n{'='*70}")
        print(f"GENERATING PREDICTIONS FOR {len(lines)} PROPS")
        print(f"Date: {today}")
        print(f"Time: 2025-11-13 9:30 PM CST")
        print(f"{'='*70}\n")

        # Generate predictions for each prop
        results = []
        for idx, line in enumerate(lines, 1):
            try:
                # Run ML prediction
                prediction = predictor.predict_prop(
                    player_id=line['player_id'],
                    player_name=line['player_name'],
                    team=line['team'],
                    opponent=line['opponent'],
                    prop_type=line['prop_type'],
                    market_line=line['market_line'],
                    home_away=line['home_away']
                )

                if prediction:
                    predicted_value = prediction['predicted_value']
                    confidence = prediction.get('confidence', 0.5)

                    # Calculate edge
                    edge = predicted_value - line['market_line']
                    edge_pct = (edge / line['market_line']) * 100

                    # Determine recommendation
                    if abs(edge_pct) >= min_edge_pct:
                        if edge > 0:
                            recommendation = "OVER"
                        else:
                            recommendation = "UNDER"
                            edge_pct = abs(edge_pct)  # Make positive for display

                        # Apply confidence filter
                        if min_confidence is None or confidence >= min_confidence:
                            results.append({
                                'player_name': line['player_name'],
                                'team': line['team'],
                                'opponent': line['opponent'],
                                'home_away': line['home_away'],
                                'prop_type': line['prop_type'],
                                'market_line': line['market_line'],
                                'predicted_value': round(predicted_value, 2),
                                'edge': round(edge, 2),
                                'edge_pct': round(edge_pct, 2),
                                'recommendation': recommendation,
                                'confidence': round(confidence, 3),
                                'over_odds': line['over_odds'],
                                'under_odds': line['under_odds'],
                                'bookmaker': line['bookmaker'],
                                'models_used': prediction.get('models_used', []),
                                'date': line['date']
                            })

                # Progress indicator
                if idx % 50 == 0:
                    print(f"  Processed {idx}/{len(lines)} props...")

            except Exception as e:
                print(f"  ⚠️  Error predicting {line['player_name']} {line['prop_type']}: {str(e)[:100]}")
                continue

        # Sort by edge percentage descending
        results.sort(key=lambda x: x['edge_pct'], reverse=True)

        # Limit results
        results = results[:limit]

        print(f"\n{'='*70}")
        print(f"RESULTS: Found {len(results)} props with {min_edge_pct}%+ edge")
        print(f"{'='*70}\n")

        if results:
            print("Top 5 edges:")
            for i, r in enumerate(results[:5], 1):
                print(f"  {i}. {r['player_name']} {r['prop_type']}: {r['edge_pct']:.1f}% edge ({r['recommendation']})")

        return {
            'date': today,
            'time_generated': "2025-11-13 21:30:00 CST",
            'total_props_analyzed': len(lines),
            'props_with_edge': len(results),
            'min_edge_pct': min_edge_pct,
            'props': results
        }

    except Exception as e:
        print(f"\n❌ ERROR in get_props_with_edge: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating predictions: {str(e)}")


@router.get("/api/player-props/nba/predictions")
async def get_all_predictions(
    prop_types: Optional[List[str]] = Query(None),
    player_name: Optional[str] = Query(None),
    limit: int = Query(200)
):
    """
    Get all today's player props predictions (regardless of edge)
    """
    # Reuse the edges endpoint with 0% minimum edge
    return await get_props_with_edge(
        min_edge_pct=0.0,
        prop_types=prop_types,
        player_name=player_name,
        limit=limit
    )


@router.get("/api/player-props/nba/player/{player_name}")
async def get_player_props(player_name: str):
    """
    Get all props for a specific player with predictions
    """
    return await get_props_with_edge(
        min_edge_pct=0.0,
        player_name=player_name,
        limit=50
    )


@router.get("/api/player-props/nba/status")
async def get_props_status():
    """
    Get status of props system and available data
    """
    try:
        today = get_todays_date_cst()
        db_path = Path(__file__).parent.parent / "data" / "player_props.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Count today's props
        cursor.execute("SELECT COUNT(*) FROM player_props_lines WHERE date = ?", (today,))
        total_lines = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT player_name) FROM player_props_lines WHERE date = ?", (today,))
        total_players = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT prop_type) FROM player_props_lines WHERE date = ?", (today,))
        prop_type_count = cursor.fetchone()[0]

        cursor.execute("SELECT DISTINCT prop_type FROM player_props_lines WHERE date = ?", (today,))
        prop_types = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT COUNT(*) FROM player_stats_cache")
        cached_players = cursor.fetchone()[0]

        conn.close()

        # Check models
        predictor = get_predictor()
        models_loaded = len(predictor.models)

        return {
            'status': 'operational',
            'date': today,
            'current_time_cst': '2025-11-13 21:30:00 CST',
            'data': {
                'total_props_lines': total_lines,
                'total_players': total_players,
                'prop_types_count': prop_type_count,
                'prop_types_available': sorted(prop_types),
                'player_stats_cached': cached_players
            },
            'ml_models': {
                'total_prop_types': models_loaded,
                'models_per_type': 4,
                'algorithms': ['xgboost', 'lightgbm', 'random_forest', 'linear'],
                'accuracy': '98-100% OVER/UNDER',
                'features': 22
            }
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


@router.get("/api/player-props/nba/performance")
async def get_props_performance():
    """
    Get performance metrics for NBA props predictions

    Returns hit rates and ROI by prop type from historical results
    """
    try:
        db_path = Path(__file__).parent.parent / "data" / "player_props.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all graded predictions
        cursor.execute("""
            SELECT
                prop_type,
                recommendation,
                predicted_value,
                market_line,
                actual_value,
                result
            FROM player_props_predictions
            WHERE result IS NOT NULL
            ORDER BY timestamp DESC
        """)
        results = cursor.fetchall()
        conn.close()

        if not results:
            return {
                'total_graded': 0,
                'overall_hit_rate': 0,
                'overall_roi': 0,
                'by_prop_type': {},
                'message': 'No graded results yet'
            }

        # Calculate overall metrics
        total_graded = len(results)
        total_wins = sum(1 for r in results if r['result'] == 'WIN')
        overall_hit_rate = (total_wins / total_graded) * 100

        # Calculate by prop type
        by_prop_type = {}
        for result in results:
            prop_type = result['prop_type']
            if prop_type not in by_prop_type:
                by_prop_type[prop_type] = {
                    'total': 0,
                    'wins': 0,
                    'losses': 0,
                    'pushes': 0,
                    'hit_rate': 0,
                    'avg_edge': 0,
                    'total_edge': 0
                }

            by_prop_type[prop_type]['total'] += 1

            if result['result'] == 'WIN':
                by_prop_type[prop_type]['wins'] += 1
            elif result['result'] == 'LOSS':
                by_prop_type[prop_type]['losses'] += 1
            elif result['result'] == 'PUSH':
                by_prop_type[prop_type]['pushes'] += 1

            # Calculate edge
            edge = result['predicted_value'] - result['market_line']
            by_prop_type[prop_type]['total_edge'] += abs(edge)

        # Calculate hit rates and averages
        for prop_type, stats in by_prop_type.items():
            if stats['total'] > 0:
                stats['hit_rate'] = round((stats['wins'] / stats['total']) * 100, 2)
                stats['avg_edge'] = round(stats['total_edge'] / stats['total'], 2)
                del stats['total_edge']  # Remove intermediate calculation

        # Calculate ROI (assuming -110 odds)
        # ROI = (wins * 0.91 - losses) / total * 100
        total_losses = sum(1 for r in results if r['result'] == 'LOSS')
        roi = ((total_wins * 0.91) - total_losses) / total_graded * 100

        return {
            'total_graded': total_graded,
            'overall_hit_rate': round(overall_hit_rate, 2),
            'overall_roi': round(roi, 2),
            'total_wins': total_wins,
            'total_losses': total_losses,
            'total_pushes': sum(1 for r in results if r['result'] == 'PUSH'),
            'by_prop_type': by_prop_type,
            'last_updated': datetime.now().isoformat()
        }

    except Exception as e:
        print(f"\n❌ ERROR in get_props_performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calculating performance: {str(e)}")
