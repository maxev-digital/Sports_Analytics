"""API routes for strategy backtest results"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

# Add backtesting directory to path
backtesting_path = Path(__file__).parent.parent / "backtesting"
sys.path.append(str(backtesting_path))

from database.backtest_db import BacktestDB

router = APIRouter(prefix="/api/strategies", tags=["strategies"])

# Strategy metadata (from Live Betting Angles.md)
STRATEGIES = [
    {
        "id": 1,
        "name": "The Hot-Shooting Fade",
        "angle_number": 1,
        "description": "Fade teams that had an unusually hot shooting night in their previous game",
        "why_it_works": "Shooting percentages regress to the mean. Teams that shoot 15%+ above their season average are likely to cool off in subsequent games, creating betting value on the opposing team or under.",
        "sports": ["NBA", "NCAA Basketball"],
        "difficulty": "EASY",
        "typical_ev_min": 8.0,
        "typical_ev_max": 15.0,
        "status": "pending"
    },
    {
        "id": 2,
        "name": "Momentum Shift Betting",
        "angle_number": 2,
        "description": "Bet on teams immediately after a major momentum shift in the game",
        "why_it_works": "Books are slow to adjust lines after key events (ejections, injury timeouts, flagrant fouls). Quick bettors can capture value before the line corrects.",
        "sports": ["NBA", "NFL", "NHL"],
        "difficulty": "MEDIUM",
        "typical_ev_min": 5.0,
        "typical_ev_max": 12.0,
        "status": "pending"
    },
    {
        "id": 3,
        "name": "Injury Cascade Props",
        "angle_number": 3,
        "description": "Target player props on role players when stars get injured mid-game",
        "why_it_works": "When a star exits, usage rates shift dramatically to role players. Books are slow to adjust player props for bench players, creating massive edges on rebounds, points, assists for the replacements.",
        "sports": ["NBA", "NFL"],
        "difficulty": "HARD",
        "typical_ev_min": 15.0,
        "typical_ev_max": 30.0,
        "status": "pending"
    },
    {
        "id": 4,
        "name": "The Pace Trap",
        "angle_number": 4,
        "description": "Bet overs when slow-paced teams fall behind early",
        "why_it_works": "Teams that normally play slow (rank 25-30 in pace) are forced to speed up when trailing by 10+ points. This increases possessions and total scoring beyond what the market expects.",
        "sports": ["NBA", "NCAA Basketball"],
        "difficulty": "EASY",
        "typical_ev_min": 10.0,
        "typical_ev_max": 18.0,
        "status": "pending"
    },
    {
        "id": 5,
        "name": "Foul Trouble Overs",
        "angle_number": 5,
        "description": "Bet team totals over when key defenders pick up early fouls",
        "why_it_works": "When elite defenders sit with foul trouble, opposing team efficiency skyrockets. Books undervalue defensive replacements, especially in Q1-Q2.",
        "sports": ["NBA", "NCAA Basketball"],
        "difficulty": "MEDIUM",
        "typical_ev_min": 8.0,
        "typical_ev_max": 16.0,
        "status": "pending"
    },
    {
        "id": 6,
        "name": "Goalie Pull Alert",
        "angle_number": 6,
        "description": "Bet team totals over when trailing teams pull their goalie early",
        "why_it_works": "Empty net situations create asymmetric scoring opportunities. 2023-24 NHL data (581 pulls) shows 80.4% hit rate with at least 1 goal scored, averaging 0.97 goals added per game. Moneypuck verified.",
        "sports": ["NHL"],
        "difficulty": "EASY",
        "typical_ev_min": 45.0,
        "typical_ev_max": 65.0,
        "status": "proven"
    },
    {
        "id": 7,
        "name": "Blowout Contrarian Spreads",
        "angle_number": 7,
        "description": "Bet underdogs when they're down big at halftime but showing fight",
        "why_it_works": "Public hammers favorites in blowouts, inflating 2H spreads. Underdogs that keep it within 20-25 at half often cover 2H spreads due to garbage time and favorite complacency.",
        "sports": ["NBA", "NFL"],
        "difficulty": "MEDIUM",
        "typical_ev_min": 6.0,
        "typical_ev_max": 14.0,
        "status": "pending"
    },
    {
        "id": 8,
        "name": "End-Game Unders",
        "angle_number": 8,
        "description": "Bet Q4 under when there's a blowout after Q3",
        "why_it_works": "Books undervalue garbage time clock management. When games are decided (15+ point differential after Q3), both teams sub in benches and milk the clock, leading to significantly lower Q4 scoring.",
        "sports": ["NBA", "NCAA Basketball"],
        "difficulty": "EASY",
        "typical_ev_min": 10.0,
        "typical_ev_max": 20.0,
        "status": "active"  # This one has backtest data
    },
    {
        "id": 9,
        "name": "Overtime Total Resets",
        "angle_number": 9,
        "description": "Bet under on adjusted OT totals after high-scoring regulation",
        "why_it_works": "If regulation goes over by a lot, OT totals are often inflated. Teams are exhausted, defensive intensity drops unevenly, and variance regresses.",
        "sports": ["NBA", "NFL", "NHL"],
        "difficulty": "MEDIUM",
        "typical_ev_min": 7.0,
        "typical_ev_max": 15.0,
        "status": "pending"
    },
    {
        "id": 10,
        "name": "Fatigue Spreads (Back-to-Backs)",
        "angle_number": 10,
        "description": "Bet against teams on 2nd night of back-to-back playing against rested opponents",
        "why_it_works": "Live lines don't adjust enough for cumulative fatigue. Performance drops significantly in Q3-Q4 for teams playing B2B games, especially on the road.",
        "sports": ["NBA", "NHL"],
        "difficulty": "EASY",
        "typical_ev_min": 8.0,
        "typical_ev_max": 16.0,
        "status": "pending"
    },
    {
        "id": 11,
        "name": "Coaching Timeout Value",
        "angle_number": 11,
        "description": "Bet against teams immediately after burning all timeouts early",
        "why_it_works": "Teams without timeouts can't stop opponent runs or draw up plays in crucial moments. Books underestimate the strategic disadvantage.",
        "sports": ["NBA", "NFL"],
        "difficulty": "HARD",
        "typical_ev_min": 5.0,
        "typical_ev_max": 12.0,
        "status": "pending"
    },
    {
        "id": 12,
        "name": "Weather-Driven Live Totals",
        "angle_number": 12,
        "description": "Bet unders when weather deteriorates during outdoor games",
        "why_it_works": "Books set pregame totals on forecasts, but actual conditions (wind gusts, rain intensity) impact play more than modeled. Live totals lag real-time weather impact.",
        "sports": ["NFL", "MLB"],
        "difficulty": "MEDIUM",
        "typical_ev_min": 10.0,
        "typical_ev_max": 20.0,
        "status": "pending"
    },
    {
        "id": 13,
        "name": "Favorite Comeback Detection",
        "description": "Identify when pre-game favorites trailing after hot underdog starts are prime comeback candidates",
        "why_it_works": "Strong favorites often trail early due to underdog variance (hot shooting, crowd energy). When talent gap is 5+ PPG, regression to the mean favors comeback. Historical data: favorites down at halftime cover 2H spread 60.3% (2005-2023).",
        "sports": ["NBA"],
        "difficulty": "MEDIUM",
        "typical_ev_min": 8.0,
        "typical_ev_max": 12.0,
        "status": "pending"
    },
    {
        "id": 14,
        "name": "Quarter Reversal Strategy",
        "description": "Teams winning 2 consecutive quarters lose the next quarter at 55-61% rate (+8-35% ROI)",
        "why_it_works": "Regression to mean after hot quarters. Real backtested data: Q1-Q2 winners lose Q3 at 55.3% (+12.1% ROI). Q2-Q3 winners lose Q4 at 52.7% (+8.9% ROI). Q3-Q4 winners lose OT at 60.7% (+35.2% ROI). 1,230 NBA games from balldontlie.io (2023-2024 season).",
        "sports": ["NBA"],
        "difficulty": "MEDIUM",
        "typical_ev_min": 8.0,
        "typical_ev_max": 35.0,
        "status": "active"
    },
    {
        "id": 15,
        "name": "Line Movement Arbitrage",
        "description": "Capitalize on line movement discrepancies between bookmakers",
        "why_it_works": "Different books adjust lines at different speeds. Quick detection of line movement creates arbitrage opportunities before markets sync.",
        "sports": ["NBA", "NFL", "NHL", "MLB"],
        "difficulty": "MEDIUM",
        "typical_ev_min": 2.0,
        "typical_ev_max": 8.0,
        "status": "pending"
    },
    {
        "id": 16,
        "name": "Middle Opportunity Detection",
        "description": "Identify and exploit middle betting opportunities across multiple bookmakers",
        "why_it_works": "Line discrepancies create windows where you can bet both sides with a chance to win both bets. Risk-free profit when the result lands in the middle.",
        "sports": ["NBA", "NFL", "NHL", "MLB"],
        "difficulty": "EASY",
        "typical_ev_min": 5.0,
        "typical_ev_max": 15.0,
        "status": "pending"
    },
    {
        "id": 17,
        "name": "Sharp Money Tracking",
        "description": "Follow professional betting patterns by monitoring line movements without corresponding public betting trends",
        "why_it_works": "Sharp money moves lines even when public is betting the other side. Tracking reverse line movement identifies where professionals are placing bets.",
        "sports": ["NBA", "NFL", "NHL", "MLB"],
        "difficulty": "HARD",
        "typical_ev_min": 4.0,
        "typical_ev_max": 10.0,
        "status": "pending"
    },
    {
        "id": 18,
        "name": "CLV Tracker (Closing Line Value)",
        "description": "Tracks whether user bets beat the closing line - the most important metric for long-term profitability",
        "why_it_works": "Beating closing line = 53%+ win rate long-term. The market is most efficient at closing (sharpest number). If you beat closing consistently, you WILL profit long-term. Sharp bettors average +2 to +5 points CLV.",
        "sports": ["NBA", "NFL", "NHL", "MLB"],
        "difficulty": "MEDIUM",
        "typical_ev_min": 4.0,
        "typical_ev_max": 10.0,
        "status": "pending"
    },
    {
        "id": 19,
        "name": "Home/Away Splits Strategy",
        "description": "Identifies betting value based on team performance differentials between home and away games",
        "why_it_works": "Teams with 10+ point home/away differential: 56-58% ATS. Extreme home teams hosting weak road teams: 60%+ ATS. Market often undervalues these splits.",
        "sports": ["NBA", "NFL", "NHL", "MLB"],
        "difficulty": "MEDIUM",
        "typical_ev_min": 6.0,
        "typical_ev_max": 14.0,
        "status": "pending"
    },
    {
        "id": 20,
        "name": "Divisional Rivalries Strategy",
        "description": "Identifies betting value in division games based on historical trends and rivalry dynamics",
        "why_it_works": "NFL Division Games: Underdogs 54-56% ATS (vs 48-50% non-division). NBA Division Games: Totals 53% UNDER. Division games are MORE competitive as teams know each other well.",
        "sports": ["NBA", "NFL", "NHL"],
        "difficulty": "MEDIUM",
        "typical_ev_min": 4.0,
        "typical_ev_max": 10.0,
        "status": "pending"
    },
    {
        "id": 21,
        "name": "Key Numbers Strategy (NFL)",
        "description": "Analyzes NFL spreads for key number opportunities (3, 7, 10)",
        "why_it_works": "Key number 3 occurs in 15.1% of NFL games, 7 in 9.0%. When lines cross key numbers, getting the right side provides significant edge. Half-point positions near key numbers are premium.",
        "sports": ["NFL"],
        "difficulty": "EASY",
        "typical_ev_min": 10.0,
        "typical_ev_max": 18.0,
        "status": "pending"
    },
    {
        "id": 22,
        "name": "Low-Hold Opportunities",
        "description": "Identifies betting opportunities with low bookmaker hold (vig)",
        "why_it_works": "Betting only <3% hold games improves expected ROI by 1-2%. Sharp books (Pinnacle, Circa) have low holds (2-3%). Lower hold = less bookmaker edge and more potential profit.",
        "sports": ["NBA", "NFL", "NHL", "MLB"],
        "difficulty": "EASY",
        "typical_ev_min": 2.0,
        "typical_ev_max": 5.0,
        "status": "pending"
    },
    {
        "id": 23,
        "name": "Halftime Tracker",
        "description": "Identifies 2H betting opportunities based on 1H performance and regression analysis",
        "why_it_works": "60.2% ATS on 2H spreads (2015-2023), +11.3% ROI. Uses 5-factor scoring system (shooting deviation, pace deviation, fatigue, score situation, coaching adjustments). Teams regress to season averages in 2H.",
        "sports": ["NBA", "NCAA Basketball"],
        "difficulty": "MEDIUM",
        "typical_ev_min": 9.0,
        "typical_ev_max": 13.0,
        "status": "active"
    },
    {
        "id": 24,
        "name": "Momentum Detector",
        "description": "Detects when teams are 'on a run' and live odds haven't fully adjusted",
        "why_it_works": "Short-term momentum shifts create betting value before markets catch up. NBA: 10+ point runs. NHL: Goal clusters (2+ goals in 5 min), shot spikes. Books are slow to adjust live odds during runs.",
        "sports": ["NBA", "NHL"],
        "difficulty": "MEDIUM",
        "typical_ev_min": 6.0,
        "typical_ev_max": 15.0,
        "status": "active"
    },
    {
        "id": 25,
        "name": "Pace Mismatch Detector",
        "description": "Detects EV opportunities based on pace tempo mismatches and projections",
        "why_it_works": "Fast teams vs slow teams create exploitable totals. Rest advantages increase pace, back-to-backs decrease pace. Home teams control tempo more. Significant pace mismatch (5+ possessions) = 56-58% ATS on totals.",
        "sports": ["NBA", "NCAA Basketball"],
        "difficulty": "MEDIUM",
        "typical_ev_min": 8.0,
        "typical_ev_max": 15.0,
        "status": "active"
    }
]


@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_strategies(sport: Optional[str] = None):
    """
    Get all strategies with metadata

    Args:
        sport: Optional filter by sport (NBA, NFL, NHL, MLB)

    Returns:
        List of strategy metadata
    """
    try:
        strategies = STRATEGIES.copy()

        # Filter by sport if provided
        if sport and sport.upper() != "ALL":
            strategies = [
                s for s in strategies
                if sport.upper() in [sp.upper() for sp in s["sports"]]
            ]

        return strategies

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}", response_model=Dict[str, Any])
async def get_strategy(strategy_id: int):
    """
    Get a specific strategy by ID

    Args:
        strategy_id: Strategy ID

    Returns:
        Strategy metadata
    """
    try:
        strategy = next((s for s in STRATEGIES if s["id"] == strategy_id), None)

        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

        return strategy

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}/backtest-results", response_model=Dict[str, Any])
async def get_strategy_backtest_results(strategy_id: int):
    """
    Get backtest results for a specific strategy

    Args:
        strategy_id: Strategy ID

    Returns:
        Backtest results with performance metrics
    """
    try:
        # Get strategy metadata
        strategy = next((s for s in STRATEGIES if s["id"] == strategy_id), None)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

        # Get backtest results from database
        db = BacktestDB()
        backtest_results = db.get_backtest_results(strategy_id=strategy_id)

        if not backtest_results:
            # No backtest data yet
            return {
                "strategy": strategy,
                "backtest_status": "pending",
                "message": "Backtest not yet run for this strategy"
            }

        # Get the most recent backtest result
        latest_result = backtest_results[0]

        return {
            "strategy": strategy,
            "backtest_status": "complete",
            "results": latest_result,
            "all_backtests": backtest_results  # Include historical backtests
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/summary", response_model=Dict[str, Any])
async def get_performance_summary(sport: Optional[str] = None):
    """
    Get aggregate performance summary across all strategies

    Args:
        sport: Optional filter by sport

    Returns:
        Overall performance metrics
    """
    try:
        db = BacktestDB()

        # Get all backtest results
        all_results = db.get_backtest_results(sport=sport)

        if not all_results:
            return {
                "total_strategies": len(STRATEGIES),
                "backtested_strategies": 0,
                "overall_win_rate": 0.0,
                "overall_roi": 0.0,
                "total_bets": 0,
                "total_wins": 0,
                "total_losses": 0,
                "total_pushes": 0,
                "total_profit": 0.0,
                "strategies": [],  # Add empty array to prevent frontend errors
                "message": "No backtest data available yet"
            }

        # Calculate aggregate metrics
        total_bets = sum(r["bets_placed"] for r in all_results)
        total_wins = sum(r["wins"] for r in all_results)
        total_losses = sum(r["losses"] for r in all_results)
        total_pushes = sum(r["pushes"] for r in all_results)
        total_profit = sum(r["profit_loss"] for r in all_results)

        overall_win_rate = (total_wins / total_bets * 100) if total_bets > 0 else 0.0
        overall_roi = (total_profit / total_bets * 100) if total_bets > 0 else 0.0

        # Get unique strategy count
        backtested_strategy_ids = set(r["strategy_id"] for r in all_results)

        return {
            "total_strategies": len(STRATEGIES),
            "backtested_strategies": len(backtested_strategy_ids),
            "overall_win_rate": round(overall_win_rate, 1),
            "overall_roi": round(overall_roi, 1),
            "total_bets": total_bets,
            "total_wins": total_wins,
            "total_losses": total_losses,
            "total_pushes": total_pushes,
            "total_profit": round(total_profit, 2),
            "strategies": [
                {
                    "strategy_id": r["strategy_id"],
                    "strategy_name": next((s["name"] for s in STRATEGIES if s["id"] == r["strategy_id"]), "Unknown"),
                    "win_rate": r["win_rate"],
                    "roi": r["roi"],
                    "bets_placed": r["bets_placed"],
                    "baseline_odds": r.get("baseline_odds", -110),
                    "bet_type": r.get("bet_type", "Live Total"),
                    "odds_trigger": r.get("odds_trigger", "+110 or better"),
                    "frequency": r.get("frequency", "2x/week"),
                    "confidence": r.get("confidence", 7),
                    "wins": r["wins"],
                    "losses": r["losses"]
                }
                for r in all_results
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regression-to-mean/analyze")
async def analyze_regression_opportunities(
    game_features: Dict[str, Any],
    live_totals: Dict[str, float],
    pregame_total: Optional[float] = None
):
    """
    Analyze a game for regression-to-mean betting opportunities

    STRATEGY: Regression to Mean Basketball Totals
    - Identifies when live totals deviate significantly from model predictions
    - Bets on statistical regression toward expected value
    - Kelly sizing based on deviation distance

    Args:
        game_features: Dict with team stats and features
        live_totals: Dict of {bookmaker: live_total}
        pregame_total: Opening total for reference (optional)

    Returns:
        List of betting alerts with recommendations

    Example Request:
    {
        "game_features": {
            "home_team": "Duke",
            "away_team": "North Carolina",
            "home_adj_em": 25.5,
            "away_adj_em": 22.1,
            "home_off_eff": 118.2,
            "away_off_eff": 115.7,
            "home_def_eff": 92.7,
            "away_def_eff": 93.6,
            "home_tempo": 72.5,
            "away_tempo": 70.2
        },
        "live_totals": {
            "DraftKings": 155.5,
            "FanDuel": 156.0,
            "BetMGM": 154.5
        },
        "pregame_total": 158.5
    }
    """
    try:
        import sys
        from pathlib import Path
        strategies_path = Path(__file__).parent.parent / "strategies"
        sys.path.append(str(strategies_path))

        from regression_to_mean_totals import RegressionToMeanStrategy

        # Initialize strategy
        strategy = RegressionToMeanStrategy(
            model_path="backend/ml/models/ncaab_quantile_mean_latest.json",
            z_score_threshold=2.0,
            min_confidence=0.60,
            min_edge=3.0
        )

        # Analyze game
        alerts = strategy.analyze_game(
            game_features=game_features,
            live_totals=live_totals,
            pregame_total=pregame_total
        )

        return {
            "status": "success",
            "game": f"{game_features.get('home_team', 'Home')} vs {game_features.get('away_team', 'Away')}",
            "opportunities_found": len(alerts),
            "alerts": alerts
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regression-to-mean/live-alerts")
async def get_live_regression_alerts():
    """
    Get current regression-to-mean alerts for all live games

    Returns:
        Latest alerts from the live monitoring system
    """
    try:
        from pathlib import Path
        import json

        # Read latest alerts file
        alerts_path = Path("backend/data/alerts/regression_alerts_latest.json")

        if not alerts_path.exists():
            return {
                "status": "success",
                "alerts": [],
                "message": "No active alerts"
            }

        with open(alerts_path, 'r') as f:
            alerts = json.load(f)

        # Filter alerts from last 10 minutes
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(minutes=10)

        recent_alerts = [
            a for a in alerts
            if datetime.fromisoformat(a['timestamp']) > cutoff
        ]

        return {
            "status": "success",
            "alerts": recent_alerts,
            "total_alerts": len(recent_alerts),
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
