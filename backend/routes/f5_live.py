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

from services.mlb_umpire_stats import classify_umpire, get_umpire_stats
from services.mlb_bullpen import get_bullpen_data
from services.mlb_platoon_splits import get_platoon_splits_for_matchup
from services.mlb_lineup import check_lineup_confirmed, get_game_context, get_catcher_framing
from services.mlb_rolling_stats import get_team_rolling_stats
from services.mlb_bvp import get_bvp_for_game

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/f5", tags=["f5-live"])

ODDS_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_API = "https://api.the-odds-api.com/v4"
MLB_API = "https://statsapi.mlb.com/api/v1"
BACKTEST_DIR = Path(__file__).parent.parent / "f5_backtest"

# ── Odds cache: disk-backed, survives restarts, one Odds API hit per day ─────
_ODDS_CACHE_FILE = BACKTEST_DIR / "odds_cache_today.json"
_mem_cache: dict = {}  # hot path: avoid disk read on every request


def _get_cached_odds() -> tuple[dict, str] | None:
    today = date.today().isoformat()
    # 1. Check hot in-memory cache first
    if _mem_cache.get("date") == today and _mem_cache.get("data"):
        return _mem_cache["data"], _mem_cache.get("remaining", "?")
    # 2. Fall back to disk cache (survives restarts)
    try:
        if _ODDS_CACHE_FILE.exists():
            payload = json.loads(_ODDS_CACHE_FILE.read_text())
            if payload.get("date") == today and payload.get("data"):
                # Warm the in-memory cache
                _mem_cache.update(payload)
                logger.info("Odds loaded from disk cache")
                return payload["data"], payload.get("remaining", "?")
    except Exception as exc:
        logger.warning(f"Odds disk cache read failed: {exc}")
    return None


