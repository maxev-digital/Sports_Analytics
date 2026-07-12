"""
Soccer prediction engine — MLS + EPL multibook vig detector.

Entry point
-----------
rule_based_soccer_edges(min_edge)
    Two detectors per game:
      Detector A — Totals (Over/Under goals)
        Same multibook vig pattern as MLB totals.
        Lines are 2.5 in soccer (most books).
      Detector B — Moneyline (3-way: Home / Draw / Away)
        Soccer h2h has three outcomes; each is checked independently.
        implied prob = 1 / (1 + 100/|odds|) — same American formula.

Pick dict schema
----------------
{
  'sport'               : 'soccer_mls' | 'soccer_epl',
  'game_id'             : str,
  'home_team'           : str,
  'away_team'           : str,
  'game_time_cst'       : str,
  'pick_side'           : 'over'|'under'|'home'|'away'|'draw',
  'pick_type'           : 'total' | 'ml',
  'our_probability'     : float,
  'market_odds'         : int,
  'market_implied_prob' : float,
  'edge_pct'            : float,
  'total_line'          : float | None,  # goals line for totals picks
  'detector'            : str,
  'features'            : dict,
}

Grading
-------
Soccer grader will use ESPN soccer scoreboards (task #35).
Picks remain 'pending' until grader is wired in.

Time window
-----------
Only processes games within HOURS_AHEAD of current time to avoid
acting on stale opening-week odds that will shift before bet placement.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import numpy as np

from pipeline.ingestion.live_odds import fetch_live_odds
from pipeline.config import now_cst, CST

logger = logging.getLogger(__name__)

SPORT_KEYS = {
    "mls": "soccer_usa_mls",
    "epl": "soccer_epl",
}

HOURS_AHEAD = 48  # only flag games starting within 48 hours

_MULTIBOOK_PROB_DIVERGENCE = 0.04  # 4% off consensus — between tennis (2%) and MLB (5%)
_SOCCER_MIN_EDGE = 2.0             # 2% floor

# Minimum books required — soccer books can be fewer than MLB
_MIN_BOOKS = 3


def _american_to_implied(american_odds: int) -> float:
    if american_odds > 0:
        return 100.0 / (american_odds + 100.0)
    return abs(american_odds) / (abs(american_odds) + 100.0)


def _to_cst_str(iso_str: str) -> str:
    try:
        cst = CST
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.astimezone(cst).strftime("%Y-%m-%d %I:%M %p CST")
    except Exception:
        return iso_str


def _within_window(commence_time: str) -> bool:
    """Return True if the game starts within HOURS_AHEAD from now."""
    try:
        dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = dt - now
        return timedelta(0) <= delta <= timedelta(hours=HOURS_AHEAD)
    except Exception:
        return True  # if we can't parse, include it


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
    total_line: Optional[float],
    features: dict,
) -> dict:
    return {
        "sport": sport,
        "game_id": game.get("game_id", game.get("id", "")),
        "home_team": game.get("home_team", ""),
        "away_team": game.get("away_team", ""),
        "game_time_cst": game_time_cst,
        "pick_side": pick_side,
        "pick_type": pick_type,
        "our_probability": round(our_prob, 4),
        "market_odds": market_odds,
        "market_implied_prob": round(market_implied, 4),
        "edge_pct": round((our_prob - market_implied) * 100, 2),
        "total_line": total_line,
        "detector": "rule_multibook_vig",
        "features": features,
    }


def rule_based_soccer_edges(min_edge: Optional[float] = None) -> list[dict]:
    """
    Run multibook vig detectors across MLS and EPL games within 48h.

    Returns list of pick dicts sorted by edge_pct descending.
    Generates 0 picks when no same-window games have enough books
    (e.g., off-season or early posting with 1 book).
    """
    if min_edge is None:
        min_edge = _SOCCER_MIN_EDGE

    picks: list[dict] = []

    for league, sport_key in SPORT_KEYS.items():
        sport_label = f"soccer_{league}"

        try:
            games = fetch_live_odds(sport_key)
        except Exception as exc:
            logger.error("[soccer_predictor] fetch_live_odds failed for %s: %s", sport_key, exc)
            continue

        if not games:
            logger.info("[soccer_predictor] No %s games available", sport_key)
            continue

        windowed = [g for g in games if _within_window(g.get("commence_time", ""))]
        logger.info("[soccer_predictor] %s: %d/%d games in %dh window",
                    league.upper(), len(windowed), len(games), HOURS_AHEAD)

        for game in windowed:
            home_team = game.get("home_team", "")
            away_team = game.get("away_team", "")
            game_time_cst = _to_cst_str(game.get("commence_time", ""))
            bookmakers = game.get("bookmakers", [])

            _detect_totals(picks, sport_label, game, game_time_cst, bookmakers,
                           home_team, away_team, min_edge)
            _detect_ml_3way(picks, sport_label, game, game_time_cst, bookmakers,
                            home_team, away_team, min_edge)

    # Deduplicate: same game + side → keep highest edge
    seen: dict[str, dict] = {}
    for pick in picks:
        key = f"{pick['game_id']}_{pick['pick_side']}_{pick['pick_type']}"
        if key not in seen or pick["edge_pct"] > seen[key]["edge_pct"]:
            seen[key] = pick

    result = sorted(seen.values(), key=lambda p: p["edge_pct"], reverse=True)
    logger.info(
        "[soccer_predictor] rule_based_soccer_edges — %d pick(s) above %.1f%% edge",
        len(result), min_edge,
    )
    return result


def _detect_totals(
    picks: list, sport: str, game: dict, game_time_cst: str,
    bookmakers: list, home_team: str, away_team: str, min_edge: float,
) -> None:
    """Totals (Over/Under goals) multibook vig detector."""
    try:
        by_line: dict[float, dict] = {}

        for bk in bookmakers:
            bk_key = bk.get("key", "unknown")
            markets_dict = bk.get("markets", {})
            if not isinstance(markets_dict, dict):
                continue
            outcomes = markets_dict.get("totals", [])
            if not outcomes:
                continue
            over_out  = next((o for o in outcomes if o.get("name") == "Over"), None)
            under_out = next((o for o in outcomes if o.get("name") == "Under"), None)
            if not (over_out and under_out):
                continue
            over_odds  = over_out.get("price", 0)
            under_odds = under_out.get("price", 0)
            point = over_out.get("point")
            if not (over_odds and under_odds and point is not None):
                continue
            try:
                point = float(point)
            except (TypeError, ValueError):
                continue
            if point not in by_line:
                by_line[point] = {"over": [], "under": []}
            by_line[point]["over"].append((bk_key, _american_to_implied(int(over_odds)), int(over_odds)))
            by_line[point]["under"].append((bk_key, _american_to_implied(int(under_odds)), int(under_odds)))

        for line, sides in by_line.items():
            for pick_side, side_probs in [("over", sides["over"]), ("under", sides["under"])]:
                if len(side_probs) < _MIN_BOOKS:
                    continue
                all_probs = [p for _, p, _ in side_probs]
                consensus = float(np.mean(all_probs))
                if not (0.20 <= consensus <= 0.80):
                    continue
                for bk_key, bk_prob, bk_odds in side_probs:
                    divergence = bk_prob - consensus
                    if (divergence < 0
                            and abs(divergence) >= _MULTIBOOK_PROB_DIVERGENCE
                            and abs(divergence) < 0.15):
                        edge_pct = (consensus - bk_prob) * 100
                        if edge_pct >= min_edge:
                            picks.append(_build_pick(
                                sport=sport, game=game, game_time_cst=game_time_cst,
                                pick_side=pick_side, pick_type="total",
                                our_prob=consensus, market_odds=bk_odds,
                                market_implied=bk_prob, total_line=line,
                                features={
                                    "flagged_book": bk_key,
                                    "book_implied_prob": round(bk_prob, 4),
                                    "consensus_prob": round(consensus, 4),
                                    "divergence_pct": round(abs(divergence) * 100, 2),
                                    "total_line": line,
                                    "market": "totals",
                                    "books_sampled": len(side_probs),
                                },
                            ))
    except Exception as exc:
        logger.warning("[soccer_predictor] Totals detector failed for %s @ %s: %s",
                       away_team, home_team, exc)


def _detect_ml_3way(
    picks: list, sport: str, game: dict, game_time_cst: str,
    bookmakers: list, home_team: str, away_team: str, min_edge: float,
) -> None:
    """
    Moneyline 3-way (Home / Draw / Away) multibook vig detector.
    Soccer h2h has a draw outcome — handle all three sides independently.
    """
    try:
        # sides: (pick_side_name, outcome_name_in_api)
        # The Odds API uses team names for home/away and "Draw" for the draw
        sides_map = [
            ("home", home_team),
            ("away", away_team),
            ("draw", "Draw"),
        ]
        side_probs: dict[str, list[tuple[str, float, int]]] = {
            "home": [], "away": [], "draw": []
        }

        for bk in bookmakers:
            bk_key = bk.get("key", "unknown")
            markets_dict = bk.get("markets", {})
            if not isinstance(markets_dict, dict):
                continue
            outcomes = markets_dict.get("h2h", [])
            if not outcomes:
                continue

            for pick_side, outcome_name in sides_map:
                out = next((o for o in outcomes if o.get("name") == outcome_name), None)
                if out:
                    odds = out.get("price", 0)
                    if odds:
                        ip = _american_to_implied(int(odds))
                        side_probs[pick_side].append((bk_key, ip, int(odds)))

        for pick_side, probs in side_probs.items():
            if len(probs) < _MIN_BOOKS:
                continue
            all_p = [p for _, p, _ in probs]
            consensus = float(np.mean(all_p))
            # Draw probability is naturally lower — allow 10%-80% range for draw
            min_prob = 0.10 if pick_side == "draw" else 0.20
            if not (min_prob <= consensus <= 0.80):
                continue
            for bk_key, bk_prob, bk_odds in probs:
                divergence = bk_prob - consensus
                if (divergence < 0
                        and abs(divergence) >= _MULTIBOOK_PROB_DIVERGENCE
                        and abs(divergence) < 0.15):
                    edge_pct = (consensus - bk_prob) * 100
                    if edge_pct >= min_edge:
                        picks.append(_build_pick(
                            sport=sport, game=game, game_time_cst=game_time_cst,
                            pick_side=pick_side, pick_type="ml",
                            our_prob=consensus, market_odds=bk_odds,
                            market_implied=bk_prob, total_line=None,
                            features={
                                "flagged_book": bk_key,
                                "book_implied_prob": round(bk_prob, 4),
                                "consensus_prob": round(consensus, 4),
                                "divergence_pct": round(abs(divergence) * 100, 2),
                                "market": "h2h",
                                "books_sampled": len(probs),
                            },
                        ))
    except Exception as exc:
        logger.warning("[soccer_predictor] H2H 3-way detector failed for %s @ %s: %s",
                       away_team, home_team, exc)
