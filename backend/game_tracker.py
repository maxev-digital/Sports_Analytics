"""Game tracking and state management"""
from live_models import GameState, LiveGame, GameOdds, Team, GameProjection, TeamStats, NFLLiveStats, NFLTeamStats, NHLMomentumStats, NBAMomentumStats, NFLMomentumStats, NHLTeamStats, MLBTeamStats, WeatherInfo
from odds_client import OddsAPIClient
from projector import GameProjector
from momentum_calculator import MomentumCalculator
# DISABLED: NBA API causes timeouts - using ESPN only
# from nba_stats_client import NBAStatsClient
from nba_live_client import NBALiveClient
# from nba_momentum_client import NBAMomentumClient
from espn_nba_client import ESPNnbaClient  # ESPN NBA stats client (fallback only)
from scrapers.teamrankings_nba_scraper import TeamRankingsNBAScraper  # Primary NBA stats source
from config import POLL_INTERVAL, ENABLE_ESPN_STATS, QUIET_HOURS_ENABLED, QUIET_HOURS_START, QUIET_HOURS_END
# Conditionally import ESPN clients based on feature flag
if ENABLE_ESPN_STATS:
    from espn_nfl_client import ESPNNFLClient
    from nfl_stats_client import NFLStatsClient
    from nfl_momentum_client import NFLMomentumClient
    from nhl_stats_client import NHLStatsClient
    from mlb_stats_client import MLBStatsClient
    from espn_ncaab_client import ESPNNCAABClient
from nhl_goalie_pull_predictor import GoaliePullPredictor
from strategies.favorite_comeback_detector import FavoriteComebackDetector
from strategies.halftime_tracker import HalftimeTracker
from strategies.momentum_detector import MomentumDetector
from strategies.nba_quarter_reversal import QuarterReversalDetector
from ml.nba_regression_analyzer import NBARegressionAnalyzer
from ml.ncaab_regression_analyzer import NCAABRegressionAnalyzer
from typing import Dict, List, Optional
import asyncio
import logging
import time

logger = logging.getLogger(__name__)

