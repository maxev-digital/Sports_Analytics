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
    side_a: str = ''  # 'Over', 'Under', team name, etc.
    side_b: str = ''  # 'Over', 'Under', team name, etc.
    point_a: Optional[float] = None  # Point value for spreads/totals (e.g., 5.5, -3.5)
    point_b: Optional[float] = None  # Point value for spreads/totals (e.g., 5.5, 3.5)
    profit_percent: float = 0.0
    stake_a: float = 0.0
    stake_b: float = 0.0
    total_stake: float = 0.0
    guaranteed_profit: float = 0.0
    timestamp: datetime = None
    expires_in: int = 0  # seconds until game starts

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
    movement_direction: str  # 'up' or 'down'
    books_moved: List[str]
    consensus_percent: float
    books_not_moved: List[str]  # Books that still have old line
    best_stale_book: str  # Best book with stale line
    best_stale_line: float  # The old line value
    best_stale_odds: float  # Best odds at stale line
    timestamp: datetime

@dataclass
class MiddleAlert:
    """Middle opportunity alert - potential to win both sides"""
    game_id: str
    sport: str
    home_team: str
    away_team: str
    market_type: str  # 'spreads' or 'totals'
    book_low: str  # Book with lower line
    book_high: str  # Book with higher line
    low_line: float  # Lower line value
    high_line: float  # Higher line value
    gap: float  # Middle gap size
    side_low: str  # Bet side for low line (e.g., "Over 5.5", "Lakers +2.5")
    side_high: str  # Bet side for high line (e.g., "Under 6.5", "Warriors -3.5")
    odds_low: float  # Odds at low line
    odds_high: float  # Odds at high line
    timestamp: datetime
    expires_in: int = 0  # seconds until game starts


