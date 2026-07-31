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
from zoneinfo import ZoneInfo as _ZI
_CST = _ZI("America/Chicago")
def get_cst_now():
    from datetime import datetime
    return datetime.now(_CST)
def get_cst_today():
    from datetime import datetime
    return datetime.now(_CST).date()
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
    """Returns model performance stats from PostgreSQL pipeline DB."""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PG_DSN = "postgresql://maxev:maxev_sports@localhost:5432/maxev_sports"
    try:
        conn = psycopg2.connect(PG_DSN)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cutoff = (datetime.utcnow() - timedelta(days=days)).date()
        query = """
            SELECT
                id::text AS prediction_id,
                created_at_cst::date AS game_date,
                sport,
                pick_type AS bet_type,
                detector AS model,
                confidence_tier AS confidence,
                status AS result,
                COALESCE(pl_units, 0) AS pl_units,
                edge_pct,
                our_probability * 100 AS predicted_value,
                market_implied_prob * 100 AS market_value,
                pick_side AS recommendation,
                away_team,
                home_team
            FROM predictions
            WHERE created_at_cst::date >= %s
              AND status IN ('win', 'loss', 'push')
        """
        params = [cutoff]
        if sport:
            query += " AND LOWER(sport) = LOWER(%s)"
            params.append(sport)
        if bet_type:
            _bt = {'totals': 'total', 'moneyline': 'ml', 'spreads': 'spread'}.get((bet_type or '').lower(), bet_type)
            query += " AND LOWER(pick_type) = LOWER(%s)"
            params.append(_bt)
        if model:
            query += " AND LOWER(detector) LIKE LOWER(%s)"
            params.append(f"%{model}%")
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()

        empty_resp = {
            "summary": {
                "total_predictions": 0, "wins": 0, "losses": 0, "pushes": 0,
                "win_rate": 0, "roi": 0, "avg_edge": 0, "units_won": 0,
                "record": "0-0", "display_win_rate": "0%", "display_units": "0.00u",
                "display_roi": "+0.0%", "pnl_dollars": 0, "display_pnl": "$0",
                "time_period": f"Last {days} days"
            },
            "by_sport": {}, "by_model": {}, "by_confidence": {},
            "history": [], "predictions": [], "predictions_total": 0,
            "models": [{"name": "rule_multibook_vig", "description": "Multi-Book Vig Detector", "type": "rule"}],
            "filters": {"sport": sport, "model": model, "bet_type": bet_type, "days": days},
            "settings": {"unit_size": unit_size, "bankroll": bankroll},
            "generated_at": datetime.utcnow().isoformat()
        }
        if not rows:
            return empty_resp

        total  = len(rows)
        wins   = sum(1 for r in rows if r["result"] == "win")
        losses = sum(1 for r in rows if r["result"] == "loss")
        pushes = sum(1 for r in rows if r["result"] == "push")
        decided   = wins + losses
        win_rate  = wins / decided if decided > 0 else 0
        units_won = sum(float(r["pl_units"] or 0) for r in rows)
        roi       = (units_won / total) if total > 0 else 0
        avg_edge  = sum(abs(float(r["edge_pct"] or 0)) for r in rows) / total if total > 0 else 0
        pnl_dollars = units_won * unit_size

        def _rec(w, l, p=0):
            return f"{w}-{l}" + (f"-{p}" if p else "")

        by_sport = {}
        for s in set(r["sport"] for r in rows if r["sport"]):
            sr = [r for r in rows if r["sport"] == s]
            sw = sum(1 for r in sr if r["result"] == "win")
            sl = sum(1 for r in sr if r["result"] == "loss")
            sp = sum(1 for r in sr if r["result"] == "push")
            sd = sw + sl
            su = sum(float(r["pl_units"] or 0) for r in sr)
            by_sport[s.upper()] = {
                "total": len(sr), "wins": sw, "losses": sl, "pushes": sp,
                "record": _rec(sw, sl, sp),
                "win_rate": round(sw / sd, 4) if sd > 0 else 0,
                "display_win_rate": f"{round(sw/sd*100,1)}%" if sd > 0 else "0%",
                "units": round(su, 2),
                "roi": round(su / len(sr), 4) if sr else 0,
                "pnl_dollars": round(su * unit_size, 0),
                "display_pnl": f"{'+'if su>=0 else ''}${abs(su*unit_size):.0f}",
            }

        by_model = {}
        for m in set(r["model"] for r in rows if r["model"]):
            mr = [r for r in rows if r["model"] == m]
            mw = sum(1 for r in mr if r["result"] == "win")
            ml_cnt = sum(1 for r in mr if r["result"] == "loss")
            md = mw + ml_cnt
            mu = sum(float(r["pl_units"] or 0) for r in mr)
            by_model[m] = {
                "total": len(mr), "wins": mw, "losses": ml_cnt,
                "record": _rec(mw, ml_cnt),
                "win_rate": round(mw / md, 4) if md > 0 else 0,
                "display_win_rate": f"{round(mw/md*100,1)}%" if md > 0 else "0%",
                "units": round(mu, 2),
            }

        by_confidence = {}
        for conf in ["high", "medium", "low"]:
            cr = [r for r in rows if (r["confidence"] or "").lower() == conf]
            if cr:
                cw = sum(1 for r in cr if r["result"] == "win")
                cl_cnt = sum(1 for r in cr if r["result"] == "loss")
                cd = cw + cl_cnt
                by_confidence[conf] = {
                    "total": len(cr), "wins": cw, "losses": cl_cnt,
                    "record": _rec(cw, cl_cnt),
                    "win_rate": round(cw / cd, 4) if cd > 0 else 0,
                    "display_win_rate": f"{round(cw/cd*100,1)}%" if cd > 0 else "0%",
                    "roi": 0,
                    "color": "green" if conf == "high" else ("yellow" if conf == "medium" else "gray"),
                }

        dates = sorted(set(str(r["game_date"]) for r in rows if r["game_date"]))
        history_data = []
        cum_units = 0
        for d in dates:
            dr = [r for r in rows if str(r["game_date"]) == d]
            dw = sum(1 for r in dr if r["result"] == "win")
            dl = sum(1 for r in dr if r["result"] == "loss")
            dd = dw + dl
            du = sum(float(r["pl_units"] or 0) for r in dr)
            cum_units += du
            history_data.append({
                "period": d,
                "predictions": len(dr),
                "wins": dw, "losses": dl,
                "win_rate": round(dw / dd, 4) if dd > 0 else 0,
                "daily_win_rate": round(dw / dd, 4) if dd > 0 else 0,
                "roi": round(cum_units / total, 4) if total > 0 else 0,
                "units_won": round(cum_units, 2),
                "pnl_dollars": round(cum_units * unit_size, 0),
            })

        preds_list = []
        for r in sorted(rows, key=lambda x: str(x["game_date"]), reverse=True)[:50]:
            preds_list.append({
                "prediction_id": r["prediction_id"],
                "game_date": str(r["game_date"]),
                "sport": (r["sport"] or "").upper(),
                "away_team": r["away_team"] or "",
                "home_team": r["home_team"] or "",
                "bet_type": r["bet_type"] or "",
                "predicted_value": round(float(r["predicted_value"] or 0), 1),
                "market_value": round(float(r["market_value"] or 0), 1),
                "edge": round(float(r["edge_pct"] or 0), 2),
                "recommendation": r["recommendation"] or "",
                "confidence": (r["confidence"] or "medium").upper(),
                "model": r["model"] or "rule_multibook_vig",
                "result": (r["result"] or "pending").upper(),
                "profit_loss": round(float(r["pl_units"] or 0) * unit_size, 2),
            })

        return {
            "summary": {
                "total_predictions": total,
                "wins": wins, "losses": losses, "pushes": pushes,
                "record": _rec(wins, losses, pushes),
                "win_rate": round(win_rate, 4),
                "display_win_rate": f"{round(win_rate*100,1)}%",
                "units_won": round(units_won, 2),
                "display_units": f"{'+'if units_won>=0 else ''}{ units_won:.2f}u",
                "roi": round(roi * 100, 2),
                "display_roi": f"{'+'if roi>=0 else ''}{roi*100:.1f}%",
                "pnl_dollars": round(pnl_dollars, 0),
                "display_pnl": f"{'+'if pnl_dollars>=0 else ''}${abs(pnl_dollars):.0f}",
                "avg_edge": round(avg_edge, 2),
                "time_period": f"Last {days} days",
            },
            "by_sport": by_sport,
            "by_model": by_model,
            "by_confidence": by_confidence,
            "history": history_data,
            "predictions": preds_list,
            "predictions_total": total,
            "models": [{"name": "rule_multibook_vig", "description": "Multi-Book Vig Detector", "type": "rule"}],
            "filters": {"sport": sport, "model": model, "bet_type": bet_type, "days": days},
            "settings": {"unit_size": unit_size, "bankroll": bankroll},
            "generated_at": datetime.utcnow().isoformat(),
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
    model: str = Query(None),
    bet_type: str = Query(None),
    days: int = Query(7),
    result: str = Query(None, description="win, loss, push, or pending"),
    limit: int = Query(100)
):
    """Returns historical predictions from PostgreSQL pipeline DB."""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PG_DSN = "postgresql://maxev:maxev_sports@localhost:5432/maxev_sports"
    try:
        conn = psycopg2.connect(PG_DSN)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cutoff = (datetime.utcnow() - timedelta(days=days)).date()

        query = """
            SELECT
                p.id::text AS prediction_id,
                p.created_at_cst::date AS game_date,
                p.game_time_cst AS game_time,
                p.sport,
                p.away_team,
                p.home_team,
                p.pick_type AS bet_type,
                p.detector AS model,
                p.our_probability * 100 AS predicted_value,
                p.market_implied_prob * 100 AS market_value,
                p.edge_pct AS edge,
                p.pick_side AS recommendation,
                p.confidence_tier AS confidence,
                p.status AS result,
                COALESCE(p.pl_units, 0) * 100 AS profit_loss,
                p.market_odds,
                gr.home_score,
                gr.away_score,
                gr.total AS actual_total
            FROM predictions p
            LEFT JOIN game_results gr ON
                gr.sport = p.sport AND
                gr.home_team = p.home_team AND
                gr.away_team = p.away_team AND
                gr.game_date_cst = p.created_at_cst::date
            WHERE p.created_at_cst::date >= %s
        """
        params = [cutoff]
        if sport:
            query += " AND LOWER(p.sport) = LOWER(%s)"
            params.append(sport)
        if bet_type:
            _bt = {'totals': 'total', 'moneyline': 'ml', 'spreads': 'spread'}.get((bet_type or '').lower(), bet_type)
            query += " AND LOWER(p.pick_type) = LOWER(%s)"
            params.append(_bt)
        if model:
            query += " AND LOWER(p.detector) LIKE LOWER(%s)"
            params.append(f"%{model}%")
        if result:
            query += " AND LOWER(p.status) = LOWER(%s)"
            params.append(result)
        query += " ORDER BY p.created_at_cst DESC LIMIT %s"
        params.append(limit)

        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()

        predictions = []
        for row in rows:
            result_raw = (row.get("result") or "pending").upper()
            conf_raw   = (row.get("confidence") or "medium").upper()
            predictions.append({
                "prediction_id": row["prediction_id"],
                "game_date": str(row["game_date"]) if row.get("game_date") else "",
                "game_time": str(row["game_time"]) if row.get("game_time") else "",
                "sport": (row.get("sport") or "").upper(),
                "away_team": row.get("away_team") or "",
                "home_team": row.get("home_team") or "",
                "bet_type": row.get("bet_type") or "",
                "model": row.get("model") or "rule_multibook_vig",
                "predicted_value": round(float(row["predicted_value"] or 0), 1),
                "market_value": round(float(row["market_value"] or 0), 1),
                "edge": round(float(row["edge"] or 0), 2),
                "model_prob": round(float(row["predicted_value"] or 0), 1),
                "kelly": 0.0,
                "recommendation": row.get("recommendation") or "",
                "confidence": conf_raw,
                "bet_placed": "Y" if result_raw not in ("PENDING",) else "N",
                "actual_total": float(row["actual_total"]) if row.get("actual_total") is not None else None,
                "away_score": int(row["away_score"]) if row.get("away_score") is not None else None,
                "home_score": int(row["home_score"]) if row.get("home_score") is not None else None,
                "result": result_raw if result_raw != "PENDING" else None,
                "profit_loss": round(float(row["profit_loss"] or 0), 2),
                "market_odds": int(row["market_odds"]) if row.get("market_odds") is not None else None,
                "odds_source": "odds_api",
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
