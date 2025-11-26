"""
Goalie Pull Timing Alpha - API Routes

Endpoints:
- GET /api/goalie-pull/status - Monitor service status
- POST /api/goalie-pull/start - Start monitoring
- POST /api/goalie-pull/stop - Stop monitoring
- GET /api/goalie-pull/alerts - Get recent alerts
- GET /api/goalie-pull/alerts/{alert_id} - Get specific alert
- GET /api/goalie-pull/performance - Performance metrics (CLV, ROI)
- GET /api/goalie-pull/team-stats - Empty net team statistics and rankings
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import threading
import sys
import os
import pandas as pd

# Add goalie_pull directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ml', 'goalie_pull'))

from database_schema import GoaliePullDB
from live_monitor_service import LiveGoaliePullMonitor

router = APIRouter(prefix="/api/goalie-pull", tags=["goalie-pull"])

# Global monitor instance
monitor_instance: Optional[LiveGoaliePullMonitor] = None
monitor_thread: Optional[threading.Thread] = None


class MonitorStatus(BaseModel):
    """Monitor service status"""
    running: bool
    uptime_seconds: Optional[float]
    scans_completed: int
    games_monitored: int
    alerts_generated: int
    bets_recommended: int


class Alert(BaseModel):
    """Goalie pull alert"""
    alert_id: Optional[int]
    alert_timestamp: str
    game_id: str
    home_team: str
    away_team: str
    trailing_team: str
    time_remaining: str
    time_remaining_seconds: int
    score_diff: int
    coach_id: Optional[str]
    pull_propensity: float
    p_at_least_1_goal: float
    fair_price_american: int
    offered_price_american: Optional[int]
    bet_size: Optional[float]
    ev_at_entry: Optional[float]
    bet_placed: bool


@router.get("/status")
async def get_monitor_status() -> MonitorStatus:
    """Get current status of monitoring service"""
    global monitor_instance

    if not monitor_instance or not monitor_instance.running:
        return MonitorStatus(
            running=False,
            uptime_seconds=None,
            scans_completed=0,
            games_monitored=0,
            alerts_generated=0,
            bets_recommended=0
        )

    # Calculate uptime
    uptime = None
    if monitor_instance.stats['start_time']:
        uptime = (datetime.now() - monitor_instance.stats['start_time']).total_seconds()

    return MonitorStatus(
        running=True,
        uptime_seconds=uptime,
        scans_completed=monitor_instance.stats['scans_completed'],
        games_monitored=monitor_instance.stats['games_monitored'],
        alerts_generated=monitor_instance.stats['alerts_generated'],
        bets_recommended=monitor_instance.stats['bets_recommended']
    )


@router.post("/start")
async def start_monitor(background_tasks: BackgroundTasks):
    """Start the goalie pull monitoring service"""
    global monitor_instance, monitor_thread

    if monitor_instance and monitor_instance.running:
        raise HTTPException(status_code=400, detail="Monitor is already running")

    # Create monitor with production config
    config = {
        'propensity_threshold_aggressive': 0.35,
        'propensity_threshold_moderate': 0.45,
        'propensity_threshold_conservative': 0.60,
        'cushion_decimal': 0.12,
        'min_ev_pct': 2.0,
        'kelly_fraction': 0.25,
        'max_bet_pct_bankroll': 0.02,
        'scan_interval_seconds': 5,
    }

    monitor_instance = LiveGoaliePullMonitor(config=config)

    # Run in background thread
    def run_monitor():
        monitor_instance.start(duration_seconds=None)  # Run indefinitely

    monitor_thread = threading.Thread(target=run_monitor, daemon=True)
    monitor_thread.start()

    return {
        "success": True,
        "message": "Goalie pull monitor started",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/stop")
async def stop_monitor():
    """Stop the goalie pull monitoring service"""
    global monitor_instance

    if not monitor_instance or not monitor_instance.running:
        raise HTTPException(status_code=400, detail="Monitor is not running")

    monitor_instance.running = False

    return {
        "success": True,
        "message": "Goalie pull monitor stopped",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/alerts", response_model=List[Alert])
async def get_recent_alerts(limit: int = 20, hours: int = 24):
    """
    Get recent alerts

    Args:
        limit: Maximum number of alerts to return
        hours: Look back window in hours (default 24)
    """
    db = GoaliePullDB()

    try:
        # Query recent alerts
        query = """
            SELECT *
            FROM goalie_pull_alerts
            WHERE alert_timestamp >= datetime('now', '-{} hours')
            ORDER BY alert_timestamp DESC
            LIMIT ?
        """.format(hours)

        alerts = db.conn.execute(query, (limit,)).fetchall()

        # Convert to dicts
        alert_list = []
        for row in alerts:
            alert_dict = dict(row)
            alert_list.append(Alert(**alert_dict))

        return alert_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")


@router.get("/alerts/{alert_id}")
async def get_alert(alert_id: int):
    """Get specific alert by ID"""
    db = GoaliePullDB()

    try:
        query = "SELECT * FROM goalie_pull_alerts WHERE id = ?"
        row = db.conn.execute(query, (alert_id,)).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

        return dict(row)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alert: {str(e)}")


@router.get("/performance")
async def get_performance_metrics(days: int = 30):
    """
    Get performance metrics for goalie pull alerts

    Args:
        days: Number of days to analyze

    Returns:
        CLV, ROI, hit rate, etc.
    """
    db = GoaliePullDB()

    try:
        # Query alerts with results
        query = """
            SELECT
                COUNT(*) as total_alerts,
                SUM(CASE WHEN bet_placed = 1 THEN 1 ELSE 0 END) as bets_placed,
                SUM(CASE WHEN bet_result = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN bet_result = 'LOSS' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN bet_result = 'PUSH' THEN 1 ELSE 0 END) as pushes,
                AVG(CASE WHEN clv_captured IS NOT NULL THEN clv_captured ELSE 0 END) as avg_clv,
                AVG(CASE WHEN ev_at_entry IS NOT NULL THEN ev_at_entry ELSE 0 END) as avg_ev_entry
            FROM goalie_pull_alerts
            WHERE alert_timestamp >= datetime('now', '-{} days')
        """.format(days)

        row = db.conn.execute(query).fetchone()
        stats = dict(row)

        # Calculate metrics
        total_bets = stats['bets_placed'] or 0
        wins = stats['wins'] or 0
        losses = stats['losses'] or 0
        pushes = stats['pushes'] or 0

        if total_bets > 0:
            hit_rate = (wins / total_bets) * 100 if total_bets > 0 else 0

            # Calculate ROI (simplified - assumes flat betting)
            roi = ((wins - losses) / total_bets) * 100 if total_bets > 0 else 0
        else:
            hit_rate = 0
            roi = 0

        return {
            "period_days": days,
            "total_alerts": stats['total_alerts'],
            "bets_placed": total_bets,
            "wins": wins,
            "losses": losses,
            "pushes": pushes,
            "hit_rate_pct": round(hit_rate, 1),
            "roi_pct": round(roi, 1),
            "avg_clv_cents": round(stats['avg_clv'] * 100, 1) if stats['avg_clv'] else 0,
            "avg_ev_entry_pct": round(stats['avg_ev_entry'], 1) if stats['avg_ev_entry'] else 0
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate metrics: {str(e)}")


@router.get("/coach-profiles")
async def get_coach_profiles():
    """Get all coach pull profiles"""
    db = GoaliePullDB()

    try:
        query = """
            SELECT *
            FROM coach_profiles
            ORDER BY total_pulls DESC
        """

        coaches = db.conn.execute(query).fetchall()

        return [dict(row) for row in coaches]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch coaches: {str(e)}")


@router.get("/live-games")
async def get_live_games():
    """Get current NHL games being monitored"""
    global monitor_instance

    if not monitor_instance:
        return {"games": [], "message": "Monitor not running"}

    return {
        "games": list(monitor_instance.active_games.values()),
        "count": len(monitor_instance.active_games)
    }


@router.get("/team-stats")
async def get_empty_net_team_stats():
    """
    Get empty net statistics and rankings for all NHL teams

    Returns team rankings for:
    - Goals scored (offensive)
    - Goals allowed (offensive situations)
    - Goals scored (defensive situations)
    - Goals allowed (defensive)
    - Success rates and differentials
    """
    try:
        # Path to EN_DATA.csv
        en_data_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'data',
            'raw',
            'nhl',
            'EN_DATA.csv'
        )

        # Alternative path if not found
        if not os.path.exists(en_data_path):
            en_data_path = r'D:\backend\data\NHL Empty_Net_Data_Daily\EN_DATA.csv'

        if not os.path.exists(en_data_path):
            raise HTTPException(
                status_code=404,
                detail="EN_DATA.csv not found. Please ensure empty net data is scraped."
            )

        # Read CSV
        df = pd.read_csv(en_data_path)

        # Convert to list of dicts
        teams = df.to_dict('records')

        # Sort by differential (best teams first)
        teams_sorted = sorted(teams, key=lambda x: x.get('en_differential', 0), reverse=True)

        return {
            "teams": teams_sorted,
            "total_teams": len(teams_sorted),
            "last_updated": datetime.now().isoformat(),
            "data_path": en_data_path
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Empty net data file not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load team stats: {str(e)}"
        )
