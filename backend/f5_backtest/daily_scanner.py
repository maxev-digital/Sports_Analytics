#!/usr/bin/env python3
"""
F5 Edge Daily Scanner — Live Game Scanner for 2026 MLB Season

Scans today's MLB games against all proven signals.
Outputs a ranked bet slip with book routing.

Usage:
  python3 daily_scanner.py                          # scan today
  python3 daily_scanner.py --date 2026-08-01        # scan specific date
  python3 daily_scanner.py --dry-run                # don't use Odds API credits

Requires: ODDS_API_KEY env var or --key argument
"""

import httpx
import json
import sys
import os
import argparse
from datetime import datetime, date
from collections import defaultdict

ODDS_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_API = "https://api.the-odds-api.com/v4"
MLB_API = "https://statsapi.mlb.com/api/v1"

# High-tie umpires (>17% F5 tie rate from 2023-2024 data)
HIGH_TIE_UMPS = [
    "Bill Miller", "Lance Barrett", "Larry Vanover", "CB Bucknor",
    "Gabe Morales", "Will Little", "Shane Livensparger", "Alfonso Márquez",
    "Dan Merzel", "Quinn Wolcott", "Mark Wegner", "Nestor Ceja",
    "Mike Muchlinski", "D.J. Reyburn", "Vic Carapazza", "Phil Cuzzi",
    "Ryan Additon", "Tripp Gibson", "Adrian Johnson"
]

# Low-tie umpires (<10% F5 tie rate)
LOW_TIE_UMPS = [
    "Edwin Jimenez", "Mark Carlson", "Hunter Wendelstedt", "Erich Bacchus",
    "Roberto Ortiz", "Paul Clemons", "Chad Whitson", "Jim Wolf"
]

# Venue classifications for under/over edges
UNDER_VENUES = ["Globe Life Field", "Kauffman Stadium", "Comerica Park", "Wrigley Field", "Citi Field"]
OVER_VENUES = ["loanDepot park", "Progressive Field", "Angel Stadium", "Chase Field", "American Family Field"]
HIGH_TIE_VENUES = ["Chase Field", "Globe Life Field", "Yankee Stadium", "Citi Field", "Busch Stadium", "American Family Field"]

# BetMGM = soft book for F5 ties (best odds 80.5% of time)
TIE_BEST_BOOK = "BetMGM"


def american_to_decimal(a):
    if a > 0: return 1 + a / 100
    return 1 + 100 / abs(a)


def implied_prob(a):
    return 1 / american_to_decimal(a)


def get_mlb_games(scan_date):
    """Pull today's games with pitchers, umpires, venue from MLB API (FREE)"""
    with httpx.Client() as client:
        r = client.get(f"{MLB_API}/schedule", params={
            "sportId": 1, "startDate": scan_date, "endDate": scan_date,
            "gameType": "R", "hydrate": "probablePitcher,officials,venue,weather"
        }, timeout=15)

        games = []
        for d in r.json().get("dates", []):
            for g in d.get("games", []):
                if g.get("status", {}).get("abstractGameState") == "Final":
                    continue  # skip completed games

                away = g["teams"]["away"]["team"]["name"]
                home = g["teams"]["home"]["team"]["name"]
                venue = g.get("venue", {}).get("name", "Unknown")

                ap = g["teams"]["away"].get("probablePitcher", {})
                hp = g["teams"]["home"].get("probablePitcher", {})

                # Get umpire
                officials = g.get("officials", [])
                hp_ump = next((o["official"]["fullName"] for o in officials
                              if o.get("officialType") == "Home Plate"), None)

                # Weather
                weather = g.get("weather", {})

                # Get pitcher ERAs
                away_era = None
                home_era = None
                if ap.get("id"):
                    try:
                        r2 = client.get(f"{MLB_API}/people/{ap['id']}/stats",
                                       params={"stats": "season", "season": scan_date[:4], "group": "pitching"},
                                       timeout=10)
                        splits = r2.json().get("stats", [{}])[0].get("splits", [])
                        if splits:
                            away_era = float(splits[0]["stat"].get("era", 99))
                    except:
                        pass

                if hp.get("id"):
                    try:
                        r2 = client.get(f"{MLB_API}/people/{hp['id']}/stats",
                                       params={"stats": "season", "season": scan_date[:4], "group": "pitching"},
                                       timeout=10)
                        splits = r2.json().get("stats", [{}])[0].get("splits", [])
                        if splits:
                            home_era = float(splits[0]["stat"].get("era", 99))
                    except:
                        pass

                games.append({
                    "away_team": away, "home_team": home, "venue": venue,
                    "away_pitcher": ap.get("fullName", "TBD"),
                    "home_pitcher": hp.get("fullName", "TBD"),
                    "away_era": away_era, "home_era": home_era,
                    "era_diff": abs(away_era - home_era) if away_era and home_era else None,
                    "hp_umpire": hp_ump,
                    "temp": weather.get("temp"),
                    "wind": weather.get("wind"),
                    "commence": g.get("gameDate", ""),
                    "game_pk": g["gamePk"],
                })

        return games


