"""DEAD SIMPLE NHL stats loader - just reads from CSV, no API calls"""
import pandas as pd
import logging
from pathlib import Path
from typing import Optional, Dict
from live_models import NHLTeamStats

logger = logging.getLogger(__name__)
logger.info("=" * 80)
logger.info("SIMPLE_NHL_STATS MODULE IS BEING LOADED - CSV-BASED STATS LOADER")
logger.info("=" * 80)

# Global cache loaded ONCE on import
_NHL_STATS_CACHE: Dict[str, NHLTeamStats] = {}

def _load_stats_from_csv():
    """Load stats from CSV file ONCE on module import"""
    try:
        csv_path = Path(__file__).parent / "data" / "raw" / "nhl" / "team_stats_combined.csv"

        if not csv_path.exists():
            logger.error(f"NHL stats CSV not found: {csv_path}")
            return {}

        df = pd.read_csv(csv_path)
        cache = {}

        for _, row in df.iterrows():
            team_name = row['team_name']
            stats = NHLTeamStats(
                team_id=row['team_abbr'],
                team_name=team_name,
                games_played=int(row['games_played']),
                wins=int(row['wins']),
                losses=int(row['losses']),
                ot_losses=0,
                points=int(row['points']),
                win_pct=float(row['wins']) / float(row['games_played']) if row['games_played'] > 0 else 0.0,
                goals_per_game=float(row['goals_per_game']),
                goals_against_per_game=float(row['goals_against_per_game']),
                shots_per_game=float(row['shots_per_game']),
                shots_against_per_game=30.0,  # Placeholder
                power_play_pct=float(row['power_play_pct']),
                penalty_kill_pct=float(row['penalty_kill_pct']),
                faceoff_win_pct=50.0,
                shooting_pct=10.0,
                save_pct=0.910,
                pdo=100.0,
                # Empty net stats from CSV
                en_goals_for=float(row['en_goals_for']),
                en_goals_against=float(row['en_goals_against']),
                en_differential=float(row['en_differential']),
                en_situations=0.0,
                en_success_rate=0.0,
                # Simple rankings (could calculate from sorted data)
                goals_per_game_rank=16,
                goals_against_per_game_rank=16,
                power_play_rank=16,
                penalty_kill_rank=16,
                faceoff_rank=16,
                en_goals_for_rank=16,
                en_goals_against_rank=16,
            )
            cache[team_name] = stats

        logger.info(f"✅ Loaded NHL stats for {len(cache)} teams from CSV")
        return cache

    except Exception as e:
        logger.error(f"Error loading NHL stats CSV: {e}", exc_info=True)
        return {}

# Load stats ONCE when module is imported
_NHL_STATS_CACHE = _load_stats_from_csv()

def get_nhl_team_stats(team_name: str) -> Optional[NHLTeamStats]:
    """Get NHL team stats - simple lookup from pre-loaded cache"""
    # Try exact match first
    stats = _NHL_STATS_CACHE.get(team_name)

    # If not found and team name has special characters, try without accents
    if not stats and team_name == "Montréal Canadiens":
        stats = _NHL_STATS_CACHE.get("Montreal Canadiens")

    if stats:
        logger.info(f"✅ Found NHL stats for {team_name} (EN goals: {stats.en_goals_for})")
    else:
        logger.warning(f"❌ No NHL stats found for: {team_name}. Available teams: {list(_NHL_STATS_CACHE.keys())[:3]}...")
    return stats
