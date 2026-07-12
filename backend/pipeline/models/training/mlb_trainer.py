"""
MLB model training pipeline.

Walk-forward validation: train on seasons [N-3 … N-1], evaluate on season N.
Four model types: random_forest, xgboost, lightgbm, logistic_regression.
All calibrated via CalibratedClassifierCV(method='isotonic').

Public API
----------
train_mlb_models(historical_df, bet_type) -> dict
save_mlb_models(trained_models, bet_type)
load_mlb_models(bet_type) -> dict
get_ensemble_probability(models, features) -> dict
"""
from __future__ import annotations

import json
import logging
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

from pipeline.models.features.mlb_features import MLB_FEATURE_COLUMNS
from pipeline.config import now_cst

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODELS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "saved")
)

TARGET_MAP: dict[str, str] = {
    "total": "went_over",
    "ml": "home_won",
    "spread": "home_covered",
}

# Ensemble weights must sum to 1.0
ENSEMBLE_WEIGHTS: dict[str, float] = {
    "xgboost": 0.35,
    "lightgbm": 0.35,
    "random_forest": 0.20,
    "logistic_regression": 0.10,
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_base_estimators() -> dict[str, Pipeline]:
    """
    Return a fresh dict of unfitted sklearn Pipelines, one per model type.

    Tree models get no scaler (tree splits are scale-invariant).
    Logistic regression gets a StandardScaler prepended.
    """
    return {
        "random_forest": Pipeline([
            ("clf", RandomForestClassifier(
                n_estimators=200,
                max_depth=8,
                min_samples_leaf=10,
                max_features="sqrt",
                class_weight="balanced",
                n_jobs=-1,
                random_state=42,
            )),
        ]),
        "xgboost": Pipeline([
            ("clf", xgb.XGBClassifier(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                objective="binary:logistic",
                eval_metric="logloss",
                tree_method="hist",
                n_jobs=-1,
                random_state=42,
                verbosity=0,
            )),
        ]),
        "lightgbm": Pipeline([
            ("clf", lgb.LGBMClassifier(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                feature_fraction=0.8,
                class_weight="balanced",
                n_jobs=-1,
                random_state=42,
                verbose=-1,
            )),
        ]),
        "logistic_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(
                C=0.1,
                max_iter=1000,
                solver="lbfgs",
                class_weight="balanced",
                random_state=42,
            )),
        ]),
    }


def _extract_feature_importance(
    calibrated_model: CalibratedClassifierCV,
    feature_names: list[str],
) -> dict[str, float]:
    """
    Average feature importances across all CV-fold calibrators.

    Handles RandomForest/XGBoost/LightGBM (feature_importances_) and
    LogisticRegression (|coef_[0]|). Returns {} when unavailable.
    """
    importances_list: list[np.ndarray] = []

    for cal in calibrated_model.calibrated_classifiers_:
        est: Pipeline = cal.estimator
        clf_step = est.named_steps["clf"]

        if hasattr(clf_step, "feature_importances_"):
            importances_list.append(np.asarray(clf_step.feature_importances_, dtype=float))
        elif hasattr(clf_step, "coef_"):
            importances_list.append(np.abs(clf_step.coef_[0]).astype(float))

    if not importances_list:
        return {}

    mean_imp = np.mean(importances_list, axis=0)
    total = mean_imp.sum()
    if total > 0:
        mean_imp = mean_imp / total

    return {
        name: round(float(imp), 6)
        for name, imp in zip(feature_names, mean_imp)
    }


