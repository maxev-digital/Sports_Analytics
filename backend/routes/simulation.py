"""
Monte Carlo Simulation API Routes
FastAPI endpoints for possession-based Monte Carlo simulations
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import sys
from pathlib import Path

# Add simulation directory to path
sim_path = Path(__file__).parent.parent / "simulation"
sys.path.append(str(sim_path))

from monte_carlo_totals import (
    PossessionMonteCarloSimulator,
    GameState,
    TeamStats
)

router = APIRouter(prefix="/api/simulation", tags=["simulation"])

# Initialize simulator (singleton pattern)
simulator = None


def get_simulator():
    """Lazy load simulator"""
    global simulator
    if simulator is None:
        simulator = PossessionMonteCarloSimulator()
    return simulator


# ========== REQUEST/RESPONSE MODELS ==========

class CurrentState(BaseModel):
    """Current game state"""
    quarter: int = Field(..., ge=1, le=4, description="Current quarter (1-4)")
    time_remaining: str = Field(..., description="Time remaining in current quarter (MM:SS format)")
    home_score: int = Field(..., ge=0, description="Current home team score")
    away_score: int = Field(..., ge=0, description="Current away team score")

    class Config:
        schema_extra = {
            "example": {
                "quarter": 3,
                "time_remaining": "4:32",
                "home_score": 82,
                "away_score": 78
            }
        }


class TeamStatsRequest(BaseModel):
    """Team statistics for simulation"""
    pace: float = Field(..., gt=0, description="Possessions per 48 minutes")
    off_rating: float = Field(..., gt=0, description="Offensive rating (points per 100 possessions)")
    def_rating: float = Field(..., gt=0, description="Defensive rating (points allowed per 100 possessions)")

    class Config:
        schema_extra = {
            "example": {
                "pace": 100.5,
                "off_rating": 118.2,
                "def_rating": 110.5
            }
        }


class MonteCarloRequest(BaseModel):
    """Request model for Monte Carlo simulation"""
    game_id: str = Field(..., description="Unique game identifier")
    current_state: CurrentState = Field(..., description="Current game state")
    home_stats: TeamStatsRequest = Field(..., description="Home team statistics")
    away_stats: TeamStatsRequest = Field(..., description="Away team statistics")
    market_total: float = Field(..., gt=0, description="Current betting market total")
    n_simulations: Optional[int] = Field(10000, ge=1000, le=50000, description="Number of simulations (default 10000)")

    class Config:
        schema_extra = {
            "example": {
                "game_id": "nba_20251108_LAL_BOS",
                "current_state": {
                    "quarter": 3,
                    "time_remaining": "4:32",
                    "home_score": 82,
                    "away_score": 78
                },
                "home_stats": {
                    "pace": 100.5,
                    "off_rating": 118.2,
                    "def_rating": 110.5
                },
                "away_stats": {
                    "pace": 98.3,
                    "off_rating": 115.8,
                    "def_rating": 108.9
                },
                "market_total": 235.5,
                "n_simulations": 10000
            }
        }


class MonteCarloResponse(BaseModel):
    """Response model for Monte Carlo simulation"""
    status: str
    game_id: str

    # Probability distribution
    over_probability: float
    under_probability: float
    push_probability: float

    # Expected value
    over_ev: float
    under_ev: float

    # Recommendation
    recommended_bet: Optional[str]
    edge: float
    kelly_pct: float

    # Distribution statistics
    percentiles: Dict[str, float]
    mean: float
    median: float
    std_dev: float
    min: float
    max: float

    # Metadata
    metadata: Dict[str, Any]

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "game_id": "nba_20251108_LAL_BOS",
                "over_probability": 0.0012,
                "under_probability": 0.9988,
                "push_probability": 0.0000,
                "over_ev": -0.9989,
                "under_ev": 0.9079,
                "recommended_bet": "UNDER",
                "edge": 0.9079,
                "kelly_pct": 5.00,
                "percentiles": {
                    "5th": 192.9,
                    "10th": 194.4,
                    "25th": 196.9,
                    "50th": 199.6,
                    "75th": 202.3,
                    "90th": 204.8,
                    "95th": 206.2
                },
                "mean": 199.6,
                "median": 199.6,
                "std_dev": 4.04,
                "min": 187.2,
                "max": 212.8,
                "metadata": {
                    "current_total": 160,
                    "remaining_minutes": 16.53,
                    "estimated_remaining_possessions": 34.2,
                    "n_simulations": 10000
                }
            }
        }


# ========== ENDPOINTS ==========

@router.post("/monte-carlo", include_in_schema=True)
@router.post("/monte-carlo/totals", response_model=MonteCarloResponse)
async def run_monte_carlo_simulation(request: MonteCarloRequest):
    """
    Run possession-by-possession Monte Carlo simulation for live game

    This endpoint simulates the remaining possessions in a live game and returns
    probability distributions, expected value calculations, and betting recommendations.

    **How it works:**
    1. Calculates remaining game time and possessions based on current state
    2. Simulates each remaining possession individually with realistic variance
    3. Generates probability distribution of final totals
    4. Calculates over/under probabilities vs market line
    5. Computes expected value and Kelly Criterion bet sizing

    **Use Cases:**
    - Live betting decision support
    - Visualizing probability distributions for user
    - Identifying +EV opportunities during games
    - Kelly Criterion bankroll management
    """
    try:
        # Get simulator instance
        sim = get_simulator()

        # Convert request models to simulation objects
        game_state = GameState(
            quarter=request.current_state.quarter,
            time_remaining=request.current_state.time_remaining,
            home_score=request.current_state.home_score,
            away_score=request.current_state.away_score
        )

        home_stats = TeamStats(
            pace=request.home_stats.pace,
            off_rating=request.home_stats.off_rating,
            def_rating=request.home_stats.def_rating
        )

        away_stats = TeamStats(
            pace=request.away_stats.pace,
            off_rating=request.away_stats.off_rating,
            def_rating=request.away_stats.def_rating
        )

        # Run Monte Carlo simulation
        result = sim.run_monte_carlo(
            game_state=game_state,
            home_stats=home_stats,
            away_stats=away_stats,
            market_total=request.market_total,
            n_simulations=request.n_simulations
        )

        # Build response
        response = MonteCarloResponse(
            status="success",
            game_id=request.game_id,
            over_probability=result['over_probability'],
            under_probability=result['under_probability'],
            push_probability=result['push_probability'],
            over_ev=result['over_ev'],
            under_ev=result['under_ev'],
            recommended_bet=result['recommended_bet'],
            edge=result['edge'],
            kelly_pct=result['kelly_pct'],
            percentiles=result['percentiles'],
            mean=result['mean'],
            median=result['median'],
            std_dev=result['std_dev'],
            min=result['min'],
            max=result['max'],
            metadata=result['metadata']
        )

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Monte Carlo Simulation",
        "version": "1.0.0"
    }
