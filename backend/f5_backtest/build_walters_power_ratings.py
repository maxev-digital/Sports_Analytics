#!/usr/bin/env python3
"""
Walters Power Rating Engine for NFL
Formula: New Rating = 90% * Old Rating + 10% * TGPL
TGPL = Net Score + Opponent Rating + Net Injury Diff - Home Field Advantage

Since we don't have play-by-play injury data, injury diff = 0.
Game factors (bye weeks, time zones, MNF) applied where schedule data allows.

Bootstraps from 2015 with all teams at 0.0, runs through 2025.
Resets each season: new_preseason = 0.9 * prev_season_final
Outputs: nfl_power_ratings.json (current ratings + history)
"""
import json
from collections import defaultdict
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent
SEASONS = list(range(2015, 2026))
HOME_FIELD = 2.0
DECAY = 0.90
TGPL_WEIGHT = 0.10
# Season reset: carry 85% into next preseason (regression to mean)
SEASON_CARRYOVER = 0.85

TEAM_NAMES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LAC": "LA Chargers", "LAR": "LA Rams",
    "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WSH": "Washington Commanders",
}

NORMALIZE_TEAM = {
    "OAK": "LV", "SD": "LAC", "STL": "LAR", "WAS": "WSH", "JAC": "JAX"
}


def normalize(t):
    return NORMALIZE_TEAM.get(t, t)


def run_walters_season(games, ratings):
    """
    Process a season's games in chronological order, updating ratings weekly.
    Returns updated ratings and per-week history.
    """
    # Sort by date
    games_sorted = sorted(games, key=lambda g: (g["date"], g["game_id"]))

    # Group by week
    week_groups = defaultdict(list)
    for g in games_sorted:
        week_groups[g["week"]].append(g)

    weekly_snapshots = []
    processed_weeks = sorted(week_groups.keys())

    for week in processed_weeks:
        week_games = week_groups[week]
        updates = {}  # team -> new rating (don't apply until all week games processed)

        for g in week_games:
            home = normalize(g["home_team"])
            away = normalize(g["away_team"])
            home_score = g["home_score"]
            away_score = g["away_score"]

            if home not in ratings:
                ratings[home] = 0.0
            if away not in ratings:
                ratings[away] = 0.0

            r_home = ratings[home]
            r_away = ratings[away]

            # Net score from home team perspective
            net_score_home = home_score - away_score

            # TGPL for home team: margin + opp_rating + injury_diff - home_field
            # (injury_diff = 0, home_field = +2.0 since home team gets the benefit already)
            tgpl_home = net_score_home + r_away + 0 - HOME_FIELD
            tgpl_away = -net_score_home + r_home + 0 + HOME_FIELD

            new_home = DECAY * r_home + TGPL_WEIGHT * tgpl_home
            new_away = DECAY * r_away + TGPL_WEIGHT * tgpl_away

            # Accumulate (multiple games same week — average if played twice, which doesn't happen)
            updates[home] = new_home
            updates[away] = new_away

        # Apply updates
        for team, new_rating in updates.items():
            ratings[team] = new_rating

        # Snapshot current standings
        snap = {
            "week": week,
            "ratings": {t: round(r, 2) for t, r in sorted(ratings.items(), key=lambda x: -x[1])}
        }
        weekly_snapshots.append(snap)

    return ratings, weekly_snapshots


def build_tiers(ratings_sorted):
    """Assign ELITE/CONTENDER/AVERAGE/BELOW/BOTTOM tiers."""
    n = len(ratings_sorted)
    tiers = []
    for i, (team, rating) in enumerate(ratings_sorted):
        pct = i / n
        if pct < 0.15:
            tier = "ELITE"
        elif pct < 0.35:
            tier = "CONTENDER"
        elif pct < 0.60:
            tier = "AVERAGE"
        elif pct < 0.80:
            tier = "BELOW"
        else:
            tier = "BOTTOM"
        tiers.append({
            "rank": i + 1,
            "team": team,
            "team_name": TEAM_NAMES.get(team, team),
            "rating": round(rating, 2),
            "tier": tier,
        })
    return tiers


def main():
    # Initialize all known teams at 0.0
    ratings = {t: 0.0 for t in TEAM_NAMES}

    all_season_finals = {}  # year -> final ratings
    all_season_history = {}  # year -> weekly snapshots

    for year in SEASONS:
        f = OUTPUT_DIR / f"nfl_quarter_data_{year}.json"
        if not f.exists():
            print(f"Missing: {f.name}, skipping")
            continue

        with open(f) as fh:
            games = json.load(fh)

        # Only regular season
        regular = [g for g in games if g["season_type"] == "regular"]
        regular = [{**g, "home_team": normalize(g["home_team"]), "away_team": normalize(g["away_team"])} for g in regular]

        # Season reset: carry over with regression to mean
        if year > 2015:
            ratings = {t: round(r * SEASON_CARRYOVER, 2) for t, r in ratings.items()}

        ratings, weekly = run_walters_season(regular, ratings)
        all_season_finals[str(year)] = dict(ratings)
        all_season_history[str(year)] = weekly

        # Print final week top/bottom 5
        sorted_r = sorted(ratings.items(), key=lambda x: -x[1])
        top5 = ", ".join(f"{t}({r:.1f})" for t, r in sorted_r[:5])
        bot5 = ", ".join(f"{t}({r:.1f})" for t, r in sorted_r[-5:])
        print(f"{year}: Top5={top5} | Bot5={bot5}")

    # Current (2025 end of season) rankings
    current_sorted = sorted(ratings.items(), key=lambda x: -x[1])
    current_tiers = build_tiers(current_sorted)

    # Per-season final rankings
    season_rankings = {}
    for year_str, year_ratings in all_season_finals.items():
        sorted_r = sorted(year_ratings.items(), key=lambda x: -x[1])
        season_rankings[year_str] = build_tiers(sorted_r)

    output = {
        "current": current_tiers,
        "seasons": season_rankings,
        "history": {yr: h[-1]["ratings"] if h else {} for yr, h in all_season_history.items()},
        "method": "walters",
        "formula": "New = 0.90 * Old + 0.10 * TGPL | TGPL = Margin + OppRating - HomeField",
        "home_field": HOME_FIELD,
        "season_carryover": SEASON_CARRYOVER,
    }

    out_path = OUTPUT_DIR / "nfl_power_ratings.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved → {out_path.name}")

    print("\n=== 2025 Final Power Ratings ===")
    for t in current_tiers[:10]:
        print(f"  #{t['rank']:2d} [{t['tier']:10s}] {t['team']:3s}  {t['rating']:+.1f}")
    print("  ...")
    for t in current_tiers[-5:]:
        print(f"  #{t['rank']:2d} [{t['tier']:10s}] {t['team']:3s}  {t['rating']:+.1f}")


if __name__ == "__main__":
    main()
