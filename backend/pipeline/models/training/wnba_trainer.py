"""
WNBA model training pipeline.

Adaptive training strategy
---------------------------
- 4+ seasons of data : walk-forward (train on all-but-last, evaluate on last)
- < 4 seasons        : 5-fold stratified CV for metrics, final model trained on
                       all available data to maximise sample use on thin datasets

Compared with the MLB trainer:
  - min_samples_leaf = 5  (vs 10) — WNBA has fewer games per season
  - n_estimators     = 100 (vs 200) — avoid overfitting thin data
  - Bet types        : 'spread' and 'total' only (no ML market)

Public API
----------
train_wnba_models(historical_df, bet_type) -> dict
save_wnba_models(trained_models, bet_type)
load_wnba_models(bet_type) -> dict
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
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import lightgbm as lgb

from pipeline.models.features.wnba_features import WNBA_FEATURE_COLUMNS
from pipeline.config import now_cst

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODELS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "saved")
)

TARGET_MAP: dict[str, str] = {
    "spread": "home_covered",
    "total": "went_over",
}

ENSEMBLE_WEIGHTS: dict[str, float] = {
    "xgboost": 0.35,
    "lightgbm": 0.35,
    "random_forest": 0.20,
    "logistic_regression": 0.10,
}

# Season threshold below which we fall back to CV rather than walk-forward
MIN_SEASONS_FOR_WALKFORWARD = 4


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_base_estimators() -> dict[str, Pipeline]:
    """
    Return unfitted sklearn Pipelines with WNBA-tuned hyperparameters.

    Key differences vs MLB:
      - n_estimators = 100 (smaller ensemble; fewer samples per class)
      - min_samples_leaf = 5 (vs 10; allows finer splits on a smaller dataset)
    """
    return {
        "random_forest": Pipeline([
            ("clf", RandomForestClassifier(
                n_estimators=100,
                max_depth=6,
                min_samples_leaf=5,
                max_features="sqrt",
                class_weight="balanced",
                n_jobs=-1,
                random_state=42,
            )),
        ]),
        "xgboost": Pipeline([
            ("clf", xgb.XGBClassifier(
                n_estimators=100,
                max_depth=5,
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
                n_estimators=100,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.8,
                feature_fraction=0.8,
                min_child_samples=5,
                class_weight="balanced",
                n_jobs=-1,
                random_state=42,
                verbose=-1,
            )),
        ]),
        "logistic_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(
                C=0.5,          # slightly less regularisation than MLB; smaller n
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
    """Average feature importances across all CV-fold calibrators."""
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
    if bet_type not in TARGET_MAP:
        raise ValueError(
            f"Unknown bet_type '{bet_type}'. Valid options: {list(TARGET_MAP)}"
        )
    target_col = TARGET_MAP[bet_type]
    required = WNBA_FEATURE_COLUMNS + ["season", target_col]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"historical_df is missing {len(missing)} column(s): {missing[:10]}"
            + (" ..." if len(missing) > 10 else "")
        )
    return target_col


def _train_walkforward(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    model_name: str,
    pipe: Pipeline,
) -> Optional[dict]:
    """Fit, calibrate, and evaluate a single model via walk-forward split."""
    try:
        calibrated = CalibratedClassifierCV(pipe, method="isotonic", cv=5)
        calibrated.fit(X_train, y_train)

        proba = calibrated.predict_proba(X_val)[:, 1]
        preds = (proba >= 0.5).astype(int)

        return {
            "model": calibrated,
            "auc": round(float(roc_auc_score(y_val, proba)), 4),
            "brier": round(float(brier_score_loss(y_val, proba)), 4),
            "accuracy": round(float(accuracy_score(y_val, preds)), 4),
        }
    except Exception:
        logger.exception("[wnba_trainer] Walk-forward training failed for %s", model_name)
        return None


def _train_cv(
    X_all: np.ndarray,
    y_all: np.ndarray,
    model_name: str,
    pipe: Pipeline,
) -> Optional[dict]:
    """
    Thin-data path: evaluate via 5-fold stratified CV, then fit final model
    on all available data.

    Metrics (AUC, Brier, Accuracy) are computed on out-of-fold predictions to
    give an honest estimate without a dedicated held-out season.
    """
    try:
        cv_outer = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

        # Out-of-fold probability predictions for metric calculation
        # Use the uncalibrated pipeline so CV predictions are meaningful
        oof_proba = cross_val_predict(
            pipe, X_all, y_all, cv=cv_outer, method="predict_proba"
        )[:, 1]

        auc = round(float(roc_auc_score(y_all, oof_proba)), 4)
        brier = round(float(brier_score_loss(y_all, oof_proba)), 4)
        acc = round(float(accuracy_score(y_all, (oof_proba >= 0.5).astype(int))), 4)

        # Final model trained on ALL data with isotonic calibration
        calibrated = CalibratedClassifierCV(pipe, method="isotonic", cv=5)
        calibrated.fit(X_all, y_all)

        return {
            "model": calibrated,
            "auc": auc,
            "brier": brier,
            "accuracy": acc,
        }
    except Exception:
        logger.exception("[wnba_trainer] CV training failed for %s", model_name)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def train_wnba_models(
    historical_df: pd.DataFrame,
    bet_type: str = "total",
) -> dict:
    """
    Train four model types for the given bet_type.

    Strategy
    --------
    - >= 4 seasons available : walk-forward (last season = held-out validation)
    - <  4 seasons available : 5-fold stratified CV for metrics; final model
                               trained on all data

    Parameters
    ----------
    historical_df : pd.DataFrame
        Must contain 'season', all WNBA_FEATURE_COLUMNS, and the target column.
    bet_type : {'spread', 'total'}

    Returns
    -------
    dict[model_name -> {model, auc, brier, accuracy, feature_importance}]
    """
    target_col = _validate_dataframe(historical_df, bet_type)

    df = (
        historical_df
        .dropna(subset=WNBA_FEATURE_COLUMNS + [target_col])
        .copy()
        .sort_values("season")
    )

    seasons = sorted(df["season"].unique())
    n_seasons = len(seasons)

    if n_seasons < 2:
        raise ValueError(
            f"Need at least 2 seasons of data; got {n_seasons}: {seasons}"
        )

    use_walkforward = n_seasons >= MIN_SEASONS_FOR_WALKFORWARD
    logger.info(
        "[wnba_trainer] bet_type=%s | seasons=%s | strategy=%s",
        bet_type,
        seasons,
        "walk-forward" if use_walkforward else "5-fold-cv",
    )

    X_all = df[WNBA_FEATURE_COLUMNS].astype(float).values
    y_all = df[target_col].astype(int).values

    if use_walkforward:
        val_season = seasons[-1]
        train_seasons = seasons[:-1]
        train_mask = df["season"].isin(train_seasons).values
        val_mask = (df["season"] == val_season).values

        X_train, y_train = X_all[train_mask], y_all[train_mask]
        X_val, y_val = X_all[val_mask], y_all[val_mask]

        if len(X_val) == 0:
            raise ValueError(
                f"Validation set for season={val_season} is empty."
            )

        logger.info(
            "[wnba_trainer] Train rows=%d (pos=%.1f%%) | Val rows=%d (pos=%.1f%%)",
            len(y_train), y_train.mean() * 100,
            len(y_val), y_val.mean() * 100,
        )
    else:
        X_train = y_train = X_val = y_val = None  # unused in CV path

    base_estimators = _build_base_estimators()
    results: dict = {}

    for model_name, pipe in base_estimators.items():
        logger.info("[wnba_trainer] Training %s ...", model_name)

        if use_walkforward:
            outcome = _train_walkforward(X_train, y_train, X_val, y_val, model_name, pipe)
        else:
            outcome = _train_cv(X_all, y_all, model_name, pipe)

        if outcome is None:
            continue

        feat_imp = _extract_feature_importance(outcome["model"], WNBA_FEATURE_COLUMNS)
        outcome["feature_importance"] = feat_imp

        results[model_name] = outcome
        logger.info(
            "[wnba_trainer] %s done — AUC=%.4f  Brier=%.4f  Acc=%.4f",
            model_name, outcome["auc"], outcome["brier"], outcome["accuracy"],
        )

    if not results:
        raise RuntimeError("[wnba_trainer] All model types failed to train. Check logs.")

    return results


def save_wnba_models(trained_models: dict, bet_type: str) -> None:
    """
    Persist each trained model and a companion JSON metadata file.

    Paths
    -----
    Model   : pipeline/models/saved/wnba_{bet_type}_{model_name}.joblib
    Metadata: pipeline/models/saved/wnba_{bet_type}_metadata.json
    """
    if bet_type not in TARGET_MAP:
        raise ValueError(f"Unknown bet_type '{bet_type}'")

    os.makedirs(MODELS_DIR, exist_ok=True)
    trained_at = now_cst().isoformat()
    meta_all: dict = {}

    for model_name, info in trained_models.items():
        model_path = os.path.join(MODELS_DIR, f"wnba_{bet_type}_{model_name}.joblib")
        joblib.dump(info["model"], model_path, compress=3)
        logger.info("[wnba_trainer] Saved %-20s → %s", model_name, model_path)

        top10 = dict(
            sorted(
                info.get("feature_importance", {}).items(),
                key=lambda kv: kv[1],
                reverse=True,
            )[:10]
        )

        meta_all[model_name] = {
            "sport": "wnba",
            "bet_type": bet_type,
            "auc": info["auc"],
            "brier": info["brier"],
            "accuracy": info["accuracy"],
            "trained_at": trained_at,
            "feature_importance_top10": top10,
        }

    meta_path = os.path.join(MODELS_DIR, f"wnba_{bet_type}_metadata.json")
    with open(meta_path, "w") as fh:
        json.dump(meta_all, fh, indent=2)
    logger.info("[wnba_trainer] Metadata written → %s", meta_path)


def load_wnba_models(bet_type: str) -> dict:
    """
    Load all saved models for the given bet_type.

    Returns an empty dict if no saved models are found for that bet_type.
    """
    if bet_type not in TARGET_MAP:
        raise ValueError(f"Unknown bet_type '{bet_type}'")

    model_names = list(ENSEMBLE_WEIGHTS.keys())

    meta_all: dict = {}
    meta_path = os.path.join(MODELS_DIR, f"wnba_{bet_type}_metadata.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path) as fh:
                meta_all = json.load(fh)
        except Exception:
            logger.warning("[wnba_trainer] Could not read metadata from %s", meta_path)

    loaded: dict = {}
    for model_name in model_names:
        model_path = os.path.join(MODELS_DIR, f"wnba_{bet_type}_{model_name}.joblib")
        if not os.path.exists(model_path):
            logger.debug("[wnba_trainer] No saved file at %s", model_path)
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
            logger.info("[wnba_trainer] Loaded %-20s (AUC=%s)", model_name, meta.get("auc"))
        except Exception:
            logger.exception("[wnba_trainer] Failed to load %s; skipping", model_name)

    if not loaded:
        logger.warning(
            "[wnba_trainer] No saved models found for bet_type='%s' in %s",
            bet_type, MODELS_DIR,
        )
    return loaded


def get_ensemble_probability(models: dict, features: pd.Series) -> dict:
    """
    Compute per-model and ensemble probabilities for a single WNBA game.

    Ensemble weights: xgboost=35%  lightgbm=35%  random_forest=20%
                      logistic_regression=10%

    Missing models are excluded and remaining weights are renormalised.

    Parameters
    ----------
    models   : dict from load_wnba_models / train_wnba_models
    features : pd.Series whose index includes WNBA_FEATURE_COLUMNS

    Returns
    -------
    dict with model-name probability keys, 'ensemble_mean', 'ensemble_std'
    """
    X = (
        pd.DataFrame([features])
        .reindex(columns=WNBA_FEATURE_COLUMNS)
        .astype(float)
    )

    raw_probs: dict[str, float] = {}
    for model_name, info in models.items():
        try:
            p = float(info["model"].predict_proba(X.values)[0, 1])
            raw_probs[model_name] = round(p, 4)
        except Exception:
            logger.warning(
                "[wnba_trainer] predict_proba failed for %s; excluding from ensemble",
                model_name,
            )

    if not raw_probs:
        logger.error("[wnba_trainer] All models failed — returning 0.50 fallback")
        return {"ensemble_mean": 0.50, "ensemble_std": 0.0}

    total_weight = sum(ENSEMBLE_WEIGHTS.get(n, 0.0) for n in raw_probs)
    if total_weight <= 0:
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
