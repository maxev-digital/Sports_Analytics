"""Storage layer for alert performance tracking using JSON file database"""
import json
import os
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path
import uuid

from models.alert_tracking import (
    TrackedAlert,
    AlertPerformanceStats,
    SettleAlertRequest,
    calculate_alert_profit
)


class AlertStorage:
    """Manages storage of alerts for performance tracking"""

    def __init__(self, data_dir: str = "data/alerts"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.alerts_file = self.data_dir / "tracked_alerts.json"

        # Initialize file if it doesn't exist
        if not self.alerts_file.exists():
            self._write_alerts([])

    def _read_alerts(self) -> List[dict]:
        """Read all alerts from file"""
        try:
            with open(self.alerts_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _write_alerts(self, alerts: List[dict]):
        """Write all alerts to file"""
        with open(self.alerts_file, 'w') as f:
            json.dump(alerts, f, indent=2)

    def create_alert(
        self,
        alert_type: str,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        commence_time: str,
        market_type: str,
        recommended_side: str,
        recommended_odds: float,
        recommended_bookmaker: str,
        confidence: Optional[str] = None,
        edge_percent: Optional[float] = None,
        profit_potential: Optional[float] = None,
        expires_at: Optional[str] = None,
        strategy_details: Optional[dict] = None
    ) -> TrackedAlert:
        """Create a new tracked alert"""
        alert = TrackedAlert(
            id=str(uuid.uuid4()),
            alert_type=alert_type,
            game_id=game_id,
            sport=sport,
            home_team=home_team,
            away_team=away_team,
            commence_time=commence_time,
            market_type=market_type,
            recommended_side=recommended_side,
            recommended_odds=recommended_odds,
            recommended_bookmaker=recommended_bookmaker,
            confidence=confidence,
            edge_percent=edge_percent,
            profit_potential=profit_potential,
            generated_at=datetime.utcnow().isoformat(),
            expires_at=expires_at,
            status='pending',
            strategy_details=strategy_details
        )

        # Save to file
        alerts = self._read_alerts()
        alerts.append(alert.dict())
        self._write_alerts(alerts)

        return alert

    def get_alert(self, alert_id: str) -> Optional[TrackedAlert]:
        """Get a specific alert by ID"""
        alerts = self._read_alerts()
        for alert_data in alerts:
            if alert_data['id'] == alert_id:
                return TrackedAlert(**alert_data)
        return None

    def get_alerts_by_type(
        self,
        alert_type: str,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[TrackedAlert]:
        """Get alerts by type with optional status filter"""
        alerts = self._read_alerts()
        filtered = []

        for alert_data in alerts:
            if alert_data['alert_type'] == alert_type:
                if status is None or alert_data['status'] == status:
                    filtered.append(TrackedAlert(**alert_data))

        # Sort by generated_at (most recent first)
        filtered.sort(key=lambda a: a.generated_at, reverse=True)

        if limit:
            filtered = filtered[:limit]

        return filtered

    def increment_clicks(self, alert_id: str) -> Optional[TrackedAlert]:
        """Increment click counter when user clicks alert"""
        alerts = self._read_alerts()

        for i, alert_data in enumerate(alerts):
            if alert_data['id'] == alert_id:
                alert_data['times_clicked'] = alert_data.get('times_clicked', 0) + 1

                # Save changes
                alerts[i] = alert_data
                self._write_alerts(alerts)

                return TrackedAlert(**alert_data)

        return None

    def increment_bets(self, alert_id: str) -> Optional[TrackedAlert]:
        """Increment bet counter when user places bet from alert"""
        alerts = self._read_alerts()

        for i, alert_data in enumerate(alerts):
            if alert_data['id'] == alert_id:
                alert_data['times_bet'] = alert_data.get('times_bet', 0) + 1

                # Change status to active if still pending
                if alert_data['status'] == 'pending':
                    alert_data['status'] = 'active'

                # Save changes
                alerts[i] = alert_data
                self._write_alerts(alerts)

                return TrackedAlert(**alert_data)

        return None

    def settle_alert(
        self,
        alert_id: str,
        outcome: str,
        actual_result: Optional[str] = None
    ) -> Optional[TrackedAlert]:
        """Settle an alert with outcome"""
        alerts = self._read_alerts()

        for i, alert_data in enumerate(alerts):
            if alert_data['id'] == alert_id:
                # Update alert
                alert_data['outcome'] = outcome
                alert_data['actual_result'] = actual_result
                alert_data['settled_at'] = datetime.utcnow().isoformat()

                # Update status based on outcome
                if outcome == 'push':
                    alert_data['status'] = 'push'
                elif outcome == 'win':
                    alert_data['status'] = 'won'
                else:
                    alert_data['status'] = 'lost'

                # Save changes
                alerts[i] = alert_data
                self._write_alerts(alerts)

                return TrackedAlert(**alert_data)

        return None

    def get_performance_stats(self, alert_type: str) -> AlertPerformanceStats:
        """Calculate performance statistics for an alert type"""
        alerts = self._read_alerts()
        type_alerts = [a for a in alerts if a['alert_type'] == alert_type]

        if not type_alerts:
            return AlertPerformanceStats(
                alert_type=alert_type,
                last_updated=datetime.utcnow().isoformat()
            )

        # Count by status
        total_alerts = len(type_alerts)
        pending_alerts = len([a for a in type_alerts if a['status'] == 'pending'])
        active_alerts = len([a for a in type_alerts if a['status'] == 'active'])
        expired_alerts = len([a for a in type_alerts if a['status'] == 'expired'])

        # Settled alerts (won/lost/push)
        settled_alerts = [a for a in type_alerts if a['status'] in ['won', 'lost', 'push']]
        successful_alerts = len([a for a in settled_alerts if a['status'] == 'won'])
        failed_alerts = len([a for a in settled_alerts if a['status'] == 'lost'])
        push_alerts = len([a for a in settled_alerts if a['status'] == 'push'])

        # Win rate (exclude pushes)
        decisive_alerts = successful_alerts + failed_alerts
        win_rate = (successful_alerts / decisive_alerts * 100) if decisive_alerts > 0 else 0.0

        # Calculate profit (using avg stake of 100 or actual profit_potential)
        total_profit = 0.0
        for alert in settled_alerts:
            if alert.get('profit_potential'):
                # Use stored profit potential if available
                if alert['outcome'] == 'win':
                    total_profit += alert['profit_potential']
                elif alert['outcome'] == 'loss':
                    total_profit -= 100  # Assume $100 stake
            else:
                # Calculate from odds
                profit = calculate_alert_profit(
                    odds=alert['recommended_odds'],
                    stake=100,  # Assume $100 unit
                    outcome=alert['outcome']
                )
                total_profit += profit

        avg_profit = (total_profit / len(settled_alerts)) if settled_alerts else 0.0

        # Engagement metrics
        total_clicks = sum(a.get('times_clicked', 0) for a in type_alerts)
        total_bets = sum(a.get('times_bet', 0) for a in type_alerts)
        click_to_bet_rate = (total_bets / total_clicks * 100) if total_clicks > 0 else 0.0

        return AlertPerformanceStats(
            alert_type=alert_type,
            total_alerts=total_alerts,
            pending_alerts=pending_alerts,
            active_alerts=active_alerts,
            settled_alerts=len(settled_alerts),
            successful_alerts=successful_alerts,
            failed_alerts=failed_alerts,
            push_alerts=push_alerts,
            expired_alerts=expired_alerts,
            win_rate=round(win_rate, 1),
            avg_profit=round(avg_profit, 2),
            total_profit=round(total_profit, 2),
            total_clicks=total_clicks,
            total_bets=total_bets,
            click_to_bet_rate=round(click_to_bet_rate, 1),
            last_updated=datetime.utcnow().isoformat()
        )

    def get_all_performance_stats(self) -> Dict[str, AlertPerformanceStats]:
        """Get performance stats for all alert types"""
        alert_types = [
            'arbitrage', 'steam_move', 'middle', 'goalie_pull',
            'favorite_comeback', 'halftime_tracker', 'momentum_shift',
            'late_line_movement', 'quarter_reversal'
        ]

        return {
            alert_type: self.get_performance_stats(alert_type)
            for alert_type in alert_types
        }

    def expire_old_alerts(self) -> int:
        """Mark alerts as expired if game time has passed and alert wasn't bet"""
        alerts = self._read_alerts()
        expired_count = 0
        now = datetime.utcnow()

        for i, alert_data in enumerate(alerts):
            # Only expire pending alerts
            if alert_data['status'] == 'pending':
                commence_time = datetime.fromisoformat(alert_data['commence_time'].replace('Z', '+00:00'))

                # If game has started and alert wasn't bet on
                if now > commence_time and alert_data.get('times_bet', 0) == 0:
                    alert_data['status'] = 'expired'
                    alerts[i] = alert_data
                    expired_count += 1

        if expired_count > 0:
            self._write_alerts(alerts)

        return expired_count


# Global storage instance
alert_storage = AlertStorage()
