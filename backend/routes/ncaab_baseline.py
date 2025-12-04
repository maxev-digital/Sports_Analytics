"""NCAAB Live Baseline Comparison - With team name normalization"""

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

espn_client = ESPNNCAABClient()
stats_calculator = NCAABLiveStatsCalculator()
teamrankings_scraper = TeamRankingsNCAABScraper()


def normalize_team_name(espn_name: str) -> str:
    """Strip mascot from ESPN team name"""
    mascots = ['Cardinals', 'Bearcats', 'Wildcats', 'Tigers', 'Bulldogs', 'Eagles',
               'Hawks', 'Tar Heels', 'Blue Devils', 'Spartans', 'Trojans', 'Bears',
               'Panthers', 'Lions', 'Cougars', 'Huskies', 'Terrapins', 'Buckeyes',
               'Mountain Hawks', 'Leopards', 'Cavaliers', 'Gaels', 'Zips',
               'Seminoles', 'Gators', 'Warriors', 'Purple Eagles']
    
    for mascot in mascots:
        if espn_name.endswith(f' {mascot}'):
            return espn_name[:-len(mascot)].strip()
    return espn_name


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
    """Get live vs baseline - with team name normalization"""
    try:
        espn_event_id = event_id

        if home_team and away_team and len(event_id) > 20:
            found_id = await find_espn_event_by_teams(home_team, away_team)
            if found_id:
                espn_event_id = found_id
            else:
                raise HTTPException(status_code=404, detail=f"ESPN event not found")

        live_box_score = await espn_client.get_live_box_score(espn_event_id)
        if not live_box_score or not live_box_score.get('is_live'):
            raise HTTPException(status_code=404, detail="Box score not found or game not live")

        # Normalize team names to match TeamRankings format
        home_team_name = normalize_team_name(live_box_score['home']['team_name'])
        away_team_name = normalize_team_name(live_box_score['away']['team_name'])
        logger.info(f"Normalized names: {away_team_name} @ {home_team_name}")

        all_team_stats = teamrankings_scraper.fetch_all_team_stats()
        home_baseline = all_team_stats.get(home_team_name)
        away_baseline = all_team_stats.get(away_team_name)

        if not home_baseline or not away_baseline:
            logger.warning(f"Missing baseline: home={home_baseline is not None}, away={away_baseline is not None}")
            raise HTTPException(status_code=404, detail=f"Baseline stats not found for {home_team_name if not home_baseline else away_team_name}")

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


@router.get("/api/ncaab/live-baseline-batch")
async def get_live_baseline_batch(event_ids: str):
    try:
        ids = [id.strip() for id in event_ids.split(',')]
        results = {}
        for event_id in ids:
            try:
                results[event_id] = await get_live_baseline_comparison(event_id)
            except Exception as e:
                results[event_id] = None
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
