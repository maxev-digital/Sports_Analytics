"""
MLB feature engineering for moneyline / totals ML models.

Builds a fixed-width numeric feature vector for each game by combining:
  - Starting-pitcher Statcast data  (ERA gap, K%, BB%)
  - Team batting expected-stats      (wOBA gap = wOBA - xwOBA)
  - Consensus market lines           (vig-removed home win prob, O/U total)

Exported API
------------
MLB_FEATURE_COLUMNS                           list[str]
build_game_features(game, pitching_df, batting_df) -> pd.Series | None
build_feature_matrix(games, pitching_df, batting_df)
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

MLB_FEATURE_COLUMNS: list[str] = [
    "sp_era_gap",         # Home SP: ERA - xERA  (positive → lucky/regression risk)
    "opp_sp_era_gap",     # Away SP: ERA - xERA
    "team_woba_gap",      # Home team: wOBA - xwOBA  (positive → overperforming)
    "opp_woba_gap",       # Away team: wOBA - xwOBA
    "home_advantage",     # 1.0 (home perspective is always home in this frame)
    "implied_total",      # Market O/U line
    "home_implied_prob",  # Vig-removed consensus home win probability
    "sp_k_pct",           # Home SP strikeout percentage
    "opp_sp_k_pct",       # Away SP strikeout percentage
    "sp_bb_pct",          # Home SP walk percentage  (higher = worse command)
    "opp_sp_bb_pct",      # Away SP walk percentage
]

# ---------------------------------------------------------------------------
# Internal: team-level batting helpers
# ---------------------------------------------------------------------------


def _team_rows(batting_df: pd.DataFrame, team: str) -> pd.DataFrame:
    """
    Return all rows in *batting_df* belonging to *team*.

    Tries exact case-insensitive match first; falls back to substring
    containment so that ``"NYY"`` matches ``"New York Yankees"`` etc.

    Args:
        batting_df: DataFrame from fetch_batting_statcast.
        team:       Team name or abbreviation.

    Returns:
        Filtered DataFrame (possibly empty).
    """
    if batting_df is None or batting_df.empty or "team" not in batting_df.columns:
        return pd.DataFrame()

    team_upper = team.strip().upper()

    # Exact match (case-insensitive)
    exact = batting_df[batting_df["team"].str.upper() == team_upper]
    if not exact.empty:
        return exact

    # Substring fallback
    partial = batting_df[
        batting_df["team"].str.upper().str.contains(team_upper, na=False)
    ]
    return partial


def _team_woba_gap(batting_df: pd.DataFrame, team: str) -> Optional[float]:
    """
    Compute the mean (wOBA - xwOBA) for *team*'s batters.

    A positive gap indicates the team is overperforming its expected
    production and faces negative regression risk.

    Args:
        batting_df: DataFrame from fetch_batting_statcast.
        team:       Team name or abbreviation.

    Returns:
        Mean wOBA gap as a float, or ``None`` if data is unavailable.
    """
    rows = _team_rows(batting_df, team)
    if rows.empty:
        logger.debug("No batting rows found for team '%s'.", team)
        return None

    if "woba" not in rows.columns or "xwoba" not in rows.columns:
        logger.debug(
            "woba / xwoba columns missing for team '%s' — cannot compute gap.",
            team,
        )
        return None

    woba = pd.to_numeric(rows["woba"], errors="coerce").dropna()
    xwoba = pd.to_numeric(rows["xwoba"], errors="coerce").dropna()

    if woba.empty or xwoba.empty:
        return None

    # Align on common index so the subtraction is element-wise
    common = woba.index.intersection(xwoba.index)
    if common.empty:
        return float(woba.mean() - xwoba.mean())
    return float((woba[common] - xwoba[common]).mean())


# ---------------------------------------------------------------------------
# Internal: starting-pitcher helpers
# ---------------------------------------------------------------------------


def _sp_rows(pitching_df: pd.DataFrame, pitcher_name: str) -> pd.DataFrame:
    """
    Return all rows in *pitching_df* matching *pitcher_name*.

    Case-insensitive substring search.

    Args:
        pitching_df:  DataFrame from fetch_pitching_statcast.
        pitcher_name: Full or partial pitcher name.

    Returns:
        Filtered DataFrame sorted by PA descending (best match first).
    """
    if (
        pitching_df is None
        or pitching_df.empty
        or "player_name" not in pitching_df.columns
    ):
        return pd.DataFrame()

    mask = pitching_df["player_name"].str.contains(
        pitcher_name.strip(), case=False, na=False
    )
    matches = pitching_df[mask]

    if matches.empty:
        return matches

    # Sort so the pitcher with more PA (more reliable sample) is first
    if "pa" in matches.columns:
        matches = matches.sort_values("pa", ascending=False)

    return matches


def _sp_stats(
    pitching_df: pd.DataFrame, pitcher_name: str
) -> Optional[dict]:
    """
    Look up a starting pitcher and return era_gap, k_pct, bb_pct.

    Args:
        pitching_df:  DataFrame from fetch_pitching_statcast.
        pitcher_name: Full or partial pitcher name.

    Returns:
        Dict with:
        - ``era_gap``: ERA - xERA (float; NaN if either stat is missing)
        - ``k_pct``:   strikeout percentage (float; NaN if missing)
        - ``bb_pct``:  walk percentage (float; NaN if missing)

        Returns ``None`` if no matching pitcher is found.
    """
    if not pitcher_name or not pitcher_name.strip():
        return None

    rows = _sp_rows(pitching_df, pitcher_name)
    if rows.empty:
        logger.debug("No pitcher matching '%s' found in pitching DataFrame.", pitcher_name)
        return None

    row = rows.iloc[0]

    def _f(col: str) -> float:
        v = pd.to_numeric(row.get(col), errors="coerce")
        return float(v) if pd.notna(v) else math.nan

    era = _f("era")
    xera = _f("xera")
    era_gap = era - xera if not (math.isnan(era) or math.isnan(xera)) else math.nan

    return {
        "era_gap": era_gap,
        "k_pct": _f("k_percent"),
        "bb_pct": _f("bb_percent"),
    }


# ---------------------------------------------------------------------------
# Single-game feature builder
# ---------------------------------------------------------------------------


def build_game_features(
    game: dict,
    pitching_df: pd.DataFrame,
    batting_df: pd.DataFrame,
) -> Optional[pd.Series]:
    """
    Build a feature vector for one MLB game.

    Expected keys in *game*
    -----------------------
    home_team         str   home team name or abbreviation
    away_team         str   away team name or abbreviation
    home_sp           str   home starting pitcher name
    away_sp           str   away starting pitcher name
    consensus_h2h     dict  from ``extract_consensus_line(game, 'h2h')``
    consensus_totals  dict  from ``extract_consensus_line(game, 'totals')``

    The consensus dicts must contain at minimum:
    - ``home_implied_prob`` (h2h)
    - ``consensus_total``   (totals)

    Both are critical; if either is absent the function returns ``None``
    and the game is excluded from the feature matrix.

    SP stats and team wOBA gaps are included when available and NaN-filled
    when not, so that the caller can decide whether to impute or drop.

    Args:
        game:        Game descriptor dict.
        pitching_df: Pitching Statcast DataFrame (from fetch_pitching_statcast).
        batting_df:  Batting Statcast DataFrame  (from fetch_batting_statcast).

    Returns:
        pd.Series indexed by :data:`MLB_FEATURE_COLUMNS`, or ``None`` if
        a critical market feature is missing.
    """
    home_team = game.get("home_team", "")
    away_team = game.get("away_team", "")
    home_sp = game.get("home_sp", "")
    away_sp = game.get("away_sp", "")

    # ---- Critical: market consensus lines ----
    h2h = game.get("consensus_h2h") or {}
    totals = game.get("consensus_totals") or {}

    implied_total = totals.get("consensus_total")
    home_implied_prob = h2h.get("home_implied_prob")

    if implied_total is None or home_implied_prob is None:
        logger.debug(
            "Skipping game '%s' @ '%s' — consensus_h2h or consensus_totals missing.",
            away_team,
            home_team,
        )
        return None

    # ---- Home SP ----
    home_sp_data = _sp_stats(pitching_df, home_sp) if home_sp else None
    sp_era_gap = home_sp_data["era_gap"] if home_sp_data else math.nan
    sp_k_pct = home_sp_data["k_pct"] if home_sp_data else math.nan
    sp_bb_pct = home_sp_data["bb_pct"] if home_sp_data else math.nan

    if home_sp_data is None and home_sp:
        logger.debug("No Statcast data found for home SP '%s'.", home_sp)

    # ---- Away SP ----
    away_sp_data = _sp_stats(pitching_df, away_sp) if away_sp else None
    opp_sp_era_gap = away_sp_data["era_gap"] if away_sp_data else math.nan
    opp_sp_k_pct = away_sp_data["k_pct"] if away_sp_data else math.nan
    opp_sp_bb_pct = away_sp_data["bb_pct"] if away_sp_data else math.nan

    if away_sp_data is None and away_sp:
        logger.debug("No Statcast data found for away SP '%s'.", away_sp)

    # ---- Team batting wOBA gaps ----
    raw_team_woba_gap = _team_woba_gap(batting_df, home_team)
    raw_opp_woba_gap = _team_woba_gap(batting_df, away_team)

    values = {
        "sp_era_gap": sp_era_gap,
        "opp_sp_era_gap": opp_sp_era_gap,
        "team_woba_gap": (
            raw_team_woba_gap if raw_team_woba_gap is not None else math.nan
        ),
        "opp_woba_gap": (
            raw_opp_woba_gap if raw_opp_woba_gap is not None else math.nan
        ),
        "home_advantage": 1.0,
        "implied_total": float(implied_total),
        "home_implied_prob": float(home_implied_prob),
        "sp_k_pct": sp_k_pct,
        "opp_sp_k_pct": opp_sp_k_pct,
        "sp_bb_pct": sp_bb_pct,
        "opp_sp_bb_pct": opp_sp_bb_pct,
    }

    return pd.Series(values, index=MLB_FEATURE_COLUMNS, dtype=float)


# ---------------------------------------------------------------------------
# Batch feature matrix builder
# ---------------------------------------------------------------------------


def build_feature_matrix(
    games: list[dict],
    pitching_df: pd.DataFrame,
    batting_df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[int]]:
    """
    Build a feature matrix for a list of MLB games.

    Games for which :func:`build_game_features` returns ``None`` (missing
    consensus lines) are excluded; NaN values from missing SP / batting data
    are preserved so the caller can choose an imputation strategy.

    Args:
        games:       List of game dicts (see :func:`build_game_features`).
        pitching_df: Pitching Statcast DataFrame.
        batting_df:  Batting Statcast DataFrame.

    Returns:
        Tuple ``(feature_df, valid_game_indices)`` where:

        - ``feature_df`` — DataFrame with shape
          ``(n_valid, len(MLB_FEATURE_COLUMNS))``, reset index.
        - ``valid_game_indices`` — list of original indices into *games*
          that produced valid rows, preserving order.  Use this to align
          the feature matrix back to your games list.
    """
    rows: list[pd.Series] = []
    valid_indices: list[int] = []

    for idx, game in enumerate(games):
        features = build_game_features(game, pitching_df, batting_df)
        if features is not None:
            rows.append(features)
            valid_indices.append(idx)
        else:
            logger.info(
                "Game %d ('%s' @ '%s') excluded — insufficient features.",
                idx,
                game.get("away_team", "?"),
                game.get("home_team", "?"),
            )

    if not rows:
        logger.warning(
            "build_feature_matrix: 0 of %d games produced valid features.",
            len(games),
        )
        return pd.DataFrame(columns=MLB_FEATURE_COLUMNS), []

    feature_df = (
        pd.DataFrame(rows, columns=MLB_FEATURE_COLUMNS)
        .reset_index(drop=True)
        .astype(float)
    )

    logger.info(
        "build_feature_matrix: %d / %d games have valid feature vectors.",
        len(valid_indices),
        len(games),
    )
    return feature_df, valid_indices
