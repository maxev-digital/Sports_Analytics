"""
Alert Performance API Routes
Tracks alert performance, win rates, and ROI across all alert types and sports
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import pandas as pd
from pathlib import Path
import numpy as np
import math

logger = logging.getLogger(__name__)

def safe_float(value):
    """Convert to float, returning None for NaN/inf values"""
    if value is None:
        return None
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None

router = APIRouter(prefix="/api/alert-performance", tags=["alert-performance"])

# Data paths
TRACKING_DIR = Path(__file__).parent.parent / "data" / "tracking"
ALERTS_LOG = TRACKING_DIR / "alerts_log.csv"
ALERTS_RESULTS_LOG = TRACKING_DIR / "alerts_results_log.csv"
ALERTS_PERFORMANCE_SUMMARY = TRACKING_DIR / "alerts_performance_summary.csv"


@router.get("/overview")
async def get_performance_overview(
    sport: Optional[str] = None,
    alert_type: Optional[str] = None,
    confidence: Optional[str] = None,
    days: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get comprehensive alert performance overview

    Query Parameters:
    - sport: Filter by sport (basketball_nba, icehockey_nhl, etc.)
    - alert_type: Filter by alert type (arbitrage, steam_move, middle, goalie_pull, etc.)
    - confidence: Filter by confidence level (HIGH, MEDIUM, LOW)
    - days: Number of days to include (default: all time)

    Returns:
    - overall_stats: Total performance metrics
    - by_alert_type: Performance breakdown by type
    - by_sport: Performance breakdown by sport
    - by_confidence: Performance breakdown by confidence level
    """
    try:
        # Read alerts and results
        if not ALERTS_LOG.exists():
            return {
                "overall_stats": {},
                "by_alert_type": [],
                "by_sport": [],
                "by_confidence": [],
                "message": "No alert data available yet"
            }

        alerts_df = pd.read_csv(ALERTS_LOG)

        # Read results if exists
        if ALERTS_RESULTS_LOG.exists():
            results_df = pd.read_csv(ALERTS_RESULTS_LOG)
            # Merge on alert_id
            df = pd.merge(
                alerts_df,
                results_df,
                on='alert_id',
                how='left',
                suffixes=('', '_result')
            )
        else:
            df = alerts_df
            df['outcome'] = None
            df['profit_loss'] = None

        # Apply filters
        if sport:
            df = df[df['sport'] == sport]

        if alert_type:
            df = df[df['alert_type'] == alert_type]

        if confidence:
            df = df[df['confidence'] == confidence]

        if days:
            df['date_generated'] = pd.to_datetime(df['date_generated'])
            cutoff_date = datetime.now() - timedelta(days=days)
            df = df[df['date_generated'] >= cutoff_date]

        # Calculate overall stats
        total_alerts = len(df)
        settled = df[df['outcome'].notna()]
        settled_count = len(settled)
        pending_count = total_alerts - settled_count

        if settled_count > 0:
            wins = len(settled[settled['outcome'] == 'won'])
            losses = len(settled[settled['outcome'] == 'lost'])
            pushes = len(settled[settled['outcome'] == 'push'])

            # Win rate excludes pushes
            win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

            # Total profit/loss
            total_profit = settled['profit_loss'].sum()

            # ROI = (total profit / total bets) * 100
            roi = (total_profit / settled_count) * 100 if settled_count > 0 else 0

            # Average edge
            avg_edge = settled['edge_percent'].mean() if 'edge_percent' in settled.columns else 0

            # Average odds
            avg_odds = settled['recommended_odds'].mean()
        else:
            wins = losses = pushes = 0
            win_rate = roi = avg_edge = avg_odds = 0
            total_profit = 0

        overall_stats = {
            "total_alerts": total_alerts,
            "settled_alerts": settled_count,
            "pending_alerts": pending_count,
            "wins": wins,
            "losses": losses,
            "pushes": pushes,
            "win_rate": round(safe_float(win_rate) or 0, 1),
            "roi": round(safe_float(roi) or 0, 1),
            "total_profit": round(safe_float(total_profit) or 0, 2),
            "avg_edge": round(safe_float(avg_edge) or 0, 1),
            "avg_odds": round(safe_float(avg_odds) or 0, 0)
        }

        # Breakdown by alert type
        by_alert_type = []
        if not df.empty:
            for atype in df['alert_type'].unique():
                if pd.isna(atype):
                    continue

                type_df = df[df['alert_type'] == atype]
                type_settled = type_df[type_df['outcome'].notna()]

                type_stats = calculate_stats(type_df, type_settled)
                type_stats['alert_type'] = atype
                by_alert_type.append(type_stats)

            # Sort by ROI descending
            by_alert_type = sorted(by_alert_type, key=lambda x: x.get('roi', 0), reverse=True)

        # Breakdown by sport
        by_sport = []
        if not df.empty:
            for sport_key in df['sport'].unique():
                if pd.isna(sport_key):
                    continue

                sport_df = df[df['sport'] == sport_key]
                sport_settled = sport_df[sport_df['outcome'].notna()]

                sport_stats = calculate_stats(sport_df, sport_settled)
                sport_stats['sport'] = sport_key
                by_sport.append(sport_stats)

            # Sort by total alerts descending
            by_sport = sorted(by_sport, key=lambda x: x.get('total_alerts', 0), reverse=True)

        # Breakdown by confidence
        by_confidence = []
        if not df.empty and 'confidence' in df.columns:
            for conf in df['confidence'].unique():
                if pd.isna(conf) or conf == '':
                    continue

                conf_df = df[df['confidence'] == conf]
                conf_settled = conf_df[conf_df['outcome'].notna()]

                conf_stats = calculate_stats(conf_df, conf_settled)
                conf_stats['confidence'] = conf
                by_confidence.append(conf_stats)

            # Sort by confidence level (HIGH > MEDIUM > LOW)
            conf_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
            by_confidence = sorted(by_confidence, key=lambda x: conf_order.get(x.get('confidence', ''), 99))

        return {
            "overall_stats": overall_stats,
            "by_alert_type": by_alert_type,
            "by_sport": by_sport,
            "by_confidence": by_confidence
        }

    except Exception as e:
        logger.error(f"Error getting alert performance overview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def calculate_stats(df: pd.DataFrame, settled: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate performance statistics for a subset of alerts

    Args:
        df: All alerts dataframe
        settled: Settled alerts dataframe

    Returns:
        Dictionary with performance metrics
    """
    total = len(df)
    settled_count = len(settled)
    pending = total - settled_count

    if settled_count > 0:
        wins = len(settled[settled['outcome'] == 'won'])
        losses = len(settled[settled['outcome'] == 'lost'])
        pushes = len(settled[settled['outcome'] == 'push'])

        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        total_profit = settled['profit_loss'].sum()
        roi = (total_profit / settled_count) * 100 if settled_count > 0 else 0
        avg_edge = settled['edge_percent'].mean() if 'edge_percent' in settled.columns else 0
    else:
        wins = losses = pushes = 0
        win_rate = roi = avg_edge = 0
        total_profit = 0

    return {
        "total_alerts": total,
        "settled_alerts": settled_count,
        "pending_alerts": pending,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "win_rate": round(safe_float(win_rate) or 0, 1),
        "roi": round(safe_float(roi) or 0, 1),
        "total_profit": round(safe_float(total_profit) or 0, 2),
        "avg_edge": round(safe_float(avg_edge) or 0, 1)
    }


@router.get("/history")
async def get_performance_history(
    period: str = 'daily',  # daily, weekly, monthly
    days: int = 30,
    alert_type: Optional[str] = None,
    sport: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get historical performance over time

    Query Parameters:
    - period: Aggregation period (daily, weekly, monthly)
    - days: Number of days to include
    - alert_type: Filter by alert type
    - sport: Filter by sport

    Returns:
    - historical data with cumulative profit, win rate over time
    """
    try:
        if not ALERTS_LOG.exists():
            return {"history": [], "message": "No alert data available"}

        alerts_df = pd.read_csv(ALERTS_LOG)

        # Read results
        if ALERTS_RESULTS_LOG.exists():
            results_df = pd.read_csv(ALERTS_RESULTS_LOG)
            df = pd.merge(alerts_df, results_df, on='alert_id', how='left', suffixes=('', '_result'))
        else:
            df = alerts_df
            df['outcome'] = None
            df['profit_loss'] = None

        # Filter only settled alerts
        df = df[df['outcome'].notna()]

        if df.empty:
            return {"history": [], "message": "No settled alerts yet"}

        # Apply filters
        if alert_type:
            df = df[df['alert_type'] == alert_type]

        if sport:
            df = df[df['sport'] == sport]

        # Convert date
        df['date_generated'] = pd.to_datetime(df['date_generated'])

        # Filter to date range
        cutoff_date = datetime.now() - timedelta(days=days)
        df = df[df['date_generated'] >= cutoff_date]

        if df.empty:
            return {"history": [], "message": "No data in selected time range"}

        # Group by period
        if period == 'daily':
            df['period'] = df['date_generated'].dt.date
        elif period == 'weekly':
            df['period'] = df['date_generated'].dt.to_period('W').apply(lambda r: r.start_time.date())
        elif period == 'monthly':
            df['period'] = df['date_generated'].dt.to_period('M').apply(lambda r: r.start_time.date())
        else:
            df['period'] = df['date_generated'].dt.date

        # Aggregate by period
        grouped = df.groupby('period').agg({
            'alert_id': 'count',
            'profit_loss': 'sum',
            'outcome': lambda x: (x == 'won').sum()
        }).reset_index()

        grouped.columns = ['date', 'total_alerts', 'profit', 'wins']

        # Calculate win rate
        grouped['win_rate'] = (grouped['wins'] / grouped['total_alerts'] * 100).round(1)

        # Calculate cumulative profit
        grouped['cumulative_profit'] = grouped['profit'].cumsum()

        # Convert date to string for JSON serialization
        grouped['date'] = grouped['date'].astype(str)

        # Fill in missing dates
        # Create date range
        date_range = pd.date_range(
            start=cutoff_date.date(),
            end=datetime.now().date(),
            freq='D' if period == 'daily' else 'W' if period == 'weekly' else 'MS'
        )

        history = grouped.to_dict('records')

        return {
            "history": history,
            "period": period,
            "days": days
        }

    except Exception as e:
        logger.error(f"Error getting alert performance history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions")
async def get_individual_predictions(
    alert_type: Optional[str] = None,
    sport: Optional[str] = None,
    confidence: Optional[str] = None,
    outcome: Optional[str] = None,  # won, lost, push, pending
    days: Optional[int] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get individual alert predictions with filters

    Query Parameters:
    - alert_type: Filter by alert type
    - sport: Filter by sport
    - confidence: Filter by confidence level
    - outcome: Filter by outcome (won, lost, push, pending)
    - days: Number of days to include
    - limit: Max number of results
    - offset: Pagination offset

    Returns:
    - List of alerts with outcomes
    """
    try:
        if not ALERTS_LOG.exists():
            return {"predictions": [], "total": 0, "message": "No alert data available"}

        alerts_df = pd.read_csv(ALERTS_LOG)

        # Read results
        if ALERTS_RESULTS_LOG.exists():
            results_df = pd.read_csv(ALERTS_RESULTS_LOG)
            df = pd.merge(alerts_df, results_df, on='alert_id', how='left', suffixes=('', '_result'))
        else:
            df = alerts_df
            df['outcome'] = None
            df['profit_loss'] = None

        # Apply filters
        if alert_type:
            df = df[df['alert_type'] == alert_type]

        if sport:
            df = df[df['sport'] == sport]

        if confidence:
            df = df[df['confidence'] == confidence]

        if outcome:
            if outcome == 'pending':
                df = df[df['outcome'].isna()]
            else:
                df = df[df['outcome'] == outcome]

        if days:
            df['date_generated'] = pd.to_datetime(df['date_generated'])
            cutoff_date = datetime.now() - timedelta(days=days)
            df = df[df['date_generated'] >= cutoff_date]

        # Sort by date descending
        df = df.sort_values('date_generated', ascending=False)

        # Get total count before pagination
        total = len(df)

        # Apply pagination
        df = df.iloc[offset:offset+limit]

        # Convert to records
        predictions = []
        for _, row in df.iterrows():
            pred = {
                "alert_id": row.get('alert_id', ''),
                "alert_type": row.get('alert_type', ''),
                "date_generated": row.get('date_generated', ''),
                "game_id": row.get('game_id', ''),
                "sport": row.get('sport', ''),
                "away_team": row.get('away_team', ''),
                "home_team": row.get('home_team', ''),
                "game_date": row.get('game_date', ''),
                "market_type": row.get('market_type', ''),
                "recommended_side": row.get('recommended_side', ''),
                "recommended_odds": safe_float(row.get('recommended_odds', 0)),
                "recommended_bookmaker": row.get('recommended_bookmaker', ''),
                "confidence": row.get('confidence', ''),
                "edge_percent": safe_float(row.get('edge_percent', 0)),
                "profit_potential": safe_float(row.get('profit_potential', 0)),
                "status": row.get('status', 'pending'),
                "outcome": row.get('outcome', None),
                "profit_loss": safe_float(row.get('profit_loss', None)),
                "away_score": safe_float(row.get('away_score', None)),
                "home_score": safe_float(row.get('home_score', None)),
                "actual_total": safe_float(row.get('actual_total', None)),
                "notes": row.get('notes', '')
            }
            predictions.append(pred)

        return {
            "predictions": predictions,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error getting individual predictions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_summary() -> Dict[str, Any]:
    """
    Get quick summary stats for all alert types
    Reads from cached performance summary file

    Returns:
    - Summary statistics by alert type
    """
    try:
        if not ALERTS_PERFORMANCE_SUMMARY.exists():
            return {"summary": [], "message": "No summary data available"}

        df = pd.read_csv(ALERTS_PERFORMANCE_SUMMARY)

        summary = []
        for _, row in df.iterrows():
            summary.append({
                "alert_type": row.get('alert_type', ''),
                "total_alerts": int(row.get('total_alerts', 0)),
                "settled_alerts": int(row.get('settled_alerts', 0)),
                "pending_alerts": int(row.get('pending_alerts', 0)),
                "wins": int(row.get('wins', 0)),
                "losses": int(row.get('losses', 0)),
                "pushes": int(row.get('pushes', 0)),
                "win_rate": safe_float(row.get('win_rate', 0)),
                "roi": safe_float(row.get('roi', 0)),
                "total_profit": safe_float(row.get('total_profit', 0)),
                "avg_odds": safe_float(row.get('avg_odds', 0)),
                "last_updated": row.get('last_updated', '')
            })

        return {"summary": summary}

    except Exception as e:
        logger.error(f"Error getting summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
