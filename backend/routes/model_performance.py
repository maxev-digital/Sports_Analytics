"""
Model Performance API Routes
Tracks ML model performance, accuracy, and improvement over time across all sports
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import pandas as pd
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/model-performance", tags=["model-performance"])

# Data paths
TRACKING_DIR = Path(__file__).parent.parent / "data" / "tracking"
PREDICTIONS_LOG = TRACKING_DIR / "predictions_log_multi_bet.csv"
RESULTS_LOG = TRACKING_DIR / "results_log.csv"
PERFORMANCE_SUMMARY = TRACKING_DIR / "performance_summary.csv"


@router.get("/overview")
async def get_performance_overview(
    sport: Optional[str] = None,
    model: Optional[str] = None,
    bet_type: Optional[str] = None,
    days: int = 30
):
    """
    Get overall model performance metrics

    Args:
        sport: Filter by sport (nba, ncaab, nfl, nhl, ncaaf)
        model: Filter by model (ensemble, xgboost, random_forest, lightgbm, linear_regression)
        bet_type: Filter by bet type (totals, spreads, moneyline)
        days: Number of days of history to include (default 30)

    Returns:
        Overall performance metrics including win rate, ROI, accuracy by confidence level
    """
    try:
        if not PREDICTIONS_LOG.exists() or not RESULTS_LOG.exists():
            return {
                "error": "No tracking data available yet",
                "message": "Model performance tracking will begin once predictions are logged",
                "total_predictions": 0,
                "total_results": 0
            }

        # Load predictions and results
        predictions_df = pd.read_csv(PREDICTIONS_LOG)
        results_df = pd.read_csv(RESULTS_LOG)

        # Filter by date
        cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days)
        predictions_df['date_predicted'] = pd.to_datetime(predictions_df['date_predicted'], format='mixed', errors='coerce')
        predictions_df = predictions_df[predictions_df['date_predicted'] >= cutoff_date]

        # Apply filters
        if sport:
            predictions_df = predictions_df[predictions_df['sport'].str.lower() == sport.lower()]
        if model:
            predictions_df = predictions_df[predictions_df['model'].str.lower() == model.lower()]
        if bet_type:
            predictions_df = predictions_df[predictions_df['bet_type'].str.lower() == bet_type.lower()]

        # Merge predictions with results
        merged_df = predictions_df.merge(
            results_df,
            on='prediction_id',
            how='inner'
        )

        if len(merged_df) == 0:
            return {
                "message": "No completed predictions in selected timeframe",
                "total_predictions": len(predictions_df),
                "total_results": 0,
                "filters": {
                    "sport": sport or "all",
                    "model": model or "all",
                    "bet_type": bet_type or "all",
                    "days": days
                }
            }

        # Calculate overall metrics
        total_bets = len(merged_df)
        wins = len(merged_df[merged_df['result'] == 'WIN'])
        losses = len(merged_df[merged_df['result'] == 'LOSS'])
        pushes = len(merged_df[merged_df['result'] == 'PUSH'])
        win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0

        # ROI calculation
        total_profit_loss = merged_df['profit_loss'].sum() if 'profit_loss' in merged_df.columns else 0
        roi = (total_profit_loss / total_bets) * 100 if total_bets > 0 else 0

        # Average edge
        avg_edge = merged_df['edge'].abs().mean()

        # Performance by confidence level
        confidence_levels = ['HIGH', 'MEDIUM', 'LOW']
        confidence_stats = {}
        for conf in confidence_levels:
            conf_df = merged_df[merged_df['confidence'] == conf]
            if len(conf_df) > 0:
                conf_wins = len(conf_df[conf_df['result'] == 'WIN'])
                conf_total = len(conf_df[conf_df['result'].isin(['WIN', 'LOSS'])])
                confidence_stats[conf.lower()] = {
                    "total": len(conf_df),
                    "wins": conf_wins,
                    "win_rate": conf_wins / conf_total if conf_total > 0 else 0,
                    "roi": (conf_df['profit_loss'].sum() / len(conf_df)) * 100 if 'profit_loss' in conf_df.columns else 0
                }

        # Performance by sport
        sports_stats = {}
        for sport_name in merged_df['sport'].unique():
            sport_df = merged_df[merged_df['sport'] == sport_name]
            sport_wins = len(sport_df[sport_df['result'] == 'WIN'])
            sport_total = len(sport_df[sport_df['result'].isin(['WIN', 'LOSS'])])
            sports_stats[sport_name.lower()] = {
                "total": len(sport_df),
                "wins": sport_wins,
                "win_rate": sport_wins / sport_total if sport_total > 0 else 0
            }

        # Performance by model
        models_stats = {}
        for model_name in merged_df['model'].unique():
            model_df = merged_df[merged_df['model'] == model_name]
            model_wins = len(model_df[model_df['result'] == 'WIN'])
            model_total = len(model_df[model_df['result'].isin(['WIN', 'LOSS'])])
            models_stats[model_name.lower()] = {
                "total": len(model_df),
                "wins": model_wins,
                "win_rate": model_wins / model_total if model_total > 0 else 0
            }

        return {
            "summary": {
                "total_predictions": total_bets,
                "wins": wins,
                "losses": losses,
                "pushes": pushes,
                "win_rate": round(win_rate, 4),
                "roi": round(roi, 2),
                "avg_edge": round(avg_edge, 2),
                "units_won": round(total_profit_loss, 2) if 'profit_loss' in merged_df.columns else 0
            },
            "by_confidence": confidence_stats,
            "by_sport": sports_stats,
            "by_model": models_stats,
            "filters": {
                "sport": sport or "all",
                "model": model or "all",
                "bet_type": bet_type or "all",
                "days": days
            },
            "generated_at": datetime.utcnow().isoformat() + 'Z'
        }

    except Exception as e:
        logger.error(f"Error generating performance overview: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_performance_history(
    sport: Optional[str] = None,
    model: Optional[str] = None,
    bet_type: Optional[str] = None,
    days: int = 90
):
    """
    Get historical performance data over time (for charts)

    Returns daily/weekly performance metrics to show improvement over time
    """
    try:
        if not PREDICTIONS_LOG.exists() or not RESULTS_LOG.exists():
            return {
                "error": "No tracking data available yet",
                "history": []
            }

        # Load predictions and results
        predictions_df = pd.read_csv(PREDICTIONS_LOG)
        results_df = pd.read_csv(RESULTS_LOG)

        # Filter by date
        cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days)
        predictions_df['date_predicted'] = pd.to_datetime(predictions_df['date_predicted'], format='mixed', errors='coerce')
        predictions_df['game_date_dt'] = pd.to_datetime(predictions_df['game_date'], format='mixed', errors='coerce')
        predictions_df = predictions_df[predictions_df['date_predicted'] >= cutoff_date]

        # Apply filters
        if sport:
            predictions_df = predictions_df[predictions_df['sport'].str.lower() == sport.lower()]
        if model:
            predictions_df = predictions_df[predictions_df['model'].str.lower() == model.lower()]
        if bet_type:
            predictions_df = predictions_df[predictions_df['bet_type'].str.lower() == bet_type.lower()]

        # Merge with results
        merged_df = predictions_df.merge(
            results_df,
            on='prediction_id',
            how='inner'
        )

        if len(merged_df) == 0:
            return {
                "message": "No completed predictions in selected timeframe",
                "history": []
            }

        # Group by week
        merged_df['week'] = merged_df['game_date_dt'].dt.to_period('W').astype(str)

        history_data = []
        for week in sorted(merged_df['week'].unique()):
            week_df = merged_df[merged_df['week'] == week]
            week_wins = len(week_df[week_df['result'] == 'WIN'])
            week_total = len(week_df[week_df['result'].isin(['WIN', 'LOSS'])])
            week_win_rate = week_wins / week_total if week_total > 0 else 0
            week_profit = week_df['profit_loss'].sum() if 'profit_loss' in week_df.columns else 0

            history_data.append({
                "period": week,
                "predictions": len(week_df),
                "wins": week_wins,
                "win_rate": round(week_win_rate, 4),
                "roi": round((week_profit / len(week_df)) * 100, 2) if len(week_df) > 0 else 0,
                "units_won": round(week_profit, 2)
            })

        return {
            "history": history_data,
            "filters": {
                "sport": sport or "all",
                "model": model or "all",
                "bet_type": bet_type or "all",
                "days": days
            },
            "generated_at": datetime.utcnow().isoformat() + 'Z'
        }

    except Exception as e:
        logger.error(f"Error generating performance history: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_models_info():
    """
    Get information about all available models, their purposes, and current performance
    """
    try:
        # Load model metadata
        ml_models_dir = Path(__file__).parent.parent / "ml" / "models"

        models_info = {
            "nba": {
                "ensemble": {
                    "name": "Edge Lab Ensemble",
                    "description": "Combines predictions from all 4 base models using weighted averaging based on historical performance",
                    "markets": ["totals", "spreads", "moneyline"],
                    "strength": "Most reliable - averages out individual model biases"
                },
                "xgboost": {
                    "name": "XGBoost",
                    "description": "Gradient boosting model optimized for capturing complex non-linear relationships in team statistics",
                    "markets": ["totals", "spreads", "moneyline"],
                    "strength": "Best for outlier games with unusual team dynamics"
                },
                "random_forest": {
                    "name": "Random Forest",
                    "description": "Ensemble of decision trees providing stable predictions across different game scenarios",
                    "markets": ["totals", "spreads", "moneyline"],
                    "strength": "Most stable - resistant to overfitting"
                },
                "lightgbm": {
                    "name": "LightGBM",
                    "description": "Fast gradient boosting model ideal for real-time predictions during live games",
                    "markets": ["totals", "spreads", "moneyline"],
                    "strength": "Fastest inference time for live betting"
                },
                "linear_regression": {
                    "name": "Linear Regression",
                    "description": "Baseline model using linear relationships between features (totals/spreads) or logistic regression (moneyline)",
                    "markets": ["totals", "spreads", "moneyline"],
                    "strength": "Interpretable - shows direct feature importance"
                }
            }
        }

        # Replicate structure for other sports
        for sport in ["ncaab", "nhl", "nfl", "ncaaf"]:
            models_info[sport] = models_info["nba"].copy()

        # Add real performance data if available
        if PREDICTIONS_LOG.exists() and RESULTS_LOG.exists():
            try:
                predictions_df = pd.read_csv(PREDICTIONS_LOG)
                results_df = pd.read_csv(RESULTS_LOG)
                merged_df = predictions_df.merge(results_df, on='prediction_id', how='inner')

                for sport in models_info.keys():
                    sport_df = merged_df[merged_df['sport'].str.lower() == sport.lower()]
                    for model_key in models_info[sport].keys():
                        model_df = sport_df[sport_df['model'].str.lower() == model_key.lower()]
                        if len(model_df) > 0:
                            wins = len(model_df[model_df['result'] == 'WIN'])
                            total = len(model_df[model_df['result'].isin(['WIN', 'LOSS'])])
                            models_info[sport][model_key]["performance"] = {
                                "predictions": len(model_df),
                                "win_rate": round(wins / total, 4) if total > 0 else 0,
                                "last_updated": datetime.utcnow().isoformat() + 'Z'
                            }
            except Exception as e:
                logger.warning(f"Could not load performance data: {e}")

        return {
            "models": models_info,
            "total_sports": len(models_info),
            "models_per_sport": 5,
            "total_models": len(models_info) * 5,
            "generated_at": datetime.utcnow().isoformat() + 'Z'
        }

    except Exception as e:
        logger.error(f"Error getting models info: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
