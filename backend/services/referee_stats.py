"""
Referee statistics computation service.

Reads nfl_games from SQLite and computes per-referee aggregates.
Requires the `referee` column to exist in nfl_games (added in build_nfl_trends.py v2).
LEFT JOINs nfl_referee_penalties when available (run build_referee_penalties.py).
"""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from models.referee import (
    RefereeListResponse, RefereeProfile, RefereeSummary,
    RefereeSeasonSplit, TendencyLabel,
)

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "f5_backtest" / "nfl_trends.db"

SORT_COLUMNS: dict[str, str] = {
    "games":          "games",
    "avg_total":      "avg_total",
    "over_rate":      "over_rate",
    "home_cover_pct": "home_cover_pct",
    "flags_per_game": "flags_per_game",
    "yards_per_game": "yards_per_game",
    "home_bias":      "home_bias",
    "ot_rate":        "ot_rate",
    "dome_pct":       "dome_pct",
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


def _penalty_table_exists(con: sqlite3.Connection) -> bool:
    cur = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='nfl_referee_penalties'"
    )
    return cur.fetchone() is not None


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


_GAME_SQL = """
    SELECT
        g.referee                                                   AS name,
        COUNT(*)                                                    AS games,
        AVG(g.total_actual)                                         AS avg_total,
        AVG(CASE WHEN g.went_over  = 1 THEN 1.0 ELSE 0.0 END)     AS over_rate,
        AVG(CASE WHEN g.went_under = 1 THEN 1.0 ELSE 0.0 END)     AS under_rate,
        AVG(CASE WHEN g.home_cover = 1 THEN 1.0 ELSE 0.0 END)     AS home_cover_pct,
        AVG(CASE WHEN g.overtime   = 1 THEN 1.0 ELSE 0.0 END)     AS ot_rate,
        AVG(CASE WHEN g.roof IN ('dome','retractable_roof','closed')
                 THEN 1.0 ELSE 0.0 END)                            AS dome_pct,
        AVG(CASE WHEN strftime('%w', g.gameday) IN ('1','4')
                 THEN 1.0 ELSE 0.0 END)                            AS primetime_pct,
        AVG(CASE WHEN g.roof NOT IN ('dome','closed')
                 THEN g.temp ELSE NULL END)                        AS avg_temp,
        AVG(CASE WHEN g.roof NOT IN ('dome','closed')
                 THEN g.wind ELSE NULL END)                        AS avg_wind,
        AVG(CASE WHEN g.div_game = 1 THEN 1.0 ELSE 0.0 END)      AS div_game_pct,
        p.flags_per_game, p.yards_per_game, p.home_bias
    FROM nfl_games g
    {penalty_join}
    WHERE g.referee IS NOT NULL AND g.referee != ''
      AND g.home_score IS NOT NULL AND g.game_type = 'REG'
    GROUP BY g.referee
    HAVING COUNT(*) >= ?
    ORDER BY {sort_col} DESC
"""

_PENALTY_JOIN = (
    "LEFT JOIN nfl_referee_penalties p ON p.referee = g.referee "
    "AND p.season = (SELECT MAX(season) FROM nfl_referee_penalties WHERE referee = g.referee)"
)


