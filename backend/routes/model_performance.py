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
import math
import sqlite3

logger = logging.getLogger(__name__)

def safe_float(value):
    """Convert to float, returning None for NaN/inf values"""
    if value is None:
        return None
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None

def safe_value(value):
    """Convert pandas values to JSON-serializable types, handling NaN"""
    if pd.isna(value):
        return None
    # Convert numpy types to Python types
    if hasattr(value, 'item'):
        return value.item()
    return value

router = APIRouter(prefix="/api/model-performance", tags=["model-performance"])

# Data paths
TRACKING_DIR = Path(__file__).parent.parent / "data" / "tracking"
PREDICTIONS_LOG = TRACKING_DIR / "predictions_log_multi_bet.csv"
RESULTS_LOG = TRACKING_DIR / "results_log.csv"
PERFORMANCE_SUMMARY = TRACKING_DIR / "performance_summary.csv"
PREDICTIONS_DB = Path(__file__).parent.parent / "ml" / "predictions.db"  # SINGLE SOURCE OF TRUTH


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
        # Read from predictions.db - SINGLE SOURCE OF TRUTH
        if not PREDICTIONS_DB.exists():
            return {
                "error": "No tracking data available yet",
                "message": "Database not found",
                "total_predictions": 0,
                "total_results": 0
            }

        # Load results from database (contains all predictions with results)
        conn = sqlite3.connect(str(PREDICTIONS_DB))
        merged_df = pd.read_sql_query("SELECT * FROM results", conn)
        conn.close()

        # Add aliased columns for compatibility (database uses predicted_value/market_value)
        if 'predicted_total' not in merged_df.columns and 'predicted_value' in merged_df.columns:
            merged_df['predicted_total'] = merged_df['predicted_value']
        if 'market_total' not in merged_df.columns and 'market_value' in merged_df.columns:
            merged_df['market_total'] = merged_df['market_value']

        # Calculate edge column
        merged_df['edge'] = merged_df['predicted_total'] - merged_df['market_total']

        # Filter by date
        cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days)
        merged_df['game_date'] = pd.to_datetime(merged_df['game_date'], format='mixed', errors='coerce')
        merged_df = merged_df[merged_df['game_date'] >= cutoff_date]

        # Apply filters
        if sport:
            merged_df = merged_df[merged_df['sport'].str.lower() == sport.lower()]
        if model:
            merged_df = merged_df[merged_df['model'].str.lower() == model.lower()]
        if bet_type:
            merged_df = merged_df[merged_df['bet_type'].str.lower() == bet_type.lower()]

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
        # profit_loss is in dollars, convert to units by dividing by 100 (standard unit size)
        total_profit_loss_dollars = merged_df['profit_loss'].sum() if 'profit_loss' in merged_df.columns else 0
        units_won = total_profit_loss_dollars / 100  # Convert dollars to units
        # ROI should be calculated on graded bets only (wins + losses), not including pushes
        graded_bets = wins + losses
        roi = (units_won / graded_bets) * 100 if graded_bets > 0 else 0

        # Average edge
        avg_edge = merged_df['edge'].abs().mean()

        # Get last updated date (most recent game date)
        last_updated = merged_df['game_date'].max() if 'game_date' in merged_df.columns else None

        # Performance by confidence level
        confidence_levels = ['HIGH', 'MEDIUM', 'LOW']
        confidence_stats = {}
        for conf in confidence_levels:
            conf_df = merged_df[merged_df['confidence'] == conf]
            if len(conf_df) > 0:
                conf_wins = len(conf_df[conf_df['result'] == 'WIN'])
                conf_total = len(conf_df[conf_df['result'].isin(['WIN', 'LOSS'])])
                # Convert profit_loss from dollars to units for confidence stats
                conf_units_won = conf_df['profit_loss'].sum() / 100 if 'profit_loss' in conf_df.columns else 0
                confidence_stats[conf.lower()] = {
                    "total": len(conf_df),
                    "wins": conf_wins,
                    "win_rate": conf_wins / conf_total if conf_total > 0 else 0,
                    "roi": (conf_units_won / len(conf_df)) * 100 if len(conf_df) > 0 else 0
                }

        # Performance by sport
        sports_stats = {}
        for sport_name in merged_df['sport'].unique():
            # Skip NaN values
            if pd.isna(sport_name):
                continue
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
            # Skip NaN values
            if pd.isna(model_name):
                continue
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
                "units_won": round(units_won, 2),
                "last_updated": last_updated
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
        # Read from predictions.db - SINGLE SOURCE OF TRUTH
        if not PREDICTIONS_DB.exists():
            return {
                "error": "No tracking data available yet",
                "history": []
            }

        # Load results from database
        conn = sqlite3.connect(str(PREDICTIONS_DB))
        merged_df = pd.read_sql_query("SELECT * FROM results", conn)
        conn.close()

        # Convert dates
        merged_df['game_date_dt'] = pd.to_datetime(merged_df['game_date'], format='mixed', errors='coerce')

        # Filter by game_date (not prediction date)
        if days > 0:
            cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days)
            merged_df = merged_df[merged_df['game_date_dt'] >= cutoff_date]

        # Apply sport/model/bet_type filters
        if sport:
            merged_df = merged_df[merged_df['sport'].str.lower() == sport.lower()]
        if model:
            merged_df = merged_df[merged_df['model'].str.lower() == model.lower()]
        if bet_type:
            merged_df = merged_df[merged_df['bet_type'].str.lower() == bet_type.lower()]

        if len(merged_df) == 0:
            return {
                "message": "No completed predictions in selected timeframe",
                "history": []
            }

        # Group by day for better chart granularity
        # Convert game_date to date string for grouping
        merged_df['date'] = merged_df['game_date_dt'].dt.date

        history_data = []
        cumulative_wins = 0
        cumulative_total = 0
        cumulative_profit = 0

        for date in sorted(merged_df['date'].unique()):
            day_df = merged_df[merged_df['date'] == date]
            day_wins = len(day_df[day_df['result'] == 'WIN'])
            day_losses = len(day_df[day_df['result'] == 'LOSS'])
            day_total = day_wins + day_losses
            day_win_rate = day_wins / day_total if day_total > 0 else 0
            # profit_loss is in dollars, convert to units
            day_profit_dollars = day_df['profit_loss'].sum() if 'profit_loss' in day_df.columns else 0
            day_profit_units = day_profit_dollars / 100

            # Update cumulative stats
            cumulative_wins += day_wins
            cumulative_total += day_total
            cumulative_profit += day_profit_units  # Now accumulating units, not dollars

            # Calculate cumulative win rate
            cumulative_win_rate = cumulative_wins / cumulative_total if cumulative_total > 0 else 0

            history_data.append({
                "period": str(date),
                "predictions": len(day_df),
                "wins": day_wins,
                "losses": day_losses,
                "win_rate": round(cumulative_win_rate, 4),  # Use cumulative for trend
                "daily_win_rate": round(day_win_rate, 4),  # Daily for reference
                "roi": round((cumulative_profit / cumulative_total) * 100, 2) if cumulative_total > 0 else 0,
                "daily_roi": round((day_profit_units / len(day_df)) * 100, 2) if len(day_df) > 0 else 0,
                "units_won": round(cumulative_profit, 2)
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

                # Drop duplicate columns from results before merging
                results_cols_to_keep = ['prediction_id', 'away_score', 'home_score', 'actual_total', 'result', 'profit_loss']
                results_df_clean = results_df[results_cols_to_keep]

                merged_df = predictions_df.merge(results_df_clean, on='prediction_id', how='inner')

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


@router.get("/predictions")
async def get_individual_predictions(
    days: int = 30,
    limit: int = 50,
    sport: Optional[str] = None,
    model: Optional[str] = None,
    bet_type: Optional[str] = None
):
    """
    Get individual predictions with results for detailed analysis

    Args:
        days: Number of days to look back
        limit: Maximum number of predictions to return
        sport: Filter by sport (nba, ncaab, nhl, etc.)
        model: Filter by model (ensemble, xgboost, etc.)
        bet_type: Filter by bet type (totals, spreads, moneyline)

    Returns:
        Individual predictions with game details and results
    """
    try:
        # Read from predictions.db - SINGLE SOURCE OF TRUTH
        if not PREDICTIONS_DB.exists():
            return {
                "predictions": [],
                "total": 0,
                "message": "No results data available yet"
            }

        # Load results from database (contains all predictions with results)
        conn = sqlite3.connect(str(PREDICTIONS_DB))
        predictions_df = pd.read_sql_query("SELECT * FROM results", conn)
        conn.close()

        # Add aliased columns for compatibility (database uses predicted_value/market_value)
        if 'predicted_total' not in predictions_df.columns and 'predicted_value' in predictions_df.columns:
            predictions_df['predicted_total'] = predictions_df['predicted_value']
        if 'market_total' not in predictions_df.columns and 'market_value' in predictions_df.columns:
            predictions_df['market_total'] = predictions_df['market_value']

        # Convert date column
        if 'game_date' in predictions_df.columns:
            predictions_df['game_date'] = pd.to_datetime(predictions_df['game_date'], format='mixed', errors='coerce')

        # Filter by date range
        cutoff_date = datetime.now() - timedelta(days=days)
        if 'game_date' in predictions_df.columns:
            predictions_df = predictions_df[predictions_df['game_date'] >= cutoff_date]

        # Apply filters
        if sport:
            predictions_df = predictions_df[predictions_df['sport'].str.lower() == sport.lower()]
        if model:
            predictions_df = predictions_df[predictions_df['model'].str.lower() == model.lower()]
        if bet_type:
            predictions_df = predictions_df[predictions_df['bet_type'].str.lower() == bet_type.lower()]

        # 🛡️ SAFEGUARD #1: Filter out UNKNOWN results (games not yet graded)
        predictions_df = predictions_df[predictions_df['result'].isin(['WIN', 'LOSS', 'PUSH'])]

        # Sort by date descending
        predictions_df = predictions_df.sort_values('game_date', ascending=False)

        # Limit results
        total_count = len(predictions_df)
        predictions_df = predictions_df.head(limit)

        # Convert to list of dicts
        predictions = []
        for idx, row in predictions_df.iterrows():
            try:
                pred = {
                    'prediction_id': safe_value(row.get('prediction_id')),
                    'game_date': row.get('game_date').strftime('%Y-%m-%d') if pd.notna(row.get('game_date')) else None,
                    'game_time': safe_value(row.get('game_time')),
                    'sport': safe_value(row.get('sport')),
                    'away_team': safe_value(row.get('away_team')),
                    'home_team': safe_value(row.get('home_team')),
                    'bet_type': safe_value(row.get('bet_type')),
                    'model': safe_value(row.get('model')),
                    'predicted_value': safe_float(row.get('predicted_total')),  # Use predicted_total alias
                    'market_value': safe_float(row.get('market_total')),  # Use market_total alias
                    'edge': safe_float(row.get('predicted_total')) - safe_float(row.get('market_total')) if pd.notna(row.get('predicted_total')) and pd.notna(row.get('market_total')) else None,
                    'recommendation': safe_value(row.get('recommendation')),
                    'confidence': safe_value(row.get('confidence')),
                    'bet_placed': safe_value(row.get('bet_placed')),
                    'actual_total': safe_float(row.get('actual_total')),
                    'away_score': safe_float(row.get('away_score')),
                    'home_score': safe_float(row.get('home_score')),
                    'result': safe_value(row.get('result')),
                    'profit_loss': safe_float(row.get('profit_loss')) or 0
                }
                predictions.append(pred)
            except Exception as e:
                logger.error(f"Error processing row {idx}: {str(e)}, row data: {row.to_dict()}")
                raise

        return {
            "predictions": predictions,
            "total": total_count
        }

    except Exception as e:
        logger.error(f"Error getting predictions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
