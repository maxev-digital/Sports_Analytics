"""Add missing fields to NFLTeamStats model"""

with open('live_models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add the two missing fields
old_section = """    # === NEW: MISCELLANEOUS (5 fields) ===
    two_point_conversion_pct: Optional[float] = None  # 2-pt conversions
    penalty_yards_per_game: Optional[float] = None  # Penalty yards
    plays_per_game: Optional[float] = None  # Total plays
    opponent_plays_per_game: Optional[float] = None  # Opponent plays
    opponent_first_downs_per_game: Optional[float] = None  # First downs allowed"""

new_section = """    # === NEW: MISCELLANEOUS (7 fields) ===
    two_point_conversion_pct: Optional[float] = None  # 2-pt conversions
    penalty_yards_per_game: Optional[float] = None  # Penalty yards
    plays_per_game: Optional[float] = None  # Total plays
    opponent_plays_per_game: Optional[float] = None  # Opponent plays
    first_downs_per_game: Optional[float] = None  # First downs gained
    time_of_possession: Optional[float] = None  # Average time of possession
    opponent_first_downs_per_game: Optional[float] = None  # First downs allowed"""

content = content.replace(old_section, new_section)

with open('live_models.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] Added first_downs_per_game and time_of_possession to NFLTeamStats model")
