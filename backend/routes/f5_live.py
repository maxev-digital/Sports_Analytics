"""
F5 Edge Engine — Live API Endpoints

Serves real-time data to the frontend dashboard:
  GET /api/f5/today      — Today's games scored against all signals
  GET /api/f5/signals    — Signal performance stats
  GET /api/f5/matrix     — Edge matrix data
  GET /api/f5/venues     — Venue edge data
  GET /api/f5/pl          — P&L tracker data
  GET /api/f5/scan       — Trigger a fresh scan (uses Odds API credits)
"""

from fastapi import APIRouter, Query
from datetime import date, datetime
import httpx
import os
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/f5", tags=["f5-live"])

ODDS_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_API = "https://api.the-odds-api.com/v4"
MLB_API = "https://statsapi.mlb.com/api/v1"
BACKTEST_DIR = Path(__file__).parent.parent / "f5_backtest"

HIGH_TIE_UMPS = {
    "Bill Miller", "Lance Barrett", "Larry Vanover", "CB Bucknor",
    "Gabe Morales", "Will Little", "Shane Livensparger", "Alfonso Márquez",
    "Dan Merzel", "Quinn Wolcott", "Mark Wegner", "Nestor Ceja",
    "Mike Muchlinski", "D.J. Reyburn", "Vic Carapazza", "Phil Cuzzi",
    "Ryan Additon", "Tripp Gibson", "Adrian Johnson",
}

LOW_TIE_UMPS = {
    "Edwin Jimenez", "Mark Carlson", "Hunter Wendelstedt", "Erich Bacchus",
    "Roberto Ortiz", "Paul Clemons", "Chad Whitson", "Jim Wolf",
}

HIGH_TIE_VENUES = {
    "Chase Field", "Globe Life Field", "Yankee Stadium",
    "Citi Field", "Busch Stadium", "American Family Field",
}

UNDER_VENUES = {
    "Globe Life Field", "Kauffman Stadium", "Comerica Park",
    "Wrigley Field", "Citi Field",
}


def _american_to_decimal(a: int) -> float:
    if a > 0:
        return 1 + a / 100
    return 1 + 100 / abs(a)


async def _fetch_mlb_games(scan_date: str) -> list:
    """Pull games + pitchers + umpires from MLB Stats API (free)."""
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{MLB_API}/schedule", params={
            "sportId": 1, "startDate": scan_date, "endDate": scan_date,
            "gameType": "R", "hydrate": "probablePitcher,officials,venue,weather",
        })

        games = []
        for d in r.json().get("dates", []):
            for g in d.get("games", []):
                away = g["teams"]["away"]["team"]["name"]
                home = g["teams"]["home"]["team"]["name"]
                venue = g.get("venue", {}).get("name", "Unknown")

                ap = g["teams"]["away"].get("probablePitcher", {})
                hp = g["teams"]["home"].get("probablePitcher", {})

                officials = g.get("officials", [])
                hp_ump = next(
                    (o["official"]["fullName"] for o in officials
                     if o.get("officialType") == "Home Plate"),
                    None,
                )

                weather = g.get("weather", {})
                status = g.get("status", {}).get("abstractGameState", "")

                away_era = await _fetch_era(client, ap.get("id"), scan_date[:4])
                home_era = await _fetch_era(client, hp.get("id"), scan_date[:4])

                era_diff = abs(away_era - home_era) if away_era and home_era else None

                games.append({
                    "away_team": away,
                    "home_team": home,
                    "venue": venue,
                    "away_pitcher": ap.get("fullName", "TBD"),
                    "home_pitcher": hp.get("fullName", "TBD"),
                    "away_era": away_era,
                    "home_era": home_era,
                    "era_diff": round(era_diff, 2) if era_diff else None,
                    "hp_umpire": hp_ump,
                    "ump_tag": (
                        "HIGH_TIE" if hp_ump in HIGH_TIE_UMPS
                        else "LOW_TIE" if hp_ump in LOW_TIE_UMPS
                        else None
                    ),
                    "venue_tag": (
                        "UNDER" if venue in UNDER_VENUES
                        else "HIGH_TIE" if venue in HIGH_TIE_VENUES
                        else None
                    ),
                    "temp": weather.get("temp"),
                    "wind": weather.get("wind"),
                    "condition": weather.get("condition"),
                    "commence": g.get("gameDate", ""),
                    "game_pk": g["gamePk"],
                    "status": status,
                })
        return games


