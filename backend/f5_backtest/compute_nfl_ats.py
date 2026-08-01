"""Compute NFL ATS/O-U records from VPS PostgreSQL nfl_historical_odds table."""
import psycopg2
import psycopg2.extras
import os
import json
from collections import defaultdict

DB_URL = os.getenv('DATABASE_URL', 'postgresql://maxev:maxev_sports@localhost:5432/maxev_sports')

conn = psycopg2.connect(DB_URL)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT season, home_team, away_team, home_score, away_score,
           spread_close, total_close, home_covered, total_went_over, week
    FROM nfl_historical_odds
    WHERE home_score IS NOT NULL AND spread_close IS NOT NULL
    ORDER BY season, week
""")
rows = cur.fetchall()
print(f"Total rows with scores + spreads: {len(rows)}")

seasons = defaultdict(lambda: defaultdict(lambda: {
    "games": 0, "ats_covers": 0, "ats_pushes": 0,
    "ou_overs": 0, "ou_unders": 0, "ou_pushes": 0,
    "as_fav": 0, "fav_covers": 0,
    "as_dog": 0, "dog_covers": 0,
    "home_covers": 0, "home_games": 0,
    "away_covers": 0, "away_games": 0,
    "avg_total": [],
}))

for r in rows:
    season = r["season"]
    home = r["home_team"]
    away = r["away_team"]
    hs = r["home_score"]
    as_ = r["away_score"]
    spread = float(r["spread_close"])
    if r["total_close"] is None:
        continue
    total = float(r["total_close"])
    actual_total = hs + as_
    margin = hs - as_

    for team, is_home in [(home, True), (away, False)]:
        s = seasons[season][team]
        s["games"] += 1
        s["avg_total"].append(total)

        team_margin = margin if is_home else -margin
        team_spread = spread if is_home else -spread

        covered = team_margin + team_spread > 0
        push_ats = team_margin + team_spread == 0

        if is_home:
            s["home_games"] += 1
            if covered:
                s["home_covers"] += 1
        else:
            s["away_games"] += 1
            if covered:
                s["away_covers"] += 1

        if covered:
            s["ats_covers"] += 1
        elif push_ats:
            s["ats_pushes"] += 1

        is_fav = team_spread < 0
        if is_fav:
            s["as_fav"] += 1
            if covered:
                s["fav_covers"] += 1
        else:
            s["as_dog"] += 1
            if covered:
                s["dog_covers"] += 1

        if actual_total > total:
            s["ou_overs"] += 1
        elif actual_total < total:
            s["ou_unders"] += 1
        else:
            s["ou_pushes"] += 1

for season in sorted(seasons.keys()):
    results = []
    for team, s in sorted(seasons[season].items()):
        n = s["games"]
        if n < 3:
            continue
        ga = n - s["ats_pushes"]
        go = n - s["ou_pushes"]

        def pct(a, b):
            return round(a / b * 100, 1) if b > 0 else 0

        results.append({
            "team": team,
            "games": n,
            "ats_record": f"{s['ats_covers']}-{ga - s['ats_covers']}-{s['ats_pushes']}",
            "ats_cover_pct": pct(s["ats_covers"], ga),
            "home_ats": f"{s['home_covers']}-{s['home_games'] - s['home_covers']}",
            "home_ats_pct": pct(s["home_covers"], s["home_games"]),
            "away_ats": f"{s['away_covers']}-{s['away_games'] - s['away_covers']}",
            "away_ats_pct": pct(s["away_covers"], s["away_games"]),
            "fav_ats": f"{s['fav_covers']}-{s['as_fav'] - s['fav_covers']}",
            "fav_cover_pct": pct(s["fav_covers"], s["as_fav"]),
            "dog_ats": f"{s['dog_covers']}-{s['as_dog'] - s['dog_covers']}",
            "dog_cover_pct": pct(s["dog_covers"], s["as_dog"]),
            "ou_record": f"{s['ou_overs']}-{s['ou_unders']}-{s['ou_pushes']}",
            "over_pct": pct(s["ou_overs"], go),
            "avg_total": round(sum(s["avg_total"]) / len(s["avg_total"]), 1) if s["avg_total"] else 0,
        })

    results.sort(key=lambda x: x["ats_cover_pct"], reverse=True)
    outpath = f"/tmp/nfl_ats_{season}.json"
    with open(outpath, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Season {season}: {len(results)} teams → {outpath}")
    for r in results[:3]:
        print(f"  {r['team']}: ATS {r['ats_record']} ({r['ats_cover_pct']}%) | O/U {r['ou_record']} ({r['over_pct']}% over)")

conn.close()
