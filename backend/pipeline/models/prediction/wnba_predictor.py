"""
WNBA prediction engine — generates today's picks from live odds + ESPN team stats.

Two entry points
----------------
generate_wnba_picks(min_edge)
    Full ML pipeline: loads trained models, fetches live WNBA odds, builds
    feature vectors from team stats, runs ensemble inference, filters by edge.
    Falls back to rule_based_wnba_edges when no trained models exist.

rule_based_wnba_edges(min_edge)
    Heuristic-only pipeline — works before any model training is done.
    Two detectors:
      1. Efficiency Delta — large net rating gap mispriced in the spread market
      2. Vig-Removed Multi-Book — cross-book line discrepancies (same as MLB)

Pick dict schema (both functions return this structure)
-------------------------------------------------------
{
  'sport'               : 'wnba',
  'game_id'             : str,
  'home_team'           : str,
  'away_team'           : str,
  'game_time_cst'       : str,
  'pick_side'           : 'over'|'under'|'home'|'away',
  'pick_type'           : 'total'|'spread',
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
import requests

from pipeline.ingestion.live_odds import (
    fetch_live_odds,
    extract_consensus_line,
    remove_vig,
)
from pipeline.models.features.wnba_features import (
    WNBA_FEATURE_COLUMNS,
    build_wnba_game_features,
)
from pipeline.models.training.wnba_trainer import load_wnba_models, get_ensemble_probability
from pipeline.config import MIN_EDGE_PCT, MIN_CONFIDENCE, now_cst

logger = logging.getLogger(__name__)

SPORT_KEY = "basketball_wnba"

# Internal ESPN / analytics endpoint
_ESPN_TEAM_STATS_URL = "http://localhost:8000/api/analytics-data/team-scoring/wnba"
_ESPN_REQUEST_TIMEOUT = 10  # seconds

# Detector thresholds
_EFFICIENCY_DELTA_MIN = 8.0        # net rating diff above which we look for misprice
_EFFICIENCY_SPREAD_MISMATCH = 4.0  # max market spread to flag as under-priced
_MULTIBOOK_PROB_DIVERGENCE = 0.05  # 5% off consensus = flaggable


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
    Use remove_vig() when available; fall back to simple normalisation
    if the import fails or returns unexpected data.

    Returns the fair (vig-free) probability for odds_side.
    """
    try:
        result = remove_vig(odds_side, odds_other)
        return float(result.get("side1", _shin_fair_prob(odds_side, odds_other)))
    except Exception:
        return _shin_fair_prob(odds_side, odds_other)


def _shin_fair_prob(odds_side: int, odds_other: int) -> float:
    p1 = _american_to_implied(odds_side)
    p2 = _american_to_implied(odds_other)
    return p1 / (p1 + p2)


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
    """Assemble a standardised WNBA pick dict."""
    return {
        "sport": "wnba",
        "game_id": game.get("id", ""),
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
    }


# ---------------------------------------------------------------------------
# fetch_wnba_team_stats
# ---------------------------------------------------------------------------