async def _fetch_era(client: httpx.AsyncClient, pid: int | None, season: str) -> float | None:
    if not pid:
        return None
    try:
        r = await client.get(
            f"{MLB_API}/people/{pid}/stats",
            params={"stats": "season", "season": season, "group": "pitching"},
        )
        splits = r.json().get("stats", [{}])[0].get("splits", [])
        if splits:
            return float(splits[0]["stat"].get("era", 99))
    except Exception:
        pass
    return None


async def _fetch_fg_odds() -> tuple[dict, str]:
    """Pull full-game odds from Odds API (30 credits)."""
    if not ODDS_KEY:
        return {}, "no_key"

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{ODDS_API}/sports/baseball_mlb/odds", params={
            "apiKey": ODDS_KEY, "regions": "us",
            "markets": "h2h,totals", "oddsFormat": "american",
        })

        remaining = r.headers.get("x-requests-remaining", "?")
        events = r.json() if r.status_code == 200 else []
        odds_map: dict = {}

        for e in events:
            key = f"{e['away_team']}|{e['home_team']}"
            fg_total = fg_under = fg_ml_away = fg_ml_home = None

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

            odds_map[key] = {
                "fg_total": fg_total,
                "fg_under_odds": fg_under,
                "fg_ml_away": fg_ml_away,
                "fg_ml_home": fg_ml_home,
                "event_id": e["id"],
            }

        return odds_map, remaining


def _score_game(game: dict, odds: dict) -> list[dict]:
    """Score one game against all signal filters. Returns list of plays."""
    plays = []
    ae = game["away_era"]
    he = game["home_era"]
    ed = game["era_diff"]
    venue = game["venue"]
    ump = game["hp_umpire"]
    fg_total = odds.get("fg_total")

    # ── F1 Tie + FG Under SGP ──
    if fg_total and ae and he:
        tier = None
        if fg_total <= 8.0 and ae < 4.0 and he < 4.0 and ump in HIGH_TIE_UMPS:
            tier = 1
        elif fg_total <= 8.0 and ae < 4.5 and he < 4.5:
            tier = 2
        elif fg_total <= 8.5 and ae < 4.5 and he < 4.5:
            tier = 3
        if tier:
            plays.append({
                "type": "F1 Tie + FG Under SGP",
                "book": "Bovada",
                "tier": tier,
                "unit": {1: 50, 2: 25, 3: 15}[tier],
                "signal": f"FG {fg_total} / ERA {ae:.2f} vs {he:.2f}"
                          + (f" / Ump: {ump}" if tier == 1 else ""),
                "expected_hit": {1: "43%", 2: "37%", 3: "38%"}[tier],
                "historical_roi": {1: "+76%", 2: "+50%", 3: "+52%"}[tier],
                "needs_f5_odds": False,
            })

    # ── F5 Under ──
    if ae and he and ae < 4.5 and he < 4.5:
        plays.append({
            "type": "F5 Under",
            "book": "Best line (check all books)",
            "tier": 1 if ae < 3.5 and he < 3.5 else 2,
            "unit": 100,
            "signal": f"Both ERA < {'3.50' if ae < 3.5 and he < 3.5 else '4.50'}",
            "expected_hit": "59%" if ae < 3.5 and he < 3.5 else "55%",
            "historical_roi": "+10.7%" if ae < 3.5 and he < 3.5 else "+3.2%",
            "needs_f5_odds": True,
        })

    # ── F5 Fav ML ──
    if ed and ed >= 1.0:
        fav = "home" if he and ae and he < ae else "away"
        hitter_park = venue in UNDER_VENUES or venue in {
            "Great American Ball Park", "Fenway Park", "Yankee Stadium",
        }
        plays.append({
            "type": "F5 Favorite ML",
            "book": "Best price across all books",
            "tier": 1 if ed >= 1.5 and hitter_park else 2 if ed >= 1.5 else 3,
            "unit": 100,
            "signal": f"ERA diff {ed:.2f} / Fav: {game[fav + '_pitcher']}"
                      + (" + hitter park" if hitter_park else ""),
            "expected_hit": (
                "66%" if ed >= 1.5 and hitter_park
                else "63%" if ed >= 1.5 else "60%"
            ),
            "historical_roi": (
                "+17.0%" if ed >= 1.5 and hitter_park
                else "+11.7%" if ed >= 1.5 else "+6.4%"
            ),
            "needs_f5_odds": True,
            "fav_side": fav,
        })

    # ── F5 Tie ──
    if ae and he:
        ace_ace = ae < 3.5 and he < 3.5
        venue_play = venue in HIGH_TIE_VENUES and ae < 4.0 and he < 4.0
        if ace_ace or venue_play:
            plays.append({
                "type": "F5 Tie",
                "book": "BetMGM (soft — best odds 80% of time)",
                "tier": 1 if ace_ace and venue in HIGH_TIE_VENUES else 2,
                "unit": 100,
                "signal": ("Ace vs Ace" if ace_ace else "High-tie venue")
                          + (f" + {ump}" if ump in HIGH_TIE_UMPS else ""),
                "expected_hit": "22-44%" if ace_ace and venue in HIGH_TIE_VENUES else "22%",
                "historical_roi": "+22% to +153%",
                "needs_f5_odds": True,
            })
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

    # ── Venue Under Edge ──
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


