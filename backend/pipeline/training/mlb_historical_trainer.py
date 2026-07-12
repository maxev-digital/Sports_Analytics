"""
MLB historical model trainer — 2023 through 2025 seasons.

Reads from tables produced by historical_mlb.py:
  hist_mlb_games              — completed games with scores + SP names
  hist_mlb_statcast_pitching  — individual pitcher era/xera/k%/bb%
  hist_mlb_statcast_batting   — individual batter woba/xwoba

Feature set (9 features — market-independent probability estimate):
  sp_era_gap       home SP: ERA - xERA  (positive = regression risk)
  opp_sp_era_gap   away SP: ERA - xERA
  team_woba_gap    home team mean (wOBA - xwOBA)  (season avg proxy)
  opp_woba_gap     away team mean (wOBA - xwOBA)
  home_advantage   constant 1.0
  sp_k_pct         home SP strikeout %
  opp_sp_k_pct     away SP strikeout %
  sp_bb_pct        home SP walk %
  opp_sp_bb_pct    away SP walk %

Labels:
  home_won     → moneyline model
  went_over    → totals model  (total > 8.5 league-average placeholder)
  home_covered → run-line model (home margin > 1.5)

Models saved to:  pipeline/models/saved/mlb_{bet_type}_hist_{model_name}.joblib
Metadata saved:   pipeline/models/saved/mlb_{bet_type}_hist_metadata.json

Run manually:
    cd /root/sporttrader/backend
    python3 -m pipeline.training.mlb_historical_trainer
"""

from __future__ import annotations

import json
import logging
import math
import os
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import lightgbm as lgb

from pipeline.db.connection import execute_query
from pipeline.config import now_cst

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature schema (market-independent, 9 columns)
# ---------------------------------------------------------------------------
HIST_FEATURE_COLUMNS: list[str] = [
    "sp_era_gap",
    "opp_sp_era_gap",
    "team_woba_gap",
    "opp_woba_gap",
    "home_advantage",
    "sp_k_pct",
    "opp_sp_k_pct",
    "sp_bb_pct",
    "opp_sp_bb_pct",
]

# Placeholder totals line for went_over label (league average)
_LEAGUE_AVG_TOTAL = 8.5

# Minimum games needed to proceed
_MIN_GAMES = 200

# Save directory (same as standard models)
_MODELS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "saved")
)

# Ensemble weights (matching mlb_trainer.py)
_ENSEMBLE_WEIGHTS = {
    "xgboost": 0.35,
    "lightgbm": 0.35,
    "random_forest": 0.20,
    "logistic_regression": 0.10,
}


# ---------------------------------------------------------------------------
# Load raw data from DB
# ---------------------------------------------------------------------------

def _load_pitching(seasons: list[int]) -> pd.DataFrame:
    placeholders = ",".join(["%s"] * len(seasons))
    rows = execute_query(
        f"SELECT season, player_name, era, xera, era_gap, k_percent, bb_percent, pa "
        f"FROM hist_mlb_statcast_pitching WHERE season IN ({placeholders}) ORDER BY season, pa DESC",
        tuple(seasons),
    )
    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["season", "player_name", "era", "xera", "era_gap", "k_percent", "bb_percent", "pa"]
    )


def _load_batting(seasons: list[int]) -> pd.DataFrame:
    placeholders = ",".join(["%s"] * len(seasons))
    rows = execute_query(
        f"SELECT season, player_name, woba, xwoba, woba_gap, pa "
        f"FROM hist_mlb_statcast_batting WHERE season IN ({placeholders}) ORDER BY season, pa DESC",
        tuple(seasons),
    )
    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["season", "player_name", "woba", "xwoba", "woba_gap", "pa"]
    )


def _load_games(seasons: list[int]) -> pd.DataFrame:
    placeholders = ",".join(["%s"] * len(seasons))
    rows = execute_query(
        f"SELECT season, game_date, home_team, away_team, "
        f"home_score, away_score, home_sp_lf, away_sp_lf "
        f"FROM hist_mlb_games "
        f"WHERE season IN ({placeholders}) AND home_score IS NOT NULL AND away_score IS NOT NULL "
        f"ORDER BY season, game_date",
        tuple(seasons),
    )
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ---------------------------------------------------------------------------
# Build lookup indices from Statcast data
# ---------------------------------------------------------------------------

