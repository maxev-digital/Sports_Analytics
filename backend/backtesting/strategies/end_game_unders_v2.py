"""
End-Game Unders Strategy Backtester (V2 - With Real Odds Integration)

Strategy: Bet Q4 under when there's a blowout after Q3
Logic: Books undervalue garbage time clock management

Expected EV: +10-20%
Win Rate Target: 65-70%

From "Interception" by Ed Miller (Angle #8)

V2 IMPROVEMENTS:
- Uses real historical odds from odds_history table
- Calculates ROI based on actual market prices (not assumed -110)
- Provides accurate profitability metrics
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from database.backtest_db import BacktestDB


class EndGameUndersBacktesterV2:
    """Backtest the End-Game Unders strategy with real odds"""

    def __init__(self, blowout_threshold: float = 15.0, league_avg_q4: float = 52.0):
        """
        Args:
            blowout_threshold: Point differential after Q3 to trigger bet
            league_avg_q4: League average Q4 total (fallback line)
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

    def get_game_odds(self, game: Dict, market_type: str = 'totals') -> Optional[Dict]:
        """
        Get historical odds for a game from odds_history table

        Args:
            game: Game dict with game_id, date, teams
            market_type: 'totals', 'spreads', or 'h2h'

        Returns:
            Dict with odds data or None if not found
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Try to find odds for this game
        # Match by date and teams (odds_history may not have same game_id format)
        cursor.execute("""
            SELECT bookmaker, line_value, odds, period
            FROM odds_history
            WHERE sport = 'basketball_nba'
              AND market_type = ?
              AND date(timestamp) = date(?)
              AND (
                  (home_team LIKE ? AND away_team LIKE ?)
                  OR (home_team LIKE ? AND away_team LIKE ?)
              )
            ORDER BY timestamp DESC
            LIMIT 1
        """, (
            market_type,
            game['date'],
            f"%{game['home_team'].split()[-1]}%",  # Match by team name suffix (e.g., "Lakers")
            f"%{game['away_team'].split()[-1]}%",
            f"%{game['home_team']}%",
            f"%{game['away_team']}%"
        ))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'bookmaker': row[0],
                'line': row[1],
                'odds': row[2],
                'period': row[3]
            }
        return None

    def calculate_profit(self, outcome: str, odds: int = -110) -> float:
        """
        Calculate profit for a bet based on outcome and actual odds

        Args:
            outcome: 'WIN', 'LOSS', or 'PUSH'
            odds: American odds (e.g., -110, -120, +150)

        Returns:
            Profit in units (negative for loss)
        """
        if outcome == 'WIN':
            # Calculate payout based on odds
            if odds > 0:
                # Positive odds: risk 1 unit to win (odds/100) units
                return odds / 100
            else:
                # Negative odds: risk 1 unit to win (100/abs(odds)) units
                return 100 / abs(odds)
        elif outcome == 'LOSS':
            return -1.0  # Always lose 1 unit
        else:  # PUSH
            return 0.0

    def run_backtest(
        self,
        sport: str = 'NBA',
        season: int = None,
        min_games: int = 50,
        use_real_odds: bool = True
    ) -> Dict:
        """
        Run backtest on historical data

        Args:
            sport: Sport to backtest
            season: Specific season or None for all
            min_games: Minimum games needed for valid backtest
            use_real_odds: If True, use historical odds; if False, assume -110

        Returns:
            Backtest results dict
        """
        print("\n" + "="*60)
        print("END-GAME UNDERS BACKTEST V2")
        print("="*60)
        print(f"Blowout threshold: {self.blowout_threshold} points after Q3")
        print(f"Q4 Line (fallback): {self.league_avg_q4} points")
        print(f"Using real odds: {use_real_odds}")
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
        total_profit = 0.0
        odds_found = 0
        odds_missing = 0

        # Analyze each game
        for game in games:
            # Check for blowout
            if self.is_blowout_after_q3(game):
                actual_q4 = self.get_q4_total(game)

                # Try to get real odds
                line = self.league_avg_q4
                odds_value = -110  # Default

                if use_real_odds:
                    odds_data = self.get_game_odds(game)
                    if odds_data:
                        if odds_data['line'] is not None:
                            line = odds_data['line']
                        if odds_data['odds'] is not None:
                            odds_value = odds_data['odds']
                        odds_found += 1
                    else:
                        odds_missing += 1

                edge = self.calculate_edge(actual_q4, line)
                outcome = self.would_bet_win(actual_q4, line)

                # Calculate profit using actual odds
                profit = self.calculate_profit(outcome, odds_value)
                total_profit += profit

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
                    'line': line,
                    'odds': odds_value,
                    'edge': edge,
                    'outcome': outcome,
                    'profit': profit
                })

        # Calculate metrics
        total_opportunities = len(opportunities)
        total_bets = wins + losses + pushes
        win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
        avg_edge = (total_edge / total_opportunities) if total_opportunities > 0 else 0
        roi = (total_profit / total_bets * 100) if total_bets > 0 else 0

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
        print(f"Profit/Loss: {total_profit:+.2f} units")

        if use_real_odds:
            print(f"\nOdds Coverage:")
            print(f"  Real odds found: {odds_found} games")
            print(f"  Missing odds (used -110): {odds_missing} games")
            print(f"  Coverage: {(odds_found / total_opportunities * 100):.1f}%")

        print("="*60 + "\n")

        # Show sample opportunities
        if opportunities:
            print("Sample opportunities:")
            for opp in opportunities[:5]:
                print(f"  {opp['date']}: {opp['matchup']}")
                print(f"    Q3 diff: {opp['q3_diff']:.0f} pts, Q4: {opp['actual_q4']:.0f} (line {opp['line']:.0f})")
                print(f"    Odds: {opp['odds']}, Edge: {opp['edge']:+.1f} pts -> {opp['outcome']} ({opp['profit']:+.2f}u)")

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
            'profit_loss': total_profit,
            'data_source': 'espn + real_odds' if use_real_odds else 'espn',
            'odds_coverage': (odds_found / total_opportunities * 100) if total_opportunities > 0 and use_real_odds else 100.0
        }

        return result

    def save_backtest(self, result: Dict) -> int:
        """Save backtest result to database"""
        backtest_id = self.db.save_backtest_result(result)
        print(f"[OK] Backtest saved to database (ID: {backtest_id})")
        return backtest_id


def main():
    """Run backtest with real odds integration"""
    backtester = EndGameUndersBacktesterV2(
        blowout_threshold=15.0,  # 15+ point lead after Q3
        league_avg_q4=52.0       # NBA Q4 average ~52 points
    )

    # Run backtest on all available NBA games WITH real odds
    print("Running backtest WITH real historical odds...")
    result_with_odds = backtester.run_backtest(sport='NBA', use_real_odds=True)

    # Compare to assumed -110 odds
    print("\n\n" + "="*60)
    print("COMPARISON: Running same backtest assuming -110 odds")
    print("="*60)
    result_assumed = backtester.run_backtest(sport='NBA', use_real_odds=False)

    # Show comparison
    print("\n" + "="*60)
    print("REAL ODDS vs ASSUMED -110 COMPARISON")
    print("="*60)
    print(f"Win Rate: {result_with_odds['win_rate']:.1f}% (same for both)")
    print(f"\nROI with REAL odds: {result_with_odds['roi']:+.1f}%")
    print(f"ROI assuming -110:  {result_assumed['roi']:+.1f}%")
    print(f"Difference: {(result_with_odds['roi'] - result_assumed['roi']):+.1f}%")
    print(f"\nProfit with REAL odds: {result_with_odds['profit_loss']:+.2f} units")
    print(f"Profit assuming -110:  {result_assumed['profit_loss']:+.2f} units")
    print(f"Difference: {(result_with_odds['profit_loss'] - result_assumed['profit_loss']):+.2f} units")
    print("="*60)

    # Save the real odds version
    if result_with_odds['total_opportunities'] > 0:
        backtester.save_backtest(result_with_odds)


if __name__ == "__main__":
    main()
