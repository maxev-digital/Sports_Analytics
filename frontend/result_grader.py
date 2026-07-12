"""
Result grading agent — polls ESPN for final scores and grades pending picks.

Runs as a cron job every 30 min from 7 PM CST to 1 AM CST.
Grades:
  ML picks   → winner field from ESPN
  Total picks → stored total_line vs actual total; fallback heuristic for missing lines
Updates: predictions.status/result/pl_units, game_results, model_performance
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import unicodedata
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import psycopg2
import requests

sys.path.insert(0, os.path.dirname(__file__))
from pipeline.config import DB_URL

logger = logging.getLogger(__name__)

CST = ZoneInfo("America/Chicago")

ESPN_MLB  = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
ESPN_WNBA = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard"

SPORT_ESPN = {"mlb": ESPN_MLB, "wnba": ESPN_WNBA}

# American odds → P/L in units (1 unit = 1 standard bet)
def _pl_units(odds: int, result: str) -> float:
    if result == "push":
        return 0.0
    if result == "loss":
        return -1.0
    # win
    if odds >= 0:
        return round(odds / 100, 4)
    else:
        return round(100 / abs(odds), 4)


def _normalise_name(name: str) -> str:
    """Lowercase, strip accents, collapse whitespace — for fuzzy team matching."""
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", name.lower().strip())


def fetch_espn_scores(sport: str, game_date: date) -> list[dict]:
    """
    Pull ESPN scoreboard for sport on game_date.
    Returns list of game dicts:
      {espn_id, home_team, away_team, home_score, away_score,
       total_score, home_winner, away_winner, status, final}
    """
    url = SPORT_ESPN.get(sport)
    if not url:
        logger.warning("No ESPN URL for sport=%s", sport)
        return []

    date_str = game_date.strftime("%Y%m%d")
    try:
        resp = requests.get(url, params={"dates": date_str}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.error("ESPN fetch failed for %s %s: %s", sport, date_str, exc)
        return []

    games = []
    for event in data.get("events", []):
        comp = event["competitions"][0]
        status = event["status"]["type"]
        is_final = status.get("completed", False) or status.get("name") in ("STATUS_FINAL",)

        teams = {t["homeAway"]: t for t in comp["competitors"]}
        home = teams.get("home", {})
        away = teams.get("away", {})

        try:
            home_score = int(home.get("score", 0) or 0)
            away_score = int(away.get("score", 0) or 0)
        except (ValueError, TypeError):
            home_score = away_score = 0

        games.append({
            "espn_id":     event["id"],
            "home_team":   home.get("team", {}).get("displayName", ""),
            "away_team":   away.get("team", {}).get("displayName", ""),
            "home_score":  home_score,
            "away_score":  away_score,
            "total_score": home_score + away_score,
            "home_winner": bool(home.get("winner", False)),
            "away_winner": bool(away.get("winner", False)),
            "status":      status.get("description", ""),
            "final":       is_final,
        })

    logger.info("ESPN %s %s: %d events (%d final)",
                sport, date_str, len(games),
                sum(1 for g in games if g["final"]))
    return games


def _match_pick_to_game(pick: dict, games: list[dict]) -> dict | None:
    """
    Match a pick (home_team, away_team) to an ESPN game by normalised team name.
    Returns the matched game dict or None.
    """
    ph = _normalise_name(pick["home_team"])
    pa = _normalise_name(pick["away_team"])

    for g in games:
        gh = _normalise_name(g["home_team"])
        ga = _normalise_name(g["away_team"])

        # Direct match
        if ph == gh and pa == ga:
            return g

        # Partial match — ESPN uses full names, our DB might have shorter ones
        if (ph in gh or gh in ph) and (pa in ga or ga in pa):
            return g

    return None


def _grade_pick(pick: dict, game: dict) -> tuple[str, float] | None:
    """
    Grade a pick against a final game result.
    Returns (result, pl_units) or None if ungradeable.

    result values: 'win' | 'loss' | 'push' | 'needs_review'
    """
    pick_side = pick["pick_side"]   # home | away | over | under | home_cover | away_cover
    pick_type = pick["pick_type"]   # ml | total | spread
    odds      = int(pick["market_odds"])
    total_line = pick.get("total_line")  # may be None for older picks

    if pick_type == "ml":
        if pick_side == "home":
            result = "win" if game["home_winner"] else "loss"
        elif pick_side == "away":
            result = "win" if game["away_winner"] else "loss"
        else:
            logger.warning("Unknown ML pick_side=%s", pick_side)
            return None

        return result, _pl_units(odds, result)

    elif pick_type == "total":
        actual_total = game["total_score"]

        if total_line is not None:
            if actual_total > total_line:
                actual_side = "over"
            elif actual_total < total_line:
                actual_side = "under"
            else:
                actual_side = "push"
        else:
            # Heuristic for missing line (typical MLB: 7.5–9.5)
            if actual_total <= 5:
                actual_side = "under"    # definitely under any reasonable line
            elif actual_total >= 14:
                actual_side = "over"     # definitely over any reasonable line
            else:
                # Ambiguous — flag for manual review
                logger.warning(
                    "Total pick ungradeable (no line stored, score=%d): %s @ %s",
                    actual_total, pick["away_team"], pick["home_team"],
                )
                return "needs_review", 0.0

        if actual_side == "push":
            result = "push"
        elif pick_side in ("over", "under"):
            result = "win" if pick_side == actual_side else "loss"
        else:
            return None

        return result, _pl_units(odds, result)

    elif pick_type == "spread":
        # Home cover: home wins by more than the spread (negative spread = favourite)
        spread = total_line  # we reuse total_line for spread value
        if spread is None:
            return "needs_review", 0.0

        home_margin = game["home_score"] - game["away_score"]
        if pick_side in ("home", "home_cover"):
            covered = home_margin > spread
            push    = home_margin == spread
        elif pick_side in ("away", "away_cover"):
            covered = -home_margin > spread
            push    = home_margin == -spread
        else:
            return None

        result = "push" if push else ("win" if covered else "loss")
        return result, _pl_units(odds, result)

    return None


def _upsert_game_result(cur, sport: str, game: dict, game_date: date):
    """Insert or update game_results row."""
    cur.execute("""
        INSERT INTO game_results
          (sport, home_team, away_team, game_date_cst,
           home_score, away_score, total, source, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,'espn',NOW())
        ON CONFLICT DO NOTHING
    """, (
        sport, game["home_team"], game["away_team"], game_date,
        game["home_score"], game["away_score"], game["total_score"],
    ))


def _refresh_model_performance(cur):
    """Recompute model_performance from graded predictions (last 30 days)."""
    cur.execute("""
        SELECT sport, pick_type,
               COUNT(*) FILTER (WHERE status='win')  AS wins,
               COUNT(*) FILTER (WHERE status='loss') AS losses,
               COUNT(*) FILTER (WHERE status='push') AS pushes,
               COUNT(*) AS total,
               ROUND(AVG(pl_units) FILTER (WHERE status IN ('win','loss'))::numeric,4) AS avg_pl,
               ROUND(AVG(edge_pct)::numeric,2) AS avg_edge
        FROM predictions
        WHERE status IN ('win','loss','push')
          AND created_at_cst >= NOW() - INTERVAL '30 days'
        GROUP BY sport, pick_type
    """)
    rows = cur.fetchall()

    for sport, bet_type, wins, losses, pushes, total, avg_pl, avg_edge in rows:
        settled = wins + losses + pushes
        win_rate = round(wins / settled, 4) if settled > 0 else 0.0
        roi_pct  = round(float(avg_pl or 0) * 100, 2)

        cur.execute("""
            INSERT INTO model_performance
              (sport, model_name, bet_type, period_days, total_picks,
               wins, losses, pushes, win_rate, roi_pct, avg_edge_pct, computed_at_cst)
            VALUES (%s, 'rule_based', %s, 30, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT DO NOTHING
        """, (sport, bet_type, total, wins, losses, pushes, win_rate, roi_pct, avg_edge))

    if rows:
        logger.info("model_performance refreshed: %d sport/bet_type combos", len(rows))


def grade_picks_for_date(grade_date: date | None = None) -> dict:
    """
    Main entry point. Grades all pending picks for grade_date (default: today CST).
    Returns summary dict.
    """
    if grade_date is None:
        grade_date = datetime.now(CST).date()

    logger.info("Grading picks for %s", grade_date)

    conn = psycopg2.connect(DB_URL)
    cur  = conn.cursor()

    # Fetch pending picks for this date (match on game_time_cst date OR created_at_cst date)
    cur.execute("""
        SELECT id, sport, home_team, away_team, pick_side, pick_type,
               market_odds, total_line, status
        FROM predictions
        WHERE status = 'pending'
          AND (game_time_cst::date = %s OR created_at_cst::date = %s)
    """, (grade_date, grade_date))
    picks = [
        dict(zip(
            ["id","sport","home_team","away_team","pick_side","pick_type",
             "market_odds","total_line","status"],
            row
        ))
        for row in cur.fetchall()
    ]

    if not picks:
        logger.info("No pending picks for %s", grade_date)
        conn.close()
        return {"date": str(grade_date), "graded": 0, "skipped": 0}

    logger.info("Found %d pending picks for %s", len(picks), grade_date)

    # Group picks by sport and fetch ESPN scores once per sport
    sports = list({p["sport"] for p in picks})
    espn_by_sport: dict[str, list[dict]] = {}
    for sport in sports:
        espn_by_sport[sport] = fetch_espn_scores(sport, grade_date)

    graded = skipped = needs_review = 0

    for pick in picks:
        games = espn_by_sport.get(pick["sport"], [])
        final_games = [g for g in games if g["final"]]

        game = _match_pick_to_game(pick, final_games)
        if game is None:
            # Game not final yet or not found
            logger.debug("No final result for pick %d: %s @ %s",
                         pick["id"], pick["away_team"], pick["home_team"])
            skipped += 1
            continue

        grade = _grade_pick(pick, game)
        if grade is None:
            logger.warning("Could not grade pick %d (type=%s side=%s)",
                           pick["id"], pick["pick_type"], pick["pick_side"])
            skipped += 1
            continue

        result, pl = grade
        if result == "needs_review":
            needs_review += 1
            cur.execute(
                "UPDATE predictions SET status='needs_review' WHERE id=%s",
                (pick["id"],)
            )
            logger.info("Pick %d (%s @ %s %s %s) → needs_review (total=%d, no line)",
                        pick["id"], pick["away_team"], pick["home_team"],
                        pick["pick_side"], pick["pick_type"],
                        game["total_score"])
        else:
            cur.execute(
                "UPDATE predictions SET status=%s, result=%s, pl_units=%s WHERE id=%s",
                (result, result, pl, pick["id"])
            )
            logger.info("Pick %d (%s @ %s %s %s) → %s (P/L: %+.2f units)",
                        pick["id"], pick["away_team"], pick["home_team"],
                        pick["pick_side"], pick["pick_type"], result, pl)
            graded += 1

        # Store game result
        _upsert_game_result(cur, pick["sport"], game, grade_date)

    # Refresh model performance after grading
    if graded > 0:
        _refresh_model_performance(cur)

    conn.commit()
    conn.close()

    summary = {
        "date":         str(grade_date),
        "graded":       graded,
        "needs_review": needs_review,
        "skipped":      skipped,
    }
    logger.info("Grading complete: %s", summary)
    return summary


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    # Allow optional date arg: python grade_results.py 2026-06-30
    if len(sys.argv) > 1:
        grade_date = date.fromisoformat(sys.argv[1])
    else:
        grade_date = None

    result = grade_picks_for_date(grade_date)
    print(json.dumps(result, indent=2))