def _build_pitcher_lookup(pitching_df: pd.DataFrame) -> dict[tuple[int, str], dict]:
    """Returns {(season, 'Last, First'): {era_gap, k_pct, bb_pct}}."""
    lookup: dict[tuple[int, str], dict] = {}
    for _, row in pitching_df.iterrows():
        key = (int(row["season"]), str(row["player_name"]))
        lookup[key] = {
            "era_gap": float(row["era_gap"]) if pd.notna(row.get("era_gap")) else math.nan,
            "k_pct":   float(row["k_percent"]) if pd.notna(row.get("k_percent")) else math.nan,
            "bb_pct":  float(row["bb_percent"]) if pd.notna(row.get("bb_percent")) else math.nan,
        }
    return lookup


def _build_season_pitching_avg(pitching_df: pd.DataFrame) -> dict[int, dict]:
    """Season-level league-average pitcher stats as fallback."""
    avgs: dict[int, dict] = {}
    for season, grp in pitching_df.groupby("season"):
        avgs[int(season)] = {
            "era_gap": float(grp["era_gap"].dropna().mean()) if not grp["era_gap"].dropna().empty else 0.0,
            "k_pct":   float(grp["k_percent"].dropna().mean()) if not grp["k_percent"].dropna().empty else 22.0,
            "bb_pct":  float(grp["bb_percent"].dropna().mean()) if not grp["bb_percent"].dropna().empty else 8.5,
        }
    return avgs


def _build_season_batting_avg(batting_df: pd.DataFrame) -> dict[int, float]:
    """Season-level average woba_gap as team proxy fallback."""
    avgs: dict[int, float] = {}
    for season, grp in batting_df.groupby("season"):
        mean_val = grp["woba_gap"].dropna().mean()
        avgs[int(season)] = float(mean_val) if pd.notna(mean_val) else 0.0
    return avgs


# ---------------------------------------------------------------------------
# Feature builder for one game
# ---------------------------------------------------------------------------

def _sp_features(
    season: int,
    sp_lf: Optional[str],
    pitcher_lookup: dict,
    season_avg: dict,
) -> tuple[float, float, float]:
    if sp_lf:
        hit = pitcher_lookup.get((season, sp_lf))
        if hit:
            return hit["era_gap"], hit["k_pct"], hit["bb_pct"]
    avg = season_avg.get(season, {"era_gap": 0.0, "k_pct": 22.0, "bb_pct": 8.5})
    return avg["era_gap"], avg["k_pct"], avg["bb_pct"]


def _build_dataset(
    games_df: pd.DataFrame,
    pitching_df: pd.DataFrame,
    batting_df: pd.DataFrame,
) -> pd.DataFrame:
    pitcher_lookup = _build_pitcher_lookup(pitching_df)
    season_pitch   = _build_season_pitching_avg(pitching_df)
    season_bat     = _build_season_batting_avg(batting_df)

    records = []
    for _, row in games_df.iterrows():
        season     = int(row["season"])
        home_score = int(row["home_score"])
        away_score = int(row["away_score"])
        home_sp_lf = row.get("home_sp_lf") or None
        away_sp_lf = row.get("away_sp_lf") or None

        h_era, h_k, h_bb = _sp_features(season, home_sp_lf, pitcher_lookup, season_pitch)
        a_era, a_k, a_bb = _sp_features(season, away_sp_lf, pitcher_lookup, season_pitch)

        bat_gap    = season_bat.get(season, 0.0)
        total_runs = home_score + away_score

        records.append({
            "sp_era_gap":     h_era,
            "opp_sp_era_gap": a_era,
            "team_woba_gap":  bat_gap,
            "opp_woba_gap":   bat_gap,
            "home_advantage": 1.0,
            "sp_k_pct":       h_k,
            "opp_sp_k_pct":   a_k,
            "sp_bb_pct":      h_bb,
            "opp_sp_bb_pct":  a_bb,
            "home_won":       int(home_score > away_score),
            "went_over":      int(total_runs > _LEAGUE_AVG_TOTAL),
            "home_covered":   int((home_score - away_score) > 1.5),
            "total_runs":     total_runs,
            "season":         season,
        })

    df = pd.DataFrame(records)
    if not df.empty:
        df = df.replace([float("inf"), float("-inf")], float("nan"))
    return df


# ---------------------------------------------------------------------------
# Model builders (parallel to mlb_trainer.py, uses HIST_FEATURE_COLUMNS)
# ---------------------------------------------------------------------------

