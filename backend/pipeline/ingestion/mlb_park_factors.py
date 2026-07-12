"""
MLB park factors — 2026 run factors (multi-year average from Baseball Reference).
Factor > 1.0 means hitter-friendly; < 1.0 means pitcher-friendly.
"""
from __future__ import annotations

_PARK_FACTORS: dict[str, float] = {
    "Colorado Rockies": 1.16,
    "Cincinnati Reds": 1.10,
    "Arizona Diamondbacks": 1.07,
    "Texas Rangers": 1.06,
    "Boston Red Sox": 1.05,
    "Chicago White Sox": 1.04,
    "Milwaukee Brewers": 1.03,
    "Philadelphia Phillies": 1.02,
    "New York Yankees": 1.02,
    "Detroit Tigers": 1.01,
    "Minnesota Twins": 1.01,
    "Baltimore Orioles": 1.01,
    "Toronto Blue Jays": 1.00,
    "Kansas City Royals": 1.00,
    "Oakland Athletics": 1.00,
    "Cleveland Guardians": 0.99,
    "Houston Astros": 0.99,
    "Los Angeles Angels": 0.99,
    "Pittsburgh Pirates": 0.98,
    "Washington Nationals": 0.98,
    "New York Mets": 0.98,
    "Chicago Cubs": 0.97,
    "St. Louis Cardinals": 0.97,
    "Atlanta Braves": 0.97,
    "Miami Marlins": 0.97,
    "Tampa Bay Rays": 0.96,
    "Seattle Mariners": 0.95,
    "Los Angeles Dodgers": 0.95,
    "San Diego Padres": 0.94,
    "San Francisco Giants": 0.94,
}


def get_park_factor(home_team: str) -> float:
    """Return the run park factor for the home team. Defaults to 1.0 if unknown."""
    return _PARK_FACTORS.get(home_team, 1.0)


def apply_park_factor_to_prob(over_prob: float, home_team: str) -> float:
    """
    Adjust an over probability by the home team's park factor.
    Hitter-friendly parks (factor > 1.0) push over probability higher.
    """
    factor = get_park_factor(home_team)
    park_dev = factor - 1.0
    adjustment = park_dev * 0.35
    return max(0.10, min(0.90, over_prob + adjustment))
