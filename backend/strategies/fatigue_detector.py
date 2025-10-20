"""
Schedule Fatigue Detection
Implements back-to-back game detection and fatigue-based betting strategies

Based on Live_Betting_Strategies.md:
- NHL: Back-to-backs drop 0.108 points/game; win rates -4-5%
- NFL/NCAAF: Weather/fatigue plays
- NBA: Back-to-back detection and rest day analysis
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class FatigueDetector:
    """
    Detect schedule-based fatigue and betting opportunities
    """

    def __init__(self):
        self.team_schedules: Dict[str, List[Dict]] = {}
        self.rest_day_cache: Dict[str, int] = {}

    def update_team_schedule(
        self,
        team_name: str,
        sport: str,
        games: List[Dict[str, Any]]
    ):
        """
        Update team schedule for fatigue tracking

        Args:
            team_name: Team name
            sport: Sport type
            games: List of games with {'date': datetime, 'location': str, 'opponent': str}
        """
        key = f"{sport}_{team_name}"
        self.team_schedules[key] = sorted(games, key=lambda x: x['date'])

    def analyze_fatigue(
        self,
        home_team: str,
        away_team: str,
        sport: str,
        game_date: datetime,
        home_miles_traveled: Optional[float] = None,
        away_miles_traveled: Optional[float] = None,
        home_time_zones: Optional[int] = None,
        away_time_zones: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze fatigue factors for both teams

        Returns:
            Dict with fatigue analysis and betting opportunities
        """
        # Get rest days for both teams
        home_rest = self._calculate_rest_days(home_team, sport, game_date)
        away_rest = self._calculate_rest_days(away_team, sport, game_date)

        # Detect back-to-back situations
        home_b2b = home_rest == 0
        away_b2b = away_rest == 0

        # Calculate fatigue scores
        home_fatigue = self._calculate_fatigue_score(
            rest_days=home_rest,
            miles_traveled=home_miles_traveled or 0,
            time_zones=home_time_zones or 0,
            is_home=True
        )
        away_fatigue = self._calculate_fatigue_score(
            rest_days=away_rest,
            miles_traveled=away_miles_traveled or 0,
            time_zones=away_time_zones or 0,
            is_home=False
        )

        fatigue_diff = away_fatigue - home_fatigue

        # Generate betting opportunities
        opportunities = self._generate_fatigue_opportunities(
            sport=sport,
            home_team=home_team,
            away_team=away_team,
            home_b2b=home_b2b,
            away_b2b=away_b2b,
            home_rest=home_rest,
            away_rest=away_rest,
            fatigue_diff=fatigue_diff,
            home_fatigue=home_fatigue,
            away_fatigue=away_fatigue
        )

        return {
            'home_team': home_team,
            'away_team': away_team,
            'sport': sport,
            'home_rest_days': home_rest,
            'away_rest_days': away_rest,
            'home_back_to_back': home_b2b,
            'away_back_to_back': away_b2b,
            'home_fatigue_score': round(home_fatigue, 2),
            'away_fatigue_score': round(away_fatigue, 2),
            'fatigue_differential': round(fatigue_diff, 2),
            'opportunities': opportunities,
            'timestamp': datetime.now().isoformat()
        }

    def _calculate_rest_days(
        self,
        team_name: str,
        sport: str,
        game_date: datetime
    ) -> int:
        """
        Calculate rest days since last game

        Returns:
            Number of rest days (0 = back-to-back)
        """
        key = f"{sport}_{team_name}"
        schedule = self.team_schedules.get(key, [])

        if not schedule:
            return 1  # Default to 1 rest day if no schedule data

        # Find most recent game before this one
        previous_games = [g for g in schedule if g['date'] < game_date]
        if not previous_games:
            return 3  # Well-rested if no previous games

        last_game = max(previous_games, key=lambda x: x['date'])
        rest_days = (game_date - last_game['date']).days - 1

        return max(0, rest_days)  # Can't be negative

    def _calculate_fatigue_score(
        self,
        rest_days: int,
        miles_traveled: float,
        time_zones: int,
        is_home: bool
    ) -> float:
        """
        Calculate overall fatigue score (0-10, higher = more fatigued)

        Factors:
        - Rest days (most important)
        - Travel distance
        - Time zone changes
        - Home vs Away
        """
        score = 0.0

        # Rest days component (0-5 points)
        if rest_days == 0:
            score += 5.0  # Back-to-back = maximum fatigue
        elif rest_days == 1:
            score += 3.0
        elif rest_days == 2:
            score += 1.5
        # 3+ days = no fatigue from rest

        # Travel distance component (0-3 points)
        if miles_traveled > 2500:
            score += 3.0
        elif miles_traveled > 1500:
            score += 2.0
        elif miles_traveled > 800:
            score += 1.0

        # Time zone component (0-2 points)
        score += min(abs(time_zones) * 0.5, 2.0)

        # Away game penalty (0-1 point)
        if not is_home:
            score += 0.5

        return min(score, 10.0)  # Cap at 10

    def _generate_fatigue_opportunities(
        self,
        sport: str,
        home_team: str,
        away_team: str,
        home_b2b: bool,
        away_b2b: bool,
        home_rest: int,
        away_rest: int,
        fatigue_diff: float,
        home_fatigue: float,
        away_fatigue: float
    ) -> List[Dict]:
        """
        Generate betting opportunities based on fatigue analysis

        Strategy (from Live_Betting_Strategies.md):
        - NHL back-to-backs: -0.108 points/game, -4-5% win rate
        - Fatigue edges: Underdog moneylines, under totals
        """
        opportunities = []

        # Significant fatigue differential (3+ points)
        if abs(fatigue_diff) >= 3.0:
            favored_team = home_team if fatigue_diff > 0 else away_team
            fatigued_team = away_team if fatigue_diff > 0 else home_team

            opportunities.append({
                'type': 'fatigue_mismatch',
                'strategy': 'Fatigue and Schedule Spots (Back-to-Back or Travel)',
                'trigger': f'Fatigue differential: {abs(fatigue_diff):.1f} points',
                'confidence_level': 'HIGH' if abs(fatigue_diff) >= 5.0 else 'MEDIUM',
                'recommendation': {
                    'bet_type': 'moneyline',
                    'side': favored_team,
                    'reasoning': f'{fatigued_team} shows significant fatigue ({max(home_fatigue, away_fatigue):.1f}/10)'
                },
                'historical_performance': {
                    'win_rate': 52.0 if sport == 'NHL' else 54.0,
                    'sample': 'NHL/NBA back-to-back scenarios',
                    'variance': 'MEDIUM - Moderate volatility; infrequent'
                },
                'edge_percentage': 4.0 + (abs(fatigue_diff) * 0.5),
                'risk_level': 'MEDIUM',
                'stake_recommendation': '2-4% bankroll',
                'fatigue_details': {
                    'home_fatigue': round(home_fatigue, 2),
                    'away_fatigue': round(away_fatigue, 2),
                    'home_rest_days': home_rest,
                    'away_rest_days': away_rest
                }
            })

        # Back-to-back specific opportunities
        if home_b2b or away_b2b:
            b2b_team = home_team if home_b2b else away_team
            fresh_team = away_team if home_b2b else home_team

            if sport == 'NHL':
                # NHL specific: Back-to-backs drop 0.108 points/game
                opportunities.append({
                    'type': 'back_to_back',
                    'strategy': 'Fatigue and Schedule Spots (Back-to-Back or Travel)',
                    'trigger': f'{b2b_team} playing back-to-back games',
                    'confidence_level': 'MEDIUM',
                    'recommendation': {
                        'bet_type': 'total',
                        'side': 'under',
                        'reasoning': f'NHL back-to-backs drop 0.108 points/game historically; {b2b_team} fatigued'
                    },
                    'historical_performance': {
                        'win_rate': 52.8,
                        'points_impact': -0.108,
                        'win_rate_drop': -4.5,
                        'sample': 'NHL historical data',
                        'variance': 'MEDIUM - Moderate volatility; schedule-dependent'
                    },
                    'edge_percentage': 3.5,
                    'risk_level': 'MEDIUM',
                    'stake_recommendation': '2-4% bankroll'
                })

                # Also recommend fresh team moneyline
                opportunities.append({
                    'type': 'back_to_back_ml',
                    'strategy': 'Fatigue and Schedule Spots (Back-to-Back or Travel)',
                    'trigger': f'{fresh_team} facing back-to-back opponent',
                    'confidence_level': 'LOW',
                    'recommendation': {
                        'bet_type': 'moneyline',
                        'side': fresh_team,
                        'reasoning': f'{fresh_team} has rest advantage over {b2b_team}'
                    },
                    'historical_performance': {
                        'win_rate': 54.5,
                        'sample': 'NHL rest advantage scenarios',
                        'variance': 'MEDIUM'
                    },
                    'edge_percentage': 2.5,
                    'risk_level': 'MEDIUM',
                    'stake_recommendation': '2-3% bankroll'
                })

            elif sport in ['NBA', 'NCAAB']:
                # NBA/College basketball back-to-back
                opportunities.append({
                    'type': 'back_to_back',
                    'strategy': 'Fatigue and Schedule Spots (Back-to-Back or Travel)',
                    'trigger': f'{b2b_team} playing back-to-back games',
                    'confidence_level': 'MEDIUM',
                    'recommendation': {
                        'bet_type': 'spread',
                        'side': fresh_team,
                        'reasoning': f'{fresh_team} rested vs {b2b_team} on back-to-back'
                    },
                    'historical_performance': {
                        'win_rate': 53.5,
                        'sample': 'NBA back-to-back scenarios',
                        'variance': 'MEDIUM'
                    },
                    'edge_percentage': 3.0,
                    'risk_level': 'MEDIUM',
                    'stake_recommendation': '2-4% bankroll'
                })

        # Well-rested team advantage (3+ days vs 0-1 days)
        if (home_rest >= 3 and away_rest <= 1) or (away_rest >= 3 and home_rest <= 1):
            rested_team = home_team if home_rest >= 3 else away_team
            tired_team = away_team if home_rest >= 3 else home_team

            opportunities.append({
                'type': 'rest_advantage',
                'strategy': 'Fatigue and Schedule Spots (Back-to-Back or Travel)',
                'trigger': f'{rested_team} rested (3+ days) vs {tired_team} (0-1 days)',
                'confidence_level': 'LOW',
                'recommendation': {
                    'bet_type': 'moneyline' if sport in ['NHL', 'MLB'] else 'spread',
                    'side': rested_team,
                    'reasoning': f'Significant rest advantage: {max(home_rest, away_rest)} vs {min(home_rest, away_rest)} days'
                },
                'historical_performance': {
                    'win_rate': 52.0,
                    'sample': 'Rest advantage scenarios',
                    'variance': 'MEDIUM - Moderate volatility; reliable historical'
                },
                'edge_percentage': 2.0,
                'risk_level': 'MEDIUM',
                'stake_recommendation': '2-4% bankroll'
            })

        return opportunities

    def get_team_schedule(self, team_name: str, sport: str) -> List[Dict]:
        """Get team's schedule"""
        key = f"{sport}_{team_name}"
        return self.team_schedules.get(key, [])

    def clear_team_schedule(self, team_name: str, sport: str):
        """Clear team schedule data"""
        key = f"{sport}_{team_name}"
        if key in self.team_schedules:
            del self.team_schedules[key]
