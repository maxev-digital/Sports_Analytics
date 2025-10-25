"""NBA Player Props Manager

Coordinates the complete player props workflow:
1. Fetch props odds from The Odds API
2. Fetch player stats from NBA API
3. Generate projections
4. Calculate edges
5. Return structured data with recommendations
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from player_props_client import PlayerPropsClient
from nba_player_props_stats import NBAPlayerPropsStats
from nba_props_projector import NBAPropsProjector
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

class NBAPropsManager:
    """
    Orchestrates the complete NBA player props workflow
    """

    # Map prop market keys to our internal prop types
    PROP_TYPE_MAPPING = {
        'player_points': 'points',
        'player_rebounds': 'rebounds',
        'player_assists': 'assists',
        'player_threes': 'threes',
        'player_steals': 'steals',
        'player_blocks': 'blocks'
    }

    def __init__(self):
        self.props_client = PlayerPropsClient()
        self.stats_client = NBAPlayerPropsStats()
        self.projector = NBAPropsProjector()

    async def get_nba_props_with_edges(
        self,
        games: List[Dict],
        min_edge_pct: float = 5.0
    ) -> PlayerPropsResponse:
        """
        Get all NBA player props with calculated edges

        Args:
            games: List of NBA game dicts with 'id' and 'sport_key'
            min_edge_pct: Minimum edge percentage to include (default 5%)

        Returns:
            PlayerPropsResponse with all props that have edges
        """
        all_game_props = []
        total_props = 0
        total_strong = 0
        total_moderate = 0

        for game in games:
            event_id = game.get('id')
            sport_key = game.get('sport_key')
            home_team = game.get('home_team')
            away_team = game.get('away_team')
            commence_time = game.get('commence_time')

            if not event_id or sport_key != 'basketball_nba':
                continue

            logger.info(f"Processing props for {away_team} @ {home_team}")

            # Fetch market props
            game_props_data = await self.props_client.fetch_game_props(
                sport_key=sport_key,
                event_id=event_id
            )

            if not game_props_data:
                logger.warning(f"No props data for {event_id}")
                continue

            # Process each prop market
            game_props = []
            props_by_market = game_props_data.get('props_by_market', {})

            for market_key, players_props in props_by_market.items():
                prop_type = self.PROP_TYPE_MAPPING.get(market_key)
                if not prop_type:
                    continue  # Skip unsupported prop types

                for player_prop_data in players_props:
                    player_name = player_prop_data.get('player_name')
                    line = player_prop_data.get('line')
                    bookmakers = player_prop_data.get('bookmakers', {})

                    if not player_name or line is None:
                        continue

                    # Determine which team the player is on and opponent
                    player_team, opponent_team = self._determine_teams(
                        player_name,
                        home_team,
                        away_team
                    )

                    # Fetch player profile and generate projection
                    player_profile = self.stats_client.get_player_complete_profile(
                        player_name=player_name,
                        opponent_team=opponent_team
                    )

                    if not player_profile:
                        logger.warning(f"Could not fetch profile for {player_name}")
                        continue

                    # Generate projection
                    projections = self.projector.project_player_stats(
                        player_profile=player_profile,
                        opponent_team=opponent_team
                    )

                    projection_data = projections.get(prop_type)
                    if not projection_data:
                        continue

                    # Calculate edge
                    edge_data = self.projector.compare_to_line(
                        projection=projection_data,
                        market_line=line
                    )

                    # Filter by minimum edge
                    if abs(edge_data['edge_pct']) < min_edge_pct:
                        continue

                    # Create structured models
                    market_odds = self._create_market_odds(
                        player_name=player_name,
                        prop_type=prop_type,
                        line=line,
                        bookmakers=bookmakers
                    )

                    projection_model = self._create_projection_model(
                        prop_type=prop_type,
                        projection_data=projection_data
                    )

                    edge_model = PlayerPropEdge(
                        edge=edge_data['edge'],
                        edge_pct=edge_data['edge_pct'],
                        recommendation=edge_data['recommendation'],
                        bet_strength=edge_data['bet_strength']
                    )

                    # Create complete player prop
                    player_prop = PlayerProp(
                        player_name=player_name,
                        team=player_team,
                        opponent=opponent_team,
                        game_time=datetime.fromisoformat(commence_time.replace('Z', '+00:00')) if isinstance(commence_time, str) else commence_time,
                        prop_type=prop_type,
                        market_odds=market_odds,
                        projection=projection_model,
                        edge=edge_model
                    )

                    game_props.append(player_prop)
                    total_props += 1

                    if edge_data['bet_strength'] == 'STRONG':
                        total_strong += 1
                    elif edge_data['bet_strength'] == 'MODERATE':
                        total_moderate += 1

            # Create game props model
            if game_props:
                game_props_model = PlayerPropsGame(
                    event_id=event_id,
                    sport_key=sport_key,
                    home_team=home_team,
                    away_team=away_team,
                    commence_time=datetime.fromisoformat(commence_time.replace('Z', '+00:00')) if isinstance(commence_time, str) else commence_time,
                    props=game_props
                )
                all_game_props.append(game_props_model)

        # Create response
        response = PlayerPropsResponse(
            games=all_game_props,
            total_props=total_props,
            total_strong_bets=total_strong,
            total_moderate_bets=total_moderate,
            last_updated=datetime.now()
        )

        logger.info(f"Found {total_props} props with edges ({total_strong} strong, {total_moderate} moderate)")
        return response

    def _determine_teams(
        self,
        player_name: str,
        home_team: str,
        away_team: str
    ) -> tuple[str, str]:
        """
        Determine which team player is on and opponent

        Returns:
            (player_team, opponent_team)
        """
        # This is a simplified version - would need proper team roster lookup
        # For now, we'll return unknown and let the stats client handle it
        player = self.stats_client.get_player_by_name(player_name)

        if player:
            player_id = player['id']
            season_stats = self.stats_client.get_player_season_stats(player_id)
            if season_stats:
                player_team = season_stats.get('team_abbr')

                # Determine opponent
                if player_team == home_team:
                    return (home_team, away_team)
                else:
                    return (away_team, home_team)

        # Fallback: return None for opponent
        return (player_name, None)

    def _create_market_odds(
        self,
        player_name: str,
        prop_type: str,
        line: float,
        bookmakers: Dict
    ) -> PlayerPropOdds:
        """
        Create PlayerPropOdds model from raw bookmaker data
        """
        bookmaker_odds_list = []
        best_over = (None, float('-inf'))
        best_under = (None, float('-inf'))

        for bookmaker_name, odds in bookmakers.items():
            over_odds = odds.get('over')
            under_odds = odds.get('under')

            bookmaker_odds_list.append(BookmakerOdds(
                bookmaker=bookmaker_name,
                over_odds=over_odds,
                under_odds=under_odds
            ))

            # Track best odds
            if over_odds and over_odds > best_over[1]:
                best_over = (bookmaker_name, over_odds)
            if under_odds and under_odds > best_under[1]:
                best_under = (bookmaker_name, under_odds)

        return PlayerPropOdds(
            player_name=player_name,
            prop_type=prop_type,
            line=line,
            bookmakers=bookmaker_odds_list,
            best_over_odds=best_over[1] if best_over[0] else None,
            best_under_odds=best_under[1] if best_under[0] else None,
            best_over_book=best_over[0],
            best_under_book=best_under[0]
        )

    def _create_projection_model(
        self,
        prop_type: str,
        projection_data: Dict
    ) -> PlayerPropProjection:
        """
        Create PlayerPropProjection model from projection data
        """
        factors = projection_data.get('factors', {})

        factors_model = ProjectionFactors(
            baseline=factors.get('baseline', 0),
            recent_avg=factors.get('recent_avg', 0),
            trend=factors.get('trend', 'stable'),
            matchup_adjustment=factors.get('matchup_adjustment', 0),
            pace_adjustment=factors.get('pace_adjustment', 0),
            total_adjustment=factors.get('total_adjustment', 0)
        )

        return PlayerPropProjection(
            prop_type=prop_type,
            projection=projection_data.get('projection', 0),
            confidence=projection_data.get('confidence', 'LOW'),
            confidence_score=projection_data.get('confidence_score', 0),
            factors=factors_model,
            reasoning=projection_data.get('reasoning', '')
        )

    async def close(self):
        """Close all clients"""
        await self.props_client.close()