def _set_cached_odds(data: dict, remaining: str) -> None:
    today = date.today().isoformat()
    payload = {"date": today, "data": data, "remaining": remaining}
    _mem_cache.update(payload)
    try:
        _ODDS_CACHE_FILE.write_text(json.dumps(payload))
    except Exception as exc:
        logger.warning(f"Odds disk cache write failed: {exc}")

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

                away_stats = await _fetch_pitcher_stats(client, ap.get("id"), scan_date[:4])
                home_stats = await _fetch_pitcher_stats(client, hp.get("id"), scan_date[:4])

                away_era = away_stats.get("era")
                home_era = home_stats.get("era")
                era_diff = abs(away_era - home_era) if away_era and home_era else None

                # Umpire: quantitative classification replaces static sets
                ump_class = classify_umpire(hp_ump) if hp_ump else "NEUTRAL"
                ump_tag = (
                    "HIGH_TIE" if ump_class == "PITCHER_FRIENDLY"
                    else "LOW_TIE" if ump_class == "HITTER_FRIENDLY"
                    else None
                )

                games.append({
                    "away_team": away,
                    "home_team": home,
                    "venue": venue,
                    "away_pitcher": ap.get("fullName", "TBD"),
                    "home_pitcher": hp.get("fullName", "TBD"),
                    "away_era": away_era,
                    "home_era": home_era,
                    "era_diff": round(era_diff, 2) if era_diff else None,
                    "away_pitcher_stats": away_stats,
                    "home_pitcher_stats": home_stats,
                    "hp_umpire": hp_ump,
                    "ump_class": ump_class,
                    "ump_tag": ump_tag,
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
    """Legacy: season ERA only."""
    stats = await _fetch_pitcher_stats(client, pid, season)
    return stats.get("era")


async def _fetch_pitcher_stats(client: httpx.AsyncClient, pid: int | None, season: str) -> dict:
    """Full pitcher stats: season ERA/K9/BB9/WHIP + last 3 starts form."""
    if not pid:
        return {}
    result: dict = {}
    try:
        # Season stats
        r = await client.get(
            f"{MLB_API}/people/{pid}/stats",
            params={"stats": "season", "season": season, "group": "pitching"},
        )
        splits = r.json().get("stats", [{}])[0].get("splits", [])
        if splits:
            s = splits[0]["stat"]
            era = float(s.get("era", 99))
            ip_str = s.get("inningsPitched", "0")
            ip = float(ip_str) if ip_str else 0
            so = int(s.get("strikeOuts", 0))
            bb = int(s.get("baseOnBalls", 0))
            whip = float(s.get("whip", 0)) if s.get("whip") else None
            k9 = round((so / ip) * 9, 1) if ip > 0 else None
            bb9 = round((bb / ip) * 9, 1) if ip > 0 else None
            result.update({
                "era": era if era < 99 else None,
                "k9": k9,
                "bb9": bb9,
                "whip": round(whip, 2) if whip else None,
                "season_ip": round(ip, 1),
                "season_so": so,
                "season_gs": int(s.get("gamesStarted", 0)),
            })

        # Last 3 starts
        r2 = await client.get(
            f"{MLB_API}/people/{pid}/stats",
            params={"stats": "gameLog", "season": season, "group": "pitching"},
        )
        all_splits = r2.json().get("stats", [{}])[0].get("splits", [])
        # Filter to starts only (inningsPitched > 1.0 typically, or gamesStarted)
        starts = [sp for sp in all_splits if int(sp["stat"].get("gamesStarted", 0)) > 0]
        last3 = starts[-3:] if len(starts) >= 3 else starts
        if last3:
            recent_era = sum(float(sp["stat"].get("era", 9)) for sp in last3) / len(last3)
            recent_ip = sum(float(sp["stat"].get("inningsPitched", 0)) for sp in last3) / len(last3)
            recent_k = sum(int(sp["stat"].get("strikeOuts", 0)) for sp in last3)
            result.update({
                "recent_era": round(recent_era, 2),
                "recent_avg_ip": round(recent_ip, 1),
                "recent_k": recent_k,
                "recent_starts": len(last3),
            })
    except Exception as exc:
        logger.debug(f"Pitcher stats fetch failed pid={pid}: {exc}")
    return result


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
    force: bool = Query(default=False),
):
    """Today's games scored against all signals.
    Odds are cached per calendar day — only costs credits on first load or force=true.
    """
    target = scan_date or date.today().isoformat()

    games = await _fetch_mlb_games(target)

    fg_odds: dict = {}
    credits = "skipped"
    if use_odds and ODDS_KEY:
        cached = None if force else _get_cached_odds()
        if cached:
            fg_odds, credits = cached
            logger.info("Odds served from cache (0 credits used)")
        else:
            fg_odds, credits = await _fetch_fg_odds()
            _set_cached_odds(fg_odds, credits)
            logger.info(f"Fresh odds fetched — {credits} credits remaining")

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
async def get_team_rankings(
    sport: Optional[str] = Query(default="mlb"),
    season: Optional[str] = Query(default=None),
):
    """Betting team rankings — supports mlb, nfl, nba, nhl, ncaaf, ncaab with season filter."""
    sport = (sport or "mlb").lower()

    # Available seasons per sport (most recent first)
    SEASONS: dict = {
        "mlb":   [{"key": "2026", "label": "2026", "current": True}],
        "nfl":   [{"key": "2025", "label": "2025", "current": False}, {"key": "2024", "label": "2024", "current": False}, {"key": "2023", "label": "2023", "current": False}, {"key": "2022", "label": "2022", "current": False}, {"key": "2021", "label": "2021", "current": False}, {"key": "2020", "label": "2020", "current": False}, {"key": "2019", "label": "2019", "current": False}, {"key": "2018", "label": "2018", "current": False}, {"key": "2017", "label": "2017", "current": False}, {"key": "2016", "label": "2016", "current": False}, {"key": "2015", "label": "2015", "current": False}],
        "nba":   [{"key": "2024_25", "label": "2024-25", "current": False}, {"key": "2023_24", "label": "2023-24", "current": False}, {"key": "2022_23", "label": "2022-23", "current": False}],
        "nhl":   [{"key": "2024-25", "label": "2024-25", "current": False}],
        "ncaaf": [{"key": "2024", "label": "2024", "current": False}, {"key": "2023", "label": "2023", "current": False}],
        "ncaab": [{"key": "2025", "label": "2024-25", "current": False}, {"key": "2024", "label": "2023-24", "current": False}, {"key": "2023", "label": "2022-23", "current": False}],
    }

    available = SEASONS.get(sport, [])
    if not available:
        return {"teams": [], "seasons": [], "error": f"Unknown sport: {sport}"}

    # Default to most recent season
    sel = season or available[0]["key"]

    # File mapping
    if sport == "mlb":
        filename = "betting_rankings_2026.json"
    elif sport == "nhl":
        filename = "nhl_betting_rankings.json"
    else:
        filename = f"{sport}_betting_rankings_{sel}.json"

    json_path = BACKTEST_DIR / filename
    if json_path.exists():
        with open(json_path) as f:
            return {"teams": json.load(f), "sport": sport, "season": sel, "seasons": available}

    # Fallback to aggregate file
    fallback = BACKTEST_DIR / f"{sport}_betting_rankings.json"
    if fallback.exists():
        with open(fallback) as f:
            return {"teams": json.load(f), "sport": sport, "season": "all", "seasons": available}

    return {"teams": [], "seasons": available, "error": f"No data for {sport} season {sel}"}


@router.get("/ats-rankings")
async def get_ats_rankings(
    sport: Optional[str] = Query(default="nfl"),
    season: Optional[str] = Query(default=None),
):
    """ATS and O/U records by team — currently NFL only."""
    sport = (sport or "nfl").lower()

    ATS_SEASONS: dict = {
        "nfl": [{"key": str(y), "label": str(y), "current": False} for y in range(2025, 2014, -1)],
    }

    available = ATS_SEASONS.get(sport, [])
    sel = season or (available[0]["key"] if available else "")

    json_path = BACKTEST_DIR / f"nfl_ats_{sel}.json"
    if json_path.exists():
        with open(json_path) as f:
            return {"teams": json.load(f), "sport": sport, "season": sel, "seasons": available}

    return {"teams": [], "seasons": available, "error": f"No ATS data for {sport} {sel}"}


@router.get("/nhl-goalie-rankings")
async def get_nhl_goalie_rankings():
    """NHL team stats + goalie save%, GAA, shutouts (2024-25)."""
    json_path = BACKTEST_DIR / "nhl_goalie_rankings_2024_25.json"
    if json_path.exists():
        with open(json_path) as f:
            return json.load(f)
    return {"teams": [], "goalies": [], "error": "NHL goalie data not available"}


@router.get("/nba-efficiency")
async def get_nba_efficiency():
    """NBA pace + efficiency ratings (ESPN-derived)."""
    json_path = BACKTEST_DIR / "nba_efficiency_2024_25.json"
    if json_path.exists():
        with open(json_path) as f:
            return json.load(f)
    return {"teams": [], "error": "NBA efficiency data not available"}



@router.get("/ncaab-efficiency")
async def get_ncaab_efficiency(season: Optional[str] = Query(default="2025")):
    """NCAAB efficiency ratings with conference SOS proxy (composite AdjEM)."""
    json_path = BACKTEST_DIR / "ncaab_efficiency.json"
    if not json_path.exists():
        return {"teams": [], "error": "NCAAB efficiency data not available"}
    with open(json_path) as f:
        data = json.load(f)
    sel = season or "2025"
    teams = data.get("seasons", {}).get(sel, [])
    seasons = [
        {"key": "2025", "label": "2024-25", "current": True},
        {"key": "2024", "label": "2023-24", "current": False},
        {"key": "2023", "label": "2022-23", "current": False},
    ]
    return {
        "teams": teams,
        "season": sel,
        "seasons": seasons,
        "method": data.get("method"),
        "note": data.get("note"),
    }

@router.get("/power-ratings")
async def get_power_ratings(
    season: Optional[str] = Query(default="current"),
):
    """Walters-method NFL power ratings by season."""
    json_path = BACKTEST_DIR / "nfl_power_ratings.json"
    if not json_path.exists():
        return {"teams": [], "error": "Power ratings not built yet"}

    with open(json_path) as f:
        data = json.load(f)

    seasons_list = [{"key": "current", "label": "2025 (Current)", "current": True}]
    seasons_list += [{"key": yr, "label": yr, "current": False} for yr in reversed(sorted(data.get("seasons", {}).keys()))]

    if season == "current":
        teams = data.get("current", [])
    else:
        teams = data.get("seasons", {}).get(season, [])

    return {
        "teams": teams,
        "season": season,
        "seasons": seasons_list,
        "method": data.get("method"),
        "formula": data.get("formula"),
    }


@router.get("/firsthalf-rankings")
async def get_firsthalf_rankings(
    sport: Optional[str] = Query(default="nfl"),
    season: Optional[str] = Query(default=None),
):
    """First-half scoring stats by team — NFL only currently."""
    sport = (sport or "nfl").lower()

    FH_SEASONS: dict = {
        "nfl": [{"key": str(y), "label": str(y), "current": y == 2025} for y in range(2025, 2014, -1)],
    }
    FH_SEASONS["nfl"].insert(0, {"key": "all", "label": "All-Time", "current": False})

    available = FH_SEASONS.get(sport, [])
    sel = season or "2025"

    json_path = BACKTEST_DIR / "nfl_firsthalf_rankings.json"
    if json_path.exists():
        with open(json_path) as f:
            data = json.load(f)
        teams = data.get(sel, data.get("2025", []))
        return {"teams": teams, "sport": sport, "season": sel, "seasons": available}

    return {"teams": [], "seasons": available, "error": "No first-half data available"}


@router.get("/results")
async def get_results():
    """2026 backtest results by signal."""
    json_path = BACKTEST_DIR / "backtest_2026.json"
    if json_path.exists():
        with open(json_path) as f:
            return json.load(f)
    return {"signals": [], "games": 0, "ties": 0, "season": 2026}


@router.get("/recap")
async def get_recap(date: Optional[str] = Query(default=None)):
    """
    Grade yesterday's (or any date's) MLB F5 games against our signals.
    Pulls final scores from MLB Stats API (free) and reconstructs signal outcomes.
    """
    from datetime import date as dt_date, timedelta
    import re

    scan_date = date or str(dt_date.today() - timedelta(days=1))

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
        "Chase Field", "Globe Life Field", "Yankee Stadium", "Citi Field",
        "Busch Stadium", "American Family Field",
    }
    UNDER_VENUES = {
        "Globe Life Field", "Kauffman Stadium", "Comerica Park",
        "Wrigley Field", "Citi Field",
    }

    MLB_STATS = "https://statsapi.mlb.com/api/v1"

    async def fetch_era(client: httpx.AsyncClient, pitcher_id: int, season: str) -> Optional[float]:
        try:
            r = await client.get(
                f"{MLB_STATS}/people/{pitcher_id}/stats",
                params={"stats": "season", "season": season, "group": "pitching"},
                timeout=8,
            )
            splits = r.json().get("stats", [{}])[0].get("splits", [])
            if splits:
                return float(splits[0]["stat"].get("era", 99))
        except Exception:
            pass
        return None

    season_year = scan_date[:4]

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{MLB_STATS}/schedule", params={
            "sportId": 1, "startDate": scan_date, "endDate": scan_date,
            "gameType": "R", "hydrate": "linescore,probablePitcher,officials,venue",
        })
        raw_games = []
        for d in r.json().get("dates", []):
            for g in d.get("games", []):
                raw_games.append(g)

    games_out = []
    for g in raw_games:
        state = g.get("status", {}).get("detailedState", "")
        if state not in ("Final", "Completed Early"):
            continue

        ls = g.get("linescore", {})
        innings = ls.get("innings", [])
        if len(innings) < 5:
            continue

        away = g["teams"]["away"]["team"]["name"]
        home = g["teams"]["home"]["team"]["name"]
        venue = g.get("venue", {}).get("name", "")

        away_r5 = sum(inn.get("away", {}).get("runs", 0) for inn in innings[:5])
        home_r5 = sum(inn.get("home", {}).get("runs", 0) for inn in innings[:5])
        f1_away = innings[0].get("away", {}).get("runs", 0)
        f1_home = innings[0].get("home", {}).get("runs", 0)
        away_final = ls.get("teams", {}).get("away", {}).get("runs", 0)
        home_final = ls.get("teams", {}).get("home", {}).get("runs", 0)

        ap = g["teams"]["away"].get("probablePitcher", {})
        hp = g["teams"]["home"].get("probablePitcher", {})
        officials = g.get("officials", [])
        hp_ump = next(
            (o["official"]["fullName"] for o in officials if o.get("officialType") == "Home Plate"),
            None,
        )

        # Fetch ERAs concurrently
        async with httpx.AsyncClient(timeout=10) as ec:
            tasks = []
            if ap.get("id"):
                tasks.append(fetch_era(ec, ap["id"], season_year))
            else:
                tasks.append(None)
            if hp.get("id"):
                tasks.append(fetch_era(ec, hp["id"], season_year))
            else:
                tasks.append(None)
            import asyncio
            results_era = await asyncio.gather(*[t if t is not None else asyncio.coroutine(lambda: None)() for t in tasks], return_exceptions=True)

        away_era = results_era[0] if not isinstance(results_era[0], Exception) else None
        home_era = results_era[1] if not isinstance(results_era[1], Exception) else None
        era_diff = abs(away_era - home_era) if away_era and home_era else None

        f5_total = away_r5 + home_r5
        f5_tied = away_r5 == home_r5
        f5_leader = "away" if away_r5 > home_r5 else "home" if home_r5 > away_r5 else "tie"

        # Determine signals that fired
        ace_ace = away_era and home_era and away_era < 3.5 and home_era < 3.5
        both_under_4 = away_era and home_era and away_era < 4.0 and home_era < 4.0
        both_under_45 = away_era and home_era and away_era < 4.5 and home_era < 4.5
        venue_tie = venue in HIGH_TIE_VENUES and bool(both_under_4)
        hi_ump = hp_ump in HIGH_TIE_UMPS if hp_ump else False
        lo_ump = hp_ump in LOW_TIE_UMPS if hp_ump else False
        venue_under = venue in UNDER_VENUES

        signals_fired: list[dict] = []

        # F5 Tie (Ace vs Ace)
        if ace_ace:
            won = f5_tied
            pl = round(100 * 4.5 if won else -100, 2)
            signals_fired.append({"name": "F5 Tie (Ace vs Ace)", "tier": "STRONG", "won": won, "pl": pl, "result": "TIE" if f5_tied else f5_leader.upper()})

        # F5 Tie (Hi-Venue + ERA<4)
        if venue_tie and not ace_ace:
            won = f5_tied
            pl = round(100 * 4.5 if won else -100, 2)
            signals_fired.append({"name": "F5 Tie (Hi-Venue+ERA<4)", "tier": "STRONG", "won": won, "pl": pl, "result": "TIE" if f5_tied else f5_leader.upper()})

        # F5 Under
        if both_under_45:
            est_line = 4.5
            won = f5_total < est_line
            push = f5_total == est_line
            if not push:
                pl = round(100 * 0.91 if won else -100, 2)
                lbl = "UNDER" if won else "OVER"
                signals_fired.append({"name": f"F5 Under (ERA<4.50) — F5 Total: {f5_total}", "tier": "GOOD" if not (away_era and home_era and away_era < 3.5 and home_era < 3.5) else "STRONG", "won": won, "pl": pl, "result": lbl})

        # F5 Fav ML
        if era_diff and era_diff >= 1.5:
            fav = "home" if home_era and away_era and home_era < away_era else "away"
            won = f5_leader == fav
            tied = f5_leader == "tie"
            pl = round((-100 if tied else (100 * 0.77 if won else -100)), 2)
            signals_fired.append({"name": f"F5 Fav ML (diff>={era_diff:.1f})", "tier": "STRONG", "won": won, "pl": pl, "result": f5_leader.upper()})

        # Venue Under
        if venue_under:
            won = f5_total <= 4
            signals_fired.append({"name": f"F5 Under (Venue: {venue})", "tier": "GOOD", "won": won, "pl": round(100 * 0.91 if won else -100, 2), "result": f"F5={f5_total}"})

        game_record = {
            "away_team": away,
            "home_team": home,
            "away_pitcher": ap.get("fullName", "TBD"),
            "home_pitcher": hp.get("fullName", "TBD"),
            "away_era": away_era,
            "home_era": home_era,
            "venue": venue,
            "hp_umpire": hp_ump,
            "hi_ump": hi_ump,
            "lo_ump": lo_ump,
            "away_r5": away_r5,
            "home_r5": home_r5,
            "f5_total": f5_total,
            "f5_tied": f5_tied,
            "f5_leader": f5_leader,
            "f1_away": f1_away,
            "f1_home": f1_home,
            "away_final": away_final,
            "home_final": home_final,
            "signals": signals_fired,
        }
        games_out.append(game_record)

    # Daily summary
    all_signals = [s for g in games_out for s in g["signals"]]
    total_bets = len(all_signals)
    total_wins = sum(1 for s in all_signals if s["won"])
    total_pl = round(sum(s["pl"] for s in all_signals), 2)
    ties_today = sum(1 for g in games_out if g["f5_tied"])

    # Persist to rolling signal performance log for verification pipeline
    if games_out and total_bets > 0:
        try:
            from verification.signal_logger import append_day
            append_day(scan_date, games_out)
        except Exception as log_err:
            logger.warning(f"signal_logger append failed: {log_err}")

    return {
        "date": scan_date,
        "games": games_out,
        "total_games": len(games_out),
        "ties_today": ties_today,
        "tie_rate": round(ties_today / len(games_out) * 100, 1) if games_out else 0,
        "summary": {
            "total_bets": total_bets,
            "wins": total_wins,
            "losses": total_bets - total_wins,
            "win_rate": round(total_wins / total_bets * 100, 1) if total_bets else 0,
            "total_pl": total_pl,
        },
    }