def _build_estimators() -> dict[str, Pipeline]:
    return {
        "random_forest": Pipeline([
            ("clf", RandomForestClassifier(
                n_estimators=200, max_depth=8, min_samples_leaf=10,
                max_features="sqrt", class_weight="balanced",
                n_jobs=-1, random_state=42,
            )),
        ]),
        "xgboost": Pipeline([
            ("clf", xgb.XGBClassifier(
                n_estimators=300, max_depth=6, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8,
                objective="binary:logistic", eval_metric="logloss",
                tree_method="hist", n_jobs=-1, random_state=42, verbosity=0,
            )),
        ]),
        "lightgbm": Pipeline([
            ("clf", lgb.LGBMClassifier(
                n_estimators=300, max_depth=6, learning_rate=0.05,
                subsample=0.8, feature_fraction=0.8,
                class_weight="balanced", n_jobs=-1, random_state=42, verbose=-1,
            )),
        ]),
        "logistic_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(
                C=0.1, max_iter=1000, solver="lbfgs",
                class_weight="balanced", random_state=42,
            )),
        ]),
    }


def _feat_importance(calibrated: CalibratedClassifierCV) -> dict[str, float]:
    imps = []
    for cal in calibrated.calibrated_classifiers_:
        clf = cal.estimator.named_steps["clf"]
        if hasattr(clf, "feature_importances_"):
            imps.append(np.asarray(clf.feature_importances_, dtype=float))
        elif hasattr(clf, "coef_"):
            imps.append(np.abs(clf.coef_[0]).astype(float))
    if not imps:
        return {}
    mean_imp = np.mean(imps, axis=0)
    total = mean_imp.sum()
    if total > 0:
        mean_imp /= total
    return {col: round(float(v), 6) for col, v in zip(HIST_FEATURE_COLUMNS, mean_imp)}


def _train_for_bet_type(df: pd.DataFrame, label_col: str) -> dict:
    """Walk-forward: train on all seasons except last, validate on last."""
    seasons = sorted(df["season"].unique())
    val_season = seasons[-1]
    train_seasons = seasons[:-1]

    mask_train = df["season"].isin(train_seasons)
    mask_val   = df["season"] == val_season

    X_train = df.loc[mask_train, HIST_FEATURE_COLUMNS].astype(float)
    y_train = df.loc[mask_train, label_col].astype(int)
    X_val   = df.loc[mask_val,   HIST_FEATURE_COLUMNS].astype(float)
    y_val   = df.loc[mask_val,   label_col].astype(int)

    logger.info(
        "[hist_trainer] train=%s val=%s | rows=%d/%d | pos=%.1f%%/%.1f%%",
        train_seasons, val_season,
        len(y_train), len(y_val),
        y_train.mean() * 100, y_val.mean() * 100,
    )

    results: dict = {}
    for model_name, pipe in _build_estimators().items():
        logger.info("[hist_trainer] Training %s …", model_name)
        try:
            cal = CalibratedClassifierCV(pipe, method="isotonic", cv=5)
            cal.fit(X_train.values, y_train.values)
            proba = cal.predict_proba(X_val.values)[:, 1]
            preds = (proba >= 0.5).astype(int)
            results[model_name] = {
                "model": cal,
                "auc":      round(float(roc_auc_score(y_val, proba)), 4),
                "brier":    round(float(brier_score_loss(y_val, proba)), 4),
                "accuracy": round(float(accuracy_score(y_val, preds)), 4),
                "feature_importance": _feat_importance(cal),
            }
            logger.info("[hist_trainer] %s  AUC=%.4f  Brier=%.4f", model_name, results[model_name]["auc"], results[model_name]["brier"])
        except Exception:
            logger.exception("[hist_trainer] %s failed; skipping", model_name)

    return results


def _save_models(trained: dict, bet_type: str) -> None:
    os.makedirs(_MODELS_DIR, exist_ok=True)
    now = now_cst().isoformat()
    meta: dict = {}
    for model_name, info in trained.items():
        path = os.path.join(_MODELS_DIR, f"mlb_{bet_type}_hist_{model_name}.joblib")
        joblib.dump(info["model"], path, compress=3)
        top10 = dict(sorted(info.get("feature_importance", {}).items(), key=lambda kv: kv[1], reverse=True)[:10])
        meta[model_name] = {
            "sport": "mlb", "bet_type": bet_type, "source": "historical",
            "feature_cols": HIST_FEATURE_COLUMNS,
            "auc": info["auc"], "brier": info["brier"], "accuracy": info["accuracy"],
            "trained_at": now, "feature_importance_top10": top10,
        }
        logger.info("[hist_trainer] Saved %s → %s", model_name, path)
    meta_path = os.path.join(_MODELS_DIR, f"mlb_{bet_type}_hist_metadata.json")
    with open(meta_path, "w") as fh:
        json.dump(meta, fh, indent=2)


