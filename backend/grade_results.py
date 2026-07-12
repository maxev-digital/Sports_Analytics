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

ESPN_MLB      = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
ESPN_WNBA     = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard"
ESPN_SOCCER_MLS = "https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1/scoreboard"
ESPN_SOCCER_EPL = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"

# Tennis uses ESPN v3 competitions API (individual match level)
ESPN_TENNIS_ATP_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/tennis/atp/scoreboard"
ESPN_TENNIS_WTA_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/tennis/wta/scoreboard"
ESPN_TENNIS_V3_COMPS = "https://sports.core.api.espn.com/v2/sports/tennis/leagues/{league}/events/{event_id}/competitions"

SPORT_ESPN = {
    "mlb":         ESPN_MLB,
    "wnba":        ESPN_WNBA,
    "soccer_mls":  ESPN_SOCCER_MLS,
    "soccer_epl":  ESPN_SOCCER_EPL,
    # Tennis is handled separately via fetch_espn_scores_tennis()
    "tennis_atp":  "tennis_atp",
    "tennis_wta":  "tennis_wta",
}

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
    Tennis routes to fetch_espn_scores_tennis() — game_date is ignored for tennis.
    Returns list of game dicts:
      {espn_id, home_team, away_team, home_score, away_score,
       total_score, home_winner, away_winner, status, final}
    """
    # Tennis uses a different fetch path
    if sport in ("tennis_atp", "tennis_wta"):
        league = "atp" if sport == "tennis_atp" else "wta"
        return fetch_espn_scores_tennis(league)

    url = SPORT_ESPN.get(sport)
    if not url or url in ("tennis_atp", "tennis_wta"):
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


def fetch_espn_scores_tennis(league: str) -> list[dict]:
    """
    Fetch completed tennis match results for ATP or WTA Wimbledon via ESPN v3 API.

    ESPN v3 competitions endpoint returns individual match data including player
    names and winner flags.  Names come from competitor['name'] — no extra
    athlete fetch needed.

    league: 'atp' | 'wta'
    Returns same shape as fetch_espn_scores():
      {espn_id, home_team (player1), away_team (player2),
       home_score, away_score, total_score,
       home_winner, away_winner, status, final}
    """
    league = league.lower()
    scoreboard_url = ESPN_TENNIS_ATP_SCOREBOARD if league == "atp" else ESPN_TENNIS_WTA_SCOREBOARD
    try:
        resp = requests.get(scoreboard_url, timeout=15)
        resp.raise_for_status()
        events = resp.json().get("events", [])
        if not events:
            logger.info("ESPN tennis/%s: no events returned", league)
            return []
        event_id = events[0]["id"]
    except Exception as exc:
        logger.error("ESPN tennis/%s scoreboard failed: %s", league, exc)
        return []

    comps_url = ESPN_TENNIS_V3_COMPS.format(league=league, event_id=event_id)
    games = []
    page = 1
    while True:
        try:
            resp = requests.get(comps_url, params={"limit": 200, "page": page}, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("ESPN tennis/%s competitions page=%d failed: %s", league, page, exc)
            break

        items = data.get("items", [])
        if not items:
            break

        for item in items:
            ref = item.get("$ref", "")
            if not ref:
                continue
            try:
                comp_resp = requests.get(ref, timeout=10)
                comp_resp.raise_for_status()
                comp = comp_resp.json()
            except Exception:
                continue

            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue

            # Match is completed if any competitor has winner=True
            if not any(c.get("winner") for c in competitors):
                continue

            # competitor['name'] = "Zsombor Piros" (player full name, always inline)
            # ESPN tennis does not use homeAway labels — treat order 1 as "home", order 2 as "away"
            sorted_comps = sorted(competitors, key=lambda c: c.get("order", 999))
            p1 = sorted_comps[0]
            p2 = sorted_comps[1]
            p1_name = p1.get("name", "")
            p2_name = p2.get("name", "")
            p1_wins = bool(p1.get("winner"))
            p2_wins = bool(p2.get("winner"))

            games.append({
                "espn_id":     comp.get("id", ""),
                "home_team":   p1_name,  # "home" = player listed first (order=1)
                "away_team":   p2_name,
                "home_score":  0,
                "away_score":  0,
                "total_score": 0,
                "home_winner": p1_wins,
                "away_winner": p2_wins,
                "status":      "final",
                "final":       True,
            })

        page_count = data.get("pageCount", 1)
        if page >= page_count:
            break
        page += 1

    logger.info("ESPN tennis/%s: %d completed matches", league, len(games))
    return games


def _match_pick_to_game(pick: dict, games: list[dict]) -> dict | None:
    """
    Match a pick (home_team, away_team) to an ESPN game by normalised name.

    For tennis, the ESPN competitor name is "First Last" (order=1/2) while
    our DB stores Odds API names ("First Last" already).  For team sports,
    ESPN uses full display names which we match via substring.
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

        # Tennis cross-match: Odds API might store "Felix Auger-Aliassime" while ESPN
        # stores "Felix Auger-Aliassime" too (same), but last-name-only partial checks
        # are enough as a fallback — use last token of each name
        ph_last = ph.split()[-1] if ph else ""
        pa_last = pa.split()[-1] if pa else ""
        gh_last = gh.split()[-1] if gh else ""
        ga_last = ga.split()[-1] if ga else ""
        if ph_last and pa_last and ph_last == gh_last and pa_last == ga_last:
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
        home_won = game["home_winner"]
        away_won = game["away_winner"]
        is_draw  = not home_won and not away_won  # soccer / no OT result

        if pick_side == "home":
            result = "win" if home_won else "loss"
        elif pick_side == "away":
            result = "win" if away_won else "loss"
        elif pick_side == "draw":
            # Soccer 3-way market: win if neither team won (draw)
            result = "win" if is_draw else "loss"
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
        # total_line stores the HOME team's raw point (e.g., -1.5 when home is favourite).
        # Cover condition: adjusted_margin > 0 where adjustment flips the sign.
        #   home_cover: home_margin > -spread (e.g., -spread = 1.5 → win by 2+)
        #   away_cover: -home_margin > spread  (e.g., spread = -1.5 → -home_margin > -1.5 → home_margin < 1.5)
        spread = total_line
        if spread is None:
            return "needs_review", 0.0

        home_margin = game["home_score"] - game["away_score"]
        if pick_side in ("home", "home_cover"):
            covered = home_margin > -spread
            push    = home_margin == -spread
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

    # Fetch pending/needs_review picks for this date (needs_review picks may now have a line set)
    cur.execute("""
        SELECT id, sport, home_team, away_team, pick_side, pick_type,
               market_odds, total_line, status
        FROM predictions
        WHERE status IN ('pending', 'needs_review')
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


def grade_lookback(days: int = 7) -> list[dict]:
    """Grade all pending/needs_review picks from the past N days."""
    today = datetime.now(CST).date()
    results = []
    for offset in range(days, -1, -1):
        d = today - timedelta(days=offset)
        r = grade_picks_for_date(d)
        if r.get("graded", 0) > 0 or r.get("needs_review", 0) > 0:
            results.append(r)
    return results


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    parser = argparse.ArgumentParser(description="Grade prediction results from ESPN")
    parser.add_argument("date", nargs="?", help="Date to grade (YYYY-MM-DD), default: today")
    parser.add_argument("--lookback", type=int, metavar="N",
                        help="Grade all pending/needs_review picks from the past N days")
    args = parser.parse_args()

    if args.lookback:
        results = grade_lookback(args.lookback)
        print(json.dumps(results, indent=2))
    elif args.date:
        result = grade_picks_for_date(date.fromisoformat(args.date))
        print(json.dumps(result, indent=2))
    else:
        result = grade_picks_for_date()
        print(json.dumps(result, indent=2))
