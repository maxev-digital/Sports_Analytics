"""
Twitter Admin API Routes
Control Twitter automation settings and view statistics

Admin-only endpoints for managing Twitter bot
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/twitter", tags=["twitter-admin"])


# Global reference to Twitter service (initialized in main.py)
twitter_service = None


def set_twitter_service(service):
    """Set the global Twitter service instance"""
    global twitter_service
    twitter_service = service


# Request models
class TwitterConfigUpdate(BaseModel):
    """Update Twitter configuration"""
    enabled: Optional[bool] = None
    post_arbitrage: Optional[bool] = None
    post_steam_moves: Optional[bool] = None
    post_middles: Optional[bool] = None
    post_model_predictions: Optional[bool] = None
    post_strategy_alerts: Optional[bool] = None
    min_arbitrage_profit: Optional[float] = None
    min_steam_consensus: Optional[float] = None
    min_middle_gap_nhl: Optional[float] = None
    min_middle_gap_nba: Optional[float] = None
    min_model_edge: Optional[float] = None
    min_model_confidence: Optional[str] = None
    max_tweets_per_hour: Optional[int] = None
    scan_interval_seconds: Optional[int] = None


class TestTweetRequest(BaseModel):
    """Request to send a test tweet"""
    message: str


@router.get("/status")
async def get_twitter_status():
    """
    Get current Twitter automation status

    Returns:
        - enabled: Whether automation is active
        - authenticated: Whether Twitter client is authenticated
        - config: Current configuration
        - stats: Tweet statistics
    """
    if not twitter_service:
        raise HTTPException(status_code=503, detail="Twitter service not initialized")

    stats = twitter_service.get_stats()

    return {
        "enabled": stats.get('enabled', False),
        "authenticated": twitter_service.twitter_client.is_authenticated() if twitter_service.twitter_client else False,
        "config": stats.get('current_config', {}),
        "stats": {
            "total_tweets": stats.get('total_tweets', 0),
            "by_type": stats.get('by_type', {}),
            "last_24h": stats.get('last_24h', 0),
            "success_rate": stats.get('success_rate', '0%')
        }
    }


@router.post("/enable")
async def enable_twitter_automation():
    """
    Enable Twitter automation

    Starts automatically posting bet alerts to Twitter
    """
    if not twitter_service:
        raise HTTPException(status_code=503, detail="Twitter service not initialized")

    twitter_service.enable()

    return {
        "success": True,
        "message": "Twitter automation enabled",
        "enabled": True
    }


@router.post("/disable")
async def disable_twitter_automation():
    """
    Disable Twitter automation

    Stops automatically posting bet alerts to Twitter
    """
    if not twitter_service:
        raise HTTPException(status_code=503, detail="Twitter service not initialized")

    twitter_service.disable()

    return {
        "success": True,
        "message": "Twitter automation disabled",
        "enabled": False
    }


@router.put("/config")
async def update_twitter_config(config: TwitterConfigUpdate):
    """
    Update Twitter automation configuration

    Set thresholds for what types of alerts to post and minimum values

    **Example:**
    ```json
    {
        "enabled": true,
        "post_arbitrage": true,
        "min_arbitrage_profit": 0.5,
        "min_steam_consensus": 50,
        "max_tweets_per_hour": 20
    }
    ```
    """
    if not twitter_service:
        raise HTTPException(status_code=503, detail="Twitter service not initialized")

    updates = []

    # Boolean configs
    if config.enabled is not None:
        twitter_service._save_config('enabled', 'true' if config.enabled else 'false')
        updates.append(f"enabled = {config.enabled}")

    if config.post_arbitrage is not None:
        twitter_service._save_config('post_arbitrage', 'true' if config.post_arbitrage else 'false')
        updates.append(f"post_arbitrage = {config.post_arbitrage}")

    if config.post_steam_moves is not None:
        twitter_service._save_config('post_steam_moves', 'true' if config.post_steam_moves else 'false')
        updates.append(f"post_steam_moves = {config.post_steam_moves}")

    if config.post_middles is not None:
        twitter_service._save_config('post_middles', 'true' if config.post_middles else 'false')
        updates.append(f"post_middles = {config.post_middles}")

    if config.post_model_predictions is not None:
        twitter_service._save_config('post_model_predictions', 'true' if config.post_model_predictions else 'false')
        updates.append(f"post_model_predictions = {config.post_model_predictions}")

    if config.post_strategy_alerts is not None:
        twitter_service._save_config('post_strategy_alerts', 'true' if config.post_strategy_alerts else 'false')
        updates.append(f"post_strategy_alerts = {config.post_strategy_alerts}")

    # Numeric configs
    if config.min_arbitrage_profit is not None:
        twitter_service._save_config('min_arbitrage_profit', str(config.min_arbitrage_profit))
        updates.append(f"min_arbitrage_profit = {config.min_arbitrage_profit}%")

    if config.min_steam_consensus is not None:
        twitter_service._save_config('min_steam_consensus', str(config.min_steam_consensus))
        updates.append(f"min_steam_consensus = {config.min_steam_consensus}%")

    if config.min_middle_gap_nhl is not None:
        twitter_service._save_config('min_middle_gap_nhl', str(config.min_middle_gap_nhl))
        updates.append(f"min_middle_gap_nhl = {config.min_middle_gap_nhl}")

    if config.min_middle_gap_nba is not None:
        twitter_service._save_config('min_middle_gap_nba', str(config.min_middle_gap_nba))
        updates.append(f"min_middle_gap_nba = {config.min_middle_gap_nba}")

    if config.min_model_edge is not None:
        twitter_service._save_config('min_model_edge', str(config.min_model_edge))
        updates.append(f"min_model_edge = {config.min_model_edge}%")

    if config.min_model_confidence is not None:
        if config.min_model_confidence not in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
            raise HTTPException(status_code=400, detail="Invalid confidence level")
        twitter_service._save_config('min_model_confidence', config.min_model_confidence)
        updates.append(f"min_model_confidence = {config.min_model_confidence}")

    if config.max_tweets_per_hour is not None:
        if config.max_tweets_per_hour > 100:
            raise HTTPException(status_code=400, detail="max_tweets_per_hour cannot exceed 100")
        twitter_service._save_config('max_tweets_per_hour', str(config.max_tweets_per_hour))
        updates.append(f"max_tweets_per_hour = {config.max_tweets_per_hour}")

    if config.scan_interval_seconds is not None:
        if config.scan_interval_seconds < 60:
            raise HTTPException(status_code=400, detail="scan_interval_seconds cannot be less than 60")
        twitter_service._save_config('scan_interval_seconds', str(config.scan_interval_seconds))
        updates.append(f"scan_interval_seconds = {config.scan_interval_seconds}")

    return {
        "success": True,
        "message": "Configuration updated",
        "updates": updates
    }


@router.get("/config")
async def get_twitter_config():
    """
    Get current Twitter automation configuration

    Returns all configuration settings and thresholds
    """
    if not twitter_service:
        raise HTTPException(status_code=503, detail="Twitter service not initialized")

    config = twitter_service.config

    return {
        "enabled": config.get('enabled', 'false') == 'true',
        "post_arbitrage": config.get('post_arbitrage', 'false') == 'true',
        "post_steam_moves": config.get('post_steam_moves', 'false') == 'true',
        "post_middles": config.get('post_middles', 'false') == 'true',
        "post_model_predictions": config.get('post_model_predictions', 'false') == 'true',
        "post_strategy_alerts": config.get('post_strategy_alerts', 'false') == 'true',
        "min_arbitrage_profit": float(config.get('min_arbitrage_profit', 0.5)),
        "min_steam_consensus": float(config.get('min_steam_consensus', 50)),
        "min_middle_gap_nhl": float(config.get('min_middle_gap_nhl', 1.0)),
        "min_middle_gap_nba": float(config.get('min_middle_gap_nba', 3.0)),
        "min_model_edge": float(config.get('min_model_edge', 5.0)),
        "min_model_confidence": config.get('min_model_confidence', 'HIGH'),
        "max_tweets_per_hour": int(config.get('max_tweets_per_hour', 20)),
        "scan_interval_seconds": int(config.get('scan_interval_seconds', 300))
    }


@router.get("/stats")
async def get_twitter_stats():
    """
    Get detailed Twitter posting statistics

    Returns:
        - Total tweets posted
        - Breakdown by alert type
        - Success rate
        - Recent tweets (last 24 hours)
    """
    if not twitter_service:
        raise HTTPException(status_code=503, detail="Twitter service not initialized")

    stats = twitter_service.get_stats()

    return stats


@router.post("/test-tweet")
async def send_test_tweet(request: TestTweetRequest):
    """
    Send a test tweet to verify Twitter integration works

    **Example:**
    ```json
    {
        "message": "Testing MAX-EV Sports Twitter bot 🚀"
    }
    ```
    """
    if not twitter_service:
        raise HTTPException(status_code=503, detail="Twitter service not initialized")

    if not twitter_service.twitter_client:
        raise HTTPException(status_code=503, detail="Twitter client not authenticated")

    result = twitter_service.twitter_client.post_tweet(request.message)

    if result.success:
        return {
            "success": True,
            "tweet_id": result.tweet_id,
            "tweet_url": result.tweet_url,
            "message": "Test tweet posted successfully"
        }
    else:
        raise HTTPException(status_code=500, detail=f"Failed to post tweet: {result.error}")


@router.post("/trigger-scan")
async def trigger_immediate_scan():
    """
    Trigger an immediate scan for alerts (bypasses normal schedule)

    Useful for testing or forcing a refresh
    """
    if not twitter_service:
        raise HTTPException(status_code=503, detail="Twitter service not initialized")

    logger.info("Manual scan triggered via API")

    try:
        await twitter_service.scan_and_post()
        return {
            "success": True,
            "message": "Scan completed",
            "tweets_posted_last_3h": len(twitter_service.tweets_posted_last_3_hours)
        }
    except Exception as e:
        logger.error(f"Failed to run scan: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.get("/recent-tweets")
async def get_recent_tweets(limit: int = 50):
    """
    Get recently posted tweets

    Args:
        limit: Maximum number of tweets to return (default 50, max 200)

    Returns:
        List of recent tweets with details
    """
    if not twitter_service:
        raise HTTPException(status_code=503, detail="Twitter service not initialized")

    if limit > 200:
        limit = 200

    try:
        from db_utils import get_optimized_connection

        conn = get_optimized_connection(str(twitter_service.db_path))
        cursor = conn.execute("""
            SELECT
                tweet_id,
                tweet_url,
                alert_type,
                game_id,
                sport,
                home_team,
                away_team,
                tweet_text,
                posted_at,
                success
            FROM posted_tweets
            ORDER BY posted_at DESC
            LIMIT ?
        """, (limit,))

        tweets = []
        for row in cursor.fetchall():
            tweets.append({
                "tweet_id": row[0],
                "tweet_url": row[1],
                "alert_type": row[2],
                "game_id": row[3],
                "sport": row[4],
                "home_team": row[5],
                "away_team": row[6],
                "tweet_text": row[7],
                "posted_at": row[8],
                "success": bool(row[9])
            })

        conn.close()

        return {
            "tweets": tweets,
            "count": len(tweets)
        }

    except Exception as e:
        logger.error(f"Failed to fetch recent tweets: {e}")
        raise HTTPException(status_code=500, detail=str(e))