def fetch_wnba_team_stats() -> dict:
    """
    Fetch WNBA team statistics from the internal ESPN analytics endpoint.

    Endpoint : GET http://localhost:8000/api/analytics-data/team-scoring/wnba

    The response can be either:
      - a list  : [{team, abbreviation, ppg, papg, wins, losses, homeRecord, roadRecord, ...}]
      - a dict  : {team_name: {ppg, papg, ...}, ...}

    Returns
    -------
    dict keyed by team name (and abbreviation where present) mapping to stat
    sub-dicts.  Returns {} if the endpoint is unreachable or returns bad data.

    Note: both the full team name and the abbreviation are stored as keys so
    downstream code can look up by either form (The Odds API uses full names;
    other internal tools may use abbreviations).
    """
    try:
        resp = requests.get(_ESPN_TEAM_STATS_URL, timeout=_ESPN_REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ConnectionError:
        logger.warning(
            "[wnba_predictor] Internal ESPN endpoint not reachable (%s) — "
            "team stats will be empty; picks degrade to rule-based only",
            _ESPN_TEAM_STATS_URL,
        )
        return {}
    except requests.exceptions.Timeout:
        logger.warning("[wnba_predictor] ESPN endpoint timed out after %ds", _ESPN_REQUEST_TIMEOUT)
        return {}
    except requests.exceptions.HTTPError as exc:
        logger.warning("[wnba_predictor] ESPN endpoint returned HTTP error: %s", exc)
        return {}
    except Exception as exc:
        logger.error("[wnba_predictor] Unexpected error fetching team stats: %s", exc)
        return {}

    result: dict = {}

    if isinstance(data, list):
        for entry in data:
            if not isinstance(entry, dict):
                continue
            name = entry.get("team") or entry.get("name") or ""
            abbrev = entry.get("abbreviation") or entry.get("abbrev") or ""
            # Normalise homeRecord / roadRecord → plain win rates if only strings
            entry = _normalise_team_record(entry)
            if name:
                result[name] = entry
            if abbrev and abbrev != name:
                result[abbrev] = entry

    elif isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, dict):
                val = _normalise_team_record(val)
                result[key] = val
                abbrev = val.get("abbreviation") or val.get("abbrev") or ""
                if abbrev and abbrev != key:
                    result[abbrev] = val
    else:
        logger.error(
            "[wnba_predictor] Unexpected ESPN response type: %s", type(data).__name__
        )
        return {}

    logger.info("[wnba_predictor] Loaded ESPN stats for %d team keys", len(result))
    return result


def _normalise_team_record(entry: dict) -> dict:
    """
    Convert string record fields ('8-2') to numeric win rates where possible.
    Leaves the original string fields intact; adds *_win_pct computed versions.
    """
    out = dict(entry)
    for field, new_field in [("homeRecord", "home_win_pct"), ("roadRecord", "road_win_pct")]:
        raw = out.get(field, "")
        if isinstance(raw, str) and "-" in raw:
            parts = raw.split("-")
            if len(parts) == 2:
                try:
                    w, l = int(parts[0]), int(parts[1])
                    total = w + l
                    out[new_field] = round(w / total, 4) if total > 0 else 0.5
                except ValueError:
                    pass
        elif isinstance(raw, (int, float)):
            out[new_field] = float(raw)
    return out


def _lookup_team(stats_by_team: dict, team_name: str) -> dict:
    """
    Look up a team by name with a few fuzzy fallbacks:
    exact match → abbreviation match → substring match → {}.
    """
    if team_name in stats_by_team:
        return stats_by_team[team_name]

    # Try abbreviation stored inside any entry
    for _key, entry in stats_by_team.items():
        if (
            entry.get("team", "").lower() == team_name.lower()
            or entry.get("name", "").lower() == team_name.lower()
            or entry.get("abbreviation", "").lower() == team_name.lower()
        ):
            return entry

    # Last resort: substring
    team_lower = team_name.lower()
    for key in stats_by_team:
        if key.lower() in team_lower or team_lower in key.lower():
            return stats_by_team[key]

    logger.debug("[wnba_predictor] No stats found for team: %s", team_name)
    return {}


# ---------------------------------------------------------------------------
# generate_wnba_picks — full ML pipeline
# ---------------------------------------------------------------------------

