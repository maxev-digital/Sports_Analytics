"""
WNBA feature engineering for game-level ML models.

Builds a fixed-width numeric feature vector for each game using:
  - Team offensive / defensive ratings (per 100 possessions)
  - Pace (possessions per 40 minutes)
  - Season win percentages (overall, home/road split)
  - Consensus market lines (vig-removed home win prob, O/U total)

Exported API
------------
WNBA_FEATURE_COLUMNS                              list[str]
build_wnba_features(game, team_stats)         -> pd.Series | None
build_wnba_feature_matrix(games, team_stats)
    -> tuple[pd.DataFrame, list[int]]
"""

from __future__ import annotations

import logging
import math
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature schema
# ---------------------------------------------------------------------------

WNBA_FEATURE_COLUMNS: list[str] = [
    "home_ortg",          # Offensive rating per 100 possessions (home team)
    "away_ortg",          # Offensive rating per 100 possessions (away team)
    "home_drtg",          # Defensive rating per 100 possessions (home; lower = better)
    "away_drtg",          # Defensive rating per 100 possessions (away)
    "ortg_diff",          # home_ortg - away_ortg
    "drtg_diff",          # home_drtg - away_drtg  (positive → home D is worse)
    "net_rating_diff",    # (home_ortg - home_drtg) - (away_ortg - away_drtg)
    "home_pace",          # Possessions per 40 minutes (home team)
    "away_pace",          # Possessions per 40 minutes (away team)
    "implied_total",      # Market O/U line
    "home_implied_prob",  # Vig-removed consensus home win probability
    "home_win_pct",       # Home team overall season win percentage
    "away_win_pct",       # Away team overall season win percentage
    "home_road_gap",      # Home team's (home win%) - (road win%)
]

# ---------------------------------------------------------------------------
# Record parsing helpers
# ---------------------------------------------------------------------------


def _parse_record(record: str) -> tuple[int, int]:
    """
    Parse a W-L record string into ``(wins, losses)``.

    Accepts ``'W-L'`` or ``'W/L'`` delimiters; strips surrounding whitespace
    from each component.  Returns ``(0, 0)`` on any parse failure rather than
    raising so callers can fall back gracefully.

    Args:
        record: Record string such as ``'12-5'``, ``'7/3'``, or ``'10 - 2'``.

    Returns:
        ``(wins, losses)`` tuple of non-negative integers.
    """
    record = record.strip()
    for sep in ("-", "/"):
        parts = record.split(sep)
        if len(parts) == 2:
            try:
                return int(parts[0].strip()), int(parts[1].strip())
            except ValueError:
                continue
    logger.debug("Could not parse record string %r — defaulting to (0, 0).", record)
    return 0, 0


def _win_pct(record: str) -> float:
    """
    Convert a W-L record string to a win percentage.

    Args:
        record: Record string (e.g. ``'12-5'``).

    Returns:
        Win percentage in [0.0, 1.0]; returns ``0.5`` (neutral) when the
        record is unparseable or has zero total games.
    """
    wins, losses = _parse_record(record)
    total = wins + losses
    return wins / total if total > 0 else 0.5


# ---------------------------------------------------------------------------
# Team stats lookup
# ---------------------------------------------------------------------------


def _get_team_stats(team_stats: dict, team_name: str) -> Optional[dict]:
    """
    Look up *team_name* in *team_stats*.

    Resolution order:
    1. Exact key match.
    2. Case-insensitive exact match.
    3. Case-insensitive substring match (either direction) to handle
       abbreviation vs. full-name mismatches (e.g. ``"LV"`` → ``"Las Vegas Aces"``).

    Args:
        team_stats: Dict keyed by team name (see :func:`build_wnba_features`).
        team_name:  Team name to look up.

    Returns:
        Stats sub-dict, or ``None`` if not found.
    """
    if not team_stats or not team_name:
        return None

    # 1. Exact key match
    if team_name in team_stats:
        return team_stats[team_name]

    # 2. Case-insensitive exact match
    team_lower = team_name.lower()
    for key, stats in team_stats.items():
        if key.lower() == team_lower:
            return stats

    # 3. Substring match (either direction)
    for key, stats in team_stats.items():
        key_lower = key.lower()
        if team_lower in key_lower or key_lower in team_lower:
            logger.debug(
                "Matched team '%s' to stats key '%s' via substring.", team_name, key
            )
            return stats

    logger.debug("No WNBA team stats found for '%s'.", team_name)
    return None


# ---------------------------------------------------------------------------
# Single-game feature builder
# ---------------------------------------------------------------------------


