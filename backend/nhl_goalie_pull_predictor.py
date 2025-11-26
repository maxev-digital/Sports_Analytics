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

        # FEED DELAY ADJUSTMENT:
        # Our feed is 30 seconds delayed, so we trigger alerts earlier in our system
        # to account for real game time being 30 seconds ahead
        #
        # Alert triggers (in our delayed system):
        # - Down 2+ goals: Alert at 3:00 mark (180 sec) → Real game: ~2:30
        # - Down 1 goal:   Alert at 2:00 mark (120 sec) → Real game: ~1:30
        #
        # This gives users time to place bets before the actual pull happens

        is_imminent = False
        alert_type = None
        alert_priority = None

        if score_diff <= -2:
            # Down 2+ goals: Alert when we see 3:00 remaining (real game ~2:30)
            if current_time_remaining >= 175 and current_time_remaining <= 185:
                is_imminent = True
                alert_type = 'IMMINENT'
                alert_priority = 'HIGH' if confidence >= 0.65 else 'MEDIUM'
        elif score_diff == -1:
            # Down 1 goal: Alert when we see 2:00 remaining (real game ~1:30)
            if current_time_remaining >= 115 and current_time_remaining <= 125:
                is_imminent = True
                alert_type = 'IMMINENT'
                alert_priority = 'HIGH' if confidence >= 0.70 else 'MEDIUM'

        # Early warning removed - single alert at optimal time for bet placement
        is_early_warning = False

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
        Calculate expected value of ALL bet types: OVER, NNG (No Next Goal), UNDER, EXACT SCORE
        Uses team-specific historical empty net stats from database

        Key insight: Must factor in GOALIE PULL PROBABILITY
        - Teams with low pull rate = less likely to pull = higher NNG value
        - 1 goal deficits = best NNG opportunities
        """
        score_diff = game.get('score_diff', -1)
        trailing_team = prediction.get('trailing_team')
        current_score = game.get('home_score', 0) + game.get('away_score', 0)

        # Get database for team-specific EN stats
        db = get_database()

        # Get trailing team's EN stats (offense - when they pull goalie)
        trailing_en_stats = db.get_empty_net_stats(trailing_team, season)

        # Get opponent's EN stats (defense - goals against when other team pulls)
        opponent = game.get('home_team') if trailing_team == game.get('away_team') else game.get('away_team')
        opponent_en_stats = db.get_empty_net_stats(opponent, season)

        # ========== STEP 1: CALCULATE GOALIE PULL PROBABILITY ==========
        # KEY INSIGHT: Team must ACTUALLY PULL goalie for EN goal to happen
        # Low pull rate = less likely to pull = HIGHER NNG value

        en_situations = trailing_en_stats.get('en_opportunities', 0) if trailing_en_stats else 0
        league_avg_situations = 12  # Average team pulls goalie ~12 times per season

        if en_situations >= 3:
            # Calculate pull propensity relative to league average
            pull_propensity = en_situations / league_avg_situations

            # Base pull probability by score differential
            if score_diff == -1:
                base_pull_prob = 0.85  # 85% pull when down 1
            elif score_diff == -2:
                base_pull_prob = 0.65  # 65% pull when down 2
            else:
                base_pull_prob = 0.40  # 40% pull when down 3+

            # Adjust based on team's historical tendency
            prob_pulls_goalie = min(0.95, base_pull_prob * pull_propensity)
            logger.info(f"{trailing_team} pull probability: {prob_pulls_goalie*100:.1f}% (situations: {en_situations}, league avg: {league_avg_situations})")
        else:
            # Not enough data - use league averages
            if score_diff == -1:
                prob_pulls_goalie = 0.85
            elif score_diff == -2:
                prob_pulls_goalie = 0.65
            else:
                prob_pulls_goalie = 0.40
            logger.info(f"Using league average pull prob: {prob_pulls_goalie*100:.1f}%")

        # ========== STEP 2: CALCULATE GOAL PROBABILITIES IF GOALIE IS PULLED ==========

        # EN goal probability (opponent scores) IF goalie is pulled
        if trailing_en_stats and trailing_en_stats.get('en_opportunities', 0) >= 5:
            en_defense_rate = trailing_en_stats.get('en_defense_rate', 52.0) / 100
            en_goal_prob_if_pulled = 1 - en_defense_rate
            logger.info(f"{trailing_team} EN defense: {en_defense_rate*100:.1f}% -> EN goal prob IF pulled: {en_goal_prob_if_pulled*100:.1f}%")
        else:
            en_goal_prob_if_pulled = 0.48  # League average
            logger.info(f"Using league average EN goal prob IF pulled: {en_goal_prob_if_pulled*100:.1f}%")

        # Trailing team scoring probability IF goalie is pulled
        if trailing_en_stats and trailing_en_stats.get('en_opportunities', 0) >= 5:
            trailing_scores_prob_if_pulled = trailing_en_stats.get('en_success_rate', 15.0) / 100
            logger.info(f"{trailing_team} EN success rate IF pulled: {trailing_scores_prob_if_pulled*100:.1f}%")
        else:
            if score_diff == -1:
                trailing_scores_prob_if_pulled = 0.18  # 18% when down 1
            elif score_diff == -2:
                trailing_scores_prob_if_pulled = 0.08  # 8% when down 2
            else:
                trailing_scores_prob_if_pulled = 0.03
            logger.info(f"Using league average trailing score prob IF pulled: {trailing_scores_prob_if_pulled*100:.1f}%")

        # ========== STEP 3: CALCULATE OVERALL PROBABILITIES ==========

        # Probability of goal IF goalie pulled (EN goal OR trailing team scores)
        prob_goal_if_pulled = en_goal_prob_if_pulled + (trailing_scores_prob_if_pulled * (1 - en_goal_prob_if_pulled))

        # Probability of goal IF goalie NOT pulled (much lower - normal hockey)
        prob_goal_if_not_pulled = 0.08  # ~8% chance of goal in last 2 min if no pull

        # TOTAL probability at least one goal scored
        prob_over_hits = (prob_pulls_goalie * prob_goal_if_pulled) + ((1 - prob_pulls_goalie) * prob_goal_if_not_pulled)

        # TOTAL probability NO goal scored (NNG/Under/Exact Score)
        prob_no_goal = 1 - prob_over_hits

        logger.info(f"FINAL PROBABILITIES: Over={prob_over_hits*100:.1f}%, No Goal={prob_no_goal*100:.1f}%")

        # ========== STEP 4: GET CURRENT ODDS FOR ALL BET TYPES ==========

        current_total = current_odds.get('total', current_score + 0.5)
        current_over_odds = current_odds.get('over_odds', 140)  # Default +140
        current_under_odds = current_odds.get('under_odds', -160)  # Default -160

        # NNG odds estimation (typically between +150 and +250 depending on situation)
        # More aggressive teams (high pull prob) = higher NNG odds
        # Conservative teams (low pull prob) = lower NNG odds
        if prob_pulls_goalie > 0.80:
            current_nng_odds = 180  # +180 for aggressive teams
        elif prob_pulls_goalie > 0.60:
            current_nng_odds = 200  # +200 for average teams
        else:
            current_nng_odds = 150  # +150 for conservative teams (less likely to pull)

        current_nng_odds = current_odds.get('nng_odds', current_nng_odds)  # Use provided odds if available

        # Exact score odds (typically 2-3x higher than NNG)
        current_exact_odds = current_odds.get('exact_score_odds', current_nng_odds + 100)

        # ========== STEP 5: CALCULATE EV FOR EACH BET TYPE ==========

        def calculate_ev_for_bet(win_prob: float, american_odds: int) -> tuple:
            """Calculate edge and EV for a bet. Returns (edge%, EV%, implied_prob)"""
            if american_odds > 0:
                implied_prob = 100 / (american_odds + 100)
                payout_multiplier = american_odds / 100
            else:
                implied_prob = abs(american_odds) / (abs(american_odds) + 100)
                payout_multiplier = 100 / abs(american_odds)

            edge = win_prob - implied_prob
            edge_pct = edge * 100
            ev = (win_prob * payout_multiplier) - ((1 - win_prob) * 1)
            ev_pct = ev * 100

            return edge_pct, ev_pct, implied_prob

        # Calculate OVER bet
        over_edge, over_ev, over_implied = calculate_ev_for_bet(prob_over_hits, current_over_odds)

        # Calculate NNG bet (No Next Goal)
        nng_edge, nng_ev, nng_implied = calculate_ev_for_bet(prob_no_goal, current_nng_odds)

        # Calculate UNDER bet (only if total > current score)
        if current_total > current_score:
            under_edge, under_ev, under_implied = calculate_ev_for_bet(prob_no_goal, current_under_odds)
        else:
            under_edge, under_ev, under_implied = -100, -100, 1.0  # No value if total already under

        # Calculate EXACT SCORE bet (slightly lower prob than NNG due to OT possibility)
        prob_exact_score = prob_no_goal * 0.95  # 95% of NNG games end in regulation
        exact_edge, exact_ev, exact_implied = calculate_ev_for_bet(prob_exact_score, current_exact_odds)

        # ========== STEP 6: DETERMINE BEST BET ==========

        bets = [
            {'type': 'OVER', 'edge': over_edge, 'ev': over_ev, 'prob': prob_over_hits, 'odds': current_over_odds},
            {'type': 'NNG', 'edge': nng_edge, 'ev': nng_ev, 'prob': prob_no_goal, 'odds': current_nng_odds},
            {'type': 'UNDER', 'edge': under_edge, 'ev': under_ev, 'prob': prob_no_goal, 'odds': current_under_odds},
            {'type': 'EXACT_SCORE', 'edge': exact_edge, 'ev': exact_ev, 'prob': prob_exact_score, 'odds': current_exact_odds},
        ]

        # Filter to only positive EV bets with 5%+ EV
        positive_ev_bets = [b for b in bets if b['ev'] >= 5.0]

        # Sort by EV (highest first)
        positive_ev_bets.sort(key=lambda x: x['ev'], reverse=True)

        # Determine recommended bet and whether to alert
        if positive_ev_bets and prediction.get('is_imminent'):
            best_bet = positive_ev_bets[0]
            recommended_bet = best_bet['type']
            alert_user = True

            # Log recommendation
            logger.info(f"RECOMMENDED BET: {best_bet['type']} @ {best_bet['odds']:+d} (EV: {best_bet['ev']:.1f}%, Edge: {best_bet['edge']:.1f}%)")
            if len(positive_ev_bets) > 1:
                alt_bets_str = ', '.join([f"{b['type']} (EV: {b['ev']:.1f}%)" for b in positive_ev_bets[1:3]])
                logger.info(f"Alternative bets: {alt_bets_str}")
        else:
            recommended_bet = None
            best_bet = bets[0]  # Default to first for display
            alert_user = False

        # ========== STEP 7: RETURN ALL BETTING INFORMATION ==========

        return {
            # Primary recommendation
            'recommended_bet': recommended_bet,
            'alert_user': alert_user,

            # OVER bet details
            'current_total': current_total,
            'current_odds': current_over_odds,
            'probability_over_hits': round(prob_over_hits, 3),
            'over_edge_percentage': round(over_edge, 2),
            'over_ev_percentage': round(over_ev, 2),

            # NNG/UNDER/EXACT bet details (all based on prob_no_goal)
            'probability_no_goal': round(prob_no_goal, 3),
            'nng_odds': current_nng_odds,
            'nng_edge_percentage': round(nng_edge, 2),
            'nng_ev_percentage': round(nng_ev, 2),

            'under_odds': current_under_odds,
            'under_edge_percentage': round(under_edge, 2),
            'under_ev_percentage': round(under_ev, 2),

            'exact_score_odds': current_exact_odds,
            'exact_edge_percentage': round(exact_edge, 2),
            'exact_ev_percentage': round(exact_ev, 2),

            # Best bet details (for alert display)
            'best_bet_type': recommended_bet if recommended_bet else 'OVER',
            'best_bet_odds': best_bet['odds'],
            'best_bet_edge': round(best_bet['edge'], 2),
            'best_bet_ev': round(best_bet['ev'], 2),
            'best_bet_prob': round(best_bet['prob'], 3),

            # All positive EV opportunities
            'all_positive_ev_bets': positive_ev_bets,

            # Additional context
            'goalie_pull_probability': round(prob_pulls_goalie, 3),
            'en_situations': en_situations,
            'confidence': prediction['confidence'],
            'is_positive_ev': len(positive_ev_bets) > 0,

            # Legacy fields (for backward compatibility)
            'edge_percentage': round(best_bet['edge'], 2),
            'expected_value_percentage': round(best_bet['ev'], 2),
            'implied_probability': round(over_implied, 3),
        }

    @staticmethod
    def generate_alert_message(game: Dict, prediction: Dict, ev_analysis: Dict) -> str:
        """
        Generate user-friendly alert message for betting opportunity
        Handles OVER, NNG, UNDER, and EXACT SCORE recommendations
        """
        alert_type = prediction.get('alert_priority', 'HIGH')
        score_diff = abs(game.get('score_diff', 1))
        current_time = game.get('time_remaining_seconds', 0)
        current_score = game.get('home_score', 0) + game.get('away_score', 0)

        # Format time in MM:SS
        mins = current_time // 60
        secs = current_time % 60
        time_display = f"{mins}:{secs:02d}"

        # Get recommended bet type
        bet_type = ev_analysis.get('best_bet_type', 'OVER')
        bet_odds = ev_analysis.get('best_bet_odds', 140)
        bet_edge = ev_analysis.get('best_bet_edge', 0)
        bet_ev = ev_analysis.get('best_bet_ev', 0)
        bet_prob = ev_analysis.get('best_bet_prob', 0.5)
        goalie_pull_prob = ev_analysis.get('goalie_pull_probability', 0.85)
        en_situations = ev_analysis.get('en_situations', 12)

        # Format bet recommendation based on type
        if bet_type == 'OVER':
            bet_display = f"OVER {ev_analysis['current_total']}"
            bet_explanation = "At least one more goal will be scored"
        elif bet_type == 'NNG':
            bet_display = "NO NEXT GOAL"
            bet_explanation = "Game ends with current score (no more goals)"
        elif bet_type == 'UNDER':
            bet_display = f"UNDER {ev_analysis['current_total']}"
            bet_explanation = "Game total stays under the line"
        elif bet_type == 'EXACT_SCORE':
            bet_display = f"EXACT SCORE {game['away_score']}-{game['home_score']}"
            bet_explanation = "Game ends with this exact score"
        else:
            bet_display = bet_type
            bet_explanation = ""

        # Build situation context
        pull_context = ""
        if goalie_pull_prob < 0.50:
            pull_context = f"\n⚠️ LOW PULL PROBABILITY ({goalie_pull_prob*100:.0f}%) - Team rarely pulls goalie (only {en_situations} times this season)"
        elif goalie_pull_prob > 0.90:
            pull_context = f"\n📊 HIGH PULL PROBABILITY ({goalie_pull_prob*100:.0f}%) - Aggressive team ({en_situations} pulls this season)"

        # Alert message
        message = f"""
