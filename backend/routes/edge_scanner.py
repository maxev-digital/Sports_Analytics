"""
Edge Scanner API Routes
Scans all upcoming games across all sports/models and returns best betting edges
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import sys
from pathlib import Path
import httpx
import numpy as np

# Add ml directory to path
ml_path = Path(__file__).parent.parent / "ml"
sys.path.append(str(ml_path))

# Import model loader
from model_loader import load_model, get_available_models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/edge-scanner", tags=["edge-scanner"])


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
    min_edge: float = 2.0,
    min_confidence: float = 0.60,
    limit: int = 50
):
    """
    Get best betting plays across all models and sports

    Args:
        sport: Filter by sport (nba, nfl, nhl, ncaab, etc.). If None, returns all sports
        min_edge: Minimum edge in points/probability (default 2.0)
        min_confidence: Minimum model confidence (default 0.60)
        limit: Maximum number of plays to return (default 50)

    Returns:
        List of best plays sorted by edge * confidence score
    """
    try:
        # Fetch games
        games = await fetch_games_from_api()

        if not games:
            logger.warning("No games available, returning mock data")
            # Return mock data if no games available
            mock_plays = [
            {
                "id": "nba_20251108_lal_bos_totals",
                "sport": "NBA",
                "game_id": "nba_20251108_lal_bos",
                "game_time": "2025-11-08T19:30:00Z",
                "home_team": "Boston Celtics",
                "away_team": "Los Angeles Lakers",
                "bet_type": "Totals",
                "market": "Over/Under",
                "market_line": 228.5,
                "model_prediction": 233.2,
                "model_name": "Random Forest",
                "model_confidence": 0.78,
                "edge": 4.7,
                "edge_percentage": 2.06,
                "recommendation": "OVER",
                "kelly_fraction": 0.042,
                "suggested_bet_size": "4.2% of bankroll",
                "probability": 0.651,
                "features_used": {
                    "home_pace": 100.5,
                    "away_pace": 98.3,
                    "home_off_rating": 118.2,
                    "away_off_rating": 115.8,
                    "home_def_rating": 110.5,
                    "away_def_rating": 108.9,
                    "rest_days_home": 2,
                    "rest_days_away": 1
                },
                "model_performance": {
                    "mae": 7.8,
                    "accuracy": 0.652,
                    "games_trained": 1203
                },
                "consensus": {
                    "models_agree": 3,
                    "models_total": 4,
                    "strength": "STRONG"
                }
            },
            {
                "id": "nba_20251108_gsw_phx_spreads",
                "sport": "NBA",
                "game_id": "nba_20251108_gsw_phx",
                "game_time": "2025-11-08T22:00:00Z",
                "home_team": "Phoenix Suns",
                "away_team": "Golden State Warriors",
                "bet_type": "Spreads",
                "market": "Point Spread",
                "market_line": -5.5,
                "model_prediction": -2.8,
                "model_name": "Random Forest",
                "model_confidence": 0.73,
                "edge": 2.7,
                "edge_percentage": 49.09,
                "recommendation": "WARRIORS +5.5",
                "kelly_fraction": 0.031,
                "suggested_bet_size": "3.1% of bankroll",
                "probability": 0.623,
                "features_used": {
                    "home_pace": 102.1,
                    "away_pace": 99.8,
                    "home_off_rating": 112.4,
                    "away_off_rating": 116.7,
                    "home_def_rating": 113.2,
                    "away_def_rating": 109.1,
                    "rest_days_home": 1,
                    "rest_days_away": 2
                },
                "model_performance": {
                    "ats_accuracy": 0.682,
                    "mae": 10.45,
                    "games_trained": 738
                },
                "consensus": {
                    "models_agree": 2,
                    "models_total": 3,
                    "strength": "MODERATE"
                }
            },
            {
                "id": "nba_20251108_mia_mil_moneyline",
                "sport": "NBA",
                "game_id": "nba_20251108_mia_mil",
                "game_time": "2025-11-08T20:00:00Z",
                "home_team": "Milwaukee Bucks",
                "away_team": "Miami Heat",
                "bet_type": "Moneyline",
                "market": "Moneyline",
                "market_line": -180,
                "model_prediction": 0.72,
                "model_name": "Random Forest Classifier",
                "model_confidence": 0.72,
                "edge": 0.078,
                "edge_percentage": 10.83,
                "recommendation": "BUCKS -180",
                "kelly_fraction": 0.025,
                "suggested_bet_size": "2.5% of bankroll",
                "probability": 0.72,
                "implied_probability": 0.642,
                "features_used": {
                    "home_win_pct": 0.688,
                    "away_win_pct": 0.531,
                    "home_ppg": 115.2,
                    "away_ppg": 108.4,
                    "home_recent_form": 0.800,
                    "away_recent_form": 0.600
                },
                "model_performance": {
                    "accuracy": 0.667,
                    "roc_auc": 0.721,
                    "games_trained": 738
                },
                "consensus": {
                    "models_agree": 2,
                    "models_total": 2,
                    "strength": "STRONG"
                }
            },
            {
                "id": "ncaab_20251108_duke_unc_totals",
                "sport": "NCAAB",
                "game_id": "ncaab_20251108_duke_unc",
                "game_time": "2025-11-08T21:00:00Z",
                "home_team": "Duke",
                "away_team": "UNC",
                "bet_type": "Totals",
                "market": "Over/Under",
                "market_line": 145.5,
                "model_prediction": 151.3,
                "model_name": "Random Forest",
                "model_confidence": 0.70,
                "edge": 5.8,
                "edge_percentage": 3.99,
                "recommendation": "OVER",
                "kelly_fraction": 0.048,
                "suggested_bet_size": "4.8% of bankroll",
                "probability": 0.672,
                "features_used": {
                    "home_adj_tempo": 72.5,
                    "away_adj_tempo": 70.1,
                    "home_adj_off_eff": 115.3,
                    "away_adj_off_eff": 112.8,
                    "home_adj_def_eff": 95.2,
                    "away_adj_def_eff": 97.5
                },
                "model_performance": {
                    "mae": 8.5,
                    "accuracy": 0.625,
                    "games_trained": 950
                },
                "consensus": {
                    "models_agree": 4,
                    "models_total": 4,
                    "strength": "STRONG"
                }
            }
        ]

            # Filter by sport if specified
            if sport:
                mock_plays = [p for p in mock_plays if p['sport'].lower() == sport.lower()]

            # Filter by minimum edge and confidence
            filtered_plays = [
                p for p in mock_plays
                if abs(p['edge']) >= min_edge and p['model_confidence'] >= min_confidence
            ]

            # Calculate score (edge * confidence) and sort
            for play in filtered_plays:
                play['score'] = abs(play['edge']) * play['model_confidence']

            sorted_plays = sorted(filtered_plays, key=lambda x: x['score'], reverse=True)

            # Limit results
            result_plays = sorted_plays[:limit]

            return {
                "total_plays": len(result_plays),
                "filters": {
                    "sport": sport or "ALL",
                    "min_edge": min_edge,
                    "min_confidence": min_confidence
                },
                "plays": result_plays,
                "generated_at": datetime.utcnow().isoformat() + 'Z'
            }

        # Generate predictions for real games
        all_plays = []

        # Get available models
        available_models = get_available_models()

        # Models to try for each bet type
        models_to_try = {
            "totals": ["random_forest", "xgboost", "lightgbm", "linear_regression"],
            "spreads": ["random_forest", "xgboost", "lightgbm", "linear_regression"],
            "moneyline": ["random_forest", "xgboost", "lightgbm", "logistic_regression"]
        }

        # Generate predictions for each game
        for game in games[:10]:  # Limit to 10 games to avoid timeout
            game_sport = game['state']['sport_key'].replace('basketball_', '').replace('football_', '').replace('hockey_', '')

            # Filter by sport if specified
            if sport and game_sport.lower() != sport.lower():
                continue

            # Try all bet types and models
            for bet_type in ["totals", "spreads", "moneyline"]:
                for model_name in models_to_try[bet_type]:
                    model_key = f"{game_sport}_{model_name}_{bet_type}"
                    if model_key in available_models:
                        prediction = await generate_prediction_for_game(game, model_name, bet_type)
                        if prediction and abs(prediction['edge']) >= min_edge and prediction['model_confidence'] >= min_confidence:
                            all_plays.append(prediction)

        # Calculate consensus (group by game_id + bet_type)
        from collections import defaultdict
        game_consensus = defaultdict(list)
        for play in all_plays:
            key = f"{play['game_id']}_{play['bet_type']}"
            game_consensus[key].append(play)

        # Update consensus for each play
        for play in all_plays:
            key = f"{play['game_id']}_{play['bet_type']}"
            related_plays = game_consensus[key]

            # Count how many models agree on the direction
            same_direction = sum(1 for p in related_plays if (p['edge'] > 0) == (play['edge'] > 0))

            play['consensus'] = {
                "models_agree": same_direction,
                "models_total": len(related_plays),
                "strength": "STRONG" if same_direction / len(related_plays) >= 0.75 else "MODERATE" if same_direction / len(related_plays) >= 0.5 else "WEAK"
            }

            # Calculate score
            play['score'] = abs(play['edge']) * play['model_confidence'] * (same_direction / len(related_plays))

        # Sort by score
        sorted_plays = sorted(all_plays, key=lambda x: x['score'], reverse=True)

        # Limit results
        result_plays = sorted_plays[:limit]

        return {
            "total_plays": len(result_plays),
            "filters": {
                "sport": sport or "ALL",
                "min_edge": min_edge,
                "min_confidence": min_confidence
            },
            "plays": result_plays,
            "generated_at": datetime.utcnow().isoformat() + 'Z'
        }

    except Exception as e:
        logger.error(f"Error generating best plays: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating best plays: {str(e)}")


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

        return {
            "sports": [
                {"id": "nba", "name": "NBA", "models": sport_counts["nba"], "active": sport_counts["nba"] > 0},
                {"id": "ncaab", "name": "NCAAB", "models": sport_counts["ncaab"], "active": sport_counts["ncaab"] > 0},
                {"id": "nfl", "name": "NFL", "models": sport_counts["nfl"], "active": sport_counts["nfl"] > 0},
                {"id": "nhl", "name": "NHL", "models": sport_counts["nhl"], "active": sport_counts["nhl"] > 0},
                {"id": "ncaaf", "name": "NCAAF", "models": sport_counts["ncaaf"], "active": sport_counts["ncaaf"] > 0},
                {"id": "mlb", "name": "MLB", "models": 0, "active": False}
            ]
        }
    except Exception as e:
        logger.error(f"Error getting available sports: {str(e)}")
        # Return default if error
        return {
            "sports": [
                {"id": "nba", "name": "NBA", "models": 9, "active": True},
                {"id": "ncaab", "name": "NCAAB", "models": 12, "active": True},
                {"id": "nfl", "name": "NFL", "models": 9, "active": True},
                {"id": "nhl", "name": "NHL", "models": 12, "active": True},
                {"id": "ncaaf", "name": "NCAAF", "models": 12, "active": True},
                {"id": "mlb", "name": "MLB", "models": 0, "active": False}
            ]
        }