def get_referee_list(sort: str = "games", min_games: int = 10) -> RefereeListResponse:
    if not _db_has_referee_col():
        logger.warning("referee column missing — rebuild DB with build_nfl_trends.py")
        return RefereeListResponse(count=0, referees=[])

    sort_col = SORT_COLUMNS.get(sort, "games")

    with _con() as con:
        join = _PENALTY_JOIN if _penalty_table_exists(con) else ""
        sql = _GAME_SQL.format(penalty_join=join, sort_col=sort_col)
        rows = con.execute(sql, (min_games,)).fetchall()

    summaries = [
        RefereeSummary(
            name=r["name"],
            games=r["games"],
            avg_total=_round_or_none(r["avg_total"], 1),
            over_rate=_round_or_none(r["over_rate"]),
            under_rate=_round_or_none(r["under_rate"]),
            home_cover_pct=_round_or_none(r["home_cover_pct"]),
            tendency=_classify_tendency(r["over_rate"], r["home_cover_pct"]),
            ot_rate=_round_or_none(r["ot_rate"]),
            dome_pct=_round_or_none(r["dome_pct"]),
            primetime_pct=_round_or_none(r["primetime_pct"]),
            avg_temp=_round_or_none(r["avg_temp"], 1),
            avg_wind=_round_or_none(r["avg_wind"], 1),
            div_game_pct=_round_or_none(r["div_game_pct"]),
            flags_per_game=_round_or_none(r["flags_per_game"], 2),
            yards_per_game=_round_or_none(r["yards_per_game"], 1),
            home_bias=_round_or_none(r["home_bias"]),
        )
        for r in rows
    ]

    return RefereeListResponse(count=len(summaries), referees=summaries)


def get_referee_profile(name: str) -> RefereeProfile | None:
    if not _db_has_referee_col():
        return None

    with _con() as con:
        join = _PENALTY_JOIN if _penalty_table_exists(con) else ""
        overall = con.execute(
            f"""
            SELECT
                COUNT(*)                                                    AS games,
                AVG(g.total_actual)                                         AS avg_total,
                AVG(CASE WHEN g.went_over  = 1 THEN 1.0 ELSE 0.0 END)     AS over_rate,
                AVG(CASE WHEN g.went_under = 1 THEN 1.0 ELSE 0.0 END)     AS under_rate,
                AVG(CASE WHEN g.home_cover = 1 THEN 1.0 ELSE 0.0 END)     AS home_cover_pct,
                AVG(CASE WHEN g.overtime   = 1 THEN 1.0 ELSE 0.0 END)     AS ot_rate,
                AVG(CASE WHEN g.roof IN ('dome','retractable_roof','closed')
                         THEN 1.0 ELSE 0.0 END)                            AS dome_pct,
                AVG(CASE WHEN strftime('%w', g.gameday) IN ('1','4')
                         THEN 1.0 ELSE 0.0 END)                            AS primetime_pct,
                AVG(CASE WHEN g.roof NOT IN ('dome','closed')
                         THEN g.temp ELSE NULL END)                        AS avg_temp,
                AVG(CASE WHEN g.roof NOT IN ('dome','closed')
                         THEN g.wind ELSE NULL END)                        AS avg_wind,
                AVG(CASE WHEN g.div_game = 1 THEN 1.0 ELSE 0.0 END)      AS div_game_pct,
                p.flags_per_game, p.yards_per_game, p.home_bias
            FROM nfl_games g
            {join}
            WHERE g.referee = ? AND g.home_score IS NOT NULL AND g.game_type = 'REG'
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
                AVG(CASE WHEN went_over  = 1 THEN 1.0 ELSE 0.0 END) AS over_rate,
                AVG(CASE WHEN went_under = 1 THEN 1.0 ELSE 0.0 END) AS under_rate,
                AVG(CASE WHEN home_cover = 1 THEN 1.0 ELSE 0.0 END) AS home_cover_pct
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
        ot_rate=_round_or_none(overall["ot_rate"]),
        dome_pct=_round_or_none(overall["dome_pct"]),
        primetime_pct=_round_or_none(overall["primetime_pct"]),
        avg_temp=_round_or_none(overall["avg_temp"], 1),
        avg_wind=_round_or_none(overall["avg_wind"], 1),
        div_game_pct=_round_or_none(overall["div_game_pct"]),
        flags_per_game=_round_or_none(overall["flags_per_game"], 2),
        yards_per_game=_round_or_none(overall["yards_per_game"], 1),
        home_bias=_round_or_none(overall["home_bias"]),
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
