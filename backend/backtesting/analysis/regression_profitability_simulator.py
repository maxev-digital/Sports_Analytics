"""
Regression to Mean Profitability Simulator

Simulates live betting opportunities by using quarter scores to estimate
live totals at key moments (Q1, Halftime, Q3) and calculates expected ROI
when betting regression back to closing total.
"""

import sys
from pathlib import Path
import statistics
from typing import Dict, List, Tuple

sys.path.append(str(Path(__file__).parent.parent))
from database.backtest_db import BacktestDB


class RegressionProfitabilitySimulator:
    """Simulate regression betting profitability"""

    def __init__(self, std_deviation: float = 17.08, threshold_sigma: float = 1.5):
        """
        Args:
            std_deviation: Historical std dev of (actual - closing)
            threshold_sigma: Number of std deviations to trigger bet (default 1.5)
        """
        self.db = BacktestDB()
        self.std_deviation = std_deviation
        self.threshold = std_deviation * threshold_sigma
        self.threshold_sigma = threshold_sigma

    def get_games_with_odds(self, limit: int = 300) -> List[Dict]:
        """Fetch games with closing totals and quarter scores"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Get unique games with FanDuel odds
        cursor.execute("""
            SELECT DISTINCT
                g.game_id,
                g.date,
                g.home_team,
                g.away_team,
                g.home_score,
                g.away_score,
                g.q1_home,
                g.q1_away,
                g.q2_home,
                g.q2_away,
                g.q3_home,
                g.q3_away,
                g.q4_home,
                g.q4_away,
                (
                    SELECT o2.line_value
                    FROM odds_history o2
                    WHERE o2.home_team = g.home_team
                      AND o2.away_team = g.away_team
                      AND date(o2.timestamp) = date(g.date)
                      AND o2.market_type = 'totals'
                      AND o2.bookmaker = 'fanduel'
                    LIMIT 1
                ) as closing_total
            FROM historical_games g
            WHERE EXISTS (
                SELECT 1 FROM odds_history o
                WHERE o.home_team = g.home_team
                  AND o.away_team = g.away_team
                  AND date(o.timestamp) = date(g.date)
                  AND o.market_type = 'totals'
                  AND o.bookmaker = 'fanduel'
            )
            AND g.home_score IS NOT NULL
            AND g.q1_home IS NOT NULL
            AND g.q2_home IS NOT NULL
            AND g.q3_home IS NOT NULL
            AND g.q4_home IS NOT NULL
            ORDER BY g.date
            LIMIT ?
        """, (limit,))

        games = []
        for row in cursor.fetchall():
            if row[14] is None:  # Skip if no closing total
                continue

            games.append({
                'game_id': row[0],
                'date': row[1],
                'home_team': row[2],
                'away_team': row[3],
                'actual_total': row[4] + row[5],
                'closing_total': row[14],
                'q1_total': row[6] + row[7],
                'q2_total': row[8] + row[9],
                'q3_total': row[10] + row[11],
                'q4_total': row[12] + row[13],
                'half_total': row[6] + row[7] + row[8] + row[9],
                'q3_end_total': row[6] + row[7] + row[8] + row[9] + row[10] + row[11]
            })

        conn.close()
        return games

    def simulate_live_totals(self, game: Dict) -> List[Dict]:
        """
        Simulate live totals at key moments using quarter scores

        Returns list of betting opportunities with simulated live totals
        """
        opportunities = []

        # After Q1: Implied final = Q1 * 4
        q1_implied = game['q1_total'] * 4
        q1_deviation = q1_implied - game['closing_total']

        if abs(q1_deviation) > self.threshold:
            bet_side = 'under' if q1_deviation > 0 else 'over'

            # Result: Did remaining 3 quarters go under/over the implied pace?
            remaining_total = game['q2_total'] + game['q3_total'] + game['q4_total']
            implied_remaining = q1_implied * 0.75  # 75% of game left

            if bet_side == 'under':
                won = remaining_total < implied_remaining
            else:
                won = remaining_total > implied_remaining

            opportunities.append({
                'game_id': game['game_id'],
                'date': game['date'],
                'matchup': f"{game['away_team']} @ {game['home_team']}",
                'timing': 'After Q1',
                'closing_total': game['closing_total'],
                'live_implied_total': q1_implied,
                'deviation': q1_deviation,
                'deviation_sigma': q1_deviation / self.std_deviation,
                'bet_side': bet_side,
                'won': won,
                'actual_final': game['actual_total']
            })

        # At Halftime: Implied final = Half * 2
        half_implied = game['half_total'] * 2
        half_deviation = half_implied - game['closing_total']

        if abs(half_deviation) > self.threshold:
            bet_side = 'under' if half_deviation > 0 else 'over'

            # Result: Did 2H go under/over the implied pace?
            second_half_total = game['q3_total'] + game['q4_total']
            implied_2h = half_implied / 2

            if bet_side == 'under':
                won = second_half_total < implied_2h
            else:
                won = second_half_total > implied_2h

            opportunities.append({
                'game_id': game['game_id'],
                'date': game['date'],
                'matchup': f"{game['away_team']} @ {game['home_team']}",
                'timing': 'Halftime',
                'closing_total': game['closing_total'],
                'live_implied_total': half_implied,
                'deviation': half_deviation,
                'deviation_sigma': half_deviation / self.std_deviation,
                'bet_side': bet_side,
                'won': won,
                'actual_final': game['actual_total']
            })

        # After Q3: Implied final = Q1-Q3 * 4/3
        q3_implied = game['q3_end_total'] * (4/3)
        q3_deviation = q3_implied - game['closing_total']

        if abs(q3_deviation) > self.threshold:
            bet_side = 'under' if q3_deviation > 0 else 'over'

            # Result: Did Q4 go under/over the implied pace?
            implied_q4 = q3_implied / 4

            if bet_side == 'under':
                won = game['q4_total'] < implied_q4
            else:
                won = game['q4_total'] > implied_q4

            opportunities.append({
                'game_id': game['game_id'],
                'date': game['date'],
                'matchup': f"{game['away_team']} @ {game['home_team']}",
                'timing': 'After Q3',
                'closing_total': game['closing_total'],
                'live_implied_total': q3_implied,
                'deviation': q3_deviation,
                'deviation_sigma': q3_deviation / self.std_deviation,
                'bet_side': bet_side,
                'won': won,
                'actual_final': game['actual_total']
            })

        return opportunities

    def calculate_roi(self, opportunities: List[Dict], odds: int = -110) -> Dict:
        """Calculate ROI assuming standard -110 odds"""
        if not opportunities:
            return {'error': 'No opportunities found'}

        wins = sum(1 for o in opportunities if o['won'])
        losses = len(opportunities) - wins
        win_rate = wins / len(opportunities) * 100

        # At -110 odds, you risk 110 to win 100
        # Win: +100, Loss: -110
        if odds == -110:
            total_profit = (wins * 100) - (losses * 110)
            total_risked = len(opportunities) * 110
        else:
            # For other odds (future enhancement)
            total_profit = 0
            total_risked = len(opportunities) * 100

        roi = (total_profit / total_risked * 100) if total_risked > 0 else 0

        # Break down by timing
        timing_stats = {}
        for timing in ['After Q1', 'Halftime', 'After Q3']:
            timing_opps = [o for o in opportunities if o['timing'] == timing]
            if timing_opps:
                timing_wins = sum(1 for o in timing_opps if o['won'])
                timing_stats[timing] = {
                    'count': len(timing_opps),
                    'wins': timing_wins,
                    'losses': len(timing_opps) - timing_wins,
                    'win_rate': timing_wins / len(timing_opps) * 100
                }

        # Break down by deviation size
        high_dev = [o for o in opportunities if abs(o['deviation_sigma']) >= 2.0]
        medium_dev = [o for o in opportunities if 1.5 <= abs(o['deviation_sigma']) < 2.0]

        high_dev_stats = None
        if high_dev:
            high_wins = sum(1 for o in high_dev if o['won'])
            high_dev_stats = {
                'count': len(high_dev),
                'wins': high_wins,
                'win_rate': high_wins / len(high_dev) * 100
            }

        medium_dev_stats = None
        if medium_dev:
            med_wins = sum(1 for o in medium_dev if o['won'])
            medium_dev_stats = {
                'count': len(medium_dev),
                'wins': med_wins,
                'win_rate': med_wins / len(medium_dev) * 100
            }

        return {
            'total_opportunities': len(opportunities),
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'total_risked': total_risked,
            'roi': roi,
            'by_timing': timing_stats,
            'high_deviation': high_dev_stats,
            'medium_deviation': medium_dev_stats,
            'sample_opportunities': opportunities[:10]
        }

    def run_simulation(self, games_limit: int = 300) -> Dict:
        """Run complete profitability simulation"""

        print("\n" + "="*80)
        print("REGRESSION BETTING PROFITABILITY SIMULATION")
        print("="*80)
        print(f"Threshold: {self.threshold:.1f} points ({self.threshold_sigma} std deviations)")
        print("="*80 + "\n")

        # Fetch games
        print("Loading games with closing totals...")
        games = self.get_games_with_odds(limit=games_limit)
        print(f"[OK] Loaded {len(games)} games\n")

        # Simulate opportunities
        print("Simulating live betting opportunities...")
        all_opportunities = []
        for game in games:
            opportunities = self.simulate_live_totals(game)
            all_opportunities.extend(opportunities)

        print(f"[OK] Found {len(all_opportunities)} betting opportunities\n")

        # Calculate ROI
        print("Calculating profitability...")
        results = self.calculate_roi(all_opportunities)

        # Print results
        self._print_results(results)

        return results

    def _print_results(self, results: Dict):
        """Print simulation results"""

        print("="*80)
        print("PROFITABILITY RESULTS")
        print("="*80)
        print(f"Total Opportunities: {results['total_opportunities']}")
        print(f"Wins: {results['wins']}")
        print(f"Losses: {results['losses']}")
        print(f"Win Rate: {results['win_rate']:.1f}%")
        print(f"\nTotal Profit/Loss: ${results['total_profit']:+,.2f}")
        print(f"Total Risked: ${results['total_risked']:,.2f}")
        print(f"ROI: {results['roi']:+.1f}%\n")

        # Breakeven analysis
        breakeven_rate = 52.4  # Need 52.4% to breakeven at -110
        print(f"Breakeven Win Rate (at -110): 52.4%")
        if results['win_rate'] > breakeven_rate:
            print(f"[PROFITABLE] +{results['win_rate'] - breakeven_rate:.1f}% edge over breakeven\n")
        else:
            print(f"[UNPROFITABLE] -{breakeven_rate - results['win_rate']:.1f}% below breakeven\n")

        # By timing
        print("="*80)
        print("RESULTS BY TIMING")
        print("="*80)
        for timing, stats in results['by_timing'].items():
            print(f"\n{timing}:")
            print(f"  Opportunities: {stats['count']}")
            print(f"  Win Rate: {stats['win_rate']:.1f}%")
            edge = "PROFITABLE" if stats['win_rate'] > 52.4 else "UNPROFITABLE"
            print(f"  Status: {edge}")

        # By deviation
        print("\n" + "="*80)
        print("RESULTS BY DEVIATION SIZE")
        print("="*80)

        if results['high_deviation']:
            print(f"\nHigh Deviation (>=2.0 std dev):")
            print(f"  Opportunities: {results['high_deviation']['count']}")
            print(f"  Win Rate: {results['high_deviation']['win_rate']:.1f}%")

        if results['medium_deviation']:
            print(f"\nMedium Deviation (1.5-2.0 std dev):")
            print(f"  Opportunities: {results['medium_deviation']['count']}")
            print(f"  Win Rate: {results['medium_deviation']['win_rate']:.1f}%")

        # Sample opportunities
        print("\n" + "="*80)
        print("SAMPLE OPPORTUNITIES")
        print("="*80)
        for opp in results['sample_opportunities'][:5]:
            result = "WIN" if opp['won'] else "LOSS"
            print(f"\n{opp['date']} - {opp['timing']}")
            print(f"  {opp['matchup']}")
            print(f"  Closing Total: {opp['closing_total']:.1f}")
            print(f"  Live Implied: {opp['live_implied_total']:.1f}")
            print(f"  Deviation: {opp['deviation']:+.1f} ({opp['deviation_sigma']:+.2f} std dev)")
            print(f"  Bet: {opp['bet_side'].upper()} -> {result}")
            print(f"  Actual Final: {opp['actual_final']}")


def main():
    """Run profitability simulation"""

    # Test different threshold levels
    thresholds = [1.5, 1.75, 2.0]

    for threshold_sigma in thresholds:
        simulator = RegressionProfitabilitySimulator(
            std_deviation=17.08,
            threshold_sigma=threshold_sigma
        )

        results = simulator.run_simulation(games_limit=300)

        print("\n" + "="*80)
        print(f"THRESHOLD {threshold_sigma} STD DEV COMPLETE")
        print("="*80 + "\n")

        input("Press Enter to continue to next threshold...")


if __name__ == "__main__":
    main()
