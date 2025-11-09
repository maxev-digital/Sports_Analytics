"""
Weather API Client
Fetches weather data for NFL stadiums
"""

import requests
import os
from typing import Optional
from strategies.weather_strategy import WeatherConditions
import logging

logger = logging.getLogger(__name__)


class WeatherClient:
    """
    Weather client that uses OpenWeatherMap API

    Free tier: 1000 calls/day
    Sign up: https://openweathermap.org/api
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENWEATHER_API_KEY', '')
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.use_mock = not self.api_key  # Use mock data if no API key

    def get_weather(self, lat: float, lon: float) -> Optional[WeatherConditions]:
        """
        Get current weather for a location

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            WeatherConditions or None if error
        """
        if self.use_mock:
            return self._get_mock_weather(lat, lon)

        try:
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'imperial'  # Fahrenheit
            }

            response = requests.get(self.base_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            return self._parse_weather_response(data)

        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            return self._get_mock_weather(lat, lon)  # Fallback to mock

    def _parse_weather_response(self, data: dict) -> WeatherConditions:
        """Parse OpenWeatherMap API response"""
        main = data.get('main', {})
        wind = data.get('wind', {})
        weather = data.get('weather', [{}])[0]
        rain = data.get('rain', {})
        snow = data.get('snow', {})

        # Determine precipitation
        precipitation = None
        precip_chance = 0.0
        if snow:
            precipitation = "snow"
            precip_chance = 100.0
        elif rain:
            precipitation = "rain"
            precip_chance = 100.0

        # Wind direction (degrees to cardinal)
        wind_deg = wind.get('deg', 0)
        wind_direction = self._degrees_to_cardinal(wind_deg)

        return WeatherConditions(
            temperature=main.get('temp', 70.0),
            wind_speed=wind.get('speed', 0.0),
            precipitation=precipitation,
            precipitation_chance=precip_chance,
            humidity=main.get('humidity', 50.0),
            conditions=weather.get('main', 'Clear'),
            wind_direction=wind_direction
        )

    def _degrees_to_cardinal(self, degrees: float) -> str:
        """Convert wind degrees to cardinal direction"""
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                     'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = round(degrees / 22.5) % 16
        return directions[index]

    def _get_mock_weather(self, lat: float, lon: float) -> WeatherConditions:
        """
        Mock weather data for demo purposes

        Returns reasonable weather based on location and season
        """
        import datetime

        month = datetime.datetime.now().month

        # Northern cities (Buffalo, Green Bay, etc.)
        if lat > 42.0:
            if month in [12, 1, 2]:  # Winter
                temp = 25.0
                wind = 18.0
                precip = "snow" if month in [1, 2] else None
            elif month in [3, 4, 11]:  # Shoulder seasons
                temp = 45.0
                wind = 14.0
                precip = "rain" if month == 11 else None
            else:  # Summer
                temp = 75.0
                wind = 8.0
                precip = None
        # Southern cities (Miami, etc.)
        elif lat < 30.0:
            if month in [12, 1, 2]:
                temp = 65.0
                wind = 10.0
                precip = None
            elif month in [6, 7, 8, 9]:  # Hot/hurricane season
                temp = 88.0
                wind = 12.0
                precip = "rain" if month in [8, 9] else None
            else:
                temp = 78.0
                wind = 8.0
                precip = None
        # Mid-latitude
        else:
            if month in [12, 1, 2]:
                temp = 35.0
                wind = 15.0
                precip = "snow" if month in [1, 2] else None
            elif month in [6, 7, 8]:
                temp = 82.0
                wind = 9.0
                precip = None
            else:
                temp = 58.0
                wind = 11.0
                precip = "rain" if month in [3, 4, 10, 11] else None

        return WeatherConditions(
            temperature=temp,
            wind_speed=wind,
            precipitation=precip,
            precipitation_chance=60.0 if precip else 0.0,
            humidity=65.0,
            conditions=precip.capitalize() if precip else "Clear",
            wind_direction="W"
        )


# Example usage
if __name__ == "__main__":
    client = WeatherClient()

    # Test Buffalo in winter
    weather = client.get_weather(42.7738, -78.7870)
    print(f"Buffalo Weather:")
    print(f"  Temp: {weather.temperature}°F")
    print(f"  Wind: {weather.wind_speed} MPH {weather.wind_direction}")
    print(f"  Conditions: {weather.conditions}")
    if weather.precipitation:
        print(f"  Precipitation: {weather.precipitation} ({weather.precipitation_chance:.0f}%)")
