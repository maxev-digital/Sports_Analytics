"""
Live Regression-to-Mean Monitor

Continuously monitors live odds and detects regression-to-mean opportunities
Integrates with existing odds scraping infrastructure
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import asyncio
import json
import os

from regression_to_mean_totals import RegressionToMeanStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LiveRegressionMonitor:
    """
    Monitors live games for regression-to-mean betting opportunities
    """

    def __init__(
        self,
        strategy: RegressionToMeanStrategy,
        check_interval: int = 30,  # Check every 30 seconds
        output_dir: str = "backend/data/alerts"
    ):
        """
        Args:
            strategy: RegressionToMeanStrategy instance
            check_interval: Seconds between checks
            output_dir: Directory to save alerts
        """
        self.strategy = strategy
        self.check_interval = check_interval
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.active_alerts = {}  # Track alerts to avoid duplicates
        self.games_cache = {}    # Cache game predictions
        self.alert_history = []  # Store all alerts

    def load_live_games(self) -> List[Dict]:
        """
        Load current live games from odds API / database

        In production, this would query:
        - backend/data/odds/live_ncaab_odds.json
        - Or hit live odds API directly
        - Or query database for in-progress games

        Returns list of game dictionaries with:
        - game_id
        - home_team, away_team
        - game_status (live, pregame, final)
        - current_score (if live)
        - time_remaining
        - team stats (from KenPom or database)
        """

        # Example implementation - replace with actual data source
        live_games_path = "backend/data/odds/live_ncaab_odds.json"

        if not os.path.exists(live_games_path):
            logger.warning(f"Live odds file not found: {live_games_path}")
            return []

        with open(live_games_path, 'r') as f:
            odds_data = json.load(f)

        games = []
        for game_data in odds_data.get('games', []):
            # Only process live games
            if game_data.get('status') != 'live':
                continue

            # Load team stats (from KenPom or database)
            home_stats = self._load_team_stats(game_data['home_team'])
            away_stats = self._load_team_stats(game_data['away_team'])

            if not home_stats or not away_stats:
                continue

            # Build game dictionary
            game = {
                'game_id': game_data['game_id'],
                'home_team': game_data['home_team'],
                'away_team': game_data['away_team'],
                'game_status': 'live',
                'home_score': game_data.get('home_score'),
                'away_score': game_data.get('away_score'),
                'time_remaining': game_data.get('time_remaining'),
                'pregame_total': game_data.get('pregame_total'),

                # Team stats for feature engineering
                'home_adj_em': home_stats['AdjEM'],
                'away_adj_em': away_stats['AdjEM'],
                'home_off_eff': home_stats['AdjOffEff'],
                'away_off_eff': away_stats['AdjOffEff'],
                'home_def_eff': home_stats['AdjDefEff'],
                'away_def_eff': away_stats['AdjDefEff'],
                'home_tempo': home_stats['AdjTempo'],
                'away_tempo': away_stats['AdjTempo'],
            }

            games.append(game)

        logger.info(f"Loaded {len(games)} live games")
        return games

    def load_live_totals(self, game_id: str) -> Dict[str, float]:
        """
        Load current live totals from all tracked bookmakers

        Args:
            game_id: Game identifier

        Returns:
            Dict of {bookmaker: live_total}
        """

        # Example implementation - replace with actual data source
        live_odds_path = f"backend/data/odds/live_totals/{game_id}.json"

        if not os.path.exists(live_odds_path):
            # Fallback: query live odds API
            return self._fetch_live_totals_from_api(game_id)

        with open(live_odds_path, 'r') as f:
            odds_data = json.load(f)

        live_totals = {}
        for book_data in odds_data.get('bookmakers', []):
            bookmaker = book_data['name']
            total = book_data.get('live_total')

            if total:
                live_totals[bookmaker] = float(total)

        return live_totals

    def _fetch_live_totals_from_api(self, game_id: str) -> Dict[str, float]:
        """
        Fetch live totals directly from odds API

        This is a placeholder - implement actual API integration
        """
        # TODO: Integrate with The Odds API or other live odds provider
        # Example: https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds/
        logger.warning(f"API fetch not implemented for game {game_id}")
        return {}

    def _load_team_stats(self, team_name: str) -> Dict:
        """
        Load team's KenPom stats from database or cache

        Returns KenPom stats: AdjEM, AdjOffEff, AdjDefEff, AdjTempo
        """

        # Example implementation - replace with actual database query
        kenpom_path = "backend/data/raw/ncaab/kenpom_latest.csv"

        if not os.path.exists(kenpom_path):
            logger.warning(f"KenPom data not found: {kenpom_path}")
            return None

        import pandas as pd
        df = pd.read_csv(kenpom_path)

        team_data = df[df['Team'] == team_name]

        if len(team_data) == 0:
            logger.warning(f"Team not found in KenPom: {team_name}")
            return None

        stats = {
            'AdjEM': team_data['AdjEM'].iloc[0],
            'AdjOffEff': team_data['AdjOff'].iloc[0],
            'AdjDefEff': team_data['AdjDef'].iloc[0],
            'AdjTempo': team_data['AdjTempo'].iloc[0]
        }

        return stats

    def check_game(self, game: Dict) -> List[Dict]:
        """
        Check a single game for regression opportunities

        Args:
            game: Game dictionary with team stats

        Returns:
            List of alert dictionaries
        """
        game_id = game['game_id']

        # Load live totals from all books
        live_totals = self.load_live_totals(game_id)

        if not live_totals:
            logger.info(f"No live totals available for {game_id}")
            return []

        # Check for opportunities
        alerts = self.strategy.analyze_game(
            game_features=game,
            live_totals=live_totals,
            pregame_total=game.get('pregame_total')
        )

        # Filter out duplicate alerts (same game + book + direction within 5 minutes)
        new_alerts = []
        for alert in alerts:
            alert_key = f"{game_id}_{alert['bookmaker']}_{alert['direction']}"

            # Check if we recently alerted on this
            if alert_key in self.active_alerts:
                last_alert_time = self.active_alerts[alert_key]
                time_since_alert = (datetime.now() - last_alert_time).total_seconds()

                if time_since_alert < 300:  # 5 minutes
                    continue  # Skip duplicate

            # New alert
            self.active_alerts[alert_key] = datetime.now()
            new_alerts.append(alert)

        return new_alerts

    def run_monitoring_cycle(self):
        """
        Single monitoring cycle: check all live games
        """
        logger.info("\n" + "="*60)
        logger.info(f"Monitoring cycle: {datetime.now().strftime('%H:%M:%S')}")
        logger.info("="*60)

        # Load live games
        live_games = self.load_live_games()

        if not live_games:
            logger.info("No live games")
            return

        # Check each game
        all_alerts = []
        for game in live_games:
            logger.info(f"\nChecking: {game['home_team']} vs {game['away_team']}")
            alerts = self.check_game(game)

            if alerts:
                all_alerts.extend(alerts)
                logger.info(f"  Found {len(alerts)} opportunities!")

                # Log each alert
                for alert in alerts:
                    logger.info(f"    {alert['direction']} {alert['bet_total']} @ {alert['bookmaker']}")
                    logger.info(f"    Edge: {alert['edge_points']:.1f} pts | Kelly: {alert['bet_size_pct']:.2f}%")

        # Save alerts
        if all_alerts:
            self._save_alerts(all_alerts)
            self._send_notifications(all_alerts)
            self.alert_history.extend(all_alerts)

        logger.info(f"\nCycle complete. Found {len(all_alerts)} total alerts.")

    def _save_alerts(self, alerts: List[Dict]):
        """Save alerts to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{self.output_dir}/regression_alerts_{timestamp}.json"

        with open(output_path, 'w') as f:
            json.dump(alerts, f, indent=2)

        logger.info(f"Saved alerts to {output_path}")

        # Also save to "latest" file for frontend
        latest_path = f"{self.output_dir}/regression_alerts_latest.json"
        with open(latest_path, 'w') as f:
            json.dump(alerts, f, indent=2)

    def _send_notifications(self, alerts: List[Dict]):
        """
        Send notifications via configured channels

        Could integrate with:
        - Discord webhook
        - SMS (Twilio)
        - Email
        - Push notifications
        - Telegram
        """

        # Example: Send to Discord
        discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')

        if not discord_webhook:
            logger.info("No notification channels configured")
            return

        for alert in alerts:
            message = self._format_alert_message(alert)

            # Send to Discord (example)
            try:
                import requests
                requests.post(discord_webhook, json={'content': message})
                logger.info(f"Sent notification for {alert['game']}")
            except Exception as e:
                logger.error(f"Error sending notification: {e}")

    def _format_alert_message(self, alert: Dict) -> str:
        """Format alert as readable message"""

        message = f"""
🔔 **Regression-to-Mean Alert**

**Game:** {alert['game']}
**Bookmaker:** {alert['bookmaker']}

**Recommendation:** {alert['direction']} {alert['bet_total']}
**Edge:** {alert['edge_points']:.1f} points ({alert['deviation_description']})
**Kelly Sizing:** {alert['bet_size_pct']:.2f}% of bankroll

**Analysis:**
- Model Prediction: {alert['predicted_total']:.1f}
- Live Total: {alert['live_total']}
- Z-Score: {alert['z_score']:.2f} std devs
- Confidence: {alert['confidence']:.1%}

**Reasoning:** {alert['reasoning']}
"""
        return message.strip()

    def run(self):
        """
        Main monitoring loop - runs continuously
        """
        logger.info("\n" + "="*60)
        logger.info("REGRESSION-TO-MEAN LIVE MONITOR STARTED")
        logger.info("="*60)
        logger.info(f"Check interval: {self.check_interval} seconds")
        logger.info(f"Z-score threshold: {self.strategy.z_score_threshold}")
        logger.info(f"Min edge: {self.strategy.min_edge} points")
        logger.info("="*60)

        cycle_count = 0

        try:
            while True:
                cycle_count += 1
                logger.info(f"\nCycle #{cycle_count}")

                self.run_monitoring_cycle()

                # Wait for next cycle
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            logger.info("\n\nMonitoring stopped by user")
            logger.info(f"Total cycles: {cycle_count}")
            logger.info(f"Total alerts: {len(self.alert_history)}")


def main():
    """Start the live monitor"""

    # Initialize strategy
    strategy = RegressionToMeanStrategy(
        model_path="backend/ml/models/ncaab_quantile_mean_latest.json",
        z_score_threshold=2.0,
        min_confidence=0.60,
        min_edge=3.0
    )

    # Initialize monitor
    monitor = LiveRegressionMonitor(
        strategy=strategy,
        check_interval=30  # Check every 30 seconds
    )

    # Start monitoring
    monitor.run()


if __name__ == "__main__":
    main()
