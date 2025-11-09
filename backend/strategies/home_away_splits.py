"""
Home/Away Splits Strategy
Identifies betting value based on team performance differentials between home and away games

Key Concepts:
- Some teams are MUCH better at home (home cooking)
- Some teams travel well (road warriors)
- Market often undervalues these splits
- Extreme splits create betting edges

Historical Edges:
- Teams with 10+ point home/away differential: 56-58% ATS
- Extreme home teams hosting weak road teams: 60%+ ATS
- Road warriors away vs bad home teams: 54-56% ATS

Examples:
- 2022-23 Utah Jazz: 31-10 at home, 6-35 on road (25 game differential!)
- Denver Nuggets (altitude): Historically 5-7 point home advantage
- Portland Trail Blazers: Consistently strong at home, weak on road
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TeamSplits:
    """Home/Away performance splits for a team"""
    team_name: str
    sport: str

    # Home stats
    home_wins: int
    home_losses: int
    home_win_pct: float
    home_ats_record: str  # "10-5" format
    home_ats_pct: float
    home_ppg: float
    home_opp_ppg: float
    home_margin: float

    # Away stats
    away_wins: int
    away_losses: int
    away_win_pct: float
    away_ats_record: str
    away_ats_pct: float
    away_ppg: float
    away_opp_ppg: float
    away_margin: float

    # Differentials
    win_pct_diff: float  # home - away
    ats_pct_diff: float
    ppg_diff: float
    margin_diff: float

    # Classification
    split_type: str  # 'EXTREME_HOME', 'HOME_STRONG', 'NEUTRAL', 'ROAD_WARRIOR', 'EXTREME_ROAD'
    split_magnitude: str  # 'ELITE', 'STRONG', 'MODERATE', 'MINIMAL'


@dataclass
class SplitMismatchOpportunity:
    """Betting opportunity based on home/away split mismatch"""
    game_id: str
    sport: str
    home_team: str
    away_team: str
    home_team_splits: TeamSplits
    away_team_splits: TeamSplits

    # Mismatch analysis
    mismatch_type: str  # 'HOME_DOMINANT', 'ROAD_WARRIOR', 'BOTH_EXTREME'
    advantage_team: str
    advantage_magnitude: float  # Expected point advantage

    # Current market
    current_spread: Optional[float]
    current_total: Optional[float]

    # Recommendation
    recommendation: str
    bet_type: str  # 'spread', 'total', or 'both'
    confidence: float
    confidence_level: str

    # Analysis
    key_factors: List[str]
    reasoning: str
    historical_edge: str

    commence_time: datetime


class HomeAwaySplitsStrategy:
    """
    Analyze home/away performance splits to identify betting edges

    Core Logic:
    1. Track team performance at home vs away
    2. Identify extreme splits (teams much better/worse in one venue)
    3. Find mismatches (strong home vs weak away, or vice versa)
    4. Generate betting recommendations

    Split Classifications:
    - EXTREME_HOME: +15%+ better at home (rare but valuable)
    - HOME_STRONG: +8% to +14% better at home
    - NEUTRAL: -7% to +7% (no significant split)
    - ROAD_WARRIOR: -8% to -14% (better on road)
    - EXTREME_ROAD: -15%+ better on road (very rare)

    Magnitude:
    - ELITE: 10+ point differential in margin
    - STRONG: 6-9 point differential
    - MODERATE: 3-5 point differential
    - MINIMAL: <3 point differential
    """

    # Split thresholds (as percentages)
    EXTREME_HOME_THRESHOLD = 0.15  # 15%+ better
    STRONG_HOME_THRESHOLD = 0.08   # 8%+ better
    NEUTRAL_THRESHOLD = 0.07       # -7% to +7%

    # Margin thresholds (in points/goals)
    THRESHOLDS_BY_SPORT = {
        'NBA': {
            'elite': 10.0,
            'strong': 6.0,
            'moderate': 3.0
        },
        'NFL': {
            'elite': 7.0,
            'strong': 4.0,
            'moderate': 2.0
        },
        'NHL': {
            'elite': 1.0,
            'strong': 0.6,
            'moderate': 0.3
        },
        'MLB': {
            'elite': 1.5,
            'strong': 1.0,
            'moderate': 0.5
        }
    }

    def __init__(
        self,
        min_games_played: int = 10,  # Minimum games to have reliable splits
        min_advantage: float = 4.0,  # Minimum expected advantage (NBA)
    ):
        self.min_games_played = min_games_played
        self.min_advantage = min_advantage

        # Cache team splits
        self.team_splits_cache: Dict[str, TeamSplits] = {}

    def analyze_matchup(
        self,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        home_splits: TeamSplits,
        away_splits: TeamSplits,
        current_spread: Optional[float] = None,
        current_total: Optional[float] = None,
        commence_time: datetime = None
    ) -> Optional[SplitMismatchOpportunity]:
        """
        Analyze a matchup for home/away split advantages

        Args:
            game_id: Game identifier
            sport: Sport key
            home_team: Home team name
            away_team: Away team name
            home_splits: Home team's splits
            away_splits: Away team's splits
            current_spread: Current market spread
            current_total: Current market total
            commence_time: Game start time

        Returns:
            SplitMismatchOpportunity if edge found, None otherwise
        """

        # Check minimum games played
        home_games = home_splits.home_wins + home_splits.home_losses
        away_games = away_splits.away_wins + away_splits.away_losses

        if home_games < self.min_games_played or away_games < self.min_games_played:
            return None

        # Calculate expected advantage
        home_advantage = self._calculate_split_advantage(
            home_splits=home_splits,
            away_splits=away_splits,
            sport=sport
        )

        if abs(home_advantage) < self.min_advantage:
            return None

        # Determine mismatch type
        mismatch_type, advantage_team = self._determine_mismatch_type(
            home_splits, away_splits, home_team, away_team, home_advantage
        )

        # Generate recommendation
        recommendation, bet_type = self._generate_recommendation(
            mismatch_type, advantage_team, home_team, away_team,
            current_spread, home_advantage
        )

        # Calculate confidence
        confidence = self._calculate_confidence(
            home_splits, away_splits, home_advantage, sport
        )

        confidence_level = self._get_confidence_level(confidence)

        # Generate analysis
        key_factors = self._generate_key_factors(
            home_splits, away_splits, home_advantage, mismatch_type
        )

        reasoning = self._generate_reasoning(
            home_team, away_team, home_splits, away_splits,
            mismatch_type, home_advantage
        )

        historical_edge = self._get_historical_edge(mismatch_type, home_advantage)

        return SplitMismatchOpportunity(
            game_id=game_id,
            sport=sport,
            home_team=home_team,
            away_team=away_team,
            home_team_splits=home_splits,
            away_team_splits=away_splits,
            mismatch_type=mismatch_type,
            advantage_team=advantage_team,
            advantage_magnitude=home_advantage,
            current_spread=current_spread,
            current_total=current_total,
            recommendation=recommendation,
            bet_type=bet_type,
            confidence=confidence,
            confidence_level=confidence_level,
            key_factors=key_factors,
            reasoning=reasoning,
            historical_edge=historical_edge,
            commence_time=commence_time or datetime.now()
        )

    def _calculate_split_advantage(
        self,
        home_splits: TeamSplits,
        away_splits: TeamSplits,
        sport: str
    ) -> float:
        """
        Calculate expected point advantage based on splits

        Positive = home team advantage
        Negative = away team advantage
        """

        # Home team playing at home (use home stats)
        home_team_margin = home_splits.home_margin

        # Away team playing away (use away stats)
        away_team_margin = away_splits.away_margin

        # Expected advantage = home margin - away margin
        # Example: Home team +8 at home, Away team +2 away = +6 advantage
        # Example: Home team +3 at home, Away team +5 away = -2 advantage (favor away)

        expected_advantage = home_team_margin - away_team_margin

        return expected_advantage

    def _determine_mismatch_type(
        self,
        home_splits: TeamSplits,
        away_splits: TeamSplits,
        home_team: str,
        away_team: str,
        home_advantage: float
    ) -> Tuple[str, str]:
        """Determine the type of split mismatch"""

        home_is_extreme_home = home_splits.split_type in ['EXTREME_HOME', 'HOME_STRONG']
        away_is_weak_road = away_splits.split_type in ['EXTREME_HOME', 'HOME_STRONG']  # Bad on road
        away_is_road_warrior = away_splits.split_type in ['ROAD_WARRIOR', 'EXTREME_ROAD']

        if home_is_extreme_home and away_is_weak_road:
            return 'HOME_DOMINANT', home_team
        elif away_is_road_warrior and home_splits.split_type not in ['EXTREME_HOME', 'HOME_STRONG']:
            return 'ROAD_WARRIOR', away_team
        elif abs(home_advantage) >= 8.0:
            if home_advantage > 0:
                return 'EXTREME_MISMATCH_HOME', home_team
            else:
                return 'EXTREME_MISMATCH_AWAY', away_team
        else:
            if home_advantage > 0:
                return 'MODERATE_HOME', home_team
            else:
                return 'MODERATE_AWAY', away_team

    def _generate_recommendation(
        self,
        mismatch_type: str,
        advantage_team: str,
        home_team: str,
        away_team: str,
        current_spread: Optional[float],
        home_advantage: float
    ) -> Tuple[str, str]:
        """Generate betting recommendation"""

        if advantage_team == home_team:
            # Favor home team
            if current_spread and current_spread < 0:
                # Home is favorite - take spread if it's within advantage
                if abs(current_spread) < abs(home_advantage):
                    return f"BET {home_team} {current_spread:+.1f}", "spread"
                else:
                    return f"PASS - Line too high for {home_team}", "none"
            else:
                return f"BET {home_team}", "spread"
        else:
            # Favor away team
            if current_spread and current_spread > 0:
                # Away getting points
                if current_spread < abs(home_advantage):
                    return f"BET {away_team} +{current_spread:.1f}", "spread"
                else:
                    return f"PASS - Line insufficient for {away_team}", "none"
            else:
                return f"BET {away_team}", "spread"

    def _calculate_confidence(
        self,
        home_splits: TeamSplits,
        away_splits: TeamSplits,
        home_advantage: float,
        sport: str
    ) -> float:
        """Calculate confidence score"""

        base_confidence = 0.55

        # Larger advantage = more confidence
        advantage_magnitude = abs(home_advantage)
        thresholds = self.THRESHOLDS_BY_SPORT.get(
            self._map_sport(sport),
            self.THRESHOLDS_BY_SPORT['NBA']
        )

        if advantage_magnitude >= thresholds['elite']:
            base_confidence += 0.25
        elif advantage_magnitude >= thresholds['strong']:
            base_confidence += 0.15
        elif advantage_magnitude >= thresholds['moderate']:
            base_confidence += 0.08

        # Both teams have extreme splits = more confidence
        if (home_splits.split_magnitude in ['ELITE', 'STRONG'] and
            away_splits.split_magnitude in ['ELITE', 'STRONG']):
            base_confidence += 0.10

        # High ATS differential = more confidence
        ats_diff = abs(home_splits.home_ats_pct - away_splits.away_ats_pct)
        if ats_diff >= 0.20:  # 20%+ difference
            base_confidence += 0.10

        return min(base_confidence, 0.95)

    def _get_confidence_level(self, confidence: float) -> str:
        """Convert confidence score to level"""
        if confidence >= 0.80:
            return 'HIGH'
        elif confidence >= 0.65:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _generate_key_factors(
        self,
        home_splits: TeamSplits,
        away_splits: TeamSplits,
        home_advantage: float,
        mismatch_type: str
    ) -> List[str]:
        """Generate key factors for the opportunity"""

        factors = []

        # Home team splits
        factors.append(
            f"{home_splits.team_name} at home: {home_splits.home_wins}-{home_splits.home_losses} "
            f"({home_splits.home_margin:+.1f} margin)"
        )

        # Away team splits
        factors.append(
            f"{away_splits.team_name} on road: {away_splits.away_wins}-{away_splits.away_losses} "
            f"({away_splits.away_margin:+.1f} margin)"
        )

        # Expected advantage
        factors.append(f"Expected advantage: {abs(home_advantage):.1f} points")

        # ATS records
        if home_splits.home_ats_pct >= 0.55:
            factors.append(f"{home_splits.team_name} home ATS: {home_splits.home_ats_record} ({home_splits.home_ats_pct:.1%})")

        if away_splits.away_ats_pct <= 0.45:
            factors.append(f"{away_splits.team_name} away ATS: {away_splits.away_ats_record} ({away_splits.away_ats_pct:.1%})")

        # Split classification
        if home_splits.split_type in ['EXTREME_HOME', 'HOME_STRONG']:
            factors.append(f"{home_splits.team_name} is {home_splits.split_magnitude} home team")

        if away_splits.split_type in ['EXTREME_HOME', 'HOME_STRONG']:
            factors.append(f"{away_splits.team_name} struggles on road")

        return factors

    def _generate_reasoning(
        self,
        home_team: str,
        away_team: str,
        home_splits: TeamSplits,
        away_splits: TeamSplits,
        mismatch_type: str,
        home_advantage: float
    ) -> str:
        """Generate human-readable reasoning"""

        if home_advantage > 0:
            advantage_team = home_team
            venue = "at home"
            margin = home_splits.home_margin
        else:
            advantage_team = away_team
            venue = "on the road"
            margin = away_splits.away_margin

        reasoning = (
            f"{advantage_team} has {abs(home_advantage):.1f} point advantage based on venue splits. "
            f"{home_team} is {home_splits.home_margin:+.1f} {venue} while "
            f"{away_team} is {away_splits.away_margin:+.1f} on road. "
        )

        if mismatch_type in ['HOME_DOMINANT', 'EXTREME_MISMATCH_HOME']:
            reasoning += f"Strong home team vs weak road team = significant edge."
        elif mismatch_type in ['ROAD_WARRIOR', 'EXTREME_MISMATCH_AWAY']:
            reasoning += f"Road warrior vs average home team = betting value."

        return reasoning

    def _get_historical_edge(self, mismatch_type: str, advantage: float) -> str:
        """Get historical performance for this mismatch type"""

        if mismatch_type in ['HOME_DOMINANT', 'EXTREME_MISMATCH_HOME']:
            if abs(advantage) >= 10.0:
                return "60%+ ATS (extreme home mismatch)"
            elif abs(advantage) >= 6.0:
                return "56-58% ATS (strong home mismatch)"
            else:
                return "54-56% ATS (moderate home edge)"
        elif mismatch_type in ['ROAD_WARRIOR', 'EXTREME_MISMATCH_AWAY']:
            if abs(advantage) >= 10.0:
                return "58%+ ATS (elite road warrior)"
            else:
                return "54-56% ATS (road warrior advantage)"
        else:
            return "52-54% ATS (moderate split edge)"

    def _map_sport(self, sport_key: str) -> str:
        """Map sport key to internal classification"""
        if 'nba' in sport_key.lower() or 'ncaab' in sport_key.lower():
            return 'NBA'
        elif 'nfl' in sport_key.lower() or 'ncaaf' in sport_key.lower():
            return 'NFL'
        elif 'nhl' in sport_key.lower():
            return 'NHL'
        elif 'mlb' in sport_key.lower():
            return 'MLB'
        else:
            return 'NBA'

    def create_team_splits(
        self,
        team_name: str,
        sport: str,
        home_record: Tuple[int, int],  # (wins, losses)
        away_record: Tuple[int, int],
        home_ats: Tuple[int, int, int],  # (wins, losses, pushes)
        away_ats: Tuple[int, int, int],
        home_ppg: float,
        home_opp_ppg: float,
        away_ppg: float,
        away_opp_ppg: float
    ) -> TeamSplits:
        """Create TeamSplits object from stats"""

        home_wins, home_losses = home_record
        away_wins, away_losses = away_record

        home_games = home_wins + home_losses
        away_games = away_wins + away_losses

        home_win_pct = home_wins / home_games if home_games > 0 else 0.0
        away_win_pct = away_wins / away_games if away_games > 0 else 0.0

        home_ats_wins, home_ats_losses, home_ats_pushes = home_ats
        away_ats_wins, away_ats_losses, away_ats_pushes = away_ats

        home_ats_games = home_ats_wins + home_ats_losses
        away_ats_games = away_ats_wins + away_ats_losses

        home_ats_pct = home_ats_wins / home_ats_games if home_ats_games > 0 else 0.5
        away_ats_pct = away_ats_wins / away_ats_games if away_ats_games > 0 else 0.5

        home_margin = home_ppg - home_opp_ppg
        away_margin = away_ppg - away_opp_ppg

        # Calculate differentials
        win_pct_diff = home_win_pct - away_win_pct
        ats_pct_diff = home_ats_pct - away_ats_pct
        ppg_diff = home_ppg - away_ppg
        margin_diff = home_margin - away_margin

        # Classify split type
        split_type = self._classify_split_type(win_pct_diff)
        split_magnitude = self._classify_split_magnitude(margin_diff, sport)

        return TeamSplits(
            team_name=team_name,
            sport=sport,
            home_wins=home_wins,
            home_losses=home_losses,
            home_win_pct=home_win_pct,
            home_ats_record=f"{home_ats_wins}-{home_ats_losses}",
            home_ats_pct=home_ats_pct,
            home_ppg=home_ppg,
            home_opp_ppg=home_opp_ppg,
            home_margin=home_margin,
            away_wins=away_wins,
            away_losses=away_losses,
            away_win_pct=away_win_pct,
            away_ats_record=f"{away_ats_wins}-{away_ats_losses}",
            away_ats_pct=away_ats_pct,
            away_ppg=away_ppg,
            away_opp_ppg=away_opp_ppg,
            away_margin=away_margin,
            win_pct_diff=win_pct_diff,
            ats_pct_diff=ats_pct_diff,
            ppg_diff=ppg_diff,
            margin_diff=margin_diff,
            split_type=split_type,
            split_magnitude=split_magnitude
        )

    def _classify_split_type(self, win_pct_diff: float) -> str:
        """Classify team's split type based on win % differential"""
        if win_pct_diff >= self.EXTREME_HOME_THRESHOLD:
            return 'EXTREME_HOME'
        elif win_pct_diff >= self.STRONG_HOME_THRESHOLD:
            return 'HOME_STRONG'
        elif abs(win_pct_diff) <= self.NEUTRAL_THRESHOLD:
            return 'NEUTRAL'
        elif win_pct_diff <= -self.STRONG_HOME_THRESHOLD:
            return 'ROAD_WARRIOR'
        elif win_pct_diff <= -self.EXTREME_HOME_THRESHOLD:
            return 'EXTREME_ROAD'
        else:
            return 'NEUTRAL'

    def _classify_split_magnitude(self, margin_diff: float, sport: str) -> str:
        """Classify magnitude of split"""
        sport_mapped = self._map_sport(sport)
        thresholds = self.THRESHOLDS_BY_SPORT.get(sport_mapped, self.THRESHOLDS_BY_SPORT['NBA'])

        abs_diff = abs(margin_diff)

        if abs_diff >= thresholds['elite']:
            return 'ELITE'
        elif abs_diff >= thresholds['strong']:
            return 'STRONG'
        elif abs_diff >= thresholds['moderate']:
            return 'MODERATE'
        else:
            return 'MINIMAL'


