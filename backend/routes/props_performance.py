"""
Player Props Performance API Routes
Tracks ML props model performance, accuracy, and ROI over time
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timedelta
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/props-performance", tags=["props-performance"])

# Use relative path from backend directory
DB_PATH = Path(__file__).parent.parent / "data" / "player_props.db"


@router.get("/overview")
async def get_props_performance_overview(
    prop_type: Optional[str] = None,
    days: int = 30
):
    """
    Get overall props model performance metrics

    Args:
        prop_type: Filter by prop type (points, rebounds, assists, blocks, steals, threes, PRA)
        days: Number of days of history to include (default 30)

    Returns:
        Overall performance metrics including win rate, ROI, accuracy by prop type
    """
    try:
        if not DB_PATH.exists():
            return {
                "error": "Props database not found",
                "total_predictions": 0
            }

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Date filter
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        # Build query
        where_clauses = ["p.game_date >= ?"]
        params = [cutoff_date]

        if prop_type:
            where_clauses.append("p.prop_type = ?")
            params.append(prop_type)

        where_sql = " AND ".join(where_clauses)

        # Get overall stats
        query = f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN p.result = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN p.result = 'LOSS' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN p.result = 'PUSH' THEN 1 ELSE 0 END) as pushes,
                AVG(ABS(p.edge_pct)) as avg_edge
            FROM player_props_predictions p
            WHERE {where_sql}
              AND p.result IS NOT NULL
              AND p.recommendation != 'PASS'
        """

        cursor.execute(query, params)
        row = cursor.fetchone()

        total = row['total'] or 0
        wins = row['wins'] or 0
        losses = row['losses'] or 0
        pushes = row['pushes'] or 0
        avg_edge = row['avg_edge'] or 0

        win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0
        roi = ((wins * 0.91) - losses) / total * 100 if total > 0 else 0  # -110 odds
        units_won = (wins * 0.91) - losses

        # Performance by prop type
        prop_type_query = f"""
            SELECT
                p.prop_type,
                COUNT(*) as total,
                SUM(CASE WHEN p.result = 'WIN' THEN 1 ELSE 0 END) as wins
            FROM player_props_predictions p
            WHERE {where_sql}
              AND p.result IS NOT NULL
              AND p.recommendation != 'PASS'
            GROUP BY p.prop_type
        """

        cursor.execute(prop_type_query, params)
        prop_stats = {}
        for row in cursor.fetchall():
            pt = row['prop_type']
            pt_total = row['total']
            pt_wins = row['wins']
            pt_losses = pt_total - pt_wins
            prop_stats[pt] = {
                "total": pt_total,
                "wins": pt_wins,
                "win_rate": pt_wins / (pt_total - 0) if pt_total > 0 else 0  # Simplified
            }

        # Performance by confidence
        conf_query = f"""
            SELECT
                CASE
                    WHEN p.confidence >= 70 THEN 'high'
                    WHEN p.confidence >= 50 THEN 'medium'
                    ELSE 'low'
                END as conf_level,
                COUNT(*) as total,
                SUM(CASE WHEN p.result = 'WIN' THEN 1 ELSE 0 END) as wins
            FROM player_props_predictions p
            WHERE {where_sql}
              AND p.result IS NOT NULL
              AND p.recommendation != 'PASS'
            GROUP BY conf_level
        """

        cursor.execute(conf_query, params)
        confidence_stats = {}
        for row in cursor.fetchall():
            conf = row['conf_level']
            c_total = row['total']
            c_wins = row['wins']
            c_losses = c_total - c_wins
            confidence_stats[conf] = {
                "total": c_total,
                "wins": c_wins,
                "win_rate": c_wins / c_total if c_total > 0 else 0,
                "roi": ((c_wins * 0.91) - c_losses) / c_total * 100 if c_total > 0 else 0
            }

        conn.close()

        return {
            "summary": {
                "total_predictions": total,
                "wins": wins,
                "losses": losses,
                "pushes": pushes,
                "win_rate": round(win_rate, 4),
                "roi": round(roi, 2),
                "avg_edge": round(avg_edge, 2),
                "units_won": round(units_won, 2)
            },
            "by_prop_type": prop_stats,
            "by_confidence": confidence_stats,
            "filters": {
                "prop_type": prop_type or "all",
                "days": days
            },
            "generated_at": datetime.utcnow().isoformat() + 'Z'
        }

    except Exception as e:
        logger.error(f"Error generating props performance overview: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_props_performance_history(
    prop_type: Optional[str] = None,
    days: int = 90
):
    """
    Get historical props performance data over time (for charts)
    """
    try:
        if not DB_PATH.exists():
            return {"history": []}

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        where_clauses = ["p.game_date >= ?"]
        params = [cutoff_date]

        if prop_type:
            where_clauses.append("p.prop_type = ?")
            params.append(prop_type)

        where_sql = " AND ".join(where_clauses)

        query = f"""
            SELECT
                p.game_date as period,
                COUNT(*) as predictions,
                SUM(CASE WHEN p.result = 'WIN' THEN 1 ELSE 0 END) as wins
            FROM player_props_predictions p
            WHERE {where_sql}
              AND p.result IS NOT NULL
              AND p.recommendation != 'PASS'
            GROUP BY p.game_date
            ORDER BY p.game_date ASC
        """

        cursor.execute(query, params)

        history = []
        for row in cursor.fetchall():
            preds = row['predictions']
            w = row['wins']
            l = preds - w
            wr = w / preds if preds > 0 else 0
            roi_val = ((w * 0.91) - l) / preds * 100 if preds > 0 else 0
            units = (w * 0.91) - l

            history.append({
                "period": row['period'],
                "predictions": preds,
                "wins": w,
                "win_rate": round(wr, 4),
                "roi": round(roi_val, 2),
                "units_won": round(units, 2)
            })

        conn.close()

        return {"history": history}

    except Exception as e:
        logger.error(f"Error generating props performance history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions")
