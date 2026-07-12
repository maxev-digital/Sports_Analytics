"""
MLB prediction engine — generates today's picks from live odds + Statcast data.

Two entry points
----------------
generate_mlb_picks(min_edge)
    Full ML pipeline: loads trained models, fetches live odds, builds feature
    vectors, runs ensemble inference, filters by edge threshold.

rule_based_mlb_edges(min_edge)
    Heuristic-only pipeline — works before any model training is done.
    Three detectors:
      1. Pitching Luck  (total)  — ERA vs xERA regression
      2. Lineup Regression (ML) — xwOBA vs wOBA underperformers at juicy prices
      3. Vig-Removed Multi-Book  — cross-book line discrepancies

Pick dict schema (both functions return this structure)
-------------------------------------------------------
{
  'sport'               : 'mlb',
  'game_id'             : str,
  'home_team'           : str,
  'away_team'           : str,
  'game_time_cst'       : str,
  'pick_side'           : 'over'|'under'|'home'|'away',
  'pick_type'           : 'total'|'ml'|'spread'|'props',
  'our_probability'     : float,
  'market_odds'         : int,
  'market_implied_prob' : float,
  'edge_pct'            : float,
  'detector'            : str,
  'features'            : dict,
}
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from pipeline.ingestion.mlb_statcast import (
    get_pitcher_stats,
    fetch_pitching_statcast,
    fetch_batting_statcast,
)
from pipeline.ingestion.live_odds import (
    fetch_live_odds,
    extract_consensus_line,
    remove_vig,
)
from pipeline.models.features.mlb_features import build_game_features, MLB_FEATURE_COLUMNS
from pipeline.models.training.mlb_trainer import load_mlb_models, get_ensemble_probability
from pipeline.config import MIN_EDGE_PCT, MIN_CONFIDENCE, now_cst

logger = logging.getLogger(__name__)

SPORT_KEY = "baseball_mlb"

# Detector thresholds
_PITCHING_LUCK_OVER_THRESHOLD = 1.2   # combined xERA gap → lean over
_PITCHING_LUCK_UNDER_THRESHOLD = -1.0  # combined xERA gap → lean under
_XWOBA_REGRESSION_MIN = 0.030          # min xwOBA - wOBA delta to flag
_LINEUP_ML_MAX_PRICE = 150             # team must be ≥ +150 to be interesting
_MULTIBOOK_PROB_DIVERGENCE = 0.05      # 5% off consensus = flaggable


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _american_to_implied(american_odds: int) -> float:
    """Convert American moneyline to raw implied probability (vig included)."""
    if american_odds > 0:
        return 100.0 / (american_odds + 100.0)
    else:
        return abs(american_odds) / (abs(american_odds) + 100.0)


def _fair_prob_from_vig_removal(odds_side: int, odds_other: int) -> float:
    """
    Use remove_vig() when available; fall back to simple Shin-approximation
    if the import fails or returns unexpected data.

    Returns the fair (vig-free) probability for odds_side.
    """
    try:
        result = remove_vig(odds_side, odds_other)
        return float(result.get("side1", _shin_fair_prob(odds_side, odds_other)))
    except Exception:
        return _shin_fair_prob(odds_side, odds_other)


def _shin_fair_prob(odds_side: int, odds_other: int) -> float:
    """Shin method vig removal (simple two-outcome market)."""
    p1_raw = _american_to_implied(odds_side)
    p2_raw = _american_to_implied(odds_other)
    total = p1_raw + p2_raw
    return p1_raw / total


def _to_cst_str(iso_str: str) -> str:
    """Convert ISO 8601 UTC string to human-readable CST datetime string."""
    try:
        from datetime import datetime
        import pytz
        cst = pytz.timezone("America/Chicago")
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.astimezone(cst).strftime("%Y-%m-%d %I:%M %p CST")
    except Exception:
        return iso_str


def _safe_pitcher_stats(name: Optional[str], label: str) -> dict:
    """Fetch pitcher stats, returning {} on any failure."""
    if not name:
        return {}
    try:
        stats = get_pitcher_stats(name)
        return stats or {}
    except Exception as exc:
        logger.warning("[mlb_predictor] %s SP stats unavailable (%s): %s", label, name, exc)
        return {}


def _safe_batting_stats(team: str) -> dict:
    """Return team-level woba/xwoba aggregated from Statcast batting data.
    Returns {} if the team cannot be found or data is unavailable.
    """
    try:
        df = fetch_batting_statcast()  # no season arg = current season
        if df.empty or "team" not in df.columns:
            return {}
        team_df = df[df["team"].str.upper() == team.upper()]
        if team_df.empty:
            return {}
        agg: dict = {}
        if "woba" in team_df.columns:
            agg["woba"] = float(team_df["woba"].mean())
        if "xwoba" in team_df.columns:
            agg["xwoba"] = float(team_df["xwoba"].mean())
        if "slg" in team_df.columns:
            agg["slg"] = float(team_df["slg"].mean())
        return agg
    except Exception as exc:
        logger.debug("[mlb_predictor] Batting stats unavailable for %s: %s", team, exc)
        return {}


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
) -> dict:
    """Assemble a standardised pick dict."""
    return {
        "sport": "mlb",
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
        "detector": detector,
        "features": features,
        "total_line": features.get("total_line"),
    }


# ---------------------------------------------------------------------------
# Feature building (wraps pipeline.models.features.mlb_features)
# ---------------------------------------------------------------------------

def _build_features_for_game(
    game: dict,
    home_sp: dict,
    away_sp: dict,
    home_batting: dict,
    away_batting: dict,
    total_line: Optional[float],
    home_ml: Optional[int],
    away_ml: Optional[int],
) -> Optional[pd.Series]:
    """
    Call build_game_features() with all available data.  Returns None if the
    feature builder itself raises (e.g. missing critical fields).
    """
    try:
        features = build_game_features(
            home_team=game.get("home_team", ""),
            away_team=game.get("away_team", ""),
            home_sp_stats=home_sp,
            away_sp_stats=away_sp,
            home_batting=home_batting,
            away_batting=away_batting,
            total_line=total_line,
            home_ml=home_ml,
            away_ml=away_ml,
        )
        return features
    except Exception as exc:
        logger.warning(
            "[mlb_predictor] build_game_features failed for %s vs %s: %s",
            game.get("away_team"), game.get("home_team"), exc,
        )
        return None


# ---------------------------------------------------------------------------
# generate_mlb_picks — full ML pipeline
# ---------------------------------------------------------------------------

def generate_mlb_picks(min_edge: Optional[float] = None) -> list[dict]:
    """
    Generate today's MLB picks using the trained ensemble models.

    For each game the function attempts two markets:
      - Totals  (over/under)  → loaded from mlb_total models
      - Moneyline (home/away) → loaded from mlb_ml models

    If no models are saved yet the function falls back to rule_based_mlb_edges.

    Parameters
    ----------
    min_edge : float, optional
        Minimum edge percentage to include a pick. Defaults to MIN_EDGE_PCT
        from pipeline.config (typically 3.0).

    Returns
    -------
    list of pick dicts sorted by edge_pct descending
    """
    if min_edge is None:
        min_edge = MIN_EDGE_PCT

    # Load models for both markets
    total_models = load_mlb_models("total")
    ml_models = load_mlb_models("ml")

    if not total_models and not ml_models:
        logger.warning(
            "[mlb_predictor] No saved models found — falling back to rule-based"
        )
        return rule_based_mlb_edges(min_edge)

    # Fetch today's live MLB odds
    try:
        games = fetch_live_odds(SPORT_KEY)
    except Exception as exc:
        logger.error("[mlb_predictor] fetch_live_odds failed: %s", exc)
        return []

    if not games:
        logger.info("[mlb_predictor] No MLB games returned from odds API")
        return []

    picks: list[dict] = []

    for game in games:
        home_team = game.get("home_team", "")
        away_team = game.get("away_team", "")
        game_time_cst = _to_cst_str(game.get("commence_time", ""))
        bookmakers = game.get("bookmakers", [])

        # Fetch pitcher stats — degrade gracefully if unavailable
        home_sp_name = game.get("home_starter") or game.get("home_sp")
        away_sp_name = game.get("away_starter") or game.get("away_sp")
        home_sp = _safe_pitcher_stats(home_sp_name, "home")
        away_sp = _safe_pitcher_stats(away_sp_name, "away")

        # Team batting Statcast
        home_batting = _safe_batting_stats(home_team)
        away_batting = _safe_batting_stats(away_team)

        # ── TOTALS market ──────────────────────────────────────────────────
        if total_models:
            try:
                total_data = extract_consensus_line(game, "totals")
                if total_data:
                    total_line = total_data.get("point")
                    over_odds = total_data.get("over_odds")
                    under_odds = total_data.get("under_odds")

                    if total_line and over_odds and under_odds:
                        fair_over = _fair_prob_from_vig_removal(over_odds, under_odds)

                        features = _build_features_for_game(
                            game, home_sp, away_sp,
                            home_batting, away_batting,
                            total_line=float(total_line),
                            home_ml=None, away_ml=None,
                        )

                        if features is not None:
                            ensemble = get_ensemble_probability(total_models, features)
                            our_over_prob = ensemble["ensemble_mean"]

                            if our_over_prob >= 0.5:
                                pick_side = "over"
                                our_prob = our_over_prob
                                market_implied = fair_over
                                market_odds = int(over_odds)
                            else:
                                pick_side = "under"
                                our_prob = 1.0 - our_over_prob
                                market_implied = 1.0 - fair_over
                                market_odds = int(under_odds)

                            edge_pct = (our_prob - market_implied) * 100

                            if edge_pct >= min_edge:
                                picks.append(_build_pick(
                                    game=game,
                                    game_time_cst=game_time_cst,
                                    pick_side=pick_side,
                                    pick_type="total",
                                    our_prob=our_prob,
                                    market_odds=market_odds,
                                    market_implied=market_implied,
                                    detector="mlb_ensemble_total",
                                    features=features.to_dict(),
                                ))
            except Exception as exc:
                logger.warning(
                    "[mlb_predictor] Total market failed for %s @ %s: %s",
                    away_team, home_team, exc,
                )

        # ── ML (h2h) market ────────────────────────────────────────────────
        if ml_models:
            try:
                ml_data = extract_consensus_line(game, "h2h")
                if ml_data:
                    home_ml = ml_data.get("home_odds")
                    away_ml = ml_data.get("away_odds")

                    if home_ml and away_ml:
                        fair_home = _fair_prob_from_vig_removal(home_ml, away_ml)

                        features = _build_features_for_game(
                            game, home_sp, away_sp,
                            home_batting, away_batting,
                            total_line=None,
                            home_ml=int(home_ml),
                            away_ml=int(away_ml),
                        )

                        if features is not None:
                            ensemble = get_ensemble_probability(ml_models, features)
                            our_home_prob = ensemble["ensemble_mean"]

                            if our_home_prob >= 0.5:
                                pick_side = "home"
                                our_prob = our_home_prob
                                market_implied = fair_home
                                market_odds = int(home_ml)
                            else:
                                pick_side = "away"
                                our_prob = 1.0 - our_home_prob
                                market_implied = 1.0 - fair_home
                                market_odds = int(away_ml)

                            edge_pct = (our_prob - market_implied) * 100

                            if edge_pct >= min_edge:
                                picks.append(_build_pick(
                                    game=game,
                                    game_time_cst=game_time_cst,
                                    pick_side=pick_side,
                                    pick_type="ml",
                                    our_prob=our_prob,
                                    market_odds=market_odds,
                                    market_implied=market_implied,
                                    detector="mlb_ensemble_ml",
                                    features=features.to_dict(),
                                ))
            except Exception as exc:
                logger.warning(
                    "[mlb_predictor] ML market failed for %s @ %s: %s",
                    away_team, home_team, exc,
                )

    picks.sort(key=lambda p: p["edge_pct"], reverse=True)
    logger.info(
        "[mlb_predictor] generate_mlb_picks complete — %d pick(s) above %.1f%% edge",
        len(picks), min_edge,
    )
    return picks


# ---------------------------------------------------------------------------
# rule_based_mlb_edges — heuristic-only, no ML models required
# ---------------------------------------------------------------------------

def rule_based_mlb_edges(min_edge: float = 3.0) -> list[dict]:
    """
    Run three rule-based edge detectors against today's MLB slate.

    Requires live odds and Statcast data but NOT trained ML models.

    Detector 1 — Pitching Luck (total market)
        For each SP compute xERA_gap = xERA - ERA.
        Positive = pitcher ERA is below xERA = got lucky = regression means
        more runs allowed going forward.

        Combined gap (home + away):
          > +1.2 → lean OVER  (both pitchers have been lucky; regression = runs)
          < -1.0 → lean UNDER (both pitchers have been unlucky; regression = fewer runs)

    Detector 2 — Lineup Regression (moneyline market)
        xwOBA - wOBA > 0.030 means a team hits the ball much better than
        their results show (underperforming on balls in play).  If their
        moneyline is +150 or worse, there may be value on them.

    Detector 3 — Vig-Removed Multi-Book discrepancy (any market)
        Across all bookmakers for h2h, totals, and spreads, compute the
        consensus implied probability.  If any single book's implied prob
        differs from the consensus by >= 5%, flag it as a potential edge.

    Parameters
    ----------
    min_edge : float
        Minimum edge percentage (default 3.0 %).

    Returns
    -------
    list of pick dicts (same schema as generate_mlb_picks)
    """
    picks: list[dict] = []

    try:
        games = fetch_live_odds(SPORT_KEY)
    except Exception as exc:
        logger.error("[mlb_predictor] fetch_live_odds failed in rule-based: %s", exc)
        return []

    if not games:
        return []

    for game in games:
        home_team = game.get("home_team", "")
        away_team = game.get("away_team", "")
        game_time_cst = _to_cst_str(game.get("commence_time", ""))
        bookmakers = game.get("bookmakers", [])

        # ── Detector 1: Pitching Luck ─────────────────────────────────────
        try:
            home_sp_name = game.get("home_starter") or game.get("home_sp")
            away_sp_name = game.get("away_starter") or game.get("away_sp")

            if home_sp_name and away_sp_name:
                home_sp = _safe_pitcher_stats(home_sp_name, "home")
                away_sp = _safe_pitcher_stats(away_sp_name, "away")

                home_era = home_sp.get("era")
                home_xera = home_sp.get("xera")
                away_era = away_sp.get("era")
                away_xera = away_sp.get("xera")

                if all(v is not None for v in [home_era, home_xera, away_era, away_xera]):
                    home_xera_gap = float(home_xera) - float(home_era)
                    away_xera_gap = float(away_xera) - float(away_era)
                    combined_gap = home_xera_gap + away_xera_gap

                    total_data = extract_consensus_line(game, "totals")
                    if total_data:
                        over_odds = total_data.get("over_odds")
                        under_odds = total_data.get("under_odds")
                        total_point = total_data.get("point")

                        if over_odds and under_odds and total_point:
                            if combined_gap > _PITCHING_LUCK_OVER_THRESHOLD:
                                # Both pitchers lucky → regression → lean over
                                fair_over = _fair_prob_from_vig_removal(over_odds, under_odds)
                                # Rule-based estimate: luck gap scales probability
                                luck_boost = min(combined_gap * 0.04, 0.12)
                                our_prob = min(fair_over + luck_boost, 0.85)
                                edge_pct = (our_prob - fair_over) * 100

                                if edge_pct >= min_edge:
                                    picks.append(_build_pick(
                                        game=game,
                                        game_time_cst=game_time_cst,
                                        pick_side="over",
                                        pick_type="total",
                                        our_prob=our_prob,
                                        market_odds=int(over_odds),
                                        market_implied=fair_over,
                                        detector="rule_pitching_luck",
                                        features={
                                            "home_sp": home_sp_name,
                                            "away_sp": away_sp_name,
                                            "home_xera_gap": round(home_xera_gap, 3),
                                            "away_xera_gap": round(away_xera_gap, 3),
                                            "combined_xera_gap": round(combined_gap, 3),
                                            "total_line": total_point,
                                        },
                                    ))

                            elif combined_gap < _PITCHING_LUCK_UNDER_THRESHOLD:
                                # Both pitchers unlucky → regression → lean under
                                fair_under = _fair_prob_from_vig_removal(under_odds, over_odds)
                                luck_boost = min(abs(combined_gap) * 0.04, 0.12)
                                our_prob = min(fair_under + luck_boost, 0.85)
                                edge_pct = (our_prob - fair_under) * 100

                                if edge_pct >= min_edge:
                                    picks.append(_build_pick(
                                        game=game,
                                        game_time_cst=game_time_cst,
                                        pick_side="under",
                                        pick_type="total",
                                        our_prob=our_prob,
                                        market_odds=int(under_odds),
                                        market_implied=fair_under,
                                        detector="rule_pitching_luck",
                                        features={
                                            "home_sp": home_sp_name,
                                            "away_sp": away_sp_name,
                                            "home_xera_gap": round(home_xera_gap, 3),
                                            "away_xera_gap": round(away_xera_gap, 3),
                                            "combined_xera_gap": round(combined_gap, 3),
                                            "total_line": total_point,
                                        },
                                    ))
        except Exception as exc:
            logger.warning(
                "[mlb_predictor] Pitching luck detector failed for %s @ %s: %s",
                away_team, home_team, exc,
            )

        # ── Detector 2: Lineup Regression ─────────────────────────────────
        try:
            ml_data = extract_consensus_line(game, "h2h")
            if ml_data:
                home_ml_odds = ml_data.get("home_odds")
                away_ml_odds = ml_data.get("away_odds")

                if home_ml_odds and away_ml_odds:
                    home_batting = _safe_batting_stats(home_team)
                    away_batting = _safe_batting_stats(away_team)

                    for team, batting, team_odds, opp_odds, side in [
                        (home_team, home_batting, home_ml_odds, away_ml_odds, "home"),
                        (away_team, away_batting, away_ml_odds, home_ml_odds, "away"),
                    ]:
                        woba = batting.get("woba")
                        xwoba = batting.get("xwoba")

                        if woba is None or xwoba is None:
                            continue

                        xwoba_delta = float(xwoba) - float(woba)

                        # Team is underperforming contact quality AND priced as underdog
                        if (
                            xwoba_delta >= _XWOBA_REGRESSION_MIN
                            and int(team_odds) >= _LINEUP_ML_MAX_PRICE
                        ):
                            fair_prob = _fair_prob_from_vig_removal(team_odds, opp_odds)
                            # Conservative bump: 1pt xwOBA delta ≈ +2% win prob
                            xwoba_boost = min(xwoba_delta * 2.0, 0.10)
                            our_prob = min(fair_prob + xwoba_boost, 0.80)
                            edge_pct = (our_prob - fair_prob) * 100

                            if edge_pct >= min_edge:
                                picks.append(_build_pick(
                                    game=game,
                                    game_time_cst=game_time_cst,
                                    pick_side=side,
                                    pick_type="ml",
                                    our_prob=our_prob,
                                    market_odds=int(team_odds),
                                    market_implied=fair_prob,
                                    detector="rule_lineup_regression",
                                    features={
                                        "team": team,
                                        "woba": round(float(woba), 4),
                                        "xwoba": round(float(xwoba), 4),
                                        "xwoba_delta": round(xwoba_delta, 4),
                                        "team_ml": int(team_odds),
                                    },
                                ))
        except Exception as exc:
            logger.warning(
                "[mlb_predictor] Lineup regression detector failed for %s @ %s: %s",
                away_team, home_team, exc,
            )

        # ── Detector 3: Vig-Removed Multi-Book (H2H + Totals) ────────────
        try:
            for market_key, pick_type in [("h2h", "ml"), ("totals", "total")]:
                if not bookmakers:
                    continue

                # Collect per-book implied probabilities for the favourite / over side
                book_probs: list[tuple[str, float, int]] = []  # (book_key, implied_prob, odds)
                _market_total_line: Optional[float] = None  # populated for totals market

                for bk in bookmakers:
                    bk_key = bk.get("key", "unknown")
                    # markets is a dict {market_key: [outcomes]} after _normalise_bookmakers
                    markets_dict = bk.get("markets", {})
                    if not isinstance(markets_dict, dict):
                        continue
                    outcomes = markets_dict.get(market_key, [])
                    if not outcomes:
                        continue

                    if market_key == "h2h":
                        home_out = next(
                            (o for o in outcomes if o.get("name") == home_team), None
                        )
                        away_out = next(
                            (o for o in outcomes if o.get("name") == away_team), None
                        )
                        if home_out and away_out:
                            ho = home_out.get("price", 0)
                            ao = away_out.get("price", 0)
                            if ho and ao:
                                ip = _american_to_implied(int(ho))
                                book_probs.append((bk_key, ip, int(ho)))

                    elif market_key == "totals":
                        over_out = next(
                            (o for o in outcomes if o.get("name") == "Over"), None
                        )
                        under_out = next(
                            (o for o in outcomes if o.get("name") == "Under"), None
                        )
                        if over_out and under_out:
                            oo = over_out.get("price", 0)
                            uo = under_out.get("price", 0)
                            if oo and uo:
                                ip = _american_to_implied(int(oo))
                                book_probs.append((bk_key, ip, int(oo)))
                                # Capture line from first book that has it
                                if _market_total_line is None and over_out.get("point"):
                                    try:
                                        _market_total_line = float(over_out["point"])
                                    except (TypeError, ValueError):
                                        pass

                if len(book_probs) < 3:
                    # Need at least 3 books to compute a meaningful consensus
                    continue

                all_probs = [p for _, p, _ in book_probs]
                consensus = float(np.mean(all_probs))

                # Sanity guard: consensus outside 20%-80% for h2h means data error
                if market_key == "h2h" and not (0.20 <= consensus <= 0.80):
                    logger.debug(
                        "[mlb_predictor] Multi-book skipping %s @ %s %s — consensus %.3f outside bounds",
                        away_team, home_team, market_key, consensus,
                    )
                    continue

                for bk_key, bk_prob, bk_odds in book_probs:
                    divergence = bk_prob - consensus
                    # Cap divergence at 15% — beyond that is almost certainly a data error
                    if abs(divergence) >= _MULTIBOOK_PROB_DIVERGENCE and abs(divergence) < 0.15:
                        # This book is significantly off — there may be value
                        # at the books with LOWER implied prob (= better odds)
                        if divergence < 0:
                            # This book has lower implied prob = better odds for bettors
                            fair_prob = consensus  # consensus is our best estimate
                            our_prob = fair_prob
                            edge_pct = (fair_prob - bk_prob) * 100
                            pick_side = (
                                "over" if market_key == "totals"
                                else "home" if market_key == "h2h"
                                else "home_cover"
                            )

                            if edge_pct >= min_edge:
                                picks.append(_build_pick(
                                    game=game,
                                    game_time_cst=game_time_cst,
                                    pick_side=pick_side,
                                    pick_type=pick_type,
                                    our_prob=our_prob,
                                    market_odds=bk_odds,
                                    market_implied=bk_prob,
                                    detector="rule_multibook_vig",
                                    features={
                                        "flagged_book": bk_key,
                                        "book_implied_prob": round(bk_prob, 4),
                                        "consensus_prob": round(consensus, 4),
                                        "divergence_pct": round(abs(divergence) * 100, 2),
                                        "market": market_key,
                                        "books_sampled": len(book_probs),
                                        **({"total_line": _market_total_line} if _market_total_line is not None else {}),
                                    },
                                ))
        except Exception as exc:
            logger.warning(
                "[mlb_predictor] Multi-book detector failed for %s @ %s: %s",
                away_team, home_team, exc,
            )

        # ── Detector 3b: Run Line Multibook Vig (home + away cover) ──────
        try:
            if bookmakers:
                # Group books by the home team's point value — books posting different
                # points (e.g. some have home -1.5, others home +1.5) are NOT comparable
                # and must never be mixed into the same consensus calculation.
                # Structure: {home_point: {"home": [(bk, ip, odds)], "away": [(bk, ip, odds)]}}
                from collections import defaultdict as _dd
                by_line: dict = _dd(lambda: {"home": [], "away": []})

                for bk in bookmakers:
                    bk_key = bk.get("key", "unknown")
                    markets_dict = bk.get("markets", {})
                    if not isinstance(markets_dict, dict):
                        continue
                    outcomes = markets_dict.get("spreads", [])
                    if not outcomes:
                        continue

                    home_out = next((o for o in outcomes if o.get("name") == home_team), None)
                    away_out = next((o for o in outcomes if o.get("name") == away_team), None)

                    if home_out and away_out:
                        ho = home_out.get("price", 0)
                        ao = away_out.get("price", 0)
                        hp = home_out.get("point")
                        if ho and ao and hp is not None:
                            try:
                                hp = float(hp)
                            except (TypeError, ValueError):
                                continue
                            by_line[hp]["home"].append((bk_key, _american_to_implied(int(ho)), int(ho)))
                            by_line[hp]["away"].append((bk_key, _american_to_implied(int(ao)), int(ao)))

                # For each distinct point value, check divergence on both sides
                for home_point, sides in by_line.items():
                    for pick_side_name, side_probs in [
                        ("home_cover", sides["home"]),
                        ("away_cover", sides["away"]),
                    ]:
                        if len(side_probs) < 3:
                            continue

                        all_probs = [p for _, p, _ in side_probs]
                        consensus = float(np.mean(all_probs))

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
                                        game=game,
                                        game_time_cst=game_time_cst,
                                        pick_side=pick_side_name,
                                        pick_type="spread",
                                        our_prob=our_prob,
                                        market_odds=bk_odds,
                                        market_implied=bk_prob,
                                        detector="rule_multibook_vig",
                                        features={
                                            "flagged_book": bk_key,
                                            "book_implied_prob": round(bk_prob, 4),
                                            "consensus_prob": round(consensus, 4),
                                            "divergence_pct": round(abs(divergence) * 100, 2),
                                            "market": "spreads",
                                            "books_sampled": len(side_probs),
                                            "total_line": home_point,
                                        },
                                    ))

        except Exception as exc:
            logger.warning(
                "[mlb_predictor] Run line detector failed for %s @ %s: %s",
                away_team, home_team, exc,
            )

    # Deduplicate: if same game + market appears multiple times, keep highest edge
    seen: dict[str, dict] = {}
    for pick in picks:
        key = f"{pick['game_id']}_{pick['pick_type']}_{pick['pick_side']}"
        if key not in seen or pick["edge_pct"] > seen[key]["edge_pct"]:
            seen[key] = pick

    result = sorted(seen.values(), key=lambda p: p["edge_pct"], reverse=True)
    logger.info(
        "[mlb_predictor] rule_based_mlb_edges complete — %d pick(s) above %.1f%% edge",
        len(result), min_edge,
    )
    return result


# ---------------------------------------------------------------------------
# rule_based_mlb_strikeout_props — pitcher K props via multibook vig
# ---------------------------------------------------------------------------

def _fetch_pitcher_props(game_id: str, api_key: str) -> list[dict]:
    """
    Fetch pitcher_strikeouts market from Odds API per-event endpoint.
    Returns list of bookmaker dicts (same shape as game["bookmakers"]).
    Costs 1 API credit per call.
    """
    import requests as _req
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/events/{game_id}/odds"
    try:
        r = _req.get(url, params={
            "apiKey": api_key,
            "regions": "us",
            "markets": "pitcher_strikeouts",
            "oddsFormat": "american",
        }, timeout=15)
        r.raise_for_status()
        return r.json().get("bookmakers", [])
    except Exception as exc:
        logger.warning("[mlb_predictor] Props fetch failed for game %s: %s", game_id, exc)
        return []


def rule_based_mlb_strikeout_props(min_edge: float = 3.0) -> list[dict]:
    """
    Detect value on MLB pitcher strikeout props using multibook vig removal.

    Algorithm
    ---------
    For each today's game:
      1. Fetch pitcher_strikeouts market (1 API credit/game).
      2. Group outcomes by (pitcher_name, k_line).
      3. For each pitcher+line combo with ≥ 3 books:
         - Compute over-implied probability per book.
         - If any book diverges ≥ 5% below consensus → flag the over.
      4. Build pick with pick_type='props', total_line=k_line.

    Grading: props picks remain 'pending' until the props grader is built
    (task #35). The pitcher name is stored in features['pitcher'].

    Returns
    -------
    list of pick dicts sorted by edge_pct descending
    """
    import os as _os

    # Read API key from the backend .env
    api_key: Optional[str] = None
    try:
        env_path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(
            _os.path.dirname(__file__)))), ".env")
        with open(env_path) as f:
            for line in f:
                if line.startswith("ODDS_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    except Exception as exc:
        logger.error("[mlb_predictor] Cannot read API key for props: %s", exc)
        return []

    if not api_key:
        logger.error("[mlb_predictor] ODDS_API_KEY not found — skipping K props")
        return []

    try:
        games = fetch_live_odds(SPORT_KEY)
    except Exception as exc:
        logger.error("[mlb_predictor] fetch_live_odds failed for K props: %s", exc)
        return []

    if not games:
        return []

    picks: list[dict] = []

    for game in games:
        game_id  = game.get("id", game.get("game_id", ""))
        home_team = game.get("home_team", "")
        away_team = game.get("away_team", "")
        game_time_cst = _to_cst_str(game.get("commence_time", ""))

        if not game_id:
            continue

        bookmakers = _fetch_pitcher_props(game_id, api_key)
        if not bookmakers:
            continue

        # Build per-pitcher-per-line book probs dict
        # Structure: {(pitcher_name, k_line): [(bk_key, over_implied, over_odds, under_odds)]}
        pitcher_line_books: dict[tuple, list] = {}

        for bk in bookmakers:
            bk_key = bk.get("key", "unknown")
            for mkt in bk.get("markets", []):
                if mkt.get("key") != "pitcher_strikeouts":
                    continue
                outcomes = mkt.get("outcomes", [])

                # Group over/under by pitcher
                overs: dict[str, dict] = {}
                unders: dict[str, dict] = {}
                for o in outcomes:
                    pitcher = o.get("description", "")
                    if not pitcher:
                        continue
                    if o.get("name") == "Over":
                        overs[pitcher] = o
                    elif o.get("name") == "Under":
                        unders[pitcher] = o

                for pitcher, over_o in overs.items():
                    under_o = unders.get(pitcher)
                    if not under_o:
                        continue
                    k_line = over_o.get("point")
                    if k_line is None:
                        continue
                    try:
                        k_line = float(k_line)
                        over_odds  = int(over_o.get("price", 0))
                        under_odds = int(under_o.get("price", 0))
                    except (TypeError, ValueError):
                        continue
                    if not over_odds or not under_odds:
                        continue

                    key = (pitcher, k_line)
                    if key not in pitcher_line_books:
                        pitcher_line_books[key] = []
                    over_ip = _american_to_implied(over_odds)
                    pitcher_line_books[key].append((bk_key, over_ip, over_odds, under_odds))

        # Apply multibook vig detector per pitcher/line
        for (pitcher, k_line), book_list in pitcher_line_books.items():
            if len(book_list) < 3:
                continue

            all_probs = [ip for _, ip, _, _ in book_list]
            consensus = float(np.mean(all_probs))

            # Sanity guard
            if not (0.20 <= consensus <= 0.80):
                continue

            for bk_key, bk_prob, over_odds, under_odds in book_list:
                divergence = bk_prob - consensus
                if (
                    divergence < 0
                    and abs(divergence) >= _MULTIBOOK_PROB_DIVERGENCE
                    and abs(divergence) < 0.15
                ):
                    our_prob = consensus
                    edge_pct = (consensus - bk_prob) * 100

                    if edge_pct >= min_edge:
                        # Pseudo-game dict for _build_pick
                        game_ctx = {
                            "id": game_id,
                            "home_team": home_team,
                            "away_team": away_team,
                        }
                        picks.append(_build_pick(
                            game=game_ctx,
                            game_time_cst=game_time_cst,
                            pick_side="over",
                            pick_type="props",
                            our_prob=our_prob,
                            market_odds=over_odds,
                            market_implied=bk_prob,
                            detector="rule_multibook_vig_props",
                            features={
                                "pitcher": pitcher,
                                "k_line": k_line,
                                "total_line": k_line,
                                "flagged_book": bk_key,
                                "book_implied_prob": round(bk_prob, 4),
                                "consensus_prob": round(consensus, 4),
                                "divergence_pct": round(abs(divergence) * 100, 2),
                                "books_sampled": len(book_list),
                                "home_team": home_team,
                                "away_team": away_team,
                            },
                        ))

    # Deduplicate: same pitcher + line → keep highest edge
    seen: dict[str, dict] = {}
    for pick in picks:
        key = f"{pick['features'].get('pitcher')}_{pick['features'].get('k_line')}"
        if key not in seen or pick["edge_pct"] > seen[key]["edge_pct"]:
            seen[key] = pick

    result = sorted(seen.values(), key=lambda p: p["edge_pct"], reverse=True)
    logger.info(
        "[mlb_predictor] rule_based_mlb_strikeout_props — %d prop pick(s) above %.1f%% edge",
        len(result), min_edge,
    )
    return result
