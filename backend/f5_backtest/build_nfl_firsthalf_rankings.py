#!/usr/bin/env python3
"""
Build NFL first-half betting rankings from quarter data.
For each team per season: H1 scoring avg, H1 allowed avg, H1 O/U tendency,
Q1 lead win rate, comeback rate, H1 ATS proxy.
"""
import json
from collections import defaultdict
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent
SEASONS = list(range(2015, 2026))

# NFL teams canonical list (some franchises moved/renamed)
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
    # Legacy abbreviations
    "OAK": "Las Vegas Raiders", "SD": "LA Chargers", "STL": "LA Rams",
    "WAS": "Washington Commanders", "JAC": "Jacksonville Jaguars",
}


def normalize_team(abbr):
    """Normalize legacy abbreviations to current."""
    mapping = {"OAK": "LV", "SD": "LAC", "STL": "LAR", "WAS": "WSH", "JAC": "JAX"}
    return mapping.get(abbr, abbr)


def build_season_stats(games):
    team_stats = defaultdict(lambda: {
        "games": 0,
        "h1_scored": [], "h1_allowed": [],
        "h1_total": [],
        "q1_scored": [], "q1_allowed": [],
        "h1_wins": 0, "h1_losses": 0, "h1_ties": 0,
        "q1_lead_then_win": 0, "q1_lead_games": 0,
        "q1_trail_then_win": 0, "q1_trail_games": 0,
        "blowout_h1": 0,  # led by 14+ at half
    })

    for g in games:
        home = normalize_team(g["home_team"])
        away = normalize_team(g["away_team"])
        h_h1 = g["home_h1"]
        a_h1 = g["away_h1"]
        h_q1 = g["home_q1"]
        a_q1 = g["away_q1"]
        h_final = g["home_score"]
        a_final = g["away_score"]

        # H1 winner
        h1_winner = "home" if h_h1 > a_h1 else ("away" if a_h1 > h_h1 else "tie")

        for team, opp_team, scored_h1, allowed_h1, scored_q1, allowed_q1, final_for, final_against in [
            (home, away, h_h1, a_h1, h_q1, a_q1, h_final, a_final),
            (away, home, a_h1, h_h1, a_q1, h_q1, a_final, h_final),
        ]:
            s = team_stats[team]
            s["games"] += 1
            s["h1_scored"].append(scored_h1)
            s["h1_allowed"].append(allowed_h1)
            s["h1_total"].append(scored_h1 + allowed_h1)
            s["q1_scored"].append(scored_q1)
            s["q1_allowed"].append(allowed_q1)

            if scored_h1 > allowed_h1:
                s["h1_wins"] += 1
            elif scored_h1 < allowed_h1:
                s["h1_losses"] += 1
            else:
                s["h1_ties"] += 1

            # Q1 lead → final outcome
            if scored_q1 > allowed_q1:
                s["q1_lead_games"] += 1
                if final_for > final_against:
                    s["q1_lead_then_win"] += 1
            elif scored_q1 < allowed_q1:
                s["q1_trail_games"] += 1
                if final_for > final_against:
                    s["q1_trail_then_win"] += 1

            if scored_h1 - allowed_h1 >= 14:
                s["blowout_h1"] += 1

    # Compute derived stats
    results = []
    for team, s in team_stats.items():
        if s["games"] < 5:
            continue
        n = s["games"]
        avg_h1_scored = sum(s["h1_scored"]) / n
        avg_h1_allowed = sum(s["h1_allowed"]) / n
        avg_h1_total = sum(s["h1_total"]) / n
        avg_q1_scored = sum(s["q1_scored"]) / n
        avg_q1_allowed = sum(s["q1_allowed"]) / n
        h1_win_pct = s["h1_wins"] / n
        q1_lead_win_pct = (s["q1_lead_then_win"] / s["q1_lead_games"]) if s["q1_lead_games"] > 0 else None
        q1_trail_comeback_pct = (s["q1_trail_then_win"] / s["q1_trail_games"]) if s["q1_trail_games"] > 0 else None
        h1_over_count = sum(1 for t in s["h1_total"] if t > avg_h1_total)  # relative
        blowout_rate = s["blowout_h1"] / n

        results.append({
            "team": team,
            "team_name": TEAM_NAMES.get(team, team),
            "games": n,
            "avg_h1_scored": round(avg_h1_scored, 1),
            "avg_h1_allowed": round(avg_h1_allowed, 1),
            "avg_h1_margin": round(avg_h1_scored - avg_h1_allowed, 1),
            "avg_h1_total": round(avg_h1_total, 1),
            "avg_q1_scored": round(avg_q1_scored, 1),
            "avg_q1_allowed": round(avg_q1_allowed, 1),
            "h1_wins": s["h1_wins"],
            "h1_losses": s["h1_losses"],
            "h1_ties": s["h1_ties"],
            "h1_win_pct": round(h1_win_pct, 3),
            "q1_lead_games": s["q1_lead_games"],
            "q1_lead_win_pct": round(q1_lead_win_pct, 3) if q1_lead_win_pct is not None else None,
            "q1_trail_games": s["q1_trail_games"],
            "q1_trail_comeback_pct": round(q1_trail_comeback_pct, 3) if q1_trail_comeback_pct is not None else None,
            "blowout_rate": round(blowout_rate, 3),
        })

    return sorted(results, key=lambda x: x["avg_h1_margin"], reverse=True)


def main():
    all_seasons = {}

    for year in SEASONS:
        f = OUTPUT_DIR / f"nfl_quarter_data_{year}.json"
        if not f.exists():
            print(f"Missing: {f.name}")
            continue
        with open(f) as fh:
            games = json.load(fh)
        regular = [g for g in games if g["season_type"] == "regular"]
        stats = build_season_stats(regular)
        all_seasons[str(year)] = stats
        print(f"{year}: {len(regular)} regular season games, {len(stats)} teams")

    # All-time (2015-2025 combined)
    all_games = []
    for year in SEASONS:
        f = OUTPUT_DIR / f"nfl_quarter_data_{year}.json"
        if f.exists():
            with open(f) as fh:
                games = json.load(fh)
            all_games.extend(g for g in games if g["season_type"] == "regular")

    all_seasons["all"] = build_season_stats(all_games)
    print(f"\nAll-time: {len(all_games)} games, {len(all_seasons['all'])} teams")

    # Top 5 H1 margin teams all-time
    print("\nTop 5 H1 Margin (all-time):")
    for t in all_seasons["all"][:5]:
        print(f"  {t['team']}: +{t['avg_h1_margin']} H1 margin, {t['h1_win_pct']:.1%} H1 win%")

    print("\nBottom 5 H1 Margin (all-time):")
    for t in all_seasons["all"][-5:]:
        print(f"  {t['team']}: {t['avg_h1_margin']} H1 margin, {t['h1_win_pct']:.1%} H1 win%")

    out = OUTPUT_DIR / "nfl_firsthalf_rankings.json"
    with open(out, "w") as f:
        json.dump(all_seasons, f, indent=2)
    print(f"\nSaved → {out.name}")


if __name__ == "__main__":
    main()
