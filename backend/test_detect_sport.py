#!/usr/bin/env python3
"""Test detect_sport function"""
from sport_detector import detect_sport

teams = [
    ("Los Angeles Lakers", "Boston Celtics"),
    ("Miami Heat", "Milwaukee Bucks"),
    ("Dallas Mavericks", "Denver Nuggets"),
]

for home, away in teams:
    sport = detect_sport(home, away)
    print(f"{away} @ {home} -> '{sport}'")
