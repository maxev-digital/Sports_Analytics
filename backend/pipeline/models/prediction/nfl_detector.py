"""
NFL prediction engine — power-rating overlay + multibook vig detectors.

Entry point
-----------
rule_based_nfl_edges(min_edge)
    Two detectors, no trained model required:

    1. Rating Overlay (ATS) — compares each team's power rating (see
       ``pipeline/ingestion/team_ratings_ingestion.py``; point differential
       per game, since free NFL DVOA doesn't exist) against the market
       spread. A large rating/spread mismatch on a small spread flags
       value on the side the market is underpricing.
       Thresholds match the original task spec (rating gap > 7pts,
       market spread < 4pts) and are a starting point — tune with
       backtests once historical data is loaded.

    2. Multibook Vig (ATS + totals) — same cross-book divergence
       technique used by ``mlb_predictor.py``: for each point line,
       compare each book's price against the field consensus.

Pick dict schema
-----------------
{
  'sport'               : 'nfl',
  'home_team', 'away_team', 'game_time_cst', 'game_id',
  'pick_side'           : 'home' | 'away' | 'over' | 'under',
  'pick_type'           : 'spread' | 'total',
  'our_probability', 'market_odds', 'market_implied_prob', 'edge_pct',
  'detector', 'confidence_tier', 'total_line',
  'features'            : {'books_sampled', 'divergence_pct', ...},
}
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone as _tz
from typing import Optional

import numpy as np

from pipeline.config import MIN_EDGE_PCT
from pipeline.db.connection import execute_query
from pipeline.ingestion.live_odds import fetch_live_odds

logger = logging.getLogger(__name__)

SPORT_KEY = "americanfootball_nfl"
SPORT_LABEL = "nfl"

# Rating-overlay thresholds (task spec starting point, tune with backtests)
_ATS_MIN_RATING_GAP = 7.0
_ATS_MAX_SPREAD_FOR_VALUE = 4.0
_RATING_POINT_TO_PROB = 0.025  # ~2.5% cover-prob shift per point of gap (heuristic)
_DEFAULT_SPREAD_PRICE = -110  # assumed juice when no book-specific price available

# Multibook divergence threshold — matches the 2% corroboration floor
_MULTIBOOK_PROB_DIVERGENCE = 0.02


def _american_to_implied(odds: int) -> float:
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return abs(odds) / (abs(odds) + 100.0)


def _to_cst_str(iso_str: str) -> str:
    try:
        import pytz
        cst = pytz.timezone("America/Chicago")
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.astimezone(cst).strftime("%Y-%m-%d %I:%M %p CST")
    except Exception:
        return iso_str


def _is_future_game(commence_time: str) -> bool:
    try:
        if not commence_time:
            return True
        dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_tz.utc)
        return dt > datetime.now(_tz.utc)
    except Exception:
        return True


def _load_power_ratings(sport: str) -> dict[str, float]:
    rows = execute_query(
        "SELECT team, power_rating FROM team_ratings WHERE sport = %s AND power_rating IS NOT NULL",
        (sport,),
    )
    return {r["team"]: float(r["power_rating"]) for r in rows}


def _build_pick(
    *,
    sport: str,
    game: dict,
    game_time_cst: str,
    pick_side: str,
    pick_type: str,
    our_prob: float,
    market_odds: int,
    market_implied: float,
    detector: str,
    features: dict,
    total_line: Optional[float] = None,
) -> dict:
    return {
        "sport": sport,
        "game_id": game.get("game_id", ""),
        "home_team": game.get("home_team", ""),
        "away_team": game.get("away_team", ""),
        "game_time_cst": game_time_cst,
        "pick_side": pick_side,
        "pick_type": pick_type,
        "our_probability": round(our_prob, 4),
        "market_odds": market_odds,
        "market_implied_prob": round(market_implied, 4),
        "edge_pct": round((our_prob - market_implied) * 100, 2),
        "detector": detector,
        "confidence_tier": "medium",
        "total_line": total_line,
        "features": features,
    }


def _rating_overlay_detector(
    games: list[dict], ratings: dict[str, float], min_edge: float
) -> list[dict]:
    """Detector 1: power rating gap vs market spread (ATS)."""
    picks: list[dict] = []

    for game in games:
        home_team = game.get("home_team", "")
        away_team = game.get("away_team", "")
        if not _is_future_game(game.get("commence_time", "")):
            continue

        home_rating = ratings.get(home_team)
        away_rating = ratings.get(away_team)
        if home_rating is None or away_rating is None:
            continue

        bookmakers = game.get("bookmakers", [])
        if not bookmakers:
            continue

        # Collect spread points + prices per side, keyed by the home-team point
        # value (books quoting different points aren't directly comparable).
        by_line: dict = defaultdict(lambda: {"home": [], "away": []})
        for bk in bookmakers:
            bk_key = bk.get("key", "unknown")
            outcomes = bk.get("markets", {}).get("spreads", [])
            home_out = next((o for o in outcomes if o.get("name") == home_team), None)
            away_out = next((o for o in outcomes if o.get("name") == away_team), None)
            if not (home_out and away_out):
                continue
            hp = home_out.get("point")
            ho, ao = home_out.get("price"), away_out.get("price")
            if hp is None or ho is None or ao is None:
                continue
            by_line[float(hp)]["home"].append((bk_key, int(ho)))
            by_line[float(hp)]["away"].append((bk_key, int(ao)))

        if not by_line:
            continue

        # Use the line with the most books quoting it as "the" market spread
        market_home_point = max(by_line, key=lambda p: len(by_line[p]["home"]))
        home_prices = by_line[market_home_point]["home"]
        away_prices = by_line[market_home_point]["away"]
        books_sampled = len(home_prices)
        if books_sampled < 3 or abs(market_home_point) >= _ATS_MAX_SPREAD_FOR_VALUE:
            continue

        expected_margin_home = home_rating - away_rating
        market_margin_home = -market_home_point
        gap = expected_margin_home - market_margin_home

        if abs(gap) < _ATS_MIN_RATING_GAP:
            continue

        pick_side = "home" if gap > 0 else "away"
        side_prices = home_prices if pick_side == "home" else away_prices
        avg_price = round(sum(p for _, p in side_prices) / len(side_prices))
        # "Best" price = most favorable to the bettor. For American odds this
        # is simply the max (closest to zero on the negative side, or the
        # highest positive payout on the underdog side).
        best_price = max(p for _, p in side_prices)

        # Second-signal divergence: how far the best available price is from
        # the field average for this side (independent of the rating gap).
        implied_prices = [_american_to_implied(p) for _, p in side_prices]
        consensus_ip = float(np.mean(implied_prices))
        best_ip = _american_to_implied(best_price)
        divergence_pct = round(abs(consensus_ip - best_ip) * 100, 2)

        market_implied = _american_to_implied(avg_price)
        prob_shift = min(abs(gap) * _RATING_POINT_TO_PROB, 0.15)
        our_prob = min(market_implied + prob_shift, 0.85)
        edge_pct = (our_prob - market_implied) * 100

        if edge_pct < min_edge:
            continue

        game_time_cst = _to_cst_str(game.get("commence_time", ""))
        picks.append(_build_pick(
            sport=SPORT_LABEL,
            game=game,
            game_time_cst=game_time_cst,
            pick_side=pick_side,
            pick_type="spread",
            our_prob=our_prob,
            market_odds=avg_price,
            market_implied=market_implied,
            detector="rule_nfl_rating_overlay",
            features={
                "home_power_rating": round(home_rating, 2),
                "away_power_rating": round(away_rating, 2),
                "rating_gap": round(gap, 2),
                "market_spread_home": market_home_point,
                "books_sampled": books_sampled,
                "divergence_pct": divergence_pct,
                "rating_source": "point_diff_per_game_proxy",
            },
        ))

    return picks


def _multibook_vig_detector(games: list[dict], min_edge: float) -> list[dict]:
    """Detector 2: cross-book price divergence on spreads and totals."""
    picks: list[dict] = []

    for game in games:
        home_team = game.get("home_team", "")
        away_team = game.get("away_team", "")
        if not _is_future_game(game.get("commence_time", "")):
            continue

        bookmakers = game.get("bookmakers", [])
        if not bookmakers:
            continue

        game_time_cst = _to_cst_str(game.get("commence_time", ""))

        # --- Spreads ---
        by_line: dict = defaultdict(lambda: {"home": [], "away": []})
        for bk in bookmakers:
            bk_key = bk.get("key", "unknown")
            outcomes = bk.get("markets", {}).get("spreads", [])
            home_out = next((o for o in outcomes if o.get("name") == home_team), None)
            away_out = next((o for o in outcomes if o.get("name") == away_team), None)
            if not (home_out and away_out):
                continue
            hp, ho, ao = home_out.get("point"), home_out.get("price"), away_out.get("price")
            if hp is None or ho is None or ao is None:
                continue
            by_line[float(hp)]["home"].append((bk_key, _american_to_implied(int(ho)), int(ho)))
            by_line[float(hp)]["away"].append((bk_key, _american_to_implied(int(ao)), int(ao)))

        for home_point, sides in by_line.items():
            for pick_side, side_probs in [("home", sides["home"]), ("away", sides["away"])]:
                if len(side_probs) < 3:
                    continue
                consensus = float(np.mean([p for _, p, _ in side_probs]))
                for bk_key, bk_prob, bk_odds in side_probs:
                    divergence = bk_prob - consensus
                    if not (divergence < 0 and _MULTIBOOK_PROB_DIVERGENCE <= abs(divergence) < 0.15):
                        continue
                    our_prob = consensus
                    edge_pct = (consensus - bk_prob) * 100
                    if edge_pct < min_edge:
                        continue
                    picks.append(_build_pick(
                        sport=SPORT_LABEL,
                        game=game,
                        game_time_cst=game_time_cst,
                        pick_side=pick_side,
                        pick_type="spread",
                        our_prob=our_prob,
                        market_odds=bk_odds,
                        market_implied=bk_prob,
                        detector="rule_nfl_multibook_vig",
                        features={
                            "flagged_book": bk_key,
                            "divergence_pct": round(abs(divergence) * 100, 2),
                            "books_sampled": len(side_probs),
                            "market_spread_home": home_point,
                        },
                        total_line=None,
                    ))

        # --- Totals ---
        total_probs: list[tuple[str, float, int, int, float]] = []
        for bk in bookmakers:
            bk_key = bk.get("key", "unknown")
            outcomes = bk.get("markets", {}).get("totals", [])
            over_out = next((o for o in outcomes if o.get("name", "").lower() == "over"), None)
            under_out = next((o for o in outcomes if o.get("name", "").lower() == "under"), None)
            if not (over_out and under_out):
                continue
            oo, uo, pt = over_out.get("price"), under_out.get("price"), over_out.get("point")
            if oo is None or uo is None or pt is None:
                continue
            total_probs.append((bk_key, _american_to_implied(int(oo)), int(oo), int(uo), float(pt)))

        if len(total_probs) >= 3:
            consensus = float(np.mean([p for _, p, _, _, _ in total_probs]))
            avg_line = float(np.mean([pt for _, _, _, _, pt in total_probs]))
            for bk_key, bk_prob, over_odds, under_odds, _pt in total_probs:
                divergence = bk_prob - consensus
                if not (divergence < 0 and _MULTIBOOK_PROB_DIVERGENCE <= abs(divergence) < 0.15):
                    continue
                our_prob = consensus
                edge_pct = (consensus - bk_prob) * 100
                if edge_pct < min_edge:
                    continue
                picks.append(_build_pick(
                    sport=SPORT_LABEL,
                    game=game,
                    game_time_cst=game_time_cst,
                    pick_side="over",
                    pick_type="total",
                    our_prob=our_prob,
                    market_odds=over_odds,
                    market_implied=bk_prob,
                    detector="rule_nfl_multibook_vig",
                    features={
                        "flagged_book": bk_key,
                        "divergence_pct": round(abs(divergence) * 100, 2),
                        "books_sampled": len(total_probs),
                    },
                    total_line=round(avg_line, 1),
                ))

    return picks


def rule_based_nfl_edges(min_edge: Optional[float] = None) -> list[dict]:
    """
    Run the rating-overlay and multibook-vig detectors across the current
    NFL slate. Returns [] outside the season window (Odds API simply
    returns no games) or if no power ratings are loaded yet.
    """
    if min_edge is None:
        min_edge = MIN_EDGE_PCT

    try:
        games = fetch_live_odds(SPORT_KEY, markets=["spreads", "totals"])
    except Exception as exc:
        logger.error("[nfl_detector] fetch_live_odds failed: %s", exc)
        return []

    if not games:
        logger.info("[nfl_detector] No NFL games available")
        return []

    ratings = _load_power_ratings(SPORT_LABEL)
    if not ratings:
        logger.warning("[nfl_detector] No NFL power ratings loaded — skipping rating overlay")

    picks: list[dict] = []
    if ratings:
        picks.extend(_rating_overlay_detector(games, ratings, min_edge))
    picks.extend(_multibook_vig_detector(games, min_edge))

    # Deduplicate: same game + side + type -> keep highest edge
    seen: dict[str, dict] = {}
    for pick in picks:
        key = f"{pick['game_id']}_{pick['pick_side']}_{pick['pick_type']}"
        if key not in seen or pick["edge_pct"] > seen[key]["edge_pct"]:
            seen[key] = pick

    result = sorted(seen.values(), key=lambda p: p["edge_pct"], reverse=True)
    logger.info("[nfl_detector] rule_based_nfl_edges — %d pick(s) above %.1f%% edge", len(result), min_edge)
    return result
