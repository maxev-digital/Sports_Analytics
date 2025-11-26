"""
Bet Position Monitor - Monitors user's active bets for hedge opportunities

Scans all active user bets and checks if the opposite side has moved to favorable
odds, creating hedge alerts when profit can be locked in.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import httpx

from storage.bet_storage import bet_storage
from storage.alert_storage import alert_storage
from models.user_bet import UserBet

logger = logging.getLogger(__name__)


class BetPositionMonitor:
    """Monitors active user bets for hedge opportunities"""

    def __init__(self, odds_api_key: str):
        self.odds_api_key = odds_api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        self.recent_hedge_alerts: Dict[str, datetime] = {}  # Prevent spam
        self.alert_cooldown_minutes = 5  # Don't alert same bet more than once per 5 min

    async def fetch_live_odds(self, sport: str, markets: List[str] = None) -> List[Dict]:
        """Fetch live odds for a sport"""
        if markets is None:
            markets = ['h2h', 'spreads', 'totals']

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/sports/{sport}/odds",
                    params={
                        'apiKey': self.odds_api_key,
                        'regions': 'us',
                        'markets': ','.join(markets),
                        'oddsFormat': 'american'
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching live odds for {sport}: {e}")
            return []

    def calculate_american_to_decimal(self, american_odds: int) -> float:
        """Convert American odds to decimal"""
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1

    def calculate_hedge_profit(
        self,
        original_stake: float,
        original_odds: int,
        hedge_odds: int
    ) -> tuple[float, float]:
        """
        Calculate optimal hedge bet size and guaranteed profit

        Returns:
            (hedge_stake, guaranteed_profit)
        """
        # Convert to decimal odds
        orig_decimal = self.calculate_american_to_decimal(original_odds)
        hedge_decimal = self.calculate_american_to_decimal(hedge_odds)

        # Potential payout from original bet
        original_payout = original_stake * orig_decimal

        # Optimal hedge stake to guarantee profit
        hedge_stake = original_payout / hedge_decimal

        # Guaranteed profit (same either outcome)
        # If original bet wins: profit = original_payout - original_stake - hedge_stake
        # If hedge bet wins: profit = hedge_payout - original_stake - hedge_stake
        guaranteed_profit = original_payout - original_stake - hedge_stake

        return hedge_stake, guaranteed_profit

    def is_hedge_opportunity(
        self,
        bet: UserBet,
        current_odds: int
    ) -> tuple[bool, Optional[Dict]]:
        """
        Determine if current odds present a hedge opportunity

        For underdogs: Check if favorite has moved to + money
        For favorites: Check if underdog has moved to better + money
        For totals: Check if opposite side has moved favorably

        Returns:
            (is_opportunity, hedge_details)
        """
        if not bet.stake or bet.odds == current_odds:
            return False, None

        # Calculate potential hedge
        hedge_stake, guaranteed_profit = self.calculate_hedge_profit(
            bet.stake,
            bet.odds,
            current_odds
        )

        # Require minimum $5 guaranteed profit
        min_profit = 5.0
        if guaranteed_profit < min_profit:
            return False, None

        # Require hedge odds to be favorable (moved from original)
        # For underdogs (+odds): opposite side should have moved to + money or less negative
        # For favorites (-odds): opposite side should have moved to better + money

        if bet.odds > 0:  # Original bet was underdog
            # Hedge is the favorite - check if it moved to +money or significantly less negative
            if current_odds > 0:  # Now +money (great hedge opp)
                is_opportunity = True
            elif current_odds > -200 and abs(current_odds) < abs(bet.odds):  # Moved favorably
                is_opportunity = True
            else:
                is_opportunity = False
        else:  # Original bet was favorite
            # Hedge is the underdog - check if it moved to better +money
            if current_odds > abs(bet.odds) * 0.7:  # Significant movement
                is_opportunity = True
            else:
                is_opportunity = False

        if not is_opportunity:
            return False, None

        hedge_details = {
            'original_bet_id': bet.id,
            'original_stake': bet.stake,
            'original_odds': bet.odds,
            'original_side': bet.bet_side,
            'hedge_odds': current_odds,
            'hedge_stake': round(hedge_stake, 2),
            'guaranteed_profit': round(guaranteed_profit, 2),
            'roi_percent': round((guaranteed_profit / (bet.stake + hedge_stake)) * 100, 2)
        }

        return True, hedge_details

    def get_opposite_side(self, bet: UserBet, game_odds: Dict) -> Optional[Dict]:
        """
        Get the opposite side of the bet from current game odds

        Args:
            bet: User's active bet
            game_odds: Current game odds from API

        Returns:
            Dict with opposite side odds or None if not found
        """
        if bet.bet_type == 'moneyline':
            # Find opposite team
            for bookmaker in game_odds.get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    if market['key'] != 'h2h':
                        continue

                    for outcome in market['outcomes']:
                        # Get opposite team
                        if bet.bet_side == bet.home_team and outcome['name'] == bet.away_team:
                            return {
                                'side': bet.away_team,
                                'odds': outcome['price'],
                                'bookmaker': bookmaker['key']
                            }
                        elif bet.bet_side == bet.away_team and outcome['name'] == bet.home_team:
                            return {
                                'side': bet.home_team,
                                'odds': outcome['price'],
                                'bookmaker': bookmaker['key']
                            }

        elif bet.bet_type == 'total':
            # Find opposite total (OVER vs UNDER)
            for bookmaker in game_odds.get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    if market['key'] != 'totals':
                        continue

                    for outcome in market['outcomes']:
                        # Get opposite side
                        if 'OVER' in bet.bet_side.upper() and outcome['name'] == 'Under':
                            return {
                                'side': f"Under {outcome['point']}",
                                'odds': outcome['price'],
                                'bookmaker': bookmaker['key']
                            }
                        elif 'UNDER' in bet.bet_side.upper() and outcome['name'] == 'Over':
                            return {
                                'side': f"Over {outcome['point']}",
                                'odds': outcome['price'],
                                'bookmaker': bookmaker['key']
                            }

        elif bet.bet_type == 'spread':
            # Find opposite spread
            for bookmaker in game_odds.get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    if market['key'] != 'spreads':
                        continue

                    for outcome in market['outcomes']:
                        # Get opposite team
                        if bet.bet_side.startswith(bet.home_team) and outcome['name'] == bet.away_team:
                            return {
                                'side': f"{bet.away_team} {outcome['point']:+.1f}",
                                'odds': outcome['price'],
                                'bookmaker': bookmaker['key']
                            }
                        elif bet.bet_side.startswith(bet.away_team) and outcome['name'] == bet.home_team:
                            return {
                                'side': f"{bet.home_team} {outcome['point']:+.1f}",
                                'odds': outcome['price'],
                                'bookmaker': bookmaker['key']
                            }

        return None

    async def check_bet_for_hedge(self, bet: UserBet, live_odds: List[Dict]) -> Optional[Dict]:
        """
        Check a single bet for hedge opportunities

        Returns:
            Hedge alert dict if opportunity found, None otherwise
        """
        # Find this game in live odds
        game_odds = None
        for game in live_odds:
            if (game.get('home_team') == bet.home_team and
                game.get('away_team') == bet.away_team):
                game_odds = game
                break

        if not game_odds:
            return None

        # Get opposite side odds
        opposite = self.get_opposite_side(bet, game_odds)
        if not opposite:
            return None

        # Check if it's a hedge opportunity
        is_opp, hedge_details = self.is_hedge_opportunity(bet, opposite['odds'])
        if not is_opp:
            return None

        # Check cooldown (don't spam same bet)
        alert_key = f"{bet.id}_{opposite['odds']}"
        if alert_key in self.recent_hedge_alerts:
            last_alert = self.recent_hedge_alerts[alert_key]
            if datetime.now() - last_alert < timedelta(minutes=self.alert_cooldown_minutes):
                return None

        # Create hedge alert
        hedge_alert = {
            'alert_type': 'hedge_opportunity',
            'user_id': bet.user_id,
            'priority': 'high' if hedge_details['guaranteed_profit'] > 20 else 'medium',
            'game_id': bet.game_id,
            'sport': bet.sport,
            'home_team': bet.home_team,
            'away_team': bet.away_team,
            'original_bet': {
                'bet_id': bet.id,
                'side': bet.bet_side,
                'stake': bet.stake,
                'odds': bet.odds,
                'bookmaker': bet.bookmaker
            },
            'hedge_bet': {
                'side': opposite['side'],
                'stake': hedge_details['hedge_stake'],
                'odds': opposite['odds'],
                'bookmaker': opposite['bookmaker']
            },
            'profit': {
                'guaranteed': hedge_details['guaranteed_profit'],
                'roi_percent': hedge_details['roi_percent']
            },
            'timestamp': datetime.now().isoformat(),
            'message': (
                f"🔒 HEDGE ALERT: {bet.home_team} vs {bet.away_team}\n"
                f"Original: {bet.bet_side} ${bet.stake} @ {int(bet.odds):+d}\n"
                f"Hedge: {opposite['side']} ${hedge_details['hedge_stake']:.2f} @ {int(opposite['odds']):+d}\n"
                f"Guaranteed Profit: ${hedge_details['guaranteed_profit']:.2f} ({hedge_details['roi_percent']}% ROI)"
            )
        }

        # Mark as alerted
        self.recent_hedge_alerts[alert_key] = datetime.now()

        logger.info(f"🔒 HEDGE OPPORTUNITY: {hedge_alert['message']}")

        return hedge_alert

    async def scan_for_hedges(self, sports: List[str]) -> List[Dict]:
        """
        Scan all active user bets for hedge opportunities

        Args:
            sports: List of sport keys to check

        Returns:
            List of hedge alerts
        """
        hedge_alerts = []

        # Get all active bets (across all users)
        all_bets = bet_storage._read_bets()
        active_bets = [UserBet(**b) for b in all_bets if b['status'] == 'active' and b.get('stake')]

        if not active_bets:
            return []

        logger.debug(f"Checking {len(active_bets)} active bets for hedge opportunities")

        # Group bets by sport for efficient API calls
        bets_by_sport: Dict[str, List[UserBet]] = {}
        for bet in active_bets:
            if bet.sport not in bets_by_sport:
                bets_by_sport[bet.sport] = []
            bets_by_sport[bet.sport].append(bet)

        # Check each sport
        for sport, sport_bets in bets_by_sport.items():
            if sport not in sports:
                continue

            # Fetch live odds for this sport
            live_odds = await self.fetch_live_odds(sport)
            if not live_odds:
                continue

            # Check each bet
            for bet in sport_bets:
                hedge_alert = await self.check_bet_for_hedge(bet, live_odds)
                if hedge_alert:
                    hedge_alerts.append(hedge_alert)

        return hedge_alerts

    async def start_monitoring(self, sports: List[str], interval_seconds: int = 60):
        """
        Start continuous monitoring loop for hedge opportunities

        Args:
            sports: List of sport keys to monitor
            interval_seconds: Time between scans (default 60 seconds)
        """
        logger.info(f"Starting bet position monitor for sports: {sports} (interval: {interval_seconds}s)")

        while True:
            try:
                hedge_alerts = await self.scan_for_hedges(sports)

                # Store hedge alerts
                for alert in hedge_alerts:
                    try:
                        # Store in alert_storage
                        alert_storage.create_alert(
                            user_id=alert['user_id'],
                            alert_type='hedge_opportunity',
                            game_id=alert['game_id'],
                            sport=alert['sport'],
                            home_team=alert['home_team'],
                            away_team=alert['away_team'],
                            recommendation=alert['message'],
                            confidence='HIGH',
                            bet_type='hedge',
                            priority=alert['priority'],
                            metadata=alert
                        )
                    except Exception as e:
                        logger.error(f"Error storing hedge alert: {e}")

                logger.info(f"Hedge scan complete: {len(hedge_alerts)} opportunities detected")

                # Wait before next scan
                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Error in bet position monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)


# Global instance (initialized in main.py)
bet_position_monitor: Optional[BetPositionMonitor] = None


def init_bet_position_monitor(odds_api_key: str):
    """Initialize global bet position monitor"""
    global bet_position_monitor
    bet_position_monitor = BetPositionMonitor(odds_api_key)
    return bet_position_monitor
