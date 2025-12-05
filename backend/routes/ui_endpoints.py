"""
UI Endpoints - BULLETPROOF ARCHITECTURE
==============================================
SACRED CONTRACT - Frontend ONLY calls these endpoints
All data is pre-computed. Frontend is 100% dumb - just renders.

Required Routes (per bulletproof spec):
- /api/ui/best-plays        - Daily edges/best plays
- /api/ui/model-performance - Model performance stats
- /api/ui/live-games        - Live game data
- /api/ui/props-edges       - Player props edges
- /api/ui/historical-predictions - Past predictions
- /api/ui/odds-comparison   - Odds across books
- /api/ui/analytics-summary - Dashboard analytics
"""

from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timedelta
from utils.timezone import get_cst_now, get_cst_today
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
import sqlite3
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ui", tags=["UI Endpoints - Bulletproof"])

# Data directories
DATA_DIR = Path("/root/sporttrader/backend/data")
TRACKING_DIR = DATA_DIR / "tracking"
PREDICTIONS_DIR = DATA_DIR / "predictions"
RESULTS_LOG = TRACKING_DIR / "results_log_COMBINED.csv"
PROPS_DB = DATA_DIR / "player_props.db"
PREDICTIONS_DB = Path("/root/sporttrader/backend/ml/predictions.db")  # SINGLE SOURCE OF TRUTH


# ============================================================================
# HELPER FUNCTIONS - All formatting happens here, NOT in frontend
# ============================================================================

def format_percentage(value: float, include_sign: bool = False) -> str:
    """Format a decimal as percentage string"""
    if value is None or np.isnan(value):
        return "N/A"
    pct = value * 100 if abs(value) < 1 else value
    sign = "+" if include_sign and pct > 0 else ""
    return f"{sign}{pct:.1f}%"


def format_units(value: float) -> str:
    """Format units won/lost"""
    if value is None or np.isnan(value):
        return "0.00u"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}u"


def format_money(value: float) -> str:
    """Format as currency"""
    if value is None or np.isnan(value):
        return "$0"
    sign = "+" if value > 0 else "-"
    return f"{sign}${abs(value):,.0f}"


def format_record(wins: int, losses: int, pushes: int = 0) -> str:
    """Format W-L-P record"""
    if pushes > 0:
        return f"{wins}W-{losses}L-{pushes}P"
    return f"{wins}W-{losses}L"


def format_odds(odds: int) -> str:
    """Format American odds"""
    if odds is None:
        return "N/A"
    return f"+{odds}" if odds > 0 else str(odds)


def calculate_kelly(edge_pct: float, odds: int = -110) -> dict:
    """Calculate Kelly criterion fractions - ALL MATH BACKEND ONLY"""
    if edge_pct is None or edge_pct <= 0:
        return {"full": 0, "half": 0, "quarter": 0, "recommended": "0%"}

    decimal_odds = (odds / 100) + 1 if odds > 0 else (100 / abs(odds)) + 1
    implied_prob = 1 / decimal_odds
    true_prob = implied_prob + (edge_pct / 100)
    b = decimal_odds - 1

    kelly_pct = max(0, (b * true_prob - (1 - true_prob)) / b)
    full_kelly = min(kelly_pct * 100, 25)  # Cap at 25%

    return {
        "full": round(full_kelly, 2),
        "half": round(full_kelly * 0.5, 2),
        "quarter": round(full_kelly * 0.25, 2),
        "recommended": f"{full_kelly * 0.5:.1f}%"  # Half Kelly recommended
    }


def get_confidence_color(confidence: str) -> str:
    """Return color for confidence level"""
    colors = {
        "HIGH": "#22c55e",      # green
        "MEDIUM": "#eab308",    # yellow
        "LOW": "#ef4444"        # red
    }
    return colors.get(confidence.upper(), "#6b7280")


def get_result_color(result: str) -> str:
    """Return color for result"""
    colors = {
        "WIN": "#22c55e",
        "LOSS": "#ef4444",
        "PUSH": "#6b7280",
        "PENDING": "#3b82f6"
    }
    return colors.get(result.upper(), "#6b7280")


# ============================================================================
# ROUTE 1: /api/ui/best-plays (alias: daily-edges)
# ============================================================================