def build_wnba_features(
    game: dict,
    team_stats: dict,
) -> Optional[pd.Series]:
    """
    Build a feature vector for one WNBA game.

    Expected keys in *game*
    -----------------------
    home_team         str   home team name
    away_team         str   away team name
    consensus_h2h     dict  from ``extract_consensus_line(game, 'h2h')``
    consensus_totals  dict  from ``extract_consensus_line(game, 'totals')``

    Both consensus dicts must contain their critical fields
    (``home_implied_prob`` for h2h, ``consensus_total`` for totals).  If
    either is absent the function returns ``None``.

    Expected structure of each *team_stats* entry
    ----------------------------------------------
    .. code-block:: python

        {
            "Las Vegas Aces": {
                "ortg":        112.4,   # offensive rating per 100 possessions
                "drtg":         98.7,   # defensive rating per 100 possessions
                "pace":         97.2,   # possessions per 40 minutes
                "home_record": "10-2",  # W-L at home this season
                "road_record":  "7-5",  # W-L on the road this season
            }
        }

    ``ortg`` and ``drtg`` are critical; missing values cause the game to be
    excluded.  ``pace``, ``home_record``, and ``road_record`` are NaN-filled
    when absent.

    Args:
        game:       Game descriptor dict (see above).
        team_stats: Dict keyed by team name with efficiency/record data.

    Returns:
        pd.Series indexed by :data:`WNBA_FEATURE_COLUMNS`, or ``None`` if
        critical features (consensus lines or ortg/drtg) cannot be resolved.
    """
    home_team = game.get("home_team", "")
    away_team = game.get("away_team", "")

    # ---- Critical: market consensus lines ----
    h2h = game.get("consensus_h2h") or {}
    totals = game.get("consensus_totals") or {}

    implied_total = totals.get("consensus_total")
    home_implied_prob = h2h.get("home_implied_prob")

    if implied_total is None or home_implied_prob is None:
        logger.debug(
            "Skipping WNBA game '%s' @ '%s' — consensus lines missing.",
            away_team,
            home_team,
        )
        return None

    # ---- Team efficiency stats ----
    home_stats = _get_team_stats(team_stats, home_team)
    away_stats = _get_team_stats(team_stats, away_team)

    if home_stats is None:
        logger.debug(
            "Skipping WNBA game '%s' @ '%s' — no stats for home team '%s'.",
            away_team, home_team, home_team,
        )
        return None

    if away_stats is None:
        logger.debug(
            "Skipping WNBA game '%s' @ '%s' — no stats for away team '%s'.",
            away_team, home_team, away_team,
        )
        return None

    def _f(d: dict, key: str) -> float:
        """Safe float extraction; returns NaN on missing or non-numeric."""
        val = d.get(key)
        if val is None:
            return math.nan
        try:
            return float(val)
        except (TypeError, ValueError):
            return math.nan

    home_ortg = _f(home_stats, "ortg")
    away_ortg = _f(away_stats, "ortg")
    home_drtg = _f(home_stats, "drtg")
    away_drtg = _f(away_stats, "drtg")

    # ortg and drtg are critical — a model cannot run without them
    if any(math.isnan(v) for v in (home_ortg, away_ortg, home_drtg, away_drtg)):
        missing_labels = []
        if math.isnan(home_ortg):
            missing_labels.append(f"home ortg ({home_team})")
        if math.isnan(away_ortg):
            missing_labels.append(f"away ortg ({away_team})")
        if math.isnan(home_drtg):
            missing_labels.append(f"home drtg ({home_team})")
        if math.isnan(away_drtg):
            missing_labels.append(f"away drtg ({away_team})")
        logger.debug(
            "Skipping WNBA game '%s' @ '%s' — NaN for: %s.",
            away_team, home_team, ", ".join(missing_labels),
        )
        return None

    home_pace = _f(home_stats, "pace")
    away_pace = _f(away_stats, "pace")

    # ---- Derived efficiency deltas ----
    ortg_diff = home_ortg - away_ortg
    drtg_diff = home_drtg - away_drtg
    home_net = home_ortg - home_drtg
    away_net = away_ortg - away_drtg
    net_rating_diff = home_net - away_net

    # ---- Win percentages from W-L records ----
    home_home_str = home_stats.get("home_record", "")
    home_road_str = home_stats.get("road_record", "")
    away_home_str = away_stats.get("home_record", "")
    away_road_str = away_stats.get("road_record", "")

    home_home_w, home_home_l = _parse_record(home_home_str)
    home_road_w, home_road_l = _parse_record(home_road_str)
    away_home_w, away_home_l = _parse_record(away_home_str)
    away_road_w, away_road_l = _parse_record(away_road_str)

    # Overall season win %
    home_total_g = home_home_w + home_home_l + home_road_w + home_road_l
    home_total_w = home_home_w + home_road_w
    home_win_pct = home_total_w / home_total_g if home_total_g > 0 else 0.5

    away_total_g = away_home_w + away_home_l + away_road_w + away_road_l
    away_total_w = away_home_w + away_road_w
    away_win_pct = away_total_w / away_total_g if away_total_g > 0 else 0.5

    # Home-court advantage gap (home win% minus road win% for the home team)
    home_home_g = home_home_w + home_home_l
    home_home_pct = home_home_w / home_home_g if home_home_g > 0 else 0.5
    home_road_g = home_road_w + home_road_l
    home_road_pct = home_road_w / home_road_g if home_road_g > 0 else 0.5
    home_road_gap = home_home_pct - home_road_pct

    values = {
        "home_ortg": home_ortg,
        "away_ortg": away_ortg,
        "home_drtg": home_drtg,
        "away_drtg": away_drtg,
        "ortg_diff": ortg_diff,
        "drtg_diff": drtg_diff,
        "net_rating_diff": net_rating_diff,
        "home_pace": home_pace,
        "away_pace": away_pace,
        "implied_total": float(implied_total),
        "home_implied_prob": float(home_implied_prob),
        "home_win_pct": home_win_pct,
        "away_win_pct": away_win_pct,
        "home_road_gap": home_road_gap,
    }

    return pd.Series(values, index=WNBA_FEATURE_COLUMNS, dtype=float)


