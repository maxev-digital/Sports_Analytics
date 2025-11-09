"""
Twitter/X Injury Monitor
Monitors tweets from top sports reporters for real-time injury updates
Fastest source: Shams, Woj (NBA), Schefter, Rapoport (NFL), Bowden (MLB), Johnston (NHL)
"""

import asyncio
import logging
import re
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import tweepy
from collections import defaultdict

logger = logging.getLogger(__name__)

class InjuryKeyword(Enum):
    """Injury-related keywords to detect in tweets"""
    OUT = "out"
    RULED_OUT = "ruled out"
    DOUBTFUL = "doubtful"
    QUESTIONABLE = "questionable"
    INJURED = "injured"
    INJURY = "injury"
    DTD = "day-to-day"
    WEEK_TO_WEEK = "week-to-week"
    SIDELINED = "sidelined"
    UNAVAILABLE = "unavailable"
    WILL_MISS = "will miss"
    EXPECTED_TO_MISS = "expected to miss"
    PLACED_ON_IL = "placed on IL"
    PLACED_ON_IR = "placed on IR"
    GAME_TIME_DECISION = "game-time decision"

@dataclass
class ReporterSource:
    """Twitter reporter information"""
    username: str
    display_name: str
    sport: str
    tier: str  # tier1 (Woj/Shams level), tier2 (beat writers), tier3 (team accounts)
    reliability_score: float  # 0.0-1.0

@dataclass
class InjuryTweet:
    """Parsed injury tweet"""
    tweet_id: str
    reporter: ReporterSource
    text: str
    player_name: Optional[str]
    team_name: Optional[str]
    injury_status: str  # OUT, DOUBTFUL, QUESTIONABLE, etc.
    injury_details: str
    games_missed: Optional[int]
    timestamp: datetime
    confidence: float  # How confident we are this is an injury tweet

