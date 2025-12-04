"""
BULLETPROOF PLAYER PROPS - UI ENDPOINTS
========================================
Sacred /api/ui/ endpoints for player props

Uses unified predictions.db for all data:
- /api/ui/props-edges - Today's prop edges
- /api/ui/props-performance - Performance metrics
- /api/ui/props-historical - Historical results

IMPORTANT: This file is BULLETPROOF. Do not simplify or rename.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, date, timedelta
import logging
import sqlite3
import json
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ui", tags=["ui-props"])

# UNIFIED DATABASE PATH (Sacred - do not change)
UNIFIED_DB_PATH = Path(__file__).parent.parent / "ml" / "predictions.db"
PROPS_DB_PATH = Path(__file__).parent.parent / "data" / "player_props.db"


def get_db_connection(unified: bool = True):
    """Get database connection"""
    db_path = UNIFIED_DB_PATH if unified else PROPS_DB_PATH
    if not db_path.exists():
        raise HTTPException(status_code=500, detail=f"Database not found: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# =============================================================================
# /api/ui/props-edges - Today's Player Prop Edges
# =============================================================================

@router.get("/props-edges")
async def get_props_edges(
    sport: Optional[str] = None,
    prop_type: Optional[str] = None,
    min_confidence: int = 55,
    min_edge: float = 1.0,
    limit: int = 50,
    view_mode: str = "edges"
):
    """
    Get today's player prop edges from ML predictions

    Returns pre-computed edges with display-ready values:
    - display_edge: Formatted edge percentage
    - display_confidence: Formatted confidence
    - display_recommendation: OVER/UNDER with reasoning
    - kelly_fraction: Pre-computed Kelly bet sizing
    """
    try:
        conn = get_db_connection(unified=True)
        cursor = conn.cursor()

        today = date.today().strftime('%Y-%m-%d')

        # Build query
        where_clauses = ["prediction_date = ?"]
        params = [today]

        # For "all" view mode, show all props without filters
        if view_mode != "all":
            where_clauses.extend([
                "confidence >= ?",
                "ABS(edge) >= ?",
                "recommendation != 'NO_PLAY'"
            ])
            params.extend([min_confidence, min_edge])

        if sport:
            # Sport filtering would go here if we add sport column
            pass

        if prop_type:
            where_clauses.append("prop_type = ?")
            params.append(prop_type)

        where_sql = " AND ".join(where_clauses)
        params.append(limit)

        query = f"""
            SELECT
                id,
                player_name,
                team,
                opponent,
                prop_type,
                market_line,
                predicted_value,
                edge,
                over_probability,
                under_probability,
                confidence,
                recommendation,
                kelly_fraction,
                sportsbook,
                game_id,
                generated_at
            FROM player_prop_predictions
            WHERE {where_sql}
            ORDER BY confidence DESC, ABS(edge) DESC
            LIMIT ?
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Format edges with display-ready values
        edges = []
        for row in rows:
            edge_val = row['edge']
            conf_val = row['confidence']

            edges.append({
                # Core data
                "id": row['id'],
                "player_name": row['player_name'],
                "team": row['team'],
                "opponent": row['opponent'],
                "prop_type": row['prop_type'],
                "market_line": row['market_line'],
                "predicted_value": row['predicted_value'],

                # Pre-computed display values (BULLETPROOF)
                "display_edge": f"{edge_val:+.1f}",
                "display_confidence": f"{conf_val:.0f}%",
                "display_recommendation": row['recommendation'],
                "display_over_prob": f"{row['over_probability']:.1f}%",
                "display_under_prob": f"{row['under_probability']:.1f}%",

                # Raw values for calculations
                "edge": edge_val,
                "confidence": conf_val,
                "over_probability": row['over_probability'],
                "under_probability": row['under_probability'],
                "recommendation": row['recommendation'],
                "edge_pct": edge_val,
                "kelly_fraction": row['kelly_fraction'],

                # Odds - frontend expects over_odds and under_odds as numbers
                "over_odds": -110,  # Standard odds (we don't store actual odds)
                "under_odds": -110,  # Standard odds (we don't store actual odds)
                "odds": "-110",  # For backward compatibility

                # Metadata
                "sportsbook": row['sportsbook'] or "fanduel",
                "bookmaker": row['sportsbook'] or "fanduel",  # Alias for frontend compatibility
                "game_id": row['game_id'],
                "generated_at": row['generated_at']
            })

        conn.close()

        return {
            "edges": edges,
            "total": len(edges),
            "date": today,
            "filters": {
                "sport": sport or "all",
                "prop_type": prop_type or "all",
                "min_confidence": min_confidence,
                "min_edge": min_edge
            },
            "generated_at": datetime.utcnow().isoformat() + 'Z'
        }

    except Exception as e:
        logger.error(f"Error fetching props edges: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# /api/ui/props-performance - Props Model Performance
# =============================================================================

@router.get("/props-performance")
async def get_props_performance(
    days: int = 30,
    sport: Optional[str] = None,
    prop_type: Optional[str] = None
):
    """
    Get props ML model performance metrics

    Returns pre-computed display values:
    - display_win_rate: "52.3%"
    - display_units: "+12.5u"
    - display_roi: "+15.2%"
    """
    try:
        conn = get_db_connection(unified=False)
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        # Build where clause
        where_clauses = ["prediction_date >= ?", "result IS NOT NULL"]
        params = [cutoff_date]

        if prop_type:
            where_clauses.append("prop_type = ?")
            params.append(prop_type)

        where_sql = " AND ".join(where_clauses)

        # Overall stats
        query = f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN result = 'PUSH' THEN 1 ELSE 0 END) as pushes,
                AVG(confidence) as avg_confidence
            FROM player_props_predictions
            WHERE {where_sql}
        """

        cursor.execute(query, params)
        row = cursor.fetchone()

        total = row['total'] or 0
        wins = row['wins'] or 0
        losses = row['losses'] or 0
        pushes = row['pushes'] or 0

        # Calculate metrics
        win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0
        units_won = (wins * 0.91) - losses  # -110 odds
        roi = (units_won / total * 100) if total > 0 else 0

        # By prop type
        prop_type_query = f"""
            SELECT
                prop_type,
                COUNT(*) as total,
                SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses
            FROM player_props_predictions
            WHERE {where_sql}
            GROUP BY prop_type
        """

        cursor.execute(prop_type_query, params)
        by_prop_type = {}
        for row in cursor.fetchall():
            pt_wins = row['wins']
            pt_losses = row['losses']
            pt_total = row['total']
            pt_units = (pt_wins * 0.91) - pt_losses
            pt_wr = pt_wins / (pt_wins + pt_losses) if (pt_wins + pt_losses) > 0 else 0

            by_prop_type[row['prop_type']] = {
                "total": pt_total,
                "wins": pt_wins,
                "losses": pt_losses,
                "display_win_rate": f"{pt_wr*100:.1f}%",
                "display_units": f"{pt_units:+.2f}u",
                "display_roi": f"{(pt_units/pt_total*100):.1f}%" if pt_total > 0 else "0.0%"
            }

        # By confidence level
        conf_query = f"""
            SELECT
                CASE
                    WHEN confidence >= 70 THEN 'high'
                    WHEN confidence >= 55 THEN 'medium'
                    ELSE 'low'
                END as conf_level,
                COUNT(*) as total,
                SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses
            FROM player_props_predictions
            WHERE {where_sql}
            GROUP BY conf_level
        """

        cursor.execute(conf_query, params)
        by_confidence = {}
        for row in cursor.fetchall():
            c_wins = row['wins']
            c_losses = row['losses']
            c_total = row['total']
            c_units = (c_wins * 0.91) - c_losses
            c_wr = c_wins / (c_wins + c_losses) if (c_wins + c_losses) > 0 else 0

            by_confidence[row['conf_level']] = {
                "total": c_total,
                "wins": c_wins,
                "losses": c_losses,
                "display_win_rate": f"{c_wr*100:.1f}%",
                "display_units": f"{c_units:+.2f}u"
            }

        conn.close()

        return {
            "summary": {
                "total_predictions": total,
                "wins": wins,
                "losses": losses,
                "pushes": pushes,

                # Pre-computed display values (BULLETPROOF)
                "display_win_rate": f"{win_rate*100:.1f}%",
                "display_units": f"{units_won:+.2f}u",
                "display_roi": f"{roi:+.1f}%",
                "display_avg_confidence": f"{row['avg_confidence']:.0f}%" if row['avg_confidence'] else "N/A",

                # Raw values
                "win_rate": round(win_rate, 4),
                "units_won": round(units_won, 2),
                "roi": round(roi, 2)
            },
            "by_prop_type": by_prop_type,
            "by_confidence": by_confidence,
            "filters": {
                "days": days,
                "sport": sport or "all",
                "prop_type": prop_type or "all"
            },
            "generated_at": datetime.utcnow().isoformat() + 'Z'
        }

    except Exception as e:
        logger.error(f"Error fetching props performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# /api/ui/props-historical - Historical Props Results
# =============================================================================

@router.get("/props-historical")
async def get_props_historical(
    days: int = 90,
    prop_type: Optional[str] = None,
    result: Optional[str] = None,
    limit: int = 100
):
    """
    Get historical props predictions with results

    Returns graded predictions with display-ready values
    """
    try:
        conn = get_db_connection(unified=True)
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        where_clauses = ["prediction_date >= ?", "result IS NOT NULL"]
        params = [cutoff_date]

        if prop_type:
            where_clauses.append("prop_type = ?")
            params.append(prop_type)

        if result:
            where_clauses.append("result = ?")
            params.append(result.upper())

        where_sql = " AND ".join(where_clauses)
        params.append(limit)

        query = f"""
            SELECT
                id,
                prediction_date,
                player_name,
                team,
                opponent,
                prop_type,
                market_line,
                predicted_value,
                actual_value,
                edge,
                confidence,
                recommendation,
                result,
                graded_at
            FROM player_props_predictions
            WHERE {where_sql}
            ORDER BY prediction_date DESC, confidence DESC
            LIMIT ?
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        predictions = []
        for row in rows:
            # Calculate profit/loss
            if row['result'] == 'WIN':
                profit_loss = 0.91
            elif row['result'] == 'LOSS':
                profit_loss = -1.0
            else:
                profit_loss = 0.0

            predictions.append({
                "id": row['id'],
                "prediction_date": row['prediction_date'],
                "player_name": row['player_name'],
                "team": row['team'],
                "opponent": row['opponent'],
                "prop_type": row['prop_type'],
                "market_line": row['market_line'],
                "predicted_value": row['predicted_value'],
                "actual_value": row['actual_value'],
                "edge": row['edge'],
                "confidence": row['confidence'],
                "recommendation": row['recommendation'],
                "result": row['result'],
                "graded_at": row['graded_at'],

                # Pre-computed display values
                "display_edge": f"{row['edge']:+.1f}" if row['edge'] else "N/A",
                "display_confidence": f"{row['confidence']:.0f}%" if row['confidence'] else "N/A",
                "display_profit_loss": f"{profit_loss:+.2f}u",
                "display_result": row['result']
            })

        # Daily aggregation for charts
        daily_query = f"""
            SELECT
                prediction_date,
                COUNT(*) as total,
                SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses
            FROM player_props_predictions
            WHERE {where_sql.replace('LIMIT ?', '')}
            GROUP BY prediction_date
            ORDER BY prediction_date ASC
        """

        cursor.execute(daily_query, params[:-1])  # Remove limit param

        history = []
        cumulative_wins = 0
        cumulative_losses = 0

        for row in cursor.fetchall():
            cumulative_wins += row['wins']
            cumulative_losses += row['losses']
            cumulative_units = (cumulative_wins * 0.91) - cumulative_losses
            cumulative_total = cumulative_wins + cumulative_losses
            cumulative_wr = cumulative_wins / cumulative_total if cumulative_total > 0 else 0

            history.append({
                "date": row['prediction_date'],
                "predictions": row['total'],
                "wins": row['wins'],
                "losses": row['losses'],
                "cumulative_units": round(cumulative_units, 2),
                "cumulative_win_rate": round(cumulative_wr, 4)
            })

        conn.close()

        return {
            "predictions": predictions,
            "history": history,
            "total": len(predictions),
            "filters": {
                "days": days,
                "prop_type": prop_type or "all",
                "result": result or "all"
            },
            "generated_at": datetime.utcnow().isoformat() + 'Z'
        }

    except Exception as e:
        logger.error(f"Error fetching props historical: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# /api/ui/health - Includes props status
# =============================================================================

@router.get("/props-health")
async def get_props_health():
    """
    Health check for props system

    Returns status of:
    - Unified database
    - Props predictions table
    - Today's edges count
    """
    try:
        status = {
            "unified_db": "OFFLINE",
            "props_table": "OFFLINE",
            "todays_edges": 0,
            "total_predictions": 0,
            "graded_predictions": 0
        }

        if UNIFIED_DB_PATH.exists():
            status["unified_db"] = "ONLINE"

            conn = get_db_connection(unified=True)
            cursor = conn.cursor()

            # Check props table
            cursor.execute("""
                SELECT COUNT(*) as count FROM sqlite_master
                WHERE type='table' AND name='player_props_predictions'
            """)
            if cursor.fetchone()['count'] > 0:
                status["props_table"] = "ONLINE"

            # Today's edges
            today = date.today().strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM player_props_predictions
                WHERE prediction_date = ?
            """, (today,))
            status["todays_edges"] = cursor.fetchone()['count']

            # Total predictions
            cursor.execute("SELECT COUNT(*) as count FROM player_props_predictions")
            status["total_predictions"] = cursor.fetchone()['count']

            # Graded predictions
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM player_props_predictions
                WHERE result IS NOT NULL
            """)
            status["graded_predictions"] = cursor.fetchone()['count']

            conn.close()

        return {
            "status": "BULLETPROOF" if status["unified_db"] == "ONLINE" else "DEGRADED",
            "props_system": status,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }

    except Exception as e:
        logger.error(f"Props health check failed: {str(e)}")
        return {
            "status": "ERROR",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }


# =============================================================================
# DFS CRUSHER ENDPOINTS
# =============================================================================

@router.get("/dfs-best-picks")
async def get_dfs_best_picks():
    """Get DFS Crusher best picks from all platforms"""
    try:
        cache_file = Path("/root/sporttrader/backend/ml/dfs/cache/dfs_crusher_latest.json")
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                data = json.load(f)
            return data
        else:
            return {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "total_demons": 0,
                "plays": []
            }
    except Exception as e:
        logger.error(f"Error in dfs-best-picks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dfs-combos")
async def get_dfs_combos(sport: str = 'nba', min_demon_score: float = 0, limit: int = 50):
    """Get correlated DFS combos"""
    try:
        conn = get_db_connection(unified=True)
        cursor = conn.cursor()

        today = date.today().strftime('%Y-%m-%d')

        # Get all combos for stats
        cursor.execute("""
            SELECT combo_id, sport, players, props, lines, directions,
                   true_probability, prize_picks_payout, expected_value_percent,
                   demon_goblin_score, site_with_best_line,
                   display_edge, display_confidence, display_recommendation,
                   display_win_rate, display_units, display_roi, created_at
            FROM correlated_combos
            WHERE date(created_at) = ?
              AND sport = ?
            ORDER BY expected_value_percent DESC
        """, (today, sport))

        all_rows = cursor.fetchall()
        all_combos = [dict(row) for row in all_rows]

        # Parse JSON strings into arrays for frontend
        import json
        for combo in all_combos:
            try:
                combo['players'] = json.loads(combo['players']) if isinstance(combo['players'], str) else combo['players']
                combo['props'] = json.loads(combo['props']) if isinstance(combo['props'], str) else combo['props']
                combo['lines'] = json.loads(combo['lines']) if isinstance(combo['lines'], str) else combo['lines']
                combo['directions'] = json.loads(combo['directions']) if isinstance(combo['directions'], str) else combo['directions']

                # Add derived fields for frontend
                combo['num_legs'] = len(combo['players']) if isinstance(combo['players'], list) else 0
                combo['payout_multiplier'] = round(combo.get('prize_picks_payout', 3.0), 2)
                combo['expected_value_percent'] = round(combo.get('expected_value_percent', 0), 2)
                combo['demon_goblin_score'] = round(combo.get('demon_goblin_score', 0), 2)

                # Round all numeric database fields to 2 decimals
                if combo.get('display_edge') is not None:
                    combo['display_edge'] = round(combo['display_edge'], 2)
                if combo.get('true_probability') is not None:
                    combo['true_probability'] = round(combo['true_probability'], 2)
                if combo.get('display_units') is not None:
                    combo['display_units'] = round(combo['display_units'], 2)

                # Transform separate arrays into props array of objects for frontend
                if (isinstance(combo.get('players'), list) and
                    isinstance(combo.get('props'), list) and
                    isinstance(combo.get('lines'), list) and
                    isinstance(combo.get('directions'), list)):

                    props_objects = []
                    for i in range(len(combo['players'])):
                        props_objects.append({
                            'player_name': combo['players'][i],
                            'prop_type': combo['props'][i],
                            'display_line': combo['lines'][i],
                            'direction': combo['directions'][i]
                        })
                    combo['props'] = props_objects
            except:
                pass

        # Filter and limit for display
        filtered_combos = [c for c in all_combos if c['demon_goblin_score'] >= min_demon_score]
        display_combos = filtered_combos[:limit]

        # Calculate stats
        total_combos = len(all_combos)
        demon_mode = len([c for c in all_combos if c.get('display_recommendation') == 'DEMON_MODE'])
        goblin_mode = len([c for c in all_combos if c.get('display_recommendation') == 'GOBLIN_MODE'])
        normal = len([c for c in all_combos if c.get('display_recommendation') == 'NORMAL'])

        conn.close()

        return {
            "combos": display_combos,
            "count": len(display_combos),
            "stats": {
                "total_combos": total_combos,
                "demon_mode": demon_mode,
                "goblin_mode": goblin_mode,
                "normal": normal
            },
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"Error in dfs-combos: {e}")
        return {
            "combos": [],
            "count": 0,
            "stats": {
                "total_combos": 0,
                "demon_mode": 0,
                "goblin_mode": 0,
                "normal": 0
            },
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
