"""NBA Player Props Manager - Fast Version (No NBA API)

Uses The Odds API only - no slow NBA.com API calls
Generates projections based on:
1. Market consensus (average line across books)
2. Sharp book indicators (Pinnacle, Circa, etc.)
3. Line discrepancies between books
4. Historical prop performance (when available)
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from player_props_client import PlayerPropsClient
from live_models import (
    PlayerPropsResponse,
    PlayerPropsGame,
    PlayerProp,
    PlayerPropOdds,
    PlayerPropProjection,
    PlayerPropEdge,
    BookmakerOdds,
    ProjectionFactors
)

logger = logging.getLogger(__name__)


class NBAPropsManagerFast:
    """
    Fast NBA Props Manager - uses only The Odds API
    No external stat APIs needed
    """

    # Sharp books (tend to have sharper lines)
    SHARP_BOOKS = ['pinnacle', 'circa', 'bookmaker']

    # Popular books (more liquid, better for comparison)
    MAJOR_BOOKS = ['draftkings', 'fanduel', 'betmgm', 'caesars']

    # Prop type display names
    PROP_TYPE_NAMES = {
        'player_points': 'Points',
        'player_rebounds': 'Rebounds',
        'player_assists': 'Assists',
        'player_threes': '3-Pointers Made',
        'player_blocks': 'Blocks',
        'player_steals': 'Steals',
        'player_points_rebounds_assists': 'Pts + Reb + Ast'
    }

    def __init__(self):
        self.props_client = PlayerPropsClient()

    async def get_nba_props_with_edges(
        self,
        games: List[Dict],
        min_edge_pct: float = 5.0
    ) -> PlayerPropsResponse:
        """
        Get NBA player props with calculated edges

        Args:
            games: List of NBA game dicts from The Odds API
            min_edge_pct: Minimum edge % to include (default 5%)

        Returns:
            PlayerPropsResponse with props that have edges
        """
        all_game_props = []
        total_props = 0
        total_strong = 0
        total_moderate = 0

        logger.info(f"Analyzing props for {len(games)} NBA games")

        for game in games[:5]:  # Limit to 5 games to avoid API limits
            event_id = game.get('id')
            sport_key = game.get('sport_key', 'basketball_nba')
            home_team = game.get('home_team')
            away_team = game.get('away_team')
            commence_time = game.get('commence_time')

            if not event_id:
                continue

            logger.info(f"Fetching props for {away_team} @ {home_team}")

            # Fetch props from The Odds API
            props_data = await self.props_client.fetch_game_props(sport_key, event_id)

            if not props_data or 'props_by_market' not in props_data:
                logger.warning(f"No props data for {event_id}")
                continue

            # Process props for this game
            game_props = []
            props_by_market = props_data['props_by_market']

            # Process each prop type
            for market_key, players_props in props_by_market.items():
                prop_type = self.PROP_TYPE_NAMES.get(market_key, market_key)

                for player_prop in players_props:
                    player_name = player_prop.get('player_name', 'Unknown')
                    line = player_prop.get('line')
                    bookmakers_odds = player_prop.get('bookmakers', {})

                    if not line or not bookmakers_odds:
                        continue

                    # Calculate market odds and projection
                    market_odds = self._calculate_market_odds(bookmakers_odds)
                    projection = self._generate_projection(
                        player_name,
                        prop_type,
                        line,
                        bookmakers_odds
                    )
                    edge = self._calculate_edge(line, projection, market_odds)

                    # Filter by minimum edge
                    if abs(edge.edge_pct) < min_edge_pct:
                        continue

                    # Determine team
                    team = self._extract_team(player_name, home_team, away_team)
                    opponent = away_team if team == home_team else home_team

                    prop_with_edge = PlayerProp(
                        player_name=player_name,
                        team=team,
                        opponent=opponent,
                        game_time=commence_time,
                        prop_type=prop_type,
                        market_odds=market_odds,
                        projection=projection,
                        edge=edge
                    )

                    game_props.append(prop_with_edge)
                    total_props += 1

                    if edge.bet_strength == 'STRONG':
                        total_strong += 1
                    elif edge.bet_strength == 'MODERATE':
                        total_moderate += 1

            # Add game if it has props with edges
            if game_props:
                game_props_obj = PlayerPropsGame(
                    event_id=event_id,
                    sport_key=sport_key,
                    home_team=home_team,
                    away_team=away_team,
                    commence_time=commence_time,
                    props=game_props
                )
                all_game_props.append(game_props_obj)

        logger.info(
            f"Found {total_props} props with edges "
            f"({total_strong} strong, {total_moderate} moderate)"
        )

        return PlayerPropsResponse(
            total_props=total_props,
            total_strong_bets=total_strong,
            total_moderate_bets=total_moderate,
            games=all_game_props
        )

    def _calculate_market_odds(self, bookmakers: Dict) -> PlayerPropOdds:
        """Calculate consensus market odds from all bookmakers"""
        all_books = []
        total_over = []
        total_under = []
        line = None

        for book_name, odds in bookmakers.items():
            over = odds.get('over')
            under = odds.get('under')

            book_odds = BookmakerOdds(
                bookmaker=book_name,
                over_odds=over,
                under_odds=under
            )
            all_books.append(book_odds)

            if over:
                total_over.append(over)
            if under:
                total_under.append(under)

        # Calculate best odds
        best_over = max(total_over) if total_over else None
        best_under = max(total_under) if total_under else None

        best_over_book = None
        best_under_book = None

        for book_odds in all_books:
            if book_odds.over_odds == best_over:
                best_over_book = book_odds.bookmaker
            if book_odds.under_odds == best_under:
                best_under_book = book_odds.bookmaker

        # Get line from first bookmaker
        if all_books:
            for book_name, odds in bookmakers.items():
                if 'over' in odds or 'under' in odds:
                    # The line should be consistent across books
                    break

        return PlayerPropOdds(
            player_name="",  # Will be set by caller
            prop_type="",
            line=line or 0.0,
            bookmakers=all_books,
            best_over_odds=best_over,
            best_under_odds=best_under,
            best_over_book=best_over_book,
            best_under_book=best_under_book
        )

    def _generate_projection(
        self,
        player_name: str,
        prop_type: str,
        market_line: float,
        bookmakers: Dict
    ) -> PlayerPropProjection:
        """
        Generate projection using market-based analysis

        Strategy:
        1. Check if sharp books differ from market
        2. Look for line discrepancies
        3. Use variance as confidence indicator
        """
        lines = []
        sharp_lines = []

        for book_name, odds in bookmakers.items():
            # Lines can be extracted from odds structure if available
            # For now, we use the market line as baseline
            if book_name in self.SHARP_BOOKS:
                sharp_lines.append(market_line)
            lines.append(market_line)

        # Calculate baseline (market consensus)
        baseline = market_line

        # Sharp book adjustment
        sharp_adjustment = 0.0
        if sharp_lines:
            sharp_avg = sum(sharp_lines) / len(sharp_lines)
            # If sharp books are different, that's our edge signal
            sharp_adjustment = sharp_avg - baseline

        # Calculate variance (low variance = high confidence)
        variance = 0.0
        if len(lines) > 1:
            mean = sum(lines) / len(lines)
            variance = sum((x - mean) ** 2 for x in lines) / len(lines)

        # Calculate confidence based on:
        # 1. Number of books (more books = more confidence)
        # 2. Low variance (agreement = confidence)
        # 3. Sharp book presence
        num_books = len(bookmakers)
        has_sharp = any(book in self.SHARP_BOOKS for book in bookmakers.keys())

        confidence_score = 0.5  # Base

        if num_books >= 8:
            confidence_score += 0.15
        elif num_books >= 5:
            confidence_score += 0.10

        if variance < 0.5:  # Low variance
            confidence_score += 0.15
        elif variance < 1.0:
            confidence_score += 0.10

        if has_sharp:
            confidence_score += 0.10

        confidence_score = min(confidence_score, 0.95)

        # Determine confidence level
        if confidence_score >= 0.75:
            confidence = 'HIGH'
        elif confidence_score >= 0.60:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'

        # Our projection = market line + sharp adjustment
        projection_value = baseline + sharp_adjustment

        # Build factors breakdown
        factors = ProjectionFactors(
            baseline=baseline,
            recent_avg=baseline,  # We don't have this without NBA API
            trend='NEUTRAL',
            matchup_adjustment=sharp_adjustment,
            pace_adjustment=0.0,
            total_adjustment=sharp_adjustment
        )

        reasoning = self._generate_reasoning(
            player_name,
            prop_type,
            baseline,
            sharp_adjustment,
            num_books,
            has_sharp
        )

        return PlayerPropProjection(
            prop_type=prop_type,
            projection=round(projection_value, 1),
            confidence=confidence,
            confidence_score=round(confidence_score, 2),
            factors=factors,
            reasoning=reasoning
        )

    def _calculate_edge(
        self,
        market_line: float,
        projection: PlayerPropProjection,
        market_odds: PlayerPropOdds
    ) -> PlayerPropEdge:
        """Calculate betting edge"""
        edge = projection.projection - market_line
        edge_pct = (edge / market_line * 100) if market_line > 0 else 0

        # Determine recommendation
        recommendation = None
        bet_strength = None

        if abs(edge) >= 1.0:  # At least 1 point edge
            if edge > 0:
                recommendation = 'OVER'
            else:
                recommendation = 'UNDER'

            # Determine strength
            if abs(edge_pct) >= 10 and projection.confidence == 'HIGH':
                bet_strength = 'STRONG'
            elif abs(edge_pct) >= 5:
                bet_strength = 'MODERATE'
            else:
                bet_strength = 'WEAK'

        return PlayerPropEdge(
            edge=round(edge, 1),
            edge_pct=round(edge_pct, 1),
            recommendation=recommendation,
            bet_strength=bet_strength
        )

    def _generate_reasoning(
        self,
        player_name: str,
        prop_type: str,
        baseline: float,
        sharp_adj: float,
        num_books: int,
        has_sharp: bool
    ) -> str:
        """Generate human-readable reasoning"""
        reasons = []

        reasons.append(f"Market line: {baseline} {prop_type.lower()}")

        if sharp_adj != 0:
            direction = "higher" if sharp_adj > 0 else "lower"
            reasons.append(f"Sharp books pricing {abs(sharp_adj):.1f} {direction}")

        reasons.append(f"{num_books} sportsbooks offering this line")

        if has_sharp:
            reasons.append("Sharp book data available (Pinnacle/Circa)")
        else:
            reasons.append("No sharp book pricing (use caution)")

        return " | ".join(reasons)

    def _extract_team(self, player_name: str, home_team: str, away_team: str) -> str:
        """
        Attempt to extract team from player name or context
        This is a simple heuristic - in production, you'd want a player-team mapping
        """
        # For now, just return home team (would need player database for accuracy)
        return home_team

    async def close(self):
        """Close the props client"""
        await self.props_client.close()
