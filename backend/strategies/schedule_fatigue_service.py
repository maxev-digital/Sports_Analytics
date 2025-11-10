"""
Schedule Fatigue Monitor Service
Async monitoring service that wraps ScheduleFatigueMonitor and integrates with alert system
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from strategies.schedule_fatigue_monitor import ScheduleFatigueMonitor, FatigueAlert, get_fatigue_monitor
from storage.alert_storage import alert_storage
from alert_monitor import serialize_datetime_dict

logger = logging.getLogger(__name__)


class ScheduleFatigueService:
    """
    Async service that monitors for schedule fatigue situations
    Integrates ScheduleFatigueMonitor with alert storage and notification system
    """

    def __init__(self, odds_api_key: str):
        self.api_key = odds_api_key
        self.monitor = get_fatigue_monitor(odds_api_key)

    def _store_fatigue_alert(self, alert: FatigueAlert, sport: str) -> Optional[str]:
        """Store fatigue alert in database"""
        try:
            # Serialize alert to dict
            alert_dict = {
                'id': alert.id,
                'game_id': alert.game_id,
                'sport': alert.sport,
                'home_team': alert.home_team,
                'away_team': alert.away_team,
                'commence_time': alert.commence_time.isoformat() if hasattr(alert.commence_time, 'isoformat') else str(alert.commence_time),
                'fatigue_type': alert.fatigue_type,
                'favored_side': alert.favored_side,
                'home_rest_days': alert.home_rest_days,
                'away_rest_days': alert.away_rest_days,
                'rest_differential': alert.rest_differential,
                'home_is_b2b': alert.home_is_b2b,
                'away_is_b2b': alert.away_is_b2b,
                'home_travel_distance': alert.home_travel_distance,
                'away_travel_distance': alert.away_travel_distance,
                'confidence': alert.confidence,
                'confidence_level': alert.confidence_level,
                'edge_percent': alert.edge_percent,
                'reasoning': alert.reasoning,
                'key_factors': alert.key_factors,
                'timestamp': alert.timestamp.isoformat() if hasattr(alert.timestamp, 'isoformat') else str(alert.timestamp)
            }

            # Serialize datetime objects
            alert_dict = serialize_datetime_dict(alert_dict)

            # Determine recommended side
            if alert.favored_side == 'home':
                recommended_side = f"{alert.home_team} (Home)"
            else:
                recommended_side = f"{alert.away_team} (Away)"

            # Store in alert_storage
            tracked_alert = alert_storage.create_alert(
                alert_type='schedule_fatigue',
                game_id=alert.game_id,
                sport=sport,
                home_team=alert.home_team,
                away_team=alert.away_team,
                commence_time=alert.commence_time.isoformat() if hasattr(alert.commence_time, 'isoformat') else str(alert.commence_time),
                market_type='fatigue_advantage',
                recommended_side=recommended_side,
                recommended_odds=None,
                recommended_bookmaker='Schedule Advantage',
                edge_percent=alert.edge_percent,
                profit_potential=None,
                expires_at=None,
                strategy_details=alert_dict
            )

            return tracked_alert.id
        except Exception as e:
            logger.error(f"Error storing fatigue alert: {e}")
            return None

    async def scan_sports_for_fatigue(self, sports: List[str]) -> List[FatigueAlert]:
        """Scan multiple sports for fatigue situations"""
        all_alerts = []

        for sport in sports:
            try:
                alerts = await self.monitor.scan_sport_for_fatigue(sport)

                # Store each alert
                for alert in alerts:
                    alert_id = self._store_fatigue_alert(alert, sport)
                    if alert_id:
                        all_alerts.append(alert)

            except Exception as e:
                logger.error(f"Error scanning {sport} for fatigue: {e}")

        return all_alerts

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
                alerts = await self.scan_sports_for_fatigue(sports)

                if alerts:
                    logger.info(
                        f"Schedule fatigue scan complete: {len(alerts)} alerts detected"
                    )

                    # Log alert details
                    for alert in alerts:
                        logger.info(
                            f"  Fatigue Alert: {alert.fatigue_type} - "
                            f"{alert.away_team} @ {alert.home_team} - "
                            f"Favor {alert.favored_side} "
                            f"({alert.confidence_level} confidence, {alert.edge_percent:.1f} edge)"
                        )
                else:
                    logger.debug("Schedule fatigue scan complete: No alerts")

                # Wait before next scan
                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Error in schedule fatigue monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)


# Global instance
fatigue_service = None


def get_fatigue_service(api_key: str) -> ScheduleFatigueService:
    """Get or create schedule fatigue service instance"""
    global fatigue_service
    if fatigue_service is None:
        fatigue_service = ScheduleFatigueService(api_key)
    return fatigue_service