class AlertMonitor:
    """Monitors odds and detects betting opportunities"""

    def __init__(self, odds_api_key: str):
        self.api_key = odds_api_key
        self.base_url = "https://api.the-odds-api.com/v4"

        # Cache for tracking line movements
        self.odds_history: Dict[str, Dict] = {}

        # Alert thresholds
        self.arbitrage_min_profit = 0.5  # 0.5% minimum profit
        self.steam_move_min_books = 2  # Minimum 2 books must move
        self.steam_move_threshold = 0.5  # 50% of books moving same direction (lowered from 70%)
        self.steam_move_min_movement = 0.5  # Minimum 0.5 point movement
        self.line_movement_threshold = 1.0  # 1.0 point movement (lowered from 1.5)

        # Active alerts
        self.active_alerts: Dict[str, List[Any]] = {
            'arbitrage': [],
            'steam_moves': [],
            'middles': []  # Replaced line_movements with middles
        }

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
            'middles': AlertPerformance(
                alert_type='middles',
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
            best_odds_home = {'bookmaker': None, 'odds': -100000, 'side': None, 'point': None}
            best_odds_away = {'bookmaker': None, 'odds': -100000, 'side': None, 'point': None}

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
                        point = outcome.get('point')

                        if market_type == 'h2h':
                            if name == home_team and price > best_odds_home['odds']:
                                best_odds_home = {'bookmaker': book_name, 'odds': price, 'side': name, 'point': None}
                            elif name == away_team and price > best_odds_away['odds']:
                                best_odds_away = {'bookmaker': book_name, 'odds': price, 'side': name, 'point': None}
                        elif market_type == 'totals':
                            if name == 'Over' and price > best_odds_home['odds']:
                                best_odds_home = {'bookmaker': book_name, 'odds': price, 'side': 'Over', 'point': point}
                            elif name == 'Under' and price > best_odds_away['odds']:
                                best_odds_away = {'bookmaker': book_name, 'odds': price, 'side': 'Under', 'point': point}
                        elif market_type == 'spreads':
                            if point is not None:
                                if point < 0 and price > best_odds_home['odds']:  # Favorite
                                    best_odds_home = {'bookmaker': book_name, 'odds': price, 'side': name, 'point': point}
                                elif point > 0 and price > best_odds_away['odds']:  # Underdog
                                    best_odds_away = {'bookmaker': book_name, 'odds': price, 'side': name, 'point': point}

            # Check for arbitrage
            if best_odds_home['bookmaker'] and best_odds_away['bookmaker']:
                # Validate that points match for true arbitrage (no middle risk)
                if market_type == 'totals':
                    # For totals, Over and Under must have the same point value
                    if best_odds_home['point'] != best_odds_away['point']:
                        logger.debug(f"Skipping totals arb - mismatched points: Over {best_odds_home['point']} vs Under {best_odds_away['point']}")
                        continue
                elif market_type == 'spreads':
                    # For spreads, points must be opposite (e.g., +3.5 and -3.5)
                    if best_odds_home['point'] is None or best_odds_away['point'] is None:
                        continue
                    if abs(best_odds_home['point'] + best_odds_away['point']) > 0.01:  # Allow tiny floating point error
                        logger.debug(f"Skipping spread arb - mismatched points: {best_odds_home['point']} vs {best_odds_away['point']}")
                        continue

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
                            side_a=best_odds_home['side'],
                            side_b=best_odds_away['side'],
                            point_a=best_odds_home['point'],
                            point_b=best_odds_away['point'],
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
            movements = {'up': [], 'down': [], 'no_move': []}

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

                if abs(movement) >= self.steam_move_min_movement:  # At least 0.5 point movement
                    if movement > 0:
                        movements['up'].append({'book': book_key, 'movement': movement, 'new_line': current_line, 'old_line': prev_line, 'new_price': current_price})
                    else:
                        movements['down'].append({'book': book_key, 'movement': movement, 'new_line': current_line, 'old_line': prev_line, 'new_price': current_price})
                else:
                    # Book hasn't moved - this is the VALUE!
                    movements['no_move'].append({'book': book_key, 'line': current_line, 'price': current_price, 'prev_line': prev_line})

            # Check for steam move (50%+ books moving same direction, min 2 books)
            total_books_moved = len(movements['up']) + len(movements['down'])

            if total_books_moved >= self.steam_move_min_books:
                up_percent = len(movements['up']) / total_books_moved if total_books_moved > 0 else 0
                down_percent = len(movements['down']) / total_books_moved if total_books_moved > 0 else 0

                if up_percent >= self.steam_move_threshold or down_percent >= self.steam_move_threshold:
                    direction = 'up' if up_percent > down_percent else 'down'
                    moved_books = movements[direction]

                    avg_movement = sum(m['movement'] for m in moved_books) / len(moved_books)
                    avg_old_line = sum(m['old_line'] for m in moved_books) / len(moved_books)
                    avg_new_line = sum(m['new_line'] for m in moved_books) / len(moved_books)

                    # Find best stale book (books that haven't moved yet)
                    stale_books = movements['no_move']
                    best_stale_book = None
                    best_stale_line = avg_old_line
                    best_stale_odds = None

                    if stale_books:
                        # Find book with best odds at stale line
                        best_stale = max(stale_books, key=lambda x: x['price'])
                        best_stale_book = best_stale['book']
                        best_stale_line = best_stale['line']
                        best_stale_odds = best_stale['price']
                    else:
                        # No stale books - all have moved
                        best_stale_book = "All books moved"
                        best_stale_odds = 0

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
                        movement_direction=direction,
                        books_moved=[m['book'] for m in moved_books],
                        consensus_percent=max(up_percent, down_percent) * 100,
                        books_not_moved=[b['book'] for b in stale_books],
                        best_stale_book=best_stale_book,
                        best_stale_line=best_stale_line,
                        best_stale_odds=best_stale_odds,
                        timestamp=datetime.now()
                    )

                    alerts.append(alert)

        # Update history
        self.odds_history[game_id] = current_odds

        return alerts

    def detect_middle_opportunities(self, game_odds: Dict) -> List[MiddleAlert]:
        """Detect middle opportunities - gaps between lines at different books"""
        alerts = []

        game_id = game_odds.get('id')
        sport_key = game_odds.get('sport_key')
        home_team = game_odds.get('home_team')
        away_team = game_odds.get('away_team')
        commence_time = game_odds.get('commence_time')
        bookmakers = game_odds.get('bookmakers', [])

        if len(bookmakers) < 2:
            return alerts

        # Determine minimum gap based on sport
        is_nhl = 'hockey' in sport_key.lower()
        is_nba = 'basketball_nba' in sport_key.lower()

        # Skip if not NHL or NBA
        if not (is_nhl or is_nba):
            return alerts

        # Set minimum gaps
        min_gap_totals = 1.0 if is_nhl else 3.0  # NHL: 1+ goal, NBA: 3+ points
        min_gap_spreads = 1.0 if is_nhl else 2.0  # NHL: 1+ goal, NBA: 2+ points

        # Check each market type
        for market_type in ['spreads', 'totals']:
            # Collect all lines from all books
            book_lines = []

            for book in bookmakers:
                book_name = book.get('key')
                markets = book.get('markets', [])

                for market in markets:
                    if market.get('key') != market_type:
                        continue

                    outcomes = market.get('outcomes', [])

                    for outcome in outcomes:
                        point = outcome.get('point')
                        odds = outcome.get('price')
                        name = outcome.get('name')

                        if point is not None and odds is not None:
                            book_lines.append({
                                'book': book_name,
                                'point': point,
                                'odds': odds,
                                'side': name
                            })

            # Find gaps between lines
            if len(book_lines) < 2:
                continue

            min_gap = min_gap_totals if market_type == 'totals' else min_gap_spreads

            if market_type == 'totals':
                # For totals, a middle exists when you bet OPPOSITE sides at different totals
                # Example: Over 5.5 vs Under 6.5 - if game lands on exactly 6, BOTH bets win!
                # You need: Over at lower total, Under at higher total

                # Separate Over and Under lines
                over_lines = [line for line in book_lines if line['side'] == 'Over']
                under_lines = [line for line in book_lines if line['side'] == 'Under']

                # Compare each Over line with each Under line
                for over_line in over_lines:
                    for under_line in under_lines:
                        # For a valid middle: Under total must be higher than Over total
                        # Example: Over 5.5 and Under 6.5 creates a 1.0 point middle at 6.0
                        if under_line['point'] > over_line['point']:
                            gap = under_line['point'] - over_line['point']

                            if gap >= min_gap:
                                game_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                                expires_in = int((game_time - datetime.now(game_time.tzinfo)).total_seconds())

                                side_low = f"Over {over_line['point']}"
                                side_high = f"Under {under_line['point']}"

                                alert = MiddleAlert(
                                    game_id=game_id,
                                    sport=sport_key,
                                    home_team=home_team,
                                    away_team=away_team,
                                    market_type=market_type,
                                    book_low=over_line['book'],
                                    book_high=under_line['book'],
                                    low_line=over_line['point'],
                                    high_line=under_line['point'],
                                    gap=gap,
                                    side_low=side_low,
                                    side_high=side_high,
                                    odds_low=over_line['odds'],
                                    odds_high=under_line['odds'],
                                    timestamp=datetime.now(),
                                    expires_in=expires_in
                                )
                                alerts.append(alert)

            else:  # spreads
                # For spreads, we need to normalize all lines to ONE team to avoid counting inverse lines as middles
                # Example: Panthers -1.5 and Maple Leafs +1.5 are the SAME line (inverse), not a middle!
                # True middle: Panthers -1.5 at Book A and Panthers -2.5 at Book B = 1.0 gap

                # Key insight: In spread betting, if Team A is -1.5, then Team B is automatically +1.5
                # These are inverse lines representing the SAME bet from opposite perspectives
                # When normalizing to home team:
                #   - Home -1.5 stays as -1.5
                #   - Away +1.5 also means Home -1.5 (flip the sign)
                # So both should normalize to the same value!

                # Normalize all spread lines to the home team
                normalized_lines = []
                for line in book_lines:
                    team = line['side']
                    point = line['point']

                    # If this line is for the home team, keep as-is
                    if team == home_team:
                        normalized_lines.append({
                            'book': line['book'],
                            'point': point,  # Home team spread stays as-is
                            'odds': line['odds'],
                            'side': team,
                            'original_side': team,
                            'original_point': point
                        })
                    # If this line is for the away team, convert to home team equivalent
                    else:
                        # Away team spread needs to be flipped to get home team perspective
                        # If away is +1.5, home is -1.5 (flip sign)
                        # If away is -1.5, home is +1.5 (flip sign)
                        normalized_lines.append({
                            'book': line['book'],
                            'point': -point,  # Flip the sign to convert to home team perspective
                            'odds': line['odds'],
                            'side': home_team,  # Now comparing as if all bets are on home team
                            'original_side': team,  # Track original for display
                            'original_point': point  # Track original point for display
                        })

                # Now all lines are normalized to home team, find gaps
                if len(normalized_lines) < 2:
                    continue

                # Group lines by their normalized point value to identify true middles
                # Inverse lines will have the same normalized point and should NOT create a middle
                from collections import defaultdict
                point_groups = defaultdict(list)
                for line in normalized_lines:
                    # Round to 1 decimal to handle floating point issues
                    point_key = round(line['point'], 1)
                    point_groups[point_key].append(line)

                # Find middles between DIFFERENT normalized points
                unique_points = sorted(point_groups.keys())

                for i in range(len(unique_points)):
                    for j in range(i + 1, len(unique_points)):
                        low_point = unique_points[i]
                        high_point = unique_points[j]

                        gap = abs(high_point - low_point)

                        if gap >= min_gap:
                            # Get one representative from each group
                            low_lines = point_groups[low_point]
                            high_lines = point_groups[high_point]

                            # Create alert for each combination of books
                            for low in low_lines:
                                for high in high_lines:
                                    # Skip if same book (can't bet both sides at same book)
                                    if low['book'] == high['book']:
                                        continue

                                    # Calculate time until game starts
                                    game_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                                    expires_in = int((game_time - datetime.now(game_time.tzinfo)).total_seconds())

                                    # Use original sides and points for display (before normalization)
                                    side_low = f"{low['original_side']} {low['original_point']:+.1f}"
                                    side_high = f"{high['original_side']} {high['original_point']:+.1f}"

                                    alert = MiddleAlert(
                                        game_id=game_id,
                                        sport=sport_key,
                                        home_team=home_team,
                                        away_team=away_team,
                                        market_type=market_type,
                                        book_low=low['book'],
                                        book_high=high['book'],
                                        low_line=low_point,  # Use normalized points
                                        high_line=high_point,  # Use normalized points
                                        gap=gap,
                                        side_low=side_low,
                                        side_high=side_high,
                                        odds_low=low['odds'],
                                        odds_high=high['odds'],
                                        timestamp=datetime.now(),
                                        expires_in=expires_in
                                    )

                                    alerts.append(alert)

        return alerts

    async def scan_for_alerts(self, sports: List[str]) -> Dict[str, List[Any]]:
        """Scan all sports for alerts"""
        all_alerts = {
            'arbitrage': [],
            'steam_moves': [],
            'middles': []  # Replaced line_movements with middles
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

                # Detect middle opportunities
                middle_alerts = self.detect_middle_opportunities(game)
                all_alerts['middles'].extend(middle_alerts)

        # Add last_updated timestamp
        all_alerts['last_updated'] = datetime.now().isoformat()

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
                    f"{len(alerts['middles'])} middles"
                )

                # Wait before next scan
                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)
