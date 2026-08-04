"""
Shared game serialization cache.

Separating this from main.py so both main.py and routes/games.py can import it
without circular imports. The cache is populated by _get_all_games_response()
which is called on every /api/games request.
"""
import json
import logging
import time

import numpy as np
from fastapi.responses import Response

logger = logging.getLogger(__name__)

_GAMES_CACHE_TTL = 30  # seconds

# Shared mutable dict — populated in place so importers always see the latest state.
games_serialized_cache: dict = {
    "json_bytes": None,
    "list_data": None,
    "ts": 0.0,
    "count": 0,
}

SPORT_MAP = {
    'basketball_nba': 'NBA', 'basketball_nba_preseason': 'NBA',
    'basketball_ncaab': 'NCAAB', 'americanfootball_nfl': 'NFL',
    'americanfootball_ncaaf': 'NCAAF', 'icehockey_nhl': 'NHL',
    'baseball_mlb': 'MLB', 'basketball_wnba': 'WNBA',
    'tennis_atp_wimbledon': 'Tennis', 'tennis_wta_wimbledon': 'Tennis',
    'mma_mixed_martial_arts': 'MMA',
}


def convert_numpy_types(obj):
    """Recursively convert numpy types to Python native types for JSON serialisation."""
    if isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj


def serialize_games(games) -> list:
    """Convert game objects → JSON-safe dicts. Caller is responsible for caching."""
    from volatility_detector_simple import detect_volatility_opportunities
    games = detect_volatility_opportunities(games)
    games_dicts = [game.model_dump() for game in games]
    for game_dict, game_obj in zip(games_dicts, games):
        game_dict['sport_key'] = game_obj.state.sport_key
        game_dict['sport'] = SPORT_MAP.get(game_obj.state.sport_key)
        game_dict['home_team'] = game_obj.state.home_team.name
        game_dict['away_team'] = game_obj.state.away_team.name
        game_dict['game_id'] = game_obj.state.id
    return convert_numpy_types(games_dicts)


def get_all_games_response() -> Response:
    """
    Return a pre-serialised JSON Response, rebuilding only when stale (>30s)
    or game count has changed. Uses app_state.tracker (populated at startup).
    """
    import app_state

    tracker = app_state.tracker
    if tracker is None:
        return Response(content=b"[]", media_type="application/json")

    now = time.time()
    count = len(tracker.games)
    cache = games_serialized_cache

    if (
        cache["json_bytes"] is not None
        and now - cache["ts"] < _GAMES_CACHE_TTL
        and cache["count"] == count
    ):
        logger.info(f"[GAMES CACHE] Hit ({count} games, age={now - cache['ts']:.1f}s)")
        return Response(content=cache["json_bytes"], media_type="application/json")

    logger.info(f"[GAMES CACHE] Miss — rebuilding {count} games")
    list_data = serialize_games(tracker.get_all_games())

    class _DTEncoder(json.JSONEncoder):
        def default(self, o):
            import datetime as _dt
            if isinstance(o, (_dt.datetime, _dt.date)):
                return o.isoformat()
            return super().default(o)

    json_bytes = json.dumps(list_data, cls=_DTEncoder).encode("utf-8")
    cache["json_bytes"] = json_bytes
    cache["list_data"] = list_data
    cache["ts"] = now
    cache["count"] = count
    return Response(content=json_bytes, media_type="application/json")
