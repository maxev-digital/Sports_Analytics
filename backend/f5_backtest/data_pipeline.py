"""
F5 Backtest Data Pipeline — Pull Real MLB Data

Pulls from the MLB Stats API (free, no key required):
  - Every regular season game (2015-2024)
  - Inning-by-inning linescore (score after 5)
  - Starting pitchers + season ERA
  - Venue (for park factor)
  - Game date (for month, weather proxy)

Computes the ACTUAL tie-after-5 rate for every game, then
buckets by our signal factors to validate or invalidate
our modeled estimates.

Usage:
  python3 data_pipeline.py --seasons 2024         # one season (~2,430 games)
  python3 data_pipeline.py --seasons 2023,2024     # two seasons
  python3 data_pipeline.py --seasons 2020-2024     # range (2020 was 60-game COVID season)
  python3 data_pipeline.py --full                  # all 10 seasons (2015-2024)
"""

import httpx
import json
import sqlite3
import time
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

MLB_API = "https://statsapi.mlb.com/api/v1"

# Park classifications
PARK_FACTOR = {
    # Pitcher parks
    "Oracle Park": "pitcher_park",
    "Dodger Stadium": "pitcher_park",
    "Petco Park": "pitcher_park",
    "Tropicana Field": "pitcher_park",
    "T-Mobile Park": "pitcher_park",
    "Kauffman Stadium": "pitcher_park",
    "Oakland Coliseum": "pitcher_park",
    "RingCentral Coliseum": "pitcher_park",
    "loanDepot park": "pitcher_park",
    "Marlins Park": "pitcher_park",
    "Citi Field": "pitcher_park",
    "PNC Park": "pitcher_park",
    "Target Field": "pitcher_park",
    "Comerica Park": "pitcher_park",
    # Hitter parks
    "Coors Field": "coors_field",
    "Great American Ball Park": "hitter_park",
    "Globe Life Field": "hitter_park",
    "Globe Life Park in Arlington": "hitter_park",
    "Fenway Park": "hitter_park",
    "Yankee Stadium": "hitter_park",
    "Citizens Bank Park": "hitter_park",
    "Wrigley Field": "hitter_park",
    "Guaranteed Rate Field": "hitter_park",
    "Chase Field": "hitter_park",
    "Miller Park": "hitter_park",
    "American Family Field": "hitter_park",
    "Minute Maid Park": "hitter_park",
    # Everything else = neutral
}