def get_fg_odds(scan_date):
    """Pull full-game odds for all games (BULK — 30 credits)"""
    with httpx.Client() as client:
        r = client.get(f"{ODDS_API}/sports/baseball_mlb/odds", params={
            "apiKey": ODDS_KEY, "regions": "us", "markets": "h2h,totals",
            "oddsFormat": "american"
        }, timeout=15)

        remaining = r.headers.get("x-requests-remaining", "?")

        events = r.json() if r.status_code == 200 else []
        odds_by_game = {}

        for e in events:
            key = f"{e['away_team']}|{e['home_team']}"
            fg_total = None
            fg_under = None
            fg_ml_away = None
            fg_ml_home = None

            for b in e.get("bookmakers", []):
                for m in b.get("markets", []):
                    if m["key"] == "totals" and fg_total is None:
                        for o in m["outcomes"]:
                            if o["name"] == "Over":
                                fg_total = o.get("point")
                            elif o["name"] == "Under":
                                fg_under = o["price"]
                    elif m["key"] == "h2h" and fg_ml_away is None:
                        for o in m["outcomes"]:
                            if o["name"] == e["away_team"]:
                                fg_ml_away = o["price"]
                            elif o["name"] == e["home_team"]:
                                fg_ml_home = o["price"]

            odds_by_game[key] = {
                "fg_total": fg_total, "fg_under_odds": fg_under,
                "fg_ml_away": fg_ml_away, "fg_ml_home": fg_ml_home,
                "event_id": e["id"],
            }

        return odds_by_game, remaining


def get_f5_odds(event_id):
    """Pull F5 odds for a specific event (30 credits per event)"""
    with httpx.Client() as client:
        r = client.get(f"{ODDS_API}/sports/baseball_mlb/events/{event_id}/odds", params={
            "apiKey": ODDS_KEY, "regions": "us",
            "markets": "h2h_3_way_1st_5_innings,totals_1st_5_innings,h2h_1st_5_innings",
            "oddsFormat": "american"
        }, timeout=15)

        if r.status_code != 200:
            return {}

        data = r.json()
        result = {
            "f5_tie_odds": {}, "f5_total_line": None,
            "f5_under_odds": None, "f5_ml_fav": None
        }

        for b in data.get("bookmakers", []):
            for m in b.get("markets", []):
                if m["key"] == "h2h_3_way_1st_5_innings":
                    for o in m["outcomes"]:
                        if o["name"].lower() in ("draw", "tie"):
                            result["f5_tie_odds"][b["title"]] = o["price"]

                elif m["key"] == "totals_1st_5_innings" and result["f5_total_line"] is None:
                    for o in m["outcomes"]:
                        if o["name"] == "Over":
                            result["f5_total_line"] = o.get("point")
                        elif o["name"] == "Under":
                            result["f5_under_odds"] = o["price"]

        return result


