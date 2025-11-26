"""
Player Props Performance API Routes
Tracks ML props model performance, accuracy, and ROI over time
Aligned with ModelPerformance dashboard patterns
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
    sport: Optional[str] = None,
    prop_type: Optional[str] = None,
    model: Optional[str] = None,
    days: int = 30
):
    """
    Get overall props model performance metrics

    Args:
        sport: Filter by sport (nba, ncaab, nfl, nhl, ncaaf)
        prop_type: Filter by prop type (points, rebounds, assists, blocks, steals, threes, PRA)
        model: Filter by model type (ensemble, xgboost, lightgbm, random_forest, linear_regression)
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

        if sport:
            where_clauses.append("p.sport = ?")
            params.append(sport.lower())

        if prop_type:
            where_clauses.append("p.prop_type = ?")
            params.append(prop_type)

        if model:
            where_clauses.append("p.model_type = ?")
            params.append(model)

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
            GROUP BY p.prop_type
        """

        cursor.execute(prop_type_query, params)
        prop_stats = {}
        for row in cursor.fetchall():
            pt = row['prop_type']
            pt_total = row['total']
            pt_wins = row['wins']
            pt_losses = pt_total - pt_wins
            pt_roi = ((pt_wins * 0.91) - pt_losses) / pt_total * 100 if pt_total > 0 else 0
            prop_stats[pt] = {
                "total": pt_total,
                "wins": pt_wins,
                "win_rate": pt_wins / pt_total if pt_total > 0 else 0,
                "roi": round(pt_roi, 2)
            }

        # Performance by sport
        sport_query = f"""
            SELECT
                COALESCE(p.sport, 'nba') as sport,
                COUNT(*) as total,
                SUM(CASE WHEN p.result = 'WIN' THEN 1 ELSE 0 END) as wins
            FROM player_props_predictions p
            WHERE {where_sql}
              AND p.result IS NOT NULL
            GROUP BY COALESCE(p.sport, 'nba')
        """

        cursor.execute(sport_query, params)
        sport_stats = {}
        for row in cursor.fetchall():
            s = row['sport'] or 'nba'
            s_total = row['total']
            s_wins = row['wins']
            s_losses = s_total - s_wins
            s_roi = ((s_wins * 0.91) - s_losses) / s_total * 100 if s_total > 0 else 0
            sport_stats[s] = {
                "total": s_total,
                "wins": s_wins,
                "win_rate": s_wins / s_total if s_total > 0 else 0,
                "roi": round(s_roi, 2)
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

        # Performance by model
        model_query = f"""
            SELECT
                COALESCE(p.model_type, 'ensemble') as model,
                COUNT(*) as total,
                SUM(CASE WHEN p.result = 'WIN' THEN 1 ELSE 0 END) as wins
            FROM player_props_predictions p
            WHERE {where_sql}
              AND p.result IS NOT NULL
            GROUP BY COALESCE(p.model_type, 'ensemble')
        """

        cursor.execute(model_query, params)
        model_stats = {}
        for row in cursor.fetchall():
            m = row['model'] or 'ensemble'
            m_total = row['total']
            m_wins = row['wins']
            m_losses = m_total - m_wins
            m_roi = ((m_wins * 0.91) - m_losses) / m_total * 100 if m_total > 0 else 0
            model_stats[m] = {
                "total": m_total,
                "wins": m_wins,
                "win_rate": m_wins / m_total if m_total > 0 else 0,
                "roi": round(m_roi, 2)
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
            "by_sport": sport_stats,
            "by_confidence": confidence_stats,
            "by_model": model_stats,
            "filters": {
                "sport": sport or "all",
                "prop_type": prop_type or "all",
                "model": model or "all",
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
    sport: Optional[str] = None,
    prop_type: Optional[str] = None,
    model: Optional[str] = None,
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

        if sport:
            where_clauses.append("p.sport = ?")
            params.append(sport.lower())

        if prop_type:
            where_clauses.append("p.prop_type = ?")
            params.append(prop_type)

        if model:
            where_clauses.append("p.model_type = ?")
            params.append(model)

        where_sql = " AND ".join(where_clauses)

        query = f"""
            SELECT
                p.game_date as period,
                COUNT(*) as predictions,
                SUM(CASE WHEN p.result = 'WIN' THEN 1 ELSE 0 END) as wins
            FROM player_props_predictions p
            WHERE {where_sql}
              AND p.result IS NOT NULL
            GROUP BY p.game_date
            ORDER BY p.game_date ASC
        """

        cursor.execute(query, params)

        history = []
        cumulative_wins = 0
        cumulative_losses = 0

        for row in cursor.fetchall():
            preds = row['predictions']
            w = row['wins']
            l = preds - w

            # Daily stats
            wr = w / preds if preds > 0 else 0
            roi_val = ((w * 0.91) - l) / preds * 100 if preds > 0 else 0
            units = (w * 0.91) - l

            # Cumulative stats
            cumulative_wins += w
            cumulative_losses += l
            cumulative_units = (cumulative_wins * 0.91) - cumulative_losses
            cumulative_total = cumulative_wins + cumulative_losses
            cumulative_wr = cumulative_wins / cumulative_total if cumulative_total > 0 else 0

            history.append({
                "period": row['period'],
                "predictions": preds,
                "wins": w,
                "losses": l,
                "win_rate": round(cumulative_wr, 4),
                "daily_win_rate": round(wr, 4),
                "roi": round(roi_val, 2),
                "units_won": round(cumulative_units, 2)
            })

        conn.close()

        return {"history": history}

    except Exception as e:
        logger.error(f"Error generating props performance history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions")
async def get_props_predictions(
    sport: Optional[str] = None,
    prop_type: Optional[str] = None,
    model: Optional[str] = None,
    result: Optional[str] = None,
    days: int = 30,
    limit: int = 50
):
    """
    Get individual prop predictions with results
    """
    try:
        if not DB_PATH.exists():
            return {"predictions": [], "total": 0}

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        where_clauses = ["p.result IS NOT NULL", "p.game_date >= ?"]
        params = [cutoff_date]

        if sport:
            where_clauses.append("p.sport = ?")
            params.append(sport.lower())

        if prop_type:
            where_clauses.append("p.prop_type = ?")
            params.append(prop_type)

        if model:
            where_clauses.append("p.model_type = ?")
            params.append(model)

        if result:
            where_clauses.append("p.result = ?")
            params.append(result.upper())

        where_sql = " AND ".join(where_clauses)

        # Get total count first
        count_query = f"""
            SELECT COUNT(*) as total
            FROM player_props_predictions p
            WHERE {where_sql}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        # Get predictions with limit
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
                p.result,
                COALESCE(p.sport, 'nba') as sport,
                COALESCE(p.model_type, 'ensemble') as model
            FROM player_props_predictions p
            WHERE {where_sql}
            ORDER BY p.game_date DESC, ABS(p.edge_pct) DESC
            LIMIT ?
        """

        cursor.execute(query, params)

        predictions = []
        for row in cursor.fetchall():
            # Calculate profit/loss (assuming -110 odds)
            if row['result'] == 'WIN':
                profit_loss = 0.91  # Win 0.91 units
            elif row['result'] == 'LOSS':
                profit_loss = -1.0  # Lose 1 unit
            else:
                profit_loss = 0.0  # Push

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
                "result": row['result'],
                "sport": row['sport'],
                "model": row['model'],
                "profit_loss": profit_loss
            })

        conn.close()

        return {"predictions": predictions, "total": total}

    except Exception as e:
        logger.error(f"Error fetching props predictions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_props_models_info():
    """
    Get information about available props prediction models
    """
    return {
        "models": {
            "ensemble": {
                "name": "Ensemble",
                "description": "Combined prediction from all ML models",
                "markets": ["points", "rebounds", "assists", "threes", "blocks", "steals", "PRA"],
                "strength": "Most stable, best for consistent performance"
            },
            "xgboost": {
                "name": "XGBoost",
                "description": "Gradient boosting model",
                "markets": ["points", "rebounds", "assists", "threes", "blocks", "steals", "PRA"],
                "strength": "Best for high-edge picks"
            },
            "lightgbm": {
                "name": "LightGBM",
                "description": "Light gradient boosting model",
                "markets": ["points", "rebounds", "assists", "threes", "blocks", "steals", "PRA"],
                "strength": "Fast and accurate"
            },
            "random_forest": {
                "name": "Random Forest",
                "description": "Tree ensemble model",
                "markets": ["points", "rebounds", "assists", "threes", "blocks", "steals", "PRA"],
                "strength": "Good for outlier detection"
            }
        },
        "prop_types": ["points", "rebounds", "assists", "threes", "blocks", "steals", "PRA"],
        "sports": ["nba", "ncaab", "nfl", "nhl", "ncaaf"]
    }
