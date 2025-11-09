"""
Live Goalie Pull Monitor Service

Runs continuously during NHL game days:
1. Polls NHL API every 5-10 seconds
2. Evaluates games in the 5:00-1:00 window
3. Generates alerts when conditions are met
4. Logs to database for CLV tracking

This is the production service that runs 24/7 during NHL season.
"""

import time
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Set
import json

from nhl_api_client import NHLAPIClient
from execution_engine import GoaliePullExecutionEngine
from database_schema import GoaliePullDB


class LiveGoaliePullMonitor:
    """Live monitoring service for goalie pull timing alpha"""

    def __init__(self, config: Dict = None):
        self.nhl_client = NHLAPIClient()
        self.engine = GoaliePullExecutionEngine(config=config)
        self.db = GoaliePullDB()

        # Tracking
        self.active_games: Dict[str, Dict] = {}
        self.alerts_sent: Set[str] = set()  # To avoid duplicate alerts
        self.games_completed: Set[str] = set()

        # Service status
        self.running = False
        self.scan_interval = config.get('scan_interval_seconds', 5) if config else 5

        # Statistics
        self.stats = {
            'scans_completed': 0,
            'games_monitored': 0,
            'alerts_generated': 0,
            'bets_recommended': 0,
            'start_time': None
        }

        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown gracefully"""
        print("\n[SHUTDOWN] Received signal, stopping monitor...")
        self.running = False

    def start(self, duration_seconds: int = None):
        """
        Start live monitoring

        Args:
            duration_seconds: How long to run (None = run indefinitely)
        """
        self.running = True
        self.stats['start_time'] = datetime.now()

        print("=" * 80)
        print("GOALIE PULL LIVE MONITOR - STARTING")
        print("=" * 80)
        print(f"Start Time: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Scan Interval: {self.scan_interval}s")
        print(f"Duration: {'Indefinite' if duration_seconds is None else f'{duration_seconds}s'}")
        print("\nConfiguration:")
        print(f"  Propensity Thresholds: Aggressive={self.engine.config['propensity_threshold_aggressive']:.0%}, " +
              f"Moderate={self.engine.config['propensity_threshold_moderate']:.0%}, " +
              f"Conservative={self.engine.config['propensity_threshold_conservative']:.0%}")
        print(f"  Cushion Required: {self.engine.config['cushion_decimal']:.2f} decimal")
        print(f"  Min EV: {self.engine.config['min_ev_pct']:.1f}%")
        print(f"  Kelly Fraction: {self.engine.config['kelly_fraction']:.2f}")
        print("=" * 80)

        start_time = time.time()

        try:
            while self.running:
                # Check if duration exceeded
                if duration_seconds and (time.time() - start_time) > duration_seconds:
                    print(f"\n[TIMEOUT] Duration of {duration_seconds}s reached, stopping...")
                    break

                # Perform scan
                self._scan_games()

                # Update stats
                self.stats['scans_completed'] += 1

                # Wait for next scan
                time.sleep(self.scan_interval)

        except Exception as e:
            print(f"\n[ERROR] Monitor crashed: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self._print_summary()

    def _scan_games(self):
        """Scan all games in monitoring window"""

        # Get games in window (5:00-1:00 remaining in period 3/OT)
        games_in_window = self.nhl_client.monitor_games_in_window()

        if not games_in_window:
            # No games to monitor
            if self.stats['scans_completed'] % 12 == 0:  # Print every minute
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No games in monitoring window")
            return

        # Process each game
        for game_state in games_in_window:
            game_id = game_state['game_id']

            # Update active games tracking
            if game_id not in self.active_games:
                self.active_games[game_id] = game_state
                self.stats['games_monitored'] += 1
                print(f"\n[NEW GAME] {game_state['away_team']} @ {game_state['home_team']}")
                print(f"           {game_state['trailing_team']} down {game_state['score_differential']}, " +
                      f"{game_state['time_remaining_seconds']}s remaining")

            # Check if already alerted for this game
            alert_key = f"{game_id}_{game_state['time_remaining_seconds'] // 30}"  # Bucket by 30s
            if alert_key in self.alerts_sent:
                continue

            # Evaluate game state
            # For now, we don't have live odds, so we'll just evaluate conditions
            evaluation = self.engine.evaluate_game_state(
                game_state=game_state,
                offered_odds=None  # TODO: Fetch from odds API
            )

            # Print status
            mins = game_state['time_remaining_seconds'] // 60
            secs = game_state['time_remaining_seconds'] % 60
            timestamp = datetime.now().strftime('%H:%M:%S')

            if evaluation['alert']:
                print(f"\n[{timestamp}] ⚠️  ALERT CONDITIONS MET")
                print(f"           Game: {game_state['away_team']} @ {game_state['home_team']}")
                print(f"           Time: {mins}:{secs:02d}")
                print(f"           Trailing: {game_state['trailing_team']} (down {game_state['score_differential']})")
                print(f"           Coach: {game_state['coach_id']}")
                print(f"           Pull Propensity: {evaluation['pull_propensity']:.1%} (threshold: {evaluation['threshold']:.1%})")
                print(f"           P(≥1 goal): {evaluation['p_goal']:.1%}")
                print(f"           Fair Price: {evaluation['fair_price']['fair_american']}")
                print(f"           Min Acceptable: {evaluation['fair_price']['min_acceptable_american']}")

                # Check for live odds
                offered_odds = self.nhl_client.get_current_odds(game_id)

                if offered_odds:
                    # Re-evaluate with odds
                    evaluation_with_odds = self.engine.evaluate_game_state(
                        game_state=game_state,
                        offered_odds=offered_odds
                    )

                    if evaluation_with_odds['alert'] and 'bet_eval' in evaluation_with_odds:
                        print(f"           📊 OFFERED ODDS: {offered_odds}")
                        print(f"           💰 EV: {evaluation_with_odds['bet_eval']['ev_pct']:+.1f}%")
                        print(f"           💵 BET SIZE: ${evaluation_with_odds['bet_size']:.0f}")
                        print(f"           ✅ {evaluation_with_odds['recommendation']}")

                        # Generate and log alert
                        alert = self.engine.generate_alert(game_id, game_state, evaluation_with_odds)
                        alert_id = self.engine.log_alert(alert)

                        self.stats['alerts_generated'] += 1
                        self.stats['bets_recommended'] += 1

                        # Mark as alerted
                        self.alerts_sent.add(alert_key)

                        # TODO: Send to frontend via WebSocket
                        self._send_alert_to_frontend(alert)
                    else:
                        print(f"           ❌ Offered odds ({offered_odds}) do not meet requirements")
                else:
                    print(f"           ⏳ Awaiting live odds...")

                    # Log alert without odds (for tracking)
                    alert = self.engine.generate_alert(game_id, game_state, evaluation)
                    alert_id = self.engine.log_alert(alert)

                    self.stats['alerts_generated'] += 1

                    # Mark as alerted
                    self.alerts_sent.add(alert_key)

            else:
                # Conditions not met, just log status occasionally
                if self.stats['scans_completed'] % 12 == 0:  # Every minute
                    print(f"[{timestamp}] {game_state['game_id']}: {game_state['trailing_team']} @ {mins}:{secs:02d} - " +
                          f"Propensity {evaluation.get('pull_propensity', 0):.1%} " +
                          f"({evaluation['reason']})")

    def _send_alert_to_frontend(self, alert: Dict):
        """
        Send alert to frontend via WebSocket

        TODO: Integrate with FastAPI WebSocket endpoint
        """
        print(f"[TODO] Send alert #{alert.get('alert_id', 'N/A')} to frontend via WebSocket")

        # In production, would do:
        # await websocket_manager.broadcast({
        #     'type': 'goalie_pull_alert',
        #     'data': alert
        # })

    def _print_summary(self):
        """Print session summary"""
        duration = datetime.now() - self.stats['start_time']

        print("\n" + "=" * 80)
        print("GOALIE PULL LIVE MONITOR - SESSION SUMMARY")
        print("=" * 80)
        print(f"Start Time: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {duration}")
        print(f"\nStatistics:")
        print(f"  Scans Completed: {self.stats['scans_completed']}")
        print(f"  Games Monitored: {self.stats['games_monitored']}")
        print(f"  Alerts Generated: {self.stats['alerts_generated']}")
        print(f"  Bets Recommended: {self.stats['bets_recommended']}")
        print("=" * 80)


def run_monitor(duration_seconds: int = None, config: Dict = None):
    """
    Run the live monitor service

    Args:
        duration_seconds: How long to run (None = indefinite)
        config: Configuration dict (uses defaults if None)
    """
    monitor = LiveGoaliePullMonitor(config=config)
    monitor.start(duration_seconds=duration_seconds)


if __name__ == "__main__":
    # Test configuration
    test_config = {
        'propensity_threshold_aggressive': 0.35,
        'propensity_threshold_moderate': 0.45,
        'propensity_threshold_conservative': 0.60,
        'cushion_decimal': 0.12,
        'min_ev_pct': 2.0,
        'kelly_fraction': 0.25,
        'max_bet_pct_bankroll': 0.02,
        'scan_interval_seconds': 10,  # 10s for testing
    }

    print("\n[INFO] Starting live monitor in TEST MODE")
    print("[INFO] Will run for 5 minutes to test NHL API integration")
    print("[INFO] Press Ctrl+C to stop early\n")

    # Run for 5 minutes
    run_monitor(duration_seconds=300, config=test_config)

    print("\n[OK] Test complete!")
