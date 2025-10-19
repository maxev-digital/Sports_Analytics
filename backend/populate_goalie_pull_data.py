"""
Populate NHL Goalie Pull Database
Scrapes historical goalie pull events from NHL API and builds team/coach profiles
Run this script to initialize or update the database with real data
"""
import asyncio
import logging
from datetime import datetime, timedelta
from nhl_goalie_pull_scraper import NHLGoaliePullScraper
from nhl_goalie_pull_database import get_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def populate_historical_data(days_back: int = 90):
    """
    Scrape and populate historical goalie pull data

    Args:
        days_back: Number of days of historical data to collect (default: 90 days / 3 months)
    """
    logger.info(f"Starting historical data collection for last {days_back} days...")

    # Initialize scraper and database
    scraper = NHLGoaliePullScraper()
    db = get_database()

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    logger.info(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

    # Collect all pull events
    pulls = await scraper.collect_historical_data(
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )

    if not pulls:
        logger.warning("No goalie pull events found!")
        return

    logger.info(f"Found {len(pulls)} goalie pull events. Inserting into database...")

    # Insert all pull events into database
    season = '2024-25'  # Current NHL season
    teams_seen = set()
    coaches_seen = set()

    for pull in pulls:
        # Add season info
        pull['season'] = season

        # Determine opponent and home/away
        # Note: scraper needs to be updated to include this info
        # For now, set defaults
        pull['opponent'] = 'Unknown'
        pull['is_home'] = False
        pull['game_outcome'] = None

        # Insert into database
        try:
            db.insert_pull_event(pull)
            teams_seen.add(pull['team'])
            if pull.get('coach'):
                coaches_seen.add(pull['coach'])
        except Exception as e:
            logger.error(f"Error inserting pull event: {e}")

    logger.info(f"Inserted {len(pulls)} pull events for {len(teams_seen)} teams")

    # Rebuild team profiles
    logger.info("Rebuilding team profiles...")
    for team in teams_seen:
        try:
            db.rebuild_team_profile(team, season)
            db.update_empty_net_stats(team, season)
        except Exception as e:
            logger.error(f"Error rebuilding profile for {team}: {e}")

    # Rebuild coach profiles
    logger.info("Rebuilding coach profiles...")
    for coach in coaches_seen:
        if coach and coach != 'Unknown':
            try:
                db.rebuild_coach_profile(coach)
            except Exception as e:
                logger.error(f"Error rebuilding profile for {coach}: {e}")

    # Show summary
    logger.info("\n" + "="*60)
    logger.info("DATABASE POPULATION COMPLETE")
    logger.info("="*60)
    logger.info(f"Total pull events: {len(pulls)}")
    logger.info(f"Teams with profiles: {len(teams_seen)}")
    logger.info(f"Coaches with profiles: {len(coaches_seen)}")

    # Show top aggressive teams
    logger.info("\nTop 10 Most Aggressive Teams (by analytics score):")
    all_teams = db.get_all_teams_with_profiles(season)

    team_scores = []
    for team in all_teams:
        profile = db.get_team_profile(team, season)
        if profile:
            team_scores.append((
                team,
                profile.get('analytics_score', 0),
                profile.get('total_pulls', 0),
                profile.get('current_coach', 'Unknown')
            ))

    team_scores.sort(key=lambda x: x[1], reverse=True)

    for i, (team, score, pulls, coach) in enumerate(team_scores[:10], 1):
        logger.info(f"{i:2d}. {team:25s} | Score: {score:4.1f}/10 | {pulls:3d} pulls | Coach: {coach}")

    logger.info("\n" + "="*60)
    logger.info("Database is ready for live tracking!")
    logger.info("="*60)


async def update_recent_data(days: int = 7):
    """
    Update database with recent games only (for daily updates)

    Args:
        days: Number of recent days to update (default: 7)
    """
    logger.info(f"Updating database with last {days} days of data...")
    await populate_historical_data(days_back=days)


if __name__ == "__main__":
    import sys

    # Allow command line argument for days
    days_back = 90  # Default: 3 months

    if len(sys.argv) > 1:
        try:
            days_back = int(sys.argv[1])
        except ValueError:
            logger.error("Usage: python populate_goalie_pull_data.py [days_back]")
            sys.exit(1)

    # Run the population
    asyncio.run(populate_historical_data(days_back=days_back))
