"""
Twitter Integration for MAX-EV Sports
Automatically posts bet alerts to Twitter using Twitter API v2

Features:
- Post arbitrage opportunities
- Post steam moves
- Post middle opportunities
- Post high-confidence model predictions
- Post strategy alerts
- Rate limiting to avoid API limits
- Tweet formatting with emojis and hashtags
"""

import os
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import tweepy
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TweetResult:
    """Result of posting a tweet"""
    success: bool
    tweet_id: Optional[str] = None
    tweet_url: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = None


class TwitterClient:
    """Twitter API client for posting bet alerts"""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_token_secret: str,
        bearer_token: str
    ):
        """
        Initialize Twitter client with credentials

        Get credentials from: https://developer.twitter.com/en/portal/dashboard
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.bearer_token = bearer_token

        # Initialize Tweepy client (v2 API)
        try:
            self.client = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                wait_on_rate_limit=True
            )

            # Test authentication
            me = self.client.get_me()
            if me.data:
                self.username = me.data.username
                logger.info(f"✅ Twitter authenticated as @{self.username}")
            else:
                raise Exception("Failed to get Twitter user info")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Twitter client: {e}")
            self.client = None
            self.username = None

    def is_authenticated(self) -> bool:
        """Check if Twitter client is authenticated"""
        return self.client is not None and self.username is not None

    def post_tweet(self, text: str) -> TweetResult:
        """
        Post a tweet

        Args:
            text: Tweet text (max 280 characters)

        Returns:
            TweetResult with success status and tweet details
        """
        if not self.is_authenticated():
            return TweetResult(
                success=False,
                error="Twitter client not authenticated",
                timestamp=datetime.now()
            )

        # Validate tweet length
        if len(text) > 280:
            logger.warning(f"Tweet too long ({len(text)} chars), truncating...")
            text = text[:277] + "..."

        try:
            # Post tweet using v2 API
            response = self.client.create_tweet(text=text)

            tweet_id = response.data['id']
            tweet_url = f"https://twitter.com/{self.username}/status/{tweet_id}"

            logger.info(f"✅ Tweet posted: {tweet_url}")

            return TweetResult(
                success=True,
                tweet_id=tweet_id,
                tweet_url=tweet_url,
                timestamp=datetime.now()
            )

        except tweepy.errors.TweepyException as e:
            logger.error(f"❌ Failed to post tweet: {e}")
            return TweetResult(
                success=False,
                error=str(e),
                timestamp=datetime.now()
            )

    def post_arbitrage_alert(self, alert: Dict) -> TweetResult:
        """
        Post an arbitrage alert tweet

        Alert format:
        {
            'game_id': str,
            'sport': str,
            'home_team': str,
            'away_team': str,
            'market_type': str,
            'book_a': str,
            'book_b': str,
            'odds_a': float,
            'odds_b': float,
            'side_a': str,
            'side_b': str,
            'profit_percent': float,
            'guaranteed_profit': float
        }
        """
        sport_emoji = self._get_sport_emoji(alert['sport'])
        market_emoji = self._get_market_emoji(alert['market_type'])

        # Format team names (shorten if needed)
        matchup = f"{alert['away_team']} @ {alert['home_team']}"
        if len(matchup) > 60:
            matchup = f"{self._shorten_team(alert['away_team'])} @ {self._shorten_team(alert['home_team'])}"

        tweet = f"""🚨 ARBITRAGE ALERT {sport_emoji}

{matchup}
{market_emoji} {alert['market_type'].upper()}

💰 {alert['profit_percent']:.2f}% GUARANTEED PROFIT

Bet {alert['side_a']} at {alert['book_a']}: {self._format_odds(alert['odds_a'])}
Bet {alert['side_b']} at {alert['book_b']}: {self._format_odds(alert['odds_b'])}