def generate_wnba_picks(min_edge: Optional[float] = None) -> list[dict]:
    """
    Generate today's WNBA picks using the trained ensemble models.

    For each game the function attempts two markets:
      - Totals (over/under) → loaded from wnba_total models
      - Spreads             → loaded from wnba_spread models

    Falls back to rule_based_wnba_edges when no saved models are found.

    Parameters
    ----------
    min_edge : float, optional
        Minimum edge percentage. Defaults to MIN_EDGE_PCT from pipeline.config.

    Returns
    -------
    list of pick dicts sorted by edge_pct descending
    """
    if min_edge is None:
        min_edge = MIN_EDGE_PCT

    total_models = load_wnba_models("total")
    spread_models = load_wnba_models("spread")

    if not total_models and not spread_models:
        logger.warning(
            "[wnba_predictor] No saved WNBA models — falling back to rule-based"
        )
        return rule_based_wnba_edges(min_edge)

    # Fetch team stats and live odds concurrently (sequential here; parallelism
    # is handled at the orchestration layer if needed)
    team_stats = fetch_wnba_team_stats()

    try:
        games = fetch_live_odds(SPORT_KEY)
    except Exception as exc:
        logger.error("[wnba_predictor] fetch_live_odds failed: %s", exc)
        return []

    if not games:
        logger.info("[wnba_predictor] No WNBA games returned from odds API")
        return []

    picks: list[dict] = []

    for game in games:
        home_team = game.get("home_team", "")
        away_team = game.get("away_team", "")
        game_time_cst = _to_cst_str(game.get("commence_time", ""))
        bookmakers = game.get("bookmakers", [])

        home_stats = _lookup_team(team_stats, home_team)
        away_stats = _lookup_team(team_stats, away_team)

        # ── TOTALS market ──────────────────────────────────────────────────
        if total_models:
            try:
                total_data = extract_consensus_line(bookmakers, "totals")
                if total_data:
                    total_point = total_data.get("point")
                    over_odds = total_data.get("over_odds")
                    under_odds = total_data.get("under_odds")

                    if total_point and over_odds and under_odds:
                        fair_over = _fair_prob_from_vig_removal(over_odds, under_odds)

                        features = _safe_build_features(
                            home_team=home_team,
                            away_team=away_team,
                            home_stats=home_stats,
                            away_stats=away_stats,
                            total_line=float(total_point),
                            spread_line=None,
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
                                    detector="wnba_ensemble_total",
                                    features=features.to_dict(),
                                ))
            except Exception as exc:
                logger.warning(
                    "[wnba_predictor] Total market failed for %s @ %s: %s",
                    away_team, home_team, exc,
                )

        # ── SPREADS market ─────────────────────────────────────────────────
        if spread_models:
            try:
                spread_data = extract_consensus_line(bookmakers, "spreads")
                if spread_data:
                    home_spread = spread_data.get("home_point")   # e.g. -5.5
                    home_spread_odds = spread_data.get("home_odds")
                    away_spread_odds = spread_data.get("away_odds")

                    if home_spread is not None and home_spread_odds and away_spread_odds:
                        fair_home_cover = _fair_prob_from_vig_removal(
                            home_spread_odds, away_spread_odds
                        )

                        features = _safe_build_features(
                            home_team=home_team,
                            away_team=away_team,
                            home_stats=home_stats,
                            away_stats=away_stats,
                            total_line=None,
                            spread_line=float(home_spread),
                        )

                        if features is not None:
                            ensemble = get_ensemble_probability(spread_models, features)
                            our_home_cover_prob = ensemble["ensemble_mean"]

                            if our_home_cover_prob >= 0.5:
                                pick_side = "home"
                                our_prob = our_home_cover_prob
                                market_implied = fair_home_cover
                                market_odds = int(home_spread_odds)
                            else:
                                pick_side = "away"
                                our_prob = 1.0 - our_home_cover_prob
                                market_implied = 1.0 - fair_home_cover
                                market_odds = int(away_spread_odds)

                            edge_pct = (our_prob - market_implied) * 100

                            if edge_pct >= min_edge:
                                picks.append(_build_pick(
                                    game=game,
                                    game_time_cst=game_time_cst,
                                    pick_side=pick_side,
                                    pick_type="spread",
                                    our_prob=our_prob,
                                    market_odds=market_odds,
                                    market_implied=market_implied,
                                    detector="wnba_ensemble_spread",
                                    features=features.to_dict(),
                                ))
            except Exception as exc:
                logger.warning(
                    "[wnba_predictor] Spread market failed for %s @ %s: %s",
                    away_team, home_team, exc,
                )

    picks.sort(key=lambda p: p["edge_pct"], reverse=True)
    logger.info(
        "[wnba_predictor] generate_wnba_picks complete — %d pick(s) above %.1f%% edge",
        len(picks), min_edge,
    )
    return picks


