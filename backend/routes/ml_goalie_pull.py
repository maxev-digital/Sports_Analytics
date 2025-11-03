"""API routes for ML-powered NHL goalie pull predictions"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml/goalie-pull", tags=["ml", "goalie-pull"])


def set_dependencies(predictor, analyzer, game_tracker):
    """
    Set ML predictor, analyzer, and game tracker dependencies.
    Called from main.py during startup.
    """
    router.predictor = predictor
    router.analyzer = analyzer
    router.tracker = game_tracker


@router.get("/test")
async def test_ml_goalie_pull():
    """Test endpoint to verify ML goalie pull router is registered"""
    return {
        "status": "ML Goalie Pull router is working",
        "predictor_loaded": hasattr(router, 'predictor'),
        "analyzer_loaded": hasattr(router, 'analyzer'),
        "tracker_loaded": hasattr(router, 'tracker')
    }


@router.get("/predict")
async def predict_goalie_pull(
    team: str,
    score_diff: int,
    time_remaining: int,
    period: int = 3,
    home_game: bool = True,
    opponent: str = None,
    division_game: bool = False
):
    """
    ML-powered goalie pull prediction for live NHL games

    Args:
        team: Team name (e.g., "Boston Bruins")
        score_diff: Score differential (negative if losing, e.g., -1)
        time_remaining: Seconds remaining in period
        period: Current period (default 3)
        home_game: Whether team is at home (default True)
        opponent: Opponent team name (optional)
        division_game: Whether division game (default False)

    Returns:
        ML prediction with pull probability, expected time, betting recommendations
    """
    try:
        prediction = router.predictor.predict(
            team=team,
            score_differential=score_diff,
            time_remaining_seconds=time_remaining,
            period=period,
            home_game=home_game,
            opponent=opponent,
            division_game=division_game,
            season="20232024"
        )

        return prediction

    except Exception as e:
        logger.error(f"Error predicting goalie pull: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team-analysis/{team}")
async def get_team_goalie_pull_analysis(team: str, season: str = "20232024"):
    """
    Get complete goalie pull pattern analysis for a team

    Args:
        team: Team name
        season: Season (default "20232024")

    Returns:
        Team patterns, aggression level, trends, insights
    """
    try:
        analysis = router.analyzer.analyze_team(team, season)
        return analysis

    except Exception as e:
        logger.error(f"Error analyzing team {team}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/live-games")
async def get_live_goalie_pull_predictions():
    """
    Get goalie pull predictions for all live NHL games

    Automatically detects live NHL games and provides predictions for teams that are losing
    """
    try:
        predictions = []

        # Get all live NHL games from tracker
        for game in router.tracker.games.values():
            # Only analyze live NHL games
            if game.sport_key != 'icehockey_nhl' or game.status != 'live':
                continue

            # Get current score
            home_score = getattr(game.home_team, 'score', 0)
            away_score = getattr(game.away_team, 'score', 0)

            # Check clock/period if available
            period = getattr(game, 'period', 3)
            time_remaining = getattr(game, 'time_remaining_seconds', 180)

            # Check if home team is losing
            if home_score < away_score and period >= 3:
                score_diff = home_score - away_score

                prediction = router.predictor.predict(
                    team=game.home_team.name,
                    score_differential=score_diff,
                    time_remaining_seconds=time_remaining,
                    period=period,
                    home_game=True,
                    opponent=game.away_team.name,
                    season="20232024"
                )

                if prediction.get('alert_level') in ['CRITICAL', 'HIGH']:
                    predictions.append({
                        'game_id': game.id,
                        'matchup': f"{game.away_team.name} @ {game.home_team.name}",
                        **prediction
                    })

            # Check if away team is losing
            if away_score < home_score and period >= 3:
                score_diff = away_score - home_score

                prediction = router.predictor.predict(
                    team=game.away_team.name,
                    score_differential=score_diff,
                    time_remaining_seconds=time_remaining,
                    period=period,
                    home_game=False,
                    opponent=game.home_team.name,
                    season="20232024"
                )

                if prediction.get('alert_level') in ['CRITICAL', 'HIGH']:
                    predictions.append({
                        'game_id': game.id,
                        'matchup': f"{game.away_team.name} @ {game.home_team.name}",
                        **prediction
                    })

        # Sort by alert level
        alert_priority = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        predictions.sort(key=lambda x: alert_priority.get(x.get('alert_level', 'LOW'), 99))

        return {
            "count": len(predictions),
            "predictions": predictions,
            "note": "ML-powered goalie pull predictions for live NHL games. CRITICAL/HIGH alerts indicate imminent pulls."
        }

    except Exception as e:
        logger.error(f"Error fetching live goalie pull predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