# ─── Endpoints ────────────────────────────────────────────────────────

@router.get("/today")
async def get_today(
    scan_date: Optional[str] = Query(default=None),
    use_odds: bool = Query(default=True),
):
    """Today's games scored against all signals. Uses ~30 Odds API credits."""
    target = scan_date or date.today().isoformat()

    games = await _fetch_mlb_games(target)

    fg_odds: dict = {}
    credits = "skipped"
    if use_odds and ODDS_KEY:
        fg_odds, credits = await _fetch_fg_odds()

    results = []
    total_plays = 0
    total_risk = 0

    for g in games:
        key = f"{g['away_team']}|{g['home_team']}"
        odds = fg_odds.get(key, {})
        plays = _score_game(g, odds)
        total_plays += len(plays)
        total_risk += sum(p["unit"] for p in plays)

        results.append({
            "game": g,
            "plays": plays,
            "odds": odds,
            "has_plays": len(plays) > 0,
        })

    results.sort(key=lambda x: (
        0 if x["has_plays"] else 1,
        min((p["tier"] for p in x["plays"]), default=99),
    ))

    return {
        "date": target,
        "games_scanned": len(games),
        "qualifying_games": sum(1 for r in results if r["has_plays"]),
        "total_plays": total_plays,
        "total_risk": total_risk,
        "credits_remaining": credits,
        "results": results,
        "scanned_at": datetime.now().isoformat(),
    }


@router.get("/signals")
async def get_signals():
    """Signal performance stats from backtest data."""
    return {
        "signals": [
            {"name": "F5 Tie + Under SGP", "description": "Same-game parlay on qualifying ace matchups. 1.51x correlation.",
             "bets": 292, "wins": 53, "win_rate": 18.2, "roi": 94.2, "pl": 6873, "p_value": None, "status": "proven"},
            {"name": "F1 Tie + FG Under SGP", "description": "Bovada SGP. FG total ≤ 8.0, both ERA < 4.50.",
             "bets": 612, "wins": 229, "win_rate": 37.4, "roi": 50.3, "pl": 7699, "p_value": None, "status": "proven"},
            {"name": "F5 Tie (Ace vs Ace)", "description": "Both starters ERA < 3.50. Bet at BetMGM.",
             "bets": 187, "wins": 41, "win_rate": 21.9, "roi": 22.0, "pl": 4110, "p_value": 0.10, "status": "promising"},
            {"name": "F5 Fav ML (ERA diff ≥ 1.5 + Hitter Park)", "description": "Heavy mismatch at a hitter park.",
             "bets": 284, "wins": 187, "win_rate": 65.8, "roi": 17.0, "pl": 4842, "p_value": 0.0002, "status": "proven"},
            {"name": "F5 Fav ML (ERA diff ≥ 1.0)", "description": "Pitching mismatch — favorite leads after 5.",
             "bets": 1159, "wins": 693, "win_rate": 59.8, "roi": 6.4, "pl": 7374, "p_value": 0.0004, "status": "proven"},
            {"name": "F5 Under (Both ERA < 3.50)", "description": "Ace matchup — scoring suppressed through 5.",
             "bets": 182, "wins": 107, "win_rate": 58.8, "roi": 10.7, "pl": 1952, "p_value": 0.009, "status": "proven"},
            {"name": "F5 Under (Both ERA < 4.50)", "description": "Decent pitching matchup — broadest under filter.",
             "bets": 1144, "wins": 629, "win_rate": 55.0, "roi": 3.2, "pl": 3675, "p_value": 0.0004, "status": "proven"},
        ],
    }


@router.get("/matrix")
async def get_matrix():
    """Edge matrix — try loading from backtest JSON, fall back to hardcoded."""
    json_path = BACKTEST_DIR / "edge_matrix.json"
    if json_path.exists():
        with open(json_path) as f:
            return json.load(f)
    return {"error": "Run edge_matrix.py to generate data"}


