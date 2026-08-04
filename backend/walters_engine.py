"""
Walters Power Rating Engine — weekly recalculator.

Usage:
  python3 walters_engine.py --week 1          # process week 1 results
  python3 walters_engine.py --week 1 --dry-run # preview without writing
  python3 walters_engine.py --status          # show current state

Formula: New = 0.90 * Old + 0.10 * TGPL
         TGPL = ScoreMargin + OppRating - HomeFieldAdj

HomeField = 2.0 pts (Walters method)
Decay     = 0.90 per game (exponential)

ESPN scores endpoint:
  https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard
  ?seasontype=2&week=N&limit=20
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR    = Path(__file__).parent / "f5_backtest"
RATINGS_FILE = DATA_DIR / "nfl_power_ratings.json"
HOME_FIELD   = 2.0
DECAY        = 0.90
LEARN        = 0.10  # 1 - DECAY

# ESPN team name → our 3-letter abbr
ESPN_TO_ABBR: dict[str, str] = {
    "Arizona Cardinals": "ARI",  "Atlanta Falcons": "ATL",
    "Baltimore Ravens": "BAL",   "Buffalo Bills": "BUF",
    "Carolina Panthers": "CAR",  "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE",
    "Dallas Cowboys": "DAL",     "Denver Broncos": "DEN",
    "Detroit Lions": "DET",      "Green Bay Packers": "GB",
    "Houston Texans": "HOU",     "Indianapolis Colts": "IND",
    "Jacksonville Jaguars": "JAX","Kansas City Chiefs": "KC",
    "Las Vegas Raiders": "LV",   "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LAR",   "Miami Dolphins": "MIA",
    "Minnesota Vikings": "MIN",  "New England Patriots": "NE",
    "New Orleans Saints": "NO",  "New York Giants": "NYG",
    "New York Jets": "NYJ",      "Philadelphia Eagles": "PHI",
    "Pittsburgh Steelers": "PIT","San Francisco 49ers": "SF",
    "Seattle Seahawks": "SEA",   "Tampa Bay Buccaneers": "TB",
    "Tennessee Titans": "TEN",   "Washington Commanders": "WSH",
}

FULL_NAME: dict[str, str] = {v: k for k, v in ESPN_TO_ABBR.items()}


def _load_ratings() -> dict[str, Any]:
    data = json.loads(RATINGS_FILE.read_text())
    # Ensure week_ratings and meta fields exist
    data.setdefault("week_ratings", {})
    data.setdefault("last_updated_week", 0)
    data.setdefault("season", "2026")
    data.setdefault("season_start", "2026-09-10")
    return data


def _save_ratings(data: dict[str, Any]) -> None:
    data["updated_at"] = datetime.utcnow().isoformat()
    RATINGS_FILE.write_text(json.dumps(data, indent=2))
    logger.info("Saved ratings to %s", RATINGS_FILE)


def _ratings_map(current: list[dict]) -> dict[str, float]:
    return {r["team"]: float(r["rating"]) for r in current}


def _tier(rating: float) -> str:
    if rating >= 8:   return "ELITE"
    if rating >= 4:   return "CONTENDER"
    if rating >= 0:   return "AVERAGE"
    if rating >= -4:  return "BELOW"
    return "BOTTOM"


def _fetch_espn_scores(week: int) -> list[dict[str, Any]]:
    """
    Pull completed game scores from ESPN for a given NFL regular season week.
    Returns list of {home, away, home_score, away_score} dicts.
    """
    url = (
        f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
        f"?seasontype=2&week={week}&limit=20"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json.loads(resp.read())
    except Exception as exc:
        logger.error("ESPN fetch failed: %s", exc)
        return []

    games: list[dict[str, Any]] = []
    for event in raw.get("events", []):
        comp = event.get("competitions", [{}])[0]
        competitors = comp.get("competitors", [])
        if len(competitors) != 2:
            continue

        # status check — only completed games
        status = comp.get("status", {}).get("type", {}).get("completed", False)
        if not status:
            logger.info("Game not yet complete: %s", event.get("name", "?"))
            continue

        home_team = away_team = None
        home_score = away_score = 0
        for c in competitors:
            name = c.get("team", {}).get("displayName", "")
            abbr = ESPN_TO_ABBR.get(name)
            score = int(c.get("score", 0) or 0)
            if c.get("homeAway") == "home":
                home_team, home_score = abbr, score
            else:
                away_team, away_score = abbr, score

        if home_team and away_team:
            games.append({
                "home": home_team,
                "away": away_team,
                "home_score": home_score,
                "away_score": away_score,
                "margin": home_score - away_score,  # positive = home win
            })
            logger.info(
                "  %s %d – %s %d  (margin: %+d)",
                home_team, home_score, away_team, away_score, home_score - away_score,
            )

    return games


def recalculate_week(week: int, dry_run: bool = False) -> dict[str, Any]:
    """
    Pull ESPN scores for the given week, apply Walters formula, update ratings.
    Returns summary dict.
    """
    data = _load_ratings()
    current_ratings = _ratings_map(data["current"])

    logger.info("Fetching ESPN scores for Week %d...", week)
    games = _fetch_espn_scores(week)

    if not games:
        logger.warning("No completed games found for Week %d", week)
        return {"week": week, "games_processed": 0, "changes": []}

    # First pass — collect all TGPL values (use pre-week ratings for all calcs)
    tgpl_values: dict[str, list[float]] = {t: [] for t in current_ratings}

    for g in games:
        home, away = g["home"], g["away"]
        margin = g["margin"]  # positive = home won by margin
        opp_home = current_ratings.get(away, 0.0)
        opp_away = current_ratings.get(home, 0.0)

        if home in tgpl_values:
            tgpl_home = margin + opp_home - HOME_FIELD
            tgpl_values[home].append(tgpl_home)

        if away in tgpl_values:
            tgpl_away = (-margin) + opp_away + HOME_FIELD
            tgpl_values[away].append(tgpl_away)

    # Second pass — apply Walters formula
    new_ratings: dict[str, float] = {}
    changes: list[dict] = []

    for team, old_rating in current_ratings.items():
        tgpls = tgpl_values.get(team, [])
        if tgpls:
            avg_tgpl = sum(tgpls) / len(tgpls)
            new_rating = round(DECAY * old_rating + LEARN * avg_tgpl, 2)
        else:
            # Bye week — rating decays very slightly toward 0
            new_rating = round(old_rating * 0.99, 2)

        new_ratings[team] = new_rating
        change = round(new_rating - old_rating, 2)
        changes.append({
            "team": team,
            "team_name": FULL_NAME.get(team, team),
            "old_rating": old_rating,
            "new_rating": new_rating,
            "change": change,
            "played": bool(tgpl_values.get(team)),
        })

    # Sort by new rating descending → assign ranks
    changes.sort(key=lambda x: x["new_rating"], reverse=True)
    for i, c in enumerate(changes):
        c["new_rank"] = i + 1
        c["new_tier"] = _tier(c["new_rating"])

    # Build updated current list
    new_current = [
        {
            "rank": i + 1,
            "team": c["team"],
            "team_name": c["team_name"],
            "rating": c["new_rating"],
            "tier": c["new_tier"],
        }
        for i, c in enumerate(changes)
    ]

    summary = {
        "week": week,
        "games_processed": len(games),
        "processed_at": datetime.utcnow().isoformat(),
        "changes": changes,
        "ratings_snapshot": {c["team"]: c["new_rating"] for c in changes},
    }

    if not dry_run:
        data["current"] = new_current
        data["last_updated_week"] = week
        data["week_ratings"][f"week_{week}"] = {
            "ratings": {c["team"]: c["new_rating"] for c in changes},
            "processed_at": summary["processed_at"],
            "games": len(games),
        }
        _save_ratings(data)
        logger.info("Updated ratings through Week %d (%d games)", week, len(games))
    else:
        logger.info("[DRY RUN] Would update %d team ratings", len(changes))

    # Print top/bottom movers
    movers = sorted(changes, key=lambda x: abs(x["change"]), reverse=True)[:5]
    logger.info("\nTop movers:")
    for m in movers:
        arrow = "↑" if m["change"] > 0 else "↓"
        logger.info("  %s %s  %+.2f  (%.2f → %.2f)", m["team"], arrow, m["change"], m["old_rating"], m["new_rating"])

    return summary


def print_status() -> None:
    data = _load_ratings()
    last_week = data.get("last_updated_week", 0)
    season = data.get("season", "2026")
    updated_at = data.get("updated_at", "never")
    weeks_done = list(data.get("week_ratings", {}).keys())

    print(f"\n{'='*50}")
    print(f"  Walters Engine — {season} Season")
    print(f"{'='*50}")
    print(f"  Last updated: Week {last_week} ({updated_at[:10] if updated_at != 'never' else 'never'})")
    print(f"  Weeks processed: {', '.join(weeks_done) if weeks_done else 'none (preseason)'}")
    print(f"\n  Current Top 10:")
    for r in data["current"][:10]:
        print(f"    #{r['rank']:2d} {r['team']:<5} {r['rating']:+.2f}  [{r['tier']}]")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Walters Power Rating weekly updater")
    parser.add_argument("--week", type=int, help="NFL week number to process (1-18)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    parser.add_argument("--status", action="store_true", help="Show current engine state")
    args = parser.parse_args()

    if args.status:
        print_status()
    elif args.week:
        result = recalculate_week(args.week, dry_run=args.dry_run)
        print(f"\nProcessed {result['games_processed']} games for Week {result['week']}")
    else:
        parser.print_help()
        sys.exit(1)
