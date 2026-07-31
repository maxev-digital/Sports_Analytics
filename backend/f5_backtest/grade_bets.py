#!/usr/bin/env python3
"""
F5 Edge — Bet Grader

Checks results for a given date. Pulls final scores from MLB API (free)
and grades each signal's outcome.

Usage:
  python3 grade_bets.py                    # grade today
  python3 grade_bets.py --date 2026-07-31  # grade specific date
"""

import httpx
import sqlite3
import json
import argparse
from datetime import date, datetime
from pathlib import Path

MLB_API = "https://statsapi.mlb.com/api/v1"
DB_PATH = Path(__file__).parent / "f5_backtest.db"
TRACKER_PATH = Path(__file__).parent / "pl_tracker.json"

HIGH_TIE_UMPS = [
    "Bill Miller", "Lance Barrett", "Larry Vanover", "CB Bucknor",
    "Gabe Morales", "Will Little", "Shane Livensparger", "Alfonso Márquez",
    "Dan Merzel", "Quinn Wolcott", "Mark Wegner", "Nestor Ceja",
    "Mike Muchlinski", "D.J. Reyburn", "Vic Carapazza", "Phil Cuzzi",
    "Ryan Additon", "Tripp Gibson", "Adrian Johnson"
]

HIGH_TIE_VENUES = ["Chase Field", "Globe Life Field", "Yankee Stadium", "Citi Field",
                    "Busch Stadium", "American Family Field"]
UNDER_VENUES = ["Globe Life Field", "Kauffman Stadium", "Comerica Park", "Wrigley Field", "Citi Field"]


def get_results(scan_date):
    """Pull final scores + inning data from MLB API"""
    with httpx.Client() as client:
        r = client.get(f"{MLB_API}/schedule", params={
            "sportId": 1, "startDate": scan_date, "endDate": scan_date,
            "gameType": "R", "hydrate": "linescore,probablePitcher,officials"
        }, timeout=15)

        results = []
        for d in r.json().get("dates", []):
            for g in d.get("games", []):
                if g.get("status", {}).get("detailedState") not in ("Final", "Completed Early"):
                    continue

                ls = g.get("linescore", {})
                innings = ls.get("innings", [])
                if len(innings) < 5:
                    continue

                away = g["teams"]["away"]["team"]["name"]
                home = g["teams"]["home"]["team"]["name"]
                venue = g.get("venue", {}).get("name", "")

                away_r5 = sum(i.get("away", {}).get("runs", 0) for i in innings[:5])
                home_r5 = sum(i.get("home", {}).get("runs", 0) for i in innings[:5])
                f1_away = innings[0].get("away", {}).get("runs", 0)
                f1_home = innings[0].get("home", {}).get("runs", 0)

                away_final = ls.get("teams", {}).get("away", {}).get("runs", 0)
                home_final = ls.get("teams", {}).get("home", {}).get("runs", 0)

                ap = g["teams"]["away"].get("probablePitcher", {})
                hp_pitcher = g["teams"]["home"].get("probablePitcher", {})
                officials = g.get("officials", [])
                hp_ump = next((o["official"]["fullName"] for o in officials
                              if o.get("officialType") == "Home Plate"), None)

                # Get pitcher ERAs
                away_era = home_era = None
                if ap.get("id"):
                    try:
                        r2 = client.get(f"{MLB_API}/people/{ap['id']}/stats",
                                       params={"stats": "season", "season": scan_date[:4], "group": "pitching"}, timeout=10)
                        splits = r2.json().get("stats", [{}])[0].get("splits", [])
                        if splits:
                            away_era = float(splits[0]["stat"].get("era", 99))
                    except: pass
                if hp_pitcher.get("id"):
                    try:
                        r2 = client.get(f"{MLB_API}/people/{hp_pitcher['id']}/stats",
                                       params={"stats": "season", "season": scan_date[:4], "group": "pitching"}, timeout=10)
                        splits = r2.json().get("stats", [{}])[0].get("splits", [])
                        if splits:
                            home_era = float(splits[0]["stat"].get("era", 99))
                    except: pass

                results.append({
                    "away_team": away, "home_team": home, "venue": venue,
                    "away_pitcher": ap.get("fullName", "TBD"),
                    "home_pitcher": hp_pitcher.get("fullName", "TBD"),
                    "away_era": away_era, "home_era": home_era,
                    "era_diff": abs(away_era - home_era) if away_era and home_era else None,
                    "hp_umpire": hp_ump,
                    "f1_tied": f1_away == f1_home,
                    "f5_tied": away_r5 == home_r5,
                    "f5_total": away_r5 + home_r5,
                    "f5_leader": "away" if away_r5 > home_r5 else "home" if home_r5 > away_r5 else "tie",
                    "away_runs_5": away_r5, "home_runs_5": home_r5,
                    "total_runs_final": away_final + home_final,
                    "away_final": away_final, "home_final": home_final,
                })

        return results


