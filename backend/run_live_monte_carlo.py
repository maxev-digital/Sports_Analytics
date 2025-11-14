"""
Automated Live Game Monte Carlo Simulator
CREATED: 2025-11-09

Automatically runs Monte Carlo simulations for all live games and logs results.
This feeds the autonomous learning system.

Run every 5 minutes during game time via cron:
    */5 18-23 * * * cd /root/sporttrader/backend && source venv/bin/activate && python3 run_live_monte_carlo.py --sport nba >> logs/live_monte_carlo.log 2>&1
"""

import sys
import os
import logging
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from pathlib import Path
import argparse

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from simulation.monte_carlo_totals import PossessionMonteCarloSimulator, GameState, TeamStats

# Setup logging
log_dir = Path("backend/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'live_monte_carlo_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LiveMonteCarloRunner:
    """Runs Monte Carlo simulations for all live games automatically"""

    def __init__(self, sport: str):
        self.sport = sport.lower()
        self.simulator = PossessionMonteCarloSimulator()

        # Setup tracking
        tracking_dir = Path("backend/data/tracking/monte_carlo")
        tracking_dir.mkdir(parents=True, exist_ok=True)
        self.simulations_log = tracking_dir / f"{sport}_simulations_log.csv"

        # Initialize log file
        if not self.simulations_log.exists():
            df = pd.DataFrame(columns=[
                'simulation_id', 'timestamp', 'game_date', 'game_id',
                'quarter', 'time_remaining', 'remaining_time_minutes',
                'home_team', 'away_team', 'home_score', 'away_score',
                'current_total', 'avg_pace', 'simulated_mean', 'simulated_std',
                'prob_over', 'prob_under', 'market_total', 'recommendation'
            ])
            df.to_csv(self.simulations_log, index=False)

    def fetch_live_games(self) -> list:
        """Fetch all live games for the sport"""
        logger.info(f"Fetching live {self.sport.upper()} games...")

        if self.sport == 'nba':
            return self._fetch_nba_live_games()
        elif self.sport == 'ncaab':
            return self._fetch_ncaab_live_games()
        else:
            return []

    def _fetch_nba_live_games(self) -> list:
        """Fetch live NBA games from ESPN"""
        try:
            today = datetime.now().strftime('%Y%m%d')
            url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today}"

            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return []

            data = response.json()
            live_games = []

            for event in data.get('events', []):
                status = event.get('status', {})
                state = status.get('type', {}).get('state', '')

                # Only in-progress games
                if state != 'in':
                    continue

                comp = event.get('competitions', [{}])[0]
                competitors = comp.get('competitors', [])

                if len(competitors) != 2:
                    continue

                # Extract game info
                home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                away = next((c for c in competitors if c.get('homeAway') == 'away'), None)

                if not home or not away:
                    continue

                game = {
                    'game_id': event.get('id', ''),
                    'game_date': datetime.now().strftime('%Y-%m-%d'),
                    'home_team': home.get('team', {}).get('displayName', ''),
                    'away_team': away.get('team', {}).get('displayName', ''),
                    'home_score': int(home.get('score', 0)),
                    'away_score': int(away.get('score', 0)),
                    'quarter': int(status.get('period', 1)),
                    'time_remaining': status.get('displayClock', '0:00')
                }

                live_games.append(game)
                logger.info(f"  Found: {game['away_team']} @ {game['home_team']} - Q{game['quarter']} {game['time_remaining']}")

            return live_games

        except Exception as e:
            logger.error(f"Error fetching NBA live games: {e}")
            return []

    def _fetch_ncaab_live_games(self) -> list:
        """Fetch live NCAAB games from ESPN"""
        try:
            today = datetime.now().strftime('%Y%m%d')
            url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={today}"

            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return []

            data = response.json()
            live_games = []

            for event in data.get('events', []):
                status = event.get('status', {})
                state = status.get('type', {}).get('state', '')

                # Only in-progress games
                if state != 'in':
                    continue

                comp = event.get('competitions', [{}])[0]
                competitors = comp.get('competitors', [])

                if len(competitors) != 2:
                    continue

                home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                away = next((c for c in competitors if c.get('homeAway') == 'away'), None)

                if not home or not away:
                    continue

                game = {
                    'game_id': event.get('id', ''),
                    'game_date': datetime.now().strftime('%Y-%m-%d'),
                    'home_team': home.get('team', {}).get('displayName', ''),
                    'away_team': away.get('team', {}).get('displayName', ''),
                    'home_score': int(home.get('score', 0)),
                    'away_score': int(away.get('score', 0)),
                    'quarter': int(status.get('period', 1)),
                    'time_remaining': status.get('displayClock', '0:00')
                }

                live_games.append(game)
                logger.info(f"  Found: {game['away_team']} @ {game['home_team']} - {game['quarter']}H {game['time_remaining']}")

            return live_games

        except Exception as e:
            logger.error(f"Error fetching NCAAB live games: {e}")
            return []

    def run_simulation(self, game: dict) -> dict:
        """Run Monte Carlo simulation for a single game"""
        try:
            # Get team stats (simplified - in production, fetch real stats)
            home_stats = TeamStats(pace=100.0, off_rating=110.0, def_rating=108.0)
            away_stats = TeamStats(pace=98.0, off_rating=108.0, def_rating=110.0)

            # Create game state
            game_state = GameState(
                quarter=game['quarter'],
                time_remaining=game['time_remaining'],
                home_score=game['home_score'],
                away_score=game['away_score']
            )

            # Run simulation
            result = self.simulator.simulate(game_state, home_stats, away_stats, n_simulations=10000)

            # Get market total (simplified - in production, fetch from odds API)
            market_total = 220.0  # Placeholder

            # Calculate probabilities
            simulated_totals = result['simulated_totals']
            prob_over = (simulated_totals > market_total).mean()
            prob_under = 1 - prob_over

            # Recommendation
            if prob_over > 0.60:
                recommendation = 'OVER'
            elif prob_under > 0.60:
                recommendation = 'UNDER'
            else:
                recommendation = 'PASS'

            remaining_time = self.simulator.calculate_remaining_time(
                game['quarter'], game['time_remaining']
            )

            simulation = {
                'simulation_id': f"{game['game_id']}_{datetime.now().strftime('%H%M%S')}",
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'game_date': game['game_date'],
                'game_id': game['game_id'],
                'quarter': game['quarter'],
                'time_remaining': game['time_remaining'],
                'remaining_time_minutes': remaining_time,
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'home_score': game['home_score'],
                'away_score': game['away_score'],
                'current_total': game['home_score'] + game['away_score'],
                'avg_pace': (home_stats.pace + away_stats.pace) / 2,
                'simulated_mean': result['mean_total'],
                'simulated_std': result['std_total'],
                'prob_over': prob_over,
                'prob_under': prob_under,
                'market_total': market_total,
                'recommendation': recommendation
            }

            logger.info(f"  Simulated: Mean={result['mean_total']:.1f}, Std={result['std_total']:.1f}")
            logger.info(f"  Prob OVER {market_total}: {prob_over:.1%}")

            return simulation

        except Exception as e:
            logger.error(f"Error simulating game {game['game_id']}: {e}")
            return None

    def log_simulation(self, simulation: dict):
        """Log simulation to tracking file"""
        if not simulation:
            return

        # Load existing log
        existing = pd.read_csv(self.simulations_log)

        # Append new simulation
        new_row = pd.DataFrame([simulation])
        combined = pd.concat([existing, new_row], ignore_index=True)

        # Save
        combined.to_csv(self.simulations_log, index=False)

    def run(self):
        """Run simulations for all live games"""
        logger.info("=" * 80)
        logger.info(f"LIVE MONTE CARLO RUNNER - {self.sport.upper()}")
        logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)

        # Fetch live games
        live_games = self.fetch_live_games()

        if not live_games:
            logger.info("No live games found")
            return True

        logger.info(f"Found {len(live_games)} live games")

        # Run simulations
        for game in live_games:
            simulation = self.run_simulation(game)
            if simulation:
                self.log_simulation(simulation)

        logger.info(f"✅ Completed {len(live_games)} simulations")
        return True


def main():
    parser = argparse.ArgumentParser(description='Automated Live Game Monte Carlo Simulator')
    parser.add_argument('--sport', required=True, choices=['nba', 'ncaab'],
                       help='Sport to run simulations for')

    args = parser.parse_args()

    runner = LiveMonteCarloRunner(sport=args.sport)
    success = runner.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