@router.get("/mlb-signals/{game_pk}")
async def get_mlb_game_signals(game_pk: int):
    """
    Full MLB signal enrichment for a single game.
    Aggregates: umpire tendencies, bullpen state, platoon splits, catcher framing,
    lineup confirmation, rolling team form, and BvP matchup data.
    Used by the handicapping agent as evidence layer before Sonnet evaluation.
    """
    import asyncio

    # Step 1: basic game context from MLB Stats API
    context = await get_game_context(game_pk)
    lineup_data = await check_lineup_confirmed(game_pk)

    home_team = None
    away_team = None
    home_pitcher = None
    away_pitcher = None
    home_pitcher_id = None
    away_pitcher_id = None
    hp_umpire = None
    home_sp_hand = None
    away_sp_hand = None

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            # Use schedule endpoint — works for Preview AND Live/Final games
            r = await client.get(
                f"{MLB_API}/schedule",
                params={
                    "gamePks": game_pk,
                    "hydrate": "probablePitcher,officials,venue,weather",
                },
            )
            dates = r.json().get("dates", [])
            game_info = None
            for d in dates:
                for g in d.get("games", []):
                    if g.get("gamePk") == game_pk:
                        game_info = g
                        break

            if game_info:
                home_team = game_info["teams"]["home"]["team"]["name"]
                away_team = game_info["teams"]["away"]["team"]["name"]

                hp = game_info["teams"]["home"].get("probablePitcher", {})
                ap = game_info["teams"]["away"].get("probablePitcher", {})
                home_pitcher = hp.get("fullName")
                away_pitcher = ap.get("fullName")
                home_pitcher_id = hp.get("id")
                away_pitcher_id = ap.get("id")

                officials = game_info.get("officials", [])
                hp_umpire = next(
                    (o["official"]["fullName"] for o in officials
                     if o.get("officialType") == "Home Plate"), None
                )

                # Fetch pitcher handedness from people endpoint
                if home_pitcher_id:
                    r2 = await client.get(f"{MLB_API}/people/{home_pitcher_id}")
                    ph_info = r2.json().get("people", [{}])[0]
                    home_sp_hand = ph_info.get("pitchHand", {}).get("code", "R")
                if away_pitcher_id:
                    r3 = await client.get(f"{MLB_API}/people/{away_pitcher_id}")
                    ph_info = r3.json().get("people", [{}])[0]
                    away_sp_hand = ph_info.get("pitchHand", {}).get("code", "R")

    except Exception as exc:
        logger.error("Game signal fetch failed for game_pk=%s: %s", game_pk, exc)

    if not home_team or not away_team:
        return {"game_pk": game_pk, "error": "Game data not available"}

    # Step 2: fire all enrichment services in parallel
    tasks = {
        "umpire": asyncio.create_task(get_umpire_stats(hp_umpire)) if hp_umpire else None,
        "home_bullpen": asyncio.create_task(get_bullpen_data(home_team)),
        "away_bullpen": asyncio.create_task(get_bullpen_data(away_team)),
        "home_rolling": asyncio.create_task(get_team_rolling_stats(home_team)),
        "away_rolling": asyncio.create_task(get_team_rolling_stats(away_team)),
    }

    if home_sp_hand and away_sp_hand:
        tasks["platoon"] = asyncio.create_task(
            get_platoon_splits_for_matchup(home_team, away_team, away_sp_hand, home_sp_hand)
        )

    home_lineup_names = [p["name"] for p in lineup_data.get("home_lineup", []) if p.get("name")]
    away_lineup_names = [p["name"] for p in lineup_data.get("away_lineup", []) if p.get("name")]

    if home_pitcher and away_pitcher and home_lineup_names and away_lineup_names:
        tasks["bvp"] = asyncio.create_task(
            get_bvp_for_game(
                home_lineup_names, away_lineup_names,
                home_pitcher, away_pitcher,
                home_pitcher_id, away_pitcher_id,
            )
        )

    results = {}
    for key, task in tasks.items():
        if task is not None:
            try:
                results[key] = await task
            except Exception as exc:
                logger.warning("Signal task %s failed: %s", key, exc)
                results[key] = {"error": str(exc)}

    # Catcher framing (synchronous)
    home_catcher = lineup_data.get("home_catcher")
    away_catcher = lineup_data.get("away_catcher")
    framing = {
        "home": get_catcher_framing(home_catcher) if home_catcher else None,
        "away": get_catcher_framing(away_catcher) if away_catcher else None,
    }

    return {
        "game_pk": game_pk,
        "home_team": home_team,
        "away_team": away_team,
        "home_pitcher": home_pitcher,
        "away_pitcher": away_pitcher,
        "hp_umpire": hp_umpire,
        "lineup_confirmed": lineup_data.get("confirmed", False),
        "game_context": context,
        "umpire_stats": results.get("umpire"),
        "home_bullpen": results.get("home_bullpen"),
        "away_bullpen": results.get("away_bullpen"),
        "platoon_splits": results.get("platoon"),
        "home_rolling": results.get("home_rolling"),
        "away_rolling": results.get("away_rolling"),
        "bvp": results.get("bvp"),
        "catcher_framing": framing,
    }


