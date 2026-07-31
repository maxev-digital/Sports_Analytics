"""
F5 Historical Odds Pull — The Odds API

Pulls actual F5 betting lines for every MLB game day from May 2023
through October 2024. This data validates our edge matrix by showing
what the BOOKS were actually pricing each game at.

Markets pulled:
  - h2h_3_way_1st_5_innings  (F5 3-way: away/tie/home)
  - totals_1st_5_innings      (F5 over/under)
  - h2h_1st_5_innings         (F5 2-way ML)

Cost: ~10,800 credits (10 per region per market × 3 markets × 360 days)

Usage:
  python3 pull_historical_odds.py --key YOUR_API_KEY
  python3 pull_historical_odds.py --key YOUR_API_KEY --start 2024-07-01 --end 2024-07-31
  python3 pull_historical_odds.py --key YOUR_API_KEY --check-credits
"""

import httpx
import sqlite3
import json
import time
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

ODDS_API_BASE = "https://api.the-odds-api.com/v4"
DB_PATH = Path(__file__).parent / "f5_backtest.db"

F5_MARKETS = [
    "h2h_3_way_1st_5_innings",
    "totals_1st_5_innings",
    "h2h_1st_5_innings",
]

# MLB game days: typically Mon-Sun, but heaviest Tue-Sun
# Season: April through early October


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_odds_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS f5_odds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_date TEXT NOT NULL,
            event_id TEXT NOT NULL,
            away_team TEXT,
            home_team TEXT,
            commence_time TEXT,

            -- F5 3-way moneyline (the tie market)
            f5_3way_away_odds INTEGER,
            f5_3way_tie_odds INTEGER,
            f5_3way_home_odds INTEGER,
            f5_3way_bookmaker TEXT,

            -- F5 2-way moneyline
            f5_ml_away_odds INTEGER,
            f5_ml_home_odds INTEGER,
            f5_ml_bookmaker TEXT,

            -- F5 total (over/under)
            f5_total_line REAL,
            f5_over_odds INTEGER,
            f5_under_odds INTEGER,
            f5_total_bookmaker TEXT,

            -- Best odds across all books
            f5_3way_best_tie_odds INTEGER,
            f5_3way_best_tie_book TEXT,
            f5_total_best_line REAL,

            snapshot_time TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(event_id, game_date)
        );

        CREATE INDEX IF NOT EXISTS idx_odds_date ON f5_odds(game_date);
        CREATE INDEX IF NOT EXISTS idx_odds_event ON f5_odds(event_id);
        CREATE INDEX IF NOT EXISTS idx_odds_teams ON f5_odds(away_team, home_team);
    """)
    conn.commit()


def check_credits(api_key: str) -> dict:
    """Check remaining API credits"""
    with httpx.Client() as client:
        resp = client.get(f"{ODDS_API_BASE}/sports/", params={"apiKey": api_key})
        remaining = resp.headers.get("x-requests-remaining", "?")
        used = resp.headers.get("x-requests-used", "?")
        return {"remaining": remaining, "used": used}


def generate_game_dates(start: str, end: str) -> list:
    """Generate list of dates to query"""
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    dates = []
    current = start_dt
    while current <= end_dt:
        # Skip dates outside MLB season (roughly late March - early Oct)
        month = current.month
        if 3 <= month <= 10:
            dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates


def fetch_historical_odds(api_key: str, date: str, client: httpx.Client) -> list:
    """
    Fetch historical F5 odds for a specific date.
    Uses the historical odds endpoint with a noon ET snapshot.
    """
    # Use noon ET (16:00 UTC) as snapshot time — lines should be set by then
    snapshot = f"{date}T16:00:00Z"

    markets_str = ",".join(F5_MARKETS)

    try:
        resp = client.get(
            f"{ODDS_API_BASE}/historical/sports/baseball_mlb/odds",
            params={
                "apiKey": api_key,
                "regions": "us",
                "markets": markets_str,
                "oddsFormat": "american",
                "date": snapshot,
            },
            timeout=30,
        )

        if resp.status_code == 422:
            # No snapshot available for this date
            return []

        if resp.status_code == 401:
            print(f"  ERROR: Out of credits or invalid key")
            return []

        if resp.status_code != 200:
            print(f"  ERROR: HTTP {resp.status_code} for {date}")
            return []

        data = resp.json()

        # Check remaining credits from headers
        remaining = resp.headers.get("x-requests-remaining", "?")

        # The response has a 'data' key with the events
        events = data.get("data", [])
        timestamp = data.get("timestamp", snapshot)

        if remaining != "?":
            print(f"  Credits remaining: {remaining}")

        return [{"event": e, "snapshot": timestamp} for e in events]

    except Exception as e:
        print(f"  ERROR fetching {date}: {e}")
        return []


def extract_odds(event: dict) -> dict:
    """Extract best F5 odds from an event's bookmakers"""
    result = {
        "event_id": event.get("id", ""),
        "away_team": event.get("away_team", ""),
        "home_team": event.get("home_team", ""),
        "commence_time": event.get("commence_time", ""),
        # 3-way
        "f5_3way_away_odds": None,
        "f5_3way_tie_odds": None,
        "f5_3way_home_odds": None,
        "f5_3way_bookmaker": None,
        # Best tie odds across all books
        "f5_3way_best_tie_odds": None,
        "f5_3way_best_tie_book": None,
        # 2-way ML
        "f5_ml_away_odds": None,
        "f5_ml_home_odds": None,
        "f5_ml_bookmaker": None,
        # Totals
        "f5_total_line": None,
        "f5_over_odds": None,
        "f5_under_odds": None,
        "f5_total_bookmaker": None,
        "f5_total_best_line": None,
    }

    best_tie = -9999

    for bookmaker in event.get("bookmakers", []):
        book_name = bookmaker.get("title", "Unknown")

        for market in bookmaker.get("markets", []):
            market_key = market.get("key", "")
            outcomes = market.get("outcomes", [])

            if market_key == "h2h_3_way_1st_5_innings":
                for o in outcomes:
                    name = o.get("name", "")
                    price = o.get("price", 0)
                    if name == event.get("away_team"):
                        if result["f5_3way_away_odds"] is None:
                            result["f5_3way_away_odds"] = price
                            result["f5_3way_bookmaker"] = book_name
                    elif name == event.get("home_team"):
                        if result["f5_3way_home_odds"] is None:
                            result["f5_3way_home_odds"] = price
                    elif name.lower() in ("draw", "tie"):
                        if result["f5_3way_tie_odds"] is None:
                            result["f5_3way_tie_odds"] = price
                        if price > best_tie:
                            best_tie = price
                            result["f5_3way_best_tie_odds"] = price
                            result["f5_3way_best_tie_book"] = book_name

            elif market_key == "h2h_1st_5_innings":
                for o in outcomes:
                    name = o.get("name", "")
                    price = o.get("price", 0)
                    if name == event.get("away_team"):
                        if result["f5_ml_away_odds"] is None:
                            result["f5_ml_away_odds"] = price
                            result["f5_ml_bookmaker"] = book_name
                    elif name == event.get("home_team"):
                        if result["f5_ml_home_odds"] is None:
                            result["f5_ml_home_odds"] = price

            elif market_key == "totals_1st_5_innings":
                for o in outcomes:
                    name = o.get("name", "")
                    price = o.get("price", 0)
                    point = o.get("point", None)
                    if name == "Over":
                        if result["f5_over_odds"] is None:
                            result["f5_over_odds"] = price
                            result["f5_total_line"] = point
                            result["f5_total_bookmaker"] = book_name
                            result["f5_total_best_line"] = point
                    elif name == "Under":
                        if result["f5_under_odds"] is None:
                            result["f5_under_odds"] = price

    return result


