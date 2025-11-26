"""
NCAAB Live Baseline Comparison API Endpoint - Now accepts team names to lookup ESPN IDs
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from datetime import datetime

from espn_ncaab_client import ESPNNCAABClient
from ncaab_live_stats_calculator import NCAABLiveStatsCalculator
from scrapers.teamrankings_ncaab_scraper import TeamRankingsNCAABScraper
from live_models import NCAABBaselineComparison, NCAABTeamBaselineAnalysis

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize clients
espn_client = ESPNNCAABClient()
stats_calculator = NCAABLiveStatsCalculator()
teamrankings_scraper = TeamRankingsNCAABScraper()


async def find_espn_event_by_teams(home_team: str, away_team: str) -> Optional[str]:
    """Find ESPN event ID by matching team names"""
    try:
        scoreboard = await espn_client.get_scoreboard()
        if not scoreboard:
            return None

        for event in scoreboard.get('events', []):
            try:
                competitors = event['competitions'][0]['competitors']
                teams = {c['team']['displayName']: c for c in competitors}
                team_names = list(teams.keys())

                home_match = any(home_team.lower() in team.lower() or team.lower() in home_team.lower() for team in team_names)
                away_match = any(away_team.lower() in team.lower() or team.lower() in away_team.lower() for team in team_names)

                if home_match and away_match:
                    logger.info(f"Found ESPN event {event['id']} for {away_team} @ {home_team}")
                    return event['id']
            except (KeyError, IndexError):
                continue

        return None
    except Exception as e:
        logger.error(f"Error finding ESPN event: {e}")
        return None


@router.get("/api/ncaab/live-baseline/{event_id}", response_model=NCAABBaselineComparison)
async def get_live_baseline_comparison(
    event_id: str,
    home_team: Optional[str] = Query(None),
    away_team: Optional[str] = Query(None)
):
    """Get live vs baseline - accepts ESPN ID or Odds API ID + team names"""
    try:
        espn_event_id = event_id

        # If team names provided and event_id looks like Odds API hash, lookup ESPN ID
        if home_team and away_team and len(event_id) > 20:
            found_id = await find_espn_event_by_teams(home_team, away_team)
            if found_id:
                espn_event_id = found_id
            else:
                raise HTTPException(status_code=404, detail=f"ESPN event not found for {away_team} @ {home_team}")

        # Fetch live box score from ESPN
        live_box_score = await espn_client.get_live_box_score(espn_event_id)

        if not live_box_score:
            raise HTTPException(status_code=404, detail=f"Box score not found")

        if not live_box_score.get('is_live'):
            raise HTTPException(status_code=400, detail="Game not live")

        # Get team names
        home_team_name = live_box_score['home']['team_name']
        away_team_name = live_box_score['away']['team_name']

        # Fetch baseline stats
        all_team_stats = teamrankings_scraper.fetch_all_team_stats()
        home_baseline = all_team_stats.get(home_team_name)
        away_baseline = all_team_stats.get(away_team_name)

        if not home_baseline or not away_baseline:
            raise HTTPException(status_code=404, detail="Baseline stats not found")

        # Calculate variance
        home_analysis = stats_calculator.analyze_team_performance(
            live_box_score=live_box_score, baseline_stats=home_baseline, team_side='home')
        away_analysis = stats_calculator.analyze_team_performance(
            live_box_score=live_box_score, baseline_stats=away_baseline, team_side='away')

        return NCAABBaselineComparison(
            game_id=event_id,
            home_team_analysis=NCAABTeamBaselineAnalysis(**home_analysis),
            away_team_analysis=NCAABTeamBaselineAnalysis(**away_analysis),
            is_live=live_box_score['is_live'],
            status=live_box_score['status'],
            last_updated=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

        # Get team names and normalize
        home_team_name = normalize_team_name(live_box_score["home"]["team_name"])
        away_team_name = normalize_team_name(live_box_score["away"]["team_name"])

        logger.info(f"Looking up baseline stats for {away_team_name} @ {home_team_name}")
        # Get team names and normalize
        home_team_name = normalize_team_name(live_box_score["home"]["team_name"])
        away_team_name = normalize_team_name(live_box_score["away"]["team_name"])

        logger.info(f"Looking up baseline stats for {away_team_name} @ {home_team_name}")
        # Get team names and normalize
        home_team_name = normalize_team_name(live_box_score["home"]["team_name"])
        away_team_name = normalize_team_name(live_box_score["away"]["team_name"])

        logger.info(f"Looking up baseline stats for {away_team_name} @ {home_team_name}")
        # Get team names and normalize
        home_team_name = normalize_team_name(live_box_score["home"]["team_name"])
        away_team_name = normalize_team_name(live_box_score["away"]["team_name"])

        logger.info(f"Looking up baseline stats for {away_team_name} @ {home_team_name}")
        # Get team names and normalize
        home_team_name = normalize_team_name(live_box_score["home"]["team_name"])
        away_team_name = normalize_team_name(live_box_score["away"]["team_name"])

        logger.info(f"Looking up baseline stats for {away_team_name} @ {home_team_name}")
        ids = [id.strip() for id in event_ids.split(',')]
        results = {}

        for event_id in ids:
            try:
                comparison = await get_live_baseline_comparison(event_id)
                results[event_id] = comparison
            except Exception as e:
                logger.warning(f"Failed for {event_id}: {e}")
                results[event_id] = None

        return results
    except Exception as e:
        logger.error(f"Batch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def normalize_team_name(espn_name: str) -> str:
    """Strip mascot from ESPN team name to match TeamRankings format"""
    # Common NCAAB mascots to remove
    mascots = [
        'Cardinals', 'Bearcats', 'Wildcats', 'Tigers', 'Bulldogs', 'Eagles',
        'Hawks', 'Tar Heels', 'Blue Devils', 'Spartans', 'Trojans', 'Bears',
        'Panthers', 'Lions', 'Cougars', 'Huskies', 'Terrapins', 'Buckeyes',
        'Hoosiers', 'Jayhawks', 'Orangemen', 'Orange', 'Demon Deacons',
        'Seminoles', 'Gators', 'Volunteers', 'Commodores', 'Aggies',
        'Red Raiders', 'Longhorns', 'Sooners', 'Cowboys', 'Mountaineers',
        'Cyclones', 'Badgers', 'Golden Gophers', 'Boilermakers', 'Illini',
        'Scarlet Knights', 'Nittany Lions', 'Wolverines', 'Cornhuskers',
        'Fighting Irish', 'Bruins', 'Sun Devils', 'Ducks', 'Beavers',
        'Utes', 'Buffaloes', 'Hoya', 'Hoyas', 'Friars', 'Musketeers',
        'Billikens', 'Explorers', 'Gaels', 'Minutemen', 'Rams', 'Owls',
        'Colonials', 'Revolutionaries', 'Spiders', 'Tribe', 'Dukes',
        'Monarchs', 'Seahawks', 'Highlanders', 'Terriers', 'River Hawks',
        'Mountain Hawks', 'Leopards', 'Crusaders', 'Greyhounds',
        'Red Storm', 'Golden Eagles', 'Blue Jays', 'Muskies', 'Pirates',
        'Red Flash', 'Bonnies', 'Flyers', 'Rams', 'Billikens', 'Ramblers',
        'Redbirds', 'Salukis', 'Bears', 'Panthers', 'Braves'
    ]
    
    # Try removing each mascot
    for mascot in mascots:
        if espn_name.endswith(f' {mascot}'):
            return espn_name[:-len(mascot)].strip()
    
    # If no mascot found, return as is
    return espn_name