class GameTracker:
    def __init__(self):
        self.odds_client = OddsAPIClient()  # The Odds API (works perfectly for NCAAB)
        self.projector = GameProjector()
        # DISABLED: NBA API causes timeouts
        # self.nba_stats_client = NBAStatsClient()
        self.nba_live_client = NBALiveClient()
        # self.nba_momentum_client = NBAMomentumClient()
        self.teamrankings_scraper = TeamRankingsNBAScraper()  # Primary NBA stats source (free, reliable)
        self.espn_nba_client = ESPNnbaClient()  # ESPN NBA stats client (fallback only)
        # Conditionally initialize ESPN clients based on feature flag
        if ENABLE_ESPN_STATS:
            self.espn_nfl_client = ESPNNFLClient()
            self.nfl_stats_client = NFLStatsClient()
            self.nfl_momentum_client = NFLMomentumClient()
            self.nhl_stats_client = NHLStatsClient()
            self.espn_ncaab_client = ESPNNCAABClient()
            self.mlb_stats_client = MLBStatsClient()
        else:
            self.espn_nfl_client = None
            self.nfl_stats_client = None
            self.nfl_momentum_client = None
            self.nhl_stats_client = None
            self.espn_ncaab_client = None
            self.mlb_stats_client = None
        self.games: Dict[str, LiveGame] = {}
        self.running = False
        self.team_stats_cache: Dict[str, TeamStats] = {}  # Cache NBA team stats
        self.nfl_team_stats_cache: Dict[str, NFLTeamStats] = {}  # Cache NFL team stats
        self.nhl_team_stats_cache: Dict[str, NHLTeamStats] = {}  # Cache NHL team stats
        self.mlb_team_stats_cache: Dict[str, MLBTeamStats] = {}  # Cache MLB team stats
        self.pregame_totals_cache: Dict[str, float] = {}  # Cache pregame totals per game_id
        self.espn_scoreboard_cache: Dict = {}  # Cache ESPN scoreboard data
        self.odds_timestamp_cache: Dict[str, Dict[str, float]] = {}  # Track when each book updates odds: {game_id: {bookmaker: timestamp}}
        self.goalie_pull_opportunities: List[Dict] = []  # Track goalie pull betting opportunities
        self.favorite_comeback_opportunities: List[Dict] = []  # Track NBA favorite comeback opportunities
        self.halftime_opportunities: List[Dict] = []  # Track NBA halftime betting opportunities
        self.momentum_opportunities: List[Dict] = []  # Track momentum surge opportunities (NHL & NBA)
        self.quarter_reversal_opportunities: List[Dict] = []  # Track NBA quarter reversal opportunities
        self.injury_props_opportunities: List[Dict] = []  # Track injury props opportunities
        self.favorite_comeback_detector = FavoriteComebackDetector()
        self.halftime_tracker = HalftimeTracker()
        self.momentum_detector = MomentumDetector()
        self.quarter_reversal_detector = QuarterReversalDetector()
        # Max EV Boost ML analyzers (lazy-loaded on first use)
        self.nba_regression_analyzer = None
        self.ncaab_regression_analyzer = None
        self.max_ev_boost_alerts: List[Dict] = []  # Track Max EV Boost regression alerts

    def _is_quiet_hours(self) -> bool:
        """Check if we're currently in quiet hours (no API calls)"""
        if not QUIET_HOURS_ENABLED:
            return False

        from datetime import datetime
        current_hour = datetime.now().hour

        # Handle overnight quiet hours (e.g., 11 PM - 9 AM)
        if QUIET_HOURS_START > QUIET_HOURS_END:
            return current_hour >= QUIET_HOURS_START or current_hour < QUIET_HOURS_END
        # Handle same-day quiet hours (e.g., 2 AM - 6 AM)
        else:
            return QUIET_HOURS_START <= current_hour < QUIET_HOURS_END

    def _get_nba_regression_analyzer(self):
        """Lazy-load NBA regression analyzer"""
        if self.nba_regression_analyzer is None:
            logger.info("Loading NBA Max EV Boost analyzer...")
            self.nba_regression_analyzer = NBARegressionAnalyzer()
        return self.nba_regression_analyzer

    def _get_ncaab_regression_analyzer(self):
        """Lazy-load NCAAB regression analyzer"""
        if self.ncaab_regression_analyzer is None:
            logger.info("Loading NCAAB Max EV Boost analyzer...")
            self.ncaab_regression_analyzer = NCAABRegressionAnalyzer()
        return self.ncaab_regression_analyzer

    def _analyze_max_ev_boost_opportunities(self):
        """Analyze games for Max EV Boost regression opportunities"""
        self.max_ev_boost_alerts.clear()

        for game_id, game in self.games.items():
            try:
                sport_key = game.state.sport_key

                # Only analyze NBA and NCAAB games
                if sport_key not in ['basketball_nba', 'basketball_ncaab']:
                    continue

                # Skip if no team stats available
                if not game.home_team_stats or not game.away_team_stats:
                    continue

                # Get current live total (average across books)
                if not game.odds or len(game.odds) == 0:
                    continue

                live_total = sum(book.total for book in game.odds) / len(game.odds)

                # Prepare game data for analyzer
                if sport_key == 'basketball_nba':
                    analyzer = self._get_nba_regression_analyzer()

                    # Convert team stats to analyzer format
                    game_data = {
                        'game_id': game_id,
                        'home_team': game.state.home_team.name,
                        'away_team': game.state.away_team.name,
                        'home_stats': {
                            'games_played': game.home_team_stats.games_played,
                            'wins': game.home_team_stats.wins,
                            'win_pct': game.home_team_stats.win_pct,
                            'ppg': game.home_team_stats.pts_per_game,
                            'opp_ppg': game.home_team_stats.pts_allowed,
                            'point_diff': game.home_team_stats.net_rating,
                            'fg_pct': game.home_team_stats.fg_pct,
                            'fg3_pct': game.home_team_stats.fg3_pct,
                            'ft_pct': game.home_team_stats.ft_pct,
                            'rebounds': 44.0,  # Default value
                            'assists': 25.0,  # Default value
                            'turnovers': 13.5,  # Default value
                            'steals': 7.5,  # Default value
                            'blocks': 5.0,  # Default value
                            'plus_minus': game.home_team_stats.net_rating,
                            'last_5_ppg': game.home_team_stats.last_5_avg_pts or game.home_team_stats.pts_per_game,
                            'last_10_ppg': game.home_team_stats.pts_per_game,
                            'last_5_wins': 3,  # Default value
                            'last_10_wins': 6,  # Default value
                            'momentum': 0.0  # Default value
                        },
                        'away_stats': {
                            'games_played': game.away_team_stats.games_played,
                            'wins': game.away_team_stats.wins,
                            'win_pct': game.away_team_stats.win_pct,
                            'ppg': game.away_team_stats.pts_per_game,
                            'opp_ppg': game.away_team_stats.pts_allowed,
                            'point_diff': game.away_team_stats.net_rating,
                            'fg_pct': game.away_team_stats.fg_pct,
                            'fg3_pct': game.away_team_stats.fg3_pct,
                            'ft_pct': game.away_team_stats.ft_pct,
                            'rebounds': 44.0,  # Default value
                            'assists': 25.0,  # Default value
                            'turnovers': 13.5,  # Default value
                            'steals': 7.5,  # Default value
                            'blocks': 5.0,  # Default value
                            'plus_minus': game.away_team_stats.net_rating,
                            'last_5_ppg': game.away_team_stats.last_5_avg_pts or game.away_team_stats.pts_per_game,
                            'last_10_ppg': game.away_team_stats.pts_per_game,
                            'last_5_wins': 3,  # Default value
                            'last_10_wins': 6,  # Default value
                            'momentum': 0.0  # Default value
                        },
                        'live_total': live_total
                    }

                elif sport_key == 'basketball_ncaab':
                    # NCAAB uses KenPom data - skip if not available
                    # This would need KenPom integration which isn't in TeamStats
                    continue

                # Run analysis
                result = analyzer.analyze_game(game_data)

                # Only create alert if it's a betting opportunity (2.0+ SD)
                if result.get('is_alert', False):
                    alert = {
                        'game_id': game_id,
                        'strategy': 'Max EV Boost',
                        'sport': 'NBA' if sport_key == 'basketball_nba' else 'NCAAB',
                        'matchup': f"{game_data['away_team']} @ {game_data['home_team']}",
                        'recommendation': result['recommended_bet'],
                        'confidence': result['confidence'],
                        'kelly_pct': result['kelly_pct'],
                        'z_score': result['z_score'],
                        'predicted_total': result['predicted_mean'],
                        'live_total': result['live_total'],
                        'edge_description': f"{result['confidence']} alert: Live total {result['live_total']} is {abs(result['z_score']):.1f} SD from predicted {result['predicted_mean']}"
                    }
                    self.max_ev_boost_alerts.append(alert)
                    logger.info(f"[MAX EV BOOST] {alert['matchup']}: {alert['recommendation']} @ {live_total} (Z={result['z_score']:.2f}, Confidence={result['confidence']})")

            except Exception as e:
                logger.error(f"Error analyzing Max EV Boost for game {game_id}: {e}")
                continue

    async def start(self):
        """Start tracking games"""
        self.running = True
        while self.running:
            try:
                # Skip API calls during quiet hours to save credits
                if self._is_quiet_hours():
                    logger.info(f"Quiet hours active ({QUIET_HOURS_START}:00 - {QUIET_HOURS_END}:00). Skipping API calls.")
                    await asyncio.sleep(60)  # Check every minute during quiet hours
                    continue

                await self.update_games()
                await asyncio.sleep(POLL_INTERVAL)  # Poll based on config
            except Exception as e:
                logger.error(f"Error in game tracker: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    def _map_nhl_team_name(self, team_name: str) -> Optional[str]:
        """Map NHL team name to API abbreviation"""
        team_map = {
            'Anaheim Ducks': 'ana',
            'Arizona Coyotes': 'ari',
            'Boston Bruins': 'bos',
            'Buffalo Sabres': 'buf',
            'Calgary Flames': 'cgy',
            'Carolina Hurricanes': 'car',
            'Chicago Blackhawks': 'chi',
            'Colorado Avalanche': 'col',
            'Columbus Blue Jackets': 'cbj',
            'Dallas Stars': 'dal',
            'Detroit Red Wings': 'det',
            'Edmonton Oilers': 'edm',
            'Florida Panthers': 'fla',
            'Los Angeles Kings': 'lak',
            'Minnesota Wild': 'min',
            'Montreal Canadiens': 'mtl',
            'Montréal Canadiens': 'mtl',
            'Nashville Predators': 'nsh',
            'New Jersey Devils': 'njd',
            'New York Islanders': 'nyi',
            'New York Rangers': 'nyr',
            'Ottawa Senators': 'ott',
            'Philadelphia Flyers': 'phi',
            'Pittsburgh Penguins': 'pit',
            'San Jose Sharks': 'sjs',
            'Seattle Kraken': 'sea',
            'St Louis Blues': 'stl',
            'St. Louis Blues': 'stl',
            'Tampa Bay Lightning': 'tbl',
            'Toronto Maple Leafs': 'tor',
            'Vancouver Canucks': 'van',
            'Vegas Golden Knights': 'vgk',
            'Washington Capitals': 'wsh',
            'Winnipeg Jets': 'wpg',
            'Utah Hockey Club': 'uta',
            # Sports Data IO abbreviations (uppercase) -> API abbreviations (lowercase)
            'ANA': 'ana', 'ARI': 'ari', 'BOS': 'bos', 'BUF': 'buf', 'CGY': 'cgy',
            'CAR': 'car', 'CHI': 'chi', 'COL': 'col', 'CBJ': 'cbj', 'DAL': 'dal',
            'DET': 'det', 'EDM': 'edm', 'FLA': 'fla', 'LA': 'lak', 'MIN': 'min',
            'MON': 'mtl', 'NAS': 'nsh', 'NJ': 'njd', 'NYI': 'nyi', 'NYR': 'nyr',
            'OTT': 'ott', 'PHI': 'phi', 'PIT': 'pit', 'SJ': 'sjs', 'SEA': 'sea',
            'STL': 'stl', 'TB': 'tbl', 'TOR': 'tor', 'VAN': 'van', 'VEG': 'vgk',
            'WAS': 'wsh', 'WSH': 'wsh', 'WPG': 'wpg', 'UTA': 'uta'
        }
        return team_map.get(team_name)

    def _map_mlb_team_name(self, team_name: str) -> Optional[str]:
        """Map MLB team name to ESPN API abbreviation"""
        team_map = {
            'Arizona Diamondbacks': 'ARI',
            'Atlanta Braves': 'ATL',
            'Baltimore Orioles': 'BAL',
            'Boston Red Sox': 'BOS',
            'Chicago Cubs': 'CHC',
            'Chicago White Sox': 'CHW',
            'Cincinnati Reds': 'CIN',
            'Cleveland Guardians': 'CLE',
            'Colorado Rockies': 'COL',
            'Detroit Tigers': 'DET',
            'Houston Astros': 'HOU',
            'Kansas City Royals': 'KC',
            'Los Angeles Angels': 'LAA',
            'Los Angeles Dodgers': 'LAD',
            'Miami Marlins': 'MIA',
            'Milwaukee Brewers': 'MIL',
            'Minnesota Twins': 'MIN',
            'New York Mets': 'NYM',
            'New York Yankees': 'NYY',
            'Oakland Athletics': 'OAK',
            'Philadelphia Phillies': 'PHI',
            'Pittsburgh Pirates': 'PIT',
            'San Diego Padres': 'SD',
            'San Francisco Giants': 'SF',
            'Seattle Mariners': 'SEA',
            'St Louis Cardinals': 'STL',
            'St. Louis Cardinals': 'STL',
            'Tampa Bay Rays': 'TB',
            'Texas Rangers': 'TEX',
            'Toronto Blue Jays': 'TOR',
            'Washington Nationals': 'WSH',
        }
        return team_map.get(team_name)

    def _map_nfl_team_name(self, team_name: str) -> Optional[str]:
        """Map NFL team name to ESPN API abbreviation"""
        team_map = {
            'Arizona Cardinals': 'ARI',
            'Atlanta Falcons': 'ATL',
            'Baltimore Ravens': 'BAL',
            'Buffalo Bills': 'BUF',
            'Carolina Panthers': 'CAR',
            'Chicago Bears': 'CHI',
            'Cincinnati Bengals': 'CIN',
            'Cleveland Browns': 'CLE',
            'Dallas Cowboys': 'DAL',
            'Denver Broncos': 'DEN',
            'Detroit Lions': 'DET',
            'Green Bay Packers': 'GB',
            'Houston Texans': 'HOU',
            'Indianapolis Colts': 'IND',
            'Jacksonville Jaguars': 'JAX',
            'Kansas City Chiefs': 'KC',
            'Las Vegas Raiders': 'LV',
            'Los Angeles Chargers': 'LAC',
            'Los Angeles Rams': 'LAR',
            'Miami Dolphins': 'MIA',
            'Minnesota Vikings': 'MIN',
            'New England Patriots': 'NE',
            'New Orleans Saints': 'NO',
            'New York Giants': 'NYG',
            'New York Jets': 'NYJ',
            'Philadelphia Eagles': 'PHI',
            'Pittsburgh Steelers': 'PIT',
            'San Francisco 49ers': 'SF',
            'Seattle Seahawks': 'SEA',
            'Tampa Bay Buccaneers': 'TB',
            'Tennessee Titans': 'TEN',
            'Washington Commanders': 'WSH',
            # Sports Data IO abbreviations (already uppercase) -> ESPN abbreviations
            'ARI': 'ARI', 'ATL': 'ATL', 'BAL': 'BAL', 'BUF': 'BUF', 'CAR': 'CAR',
            'CHI': 'CHI', 'CIN': 'CIN', 'CLE': 'CLE', 'DAL': 'DAL', 'DEN': 'DEN',
            'DET': 'DET', 'GB': 'GB', 'HOU': 'HOU', 'IND': 'IND', 'JAX': 'JAX',
            'KC': 'KC', 'LV': 'LV', 'LAC': 'LAC', 'LAR': 'LAR', 'MIA': 'MIA',
            'MIN': 'MIN', 'NE': 'NE', 'NO': 'NO', 'NYG': 'NYG', 'NYJ': 'NYJ',
            'PHI': 'PHI', 'PIT': 'PIT', 'SF': 'SF', 'SEA': 'SEA', 'TB': 'TB',
            'TEN': 'TEN', 'WAS': 'WSH', 'WSH': 'WSH'  # Sports Data IO uses WAS, ESPN uses WSH
        }
        return team_map.get(team_name)

    def _map_ncaaf_team_name(self, team_name: str) -> Optional[str]:
        """Map Odds API NCAAF team name to ESPN API full team name"""
        # Odds API often uses short names (e.g., "Alabama"), ESPN needs full names (e.g., "Alabama Crimson Tide")
        team_map = {
            # SEC
            'Alabama': 'Alabama Crimson Tide',
            'Arkansas': 'Arkansas Razorbacks',
            'Auburn': 'Auburn Tigers',
            'Florida': 'Florida Gators',
            'Georgia': 'Georgia Bulldogs',
            'Kentucky': 'Kentucky Wildcats',
            'LSU': 'LSU Tigers',
            'Ole Miss': 'Ole Miss Rebels',
            'Mississippi State': 'Mississippi State Bulldogs',
            'Missouri': 'Missouri Tigers',
            'South Carolina': 'South Carolina Gamecocks',
            'Tennessee': 'Tennessee Volunteers',
            'Texas A&M': 'Texas A&M Aggies',
            'Vanderbilt': 'Vanderbilt Commodores',
            'Texas': 'Texas Longhorns',
            'Oklahoma': 'Oklahoma Sooners',

            # Big Ten
            'Illinois': 'Illinois Fighting Illini',
            'Indiana': 'Indiana Hoosiers',
            'Iowa': 'Iowa Hawkeyes',
            'Maryland': 'Maryland Terrapins',
            'Michigan': 'Michigan Wolverines',
            'Michigan State': 'Michigan State Spartans',
            'Minnesota': 'Minnesota Golden Gophers',
            'Nebraska': 'Nebraska Cornhuskers',
            'Northwestern': 'Northwestern Wildcats',
            'Ohio State': 'Ohio State Buckeyes',
            'Penn State': 'Penn State Nittany Lions',
            'Purdue': 'Purdue Boilermakers',
            'Rutgers': 'Rutgers Scarlet Knights',
            'Wisconsin': 'Wisconsin Badgers',
            'UCLA': 'UCLA Bruins',
            'USC': 'USC Trojans',
            'Oregon': 'Oregon Ducks',
            'Washington': 'Washington Huskies',

            # Big 12
            'Baylor': 'Baylor Bears',
            'BYU': 'BYU Cougars',
            'Cincinnati': 'Cincinnati Bearcats',
            'Houston': 'Houston Cougars',
            'Iowa State': 'Iowa State Cyclones',
            'Kansas': 'Kansas Jayhawks',
            'Kansas State': 'Kansas State Wildcats',
            'Oklahoma State': 'Oklahoma State Cowboys',
            'TCU': 'TCU Horned Frogs',
            'Texas Tech': 'Texas Tech Red Raiders',
            'UCF': 'UCF Knights',
            'West Virginia': 'West Virginia Mountaineers',
            'Arizona': 'Arizona Wildcats',
            'Arizona State': 'Arizona State Sun Devils',
            'Colorado': 'Colorado Buffaloes',
            'Utah': 'Utah Utes',

            # ACC
            'Boston College': 'Boston College Eagles',
            'Clemson': 'Clemson Tigers',
            'Duke': 'Duke Blue Devils',
            'Florida State': 'Florida State Seminoles',
            'Georgia Tech': 'Georgia Tech Yellow Jackets',
            'Louisville': 'Louisville Cardinals',
            'Miami': 'Miami Hurricanes',
            'NC State': 'NC State Wolfpack',
            'North Carolina': 'North Carolina Tar Heels',
            'Pittsburgh': 'Pittsburgh Panthers',
            'Syracuse': 'Syracuse Orange',
            'Virginia': 'Virginia Cavaliers',
            'Virginia Tech': 'Virginia Tech Hokies',
            'Wake Forest': 'Wake Forest Demon Deacons',
            'California': 'California Golden Bears',
            'SMU': 'SMU Mustangs',
            'Stanford': 'Stanford Cardinal',

            # Notable Independents & Others
            'Notre Dame': 'Notre Dame Fighting Irish',
            'Army': 'Army Black Knights',
            'Navy': 'Navy Midshipmen',
        }

        # Try exact match first
        if team_name in team_map:
            return team_map[team_name]

        # If not found, try to match if the team_name is already in full format
        # (in case Odds API already returns full names)
        for full_name in team_map.values():
            if team_name == full_name:
                return team_name

        # Return as-is if no mapping found (will attempt to use it directly)
        logger.warning(f"No NCAAF team mapping found for: {team_name}, using as-is")
        return team_name

    async def _get_nfl_team_stats(self, team_name: str, is_ncaaf: bool = False) -> Optional[NFLTeamStats]:
        """Get NFL/NCAAF team stats with caching"""
        # Check if we have cached stats
        if team_name in self.nfl_team_stats_cache:
            return self.nfl_team_stats_cache[team_name]

        if is_ncaaf:
            # For NCAAF, map team name to ESPN's full name format
            mapped_team_name = self._map_ncaaf_team_name(team_name)
            if not mapped_team_name:
                logger.warning(f"Could not map NCAAF team name: {team_name}")
                return None

            try:
                # Fetch season stats from ESPN API using mapped name
                nfl_stats = await self.nfl_stats_client.get_team_season_stats(mapped_team_name, is_ncaaf=True)
                if not nfl_stats:
                    return None

                # Cache the stats (using original team name as key)
                self.nfl_team_stats_cache[team_name] = nfl_stats
                return nfl_stats

            except Exception as e:
                logger.warning(f"Error fetching NCAAF stats for {team_name} (mapped to {mapped_team_name}): {e}")
                return None
        else:
            # For NFL, map team name to abbreviation
            team_abbr = self._map_nfl_team_name(team_name)
            if not team_abbr:
                logger.warning(f"Could not map NFL team name: {team_name}")
                return None

            try:
                # Fetch season stats from ESPN API with rankings
                nfl_stats = await self.nfl_stats_client.get_team_stats_with_rankings(team_abbr, is_ncaaf=False)
                if not nfl_stats:
                    return None

                # Cache the stats
                self.nfl_team_stats_cache[team_name] = nfl_stats
                return nfl_stats

            except Exception as e:
                logger.warning(f"Error fetching NFL stats for {team_name}: {e}")
                return None

    async def _get_nhl_team_stats(self, team_name: str) -> Optional[NHLTeamStats]:
        """Get NHL team stats with caching"""
        # Check if we have cached stats
        if team_name in self.nhl_team_stats_cache:
            return self.nhl_team_stats_cache[team_name]

        # Map team name to abbreviation
        team_abbr = self._map_nhl_team_name(team_name)
        if not team_abbr:
            logger.warning(f"Could not map NHL team name: {team_name}")
            return None

        try:
            # Fetch season stats from NHL API with rankings
            nhl_stats = await self.nhl_stats_client.get_team_stats_with_rankings(team_abbr)
            if not nhl_stats:
                return None

            # Update the team_name to use the proper display name (not just abbreviation)
            nhl_stats.team_name = team_name

            # Cache the stats
            self.nhl_team_stats_cache[team_name] = nhl_stats
            return nhl_stats

        except Exception as e:
            logger.warning(f"Error fetching NHL stats for {team_name}: {e}")
            return None

    async def _get_mlb_team_stats(self, team_name: str) -> Optional[MLBTeamStats]:
        """Get MLB team stats with caching"""
        # Check if we have cached stats
        if team_name in self.mlb_team_stats_cache:
            return self.mlb_team_stats_cache[team_name]

        # Map team name to abbreviation
        team_abbr = self._map_mlb_team_name(team_name)
        if not team_abbr:
            logger.warning(f"Could not map MLB team name: {team_name}")
            return None

        try:
            # Fetch season stats from ESPN API with rankings
            mlb_stats = await self.mlb_stats_client.get_team_stats_with_rankings(team_abbr)
            if not mlb_stats:
                return None

            # Update the team_name to use the proper display name (not just abbreviation)
            mlb_stats.team_name = team_name

            # Cache the stats
            self.mlb_team_stats_cache[team_name] = mlb_stats
            return mlb_stats

        except Exception as e:
            logger.warning(f"Error fetching MLB stats for {team_name}: {e}")
            return None

    def _get_team_stats(self, team_name: str) -> Optional[TeamStats]:
        """Get NBA team stats from TeamRankings (PRIMARY) with ESPN fallback"""
        # Check cache first
        if team_name in self.team_stats_cache:
            return self.team_stats_cache[team_name]

        try:
            # PRIMARY: Try TeamRankings first (has real pace data)
            teamrankings_data = self.teamrankings_scraper.fetch_all_team_stats()

            # Normalize team name for better matching (handle LA vs Los Angeles)
            normalized_name = team_name.lower()
            if normalized_name.startswith('los angeles'):
                normalized_name_alt = normalized_name.replace('los angeles', 'la')
            elif normalized_name.startswith('la '):
                normalized_name_alt = normalized_name.replace('la ', 'los angeles ')
            else:
                normalized_name_alt = normalized_name

            # Try to find team in TeamRankings data
            tr_stats = None
            for team_key, stats in teamrankings_data.items():
                team_key_lower = team_key.lower()
                # Try both original and alternate names
                if (normalized_name in team_key_lower or team_key_lower in normalized_name or
                    normalized_name_alt in team_key_lower or team_key_lower in normalized_name_alt):
                    tr_stats = stats
                    break

            if tr_stats:
                # Use TeamRankings data (has REAL pace!)
                team_stats = TeamStats(
                    team_id=str(tr_stats.get('team_id', '')),
                    team_name=team_name,
                    games_played=int(tr_stats.get('games_played', 0)),
                    wins=int(tr_stats.get('wins', 0)),
                    losses=int(tr_stats.get('losses', 0)),
                    win_pct=float(tr_stats.get('win_pct', 0.0)),
                    off_rating=float(tr_stats.get('off_rating', 110.0)),
                    def_rating=float(tr_stats.get('def_rating', 110.0)),
                    net_rating=float(tr_stats.get('net_rating', 0.0)),
                    pace=float(tr_stats.get('pace', 100.0)),  # REAL pace from TeamRankings!
                    fg_pct=float(tr_stats.get('fg_pct', 45.0)),
                    fg3_pct=float(tr_stats.get('fg3_pct', 35.0)),
                    ft_pct=float(tr_stats.get('ft_pct', 75.0)),
                    pts_per_game=float(tr_stats.get('pts_per_game', 110.0)),
                    pts_allowed=float(tr_stats.get('pts_allowed', 110.0)),
                    last_5_record=tr_stats.get('last_5_record'),
                    last_5_avg_pts=float(tr_stats.get('pts_per_game', 110.0)),
                    last_5_avg_margin=float(tr_stats.get('point_diff', 0.0)),
                    form_trend=tr_stats.get('form_trend', 'NEUTRAL'),
                    pts_per_game_rank=tr_stats.get('pts_per_game_rank'),
                    off_rating_rank=tr_stats.get('off_rating_rank'),
                    def_rating_rank=tr_stats.get('def_rating_rank'),
                    net_rating_rank=tr_stats.get('net_rating_rank'),
                    pace_rank=tr_stats.get('pace_rank'),
                    fg_pct_rank=tr_stats.get('fg_pct_rank'),
                    fg3_pct_rank=tr_stats.get('fg3_pct_rank'),
                    ft_pct_rank=tr_stats.get('ft_pct_rank')
                )

                self.team_stats_cache[team_name] = team_stats
                logger.info(f"✅ Fetched TeamRankings NBA stats for {team_name}: {team_stats.pts_per_game} PPG, {team_stats.pace} pace")
                return team_stats

            # FALLBACK: Use ESPN if TeamRankings failed
            logger.warning(f"TeamRankings data not found for {team_name}, trying ESPN fallback")
            team_abbr = self._nba_team_name_to_abbr(team_name)
            if not team_abbr:
                logger.warning(f"Could not map NBA team name to abbreviation: {team_name}")
                return None

            espn_data = self.espn_nba_client.fetch_team_season_stats(team_abbr)
            if not espn_data:
                logger.warning(f"No ESPN stats available for {team_name} ({team_abbr})")
                return None

            season_stats = espn_data.get('season_stats', {})
            rankings = espn_data.get('rankings', {})
            games_played = int(season_stats.get('gamesplayed', 0))
            ppg = round(season_stats.get('avgpointsfor', 110.0), 1)
            opp_ppg = round(season_stats.get('avgpointsagainst', 110.0), 1)
            approx_off_rating = round(ppg * 100 / 100, 1)
            approx_def_rating = round(opp_ppg * 100 / 100, 1)

            team_stats = TeamStats(
                team_id=str(espn_data.get('team_id', '')),
                team_name=team_name,
                games_played=games_played,
                wins=espn_data.get('wins', 0),
                losses=espn_data.get('losses', 0),
                win_pct=espn_data.get('win_pct', 0.0),
                off_rating=approx_off_rating,
                def_rating=approx_def_rating,
                net_rating=round(approx_off_rating - approx_def_rating, 1),
                pace=100.0,  # ESPN fallback still uses 100.0
                fg_pct=round(season_stats.get('fieldgoalpct', 45.0) * 100, 1),
                fg3_pct=round(season_stats.get('threepoint​pct', 35.0) * 100, 1),
                ft_pct=round(season_stats.get('freethrowpct', 75.0) * 100, 1),
                pts_per_game=ppg,
                pts_allowed=opp_ppg,
                last_5_record=espn_data.get('last_5_record'),
                last_5_avg_pts=ppg,
                last_5_avg_margin=round(season_stats.get('differential', 0.0), 1),
                form_trend=espn_data.get('form_trend', 'NEUTRAL'),
                pts_per_game_rank=rankings.get('avgpointsfor_rank'),
                off_rating_rank=None,
                def_rating_rank=None,
                net_rating_rank=None,
                pace_rank=None,
                fg_pct_rank=rankings.get('fieldgoalpct_rank'),
                fg3_pct_rank=rankings.get('threepointpct_rank'),
                ft_pct_rank=rankings.get('freethrowpct_rank')
            )

            self.team_stats_cache[team_name] = team_stats
            logger.info(f"⚠️ Fetched ESPN NBA stats (fallback) for {team_name}: {team_stats.pts_per_game} PPG, {team_stats.pace} pace")
            return team_stats

        except Exception as e:
            logger.error(f"Error fetching NBA stats for {team_name}: {e}")
            return None

    def _nba_team_name_to_abbr(self, team_name: str) -> Optional[str]:
        """Convert NBA team name to ESPN abbreviation"""
        # Normalize team name for matching
        name_lower = team_name.lower()

        # ESPN abbreviation mapping (full team names)
        team_map = {
            'atlanta hawks': 'ATL', 'boston celtics': 'BOS', 'brooklyn nets': 'BKN',
            'charlotte hornets': 'CHA', 'chicago bulls': 'CHI', 'cleveland cavaliers': 'CLE',
            'dallas mavericks': 'DAL', 'denver nuggets': 'DEN', 'detroit pistons': 'DET',
            'golden state warriors': 'GSW', 'houston rockets': 'HOU', 'indiana pacers': 'IND',
            'la clippers': 'LAC', 'los angeles clippers': 'LAC', 'la lakers': 'LAL',
            'los angeles lakers': 'LAL', 'memphis grizzlies': 'MEM', 'miami heat': 'MIA',
            'milwaukee bucks': 'MIL', 'minnesota timberwolves': 'MIN', 'new orleans pelicans': 'NOP',
            'new york knicks': 'NYK', 'oklahoma city thunder': 'OKC', 'orlando magic': 'ORL',
            'philadelphia 76ers': 'PHI', 'phoenix suns': 'PHX', 'portland trail blazers': 'POR',
            'sacramento kings': 'SAC', 'san antonio spurs': 'SAS', 'toronto raptors': 'TOR',
            'utah jazz': 'UTA', 'washington wizards': 'WAS',
            # Sports Data IO abbreviation mappings (abbr -> ESPN abbr)
            'pho': 'PHX',  # Phoenix uses PHO in Sports Data IO but PHX in ESPN
            'uta': 'UTA', 'por': 'POR', 'sac': 'SAC', 'gsw': 'GSW', 'lac': 'LAC',
            'lal': 'LAL', 'den': 'DEN', 'min': 'MIN', 'okc': 'OKC', 'dal': 'DAL',
            'hou': 'HOU', 'mem': 'MEM', 'nor': 'NOP', 'nop': 'NOP', 'sa': 'SAS', 'sas': 'SAS',
            'atl': 'ATL', 'cha': 'CHA', 'mia': 'MIA', 'orl': 'ORL', 'was': 'WAS',
            'bkn': 'BKN', 'bos': 'BOS', 'ny': 'NYK', 'nyk': 'NYK', 'phi': 'PHI', 'tor': 'TOR',
            'chi': 'CHI', 'cle': 'CLE', 'det': 'DET', 'ind': 'IND', 'mil': 'MIL'
        }

        return team_map.get(name_lower)

    async def update_games(self):
        """Fetch and update all games"""
        logger.info("Updating games...")

        # Fetch odds and scores
        odds_data = await self.odds_client.get_live_games()
        scores_data = await self.odds_client.get_game_scores()

        # Fetch live NBA scoreboard for real-time quarter/time data (CONDITIONAL)
        from config import ENABLE_ESPN_STATS
        if ENABLE_ESPN_STATS:
            live_scoreboard = self.nba_live_client.fetch_live_scoreboard()
            # Fetch ESPN NFL scoreboard for real-time NFL data
            self.espn_scoreboard_cache = self.espn_nfl_client.fetch_scoreboard()
            # Fetch ESPN NCAAB scoreboard for real-time NCAAB data
            ncaab_scoreboard_cache = self.espn_ncaab_client.fetch_scoreboard()
            logger.info(f"Fetched live scoreboard with {len(live_scoreboard)} team entries")
            logger.info(f"Fetched ESPN NFL scoreboard with {len(self.espn_scoreboard_cache.get('events', []))} games")
            logger.info(f"Fetched ESPN NCAAB scoreboard with {len(ncaab_scoreboard_cache.get('events', []))} games")
        else:
            live_scoreboard = {}
            self.espn_scoreboard_cache = {'events': []}
            logger.info("⚠️ ESPN stats disabled - games will have odds only (no live scores/quarters)")

        logger.info(f"Fetched {len(odds_data)} games from odds API")
        logger.info(f"Scores data type: {type(scores_data)}, length: {len(scores_data) if scores_data else 0}")

        # FILTER: Process LIVE games (all sports) + UPCOMING games (NBA, NHL, NCAAF only)
        # This shows live action + allows users to prepare for upcoming games in key sports

        filtered_odds = []
        for game in odds_data:
            game_id = game['id']
            sport_key = game.get('sport_key', '')

            # Check if game is in scores data
            if game_id not in scores_data:
                continue

            score_info = scores_data[game_id]
            is_completed = score_info.get('completed') == True
            has_scores = score_info.get('scores') is not None

            # Skip completed games
            if is_completed:
                continue

            # Include live games (all sports)
            if has_scores:
                filtered_odds.append(game)
                continue

            # Include upcoming games for NBA, NHL, NCAAF, NCAAB, NFL, and MLB
            if sport_key in ['basketball_nba', 'icehockey_nhl', 'americanfootball_ncaaf', 'basketball_ncaab', 'americanfootball_nfl', 'baseball_mlb']:
                filtered_odds.append(game)
                logger.info(f"Including upcoming {sport_key} game: {game['away_team']} @ {game['home_team']}")

        logger.info(f"✓ Filtered to {len(filtered_odds)} games (live + upcoming NBA/NHL/NCAAF) out of {len(odds_data)} total")

        new_games = {}

        for game_data in filtered_odds:
            try:
                game_id = game_data['id']

                # Parse odds
                bookmakers = game_data.get('bookmakers', [])
                odds_list = []
                pregame_total = None
                home_spread = None
                away_spread = None
                home_spread_price = None
                away_spread_price = None
                home_ml = None
                away_ml = None

                # Parse all markets from all books
                for book in bookmakers:
                    book_data = {'bookmaker': book['title']}

                    # DEBUG: Log what markets are available
                    logger.info(f"Book {book['title']} has markets: {[m['key'] for m in book.get('markets', [])]}")

                    for market in book.get('markets', []):
                        if market['key'] == 'totals':
                            outcomes = market['outcomes']
                            # DEBUG: Log outcome names to debug NCAAB
                            if sport_key == 'basketball_ncaab':
                                logger.info(f"[NCAAB DEBUG] Book {book['title']} totals outcomes: {[o.get('name') for o in outcomes]}")
                            over_outcome = next((o for o in outcomes if o['name'] == 'Over'), None)
                            under_outcome = next((o for o in outcomes if o['name'] == 'Under'), None)
                            if over_outcome:
                                book_data['total'] = over_outcome['point']
                                book_data['over_price'] = over_outcome['price']
                                book_data['under_price'] = under_outcome['price'] if under_outcome else 0
                                # Use FanDuel as reference pregame total
                                if book['title'] == 'FanDuel':
                                    pregame_total = over_outcome['point']
                                elif pregame_total is None:
                                    pregame_total = over_outcome['point']

                        elif market['key'] == 'spreads':
                            outcomes = market['outcomes']
                            home_outcome = next((o for o in outcomes if o['name'] == game_data['home_team']), None)
                            away_outcome = next((o for o in outcomes if o['name'] == game_data['away_team']), None)
                            if home_outcome and away_outcome:
                                book_data['home_spread'] = home_outcome.get('point')
                                book_data['away_spread'] = away_outcome.get('point')
                                book_data['home_spread_price'] = home_outcome.get('price')
                                book_data['away_spread_price'] = away_outcome.get('price')
                                # Save first book's spread for game state
                                if home_spread is None:
                                    home_spread = home_outcome.get('point')
                                    away_spread = away_outcome.get('point')
                                    home_spread_price = home_outcome.get('price')
                                    away_spread_price = away_outcome.get('price')

                        elif market['key'] == 'h2h':
                            outcomes = market['outcomes']
                            home_outcome = next((o for o in outcomes if o['name'] == game_data['home_team']), None)
                            away_outcome = next((o for o in outcomes if o['name'] == game_data['away_team']), None)
                            if home_outcome and away_outcome:
                                book_data['home_ml'] = home_outcome.get('price')
                                book_data['away_ml'] = away_outcome.get('price')
                                # Save first book's ML for game state
                                if home_ml is None:
                                    home_ml = home_outcome.get('price')
                                    away_ml = away_outcome.get('price')

                    # Add book to odds_list if it has totals (required)
                    if 'total' in book_data:
                        # MOCK DATA: Add realistic spread/ML odds for demonstration
                        # This will be replaced with real data from The Odds API when available
                        import random
                        if 'home_spread' not in book_data:
                            # Generate realistic spread based on book (some books have better lines)
                            base_spread = random.choice([-7.5, -6.5, -5.5, -4.5, -3.5, -2.5, -1.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5])
                            spread_variance = random.choice([-0.5, 0, 0.5])  # Books have slightly different spreads
                            book_data['home_spread'] = base_spread + spread_variance
                            book_data['away_spread'] = -(base_spread + spread_variance)
                            book_data['home_spread_price'] = random.choice([-115, -110, -108, -105])
                            book_data['away_spread_price'] = random.choice([-115, -110, -108, -105])

                        if 'home_ml' not in book_data:
                            # Generate realistic money lines (correlated with spread)
                            if book_data.get('home_spread', 0) < -5:
                                # Heavy favorite
                                book_data['home_ml'] = random.randint(-350, -250)
                                book_data['away_ml'] = random.randint(200, 300)
                            elif book_data.get('home_spread', 0) < -2:
                                # Moderate favorite
                                book_data['home_ml'] = random.randint(-200, -150)
                                book_data['away_ml'] = random.randint(140, 180)
                            elif book_data.get('home_spread', 0) < 0:
                                # Slight favorite
                                book_data['home_ml'] = random.randint(-140, -105)
                                book_data['away_ml'] = random.randint(105, 130)
                            elif book_data.get('home_spread', 0) > 5:
                                # Heavy underdog
                                book_data['home_ml'] = random.randint(200, 300)
                                book_data['away_ml'] = random.randint(-350, -250)
                            elif book_data.get('home_spread', 0) > 2:
                                # Moderate underdog
                                book_data['home_ml'] = random.randint(140, 180)
                                book_data['away_ml'] = random.randint(-200, -150)
                            else:
                                # Close game/pick'em
                                book_data['home_ml'] = random.randint(-120, 120)
                                book_data['away_ml'] = random.randint(-120, 120)

                        # Add line movement data (placeholder - simulates movement from opening)
                        import random
                        if random.random() < 0.6:  # 60% of games show movement
                            movement = random.choice([-2.5, -2.0, -1.5, -1.0, -0.5, 0.5, 1.0, 1.5, 2.0, 2.5])
                            book_data["opening_total"] = book_data["total"] - movement
                            book_data["total_movement"] = movement
                        else:
                            book_data["opening_total"] = None
                            book_data["total_movement"] = None
                        odds_list.append(GameOdds(**book_data))

                # Show all sportsbooks (no filtering)
                # This allows us to track latency across all books

                # Calculate average pregame total from all books (better than using just one book)
                if odds_list:
                    current_avg_total = sum(o.total for o in odds_list) / len(odds_list)

                    # Use cached pregame total if available, otherwise store current average for upcoming games
                    if game_id in self.pregame_totals_cache:
                        pregame_total = self.pregame_totals_cache[game_id]
                    else:
                        pregame_total = current_avg_total

                    # Display average latency times for each sportsbook
                    # These represent typical speed differences between books

                    # Define average latency for different books (in seconds)
                    # These are consistent averages so users can compare book speeds
                    book_avg_latency = {
                        'DraftKings': 1,      # Very fast (avg 1s)
                        'FanDuel': 1.5,       # Very fast (avg 1.5s)
                        'BetMGM': 3,          # Fast (avg 3s)
                        'Caesars': 5,         # Medium-fast (avg 5s)
                        'BetRivers': 6,       # Medium (avg 6s)
                        'Bovada': 10,         # Medium-slow (avg 10s)
                        'BetOnline.ag': 14,   # Slower (avg 14s)
                        'MyBookie.ag': 17,    # Slow (avg 17s)
                        'BetUS': 21,          # Very slow (avg 21s)
                        'LowVig.ag': 25,      # Very slow (avg 25s)
                        'Fanatics': 4,        # Medium-fast (avg 4s)
                    }

                    # Assign consistent average latencies
                    for odd in odds_list:
                        if odd.bookmaker in book_avg_latency:
                            delay_seconds = book_avg_latency[odd.bookmaker]
                            odd.latency_ms = delay_seconds * 1000
                        else:
                            # Default for unknown books: medium latency (10s avg)
                            odd.latency_ms = 10 * 1000

                    # Find best over (highest total or best price at same total)
                    best_over = max(odds_list, key=lambda x: (x.total, -x.over_price))
                    # Find best under (lowest total or best price at same total)
                    best_under = min(odds_list, key=lambda x: (x.total, -x.under_price))

                    for odd in odds_list:
                        if odd.bookmaker == best_over.bookmaker and odd.total == best_over.total:
                            odd.is_best_over = True
                        if odd.bookmaker == best_under.bookmaker and odd.total == best_under.total:
                            odd.is_best_under = True

                    # Sort by total (best overs first, best unders last) for display
                    odds_list.sort(key=lambda x: x.total, reverse=True)

                if not odds_list or pregame_total is None:
                    logger.info(f"Skipping game {game_id}: odds_list={len(odds_list) if odds_list else 0}, pregame_total={pregame_total}")
                    continue

                logger.info(f"Processing game {game_id}: {game_data['away_team']} @ {game_data['home_team']}")

                # Parse game state (with better error handling)
                score_info = scores_data.get(game_id, {})
                scores = score_info.get('scores')  # Can be None, [], or list of scores

                home_score = None
                away_score = None
                if scores and isinstance(scores, list) and len(scores) >= 2:
                    # Scores array contains objects with 'name' and 'score' fields
                    # Match scores to teams by name (API home/away labels may be incorrect)
                    for score_entry in scores:
                        if score_entry and 'name' in score_entry:
                            team_name = score_entry['name']
                            score_value = score_entry.get('score')

                            # Match by team name
                            if team_name == game_data['home_team']:
                                home_score = score_value
                            elif team_name == game_data['away_team']:
                                away_score = score_value

                is_live = score_info.get('completed') == False and scores is not None and home_score is not None

                # Get real-time quarter and time data
                quarter = None
                time_remaining = None
                nfl_game_id = None
                from config import ENABLE_ESPN_STATS
                if is_live and ENABLE_ESPN_STATS:
                    # For NFL games, use ESPN API
                    if game_data.get('sport_key', '').startswith('americanfootball'):
                        espn_live_info = self.espn_nfl_client.get_live_game_info(
                            game_data['home_team'],
                            self.espn_scoreboard_cache
                        )
                        if espn_live_info and espn_live_info['is_live']:
                            quarter = espn_live_info['period']
                            time_remaining = espn_live_info['clock']
                            nfl_game_id = espn_live_info['game_id']
                            logger.info(f"ESPN NFL data: {game_data['home_team']} vs {game_data['away_team']} - Q{quarter} {time_remaining}")
                        else:
                            logger.warning(f"No ESPN NFL data for {game_data['home_team']} vs {game_data['away_team']}")
                    elif game_data.get('sport_key', '') == 'basketball_ncaab':
                        # For NCAAB games, use ESPN NCAAB client
                        ncaab_live_info = self.espn_ncaab_client.get_live_game_info(game_data['home_team'])
                        if not ncaab_live_info:
                            ncaab_live_info = self.espn_ncaab_client.get_live_game_info(game_data['away_team'])
                        
                        if ncaab_live_info and ncaab_live_info['is_live']:
                            quarter = ncaab_live_info['period']
                            time_remaining = ncaab_live_info['clock']
                            logger.info(f"ESPN NCAAB data: {game_data['home_team']} vs {game_data['away_team']} - Period {quarter} {time_remaining}")
                        else:
                            logger.warning(f"No ESPN NCAAB data for {game_data['home_team']} vs {game_data['away_team']}")
                    else:
                        # For NBA/other sports, use existing NBA client
                        live_info = self.nba_live_client.get_game_info(game_data['home_team'])
                        if not live_info:
                            live_info = self.nba_live_client.get_game_info(game_data['away_team'])

                        if live_info and live_info['is_live']:
                            quarter = live_info['period']
                            time_remaining = live_info['time_remaining']
                            logger.info(f"Live game data: {game_data['home_team']} vs {game_data['away_team']} - Q{quarter} {time_remaining}")

                # Calculate momentum for ALL LIVE games using MomentumCalculator
                home_momentum = None
                away_momentum = None
                if is_live and home_score is not None and away_score is not None:
                    # Convert scores to int (API may return them as strings)
                    home_score_int = int(home_score) if isinstance(home_score, str) else home_score
                    away_score_int = int(away_score) if isinstance(away_score, str) else away_score

                    # Calculate momentum using sport-specific algorithms
                    home_momentum, away_momentum = MomentumCalculator.calculate_momentum(
                        home_score=home_score_int,
                        away_score=away_score_int,
                        sport_key=game_data.get('sport_key', 'unknown'),
                        period=quarter,
                        time_remaining=time_remaining
                    )

                game_state = GameState(
                    id=game_id,
                    sport_key=game_data.get('sport_key', 'unknown'),
                    home_team=Team(
                        name=game_data['home_team'],
                        score=home_score,
                        spread=home_spread,
                        spread_price=home_spread_price,
                        money_line=home_ml,
                        momentum=home_momentum
                    ),
                    away_team=Team(
                        name=game_data['away_team'],
                        score=away_score,
                        spread=away_spread,
                        spread_price=away_spread_price,
                        money_line=away_ml,
                        momentum=away_momentum
                    ),
                    commence_time=game_data['commence_time'],
                    status='live' if is_live else 'upcoming',
                    quarter=quarter,
                    time_remaining=time_remaining
                )

                # Cache pregame total for upcoming games (will be used when game goes live)
                if game_state.status == 'upcoming' and game_id not in self.pregame_totals_cache:
                    self.pregame_totals_cache[game_id] = pregame_total
                    logger.info(f"Cached pregame total for {game_id}: {pregame_total}")

                # Get team stats (fetch early so projector can use them) - basketball only (NBA & NCAAB)
                home_stats = None
                away_stats = None
                if sport_key in ['basketball_nba', 'basketball_ncaab']:
                    home_stats = self._get_team_stats(game_state.home_team.name)
                    away_stats = self._get_team_stats(game_state.away_team.name)

                # Calculate projection
                if game_state.status == 'live' and game_state.quarter and game_state.time_remaining:
                    current_score = (game_state.home_team.score or 0) + (game_state.away_team.score or 0)
                    time_elapsed = self.projector.calculate_time_elapsed_seconds(
                        game_state.quarter,
                        game_state.time_remaining,
                        game_state.sport_key
                    )

                    projection = self.projector.project_final_total(
                        current_score,
                        time_elapsed,
                        pregame_total,
                        game_state.quarter,
                        home_stats,
                        away_stats
                    )

                    # Get current live total and calculate disparities
                    if odds_list:
                        avg_live_total = sum(o.total for o in odds_list) / len(odds_list)
                        projection.current_live_total = avg_live_total

                        # Calculate line movement from pregame
                        projection.line_movement = avg_live_total - pregame_total

                        # Find book with largest disparity from average
                        max_disparity = 0
                        best_book = None
                        for odd in odds_list:
                            disparity = abs(odd.total - avg_live_total)
                            if disparity > max_disparity:
                                max_disparity = disparity
                                best_book = odd.bookmaker

                        if best_book and max_disparity > 0:
                            projection.best_book_disparity = best_book
                            projection.best_disparity_amount = max_disparity

                        # Calculate edge
                        edge, recommendation = self.projector.calculate_edge(
                            projection.projected_final,
                            avg_live_total,
                            pregame_total
                        )
                        projection.edge = edge
                        projection.recommendation = recommendation

                        # Calculate strength factor and unit recommendation
                        if edge and recommendation:
                            minutes_played = time_elapsed / 60.0
                            strength_factor = self.projector.calculate_strength_factor(
                                edge,
                                projection.confidence,
                                projection.pace_differential,
                                projection.efficiency_factor,
                                minutes_played
                            )
                            projection.strength_factor = strength_factor

                            # Get best odds for the recommended side
                            if recommendation == "OVER":
                                best_odds = best_over.over_price
                            else:
                                best_odds = best_under.under_price

                            unit_recommendation = self.projector.calculate_unit_recommendation(
                                strength_factor,
                                best_odds
                            )
                            projection.unit_recommendation = unit_recommendation

                    # Calculate first half totals for NFL games in Q1 or Q2
                    if game_state.sport_key.startswith('americanfootball') and game_state.quarter and game_state.quarter <= 2:
                        # Simple first half projection: use pace to project
                        # NFL halves are 30 minutes, so use current pace to project end of half
                        HALF_TIME = 1800  # 30 minutes in seconds
                        if time_elapsed < HALF_TIME:
                            time_remaining_in_half = HALF_TIME - time_elapsed
                            if time_elapsed > 0:
                                current_pace_per_second = current_score / time_elapsed
                                projected_half_total = current_score + (current_pace_per_second * time_remaining_in_half)
                                projection.first_half_total = projected_half_total
                                projection.first_half_current = current_score
                else:
                    projection = GameProjection(
                        current_total=0,
                        projected_final=pregame_total,
                        pregame_total=pregame_total,
                        confidence="LOW"
                    )

                # Fetch NFL live stats and season stats if this is an NFL game
                home_nfl_live_stats = None
                away_nfl_live_stats = None
                home_nfl_stats = None
                away_nfl_stats = None

                if game_state.sport_key.startswith('americanfootball'):
                    # Determine if this is NFL or NCAAF
                    is_ncaaf = 'ncaaf' in game_state.sport_key.lower() or 'college' in game_state.sport_key.lower()
                    sport_label = 'NCAAF' if is_ncaaf else 'NFL'

                    # Fetch season stats (both for upcoming and live games)
                    print(f"[{sport_label} STATS] Fetching for {game_state.home_team.name} vs {game_state.away_team.name}")
                    logger.info(f"Fetching {sport_label} stats for {game_state.home_team.name} vs {game_state.away_team.name}")
                    home_nfl_stats = await self._get_nfl_team_stats(game_state.home_team.name, is_ncaaf=is_ncaaf)
                    away_nfl_stats = await self._get_nfl_team_stats(game_state.away_team.name, is_ncaaf=is_ncaaf)
                    print(f"[{sport_label} STATS] Fetched - Home: {home_nfl_stats is not None}, Away: {away_nfl_stats is not None}")
                    logger.info(f"{sport_label} stats fetched - Home: {home_nfl_stats is not None}, Away: {away_nfl_stats is not None}")

                    # Fetch live stats only for live games
                    if nfl_game_id and game_state.status == 'live':
                        try:
                            summary = self.espn_nfl_client.fetch_game_summary(nfl_game_id)
                            stats_by_team = self.espn_nfl_client.parse_game_stats(summary)

                            # Match stats to home/away teams
                            for team_name, stats in stats_by_team.items():
                                # Create NFLLiveStats object
                                nfl_live_stats = NFLLiveStats(
                                    first_downs=stats.get('firstDowns'),
                                    first_downs_passing=stats.get('firstDownsPassing'),
                                    first_downs_rushing=stats.get('firstDownsRushing'),
                                    first_downs_penalty=stats.get('firstDownsPenalty'),
                                    third_down_eff=stats.get('thirdDownEff'),
                                    fourth_down_eff=stats.get('fourthDownEff'),
                                    total_yards=stats.get('totalYards'),
                                    yards_per_play=stats.get('yardsPerPlay'),
                                    passing_yards=stats.get('passingYards'),
                                    comp_att=stats.get('completionAttempts'),
                                    yards_per_pass=stats.get('yardsPerPass'),
                                    interceptions_thrown=stats.get('interceptionThrown'),
                                    sacks_yards_lost=stats.get('sacksYardsLost'),
                                    rushing_yards=stats.get('rushingYards'),
                                    rushing_attempts=stats.get('rushingAttempts'),
                                    yards_per_rush=stats.get('yardsPerRushAttempt'),
                                    red_zone=stats.get('redZoneAttempts'),
                                    penalties=stats.get('penalties'),
                                    turnovers=stats.get('turnovers'),
                                    fumbles_lost=stats.get('fumblesLost'),
                                    defensive_td=stats.get('defensiveTouchdowns'),
                                    possession=stats.get('possessionTime'),
                                    total_plays=stats.get('totalPlays')
                                )

                                if game_state.home_team.name.lower() in team_name.lower() or team_name.lower() in game_state.home_team.name.lower():
                                    home_nfl_live_stats = nfl_live_stats
                                elif game_state.away_team.name.lower() in team_name.lower() or team_name.lower() in game_state.away_team.name.lower():
                                    away_nfl_live_stats = nfl_live_stats
                        except Exception as e:
                            logger.warning(f"Error fetching NFL live stats for game {nfl_game_id}: {e}")

                # Fetch NHL momentum stats and season stats if this is an NHL game
                home_nhl_momentum = None
                away_nhl_momentum = None
                home_nhl_stats = None
                away_nhl_stats = None

                if game_state.sport_key.startswith('icehockey'):
                    # Fetch NHL season stats
                    logger.info(f"Fetching NHL stats for {game_state.away_team.name} @ {game_state.home_team.name}")
                    home_nhl_stats = await self._get_nhl_team_stats(game_state.home_team.name)
                    away_nhl_stats = await self._get_nhl_team_stats(game_state.away_team.name)
                    logger.info(f"NHL stats fetched - Home: {home_nhl_stats is not None}, Away: {away_nhl_stats is not None}")

                    # Fetch live momentum stats only for live games
                    if False and game_state.status == 'live':
                        try:
                            # Get NHL game ID (format might need adjustment based on API)
                            # For now, use our game_id directly
                            live_stats = await self.nhl_stats_client.get_live_game_stats(game_id)

                            if live_stats and 'play_by_play' in live_stats:
                                # Use ENHANCED momentum calculation with PP/Penalties
                                momentum_data = self.nhl_stats_client.extract_enhanced_momentum_from_pbp(
                                    live_stats['play_by_play'],
                                    live_stats.get('boxscore', {})
                                )

                                # Create momentum stats for home team with new fields
                                home_data = momentum_data.get('home', {})
                                home_nhl_momentum = NHLMomentumStats(
                                    momentum_score=home_data.get('momentum_score', 50.0),
                                    recent_shots=home_data.get('recent_shots', 0),
                                    scoring_chances=home_data.get('scoring_chances', 0),
                                    faceoff_wins=home_data.get('faceoff_wins', 0),
                                    offensive_zone_events=home_data.get('offensive_zone_events', 0),
                                    possession_indicator="ATTACKING" if home_data.get('momentum_score', 50) > 60
                                                        else "DEFENDING" if home_data.get('momentum_score', 50) < 40
                                                        else "NEUTRAL",
                                    power_play_opps=home_data.get('power_play_opps', "0/0"),
                                    penalty_minutes=home_data.get('penalty_minutes', 0),
                                    blocked_shots=home_data.get('blocked_shots', 0)
                                )

                                # Create momentum stats for away team with new fields
                                away_data = momentum_data.get('away', {})
                                away_nhl_momentum = NHLMomentumStats(
                                    momentum_score=away_data.get('momentum_score', 50.0),
                                    recent_shots=away_data.get('recent_shots', 0),
                                    scoring_chances=away_data.get('scoring_chances', 0),
                                    faceoff_wins=away_data.get('faceoff_wins', 0),
                                    offensive_zone_events=away_data.get('offensive_zone_events', 0),
                                    possession_indicator="ATTACKING" if away_data.get('momentum_score', 50) > 60
                                                        else "DEFENDING" if away_data.get('momentum_score', 50) < 40
                                                        else "NEUTRAL",
                                    power_play_opps=away_data.get('power_play_opps', "0/0"),
                                    penalty_minutes=away_data.get('penalty_minutes', 0),
                                    blocked_shots=away_data.get('blocked_shots', 0)
                                )

                                logger.info(f"NHL momentum: {game_state.home_team.name} ({home_nhl_momentum.momentum_score}) vs {game_state.away_team.name} ({away_nhl_momentum.momentum_score}) | PP: {home_nhl_momentum.power_play_opps} vs {away_nhl_momentum.power_play_opps}")
                        except Exception as e:
                            logger.warning(f"Error fetching NHL momentum for game {game_id}: {e}")

                # Fetch NBA momentum stats for live games
                home_nba_momentum = None
                away_nba_momentum = None

                if game_state.sport_key.startswith('basketball_nba') and game_state.status == 'live':
                    try:
                        # DISABLED: NBA API causes timeouts
                        logger.info(f"NBA momentum disabled for game {game_id}")
                        momentum_data = None

                        # OLD CODE - DISABLED
                        # Get NBA game ID from the live client's scoreboard
                        # The game_id format needs to match NBA API format
                        # Try to extract NBA game ID from our game_id or scoreboard data

                        # For now, log and try with the existing game_id
                        # logger.info(f"Attempting to fetch NBA momentum for game {game_id}")

                        # momentum_data = self.nba_momentum_client.get_live_momentum(game_id)

                        if momentum_data:
                            # Create momentum stats for home team
                            home_data = momentum_data.get('home', {})
                            home_nba_momentum = NBAMomentumStats(
                                momentum_score=home_data.get('momentum_score', 50.0),
                                points_last_5min=home_data.get('points_last_5min', 0),
                                fg_pct_recent=home_data.get('fg_pct_recent', 0.0),
                                offensive_rebounds=home_data.get('offensive_rebounds', 0),
                                turnovers=home_data.get('turnovers', 0),
                                steals=home_data.get('steals', 0),
                                assists=home_data.get('assists', 0),
                                possession_indicator=home_data.get('possession_indicator', 'NEUTRAL')
                            )

                            # Create momentum stats for away team
                            away_data = momentum_data.get('away', {})
                            away_nba_momentum = NBAMomentumStats(
                                momentum_score=away_data.get('momentum_score', 50.0),
                                points_last_5min=away_data.get('points_last_5min', 0),
                                fg_pct_recent=away_data.get('fg_pct_recent', 0.0),
                                offensive_rebounds=away_data.get('offensive_rebounds', 0),
                                turnovers=away_data.get('turnovers', 0),
                                steals=away_data.get('steals', 0),
                                assists=away_data.get('assists', 0),
                                possession_indicator=away_data.get('possession_indicator', 'NEUTRAL')
                            )

                            logger.info(f"NBA momentum: {game_state.home_team.name} ({home_nba_momentum.momentum_score}) vs {game_state.away_team.name} ({away_nba_momentum.momentum_score}) | Recent scoring: {home_nba_momentum.points_last_5min}-{away_nba_momentum.points_last_5min}")
                    except Exception as e:
                        logger.warning(f"Error fetching NBA momentum for game {game_id}: {e}")

                # Fetch NFL/NCAAF momentum stats for live games
                home_nfl_momentum = None
                away_nfl_momentum = None
                home_ncaaf_momentum = None
                away_ncaaf_momentum = None

                is_nfl = game_state.sport_key.startswith('americanfootball_nfl')
                is_ncaaf = game_state.sport_key.startswith('americanfootball_ncaaf')

                if (is_nfl or is_ncaaf) and game_state.status == 'live':
                    try:
                        logger.info(f"Attempting to fetch {'NFL' if is_nfl else 'NCAAF'} momentum for game {game_id}")

                        momentum_data = self.nfl_momentum_client.get_live_momentum(game_id, is_college=is_ncaaf)

                        if momentum_data:
                            # Create momentum stats for home team
                            home_data = momentum_data.get('home', {})
                            momentum_stats_home = NFLMomentumStats(
                                momentum_score=home_data.get('momentum_score', 50.0),
                                yards_per_play=home_data.get('yards_per_play', 0.0),
                                recent_yards=home_data.get('recent_yards', 0),
                                recent_points=home_data.get('recent_points', 0),
                                touchdowns=home_data.get('touchdowns', 0),
                                field_goals=home_data.get('field_goals', 0),
                                turnovers=home_data.get('turnovers', 0),
                                red_zone_efficiency=home_data.get('red_zone_efficiency', '0/0'),
                                drive_state=home_data.get('drive_state', 'NEUTRAL')
                            )

                            # Create momentum stats for away team
                            away_data = momentum_data.get('away', {})
                            momentum_stats_away = NFLMomentumStats(
                                momentum_score=away_data.get('momentum_score', 50.0),
                                yards_per_play=away_data.get('yards_per_play', 0.0),
                                recent_yards=away_data.get('recent_yards', 0),
                                recent_points=away_data.get('recent_points', 0),
                                touchdowns=away_data.get('touchdowns', 0),
                                field_goals=away_data.get('field_goals', 0),
                                turnovers=away_data.get('turnovers', 0),
                                red_zone_efficiency=away_data.get('red_zone_efficiency', '0/0'),
                                drive_state=away_data.get('drive_state', 'NEUTRAL')
                            )

                            # Assign to correct sport
                            if is_nfl:
                                home_nfl_momentum = momentum_stats_home
                                away_nfl_momentum = momentum_stats_away
                            else:
                                home_ncaaf_momentum = momentum_stats_home
                                away_ncaaf_momentum = momentum_stats_away

                            logger.info(f"{'NFL' if is_nfl else 'NCAAF'} momentum: {game_state.home_team.name} ({momentum_stats_home.momentum_score}) vs {game_state.away_team.name} ({momentum_stats_away.momentum_score}) | Recent points: {momentum_stats_home.recent_points}-{momentum_stats_away.recent_points}")
                    except Exception as e:
                        logger.warning(f"Error fetching {'NFL' if is_nfl else 'NCAAF'} momentum for game {game_id}: {e}")

                # Fetch MLB team stats if this is an MLB game
                home_mlb_stats = None
                away_mlb_stats = None
                # Generate placeholder alternate market lines (1H/2H) for NBA/NHL/NFL
                alternate_lines = []
                if 'basketball_nba' in game_state.sport_key or 'icehockey_nhl' in game_state.sport_key or 'americanfootball_nfl' in game_state.sport_key:
                    # Get first few bookmakers for demo
                    sample_books = ['DraftKings', 'FanDuel', 'BetMGM', 'Caesars']

                    # Default totals if no odds available
                    if 'basketball_nba' in game_state.sport_key:
                        game_total = current_avg_total if odds_list else 220.0
                    elif 'icehockey_nhl' in game_state.sport_key:
                        game_total = current_avg_total if odds_list else 6.0
                    elif 'americanfootball_nfl' in game_state.sport_key:
                        game_total = current_avg_total if odds_list else 47.0
                    else:
                        game_total = current_avg_total if odds_list else 100.0

                    for bookmaker in sample_books:
                        # 1st Half lines (typically ~45-48% of game total)
                        half_total = game_total * 0.465
                        alternate_lines.append({
                            'market_type': '1H',
                            'bookmaker': bookmaker,
                            'total': round(half_total + random.uniform(-1, 1), 1),
                            'over_price': random.choice([-115, -110, -108, -105]),
                            'under_price': random.choice([-115, -110, -108, -105])
                        })

                        # 2nd Half lines (typically ~52-55% of game total)
                        half_total_2h = game_total * 0.535
                        alternate_lines.append({
                            'market_type': '2H',
                            'bookmaker': bookmaker,
                            'total': round(half_total_2h + random.uniform(-1, 1), 1),
                            'over_price': random.choice([-115, -110, -108, -105]),
                            'under_price': random.choice([-115, -110, -108, -105])
                        })
                

                if game_state.sport_key.startswith('baseball'):
                    # Fetch MLB season stats
                    logger.info(f"Fetching MLB stats for {game_state.away_team.name} @ {game_state.home_team.name}")
                    home_mlb_stats = await self._get_mlb_team_stats(game_state.home_team.name)
                    away_mlb_stats = await self._get_mlb_team_stats(game_state.away_team.name)
                    logger.info(f"MLB stats fetched - Home: {home_mlb_stats is not None}, Away: {away_mlb_stats is not None}")

                # Team stats already fetched earlier
                new_games[game_id] = LiveGame(
                    state=game_state,
                    odds=odds_list,
                    projection=projection,
                    home_team_stats=home_stats,
                    away_team_stats=away_stats,
                    home_nfl_live_stats=home_nfl_live_stats,
                    away_nfl_live_stats=away_nfl_live_stats,
                    home_nfl_stats=home_nfl_stats,
                    away_nfl_stats=away_nfl_stats,
                    home_nhl_momentum=home_nhl_momentum,
                    away_nhl_momentum=away_nhl_momentum,
                    home_nhl_stats=home_nhl_stats,
                    away_nhl_stats=away_nhl_stats,
                    home_nba_momentum=home_nba_momentum,
                    away_nba_momentum=away_nba_momentum,
                    home_nfl_momentum=home_nfl_momentum,
                    away_nfl_momentum=away_nfl_momentum,
                    home_ncaaf_momentum=home_ncaaf_momentum,
                    away_ncaaf_momentum=away_ncaaf_momentum,
                    home_mlb_stats=home_mlb_stats,
                    away_mlb_stats=away_mlb_stats,
                    player_props_count=63 if "basketball_nba" in game_state.sport_key else (100 if "icehockey_nhl" in game_state.sport_key else (95 if "americanfootball_nfl" in game_state.sport_key else 0)),
                    alternate_lines=alternate_lines,
                    # TV and Weather information
                    channel=game_data.get('channel'),
                    weather=WeatherInfo(
                        temp_high=game_data.get('forecast_temp_high'),
                        temp_low=game_data.get('forecast_temp_low'),
                        description=game_data.get('forecast_description'),
                        wind_chill=game_data.get('forecast_wind_chill'),
                        wind_speed=game_data.get('forecast_wind_speed'),
                    ) if (game_data.get('forecast_temp_high') or game_data.get('forecast_description')) else None
                )
            except Exception as e:
                logger.warning(f"Error parsing game {game_data.get('id', 'unknown')}: {e}", exc_info=True)
                continue

        self.games = new_games
        logger.info(f"Updated {len(self.games)} games")

        # Check for NHL goalie pull opportunities
        await self._check_goalie_pull_opportunities()
        await self._check_favorite_comeback_opportunities()
        await self._check_halftime_opportunities()
        await self._check_momentum_opportunities()
        await self._check_quarter_reversal_opportunities()

        # Run Max EV Boost regression analysis (NBA & NCAAB)
        self._analyze_max_ev_boost_opportunities()

    async def _check_goalie_pull_opportunities(self):
        """Check all live NHL games for goalie pull betting opportunities"""
        # Get all live NHL games
        live_nhl_games = []

        for game_id, live_game in self.games.items():
            if live_game.state.sport_key.startswith('icehockey') and live_game.state.status == 'live':
                # Convert to format expected by GoaliePullPredictor
                game_dict = {
                    'game_id': game_id,
                    'away_team': live_game.state.away_team.name,
                    'home_team': live_game.state.home_team.name,
                    'away_score': live_game.state.away_team.score or 0,
                    'home_score': live_game.state.home_team.score or 0,
                    'period': live_game.state.quarter or 0,
                    'time_remaining': live_game.state.time_remaining or '0:00',
                    'time_remaining_seconds': self._parse_time_to_seconds(live_game.state.time_remaining or '0:00'),
                    'current_score': (live_game.state.home_team.score or 0) + (live_game.state.away_team.score or 0)
                }

                live_nhl_games.append(game_dict)

        if not live_nhl_games:
            # No live NHL games, clear opportunities
            self.goalie_pull_opportunities = []
            return

        # Prepare odds data for each game
        odds_data = {}
        for game in live_nhl_games:
            game_id = game['game_id']
            live_game = self.games.get(game_id)

            if live_game and live_game.odds:
                # Get average total from all books
                avg_total = sum(odd.total for odd in live_game.odds) / len(live_game.odds)
                # Get best over odds
                best_over_odds = max(odd.over_price for odd in live_game.odds)

                odds_data[game_id] = {
                    'total': avg_total,
                    'over_odds': best_over_odds
                }

        # Check for opportunities
        opportunities = GoaliePullPredictor.check_for_opportunities(live_nhl_games, odds_data)

        # Update stored opportunities
        self.goalie_pull_opportunities = opportunities

        # Log any HIGH priority opportunities
        for opp in opportunities:
            if opp['priority'] == 'HIGH':
                logger.warning(f"🚨 HIGH PRIORITY GOALIE PULL OPPORTUNITY: {opp['game']}")
                logger.warning(opp['alert_message'])

    def _parse_time_to_seconds(self, time_str: str) -> int:
        """Parse time string like '2:30' to seconds"""
        try:
            parts = time_str.split(':')
            minutes = int(parts[0])
            seconds = int(parts[1])
            return (minutes * 60) + seconds
        except:
            return 0

    async def stop(self):
        """Stop tracking"""
        self.running = False
        await self.odds_client.close()

    def _attach_strategy_alerts_to_games(self):
        """Attach strategy alerts to their corresponding games"""
        # Create a mapping of game_id -> alerts
        alerts_by_game = {}

        # Add Quarter Reversal alerts
        for alert in self.quarter_reversal_opportunities:
            game_id = alert.get('game_id')
            if game_id:
                if game_id not in alerts_by_game:
                    alerts_by_game[game_id] = []
                # Format alert to match frontend interface
                formatted_alert = self._format_quarter_reversal_alert(alert)
                alerts_by_game[game_id].append(formatted_alert)

        # Add Max EV Boost alerts
        for alert in self.max_ev_boost_alerts:
            game_id = alert.get('game_id')
            if game_id:
                if game_id not in alerts_by_game:
                    alerts_by_game[game_id] = []
                alerts_by_game[game_id].append(alert)

        # Attach alerts to games
        for game_id, game in self.games.items():
            if game_id in alerts_by_game:
                # Convert LiveGame to dict, add alerts, create new LiveGame
                game_dict = game.dict()
                game_dict['strategy_alerts'] = alerts_by_game[game_id]
                # Update the game with alerts
                self.games[game_id] = LiveGame(**game_dict)

    def get_all_games(self) -> List[LiveGame]:
        """Get all tracked games with strategy alerts attached"""
        # Attach latest strategy alerts to games
        self._attach_strategy_alerts_to_games()
        return list(self.games.values())

    def get_game(self, game_id: str) -> LiveGame:
        """Get specific game"""
        return self.games.get(game_id)

    def get_goalie_pull_opportunities(self) -> List[Dict]:
        """Get current goalie pull betting opportunities"""
        return self.goalie_pull_opportunities

    async def _check_favorite_comeback_opportunities(self):
        """Check all live NBA games for favorite comeback opportunities"""
        opportunities = []

        # Filter for live NBA games only
        live_nba_games = [
            (game_id, game) for game_id, game in self.games.items()
            if game.state.sport_key == 'basketball_nba' and game.state.status == 'live'
        ]

        for game_id, live_game in live_nba_games:
            # Check if in valid period (Q1, Q2, Half)
            period = live_game.state.quarter or ''
            if period not in ['1Q', 'Q1', 'Q2', '2Q', 'Half', 'Halftime']:
                continue

            home_team = live_game.state.home_team.name
            away_team = live_game.state.away_team.name
            home_score = live_game.state.home_team.score or 0
            away_score = live_game.state.away_team.score or 0
            time_remaining = live_game.state.time_remaining or '0:00'

            # Determine favorite from pregame spread (negative spread = favorite)
            pregame_spread = None
            current_spread = None
            home_team_favorite = False

            if live_game.odds:
                # Get average pregame spread
                spreads = [odd.home_line for odd in live_game.odds if odd.home_line is not None]
                if spreads:
                    pregame_spread = sum(spreads) / len(spreads)
                    home_team_favorite = pregame_spread < 0
                    current_spread = spreads[0]  # Use first available spread

            if pregame_spread is None:
                continue  # Skip if no spread data

            # Get season stats from cache
            home_season_stats = {}
            away_season_stats = {}

            # Convert team names to cache keys
            home_cache_key = home_team
            away_cache_key = away_team

            if home_cache_key in self.team_stats_cache:
                home_stats = self.team_stats_cache[home_cache_key]
                home_season_stats = {
                    'ppg': home_stats.ppg,
                    'fg_pct': home_stats.fg_pct
                }

            if away_cache_key in self.team_stats_cache:
                away_stats = self.team_stats_cache[away_cache_key]
                away_season_stats = {
                    'ppg': away_stats.ppg,
                    'fg_pct': away_stats.fg_pct
                }

            # Analyze comeback opportunity
            result = self.favorite_comeback_detector.analyze_comeback_opportunity(
                game_id=game_id,
                sport='NBA',
                home_team=home_team,
                away_team=away_team,
                home_score=home_score,
                away_score=away_score,
                period=period,
                time_remaining=time_remaining,
                home_team_favorite=home_team_favorite,
                pregame_spread=pregame_spread,
                current_spread=current_spread,
                home_season_stats=home_season_stats,
                away_season_stats=away_season_stats,
                quarter_stats={}  # TODO: Add quarter shooting stats if available
            )

            if result.get('has_opportunity'):
                # Format for frontend
                for opp in result.get('opportunities', []):
                    opportunities.append({
                        **opp,
                        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
                    })

        # Update stored opportunities
        self.favorite_comeback_opportunities = opportunities

        # Log any HIGH confidence opportunities
        for opp in opportunities:
            if opp.get('confidence_level') == 'HIGH':
                logger.warning(f"🔥 HIGH CONFIDENCE COMEBACK: {opp['favorite']} trailing {opp['underdog']}")

    def get_favorite_comeback_opportunities(self) -> List[Dict]:
        """Get current NBA favorite comeback betting opportunities"""
        return self.favorite_comeback_opportunities

    async def _check_halftime_opportunities(self):
        """Check all NBA games at halftime for 2H betting opportunities"""
        opportunities = []

        # Filter for NBA games at halftime
        halftime_nba_games = [
            (game_id, game) for game_id, game in self.games.items()
            if game.state.sport_key == 'basketball_nba'
            and game.state.status == 'live'
            and game.state.time_remaining in ['Halftime', 'Half']
        ]

        for game_id, live_game in halftime_nba_games:
            home_team = live_game.state.home_team.name
            away_team = live_game.state.away_team.name
            home_score = live_game.state.home_team.score or 0
            away_score = live_game.state.away_team.score or 0
            time_remaining = live_game.state.time_remaining or ''

            # Get pregame spread and total
            pregame_spread = None
            pregame_total = None
            second_half_spread = None
            second_half_total = None

            if live_game.odds:
                spreads = [odd.home_line for odd in live_game.odds if odd.home_line is not None]
                totals = [odd.total for odd in live_game.odds if odd.total is not None]
                if spreads:
                    pregame_spread = sum(spreads) / len(spreads)
                if totals:
                    pregame_total = sum(totals) / len(totals)

                # In a real implementation, would fetch 2H lines from odds API
                # For now, estimate based on pregame lines
                second_half_spread = pregame_spread
                second_half_total = pregame_total / 2 if pregame_total else None

            # Get season stats from cache
            home_season_stats = {}
            away_season_stats = {}
            home_1h_stats = {}
            away_1h_stats = {}

            if home_team in self.team_stats_cache:
                home_stats = self.team_stats_cache[home_team]
                home_season_stats = {
                    'team': home_team,
                    'ppg': home_stats.ppg,
                    'fg_pct': home_stats.fg_pct
                }

            if away_team in self.team_stats_cache:
                away_stats = self.team_stats_cache[away_team]
                away_season_stats = {
                    'team': away_team,
                    'ppg': away_stats.ppg,
                    'fg_pct': away_stats.fg_pct
                }

            # Get rest days (simplified - would need actual schedule data)
            home_rest_days = 1
            away_rest_days = 1

            # Analyze halftime opportunity
            result = self.halftime_tracker.analyze_halftime_opportunity(
                game_id=game_id,
                sport='NBA',
                home_team=home_team,
                away_team=away_team,
                home_score_1h=home_score,
                away_score_1h=away_score,
                time_remaining=time_remaining,
                home_season_stats=home_season_stats,
                away_season_stats=away_season_stats,
                home_1h_stats=home_1h_stats,
                away_1h_stats=away_1h_stats,
                home_rest_days=home_rest_days,
                away_rest_days=away_rest_days,
                pregame_spread=pregame_spread,
                pregame_total=pregame_total,
                second_half_spread=second_half_spread,
                second_half_total=second_half_total
            )

            if result.get('has_opportunity'):
                # Format for frontend
                for opp in result.get('opportunities', []):
                    opportunities.append({
                        **opp,
                        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
                    })

        # Update stored opportunities
        self.halftime_opportunities = opportunities

        # Log any HIGH confidence opportunities
        for opp in opportunities:
            if opp.get('confidence_level') == 'HIGH':
                logger.warning(f"⏰ HIGH CONFIDENCE HALFTIME: {opp['home_team']} vs {opp['away_team']} - {opp['bet_type']}")

    def get_halftime_opportunities(self) -> List[Dict]:
        """Get current NBA halftime betting opportunities"""
        return self.halftime_opportunities

    async def _check_momentum_opportunities(self):
        """Check all live NHL and NBA games for momentum surge betting opportunities"""
        opportunities = []

        # Check NHL games
        nhl_games = [
            (game_id, game) for game_id, game in self.games.items()
            if game.state.sport_key == 'icehockey_nhl' and game.state.status == 'live'
        ]

        for game_id, live_game in nhl_games:
            try:
                # Extract game details
                home_team = live_game.state.home_team
                away_team = live_game.state.away_team
                home_score = live_game.state.home_score or 0
                away_score = live_game.state.away_score or 0
                period = live_game.state.period or "1st"
                time_remaining = live_game.state.time_remaining or "20:00"

                # Get momentum stats (from live_game.state if available)
                home_momentum = None
                away_momentum = None
                if hasattr(live_game.state, 'home_momentum') and live_game.state.home_momentum:
                    home_momentum = live_game.state.home_momentum.dict() if hasattr(live_game.state.home_momentum, 'dict') else live_game.state.home_momentum
                if hasattr(live_game.state, 'away_momentum') and live_game.state.away_momentum:
                    away_momentum = live_game.state.away_momentum.dict() if hasattr(live_game.state.away_momentum, 'dict') else live_game.state.away_momentum

                # Get season stats from cache
                home_season_stats = self.nhl_team_stats_cache.get(home_team)
                away_season_stats = self.nhl_team_stats_cache.get(away_team)

                # Analyze momentum
                result = self.momentum_detector.analyze_nhl_momentum(
                    game_id=game_id,
                    sport='icehockey_nhl',
                    home_team=home_team,
                    away_team=away_team,
                    home_score=home_score,
                    away_score=away_score,
                    period=period,
                    time_remaining=time_remaining,
                    home_momentum=home_momentum,
                    away_momentum=away_momentum,
                    home_season_stats=home_season_stats.dict() if home_season_stats else None,
                    away_season_stats=away_season_stats.dict() if away_season_stats else None,
                )

                if result.get('has_opportunity'):
                    opportunities.extend(result['opportunities'])

            except Exception as e:
                logger.error(f"Error analyzing NHL momentum for {game_id}: {e}", exc_info=True)

        # Check NBA games
        nba_games = [
            (game_id, game) for game_id, game in self.games.items()
            if game.state.sport_key == 'basketball_nba' and game.state.status == 'live'
        ]

        for game_id, live_game in nba_games:
            try:
                # Extract game details
                home_team = live_game.state.home_team
                away_team = live_game.state.away_team
                home_score = live_game.state.home_score or 0
                away_score = live_game.state.away_score or 0
                quarter = live_game.state.period or "1st"
                time_remaining = live_game.state.time_remaining or "12:00"

                # Get momentum stats (from live_game.state if available)
                home_momentum = None
                away_momentum = None
                if hasattr(live_game.state, 'home_momentum') and live_game.state.home_momentum:
                    home_momentum = live_game.state.home_momentum.dict() if hasattr(live_game.state.home_momentum, 'dict') else live_game.state.home_momentum
                if hasattr(live_game.state, 'away_momentum') and live_game.state.away_momentum:
                    away_momentum = live_game.state.away_momentum.dict() if hasattr(live_game.state.away_momentum, 'dict') else live_game.state.away_momentum

                # Get season stats from cache
                home_season_stats = self.team_stats_cache.get(home_team)
                away_season_stats = self.team_stats_cache.get(away_team)

                # Analyze momentum
                result = self.momentum_detector.analyze_nba_momentum(
                    game_id=game_id,
                    sport='basketball_nba',
                    home_team=home_team,
                    away_team=away_team,
                    home_score=home_score,
                    away_score=away_score,
                    quarter=quarter,
                    time_remaining=time_remaining,
                    home_momentum=home_momentum,
                    away_momentum=away_momentum,
                    home_season_stats=home_season_stats.dict() if home_season_stats else None,
                    away_season_stats=away_season_stats.dict() if away_season_stats else None,
                )

                if result.get('has_opportunity'):
                    opportunities.extend(result['opportunities'])

            except Exception as e:
                logger.error(f"Error analyzing NBA momentum for {game_id}: {e}", exc_info=True)

        # Update stored opportunities
        self.momentum_opportunities = opportunities

        # Log any HIGH confidence opportunities
        for opp in opportunities:
            if opp.get('confidence_level') == 'HIGH':
                logger.warning(f"🔥 HIGH CONFIDENCE MOMENTUM: {opp['momentum_team']} ({opp['sport']}) - Score {opp['momentum_score']}/100")

    def get_momentum_opportunities(self) -> List[Dict]:
        """Get current momentum surge betting opportunities"""
        return self.momentum_opportunities

    def _format_quarter_reversal_alert(self, alert: Dict) -> Dict:
        """
        Format Quarter Reversal alert to match StrategyAlert TypeScript interface

        Converts from Quarter Reversal detector format to frontend StrategyAlert format
        """
        # Map alert_level to confidence
        confidence_map = {
            'CRITICAL': 'CRITICAL',
            'HIGH': 'HIGH',
            'MEDIUM': 'MEDIUM',
            'LOW': 'LOW'
        }

        # Extract best recommendation for summary
        recommendations = alert.get('recommendations', [])
        best_bet = recommendations[0] if recommendations else None

        recommendation_text = alert.get('reversal_team', '') + f" {alert.get('quarter', '')} Win"
        if best_bet:
            recommendation_text = best_bet.get('label', recommendation_text)

        # Format bet options to match BetOption interface
        bet_options = []
        for rec in recommendations:
            bet_option = {
                'label': rec.get('label', ''),
                'market_type': rec.get('bet_type', 'moneyline'),  # 'moneyline', 'spread', 'totals'
                'bet_side': rec.get('side', 'HOME'),
                'line': rec.get('line'),
                'odds': rec.get('odds_american', -110),
                'bookmaker': rec.get('bookmaker', 'draftkings'),
                'bookmaker_title': rec.get('bookmaker', 'DraftKings').title(),
                'probability': rec.get('probability', alert.get('reversal_prob', 0.5)),
                'expected_value': rec.get('expected_value', 0.0),
                'kelly_size': rec.get('kelly_size')
            }
            bet_options.append(bet_option)

        # Calculate edge percentage from expected ROI
        edge_pct = alert.get('expected_roi', 0.0) * 100  # Convert 0.121 to 12.1%

        # Determine urgency based on quarter
        quarter = alert.get('quarter', '')
        urgency = 'HIGH' if quarter in ['Q3', 'Q4'] else 'CRITICAL' if quarter == 'OT' else 'MEDIUM'

        # Estimate expiration time (quarters last ~12 mins, give 3 mins to place bet)
        expires_in = 180  # 3 minutes in seconds

        return {
            'strategy_id': f"quarter_reversal_{alert.get('strategy', '')}",
            'strategy_name': 'NBA Quarter Reversal',
            'confidence': confidence_map.get(alert.get('alert_level', 'MEDIUM'), 'MEDIUM'),
            'trigger': alert.get('trigger', ''),
            'recommendation': recommendation_text,
            'edge_percentage': edge_pct,
            'expected_roi': alert.get('expected_roi', 0.0) * 100,  # Convert to percentage
            'win_probability': alert.get('reversal_prob', 0.5),
            'stake_recommendation': best_bet.get('kelly_size', 1.0) if best_bet else 1.0,
            'bet_options': bet_options,
            'reasoning': alert.get('reasoning', ''),
            'urgency': urgency,
            'expires_in': expires_in,
            'sound_alert': alert.get('alert_level') in ['HIGH', 'CRITICAL'],
            'timestamp': alert.get('timestamp', datetime.now().isoformat())
        }

    async def _check_quarter_reversal_opportunities(self):
        """Check all live NBA games for quarter reversal opportunities"""
        opportunities = []

        # Filter for live NBA games only
        live_nba_games = [
            (game_id, game) for game_id, game in self.games.items()
            if game.state.sport_key == 'basketball_nba' and game.state.status == 'live'
        ]

        for game_id, live_game in live_nba_games:
            try:
                # Get ESPN game ID from scoreboard lookup
                home_team = live_game.state.home_team.name
                away_team = live_game.state.away_team.name

                # Try to get game info from NBA live client's cache
                game_info = None
                if hasattr(self.nba_live_client, 'scoreboard_cache'):
                    game_info = self.nba_live_client.scoreboard_cache.get(home_team)
                    if not game_info:
                        game_info = self.nba_live_client.scoreboard_cache.get(away_team)

                if not game_info or not game_info.get('game_id'):
                    logger.warning(f"No ESPN game ID found for {away_team} @ {home_team}")
                    continue

                espn_game_id = game_info['game_id']

                # Fetch quarter scores from ESPN API
                quarter_scores = self.espn_nba_client.get_quarter_scores(espn_game_id)

                if not quarter_scores:
                    logger.info(f"No quarter scores available yet for game {game_id}")
                    continue

                # Prepare game data for quarter reversal detector
                game_data = {
                    'id': game_id,
                    'period': live_game.state.quarter or 1,
                    'home_team': {'name': home_team},
                    'away_team': {'name': away_team},
                    'quarters': quarter_scores,
                    'bookmakers': [],  # Will be populated from odds data
                    'home_team_stats': live_game.home_team_stats.dict() if live_game.home_team_stats else None,
                    'away_team_stats': live_game.away_team_stats.dict() if live_game.away_team_stats else None
                }

                # Add bookmaker data from odds
                if live_game.odds:
                    for odd in live_game.odds:
                        bookmaker_data = {
                            'name': odd.bookmaker,
                            'markets': []
                        }

                        # Add spreads if available
                        if odd.home_spread is not None:
                            bookmaker_data['markets'].append({
                                'key': 'spreads',
                                'outcomes': [
                                    {'name': home_team, 'point': odd.home_spread, 'price': odd.home_spread_price or -110},
                                    {'name': away_team, 'point': odd.away_spread, 'price': odd.away_spread_price or -110}
                                ]
                            })

                        # Add moneylines if available
                        if odd.home_ml is not None:
                            bookmaker_data['markets'].append({
                                'key': 'h2h',
                                'outcomes': [
                                    {'name': home_team, 'price': odd.home_ml},
                                    {'name': away_team, 'price': odd.away_ml}
                                ]
                            })

                        game_data['bookmakers'].append(bookmaker_data)

                # Analyze for quarter reversal opportunity
                alert = self.quarter_reversal_detector.analyze_game(
                    game_data,
                    bankroll=None,  # Could be fetched from user settings
                    risk_profile='balanced'
                )

                if alert:
                    opportunities.append(alert)
                    logger.info(f"🔄 QUARTER REVERSAL: {alert['matchup']} - {alert['trigger']} ({alert['alert_level']})")

            except Exception as e:
                logger.error(f"Error analyzing quarter reversal for game {game_id}: {e}", exc_info=True)

        # Update stored opportunities
        self.quarter_reversal_opportunities = opportunities

        # Log any HIGH/CRITICAL alerts
        for opp in opportunities:
            if opp.get('alert_level') in ['HIGH', 'CRITICAL']:
                logger.warning(f"🔥 {opp['alert_level']} QUARTER REVERSAL: {opp['matchup']} - {opp['trigger']}")

    def get_quarter_reversal_opportunities(self) -> List[Dict]:
        """Get current NBA quarter reversal betting opportunities"""
        return self.quarter_reversal_opportunities

    def get_injury_props_opportunities(self) -> List[Dict]:
        """Get current injury props betting opportunities"""
        return self.injury_props_opportunities
