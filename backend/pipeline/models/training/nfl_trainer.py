"""
NFL cover-prediction model — Random Forest, calibrated (Task 14).

Public API
----------
build_training_frame(seasons) -> pd.DataFrame
train_nfl_cover_model(df) -> dict
save_nfl_cover_model(trained) -> None
load_nfl_cover_model() -> dict | None

Same conventions as mlb_trainer.py (CalibratedClassifierCV isotonic,
joblib + JSON metadata saved to pipeline/models/saved/), scoped down
to a single model since Task 14 asks for "a meaningful random forest"
predicting cover probability, not a full multi-model ensemble.

Features
--------
spread_close, total_close, rating_gap (home power rating - away power
rating, computed from prior-games-only point differential per game -
same no-lookahead methodology as scripts/backtest_nfl_rating_overlay.py),
is_division_game.

Target: home_covered (bool)
"""
from __future__ import annotations

import json
import logging
import os
from collections import defaultdict
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split

from pipeline.config import now_cst
from pipeline.db.connection import execute_query

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "saved"))
MIN_GAMES_PLAYED = 3

FEATURE_COLUMNS = ["spread_close", "total_close", "rating_gap", "is_division_game"]

_DIVISIONS: dict[str, str] = {
    "Buffalo Bills": "AFC East", "Miami Dolphins": "AFC East",
    "New England Patriots": "AFC East", "New York Jets": "AFC East",
    "Baltimore Ravens": "AFC North", "Cincinnati Bengals": "AFC North",
    "Cleveland Browns": "AFC North", "Pittsburgh Steelers": "AFC North",
    "Houston Texans": "AFC South", "Indianapolis Colts": "AFC South",
    "Jacksonville Jaguars": "AFC South", "Tennessee Titans": "AFC South",
    "Denver Broncos": "AFC West", "Kansas City Chiefs": "AFC West",
    "Las Vegas Raiders": "AFC West", "Los Angeles Chargers": "AFC West",
    "Dallas Cowboys": "NFC East", "New York Giants": "NFC East",
    "Philadelphia Eagles": "NFC East", "Washington Commanders": "NFC East",
    "Chicago Bears": "NFC North", "Detroit Lions": "NFC North",
    "Green Bay Packers": "NFC North", "Minnesota Vikings": "NFC North",
    "Atlanta Falcons": "NFC South", "Carolina Panthers": "NFC South",
    "New Orleans Saints": "NFC South", "Tampa Bay Buccaneers": "NFC South",
    "Arizona Cardinals": "NFC West", "Los Angeles Rams": "NFC West",
    "San Francisco 49ers": "NFC West", "Seattle Seahawks": "NFC West",
}


def build_training_frame(seasons: list[int]) -> pd.DataFrame:
    """
    Build a feature/target dataframe from nfl_historical_odds, computing
    rating_gap with the same no-lookahead (prior-games-only) methodology
    used by scripts/backtest_nfl_rating_overlay.py.
    """
    rows = execute_query(
        """SELECT season, week, home_team, away_team, spread_close, total_close,
                  home_score, away_score, home_covered
           FROM nfl_historical_odds
           WHERE sport = 'nfl' AND season = ANY(%s)
             AND spread_close IS NOT NULL AND total_close IS NOT NULL
             AND home_covered IS NOT NULL
           ORDER BY season, week, game_date""",
        (seasons,),
    )

    records: list[dict] = []
    for season in sorted({r["season"] for r in rows}):
        season_rows = [r for r in rows if r["season"] == season]
        history: dict[str, list[float]] = defaultdict(list)

        for r in season_rows:
            home, away = r["home_team"], r["away_team"]
            home_hist, away_hist = history[home], history[away]

            if len(home_hist) >= MIN_GAMES_PLAYED and len(away_hist) >= MIN_GAMES_PLAYED:
                home_rating = sum(home_hist) / len(home_hist)
                away_rating = sum(away_hist) / len(away_hist)
                records.append({
                    "spread_close": float(r["spread_close"]),
                    "total_close": float(r["total_close"]),
                    "rating_gap": home_rating - away_rating,
                    "is_division_game": int(_DIVISIONS.get(home) == _DIVISIONS.get(away)),
                    "home_covered": bool(r["home_covered"]),
                })

            margin = r["home_score"] - r["away_score"]
            history[home].append(margin)
            history[away].append(-margin)

    return pd.DataFrame.from_records(records)


def train_nfl_cover_model(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> dict:
    """Train + calibrate a RandomForestClassifier predicting home_covered."""
    if len(df) < 50:
        raise ValueError(f"Only {len(df)} training rows - need at least 50 for a meaningful split.")

    X = df[FEATURE_COLUMNS]
    y = df["home_covered"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    base = RandomForestClassifier(
        n_estimators=200, max_depth=5, min_samples_leaf=10, random_state=random_state
    )
    calibrated = CalibratedClassifierCV(base, method="isotonic", cv=5)
    calibrated.fit(X_train, y_train)

    pred_proba = calibrated.predict_proba(X_test)[:, 1]
    pred_class = (pred_proba >= 0.5).astype(int)

    metrics = {
        "n_train": len(X_train),
        "n_test": len(X_test),
        "accuracy": round(accuracy_score(y_test, pred_class), 4),
        "brier_score": round(brier_score_loss(y_test, pred_proba), 4),
        "roc_auc": round(roc_auc_score(y_test, pred_proba), 4),
        "trained_at": now_cst().isoformat(),
        "feature_columns": FEATURE_COLUMNS,
    }
    logger.info("[nfl_trainer] Trained cover model: %s", metrics)

    return {"model": calibrated, "metrics": metrics}


def save_nfl_cover_model(trained: dict) -> None:
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "nfl_cover_rf.joblib")
    meta_path = os.path.join(MODELS_DIR, "nfl_cover_metadata.json")

    joblib.dump(trained["model"], model_path, compress=3)
    with open(meta_path, "w") as f:
        json.dump(trained["metrics"], f, indent=2)

    logger.info("[nfl_trainer] Saved model to %s", model_path)


def load_nfl_cover_model() -> Optional[dict]:
    model_path = os.path.join(MODELS_DIR, "nfl_cover_rf.joblib")
    meta_path = os.path.join(MODELS_DIR, "nfl_cover_metadata.json")

    if not (os.path.exists(model_path) and os.path.exists(meta_path)):
        logger.warning("[nfl_trainer] No saved NFL cover model found at %s", MODELS_DIR)
        return None

    model = joblib.load(model_path)
    with open(meta_path) as f:
        metrics = json.load(f)
    return {"model": model, "metrics": metrics}


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", nargs="+", type=int, default=[2023, 2024, 2025])
    args = parser.parse_args()

    frame = build_training_frame(args.seasons)
    print(f"Training frame: {len(frame)} rows")
    result = train_nfl_cover_model(frame)
    save_nfl_cover_model(result)
    print(json.dumps(result["metrics"], indent=2))
