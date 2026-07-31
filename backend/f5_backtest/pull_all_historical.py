"""
Complete Historical Odds Pull — One Pass

Pulls ALL markets for the 2024 MLB season in a single pass:
  1. Full-game odds (bulk endpoint): h2h, totals, spreads — 30 credits/day
  2. Event list per day — 1 credit/day
  3. Per-event F5 odds: 3-way, totals, 2-way ML — 30 credits/event

Total: ~87,000 credits for ~2,430 games

Usage:
  python3 pull_all_historical.py --key YOUR_API_KEY
  python3 pull_all_historical.py --key YOUR_API_KEY --start 2024-04-01 --end 2024-09-30
  python3 pull_all_historical.py --key YOUR_API_KEY --check-credits
  python3 pull_all_historical.py --key YOUR_API_KEY --resume  # skip already-fetched dates
"""

import httpx
import sqlite3
import json
import time
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

ODDS_API = "https://api.the-odds-api.com/v4"
DB_PATH = Path(__file__).parent / "f5_backtest.db"

F5_MARKETS = "h2h_3_way_1st_5_innings,totals_1st_5_innings,h2h_1st_5_innings"
FG_MARKETS = "h2h,totals,spreads"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS odds_pulls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_date TEXT NOT NULL,
            event_id TEXT NOT NULL,
            away_team TEXT,
            home_team TEXT,
            commence_time TEXT,
            snapshot_time TEXT,

            -- Full-game odds (first book found)
            fg_ml_away INTEGER,
            fg_ml_home INTEGER,
            fg_total_line REAL,
            fg_over_odds INTEGER,
            fg_under_odds INTEGER,
            fg_spread_line REAL,
            fg_spread_away_odds INTEGER,
            fg_spread_home_odds INTEGER,

            -- F5 3-way (best tie odds across books)
            f5_3way_away INTEGER,
            f5_3way_tie INTEGER,
            f5_3way_home INTEGER,
            f5_3way_book TEXT,
            f5_best_tie INTEGER,
            f5_best_tie_book TEXT,
            f5_worst_tie INTEGER,
            f5_tie_book_count INTEGER,

            -- F5 total (most common line)
            f5_total_line REAL,
            f5_over_odds INTEGER,
            f5_under_odds INTEGER,
            f5_total_book TEXT,
            f5_line_variations TEXT,  -- JSON: all unique lines offered

            -- F5 2-way ML
            f5_ml_away INTEGER,
            f5_ml_home INTEGER,
            f5_ml_book TEXT,

            -- All books raw data (JSON for deep analysis later)
            f5_3way_all_books TEXT,  -- JSON array of {book, away, tie, home}
            f5_total_all_books TEXT, -- JSON array of {book, line, over, under}
            fg_total_all_books TEXT, -- JSON array of {book, line, over, under}

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(event_id, game_date)
        );

        CREATE TABLE IF NOT EXISTS pull_log (
            game_date TEXT PRIMARY KEY,
            fg_pulled INTEGER DEFAULT 0,
            f5_pulled INTEGER DEFAULT 0,
            events_found INTEGER DEFAULT 0,
            events_with_f5 INTEGER DEFAULT 0,
            credits_used INTEGER DEFAULT 0,
            pulled_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_op_date ON odds_pulls(game_date);
        CREATE INDEX IF NOT EXISTS idx_op_teams ON odds_pulls(away_team, home_team);
    """)
    conn.commit()


def check_credits(api_key):
    with httpx.Client() as client:
        r = client.get(f"{ODDS_API}/sports/", params={"apiKey": api_key})
        return {
            "remaining": r.headers.get("x-requests-remaining", "?"),
            "used": r.headers.get("x-requests-used", "?"),
        }


def generate_dates(start, end):
    dates = []
    current = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    while current <= end_dt:
        if 3 <= current.month <= 10:
            dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates


def extract_fg_odds(event):
    """Extract full-game odds from bulk endpoint event"""
    result = {
        "fg_ml_away": None, "fg_ml_home": None,
        "fg_total_line": None, "fg_over_odds": None, "fg_under_odds": None,
        "fg_spread_line": None, "fg_spread_away_odds": None, "fg_spread_home_odds": None,
        "fg_total_all_books": [],
    }

    away = event.get("away_team", "")
    home = event.get("home_team", "")

    for b in event.get("bookmakers", []):
        for m in b.get("markets", []):
            if m["key"] == "h2h" and result["fg_ml_away"] is None:
                for o in m["outcomes"]:
                    if o["name"] == away:
                        result["fg_ml_away"] = o["price"]
                    elif o["name"] == home:
                        result["fg_ml_home"] = o["price"]

            elif m["key"] == "totals":
                over = under = line = None
                for o in m["outcomes"]:
                    if o["name"] == "Over":
                        over = o["price"]
                        line = o.get("point")
                    elif o["name"] == "Under":
                        under = o["price"]
                if line is not None:
                    result["fg_total_all_books"].append({
                        "book": b["title"], "line": line, "over": over, "under": under
                    })
                    if result["fg_total_line"] is None:
                        result["fg_total_line"] = line
                        result["fg_over_odds"] = over
                        result["fg_under_odds"] = under

            elif m["key"] == "spreads" and result["fg_spread_line"] is None:
                for o in m["outcomes"]:
                    if o["name"] == away:
                        result["fg_spread_line"] = o.get("point")
                        result["fg_spread_away_odds"] = o["price"]
                    elif o["name"] == home:
                        result["fg_spread_home_odds"] = o["price"]

    result["fg_total_all_books"] = json.dumps(result["fg_total_all_books"])
    return result


def extract_f5_odds(event_data):
    """Extract F5 odds from per-event endpoint"""
    result = {
        "f5_3way_away": None, "f5_3way_tie": None, "f5_3way_home": None,
        "f5_3way_book": None, "f5_best_tie": None, "f5_best_tie_book": None,
        "f5_worst_tie": None, "f5_tie_book_count": 0,
        "f5_total_line": None, "f5_over_odds": None, "f5_under_odds": None,
        "f5_total_book": None, "f5_line_variations": None,
        "f5_ml_away": None, "f5_ml_home": None, "f5_ml_book": None,
        "f5_3way_all_books": [], "f5_total_all_books": [],
    }

    away = event_data.get("away_team", "")
    home = event_data.get("home_team", "")
    tie_odds_list = []
    f5_lines = []

    for b in event_data.get("bookmakers", []):
        book = b["title"]
        for m in b.get("markets", []):
            if m["key"] == "h2h_3_way_1st_5_innings":
                entry = {"book": book}
                for o in m["outcomes"]:
                    if o["name"] == away:
                        entry["away"] = o["price"]
                        if result["f5_3way_away"] is None:
                            result["f5_3way_away"] = o["price"]
                            result["f5_3way_book"] = book
                    elif o["name"] == home:
                        entry["home"] = o["price"]
                        if result["f5_3way_home"] is None:
                            result["f5_3way_home"] = o["price"]
                    elif o["name"].lower() in ("draw", "tie"):
                        entry["tie"] = o["price"]
                        tie_odds_list.append(o["price"])
                        if result["f5_3way_tie"] is None:
                            result["f5_3way_tie"] = o["price"]
                result["f5_3way_all_books"].append(entry)

            elif m["key"] == "totals_1st_5_innings":
                entry = {"book": book}
                for o in m["outcomes"]:
                    if o["name"] == "Over":
                        entry["over"] = o["price"]
                        entry["line"] = o.get("point")
                        f5_lines.append(o.get("point"))
                        if result["f5_total_line"] is None:
                            result["f5_total_line"] = o.get("point")
                            result["f5_over_odds"] = o["price"]
                            result["f5_total_book"] = book
                    elif o["name"] == "Under":
                        entry["under"] = o["price"]
                        if result["f5_under_odds"] is None:
                            result["f5_under_odds"] = o["price"]
                result["f5_total_all_books"].append(entry)

            elif m["key"] == "h2h_1st_5_innings":
                for o in m["outcomes"]:
                    if o["name"] == away and result["f5_ml_away"] is None:
                        result["f5_ml_away"] = o["price"]
                        result["f5_ml_book"] = book
                    elif o["name"] == home and result["f5_ml_home"] is None:
                        result["f5_ml_home"] = o["price"]

    if tie_odds_list:
        result["f5_best_tie"] = max(tie_odds_list)
        result["f5_worst_tie"] = min(tie_odds_list)
        result["f5_tie_book_count"] = len(tie_odds_list)
        # Find which book has best tie
        for entry in result["f5_3way_all_books"]:
            if entry.get("tie") == result["f5_best_tie"]:
                result["f5_best_tie_book"] = entry["book"]
                break

    if f5_lines:
        result["f5_line_variations"] = json.dumps(sorted(set(f5_lines)))

    result["f5_3way_all_books"] = json.dumps(result["f5_3way_all_books"])
    result["f5_total_all_books"] = json.dumps(result["f5_total_all_books"])
    return result


def run_full_pull(api_key, start, end, resume=False):
    conn = get_db()
    init_tables(conn)

    dates = generate_dates(start, end)

    # Check what's already done
    done = set()
    if resume:
        rows = conn.execute("SELECT game_date FROM pull_log WHERE f5_pulled = 1").fetchall()
        done = {r["game_date"] for r in rows}

    dates_todo = [d for d in dates if d not in done]

    credits = check_credits(api_key)
    print(f"{'='*70}")
    print(f"FULL HISTORICAL PULL — ONE PASS")
    print(f"{'='*70}")
    print(f"  Range: {start} to {end}")
    print(f"  Total dates: {len(dates)}")
    print(f"  Already done: {len(done)}")
    print(f"  To fetch: {len(dates_todo)}")
    print(f"  Credits available: {credits['remaining']}")
    print(f"{'='*70}\n")

    total_events = 0
    total_f5 = 0
    credits_spent = 0

    with httpx.Client(timeout=30) as client:
        for i, date in enumerate(dates_todo):
            snapshot = f"{date}T16:00:00Z"
            day_credits = 0

            # ── Step 1: Full-game bulk odds ──
            try:
                r = client.get(f"{ODDS_API}/historical/sports/baseball_mlb/odds",
                              params={"apiKey": api_key, "regions": "us",
                                      "markets": FG_MARKETS, "oddsFormat": "american",
                                      "date": snapshot})
                day_credits += 30
                fg_events = r.json().get("data", []) if r.status_code == 200 else []
            except Exception as e:
                print(f"  [{i+1}/{len(dates_todo)}] {date}: FG bulk error: {e}")
                fg_events = []
            time.sleep(0.5)

            # ── Step 2: Event list ──
            try:
                r = client.get(f"{ODDS_API}/historical/sports/baseball_mlb/events",
                              params={"apiKey": api_key, "date": snapshot})
                day_credits += 1
                events = r.json().get("data", []) if r.status_code == 200 else []
            except Exception as e:
                print(f"  [{i+1}/{len(dates_todo)}] {date}: events error: {e}")
                events = []
            time.sleep(0.3)

            if not events:
                # Log and skip
                conn.execute("INSERT OR REPLACE INTO pull_log (game_date, fg_pulled, f5_pulled, events_found, credits_used) VALUES (?,1,1,0,?)",
                            (date, day_credits))
                conn.commit()
                credits_spent += day_credits
                print(f"  [{i+1}/{len(dates_todo)}] {date}: no events")
                continue

            # Build FG lookup by teams
            fg_lookup = {}
            for e in fg_events:
                key = f"{e.get('away_team')}|{e.get('home_team')}"
                fg_lookup[key] = e

            # ── Step 3: Per-event F5 odds ──
            day_f5_count = 0
            for event in events:
                eid = event["id"]
                away = event.get("away_team", "")
                home = event.get("home_team", "")

                try:
                    r = client.get(f"{ODDS_API}/historical/sports/baseball_mlb/events/{eid}/odds",
                                  params={"apiKey": api_key, "regions": "us",
                                          "markets": F5_MARKETS, "oddsFormat": "american",
                                          "date": snapshot})
                    day_credits += 30  # 3 markets × 10
                    f5_data = r.json().get("data", {}) if r.status_code == 200 else {}
                except Exception as e:
                    f5_data = {}
                time.sleep(0.4)

                # Extract odds
                fg_event = fg_lookup.get(f"{away}|{home}", {})
                fg_odds = extract_fg_odds(fg_event) if fg_event else {
                    "fg_ml_away": None, "fg_ml_home": None,
                    "fg_total_line": None, "fg_over_odds": None, "fg_under_odds": None,
                    "fg_spread_line": None, "fg_spread_away_odds": None, "fg_spread_home_odds": None,
                    "fg_total_all_books": "[]",
                }
                f5_odds = extract_f5_odds(f5_data) if f5_data else {
                    "f5_3way_away": None, "f5_3way_tie": None, "f5_3way_home": None,
                    "f5_3way_book": None, "f5_best_tie": None, "f5_best_tie_book": None,
                    "f5_worst_tie": None, "f5_tie_book_count": 0,
                    "f5_total_line": None, "f5_over_odds": None, "f5_under_odds": None,
                    "f5_total_book": None, "f5_line_variations": None,
                    "f5_ml_away": None, "f5_ml_home": None, "f5_ml_book": None,
                    "f5_3way_all_books": "[]", "f5_total_all_books": "[]",
                }

                has_f5 = f5_odds["f5_3way_tie"] is not None or f5_odds["f5_total_line"] is not None
                if has_f5:
                    day_f5_count += 1

                # Store
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO odds_pulls (
                            game_date, event_id, away_team, home_team, commence_time, snapshot_time,
                            fg_ml_away, fg_ml_home, fg_total_line, fg_over_odds, fg_under_odds,
                            fg_spread_line, fg_spread_away_odds, fg_spread_home_odds,
                            f5_3way_away, f5_3way_tie, f5_3way_home, f5_3way_book,
                            f5_best_tie, f5_best_tie_book, f5_worst_tie, f5_tie_book_count,
                            f5_total_line, f5_over_odds, f5_under_odds, f5_total_book, f5_line_variations,
                            f5_ml_away, f5_ml_home, f5_ml_book,
                            f5_3way_all_books, f5_total_all_books, fg_total_all_books
                        ) VALUES (
                            :gd, :eid, :away, :home, :ct, :snap,
                            :fg_ml_away, :fg_ml_home, :fg_total_line, :fg_over_odds, :fg_under_odds,
                            :fg_spread_line, :fg_spread_away_odds, :fg_spread_home_odds,
                            :f5_3way_away, :f5_3way_tie, :f5_3way_home, :f5_3way_book,
                            :f5_best_tie, :f5_best_tie_book, :f5_worst_tie, :f5_tie_book_count,
                            :f5_total_line, :f5_over_odds, :f5_under_odds, :f5_total_book, :f5_line_variations,
                            :f5_ml_away, :f5_ml_home, :f5_ml_book,
                            :f5_3way_all_books, :f5_total_all_books, :fg_total_all_books
                        )
                    """, {
                        "gd": date, "eid": eid, "away": away, "home": home,
                        "ct": event.get("commence_time", ""), "snap": snapshot,
                        **fg_odds, **f5_odds,
                    })
                except Exception as e:
                    print(f"    Store error: {e}")

                total_events += 1

            conn.commit()
            total_f5 += day_f5_count
            credits_spent += day_credits

            # Log this date as done
            conn.execute("""
                INSERT OR REPLACE INTO pull_log
                (game_date, fg_pulled, f5_pulled, events_found, events_with_f5, credits_used)
                VALUES (?,1,1,?,?,?)
            """, (date, len(events), day_f5_count, day_credits))
            conn.commit()

            print(f"  [{i+1}/{len(dates_todo)}] {date}: {len(events)} games, {day_f5_count} w/F5 data ({day_credits} credits)")

            # Progress checkpoint every 20 dates
            if (i + 1) % 20 == 0:
                cr = check_credits(api_key)
                print(f"\n  --- Checkpoint: {i+1}/{len(dates_todo)} dates | {total_events} events | "
                      f"{total_f5} w/F5 | Credits: {cr['remaining']} remaining ---\n")

    # Final summary
    cr = check_credits(api_key)
    total_records = conn.execute("SELECT COUNT(*) as c FROM odds_pulls").fetchone()["c"]
    with_f5_tie = conn.execute("SELECT COUNT(*) as c FROM odds_pulls WHERE f5_3way_tie IS NOT NULL").fetchone()["c"]
    with_f5_total = conn.execute("SELECT COUNT(*) as c FROM odds_pulls WHERE f5_total_line IS NOT NULL").fetchone()["c"]
    with_fg = conn.execute("SELECT COUNT(*) as c FROM odds_pulls WHERE fg_total_line IS NOT NULL").fetchone()["c"]

    print(f"\n{'='*70}")
    print(f"PULL COMPLETE")
    print(f"{'='*70}")
    print(f"  Total records: {total_records:,}")
    print(f"  With full-game odds: {with_fg:,}")
    print(f"  With F5 3-way (tie): {with_f5_tie:,}")
    print(f"  With F5 total line: {with_f5_total:,}")
    print(f"  Credits used this run: ~{credits_spent:,}")
    print(f"  Credits remaining: {cr['remaining']}")
    print(f"  Database: {DB_PATH}")
    print(f"{'='*70}")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    parser.add_argument("--start", default="2024-03-20")
    parser.add_argument("--end", default="2024-10-01")
    parser.add_argument("--check-credits", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Skip already-fetched dates")
    args = parser.parse_args()

    if args.check_credits:
        cr = check_credits(args.key)
        print(f"Credits: {cr['remaining']} remaining ({cr['used']} used)")
    else:
        run_full_pull(args.key, args.start, args.end, args.resume)
