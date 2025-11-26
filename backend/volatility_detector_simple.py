"""
Simple Volatility Opportunity Detector
Detects +money underdog opportunities for volatility arbitrage
"""

import logging

logger = logging.getLogger(__name__)


def detect_volatility_opportunities(games):
    """
    Detect volatility arbitrage opportunities for games
    Simplified version - detects +money underdogs with good edges

    Args:
        games: List of game objects with odds data

    Returns:
        games: Same list with volatility_opportunity added to qualifying games
    """
    try:
        opportunities_found = 0

        # Debug: Log what type of objects we're working with
        if games:
            logger.info(f"[VOLATILITY] Processing {len(games)} games, first game type: {type(games[0])}")

        # For each game, check if there's a volatility opportunity
        for game in games:
            try:
                # Skip if game doesn't have odds
                if not hasattr(game, 'odds') or not game.odds:
                    continue

                # Get best moneyline odds for each side
                home_ml = None
                away_ml = None

                # Check if game has state with money_line in teams (primary source)
                if hasattr(game, 'state') and game.state:
                    state = game.state
                    if hasattr(state, 'home_team') and hasattr(state.home_team, 'money_line'):
                        home_ml = state.home_team.money_line
                    if hasattr(state, 'away_team') and hasattr(state.away_team, 'money_line'):
                        away_ml = state.away_team.money_line

                # Also check odds array for best prices
                for odds_obj in game.odds:
                    if hasattr(odds_obj, 'home_ml') and odds_obj.home_ml:
                        home_ml = odds_obj.home_ml if home_ml is None else max(home_ml, odds_obj.home_ml)
                    if hasattr(odds_obj, 'away_ml') and odds_obj.away_ml:
                        away_ml = odds_obj.away_ml if away_ml is None else max(away_ml, odds_obj.away_ml)

                if home_ml is None or away_ml is None:
                    continue

                # Check for +money opportunities (odds > 100)
                # Entry criteria:
                # 1. Underdog at +money odds (> +150)
                # 2. Not huge underdog (< +400)
                # 3. Game is upcoming or early

                entry_team = None
                entry_odds = None
                confidence = None

                # Get team names
                home_team_name = None
                away_team_name = None
                if hasattr(game, 'state') and game.state:
                    if hasattr(game.state, 'home_team'):
                        home_team_name = getattr(game.state.home_team, 'name', None)
                    if hasattr(game.state, 'away_team'):
                        away_team_name = getattr(game.state.away_team, 'name', None)

                # Check away team (underdog if positive and larger)
                if away_ml > 150 and away_ml < 400 and away_team_name:
                    entry_team = away_team_name
                    entry_odds = away_ml
                    if away_ml > 200:
                        confidence = "HIGH"
                    elif away_ml > 170:
                        confidence = "MEDIUM"
                    else:
                        confidence = "LOW"

                # Check home team (underdog if positive and larger)
                elif home_ml > 150 and home_ml < 400 and home_team_name:
                    entry_team = home_team_name
                    entry_odds = home_ml
                    if home_ml > 200:
                        confidence = "HIGH"
                    elif home_ml > 170:
                        confidence = "MEDIUM"
                    else:
                        confidence = "LOW"

                # If we found an opportunity, add it to the game
                if entry_team and entry_odds:
                    # Calculate edge percentage (simplified)
                    edge_percent = (entry_odds - 100) * 0.04  # Rough approximation

                    opportunity = {
                        "entry_team": entry_team,
                        "entry_odds": int(entry_odds),
                        "entry_edge_percent": round(edge_percent, 1),
                        "confidence": confidence,
                        "trigger_price": int(entry_odds + 70),  # Suggest trigger +70 points higher
                        "expected_profit_percent": round(edge_percent * 0.6, 1)  # Conservative
                    }

                    # Add to game object (works with both Pydantic models and dicts)
                    if hasattr(game, '__dict__'):
                        game.__dict__['volatility_opportunity'] = opportunity
                    else:
                        game['volatility_opportunity'] = opportunity

                    opportunities_found += 1
                    logger.info(f"[VOLATILITY] Found opportunity: {entry_team} at {entry_odds} ({confidence})")

            except Exception as e:
                import traceback
                game_id = 'unknown'
                try:
                    if hasattr(game, 'state') and hasattr(game.state, 'id'):
                        game_id = game.state.id
                except:
                    pass
                logger.warning(f"[VOLATILITY] Error checking game {game_id}: {e}")
                logger.warning(f"[VOLATILITY] Traceback: {traceback.format_exc()}")
                continue

        if opportunities_found > 0:
            logger.info(f"[VOLATILITY] Detected {opportunities_found} opportunities total")

        return games

    except Exception as e:
        logger.error(f"[VOLATILITY] Error in detect_volatility_opportunities: {e}")
        return games  # Return games unchanged on error
