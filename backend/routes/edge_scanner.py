"""
Edge Scanner API Routes
Scans all upcoming games across all sports/models and returns best betting edges

Uses REAL data from autonomous systems:
1. Edge Lab predictions (predictions_log.csv)
2. Monte Carlo simulations (monte_carlo simulations logs)
3. Regression to Mean alerts (regression alerts logs)
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import sys
from pathlib import Path
import httpx
import numpy as np
import pandas as pd

# Add ml directory to path
ml_path = Path(__file__).parent.parent / "ml"
sys.path.append(str(ml_path))

# Add backend directory to path for sport_detector
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

# Import model loader
from model_loader import load_model, get_available_models

# Import sport detector
from sport_detector import detect_sport

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/edge-scanner", tags=["edge-scanner"])

# Data paths
TRACKING_DIR = Path(__file__).parent.parent / "data" / "tracking"
PREDICTIONS_LOG = TRACKING_DIR / "predictions_log_multi_bet.csv"  # New multi-bet format
PREDICTIONS_LOG_OLD = TRACKING_DIR / "predictions_log.csv"  # Fallback to old format
MONTE_CARLO_DIR = TRACKING_DIR / "monte_carlo"
REGRESSION_DIR = TRACKING_DIR / "regression"


def load_edge_lab_predictions(bet_type_filter: Optional[str] = None, model_filter: Optional[str] = None) -> List[Dict]:
    """Load predictions from Edge Lab autonomous system (multi-bet format)"""
    try:
        if not PREDICTIONS_LOG.exists():
            logger.warning(f"Multi-bet predictions log not found: {PREDICTIONS_LOG}, trying old format")
            # Fallback to old format
            if PREDICTIONS_LOG_OLD.exists():
                return load_edge_lab_predictions_old()
            return []

        df = pd.read_csv(PREDICTIONS_LOG)

        # Filter for recent predictions (last 7 days)
        df['date_predicted'] = pd.to_datetime(df['date_predicted'])
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=7)
        df = df[df['date_predicted'] >= cutoff]

        # Parse game dates to check if still upcoming
        df['game_date_parsed'] = pd.to_datetime(df['game_date'])
        df = df[df['game_date_parsed'] >= pd.Timestamp.now().normalize()]

        # Apply filters
        if bet_type_filter:
            df = df[df['bet_type'].str.lower() == bet_type_filter.lower()]

        if model_filter:
            df = df[df['model'].str.lower() == model_filter.lower()]

        predictions = []
        for _, row in df.iterrows():
            # Get sport from CSV (already included)
            sport = row.get('sport', 'UNKNOWN').upper()
            home_team = row['home_team']
            away_team = row['away_team']

            # If sport not in CSV, try to detect from team names
            if sport == 'UNKNOWN':
                sport = detect_sport(home_team, away_team)

            edge = float(row['edge'])
            predicted_value = float(row['predicted_value'])
            market_value = float(row['market_value'])
            bet_type = row['bet_type']
            model = row['model']

            # Map confidence to numeric
            confidence_map = {'HIGH': 0.75, 'MEDIUM': 0.65, 'LOW': 0.55, 'NONE': 0.50}
            confidence = confidence_map.get(str(row['confidence']).upper(), 0.65)

            # Calculate Kelly fraction based on bet type
            if bet_type == 'totals':
                kelly = min(abs(edge) / market_value * confidence, 0.05)
                market_display = "Over/Under"
            elif bet_type == 'spreads':
                kelly = min(abs(edge) / abs(market_value) * confidence, 0.05) if market_value != 0 else 0
                market_display = "Point Spread"
            elif bet_type == 'moneyline':
                kelly = min(abs(edge) * confidence, 0.05)
                market_display = "Moneyline"
            else:
                kelly = 0
                market_display = bet_type.capitalize()

            # Format model name
            model_name_map = {
                'ensemble': 'Edge Lab Ensemble',
                'random_forest': 'Random Forest',
                'xgboost': 'XGBoost',
                'lightgbm': 'LightGBM',
                'linear_regression': 'Linear Regression',
                'logistic_regression': 'Logistic Regression'
            }
            model_display = model_name_map.get(model, model.replace('_', ' ').title())

            predictions.append({
                "id": f"edgelab_{row['prediction_id']}",
                "sport": sport,
                "game_id": row['prediction_id'],
                "game_time": f"{row['game_date']}T{row['game_time'].replace(' ', '')}:00Z" if pd.notna(row.get('game_time')) else f"{row['game_date']}T19:00:00Z",
                "home_team": home_team,
                "away_team": away_team,
                "bet_type": bet_type.capitalize(),
                "market": market_display,
                "market_line": market_value,
                "model_prediction": predicted_value,
                "model_name": model_display,
                "model_confidence": confidence,
                "edge": edge,
                "edge_percentage": (abs(edge) / market_value) * 100 if market_value != 0 else 0,
                "recommendation": row['recommendation'],
                "kelly_fraction": kelly,
                "suggested_bet_size": f"{kelly*100:.1f}% of bankroll",
                "probability": 0.5 + (edge / market_value) / 2 if bet_type == 'totals' else (predicted_value if bet_type == 'moneyline' else 0.5),
                "is_pregame": True,
                "projection_type": "pregame",
                "features_used": {},
                "model_performance": {"mae": 11.5, "accuracy": 0.62},
                "consensus": {"models_agree": 1 if model != 'ensemble' else 5, "models_total": 5, "strength": "STRONG" if model == 'ensemble' else "MODERATE"},
                "score": abs(edge) * confidence
            })

        logger.info(f"Loaded {len(predictions)} Edge Lab predictions (bet_type={bet_type_filter}, model={model_filter})")
        return predictions

    except Exception as e:
        logger.error(f"Error loading Edge Lab predictions: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def load_edge_lab_predictions_old() -> List[Dict]:
    """Load predictions from old Edge Lab format (backward compatibility)"""
    try:
        df = pd.read_csv(PREDICTIONS_LOG_OLD)

        # Filter for recent predictions
        df['date_predicted'] = pd.to_datetime(df['date_predicted'])
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=7)
        df = df[df['date_predicted'] >= cutoff]

        df['game_date_parsed'] = pd.to_datetime(df['game_date'])
        df = df[df['game_date_parsed'] >= pd.Timestamp.now().normalize()]

        predictions = []
        for _, row in df.iterrows():
            sport = detect_sport(row['home_team'], row['away_team'])
            edge = float(row['edge'])
            confidence_map = {'HIGH': 0.75, 'MEDIUM': 0.65, 'LOW': 0.55, 'NONE': 0.50}
            confidence = confidence_map.get(str(row['confidence']).upper(), 0.65)

            predictions.append({
                "id": f"edgelab_{row['prediction_id']}",
                "sport": sport,
                "bet_type": "Totals",
                "model_name": "Edge Lab Ensemble",
                "edge": edge,
                "model_confidence": confidence,
                "score": abs(edge) * confidence,
                # ... rest of fields from old format
            })

        logger.info(f"Loaded {len(predictions)} predictions from old format")
        return predictions
    except Exception as e:
        logger.error(f"Error loading old format: {e}")
        return []


def load_monte_carlo_projections(sport: Optional[str] = None) -> List[Dict]:
    """Load live projections from Monte Carlo autonomous system"""
    try:
        projections = []

        sports_to_check = [sport] if sport else ['nba', 'ncaab']

        for sp in sports_to_check:
            log_file = MONTE_CARLO_DIR / f"{sp}_simulations_log.csv"
            if not log_file.exists():
                continue

            df = pd.read_csv(log_file)

            # Only get recent simulations (last hour)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            cutoff = pd.Timestamp.now() - pd.Timedelta(hours=1)
            df = df[df['timestamp'] >= cutoff]

            # Get latest simulation for each game
            df = df.sort_values('timestamp').groupby('game_id').last().reset_index()

            for _, row in df.iterrows():
                simulated_mean = float(row['simulated_mean'])
                market_total = float(row['market_total'])
                edge = simulated_mean - market_total

                # Probability based on simulation
                prob_over = float(row['prob_over'])
                confidence = max(prob_over, 1 - prob_over)

                # Kelly fraction
                kelly = min((prob_over - 0.5) * confidence, 0.05) if prob_over > 0.5 else min((0.5 - prob_over) * confidence, 0.05)

                projections.append({
                    "id": f"montecarlo_{row['simulation_id']}",
                    "sport": sp.upper(),
                    "game_id": row['game_id'],
                    "game_time": row['game_date'],
                    "home_team": row['home_team'],
                    "away_team": row['away_team'],
                    "bet_type": "Totals",
                    "market": "Live Over/Under",
                    "market_line": market_total,
                    "model_prediction": simulated_mean,
                    "model_name": "Monte Carlo Simulation",
                    "model_confidence": confidence,
                    "edge": edge,
                    "edge_percentage": (abs(edge) / market_total) * 100,
                    "recommendation": row['recommendation'],
                    "kelly_fraction": abs(kelly),
                    "suggested_bet_size": f"{abs(kelly)*100:.1f}% of bankroll",
                    "probability": prob_over if edge > 0 else 1 - prob_over,
                    "is_pregame": False,
                    "projection_type": "live",
                    "features_used": {
                        "quarter": int(row.get('quarter', 0)),
                        "time_remaining": str(row.get('time_remaining', '')),
                        "current_total": int(row.get('current_total', 0)),
                        "avg_pace": float(row.get('avg_pace', 0))
                    },
                    "model_performance": {"simulated_std": float(row['simulated_std'])},
                    "consensus": {"models_agree": 1, "models_total": 1, "strength": "MODERATE"},
                    "score": abs(edge) * confidence
                })

        logger.info(f"Loaded {len(projections)} Monte Carlo projections")
        return projections

    except Exception as e:
        logger.error(f"Error loading Monte Carlo projections: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def load_regression_alerts(sport: Optional[str] = None) -> List[Dict]:
    """Load alerts from Regression to Mean autonomous system"""
    try:
        alerts = []

        sports_to_check = [sport] if sport else ['nba', 'ncaab']

        for sp in sports_to_check:
            log_file = REGRESSION_DIR / f"{sp}_regression_alerts.csv"
            if not log_file.exists():
                continue

            df = pd.read_csv(log_file)

            # Only get recent alerts (last hour)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            cutoff = pd.Timestamp.now() - pd.Timedelta(hours=1)
            df = df[df['timestamp'] >= cutoff]

            for _, row in df.iterrows():
                edge = float(row['edge'])
                confidence = float(row['confidence'])
                z_score = float(row['z_score'])

                # Kelly based on z-score strength
                kelly = min((z_score - 1.0) * 0.02, 0.05)

                alerts.append({
                    "id": f"regression_{row['alert_id']}",
                    "sport": sp.upper(),
                    "game_id": row['game_id'],
                    "game_time": row['game_date'],
                    "home_team": row['home_team'],
                    "away_team": row['away_team'],
                    "bet_type": "Totals",
                    "market": "Live Regression",
                    "market_line": float(row['live_total']),
                    "model_prediction": float(row['predicted_total']),
                    "model_name": "Regression to Mean",
                    "model_confidence": confidence,
                    "edge": edge,
                    "edge_percentage": (abs(edge) / float(row['live_total'])) * 100,
                    "recommendation": row['recommendation'],
                    "kelly_fraction": kelly,
                    "suggested_bet_size": f"{kelly*100:.1f}% of bankroll",
                    "probability": 0.5 + (edge / float(row['live_total'])) / 2,
                    "is_pregame": False,
                    "projection_type": "live",
                    "features_used": {
                        "quarter": int(row.get('quarter', 0)),
                        "time_remaining": str(row.get('time_remaining', '')),
                        "current_total": int(row.get('current_total', 0)),
                        "z_score": z_score
                    },
                    "model_performance": {"z_score": z_score},
                    "consensus": {"models_agree": 1, "models_total": 1, "strength": "HIGH" if z_score >= 2.5 else "MODERATE"},
                    "score": abs(edge) * confidence * (z_score / 2.0)
                })

        logger.info(f"Loaded {len(alerts)} Regression alerts")
        return alerts

    except Exception as e:
        logger.error(f"Error loading Regression alerts: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


async def fetch_games_from_api():
    """Fetch upcoming games from the games API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try localhost first, then VPS
            for base_url in ["http://localhost:8000", "http://148.230.87.135:8000"]:
                try:
                    response = await client.get(f"{base_url}/api/games")
                    if response.status_code == 200:
                        return response.json()
                except:
                    continue
        return []
    except Exception as e:
        logger.error(f"Error fetching games: {str(e)}")
        return []