def store_odds(conn, game_date: str, odds_list: list, snapshot: str):
    """Store extracted odds in the database"""
    for odds in odds_list:
        try:
            conn.execute("""
                INSERT OR REPLACE INTO f5_odds (
                    game_date, event_id, away_team, home_team, commence_time,
                    f5_3way_away_odds, f5_3way_tie_odds, f5_3way_home_odds, f5_3way_bookmaker,
                    f5_ml_away_odds, f5_ml_home_odds, f5_ml_bookmaker,
                    f5_total_line, f5_over_odds, f5_under_odds, f5_total_bookmaker,
                    f5_3way_best_tie_odds, f5_3way_best_tie_book,
                    f5_total_best_line, snapshot_time
                ) VALUES (
                    :game_date, :event_id, :away_team, :home_team, :commence_time,
                    :f5_3way_away_odds, :f5_3way_tie_odds, :f5_3way_home_odds, :f5_3way_bookmaker,
                    :f5_ml_away_odds, :f5_ml_home_odds, :f5_ml_bookmaker,
                    :f5_total_line, :f5_over_odds, :f5_under_odds, :f5_total_bookmaker,
                    :f5_3way_best_tie_odds, :f5_3way_best_tie_book,
                    :f5_total_best_line, :snapshot_time
                )
            """, {**odds, "game_date": game_date, "snapshot_time": snapshot})
        except Exception as e:
            print(f"  Store error: {e}")
    conn.commit()


