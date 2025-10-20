"""
Weather Integration for Outdoor Sports
Implements weather-based betting strategies for NFL, NCAAF, MLB, MLS, Golf

Based on Live_Betting_Strategies.md:
- NFL/NCAAF: Rain decreases passing ~12%; snow ~25%; scoring drops 4-6 points/game
- MLB: Wind >10 mph increases scoring 0.1 strokes/round
- Golf: Wind +1 mph increases scoring 0.1 strokes
- MLS: Weather impacts (outdoor venues)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WeatherIntegration:
    """
    Integrate weather data for outdoor sports betting strategies
    """

    def __init__(self):
        self.weather_cache: Dict[str, Dict] = {}

    def update_weather(
        self,
        game_id: str,
        location: str,
        temperature: Optional[float] = None,
        precipitation: Optional[str] = None,  # 'none', 'rain', 'snow'
        wind_speed: Optional[float] = None,  # mph
        wind_direction: Optional[str] = None,
        humidity: Optional[float] = None,  # percentage
        conditions: Optional[str] = None  # 'clear', 'cloudy', 'overcast', etc.
    ) -> Dict[str, Any]:
        """
        Update weather conditions for a game

        Args:
            game_id: Unique game identifier
            location: Stadium/venue location
            temperature: Temperature in Fahrenheit
            precipitation: Type of precipitation
            wind_speed: Wind speed in mph
            wind_direction: Wind direction (N, S, E, W, NE, etc.)
            humidity: Humidity percentage
            conditions: General conditions

        Returns:
            Dict with weather analysis
        """
        weather_data = {
            'game_id': game_id,
            'location': location,
            'temperature': temperature,
            'precipitation': precipitation,
            'wind_speed': wind_speed,
            'wind_direction': wind_direction,
            'humidity': humidity,
            'conditions': conditions,
            'timestamp': datetime.now().isoformat()
        }

        self.weather_cache[game_id] = weather_data

        return weather_data

    def analyze_weather_impact(
        self,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        current_total: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analyze weather impact on betting opportunities

        Args:
            game_id: Game identifier
            sport: Sport type (NFL, NCAAF, MLB, MLS, PGA, NCAAF)
            home_team: Home team name
            away_team: Away team name
            current_total: Current over/under line

        Returns:
            Dict with weather impact analysis and opportunities
        """
        weather = self.weather_cache.get(game_id)

        if not weather:
            return {
                'game_id': game_id,
                'sport': sport,
                'has_weather_data': False,
                'message': 'No weather data available'
            }

        # Sport-specific analysis
        opportunities = []

        if sport in ['NFL', 'NCAAF']:
            opportunities.extend(self._analyze_football_weather(
                weather, sport, home_team, away_team, current_total
            ))
        elif sport in ['MLB']:
            opportunities.extend(self._analyze_baseball_weather(
                weather, sport, home_team, away_team, current_total
            ))
        elif sport in ['MLS', 'NCAAS']:  # NCAAS = NCAA Soccer
            opportunities.extend(self._analyze_soccer_weather(
                weather, sport, home_team, away_team, current_total
            ))
        elif sport in ['PGA', 'NCAAG']:  # NCAAG = NCAA Golf
            opportunities.extend(self._analyze_golf_weather(
                weather, sport, current_total
            ))

        return {
            'game_id': game_id,
            'sport': sport,
            'home_team': home_team,
            'away_team': away_team,
            'has_weather_data': True,
            'weather': weather,
            'opportunities': opportunities,
            'timestamp': datetime.now().isoformat()
        }

    def _analyze_football_weather(
        self,
        weather: Dict,
        sport: str,
        home_team: str,
        away_team: str,
        current_total: Optional[float]
    ) -> List[Dict]:
        """
        Analyze NFL/NCAAF weather impact

        Historical data:
        - Rain: -12% passing yards, -4-6 points per game
        - Snow: -25% passing yards, significant scoring decrease
        - Wind: Impacts kicking and passing
        """
        opportunities = []

        precipitation = weather.get('precipitation', 'none')
        wind_speed = weather.get('wind_speed', 0)
        temperature = weather.get('temperature')

        # Rain impact
        if precipitation == 'rain':
            estimated_impact = -5.0  # Points reduction
            confidence = 'MEDIUM'

            opportunities.append({
                'type': 'weather_precipitation',
                'strategy': 'Weather/Fatigue Plays (Late-Game)',
                'trigger': 'Rain conditions',
                'confidence_level': confidence,
                'recommendation': {
                    'bet_type': 'total',
                    'side': 'under',
                    'estimated_impact': estimated_impact,
                    'reasoning': 'Rain decreases passing efficiency ~12% and scoring by 4-6 points historically'
                },
                'historical_performance': {
                    'passing_impact': -12.0,
                    'scoring_impact': -5.0,
                    'sample': 'NFL/NCAAF rain games',
                    'variance': 'MEDIUM - Volatility from conditions'
                },
                'edge_percentage': 5.0,
                'risk_level': 'MEDIUM',
                'stake_recommendation': '2-4% bankroll',
                'weather_details': {
                    'precipitation': precipitation,
                    'wind_speed': wind_speed,
                    'temperature': temperature
                }
            })

        # Snow impact
        elif precipitation == 'snow':
            estimated_impact = -8.0  # Significant points reduction
            confidence = 'HIGH'

            opportunities.append({
                'type': 'weather_precipitation',
                'strategy': 'Weather/Fatigue Plays (Late-Game)',
                'trigger': 'Snow conditions',
                'confidence_level': confidence,
                'recommendation': {
                    'bet_type': 'total',
                    'side': 'under',
                    'estimated_impact': estimated_impact,
                    'reasoning': 'Snow decreases passing efficiency ~25% and significantly reduces scoring'
                },
                'historical_performance': {
                    'passing_impact': -25.0,
                    'scoring_impact': -8.0,
                    'sample': 'NFL/NCAAF snow games',
                    'variance': 'MEDIUM - Volatility from conditions'
                },
                'edge_percentage': 7.0,
                'risk_level': 'MEDIUM',
                'stake_recommendation': '3-5% bankroll',
                'weather_details': {
                    'precipitation': precipitation,
                    'wind_speed': wind_speed,
                    'temperature': temperature
                }
            })

        # High wind impact
        if wind_speed and wind_speed >= 15:
            opportunities.append({
                'type': 'weather_wind',
                'strategy': 'Weather/Fatigue Plays (Late-Game)',
                'trigger': f'High winds: {wind_speed} mph',
                'confidence_level': 'MEDIUM',
                'recommendation': {
                    'bet_type': 'total',
                    'side': 'under',
                    'estimated_impact': -3.0,
                    'reasoning': f'Winds {wind_speed} mph impact passing and kicking game significantly'
                },
                'historical_performance': {
                    'scoring_impact': -3.0,
                    'sample': 'NFL/NCAAF high-wind games',
                    'variance': 'MEDIUM'
                },
                'edge_percentage': 4.0,
                'risk_level': 'MEDIUM',
                'stake_recommendation': '2-4% bankroll',
                'weather_details': {
                    'wind_speed': wind_speed,
                    'wind_direction': weather.get('wind_direction')
                }
            })

        # Extreme cold impact
        if temperature and temperature <= 20:
            opportunities.append({
                'type': 'weather_temperature',
                'strategy': 'Weather/Fatigue Plays (Late-Game)',
                'trigger': f'Extreme cold: {temperature}°F',
                'confidence_level': 'LOW',
                'recommendation': {
                    'bet_type': 'total',
                    'side': 'under',
                    'estimated_impact': -2.0,
                    'reasoning': 'Extreme cold affects ball handling, player performance'
                },
                'historical_performance': {
                    'scoring_impact': -2.0,
                    'sample': 'NFL extreme cold games',
                    'variance': 'MEDIUM'
                },
                'edge_percentage': 2.5,
                'risk_level': 'MEDIUM',
                'stake_recommendation': '2-3% bankroll',
                'weather_details': {
                    'temperature': temperature
                }
            })

        return opportunities

    def _analyze_baseball_weather(
        self,
        weather: Dict,
        sport: str,
        home_team: str,
        away_team: str,
        current_total: Optional[float]
    ) -> List[Dict]:
        """
        Analyze MLB weather impact

        Historical data:
        - Wind >10 mph: Increases scoring
        - Temperature: Hot days favor hitting
        - Rain delays impact
        """
        opportunities = []

        wind_speed = weather.get('wind_speed', 0)
        temperature = weather.get('temperature')
        wind_direction = weather.get('wind_direction', '')

        # Wind impact (blowing out)
        if wind_speed and wind_speed >= 10:
            # Check if wind is blowing out (towards outfield)
            is_blowing_out = 'out' in wind_direction.lower() if wind_direction else False

            opportunities.append({
                'type': 'weather_wind',
                'strategy': 'Weather Impacts (Real-Time)',
                'trigger': f'Wind {wind_speed} mph {wind_direction}',
                'confidence_level': 'MEDIUM' if is_blowing_out else 'LOW',
                'recommendation': {
                    'bet_type': 'total',
                    'side': 'over' if is_blowing_out else 'under',
                    'estimated_impact': 0.5 if is_blowing_out else -0.3,
                    'reasoning': f'Wind {wind_speed} mph {"enhances" if is_blowing_out else "suppresses"} scoring'
                },
                'historical_performance': {
                    'run_impact': 0.5 if is_blowing_out else -0.3,
                    'sample': 'MLB wind impact studies',
                    'variance': 'MEDIUM - Volatility from weather'
                },
                'edge_percentage': 3.0 if is_blowing_out else 2.0,
                'risk_level': 'MEDIUM',
                'stake_recommendation': '2-4% bankroll',
                'weather_details': {
                    'wind_speed': wind_speed,
                    'wind_direction': wind_direction
                }
            })

        # Temperature impact (hot weather)
        if temperature and temperature >= 85:
            opportunities.append({
                'type': 'weather_temperature',
                'strategy': 'Weather Impacts (Real-Time)',
                'trigger': f'Hot weather: {temperature}°F',
                'confidence_level': 'LOW',
                'recommendation': {
                    'bet_type': 'total',
                    'side': 'over',
                    'estimated_impact': 0.3,
                    'reasoning': 'Hot weather (85°F+) historically favors hitters, ball travels farther'
                },
                'historical_performance': {
                    'run_impact': 0.3,
                    'sample': 'MLB hot weather games',
                    'variance': 'MEDIUM'
                },
                'edge_percentage': 2.0,
                'risk_level': 'MEDIUM',
                'stake_recommendation': '2-3% bankroll',
                'weather_details': {
                    'temperature': temperature
                }
            })

        return opportunities

    def _analyze_soccer_weather(
        self,
        weather: Dict,
        sport: str,
        home_team: str,
        away_team: str,
        current_total: Optional[float]
    ) -> List[Dict]:
        """
        Analyze MLS/NCAA Soccer weather impact

        Rain and wet conditions can increase goals (slippery defense)
        or decrease them (ball control issues)
        """
        opportunities = []

        precipitation = weather.get('precipitation', 'none')
        wind_speed = weather.get('wind_speed', 0)

        if precipitation in ['rain', 'heavy_rain']:
            opportunities.append({
                'type': 'weather_precipitation',
                'strategy': 'Weather Impacts (Real-Time)',
                'trigger': f'{precipitation.capitalize()} conditions',
                'confidence_level': 'LOW',
                'recommendation': {
                    'bet_type': 'total',
                    'side': 'over',  # Defensive errors increase in rain
                    'reasoning': 'Wet conditions cause defensive errors, increase goal-scoring opportunities'
                },
                'historical_performance': {
                    'goal_impact': 0.3,
                    'sample': 'MLS rain games',
                    'variance': 'MEDIUM'
                },
                'edge_percentage': 2.5,
                'risk_level': 'MEDIUM',
                'stake_recommendation': '2-3% bankroll',
                'weather_details': {
                    'precipitation': precipitation
                }
            })

        return opportunities

    def _analyze_golf_weather(
        self,
        weather: Dict,
        sport: str,
        current_total: Optional[float]
    ) -> List[Dict]:
        """
        Analyze PGA/NCAA Golf weather impact

        Historical data:
        - Wind +1 mph increases scoring 0.1 strokes/round
        """
        opportunities = []

        wind_speed = weather.get('wind_speed', 0)

        if wind_speed and wind_speed >= 15:
            stroke_impact = (wind_speed - 10) * 0.1  # Estimate

            opportunities.append({
                'type': 'weather_wind',
                'strategy': 'Weather Shifts (Wind/Rain)',
                'trigger': f'Wind {wind_speed} mph',
                'confidence_level': 'MEDIUM',
                'recommendation': {
                    'bet_type': 'round_total',
                    'side': 'over',
                    'estimated_impact': stroke_impact,
                    'reasoning': f'Wind +{wind_speed} mph increases scoring ~{stroke_impact:.1f} strokes/round'
                },
                'historical_performance': {
                    'stroke_impact_per_mph': 0.1,
                    'sample': 'PGA Tour wind studies',
                    'variance': 'HIGH - High weather unpredictability'
                },
                'edge_percentage': 4.0,
                'risk_level': 'HIGH',
                'stake_recommendation': '1-3% bankroll',
                'weather_details': {
                    'wind_speed': wind_speed,
                    'estimated_stroke_increase': round(stroke_impact, 2)
                }
            })

        return opportunities

    def get_weather(self, game_id: str) -> Optional[Dict]:
        """Get cached weather data for a game"""
        return self.weather_cache.get(game_id)

    def clear_weather_cache(self, game_id: Optional[str] = None):
        """Clear weather cache for a game or all games"""
        if game_id:
            if game_id in self.weather_cache:
                del self.weather_cache[game_id]
        else:
            self.weather_cache.clear()