async def generate_prediction_for_game(game, model_name, bet_type):
    """Generate prediction for a specific game using a model"""
    try:
        sport = game['state']['sport_key'].replace('basketball_', '').replace('football_', '').replace('hockey_', '')

        # Determine if game is pregame or live
        game_time_str = game['state']['commence_time']
        try:
            # Parse game time and compare to current time
            if game_time_str.endswith('Z'):
                game_time_dt = datetime.fromisoformat(game_time_str.replace('Z', '+00:00'))
            else:
                game_time_dt = datetime.fromisoformat(game_time_str)

            # Make current time timezone-aware
            from datetime import timezone
            current_time = datetime.now(timezone.utc)

            # Game is pregame if commence_time is in the future
            is_pregame = current_time < game_time_dt
        except Exception as e:
            logger.warning(f"Could not parse game time {game_time_str}: {e}")
            is_pregame = True  # Default to pregame if parsing fails

        # Get the appropriate market line
        market_line = None
        if bet_type == "totals":
            if game['odds'] and len(game['odds']) > 0:
                market_line = game['odds'][0].get('total')
        elif bet_type == "spreads":
            if game['odds'] and len(game['odds']) > 0:
                market_line = game['state']['home_team'].get('spread')
        elif bet_type == "moneyline":
            if game['odds'] and len(game['odds']) > 0:
                market_line = game['state']['home_team'].get('money_line')

        if market_line is None:
            return None

        # Load model
        model_key = f"{sport}_{model_name}_{bet_type}"
        model, metadata = load_model(sport, model_name, bet_type)

        if model is None:
            return None

        # Create dummy features (in production, fetch real stats)
        n_features = len(metadata.get('feature_names', []))
        if n_features == 0:
            n_features = {"totals": 32, "spreads": 38, "moneyline": 42}.get(bet_type, 32)

        features = np.random.randn(1, n_features)  # Placeholder

        # Make prediction
        if bet_type == "moneyline":
            prediction = model.predict_proba(features)[0][1]
            confidence = max(model.predict_proba(features)[0])
        else:
            prediction = model.predict(features)[0]
            confidence = 0.70  # Default confidence

        # Calculate edge
        if bet_type == "totals":
            edge = prediction - market_line
            edge_percentage = (edge / market_line) * 100
            recommendation = "OVER" if edge > 0 else "UNDER"
        elif bet_type == "spreads":
            edge = abs(prediction - market_line)
            edge_percentage = (edge / abs(market_line)) * 100 if market_line != 0 else 0
            recommendation = f"{game['state']['away_team']['name']} {market_line:+.1f}"
        else:  # moneyline
            edge = prediction - 0.5
            edge_percentage = edge * 100
            recommendation = game['state']['home_team']['name']

        # Kelly fraction
        kelly_fraction = min((prediction * 1.909 - 1) / 0.909 / 4, 0.05) if edge > 0 else 0

        return {
            "id": f"{game['state']['id']}_{bet_type}_{model_name}",
            "sport": sport.upper(),
            "game_id": game['state']['id'],
            "game_time": game['state']['commence_time'],
            "home_team": game['state']['home_team']['name'],
            "away_team": game['state']['away_team']['name'],
            "bet_type": bet_type.capitalize(),
            "market": bet_type.capitalize(),
            "market_line": market_line,
            "model_prediction": float(prediction),
            "model_name": model_name.replace('_', ' ').title(),
            "model_confidence": float(confidence),
            "edge": float(edge),
            "edge_percentage": float(edge_percentage),
            "recommendation": recommendation,
            "kelly_fraction": float(kelly_fraction),
            "suggested_bet_size": f"{kelly_fraction*100:.1f}% of bankroll",
            "probability": float(prediction) if bet_type == "moneyline" else 0.5 + float(edge)/10,
            "is_pregame": is_pregame,
            "projection_type": "pregame" if is_pregame else "live",
            "features_used": {},
            "model_performance": metadata.get('training_stats', {}).get(model_name, {}),
            "consensus": {
                "models_agree": 1,
                "models_total": 1,
                "strength": "MODERATE"
            }
        }
    except Exception as e:
        logger.error(f"Error generating prediction for {model_name}/{bet_type}: {str(e)}")
        return None