🚨 GOALIE PULL ALERT - {alert_type} PRIORITY

{game['away_team']} @ {game['home_team']}
Score: {game['away_score']}-{game['home_score']} (Total: {current_score})
Time: {time_display} remaining (Period {game['period']})

📊 SITUATION:
{prediction['trailing_team']} trailing by {score_diff} goal(s)
Goalie pull probability: {goalie_pull_prob*100:.0f}%
Coach: {prediction['coach']} (Analytics: {prediction['analytics_rating']}/10){pull_context}

💰 RECOMMENDED BET - {bet_display} @ {bet_odds:+d}
{bet_explanation}

📈 BETTING EDGE:
Edge: {bet_edge:+.1f}%
Expected Value: {bet_ev:+.1f}%
Win Probability: {bet_prob*100:.1f}%

⏰ PLACE BET IMMEDIATELY!
Feed is 30 seconds delayed - goalie pull happening soon in real time.
"""

        # Add alternative bets if available
        alt_bets = ev_analysis.get('all_positive_ev_bets', [])
        if len(alt_bets) > 1:
            message += "\n🎯 ALTERNATIVE BETS (also positive EV):\n"
            for i, alt in enumerate(alt_bets[1:3], 1):  # Show top 2 alternatives
                alt_type = alt['type']
                alt_odds = alt['odds']
                alt_ev = alt['ev']

                if alt_type == 'OVER':
                    alt_display = f"OVER {ev_analysis['current_total']}"
                elif alt_type == 'NNG':
                    alt_display = "NO NEXT GOAL"
                elif alt_type == 'UNDER':
                    alt_display = f"UNDER {ev_analysis['current_total']}"
                elif alt_type == 'EXACT_SCORE':
                    alt_display = f"EXACT SCORE {game['away_score']}-{game['home_score']}"
                else:
                    alt_display = alt_type

                message += f"  {i}. {alt_display} @ {alt_odds:+d} (EV: {alt_ev:+.1f}%)\n"

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