def _validate_dataframe(df: pd.DataFrame, bet_type: str) -> str:
    """Raise ValueError early if required columns are missing. Returns target col."""
    if bet_type not in TARGET_MAP:
        raise ValueError(
            f"Unknown bet_type '{bet_type}'. Valid options: {list(TARGET_MAP)}"
        )
    target_col = TARGET_MAP[bet_type]
    required = MLB_FEATURE_COLUMNS + ["season", target_col]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"historical_df is missing {len(missing)} column(s): {missing[:10]}"
            + (" ..." if len(missing) > 10 else "")
        )
    return target_col


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def train_mlb_models(
    historical_df: pd.DataFrame,
    bet_type: str = "total",
) -> dict:
    """
    Train four model types for the given bet_type using walk-forward validation.

    Walk-forward scheme
    -------------------
    - train  : all seasons except the most recent one
    - validate: the most recent season (held out entirely — no data leakage)

    Each base Pipeline is wrapped with CalibratedClassifierCV(method='isotonic',
    cv=5), which does internal cross-validation on the *training* set to learn
    calibration parameters.  Final predictions are evaluated on the held-out
    validation season.

    Parameters
    ----------
    historical_df : pd.DataFrame
        Must contain columns: 'season', all MLB_FEATURE_COLUMNS, and the
        target column determined by bet_type.
    bet_type : {'total', 'ml', 'spread'}

    Returns
    -------
    dict keyed by model_name:
        {
          'model'             : CalibratedClassifierCV (fitted),
          'auc'               : float,
          'brier'             : float,
          'accuracy'          : float,
          'feature_importance': dict[str, float],
        }
    """
    target_col = _validate_dataframe(historical_df, bet_type)

    df = (
        historical_df
        .dropna(subset=MLB_FEATURE_COLUMNS + [target_col])
        .copy()
        .sort_values("season")
    )

    seasons = sorted(df["season"].unique())
    if len(seasons) < 2:
        raise ValueError(
            f"Need at least 2 seasons of data; got {len(seasons)}: {seasons}"
        )

    val_season = seasons[-1]
    train_seasons = seasons[:-1]

    logger.info(
        "[mlb_trainer] Walk-forward | bet_type=%s | train=%s | val=%s",
        bet_type, train_seasons, val_season,
    )

    train_mask = df["season"].isin(train_seasons)
    val_mask = df["season"] == val_season

    X_train = df.loc[train_mask, MLB_FEATURE_COLUMNS].astype(float)
    y_train = df.loc[train_mask, target_col].astype(int)
    X_val = df.loc[val_mask, MLB_FEATURE_COLUMNS].astype(float)
    y_val = df.loc[val_mask, target_col].astype(int)

    if len(X_val) == 0:
        raise ValueError(
            f"Validation set for season={val_season} is empty. "
            "Check the 'season' column values in historical_df."
        )

    logger.info(
        "[mlb_trainer] Train rows=%d (pos=%.1f%%) | Val rows=%d (pos=%.1f%%)",
        len(y_train), y_train.mean() * 100,
        len(y_val), y_val.mean() * 100,
    )

    base_estimators = _build_base_estimators()
    results: dict = {}

    for model_name, pipe in base_estimators.items():
        logger.info("[mlb_trainer] Training %s ...", model_name)
        try:
            calibrated = CalibratedClassifierCV(pipe, method="isotonic", cv=5)
            calibrated.fit(X_train.values, y_train.values)

            proba = calibrated.predict_proba(X_val.values)[:, 1]
            preds = (proba >= 0.5).astype(int)

            auc = float(roc_auc_score(y_val, proba))
            brier = float(brier_score_loss(y_val, proba))
            acc = float(accuracy_score(y_val, preds))
            feat_imp = _extract_feature_importance(calibrated, MLB_FEATURE_COLUMNS)

            results[model_name] = {
                "model": calibrated,
                "auc": round(auc, 4),
                "brier": round(brier, 4),
                "accuracy": round(acc, 4),
                "feature_importance": feat_imp,
            }
            logger.info(
                "[mlb_trainer] %s done — AUC=%.4f  Brier=%.4f  Acc=%.4f",
                model_name, auc, brier, acc,
            )
        except Exception:
            logger.exception("[mlb_trainer] Failed to train %s; skipping", model_name)

    if not results:
        raise RuntimeError("All four model types failed to train. Check logs.")

    return results


def save_mlb_models(trained_models: dict, bet_type: str) -> None:
    """
    Persist each trained model and a companion JSON metadata file.

    Paths
    -----
    Model  : pipeline/models/saved/mlb_{bet_type}_{model_name}.joblib
    Metadata: pipeline/models/saved/mlb_{bet_type}_metadata.json
    """
    if bet_type not in TARGET_MAP:
        raise ValueError(f"Unknown bet_type '{bet_type}'")

    os.makedirs(MODELS_DIR, exist_ok=True)
    trained_at = now_cst().isoformat()
    meta_all: dict = {}

    for model_name, info in trained_models.items():
        model_path = os.path.join(MODELS_DIR, f"mlb_{bet_type}_{model_name}.joblib")
        joblib.dump(info["model"], model_path, compress=3)
        logger.info("[mlb_trainer] Saved %-20s → %s", model_name, model_path)

        # Top-10 features by importance for quick reference in metadata
        top10 = dict(
            sorted(
                info.get("feature_importance", {}).items(),
                key=lambda kv: kv[1],
                reverse=True,
            )[:10]
        )

        meta_all[model_name] = {
            "sport": "mlb",
            "bet_type": bet_type,
            "auc": info["auc"],
            "brier": info["brier"],
            "accuracy": info["accuracy"],
            "trained_at": trained_at,
            "feature_importance_top10": top10,
        }

    meta_path = os.path.join(MODELS_DIR, f"mlb_{bet_type}_metadata.json")
    with open(meta_path, "w") as fh:
        json.dump(meta_all, fh, indent=2)
    logger.info("[mlb_trainer] Metadata written → %s", meta_path)