def grade(scan_date, fg_total_lines=None):
    """Grade all signals against actual results"""
    results = get_results(scan_date)

    if not results:
        print(f"No completed games found for {scan_date}")
        return

    print(f"\n{'='*80}")
    print(f"  GRADING — {scan_date} ({len(results)} completed games)")
    print(f"{'='*80}")

    grades = {
        "f5_tie": {"bets": 0, "wins": 0, "pl": 0},
        "f5_under": {"bets": 0, "wins": 0, "pl": 0},
        "f5_fav_ml": {"bets": 0, "wins": 0, "pl": 0},
        "f5_tie_under_sgp": {"bets": 0, "wins": 0, "pl": 0},
        "f1_fg_under_sgp": {"bets": 0, "wins": 0, "pl": 0},
        "venue_under": {"bets": 0, "wins": 0, "pl": 0},
    }

    for g in results:
        plays = []
        away_era = g["away_era"]
        home_era = g["home_era"]
        era_diff = g["era_diff"]

        # Determine which signals fired (same logic as scanner)
        ace_ace = away_era and home_era and away_era < 3.5 and home_era < 3.5
        both_under_4 = away_era and home_era and away_era < 4.0 and home_era < 4.0
        both_under_45 = away_era and home_era and away_era < 4.5 and home_era < 4.5
        venue_tie = g["venue"] in HIGH_TIE_VENUES and both_under_4

        # F5 Tie
        if ace_ace or venue_tie:
            won = g["f5_tied"]
            # Estimate tie odds at +450 avg
            pl = 100 * 4.5 if won else -100
            grades["f5_tie"]["bets"] += 1
            grades["f5_tie"]["wins"] += int(won)
            grades["f5_tie"]["pl"] += pl
            plays.append(("F5 Tie", won, pl))

        # F5 Under
        if both_under_45:
            # Need to know the F5 line — estimate from FG total
            # Use 4.5 as default F5 line
            est_line = 4.5
            won = g["f5_total"] < est_line
            push = g["f5_total"] == est_line
            if not push:
                pl = 100 * 0.91 if won else -100  # -110 odds
                grades["f5_under"]["bets"] += 1
                grades["f5_under"]["wins"] += int(won)
                grades["f5_under"]["pl"] += pl
                plays.append(("F5 Under", won, pl))

        # F5 Fav ML
        if era_diff and era_diff >= 1.0:
            fav = "home" if home_era and away_era and home_era < away_era else "away"
            won = g["f5_leader"] == fav
            tied = g["f5_leader"] == "tie"
            # Estimate fav odds at -130 avg
            if tied:
                pl = -100  # tie = loss on 2-way ML
            elif won:
                pl = 100 * 0.77  # -130 odds
            else:
                pl = -100
            grades["f5_fav_ml"]["bets"] += 1
            grades["f5_fav_ml"]["wins"] += int(won)
            grades["f5_fav_ml"]["pl"] += pl
            plays.append(("F5 Fav ML", won, pl))

        # F5 Tie + Under SGP
        if ace_ace or venue_tie:
            est_line = 4.5
            won = g["f5_tied"] and g["f5_total"] < est_line
            pl = 25 * 9.0 if won else -25  # ~+900 parlay odds
            grades["f5_tie_under_sgp"]["bets"] += 1
            grades["f5_tie_under_sgp"]["wins"] += int(won)
            grades["f5_tie_under_sgp"]["pl"] += pl
            plays.append(("Tie+Under SGP", won, pl))

        # F1 + FG Under SGP
        if both_under_45:
            won = g["f1_tied"] and g["total_runs_final"] < 8.5  # est FG line
            pl = 25 * 3.0 if won else -25  # ~+300 parlay odds est
            grades["f1_fg_under_sgp"]["bets"] += 1
            grades["f1_fg_under_sgp"]["wins"] += int(won)
            grades["f1_fg_under_sgp"]["pl"] += pl
            plays.append(("F1+FG Under SGP", won, pl))

        if plays:
            result_str = f"{g['away_runs_5']}-{g['home_runs_5']} after 5 (F1: {'tied' if g['f1_tied'] else 'not tied'}) | Final: {g['away_final']}-{g['home_final']}"
            print(f"\n  {g['away_team']} @ {g['home_team']}")
            print(f"    {g['away_pitcher']} ({g['away_era']:.2f}) vs {g['home_pitcher']} ({g['home_era']:.2f})")
            print(f"    Result: {result_str}")
            for name, won, pl in plays:
                status = "WIN" if won else "LOSS"
                print(f"    {'$' if won else ' '} {name:<22} {status:<5} ${pl:+.0f}")

    # Summary
    print(f"\n{'='*80}")
    print(f"  DAILY P&L SUMMARY — {scan_date}")
    print(f"{'='*80}")

    total_pl = 0
    total_bets = 0
    total_wins = 0
    print(f"\n  {'Signal':<25} {'Bets':>5} {'Wins':>5} {'W%':>6} {'P&L':>9}")
    print(f"  {'-'*55}")
    for name, data in grades.items():
        if data["bets"] > 0:
            pct = data["wins"] / data["bets"] * 100
            print(f"  {name:<25} {data['bets']:>5} {data['wins']:>5} {pct:>5.0f}% ${data['pl']:>8,.0f}")
            total_pl += data["pl"]
            total_bets += data["bets"]
            total_wins += data["wins"]

    print(f"  {'-'*55}")
    print(f"  {'TOTAL':<25} {total_bets:>5} {total_wins:>5} {total_wins/total_bets*100 if total_bets else 0:>5.0f}% ${total_pl:>8,.0f}")

    # Save to tracker
    save_to_tracker(scan_date, grades, total_pl)

    return grades


