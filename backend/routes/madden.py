"""
Madden 26 Player Ratings — API routes.

GET /api/f5/madden/players              — all players (OVR + name + team, lightweight)
GET /api/f5/madden/players?team=KC      — filtered by team abbreviation
GET /api/f5/madden/players?pos=QB       — filtered by position group (QB/RB/WR/TE/OL/DL/LB/DB)
GET /api/f5/madden/players?team=KC&pos=QB
GET /api/f5/madden/team/{abbr}          — full roster for one team with all attributes
GET /api/f5/madden/status               — scraper metadata (when scraped, player count)
GET /api/f5/madden/top?pos=QB&limit=10  — top players at a position by OVR
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()
logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).parent.parent / "f5_backtest" / "madden26_players.json"

# Lightweight player fields for list endpoints
LIST_FIELDS = {"id", "name", "first_name", "last_name", "position", "pos_group",
               "ovr", "rating_overall", "team", "team_name", "age", "years_pro",
               "rating_speed", "rating_strength", "rating_awareness",
               "rating_agility", "rating_acceleration"}


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    if not DATA_FILE.exists():
        return {}
    return json.loads(DATA_FILE.read_text())


def _players() -> list[dict]:
    return _load().get("players", [])


def _slim(p: dict) -> dict:
    """Return lightweight player dict for list responses."""
    out = {k: p[k] for k in LIST_FIELDS if k in p}
    # Prefer rating_overall; fall back to ovr for consistency
    out["ovr"] = p.get("rating_overall") or p.get("ovr", 0)
    return out


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/madden/status")
def madden_status():
    data = _load()
    if not data:
        return {"available": False, "message": "Run scrape_madden26.py to populate data"}
    return {
        "available":    True,
        "game":         data.get("game", "Madden NFL 26"),
        "season":       data.get("season", "2026"),
        "scraped_at":   data.get("scraped_at"),
        "player_count": data.get("player_count", 0),
        "ovr_threshold": data.get("ovr_threshold", 70),
    }


@router.get("/madden/players")
def madden_players(
    team: str | None = Query(None, description="Team abbreviation e.g. KC, SF"),
    pos:  str | None = Query(None, description="Position group: QB RB WR TE OL DL LB DB K P"),
    min_ovr: int     = Query(0,   ge=0, le=99, description="Minimum OVR filter"),
    limit:   int     = Query(500, ge=1, le=3200),
):
    players = _players()
    if not players:
        raise HTTPException(status_code=503, detail="Madden data not yet available — run scraper first")

    if team:
        players = [p for p in players if p.get("team", "").upper() == team.upper()]
    if pos:
        players = [p for p in players if p.get("pos_group", "").upper() == pos.upper()
                   or p.get("position", "").upper() == pos.upper()]
    if min_ovr:
        players = [p for p in players if (p.get("rating_overall") or p.get("ovr", 0)) >= min_ovr]

    players = sorted(players, key=lambda p: p.get("rating_overall") or p.get("ovr", 0), reverse=True)
    return {
        "count":   min(len(players), limit),
        "filters": {"team": team, "pos": pos, "min_ovr": min_ovr},
        "players": [_slim(p) for p in players[:limit]],
    }


@router.get("/madden/team/{abbr}")
def madden_team(abbr: str):
    """Full roster for a team with all scraped attributes."""
    data = _load()
    if not data:
        raise HTTPException(status_code=503, detail="Madden data not yet available")

    by_team: dict[str, list] = data.get("by_team", {})
    roster = by_team.get(abbr.upper())
    if roster is None:
        raise HTTPException(status_code=404, detail=f"Team '{abbr}' not found")

    # Group by position for UI convenience
    by_pos: dict[str, list] = {}
    for p in roster:
        g = p.get("pos_group", p.get("position", "OTH"))
        by_pos.setdefault(g, []).append(p)

    # Sort each group by OVR
    for g in by_pos:
        by_pos[g].sort(key=lambda p: p.get("rating_overall") or p.get("ovr", 0), reverse=True)

    return {
        "team":         abbr.upper(),
        "player_count": len(roster),
        "by_position":  by_pos,
        "roster":       sorted(roster, key=lambda p: p.get("rating_overall") or p.get("ovr", 0), reverse=True),
    }


@router.get("/madden/top")
def madden_top(
    pos:   str | None = Query(None, description="Position group filter"),
    limit: int        = Query(10, ge=1, le=100),
):
    """Top players by OVR, optionally filtered by position."""
    players = _players()
    if not players:
        raise HTTPException(status_code=503, detail="Madden data not yet available")

    if pos:
        players = [p for p in players if p.get("pos_group", "").upper() == pos.upper()
                   or p.get("position", "").upper() == pos.upper()]

    players = sorted(players, key=lambda p: p.get("rating_overall") or p.get("ovr", 0), reverse=True)
    return {
        "pos":     pos,
        "limit":   limit,
        "players": [_slim(p) for p in players[:limit]],
    }
