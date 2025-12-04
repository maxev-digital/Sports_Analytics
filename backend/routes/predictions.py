"""
Predictions API Routes
Exposes ML predictions from the predictions database

Endpoints:
- GET /api/predictions/today - Today's predictions
- GET /api/predictions/recent - Recent predictions with filters
- GET /api/predictions/by-sport/{sport} - Predictions for specific sport
- GET /api/predictions/stats - Prediction statistics
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from pathlib import Path
import sqlite3
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

# Database path
DB_PATH = Path(__file__).parent.parent / "ml" / "predictions.db"


def get_db_connection():
    """Get database connection"""
    if not DB_PATH.exists():
        raise HTTPException(status_code=500, detail="Predictions database not found")
    return sqlite3.connect(DB_PATH)


def dict_factory(cursor, row):
    """Convert SQLite rows to dictionaries"""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


@router.get("/today")
async def get_today_predictions(
    sport: Optional[str] = Query(None, description="Filter by sport (NBA, NCAAB, etc.)"),
    bet_type: Optional[str] = Query(None, description="Filter by bet type (totals, spreads, moneyline)")
):
    """Get all predictions for today's games"""
    try:
        conn = get_db_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        query = """
            SELECT *
            FROM predictions
            WHERE date(game_date) = date('now')
        """
        params = []

        if sport:
            query += " AND UPPER(sport) = UPPER(?)"
            params.append(sport)

        if bet_type:
            query += " AND LOWER(bet_type) = LOWER(?)"
            params.append(bet_type)

        query += " ORDER BY game_time, sport, home_team"

        cursor.execute(query, params)
        predictions = cursor.fetchall()
        conn.close()

        return {
            "total": len(predictions),
            "date": date.today().isoformat(),
            "filters": {
                "sport": sport or "all",
                "bet_type": bet_type or "all"
            },
            "predictions": predictions
        }

    except Exception as e:
        logger.error(f"Error fetching today's predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_predictions(
    sport: Optional[str] = Query(None, description="Filter by sport"),
    bet_type: Optional[str] = Query(None, description="Filter by bet type"),
    limit: int = Query(50, ge=1, le=500, description="Number of predictions to return"),
    days: int = Query(7, ge=1, le=90, description="Number of days to look back")
):
    """Get recent predictions with filters"""
    try:
        conn = get_db_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        query = """
            SELECT *
            FROM predictions
            WHERE date(created_at) >= date('now', ? || ' days')
        """
        params = [f"-{days}"]

        if sport:
            query += " AND UPPER(sport) = UPPER(?)"
            params.append(sport)

        if bet_type:
            query += " AND LOWER(bet_type) = LOWER(?)"
            params.append(bet_type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        predictions = cursor.fetchall()
        conn.close()

        return {
            "total": len(predictions),
            "filters": {
                "sport": sport or "all",
                "bet_type": bet_type or "all",
                "days": days,
                "limit": limit
            },
            "predictions": predictions
        }

    except Exception as e:
        logger.error(f"Error fetching recent predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-sport/{sport}")
async def get_predictions_by_sport(
    sport: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    bet_type: Optional[str] = Query(None, description="Filter by bet type")
):
    """Get predictions for a specific sport"""
    try:
        conn = get_db_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        query = """
            SELECT *
            FROM predictions
            WHERE UPPER(sport) = UPPER(?)
            AND date(game_date) >= date('now', ? || ' days')
        """
        params = [sport, f"-{days}"]

        if bet_type:
            query += " AND LOWER(bet_type) = LOWER(?)"
            params.append(bet_type)

        query += " ORDER BY game_date DESC, game_time, home_team"

        cursor.execute(query, params)
        predictions = cursor.fetchall()
        conn.close()

        return {
            "sport": sport.upper(),
            "total": len(predictions),
            "filters": {
                "days": days,
                "bet_type": bet_type or "all"
            },
            "predictions": predictions
        }

    except Exception as e:
        logger.error(f"Error fetching predictions for {sport}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_prediction_stats():
    """Get prediction statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Total predictions
        cursor.execute("SELECT COUNT(*) FROM predictions")
        total_predictions = cursor.fetchone()[0]

        # Today's predictions
        cursor.execute("""
            SELECT COUNT(*) FROM predictions
            WHERE date(game_date) = date('now')
        """)
        today_count = cursor.fetchone()[0]

        # Last 7 days
        cursor.execute("""
            SELECT COUNT(*) FROM predictions
            WHERE date(created_at) >= date('now', '-7 days')
        """)
        last_7_days = cursor.fetchone()[0]

        # By sport (last 7 days)
        cursor.execute("""
            SELECT sport, COUNT(*) as count
            FROM predictions
            WHERE date(created_at) >= date('now', '-7 days')
            GROUP BY sport
            ORDER BY count DESC
        """)
        by_sport = {row[0]: row[1] for row in cursor.fetchall()}

        # By bet type (last 7 days)
        cursor.execute("""
            SELECT bet_type, COUNT(*) as count
            FROM predictions
            WHERE date(created_at) >= date('now', '-7 days')
            GROUP BY bet_type
            ORDER BY count DESC
        """)
        by_bet_type = {row[0]: row[1] for row in cursor.fetchall()}

        # Predictions with NULL values (failures)
        cursor.execute("""
            SELECT COUNT(*) FROM predictions
            WHERE predicted_value IS NULL
            AND date(created_at) >= date('now', '-7 days')
        """)
        null_predictions = cursor.fetchone()[0]

        # Graded predictions accuracy (if graded field exists)
        try:
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins
                FROM predictions
                WHERE result IS NOT NULL
                AND date(created_at) >= date('now', '-30 days')
            """)
            graded_row = cursor.fetchone()
            if graded_row and graded_row[0] > 0:
                accuracy = (graded_row[1] / graded_row[0]) * 100
            else:
                accuracy = None
        except:
            accuracy = None

        conn.close()

        return {
            "total_predictions": total_predictions,
            "today": today_count,
            "last_7_days": last_7_days,
            "by_sport": by_sport,
            "by_bet_type": by_bet_type,
            "null_predictions_7d": null_predictions,
            "accuracy_30d": accuracy,
            "database_path": str(DB_PATH.relative_to(DB_PATH.parent.parent)),
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error fetching prediction stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-date/{prediction_date}")
async def get_predictions_by_date(
    prediction_date: str,
    sport: Optional[str] = Query(None, description="Filter by sport"),
    bet_type: Optional[str] = Query(None, description="Filter by bet type")
):
    """Get predictions for a specific date (format: YYYY-MM-DD)"""
    try:
        # Validate date format
        try:
            date.fromisoformat(prediction_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        conn = get_db_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        query = """
            SELECT *
            FROM predictions
            WHERE date(game_date) = ?
        """
        params = [prediction_date]

        if sport:
            query += " AND UPPER(sport) = UPPER(?)"
            params.append(sport)

        if bet_type:
            query += " AND LOWER(bet_type) = LOWER(?)"
            params.append(bet_type)

        query += " ORDER BY game_time, sport, home_team"

        cursor.execute(query, params)
        predictions = cursor.fetchall()
        conn.close()

        return {
            "date": prediction_date,
            "total": len(predictions),
            "filters": {
                "sport": sport or "all",
                "bet_type": bet_type or "all"
            },
            "predictions": predictions
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching predictions for date {prediction_date}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/edges")
async def get_predictions_with_edges(
    min_edge: float = Query(0.5, ge=0, description="Minimum edge percentage"),
    min_confidence: float = Query(0.0, ge=0, le=1, description="Minimum confidence"),
    sport: Optional[str] = Query(None, description="Filter by sport"),
    bet_type: Optional[str] = Query(None, description="Filter by bet type"),
    limit: int = Query(100, ge=1, le=500, description="Number of predictions to return")
):
    """Get predictions with positive edges above threshold"""
    try:
        conn = get_db_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        query = """
            SELECT *
            FROM predictions
            WHERE date(game_date) >= date('now')
            AND ABS(edge) >= ?
        """
        params = [min_edge]

        if min_confidence > 0:
            query += " AND confidence >= ?"
            params.append(min_confidence)

        if sport:
            query += " AND UPPER(sport) = UPPER(?)"
            params.append(sport)

        if bet_type:
            query += " AND LOWER(bet_type) = LOWER(?)"
            params.append(bet_type)

        query += " ORDER BY ABS(edge) DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        predictions = cursor.fetchall()
        conn.close()

        return {
            "total": len(predictions),
            "filters": {
                "min_edge": min_edge,
                "min_confidence": min_confidence,
                "sport": sport or "all",
                "bet_type": bet_type or "all"
            },
            "predictions": predictions
        }

    except Exception as e:
        logger.error(f"Error fetching edge predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
