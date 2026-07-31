"""
NFL/NCAAF odds ingestion — fetches live lines from The Odds API and stores
consensus lines in ``nfl_game_odds`` (shared table, differentiated by the
``sport`` column: ``'nfl'`` or ``'ncaaf'``).

Entry point
-----------
run_nfl_ingestion() -> dict
    Ingests both NFL and NCAAF, returns a combined report matching the
    same shape as ``run_mlb_ingestion()`` / ``run_wnba_ingestion()`` in
    ``pipeline/orchestrator.py``.

Season windows
--------------
NFL:   September - February
NCAAF: August - January
Outside those windows, The Odds API simply returns no games for the
sport_key, so this module doesn't need its own date gating.
"""
from __future__ import annotations

import logging

from pipeline.config import now_cst
from pipeline.db.connection import execute_write
from pipeline.ingestion.live_odds import fetch_live_odds

logger = logging.getLogger(__name__)

SPORT_KEYS: dict[str, str] = {
    "nfl": "americanfootball_nfl",
    "ncaaf": "americanfootball_ncaaf",
}


def _avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def _extract_game_lines(game: dict) -> dict:
    """
    Aggregate raw per-book outcomes into averaged spread/total/moneyline
    values for one game.  Unlike ``live_odds.extract_consensus_line``
    (which is price/probability focused), this pulls the actual point
    values needed for ``nfl_game_odds`` (spread_home, spread_away,
    total_line) alongside average moneyline prices.
    """
    home_team = game.get("home_team", "")
    away_team = game.get("away_team", "")

    spread_home_pts: list[float] = []
    spread_away_pts: list[float] = []
    total_pts: list[float] = []
    home_ml_prices: list[float] = []
    away_ml_prices: list[float] = []
    books_with_market: set[str] = set()

    for bk in game.get("bookmakers", []):
        bk_key = bk.get("key", "unknown")
        markets = bk.get("markets", {})

        spreads = markets.get("spreads", [])
        for o in spreads:
            if o.get("name") == home_team and o.get("point") is not None:
                spread_home_pts.append(float(o["point"]))
                books_with_market.add(bk_key)
            elif o.get("name") == away_team and o.get("point") is not None:
                spread_away_pts.append(float(o["point"]))
                books_with_market.add(bk_key)

        totals = markets.get("totals", [])
        for o in totals:
            if o.get("name", "").lower() == "over" and o.get("point") is not None:
                total_pts.append(float(o["point"]))
                books_with_market.add(bk_key)

        h2h = markets.get("h2h", [])
        for o in h2h:
            if o.get("name") == home_team and o.get("price") is not None:
                home_ml_prices.append(float(o["price"]))
                books_with_market.add(bk_key)
            elif o.get("name") == away_team and o.get("price") is not None:
                away_ml_prices.append(float(o["price"]))
                books_with_market.add(bk_key)

    return {
        "spread_home": _avg(spread_home_pts),
        "spread_away": _avg(spread_away_pts),
        "total_line": _avg(total_pts),
        "home_ml": round(_avg(home_ml_prices)) if home_ml_prices else None,
        "away_ml": round(_avg(away_ml_prices)) if away_ml_prices else None,
        "books_sampled": len(books_with_market),
    }


def _upsert_game_odds(sport: str, game: dict, lines: dict) -> None:
    execute_write(
        """INSERT INTO nfl_game_odds
           (game_id, sport, home_team, away_team, game_time,
            spread_home, spread_away, total_line, home_ml, away_ml,
            books_sampled, fetched_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
           ON CONFLICT (game_id, sport) DO UPDATE SET
             spread_home   = EXCLUDED.spread_home,
             spread_away   = EXCLUDED.spread_away,
             total_line    = EXCLUDED.total_line,
             home_ml       = EXCLUDED.home_ml,
             away_ml       = EXCLUDED.away_ml,
             books_sampled = EXCLUDED.books_sampled,
             fetched_at    = EXCLUDED.fetched_at""",
        (
            game.get("game_id", ""),
            sport,
            game.get("home_team", ""),
            game.get("away_team", ""),
            game.get("commence_time") or None,
            lines["spread_home"],
            lines["spread_away"],
            lines["total_line"],
            lines["home_ml"],
            lines["away_ml"],
            lines["books_sampled"],
            now_cst(),
        ),
    )


def _ingest_one_sport(sport: str, sport_key: str) -> dict:
    """Fetch + upsert odds for a single sport. Returns a sub-report."""
    fetched = 0
    stored = 0
    try:
        games = fetch_live_odds(sport_key, markets=["h2h", "spreads", "totals"])
        fetched = len(games)
        for game in games:
            lines = _extract_game_lines(game)
            if lines["books_sampled"] == 0:
                continue
            _upsert_game_odds(sport, game, lines)
            stored += 1
        logger.info(
            "[nfl_ingestion] %s: %d games fetched, %d stored", sport, fetched, stored
        )
        return {"fetched": fetched, "stored": stored, "status": "ok", "error_msg": None}
    except Exception as e:
        logger.error("[nfl_ingestion] %s ingestion failed: %s", sport, e)
        return {"fetched": fetched, "stored": stored, "status": "error", "error_msg": str(e)}


def run_nfl_ingestion() -> dict:
    """
    Fetch and store live odds for NFL and NCAAF.

    Returns a report dict matching the shape used by
    ``run_mlb_ingestion()`` / ``run_wnba_ingestion()`` so it can be
    logged and consumed the same way by the orchestrator.
    """
    report = {
        "sport": "nfl_ncaaf",
        "source": "odds_api",
        "records_fetched": 0,
        "records_valid": 0,
        "records_rejected": 0,
        "haiku_flags": [],
        "status": "ok",
        "error_msg": None,
    }

    sub_reports: dict[str, dict] = {}
    for sport, sport_key in SPORT_KEYS.items():
        sub_reports[sport] = _ingest_one_sport(sport, sport_key)

    report["records_fetched"] = sum(r["fetched"] for r in sub_reports.values())
    report["records_valid"] = sum(r["stored"] for r in sub_reports.values())
    report["records_rejected"] = report["records_fetched"] - report["records_valid"]

    errors = [
        f"{sport}: {r['error_msg']}"
        for sport, r in sub_reports.items()
        if r["status"] == "error"
    ]
    if errors:
        report["status"] = "error" if len(errors) == len(sub_reports) else "ok"
        report["error_msg"] = "; ".join(errors)

    return report