DB_PATH = Path(__file__).parent / "f5_backtest.db"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS games (
            game_pk INTEGER PRIMARY KEY,
            season INTEGER NOT NULL,
            game_date TEXT NOT NULL,
            month INTEGER NOT NULL,
            away_team TEXT NOT NULL,
            home_team TEXT NOT NULL,
            venue TEXT NOT NULL,
            park_type TEXT NOT NULL,

            away_pitcher_id INTEGER,
            away_pitcher_name TEXT,
            away_pitcher_era REAL,
            home_pitcher_id INTEGER,
            home_pitcher_name TEXT,
            home_pitcher_era REAL,
            era_differential REAL,
            era_bucket TEXT,

            total_innings INTEGER,
            away_runs_5 INTEGER NOT NULL,
            home_runs_5 INTEGER NOT NULL,
            tied_after_5 INTEGER NOT NULL,  -- 1 = tied, 0 = not tied
            away_runs_final INTEGER,
            home_runs_final INTEGER,

            total_runs_final INTEGER,
            total_bucket TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_games_season ON games(season);
        CREATE INDEX IF NOT EXISTS idx_games_tied ON games(tied_after_5);
        CREATE INDEX IF NOT EXISTS idx_games_park ON games(park_type);
        CREATE INDEX IF NOT EXISTS idx_games_era_bucket ON games(era_bucket);
        CREATE INDEX IF NOT EXISTS idx_games_total_bucket ON games(total_bucket);
        CREATE INDEX IF NOT EXISTS idx_games_month ON games(month);
    """)
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")


def classify_park(venue_name: str) -> str:
    return PARK_FACTOR.get(venue_name, "neutral")


def classify_era_bucket(era_diff: float, away_era: float, home_era: float) -> str:
    if away_era is None or home_era is None:
        return "unknown"
    if away_era < 3.50 and home_era < 3.50:
        return "both_under_3"
    if era_diff < 0.5:
        return "diff_under_0.5"
    if era_diff < 1.0:
        return "diff_0.5_to_1.0"
    if era_diff < 1.5:
        return "diff_1.0_to_1.5"
    return "diff_over_1.5"


def classify_total_bucket(total_runs: int) -> str:
    if total_runs is None:
        return "unknown"
    if total_runs < 7:
        return "under_7"
    if total_runs <= 8:
        return "7_to_8"
    if total_runs <= 9:
        return "8_to_9"
    if total_runs <= 10:
        return "over_9"
    return "over_10"


def fetch_pitcher_era(pitcher_id: int, season: int, client: httpx.Client) -> float:
    """Get pitcher's season ERA up to this point"""
    try:
        url = f"{MLB_API}/people/{pitcher_id}/stats?stats=season&season={season}&group=pitching"
        resp = client.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            splits = data.get("stats", [{}])[0].get("splits", [])
            if splits:
                era_str = splits[0]["stat"].get("era", "0.00")
                return float(era_str)
    except Exception as e:
        pass
    return None


def fetch_season_games(season: int, client: httpx.Client) -> list:
    """Fetch all regular season games for a year"""
    # MLB regular season: April-September (approximately)
    start = f"{season}-03-20"
    end = f"{season}-10-05"

    # COVID 2020 was July-September
    if season == 2020:
        start = f"{season}-07-20"
        end = f"{season}-10-01"

    games = []
    # Fetch in month chunks to avoid massive responses
    current = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")

    while current < end_dt:
        chunk_end = min(current + timedelta(days=30), end_dt)
        url = (f"{MLB_API}/schedule?sportId=1"
               f"&startDate={current.strftime('%Y-%m-%d')}"
               f"&endDate={chunk_end.strftime('%Y-%m-%d')}"
               f"&gameType=R"  # Regular season only
               f"&hydrate=linescore,probablePitcher")

        try:
            resp = client.get(url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                for date_entry in data.get("dates", []):
                    for game in date_entry.get("games", []):
                        status = game.get("status", {}).get("detailedState", "")
                        if status in ("Final", "Completed Early"):
                            games.append(game)
        except Exception as e:
            print(f"  Error fetching {current.strftime('%Y-%m-%d')}: {e}")

        current = chunk_end + timedelta(days=1)
        time.sleep(0.3)  # Be nice to the API

    return games


def process_game(game: dict, season: int, pitcher_cache: dict, client: httpx.Client) -> dict:
    """Extract all fields from a single game"""
    ls = game.get("linescore", {})
    innings = ls.get("innings", [])

    if len(innings) < 5:
        return None  # Game didn't go 5 innings (rain/suspended)

    # Score after 5 innings
    away_r5 = sum(i.get("away", {}).get("runs", 0) for i in innings[:5])
    home_r5 = sum(i.get("home", {}).get("runs", 0) for i in innings[:5])
    tied = 1 if away_r5 == home_r5 else 0

    # Final score
    away_final = ls.get("teams", {}).get("away", {}).get("runs", 0)
    home_final = ls.get("teams", {}).get("home", {}).get("runs", 0)
    total_final = (away_final or 0) + (home_final or 0)

    # Teams
    away_team = game["teams"]["away"]["team"]["name"]
    home_team = game["teams"]["home"]["team"]["name"]

    # Venue
    venue = game.get("venue", {}).get("name", "Unknown")
    park_type = classify_park(venue)

    # Date
    game_date = game.get("gameDate", game.get("officialDate", ""))[:10]
    month = int(game_date[5:7]) if len(game_date) >= 7 else 0

    # Pitchers
    away_pitcher = game["teams"]["away"].get("probablePitcher", {})
    home_pitcher = game["teams"]["home"].get("probablePitcher", {})

    ap_id = away_pitcher.get("id")
    hp_id = home_pitcher.get("id")
    ap_name = away_pitcher.get("fullName", "Unknown")
    hp_name = home_pitcher.get("fullName", "Unknown")

    # Get ERA (cached per pitcher per season)
    ap_era = None
    hp_era = None
    era_diff = None
    era_bucket = "unknown"

    if ap_id:
        cache_key = f"{ap_id}_{season}"
        if cache_key not in pitcher_cache:
            pitcher_cache[cache_key] = fetch_pitcher_era(ap_id, season, client)
        ap_era = pitcher_cache[cache_key]

    if hp_id:
        cache_key = f"{hp_id}_{season}"
        if cache_key not in pitcher_cache:
            pitcher_cache[cache_key] = fetch_pitcher_era(hp_id, season, client)
        hp_era = pitcher_cache[cache_key]

    if ap_era is not None and hp_era is not None:
        era_diff = abs(ap_era - hp_era)
        era_bucket = classify_era_bucket(era_diff, ap_era, hp_era)

    return {
        "game_pk": game["gamePk"],
        "season": season,
        "game_date": game_date,
        "month": month,
        "away_team": away_team,
        "home_team": home_team,
        "venue": venue,
        "park_type": park_type,
        "away_pitcher_id": ap_id,
        "away_pitcher_name": ap_name,
        "away_pitcher_era": ap_era,
        "home_pitcher_id": hp_id,
        "home_pitcher_name": hp_name,
        "home_pitcher_era": hp_era,
        "era_differential": era_diff,
        "era_bucket": era_bucket,
        "total_innings": len(innings),
        "away_runs_5": away_r5,
        "home_runs_5": home_r5,
        "tied_after_5": tied,
        "away_runs_final": away_final,
        "home_runs_final": home_final,
        "total_runs_final": total_final,
        "total_bucket": classify_total_bucket(total_final),
    }


def insert_games(games: list, conn: sqlite3.Connection):
    """Batch insert processed games"""
    for g in games:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO games (
                    game_pk, season, game_date, month, away_team, home_team,
                    venue, park_type, away_pitcher_id, away_pitcher_name,
                    away_pitcher_era, home_pitcher_id, home_pitcher_name,
                    home_pitcher_era, era_differential, era_bucket,
                    total_innings, away_runs_5, home_runs_5, tied_after_5,
                    away_runs_final, home_runs_final, total_runs_final, total_bucket
                ) VALUES (
                    :game_pk, :season, :game_date, :month, :away_team, :home_team,
                    :venue, :park_type, :away_pitcher_id, :away_pitcher_name,
                    :away_pitcher_era, :home_pitcher_id, :home_pitcher_name,
                    :home_pitcher_era, :era_differential, :era_bucket,
                    :total_innings, :away_runs_5, :home_runs_5, :tied_after_5,
                    :away_runs_final, :home_runs_final, :total_runs_final, :total_bucket
                )
            """, g)
        except Exception as e:
            print(f"  Insert error for game {g['game_pk']}: {e}")
    conn.commit()


def run_pipeline(seasons: list):
    """Main pipeline: fetch, process, store"""
    init_db()
    conn = get_db()

    total_games = 0
    total_ties = 0

    with httpx.Client() as client:
        pitcher_cache = {}

        for season in seasons:
            # Check if season already loaded
            existing = conn.execute(
                "SELECT COUNT(*) as c FROM games WHERE season = ?", (season,)
            ).fetchone()["c"]

            if existing > 100:
                print(f"\n[{season}] Already have {existing} games — skipping (use --force to re-fetch)")
                row = conn.execute(
                    "SELECT COUNT(*) as total, SUM(tied_after_5) as ties FROM games WHERE season = ?",
                    (season,)
                ).fetchone()
                total_games += row["total"]
                total_ties += row["ties"]
                continue

            print(f"\n[{season}] Fetching games from MLB Stats API...")
            raw_games = fetch_season_games(season, client)
            print(f"  Found {len(raw_games)} completed regular season games")

            processed = []
            for i, game in enumerate(raw_games):
                result = process_game(game, season, pitcher_cache, client)
                if result:
                    processed.append(result)

                # Progress update every 100 games
                if (i + 1) % 100 == 0:
                    ties_so_far = sum(1 for p in processed if p["tied_after_5"])
                    print(f"  Processed {i+1}/{len(raw_games)} — "
                          f"{ties_so_far} ties so far ({ties_so_far/len(processed)*100:.1f}%)")

                # Rate limit on pitcher ERA fetches
                if (i + 1) % 50 == 0:
                    time.sleep(0.5)

            insert_games(processed, conn)

            ties = sum(1 for p in processed if p["tied_after_5"])
            tie_rate = ties / len(processed) * 100 if processed else 0
            total_games += len(processed)
            total_ties += ties

            print(f"  [{season}] COMPLETE: {len(processed)} games, "
                  f"{ties} ties ({tie_rate:.1f}%)")
            print(f"  Pitcher ERA cache: {len(pitcher_cache)} pitchers")

    # Final summary
    overall_rate = total_ties / total_games * 100 if total_games > 0 else 0
    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE")
    print(f"  Seasons: {seasons}")
    print(f"  Total games: {total_games:,}")
    print(f"  Total ties after 5: {total_ties:,}")
    print(f"  Overall tie rate: {overall_rate:.2f}%")
    print(f"  Database: {DB_PATH}")
    print(f"{'='*60}")

    conn.close()


def parse_seasons(arg: str) -> list:
    """Parse season argument: '2024', '2023,2024', '2020-2024'"""
    if "-" in arg and "," not in arg:
        start, end = arg.split("-")
        return list(range(int(start), int(end) + 1))
    return [int(s.strip()) for s in arg.split(",")]


if __name__ == "__main__":
    if "--full" in sys.argv:
        seasons = list(range(2015, 2025))
    elif "--seasons" in sys.argv:
        idx = sys.argv.index("--seasons") + 1
        seasons = parse_seasons(sys.argv[idx])
    else:
        # Default: just 2024 for quick testing
        seasons = [2024]
        print("Usage: python3 data_pipeline.py --seasons 2024")
        print("       python3 data_pipeline.py --seasons 2020-2024")
        print("       python3 data_pipeline.py --full")
        print(f"\nDefaulting to {seasons}")

    run_pipeline(seasons)
