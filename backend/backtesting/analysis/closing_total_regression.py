"""
Closing Total vs Actual Total Regression Analysis

Analyzes the relationship between pregame closing totals and actual game totals
to identify profitable live betting windows based on regression to the mean.

Strategy Concept:
- Closing totals are efficient market predictions
- Games deviate from closing totals during live play
- When deviation exceeds normal variance, regression occurs
- This creates profitable live betting opportunities

Analysis Output:
1. Mean/Std deviation of (Actual Total - Closing Total)
2. Confidence intervals for normal variance
3. Quarter-by-quarter progression patterns
4. Profitable betting trigger points
5. Expected ROI by deviation level
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
import statistics

sys.path.append(str(Path(__file__).parent.parent))
from database.backtest_db import BacktestDB


class ClosingTotalRegressionAnalysis:
    """Analyze closing total vs actual total regression patterns"""

    def __init__(self):
        self.db = BacktestDB()

    def get_games_with_closing_totals(self) -> List[Dict]:
        """
        Fetch all games that have closing total data from odds_history

        Returns:
            List of game dicts with closing totals and actual scores
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Get all games
        cursor.execute("""
            SELECT game_id, date, home_team, away_team,
                   q1_home, q2_home, q3_home, q4_home, home_score,
                   q1_away, q2_away, q3_away, q4_away, away_score
            FROM historical_games
            ORDER BY date
        """)

        games = []
        for row in cursor.fetchall():
            game_id, date, home_team, away_team = row[:4]
            q1_h, q2_h, q3_h, q4_h, final_h = row[4:9]
            q1_a, q2_a, q3_a, q4_a, final_a = row[9:14]

            # Skip if missing quarter data
            if None in [q1_h, q2_h, q3_h, q4_h, q1_a, q2_a, q3_a, q4_a]:
                continue

            # Look up closing total from odds_history
            cursor.execute("""
                SELECT line_value
                FROM odds_history
                WHERE sport = 'basketball_nba'
                  AND market_type = 'totals'
                  AND date(timestamp) = date(?)
                  AND (
                      (home_team LIKE ? AND away_team LIKE ?)
                      OR (home_team LIKE ? AND away_team LIKE ?)
                  )
                ORDER BY timestamp DESC
                LIMIT 1
            """, (
                date,
                f"%{home_team.split()[-1]}%",
                f"%{away_team.split()[-1]}%",
                f"%{home_team}%",
                f"%{away_team}%"
            ))

            closing_total_row = cursor.fetchone()
            if not closing_total_row or closing_total_row[0] is None:
                continue

            closing_total = closing_total_row[0]
            actual_total = final_h + final_a

            games.append({
                'game_id': game_id,
                'date': date,
                'home_team': home_team,
                'away_team': away_team,
                'closing_total': closing_total,
                'actual_total': actual_total,
                'deviation': actual_total - closing_total,
                'q1_total': q1_h + q1_a,
                'q2_total': q2_h + q2_a,
                'q3_total': q3_h + q3_a,
                'q4_total': q4_h + q4_a,
                'half_total': q1_h + q2_h + q1_a + q2_a,
                'q3_end_total': q1_h + q2_h + q3_h + q1_a + q2_a + q3_a
            })

        conn.close()
        return games

    def analyze_regression_patterns(self, games: List[Dict]) -> Dict:
        """
        Analyze regression to mean patterns

        Args:
            games: List of games with closing totals

        Returns:
            Analysis results dict
        """
        if not games:
            return {'error': 'No games with closing total data'}

        # Calculate deviations
        deviations = [g['deviation'] for g in games]

        # Basic statistics
        mean_dev = statistics.mean(deviations)
        std_dev = statistics.stdev(deviations)

        # Confidence intervals
        ci_68 = std_dev * 1  # 68% of games
        ci_95 = std_dev * 2  # 95% of games
        ci_99 = std_dev * 3  # 99.7% of games

        # Count distribution
        overs = sum(1 for d in deviations if d > 0)
        unders = sum(1 for d in deviations if d < 0)
        pushes = sum(1 for d in deviations if d == 0)

        # Analyze by deviation buckets
        buckets = self._analyze_deviation_buckets(games, std_dev)

        # Quarter progression patterns
        progression = self._analyze_quarter_progression(games)

        return {
            'total_games': len(games),
            'mean_deviation': mean_dev,
            'std_deviation': std_dev,
            'confidence_intervals': {
                '68%': ci_68,
                '95%': ci_95,
                '99.7%': ci_99
            },
            'distribution': {
                'overs': overs,
                'unders': unders,
                'pushes': pushes,
                'over_pct': overs / len(games) * 100
            },
            'deviation_buckets': buckets,
            'quarter_progression': progression
        }

    def _analyze_deviation_buckets(self, games: List[Dict], std_dev: float) -> Dict:
        """Analyze games by deviation magnitude"""

        buckets = {
            'within_1std': [],
            'between_1_2std': [],
            'beyond_2std': []
        }

        for game in games:
            abs_dev = abs(game['deviation'])
            if abs_dev <= std_dev:
                buckets['within_1std'].append(game)
            elif abs_dev <= 2 * std_dev:
                buckets['between_1_2std'].append(game)
            else:
                buckets['beyond_2std'].append(game)

        return {
            'within_1std': {
                'count': len(buckets['within_1std']),
                'percentage': len(buckets['within_1std']) / len(games) * 100
            },
            'between_1_2std': {
                'count': len(buckets['between_1_2std']),
                'percentage': len(buckets['between_1_2std']) / len(games) * 100
            },
            'beyond_2std': {
                'count': len(buckets['beyond_2std']),
                'percentage': len(buckets['beyond_2std']) / len(games) * 100
            }
        }

    def _analyze_quarter_progression(self, games: List[Dict]) -> Dict:
        """
        Analyze how totals progress quarter by quarter
        relative to closing total
        """

        # Calculate expected pace (closing total / 4 quarters)
        q1_deviations = []
        half_deviations = []
        q3_deviations = []

        for game in games:
            expected_q1 = game['closing_total'] / 4
            expected_half = game['closing_total'] / 2
            expected_q3 = game['closing_total'] * 0.75

            q1_deviations.append(game['q1_total'] - expected_q1)
            half_deviations.append(game['half_total'] - expected_half)
            q3_deviations.append(game['q3_end_total'] - expected_q3)

        return {
            'q1': {
                'mean_deviation': statistics.mean(q1_deviations),
                'std_deviation': statistics.stdev(q1_deviations)
            },
            'halftime': {
                'mean_deviation': statistics.mean(half_deviations),
                'std_deviation': statistics.stdev(half_deviations)
            },
            'q3_end': {
                'mean_deviation': statistics.mean(q3_deviations),
                'std_deviation': statistics.stdev(q3_deviations)
            }
        }

    def identify_betting_opportunities(self, games: List[Dict], std_dev: float) -> Dict:
        """
        Identify profitable betting scenarios based on regression

        Strategy: When live total deviates beyond normal variance,
        bet on regression back to closing total.
        """

        # Simulate halftime betting opportunities
        # Assumption: We can bet live total at halftime

        opportunities = []

        for game in games:
            # Calculate implied live total at halftime
            # (Assumes live total = 2x halftime score)
            implied_live_total = game['half_total'] * 2
            closing_total = game['closing_total']

            # Deviation of implied live total from closing
            live_deviation = implied_live_total - closing_total

            # Only bet when deviation exceeds threshold
            threshold = std_dev * 1.5  # 1.5 standard deviations

            if abs(live_deviation) > threshold:
                # Bet direction: If live total too high, bet under. If too low, bet over.
                bet_side = 'under' if live_deviation > 0 else 'over'

                # Determine if bet won
                actual_2h_total = game['q3_total'] + game['q4_total']
                implied_2h_total = implied_live_total / 2

                if bet_side == 'under':
                    won = actual_2h_total < implied_2h_total
                else:
                    won = actual_2h_total > implied_2h_total

                opportunities.append({
                    'game_id': game['game_id'],
                    'date': game['date'],
                    'closing_total': closing_total,
                    'implied_live_total': implied_live_total,
                    'deviation': live_deviation,
                    'bet_side': bet_side,
                    'won': won
                })

        if not opportunities:
            return {'message': 'No opportunities found with current threshold'}

        wins = sum(1 for o in opportunities if o['won'])
        losses = len(opportunities) - wins
        win_rate = wins / len(opportunities) * 100 if opportunities else 0

        # Assume -110 odds
        roi = ((wins * 0.91) - losses) / len(opportunities) * 100 if opportunities else 0

        return {
            'total_opportunities': len(opportunities),
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'roi': roi,
            'sample_opportunities': opportunities[:5]
        }

    def run_analysis(self) -> Dict:
        """Run complete regression analysis"""

        print("\n" + "="*80)
        print("CLOSING TOTAL vs ACTUAL TOTAL REGRESSION ANALYSIS")
        print("="*80)
        print("Analyzing relationship between pregame closing totals and actual game totals")
        print("="*80 + "\n")

        # Fetch games with closing totals
        print("Loading games with closing total data...")
        games = self.get_games_with_closing_totals()
        print(f"[OK] Found {len(games)} games with closing totals\n")

        if len(games) < 50:
            print(f"[WARNING] Only {len(games)} games available. Need more odds data.")
            print("          Background odds fetching is still running...")
            return {'error': 'Insufficient data'}

        # Run regression analysis
        print("Analyzing regression patterns...")
        analysis = self.analyze_regression_patterns(games)

        # Print results
        self._print_results(analysis)

        # Identify betting opportunities
        print("\n" + "="*80)
        print("BETTING OPPORTUNITY SIMULATION")
        print("="*80)
        print("Simulating halftime live total bets based on regression...\n")

        opportunities = self.identify_betting_opportunities(games, analysis['std_deviation'])
        self._print_opportunities(opportunities)

        return {
            'analysis': analysis,
            'opportunities': opportunities,
            'games_analyzed': len(games)
        }

    def _print_results(self, analysis: Dict):
        """Print analysis results in readable format"""

        print("="*80)
        print("VARIANCE ANALYSIS")
        print("="*80)
        print(f"Total Games Analyzed: {analysis['total_games']}")
        print(f"Mean Deviation: {analysis['mean_deviation']:+.2f} points")
        print(f"Standard Deviation: {analysis['std_deviation']:.2f} points")
        print()

        print("Confidence Intervals (Normal Variance):")
        print(f"  68% of games: ±{analysis['confidence_intervals']['68%']:.2f} points")
        print(f"  95% of games: ±{analysis['confidence_intervals']['95%']:.2f} points")
        print(f"  99.7% of games: ±{analysis['confidence_intervals']['99.7%']:.2f} points")
        print()

        print("Distribution:")
        print(f"  Overs: {analysis['distribution']['overs']} ({analysis['distribution']['over_pct']:.1f}%)")
        print(f"  Unders: {analysis['distribution']['unders']}")
        print(f"  Pushes: {analysis['distribution']['pushes']}")
        print()

        print("="*80)
        print("QUARTER PROGRESSION PATTERNS")
        print("="*80)
        prog = analysis['quarter_progression']
        print(f"After Q1: Mean Dev {prog['q1']['mean_deviation']:+.2f} ± {prog['q1']['std_deviation']:.2f} pts")
        print(f"At Halftime: Mean Dev {prog['halftime']['mean_deviation']:+.2f} ± {prog['halftime']['std_deviation']:.2f} pts")
        print(f"After Q3: Mean Dev {prog['q3_end']['mean_deviation']:+.2f} ± {prog['q3_end']['std_deviation']:.2f} pts")
        print()

    def _print_opportunities(self, opp: Dict):
        """Print betting opportunities"""

        if 'message' in opp:
            print(opp['message'])
            return

        print(f"Total Opportunities: {opp['total_opportunities']}")
        print(f"Wins: {opp['wins']}")
        print(f"Losses: {opp['losses']}")
        print(f"Win Rate: {opp['win_rate']:.1f}%")
        print(f"ROI (at -110 odds): {opp['roi']:+.1f}%")
        print()

        if opp.get('sample_opportunities'):
            print("Sample Opportunities:")
            for sample in opp['sample_opportunities']:
                result = "WIN" if sample['won'] else "LOSS"
                print(f"  {sample['date']}: Closing {sample['closing_total']:.1f}, "
                      f"Live (implied) {sample['implied_live_total']:.1f}, "
                      f"Dev {sample['deviation']:+.1f} → {sample['bet_side'].upper()} → {result}")


def main():
    """Run the analysis"""
    analysis = ClosingTotalRegressionAnalysis()
    results = analysis.run_analysis()

    if 'error' not in results:
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print(f"Games Analyzed: {results['games_analyzed']}")
        print("\nKey Findings:")
        print(f"  - Typical variance window: ±{results['analysis']['std_deviation']:.1f} points")
        print(f"  - Market efficiency: {results['analysis']['distribution']['over_pct']:.1f}% overs")
        print(f"  - Regression betting opportunities found: {results['opportunities'].get('total_opportunities', 0)}")
        print("="*80)


if __name__ == "__main__":
    main()
