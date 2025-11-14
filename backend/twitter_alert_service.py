"""
Twitter Alert Service - Automated Bet Alert Posting
Monitors for new high-value alerts and automatically posts them to Twitter

Features:
- Real-time monitoring of arbitrage, steam moves, middles
- Monitors Edge Lab predictions (high confidence only)
- Monitors strategy alerts (quarter reversal, favorite comeback, etc.)
- Intelligent filtering (only post high-value alerts)
- Duplicate prevention (don't post same alert twice)
- Rate limiting (respect Twitter API limits)
- Admin controls (enable/disable, set thresholds)
"""

import asyncio
import logging
import sqlite3
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from pathlib import Path
import json

from twitter_integration import get_twitter_client, TweetResult
from alert_monitor import AlertMonitor
from db_utils import get_optimized_connection

logger = logging.getLogger(__name__)


class TwitterAlertService:
    """Service that monitors alerts and posts them to Twitter"""

    def __init__(self, odds_api_key: str):
        """
        Initialize Twitter alert service

        Args:
            odds_api_key: The Odds API key for fetching alerts
        """
        # Initialize Twitter client
        self.twitter_client = get_twitter_client()
        if not self.twitter_client:
            logger.error("❌ Twitter client initialization failed")
            self.enabled = False
        else:
            logger.info("✅ Twitter alert service initialized")
            self.enabled = True

        # Initialize alert monitor
        self.alert_monitor = AlertMonitor(odds_api_key)

        # Database for tracking posted tweets
        self.db_path = Path(__file__).parent / "twitter_alerts.db"
        self._init_database()

        # Configuration (loaded from database)
        self.config = self._load_config()

        # Set of already-posted alert IDs (prevent duplicates)
        self.posted_alerts: Set[str] = set()
        self._load_posted_alerts()

        # Rate limiting (Twitter allows 300 tweets per 3 hours)
        self.tweets_posted_last_3_hours: List[datetime] = []

    def _init_database(self):
        """Initialize SQLite database for tracking posted tweets"""
        try:
            conn = get_optimized_connection(str(self.db_path))

            # Table for posted tweets
            conn.execute("""
                CREATE TABLE IF NOT EXISTS posted_tweets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tweet_id TEXT,
                    tweet_url TEXT,
                    alert_type TEXT NOT NULL,
                    alert_id TEXT NOT NULL UNIQUE,
                    game_id TEXT,
                    sport TEXT,
                    home_team TEXT,
                    away_team TEXT,
                    tweet_text TEXT,
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success INTEGER DEFAULT 1,
                    error_message TEXT
                )
            """)

            # Table for configuration
            conn.execute("""
                CREATE TABLE IF NOT EXISTS twitter_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Initialize default config if not exists
            default_config = {
                'enabled': 'true',
                'post_arbitrage': 'true',
                'post_steam_moves': 'true',
                'post_middles': 'true',
                'post_model_predictions': 'true',
                'post_strategy_alerts': 'true',
                'min_arbitrage_profit': '0.5',  # 0.5% minimum
                'min_steam_consensus': '50',  # 50% of books must move
                'min_middle_gap_nhl': '1.0',  # 1.0 for NHL
                'min_middle_gap_nba': '3.0',  # 3.0 for NBA
                'min_model_edge': '5.0',  # 5% minimum edge
                'min_model_confidence': 'HIGH',  # HIGH or CRITICAL only
                'max_tweets_per_hour': '20',  # Max 20 tweets per hour
                'scan_interval_seconds': '300'  # Scan every 5 minutes
            }

            for key, value in default_config.items():
                conn.execute("""
                    INSERT OR IGNORE INTO twitter_config (key, value)
                    VALUES (?, ?)
                """, (key, value))

            conn.commit()
            conn.close()

            logger.info("✅ Twitter alerts database initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")

    def _load_config(self) -> Dict:
        """Load configuration from database"""
        try:
            conn = get_optimized_connection(str(self.db_path))
            cursor = conn.execute("SELECT key, value FROM twitter_config")
            config = {row[0]: row[1] for row in cursor.fetchall()}
            conn.close()
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def _save_config(self, key: str, value: str):
        """Save configuration to database"""
        try:
            conn = get_optimized_connection(str(self.db_path))
            conn.execute("""
                INSERT OR REPLACE INTO twitter_config (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))
            conn.commit()
            conn.close()
            self.config[key] = value
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def _load_posted_alerts(self):
        """Load already-posted alert IDs from database (last 7 days)"""
        try:
            conn = get_optimized_connection(str(self.db_path))
            cutoff = datetime.now() - timedelta(days=7)
            cursor = conn.execute("""
                SELECT alert_id FROM posted_tweets
                WHERE posted_at >= ?
            """, (cutoff,))
            self.posted_alerts = {row[0] for row in cursor.fetchall()}
            conn.close()
            logger.info(f"Loaded {len(self.posted_alerts)} posted alerts from last 7 days")
        except Exception as e:
            logger.error(f"Failed to load posted alerts: {e}")

    def _record_tweet(
        self,
        alert_type: str,
        alert_id: str,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        tweet_text: str,
        result: TweetResult
    ):
        """Record a posted tweet in the database"""
        try:
            conn = get_optimized_connection(str(self.db_path))
            conn.execute("""
                INSERT INTO posted_tweets (
                    tweet_id, tweet_url, alert_type, alert_id,
                    game_id, sport, home_team, away_team,
                    tweet_text, success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.tweet_id,
                result.tweet_url,
                alert_type,
                alert_id,
                game_id,
                sport,
                home_team,
                away_team,
                tweet_text,
                1 if result.success else 0,
                result.error
            ))
            conn.commit()
            conn.close()

            # Add to posted_alerts set
            self.posted_alerts.add(alert_id)

        except Exception as e:
            logger.error(f"Failed to record tweet: {e}")

    def _check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits

        Returns:
            True if we can post, False if rate limit exceeded
        """
        # Clean old entries (older than 3 hours)
        cutoff = datetime.now() - timedelta(hours=3)
        self.tweets_posted_last_3_hours = [
            t for t in self.tweets_posted_last_3_hours if t > cutoff
        ]

        # Twitter allows 300 tweets per 3 hours
        # We'll be more conservative: max 20 per hour = 60 per 3 hours
        max_per_hour = int(self.config.get('max_tweets_per_hour', 20))
        max_per_3_hours = max_per_hour * 3

        if len(self.tweets_posted_last_3_hours) >= max_per_3_hours:
            logger.warning(f"⚠️ Rate limit reached: {len(self.tweets_posted_last_3_hours)} tweets in last 3 hours")
            return False

        return True

    def _should_post_arbitrage(self, alert: Dict) -> bool:
        """Check if arbitrage alert should be posted"""
        if self.config.get('post_arbitrage', 'true') != 'true':
            return False

        min_profit = float(self.config.get('min_arbitrage_profit', 0.5))
        return alert['profit_percent'] >= min_profit

    def _should_post_steam_move(self, alert: Dict) -> bool:
        """Check if steam move alert should be posted"""
        if self.config.get('post_steam_moves', 'true') != 'true':
            return False

        min_consensus = float(self.config.get('min_steam_consensus', 50))
        return alert['consensus_percent'] >= min_consensus

    def _should_post_middle(self, alert: Dict) -> bool:
        """Check if middle alert should be posted"""
        if self.config.get('post_middles', 'true') != 'true':
            return False

        sport = alert['sport'].lower()
        if 'hockey' in sport or 'nhl' in sport:
            min_gap = float(self.config.get('min_middle_gap_nhl', 1.0))
        else:  # NBA
            min_gap = float(self.config.get('min_middle_gap_nba', 3.0))

        return alert['gap'] >= min_gap

    def _should_post_model_prediction(self, prediction: Dict) -> bool:
        """Check if model prediction should be posted"""
        if self.config.get('post_model_predictions', 'true') != 'true':
            return False

        # Check edge percentage
        min_edge = float(self.config.get('min_model_edge', 5.0))
        if prediction.get('edge_percent', 0) < min_edge:
            return False

        # Check confidence level
        min_confidence = self.config.get('min_model_confidence', 'HIGH')
        confidence_levels = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2, 'CRITICAL': 3}
        pred_conf_level = confidence_levels.get(prediction.get('confidence', 'LOW'), 0)
        min_conf_level = confidence_levels.get(min_confidence, 2)

        return pred_conf_level >= min_conf_level

    def _should_post_strategy_alert(self, alert: Dict) -> bool:
        """Check if strategy alert should be posted"""
        if self.config.get('post_strategy_alerts', 'true') != 'true':
            return False

        # Only post HIGH and CRITICAL confidence
        return alert.get('confidence', 'LOW') in ['HIGH', 'CRITICAL']

    async def process_arbitrage_alerts(self, alerts: List[Dict]):
        """Process and post arbitrage alerts"""
        for alert in alerts:
            alert_id = f"arb_{alert['game_id']}_{alert['market_type']}_{alert['book_a']}_{alert['book_b']}"

            # Skip if already posted
            if alert_id in self.posted_alerts:
                continue

            # Check if should post
            if not self._should_post_arbitrage(alert):
                continue

            # Check rate limit
            if not self._check_rate_limit():
                logger.warning("⚠️ Rate limit reached, skipping remaining alerts")
                return

            # Post to Twitter
            logger.info(f"📤 Posting arbitrage alert: {alert['home_team']} vs {alert['away_team']}")
            result = self.twitter_client.post_arbitrage_alert(alert)

            if result.success:
                self.tweets_posted_last_3_hours.append(datetime.now())
                self._record_tweet(
                    alert_type='arbitrage',
                    alert_id=alert_id,
                    game_id=alert['game_id'],
                    sport=alert['sport'],
                    home_team=alert['home_team'],
                    away_team=alert['away_team'],
                    tweet_text=f"Arbitrage: {alert['market_type']}",
                    result=result
                )
                logger.info(f"✅ Posted: {result.tweet_url}")
            else:
                logger.error(f"❌ Failed to post: {result.error}")

            # Wait 5 seconds between tweets
            await asyncio.sleep(5)

    async def process_steam_moves(self, alerts: List[Dict]):
        """Process and post steam move alerts"""
        for alert in alerts:
            alert_id = f"steam_{alert['game_id']}_{alert['market_type']}_{alert['movement_direction']}"

            if alert_id in self.posted_alerts:
                continue

            if not self._should_post_steam_move(alert):
                continue

            if not self._check_rate_limit():
                return

            logger.info(f"📤 Posting steam move: {alert['home_team']} vs {alert['away_team']}")
            result = self.twitter_client.post_steam_move_alert(alert)

            if result.success:
                self.tweets_posted_last_3_hours.append(datetime.now())
                self._record_tweet(
                    alert_type='steam_move',
                    alert_id=alert_id,
                    game_id=alert['game_id'],
                    sport=alert['sport'],
                    home_team=alert['home_team'],
                    away_team=alert['away_team'],
                    tweet_text=f"Steam Move: {alert['market_type']}",
                    result=result
                )
                logger.info(f"✅ Posted: {result.tweet_url}")
            else:
                logger.error(f"❌ Failed to post: {result.error}")

            await asyncio.sleep(5)

    async def process_middles(self, alerts: List[Dict]):
        """Process and post middle opportunity alerts"""
        for alert in alerts:
            alert_id = f"middle_{alert['game_id']}_{alert['market_type']}_{alert['gap']}"

            if alert_id in self.posted_alerts:
                continue

            if not self._should_post_middle(alert):
                continue

            if not self._check_rate_limit():
                return

            logger.info(f"📤 Posting middle opportunity: {alert['home_team']} vs {alert['away_team']}")
            result = self.twitter_client.post_middle_alert(alert)

            if result.success:
                self.tweets_posted_last_3_hours.append(datetime.now())
                self._record_tweet(
                    alert_type='middle',
                    alert_id=alert_id,
                    game_id=alert['game_id'],
                    sport=alert['sport'],
                    home_team=alert['home_team'],
                    away_team=alert['away_team'],
                    tweet_text=f"Middle: {alert['market_type']}",
                    result=result
                )
                logger.info(f"✅ Posted: {result.tweet_url}")
            else:
                logger.error(f"❌ Failed to post: {result.error}")

            await asyncio.sleep(5)

    async def scan_and_post(self):
        """Main scan loop - check for alerts and post to Twitter"""
        if not self.enabled:
            logger.warning("⚠️ Twitter alert service is disabled")
            return

        if self.config.get('enabled', 'true') != 'true':
            logger.info("Twitter automation is disabled in config")
            return

        logger.info("🔍 Scanning for alerts...")

        # Scan for alerts
        sports = ['basketball_nba', 'icehockey_nhl', 'americanfootball_nfl']
        alerts = await self.alert_monitor.scan_for_alerts(sports)

        # Process each alert type
        await self.process_arbitrage_alerts(alerts.get('arbitrage', []))
        await self.process_steam_moves(alerts.get('steam_moves', []))
        await self.process_middles(alerts.get('middles', []))

        logger.info(f"✅ Scan complete. Posted {len(self.tweets_posted_last_3_hours)} tweets in last 3 hours")

    async def start_monitoring(self):
        """Start continuous monitoring loop"""
        logger.info("🚀 Starting Twitter alert service...")

        scan_interval = int(self.config.get('scan_interval_seconds', 300))

        while True:
            try:
                await self.scan_and_post()
                await asyncio.sleep(scan_interval)
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    # Admin controls
    def enable(self):
        """Enable Twitter automation"""
        self._save_config('enabled', 'true')
        logger.info("✅ Twitter automation enabled")

    def disable(self):
        """Disable Twitter automation"""
        self._save_config('enabled', 'false')
        logger.info("⏸️ Twitter automation disabled")

    def set_threshold(self, key: str, value: str):
        """Set a configuration threshold"""
        valid_keys = [
            'min_arbitrage_profit',
            'min_steam_consensus',
            'min_middle_gap_nhl',
            'min_middle_gap_nba',
            'min_model_edge',
            'min_model_confidence',
            'max_tweets_per_hour',
            'scan_interval_seconds'
        ]

        if key in valid_keys:
            self._save_config(key, value)
            logger.info(f"✅ Set {key} = {value}")
        else:
            logger.warning(f"⚠️ Invalid config key: {key}")

    def get_stats(self) -> Dict:
        """Get statistics about posted tweets"""
        try:
            conn = get_optimized_connection(str(self.db_path))

            # Total tweets
            cursor = conn.execute("SELECT COUNT(*) FROM posted_tweets")
            total_tweets = cursor.fetchone()[0]

            # Tweets by type
            cursor = conn.execute("""
                SELECT alert_type, COUNT(*) as count
                FROM posted_tweets
                GROUP BY alert_type
            """)
            by_type = {row[0]: row[1] for row in cursor.fetchall()}

            # Tweets last 24 hours
            cutoff = datetime.now() - timedelta(hours=24)
            cursor = conn.execute("""
                SELECT COUNT(*) FROM posted_tweets
                WHERE posted_at >= ?
            """, (cutoff,))
            last_24h = cursor.fetchone()[0]

            # Success rate
            cursor = conn.execute("""
                SELECT
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                    COUNT(*) as total
                FROM posted_tweets
            """)
            successes, total = cursor.fetchone()
            success_rate = (successes / total * 100) if total > 0 else 0

            conn.close()

            return {
                'total_tweets': total_tweets,
                'by_type': by_type,
                'last_24h': last_24h,
                'success_rate': f"{success_rate:.1f}%",
                'enabled': self.config.get('enabled', 'true') == 'true',
                'current_config': self.config
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


# Standalone script for testing
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Load environment variables
    load_dotenv()

    odds_api_key = os.getenv('ODDS_API_KEY')
    if not odds_api_key:
        print("❌ ODDS_API_KEY not found in environment")
        exit(1)

    # Create service
    service = TwitterAlertService(odds_api_key)

    # Run monitoring loop
    asyncio.run(service.start_monitoring())