class TwitterInjuryMonitor:
    """Monitors Twitter/X for real-time injury reports"""

    def __init__(self, bearer_token: Optional[str] = None):
        self.bearer_token = bearer_token

        # Initialize Tweepy Client with AUTOMATIC RATE LIMIT HANDLING
        # wait_on_rate_limit=True will automatically wait when hitting rate limits (no more 429 errors!)
        self.client = tweepy.Client(
            bearer_token=bearer_token,
            wait_on_rate_limit=True,  # Automatically wait when rate limited
            return_type=dict  # Return data as dict for easy parsing
        ) if bearer_token else None

        # Top reporters by sport (tier 1)
        self.reporters = self._initialize_reporters()

        # Track processed tweets to avoid duplicates
        self.processed_tweets: Set[str] = set()

        # Injury alerts detected
        self.injury_alerts: List[InjuryTweet] = []

        # Team name mappings for parsing
        self.team_mappings = self._initialize_team_mappings()

    def _initialize_reporters(self) -> List[ReporterSource]:
        """Initialize list of top sports reporters to monitor"""
        from twitter_reporter_database import get_all_reporters

        reporters = []
        all_reporters = get_all_reporters()

        # RATE LIMIT OPTIMIZATION: Only monitor in-season sports
        # NBA (Nov-Jun), NFL (Sep-Feb), NHL (Oct-Jun) are priority
        # Skip MLB (offseason Oct-Mar) - less critical for injury cascade
        IN_SEASON_SPORTS = ['NBA', 'NFL', 'NHL']

        for sport, reporter_list in all_reporters.items():
            # Skip out-of-season sports to save API requests
            if sport not in IN_SEASON_SPORTS:
                logger.info(f"Skipping {sport} - out of season or lower priority")
                continue

            for r in reporter_list:
                # ONLY monitor Tier 1 reporters (reliability >= 0.95)
                # These are the fastest breakers (Woj, Shams, Schefter, Rapoport, etc.)
                if r['reliability'] < 0.95:
                    continue

                # Determine tier from reliability
                if r['reliability'] >= 0.95:
                    tier = "tier1"
                elif r['reliability'] >= 0.85:
                    tier = "tier2"
                else:
                    tier = "tier3"

                reporters.append(ReporterSource(
                    username=r['username'],
                    display_name=r['name'],
                    sport=sport,
                    tier=tier,
                    reliability_score=r['reliability']
                ))

        return reporters

    def _initialize_team_mappings(self) -> Dict[str, Dict]:
        """Initialize team name variations for parsing"""
        from twitter_reporter_database import get_team_mappings
        return get_team_mappings()

    async def fetch_recent_tweets(self, username: str, max_results: int = 10) -> List[Dict]:
        """
        Fetch recent tweets from a reporter using Tweepy (with automatic rate limit handling)

        Tweepy will automatically wait when rate limited (no more 429 errors!)
        Query: from:{username} (injury OR out OR ruled out OR doubtful)
        """
        if not self.client:
            logger.warning("No Twitter client configured - using mock data")
            return []

        try:
            # Build query to filter for injury-related tweets
            query = f'from:{username} (injury OR "ruled out" OR out OR doubtful OR questionable OR "will miss")'

            # Use Tweepy's search_recent_tweets with automatic rate limit handling
            response = self.client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=['created_at', 'author_id', 'text']
            )

            # Return tweets as list of dicts
            if response and 'data' in response:
                return response['data']
            return []

        except tweepy.TweepyException as e:
            logger.error(f"Tweepy error fetching tweets from @{username}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching tweets from @{username}: {e}")
            return []

    def parse_injury_tweet(self, tweet: Dict, reporter: ReporterSource) -> Optional[InjuryTweet]:
        """Parse a tweet to extract injury information"""
        text = tweet.get('text', '')
        tweet_id = tweet.get('id', '')

        # Skip if already processed
        if tweet_id in self.processed_tweets:
            return None

        # Check for injury keywords
        injury_keywords_found = []
        for keyword in InjuryKeyword:
            if keyword.value.lower() in text.lower():
                injury_keywords_found.append(keyword.value)

        if not injury_keywords_found:
            return None

        # Extract player name (capital letters pattern: "FirstName LastName")
        player_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
        player_matches = re.findall(player_pattern, text)
        player_name = player_matches[0] if player_matches else None

        # Extract team name
        team_name = None
        for team, variations in self.team_mappings.get(reporter.sport, {}).items():
            for variation in variations:
                if variation in text:
                    team_name = team
                    break
            if team_name:
                break

        # Determine injury status (most severe keyword wins)
        status_priority = {
            'ruled out': 5,
            'out': 4,
            'doubtful': 3,
            'questionable': 2,
            'day-to-day': 1,
        }

        injury_status = None
        max_priority = 0
        for keyword in injury_keywords_found:
            priority = status_priority.get(keyword.lower(), 0)
            if priority > max_priority:
                max_priority = priority
                injury_status = keyword.upper()

        # Extract games missed (e.g., "next 2 games", "3-4 weeks")
        games_missed = None
        games_pattern = r'(?:next|miss)\s+(\d+)\s+(?:games?|weeks?)'
        games_match = re.search(games_pattern, text.lower())
        if games_match:
            games_missed = int(games_match.group(1))

        # Calculate confidence based on reporter tier and keyword clarity
        confidence = reporter.reliability_score
        if injury_status in ['RULED OUT', 'OUT']:
            confidence *= 1.0  # Most clear
        elif injury_status in ['DOUBTFUL']:
            confidence *= 0.85
        elif injury_status in ['QUESTIONABLE']:
            confidence *= 0.7

        # Create parsed tweet
        injury_tweet = InjuryTweet(
            tweet_id=tweet_id,
            reporter=reporter,
            text=text,
            player_name=player_name,
            team_name=team_name,
            injury_status=injury_status or 'INJURY',
            injury_details=text,
            games_missed=games_missed,
            timestamp=datetime.fromisoformat(tweet.get('created_at', '').replace('Z', '+00:00')),
            confidence=confidence
        )

        # Mark as processed
        self.processed_tweets.add(tweet_id)

        return injury_tweet

    async def scan_reporter(self, reporter: ReporterSource) -> List[InjuryTweet]:
        """Scan a single reporter's recent tweets for injuries"""
        logger.info(f"📡 Scanning @{reporter.username} ({reporter.sport}) for injury tweets...")

        tweets = await self.fetch_recent_tweets(reporter.username)

        injury_tweets = []
        for tweet in tweets:
            parsed = self.parse_injury_tweet(tweet, reporter)
            if parsed:
                logger.info(f"   🚨 INJURY DETECTED: {parsed.player_name or 'Unknown'} - {parsed.injury_status}")
                logger.info(f"      Team: {parsed.team_name or 'Unknown'}")
                logger.info(f"      Source: @{reporter.username} (confidence: {parsed.confidence:.0%})")
                injury_tweets.append(parsed)

        return injury_tweets

    async def scan_all_reporters(self, sport: Optional[str] = None) -> List[InjuryTweet]:
        """Scan all reporters (or filter by sport) for injury tweets"""
        reporters_to_scan = self.reporters

        if sport:
            reporters_to_scan = [r for r in self.reporters if r.sport == sport]

        logger.info(f"🔍 Starting Twitter injury scan for {len(reporters_to_scan)} reporters...")

        all_injury_tweets = []

        # Scan reporters with rate limiting (Twitter Free tier: 450 requests per 15 min)
        # That's 30 requests/minute or 1 request every 2 seconds
        for reporter in reporters_to_scan:
            injury_tweets = await self.scan_reporter(reporter)
            all_injury_tweets.extend(injury_tweets)
            await asyncio.sleep(2)  # Rate limit: 2 seconds between reporters to avoid 429

        logger.info(f"✅ Twitter scan complete: {len(all_injury_tweets)} injury alerts found")

        return all_injury_tweets

    async def start_monitoring(self, interval_seconds: int = 60, sport: Optional[str] = None):
        """Start continuous Twitter monitoring loop"""
        logger.info(f"🐦 Starting Twitter injury monitor...")
        logger.info(f"📊 Monitoring {len(self.reporters)} reporters every {interval_seconds} seconds")

        # Add initial delay on startup to prevent immediate rate limit hit
        # This allows the server to start accepting requests first
        logger.info(f"⏸️  Initial 30-second delay before first scan (allows server startup)")
        await asyncio.sleep(30)

        while True:
            try:
                new_alerts = await self.scan_all_reporters(sport=sport)

                # Store new alerts
                self.injury_alerts.extend(new_alerts)

                # Process alerts (send to main injury monitor)
                for alert in new_alerts:
                    await self._process_injury_alert(alert, injury_monitor=getattr(self, 'injury_monitor', None))

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Error in Twitter monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)

    async def _process_injury_alert(self, alert: InjuryTweet, injury_monitor=None):
        """Process an injury alert and send to main injury monitor"""
        logger.info(f"📤 Processing Twitter injury alert: {alert.player_name} ({alert.team_name}) - {alert.injury_status}")

        if not injury_monitor:
            logger.warning("No injury monitor connected - storing alert only")
            return

        # Convert InjuryTweet -> InjuryReport format
        from injury_monitor import InjuryReport, InjuryStatus, PlayerImpact

        # Map Twitter status to ESPN status enum
        status_map = {
            'RULED OUT': InjuryStatus.OUT,
            'OUT': InjuryStatus.OUT,
            'DOUBTFUL': InjuryStatus.DOUBTFUL,
            'QUESTIONABLE': InjuryStatus.QUESTIONABLE,
            'DAY-TO-DAY': InjuryStatus.DAY_TO_DAY,
        }

        status = status_map.get(alert.injury_status, InjuryStatus.OUT)

        # Estimate player impact (will be refined by injury_monitor when it gets PPG)
        # For now, assume high impact since Twitter reporters usually tweet about stars
        impact = PlayerImpact.STAR

        # Create InjuryReport
        injury_report = InjuryReport(
            player_id=f"twitter_{alert.tweet_id}",  # Temporary ID until we get ESPN data
            player_name=alert.player_name or "Unknown Player",
            team=alert.team_name or "Unknown Team",
            position="N/A",  # Will be filled in by injury_monitor
            status=status,
            description=alert.injury_details,
            ppg=0.0,  # Will be fetched by injury_monitor
            impact_rating=impact,
            expected_total_drop=0.0,  # Will be calculated
            timestamp=alert.timestamp,
            game_id=None,
            game_time=None
        )

        # Send to injury monitor for processing
        logger.info(f"   🔄 Forwarding to injury monitor for full analysis...")
        await injury_monitor.process_injury(injury_report, game_tracker=injury_monitor.game_tracker)

        # **NEW**: INSTANT PROPS ANALYSIS (60-second window!)
        if hasattr(self, 'props_analyzer') and self.props_analyzer:
            logger.info(f"   ⚡ TRIGGERING FAST PROPS ANALYSIS (targeting <10s)...")
            try:
                # Determine sport from team
                sport_map = {'NBA': 'NBA', 'NFL': 'NFL', 'NHL': 'NHL'}
                sport = 'NBA'  # Default, would improve with better team→sport mapping

                # Get player PPG (estimate 20 for stars since reporters tweet about big names)
                player_ppg = 20.0 if impact == PlayerImpact.STAR else 15.0

                # Run ML-powered props analysis
                opportunities = await self.props_analyzer.analyze_injury_props(
                    player_name=alert.player_name or "Unknown",
                    team=alert.team_name or "Unknown",
                    sport=sport,
                    injury_status=alert.injury_status,
                    player_ppg=player_ppg,
                    tweet_timestamp=alert.timestamp
                )

                if opportunities:
                    logger.info(f"   🎯 FOUND {len(opportunities)} PROP OPPORTUNITIES!")
                    for i, opp in enumerate(opportunities[:3], 1):
                        logger.info(f"      {i}. {opp.prop_type.upper()} {opp.prop_side} {opp.prop_line}")
                        logger.info(f"         {opp.best_book} @ {opp.best_odds} | EV: {opp.expected_value:.1%} | ⏱️  {opp.time_since_tweet:.1f}s")

                    # Store opportunities globally for API endpoint
                    if hasattr(self, 'prop_opportunities'):
                        self.prop_opportunities.extend(opportunities)
                else:
                    logger.info(f"   ℹ️  No high-EV prop opportunities found")

            except Exception as e:
                logger.error(f"Error in props analysis: {e}")

    def set_injury_monitor(self, injury_monitor):
        """Set the injury monitor instance for processing alerts"""
        self.injury_monitor = injury_monitor
        logger.info(f"✅ Connected to injury monitor")

    def set_props_analyzer(self, props_analyzer):
        """Set the props analyzer for instant props analysis"""
        self.props_analyzer = props_analyzer
        self.prop_opportunities = []  # Store detected opportunities
        logger.info(f"✅ Connected to props analyzer (60-second window mode)")

    def get_recent_alerts(self, hours: int = 24) -> List[InjuryTweet]:
        """Get injury alerts from the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.injury_alerts
            if alert.timestamp >= cutoff
        ]

# Global instance
twitter_injury_monitor = None
