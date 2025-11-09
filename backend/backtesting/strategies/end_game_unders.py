"""
End-Game Unders Strategy Backtester

Strategy: Bet Q4 under when there's a blowout after Q3
Logic: Books undervalue garbage time clock management

Expected EV: +10-20%
Win Rate Target: 65-70%

From "Interception" by Ed Miller (Angle #8)
"""

from typing import Dict, List, Tuple
from datetime import datetime
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from database.backtest_db import BacktestDB


class EndGameUndersBacktester:
    """Backtest the End-Game Unders strategy"""

    def __init__(self, blowout_threshold: float = 15.0, league_avg_q4: float = 52.0):
        """
        Args:
            blowout_threshold: Point differential after Q3 to trigger bet
            league_avg_q4: League average Q4 total (used as the "line")
        """
        self.blowout_threshold = blowout_threshold
        self.league_avg_q4 = league_avg_q4
        self.db = BacktestDB()

    def is_blowout_after_q3(self, game: Dict) -> bool:
        """
        Check if game is a blowout after Q3

        Args:
            game: Game dict with quarter scores

        Returns:
            True if score differential >= threshold
        """
        # Calculate score after Q3
        home_through_q3 = game['q1_home'] + game['q2_home'] + game['q3_home']
        away_through_q3 = game['q1_away'] + game['q2_away'] + game['q3_away']

        # Get differential
        diff = abs(home_through_q3 - away_through_q3)

        return diff >= self.blowout_threshold

    def get_q4_total(self, game: Dict) -> float:
        """Get actual Q4 total"""
        return game['q4_home'] + game['q4_away']

    def calculate_edge(self, actual_q4: float, line: float) -> float:
        """Calculate edge in points"""
        return line - actual_q4

    def would_bet_win(self, actual_q4: float, line: float) -> str:
        """
        Determine if under bet won

        Args:
            actual_q4: Actual Q4 total
            line: The line we're betting under

        Returns:
            'WIN', 'LOSS', or 'PUSH'
        """
        if actual_q4 < line:
            return 'WIN'
        elif actual_q4 > line:
            return 'LOSS'
        else:
            return 'PUSH'

    def run_backtest(self, sport: str = 'NBA', season: int = None, min_games: int = 50) -> Dict:
        """
        Run backtest on historical data

        Args:
            sport: Sport to backtest
            season: Specific season or None for all
            min_games: Minimum games needed for valid backtest

        Returns:
            Backtest results dict
        """
        print("\n" + "="*60)
        print("END-GAME UNDERS BACKTEST")
        print("="*60)
        print(f"Blowout threshold: {self.blowout_threshold} points after Q3")
        print(f"Q4 Line (league avg): {self.league_avg_q4} points")
        print("="*60 + "\n")

        # Fetch games from database
        games = self.db.get_games(sport=sport, season=season, limit=10000)

        if len(games) < min_games:
            print(f"[WARNING] Only {len(games)} games found. Need at least {min_games} for valid backtest.")
            print(f"          Run ESPN client to import more historical data.")

        # Track results
        opportunities = []
        wins = 0
        losses = 0
        pushes = 0
        total_edge = 0.0

        # Analyze each game
        for game in games:
            # Check for blowout
            if self.is_blowout_after_q3(game):
                actual_q4 = self.get_q4_total(game)
                edge = self.calculate_edge(actual_q4, self.league_avg_q4)
                outcome = self.would_bet_win(actual_q4, self.league_avg_q4)

                # Track
                if outcome == 'WIN':
                    wins += 1
                elif outcome == 'LOSS':
                    losses += 1
                else:
                    pushes += 1

                total_edge += edge

                opportunities.append({
                    'game_id': game['game_id'],
                    'date': game['date'],
                    'matchup': f"{game['away_team']} @ {game['home_team']}",
                    'q3_diff': abs((game['q1_home'] + game['q2_home'] + game['q3_home']) -
                                  (game['q1_away'] + game['q2_away'] + game['q3_away'])),
                    'actual_q4': actual_q4,
                    'line': self.league_avg_q4,
                    'edge': edge,
                    'outcome': outcome
                })

        # Calculate metrics
        total_opportunities = len(opportunities)
        total_bets = wins + losses + pushes
        win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
        avg_edge = (total_edge / total_opportunities) if total_opportunities > 0 else 0

        # Calculate ROI (assuming -110 odds on both sides)
        # Win = +0.91 units, Loss = -1 unit
        profit = (wins * 0.91) - losses
        roi = (profit / total_bets * 100) if total_bets > 0 else 0

        # Print results
        print("\n" + "="*60)
        print("RESULTS")
        print("="*60)
        print(f"Total opportunities: {total_opportunities}")
        print(f"Bets placed: {total_bets}")
        print(f"  Wins: {wins}")
        print(f"  Losses: {losses}")
        print(f"  Pushes: {pushes}")
        print(f"Win rate: {win_rate:.1f}%")
        print(f"Average edge: {avg_edge:.2f} points")
        print(f"ROI: {roi:+.1f}%")
        print(f"Profit/Loss: {profit:+.2f} units")
        print("="*60 + "\n")

        # Show sample opportunities
        if opportunities:
            print("Sample opportunities:")
            for opp in opportunities[:5]:
                print(f"  {opp['date']}: {opp['matchup']}")
                print(f"    Q3 diff: {opp['q3_diff']:.0f} pts, Q4: {opp['actual_q4']:.0f} (line {opp['line']:.0f})")
                print(f"    Edge: {opp['edge']:+.1f} pts -> {opp['outcome']}")

        result = {
            'strategy_id': 8,  # End-Game Unders
            'sport': sport,
            'date_range_start': min([g['date'] for g in games]) if games else '',
            'date_range_end': max([g['date'] for g in games]) if games else '',
            'total_opportunities': total_opportunities,
            'bets_placed': total_bets,
            'wins': wins,
            'losses': losses,
            'pushes': pushes,
            'win_rate': win_rate,
            'roi': roi,
            'avg_edge': avg_edge,
            'profit_loss': profit,
            'data_source': 'espn'
        }

        return result

    def save_backtest(self, result: Dict) -> int:
        """Save backtest result to database"""
        backtest_id = self.db.save_backtest_result(result)
        print(f"[OK] Backtest saved to database (ID: {backtest_id})")
        return backtest_id


def main():
    """Run backtest"""
    backtester = EndGameUndersBacktester(
        blowout_threshold=15.0,  # 15+ point lead after Q3
        league_avg_q4=52.0       # NBA Q4 average ~52 points
    )

    # Run backtest on all available NBA games
    result = backtester.run_backtest(sport='NBA')

    # Save to database
    if result['total_opportunities'] > 0:
        backtester.save_backtest(result)

    # Test with different thresholds
    print("\n" + "="*60)
    print("SENSITIVITY ANALYSIS")
    print("="*60)

    for threshold in [10, 12, 15, 18, 20]:
        print(f"\nBlowout threshold: {threshold} points")
        bt = EndGameUndersBacktester(blowout_threshold=threshold, league_avg_q4=52.0)
        res = bt.run_backtest(sport='NBA')
        print(f"  Opportunities: {res['total_opportunities']}, Win Rate: {res['win_rate']:.1f}%, ROI: {res['roi']:+.1f}%")


if __name__ == "__main__":
    main()