# ---------------------------------------------------------------------------
# Batch feature matrix builder
# ---------------------------------------------------------------------------


def build_wnba_feature_matrix(
    games: list[dict],
    team_stats: dict,
) -> tuple[pd.DataFrame, list[int]]:
    """
    Build a feature matrix for a list of WNBA games.

    Games for which :func:`build_wnba_features` returns ``None`` are
    excluded; NaN values (e.g. missing pace) are preserved for the caller
    to impute or drop.

    Args:
        games:      List of game dicts (see :func:`build_wnba_features`).
        team_stats: Dict of team efficiency/record data
                    (see :func:`build_wnba_features`).

    Returns:
        Tuple ``(feature_df, valid_game_indices)`` where:

        - ``feature_df`` — DataFrame with shape
          ``(n_valid, len(WNBA_FEATURE_COLUMNS))``, reset index.
        - ``valid_game_indices`` — list of original indices into *games*
          that produced valid rows.  Use this to align the feature matrix
          back to your games list.
    """
    rows: list[pd.Series] = []
    valid_indices: list[int] = []

    for idx, game in enumerate(games):
        features = build_wnba_features(game, team_stats)
        if features is not None:
            rows.append(features)
            valid_indices.append(idx)
        else:
            logger.info(
                "WNBA game %d ('%s' @ '%s') excluded — insufficient features.",
                idx,
                game.get("away_team", "?"),
                game.get("home_team", "?"),
            )

    if not rows:
        logger.warning(
            "build_wnba_feature_matrix: 0 of %d games produced valid features.",
            len(games),
        )
        return pd.DataFrame(columns=WNBA_FEATURE_COLUMNS), []

    feature_df = (
        pd.DataFrame(rows, columns=WNBA_FEATURE_COLUMNS)
        .reset_index(drop=True)
        .astype(float)
    )

    logger.info(
        "build_wnba_feature_matrix: %d / %d games have valid feature vectors.",
        len(valid_indices),
        len(games),
    )
    return feature_df, valid_indices


# ---------------------------------------------------------------------------
# Compatibility bridge — called by wnba_predictor.py
# ---------------------------------------------------------------------------

def build_wnba_game_features(
    home_team: str,
    away_team: str,
    home_stats: dict,
    away_stats: dict,
    total_line: float,
    spread_line: float,
) -> "Optional[pd.Series]":
    """
    Bridge between wnba_predictor's call signature and build_wnba_features.
    Assembles the game/team_stats dicts expected by the core function.
    """
    game = {
        "home_team": home_team,
        "away_team": away_team,
        "consensus_h2h": {
            "home_implied_prob": home_stats.get("home_implied_prob", 0.5),
            "away_implied_prob": away_stats.get("away_implied_prob", 0.5),
        },
        "consensus_totals": {
            "consensus_total": total_line,
        },
        "consensus_spreads": {
            "spread_line": spread_line,
        },
    }
    team_stats = {home_team: home_stats, away_team: away_stats}
    return build_wnba_features(game, team_stats)