def _safe_build_features(
    home_team: str,
    away_team: str,
    home_stats: dict,
    away_stats: dict,
    total_line: Optional[float],
    spread_line: Optional[float],
) -> Optional[pd.Series]:
    """Call build_wnba_game_features, returning None on failure."""
    try:
        features = build_wnba_game_features(
            home_team=home_team,
            away_team=away_team,
            home_stats=home_stats,
            away_stats=away_stats,
            total_line=total_line,
            spread_line=spread_line,
        )
        return features
    except Exception as exc:
        logger.warning(
            "[wnba_predictor] build_wnba_game_features failed for %s @ %s: %s",
            away_team, home_team, exc,
        )
        return None


# ---------------------------------------------------------------------------
# rule_based_wnba_edges — heuristic-only, no ML models required
# ---------------------------------------------------------------------------

def rule_based_wnba_edges(min_edge: float = 3.0) -> list[dict]:
    """
    Run two rule-based edge detectors against today's WNBA slate.

    Requires live odds and ESPN team stats but NOT trained ML models.

    Detector 1 — Efficiency Delta (spread market)
        net_rating = ppg - papg  (points scored minus points allowed per game)
        net_rating_diff = home_net_rating - away_net_rating

        If |net_rating_diff| > 8 BUT |market_spread| < 4, the market
        hasn't fully priced in the efficiency gap.  Flag a spread edge for
        the team with the higher net rating.

        Edge size estimate: for every additional net-rating point beyond the
        threshold, add ~1.5% to the expected win probability.

    Detector 2 — Vig-Removed Multi-Book discrepancy (totals and spreads)
        Across all bookmakers, compute each book's implied probability for
        the favourite / over side.  If any book's implied prob differs from
        the mean of all other books by >= 5%, that book's line is suspect
        and the opposing side may offer value.

    Parameters
    ----------
    min_edge : float
        Minimum edge percentage (default 3.0%).

    Returns
    -------
    list of pick dicts (same schema as generate_wnba_picks)
    """
    picks: list[dict] = []

    # Fetch team stats once for the whole slate
    team_stats = fetch_wnba_team_stats()

    try:
        games = fetch_live_odds(SPORT_KEY)
    except Exception as exc:
        logger.error("[wnba_predictor] fetch_live_odds failed in rule-based: %s", exc)
        return []

    if not games:
        return []

    for game in games:
        home_team = game.get("home_team", "")
        away_team = game.get("away_team", "")
        game_time_cst = _to_cst_str(game.get("commence_time", ""))
        bookmakers = game.get("bookmakers", [])

        home_stats = _lookup_team(team_stats, home_team)
        away_stats = _lookup_team(team_stats, away_team)

        # ── Detector 1: Efficiency Delta ──────────────────────────────────
        try:
            home_ppg = home_stats.get("ppg")
            home_papg = home_stats.get("papg")
            away_ppg = away_stats.get("ppg")
            away_papg = away_stats.get("papg")

            if all(v is not None for v in [home_ppg, home_papg, away_ppg, away_papg]):
                home_net = float(home_ppg) - float(home_papg)
                away_net = float(away_ppg) - float(away_papg)
                net_diff = home_net - away_net  # positive = home dominates

                spread_data = extract_consensus_line(bookmakers, "spreads")
                if spread_data:
                    home_point = spread_data.get("home_point")   # e.g. -3.5 or +3.5
                    home_spread_odds = spread_data.get("home_odds")
                    away_spread_odds = spread_data.get("away_odds")

                    if home_point is not None and home_spread_odds and away_spread_odds:
                        market_spread_abs = abs(float(home_point))

                        if (
                            abs(net_diff) >= _EFFICIENCY_DELTA_MIN
                            and market_spread_abs < _EFFICIENCY_SPREAD_MISMATCH
                        ):
                            # Market spread is tight but efficiency gap is large
                            gap_excess = abs(net_diff) - _EFFICIENCY_DELTA_MIN
                            probability_boost = min(gap_excess * 0.015, 0.12)

                            if net_diff > 0:
                                # Home team is significantly better
                                fair_home = _fair_prob_from_vig_removal(
                                    home_spread_odds, away_spread_odds
                                )
                                our_prob = min(fair_home + probability_boost, 0.82)
                                edge_pct = (our_prob - fair_home) * 100
                                pick_side = "home"
                                market_odds = int(home_spread_odds)
                                market_implied = fair_home
                            else:
                                # Away team is significantly better
                                fair_away = _fair_prob_from_vig_removal(
                                    away_spread_odds, home_spread_odds
                                )
                                our_prob = min(fair_away + probability_boost, 0.82)
                                edge_pct = (our_prob - fair_away) * 100
                                pick_side = "away"
                                market_odds = int(away_spread_odds)
                                market_implied = fair_away

                            if edge_pct >= min_edge:
                                picks.append(_build_pick(
                                    game=game,
                                    game_time_cst=game_time_cst,
                                    pick_side=pick_side,
                                    pick_type="spread",
                                    our_prob=our_prob,
                                    market_odds=market_odds,
                                    market_implied=market_implied,
                                    detector="rule_efficiency_delta",
                                    features={
                                        "home_team": home_team,
                                        "away_team": away_team,
                                        "home_net_rating": round(home_net, 2),
                                        "away_net_rating": round(away_net, 2),
                                        "net_rating_diff": round(net_diff, 2),
                                        "market_spread": float(home_point),
                                        "home_ppg": home_ppg,
                                        "home_papg": home_papg,
                                        "away_ppg": away_ppg,
                                        "away_papg": away_papg,
                                    },
                                ))
        except Exception as exc:
            logger.warning(
                "[wnba_predictor] Efficiency delta detector failed for %s @ %s: %s",
                away_team, home_team, exc,
            )

        # ── Detector 2: Vig-Removed Multi-Book ────────────────────────────
        try:
            for market_key, pick_type in [("totals", "total"), ("spreads", "spread")]:
                if not bookmakers:
                    continue

                book_probs: list[tuple[str, float, int]] = []

                for bk in bookmakers:
                    bk_key = bk.get("key", "unknown")
                    for mkt in bk.get("markets", []):
                        if mkt.get("key") != market_key:
                            continue
                        outcomes = mkt.get("outcomes", [])
                        if not outcomes:
                            continue

                        if market_key == "totals":
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

                        elif market_key == "spreads":
                            home_out = next(
                                (
                                    o for o in outcomes
                                    if o.get("name") == home_team
                                    or o.get("name", "").lower() == "home"
                                ),
                                None,
                            )
                            away_out = next(
                                (
                                    o for o in outcomes
                                    if o.get("name") == away_team
                                    or o.get("name", "").lower() == "away"
                                ),
                                None,
                            )
                            if home_out and away_out:
                                ho = home_out.get("price", 0)
                                ao = away_out.get("price", 0)
                                if ho and ao:
                                    ip = _american_to_implied(int(ho))
                                    book_probs.append((bk_key, ip, int(ho)))

                if len(book_probs) < 3:
                    continue

                all_probs = [p for _, p, _ in book_probs]
                consensus = float(np.mean(all_probs))

                for bk_key, bk_prob, bk_odds in book_probs:
                    divergence = bk_prob - consensus
                    if abs(divergence) >= _MULTIBOOK_PROB_DIVERGENCE and divergence < 0:
                        # This book has better odds (lower implied prob) than consensus
                        our_prob = consensus
                        edge_pct = (consensus - bk_prob) * 100
                        pick_side = "over" if market_key == "totals" else "home"

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
                                },
                            ))
        except Exception as exc:
            logger.warning(
                "[wnba_predictor] Multi-book detector failed for %s @ %s: %s",
                away_team, home_team, exc,
            )

    # Deduplicate: same game + market + side → keep highest edge
    seen: dict[str, dict] = {}
    for pick in picks:
        key = f"{pick['game_id']}_{pick['pick_type']}_{pick['pick_side']}"
        if key not in seen or pick["edge_pct"] > seen[key]["edge_pct"]:
            seen[key] = pick

    result = sorted(seen.values(), key=lambda p: p["edge_pct"], reverse=True)
    logger.info(
        "[wnba_predictor] rule_based_wnba_edges complete — %d pick(s) above %.1f%% edge",
        len(result), min_edge,
    )
    return result
