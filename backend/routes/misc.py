"""
Miscellaneous routes — props cache, ML player props, bets extras,
real-time alerts WebSocket (/ws), and user feedback.
"""
import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

import app_state
import auth

logger = logging.getLogger(__name__)

router = APIRouter(tags=["misc"])


# ========== PROPS ==========

@router.get("/api/props/{sport}")
async def get_player_props(sport: str):
    """Get cached player props for a sport — returns instantly from memory cache."""
    sport_lower = sport.lower()
    if sport_lower in app_state.props_cache:
        cached = app_state.props_cache[sport_lower]
        return {
            "sport": sport,
            "count": cached["count"],
            "props": cached["props"],
            "last_updated": cached["last_updated"],
            "cached": True,
        }
    return {"sport": sport, "count": 0, "props": [], "error": "Invalid sport", "cached": False}


@router.get("/api/player-props/nba/edges")
async def get_nba_props_with_edges(min_edge_pct: float = 5.0):
    """NBA player props with ML-powered edge analysis from the autonomous props DB."""
    try:
        logger.info(f"Fetching ML NBA props with edges (min_edge: {min_edge_pct}%)")

        db_path = "D:/backend/data/player_props.db"
        if not os.path.exists(db_path):
            logger.warning(f"ML props database not found at {db_path}")
            return {
                "games": [], "total_props": 0,
                "total_strong_bets": 0, "total_moderate_bets": 0,
                "last_updated": datetime.now().isoformat(),
            }

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        today = datetime.now().date().isoformat()
        cursor.execute(
            """
            SELECT p.player_name, p.team, p.opponent, p.prop_type, p.market_line,
                   p.predicted_value, p.recommendation, p.confidence, p.edge_pct,
                   p.game_date, p.game_time, p.event_id,
                   s.minutes_per_game, s.season_avg, s.last_10_avg
            FROM player_props_predictions p
            LEFT JOIN player_stats_cache s
                ON p.player_name = s.player_name AND p.prop_type = s.stat_type
            WHERE p.game_date = ? AND p.recommendation != 'PASS' AND ABS(p.edge_pct) >= ?
            ORDER BY ABS(p.edge_pct) DESC
            """,
            (today, min_edge_pct),
        )
        predictions = cursor.fetchall()
        conn.close()

        games_dict: dict = {}
        total_strong = total_moderate = 0

        for pred in predictions:
            event_id = pred["event_id"] or f"{pred['team']}-{pred['opponent']}-{pred['game_date']}"
            if event_id not in games_dict:
                games_dict[event_id] = {
                    "event_id": event_id,
                    "sport_key": "basketball_nba",
                    "home_team": pred["team"] or "TBD",
                    "away_team": pred["opponent"] or "TBD",
                    "commence_time": pred["game_time"] or pred["game_date"],
                    "props": [],
                }
            edge_pct = abs(pred["edge_pct"])
            if edge_pct >= 10.0:
                bet_strength, total_strong = "STRONG", total_strong + 1
            elif edge_pct >= 7.0:
                bet_strength, total_moderate = "MODERATE", total_moderate + 1
            else:
                bet_strength = "WEAK"

            games_dict[event_id]["props"].append({
                "player_name": pred["player_name"],
                "team": pred["team"],
                "opponent": pred["opponent"],
                "game_time": pred["game_time"] or pred["game_date"],
                "prop_type": pred["prop_type"],
                "market_odds": {
                    "player_name": pred["player_name"],
                    "prop_type": pred["prop_type"],
                    "line": pred["market_line"],
                    "bookmakers": [],
                    "best_over_odds": -110,
                    "best_under_odds": -110,
                    "best_over_book": "DraftKings",
                    "best_under_book": "DraftKings",
                },
                "projection": {
                    "prop_type": pred["prop_type"],
                    "projection": round(pred["predicted_value"], 1),
                    "confidence": (
                        "HIGH" if pred["confidence"] >= 0.75
                        else "MEDIUM" if pred["confidence"] >= 0.60
                        else "LOW"
                    ),
                    "confidence_score": pred["confidence"],
                    "factors": {
                        "baseline": pred["season_avg"] or pred["predicted_value"],
                        "recent_avg": pred["last_10_avg"] or pred["predicted_value"],
                        "trend": "stable",
                        "total_adjustment": round(pred["predicted_value"] - pred["market_line"], 1),
                    },
                    "reasoning": (
                        f"ML model predicts {pred['predicted_value']:.1f} vs market line "
                        f"{pred['market_line']}. {pred['recommendation']} has {edge_pct:.1f}% edge."
                    ),
                },
                "edge": {
                    "edge": round(pred["predicted_value"] - pred["market_line"], 1),
                    "edge_pct": round(pred["edge_pct"], 1),
                    "recommendation": pred["recommendation"],
                    "bet_strength": bet_strength,
                },
            })

        games_list = list(games_dict.values())
        logger.info(
            f"Returning {len(predictions)} ML props from {len(games_list)} games "
            f"({total_strong} strong, {total_moderate} moderate)"
        )
        return {
            "games": games_list,
            "total_props": len(predictions),
            "total_strong_bets": total_strong,
            "total_moderate_bets": total_moderate,
            "last_updated": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error fetching ML NBA props: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========== BETS EXTRAS ==========

@router.post("/api/bets/grade-now")
async def manual_grade_bets():
    """Manually trigger bet grading for the past 7 days (runs in thread to avoid blocking)."""
    from datetime import date as _date, timedelta
    from grade_results import grade_picks_for_date

    def _run_grader():
        total_graded = total_won = total_lost = total_push = 0
        for days_ago in range(7):
            result = grade_picks_for_date(_date.today() - timedelta(days=days_ago))
            total_graded += result.get("graded", 0)
            total_won += result.get("won", 0)
            total_lost += result.get("lost", 0)
            total_push += result.get("push", 0)
        return total_graded, total_won, total_lost, total_push

    try:
        total_graded, total_won, total_lost, total_push = await asyncio.to_thread(_run_grader)
        return {
            "success": True,
            "graded": total_graded,
            "won": total_won,
            "lost": total_lost,
            "push": total_push,
            "errors": 0,
            "message": f"Graded {total_graded} picks ({total_won}W / {total_lost}L / {total_push}P)",
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in grade-now: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/bets/user-statistics")
async def get_user_bet_statistics(request: Request):
    """Win rate, ROI, and profit stats for the authenticated user."""
    try:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")

        username = auth.verify_session(auth_header.split(" ")[1])
        if not username:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        from storage.bet_storage import bet_storage
        all_bets = bet_storage.get_user_bets(username)
        settled = [b for b in all_bets if b.status in ("win", "loss", "push") and b.result and b.stake]

        if not settled:
            return {
                "total_bets": 0, "wins": 0, "losses": 0, "pushes": 0,
                "win_rate": 0.0, "roi": 0.0, "total_profit": 0.0, "total_wagered": 0.0,
            }

        wins = sum(1 for b in settled if b.result == "win")
        losses = sum(1 for b in settled if b.result == "loss")
        pushes = sum(1 for b in settled if b.result == "push")
        total_profit = sum(b.profit_loss for b in settled if b.profit_loss is not None)
        total_wagered = sum(b.stake for b in settled if b.stake is not None)
        decisive = wins + losses
        win_rate = (wins / decisive * 100) if decisive > 0 else 0.0
        roi = (total_profit / total_wagered * 100) if total_wagered > 0 else 0.0

        return {
            "total_bets": len(settled),
            "wins": wins, "losses": losses, "pushes": pushes,
            "win_rate": round(win_rate, 1),
            "roi": round(roi, 1),
            "total_profit": round(total_profit, 2),
            "total_wagered": round(total_wagered, 2),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating user bet statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate statistics: {str(e)}")


# ========== WEBSOCKET /ws (alerts) ==========

_active_ws_connections: list = []


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time alerts WebSocket — pushes arbitrage opportunities to connected clients."""
    try:
        await websocket.accept()
        _active_ws_connections.append(websocket)
        logger.info(f"[WS] Client connected. Total: {len(_active_ws_connections)}")

        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to ARB Auto Bettor™ WebSocket",
            "timestamp": datetime.now().isoformat(),
        })

        # Send current arbitrage alerts
        try:
            arbitrage_alerts = (
                app_state.alert_monitor.active_alerts.get("arbitrage", [])
                if app_state.alert_monitor else []
            )
        except Exception as e:
            logger.error(f"[WS] Error getting alerts: {e}")
            arbitrage_alerts = []

        serialized: list = []
        for alert in arbitrage_alerts:
            try:
                serialized.append({
                    "game_id": str(alert.game_id),
                    "sport": str(alert.sport),
                    "home_team": str(alert.home_team),
                    "away_team": str(alert.away_team),
                    "game": f"{alert.away_team} @ {alert.home_team}",
                    "market_type": str(alert.market_type),
                    "bookmaker1": str(alert.book_a),
                    "bookmaker2": str(alert.book_b),
                    "odds1": float(alert.odds_a),
                    "odds2": float(alert.odds_b),
                    "profit_percentage": float(alert.profit_percent),
                    "stake1": float(alert.stake_a),
                    "stake2": float(alert.stake_b),
                    "total_stake": float(alert.total_stake),
                    "guaranteed_profit": float(alert.guaranteed_profit),
                    "timestamp": alert.timestamp.isoformat(),
                    "expires_in": int(alert.expires_in),
                    "id": str(alert.game_id),
                })
            except Exception as e:
                logger.error(f"[WS] Alert serialization error: {e}")

        await websocket.send_json({"type": "opportunities_update", "opportunities": serialized})

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data) if data else {}
                if message.get("type") == "subscribe":
                    channel = message.get("channel", "all")
                    await websocket.send_json({
                        "type": "subscribed",
                        "channel": channel,
                        "message": f"Subscribed to {channel}",
                    })
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping", "timestamp": datetime.now().isoformat()})

    except WebSocketDisconnect:
        logger.info("[WS] Client disconnected")
    except Exception as e:
        logger.error(f"[WS] Error: {e}")
        raise
    finally:
        if websocket in _active_ws_connections:
            _active_ws_connections.remove(websocket)


# ========== FEEDBACK ==========

from storage.feedback_storage import feedback_storage


class FeedbackRequest(BaseModel):
    type: str
    comment: str
    page: str
    timestamp: str


def _get_username_from_request(request: Request) -> str:
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        verified = auth.verify_session(auth_header.split(" ")[1])
        if verified:
            return verified
    return "anonymous"


@router.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest, request: Request):
    """Submit a bug report, feature request, or general feedback."""
    try:
        username = _get_username_from_request(request)
        entry = feedback_storage.add_feedback(
            username=username,
            feedback_type=feedback.type,
            comment=feedback.comment,
            page=feedback.page,
            timestamp=feedback.timestamp,
        )
        logger.info(f"Feedback received from {username}: {feedback.type} on {feedback.page}")
        return {"status": "success", "message": "Thank you for your feedback!", "feedback_id": entry["id"]}
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@router.get("/api/feedback/all")
async def get_all_feedback(status: Optional[str] = None):
    """Get all feedback entries (admin only)."""
    try:
        return {
            "feedback": feedback_storage.get_all_feedback(status=status),
            "stats": feedback_storage.get_stats(),
        }
    except Exception as e:
        logger.error(f"Error retrieving feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback")


@router.post("/api/feedback/{feedback_id}/respond")
async def respond_to_feedback(feedback_id: str, request: Request):
    """Send an admin response to a feedback item."""
    try:
        data = await request.json()
        admin_response = data.get("response", "")
        if not admin_response:
            raise HTTPException(status_code=400, detail="Response cannot be empty")

        all_feedback = feedback_storage.get_all_feedback()
        item = next((f for f in all_feedback if f["id"] == feedback_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Feedback not found")

        users = auth.load_users()
        username = item.get("username", "anonymous")
        user_email = users.get(username, {}).get("email") if username != "anonymous" else None

        item["admin_response"] = admin_response
        item["admin_response_date"] = datetime.now().isoformat()
        item["status"] = "responded"
        feedback_storage._save_feedback(all_feedback)

        if user_email:
            try:
                from brevo_service import send_feedback_response_email
                send_feedback_response_email(
                    to_email=user_email,
                    username=username,
                    original_feedback=item["comment"],
                    admin_response=admin_response,
                    feedback_type=item["type"],
                )
            except Exception as email_err:
                logger.error(f"Failed to send feedback response email (non-critical): {email_err}")

        return {"status": "success", "message": "Response sent", "email_sent": user_email is not None}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error responding to feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to send response")


@router.get("/api/feedback/my-feedback")
async def get_my_feedback(request: Request):
    """Get feedback submitted by the current authenticated user."""
    try:
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")
        username = auth.verify_session(auth_header.split(" ")[1])
        if not username:
            raise HTTPException(status_code=401, detail="Invalid session")

        all_feedback = feedback_storage.get_all_feedback()
        user_feedback = sorted(
            [f for f in all_feedback if f.get("username") == username],
            key=lambda x: x.get("timestamp", ""),
            reverse=True,
        )
        return {"feedback": user_feedback}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback")


@router.post("/api/feedback/{feedback_id}/mark-viewed")
async def mark_feedback_viewed(feedback_id: str, request: Request):
    """Mark an admin response as viewed by the user."""
    try:
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")
        username = auth.verify_session(auth_header.split(" ")[1])
        if not username:
            raise HTTPException(status_code=401, detail="Invalid session")

        all_feedback = feedback_storage.get_all_feedback()
        item = next((f for f in all_feedback if f["id"] == feedback_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Feedback not found")
        if item.get("username") != username:
            raise HTTPException(status_code=403, detail="Not authorized")

        item["response_viewed"] = True
        item["response_viewed_date"] = datetime.now().isoformat()
        feedback_storage._save_feedback(all_feedback)
        return {"status": "success", "message": "Marked as viewed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking feedback as viewed: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark as viewed")