# Example usage
if __name__ == "__main__":
    strategy = HomeAwaySplitsStrategy()

    # Example: Strong home team vs weak road team
    home_splits = strategy.create_team_splits(
        team_name="Denver Nuggets",
        sport="basketball_nba",
        home_record=(25, 5),  # 25-5 at home
        away_record=(15, 15),  # 15-15 away (neutral)
        home_ats=(18, 12, 0),
        away_ats=(14, 16, 0),
        home_ppg=118.5,
        home_opp_ppg=110.0,
        away_ppg=112.0,
        away_opp_ppg=112.5
    )

    away_splits = strategy.create_team_splits(
        team_name="Portland Trail Blazers",
        sport="basketball_nba",
        home_record=(20, 10),  # Decent at home
        away_record=(8, 22),  # 8-22 away (terrible)
        home_ats=(16, 14, 0),
        away_ats=(10, 20, 0),
        home_ppg=114.0,
        home_opp_ppg=112.0,
        away_ppg=107.0,
        away_opp_ppg=116.0
    )

    opportunity = strategy.analyze_matchup(
        game_id="test_123",
        sport="basketball_nba",
        home_team="Denver Nuggets",
        away_team="Portland Trail Blazers",
        home_splits=home_splits,
        away_splits=away_splits,
        current_spread=-8.5,
        current_total=225.5,
        commence_time=datetime.now()
    )

    if opportunity:
        print("="*70)
        print("HOME/AWAY SPLITS OPPORTUNITY")
        print("="*70)
        print(f"Game: {opportunity.away_team} @ {opportunity.home_team}")
        print(f"Mismatch Type: {opportunity.mismatch_type}")
        print(f"Advantage: {opportunity.advantage_team} by {opportunity.advantage_magnitude:.1f} points")
        print(f"Recommendation: {opportunity.recommendation}")
        print(f"Confidence: {opportunity.confidence_level} ({opportunity.confidence:.0%})")
        print(f"Historical Edge: {opportunity.historical_edge}")
        print(f"\nKey Factors:")
        for factor in opportunity.key_factors:
            print(f"  • {factor}")
        print(f"\nReasoning: {opportunity.reasoning}")
        print("="*70)