def save_to_tracker(scan_date, grades, total_pl):
    """Append today's results to the running P&L tracker"""
    tracker = {}
    if TRACKER_PATH.exists():
        with open(TRACKER_PATH) as f:
            tracker = json.load(f)

    if "daily" not in tracker:
        tracker["daily"] = {}
    if "running" not in tracker:
        tracker["running"] = {"total_pl": 0, "total_bets": 0, "total_wins": 0, "days": 0}

    tracker["daily"][scan_date] = {
        "pl": total_pl,
        "bets": sum(d["bets"] for d in grades.values()),
        "wins": sum(d["wins"] for d in grades.values()),
        "signals": {k: dict(v) for k, v in grades.items() if v["bets"] > 0},
    }

    tracker["running"]["total_pl"] += total_pl
    tracker["running"]["total_bets"] += sum(d["bets"] for d in grades.values())
    tracker["running"]["total_wins"] += sum(d["wins"] for d in grades.values())
    tracker["running"]["days"] += 1

    r = tracker["running"]
    roi = r["total_pl"] / (r["total_bets"] * 100) * 100 if r["total_bets"] > 0 else 0

    print(f"\n  RUNNING TOTALS ({r['days']} days):")
    print(f"    Total P&L: ${r['total_pl']:+,.0f}")
    print(f"    Total bets: {r['total_bets']}")
    print(f"    Win rate: {r['total_wins']/r['total_bets']*100:.1f}%" if r["total_bets"] else "    No bets")
    print(f"    ROI: {roi:+.1f}%")

    with open(TRACKER_PATH, "w") as f:
        json.dump(tracker, f, indent=2)
    print(f"\n  Saved to {TRACKER_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()
    grade(args.date)