def score_game(game, fg_odds):
    """Score a game against all signal filters. Return list of plays."""
    plays = []

    away_era = game["away_era"]
    home_era = game["home_era"]
    era_diff = game["era_diff"]
    venue = game["venue"]
    ump = game["hp_umpire"]
    fg_total = fg_odds.get("fg_total") if fg_odds else None
    fg_under = fg_odds.get("fg_under_odds") if fg_odds else None

    # ── SIGNAL: F1 Tie + FG Under (Bovada SGP) ──
    if fg_total and fg_under and away_era and home_era:
        tier = None
        if fg_total <= 8.0 and away_era < 4.0 and home_era < 4.0 and ump in HIGH_TIE_UMPS:
            tier = 1
        elif fg_total <= 8.0 and away_era < 4.5 and home_era < 4.5:
            tier = 2
        elif fg_total <= 8.5 and away_era < 4.5 and home_era < 4.5:
            tier = 3

        if tier:
            unit = {1: 50, 2: 25, 3: 15}[tier]
            plays.append({
                "type": "F1 Tie + FG Under SGP",
                "book": "Bovada",
                "tier": tier,
                "unit": unit,
                "signal": f"FG {fg_total} / ERA {away_era:.2f} vs {home_era:.2f}" + (f" / Ump: {ump}" if tier == 1 else ""),
                "expected_hit": {1: "43%", 2: "37%", 3: "38%"}[tier],
                "historical_roi": {1: "+76%", 2: "+50%", 3: "+52%"}[tier],
                "needs_f5_odds": False,
            })

    # ── SIGNAL: F5 Under (both ERA < 4.50) ──
    if away_era and home_era and away_era < 4.5 and home_era < 4.5:
        plays.append({
            "type": "F5 Under",
            "book": "Best line (check all books)",
            "tier": 1 if away_era < 3.5 and home_era < 3.5 else 2,
            "unit": 100,
            "signal": f"Both ERA < {'3.50' if away_era < 3.5 and home_era < 3.5 else '4.50'}",
            "expected_hit": "59%" if away_era < 3.5 and home_era < 3.5 else "55%",
            "historical_roi": "+10.7%" if away_era < 3.5 and home_era < 3.5 else "+3.2%",
            "needs_f5_odds": True,
        })

    # ── SIGNAL: F5 Fav ML (ERA diff >= 1.0) ──
    if era_diff and era_diff >= 1.0:
        fav = "home" if home_era and away_era and home_era < away_era else "away"
        hitter_park = venue in OVER_VENUES or venue in ["Great American Ball Park", "Fenway Park", "Yankee Stadium"]

        plays.append({
            "type": "F5 Favorite ML",
            "book": "Best price across all books",
            "tier": 1 if era_diff >= 1.5 and hitter_park else 2 if era_diff >= 1.5 else 3,
            "unit": 100,
            "signal": f"ERA diff {era_diff:.2f} / Fav: {game[fav+'_pitcher']}" + (" + hitter park" if hitter_park else ""),
            "expected_hit": "66%" if era_diff >= 1.5 and hitter_park else "63%" if era_diff >= 1.5 else "60%",
            "historical_roi": "+17.0%" if era_diff >= 1.5 and hitter_park else "+11.7%" if era_diff >= 1.5 else "+6.4%",
            "needs_f5_odds": True,
            "fav_side": fav,
        })

    # ── SIGNAL: F5 Tie (ace vs ace OR high-tie venue) ──
    if away_era and home_era:
        ace_ace = away_era < 3.5 and home_era < 3.5
        venue_play = venue in HIGH_TIE_VENUES and away_era < 4.0 and home_era < 4.0

        if ace_ace or venue_play:
            plays.append({
                "type": "F5 Tie",
                "book": "BetMGM (soft book, best odds 80% of time)",
                "tier": 1 if ace_ace and venue in HIGH_TIE_VENUES else 2,
                "unit": 100,
                "signal": ("Ace vs Ace" if ace_ace else "High-tie venue") + (f" + {ump}" if ump in HIGH_TIE_UMPS else ""),
                "expected_hit": "22-44%" if ace_ace and venue in HIGH_TIE_VENUES else "22%" if ace_ace else "26%",
                "historical_roi": "+22% to +153%",
                "needs_f5_odds": True,
            })

            # Also add the SGP: Tie + Under
            plays.append({
                "type": "F5 Tie + Under SGP",
                "book": "DraftKings or FanDuel",
                "tier": 1,
                "unit": 25,
                "signal": "Correlated parlay (1.51x correlation)",
                "expected_hit": "18.2%",
                "historical_roi": "+94.2%",
                "needs_f5_odds": True,
            })

    # ── SIGNAL: Venue Under/Over ──
    if venue in UNDER_VENUES and fg_total and fg_total <= 8.5:
        plays.append({
            "type": "F5 Under (venue edge)",
            "book": "Best line",
            "tier": 3,
            "unit": 50,
            "signal": f"{venue} — historically 60%+ unders",
            "expected_hit": "60-64%",
            "historical_roi": "+13 to +23%",
            "needs_f5_odds": True,
        })

    return plays