def run_historical_pull(api_key: str, start: str, end: str):
    """Main pull: iterate through dates, fetch odds, store"""
    conn = get_db()
    init_odds_tables(conn)

    # Check what we already have
    existing = conn.execute(
        "SELECT DISTINCT game_date FROM f5_odds ORDER BY game_date"
    ).fetchall()
    existing_dates = {r["game_date"] for r in existing}

    dates = generate_game_dates(start, end)
    dates_to_fetch = [d for d in dates if d not in existing_dates]

    print(f"Historical F5 Odds Pull")
    print(f"  Date range: {start} to {end}")
    print(f"  Total dates in range: {len(dates)}")
    print(f"  Already fetched: {len(existing_dates)}")
    print(f"  Dates to fetch: {len(dates_to_fetch)}")
    print(f"  Estimated credits: {len(dates_to_fetch) * 30}")

    if not dates_to_fetch:
        print("  Nothing to fetch — all dates already in database.")
        conn.close()
        return

    # Check credits first
    credits = check_credits(api_key)
    print(f"  Credits remaining: {credits['remaining']} (used: {credits['used']})")

    remaining = int(credits["remaining"]) if credits["remaining"] != "?" else 0
    needed = len(dates_to_fetch) * 30
    if remaining < needed:
        print(f"  WARNING: Need ~{needed} credits but only {remaining} remaining.")
        print(f"  Will fetch as many dates as possible ({remaining // 30} dates).")
        dates_to_fetch = dates_to_fetch[:remaining // 30]

    total_events = 0
    total_with_f5 = 0

    with httpx.Client() as client:
        for i, date in enumerate(dates_to_fetch):
            print(f"  [{i+1}/{len(dates_to_fetch)}] {date}...", end=" ")

            events_data = fetch_historical_odds(api_key, date, client)

            if not events_data:
                print("no data")
                time.sleep(0.5)
                continue

            odds_list = []
            for ed in events_data:
                event = ed["event"]
                odds = extract_odds(event)
                has_f5 = (odds["f5_3way_tie_odds"] is not None or
                          odds["f5_total_line"] is not None or
                          odds["f5_ml_away_odds"] is not None)
                if has_f5:
                    odds_list.append(odds)
                    total_with_f5 += 1
                total_events += 1

            store_odds(conn, date, odds_list, events_data[0]["snapshot"] if events_data else "")
            print(f"{len(events_data)} games, {len(odds_list)} with F5 lines")

            # Rate limit: 1 request per second
            time.sleep(1.0)

            # Progress checkpoint every 50 dates
            if (i + 1) % 50 == 0:
                print(f"\n  --- Checkpoint: {i+1} dates done, {total_events} events, "
                      f"{total_with_f5} with F5 data ---\n")

    # Summary
    total_odds = conn.execute("SELECT COUNT(*) as c FROM f5_odds").fetchone()["c"]
    with_tie = conn.execute(
        "SELECT COUNT(*) as c FROM f5_odds WHERE f5_3way_tie_odds IS NOT NULL"
    ).fetchone()["c"]
    with_total = conn.execute(
        "SELECT COUNT(*) as c FROM f5_odds WHERE f5_total_line IS NOT NULL"
    ).fetchone()["c"]

    print(f"\n{'='*60}")
    print(f"PULL COMPLETE")
    print(f"  Total odds records: {total_odds:,}")
    print(f"  With F5 3-way (tie) odds: {with_tie:,}")
    print(f"  With F5 total line: {with_total:,}")
    print(f"  Database: {DB_PATH}")
    print(f"{'='*60}")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pull historical F5 odds from The Odds API")
    parser.add_argument("--key", required=True, help="Odds API key")
    parser.add_argument("--start", default="2023-05-03", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="2024-10-01", help="End date (YYYY-MM-DD)")
    parser.add_argument("--check-credits", action="store_true", help="Just check credit balance")
    args = parser.parse_args()

    if args.check_credits:
        credits = check_credits(args.key)
        print(f"Credits remaining: {credits['remaining']}")
        print(f"Credits used: {credits['used']}")
    else:
        run_historical_pull(args.key, args.start, args.end)
