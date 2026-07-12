"""
Tennis prediction engine — Wimbledon ATP/WTA multibook vig detector.

Entry point
-----------
rule_based_tennis_edges(min_edge)
    Heuristic-only pipeline — no trained models required.
    One detector:
      Vig-Removed Multi-Book — cross-book moneyline discrepancies.
      For each match, compare each book's player implied probability
      against the consensus.  If one book diverges >= 5%, flag the
      underpriced player as a value bet.

Pick dict schema
----------------
{
  'sport'               : 'tennis_atp' | 'tennis_wta',
  'game_id'             : str,
  'home_team'           : str,   # Player 1 (as labeled by Odds API)
  'away_team'           : str,   # Player 2
  'game_time_cst'       : str,
  'pick_side'           : 'home' | 'away',  # home = Player 1, away = Player 2
  'pick_type'           : 'ml',
  'our_probability'     : float,
  'market_odds'         : int,
  'market_implied_prob' : float,
  'edge_pct'            : float,
  'detector'            : str,
  'features'            : dict,
}

Grading
-------
Tennis picks remain 'pending' until a tennis grader is added.
ESPN tennis endpoint: will be wired in the grader auto-settlement task.
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from pipeline.ingestion.live_odds import fetch_live_odds
from pipeline.config import MIN_EDGE_PCT, now_cst

logger = logging.getLogger(__name__)

SPORT_KEYS = {
    "atp": "tennis_atp_wimbledon",
    "wta": "tennis_wta_wimbledon",
}

# Tennis books are tighter than MLB/WNBA (no home-court effect, lower vig ~5-6%).
# 2% cross-book divergence across 7-10 books is statistically meaningful here.
_MULTIBOOK_PROB_DIVERGENCE = 0.02
_TENNIS_MIN_EDGE = 1.5  # lower floor than MLB's 3% — same logic, tighter market


def _american_to_implied(american_odds: int) -> float:
    if american_odds > 0:
        return 100.0 / (american_odds + 100.0)
    return abs(american_odds) / (abs(american_odds) + 100.0)


def _to_cst_str(iso_str: str) -> str:
    try:
        from datetime import datetime
        import pytz
        cst = pytz.timezone("America/Chicago")
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.astimezone(cst).strftime("%Y-%m-%d %I:%M %p CST")
    except Exception:
        return iso_str


def _build_pick(
    *,
    sport: str,
    game: dict,
    game_time_cst: str,
    pick_side: str,
    our_prob: float,
    market_odds: int,
    market_implied: float,
    features: dict,
) -> dict:
    return {
        "sport": sport,
        "game_id": game.get("game_id", game.get("id", "")),
        "home_team": game.get("home_team", ""),
        "away_team": game.get("away_team", ""),
        "game_time_cst": game_time_cst,
        "pick_side": pick_side,
        "pick_type": "ml",
        "our_probability": round(our_prob, 4),
        "market_odds": market_odds,
        "market_implied_prob": round(market_implied, 4),
        "edge_pct": round((our_prob - market_implied) * 100, 2),
        "detector": "rule_multibook_vig",
        "features": features,
        "total_line": None,  # not applicable for ML picks
    }


def rule_based_tennis_edges(min_edge: Optional[float] = None) -> list[dict]:
    """
    Run multibook vig detector across ATP and WTA Wimbledon matches.

    For each match, for each player:
      - Collect implied probability across all books.
      - If any book's implied prob is >= 5% below consensus (better odds),
        flag that player as a value bet on the ML.

    Sanity guard: skip extreme favourites (consensus > 80% or < 20%)
    since the divergence is less reliable in lopsided matchups.

    Returns list of pick dicts sorted by edge_pct descending.
    """
    if min_edge is None:
        min_edge = _TENNIS_MIN_EDGE

    picks: list[dict] = []

    for tour, sport_key in SPORT_KEYS.items():
        sport_label = f"tennis_{tour}"

        try:
            games = fetch_live_odds(sport_key)
        except Exception as exc:
            logger.error("[tennis_predictor] fetch_live_odds failed for %s: %s", sport_key, exc)
            continue

        if not games:
            logger.info("[tennis_predictor] No %s matches available", sport_key)
            continue

        for game in games:
            player1 = game.get("home_team", "")  # Odds API "home" in tennis
            player2 = game.get("away_team", "")   # Odds API "away" in tennis
            game_time_cst = _to_cst_str(game.get("commence_time", ""))
            bookmakers = game.get("bookmakers", [])

            if not bookmakers:
                continue

            # Collect per-player implied probs across books
            p1_book_probs: list[tuple[str, float, int]] = []
            p2_book_probs: list[tuple[str, float, int]] = []

            for bk in bookmakers:
                bk_key = bk.get("key", "unknown")
                markets_dict = bk.get("markets", {})
                if not isinstance(markets_dict, dict):
                    continue
                outcomes = markets_dict.get("h2h", [])
                if not outcomes:
                    continue

                # Outcomes are keyed by player name
                p1_out = next(
                    (o for o in outcomes if o.get("name") == player1), None
                )
                p2_out = next(
                    (o for o in outcomes if o.get("name") == player2), None
                )

                if p1_out and p2_out:
                    p1_odds = p1_out.get("price", 0)
                    p2_odds = p2_out.get("price", 0)
                    if p1_odds and p2_odds:
                        p1_ip = _american_to_implied(int(p1_odds))
                        p2_ip = _american_to_implied(int(p2_odds))
                        p1_book_probs.append((bk_key, p1_ip, int(p1_odds)))
                        p2_book_probs.append((bk_key, p2_ip, int(p2_odds)))

            # Apply divergence check for each player side
            for pick_side, side_probs, player_name in [
                ("home", p1_book_probs, player1),
                ("away", p2_book_probs, player2),
            ]:
                if len(side_probs) < 3:
                    continue

                all_probs = [p for _, p, _ in side_probs]
                consensus = float(np.mean(all_probs))

                # Skip extreme favourites — consensus outside 20%-80%
                if not (0.20 <= consensus <= 0.80):
                    continue

                for bk_key, bk_prob, bk_odds in side_probs:
                    divergence = bk_prob - consensus
                    if (
                        divergence < 0
                        and abs(divergence) >= _MULTIBOOK_PROB_DIVERGENCE
                        and abs(divergence) < 0.15
                    ):
                        our_prob = consensus
                        edge_pct = (consensus - bk_prob) * 100

                        if edge_pct >= min_edge:
                            picks.append(_build_pick(
                                sport=sport_label,
                                game=game,
                                game_time_cst=game_time_cst,
                                pick_side=pick_side,
                                our_prob=our_prob,
                                market_odds=bk_odds,
                                market_implied=bk_prob,
                                features={
                                    "player": player_name,
                                    "flagged_book": bk_key,
                                    "book_implied_prob": round(bk_prob, 4),
                                    "consensus_prob": round(consensus, 4),
                                    "divergence_pct": round(abs(divergence) * 100, 2),
                                    "books_sampled": len(side_probs),
                                    "tour": tour.upper(),
                                    "tournament": "wimbledon",
                                },
                            ))

    # Deduplicate: same match + side → keep highest edge
    seen: dict[str, dict] = {}
    for pick in picks:
        key = f"{pick['game_id']}_{pick['pick_side']}"
        if key not in seen or pick["edge_pct"] > seen[key]["edge_pct"]:
            seen[key] = pick

    result = sorted(seen.values(), key=lambda p: p["edge_pct"], reverse=True)
    logger.info(
        "[tennis_predictor] rule_based_tennis_edges — %d pick(s) above %.1f%% edge",
        len(result), min_edge,
    )
    return result
