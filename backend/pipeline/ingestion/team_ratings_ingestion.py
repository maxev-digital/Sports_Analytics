"""
Team ratings ingestion for NFL and NCAAF — populates ``team_ratings``.

NFL: no free DVOA source exists (Football Outsiders is paywalled), so we
derive a simple power rating from ESPN standings: point differential per
game. This is flagged in the row itself (``dvoa_total`` stays NULL; only
``power_rating``/``point_diff_avg`` are populated) so downstream detectors
know which proxy was used.

NCAAF: SP+ ratings from collegefootballdata.com (CFBD). Requires a free
API key (CFBD_API_KEY) — the site added Bearer-token auth after this
project's original notes were written. Sport is skipped with a clear log
message if the key isn't configured, rather than failing the whole run.
"""
from __future__ import annotations

import logging
import os

import requests

from pipeline.config import now_cst
from pipeline.db.connection import execute_write

logger = logging.getLogger(__name__)

_ESPN_NFL_STANDINGS_URL = (
    "https://site.api.espn.com/apis/v2/sports/football/nfl/standings"
)
_CFBD_SP_URL = "https://api.collegefootballdata.com/ratings/sp"


def _upsert_rating(sport: str, team: str, fields: dict) -> None:
    columns = ["team", "sport"] + list(fields.keys()) + ["updated_at"]
    placeholders = ", ".join(["%s"] * len(columns))
    update_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in fields.keys())
    execute_write(
        f"""INSERT INTO team_ratings ({", ".join(columns)})
            VALUES ({placeholders})
            ON CONFLICT (team, sport) DO UPDATE SET
              {update_clause}, updated_at = EXCLUDED.updated_at""",
        (team, sport, *fields.values(), now_cst()),
    )


def ingest_nfl_power_ratings(season: int | None = None) -> dict:
    """
    Derive a simple NFL power rating (point differential per game) from
    ESPN standings and store it in ``team_ratings`` (sport='nfl').

    This is an explicit proxy, not DVOA — Football Outsiders DVOA is
    paywalled and has no free API. Flagged via docstring/log, not stored
    in a "we pretended this was DVOA" way: dvoa_* columns stay NULL.
    """
    params = {"season": season} if season else {}
    try:
        resp = requests.get(_ESPN_NFL_STANDINGS_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("[team_ratings_ingestion] NFL standings fetch failed: %s", e)
        return {"stored": 0, "status": "error", "error_msg": str(e)}

    stored = 0
    for conference in data.get("children", []):
        entries = conference.get("standings", {}).get("entries", [])
        for entry in entries:
            team_name = entry.get("team", {}).get("displayName", "")
            if not team_name:
                continue
            stats = {s.get("name"): s for s in entry.get("stats", [])}

            def _stat_value(name: str) -> float | None:
                s = stats.get(name)
                if s is None:
                    return None
                v = s.get("value")
                return float(v) if v is not None else None

            wins = _stat_value("wins") or 0
            losses = _stat_value("losses") or 0
            point_diff = _stat_value("pointDifferential") or 0.0
            games = wins + losses
            point_diff_avg = round(point_diff / games, 2) if games > 0 else 0.0

            try:
                _upsert_rating(
                    "nfl",
                    team_name,
                    {
                        "power_rating": point_diff_avg,
                        "wins": int(wins),
                        "losses": int(losses),
                        "point_diff_avg": point_diff_avg,
                    },
                )
                stored += 1
            except Exception as e:
                logger.error(
                    "[team_ratings_ingestion] Failed to store NFL rating for %s: %s",
                    team_name, e,
                )

    logger.info("[team_ratings_ingestion] NFL: stored %d team power ratings", stored)
    return {"stored": stored, "status": "ok", "error_msg": None}


def ingest_ncaaf_sp_ratings(year: int = 2025) -> dict:
    """
    Fetch NCAAF SP+ ratings from collegefootballdata.com and store in
    ``team_ratings`` (sport='ncaaf').

    Requires CFBD_API_KEY env var (free registration at
    collegefootballdata.com/key). Skips cleanly with a clear log message
    if the key is absent — does not raise, so callers can keep running
    other ingestion steps.
    """
    api_key = os.environ.get("CFBD_API_KEY", "")
    if not api_key:
        msg = (
            "CFBD_API_KEY not configured — register for a free key at "
            "collegefootballdata.com/key. Skipping NCAAF SP+ ingestion."
        )
        logger.warning("[team_ratings_ingestion] %s", msg)
        return {"stored": 0, "status": "skipped", "error_msg": msg}

    try:
        resp = requests.get(
            _CFBD_SP_URL,
            params={"year": year},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=20,
        )
        resp.raise_for_status()
        ratings = resp.json()
    except Exception as e:
        logger.error("[team_ratings_ingestion] NCAAF SP+ fetch failed: %s", e)
        return {"stored": 0, "status": "error", "error_msg": str(e)}

    stored = 0
    for r in ratings:
        team_name = r.get("team", "")
        if not team_name:
            continue
        try:
            _upsert_rating(
                "ncaaf",
                team_name,
                {
                    "sp_rating": r.get("rating"),
                    "sp_offense": (r.get("offense") or {}).get("rating"),
                    "sp_defense": (r.get("defense") or {}).get("rating"),
                },
            )
            stored += 1
        except Exception as e:
            logger.error(
                "[team_ratings_ingestion] Failed to store NCAAF SP+ for %s: %s",
                team_name, e,
            )

    logger.info("[team_ratings_ingestion] NCAAF: stored %d SP+ ratings", stored)
    return {"stored": stored, "status": "ok", "error_msg": None}


def run_ratings_ingestion() -> dict:
    """Run both NFL power-rating and NCAAF SP+ ingestion. Returns combined report."""
    nfl_report = ingest_nfl_power_ratings()
    ncaaf_report = ingest_ncaaf_sp_ratings()
    return {"nfl": nfl_report, "ncaaf": ncaaf_report}
