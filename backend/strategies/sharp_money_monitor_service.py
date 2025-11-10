"""
Sharp Money Monitor Service
Async monitoring service that wraps SharpMoneyTracker and integrates with alert system
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional
import httpx

from strategies.sharp_money_tracker import SharpMoneyTracker, SharpMoneyAlert, BookmakerOdds
from storage.alert_storage import alert_storage
from alert_monitor import serialize_datetime_dict

logger = logging.getLogger(__name__)


class SharpMoneyMonitorService:
    """
    Async service that monitors for sharp money movements
    Integrates SharpMoneyTracker with alert storage and notification system
    """

    def __init__(self, odds_api_key: str):
        self.api_key = odds_api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        self.tracker = SharpMoneyTracker(
            min_sharp_books=2,
            min_movement_magnitude=1.5,
            steam_move_threshold=5
        )

        # Track games we've seen (for opening lines)
        self.seen_games: Dict[str, Dict] = {}

    async def fetch_odds(self, sport: str) -> Optional[List[Dict]]:
        """Fetch current odds from The Odds API"""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/sports/{sport}/odds"
                params = {
                    'apiKey': self.api_key,
                    'regions': 'us',
                    'markets': 'h2h,spreads,totals',
                    'oddsFormat': 'american',
                }

                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()

                return response.json()
        except Exception as e:
            logger.error(f"Error fetching odds for {sport}: {e}")
            return None

    def _convert_to_bookmaker_odds(self, bookmakers: List[Dict]) -> List[BookmakerOdds]:
        """Convert API odds format to BookmakerOdds objects"""
        bookmaker_odds_list = []

        for book in bookmakers:
            book_key = book.get('key')
            markets = book.get('markets', [])

            # Extract spread, total, and h2h data
            spread_home = None
            spread_away = None
            spread_home_price = None
            spread_away_price = None
            total = None
            over_price = None
            under_price = None
            ml_home = None
            ml_away = None

            for market in markets:
                market_key = market.get('key')
                outcomes = market.get('outcomes', [])

                if market_key == 'spreads' and len(outcomes) >= 2:
                    for outcome in outcomes:
                        point = outcome.get('point')
                        price = outcome.get('price')
                        name = outcome.get('name')

                        if point is not None and price is not None:
                            if point < 0:  # Home spread
                                spread_home = point
                                spread_home_price = price
                            else:  # Away spread
                                spread_away = point
                                spread_away_price = price

                elif market_key == 'totals' and len(outcomes) >= 2:
                    for outcome in outcomes:
                        name = outcome.get('name')
                        point = outcome.get('point')
                        price = outcome.get('price')

                        if point is not None:
                            total = point
                            if name == 'Over':
                                over_price = price
                            else:
                                under_price = price

                elif market_key == 'h2h' and len(outcomes) >= 2:
                    # Determine home/away from first outcome
                    for outcome in outcomes:
                        name = outcome.get('name')
                        price = outcome.get('price')
                        # Would need home_team/away_team from parent to match correctly
                        # For now, assume first is home, second is away
                        if ml_home is None:
                            ml_home = price
                        else:
                            ml_away = price

            bookmaker_odds_list.append(BookmakerOdds(
                bookmaker=book_key,
                spread_home=spread_home,
                spread_away=spread_away,
                spread_home_price=spread_home_price,
                spread_away_price=spread_away_price,
                total=total,
                over_price=over_price,
                under_price=under_price,
                moneyline_home=ml_home,
                moneyline_away=ml_away,
                last_update=datetime.now()
            ))

        return bookmaker_odds_list

    def _store_sharp_money_alert(self, alert: SharpMoneyAlert, sport: str) -> Optional[str]:
        """Store sharp money alert in database"""
        try:
            # Serialize alert to dict
            alert_dict = {
                'game_id': alert.game_id,
                'sport': alert.sport,
                'home_team': alert.home_team,
                'away_team': alert.away_team,
                'alert_type': alert.alert_type,
                'market_type': alert.market_type,
                'recommendation': alert.recommendation,
                'opening_line': alert.opening_line,
                'current_line': alert.current_line,
                'movement': alert.movement,
                'sharp_books_involved': alert.sharp_books_involved,
                'confidence': alert.confidence,
                'confidence_level': alert.confidence_level,
                'reasoning': alert.reasoning,
                'key_factors': alert.key_factors,
                'timestamp': alert.timestamp.isoformat() if hasattr(alert.timestamp, 'isoformat') else str(alert.timestamp)
            }

            # Serialize datetime objects
            alert_dict = serialize_datetime_dict(alert_dict)

            # Store in alert_storage
            tracked_alert = alert_storage.create_alert(
                alert_type='sharp_money',
                game_id=alert.game_id,
                sport=sport,
                home_team=alert.home_team,
                away_team=alert.away_team,
                commence_time=alert.timestamp.isoformat() if hasattr(alert.timestamp, 'isoformat') else str(alert.timestamp),
                market_type=alert.market_type,
                recommended_side=alert.recommendation,
                recommended_odds=None,  # Could extract from bookmaker data
                recommended_bookmaker='Sharp Books',
                edge_percent=alert.confidence * 100,
                profit_potential=None,
                expires_at=None,
                strategy_details=alert_dict
            )

            return tracked_alert.id
        except Exception as e:
            logger.error(f"Error storing sharp money alert: {e}")
            return None

    async def scan_sport_for_sharp_money(self, sport: str) -> List[SharpMoneyAlert]:
        """Scan a single sport for sharp money movements"""
        alerts = []

        try:
            # Fetch current odds
            odds_data = await self.fetch_odds(sport)
            if not odds_data:
                return alerts

            for game in odds_data:
                game_id = game.get('id')
                home_team = game.get('home_team')
                away_team = game.get('away_team')
                bookmakers = game.get('bookmakers', [])

                if not bookmakers:
                    continue

                # Convert to BookmakerOdds format
                bookmaker_odds = self._convert_to_bookmaker_odds(bookmakers)

                # Check if this is first time seeing this game (for opening lines)
                opening_odds = None
                if game_id not in self.seen_games:
                    self.seen_games[game_id] = {
                        'bookmaker_odds': bookmaker_odds,
                        'first_seen': datetime.now()
                    }
                    opening_odds = bookmaker_odds
                else:
                    # Use first seen as opening odds
                    opening_odds = self.seen_games[game_id]['bookmaker_odds']

                # Analyze game for sharp money
                game_alerts = self.tracker.analyze_game(
                    game_id=game_id,
                    sport=sport,
                    home_team=home_team,
                    away_team=away_team,
                    bookmaker_odds=bookmaker_odds,
                    opening_odds=opening_odds
                )

                # Store each alert
                for alert in game_alerts:
                    alert_id = self._store_sharp_money_alert(alert, sport)
                    if alert_id:
                        alerts.append(alert)

        except Exception as e:
            logger.error(f"Error scanning {sport} for sharp money: {e}")

        return alerts

    async def monitor_loop(self, sports: List[str], interval_seconds: int = 120):
        """
        Continuous monitoring loop for sharp money

        Args:
            sports: List of sport keys to monitor
            interval_seconds: Seconds between scans (default 120 = 2 minutes)
        """
        logger.info(f"Starting sharp money monitor for sports: {sports}")

        while True:
            try:
                all_alerts = []

                for sport in sports:
                    alerts = await self.scan_sport_for_sharp_money(sport)
                    all_alerts.extend(alerts)

                if all_alerts:
                    logger.info(
                        f"Sharp money scan complete: {len(all_alerts)} alerts detected"
                    )

                    # Log alert details
                    for alert in all_alerts:
                        logger.info(
                            f"  Sharp Money: {alert.market_type} - {alert.recommendation} "
                            f"({alert.confidence_level} confidence) - "
                            f"{', '.join(alert.sharp_books_involved)}"
                        )
                else:
                    logger.debug("Sharp money scan complete: No alerts")

                # Wait before next scan
                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Error in sharp money monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)


# Global instance
sharp_money_service = None


def get_sharp_money_service(api_key: str) -> SharpMoneyMonitorService:
    """Get or create sharp money service instance"""
    global sharp_money_service
    if sharp_money_service is None:
        sharp_money_service = SharpMoneyMonitorService(api_key)
    return sharp_money_service
