"""
NFL Weather Impact Strategy
Analyzes weather conditions and their impact on game totals
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

# NFL Stadium Locations (lat/lon for weather API)
NFL_STADIUMS = {
    # Outdoor stadiums only
    "Buffalo Bills": {"city": "Buffalo", "lat": 42.7738, "lon": -78.7870, "outdoor": True},
    "Miami Dolphins": {"city": "Miami Gardens", "lat": 25.9580, "lon": -80.2389, "outdoor": True},
    "New England Patriots": {"city": "Foxborough", "lat": 42.0909, "lon": -71.2643, "outdoor": True},
    "New York Jets": {"city": "East Rutherford", "lat": 40.8135, "lon": -74.0745, "outdoor": True},
    "Baltimore Ravens": {"city": "Baltimore", "lat": 39.2780, "lon": -76.6227, "outdoor": True},
    "Cincinnati Bengals": {"city": "Cincinnati", "lat": 39.0954, "lon": -84.5160, "outdoor": True},
    "Cleveland Browns": {"city": "Cleveland", "lat": 41.5061, "lon": -81.6995, "outdoor": True},
    "Pittsburgh Steelers": {"city": "Pittsburgh", "lat": 40.4468, "lon": -80.0158, "outdoor": True},
    "Denver Broncos": {"city": "Denver", "lat": 39.7439, "lon": -105.0201, "outdoor": True},
    "Kansas City Chiefs": {"city": "Kansas City", "lat": 39.0489, "lon": -94.4839, "outdoor": True},
    "Las Vegas Raiders": {"city": "Las Vegas", "lat": 36.0909, "lon": -115.1833, "outdoor": False},  # Dome
    "Los Angeles Chargers": {"city": "Inglewood", "lat": 33.9535, "lon": -118.3390, "outdoor": False},  # Dome
    "Chicago Bears": {"city": "Chicago", "lat": 41.8623, "lon": -87.6167, "outdoor": True},
    "Green Bay Packers": {"city": "Green Bay", "lat": 44.5013, "lon": -88.0622, "outdoor": True},
    "Carolina Panthers": {"city": "Charlotte", "lat": 35.2258, "lon": -80.8528, "outdoor": True},
    "Philadelphia Eagles": {"city": "Philadelphia", "lat": 39.9008, "lon": -75.1675, "outdoor": True},
    "Washington Commanders": {"city": "Landover", "lat": 38.9076, "lon": -76.8645, "outdoor": True},
    "San Francisco 49ers": {"city": "Santa Clara", "lat": 37.4032, "lon": -121.9698, "outdoor": True},
    "Seattle Seahawks": {"city": "Seattle", "lat": 47.5952, "lon": -122.3316, "outdoor": True},
    "Tennessee Titans": {"city": "Nashville", "lat": 36.1665, "lon": -86.7713, "outdoor": True},
    "Jacksonville Jaguars": {"city": "Jacksonville", "lat": 30.3239, "lon": -81.6374, "outdoor": True},
    # Indoor stadiums (no weather impact)
    "Dallas Cowboys": {"city": "Arlington", "lat": 32.7473, "lon": -97.0945, "outdoor": False},
    "Houston Texans": {"city": "Houston", "lat": 29.6847, "lon": -95.4107, "outdoor": False},
    "Indianapolis Colts": {"city": "Indianapolis", "lat": 39.7600, "lon": -86.1639, "outdoor": False},
    "Detroit Lions": {"city": "Detroit", "lat": 42.3400, "lon": -83.0456, "outdoor": False},
    "Minnesota Vikings": {"city": "Minneapolis", "lat": 44.9738, "lon": -93.2577, "outdoor": False},
    "New Orleans Saints": {"city": "New Orleans", "lat": 29.9511, "lon": -90.0812, "outdoor": False},
    "Atlanta Falcons": {"city": "Atlanta", "lat": 33.7555, "lon": -84.4009, "outdoor": False},
    "Arizona Cardinals": {"city": "Glendale", "lat": 33.5276, "lon": -112.2626, "outdoor": False},
    "Los Angeles Rams": {"city": "Inglewood", "lat": 33.9535, "lon": -118.3390, "outdoor": False},
}


@dataclass
class WeatherConditions:
    """Current weather conditions at game location"""
    temperature: float  # Fahrenheit
    wind_speed: float  # MPH
    precipitation: Optional[str] = None  # "rain", "snow", None
    precipitation_chance: float = 0.0  # 0-100%
    humidity: float = 0.0
    conditions: str = "Clear"
    wind_direction: Optional[str] = None


@dataclass
class WeatherImpact:
    """Weather impact analysis for betting"""
    has_impact: bool
    impact_level: str  # "NONE", "LOW", "MODERATE", "HIGH", "EXTREME"
    recommendation: Optional[str]  # "UNDER", "OVER", None
    confidence: float  # 0-1
    edge_estimate: float  # Expected edge in points
    total_adjustment: float  # Suggested points to subtract from total
    key_factors: List[str]
    reasoning: str


class WeatherStrategy:
    """
    NFL Weather Impact Strategy

    Historical data shows:
    - Wind >15 MPH: -3 to -5 points on total (passing game affected)
    - Wind >20 MPH: -5 to -8 points (extreme impact)
    - Rain: -2 to -4 points (ball handling, footing)
    - Snow: -4 to -6 points (visibility, footing, cold)
    - Extreme cold (<20°F): -2 to -3 points
    - Heat >95°F: -1 to -2 points (fatigue in 4Q)

    Combined effects multiply impact
    """

    def __init__(
        self,
        wind_threshold_low: float = 15.0,  # MPH for moderate impact
        wind_threshold_high: float = 20.0,  # MPH for extreme impact
        temp_cold_threshold: float = 20.0,  # °F for cold impact
        temp_hot_threshold: float = 95.0,  # °F for heat impact
        precip_threshold: float = 30.0,  # % chance for impact
        min_total_adjustment: float = 3.0,  # Minimum adjustment to recommend bet
    ):
        self.wind_threshold_low = wind_threshold_low
        self.wind_threshold_high = wind_threshold_high
        self.temp_cold_threshold = temp_cold_threshold
        self.temp_hot_threshold = temp_hot_threshold
        self.precip_threshold = precip_threshold
        self.min_total_adjustment = min_total_adjustment

    def analyze_weather_impact(
        self,
        weather: WeatherConditions,
        market_total: float
    ) -> WeatherImpact:
        """
        Analyze weather conditions and determine betting impact

        Args:
            weather: Current weather conditions
            market_total: Current betting total

        Returns:
            WeatherImpact with recommendation
        """
        total_adjustment = 0.0
        key_factors = []
        impact_level = "NONE"

        # Wind Impact (most significant factor)
        if weather.wind_speed >= self.wind_threshold_high:
            wind_impact = -6.0  # Extreme wind
            total_adjustment += wind_impact
            key_factors.append(f"EXTREME WIND: {weather.wind_speed:.0f} MPH (passing game severely limited)")
            impact_level = "EXTREME"
        elif weather.wind_speed >= self.wind_threshold_low:
            wind_impact = -3.5  # Moderate wind
            total_adjustment += wind_impact
            key_factors.append(f"HIGH WIND: {weather.wind_speed:.0f} MPH (passing affected)")
            impact_level = "HIGH" if impact_level != "EXTREME" else impact_level

        # Precipitation Impact
        if weather.precipitation:
            if weather.precipitation.lower() == "snow":
                precip_impact = -5.0
                total_adjustment += precip_impact
                key_factors.append("SNOW: Visibility and footing severely impacted")
                impact_level = "EXTREME"
            elif weather.precipitation.lower() == "rain":
                if weather.precipitation_chance >= 70:
                    precip_impact = -3.5
                    total_adjustment += precip_impact
                    key_factors.append("HEAVY RAIN: Ball handling and passing impacted")
                    impact_level = "HIGH" if impact_level not in ["EXTREME"] else impact_level
                elif weather.precipitation_chance >= self.precip_threshold:
                    precip_impact = -2.0
                    total_adjustment += precip_impact
                    key_factors.append("RAIN: Moderate impact on passing game")
                    impact_level = "MODERATE" if impact_level == "NONE" else impact_level

        # Temperature Impact
        if weather.temperature <= self.temp_cold_threshold:
            temp_impact = -2.5
            total_adjustment += temp_impact
            key_factors.append(f"EXTREME COLD: {weather.temperature:.0f}°F (ball harder, fingers numb)")
            if impact_level == "NONE":
                impact_level = "MODERATE"
        elif weather.temperature >= self.temp_hot_threshold:
            temp_impact = -1.5
            total_adjustment += temp_impact
            key_factors.append(f"EXTREME HEAT: {weather.temperature:.0f}°F (4Q fatigue)")
            if impact_level == "NONE":
                impact_level = "LOW"

        # Combined extreme conditions (multiplicative effect)
        if len(key_factors) >= 2:
            combo_penalty = -1.0
            total_adjustment += combo_penalty
            key_factors.append("MULTIPLE FACTORS: Combined weather impact")

        # Determine recommendation
        has_impact = abs(total_adjustment) >= self.min_total_adjustment

        if has_impact and total_adjustment < 0:
            recommendation = "UNDER"
            edge_estimate = abs(total_adjustment)

            # Calculate confidence based on severity
            if impact_level == "EXTREME":
                confidence = 0.85
            elif impact_level == "HIGH":
                confidence = 0.75
            elif impact_level == "MODERATE":
                confidence = 0.65
            else:
                confidence = 0.55
        else:
            recommendation = None
            edge_estimate = 0.0
            confidence = 0.0
            impact_level = "NONE"

        # Generate reasoning
        reasoning = self._generate_reasoning(weather, total_adjustment, market_total, key_factors)

        return WeatherImpact(
            has_impact=has_impact,
            impact_level=impact_level,
            recommendation=recommendation,
            confidence=confidence,
            edge_estimate=edge_estimate,
            total_adjustment=total_adjustment,
            key_factors=key_factors,
            reasoning=reasoning
        )

    def _generate_reasoning(
        self,
        weather: WeatherConditions,
        adjustment: float,
        market_total: float,
        factors: List[str]
    ) -> str:
        """Generate human-readable reasoning"""
        if not factors:
            return "No significant weather impact expected"

        lines = []
        lines.append(f"Weather conditions significantly favor the UNDER {market_total}")
        lines.append(f"Expected total reduction: {abs(adjustment):.1f} points")

        for factor in factors:
            lines.append(f"• {factor}")

        adjusted_total = market_total + adjustment
        lines.append(f"Weather-adjusted total: {adjusted_total:.1f} (vs market {market_total})")

        return " | ".join(lines)

    def is_outdoor_stadium(self, team_name: str) -> bool:
        """Check if team plays in outdoor stadium"""
        stadium = NFL_STADIUMS.get(team_name, {})
        return stadium.get("outdoor", False)

    def get_stadium_location(self, team_name: str) -> Optional[dict]:
        """Get stadium location for weather lookup"""
        return NFL_STADIUMS.get(team_name)


# Example usage
if __name__ == "__main__":
    strategy = WeatherStrategy()

    # Example: Buffalo in winter
    weather = WeatherConditions(
        temperature=18.0,
        wind_speed=22.0,
        precipitation="snow",
        precipitation_chance=80.0,
        conditions="Heavy Snow"
    )

    market_total = 47.5
    impact = strategy.analyze_weather_impact(weather, market_total)

    print("="*70)
    print("NFL WEATHER IMPACT ANALYSIS")
    print("="*70)
    print(f"Market Total: {market_total}")
    print(f"Impact Level: {impact.impact_level}")
    print(f"Recommendation: {impact.recommendation}")
    print(f"Confidence: {impact.confidence:.0%}")
    print(f"Expected Edge: {impact.edge_estimate:.1f} points")
    print(f"Total Adjustment: {impact.total_adjustment:+.1f}")
    print(f"\nKey Factors:")
    for factor in impact.key_factors:
        print(f"  • {factor}")
    print(f"\nReasoning: {impact.reasoning}")
    print("="*70)