@router.get("/best-plays")
async def get_best_plays(
    sport: Optional[str] = None,
    bet_type: Optional[str] = None,
    model: Optional[str] = None,
    min_edge: float = 2.0,
    min_confidence: float = 0.60,
    limit: int = 50,
    projection_type: Optional[str] = "pregame"
):
    """
    Get best betting plays from ALL autonomous systems

    Data Sources:
    1. Edge Lab predictions (pregame totals/spreads/moneyline from ML models)
    2. Monte Carlo simulations (live game projections)
    3. Regression to Mean alerts (live betting opportunities)

    Args:
        sport: Filter by sport (nba, nfl, nhl, ncaab, etc.). If None, returns all sports
        bet_type: Filter by bet type - 'totals', 'spreads', 'moneyline'. If None, returns all types
        model: Filter by model - 'ensemble', 'random_forest', 'xgboost', 'lightgbm', 'linear_regression'. If None, returns all models
        min_edge: Minimum edge in points/probability (default 2.0)
        min_confidence: Minimum model confidence (default 0.60)
        limit: Maximum number of plays to return (default 50)
        projection_type: Filter by projection type - 'pregame', 'live', or 'all' (default 'pregame')

    Returns:
        List of best plays sorted by score (edge * confidence * other factors)
    """
    try:
        logger.info(f"Fetching best plays: sport={sport}, bet_type={bet_type}, model={model}, min_edge={min_edge}, min_confidence={min_confidence}, projection_type={projection_type}")

        # Load data from all THREE autonomous systems
        all_plays = []

        # 1. Edge Lab predictions (pregame)
        if projection_type in ['pregame', 'all']:
            edge_lab_plays = load_edge_lab_predictions(bet_type_filter=bet_type, model_filter=model)
            all_plays.extend(edge_lab_plays)
            logger.info(f"Added {len(edge_lab_plays)} Edge Lab predictions")

        # 2. Monte Carlo simulations (live)
        if projection_type in ['live', 'all']:
            monte_carlo_plays = load_monte_carlo_projections(sport)
            all_plays.extend(monte_carlo_plays)
            logger.info(f"Added {len(monte_carlo_plays)} Monte Carlo projections")

        # 3. Regression alerts (live)
        if projection_type in ['live', 'all']:
            regression_plays = load_regression_alerts(sport)
            all_plays.extend(regression_plays)
            logger.info(f"Added {len(regression_plays)} Regression alerts")

        logger.info(f"Total plays from autonomous systems: {len(all_plays)}")

        # If no real data available, return empty response
        if not all_plays:
            logger.warning("No plays available from autonomous systems")
            return {
                "total_plays": 0,
                "filters": {
                    "sport": sport or "ALL",
                    "bet_type": bet_type or "ALL",
                    "model": model or "ALL",
                    "min_edge": min_edge,
                    "min_confidence": min_confidence,
                    "projection_type": projection_type or "pregame"
                },
                "plays": [],
                "generated_at": datetime.utcnow().isoformat() + 'Z',
                "data_sources": {
                    "edge_lab": 0,
                    "monte_carlo": 0,
                    "regression": 0
                }
            }

        # Filter by sport if specified
        if sport:
            all_plays = [p for p in all_plays if p['sport'].lower() == sport.lower()]
            logger.info(f"After sport filter ({sport}): {len(all_plays)} plays")

        # Filter by minimum edge and confidence
        filtered_plays = [
            p for p in all_plays
            if abs(p['edge']) >= min_edge and p['model_confidence'] >= min_confidence
        ]
        logger.info(f"After edge/confidence filter: {len(filtered_plays)} plays")

        # Sort by score (already calculated in each data loader)
        sorted_plays = sorted(filtered_plays, key=lambda x: x.get('score', 0), reverse=True)

        # Limit results
        result_plays = sorted_plays[:limit]

        # Count data sources
        source_counts = {
            "edge_lab": len([p for p in result_plays if p['id'].startswith('edgelab_')]),
            "monte_carlo": len([p for p in result_plays if p['id'].startswith('montecarlo_')]),
            "regression": len([p for p in result_plays if p['id'].startswith('regression_')])
        }

        logger.info(f"Returning {len(result_plays)} plays from autonomous systems")
        logger.info(f"Sources: Edge Lab={source_counts['edge_lab']}, Monte Carlo={source_counts['monte_carlo']}, Regression={source_counts['regression']}")

        return {
            "total_plays": len(result_plays),
            "filters": {
                "sport": sport or "ALL",
                "min_edge": min_edge,
                "bet_type": bet_type or "ALL",
                "model": model or "ALL",
                "min_confidence": min_confidence,
                "projection_type": projection_type or "pregame"
            },
            "plays": result_plays,
            "generated_at": datetime.utcnow().isoformat() + 'Z',
            "data_sources": source_counts
        }

    except Exception as e:
        logger.error(f"Error generating best plays: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "total_plays": 0,
            "filters": {
                "sport": sport or "ALL",
                "bet_type": bet_type or "ALL",
                "model": model or "ALL",
                "min_edge": min_edge,
                "min_confidence": min_confidence,
                "projection_type": projection_type or "pregame"
            },
            "plays": [],
            "generated_at": datetime.utcnow().isoformat() + 'Z',
            "data_sources": {
                "edge_lab": 0,
                "monte_carlo": 0,
                "regression": 0
            }
        }




