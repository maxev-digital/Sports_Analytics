"""
Referee statistics computation service.

Reads nfl_games from SQLite and computes per-referee aggregates.
Requires the `referee` column to exist in nfl_games (added in build_nfl_trends.py v2).
"""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from models.referee import RefereeListResponse, RefereeProfile, RefereeSummary, RefereeSeasonSplit, TendencyLabel

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "f5_backtest" / "nfl_trends.db"

SORT_COLUMNS: dict[str, str] = {
    "games":          "games",
    "avg_total":      "avg_total",
    "over_rate":      "over_rate",
    "home_cover_pct": "home_cover_pct",
}


def _con() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _db_has_referee_col() -> bool:
    if not DB_PATH.exists():
        return False
    with _con() as con:
        cur = con.execute("PRAGMA table_info(nfl_games)")
        cols = {row["name"] for row in cur.fetchall()}
        return "referee" in cols


def _classify_tendency(over_rate: float | None, home_cover_pct: float | None) -> TendencyLabel:
    if over_rate is not None and over_rate >= 0.58:
        return "OVER_HEAVY"
    if over_rate is not None and over_rate <= 0.42:
        return "UNDER_HEAVY"
    if home_cover_pct is not None and home_cover_pct >= 0.58:
        return "HOME_FRIENDLY"
    return "NEUTRAL"


def _round_or_none(val: float | None, places: int = 3) -> float | None:
    return round(val, places) if val is not None else None


def get_referee_list(sort: str = "games", min_games: int = 10) -> RefereeListResponse:
    if not _db_has_referee_col():
        logger.warning("referee column missing — rebuild DB with build_nfl_trends.py")
        return RefereeListResponse(count=0, referees=[])

    sort_col = SORT_COLUMNS.get(sort, "games")

    with _con() as con:
        rows = con.execute(
            f"""
            SELECT
                referee                                          AS name,
                COUNT(*)                                         AS games,
                AVG(total_actual)                                AS avg_total,
                AVG(CASE WHEN went_over = 1 THEN 1.0 ELSE 0.0 END) AS over_rate,
                AVG(CASE WHEN went_under = 1 THEN 1.0 ELSE 0.0 END) AS under_rate,
                AVG(CASE WHEN home_cover = 1 THEN 1.0 ELSE 0.0 END) AS home_cover_pct
            FROM nfl_games
            WHERE referee IS NOT NULL AND referee != ''
              AND home_score IS NOT NULL AND game_type = 'REG'
            GROUP BY referee
            HAVING COUNT(*) >= ?
            ORDER BY {sort_col} DESC
            """,
            (min_games,),
        ).fetchall()

    summaries = [
        RefereeSummary(
            name=r["name"],
            games=r["games"],
            avg_total=_round_or_none(r["avg_total"], 1),
            over_rate=_round_or_none(r["over_rate"]),
            under_rate=_round_or_none(r["under_rate"]),
            home_cover_pct=_round_or_none(r["home_cover_pct"]),
            tendency=_classify_tendency(r["over_rate"], r["home_cover_pct"]),
        )
        for r in rows
    ]

    return RefereeListResponse(count=len(summaries), referees=summaries)


def get_referee_profile(name: str) -> RefereeProfile | None:
    if not _db_has_referee_col():
        return None

    with _con() as con:
        overall = con.execute(
            """
            SELECT
                COUNT(*)                                             AS games,
                AVG(total_actual)                                    AS avg_total,
                AVG(CASE WHEN went_over = 1 THEN 1.0 ELSE 0.0 END)  AS over_rate,
                AVG(CASE WHEN went_under = 1 THEN 1.0 ELSE 0.0 END)  AS under_rate,
                AVG(CASE WHEN home_cover = 1 THEN 1.0 ELSE 0.0 END)  AS home_cover_pct
            FROM nfl_games
            WHERE referee = ? AND home_score IS NOT NULL AND game_type = 'REG'
            """,
            (name,),
        ).fetchone()

        if not overall or overall["games"] == 0:
            return None

        season_rows = con.execute(
            """
            SELECT
                season,
                COUNT(*)                                             AS games,
                AVG(total_actual)                                    AS avg_total,
                AVG(CASE WHEN went_over = 1 THEN 1.0 ELSE 0.0 END)  AS over_rate,
                AVG(CASE WHEN went_under = 1 THEN 1.0 ELSE 0.0 END)  AS under_rate,
                AVG(CASE WHEN home_cover = 1 THEN 1.0 ELSE 0.0 END)  AS home_cover_pct
            FROM nfl_games
            WHERE referee = ? AND home_score IS NOT NULL AND game_type = 'REG'
            GROUP BY season
            ORDER BY season DESC
            """,
            (name,),
        ).fetchall()

    summary = RefereeSummary(
        name=name,
        games=overall["games"],
        avg_total=_round_or_none(overall["avg_total"], 1),
        over_rate=_round_or_none(overall["over_rate"]),
        under_rate=_round_or_none(overall["under_rate"]),
        home_cover_pct=_round_or_none(overall["home_cover_pct"]),
        tendency=_classify_tendency(overall["over_rate"], overall["home_cover_pct"]),
    )

    splits = [
        RefereeSeasonSplit(
            season=r["season"],
            games=r["games"],
            avg_total=_round_or_none(r["avg_total"], 1),
            over_rate=_round_or_none(r["over_rate"]),
            under_rate=_round_or_none(r["under_rate"]),
            home_cover_pct=_round_or_none(r["home_cover_pct"]),
        )
        for r in season_rows
    ]

    return RefereeProfile(name=name, summary=summary, season_splits=splits)
