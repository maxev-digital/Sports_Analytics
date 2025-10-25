"""
Matchup History Strategy Engine
Analyzes head-to-head history and situational matchups to identify betting edges
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime
import numpy as np


@dataclass
class HistoricalGame:
    """Single historical matchup result"""
    date: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    total: int
    spread: Optional[float] = None
    location: str = "home"  # home, away, neutral
    season: str = ""
    playoff: bool = False


@dataclass
class TeamMatchupStats:
    """Head-to-head statistics between two teams"""
    team_a: str
    team_b: str
    total_games: int
    team_a_wins: int
    team_b_wins: int
    avg_total: float
    avg_spread: float  # Positive means team_a wins by this much on avg
    last_5_games: List[HistoricalGame]
    home_away_split: Dict[str, int]  # Win counts by location
    recent_trend: str  # TEAM_A_HOT, TEAM_B_HOT, BALANCED


@dataclass
class SituationalTrend:
    """Situational betting trends (e.g., "Team vs division rivals")"""
    situation: str
    record: str  # e.g., "8-2 ATS"
    win_rate: float
    avg_margin: float
    sample_size: int
    confidence: float


@dataclass
class MatchupPrediction:
    """Prediction based on historical matchups"""
    predicted_winner: str
    predicted_spread: float
    predicted_total: float
    confidence: float
    key_trends: List[str]
    situational_edges: List[SituationalTrend]
    revenge_game: bool
    playoff_implications: bool


class MatchupHistoryStrategy:
    """
    Strategy that analyzes head-to-head history and situational trends

    Key Concepts:
    - Recent H2H results weigh more than older results
    - Playoff games and rivalry games have different patterns
    - Home/away splits matter significantly
    - Revenge games (team lost last meeting) show stronger motivation
    - Situational trends (vs division, back-to-back, etc.)
    """

    def __init__(
        self,
        recent_game_weight: float = 0.6,  # Weight recent games more
        historical_game_weight: float = 0.4,
        min_sample_size: int = 3,  # Minimum games for reliable trends
        revenge_boost: float = 2.0,  # Points boost for revenge games
        rivalry_boost: float = 1.5,  # Boost for rivalry games
    ):
        """
        Initialize Matchup History Strategy

        Args:
            recent_game_weight: How much to weight recent games vs historical
            historical_game_weight: Weight for older historical games
            min_sample_size: Minimum games needed for trend analysis
            revenge_boost: Point adjustment for revenge game motivation
            rivalry_boost: Point adjustment for rivalry matchups
        """
        self.recent_game_weight = recent_game_weight
        self.historical_game_weight = historical_game_weight
        self.min_sample_size = min_sample_size
        self.revenge_boost = revenge_boost
        self.rivalry_boost = rivalry_boost

    def analyze_head_to_head(
        self,
        team_a: str,
        team_b: str,
        historical_games: List[HistoricalGame],
        is_playoff: bool = False
    ) -> TeamMatchupStats:
        """
        Analyze head-to-head history between two teams

        Args:
            team_a: First team name
            team_b: Second team name
            historical_games: List of historical games between teams
            is_playoff: Whether this is a playoff matchup

        Returns:
            TeamMatchupStats with complete H2H analysis
        """
        if not historical_games:
            return TeamMatchupStats(
                team_a=team_a,
                team_b=team_b,
                total_games=0,
                team_a_wins=0,
                team_b_wins=0,
                avg_total=0.0,
                avg_spread=0.0,
                last_5_games=[],
                home_away_split={},
                recent_trend="BALANCED"
            )

        # Sort by date (most recent first)
        sorted_games = sorted(
            historical_games,
            key=lambda x: x.date,
            reverse=True
        )

        # Calculate wins
        team_a_wins = 0
        team_b_wins = 0
        totals = []
        spreads = []
        home_away_split = {"team_a_home": 0, "team_a_away": 0, "team_b_home": 0, "team_b_away": 0}

        for game in sorted_games:
            total = game.total
            totals.append(total)

            # Determine winner and spread
            if game.home_team == team_a:
                margin = game.home_score - game.away_score
                if margin > 0:
                    team_a_wins += 1
                    home_away_split["team_a_home"] += 1
                else:
                    team_b_wins += 1
                spreads.append(margin)
            else:
                margin = game.away_score - game.home_score
                if margin > 0:
                    team_a_wins += 1
                    home_away_split["team_a_away"] += 1
                else:
                    team_b_wins += 1
                    home_away_split["team_b_home"] += 1
                spreads.append(margin)

        # Calculate averages
        avg_total = np.mean(totals) if totals else 0.0
        avg_spread = np.mean(spreads) if spreads else 0.0

        # Determine recent trend (last 5 games)
        last_5 = sorted_games[:5]
        recent_team_a_wins = sum(
            1 for g in last_5
            if (g.home_team == team_a and g.home_score > g.away_score) or
               (g.away_team == team_a and g.away_score > g.home_score)
        )

        if recent_team_a_wins >= 4:
            recent_trend = "TEAM_A_HOT"
        elif recent_team_a_wins <= 1:
            recent_trend = "TEAM_B_HOT"
        else:
            recent_trend = "BALANCED"

        return TeamMatchupStats(
            team_a=team_a,
            team_b=team_b,
            total_games=len(historical_games),
            team_a_wins=team_a_wins,
            team_b_wins=team_b_wins,
            avg_total=avg_total,
            avg_spread=avg_spread,
            last_5_games=last_5,
            home_away_split=home_away_split,
            recent_trend=recent_trend
        )

    def detect_revenge_game(
        self,
        team_a: str,
        team_b: str,
        last_5_games: List[HistoricalGame]
    ) -> tuple[bool, str]:
        """
        Detect if this is a revenge game scenario

        Args:
            team_a: First team
            team_b: Second team
            last_5_games: Recent games between teams

        Returns:
            (is_revenge_game, revenge_team_name)
        """
        if not last_5_games:
            return False, ""

        # Check last meeting
        last_game = last_5_games[0]

        # Determine who lost last meeting
        if last_game.home_team == team_a:
            if last_game.home_score < last_game.away_score:
                return True, team_a  # Team A lost at home, wants revenge
        else:
            if last_game.away_score < last_game.home_score:
                return True, team_a  # Team A lost on road, wants revenge

        # Check if team_b lost
        if last_game.home_team == team_b:
            if last_game.home_score < last_game.away_score:
                return True, team_b
        else:
            if last_game.away_score < last_game.home_score:
                return True, team_b

        return False, ""

    def analyze_situational_trends(
        self,
        team: str,
        situation: str,
        games: List[HistoricalGame]
    ) -> Optional[SituationalTrend]:
        """
        Analyze team performance in specific situations

        Args:
            team: Team name
            situation: Situation description (e.g., "vs_division_rivals")
            games: Games matching this situation

        Returns:
            SituationalTrend if sample size sufficient, else None
        """
        if len(games) < self.min_sample_size:
            return None

        wins = 0
        margins = []

        for game in games:
            if game.home_team == team:
                margin = game.home_score - game.away_score
                if margin > 0:
                    wins += 1
                margins.append(margin)
            else:
                margin = game.away_score - game.home_score
                if margin > 0:
                    wins += 1
                margins.append(margin)

        win_rate = wins / len(games)
        avg_margin = np.mean(margins)

        # Calculate confidence based on sample size and consistency
        consistency = 1.0 - (np.std(margins) / (abs(avg_margin) + 1))
        sample_confidence = min(len(games) / 10.0, 1.0)
        confidence = (consistency * 0.6) + (sample_confidence * 0.4)

        record = f"{wins}-{len(games)-wins}"

        return SituationalTrend(
            situation=situation,
            record=record,
            win_rate=win_rate,
            avg_margin=avg_margin,
            sample_size=len(games),
            confidence=confidence
        )

    def predict(
        self,
        team_a: str,
        team_b: str,
        historical_games: List[HistoricalGame],
        team_a_home: bool = True,
        is_playoff: bool = False,
        is_rivalry: bool = False,
        situational_games: Optional[Dict[str, List[HistoricalGame]]] = None
    ) -> MatchupPrediction:
        """
        Generate prediction based on matchup history

        Args:
            team_a: First team (typically home team)
            team_b: Second team
            historical_games: Historical H2H games
            team_a_home: Whether team_a is home
            is_playoff: Playoff game flag
            is_rivalry: Rivalry game flag
            situational_games: Dict of situation -> games for trend analysis

        Returns:
            MatchupPrediction with complete analysis
        """
        # Analyze H2H
        h2h_stats = self.analyze_head_to_head(team_a, team_b, historical_games, is_playoff)

        # Check for revenge game
        is_revenge, revenge_team = self.detect_revenge_game(
            team_a,
            team_b,
            h2h_stats.last_5_games
        )

        # Base prediction from historical average
        predicted_spread = h2h_stats.avg_spread
        predicted_total = h2h_stats.avg_total

        # Adjust for home court if applicable
        if team_a_home:
            predicted_spread += 2.5  # Home court advantage
        else:
            predicted_spread -= 2.5

        # Adjust for revenge game
        if is_revenge:
            if revenge_team == team_a:
                predicted_spread += self.revenge_boost
            else:
                predicted_spread -= self.revenge_boost

        # Adjust for rivalry
        if is_rivalry:
            # Rivalry games tend to be closer and higher scoring
            predicted_spread *= 0.8  # Compress spread
            predicted_total += self.rivalry_boost

        # Analyze situational trends
        situational_edges = []
        if situational_games:
            for situation, games in situational_games.items():
                trend = self.analyze_situational_trends(team_a, situation, games)
                if trend and trend.confidence >= 0.5:
                    situational_edges.append(trend)
                    # Adjust prediction based on strong trends
                    if trend.confidence >= 0.7:
                        predicted_spread += trend.avg_margin * 0.3

        # Generate key trends
        key_trends = []

        if h2h_stats.total_games >= self.min_sample_size:
            key_trends.append(
                f"H2H: {team_a} {h2h_stats.team_a_wins}-{h2h_stats.team_b_wins} vs {team_b}"
            )

        if h2h_stats.recent_trend != "BALANCED":
            winning_team = team_a if "TEAM_A" in h2h_stats.recent_trend else team_b
            key_trends.append(f"{winning_team} won {4 if 'HOT' in h2h_stats.recent_trend else 3} of last 5 meetings")

        if is_revenge:
            key_trends.append(f"REVENGE GAME: {revenge_team} lost last meeting")

        if is_rivalry:
            key_trends.append("RIVALRY GAME: Expect closer, higher-scoring contest")

        # Calculate confidence
        base_confidence = min(h2h_stats.total_games / 10.0, 0.7)

        if h2h_stats.recent_trend != "BALANCED":
            base_confidence += 0.15

        if is_revenge:
            base_confidence += 0.10

        situational_confidence = np.mean([t.confidence for t in situational_edges]) if situational_edges else 0

        final_confidence = min(base_confidence + (situational_confidence * 0.15), 1.0)

        # Determine predicted winner
        predicted_winner = team_a if predicted_spread > 0 else team_b

        return MatchupPrediction(
            predicted_winner=predicted_winner,
            predicted_spread=predicted_spread,
            predicted_total=predicted_total,
            confidence=final_confidence,
            key_trends=key_trends,
            situational_edges=situational_edges,
            revenge_game=is_revenge,
            playoff_implications=is_playoff
        )

    def compare_to_market(
        self,
        prediction: MatchupPrediction,
        market_spread: float,
        market_total: float
    ) -> Dict:
        """
        Compare prediction to market lines to find edges

        Args:
            prediction: MatchupPrediction from predict()
            market_spread: Current market spread
            market_total: Current market total

        Returns:
            Dict with edge analysis
        """
        spread_edge = prediction.predicted_spread - market_spread
        total_edge = prediction.predicted_total - market_total

        # Determine if there's a bet
        spread_bet = None
        total_bet = None

        if abs(spread_edge) >= 3.0 and prediction.confidence >= 0.6:
            if spread_edge > 0:
                spread_bet = f"{prediction.predicted_winner} to cover"
            else:
                loser = prediction.predicted_winner  # Swap
                spread_bet = f"{loser} to cover (fade {prediction.predicted_winner})"

        if abs(total_edge) >= 4.0 and prediction.confidence >= 0.6:
            total_bet = "OVER" if total_edge > 0 else "UNDER"

        return {
            "spread_edge": spread_edge,
            "total_edge": total_edge,
            "spread_bet": spread_bet,
            "total_bet": total_bet,
            "confidence": prediction.confidence,
            "key_trends": prediction.key_trends,
            "situational_edges": [
                {
                    "situation": t.situation,
                    "record": t.record,
                    "avg_margin": f"{t.avg_margin:+.1f}",
                    "confidence": f"{t.confidence:.2f}"
                }
                for t in prediction.situational_edges
            ],
            "revenge_game": prediction.revenge_game
        }


# Example usage
if __name__ == "__main__":
    # Initialize strategy
    strategy = MatchupHistoryStrategy()

    # Example: NHL matchup - Maple Leafs vs Bruins (historical rivalry)
    historical_games = [
        HistoricalGame("2024-12-15", "Toronto Maple Leafs", "Boston Bruins", 4, 3, 7, location="home"),
        HistoricalGame("2024-11-20", "Boston Bruins", "Toronto Maple Leafs", 5, 2, 7, location="home"),
        HistoricalGame("2024-10-15", "Toronto Maple Leafs", "Boston Bruins", 3, 4, 7, location="home"),
        HistoricalGame("2024-04-10", "Boston Bruins", "Toronto Maple Leafs", 6, 3, 9, location="home", playoff=True),
        HistoricalGame("2024-03-15", "Toronto Maple Leafs", "Boston Bruins", 2, 1, 3, location="home"),
        HistoricalGame("2024-02-20", "Boston Bruins", "Toronto Maple Leafs", 4, 2, 6, location="home"),
        HistoricalGame("2024-01-10", "Toronto Maple Leafs", "Boston Bruins", 5, 4, 9, location="home"),
    ]

    # Generate prediction
    prediction = strategy.predict(
        team_a="Toronto Maple Leafs",
        team_b="Boston Bruins",
        historical_games=historical_games,
        team_a_home=True,
        is_rivalry=True
    )

    # Market lines
    market_spread = -1.5  # Leafs favored by 1.5
    market_total = 6.5

    # Compare to market
    analysis = strategy.compare_to_market(prediction, market_spread, market_total)

    # Print results
    print("="*70)
    print("MATCHUP HISTORY ANALYSIS: Maple Leafs vs Bruins")
    print("="*70)
    print(f"\nPredicted Winner: {prediction.predicted_winner}")
    print(f"Predicted Spread: {prediction.predicted_spread:+.1f}")
    print(f"Predicted Total: {prediction.predicted_total:.1f}")
    print(f"Confidence: {prediction.confidence:.2f}")

    print(f"\nMarket Lines:")
    print(f"  Spread: {market_spread:+.1f}")
    print(f"  Total: {market_total:.1f}")

    print(f"\nEdges:")
    print(f"  Spread Edge: {analysis['spread_edge']:+.1f}")
    print(f"  Total Edge: {analysis['total_edge']:+.1f}")

    print(f"\nRecommendations:")
    print(f"  Spread Bet: {analysis['spread_bet']}")
    print(f"  Total Bet: {analysis['total_bet']}")

    print(f"\nKey Trends:")
    for trend in analysis['key_trends']:
        print(f"  • {trend}")

    if analysis['revenge_game']:
        print(f"\n  ⚠️  REVENGE GAME FACTOR")

    print("="*70)
