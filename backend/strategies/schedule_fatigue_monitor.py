"""
Schedule Fatigue Monitor
Detects back-to-back situations and rest advantages across NBA, NFL, NHL
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import asyncio
import httpx

logger = logging.getLogger(__name__)


@dataclass
class FatigueAlert:
    """Alert for schedule fatigue advantage"""
    id: str
    game_id: str
    sport: str
    home_team: str
    away_team: str
    commence_time: datetime

    # Fatigue details
    fatigue_type: str  # "b2b_vs_rested", "3in4", "travel_fatigue", "rest_advantage"
    favored_side: str  # "home" or "away"
    home_rest_days: int
    away_rest_days: int
    rest_differential: int

    # Additional context
    home_is_b2b: bool
    away_is_b2b: bool
    home_travel_distance: Optional[float]
    away_travel_distance: Optional[float]

    # Confidence
    confidence: float  # 0.0 to 1.0
    confidence_level: str  # HIGH, MEDIUM, LOW
    edge_percent: float

    # Analysis
    reasoning: str
    key_factors: List[str]

    timestamp: datetime


class ScheduleFatigueMonitor:
    """
    Monitors schedule situations that create betting edges:
    - Back-to-back vs rested team
    - 3-in-4 nights (NBA/NHL)
    - Extended rest (4+ days)
    - Cross-country travel on B2B
    """

    def __init__(self, odds_api_key: str):
        self.api_key = odds_api_key
        self.base_url = "https://api.the-odds-api.com/v4"

        # Track team schedules
        self.team_schedules: Dict[str, List[Dict]] = {}

        # Fatigue thresholds by sport
        self.sport_config = {
            'basketball_nba': {
                'b2b_handicap': 2.5,  # Points disadvantage on B2B
                '3in4_handicap': 1.5,  # Additional handicap for 3-in-4
                'rest_advantage': 1.0,  # Points per extra rest day (capped)
                'max_rest_advantage': 3.0,
                'travel_fatigue_miles': 1500,  # Cross-country threshold
                'min_edge': 2.0
            },
            'icehockey_nhl': {
                'b2b_handicap': 0.3,  # Goals disadvantage on B2B
                '3in4_handicap': 0.2,
                'rest_advantage': 0.15,
                'max_rest_advantage': 0.5,
                'travel_fatigue_miles': 1500,
                'min_edge': 0.25
            },
            'americanfootball_nfl': {
                'short_week_handicap': 3.0,  # Thursday game disadvantage
                'rest_advantage': 1.5,
                'max_rest_advantage': 3.0,
                'min_edge': 2.0
            }
        }

        # Team locations for travel distance (sample - would need full DB)
        self.team_locations = {
            # NBA
            'Los Angeles Lakers': {'lat': 34.0430, 'lon': -118.2673},
            'Miami Heat': {'lat': 25.7814, 'lon': -80.1870},
            'Boston Celtics': {'lat': 42.3662, 'lon': -71.0621},
            # NHL
            'Tampa Bay Lightning': {'lat': 27.9427, 'lon': -82.4517},
            'Vancouver Canucks': {'lat': 49.2778, 'lon': -123.1089},
            # Add more as needed
        }

    async def fetch_schedule(self, sport: str) -> Optional[List[Dict]]:
        """Fetch upcoming schedule from Odds API"""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/sports/{sport}/odds"
                params = {
                    'apiKey': self.api_key,
                    'regions': 'us',
                    'markets': 'h2h',
                    'oddsFormat': 'american',
                }

                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()

                return response.json()
        except Exception as e:
            logger.error(f"Error fetching schedule for {sport}: {e}")
            return None

    def _calculate_travel_distance(self, team1: str, team2: str) -> Optional[float]:
        """Calculate approximate travel distance between teams (miles)"""
        if team1 not in self.team_locations or team2 not in self.team_locations:
            return None

        # Simple Haversine formula
        from math import radians, sin, cos, sqrt, atan2

        loc1 = self.team_locations[team1]
        loc2 = self.team_locations[team2]

        lat1, lon1 = radians(loc1['lat']), radians(loc1['lon'])
        lat2, lon2 = radians(loc2['lat']), radians(loc2['lon'])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        # Earth radius in miles
        distance = 3959 * c
        return distance

    def _get_team_rest_days(self, team: str, game_time: datetime, sport: str) -> int:
        """Calculate rest days for a team before this game"""
        # This is a simplified version - in production, would query real schedule data
        # For now, return placeholder that would be replaced with actual API calls

        # Would check team_schedules[team] for last game before game_time
        # For demo purposes, assume some teams are on B2B

        # Placeholder logic - would be replaced with real schedule tracking
        if sport not in self.team_schedules:
            self.team_schedules[sport] = {}

        if team not in self.team_schedules[sport]:
            return 2  # Default 2 days rest

        # In production: calculate from actual last game
        return 2

    def _analyze_fatigue_situation(
        self,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        commence_time: datetime,
        home_rest: int,
        away_rest: int
    ) -> Optional[FatigueAlert]:
        """Analyze a game for fatigue-based betting edges"""

        config = self.sport_config.get(sport)
        if not config:
            return None

        rest_diff = abs(home_rest - away_rest)

        # Determine if there's a significant fatigue situation
        is_b2b_situation = (home_rest == 0 and away_rest >= 2) or (away_rest == 0 and home_rest >= 2)
        is_3in4_situation = (home_rest == 1 and away_rest >= 3) or (away_rest == 1 and home_rest >= 3)
        is_rest_advantage = rest_diff >= 2

        if not (is_b2b_situation or is_3in4_situation or is_rest_advantage):
            return None

        # Calculate edge
        edge = 0.0
        confidence = 0.5
        key_factors = []

        # B2B vs rested
        if home_rest == 0 and away_rest >= 2:
            edge = config['b2b_handicap']
            favored_side = 'away'
            fatigue_type = 'b2b_vs_rested'
            key_factors.append('Home team on back-to-back')
            key_factors.append('Away team rested')
            confidence += 0.2
        elif away_rest == 0 and home_rest >= 2:
            edge = config['b2b_handicap']
            favored_side = 'home'
            fatigue_type = 'b2b_vs_rested'
            key_factors.append('Away team on back-to-back')
            key_factors.append('Home team rested')
            confidence += 0.2
        else:
            # Rest advantage calculation
            rest_edge = min(rest_diff * config['rest_advantage'], config['max_rest_advantage'])
            edge = rest_edge
            favored_side = 'home' if home_rest > away_rest else 'away'
            fatigue_type = 'rest_advantage'
            key_factors.append(f'{rest_diff} day rest advantage for {favored_side}')
            confidence += 0.1

        # 3-in-4 additional penalty
        if is_3in4_situation:
            if '3in4_handicap' in config:
                edge += config['3in4_handicap']
                key_factors.append('3-in-4 nights situation')
                confidence += 0.1

        # Travel fatigue (if available)
        travel_dist = None
        if sport in ['basketball_nba', 'icehockey_nhl']:
            if home_rest == 0:  # Home team on B2B
                # Check if they traveled far for previous game
                travel_dist = self._calculate_travel_distance(home_team, away_team)
                if travel_dist and travel_dist > config['travel_fatigue_miles']:
                    edge += 1.0
                    key_factors.append(f'Cross-country travel ({int(travel_dist)} miles)')
                    confidence += 0.1

        # Only create alert if edge exceeds minimum
        if edge < config['min_edge']:
            return None

        # Confidence level
        confidence = min(confidence, 1.0)
        if confidence >= 0.7:
            confidence_level = 'HIGH'
        elif confidence >= 0.5:
            confidence_level = 'MEDIUM'
        else:
            confidence_level = 'LOW'

        # Build reasoning
        if fatigue_type == 'b2b_vs_rested':
            reasoning = f"{favored_side.title()} team has significant rest advantage. "
            reasoning += f"{'Home' if favored_side == 'away' else 'Away'} team playing back-to-back "
            reasoning += f"while {favored_side} team has {max(home_rest, away_rest)} days rest. "
            reasoning += "Historical data shows teams on B2B cover at 45% against rested opponents."
        else:
            reasoning = f"{favored_side.title()} team has {rest_diff} day rest advantage. "
            reasoning += "Well-rested teams historically perform better, especially late in games."

        alert_id = f"fatigue_{game_id}_{favored_side}_{int(datetime.now().timestamp())}"

        return FatigueAlert(
            id=alert_id,
            game_id=game_id,
            sport=sport,
            home_team=home_team,
            away_team=away_team,
            commence_time=commence_time,
            fatigue_type=fatigue_type,
            favored_side=favored_side,
            home_rest_days=home_rest,
            away_rest_days=away_rest,
            rest_differential=rest_diff,
            home_is_b2b=(home_rest == 0),
            away_is_b2b=(away_rest == 0),
            home_travel_distance=travel_dist if favored_side == 'away' else None,
            away_travel_distance=travel_dist if favored_side == 'home' else None,
            confidence=confidence,
            confidence_level=confidence_level,
            edge_percent=edge,
            reasoning=reasoning,
            key_factors=key_factors,
            timestamp=datetime.now()
        )

    async def scan_sport_for_fatigue(self, sport: str) -> List[FatigueAlert]:
        """Scan a sport for schedule fatigue situations"""
        alerts = []

        try:
            games = await self.fetch_schedule(sport)
            if not games:
                return alerts

            for game in games:
                game_id = game.get('id')
                home_team = game.get('home_team')
                away_team = game.get('away_team')
                commence_time = datetime.fromisoformat(game.get('commence_time').replace('Z', '+00:00'))

                # Get rest days for each team
                home_rest = self._get_team_rest_days(home_team, commence_time, sport)
                away_rest = self._get_team_rest_days(away_team, commence_time, sport)

                # Analyze for fatigue edge
                alert = self._analyze_fatigue_situation(
                    game_id, sport, home_team, away_team, commence_time,
                    home_rest, away_rest
                )

                if alert:
                    alerts.append(alert)
                    logger.info(
                        f"Fatigue alert: {alert.fatigue_type} - "
                        f"{away_team} @ {home_team} - "
                        f"Favor {alert.favored_side} ({alert.confidence_level} confidence, "
                        f"{alert.edge_percent:.1f} edge)"
                    )

        except Exception as e:
            logger.error(f"Error scanning {sport} for fatigue: {e}")

        return alerts

    async def monitor_loop(self, sports: List[str], interval_seconds: int = 3600):
        """
        Continuous monitoring loop for schedule fatigue

        Args:
            sports: List of sport keys to monitor
            interval_seconds: Seconds between scans (default 3600 = 1 hour)
        """
        logger.info(f"Starting schedule fatigue monitor for sports: {sports}")

        while True:
            try:
                all_alerts = []

                for sport in sports:
                    alerts = await self.scan_sport_for_fatigue(sport)
                    all_alerts.extend(alerts)

                if all_alerts:
                    logger.info(
                        f"Schedule fatigue scan complete: {len(all_alerts)} alerts detected"
                    )
                else:
                    logger.debug("Schedule fatigue scan complete: No alerts")

                # Wait before next scan
                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Error in schedule fatigue monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)


# Global instance
fatigue_monitor = None


def get_fatigue_monitor(api_key: str) -> ScheduleFatigueMonitor:
    """Get or create schedule fatigue monitor instance"""
    global fatigue_monitor
    if fatigue_monitor is None:
        fatigue_monitor = ScheduleFatigueMonitor(api_key)
    return fatigue_monitor