@router.get("/venues")
async def get_venues():
    """Venue edge data."""
    return {
        "venues": [
            {"venue": "Globe Life Field", "games": 76, "under_pct": 64, "under_roi": 22.9, "over_pct": 36, "over_roi": -32.0, "tie_pct": 20, "fav_pct": 50, "fav_roi": -7.1},
            {"venue": "Kauffman Stadium", "games": 77, "under_pct": 62, "under_roi": 16.5, "over_pct": 38, "over_roi": -28.6, "tie_pct": 17, "fav_pct": 53, "fav_roi": -4.8},
            {"venue": "Comerica Park", "games": 85, "under_pct": 61, "under_roi": 12.8, "over_pct": 39, "over_roi": -24.1, "tie_pct": 12, "fav_pct": 61, "fav_roi": 9.1},
            {"venue": "Wrigley Field", "games": 82, "under_pct": 59, "under_roi": 12.9, "over_pct": 41, "over_roi": -22.6, "tie_pct": 15, "fav_pct": 46, "fav_roi": -17.4},
            {"venue": "Citi Field", "games": 84, "under_pct": 59, "under_roi": 12.0, "over_pct": 41, "over_roi": -21.2, "tie_pct": 18, "fav_pct": 43, "fav_roi": -26.0},
            {"venue": "Chase Field", "games": 77, "under_pct": 41, "under_roi": -21.9, "over_pct": 59, "over_roi": 13.3, "tie_pct": 21, "fav_pct": 51, "fav_roi": 3.9},
            {"venue": "Progressive Field", "games": 86, "under_pct": 39, "under_roi": -28.9, "over_pct": 61, "over_roi": 17.6, "tie_pct": 7, "fav_pct": 62, "fav_roi": 16.6},
            {"venue": "loanDepot park", "games": 81, "under_pct": 37, "under_roi": -30.3, "over_pct": 63, "over_roi": 20.0, "tie_pct": 9, "fav_pct": 54, "fav_roi": -2.4},
            {"venue": "Angel Stadium", "games": 73, "under_pct": 39, "under_roi": -25.7, "over_pct": 61, "over_roi": 14.8, "tie_pct": 16, "fav_pct": 47, "fav_roi": -17.3},
            {"venue": "Target Field", "games": 83, "under_pct": 42, "under_roi": -21.0, "over_pct": 58, "over_roi": 10.9, "tie_pct": 13, "fav_pct": 53, "fav_roi": 1.4},
        ],
    }


@router.get("/pl")
async def get_pl():
    """P&L tracker data."""
    tracker_path = BACKTEST_DIR / "pl_tracker.json"
    if tracker_path.exists():
        with open(tracker_path) as f:
            return json.load(f)
    return {"daily": {}, "running": {"total_pl": 0, "total_bets": 0, "total_wins": 0, "days": 0}}


@router.get("/team-rankings")
async def get_team_rankings(sport: Optional[str] = Query(default="mlb")):
    """Betting team rankings — supports mlb, nfl, nba, nhl, ncaaf, ncaab."""
    sport = (sport or "mlb").lower()

    # Sport-specific file mapping
    file_map = {
        "mlb": "betting_rankings_2026.json",
        "nfl": "nfl_betting_rankings.json",
        "nba": "nba_betting_rankings.json",
        "nhl": "nhl_betting_rankings.json",
        "ncaaf": "ncaaf_betting_rankings.json",
        "ncaab": "ncaab_betting_rankings.json",
    }

    filename = file_map.get(sport)
    if not filename:
        return {"teams": [], "error": f"Unknown sport: {sport}"}

    json_path = BACKTEST_DIR / filename
    if json_path.exists():
        with open(json_path) as f:
            return {"teams": json.load(f), "sport": sport}
    return {"teams": [], "error": f"No data for {sport}"}


@router.get("/results")
async def get_results():
    """2026 backtest results by signal."""
    json_path = BACKTEST_DIR / "backtest_2026.json"
    if json_path.exists():
        with open(json_path) as f:
            return json.load(f)
    return {"signals": [], "games": 0, "ties": 0, "season": 2026}


@router.get("/credits")
async def get_credits():
    """Check Odds API credit balance."""
    if not ODDS_KEY:
        return {"error": "No ODDS_API_KEY set", "remaining": 0}

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{ODDS_API}/sports/", params={"apiKey": ODDS_KEY})
        return {
            "remaining": r.headers.get("x-requests-remaining", "?"),
            "used": r.headers.get("x-requests-used", "?"),
        }