# Helper functions for NULL-safe string operations
def safe_str_upper(val):
    """Safely convert value to uppercase string, handling None/NULL"""
    if val is None or (isinstance(val, str) and val.strip() == ''):
        return ''
    return str(val).upper()

def safe_str_title(val):
    """Safely convert value to title case string, handling None/NULL"""
    if val is None or (isinstance(val, str) and val.strip() == ''):
        return ''
    return str(val).title()

def safe_str(val):
    """Safely convert value to string, handling None/NULL"""
    if val is None:
        return ''
    return str(val)

@router.get("/best-plays")
@router.get("/daily-edges")  # Alias for backwards compatibility
async def get_best_plays(
    sport: str = Query(None, description="Filter by sport"),
    min_edge: float = Query(2.0, description="Minimum edge percentage"),
    confidence: str = Query(None, description="Filter by confidence level"),
    bet_type: str = Query(None, description="Filter by bet type (spreads, totals, moneyline)"),
    limit: int = Query(50, description="Maximum results")
):
    """
    Returns today's best betting plays from predictions.db - SINGLE SOURCE OF TRUTH.
    Frontend just renders this data.
    """
    try:
        from zoneinfo import ZoneInfo
        CST = ZoneInfo("America/Chicago")
        today_cst = datetime.now(CST).strftime("%Y-%m-%d")

        conn = sqlite3.connect(PREDICTIONS_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Calculate next Sunday for NFL/NCAAF week filter
        from datetime import timedelta
        now_cst = datetime.now(CST)
        days_until_sunday = (6 - now_cst.weekday()) % 7
        if days_until_sunday == 0:  # If today is Sunday
            days_until_sunday = 7  # Go to next Sunday
        next_sunday = (now_cst + timedelta(days=days_until_sunday)).strftime("%Y-%m-%d")

        # SMART DATE FILTERING: Sport-specific date ranges
        # NBA, NHL, NCAAB: Show today's games + tomorrow's early games (before 6am)
        # NFL, NCAAF: Show next 6 days (they play weekly on weekends)
        six_days_out = (now_cst + timedelta(days=6)).strftime("%Y-%m-%d")
        tomorrow = (now_cst + timedelta(days=1)).strftime("%Y-%m-%d")
        current_time = now_cst.strftime("%H:%M")
        
        if sport and sport.upper() in ['NFL', 'NCAAF']:
            # NFL/NCAAF: Show upcoming games within next 6 days
            where_clauses = ["game_date >= ? AND game_date <= ?", "ABS(edge) >= ?"]
            params = [today_cst, six_days_out, min_edge]
        elif sport and sport.upper() in ['NBA', 'NHL', 'NCAAB']:
            # NBA/NHL/NCAAB: Show all today's games (CST dates now correct)
            where_clauses = ["game_date = ?", "ABS(edge) >= ?"]
            params = [today_cst, min_edge]
        else:
            # All sports: Show today + next 6 days for full view
            where_clauses = ["game_date >= ? AND game_date <= ?", "ABS(edge) >= ?"]
            params = [today_cst, six_days_out, min_edge]

        if sport:
            where_clauses.append("UPPER(sport) = ?")
            params.append(sport.upper())
        if confidence:
            where_clauses.append("UPPER(confidence) = ?")
            params.append(confidence.upper())
        if bet_type:
            where_clauses.append("LOWER(bet_type) = ?")
            params.append(bet_type.lower())

        where_sql = " AND ".join(where_clauses)
        params.append(limit)

        query = f"""
            SELECT * FROM predictions
            WHERE {where_sql}
            ORDER BY ABS(edge) DESC
            LIMIT ?
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        plays = []
        for row in rows:
            edge = row["edge"] or 0
            odds = -110  # Default American odds
            kelly = calculate_kelly(abs(edge), odds)

            plays.append({
                # Frontend-expected fields (MaxEvEdges.tsx compatibility)
                "id": row["prediction_id"] or "",
                "recommendation": row["recommendation"] or "",
                "model_prediction": row["predicted_value"],
                "market_line": row["market_value"],
                "edge_percentage": round(abs(edge), 2),
                "model_confidence": round((row["over_probability"] or 0.5), 3),
                "kelly_fraction": kelly["half"] / 100 if kelly["half"] else 0,
                "model_name": row["model"] or "ensemble",
                "consensus": {"models_agree": 1, "models_total": 1, "strength": "MODERATE"},
                "game_id": row["prediction_id"] or "",
                "market": (row["bet_type"] or "").title(),
                "edge": round(abs(edge), 2),
                "suggested_bet_size": kelly["recommended"],
                "probability": round((row["over_probability"] or 0.5), 3),
                "features_used": {},
                "model_performance": {},
                "score": round(abs(edge) * (row["over_probability"] or 0.5), 2),
                
                # Additional fields for display
                "sport": (row["sport"] or "").upper(),
                "game_date": row["game_date"] or today_cst,
                "game_time": row["game_time"] or "TBD",
                "home_team": row["home_team"] or "",
                "away_team": row["away_team"] or "",
                "matchup": f"{row['away_team'] or ''} @ {row['home_team'] or ''}",
                "bet_type": (row["bet_type"] or "").title(),
                "odds": odds,
                "display_odds": format_odds(odds),
                "display_edge": format_percentage(abs(edge)),
                "confidence": (row["confidence"] or "MEDIUM").upper(),
                "confidence_color": get_confidence_color(row["confidence"] or "MEDIUM"),
                "kelly": kelly,
                "display_kelly": kelly["recommended"],
                "best_book": "FanDuel",
            })

        return {
            "plays": plays,
            "count": len(plays),
            "date": today_cst,
            "filters": {"sport": sport, "min_edge": min_edge, "confidence": confidence, "bet_type": bet_type},
            "source": "predictions.db",
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in best-plays: {e}")
        import traceback
        traceback.print_exc()
        return {"plays": [], "count": 0, "error": str(e), "generated_at": datetime.utcnow().isoformat()}


# ============================================================================
# ROUTE 2: /api/ui/model-performance
# ============================================================================

@router.get("/model-performance")
async def get_model_performance(
    sport: str = Query(None),
    model: str = Query(None),
    bet_type: str = Query(None),
    days: int = Query(30),
    unit_size: int = Query(100),
    bankroll: int = Query(10000)
):
    """
    Returns FULLY FORMATTED model performance data.
    Frontend should just render - no calculations.
    """
    try:
        # BULLETPROOF: Read from predictions.db results table - SINGLE SOURCE OF TRUTH
        if not PREDICTIONS_DB.exists():
            return {"error": "No data available", "generated_at": datetime.utcnow().isoformat()}

        conn = sqlite3.connect(PREDICTIONS_DB)

        # Calculate cutoff date
        cutoff = (get_cst_now().replace(tzinfo=None) - timedelta(days=days)).strftime('%Y-%m-%d')

        # Load results from database
        query = """
            SELECT
                prediction_id, sport, bet_type, game_date,
                away_team, home_team, predicted_value, market_value,
                recommendation, confidence, result, profit_loss, model
            FROM results
            WHERE game_date >= ?
              AND result IN ('WIN', 'LOSS', 'PUSH')
        """
        df = pd.read_sql_query(query, conn, params=[cutoff])
        conn.close()

        df['game_date'] = pd.to_datetime(df['game_date'], format='mixed', errors='coerce')

        # Add edge column for compatibility
        if 'edge' not in df.columns:
            df['edge'] = df['predicted_value'] - df['market_value']

        # Apply filters
        if sport:
            df = df[df['sport'].str.lower() == sport.lower()]
        if model:
            df = df[df['model'].str.lower() == model.lower()]
        if bet_type:
            df = df[df['bet_type'].str.lower() == bet_type.lower()]

        if len(df) == 0:
            return {"error": "No data for selected filters", "generated_at": datetime.utcnow().isoformat()}

        # Calculate metrics
        total = len(df)
        wins = len(df[df['result'] == 'WIN'])
        losses = len(df[df['result'] == 'LOSS'])
        pushes = len(df[df['result'] == 'PUSH'])
        decided = wins + losses
        win_rate = wins / decided if decided > 0 else 0

        # Calculate P&L from filtered dataset (respects user's model selection)
        capped_pnl = df['profit_loss'].clip(lower=-100, upper=500) if 'profit_loss' in df.columns else pd.Series([0])
        units_won = capped_pnl.sum() / 100
        roi = (units_won / total) if total > 0 else 0
        avg_edge = df['edge'].abs().mean() if 'edge' in df.columns else 0
        kelly = calculate_kelly(avg_edge)
        pnl_dollars = units_won * unit_size

        # By sport breakdown
        by_sport = {}
        for sport_name in df['sport'].dropna().unique():
            s_df = df[df['sport'] == sport_name]
            s_wins = len(s_df[s_df['result'] == 'WIN'])
            s_losses = len(s_df[s_df['result'] == 'LOSS'])
            s_pushes = len(s_df[s_df['result'] == 'PUSH'])
            s_decided = s_wins + s_losses
            s_wr = s_wins / s_decided if s_decided > 0 else 0
            s_units = (s_df['profit_loss'].sum() / 100) if 'profit_loss' in s_df.columns else 0

            by_sport[sport_name.upper()] = {
                "total": len(s_df),
                "wins": s_wins,
                "losses": s_losses,
                "pushes": s_pushes,
                "record": format_record(s_wins, s_losses, s_pushes),
                "win_rate": round(s_wr, 4),
                "display_win_rate": format_percentage(s_wr),
                "units": round(s_units, 2),
                "display_units": format_units(s_units),
                "roi": round((s_units / len(s_df)) if len(s_df) > 0 else 0, 4),
                "display_roi": format_percentage((s_units / len(s_df)) * 100 if len(s_df) > 0 else 0, include_sign=True),
                "pnl_dollars": round(s_units * unit_size, 0),
                "display_pnl": format_money(s_units * unit_size)
            }

        # By model breakdown
        by_model = {}
        for model_name in df['model'].dropna().unique():
            m_df = df[df['model'] == model_name]
            m_wins = len(m_df[m_df['result'] == 'WIN'])
            m_losses = len(m_df[m_df['result'] == 'LOSS'])
            m_pushes = len(m_df[m_df['result'] == 'PUSH'])
            m_decided = m_wins + m_losses
            m_wr = m_wins / m_decided if m_decided > 0 else 0
            m_units = (m_df['profit_loss'].sum() / 100) if 'profit_loss' in m_df.columns else 0

            by_model[model_name.lower()] = {
                "total": len(m_df),
                "wins": m_wins,
                "losses": m_losses,
                "pushes": m_pushes,
                "record": format_record(m_wins, m_losses, m_pushes),
                "win_rate": round(m_wr, 4),
                "display_win_rate": format_percentage(m_wr),
                "units": round(m_units, 2),
                "display_units": format_units(m_units)
            }

        # By confidence breakdown
        by_confidence = {}
        for conf in ['HIGH', 'MEDIUM', 'LOW']:
            c_df = df[df['confidence'] == conf]
            if len(c_df) > 0:
                c_wins = len(c_df[c_df['result'] == 'WIN'])
                c_losses = len(c_df[c_df['result'] == 'LOSS'])
                c_pushes = len(c_df[c_df['result'] == 'PUSH'])
                c_decided = c_wins + c_losses
                c_wr = c_wins / c_decided if c_decided > 0 else 0

                by_confidence[conf.lower()] = {
                    "total": len(c_df),
                    "wins": c_wins,
                    "losses": c_losses,
                    "pushes": c_pushes,
                    "record": format_record(c_wins, c_losses, c_pushes),
                    "win_rate": round(c_wr, 4),
                    "display_win_rate": format_percentage(c_wr),
                    "color": get_confidence_color(conf)
                }


        # DAILY BREAKDOWN for charts (BULLETPROOF)
        df['date'] = df['game_date'].dt.date
        history_data = []
        cumulative_units = 0
        
        for date_val in sorted(df['date'].dropna().unique()):
            day_df = df[df['date'] == date_val]
            day_wins = len(day_df[day_df['result'] == 'WIN'])
            day_losses = len(day_df[day_df['result'] == 'LOSS'])
            day_decided = day_wins + day_losses
            day_wr = day_wins / day_decided if day_decided > 0 else 0
            day_units = (day_df['profit_loss'].sum() / 100) if 'profit_loss' in day_df.columns else 0
            cumulative_units += day_units
            
            history_data.append({
                "period": str(date_val),
                "predictions": len(day_df),
                "wins": day_wins,
                "losses": day_losses,
                "win_rate": round(day_wr, 4),
                "daily_win_rate": round(day_wr, 4),
                "roi": round((cumulative_units / total) if total > 0 else 0, 4),
                "daily_roi": round((day_units / len(day_df)) if len(day_df) > 0 else 0, 4),
                "units_won": round(cumulative_units, 2),
                "pnl_dollars": round(cumulative_units * unit_size, 0)
            })
        
        # RECENT PREDICTIONS for table (BULLETPROOF)
        recent_preds = df.sort_values('game_date', ascending=False).head(50)
        predictions_list = []
        for _, row in recent_preds.iterrows():
            predictions_list.append({
                "prediction_id": row.get('prediction_id', ''),
                "game_date": str(row.get('game_date', '')),
                "sport": row.get('sport', ''),
                "away_team": row.get('away_team', ''),
                "home_team": row.get('home_team', ''),
                "bet_type": row.get('bet_type', ''),
                "predicted_value": round(float(row.get('predicted_value', 0)), 1),
                "market_value": round(float(row.get('market_value', 0)), 1),
                "edge": round(float(row.get('edge', 0)), 1),
                "recommendation": row.get('recommendation', ''),
                "confidence": row.get('confidence', ''),
                "model": row.get('model', ''),
                "result": row.get('result', 'PENDING'),
                "profit_loss": int(row.get('profit_loss', 0))
            })
        
        # MODELS LIST (BULLETPROOF)
        models_list = [
            {"name": "all", "description": "All Models Combined", "type": "meta"},
            {"name": "ensemble", "description": "Neural Ensemble", "type": "deep_learning"},
            {"name": "pytorch", "description": "PyTorch TabularNet", "type": "deep_learning"},
            {"name": "catboost", "description": "CatBoost", "type": "ml"},
            {"name": "xgboost", "description": "XGBoost", "type": "ml"},
            {"name": "lightgbm", "description": "LightGBM", "type": "ml"},
            {"name": "random_forest", "description": "Random Forest", "type": "ml"},
            {"name": "linear", "description": "Linear Regression", "type": "baseline"}
        ]
        
        return {
            "summary": {
                "total_predictions": total,
                "wins": wins,
                "losses": losses,
                "pushes": pushes,
                "record": format_record(wins, losses, pushes),
                "win_rate": round(win_rate, 4),
                "display_win_rate": format_percentage(win_rate),
                "units_won": round(units_won, 2),
                "display_units": format_units(units_won),
                "roi": round(roi, 2),
                "display_roi": format_percentage(roi, include_sign=True),
                "pnl_dollars": round(pnl_dollars, 0),
                "display_pnl": format_money(pnl_dollars),
                "avg_edge": round(avg_edge, 2),
                "kelly": kelly,
                "time_period": f"Last {days} days"
            },
            "by_sport": by_sport,
            "by_model": by_model,
            "by_confidence": by_confidence,
            "history": history_data,
            "predictions": predictions_list,
            "predictions_total": len(df),
            "models": models_list,
            "filters": {"sport": sport, "model": model, "bet_type": bet_type, "days": days},
            "settings": {"unit_size": unit_size, "bankroll": bankroll},
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in model-performance: {e}")
        return {"error": str(e), "generated_at": datetime.utcnow().isoformat()}


# ============================================================================
# ROUTE 3: /api/ui/live-games
# ============================================================================

@router.get("/live-games")
async def get_live_games(
    sport: str = Query(None, description="Filter by sport")
):
    """
    Returns live/upcoming games with predictions - FULLY FORMATTED.
    """
    try:
        today = get_cst_now().strftime("%Y-%m-%d")
        predictions_file = PREDICTIONS_DIR / f"all_predictions_{today}.csv"

        if not predictions_file.exists():
            pred_files = list(PREDICTIONS_DIR.glob("all_predictions_*.csv"))
            if pred_files:
                predictions_file = max(pred_files, key=lambda x: x.stat().st_mtime)
            else:
                return {"games": [], "count": 0, "generated_at": datetime.utcnow().isoformat()}

        df = pd.read_csv(predictions_file)

        if sport:
            df = df[df['sport'].str.upper() == sport.upper()]

        # Group by game
        games = []
        for game_id in df['game_id'].unique():
            game_df = df[df['game_id'] == game_id]
            first_row = game_df.iloc[0]

            # Get predictions for this game
            preds = []
            for _, row in game_df.iterrows():
                preds.append({
                    "bet_type": row.get('bet_type', '').title(),
                    "pick": row.get('recommendation', ''),
                    "edge": round(row.get('edge', 0), 2),
                    "display_edge": format_percentage(row.get('edge', 0)),
                    "confidence": row.get('confidence', 'MEDIUM').upper(),
                    "confidence_color": get_confidence_color(row.get('confidence', 'MEDIUM'))
                })

            games.append({
                "game_id": game_id,
                "sport": first_row.get('sport', '').upper(),
                "game_time": first_row.get('game_time', ''),
                "home_team": first_row.get('home_team', ''),
                "away_team": first_row.get('away_team', ''),
                "matchup": f"{first_row.get('away_team', '')} @ {first_row.get('home_team', '')}",
                "status": "upcoming",
                "predictions": preds
            })

        return {
            "games": games,
            "count": len(games),
            "sport_filter": sport,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in live-games: {e}")
        return {"games": [], "count": 0, "error": str(e), "generated_at": datetime.utcnow().isoformat()}


# ============================================================================
# ROUTE 4: /api/ui/props-edges
# ============================================================================

@router.get("/props-edges")
async def get_props_edges(
    sport: str = Query("nba", description="Sport (nba, nfl, nhl)"),
    min_edge: float = Query(5.0, description="Minimum edge percentage"),
    limit: int = Query(50, description="Maximum results")
):
    """
    Returns player props edges - FULLY FORMATTED.
    """
    try:
        if not PROPS_DB.exists():
            return {"props": [], "count": 0, "error": "Props database not found", "generated_at": datetime.utcnow().isoformat()}

        conn = sqlite3.connect(str(PROPS_DB))

        query = """
            SELECT * FROM player_props_predictions
            WHERE date(prediction_date) = date('now', '-6 hours')
            AND ABS(edge_pct) >= ?
            ORDER BY ABS(edge_pct) DESC
            LIMIT ?
        """

        df = pd.read_sql_query(query, conn, params=[min_edge, limit])
        conn.close()

        props = []
        for _, row in df.iterrows():
            edge = row.get('edge_pct', 0)
            kelly = calculate_kelly(abs(edge))

            props.append({
                "player_name": row.get('player_name', ''),
                "team": row.get('team', ''),
                "opponent": row.get('opponent', ''),
                "prop_type": row.get('prop_type', '').replace('_', ' ').title(),
                "line": row.get('line', 0),
                "pick": row.get('recommendation', ''),
                "odds": row.get('odds', -110),
                "display_odds": format_odds(row.get('odds', -110)),
                "edge": round(abs(edge), 2),
                "display_edge": format_percentage(abs(edge)),
                "model_probability": round(row.get('model_probability', 0.5) * 100, 1),
                "confidence": row.get('confidence', 'MEDIUM').upper(),
                "confidence_color": get_confidence_color(row.get('confidence', 'MEDIUM')),
                "kelly": kelly,
                "display_kelly": kelly["recommended"],
                "best_book": row.get('best_book', 'DraftKings'),
                "game_time": row.get('game_time', '')
            })

        return {
            "props": props,
            "count": len(props),
            "filters": {"sport": sport, "min_edge": min_edge},
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in props-edges: {e}")
        return {"props": [], "count": 0, "error": str(e), "generated_at": datetime.utcnow().isoformat()}


# ============================================================================
# ROUTE 5: /api/ui/historical-predictions
# ============================================================================

@router.get("/historical-predictions")
async def get_historical_predictions(
    sport: str = Query(None),
    days: int = Query(7),
    result: str = Query(None, description="WIN, LOSS, PUSH, or PENDING"),
    limit: int = Query(100)
):
    """
    Returns historical predictions - FULLY FORMATTED.
    BULLETPROOF: Uses predictions.db as single source of truth
    """
    try:
        if not PREDICTIONS_DB.exists():
            return {"predictions": [], "count": 0, "generated_at": datetime.utcnow().isoformat()}

        # Connect to database
        conn = sqlite3.connect(PREDICTIONS_DB)
        
        # Calculate cutoff date
        cutoff = (get_cst_now().replace(tzinfo=None) - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Build query with filters
        query = """
            SELECT
                r.prediction_id,
                r.sport,
                r.bet_type,
                r.game_date,
                r.away_team,
                r.home_team,
                r.predicted_value,
                r.market_value,
                r.recommendation,
                r.confidence,
                r.result,
                r.profit_loss,
                r.model,
                (r.predicted_value - r.market_value) as edge
            FROM results r
            WHERE r.game_date >= ?
        """
        
        params = [cutoff]
        
        if sport:
            query += " AND UPPER(r.sport) = UPPER(?)"
            params.append(sport)
        
        if result:
            query += " AND UPPER(r.result) = UPPER(?)"
            params.append(result)
        
        query += " ORDER BY r.game_date DESC LIMIT ?"
        params.append(limit)
        
        # Load data from database
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if len(df) == 0:
            return {"predictions": [], "count": 0, "generated_at": datetime.utcnow().isoformat()}
        
        df['game_date'] = pd.to_datetime(df['game_date'], format='mixed', errors='coerce')

        predictions = []
        for _, row in df.iterrows():
            # Safely extract values with NULL handling
            sport_val = safe_str_upper(row.get("sport"))
            bet_type_val = safe_str_title(row.get("bet_type"))
            confidence_val = safe_str_upper(row.get("confidence")) or "MEDIUM"
            result_val = safe_str_upper(row.get("result"))

            # Calculate proper edge percentage (not just point difference)
            predicted_value = float(row.get("predicted_value") or 0)
            market_value = float(row.get("market_value") or 0)

            # For totals/spreads: edge is the difference in implied probabilities
            # We approximate this using a simple heuristic based on how far off the prediction is
            # A larger difference = higher edge
            raw_diff = abs(predicted_value - market_value)

            # Edge calculation:
            # For totals/spreads at -110 odds, each point difference roughly = 2-3% edge
            # This is a simplified model, but works for display purposes
            if bet_type_val.lower() in ['totals', 'spreads']:
                edge_pct = raw_diff * 2.5  # Points difference * 2.5% per point
            else:  # Moneyline
                # For moneylines, use profit_loss to infer edge
                # This is already calculated with actual odds
                edge_pct = abs(raw_diff) if raw_diff > 0 else 0

            # Model probability (approximation based on confidence)
            # HIGH confidence = 60-65%, MEDIUM = 55-60%, LOW = 52-55%
            confidence_map = {
                'HIGH': 0.625,
                'MEDIUM': 0.575,
                'LOW': 0.535
            }
            model_prob = confidence_map.get(confidence_val, 0.55)

            # Calculate Kelly (using standard -110 odds for totals/spreads)
            kelly_result = calculate_kelly(edge_pct, -110)

            predictions.append({
                "prediction_id": safe_str(row.get("prediction_id")),
                "game_date": row["game_date"].strftime("%Y-%m-%d") if pd.notna(row.get("game_date")) else "",
                "game_time": "",
                "sport": sport_val,
                "away_team": safe_str(row.get("away_team")),
                "home_team": safe_str(row.get("home_team")),
                "bet_type": bet_type_val,
                "model": safe_str(row.get("model")) or "ensemble",
                "predicted_value": predicted_value,
                "market_value": market_value,
                "edge": round(edge_pct, 2),  # Now percentage edge
                "model_prob": round(model_prob * 100, 1),  # Model probability as percentage
                "kelly": kelly_result["quarter"],  # Quarter Kelly (conservative)
                "recommendation": safe_str(row.get("recommendation")),
                "confidence": confidence_val,
                "bet_placed": "",
                "actual_total": float(row.get("actual_total") or 0) if pd.notna(row.get("actual_total")) else None,
                "away_score": int(row.get("away_score") or 0) if pd.notna(row.get("away_score")) else None,
                "home_score": int(row.get("home_score") or 0) if pd.notna(row.get("home_score")) else None,
                "result": result_val if result_val else None,
                "profit_loss": float(row.get("profit_loss") or 0),
                "market_odds": None,
                "odds_source": None
            })

        return {
            "predictions": predictions,
            "count": len(predictions),
            "filters": {"sport": sport, "days": days, "result": result},
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in historical-predictions: {e}")
        return {"predictions": [], "count": 0, "error": str(e), "generated_at": datetime.utcnow().isoformat()}


# ============================================================================
# ROUTE 6: /api/ui/odds-comparison
# ============================================================================

@router.get("/odds-comparison")
async def get_odds_comparison(
    sport: str = Query(None),
    game_id: str = Query(None)
):
    """
    Returns odds comparison across sportsbooks - FULLY FORMATTED.
    """
    try:
        # For now, return placeholder structure
        # TODO: Integrate with odds API data
        return {
            "games": [],
            "books": ["DraftKings", "FanDuel", "BetMGM", "Caesars", "PointsBet"],
            "sport_filter": sport,
            "generated_at": datetime.utcnow().isoformat(),
            "note": "Odds comparison data coming soon"
        }

    except Exception as e:
        logger.error(f"Error in odds-comparison: {e}")
        return {"games": [], "error": str(e), "generated_at": datetime.utcnow().isoformat()}


# ============================================================================
# ROUTE 7: /api/ui/analytics-summary
# ============================================================================

@router.get("/analytics-summary")
async def get_analytics_summary(
    days: int = Query(30)
):
    """
    Returns dashboard analytics summary - FULLY FORMATTED.
    """
    try:
        # BULLETPROOF: Read from predictions.db results table - SINGLE SOURCE OF TRUTH
        if not PREDICTIONS_DB.exists():
            return {"error": "No data available", "generated_at": datetime.utcnow().isoformat()}

        conn = sqlite3.connect(PREDICTIONS_DB)

        # Calculate cutoff date
        cutoff = (get_cst_now().replace(tzinfo=None) - timedelta(days=days)).strftime('%Y-%m-%d')

        # Load results from database
        query = """
            SELECT
                prediction_id, sport, bet_type, game_date,
                away_team, home_team, predicted_value, market_value,
                recommendation, confidence, result, profit_loss, model
            FROM results
            WHERE game_date >= ?
        """
        df = pd.read_sql_query(query, conn, params=[cutoff])
        conn.close()

        df['game_date'] = pd.to_datetime(df['game_date'], format='mixed', errors='coerce')

        # Add edge column for compatibility
        if 'edge' not in df.columns:
            df['edge'] = df['predicted_value'] - df['market_value']

        if len(df) == 0:
            return {"error": "No data for period", "generated_at": datetime.utcnow().isoformat()}

        # Overall stats
        total = len(df)
        wins = len(df[df['result'] == 'WIN'])
        losses = len(df[df['result'] == 'LOSS'])
        decided = wins + losses
        win_rate = wins / decided if decided > 0 else 0

        # Use ensemble for P&L
        ensemble_df = df[df['model'] == 'ensemble'] if 'model' in df.columns else df
        units_won = (ensemble_df['profit_loss'].sum() / 100) if 'profit_loss' in ensemble_df.columns else 0
        roi = (units_won / total) if total > 0 else 0

        # Daily breakdown for chart
        daily_data = []
        df_by_date = df.groupby(df['game_date'].dt.date).agg({
            'result': lambda x: (x == 'WIN').sum(),
            'profit_loss': 'sum'
        }).reset_index()

        cumulative_units = 0
        for _, row in df_by_date.iterrows():
            cumulative_units += row['profit_loss'] / 100
            daily_data.append({
                "date": str(row['game_date']),
                "wins": int(row['result']),
                "cumulative_units": round(cumulative_units, 2)
            })

        return {
            "summary": {
                "total_predictions": total,
                "win_rate": round(win_rate, 4),
                "display_win_rate": format_percentage(win_rate),
                "units_won": round(units_won, 2),
                "display_units": format_units(units_won),
                "roi": round(roi, 2),
                "display_roi": format_percentage(roi, include_sign=True),
                "time_period": f"Last {days} days"
            },
            "daily_data": daily_data,
            "sports_active": list(df['sport'].dropna().unique()),
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in analytics-summary: {e}")
        return {"error": str(e), "generated_at": datetime.utcnow().isoformat()}


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def ui_health():
    """Health check for UI endpoints"""
    return {
        "status": "healthy",
        "endpoints": [
            "/api/ui/best-plays",
            "/api/ui/model-performance",
            "/api/ui/live-games",
            "/api/ui/props-edges",
            "/api/ui/historical-predictions",
            "/api/ui/odds-comparison",
            "/api/ui/analytics-summary"
        ],
        "architecture": "BULLETPROOF",
        "generated_at": datetime.utcnow().isoformat()
    }