@router.get("/survivor")
async def get_survivor_data():
    """
    Circa Survivor helper — 2025 NFL season.
    Returns full 17-week schedule cross-referenced with Walters power ratings.
    Each game scored: win_prob = sigmoid of (home_rating - away_rating + 2.5 HFA) / 7.
    """
    import math

    schedule_path = BACKTEST_DIR / "nfl_schedule_2026.json"
    ratings_path  = BACKTEST_DIR / "nfl_power_ratings.json"

    if not schedule_path.exists() or not ratings_path.exists():
        return {"error": "Schedule or ratings data not available", "weeks": {}}

    with open(schedule_path) as f:
        raw_schedule = json.load(f)
    with open(ratings_path) as f:
        ratings_data = json.load(f)

    # Build rating lookup: abbr -> rating
    rating_map: dict[str, float] = {}
    tier_map:   dict[str, str]   = {}
    for t in ratings_data.get("current", []):
        rating_map[t["team"]] = t["rating"]
        tier_map[t["team"]]   = t.get("tier", "AVERAGE")

    def win_prob(home_rating: float, away_rating: float, home: bool = True) -> float:
        hfa = 2.5 if home else 0.0
        diff = home_rating - away_rating + hfa
        return round(1 / (1 + math.exp(-diff / 7)), 3)

    def matchup_label(prob: float) -> str:
        if prob >= 0.72:  return "GREAT"
        if prob >= 0.60:  return "GOOD"
        if prob >= 0.50:  return "LEAN"
        if prob >= 0.40:  return "TOUGH"
        return "TRAP"

    weeks_out: dict = {}
    for week_str, games in raw_schedule.items():
        week = int(week_str)
        week_games = []
        for g in games:
            home_abbr = g["home"]
            away_abbr = g["away"]
            home_rat = rating_map.get(home_abbr, 0.0)
            away_rat = rating_map.get(away_abbr, 0.0)
            home_wp  = win_prob(home_rat, away_rat, home=True)
            away_wp  = win_prob(away_rat, home_rat, home=False)
            week_games.append({
                "home": home_abbr,
                "away": away_abbr,
                "home_name": g.get("home_name", home_abbr),
                "away_name": g.get("away_name", away_abbr),
                "date": g.get("date", ""),
                "home_rating": round(home_rat, 2),
                "away_rating": round(away_rat, 2),
                "home_wp": home_wp,
                "away_wp": away_wp,
                "home_tier": tier_map.get(home_abbr, "AVERAGE"),
                "away_tier": tier_map.get(away_abbr, "AVERAGE"),
                "home_label": matchup_label(home_wp),
                "away_label": matchup_label(away_wp),
            })
        # Sort by best home win prob descending so top picks show first
        week_games.sort(key=lambda x: -max(x["home_wp"], x["away_wp"]))
        weeks_out[week] = week_games

    # Build per-team schedule view: team -> [{week, opponent, home, wp, label}]
    team_schedule: dict[str, list] = {}
    for week_str, games in raw_schedule.items():
        week = int(week_str)
        for g in games:
            for side in ("home", "away"):
                opp_side = "away" if side == "home" else "home"
                team  = g[side]
                opp   = g[opp_side]
                is_home = side == "home"
                t_rat = rating_map.get(team, 0.0)
                o_rat = rating_map.get(opp, 0.0)
                wp = win_prob(t_rat, o_rat, home=is_home)
                if team not in team_schedule:
                    team_schedule[team] = []
                team_schedule[team].append({
                    "week": week,
                    "opp": opp,
                    "home": is_home,
                    "wp": wp,
                    "label": matchup_label(wp),
                    "team_rating": round(t_rat, 2),
                    "opp_rating":  round(o_rat, 2),
                    "date": g.get("date", ""),
                })
            # Handle bye weeks implicitly (no entry for that week = bye)

    # Sort each team's schedule by week
    for team in team_schedule:
        team_schedule[team].sort(key=lambda x: x["week"])

    # Build team list with ratings + tier
    teams_out = []
    for t in ratings_data.get("current", []):
        teams_out.append({
            "team": t["team"],
            "team_name": t.get("team_name", t["team"]),
            "rating": t["rating"],
            "tier": t.get("tier", "AVERAGE"),
            "schedule": team_schedule.get(t["team"], []),
        })
    teams_out.sort(key=lambda x: -x["rating"])

    return {
        "season": 2026,
        "weeks": weeks_out,
        "teams": teams_out,
    }


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
