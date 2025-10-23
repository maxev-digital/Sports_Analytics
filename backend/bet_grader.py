"""
Automatic Bet Grading Service
Grades active bets when games complete
"""
import logging
from typing import List, Optional
from storage.bet_storage import bet_storage

logger = logging.getLogger(__name__)


class BetGrader:
    """Service to automatically grade bets when games finish"""

    def __init__(self, game_tracker):
        """
        Initialize bet grader with game tracker reference

        Args:
            game_tracker: GameTracker instance to get game results
        """
        self.game_tracker = game_tracker
        self.logger = logging.getLogger(__name__)

    def grade_bet(self, bet, final_home_score: int, final_away_score: int) -> Optional[str]:
        """
        Determine if a bet won, lost, or pushed

        Args:
            bet: UserBet object
            final_home_score: Final home team score
            final_away_score: Final away team score

        Returns:
            'won', 'lost', 'push', or None if can't be graded
        """
        bet_type = bet.bet_type.lower()

        try:
            if bet_type == 'total':
                return self._grade_total_bet(bet, final_home_score, final_away_score)
            elif bet_type == 'spread':
                return self._grade_spread_bet(bet, final_home_score, final_away_score)
            elif bet_type == 'moneyline':
                return self._grade_moneyline_bet(bet, final_home_score, final_away_score)
            else:
                self.logger.warning(f"Unknown bet type: {bet_type}")
                return None

        except Exception as e:
            self.logger.error(f"Error grading bet {bet.id}: {str(e)}")
            return None

    def _grade_total_bet(self, bet, final_home_score: int, final_away_score: int) -> str:
        """Grade an OVER/UNDER total bet"""
        actual_total = final_home_score + final_away_score
        bet_side = bet.bet_side.upper()

        # Extract the total line from the bet
        # bet_side is typically "OVER" or "UNDER"
        # We need to get the total from the odds or calculate from game data

        # For now, we'll need to look up the game's total line
        # This is stored in the game odds data
        game = self._find_game(bet.game_id)
        if not game:
            self.logger.warning(f"Game {bet.game_id} not found for bet {bet.id}")
            return 'push'

        # Get the total line from the bet's bookmaker odds
        total_line = self._get_total_line_from_game(game, bet.bookmaker)
        if total_line is None:
            self.logger.warning(f"Could not find total line for bet {bet.id}")
            return 'push'

        # Grade the bet
        if bet_side == 'OVER':
            if actual_total > total_line:
                return 'won'
            elif actual_total < total_line:
                return 'lost'
            else:
                return 'push'
        elif bet_side == 'UNDER':
            if actual_total < total_line:
                return 'won'
            elif actual_total > total_line:
                return 'lost'
            else:
                return 'push'
        else:
            self.logger.warning(f"Unknown bet side for total: {bet_side}")
            return 'push'

    def _grade_spread_bet(self, bet, final_home_score: int, final_away_score: int) -> str:
        """Grade a spread bet"""
        # Extract spread from bet_side (e.g., "Lakers -5.5" or "Celtics +3.5")
        bet_side = bet.bet_side

        # Parse the spread value
        parts = bet_side.split()
        if len(parts) < 2:
            self.logger.warning(f"Could not parse spread bet_side: {bet_side}")
            return 'push'

        team_name = ' '.join(parts[:-1])
        spread_str = parts[-1]

        try:
            spread = float(spread_str)
        except ValueError:
            self.logger.warning(f"Could not parse spread value: {spread_str}")
            return 'push'

        # Determine which team was bet on
        is_home_team = bet.home_team.lower() in team_name.lower()
        is_away_team = bet.away_team.lower() in team_name.lower()

        if not is_home_team and not is_away_team:
            self.logger.warning(f"Could not determine team from bet_side: {bet_side}")
            return 'push'

        # Apply spread and determine result
        if is_home_team:
            adjusted_score = final_home_score + spread
            opponent_score = final_away_score
        else:
            adjusted_score = final_away_score + spread
            opponent_score = final_home_score

        # Grade
        if adjusted_score > opponent_score:
            return 'won'
        elif adjusted_score < opponent_score:
            return 'lost'
        else:
            return 'push'

    def _grade_moneyline_bet(self, bet, final_home_score: int, final_away_score: int) -> str:
        """Grade a moneyline bet"""
        bet_team = bet.bet_side.strip()

        # Determine if bet was on home or away team
        is_home_team = bet.home_team.lower() in bet_team.lower()
        is_away_team = bet.away_team.lower() in bet_team.lower()

        if not is_home_team and not is_away_team:
            self.logger.warning(f"Could not determine team from bet_side: {bet_team}")
            return 'push'

        # Determine winner
        if final_home_score > final_away_score:
            winner_is_home = True
        elif final_away_score > final_home_score:
            winner_is_home = False
        else:
            # Tie game
            return 'push'

        # Grade bet
        if is_home_team and winner_is_home:
            return 'won'
        elif is_away_team and not winner_is_home:
            return 'won'
        else:
            return 'lost'

    def _find_game(self, game_id: str):
        """Find game in tracker by game_id"""
        all_games = self.game_tracker.get_all_games()
        for game in all_games:
            if game.state.id == game_id:
                return game
        return None

    def _get_total_line_from_game(self, game, bookmaker: str) -> Optional[float]:
        """Get the total line from game odds for a specific bookmaker"""
        for odd in game.odds:
            if odd.bookmaker.lower() == bookmaker.lower():
                return odd.total

        # If bookmaker not found, use average total
        if game.odds:
            totals = [odd.total for odd in game.odds if odd.total]
            if totals:
                return sum(totals) / len(totals)

        return None

    def grade_active_bets(self) -> dict:
        """
        Grade all active bets for completed games

        Returns:
            Dictionary with grading results
        """
        results = {
            'checked': 0,
            'graded': 0,
            'won': 0,
            'lost': 0,
            'push': 0,
            'errors': 0
        }

        # Get all active bets across all users
        # We'll need to get all bets and filter for active
        try:
            # Get all games
            all_games = self.game_tracker.get_all_games()
            completed_games = {g.state.id: g for g in all_games if g.state.status == 'final'}

            if not completed_games:
                self.logger.debug("No completed games found")
                return results

            # Get all bets from storage (we need to iterate through users)
            # For now, we'll read the JSON file directly
            import json
            from pathlib import Path

            bets_file = Path("data/bets/user_bets.json")
            if not bets_file.exists():
                return results

            with open(bets_file, 'r') as f:
                all_bets = json.load(f)

            # Filter for active bets with completed games
            for bet_data in all_bets:
                if bet_data.get('status') != 'active':
                    continue

                results['checked'] += 1

                game_id = bet_data.get('game_id')
                if game_id not in completed_games:
                    continue

                # Game is completed, grade the bet
                game = completed_games[game_id]

                # Get final scores
                final_home_score = game.state.home_team.score
                final_away_score = game.state.away_team.score

                if final_home_score is None or final_away_score is None:
                    self.logger.warning(f"Missing scores for completed game {game_id}")
                    continue

                # Create UserBet object
                from models.user_bet import UserBet
                bet = UserBet(**bet_data)

                # Grade the bet
                result = self.grade_bet(bet, final_home_score, final_away_score)

                if result:
                    # Settle the bet
                    try:
                        bet_storage.settle_bet(bet.id, result)
                        results['graded'] += 1
                        results[result] += 1
                        self.logger.info(f"Graded bet {bet.id} as {result}")
                    except Exception as e:
                        self.logger.error(f"Error settling bet {bet.id}: {str(e)}")
                        results['errors'] += 1
                else:
                    results['errors'] += 1

            return results

        except Exception as e:
            self.logger.error(f"Error in grade_active_bets: {str(e)}")
            results['errors'] += 1
            return results


# Grader instance will be created when game tracker is available
bet_grader: Optional[BetGrader] = None


def initialize_bet_grader(game_tracker):
    """Initialize the global bet grader instance"""
    global bet_grader
    bet_grader = BetGrader(game_tracker)
    logger.info("Bet grader initialized")
    return bet_grader