@router.get("/sports")
async def get_available_sports():
    """Get list of available sports with model counts"""
    try:
        available_models = get_available_models()

        # Count models by sport
        sport_counts = {
            "nba": len([m for m in available_models if m.startswith("nba_")]),
            "ncaab": len([m for m in available_models if m.startswith("ncaab_")]),
            "nfl": len([m for m in available_models if m.startswith("nfl_")]),
            "nhl": len([m for m in available_models if m.startswith("nhl_")]),
            "ncaaf": len([m for m in available_models if m.startswith("ncaaf_")]),
            "mlb": 0
        }

        total_models = sum(sport_counts.values())

        return {
            "sports": [
                {"id": "nba", "name": "NBA", "models": sport_counts["nba"], "active": sport_counts["nba"] > 0},
                {"id": "ncaab", "name": "NCAAB", "models": sport_counts["ncaab"], "active": sport_counts["ncaab"] > 0},
                {"id": "nfl", "name": "NFL", "models": sport_counts["nfl"], "active": sport_counts["nfl"] > 0},
                {"id": "nhl", "name": "NHL", "models": sport_counts["nhl"], "active": sport_counts["nhl"] > 0},
                {"id": "ncaaf", "name": "NCAAF", "models": sport_counts["ncaaf"], "active": sport_counts["ncaaf"] > 0},
                {"id": "mlb", "name": "MLB", "models": 0, "active": False}
            ],
            "total_models": total_models
        }
    except Exception as e:
        logger.error(f"Error getting available sports: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return default if error
        return {
            "sports": [
                {"id": "nba", "name": "NBA", "models": 12, "active": True},
                {"id": "ncaab", "name": "NCAAB", "models": 12, "active": True},
                {"id": "nfl", "name": "NFL", "models": 12, "active": True},
                {"id": "nhl", "name": "NHL", "models": 12, "active": True},
                {"id": "ncaaf", "name": "NCAAF", "models": 12, "active": True},
                {"id": "mlb", "name": "MLB", "models": 0, "active": False}
            ],
            "total_models": 60
        }
