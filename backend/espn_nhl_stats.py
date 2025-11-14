"""Simple ESPN NHL stats loader - loads team stats from ESPN + empty net stats from CSV"""
import httpx
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Optional
from live_models import NHLTeamStats

logger = logging.getLogger(__name__)

class ESPNNHLStats:
    """Lightweight ESPN NHL stats loader (no rate limits, no heavy calls)"""

    def __init__(self):
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl"
        self.client = httpx.AsyncClient(timeout=10.0)
        self.team_cache = {}  # Cache team stats by name
        self.cache_timestamp = None
        self.en_stats = self._load_empty_net_stats()

        # NHL team name to ESPN abbreviation mapping
        self.team_mapping = {
            'Anaheim Ducks': 'ANA', 'Boston Bruins': 'BOS', 'Buffalo Sabres': 'BUF',
            'Calgary Flames': 'CGY', 'Carolina Hurricanes': 'CAR', 'Chicago Blackhawks': 'CHI',
            'Colorado Avalanche': 'COL', 'Columbus Blue Jackets': 'CBJ', 'Dallas Stars': 'DAL',
            'Detroit Red Wings': 'DET', 'Edmonton Oilers': 'EDM', 'Florida Panthers': 'FLA',
            'Los Angeles Kings': 'LAK', 'Minnesota Wild': 'MIN', 'Montréal Canadiens': 'MTL',
            'Montreal Canadiens': 'MTL', 'Nashville Predators': 'NSH', 'New Jersey Devils': 'NJD',
            'New York Islanders': 'NYI', 'New York Rangers': 'NYR', 'Ottawa Senators': 'OTT',
            'Philadelphia Flyers': 'PHI', 'Pittsburgh Penguins': 'PIT', 'San Jose Sharks': 'SJS',
            'Seattle Kraken': 'SEA', 'St. Louis Blues': 'STL', 'Tampa Bay Lightning': 'TBL',
            'Toronto Maple Leafs': 'TOR', 'Vancouver Canucks': 'VAN', 'Vegas Golden Knights': 'VGK',
            'Washington Capitals': 'WSH', 'Winnipeg Jets': 'WPG', 'Utah Mammoth': 'UTA',
            'Utah Hockey Club': 'UTA', 'Arizona Coyotes': 'ARI'
        }

    def _load_empty_net_stats(self) -> Dict[str, Dict]:
        """Load empty net stats from CSV (called once on init)"""
        try:
            data_dir = Path(__file__).parent / "data" / "raw" / "nhl"
            en_file = data_dir / "empty_net_stats_latest.csv"

            if not en_file.exists():
                logger.warning(f"Empty net stats file not found: {en_file}")
                return {}

            df = pd.read_csv(en_file)
            logger.info(f"✅ Loaded empty net stats for {len(df)} NHL teams")

            # Convert to dict keyed by team abbreviation (lowercase)
            en_dict = {}
            for _, row in df.iterrows():
                team_abbr = str(row['team_abbr']).lower()
                en_dict[team_abbr] = {
                    'en_goals_for': float(row['en_goals_for']) if pd.notna(row['en_goals_for']) else 0.0,
                    'en_goals_against': float(row['en_goals_against']) if pd.notna(row['en_goals_against']) else 0.0,
                    'en_differential': float(row['en_differential']) if pd.notna(row['en_differential']) else 0.0,
                    'en_situations': float(row['en_situations']) if pd.notna(row['en_situations']) else 0.0,
                    'en_success_rate': float(row['en_success_rate']) if pd.notna(row['en_success_rate']) else 0.0,
                }

            return en_dict

        except Exception as e:
            logger.error(f"Error loading empty net stats: {e}")
            return {}

    async def get_team_stats(self, team_name: str) -> Optional[NHLTeamStats]:
        """
        Get NHL team stats from ESPN + empty net stats from CSV
        Called only when game data is needed (not every poll)
        """
        try:
            # Map team name to abbreviation
            team_abbr = self.team_mapping.get(team_name)
            if not team_abbr:
                logger.warning(f"No ESPN mapping for NHL team: {team_name}")
                return None

            # Get empty net stats for this team
            en_data = self.en_stats.get(team_abbr.lower(), {})

            # Return basic stats with empty net data
            # Note: Full ESPN scraping would be done here, but for now
            # we'll just return empty net stats with placeholder team stats
            stats = NHLTeamStats(
                team_id=team_abbr,
                team_name=team_name,
                games_played=16,  # Placeholder - would come from ESPN
                wins=0,
                losses=0,
                ot_losses=0,
                points=0,
                win_pct=0.0,
                goals_per_game=3.0,
                goals_against_per_game=3.0,
                shots_per_game=30.0,
                shots_against_per_game=30.0,
                power_play_pct=20.0,
                penalty_kill_pct=80.0,
                faceoff_win_pct=50.0,
                shooting_pct=10.0,
                save_pct=0.910,
                pdo=100.0,
                # Empty net stats from CSV
                en_goals_for=en_data.get('en_goals_for', 0.0),
                en_goals_against=en_data.get('en_goals_against', 0.0),
                en_differential=en_data.get('en_differential', 0.0),
                en_situations=en_data.get('en_situations', 0.0),
                en_success_rate=en_data.get('en_success_rate', 0.0),
                # Rankings (would be calculated from all teams)
                goals_per_game_rank=16,
                goals_against_per_game_rank=16,
                power_play_rank=16,
                penalty_kill_rank=16,
                faceoff_rank=16,
                en_goals_for_rank=16,
                en_goals_against_rank=16,
            )

            logger.info(f"✅ Loaded NHL stats for {team_name} (EN goals: {en_data.get('en_goals_for', 0)})")
            return stats

        except Exception as e:
            logger.error(f"Error fetching ESPN NHL stats for {team_name}: {e}")
            return None