def load_historical_models(bet_type: str) -> dict:
    """
    Load historical models.  Returns dict keyed by model_name, with 'model',
    'auc', 'feature_cols' keys.  Empty dict if not found.
    """
    meta_path = os.path.join(_MODELS_DIR, f"mlb_{bet_type}_hist_metadata.json")
    meta_all: dict = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path) as fh:
                meta_all = json.load(fh)
        except Exception:
            pass

    loaded: dict = {}
    for model_name in _ENSEMBLE_WEIGHTS:
        path = os.path.join(_MODELS_DIR, f"mlb_{bet_type}_hist_{model_name}.joblib")
        if not os.path.exists(path):
            continue
        try:
            model = joblib.load(path)
            meta  = meta_all.get(model_name, {})
            loaded[model_name] = {
                "model":        model,
                "auc":          meta.get("auc"),
                "brier":        meta.get("brier"),
                "accuracy":     meta.get("accuracy"),
                "feature_cols": meta.get("feature_cols", HIST_FEATURE_COLUMNS),
            }
            logger.info("[hist_trainer] Loaded %s (AUC=%s)", model_name, meta.get("auc"))
        except Exception:
            logger.exception("[hist_trainer] Failed loading %s; skipping", model_name)

    return loaded


def get_hist_ensemble_prob(models: dict, features: pd.Series) -> dict:
    """
    Compute ensemble probability from historical models.
    features must contain at least HIST_FEATURE_COLUMNS entries.
    """
    feat_cols = next(
        (info.get("feature_cols", HIST_FEATURE_COLUMNS) for info in models.values()),
        HIST_FEATURE_COLUMNS,
    )
    X = pd.DataFrame([features]).reindex(columns=feat_cols).astype(float)
    raw: dict[str, float] = {}
    for model_name, info in models.items():
        try:
            raw[model_name] = round(float(info["model"].predict_proba(X.values)[0, 1]), 4)
        except Exception:
            logger.warning("[hist_trainer] predict_proba failed for %s", model_name)

    if not raw:
        return {"ensemble_mean": 0.50, "ensemble_std": 0.0}

    total_w = sum(_ENSEMBLE_WEIGHTS.get(n, 0.0) for n in raw)
    if total_w <= 0:
        ensemble_mean = float(np.mean(list(raw.values())))
    else:
        ensemble_mean = sum(
            _ENSEMBLE_WEIGHTS.get(n, 0.0) * p / total_w for n, p in raw.items()
        )

    return {
        **raw,
        "ensemble_mean": round(ensemble_mean, 4),
        "ensemble_std":  round(float(np.std(list(raw.values()))), 4) if len(raw) > 1 else 0.0,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def build_and_train(seasons: list[int] | None = None) -> dict:
    """
    Build training dataset from historical tables and train historical MLB models.
    """
    if seasons is None:
        seasons = [2023, 2024, 2025]

    logger.info("[hist_trainer] Loading data for seasons %s …", seasons)

    pitching_df = _load_pitching(seasons)
    batting_df  = _load_batting(seasons)
    games_df    = _load_games(seasons)

    logger.info(
        "[hist_trainer] Loaded: %d pitching, %d batting, %d games.",
        len(pitching_df), len(batting_df), len(games_df),
    )

    if len(games_df) < _MIN_GAMES:
        msg = f"Only {len(games_df)} games — need {_MIN_GAMES}. Run ingestion first."
        logger.error("[hist_trainer] %s", msg)
        return {"status": "insufficient_data", "games": len(games_df), "needed": _MIN_GAMES}

    df = _build_dataset(games_df, pitching_df, batting_df)
    logger.info("[hist_trainer] Training dataset: %d rows.", len(df))

    # Impute NaN with column median
    for col in HIST_FEATURE_COLUMNS:
        median = df[col].median()
        df[col] = df[col].fillna(median if pd.notna(median) else 0.0)

    summary: dict = {"status": "ok", "games": len(df), "seasons": seasons}

    for bet_type, label_col in [("ml", "home_won"), ("total", "went_over"), ("spread", "home_covered")]:
        pos = int(df[label_col].sum())
        neg = len(df) - pos
        logger.info("[hist_trainer] %s: pos=%d neg=%d", bet_type, pos, neg)
        if pos < 50 or neg < 50:
            logger.warning("[hist_trainer] Skipping %s — class imbalance.", bet_type)
            summary[bet_type] = "skipped_class_imbalance"
            continue

        trained = _train_for_bet_type(df, label_col)
        if trained:
            _save_models(trained, bet_type)
            summary[bet_type] = {
                "models": {k: {"auc": v["auc"], "brier": v["brier"]} for k, v in trained.items()},
                "rows": len(df),
            }
        else:
            summary[bet_type] = "training_failed"

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Train historical MLB models")
    parser.add_argument("--seasons", nargs="+", type=int, default=[2023, 2024, 2025])
    args = parser.parse_args()
    result = build_and_train(args.seasons)
    print(result)