async def get_props_predictions(
    prop_type: Optional[str] = None,
    result: Optional[str] = None,
    limit: int = 50
):
    """
    Get individual prop predictions with results
    """
    try:
        if not DB_PATH.exists():
            return {"predictions": []}

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        where_clauses = ["p.result IS NOT NULL", "p.recommendation != 'PASS'"]
        params = []

        if prop_type:
            where_clauses.append("p.prop_type = ?")
            params.append(prop_type)

        if result:
            where_clauses.append("p.result = ?")
            params.append(result.upper())

        where_sql = " AND ".join(where_clauses)
        params.append(limit)

        query = f"""
            SELECT
                p.prediction_date,
                p.game_date,
                p.player_name,
                p.team,
                p.opponent,
                p.prop_type,
                p.market_line,
                p.predicted_value,
                p.actual_value,
                p.edge_pct,
                p.recommendation,
                p.confidence,
                p.result
            FROM player_props_predictions p
            WHERE {where_sql}
            ORDER BY p.game_date DESC, ABS(p.edge_pct) DESC
            LIMIT ?
        """

        cursor.execute(query, params)

        predictions = []
        for row in cursor.fetchall():
            predictions.append({
                "prediction_date": row['prediction_date'],
                "game_date": row['game_date'],
                "player_name": row['player_name'],
                "team": row['team'],
                "opponent": row['opponent'],
                "prop_type": row['prop_type'],
                "market_line": row['market_line'],
                "predicted_value": round(row['predicted_value'], 2) if row['predicted_value'] else None,
                "actual_value": round(row['actual_value'], 2) if row['actual_value'] else None,
                "edge_pct": round(row['edge_pct'], 2) if row['edge_pct'] else None,
                "recommendation": row['recommendation'],
                "confidence": row['confidence'],
                "result": row['result']
            })

        conn.close()

        return {"predictions": predictions}

    except Exception as e:
        logger.error(f"Error fetching props predictions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