#SportsBetting #Arbitrage #ValueBet"""

        return self.post_tweet(tweet)

    def post_steam_move_alert(self, alert: Dict) -> TweetResult:
        """
        Post a steam move alert tweet

        Alert format:
        {
            'game_id': str,
            'sport': str,
            'home_team': str,
            'away_team': str,
            'market_type': str,
            'movement': float,
            'movement_direction': str,
            'consensus_percent': float,
            'best_stale_book': str,
            'best_stale_odds': float
        }
        """
        sport_emoji = self._get_sport_emoji(alert['sport'])
        direction_emoji = "📈" if alert['movement_direction'] == 'up' else "📉"

        matchup = f"{alert['away_team']} @ {alert['home_team']}"
        if len(matchup) > 60:
            matchup = f"{self._shorten_team(alert['away_team'])} @ {self._shorten_team(alert['home_team'])}"

        tweet = f"""🔥 STEAM MOVE {sport_emoji}

{matchup}
{alert['market_type'].upper()}: {direction_emoji} {abs(alert['movement']):.1f} pts

{alert['consensus_percent']:.0f}% of books moved!

🎯 VALUE: {alert['best_stale_book']} still has stale line at {self._format_odds(alert['best_stale_odds'])}

#SteamMove #SharpMoney #SportsBetting"""

        return self.post_tweet(tweet)

    def post_middle_alert(self, alert: Dict) -> TweetResult:
        """
        Post a middle opportunity alert tweet

        Alert format:
        {
            'game_id': str,
            'sport': str,
            'home_team': str,
            'away_team': str,
            'market_type': str,
            'book_low': str,
            'book_high': str,
            'side_low': str,
            'side_high': str,
            'odds_low': float,
            'odds_high': float,
            'gap': float
        }
        """
        sport_emoji = self._get_sport_emoji(alert['sport'])

        matchup = f"{alert['away_team']} @ {alert['home_team']}"
        if len(matchup) > 60:
            matchup = f"{self._shorten_team(alert['away_team'])} @ {self._shorten_team(alert['home_team'])}"

        tweet = f"""⚡ MIDDLE OPPORTUNITY {sport_emoji}

{matchup}
{alert['market_type'].upper()}

{alert['gap']:.1f} pt GAP - Chance to WIN BOTH!

{alert['side_low']} at {alert['book_low']}: {self._format_odds(alert['odds_low'])}
{alert['side_high']} at {alert['book_high']}: {self._format_odds(alert['odds_high'])}

#MiddleBet #SportsBetting"""

        return self.post_tweet(tweet)

    def post_model_prediction(self, prediction: Dict) -> TweetResult:
        """
        Post a high-confidence model prediction tweet

        Prediction format:
        {
            'game_id': str,
            'sport': str,
            'home_team': str,
            'away_team': str,
            'bet_type': str,
            'recommendation': str,
            'edge_percent': float,
            'confidence': str,
            'model_name': str,
            'win_probability': float
        }
        """
        sport_emoji = self._get_sport_emoji(prediction['sport'])
        confidence_emoji = "🔥" if prediction['confidence'] == 'HIGH' else "⚡"

        matchup = f"{prediction['away_team']} @ {prediction['home_team']}"
        if len(matchup) > 60:
            matchup = f"{self._shorten_team(prediction['away_team'])} @ {self._shorten_team(prediction['home_team'])}"

        tweet = f"""{confidence_emoji} {prediction['confidence']} CONFIDENCE {sport_emoji}

{matchup}

🎯 {prediction['recommendation']}

Edge: +{prediction['edge_percent']:.1f}%
Win Rate: {prediction['win_probability']*100:.1f}%
Model: {prediction['model_name']}

#SportsBetting #MLPredictions #ValueBet"""

        return self.post_tweet(tweet)

    def post_strategy_alert(self, alert: Dict) -> TweetResult:
        """
        Post a strategy alert tweet (Quarter Reversal, Favorite Comeback, etc.)

        Alert format:
        {
            'strategy_name': str,
            'sport': str,
            'home_team': str,
            'away_team': str,
            'trigger': str,
            'recommendation': str,
            'edge_percentage': float,
            'confidence': str,
            'expected_roi': float
        }
        """
        sport_emoji = self._get_sport_emoji(alert['sport'])

        # Map strategy names to emojis
        strategy_emojis = {
            'arbitrage': '🚨',
            'steam': '🔥',
            'middle': '⚡',
            'reversal': '🔄',
            'comeback': '📈',
            'momentum': '💨',
            'fade': '🎯'
        }

        strategy_emoji = '💡'
        for key, emoji in strategy_emojis.items():
            if key in alert['strategy_name'].lower():
                strategy_emoji = emoji
                break

        matchup = f"{alert['away_team']} @ {alert['home_team']}"
        if len(matchup) > 60:
            matchup = f"{self._shorten_team(alert['away_team'])} @ {self._shorten_team(alert['home_team'])}"

        # Truncate trigger if too long
        trigger = alert['trigger']
        if len(trigger) > 80:
            trigger = trigger[:77] + "..."

        tweet = f"""{strategy_emoji} {alert['strategy_name']} {sport_emoji}

{matchup}

📊 {trigger}

🎯 {alert['recommendation']}

Edge: +{alert['edge_percentage']:.1f}%
ROI: +{alert['expected_roi']:.1f}%

#SportsBetting #BettingStrategy"""

        return self.post_tweet(tweet)

    def _get_sport_emoji(self, sport: str) -> str:
        """Get emoji for sport"""
        sport_lower = sport.lower()
        if 'nba' in sport_lower or 'basketball_nba' in sport_lower:
            return '🏀'
        elif 'ncaab' in sport_lower or 'basketball_ncaab' in sport_lower:
            return '🏀'
        elif 'nfl' in sport_lower or 'americanfootball_nfl' in sport_lower:
            return '🏈'
        elif 'ncaaf' in sport_lower or 'americanfootball_ncaaf' in sport_lower:
            return '🏈'
        elif 'nhl' in sport_lower or 'icehockey_nhl' in sport_lower:
            return '🏒'
        elif 'mlb' in sport_lower or 'baseball_mlb' in sport_lower:
            return '⚾'
        else:
            return '🎯'

    def _get_market_emoji(self, market_type: str) -> str:
        """Get emoji for market type"""
        if market_type == 'totals':
            return '📊'
        elif market_type == 'spreads':
            return '📈'
        elif market_type == 'h2h':
            return '🥊'
        else:
            return '🎲'

    def _format_odds(self, odds: float) -> str:
        """Format American odds with + or - sign"""
        if odds > 0:
            return f"+{int(odds)}"
        else:
            return str(int(odds))

    def _shorten_team(self, team_name: str) -> str:
        """Shorten team name to save characters"""
        # Common shortenings
        replacements = {
            'University': 'Univ',
            'College': 'Coll',
            'State': 'St',
            'Golden State Warriors': 'Warriors',
            'Los Angeles Lakers': 'Lakers',
            'Boston Celtics': 'Celtics',
            'New York Knicks': 'Knicks',
            'Brooklyn Nets': 'Nets',
            'Philadelphia 76ers': '76ers',
            'Miami Heat': 'Heat',
            'Milwaukee Bucks': 'Bucks'
        }

        for long_form, short_form in replacements.items():
            if long_form in team_name:
                team_name = team_name.replace(long_form, short_form)

        return team_name


def get_twitter_client() -> Optional[TwitterClient]:
    """
    Get Twitter client from environment variables

    Required environment variables:
    - TWITTER_API_KEY
    - TWITTER_API_SECRET
    - TWITTER_ACCESS_TOKEN
    - TWITTER_ACCESS_TOKEN_SECRET
    - TWITTER_BEARER_TOKEN
    """
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')

    if not all([api_key, api_secret, access_token, access_token_secret, bearer_token]):
        logger.warning("❌ Twitter credentials not found in environment variables")
        return None

    return TwitterClient(
        api_key=api_key,
        api_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
        bearer_token=bearer_token
    )
