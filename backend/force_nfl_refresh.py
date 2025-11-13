"""Force refresh NFL TeamRankings cache to get current season data with ranks"""
import sys
import os
import logging

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from scrapers.teamrankings_nfl_scraper import TeamRankingsNFLScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("🔄 Forcing NFL TeamRankings cache refresh...")

    scraper = TeamRankingsNFLScraper()

    # Force refresh (bypass cache)
    all_stats = scraper.fetch_all_team_stats(force_refresh=True)

    if not all_stats:
        logger.error("❌ Failed to fetch NFL stats")
        return False

    logger.info(f"✅ Successfully fetched stats for {len(all_stats)} NFL teams")

    # Test a few teams to verify data and ranks
    test_teams = ['New England', 'Kansas City', 'NY Jets']

    for team in test_teams:
        stats = all_stats.get(team)
        if stats:
            logger.info(f"\n{team}:")
            logger.info(f"  Record: {stats['wins']}-{stats['losses']} ({stats['games_played']} GP)")
            logger.info(f"  PPG: {stats['pts_per_game']} (Rank: {stats.get('points_per_game_rank', 'MISSING')})")
            logger.info(f"  3rd Down: {stats['third_down_conversion_pct']}% (Rank: {stats.get('third_down_pct_rank', 'MISSING')})")
            logger.info(f"  Red Zone: {stats['red_zone_scoring_pct']}% (Rank: {stats.get('red_zone_pct_rank', 'MISSING')})")
        else:
            logger.warning(f"  {team}: NOT FOUND")

    return True

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("\n✅ NFL cache refresh complete! Restart backend to use new data.")
    else:
        logger.error("\n❌ NFL cache refresh failed")
        sys.exit(1)
