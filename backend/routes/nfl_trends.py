"""
NFL Trends API routes.

GET /api/f5/nfl/ats?team=KC&season=2024&situation=overall
GET /api/f5/nfl/ats/leaderboard?season=2024&situation=overall&min_games=10&sort=ats_pct
GET /api/f5/nfl/ou?team=KC&season=2024
GET /api/f5/nfl/epa?season=2024
GET /api/f5/nfl/team/{team}?season=2024
GET /api/f5/nfl/status
"""
from __future__ import annotations

import logging
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "f5_backtest" / "nfl_trends.db"

SITUATIONS = {"overall", "home", "away", "divisional", "as_favorite", "as_underdog"}


def _con() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _db_available() -> bool:
    return DB_PATH.exists()


def _rows(query: str, params: tuple = ()) -> list[dict[str, Any]]:
    with _con() as con:
        cur = con.execute(query, params)
        return [dict(r) for r in cur.fetchall()]


# ── Status ────────────────────────────────────────────────────────────────────

@router.get("/nfl/status")
def nfl_trends_status():
    if not _db_available():
        return {"available": False, "message": "Run build_nfl_trends.py to populate data"}
    meta = {r["key"]: r["value"] for r in _rows("SELECT key, value FROM nfl_pipeline_meta")}
    counts = _rows("SELECT COUNT(*) as n FROM nfl_games")[0]["n"]
    return {
        "available":    True,
        "last_run":     meta.get("last_run"),
        "seasons":      meta.get("seasons", "").split(","),
        "games_count":  int(meta.get("games_count", 0)),
        "ats_rows":     int(meta.get("ats_rows", 0)),
        "epa_rows":     int(meta.get("epa_rows", 0)),
    }


# ── ATS records ───────────────────────────────────────────────────────────────

@router.get("/nfl/ats")
def nfl_ats(
    team:      str | None = Query(None, description="Team abbreviation e.g. KC"),
    season:    int        = Query(2024, ge=2020, le=2030),
    situation: str        = Query("overall", description="overall|home|away|divisional|as_favorite|as_underdog"),
):
    if not _db_available():
        raise HTTPException(503, "NFL trends data not yet available — run build_nfl_trends.py")

    if situation not in SITUATIONS:
        raise HTTPException(400, f"situation must be one of: {sorted(SITUATIONS)}")

    if team:
        rows = _rows(
            "SELECT * FROM nfl_ats_records WHERE team=? AND season=? AND situation=?",
            (team.upper(), season, situation),
        )
        if not rows:
            raise HTTPException(404, f"No ATS data for {team.upper()} in {season} ({situation})")
        # Return all situations for this team/season
        all_sits = _rows(
            "SELECT * FROM nfl_ats_records WHERE team=? AND season=? ORDER BY situation",
            (team.upper(), season),
        )
        return {"team": team.upper(), "season": season, "situations": all_sits}

    rows = _rows(
        "SELECT * FROM nfl_ats_records WHERE season=? AND situation=? ORDER BY ats_pct DESC",
        (season, situation),
    )
    return {"season": season, "situation": situation, "count": len(rows), "teams": rows}


@router.get("/nfl/ats/leaderboard")
def nfl_ats_leaderboard(
    season:    int = Query(2024, ge=2020, le=2030),
    situation: str = Query("overall"),
    min_games: int = Query(10, ge=1),
    sort:      str = Query("ats_pct", description="ats_pct|over_pct|avg_pts_scored|avg_pts_allowed"),
):
    if not _db_available():
        raise HTTPException(503, "NFL trends data not yet available")

    valid_sorts = {"ats_pct", "over_pct", "avg_pts_scored", "avg_pts_allowed"}
    if sort not in valid_sorts:
        sort = "ats_pct"

    rows = _rows(
        f"SELECT * FROM nfl_ats_records WHERE season=? AND situation=? AND games>=? ORDER BY {sort} DESC NULLS LAST",
        (season, situation, min_games),
    )
    return {"season": season, "situation": situation, "sort": sort, "teams": rows}


