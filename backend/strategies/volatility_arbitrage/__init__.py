"""
Volatility Arbitrage Strategy Module

Hybrid volatility arbitrage system that enters +money positions during
favorable game states and optionally hedges when the opposite side
reaches target price, creating locked profit scenarios.
"""

from .detector import VolatilityArbDetector
from .position_tracker import VolatilityPositionTracker
from .calculator import VolatilityArbCalculator
from .models import (
    EntryOpportunity,
    VolatilityPosition,
    HedgeAlert,
    PositionResult,
    PerformanceStats
)
from .config import *

__all__ = [
    'VolatilityArbDetector',
    'VolatilityPositionTracker',
    'VolatilityArbCalculator',
    'EntryOpportunity',
    'VolatilityPosition',
    'HedgeAlert',
    'PositionResult',
    'PerformanceStats',
]
