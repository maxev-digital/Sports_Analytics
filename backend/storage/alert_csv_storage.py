"""
Alert CSV Storage Layer
Provides data access functions for alert CSV files
"""
import csv
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal
import logging

logger = logging.getLogger(__name__)

# CSV file paths
TRACKING_DIR = Path(__file__).parent.parent / "data" / "tracking"
ALERTS_LOG = TRACKING_DIR / "alerts_log.csv"
ALERTS_RESULTS_LOG = TRACKING_DIR / "alerts_results_log.csv"
ALERTS_PERFORMANCE_SUMMARY = TRACKING_DIR / "alerts_performance_summary.csv"


class AlertCSVStorage:
    """Storage layer for alert CSV files"""

    @staticmethod
    def get_all_alerts() -> pd.DataFrame:
        """
        Get all alerts from alerts_log.csv

        Returns:
            DataFrame with all alerts
        """
        try:
            if not ALERTS_LOG.exists():
                return pd.DataFrame()

            df = pd.read_csv(ALERTS_LOG)
            return df

        except Exception as e:
            logger.error(f"Error reading alerts log: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def get_all_results() -> pd.DataFrame:
        """
        Get all alert results from alerts_results_log.csv

        Returns:
            DataFrame with all results
        """
        try:
            if not ALERTS_RESULTS_LOG.exists():
                return pd.DataFrame()

            df = pd.read_csv(ALERTS_RESULTS_LOG)
            return df

        except Exception as e:
            logger.error(f"Error reading results log: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def get_alerts_with_results() -> pd.DataFrame:
        """
        Get alerts merged with their results

        Returns:
            DataFrame with alerts and results merged on alert_id
        """
        try:
            alerts_df = AlertCSVStorage.get_all_alerts()
            results_df = AlertCSVStorage.get_all_results()

            if alerts_df.empty:
                return pd.DataFrame()

            if results_df.empty:
                # Return alerts with empty result columns
                return alerts_df

            # Merge on alert_id
            merged = pd.merge(
                alerts_df,
                results_df,
                on='alert_id',
                how='left',
                suffixes=('', '_result')
            )

            return merged

        except Exception as e:
            logger.error(f"Error merging alerts with results: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def get_settled_alerts() -> pd.DataFrame:
        """
        Get only settled alerts (with outcomes)

        Returns:
            DataFrame with settled alerts
        """
        try:
            merged = AlertCSVStorage.get_alerts_with_results()

            if merged.empty:
                return pd.DataFrame()

            # Filter to only rows with outcomes
            settled = merged[merged['outcome'].notna()]

            return settled

        except Exception as e:
            logger.error(f"Error getting settled alerts: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def get_pending_alerts() -> pd.DataFrame:
        """
        Get only pending alerts (no outcomes yet)

        Returns:
            DataFrame with pending alerts
        """
        try:
            alerts_df = AlertCSVStorage.get_all_alerts()

            if alerts_df.empty:
                return pd.DataFrame()

            # Filter to pending status
            pending = alerts_df[alerts_df['status'] == 'pending']

            return pending

        except Exception as e:
            logger.error(f"Error getting pending alerts: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def get_alerts_by_type(alert_type: str) -> pd.DataFrame:
        """
        Get alerts filtered by type

        Args:
            alert_type: Alert type to filter by

        Returns:
            DataFrame with filtered alerts
        """
        try:
            merged = AlertCSVStorage.get_alerts_with_results()

            if merged.empty:
                return pd.DataFrame()

            filtered = merged[merged['alert_type'] == alert_type]

            return filtered

        except Exception as e:
            logger.error(f"Error getting alerts by type: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def get_alerts_by_sport(sport: str) -> pd.DataFrame:
        """
        Get alerts filtered by sport

        Args:
            sport: Sport to filter by

        Returns:
            DataFrame with filtered alerts
        """
        try:
            merged = AlertCSVStorage.get_alerts_with_results()

            if merged.empty:
                return pd.DataFrame()

            filtered = merged[merged['sport'] == sport]

            return filtered

        except Exception as e:
            logger.error(f"Error getting alerts by sport: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def get_alerts_by_confidence(confidence: str) -> pd.DataFrame:
        """
        Get alerts filtered by confidence level

        Args:
            confidence: Confidence level (HIGH, MEDIUM, LOW)

        Returns:
            DataFrame with filtered alerts
        """
        try:
            merged = AlertCSVStorage.get_alerts_with_results()

            if merged.empty:
                return pd.DataFrame()

            filtered = merged[merged['confidence'] == confidence]

            return filtered

        except Exception as e:
            logger.error(f"Error getting alerts by confidence: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def get_alerts_by_date_range(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get alerts within a date range

        Args:
            start_date: Start date (YYYY-MM-DD) or None
            end_date: End date (YYYY-MM-DD) or None
            days: Number of days back from today (if start/end not specified)

        Returns:
            DataFrame with filtered alerts
        """
        try:
            merged = AlertCSVStorage.get_alerts_with_results()

            if merged.empty:
                return pd.DataFrame()

            # Convert date_generated to datetime
            merged['date_generated'] = pd.to_datetime(merged['date_generated'])

            # Determine date range
            if days is not None:
                end = datetime.now()
                start = end - timedelta(days=days)
            else:
                start = pd.to_datetime(start_date) if start_date else pd.to_datetime('1900-01-01')
                end = pd.to_datetime(end_date) if end_date else datetime.now()

            # Filter
            filtered = merged[
                (merged['date_generated'] >= start) &
                (merged['date_generated'] <= end)
            ]

            return filtered

        except Exception as e:
            logger.error(f"Error getting alerts by date range: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def calculate_performance_summary() -> Dict[str, Dict]:
        """
        Calculate performance summary for all alert types

        Returns:
            Dictionary with performance metrics by alert type
        """
        try:
            settled = AlertCSVStorage.get_settled_alerts()

            if settled.empty:
                return {}

            summary = {}

            # Get unique alert types
            alert_types = settled['alert_type'].unique()

            for alert_type in alert_types:
                type_alerts = settled[settled['alert_type'] == alert_type]

                total = len(type_alerts)
                wins = len(type_alerts[type_alerts['outcome'] == 'won'])
                losses = len(type_alerts[type_alerts['outcome'] == 'lost'])
                pushes = len(type_alerts[type_alerts['outcome'] == 'push'])

                win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

                # Calculate total profit
                total_profit = type_alerts['profit_loss'].sum()

                # Calculate ROI
                # ROI = (total profit / total bets) * 100
                roi = (total_profit / total) * 100 if total > 0 else 0

                # Calculate average odds
                avg_odds = type_alerts['recommended_odds'].mean()

                summary[alert_type] = {
                    'total_alerts': total,
                    'settled_alerts': total,
                    'wins': wins,
                    'losses': losses,
                    'pushes': pushes,
                    'win_rate': round(win_rate, 1),
                    'roi': round(roi, 1),
                    'total_profit': round(total_profit, 2),
                    'avg_odds': round(avg_odds, 0) if pd.notna(avg_odds) else 0
                }

            return summary

        except Exception as e:
            logger.error(f"Error calculating performance summary: {str(e)}")
            return {}

    @staticmethod
    def calculate_performance_by_sport() -> Dict[str, Dict]:
        """
        Calculate performance summary by sport

        Returns:
            Dictionary with performance metrics by sport
        """
        try:
            settled = AlertCSVStorage.get_settled_alerts()

            if settled.empty:
                return {}

            summary = {}

            # Get unique sports
            sports = settled['sport'].unique()

            for sport in sports:
                sport_alerts = settled[settled['sport'] == sport]

                total = len(sport_alerts)
                wins = len(sport_alerts[sport_alerts['outcome'] == 'won'])
                losses = len(sport_alerts[sport_alerts['outcome'] == 'lost'])
                pushes = len(sport_alerts[sport_alerts['outcome'] == 'push'])

                win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
                total_profit = sport_alerts['profit_loss'].sum()
                roi = (total_profit / total) * 100 if total > 0 else 0

                summary[sport] = {
                    'total_alerts': total,
                    'wins': wins,
                    'losses': losses,
                    'pushes': pushes,
                    'win_rate': round(win_rate, 1),
                    'roi': round(roi, 1),
                    'total_profit': round(total_profit, 2)
                }

            return summary

        except Exception as e:
            logger.error(f"Error calculating performance by sport: {str(e)}")
            return {}

    @staticmethod
    def calculate_performance_by_confidence() -> Dict[str, Dict]:
        """
        Calculate performance summary by confidence level

        Returns:
            Dictionary with performance metrics by confidence
        """
        try:
            settled = AlertCSVStorage.get_settled_alerts()

            if settled.empty:
                return {}

            summary = {}

            # Get unique confidence levels
            confidence_levels = settled['confidence'].unique()

            for confidence in confidence_levels:
                if pd.isna(confidence):
                    continue

                conf_alerts = settled[settled['confidence'] == confidence]

                total = len(conf_alerts)
                wins = len(conf_alerts[conf_alerts['outcome'] == 'won'])
                losses = len(conf_alerts[conf_alerts['outcome'] == 'lost'])
                pushes = len(conf_alerts[conf_alerts['outcome'] == 'push'])

                win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
                total_profit = conf_alerts['profit_loss'].sum()
                roi = (total_profit / total) * 100 if total > 0 else 0

                summary[confidence] = {
                    'total_alerts': total,
                    'wins': wins,
                    'losses': losses,
                    'pushes': pushes,
                    'win_rate': round(win_rate, 1),
                    'roi': round(roi, 1),
                    'total_profit': round(total_profit, 2)
                }

            return summary

        except Exception as e:
            logger.error(f"Error calculating performance by confidence: {str(e)}")
            return {}

    @staticmethod
    def get_daily_performance(days: int = 30) -> pd.DataFrame:
        """
        Get daily performance metrics

        Args:
            days: Number of days to include

        Returns:
            DataFrame with daily performance
        """
        try:
            settled = AlertCSVStorage.get_settled_alerts()

            if settled.empty:
                return pd.DataFrame()

            # Filter to date range
            settled['date_generated'] = pd.to_datetime(settled['date_generated'])
            cutoff_date = datetime.now() - timedelta(days=days)
            settled = settled[settled['date_generated'] >= cutoff_date]

            if settled.empty:
                return pd.DataFrame()

            # Group by date
            daily = settled.groupby('date_generated').agg({
                'alert_id': 'count',
                'profit_loss': 'sum',
                'outcome': lambda x: (x == 'won').sum()
            }).reset_index()

            daily.columns = ['date', 'total_alerts', 'profit', 'wins']
            daily['win_rate'] = (daily['wins'] / daily['total_alerts'] * 100).round(1)

            # Calculate cumulative profit
            daily['cumulative_profit'] = daily['profit'].cumsum()

            return daily

        except Exception as e:
            logger.error(f"Error calculating daily performance: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def save_performance_summary():
        """
        Save performance summary to CSV cache file
        """
        try:
            summary = AlertCSVStorage.calculate_performance_summary()

            if not summary:
                logger.warning("No performance data to save")
                return

            # Get all alerts to calculate pending count
            all_alerts_df = AlertCSVStorage.get_all_alerts()

            rows = []
            for alert_type, metrics in summary.items():
                # Count pending for this type
                pending_count = len(all_alerts_df[
                    (all_alerts_df['alert_type'] == alert_type) &
                    (all_alerts_df['status'] == 'pending')
                ]) if not all_alerts_df.empty else 0

                rows.append({
                    'alert_type': alert_type,
                    'total_alerts': metrics['total_alerts'] + pending_count,
                    'settled_alerts': metrics['settled_alerts'],
                    'pending_alerts': pending_count,
                    'wins': metrics['wins'],
                    'losses': metrics['losses'],
                    'pushes': metrics['pushes'],
                    'win_rate': metrics['win_rate'],
                    'roi': metrics['roi'],
                    'total_profit': metrics['total_profit'],
                    'avg_odds': metrics['avg_odds'],
                    'last_updated': datetime.now().isoformat()
                })

            # Write to CSV
            df = pd.DataFrame(rows)
            df.to_csv(ALERTS_PERFORMANCE_SUMMARY, index=False)

            logger.info(f"✅ Saved performance summary for {len(rows)} alert types")

        except Exception as e:
            logger.error(f"Error saving performance summary: {str(e)}")


if __name__ == "__main__":
    # Test storage functions
    print("Testing Alert CSV Storage...")

    storage = AlertCSVStorage()

    print("\n1. All alerts:")
    all_alerts = storage.get_all_alerts()
    print(f"Total alerts: {len(all_alerts)}")

    print("\n2. Settled alerts:")
    settled = storage.get_settled_alerts()
    print(f"Settled alerts: {len(settled)}")

    print("\n3. Pending alerts:")
    pending = storage.get_pending_alerts()
    print(f"Pending alerts: {len(pending)}")

    print("\n4. Performance summary:")
    summary = storage.calculate_performance_summary()
    for alert_type, metrics in summary.items():
        print(f"{alert_type}: {metrics['wins']}-{metrics['losses']}-{metrics['pushes']} | "
              f"Win Rate: {metrics['win_rate']}% | ROI: {metrics['roi']}%")

    print("\n5. Performance by sport:")
    sport_summary = storage.calculate_performance_by_sport()
    for sport, metrics in sport_summary.items():
        print(f"{sport}: Win Rate: {metrics['win_rate']}% | ROI: {metrics['roi']}%")

    print("\n6. Saving performance summary...")
    storage.save_performance_summary()
    print("Done!")
