"""
Model Performance API Routes
Shows historical prediction results with win/loss tracking and ROI
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/performance", tags=["performance"])

# Data path
RESULTS_LOG = Path(__file__).parent.parent / "data" / "tracking" / "results_log.csv"


@router.get("/summary")
async def get_performance_summary(
    days: int = Query(default=30, description="Number of days to analyze"),
    bet_type: Optional[str] = Query(default=None, description="Filter by bet type: totals, spreads, moneyline"),
    sport: Optional[str] = Query(default=None, description="Filter by sport: NBA, NFL, NHL, NCAAB, NCAAF")
):
    """
    Get performance summary statistics

    Returns:
        - Overall win rate, profit/loss, ROI
        - Breakdown by bet type
        - Breakdown by sport
        - Breakdown by confidence level
    """
    try:
        if not RESULTS_LOG.exists():
            return {
                "error": "No results data available",
                "total_predictions": 0
            }

        # Load results
        df = pd.read_csv(RESULTS_LOG)

        # Filter by date
        if days > 0:
            cutoff = datetime.now() - timedelta(days=days)
            df['game_date'] = pd.to_datetime(df['game_date'])
            df = df[df['game_date'] >= cutoff]

        # Detect sport from prediction_id and team names
        def detect_sport(pred_id, away_team='', home_team=''):
            # Check prediction_id first
            if 'NBA' in pred_id:
                return 'NBA'
            elif 'NFL' in pred_id:
                return 'NFL'
            elif 'NHL' in pred_id:
                return 'NHL'
            elif 'NCAAB' in pred_id:
                return 'NCAAB'
            elif 'NCAAF' in pred_id:
                return 'NCAAF'

            # Check team names for NBA/NHL keywords
            team_text = f"{away_team} {home_team}".lower()

            # NBA teams have these patterns
            nba_keywords = ['lakers', 'warriors', 'celtics', 'heat', 'knicks', 'bulls', 'nets', 'sixers',
                           'raptors', 'bucks', 'pacers', 'pistons', 'cavaliers', 'wizards', 'hawks',
                           'hornets', 'magic', 'mavericks', 'rockets', 'spurs', 'grizzlies', 'pelicans',
                           'thunder', 'suns', 'kings', 'clippers', 'nuggets', 'timberwolves', 'blazers', 'jazz']

            # NHL teams have these patterns
            nhl_keywords = ['bruins', 'canadiens', 'senators', 'sabres', 'maple leafs', 'lightning',
                          'panthers', 'red wings', 'blackhawks', 'blue jackets', 'penguins', 'flyers',
                          'rangers', 'islanders', 'devils', 'capitals', 'hurricanes', 'predators',
                          'blues', 'jets', 'wild', 'avalanche', 'stars', 'oilers', 'flames', 'canucks',
                          'golden knights', 'kraken', 'ducks', 'sharks', 'kings']

            # NFL teams have these patterns
            nfl_keywords = ['patriots', 'dolphins', 'bills', 'jets', 'ravens', 'steelers', 'browns',
                          'bengals', 'texans', 'colts', 'titans', 'jaguars', 'chiefs', 'raiders',
                          'broncos', 'chargers', 'cowboys', 'giants', 'eagles', 'commanders',
                          'packers', 'vikings', 'lions', 'bears', 'buccaneers', 'saints', 'falcons',
                          'panthers', '49ers', 'seahawks', 'rams', 'cardinals']

            if any(keyword in team_text for keyword in nba_keywords):
                return 'NBA'
            elif any(keyword in team_text for keyword in nhl_keywords):
                return 'NHL'
            elif any(keyword in team_text for keyword in nfl_keywords):
                return 'NFL'

            # Check for college keywords
            if any(x in team_text for x in ['state', 'university', 'college', 'tech', 'wildcats', 'bulldogs', 'tigers']):
                # Distinguish between NCAAB and NCAAF based on prediction_id structure
                if 'totals' in pred_id.lower() or 'spreads' in pred_id.lower():
                    # More likely basketball if using these bet types without explicit sport
                    return 'NCAAB'
                return 'NCAAF'

            return 'UNKNOWN'

        df['sport'] = df.apply(lambda row: detect_sport(row['prediction_id'], row.get('away_team', ''), row.get('home_team', '')), axis=1)

        # Detect bet type from prediction_id
        def detect_bet_type(pred_id):
            if 'totals' in pred_id.lower():
                return 'totals'
            elif 'spread' in pred_id.lower():
                return 'spreads'
            elif 'moneyline' in pred_id.lower():
                return 'moneyline'
            return 'unknown'

        df['bet_type_detected'] = df['prediction_id'].apply(detect_bet_type)

        # Apply filters
        if bet_type:
            df = df[df['bet_type_detected'] == bet_type.lower()]

        if sport:
            df = df[df['sport'] == sport.upper()]

        if len(df) == 0:
            return {
                "error": "No data matches filters",
                "total_predictions": 0
            }

        # Calculate overall stats
        total = len(df)
        wins = len(df[df['result'] == 'WIN'])
        losses = len(df[df['result'] == 'LOSS'])
        unknown = len(df[df['result'] == 'UNKNOWN'])

        win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0
        total_profit = df['profit_loss'].sum() * 100  # Convert to $100 bets
        roi = (df['profit_loss'].mean()) * 100 if len(df) > 0 else 0

        # Breakdown by bet type
        by_bet_type = []
        for bt in ['totals', 'spreads', 'moneyline']:
            bt_df = df[df['bet_type_detected'] == bt]
            if len(bt_df) > 0:
                bt_wins = len(bt_df[bt_df['result'] == 'WIN'])
                bt_losses = len(bt_df[bt_df['result'] == 'LOSS'])
                bt_wr = (bt_wins / (bt_wins + bt_losses)) * 100 if (bt_wins + bt_losses) > 0 else 0
                bt_profit = bt_df['profit_loss'].sum() * 100
                bt_roi = (bt_df['profit_loss'].mean()) * 100

                by_bet_type.append({
                    'bet_type': bt.upper(),
                    'count': len(bt_df),
                    'wins': bt_wins,
                    'losses': bt_losses,
                    'win_rate': round(bt_wr, 2),
                    'profit_loss': round(bt_profit, 2),
                    'roi': round(bt_roi, 2)
                })

        # Breakdown by sport
        by_sport = []
        for sp in df['sport'].unique():
            sp_df = df[df['sport'] == sp]
            if len(sp_df) > 0:
                sp_wins = len(sp_df[sp_df['result'] == 'WIN'])
                sp_losses = len(sp_df[sp_df['result'] == 'LOSS'])
                sp_wr = (sp_wins / (sp_wins + sp_losses)) * 100 if (sp_wins + sp_losses) > 0 else 0
                sp_profit = sp_df['profit_loss'].sum() * 100
                sp_roi = (sp_df['profit_loss'].mean()) * 100

                by_sport.append({
                    'sport': sp,
                    'count': len(sp_df),
                    'wins': sp_wins,
                    'losses': sp_losses,
                    'win_rate': round(sp_wr, 2),
                    'profit_loss': round(sp_profit, 2),
                    'roi': round(sp_roi, 2)
                })

        # Breakdown by confidence
        by_confidence = []
        for conf in ['HIGH', 'MEDIUM', 'LOW']:
            conf_df = df[df['confidence'] == conf]
            if len(conf_df) > 0:
                conf_wins = len(conf_df[conf_df['result'] == 'WIN'])
                conf_losses = len(conf_df[conf_df['result'] == 'LOSS'])
                conf_wr = (conf_wins / (conf_wins + conf_losses)) * 100 if (conf_wins + conf_losses) > 0 else 0
                conf_profit = conf_df['profit_loss'].sum() * 100
                conf_roi = (conf_df['profit_loss'].mean()) * 100

                by_confidence.append({
                    'confidence': conf,
                    'count': len(conf_df),
                    'wins': conf_wins,
                    'losses': conf_losses,
                    'win_rate': round(conf_wr, 2),
                    'profit_loss': round(conf_profit, 2),
                    'roi': round(conf_roi, 2)
                })

        return {
            'overall': {
                'total_predictions': total,
                'wins': wins,
                'losses': losses,
                'unknown': unknown,
                'win_rate': round(win_rate, 2),
                'profit_loss': round(total_profit, 2),
                'roi': round(roi, 2)
            },
            'by_bet_type': by_bet_type,
            'by_sport': by_sport,
            'by_confidence': by_confidence,
            'filters_applied': {
                'days': days,
                'bet_type': bet_type,
                'sport': sport
            }
        }

    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent-predictions")
async def get_recent_predictions(
    limit: int = Query(default=100, description="Number of predictions to return"),
    bet_type: Optional[str] = Query(default=None),
    sport: Optional[str] = Query(default=None),
    result: Optional[str] = Query(default=None, description="Filter by result: WIN, LOSS, UNKNOWN")
):
    """
    Get recent predictions with results

    Returns list of predictions with:
        - Game details (teams, date)
        - Prediction details (recommendation, confidence)
        - Actual result (WIN/LOSS)
        - Profit/loss
    """
    try:
        if not RESULTS_LOG.exists():
            return {"predictions": []}

        df = pd.read_csv(RESULTS_LOG)

        # Reuse the same sport detection logic from summary endpoint
        def detect_sport_from_teams(pred_id, away_team='', home_team=''):
            if 'NBA' in pred_id:
                return 'NBA'
            elif 'NFL' in pred_id:
                return 'NFL'
            elif 'NHL' in pred_id:
                return 'NHL'
            elif 'NCAAB' in pred_id:
                return 'NCAAB'
            elif 'NCAAF' in pred_id:
                return 'NCAAF'

            team_text = f"{away_team} {home_team}".lower()
            nba_keywords = ['lakers', 'warriors', 'celtics', 'heat', 'knicks', 'bulls', 'nets', 'sixers',
                           'raptors', 'bucks', 'pacers', 'pistons', 'cavaliers', 'wizards', 'hawks',
                           'hornets', 'magic', 'mavericks', 'rockets', 'spurs', 'grizzlies', 'pelicans',
                           'thunder', 'suns', 'kings', 'clippers', 'nuggets', 'timberwolves', 'blazers', 'jazz']
            nhl_keywords = ['bruins', 'canadiens', 'senators', 'sabres', 'maple leafs', 'lightning',
                          'panthers', 'red wings', 'blackhawks', 'blue jackets', 'penguins', 'flyers',
                          'rangers', 'islanders', 'devils', 'capitals', 'hurricanes', 'predators',
                          'blues', 'jets', 'wild', 'avalanche', 'stars', 'oilers', 'flames', 'canucks',
                          'golden knights', 'kraken', 'ducks', 'sharks', 'kings']
            nfl_keywords = ['patriots', 'dolphins', 'bills', 'jets', 'ravens', 'steelers', 'browns',
                          'bengals', 'texans', 'colts', 'titans', 'jaguars', 'chiefs', 'raiders',
                          'broncos', 'chargers', 'cowboys', 'giants', 'eagles', 'commanders',
                          'packers', 'vikings', 'lions', 'bears', 'buccaneers', 'saints', 'falcons',
                          'panthers', '49ers', 'seahawks', 'rams', 'cardinals']

            if any(keyword in team_text for keyword in nba_keywords):
                return 'NBA'
            elif any(keyword in team_text for keyword in nhl_keywords):
                return 'NHL'
            elif any(keyword in team_text for keyword in nfl_keywords):
                return 'NFL'
            if any(x in team_text for x in ['state', 'university', 'college', 'tech', 'wildcats', 'bulldogs', 'tigers']):
                if 'totals' in pred_id.lower() or 'spreads' in pred_id.lower():
                    return 'NCAAB'
                return 'NCAAF'
            return 'UNKNOWN'

        def detect_bet_type(pred_id):
            if 'totals' in pred_id.lower():
                return 'totals'
            elif 'spread' in pred_id.lower():
                return 'spreads'
            elif 'moneyline' in pred_id.lower():
                return 'moneyline'
            return 'unknown'

        df['sport'] = df.apply(lambda row: detect_sport_from_teams(row['prediction_id'], row.get('away_team', ''), row.get('home_team', '')), axis=1)
        df['bet_type_detected'] = df['prediction_id'].apply(detect_bet_type)

        # Apply filters
        if bet_type:
            df = df[df['bet_type_detected'] == bet_type.lower()]
        if sport:
            df = df[df['sport'] == sport.upper()]
        if result:
            df = df[df['result'] == result.upper()]

        # Sort by date (most recent first)
        df['game_date'] = pd.to_datetime(df['game_date'])
        df = df.sort_values('game_date', ascending=False)

        # Limit results
        df = df.head(limit)

        # Format predictions
        predictions = []
        for _, row in df.iterrows():
            predictions.append({
                'prediction_id': row['prediction_id'],
                'game_date': row['game_date'].strftime('%Y-%m-%d'),
                'sport': row['sport'],
                'away_team': row['away_team'],
                'home_team': row['home_team'],
                'away_score': int(row['away_score']) if pd.notna(row['away_score']) else None,
                'home_score': int(row['home_score']) if pd.notna(row['home_score']) else None,
                'bet_type': row['bet_type_detected'].upper(),
                'recommendation': row['recommendation'],
                'confidence': row['confidence'],
                'market_total': float(row['market_total']) if pd.notna(row['market_total']) else None,
                'predicted_total': float(row['predicted_total']) if pd.notna(row['predicted_total']) else None,
                'actual_total': float(row['actual_total']) if pd.notna(row['actual_total']) else None,
                'result': row['result'],
                'profit_loss': round(float(row['profit_loss']) * 100, 2),  # Convert to $100 bet
                'edge_accuracy': float(row['edge_accuracy']) if pd.notna(row['edge_accuracy']) else None
            })

        return {
            'predictions': predictions,
            'count': len(predictions),
            'filters_applied': {
                'limit': limit,
                'bet_type': bet_type,
                'sport': sport,
                'result': result
            }
        }

    except Exception as e:
        logger.error(f"Error getting recent predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chart-data")
async def get_chart_data(days: int = Query(default=30)):
    """
    Get cumulative profit/loss data for charting

    Returns daily cumulative P/L for the chart
    """
    try:
        if not RESULTS_LOG.exists():
            return {"chart_data": []}

        df = pd.read_csv(RESULTS_LOG)

        # Filter by days
        cutoff = datetime.now() - timedelta(days=days)
        df['game_date'] = pd.to_datetime(df['game_date'])
        df = df[df['game_date'] >= cutoff]

        # Sort by date
        df = df.sort_values('game_date')

        # Calculate cumulative profit (per $100 bet)
        df['cumulative_profit'] = (df['profit_loss'] * 100).cumsum()

        # Group by date and get last cumulative value per day
        daily = df.groupby(df['game_date'].dt.date).agg({
            'cumulative_profit': 'last',
            'profit_loss': lambda x: (x * 100).sum()
        }).reset_index()

        chart_data = []
        for _, row in daily.iterrows():
            chart_data.append({
                'date': row['game_date'].strftime('%Y-%m-%d'),
                'cumulative_profit': round(row['cumulative_profit'], 2),
                'daily_profit': round(row['profit_loss'], 2)
            })

        return {
            'chart_data': chart_data,
            'days': days
        }

    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
