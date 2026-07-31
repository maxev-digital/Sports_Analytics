"""
NCAAF prediction engine — SP+ overlay + multibook vig detectors.

Entry point
-----------
rule_based_ncaaf_edges(min_edge)
    Three detectors, no trained model required:

    1. SP+ Rating Overlay (ATS) — compares each team's SP+ overall rating
       (see ``pipeline/ingestion/team_ratings_ingestion.py``) against the
       market spread. Thresholds (15pt SP+ gap, 7pt max spread) match the
       original task spec starting point.
    2. SP+ Totals Projection — unlike NFL (only a single power-rating
       proxy), SP+ gives offense/defense splits: projected total =
       (home_offense - away_defense) + (away_offense - home_defense).
       Flags value when the projection diverges from the market total
       by more than 4 points.
    3. Multibook Vig (ATS + totals) — same cross-book divergence
       technique used by ``mlb_predictor.py`` / ``nfl_detector.py``.

Pick dict schema: identical to nfl_detector.py, sport='ncaaf'.
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

SPORT_KEY = "americanfootball_ncaaf"
SPORT_LABEL = "ncaaf"

_ATS_MIN_SP_GAP = 15.0
_ATS_MAX_SPREAD_FOR_VALUE = 7.0
_SP_POINT_TO_PROB = 0.015  # ~1.5% cover-prob shift per point of SP+ gap (heuristic)
_TOTALS_MIN_DIFF = 4.0

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


def _load_sp_ratings(sport: str) -> dict[str, dict]:
    rows = execute_query(
        """SELECT team, sp_rating, sp_offense, sp_defense
           FROM team_ratings WHERE sport = %s AND sp_rating IS NOT NULL""",
        (sport,),
    )
    return {
        r["team"]: {
            "overall": float(r["sp_rating"]),
            "offense": float(r["sp_offense"]) if r["sp_offense"] is not None else None,
            "defense": float(r["sp_defense"]) if r["sp_defense"] is not None else None,
        }
        for r in rows
    }


def _build_pick(
    *,
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
        "sport": SPORT_LABEL,
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


def _spread_lines_by_point(game: dict, home_team: str, away_team: str) -> dict:
    by_line: dict = defaultdict(lambda: {"home": [], "away": []})
    for bk in game.get("bookmakers", []):
        bk_key = bk.get("key", "unknown")
        outcomes = bk.get("markets", {}).get("spreads", [])
        home_out = next((o for o in outcomes if o.get("name") == home_team), None)
        away_out = next((o for o in outcomes if o.get("name") == away_team), None)
        if not (home_out and away_out):
            continue
        hp, ho, ao = home_out.get("point"), home_out.get("price"), away_out.get("price")
        if hp is None or ho is None or ao is None:
            continue
        by_line[float(hp)]["home"].append((bk_key, int(ho)))
        by_line[float(hp)]["away"].append((bk_key, int(ao)))
    return by_line


def _sp_rating_overlay_detector(
    games: list[dict], ratings: dict[str, dict], min_edge: float
) -> list[dict]:
    """Detector 1: SP+ overall rating gap vs market spread (ATS)."""
    picks: list[dict] = []

    for game in games:
        home_team, away_team = game.get("home_team", ""), game.get("away_team", "")
        if not _is_future_game(game.get("commence_time", "")):
            continue

        home_r, away_r = ratings.get(home_team), ratings.get(away_team)
        if home_r is None or away_r is None:
            continue

        by_line = _spread_lines_by_point(game, home_team, away_team)
        if not by_line:
            continue

        market_home_point = max(by_line, key=lambda p: len(by_line[p]["home"]))
        home_prices = by_line[market_home_point]["home"]
        away_prices = by_line[market_home_point]["away"]
        books_sampled = len(home_prices)
        if books_sampled < 3 or abs(market_home_point) >= _ATS_MAX_SPREAD_FOR_VALUE:
            continue

        expected_margin_home = home_r["overall"] - away_r["overall"]
        market_margin_home = -market_home_point
        gap = expected_margin_home - market_margin_home

        if abs(gap) < _ATS_MIN_SP_GAP:
            continue

        pick_side = "home" if gap > 0 else "away"
        side_prices = home_prices if pick_side == "home" else away_prices
        avg_price = round(sum(p for _, p in side_prices) / len(side_prices))
        best_price = max(p for _, p in side_prices)

        implied_prices = [_american_to_implied(p) for _, p in side_prices]
        consensus_ip = float(np.mean(implied_prices))
        best_ip = _american_to_implied(best_price)
        divergence_pct = round(abs(consensus_ip - best_ip) * 100, 2)

        market_implied = _american_to_implied(avg_price)
        prob_shift = min(abs(gap) * _SP_POINT_TO_PROB, 0.15)
        our_prob = min(market_implied + prob_shift, 0.85)
        edge_pct = (our_prob - market_implied) * 100

        if edge_pct < min_edge:
            continue

        picks.append(_build_pick(
            game=game,
            game_time_cst=_to_cst_str(game.get("commence_time", "")),
            pick_side=pick_side,
            pick_type="spread",
            our_prob=our_prob,
            market_odds=avg_price,
            market_implied=market_implied,
            detector="rule_ncaaf_sp_overlay",
            features={
                "home_sp_rating": round(home_r["overall"], 2),
                "away_sp_rating": round(away_r["overall"], 2),
                "sp_gap": round(gap, 2),
                "market_spread_home": market_home_point,
                "books_sampled": books_sampled,
                "divergence_pct": divergence_pct,
            },
        ))

    return picks


def _sp_totals_detector(
    games: list[dict], ratings: dict[str, dict], min_edge: float
) -> list[dict]:
    """Detector 2: SP+ offense/defense projected total vs market total."""
    picks: list[dict] = []

    for game in games:
        home_team, away_team = game.get("home_team", ""), game.get("away_team", "")
        if not _is_future_game(game.get("commence_time", "")):
            continue

        home_r, away_r = ratings.get(home_team), ratings.get(away_team)
        if home_r is None or away_r is None:
            continue
        if None in (home_r["offense"], home_r["defense"], away_r["offense"], away_r["defense"]):
            continue

        total_probs: list[tuple[str, float, int, int, float]] = []
        for bk in game.get("bookmakers", []):
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

        if len(total_probs) < 3:
            continue

        market_line = float(np.mean([pt for _, _, _, _, pt in total_probs]))

        # SP+ ratings are points-above-average; a simple points projection
        # anchors both teams' expected output around a shared FBS baseline
        # (~28 pts/team) adjusted by each side's offense-vs-opponent-defense
        # differential. This is a starting-point heuristic, not a calibrated
        # scoring model - tune against historical results once loaded.
        _BASELINE_PTS = 28.0
        home_pts = _BASELINE_PTS + home_r["offense"] - away_r["defense"]
        away_pts = _BASELINE_PTS + away_r["offense"] - home_r["defense"]
        projected_total = home_pts + away_pts

        diff = projected_total - market_line
        if abs(diff) < _TOTALS_MIN_DIFF:
            continue

        pick_side = "over" if diff > 0 else "under"
        avg_price = round(
            sum(oo if pick_side == "over" else uo for _, _, oo, uo, _ in total_probs)
            / len(total_probs)
        )
        market_implied = _american_to_implied(avg_price)

        prob_shift = min(abs(diff) * 0.02, 0.15)
        our_prob = min(market_implied + prob_shift, 0.85)
        edge_pct = (our_prob - market_implied) * 100
        if edge_pct < min_edge:
            continue

        picks.append(_build_pick(
            game=game,
            game_time_cst=_to_cst_str(game.get("commence_time", "")),
            pick_side=pick_side,
            pick_type="total",
            our_prob=our_prob,
            market_odds=avg_price,
            market_implied=market_implied,
            detector="rule_ncaaf_sp_totals",
            features={
                "home_sp_offense": round(home_r["offense"], 2),
                "home_sp_defense": round(home_r["defense"], 2),
                "away_sp_offense": round(away_r["offense"], 2),
                "away_sp_defense": round(away_r["defense"], 2),
                "projected_total": round(projected_total, 1),
                "market_total": round(market_line, 1),
                "books_sampled": len(total_probs),
                "divergence_pct": round(abs(diff) / market_line * 100, 2) if market_line else 0.0,
            },
            total_line=round(market_line, 1),
        ))

    return picks


def _multibook_vig_detector(games: list[dict], min_edge: float) -> list[dict]:
    """Detector 3: cross-book price divergence on spreads and totals."""
    picks: list[dict] = []

    for game in games:
        home_team, away_team = game.get("home_team", ""), game.get("away_team", "")
        if not _is_future_game(game.get("commence_time", "")):
            continue
        if not game.get("bookmakers"):
            continue

        game_time_cst = _to_cst_str(game.get("commence_time", ""))
        by_line = _spread_lines_by_point(game, home_team, away_team)

        for home_point, sides in by_line.items():
            for pick_side, side_probs_raw in [("home", sides["home"]), ("away", sides["away"])]:
                side_probs = [(bk, _american_to_implied(p), p) for bk, p in side_probs_raw]
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
                        game=game,
                        game_time_cst=game_time_cst,
                        pick_side=pick_side,
                        pick_type="spread",
                        our_prob=our_prob,
                        market_odds=bk_odds,
                        market_implied=bk_prob,
                        detector="rule_ncaaf_multibook_vig",
                        features={
                            "flagged_book": bk_key,
                            "divergence_pct": round(abs(divergence) * 100, 2),
                            "books_sampled": len(side_probs),
                            "market_spread_home": home_point,
                        },
                    ))

    return picks


def rule_based_ncaaf_edges(min_edge: Optional[float] = None) -> list[dict]:
    """
    Run the SP+ overlay, SP+ totals, and multibook-vig detectors across
    the current NCAAF slate. Returns [] outside the season window or if
    no SP+ ratings are loaded yet (requires CFBD_API_KEY - see
    ``pipeline/ingestion/team_ratings_ingestion.py``).
    """
    if min_edge is None:
        min_edge = MIN_EDGE_PCT

    try:
        games = fetch_live_odds(SPORT_KEY, markets=["spreads", "totals"])
    except Exception as exc:
        logger.error("[ncaaf_detector] fetch_live_odds failed: %s", exc)
        return []

    if not games:
        logger.info("[ncaaf_detector] No NCAAF games available")
        return []

    ratings = _load_sp_ratings(SPORT_LABEL)
    if not ratings:
        logger.warning("[ncaaf_detector] No NCAAF SP+ ratings loaded — skipping SP+ detectors")

    picks: list[dict] = []
    if ratings:
        picks.extend(_sp_rating_overlay_detector(games, ratings, min_edge))
        picks.extend(_sp_totals_detector(games, ratings, min_edge))
    picks.extend(_multibook_vig_detector(games, min_edge))

    seen: dict[str, dict] = {}
    for pick in picks:
        key = f"{pick['game_id']}_{pick['pick_side']}_{pick['pick_type']}"
        if key not in seen or pick["edge_pct"] > seen[key]["edge_pct"]:
            seen[key] = pick

    result = sorted(seen.values(), key=lambda p: p["edge_pct"], reverse=True)
    logger.info("[ncaaf_detector] rule_based_ncaaf_edges — %d pick(s) above %.1f%% edge", len(result), min_edge)
    return result