# ── O/U trends ────────────────────────────────────────────────────────────────

@router.get("/nfl/ou")
def nfl_ou(
    team:   str | None = Query(None),
    season: int        = Query(2024, ge=2020, le=2030),
):
    if not _db_available():
        raise HTTPException(503, "NFL trends data not yet available")

    if team:
        rows = _rows(
            "SELECT * FROM nfl_ats_records WHERE team=? AND season=? ORDER BY situation",
            (team.upper(), season),
        )
        return {"team": team.upper(), "season": season, "situations": rows}

    rows = _rows(
        "SELECT * FROM nfl_ats_records WHERE season=? AND situation='overall' ORDER BY over_pct DESC",
        (season,),
    )
    return {"season": season, "teams": rows}


# ── EPA rankings ──────────────────────────────────────────────────────────────

@router.get("/nfl/epa")
def nfl_epa(
    season: int        = Query(2024, ge=2020, le=2030),
    sort:   str        = Query("total_off_epa", description="total_off_epa|pass_epa|rush_epa|pts_per_game|pts_allowed_per_game"),
    team:   str | None = Query(None),
):
    if not _db_available():
        raise HTTPException(503, "NFL trends data not yet available")

    valid_sorts = {"total_off_epa", "pass_epa", "rush_epa", "pts_per_game", "pts_allowed_per_game"}
    if sort not in valid_sorts:
        sort = "total_off_epa"

    if team:
        rows = _rows(
            "SELECT * FROM nfl_team_epa WHERE team=? AND season=?",
            (team.upper(), season),
        )
        return {"team": team.upper(), "season": season, "data": rows[0] if rows else None}

    asc = "ASC" if sort == "pts_allowed_per_game" else "DESC"
    rows = _rows(
        f"SELECT * FROM nfl_team_epa WHERE season=? ORDER BY {sort} {asc} NULLS LAST",
        (season,),
    )
    # Add rank
    for i, r in enumerate(rows):
        r["rank"] = i + 1
    return {"season": season, "sort": sort, "teams": rows}


# ── Full team profile ─────────────────────────────────────────────────────────

@router.get("/nfl/team/{team}")
def nfl_team_profile(team: str, season: int = Query(2024, ge=2020, le=2030)):
    if not _db_available():
        raise HTTPException(503, "NFL trends data not yet available")

    t = team.upper()

    ats = _rows(
        "SELECT * FROM nfl_ats_records WHERE team=? AND season=? ORDER BY situation",
        (t, season),
    )
    epa = _rows(
        "SELECT * FROM nfl_team_epa WHERE team=? AND season=?",
        (t, season),
    )
    games = _rows(
        """SELECT game_id, week, gameday, away_team, home_team,
                  away_score, home_score, result, spread_line, total_line,
                  home_cover, away_cover, ats_push, went_over, went_under,
                  away_qb_name, home_qb_name
           FROM nfl_games
           WHERE (home_team=? OR away_team=?) AND season=? AND game_type='REG'
           AND home_score IS NOT NULL
           ORDER BY week""",
        (t, t, season),
    )

    # Annotate each game from the team's perspective
    for g in games:
        is_home = g["home_team"] == t
        g["team_score"]   = g["home_score"] if is_home else g["away_score"]
        g["opp_score"]    = g["away_score"] if is_home else g["home_score"]
        g["opponent"]     = g["away_team"]  if is_home else g["home_team"]
        g["location"]     = "HOME" if is_home else "AWAY"
        g["team_covered"] = bool(g["home_cover"]) if is_home else bool(g["away_cover"])
        g["team_qb"]      = g["home_qb_name"] if is_home else g["away_qb_name"]

    if not ats and not epa:
        raise HTTPException(404, f"No data for {t} in {season}")

    overall = next((r for r in ats if r["situation"] == "overall"), None)
    return {
        "team":          t,
        "season":        season,
        "summary":       overall,
        "epa":           epa[0] if epa else None,
        "ats_by_situation": ats,
        "games":         games,
    }
