"""
Master Script - Basketball Reversal Strategy Analysis
Runs all 3 steps: Data Fetch → Backtest → Kelly Simulation
"""

import asyncio
import logging
from pathlib import Path

# Import our modules
from reversal_data_fetcher import BasketballDataFetcher
from reversal_backtest_engine import ReversalBacktester
from reversal_kelly_simulator import KellySimulator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data" / "reversal_backtesting"
DATA_DIR.mkdir(parents=True, exist_ok=True)


async def step_1_fetch_data():
    """Step 1: Fetch historical quarter-by-quarter data"""
    logger.info("\n" + "="*80)
    logger.info("STEP 1: FETCHING HISTORICAL DATA (2023-2024 Season)")
    logger.info("="*80)

    fetcher = BasketballDataFetcher()

    # Fetch NBA
    logger.info("\n[1/2] Fetching NBA games...")
    nba_games = await fetcher.fetch_nba_games("2023-24")
    await fetcher.save_to_csv(nba_games, "nba_2023_24.csv")

    # Fetch NCAA
    logger.info("\n[2/2] Fetching NCAA Men's games...")
    ncaa_games = await fetcher.fetch_ncaa_games("2023-24")
    await fetcher.save_to_csv(ncaa_games, "ncaa_2023_24.csv")

    logger.info(f"\n✓ DATA FETCH COMPLETE")
    logger.info(f"  NBA: {len(nba_games)} games")
    logger.info(f"  NCAA: {len(ncaa_games)} games")
    logger.info(f"  Total: {len(nba_games) + len(ncaa_games)} games")

    return {
        'nba_games': len(nba_games),
        'ncaa_games': len(ncaa_games)
    }


def step_2_run_backtests():
    """Step 2: Run Q1-Q2 → Q3 reversal backtests"""
    logger.info("\n" + "="*80)
    logger.info("STEP 2: RUNNING REVERSAL BACKTESTS")
    logger.info("="*80)

    backtester = ReversalBacktester()

    # NBA
    nba_results = backtester.run_backtest('NBA', 'nba_2023_24.csv')

    # NCAA
    ncaa_results = backtester.run_backtest('NCAA', 'ncaa_2023_24.csv')

    # Save results
    backtester.save_results('backtest_results.json')

    # Summary
    summary = backtester._calculate_summary()
    logger.info(f"\n✓ BACKTEST COMPLETE")
    logger.info(f"  Total Triggers: {summary['total_triggers']}")
    logger.info(f"  Total Bets: {summary['total_bets']}")
    logger.info(f"  Win Rate: {summary['overall_win_rate']}%")
    logger.info(f"  ROI: {summary['overall_roi']}%")
    logger.info(f"  EV: +{summary['overall_ev']}%")

    return summary


def step_3_simulate_kelly():
    """Step 3: Simulate 1/4 Kelly bankroll growth"""
    logger.info("\n" + "="*80)
    logger.info("STEP 3: SIMULATING 1/4 KELLY BANKROLL GROWTH")
    logger.info("="*80)

    simulator = KellySimulator(
        starting_bankroll=20000.0,
        win_rate=0.556,
        odds=-110,
        kelly_fraction=0.25,
        total_bets=1044
    )

    # Monte Carlo
    logger.info("\nRunning Monte Carlo simulation (100 runs)...")
    monte_carlo = simulator.run_monte_carlo(num_simulations=100)

    # Monthly projection
    logger.info("\nGenerating monthly projection...")
    monthly = simulator.simulate_monthly_growth()

    # Save
    simulator.save_results(monte_carlo, monthly, 'kelly_projection.json')

    logger.info(f"\n✓ SIMULATION COMPLETE")
    logger.info(f"  Starting: ${monte_carlo['starting_bankroll']:,.2f}")
    logger.info(f"  Average Final: ${monte_carlo['avg_final_bankroll']:,.2f}")
    logger.info(f"  Average ROI: {monte_carlo['avg_roi']}%")
    logger.info(f"  Ruin Risk: {monte_carlo['ruin_risk']}%")

    return monte_carlo


async def main():
    """Run complete analysis pipeline"""
    logger.info("\n" + "="*80)
    logger.info("BASKETBALL REVERSAL STRATEGY - COMPLETE ANALYSIS")
    logger.info("="*80)

    try:
        # Step 1: Fetch data
        data_stats = await step_1_fetch_data()

        # Step 2: Backtest
        backtest_summary = step_2_run_backtests()

        # Step 3: Kelly simulation
        kelly_results = step_3_simulate_kelly()

        # Final summary
        logger.info("\n" + "="*80)
        logger.info("ANALYSIS COMPLETE - SUMMARY")
        logger.info("="*80)
        logger.info(f"\n📊 DATA COLLECTED:")
        logger.info(f"   NBA: {data_stats.get('nba_games', 0)} games")
        logger.info(f"   NCAA: {data_stats.get('ncaa_games', 0)} games")

        logger.info(f"\n📈 BACKTEST RESULTS:")
        logger.info(f"   Triggers: {backtest_summary.get('total_triggers', 0)}")
        logger.info(f"   Win Rate: {backtest_summary.get('overall_win_rate', 0)}%")
        logger.info(f"   ROI: {backtest_summary.get('overall_roi', 0)}%")

        logger.info(f"\n💰 KELLY PROJECTION ($20,000 start):")
        logger.info(f"   Average Final: ${kelly_results.get('avg_final_bankroll', 0):,.2f}")
        logger.info(f"   Average ROI: {kelly_results.get('avg_roi', 0)}%")
        logger.info(f"   Ruin Risk: {kelly_results.get('ruin_risk', 0)}%")

        logger.info(f"\n✅ All results saved to: {DATA_DIR}")

    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