def load_mlb_models(bet_type: str) -> dict:
    """
    Load all saved models for the given bet_type from disk.

    Returns the same structure as train_mlb_models (without the raw model
    object's calibrated internals — those are inside the loaded joblib).
    Returns an empty dict if no saved models are found.
    """
    if bet_type not in TARGET_MAP:
        raise ValueError(f"Unknown bet_type '{bet_type}'")

    model_names = list(ENSEMBLE_WEIGHTS.keys())

    meta_all: dict = {}
    meta_path = os.path.join(MODELS_DIR, f"mlb_{bet_type}_metadata.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path) as fh:
                meta_all = json.load(fh)
        except Exception:
            logger.warning("[mlb_trainer] Could not read metadata from %s", meta_path)

    loaded: dict = {}
    for model_name in model_names:
        model_path = os.path.join(MODELS_DIR, f"mlb_{bet_type}_{model_name}.joblib")
        if not os.path.exists(model_path):
            logger.debug("[mlb_trainer] No saved file at %s", model_path)
            continue
        try:
            model = joblib.load(model_path)
            meta = meta_all.get(model_name, {})
            loaded[model_name] = {
                "model": model,
                "auc": meta.get("auc"),
                "brier": meta.get("brier"),
                "accuracy": meta.get("accuracy"),
                "feature_importance": meta.get("feature_importance_top10", {}),
            }
            logger.info("[mlb_trainer] Loaded %-20s (AUC=%s)", model_name, meta.get("auc"))
        except Exception:
            logger.exception("[mlb_trainer] Failed to load %s; skipping", model_name)

    if not loaded:
        logger.warning(
            "[mlb_trainer] No saved models found for bet_type='%s' in %s",
            bet_type, MODELS_DIR,
        )
    return loaded


def get_ensemble_probability(models: dict, features: pd.Series) -> dict:
    """
    Compute per-model and ensemble probabilities for a single game.

    Ensemble is a weighted average with weights:
        xgboost=35%  lightgbm=35%  random_forest=20%  logistic_regression=10%

    When a model is absent the remaining weights are renormalised so they
    always sum to 1.

    Parameters
    ----------
    models   : dict returned by load_mlb_models / train_mlb_models
    features : pd.Series whose index includes MLB_FEATURE_COLUMNS

    Returns
    -------
    dict with keys: model names (float probs), 'ensemble_mean', 'ensemble_std'
    """
    X = (
        pd.DataFrame([features])
        .reindex(columns=MLB_FEATURE_COLUMNS)
        .astype(float)
    )

    raw_probs: dict[str, float] = {}
    for model_name, info in models.items():
        try:
            p = float(info["model"].predict_proba(X.values)[0, 1])
            raw_probs[model_name] = round(p, 4)
        except Exception:
            logger.warning(
                "[mlb_trainer] predict_proba failed for %s; excluding from ensemble",
                model_name,
            )

    if not raw_probs:
        logger.error("[mlb_trainer] All models failed — returning 0.50 fallback")
        return {"ensemble_mean": 0.50, "ensemble_std": 0.0}

    # Weighted average with normalisation for missing models
    total_weight = sum(ENSEMBLE_WEIGHTS.get(n, 0.0) for n in raw_probs)
    if total_weight <= 0:
        total_weight = len(raw_probs)
        ensemble_mean = float(np.mean(list(raw_probs.values())))
    else:
        ensemble_mean = sum(
            ENSEMBLE_WEIGHTS.get(n, 0.0) * p / total_weight
            for n, p in raw_probs.items()
        )

    ensemble_std = float(np.std(list(raw_probs.values()))) if len(raw_probs) > 1 else 0.0

    return {
        **raw_probs,
        "ensemble_mean": round(ensemble_mean, 4),
        "ensemble_std": round(ensemble_std, 4),
    }
