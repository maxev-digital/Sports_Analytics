"""
Madden 26 player ratings scraper.
Pulls all players from madden.tools Next.js data endpoint.
One HTTP request for the full roster, then individual calls only for players
above OVR threshold (starters) to get full attribute sets.

Output: /var/www/max-ev-sports-api/f5_backtest/madden26_players.json

Usage:
  python3 scrape_madden26.py              # full run (starters OVR >= 70)
  python3 scrape_madden26.py --ovr 75     # higher threshold = fewer detail calls
  python3 scrape_madden26.py --dry-run    # preview counts without saving
"""
from __future__ import annotations

import argparse
import json
import logging
import time
import urllib.request
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
BUILD_ID   = "PursLg0lIgGAfaYpVj7dy"
BASE_URL   = f"https://madden.tools/_next/data/{BUILD_ID}"
HEADERS    = {"User-Agent": "Mozilla/5.0 (compatible; MaxEVSports/1.0)"}
OUT_FILE   = Path(__file__).parent / "f5_backtest" / "madden26_players.json"
DELAY      = 0.25   # seconds between detail calls — polite rate limit

# Key attributes we care about for power rating / scouting use
CORE_ATTRS = [
    "rating_overall", "rating_speed", "rating_strength", "rating_awareness",
    "rating_agility", "rating_acceleration", "rating_tackle", "rating_catching",
    "rating_throw_power", "rating_throw_accuracy_short", "rating_throw_accuracy_medium",
    "rating_throw_accuracy_deep", "rating_pass_block", "rating_run_block",
    "rating_pursuit", "rating_play_recognition", "rating_man_coverage",
    "rating_zone_coverage", "rating_stamina", "rating_toughness", "rating_injury",
    "age", "height", "weight", "years_pro",
]

# Madden position → cleaner group label
POS_GROUP: dict[str, str] = {
    "QB": "QB", "HB": "RB", "FB": "RB",
    "WR": "WR", "TE": "TE",
    "LT": "OL", "LG": "OL", "C": "OL", "RG": "OL", "RT": "OL",
    "LE": "DL", "RE": "DL", "DT": "DL",
    "LOLB": "LB", "MLB": "LB", "MIKE": "LB", "ROLB": "LB",
    "CB": "DB", "FS": "DB", "SS": "DB",
    "K": "K", "P": "P",
}


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def fetch_all_teams() -> list[dict]:
    """One call — returns all 32 teams with players (OVR only)."""
    logger.info("Fetching full player roster from madden.tools…")
    data = _get(f"{BASE_URL}/players.json")
    return data["pageProps"]["teamPlayerData"]


def fetch_player_detail(slug: str) -> dict | None:
    """Individual call for full attribute set."""
    try:
        data = _get(f"{BASE_URL}/players/{slug}.json")
        return data["pageProps"]["player"]
    except Exception as exc:
        logger.warning("  Detail failed for %s: %s", slug, exc)
        return None


def scrape(ovr_threshold: int = 70, dry_run: bool = False) -> dict:
    team_data = fetch_all_teams()

    all_players: list[dict] = []
    teams_index: dict[str, list[dict]] = {}   # abbr → [player, ...]
    total_detail_calls = 0

    for td in team_data:
        team   = td["team"]
        abbr   = team["acronym"]
        t_name = team["name"]

        team_players: list[dict] = []

        for position, players in td["playersByPosition"].items():
            for p in players:
                base = {
                    "id":         p["id"],
                    "slug":       p["slug"],
                    "first_name": p["first_name"],
                    "last_name":  p["last_name"],
                    "name":       f"{p['first_name']} {p['last_name']}",
                    "position":   position,
                    "pos_group":  POS_GROUP.get(position, position),
                    "ovr":        p["rating_overall"],
                    "team":       abbr,
                    "team_name":  t_name,
                }
                team_players.append(base)

        # Sort starters first
        team_players.sort(key=lambda x: x["ovr"], reverse=True)

        # Fetch detail for starters above threshold
        for player in team_players:
            if player["ovr"] >= ovr_threshold:
                if dry_run:
                    total_detail_calls += 1
                    continue
                logger.info("  [%s] %s %s (%d OVR)", abbr, player["first_name"], player["last_name"], player["ovr"])
                detail = fetch_player_detail(player["slug"])
                if detail:
                    for attr in CORE_ATTRS:
                        if attr in detail:
                            player[attr] = detail[attr]
                total_detail_calls += 1
                time.sleep(DELAY)

        all_players.extend(team_players)
        teams_index[abbr] = team_players

    if dry_run:
        logger.info("DRY RUN — would make %d detail calls for OVR >= %d", total_detail_calls, ovr_threshold)
        return {"dry_run": True, "detail_calls": total_detail_calls}

    result = {
        "source":       "madden.tools",
        "game":         "Madden NFL 26",
        "season":       "2026",
        "scraped_at":   datetime.utcnow().isoformat(),
        "ovr_threshold": ovr_threshold,
        "player_count": len(all_players),
        "players":      all_players,
        "by_team":      teams_index,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(result, indent=2))
    logger.info("Saved %d players to %s", len(all_players), OUT_FILE)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Madden 26 player ratings")
    parser.add_argument("--ovr",     type=int, default=70, help="Minimum OVR for detail fetch (default 70)")
    parser.add_argument("--dry-run", action="store_true",  help="Preview call count without saving")
    args = parser.parse_args()

    result = scrape(ovr_threshold=args.ovr, dry_run=args.dry_run)
    if not args.dry_run:
        print(f"\nDone — {result['player_count']} players saved to {OUT_FILE}")
