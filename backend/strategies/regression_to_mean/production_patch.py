"""
Production Patch: Add NCAAB Analytics to main.py
Run this on the production server to add analytics integration
"""

import re

MAIN_PY_PATH = "/root/sporttrader/backend/main.py"

# Read the file
with open(MAIN_PY_PATH, "r") as f:
    content = f.read()

# Backup
with open(MAIN_PY_PATH + ".backup", "w") as f:
    f.write(content)
print("✅ Backup created")

# 1. Add imports after "from game_tracker import GameTracker"
import_marker = "from game_tracker import GameTracker"
import_addition = """from game_tracker import GameTracker
from strategies.regression_to_mean.quick_start_adapter import QuickStartAnalytics
import pandas as pd
import glob"""

content = content.replace(import_marker, import_addition)
print("✅ Added imports")

# 2. Add analytics initialization after "tracker = GameTracker()"
tracker_init = """tracker = GameTracker()

# Initialize NCAAB Advanced Analytics
try:
    kenpom_files = glob.glob("/root/sporttrader/backend/data/raw/ncaab/kenpom_*.csv")
    if kenpom_files:
        latest_kenpom = max(kenpom_files)
        kenpom_df = pd.read_csv(latest_kenpom)
        quick_analytics = QuickStartAnalytics(kenpom_df)
        logger.info(f"✅ NCAAB Advanced Analytics Ready! Using {latest_kenpom}")
    else:
        quick_analytics = None
        logger.warning("⚠️ No KenPom data found, Advanced analytics unavailable")
except Exception as e:
    logger.error(f"⚠️ Advanced analytics initialization failed: {e}")
    quick_analytics = None"""

content = content.replace("tracker = GameTracker()", tracker_init)
print("✅ Added analytics initialization")

# 3. Add analytics enrichment in /api/games endpoint
# Find the line and add code after it
pattern = r"(filtered_games = filter_games_by_bookmakers\(all_games, settings\['enabled_bookmakers'\]\))"
replacement = r'''\1

        # Enrich NCAAB games with advanced analytics
        if quick_analytics:
            for game in filtered_games:
                if game.state.sport_key == 'basketball_ncaab':
                    try:
                        live_total = game.odds[0].total if game.odds else None
                        pregame_total = game.projection.pregame_total if game.projection else None
                        if live_total:
                            analytics = quick_analytics.generate_analytics(
                                home_team=game.state.home_team.name,
                                away_team=game.state.away_team.name,
                                live_total=live_total,
                                pregame_total=pregame_total
                            )
                            if analytics:
                                game.ncaab_analytics = analytics
                    except Exception as e:
                        logger.warning(f"Could not generate analytics for {game.state.id}: {e}")'''

content = re.sub(pattern, replacement, content)
print("✅ Added analytics enrichment to /api/games")

# Write back
with open(MAIN_PY_PATH, "w") as f:
    f.write(content)

print("\n🎉 SUCCESS! main.py updated with NCAAB Analytics")
print("Run: systemctl restart sporttrader")
