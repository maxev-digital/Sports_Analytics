"""
Alert Monitoring System for Real-time Betting Opportunities
Monitors odds from multiple sportsbooks and detects:
- Arbitrage opportunities
- Steam moves (synchronized line movements)
- Significant line movements
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import httpx
import json

logger = logging.getLogger(__name__)

@dataclass
class AlertPerformance:
    """Track performance of alerts over time"""
    alert_type: str  # 'arbitrage', 'steam_move', 'line_movement'
    total_alerts: int = 0
    successful_alerts: int = 0
    failed_alerts: int = 0
    pending_alerts: int = 0
    win_rate: float = 0.0
    avg_profit: float = 0.0
    total_profit: float = 0.0
    last_updated: datetime = None

@dataclass
class ArbitrageAlert:
    """Arbitrage opportunity alert"""
    game_id: str
    sport: str
    home_team: str
    away_team: str
    market_type: str  # 'spreads', 'totals', 'h2h'
    book_a: str
    book_b: str
    odds_a: float
    odds_b: float
    profit_percent: float
    stake_a: float
    stake_b: float
    total_stake: float
    guaranteed_profit: float
    timestamp: datetime
    expires_in: int  # seconds until game starts

@dataclass
class SteamMoveAlert:
    """Steam move detected alert"""
    game_id: str
    sport: str
    home_team: str
    away_team: str
    market_type: str
    side: str  # 'home', 'away', 'over', 'under'
    original_line: float
    new_line: float
    movement: float
    books_moved: List[str]
    consensus_percent: float
    timestamp: datetime

@dataclass
class LineMovementAlert:
    """Significant line movement alert"""
    game_id: str
    sport: str
    home_team: str
    away_team: str
    market_type: str
    bookmaker: str
    original_line: float
    new_line: float
    movement: float
    movement_percent: float
    timestamp: datetime


class AlertMonitor:
    """Monitors odds and detects betting opportunities"""

    def __init__(self, odds_api_key: str):
        self.api_key = odds_api_key
        self.base_url = "https://api.the-odds-api.com/v4"

        # Cache for tracking line movements
        self.odds_history: Dict[str, Dict] = {}

        # Alert thresholds
        self.arbitrage_min_profit = 0.5  # 0.5% minimum profit
        self.steam_move_threshold = 0.7  # 70% of books moving same direction
        self.line_movement_threshold = 1.5  # 1.5 point movement

        # Active alerts
        self.active_alerts: List[Any] = []

        # Performance tracking - simulated data for demo purposes
        self.performance_stats = {
            'arbitrage': AlertPerformance(
                alert_type='arbitrage',
                total_alerts=847,
                successful_alerts=723,
                failed_alerts=89,
                pending_alerts=35,
                win_rate=85.4,
                avg_profit=2.3,
                total_profit=1662.90,
                last_updated=datetime.now()
            ),
            'steam_moves': AlertPerformance(
                alert_type='steam_moves',
                total_alerts=1243,
                successful_alerts=891,
                failed_alerts=267,
                pending_alerts=85,
                win_rate=71.7,
                avg_profit=1.8,
                total_profit=1603.80,
                last_updated=datetime.now()
            ),
            'line_movements': AlertPerformance(
                alert_type='line_movements',
                total_alerts=2156,
                successful_alerts=1534,
                failed_alerts=498,
                pending_alerts=124,
                win_rate=71.1,
                avg_profit=1.4,
                total_profit=2147.60,
                last_updated=datetime.now()
            )
        }

        # Historical alert log
        self.alert_history = []

    async def fetch_odds(self, sport: str, markets: List[str]) -> Optional[List[Dict]]:
        """Fetch current odds from The Odds API"""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/sports/{sport}/odds"
                params = {
                    'apiKey': self.api_key,
                    'regions': 'us',
                    'markets': ','.join(markets),
                    'oddsFormat': 'american',
                }

                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()

                return response.json()
        except Exception as e:
            logger.error(f"Error fetching odds for {sport}: {e}")
            return None

    def american_to_decimal(self, odds: float) -> float:
        """Convert American odds to decimal"""
        if odds > 0:
            return (odds / 100) + 1
        else:
            return (100 / abs(odds)) + 1

    def american_to_implied_prob(self, odds: float) -> float:
        """Convert American odds to implied probability"""
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)

    def detect_arbitrage(self, game_odds: Dict) -> List[ArbitrageAlert]:
        """Detect arbitrage opportunities in a single game"""
        alerts = []

        game_id = game_odds.get('id')
        sport = game_odds.get('sport_key')
        home_team = game_odds.get('home_team')
        away_team = game_odds.get('away_team')
        commence_time = game_odds.get('commence_time')

        bookmakers = game_odds.get('bookmakers', [])

        if len(bookmakers) < 2:
            return alerts

        # Check each market type
        for market_type in ['h2h', 'spreads', 'totals']:
            # Find best odds for each outcome
            best_odds_home = {'bookmaker': None, 'odds': -100000}
            best_odds_away = {'bookmaker': None, 'odds': -100000}

            for book in bookmakers:
                book_name = book.get('key')
                markets = book.get('markets', [])

                for market in markets:
                    if market.get('key') != market_type:
                        continue

                    outcomes = market.get('outcomes', [])

                    for outcome in outcomes:
                        name = outcome.get('name')
                        price = outcome.get('price')

                        if market_type == 'h2h':
                            if name == home_team and price > best_odds_home['odds']:
                                best_odds_home = {'bookmaker': book_name, 'odds': price}
                            elif name == away_team and price > best_odds_away['odds']:
                                best_odds_away = {'bookmaker': book_name, 'odds': price}
                        elif market_type == 'totals':
                            if name == 'Over' and price > best_odds_home['odds']:
                                best_odds_home = {'bookmaker': book_name, 'odds': price}
                            elif name == 'Under' and price > best_odds_away['odds']:
                                best_odds_away = {'bookmaker': book_name, 'odds': price}
                        elif market_type == 'spreads':
                            point = outcome.get('point', 0)
                            if point < 0 and price > best_odds_home['odds']:  # Favorite
                                best_odds_home = {'bookmaker': book_name, 'odds': price}
                            elif point > 0 and price > best_odds_away['odds']:  # Underdog
                                best_odds_away = {'bookmaker': book_name, 'odds': price}

            # Check for arbitrage
            if best_odds_home['bookmaker'] and best_odds_away['bookmaker']:
                prob_home = self.american_to_implied_prob(best_odds_home['odds'])
                prob_away = self.american_to_implied_prob(best_odds_away['odds'])

                total_implied_prob = prob_home + prob_away

                if total_implied_prob < 1:  # Arbitrage exists!
                    profit_percent = ((1 - total_implied_prob) * 100)

                    if profit_percent >= self.arbitrage_min_profit:
                        # Calculate optimal stake distribution
                        total_stake = 1000  # Example $1000
                        stake_home = (total_stake * prob_away) / total_implied_prob
                        stake_away = (total_stake * prob_home) / total_implied_prob

                        decimal_home = self.american_to_decimal(best_odds_home['odds'])
                        decimal_away = self.american_to_decimal(best_odds_away['odds'])

                        payout_home = stake_home * decimal_home
                        payout_away = stake_away * decimal_away

                        guaranteed_profit = min(payout_home, payout_away) - total_stake

                        # Calculate time until game starts
                        game_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                        expires_in = int((game_time - datetime.now(game_time.tzinfo)).total_seconds())

                        alert = ArbitrageAlert(
                            game_id=game_id,
                            sport=sport,
                            home_team=home_team,
                            away_team=away_team,
                            market_type=market_type,
                            book_a=best_odds_home['bookmaker'],
                            book_b=best_odds_away['bookmaker'],
                            odds_a=best_odds_home['odds'],
                            odds_b=best_odds_away['odds'],
                            profit_percent=profit_percent,
                            stake_a=stake_home,
                            stake_b=stake_away,
                            total_stake=total_stake,
                            guaranteed_profit=guaranteed_profit,
                            timestamp=datetime.now(),
                            expires_in=expires_in
                        )

                        alerts.append(alert)

        return alerts

    def detect_steam_move(self, game_id: str, current_odds: Dict) -> List[SteamMoveAlert]:
        """Detect steam moves (synchronized line movements across books)"""
        alerts = []

        # Get historical odds for comparison
        if game_id not in self.odds_history:
            self.odds_history[game_id] = current_odds
            return alerts

        previous_odds = self.odds_history[game_id]
        bookmakers = current_odds.get('bookmakers', [])

        if len(bookmakers) < 3:  # Need at least 3 books for steam detection
            return alerts

        # Track line movements by market
        for market_type in ['spreads', 'totals']:
            movements = {'up': [], 'down': []}

            for book in bookmakers:
                book_key = book.get('key')

                # Find matching previous book
                prev_book = next(
                    (b for b in previous_odds.get('bookmakers', []) if b.get('key') == book_key),
                    None
                )

                if not prev_book:
                    continue

                # Compare markets
                current_market = next(
                    (m for m in book.get('markets', []) if m.get('key') == market_type),
                    None
                )
                prev_market = next(
                    (m for m in prev_book.get('markets', []) if m.get('key') == market_type),
                    None
                )

                if not current_market or not prev_market:
                    continue

                # Get primary line (first outcome)
                current_outcome = current_market.get('outcomes', [])[0] if current_market.get('outcomes') else None
                prev_outcome = prev_market.get('outcomes', [])[0] if prev_market.get('outcomes') else None

                if not current_outcome or not prev_outcome:
                    continue

                current_price = current_outcome.get('price')
                prev_price = prev_outcome.get('price')

                if market_type == 'spreads':
                    current_line = current_outcome.get('point', 0)
                    prev_line = prev_outcome.get('point', 0)
                    movement = current_line - prev_line
                elif market_type == 'totals':
                    current_line = current_outcome.get('point', 0)
                    prev_line = prev_outcome.get('point', 0)
                    movement = current_line - prev_line

                if abs(movement) >= 0.5:  # At least 0.5 point movement
                    if movement > 0:
                        movements['up'].append({'book': book_key, 'movement': movement, 'new_line': current_line, 'old_line': prev_line})
                    else:
                        movements['down'].append({'book': book_key, 'movement': movement, 'new_line': current_line, 'old_line': prev_line})

            # Check for steam move (70%+ books moving same direction)
            total_books_moved = len(movements['up']) + len(movements['down'])

            if total_books_moved >= 3:
                up_percent = len(movements['up']) / total_books_moved
                down_percent = len(movements['down']) / total_books_moved

                if up_percent >= self.steam_move_threshold or down_percent >= self.steam_move_threshold:
                    direction = 'up' if up_percent > down_percent else 'down'
                    moved_books = movements[direction]

                    avg_movement = sum(m['movement'] for m in moved_books) / len(moved_books)
                    avg_old_line = sum(m['old_line'] for m in moved_books) / len(moved_books)
                    avg_new_line = sum(m['new_line'] for m in moved_books) / len(moved_books)

                    alert = SteamMoveAlert(
                        game_id=game_id,
                        sport=current_odds.get('sport_key'),
                        home_team=current_odds.get('home_team'),
                        away_team=current_odds.get('away_team'),
                        market_type=market_type,
                        side='over' if direction == 'up' and market_type == 'totals' else 'under' if market_type == 'totals' else 'favorite',
                        original_line=avg_old_line,
                        new_line=avg_new_line,
                        movement=avg_movement,
                        books_moved=[m['book'] for m in moved_books],
                        consensus_percent=max(up_percent, down_percent) * 100,
                        timestamp=datetime.now()
                    )

                    alerts.append(alert)

        # Update history
        self.odds_history[game_id] = current_odds

        return alerts

    def detect_line_movement(self, game_id: str, current_odds: Dict) -> List[LineMovementAlert]:
        """Detect significant line movements at individual books"""
        alerts = []

        if game_id not in self.odds_history:
            self.odds_history[game_id] = current_odds
            return alerts

        previous_odds = self.odds_history[game_id]

        for book in current_odds.get('bookmakers', []):
            book_key = book.get('key')

            prev_book = next(
                (b for b in previous_odds.get('bookmakers', []) if b.get('key') == book_key),
                None
            )

            if not prev_book:
                continue

            for market_type in ['spreads', 'totals']:
                current_market = next(
                    (m for m in book.get('markets', []) if m.get('key') == market_type),
                    None
                )
                prev_market = next(
                    (m for m in prev_book.get('markets', []) if m.get('key') == market_type),
                    None
                )

                if not current_market or not prev_market:
                    continue

                current_outcome = current_market.get('outcomes', [])[0] if current_market.get('outcomes') else None
                prev_outcome = prev_market.get('outcomes', [])[0] if prev_market.get('outcomes') else None

                if not current_outcome or not prev_outcome:
                    continue

                current_line = current_outcome.get('point', 0)
                prev_line = prev_outcome.get('point', 0)

                movement = abs(current_line - prev_line)

                if movement >= self.line_movement_threshold:
                    movement_percent = (movement / abs(prev_line) * 100) if prev_line != 0 else 0

                    alert = LineMovementAlert(
                        game_id=game_id,
                        sport=current_odds.get('sport_key'),
                        home_team=current_odds.get('home_team'),
                        away_team=current_odds.get('away_team'),
                        market_type=market_type,
                        bookmaker=book_key,
                        original_line=prev_line,
                        new_line=current_line,
                        movement=current_line - prev_line,
                        movement_percent=movement_percent,
                        timestamp=datetime.now()
                    )

                    alerts.append(alert)

        return alerts

    async def scan_for_alerts(self, sports: List[str]) -> Dict[str, List[Any]]:
        """Scan all sports for alerts"""
        all_alerts = {
            'arbitrage': [],
            'steam_moves': [],
            'line_movements': []
        }

        for sport in sports:
            odds_data = await self.fetch_odds(sport, ['h2h', 'spreads', 'totals'])

            if not odds_data:
                continue

            for game in odds_data:
                game_id = game.get('id')

                # Detect arbitrage
                arb_alerts = self.detect_arbitrage(game)
                all_alerts['arbitrage'].extend(arb_alerts)

                # Detect steam moves
                steam_alerts = self.detect_steam_move(game_id, game)
                all_alerts['steam_moves'].extend(steam_alerts)

                # Detect line movements
                line_alerts = self.detect_line_movement(game_id, game)
                all_alerts['line_movements'].extend(line_alerts)

        self.active_alerts = all_alerts
        return all_alerts

    async def start_monitoring(self, sports: List[str], interval_seconds: int = 60):
        """Start continuous monitoring loop"""
        logger.info(f"Starting alert monitoring for sports: {sports}")

        while True:
            try:
                alerts = await self.scan_for_alerts(sports)

                # Log summary
                logger.info(
                    f"Scan complete: "
                    f"{len(alerts['arbitrage'])} arbitrage, "
                    f"{len(alerts['steam_moves'])} steam moves, "
                    f"{len(alerts['line_movements'])} line movements"
                )

                # Wait before next scan
                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)
