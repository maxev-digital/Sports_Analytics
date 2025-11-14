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

        # Drop duplicate columns from results before merging
        results_cols_to_keep = ['prediction_id', 'away_score', 'home_score', 'actual_total', 'result', 'profit_loss']
        results_df_clean = results_df[results_cols_to_keep]

        # Merge predictions with results
        merged_df = predictions_df.merge(
            results_df_clean,
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

        # Convert dates
        predictions_df['game_date_dt'] = pd.to_datetime(predictions_df['game_date'], format='mixed', errors='coerce')

        # Drop duplicate columns from results before merging
        results_cols_to_keep = ['prediction_id', 'away_score', 'home_score', 'actual_total', 'result', 'profit_loss']
        results_df_clean = results_df[results_cols_to_keep]

        # Merge with results FIRST
        merged_df = predictions_df.merge(
            results_df_clean,
            on='prediction_id',
            how='inner'
        )

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
            day_profit = day_df['profit_loss'].sum() if 'profit_loss' in day_df.columns else 0

            # Update cumulative stats
            cumulative_wins += day_wins
            cumulative_total += day_total
            cumulative_profit += day_profit

            # Calculate cumulative win rate
            cumulative_win_rate = cumulative_wins / cumulative_total if cumulative_total > 0 else 0

            history_data.append({
                "period": str(date),
                "predictions": len(day_df),
                "wins": day_wins,
                "losses": day_losses,
                "win_rate": round(cumulative_win_rate, 4),  # Use cumulative for trend
                "daily_win_rate": round(day_win_rate, 4),  # Daily for reference
                "roi": round((cumulative_profit / (cumulative_wins + cumulative_total - cumulative_wins)) * 100, 2) if cumulative_total > 0 else 0,
                "daily_roi": round((day_profit / len(day_df)) * 100, 2) if len(day_df) > 0 else 0,
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
        # Load predictions log
        predictions_file = TRACKING_DIR / "predictions_log_multi_bet.csv"
        results_file = TRACKING_DIR / "results_log.csv"
        
        if not predictions_file.exists():
            return {
                "predictions": [],
                "total": 0,
                "message": "No predictions data available"
            }
        
        # Load data
        predictions_df = pd.read_csv(predictions_file)
        
        # Convert date columns
        if 'date_predicted' in predictions_df.columns:
            predictions_df['date_predicted'] = pd.to_datetime(predictions_df['date_predicted'])
        if 'game_date' in predictions_df.columns:
            predictions_df['game_date'] = pd.to_datetime(predictions_df['game_date'])
        
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
        
        # Load results for merging
        results_df = None
        if results_file.exists():
            results_df = pd.read_csv(results_file)
            # Merge results
            predictions_df = pd.merge(
                predictions_df,
                results_df[['prediction_id', 'actual_total', 'away_score', 'home_score', 'result', 'profit_loss']],
                on='prediction_id',
                how='left'
            )
        
        # Sort by date descending
        predictions_df = predictions_df.sort_values('game_date', ascending=False)
        
        # Limit results
        total_count = len(predictions_df)
        predictions_df = predictions_df.head(limit)
        
        # Convert to list of dicts
        predictions = []
        for _, row in predictions_df.iterrows():
            pred = {
                'prediction_id': row.get('prediction_id'),
                'game_date': row.get('game_date').strftime('%Y-%m-%d') if pd.notna(row.get('game_date')) else None,
                'game_time': row.get('game_time'),
                'sport': row.get('sport'),
                'away_team': row.get('away_team'),
                'home_team': row.get('home_team'),
                'bet_type': row.get('bet_type'),
                'model': row.get('model'),
                'predicted_value': safe_float(row.get('predicted_value')),
                'market_value': safe_float(row.get('market_value')),
                'edge': safe_float(row.get('edge')),
                'recommendation': row.get('recommendation'),
                'confidence': row.get('confidence'),
                'bet_placed': row.get('bet_placed'),
                'actual_total': safe_float(row.get('actual_total')),
                'away_score': safe_float(row.get('away_score')),
                'home_score': safe_float(row.get('home_score')),
                'result': row.get('result'),
                'profit_loss': safe_float(row.get('profit_loss')) or 0
            }
            predictions.append(pred)
        
        return {
            "predictions": predictions,
            "total": total_count
        }
    
    except Exception as e:
        logger.error(f"Error getting predictions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
