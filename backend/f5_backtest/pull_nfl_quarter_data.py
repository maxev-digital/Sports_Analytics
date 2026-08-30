#!/usr/bin/env python3
"""
Pull NFL quarter-by-quarter scoring data from ESPN API (free, no key required).
Covers 2015-2025 regular season + playoffs.
Outputs: nfl_quarter_data_{year}.json per season
"""
import json
import time
import urllib.request
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent

SEASONS = list(range(2015, 2026))  # 2015-2025
WEEKS_REGULAR = range(1, 19)       # 18 weeks (2021+), 17 before
SEASON_TYPE_REGULAR = 2
SEASON_TYPE_PLAYOFF = 3
PLAYOFF_WEEKS = range(1, 5)        # Wild Card, Divisional, Conference, Super Bowl

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"


def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt == retries - 1:
                print(f"  FAILED after {retries} attempts: {e}")
                return None
            time.sleep(2 ** attempt)
    return None


def parse_game(event, season_year, season_type, week):
    comp = event["competitions"][0]
    status = comp["status"]

    # Only include completed games
    if status["type"]["state"] != "post":
        return None

    home = next((c for c in comp["competitors"] if c["homeAway"] == "home"), None)
    away = next((c for c in comp["competitors"] if c["homeAway"] == "away"), None)
    if not home or not away:
        return None

    def get_quarters(competitor):
        ls = competitor.get("linescores", [])
        quarters = {f"q{s['period']}": int(s["value"]) for s in ls if s["period"] <= 4}
        ot = sum(int(s["value"]) for s in ls if s["period"] > 4)
        return quarters, ot

    home_q, home_ot = get_quarters(home)
    away_q, away_ot = get_quarters(away)

    home_score = int(home.get("score", 0))
    away_score = int(away.get("score", 0))

    home_h1 = home_q.get("q1", 0) + home_q.get("q2", 0)
    away_h1 = away_q.get("q1", 0) + away_q.get("q2", 0)

    return {
        "game_id": event["id"],
        "date": event["date"][:10],
        "season": season_year,
        "season_type": "regular" if season_type == SEASON_TYPE_REGULAR else "playoff",
        "week": week,
        "home_team": home["team"]["abbreviation"],
        "away_team": away["team"]["abbreviation"],
        "home_score": home_score,
        "away_score": away_score,
        "home_q1": home_q.get("q1", 0),
        "home_q2": home_q.get("q2", 0),
        "home_q3": home_q.get("q3", 0),
        "home_q4": home_q.get("q4", 0),
        "home_ot": home_ot,
        "away_q1": away_q.get("q1", 0),
        "away_q2": away_q.get("q2", 0),
        "away_q3": away_q.get("q3", 0),
        "away_q4": away_q.get("q4", 0),
        "away_ot": away_ot,
        "home_h1": home_h1,
        "away_h1": away_h1,
        "total_h1": home_h1 + away_h1,
        "total_score": home_score + away_score,
        "home_winner": home.get("winner", False),
    }


def pull_season(year):
    games = []
    # Regular season: 2021+ is 18 weeks, before is 17
    max_week = 18 if year >= 2021 else 17

    print(f"\n=== Season {year} ===")

    # Regular season
    for week in range(1, max_week + 1):
        url = f"{BASE_URL}?seasontype={SEASON_TYPE_REGULAR}&week={week}&dates={year}"
        data = fetch(url)
        if not data:
            continue
        events = data.get("events", [])
        week_games = 0
        for event in events:
            game = parse_game(event, year, SEASON_TYPE_REGULAR, week)
            if game:
                games.append(game)
                week_games += 1
        print(f"  Week {week:2d}: {week_games} games")
        time.sleep(0.3)

    # Playoffs
    for week in PLAYOFF_WEEKS:
        url = f"{BASE_URL}?seasontype={SEASON_TYPE_PLAYOFF}&week={week}&dates={year}"
        data = fetch(url)
        if not data:
            continue
        events = data.get("events", [])
        for event in events:
            game = parse_game(event, year, SEASON_TYPE_PLAYOFF, week)
            if game:
                games.append(game)
        time.sleep(0.3)

    print(f"  Total: {len(games)} completed games")
    return games


def compute_summary(games):
    """Add first-half ATS-style summary stats for each team."""
    from collections import defaultdict
    team_stats = defaultdict(lambda: {
        "h1_over_count": 0, "h1_under_count": 0, "h1_push_count": 0,
        "avg_h1_scored": 0, "avg_h1_allowed": 0,
        "q1_lead_win_rate": 0, "q1_lead_games": 0, "q1_lead_wins": 0,
        "games": 0
    })
    return games  # Summary computed separately in analysis script


def main():
    all_data = {}

    for year in SEASONS:
        games = pull_season(year)
        all_data[str(year)] = games

        out_file = OUTPUT_DIR / f"nfl_quarter_data_{year}.json"
        with open(out_file, "w") as f:
            json.dump(games, f, indent=2)
        print(f"  Saved {len(games)} games → {out_file.name}")

    # Also write a combined file
    combined = [g for season_games in all_data.values() for g in season_games]
    combined_file = OUTPUT_DIR / "nfl_quarter_data_all.json"
    with open(combined_file, "w") as f:
        json.dump(combined, f, indent=2)
    print(f"\nCombined: {len(combined)} total games → {combined_file.name}")

    # Quick summary stats
    print("\n=== Summary ===")
    for year, games in all_data.items():
        if not games:
            continue
        avg_h1 = sum(g["total_h1"] for g in games) / len(games)
        avg_total = sum(g["total_score"] for g in games) / len(games)
        home_wins = sum(1 for g in games if g["home_winner"])
        print(f"{year}: {len(games)} games | Avg H1: {avg_h1:.1f} | Avg Total: {avg_total:.1f} | Home Win%: {home_wins/len(games):.1%}")


if __name__ == "__main__":
    main()