def run_scanner(scan_date, dry_run=False):
    """Main scanner: pull data, score games, output bet slip"""
    print(f"\n{'='*80}")
    print(f"  F5 EDGE SCANNER — {scan_date}")
    print(f"  {'DRY RUN (no Odds API calls)' if dry_run else 'LIVE'}")
    print(f"{'='*80}")

    # Step 1: MLB data (free)
    print(f"\n  Pulling MLB schedule + pitchers + umpires...")
    games = get_mlb_games(scan_date)
    print(f"  Found {len(games)} games")

    if not games:
        print("  No games today.")
        return

    # Step 2: FG odds (30 credits)
    fg_odds = {}
    remaining = "?"
    if not dry_run:
        print(f"  Pulling full-game odds (30 credits)...")
        fg_odds_raw, remaining = get_fg_odds(scan_date)
        # Match by team names
        for g in games:
            key = f"{g['away_team']}|{g['home_team']}"
            if key in fg_odds_raw:
                fg_odds[g["game_pk"]] = fg_odds_raw[key]
        print(f"  Matched odds for {len(fg_odds)} games | Credits remaining: {remaining}")

    # Step 3: Score every game
    print(f"\n  Scoring games against signal filters...\n")

    all_plays = []
    for g in games:
        odds = fg_odds.get(g["game_pk"], {})
        plays = score_game(g, odds)
        if plays:
            all_plays.append({"game": g, "plays": plays, "odds": odds})

    # Step 4: Output bet slip
    if not all_plays:
        print("  No qualifying games today. PASS.")
        return

    games_with_plays = len(all_plays)
    total_plays = sum(len(x["plays"]) for x in all_plays)
    f5_needed = sum(1 for x in all_plays if any(p["needs_f5_odds"] for p in x["plays"]))

    print(f"  {'='*70}")
    print(f"  TODAY'S BET SLIP — {total_plays} plays across {games_with_plays} games")
    print(f"  {'='*70}")

    total_risk = 0
    for entry in sorted(all_plays, key=lambda x: min(p["tier"] for p in x["plays"])):
        g = entry["game"]
        print(f"\n  {g['away_team']} @ {g['home_team']} ({g['venue']})")
        print(f"    Pitchers: {g['away_pitcher']} ({g['away_era']:.2f}) vs {g['home_pitcher']} ({g['home_era']:.2f})")
        if g["hp_umpire"]:
            ump_note = " ← HIGH TIE UMP" if g["hp_umpire"] in HIGH_TIE_UMPS else " ← LOW TIE UMP" if g["hp_umpire"] in LOW_TIE_UMPS else ""
            print(f"    Umpire: {g['hp_umpire']}{ump_note}")
        if g.get("temp"):
            print(f"    Weather: {g['temp']}°F, {g.get('wind','')}")

        fg = entry["odds"]
        if fg.get("fg_total"):
            print(f"    FG Total: {fg['fg_total']}")

        for p in sorted(entry["plays"], key=lambda x: x["tier"]):
            tier_label = {1: "STRONG", 2: "GOOD", 3: "STANDARD"}[p["tier"]]
            print(f"    → [{tier_label}] {p['type']} — ${p['unit']} at {p['book']}")
            print(f"       Signal: {p['signal']}")
            print(f"       Expected: {p['expected_hit']} hit rate, {p['historical_roi']} ROI")
            total_risk += p["unit"]

    print(f"\n  {'─'*70}")
    print(f"  TOTAL RISK: ${total_risk}")
    print(f"  F5 odds needed for {f5_needed} games (~{f5_needed * 30} credits)")
    if remaining != "?":
        print(f"  Credits remaining: {remaining}")

    # Step 5: Pull F5 odds for qualifying games (if not dry run)
    if not dry_run and f5_needed > 0:
        print(f"\n  Pull F5 odds for {f5_needed} qualifying games? (y/n): ", end="")
        # In automated mode, just note it
        print("(run with --pull-f5 to auto-pull)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="F5 Edge Daily Scanner")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--key", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Don't use Odds API credits")
    args = parser.parse_args()

    if args.key:
        ODDS_KEY = args.key

    run_scanner(args.date, args.dry_run)
