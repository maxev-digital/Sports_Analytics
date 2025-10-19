"""
NHL Goalie Pull Predictor
Predicts when teams will pull their goalie and calculates betting opportunities
Uses historical database for accurate team/coach profiles and empty net stats
"""
import logging
from typing import Dict, Optional, List
from datetime import datetime
from nhl_goalie_pull_database import get_database

logger = logging.getLogger(__name__)

# League average defaults (used if no historical data exists for a team)
DEFAULT_PROFILE = {
    'coach': 'Unknown',
    'analytics_score': 5.0,
    'avg_pull_time_down_1': 105,  # 1:45 (league average)
    'avg_pull_time_down_2': 180,  # 3:00
    'earliest_pull_down_1': 135,
    'latest_pull_down_1': 85,
}


class GoaliePullPredictor:
    """Predict when teams will pull their goalie and identify betting opportunities"""

    @staticmethod
    def predict_goalie_pull(game: Dict, trailing_team: str, season: str = '2024-25') -> Optional[Dict]:
        """
        Predict when trailing team will pull goalie
        Uses historical database for accurate predictions
        Returns prediction with timing and confidence
        """
        # Only predict for 3rd period games
        if game.get('period', 0) < 3:
            return None

        score_diff = game.get('score_diff', 0)

        # Only predict for 1-2 goal deficits
        if score_diff < -2 or score_diff >= 0:
            return None

        # Get team profile from database
        db = get_database()
        team_profile = db.get_team_profile(trailing_team, season)

        if team_profile:
            # Use historical data
            profile = {
                'coach': team_profile.get('current_coach', 'Unknown'),
                'analytics_score': team_profile.get('analytics_score', 5.0),
                'avg_pull_time_down_1': team_profile.get('avg_pull_time_down_1', 105),
                'avg_pull_time_down_2': team_profile.get('avg_pull_time_down_2', 180),
                'earliest_pull_down_1': team_profile.get('earliest_pull_down_1', 135),
                'latest_pull_down_1': team_profile.get('latest_pull_down_1', 85),
            }
            logger.info(f"Using database profile for {trailing_team}: {profile['analytics_score']}/10")
        else:
            # Fall back to league average
            profile = DEFAULT_PROFILE.copy()
            logger.warning(f"No database profile for {trailing_team}, using league average")

        # Determine expected pull time based on score differential
        if score_diff == -1:
            expected_pull = profile['avg_pull_time_down_1']
            earliest = profile['earliest_pull_down_1']
            latest = profile['latest_pull_down_1']
            confidence = 0.75  # High confidence for down 1
        elif score_diff == -2:
            expected_pull = profile['avg_pull_time_down_2']
            earliest = expected_pull + 30
            latest = expected_pull - 30
            confidence = 0.65  # Medium confidence for down 2
        else:
            expected_pull = 240  # 4:00 for down 3+
            earliest = 270
            latest = 210
            confidence = 0.50  # Lower confidence

        # Calculate time until pull
        current_time_remaining = game.get('time_remaining_seconds', 0)
        time_until_pull = current_time_remaining - expected_pull

        # Two alert types:
        # 1. EARLY_WARNING: 5+ minutes remaining, alerts user to prepare betting books
        # 2. IMMINENT: 30-90 seconds before expected pull, bet must be placed NOW
        is_early_warning = current_time_remaining >= 300 and score_diff in [-1, -2]
        is_imminent = 30 <= time_until_pull <= 90

        # Determine alert type and priority
        if is_imminent:
            alert_type = 'IMMINENT'
            alert_priority = 'HIGH' if confidence >= 0.70 else 'MEDIUM'
        elif is_early_warning:
            alert_type = 'EARLY_WARNING'
            alert_priority = 'MEDIUM'
        else:
            alert_type = None
            alert_priority = None

        return {
            'trailing_team': trailing_team,
            'expected_pull_time': expected_pull,
            'time_until_pull': time_until_pull,
            'confidence': confidence,
            'earliest_likely': earliest,
            'latest_likely': latest,
            'analytics_rating': profile['analytics_score'],
            'coach': profile['coach'],
            'is_imminent': is_imminent,
            'is_early_warning': is_early_warning,
            'alert_type': alert_type,
            'alert_priority': alert_priority
        }

    @staticmethod
    def calculate_betting_ev(game: Dict, prediction: Dict, current_odds: Dict, season: str = '2024-25') -> Dict:
        """
        Calculate expected value of betting OVER before pull
        Uses team-specific historical empty net stats from database
        """
        score_diff = game.get('score_diff', -1)
        trailing_team = prediction.get('trailing_team')

        # Get database for team-specific EN stats
        db = get_database()

        # Get trailing team's EN stats (offense - when they pull goalie)
        trailing_en_stats = db.get_empty_net_stats(trailing_team, season)

        # Get opponent's EN stats (defense - goals against when other team pulls)
        opponent = game.get('home_team') if trailing_team == game.get('away_team') else game.get('away_team')
        opponent_en_stats = db.get_empty_net_stats(opponent, season)

        # Calculate EN goal probability using team-specific data
        if trailing_en_stats and trailing_en_stats.get('en_opportunities', 0) >= 5:
            # Use team's actual EN defense rate (% of time they DON'T allow EN goal)
            en_defense_rate = trailing_en_stats.get('en_defense_rate', 52.0) / 100
            en_goal_prob = 1 - en_defense_rate  # Flip to get probability OF en goal
            logger.info(f"{trailing_team} EN defense: {en_defense_rate*100:.1f}% -> EN goal prob: {en_goal_prob*100:.1f}%")
        else:
            # Use league average (45-50%)
            en_goal_prob = 0.48
            logger.info(f"Using league average EN goal prob: {en_goal_prob*100:.1f}%")

        # Calculate trailing team scoring probability using their actual success rate
        if trailing_en_stats and trailing_en_stats.get('en_opportunities', 0) >= 5:
            # Use team's actual EN success rate
            trailing_scores_prob = trailing_en_stats.get('en_success_rate', 15.0) / 100
            logger.info(f"{trailing_team} EN success rate: {trailing_scores_prob*100:.1f}%")
        else:
            # Use league average based on score differential
            if score_diff == -1:
                trailing_scores_prob = 0.18  # 18% when down 1
            elif score_diff == -2:
                trailing_scores_prob = 0.08  # 8% when down 2
            else:
                trailing_scores_prob = 0.03
            logger.info(f"Using league average trailing score prob: {trailing_scores_prob*100:.1f}%")

        # Combined probability at least one goal scored
        # P(EN goal OR trailing scores) assuming mutual exclusivity
        prob_over_hits = en_goal_prob + (trailing_scores_prob * (1 - en_goal_prob))

        # Get current odds
        current_total = current_odds.get('total', game.get('current_score', 0) + 0.5)
        current_over_odds = current_odds.get('over_odds', 140)  # Default +140

        # Convert American odds to decimal and implied prob
        if current_over_odds > 0:
            implied_prob = 100 / (current_over_odds + 100)
            payout_multiplier = current_over_odds / 100
        else:
            implied_prob = abs(current_over_odds) / (abs(current_over_odds) + 100)
            payout_multiplier = 100 / abs(current_over_odds)

        # Calculate edge
        edge = prob_over_hits - implied_prob
        edge_percentage = edge * 100

        # Calculate EV
        # EV = (Win Prob × Payout) - (Lose Prob × Stake)
        ev = (prob_over_hits * payout_multiplier) - ((1 - prob_over_hits) * 1)
        ev_percentage = ev * 100

        # Determine if we should alert user
        # IMMINENT alerts require positive EV (bet NOW)
        # EARLY_WARNING alerts shown regardless of EV (prepare books)
        alert_user = False
        if prediction.get('is_imminent'):
            alert_user = ev > 0 and ev_percentage >= 5.0  # Require positive EV for betting
        elif prediction.get('is_early_warning'):
            alert_user = True  # Always alert early warnings to prepare

        return {
            'recommended_bet': 'OVER' if ev > 0 else None,
            'current_total': current_total,
            'current_odds': current_over_odds,
            'probability_over_hits': round(prob_over_hits, 3),
            'implied_probability': round(implied_prob, 3),
            'edge_percentage': round(edge_percentage, 2),
            'expected_value_percentage': round(ev_percentage, 2),
            'confidence': prediction['confidence'],
            'is_positive_ev': ev > 0 and ev_percentage >= 5.0,  # Require 5%+ EV
            'alert_user': alert_user
        }

    @staticmethod
    def generate_alert_message(game: Dict, prediction: Dict, ev_analysis: Dict) -> str:
        """
        Generate user-friendly alert message for betting opportunity
        Handles both EARLY_WARNING and IMMINENT alert types
        """
        alert_type = prediction.get('alert_type', 'IMMINENT')
        time_until = prediction['time_until_pull']
        current_time = game.get('time_remaining_seconds', 0)

        if alert_type == 'EARLY_WARNING':
            # Early warning: prepare betting books
            message = f"""
⏰ EARLY WARNING - POSSIBLE EMPTY NET GOAL PENDING

{game['away_team']} @ {game['home_team']}
Score: {game['away_score']}-{game['home_score']}
Time: {game['time_remaining']} remaining (Period {game['period']})

📊 SITUATION:
{prediction['trailing_team']} is trailing by {abs(game.get('score_diff', 1))} goal(s)
Expected goalie pull in ~{time_until} seconds

🎯 PREPARE YOUR BETTING BOOKS NOW
Get ready to bet OVER {ev_analysis['current_total']} when goalie pull is imminent
Current odds: {ev_analysis['current_odds']:+d}

📈 EXPECTED EDGE:
Win Probability: {ev_analysis['probability_over_hits']*100:.1f}%
Expected Value: {ev_analysis['expected_value_percentage']:+.1f}%

Coach: {prediction['coach']} (Analytics: {prediction['analytics_rating']}/10)
"""
        else:
            # Imminent alert: bet NOW
            message = f"""
🚨 GOALIE PULL ALERT - {prediction['alert_priority']} PRIORITY

{game['away_team']} @ {game['home_team']}
Score: {game['away_score']}-{game['home_score']}
Time: {game['time_remaining']} remaining (Period {game['period']})

📊 PREDICTION:
{prediction['trailing_team']} will pull goalie in ~{time_until} seconds
Coach: {prediction['coach']}
Analytics Score: {prediction['analytics_rating']}/10
Confidence: {prediction['confidence']*100:.0f}%

💰 BET NOW:
OVER {ev_analysis['current_total']} @ {ev_analysis['current_odds']:+d}

Edge: +{ev_analysis['edge_percentage']:.1f}%
Expected Value: +{ev_analysis['expected_value_percentage']:.1f}%
Win Probability: {ev_analysis['probability_over_hits']*100:.1f}%

⏰ BET IMMEDIATELY! (before goalie is pulled)
Odds will shift to -110 or worse after pull.
"""

        return message.strip()

    @staticmethod
    def check_for_opportunities(live_games: List[Dict], odds_data: Dict) -> List[Dict]:
        """
        Main function: Check all live NHL games for goalie pull betting opportunities
        Returns list of opportunities with alerts
        """
        opportunities = []

        for game in live_games:
            # Only check 3rd period
            if game.get('period', 0) < 3:
                continue

            # Determine trailing team
            home_score = game.get('home_score', 0)
            away_score = game.get('away_score', 0)

            if home_score < away_score:
                trailing_team = game['home_team']
                score_diff = home_score - away_score
            elif away_score < home_score:
                trailing_team = game['away_team']
                score_diff = away_score - home_score
            else:
                continue  # Tied game

            # Only 1-2 goal deficits
            if score_diff < -2:
                continue

            # Add score_diff to game dict
            game['score_diff'] = score_diff

            # Predict when pull will happen
            prediction = GoaliePullPredictor.predict_goalie_pull(game, trailing_team)

            if not prediction:
                continue

            # Skip if no alert type (not imminent or early warning)
            if not prediction.get('alert_type'):
                continue

            # Get current odds for this game
            game_odds = odds_data.get(game['game_id'], {
                'total': home_score + away_score + 0.5,
                'over_odds': 140  # Default
            })

            # Calculate EV
            ev_analysis = GoaliePullPredictor.calculate_betting_ev(game, prediction, game_odds)

            # Only alert if positive EV and high confidence
            if ev_analysis['alert_user']:
                alert_message = GoaliePullPredictor.generate_alert_message(game, prediction, ev_analysis)

                opportunity = {
                    'game_id': game['game_id'],
                    'game': f"{game['away_team']} @ {game['home_team']}",
                    'trailing_team': trailing_team,
                    'score': f"{away_score}-{home_score}",
                    'time_remaining': game.get('time_remaining', 'Unknown'),
                    'prediction': prediction,
                    'ev_analysis': ev_analysis,
                    'alert_message': alert_message,
                    'priority': prediction['alert_priority'],
                    'timestamp': datetime.now().isoformat()
                }

                opportunities.append(opportunity)
                logger.info(f"GOALIE PULL OPPORTUNITY: {opportunity['game']}")

        return opportunities


# Test function
def test_predictor():
    """Test the predictor with sample data"""

    # Sample game data
    test_game = {
        'game_id': 'test_123',
        'away_team': 'Tampa Bay Lightning',
        'home_team': 'Boston Bruins',
        'away_score': 2,
        'home_score': 3,
        'period': 3,
        'time_remaining': '2:30',
        'time_remaining_seconds': 150,
        'current_score': 5
    }

    trailing_team = 'Tampa Bay Lightning'
    test_game['score_diff'] = -1

    # Make prediction
    prediction = GoaliePullPredictor.predict_goalie_pull(test_game, trailing_team)
    print("Prediction:")
    print(prediction)
    print()

    # Calculate EV
    current_odds = {'total': 5.5, 'over_odds': 135}
    ev = GoaliePullPredictor.calculate_betting_ev(test_game, prediction, current_odds)
    print("EV Analysis:")
    print(ev)
    print()

    # Generate alert
    if ev['alert_user']:
        message = GoaliePullPredictor.generate_alert_message(test_game, prediction, ev)
        print(message)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_predictor()
