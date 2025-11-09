"""
Key Number Strategy for NFL Betting

Key numbers are the most common final margins in NFL games:
- 3 points (field goal): ~15% of games
- 7 points (touchdown): ~9% of games
- 10 points (FG + TD): ~5% of games
- 6 points (TD no XP): ~3% of games
- 14 points (2 TDs): ~3% of games

When betting lines cross these key numbers, it creates significant value.

Historical Data (2000-2023):
- Games landing on 3: 15.1%
- Games landing on 7: 9.0%
- Games landing on 10: 4.8%
- Games landing on 6: 2.9%
- Games landing on 14: 2.7%

Strategy Edge:
- Buying through key number: -EV (expensive)
- Selling through key number: +EV (valuable)
- Getting extra half-point at key number: Worth 10-15% win probability

Example:
Line moves from -2.5 to -3.5 (crosses 3):
- If you bet -2.5: You win on 1, 2, 3 point wins
- If you bet -3.5: You lose on 3 point wins
- 3 happens 15% of the time → massive advantage!
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class KeyNumberType(Enum):
    """Types of key numbers in NFL"""
    CRITICAL = "CRITICAL"  # 3, 7
    IMPORTANT = "IMPORTANT"  # 10, 6, 14
    MINOR = "MINOR"  # 4, 1


# Key number values and their frequencies (2000-2023 data)
KEY_NUMBERS = {
    3: {'frequency': 0.151, 'type': KeyNumberType.CRITICAL, 'description': 'Field Goal'},
    7: {'frequency': 0.090, 'type': KeyNumberType.CRITICAL, 'description': 'Touchdown'},
    10: {'frequency': 0.048, 'type': KeyNumberType.IMPORTANT, 'description': 'FG + TD'},
    6: {'frequency': 0.029, 'type': KeyNumberType.IMPORTANT, 'description': 'TD (no XP)'},
    14: {'frequency': 0.027, 'type': KeyNumberType.IMPORTANT, 'description': '2 Touchdowns'},
    4: {'frequency': 0.025, 'type': KeyNumberType.MINOR, 'description': 'FG + Safety'},
    1: {'frequency': 0.020, 'type': KeyNumberType.MINOR, 'description': 'Safety or Missed XP'},
}


@dataclass
class KeyNumberOpportunity:
    """Represents a betting opportunity related to key numbers"""
    game_id: str
    sport: str
    home_team: str
    away_team: str
    commence_time: datetime

    # Line information
    current_spread: float
    previous_spread: Optional[float]
    key_number_involved: int
    key_number_type: KeyNumberType
    key_number_frequency: float

    # Opportunity details
    opportunity_type: str  # 'LINE_CROSS', 'AT_KEY', 'BETWEEN_KEYS', 'HALF_POINT_KEY'
    advantage_side: str  # 'HOME', 'AWAY'
    recommendation: str

    # Value metrics
    edge_percentage: float  # Estimated edge from key number position
    confidence: float
    confidence_level: str  # 'HIGH', 'MEDIUM', 'LOW'

    # Reasoning
    key_factors: List[str] = field(default_factory=list)
    reasoning: str = ""
    historical_impact: str = ""

    # Movement tracking
    line_movement: Optional[float] = None
    moved_through_key: bool = False
    direction: Optional[str] = None  # 'TOWARD_FAVORITE', 'TOWARD_UNDERDOG'


@dataclass
class LineMovement:
    """Track line movements for key number analysis"""
    timestamp: datetime
    spread: float
    bookmaker: str


class KeyNumberStrategy:
    """
    Analyzes NFL spreads for key number opportunities

    Detects:
    1. Lines currently AT key numbers (evaluate value)
    2. Lines that CROSSED key numbers (identify best side)
    3. Lines BETWEEN key numbers (safety zones)
    4. Half-point positions near key numbers (premium value)
    """

    def __init__(self):
        self.key_numbers = KEY_NUMBERS
        self.line_history: Dict[str, List[LineMovement]] = {}

    def analyze_game(
        self,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        current_spread: float,
        commence_time: datetime,
        previous_spread: Optional[float] = None,
        line_history: Optional[List[LineMovement]] = None
    ) -> Optional[KeyNumberOpportunity]:
        """
        Analyze a game for key number opportunities

        Args:
            game_id: Unique game identifier
            sport: Must be 'americanfootball_nfl'
            home_team: Home team name
            away_team: Away team name
            current_spread: Current spread (negative = home favored)
            commence_time: Game start time
            previous_spread: Previous spread (for movement detection)
            line_history: Historical line movements

        Returns:
            KeyNumberOpportunity if significant opportunity found, None otherwise
        """
        # Only analyze NFL
        if sport != 'americanfootball_nfl':
            return None

        # Store line history
        if line_history:
            self.line_history[game_id] = line_history

        # Get absolute spread value for analysis
        abs_spread = abs(current_spread)

        # Determine which key number scenarios apply
        opportunity = None

        # Scenario 1: Line crossed a key number
        if previous_spread is not None:
            opportunity = self._check_line_cross(
                game_id, home_team, away_team, commence_time,
                current_spread, previous_spread
            )
            if opportunity:
                return opportunity

        # Scenario 2: Line currently AT a key number
        opportunity = self._check_at_key_number(
            game_id, home_team, away_team, commence_time,
            current_spread
        )
        if opportunity:
            return opportunity

        # Scenario 3: Half-point away from key number (premium position)
        opportunity = self._check_half_point_key(
            game_id, home_team, away_team, commence_time,
            current_spread
        )
        if opportunity:
            return opportunity

        # Scenario 4: Between two key numbers (safe zone)
        opportunity = self._check_between_keys(
            game_id, home_team, away_team, commence_time,
            current_spread
        )

        return opportunity

    def _check_line_cross(
        self,
        game_id: str,
        home_team: str,
        away_team: str,
        commence_time: datetime,
        current_spread: float,
        previous_spread: float
    ) -> Optional[KeyNumberOpportunity]:
        """Check if line crossed a key number"""

        # Determine which key numbers were crossed
        abs_current = abs(current_spread)
        abs_previous = abs(previous_spread)

        min_spread = min(abs_current, abs_previous)
        max_spread = max(abs_current, abs_previous)

        crossed_keys = []
        for key_num, key_data in self.key_numbers.items():
            if min_spread < key_num < max_spread:
                crossed_keys.append((key_num, key_data))

        if not crossed_keys:
            return None

        # Use the most important crossed key number
        crossed_keys.sort(key=lambda x: x[1]['frequency'], reverse=True)
        key_number, key_data = crossed_keys[0]

        # Determine movement direction
        line_movement = current_spread - previous_spread

        if line_movement > 0:
            # Line moved toward underdog (spread increased)
            direction = 'TOWARD_UNDERDOG'
            if current_spread < 0:
                # Home is favorite, spread got smaller (better for home)
                advantage_side = 'HOME'
                favored_team = home_team
                dog_team = away_team
            else:
                # Away is favorite, spread got larger (worse for away)
                advantage_side = 'AWAY'
                favored_team = away_team
                dog_team = home_team
        else:
            # Line moved toward favorite (spread decreased)
            direction = 'TOWARD_FAVORITE'
            if current_spread < 0:
                # Home is favorite, spread got larger (worse for home)
                advantage_side = 'AWAY'
                favored_team = home_team
                dog_team = away_team
            else:
                # Away is favorite, spread got smaller (better for away)
                advantage_side = 'HOME'
                favored_team = away_team
                dog_team = home_team

        # Calculate edge
        # When you have the better side of a key number, edge = key number frequency
        edge_percentage = key_data['frequency']

        # If crossed CRITICAL key (3 or 7), this is HIGH value
        if key_data['type'] == KeyNumberType.CRITICAL:
            confidence = 0.85
            confidence_level = 'HIGH'
            edge_percentage *= 1.2  # 20% boost for critical keys
        elif key_data['type'] == KeyNumberType.IMPORTANT:
            confidence = 0.75
            confidence_level = 'MEDIUM'
        else:
            confidence = 0.65
            confidence_level = 'MEDIUM'

        # Build recommendation
        if advantage_side == 'HOME':
            recommended_team = home_team
            recommended_spread = current_spread
        else:
            recommended_team = away_team
            recommended_spread = -current_spread

        recommendation = f"BET {recommended_team} {recommended_spread:+.1f}"

        key_factors = [
            f"Line crossed key number {key_number} ({key_data['description']})",
            f"Previous: {previous_spread:+.1f} → Current: {current_spread:+.1f}",
            f"Key number {key_number} occurs in {key_data['frequency']*100:.1f}% of games",
            f"You have the better side of the key number",
            f"Direction: {direction}"
        ]

        reasoning = (
            f"Line crossed critical key number {key_number}. You're getting {recommended_spread:+.1f} "
            f"which is on the better side of {key_number}. This key number occurs in "
            f"{key_data['frequency']*100:.1f}% of NFL games, giving you significant value."
        )

        historical_impact = (
            f"When lines cross key number {key_number}, bettors on the right side gain "
            f"{edge_percentage*100:.1f}% edge. This is one of the most valuable positions in NFL betting."
        )

        return KeyNumberOpportunity(
            game_id=game_id,
            sport='americanfootball_nfl',
            home_team=home_team,
            away_team=away_team,
            commence_time=commence_time,
            current_spread=current_spread,
            previous_spread=previous_spread,
            key_number_involved=key_number,
            key_number_type=key_data['type'],
            key_number_frequency=key_data['frequency'],
            opportunity_type='LINE_CROSS',
            advantage_side=advantage_side,
            recommendation=recommendation,
            edge_percentage=edge_percentage,
            confidence=confidence,
            confidence_level=confidence_level,
            key_factors=key_factors,
            reasoning=reasoning,
            historical_impact=historical_impact,
            line_movement=line_movement,
            moved_through_key=True,
            direction=direction
        )

    def _check_at_key_number(
        self,
        game_id: str,
        home_team: str,
        away_team: str,
        commence_time: datetime,
        current_spread: float
    ) -> Optional[KeyNumberOpportunity]:
        """Check if line is currently at a key number"""

        abs_spread = abs(current_spread)

        # Check if at a key number (within 0.01 for floating point)
        at_key = None
        for key_num, key_data in self.key_numbers.items():
            if abs(abs_spread - key_num) < 0.01:
                at_key = (key_num, key_data)
                break

        if not at_key:
            return None

        key_number, key_data = at_key

        # At key number = DON'T BET unless you can get off the number
        # This is more of a warning than an opportunity

        # Only return alert for CRITICAL key numbers (3, 7)
        if key_data['type'] != KeyNumberType.CRITICAL:
            return None

        # Determine favored team
        if current_spread < 0:
            favored_team = home_team
            dog_team = away_team
        else:
            favored_team = away_team
            dog_team = home_team

        recommendation = f"AVOID betting at key number {key_number} - shop for better line"

        key_factors = [
            f"Line is exactly at key number {key_number}",
            f"Key number {key_number} occurs in {key_data['frequency']*100:.1f}% of games",
            f"Betting at key numbers reduces edge significantly",
            f"Shop for {abs_spread - 0.5:+.1f} or {abs_spread + 0.5:+.1f} if possible"
        ]

        reasoning = (
            f"Line is exactly at key number {key_number}. This is a disadvantageous position. "
            f"Try to shop for a better number - even a half-point makes a huge difference. "
            f"If betting favorite, try to get {abs_spread - 0.5:.1f}. "
            f"If betting underdog, try to get {abs_spread + 0.5:.1f}."
        )

        historical_impact = (
            f"Betting at key number {key_number} costs approximately "
            f"{key_data['frequency']*100:.1f}% in edge. Landing exactly on the key number "
            f"results in a push instead of a win."
        )

        return KeyNumberOpportunity(
            game_id=game_id,
            sport='americanfootball_nfl',
            home_team=home_team,
            away_team=away_team,
            commence_time=commence_time,
            current_spread=current_spread,
            previous_spread=None,
            key_number_involved=key_number,
            key_number_type=key_data['type'],
            key_number_frequency=key_data['frequency'],
            opportunity_type='AT_KEY',
            advantage_side='NEITHER',
            recommendation=recommendation,
            edge_percentage=-key_data['frequency'],  # Negative edge
            confidence=0.90,  # High confidence this is bad
            confidence_level='HIGH',
            key_factors=key_factors,
            reasoning=reasoning,
            historical_impact=historical_impact,
            line_movement=None,
            moved_through_key=False,
            direction=None
        )

    def _check_half_point_key(
        self,
        game_id: str,
        home_team: str,
        away_team: str,
        commence_time: datetime,
        current_spread: float
    ) -> Optional[KeyNumberOpportunity]:
        """Check if line is half-point away from key number (premium position)"""

        abs_spread = abs(current_spread)

        # Check if half-point from key number
        near_key = None
        for key_num, key_data in self.key_numbers.items():
            diff = abs(abs_spread - key_num)
            if abs(diff - 0.5) < 0.01:  # Half point away
                near_key = (key_num, key_data, abs_spread < key_num)
                break

        if not near_key:
            return None

        key_number, key_data, below_key = near_key

        # Only alert for CRITICAL and IMPORTANT keys
        if key_data['type'] == KeyNumberType.MINOR:
            return None

        # Determine advantage side
        # If you're below the key number (e.g., -2.5 when key is 3):
        #   - Favorite bettor is in good position (won't lose on key number)
        #   - Underdog bettor is in bad position (won't win on key number)
        # If you're above the key number (e.g., -3.5 when key is 3):
        #   - Favorite bettor is in bad position (will lose on key number)
        #   - Underdog bettor is in good position (will win on key number)

        if current_spread < 0:
            # Home is favorite
            favored_team = home_team
            dog_team = away_team

            if below_key:
                # Below key (e.g., -2.5 vs key 3) = good for favorite
                advantage_side = 'HOME'
                recommended_team = home_team
                recommended_spread = current_spread
            else:
                # Above key (e.g., -3.5 vs key 3) = good for underdog
                advantage_side = 'AWAY'
                recommended_team = away_team
                recommended_spread = -current_spread
        else:
            # Away is favorite
            favored_team = away_team
            dog_team = home_team

            if below_key:
                # Below key = good for favorite
                advantage_side = 'AWAY'
                recommended_team = away_team
                recommended_spread = -current_spread
            else:
                # Above key = good for underdog
                advantage_side = 'HOME'
                recommended_team = home_team
                recommended_spread = current_spread

        # Calculate edge
        edge_percentage = key_data['frequency'] * 0.8  # 80% of full key number value

        if key_data['type'] == KeyNumberType.CRITICAL:
            confidence = 0.80
            confidence_level = 'HIGH'
        else:
            confidence = 0.70
            confidence_level = 'MEDIUM'

        recommendation = f"BET {recommended_team} {recommended_spread:+.1f} (premium half-point)"

        position = "below" if below_key else "above"

        key_factors = [
            f"Line is {abs_spread:.1f}, half-point {position} key number {key_number}",
            f"Key number {key_number} occurs in {key_data['frequency']*100:.1f}% of games",
            f"Half-point positions near key numbers are premium",
            f"You're on the right side of the key number"
        ]

        reasoning = (
            f"Excellent position at {current_spread:+.1f}, which is {position} key number {key_number}. "
            f"This gives you protection from the key number landing. "
            f"With {key_number} occurring in {key_data['frequency']*100:.1f}% of games, "
            f"this half-point is worth significant value."
        )

        historical_impact = (
            f"Half-point positions near key number {key_number} provide approximately "
            f"{edge_percentage*100:.1f}% edge. This is one of the best positions in NFL betting."
        )

        return KeyNumberOpportunity(
            game_id=game_id,
            sport='americanfootball_nfl',
            home_team=home_team,
            away_team=away_team,
            commence_time=commence_time,
            current_spread=current_spread,
            previous_spread=None,
            key_number_involved=key_number,
            key_number_type=key_data['type'],
            key_number_frequency=key_data['frequency'],
            opportunity_type='HALF_POINT_KEY',
            advantage_side=advantage_side,
            recommendation=recommendation,
            edge_percentage=edge_percentage,
            confidence=confidence,
            confidence_level=confidence_level,
            key_factors=key_factors,
            reasoning=reasoning,
            historical_impact=historical_impact,
            line_movement=None,
            moved_through_key=False,
            direction=None
        )

    def _check_between_keys(
        self,
        game_id: str,
        home_team: str,
        away_team: str,
        commence_time: datetime,
        current_spread: float
    ) -> Optional[KeyNumberOpportunity]:
        """Check if line is in safe zone between key numbers"""

        abs_spread = abs(current_spread)

        # Find surrounding key numbers
        keys_below = [k for k in self.key_numbers.keys() if k < abs_spread]
        keys_above = [k for k in self.key_numbers.keys() if k > abs_spread]

        if not keys_below or not keys_above:
            return None

        key_below = max(keys_below)
        key_above = min(keys_above)

        # Only report if between CRITICAL keys (3 and 7)
        if not (key_below in [3, 7] and key_above in [3, 7]):
            # Check if between 3-4 or 6-7 (also valuable)
            if not ((key_below == 3 and key_above == 4) or
                    (key_below == 6 and key_above == 7)):
                return None

        # Being between keys is generally neutral, but can be noted
        # This is more informational than actionable

        # Low priority - only return if it's a notable safe zone
        if abs_spread < 1.5 or abs_spread > 14:
            return None

        recommendation = f"NEUTRAL - Line at {current_spread:+.1f} between keys {key_below} and {key_above}"

        key_factors = [
            f"Line at {abs_spread:.1f} is between key numbers {key_below} and {key_above}",
            f"No immediate key number concerns",
            f"Standard line movement won't cross keys unless significant"
        ]

        reasoning = (
            f"Line is in safe zone between key numbers {key_below} and {key_above}. "
            f"This position doesn't have special key number value but also doesn't "
            f"have key number risk. Standard betting evaluation applies."
        )

        return KeyNumberOpportunity(
            game_id=game_id,
            sport='americanfootball_nfl',
            home_team=home_team,
            away_team=away_team,
            commence_time=commence_time,
            current_spread=current_spread,
            previous_spread=None,
            key_number_involved=key_below,  # Reference point
            key_number_type=self.key_numbers[key_below]['type'],
            key_number_frequency=0.0,  # No specific frequency applies
            opportunity_type='BETWEEN_KEYS',
            advantage_side='NEITHER',
            recommendation=recommendation,
            edge_percentage=0.0,
            confidence=0.50,
            confidence_level='LOW',
            key_factors=key_factors,
            reasoning=reasoning,
            historical_impact="Neutral position - no key number impact",
            line_movement=None,
            moved_through_key=False,
            direction=None
        )

    def get_all_opportunities(
        self,
        games: List[Dict]
    ) -> List[KeyNumberOpportunity]:
        """
        Analyze multiple games for key number opportunities

        Args:
            games: List of game dictionaries with spread information

        Returns:
            List of KeyNumberOpportunity objects
        """
        opportunities = []

        for game in games:
            opp = self.analyze_game(
                game_id=game.get('game_id'),
                sport=game.get('sport'),
                home_team=game.get('home_team'),
                away_team=game.get('away_team'),
                current_spread=game.get('current_spread'),
                commence_time=game.get('commence_time'),
                previous_spread=game.get('previous_spread'),
                line_history=game.get('line_history')
            )

            if opp:
                opportunities.append(opp)

        return opportunities

    def calculate_key_number_value(
        self,
        spread: float,
        key_number: int
    ) -> float:
        """
        Calculate the value (in percentage points) of a position relative to key number

        Args:
            spread: Current spread
            key_number: The key number to evaluate against

        Returns:
            Value in percentage points (positive = good, negative = bad)
        """
        if key_number not in self.key_numbers:
            return 0.0

        freq = self.key_numbers[key_number]['frequency']
        abs_spread = abs(spread)

        diff = abs_spread - key_number

        if abs(diff) < 0.01:
            # Exactly on key number = bad (push risk)
            return -freq
        elif abs(diff - 0.5) < 0.01 or abs(diff + 0.5) < 0.01:
            # Half-point away = good (premium position)
            return freq * 0.8
        elif abs(diff) < 1.0:
            # Close to key number
            return freq * 0.3
        else:
            # Far from key number
            return 0.0


# Example usage and testing
if __name__ == "__main__":
    from datetime import datetime, timedelta

    strategy = KeyNumberStrategy()

    # Test scenarios
    test_games = [
        {
            'game_id': 'nfl_001',
            'sport': 'americanfootball_nfl',
            'home_team': 'Kansas City Chiefs',
            'away_team': 'Buffalo Bills',
            'current_spread': -2.5,  # Half-point below key 3
            'previous_spread': None,
            'commence_time': datetime.now() + timedelta(days=1)
        },
        {
            'game_id': 'nfl_002',
            'sport': 'americanfootball_nfl',
            'home_team': 'Dallas Cowboys',
            'away_team': 'Philadelphia Eagles',
            'current_spread': -3.5,  # Half-point above key 3
            'previous_spread': -2.5,  # Crossed key number 3!
            'commence_time': datetime.now() + timedelta(days=1)
        },
        {
            'game_id': 'nfl_003',
            'sport': 'americanfootball_nfl',
            'home_team': 'Green Bay Packers',
            'away_team': 'Chicago Bears',
            'current_spread': -7.0,  # Exactly on key 7 (bad)
            'previous_spread': None,
            'commence_time': datetime.now() + timedelta(days=2)
        },
        {
            'game_id': 'nfl_004',
            'sport': 'americanfootball_nfl',
            'home_team': 'San Francisco 49ers',
            'away_team': 'Seattle Seahawks',
            'current_spread': -6.5,  # Half-point below key 7
            'previous_spread': -7.5,  # Crossed key 7
            'commence_time': datetime.now() + timedelta(days=2)
        }
    ]

    print("=" * 80)
    print("NFL KEY NUMBER STRATEGY - TEST RESULTS")
    print("=" * 80)

    for game in test_games:
        print(f"\n{'='*80}")
        print(f"Game: {game['away_team']} @ {game['home_team']}")
        print(f"Spread: {game['current_spread']:+.1f}")
        if game['previous_spread']:
            print(f"Previous: {game['previous_spread']:+.1f}")

        opp = strategy.analyze_game(**game)

        if opp:
            print(f"\n🎯 OPPORTUNITY FOUND: {opp.opportunity_type}")
            print(f"Key Number: {opp.key_number_involved} ({opp.key_number_type.value})")
            print(f"Frequency: {opp.key_number_frequency*100:.1f}%")
            print(f"\nRecommendation: {opp.recommendation}")
            print(f"Edge: {opp.edge_percentage*100:+.1f}%")
            print(f"Confidence: {opp.confidence_level} ({opp.confidence*100:.0f}%)")
            print(f"\nReasoning: {opp.reasoning}")
            print(f"\nKey Factors:")
            for factor in opp.key_factors:
                print(f"  • {factor}")
        else:
            print("\n❌ No significant key number opportunity")

    print(f"\n{'='*80}")
    print("Strategy test complete!")
