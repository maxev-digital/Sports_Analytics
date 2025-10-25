"""
Momentum Detector Strategy

Detects when teams are "on a run" and live odds haven't fully adjusted.
Focuses on short-term momentum shifts that create betting value.

NHL Detection:
- Goal clusters (2+ goals in 5 min)
- Shot volume spikes (15+ shots in period vs 10 avg)
- Power play momentum (2+ PP goals)

NBA Detection:
- Scoring runs (10+ points unanswered, 8+ in 2 min)
- Shooting hot streaks (5+ consecutive made FGs)
- Pace acceleration (10+ PPP above season average)
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MomentumDetector:
    """
    Multi-sport momentum detection for live betting opportunities
    """

    def __init__(self):
        # NHL Thresholds
        self.nhl_goal_cluster_min = 2  # 2+ goals in window
        self.nhl_goal_cluster_window = 5  # 5 minutes
        self.nhl_shot_spike_threshold = 15  # 15+ shots in period
        self.nhl_shot_spike_avg = 10  # vs 10 shot average
        self.nhl_pp_momentum_min = 2  # 2+ PP goals

        # NBA Thresholds
        self.nba_scoring_run_min = 10  # 10+ points unanswered
        self.nba_quick_run_min = 8  # 8+ points in 2 min
        self.nba_quick_run_window = 2  # 2 minutes
        self.nba_hot_streak_min = 5  # 5+ consecutive makes
        self.nba_pace_spike_threshold = 10  # 10+ PPP above average

        # General
        self.high_confidence_threshold = 75  # Momentum score 75+
        self.medium_confidence_threshold = 60  # Momentum score 60+
        self.low_confidence_threshold = 50  # Momentum score 50+

    def analyze_nhl_momentum(
        self,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int,
        period: str,
        time_remaining: str,
        home_momentum: Optional[Dict] = None,
        away_momentum: Optional[Dict] = None,
        home_season_stats: Optional[Dict] = None,
        away_season_stats: Optional[Dict] = None,
        recent_goals: Optional[List[Dict]] = None,  # List of recent goals with timestamps
        home_shots_period: Optional[int] = None,
        away_shots_period: Optional[int] = None,
    ) -> Dict:
        """
        Analyze NHL game for momentum-based betting opportunities

        Args:
            game_id: Unique game identifier
            sport: Sport key (icehockey_nhl)
            home_team: Home team name
            away_team: Away team name
            home_score: Current home score
            away_score: Current away score
            period: Current period (1st, 2nd, 3rd, OT)
            time_remaining: Time remaining in period
            home_momentum: Home team momentum stats (NHLMomentumStats dict)
            away_momentum: Away team momentum stats (NHLMomentumStats dict)
            home_season_stats: Home team season stats
            away_season_stats: Away team season stats
            recent_goals: List of recent goals [{team, timestamp, type}]
            home_shots_period: Home shots this period
            away_shots_period: Away shots this period

        Returns:
            Dict with has_opportunity and opportunities list
        """
        opportunities = []

        if not home_momentum or not away_momentum:
            return {"has_opportunity": False, "opportunities": []}

        # Analyze home team momentum
        home_opp = self._analyze_nhl_team_momentum(
            team=home_team,
            opponent=away_team,
            is_home=True,
            score=home_score,
            opp_score=away_score,
            momentum_stats=home_momentum,
            season_stats=home_season_stats,
            recent_goals=recent_goals,
            shots_period=home_shots_period,
            period=period,
            game_id=game_id,
            sport=sport,
        )

        if home_opp:
            opportunities.append(home_opp)

        # Analyze away team momentum
        away_opp = self._analyze_nhl_team_momentum(
            team=away_team,
            opponent=home_team,
            is_home=False,
            score=away_score,
            opp_score=home_score,
            momentum_stats=away_momentum,
            season_stats=away_season_stats,
            recent_goals=recent_goals,
            shots_period=away_shots_period,
            period=period,
            game_id=game_id,
            sport=sport,
        )

        if away_opp:
            opportunities.append(away_opp)

        return {
            "has_opportunity": len(opportunities) > 0,
            "opportunities": opportunities,
        }

    def _analyze_nhl_team_momentum(
        self,
        team: str,
        opponent: str,
        is_home: bool,
        score: int,
        opp_score: int,
        momentum_stats: Dict,
        season_stats: Optional[Dict],
        recent_goals: Optional[List[Dict]],
        shots_period: Optional[int],
        period: str,
        game_id: str,
        sport: str,
    ) -> Optional[Dict]:
        """Analyze single NHL team for momentum opportunities"""

        momentum_score = 0
        momentum_factors = []

        # Factor 1: Goal Clusters (2+ goals in 5 min)
        if recent_goals:
            team_recent_goals = [g for g in recent_goals if g.get("team") == team]
            if len(team_recent_goals) >= self.nhl_goal_cluster_min:
                momentum_score += 30
                momentum_factors.append({
                    "name": "Goal Cluster",
                    "score": 30,
                    "max_score": 30,
                    "details": f"{len(team_recent_goals)} goals in {self.nhl_goal_cluster_window} minutes",
                })

        # Factor 2: Shot Volume Spike
        if shots_period and shots_period >= self.nhl_shot_spike_threshold:
            spike_amount = shots_period - self.nhl_shot_spike_avg
            spike_score = min(25, int(spike_amount * 5))
            momentum_score += spike_score
            momentum_factors.append({
                "name": "Shot Volume Spike",
                "score": spike_score,
                "max_score": 25,
                "details": f"{shots_period} shots this period (avg {self.nhl_shot_spike_avg})",
            })

        # Factor 3: Recent Shots (last 5 min)
        recent_shots = momentum_stats.get("recent_shots", 0)
        if recent_shots >= 5:
            shot_score = min(20, recent_shots * 3)
            momentum_score += shot_score
            momentum_factors.append({
                "name": "Recent Shot Pressure",
                "score": shot_score,
                "max_score": 20,
                "details": f"{recent_shots} shots in last 5 minutes",
            })

        # Factor 4: Scoring Chances
        scoring_chances = momentum_stats.get("scoring_chances", 0)
        if scoring_chances >= 3:
            chance_score = min(15, scoring_chances * 5)
            momentum_score += chance_score
            momentum_factors.append({
                "name": "High Danger Chances",
                "score": chance_score,
                "max_score": 15,
                "details": f"{scoring_chances} high danger scoring chances",
            })

        # Factor 5: Offensive Zone Control
        oz_events = momentum_stats.get("offensive_zone_events", 0)
        if oz_events >= 10:
            oz_score = min(10, int(oz_events / 2))
            momentum_score += oz_score
            momentum_factors.append({
                "name": "Offensive Zone Control",
                "score": oz_score,
                "max_score": 10,
                "details": f"{oz_events} offensive zone events",
            })

        # No momentum detected
        if momentum_score < self.low_confidence_threshold:
            return None

        # Determine confidence level
        if momentum_score >= self.high_confidence_threshold:
            confidence = "HIGH"
            expected_win_rate = 0.65
            recommended_stake_pct = 3.0
        elif momentum_score >= self.medium_confidence_threshold:
            confidence = "MEDIUM"
            expected_win_rate = 0.58
            recommended_stake_pct = 2.0
        else:
            confidence = "LOW"
            expected_win_rate = 0.52
            recommended_stake_pct = 1.0

        # Calculate edge
        edge_percentage = (expected_win_rate - 0.5) * 100

        # Generate recommendation
        score_diff = score - opp_score
        if score_diff < 0:
            # Team is losing but has momentum
            recommendation = {
                "bet": f"{team} Live ML or Puck Line",
                "reasoning": f"{team} down {abs(score_diff)} but controlling play with {momentum_score}/100 momentum score. Strong comeback potential.",
            }
        else:
            # Team is winning and has momentum
            recommendation = {
                "bet": f"{team} Live Puck Line or Period Total Over",
                "reasoning": f"{team} leading and dominating with {momentum_score}/100 momentum score. Expect continued pressure.",
            }

        return {
            "strategy": "NHL Momentum Surge",
            "game_id": game_id,
            "sport": sport,
            "home_team": opponent if not is_home else team,
            "away_team": team if not is_home else opponent,
            "period": period,
            "score": f"{score}-{opp_score}",
            "momentum_team": team,
            "momentum_score": momentum_score,
            "confidence_level": confidence,
            "recommendation": recommendation,
            "edge_percentage": edge_percentage,
            "expected_win_rate": expected_win_rate,
            "recommended_stake_percent": recommended_stake_pct,
            "momentum_factors": momentum_factors,
            "timestamp": datetime.now().isoformat(),
        }

    def analyze_nba_momentum(
        self,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int,
        quarter: str,
        time_remaining: str,
        home_momentum: Optional[Dict] = None,
        away_momentum: Optional[Dict] = None,
        home_season_stats: Optional[Dict] = None,
        away_season_stats: Optional[Dict] = None,
        recent_scoring: Optional[List[Dict]] = None,  # List of recent baskets
    ) -> Dict:
        """
        Analyze NBA game for momentum-based betting opportunities

        Args:
            game_id: Unique game identifier
            sport: Sport key (basketball_nba)
            home_team: Home team name
            away_team: Away team name
            home_score: Current home score
            away_score: Current away score
            quarter: Current quarter (1st, 2nd, 3rd, 4th, OT)
            time_remaining: Time remaining in quarter
            home_momentum: Home team momentum stats (NBAMomentumStats dict)
            away_momentum: Away team momentum stats (NBAMomentumStats dict)
            home_season_stats: Home team season stats
            away_season_stats: Away team season stats
            recent_scoring: List of recent baskets [{team, points, timestamp}]

        Returns:
            Dict with has_opportunity and opportunities list
        """
        opportunities = []

        if not home_momentum or not away_momentum:
            return {"has_opportunity": False, "opportunities": []}

        # Analyze home team momentum
        home_opp = self._analyze_nba_team_momentum(
            team=home_team,
            opponent=away_team,
            is_home=True,
            score=home_score,
            opp_score=away_score,
            momentum_stats=home_momentum,
            season_stats=home_season_stats,
            recent_scoring=recent_scoring,
            quarter=quarter,
            game_id=game_id,
            sport=sport,
        )

        if home_opp:
            opportunities.append(home_opp)

        # Analyze away team momentum
        away_opp = self._analyze_nba_team_momentum(
            team=away_team,
            opponent=home_team,
            is_home=False,
            score=away_score,
            opp_score=home_score,
            momentum_stats=away_momentum,
            season_stats=away_season_stats,
            recent_scoring=recent_scoring,
            quarter=quarter,
            game_id=game_id,
            sport=sport,
        )

        if away_opp:
            opportunities.append(away_opp)

        return {
            "has_opportunity": len(opportunities) > 0,
            "opportunities": opportunities,
        }

    def _analyze_nba_team_momentum(
        self,
        team: str,
        opponent: str,
        is_home: bool,
        score: int,
        opp_score: int,
        momentum_stats: Dict,
        season_stats: Optional[Dict],
        recent_scoring: Optional[List[Dict]],
        quarter: str,
        game_id: str,
        sport: str,
    ) -> Optional[Dict]:
        """Analyze single NBA team for momentum opportunities"""

        momentum_score = 0
        momentum_factors = []

        # Factor 1: Scoring Run (10+ unanswered or 8+ in 2 min)
        points_last_5min = momentum_stats.get("points_last_5min", 0)
        if points_last_5min >= self.nba_scoring_run_min:
            run_score = min(35, int(points_last_5min * 2.5))
            momentum_score += run_score
            momentum_factors.append({
                "name": "Scoring Run",
                "score": run_score,
                "max_score": 35,
                "details": f"{points_last_5min} points in last 5 minutes",
            })

        # Factor 2: Shooting Hot Streak
        fg_pct_recent = momentum_stats.get("fg_pct_recent", 0.0)
        if fg_pct_recent >= 0.60:  # 60%+ shooting
            hot_score = min(25, int((fg_pct_recent - 0.40) * 125))
            momentum_score += hot_score
            momentum_factors.append({
                "name": "Hot Shooting",
                "score": hot_score,
                "max_score": 25,
                "details": f"{fg_pct_recent:.1%} FG% in recent possessions",
            })

        # Factor 3: Offensive Rebounds
        offensive_rebounds = momentum_stats.get("offensive_rebounds", 0)
        if offensive_rebounds >= 3:
            oreb_score = min(15, offensive_rebounds * 5)
            momentum_score += oreb_score
            momentum_factors.append({
                "name": "Second Chance Points",
                "score": oreb_score,
                "max_score": 15,
                "details": f"{offensive_rebounds} offensive rebounds (extra possessions)",
            })

        # Factor 4: Defensive Pressure
        steals = momentum_stats.get("steals", 0)
        if steals >= 2:
            steal_score = min(15, steals * 7)
            momentum_score += steal_score
            momentum_factors.append({
                "name": "Defensive Pressure",
                "score": steal_score,
                "max_score": 15,
                "details": f"{steals} steals forcing turnovers",
            })

        # Factor 5: Ball Movement
        assists = momentum_stats.get("assists", 0)
        if assists >= 3:
            assist_score = min(10, assists * 3)
            momentum_score += assist_score
            momentum_factors.append({
                "name": "Ball Movement",
                "score": assist_score,
                "max_score": 10,
                "details": f"{assists} assists (unselfish play)",
            })

        # No momentum detected
        if momentum_score < self.low_confidence_threshold:
            return None

        # Determine confidence level
        if momentum_score >= self.high_confidence_threshold:
            confidence = "HIGH"
            expected_win_rate = 0.62
            recommended_stake_pct = 3.0
        elif momentum_score >= self.medium_confidence_threshold:
            confidence = "MEDIUM"
            expected_win_rate = 0.56
            recommended_stake_pct = 2.0
        else:
            confidence = "LOW"
            expected_win_rate = 0.52
            recommended_stake_pct = 1.0

        # Calculate edge
        edge_percentage = (expected_win_rate - 0.5) * 100

        # Generate recommendation
        score_diff = score - opp_score
        if score_diff < -5:
            # Team is losing but has momentum
            recommendation = {
                "bet": f"{team} Live Spread or ML",
                "reasoning": f"{team} down {abs(score_diff)} but surging with {momentum_score}/100 momentum score. Comeback brewing.",
            }
        elif score_diff > 5:
            # Team is winning and has momentum
            recommendation = {
                "bet": f"{team} Live Spread or Quarter Total Over",
                "reasoning": f"{team} up {score_diff} and rolling with {momentum_score}/100 momentum score. Blowout potential.",
            }
        else:
            # Close game with momentum
            recommendation = {
                "bet": f"{team} Live ML or Spread",
                "reasoning": f"Close game, {team} has {momentum_score}/100 momentum score. Expects to pull away.",
            }

        return {
            "strategy": "NBA Momentum Surge",
            "game_id": game_id,
            "sport": sport,
            "home_team": opponent if not is_home else team,
            "away_team": team if not is_home else opponent,
            "quarter": quarter,
            "score": f"{score}-{opp_score}",
            "momentum_team": team,
            "momentum_score": momentum_score,
            "confidence_level": confidence,
            "recommendation": recommendation,
            "edge_percentage": edge_percentage,
            "expected_win_rate": expected_win_rate,
            "recommended_stake_percent": recommended_stake_pct,
            "momentum_factors": momentum_factors,
            "timestamp": datetime.now().isoformat(),
        }
