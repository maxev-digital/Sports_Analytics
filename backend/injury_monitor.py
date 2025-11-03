"""
Player Injury Monitor & Cascade Strategy
Monitors NBA/NFL injuries in real-time and identifies betting opportunities when star players go down
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
import requests
from enum import Enum

logger = logging.getLogger(__name__)

class InjuryStatus(Enum):
    """Injury status types"""
    OUT = "out"
    DOUBTFUL = "doubtful"
    QUESTIONABLE = "questionable"
    PROBABLE = "probable"
    DAY_TO_DAY = "day_to_day"

class PlayerImpact(Enum):
    """Player impact level on totals"""
    SUPERSTAR = "superstar"  # 10+ PPG impact (LeBron, Curry, Jokic)
    STAR = "star"            # 5-10 PPG impact
    STARTER = "starter"      # 2-5 PPG impact
    ROLE = "role"            # <2 PPG impact

@dataclass
class InjuryReport:
    """Injury report data"""
    player_id: str
    player_name: str
    team: str
    position: str
    status: InjuryStatus
    description: str
    ppg: float
    impact_rating: PlayerImpact
    expected_total_drop: float
    timestamp: datetime
    game_id: Optional[str] = None
    game_time: Optional[datetime] = None

@dataclass
class CascadeOpportunity:
    """Injury cascade betting opportunity"""
    injury_report: InjuryReport
    game_id: str
    home_team: str
    away_team: str
    pregame_total: float
    current_total: float
    total_drop: float
    expected_drop: float
    overreaction: float  # How much books overreacted (positive = value on Over)
    confidence: str  # HIGH, MEDIUM, LOW
    recommendation: str  # BET_OVER, BET_UNDER, NO_PLAY
    edge: float
    reasoning: str
    timestamp: datetime

class InjuryMonitor:
    """Monitors player injuries and identifies cascade betting opportunities"""

    def __init__(self, game_tracker=None, alert_storage=None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.espn.com/'
        })

        # Track injuries we've already alerted on
        self.alerted_injuries: Set[str] = set()

        # Player impact database (PPG and impact ratings)
        self.player_database: Dict[str, Dict] = {}

        # Active injury reports
        self.active_injuries: Dict[str, InjuryReport] = {}

        # Cascade opportunities found
        self.opportunities: List[CascadeOpportunity] = []

        # References to game tracker and alert storage
        self.game_tracker = game_tracker
        self.alert_storage = alert_storage

    async def start_monitoring(self, interval_seconds: int = 60):
        """Start monitoring injuries continuously"""
        logger.info("🏥 Starting injury monitor...")
        logger.info(f"📊 Checking for injuries every {interval_seconds} seconds")

        while True:
            try:
                await self.check_injuries()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in injury monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)

    async def check_injuries(self):
        """Check for new injuries across all leagues"""
        try:
            # Check NBA injuries
            nba_injuries = await self.fetch_nba_injuries()

            # Check NFL injuries (if needed)
            # nfl_injuries = await self.fetch_nfl_injuries()

            # Process new injuries
            for injury in nba_injuries:
                await self.process_injury(injury, game_tracker=self.game_tracker)

        except Exception as e:
            logger.error(f"Error checking injuries: {e}")

    async def fetch_nba_injuries(self) -> List[InjuryReport]:
        """Fetch NBA injuries from ESPN"""
        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            injuries = []
            teams = data.get('teams', [])

            for team_data in teams:
                team_info = team_data.get('team', {})
                team_name = team_info.get('displayName', 'Unknown')
                team_abbr = team_info.get('abbreviation', 'UNK')

                for athlete in team_data.get('athletes', []):
                    athlete_info = athlete.get('athlete', {})
                    player_name = athlete_info.get('displayName', 'Unknown')
                    player_id = athlete_info.get('id', '')
                    position = athlete_info.get('position', {}).get('abbreviation', 'N/A')

                    # Get injury details
                    injuries_list = athlete.get('injuries', [])
                    if not injuries_list:
                        continue

                    injury_data = injuries_list[0]
                    status_str = injury_data.get('status', 'UNKNOWN').lower()
                    description = injury_data.get('longComment', injury_data.get('shortComment', 'No details'))

                    # Map status
                    status = self._map_injury_status(status_str)

                    # Get player stats and impact
                    ppg = await self.get_player_ppg(player_id, player_name)
                    impact = self.calculate_player_impact(ppg, position)
                    expected_drop = self.calculate_expected_total_drop(ppg, impact, position)

                    injury_report = InjuryReport(
                        player_id=player_id,
                        player_name=player_name,
                        team=team_abbr,
                        position=position,
                        status=status,
                        description=description,
                        ppg=ppg,
                        impact_rating=impact,
                        expected_total_drop=expected_drop,
                        timestamp=datetime.now()
                    )

                    injuries.append(injury_report)

            logger.info(f"📋 Found {len(injuries)} NBA injuries")
            return injuries

        except Exception as e:
            logger.error(f"Error fetching NBA injuries: {e}")
            return []

    def _map_injury_status(self, status_str: str) -> InjuryStatus:
        """Map ESPN status string to InjuryStatus enum"""
        status_map = {
            'out': InjuryStatus.OUT,
            'doubtful': InjuryStatus.DOUBTFUL,
            'questionable': InjuryStatus.QUESTIONABLE,
            'probable': InjuryStatus.PROBABLE,
            'day to day': InjuryStatus.DAY_TO_DAY,
            'day-to-day': InjuryStatus.DAY_TO_DAY,
        }
        return status_map.get(status_str, InjuryStatus.DAY_TO_DAY)

    async def get_player_ppg(self, player_id: str, player_name: str) -> float:
        """Get player's PPG from ESPN or cache"""
        # Check cache first
        if player_id in self.player_database:
            return self.player_database[player_id].get('ppg', 0.0)

        try:
            # Fetch from ESPN API
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/athletes/{player_id}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                athlete = data.get('athlete', {})
                stats = athlete.get('statistics', {})

                # Try to find PPG in current season stats
                for stat_group in stats.get('splits', {}).get('categories', []):
                    for stat in stat_group.get('stats', []):
                        if stat.get('name') == 'avgPoints':
                            ppg = float(stat.get('value', 0))

                            # Cache it
                            self.player_database[player_id] = {
                                'name': player_name,
                                'ppg': ppg
                            }
                            return ppg

            # Default if not found
            return 0.0

        except Exception as e:
            logger.warning(f"Could not fetch PPG for {player_name}: {e}")
            return 0.0

    def calculate_player_impact(self, ppg: float, position: str) -> PlayerImpact:
        """Calculate player's impact level based on PPG"""
        if ppg >= 25.0:
            return PlayerImpact.SUPERSTAR
        elif ppg >= 15.0:
            return PlayerImpact.STAR
        elif ppg >= 8.0:
            return PlayerImpact.STARTER
        else:
            return PlayerImpact.ROLE

    def calculate_expected_total_drop(self, ppg: float, impact: PlayerImpact, position: str) -> float:
        """
        Calculate expected total drop when player is out

        Logic:
        - Losing a player doesn't just remove their PPG
        - Team efficiency drops, pace may slow, backup is worse
        - Multiplier effect: 1.5x for superstars, 1.3x for stars
        """
        if impact == PlayerImpact.SUPERSTAR:
            # LeBron/Curry/Jokic out: 1.5x effect
            return ppg * 1.5
        elif impact == PlayerImpact.STAR:
            # Good starter out: 1.3x effect
            return ppg * 1.3
        elif impact == PlayerImpact.STARTER:
            # Regular starter: 1.1x effect
            return ppg * 1.1
        else:
            # Role player: 0.8x (backup might be similar)
            return ppg * 0.8

    async def process_injury(self, injury: InjuryReport, game_tracker=None):
        """Process an injury report and check for betting opportunities"""
        # Create unique key
        injury_key = f"{injury.player_id}_{injury.status.value}"

        # Skip if we've already alerted on this
        if injury_key in self.alerted_injuries:
            return

        # Only process OUT injuries for now (most impactful)
        if injury.status != InjuryStatus.OUT:
            return

        # Only process high-impact players
        if injury.impact_rating == PlayerImpact.ROLE:
            return

        logger.info(f"🚨 NEW INJURY: {injury.player_name} ({injury.team}) - {injury.status.value.upper()}")
        logger.info(f"   Impact: {injury.impact_rating.value} | PPG: {injury.ppg} | Expected drop: {injury.expected_total_drop:.1f}")

        # Mark as alerted
        self.alerted_injuries.add(injury_key)
        self.active_injuries[injury.player_id] = injury

        # Find games with this team and analyze cascade opportunity
        await self.analyze_cascade_opportunity(injury, game_tracker)

    async def analyze_cascade_opportunity(self, injury: InjuryReport, game_tracker=None):
        """
        Analyze if there's a betting opportunity from the injury

        Strategy:
        1. Find the game with injured player's team
        2. Check pregame total vs current total
        3. Calculate if books overreacted or underreacted
        4. If overreaction > 2 points, signal BET OVER
        """
        logger.info(f"🎯 Analyzing cascade opportunity for {injury.player_name}...")
        logger.info(f"   Expected total drop: {injury.expected_total_drop:.1f} points")

        if not game_tracker:
            logger.warning(f"   ⚠️ No game tracker provided - cannot find game data")
            return

        # Find game with this team
        matching_games = []
        for game_id, game in game_tracker.games.items():
            if injury.team in [game.home_team, game.away_team]:
                matching_games.append(game)

        if not matching_games:
            logger.info(f"   ℹ️ No upcoming game found for {injury.team}")
            return

        # Analyze each game
        for game in matching_games:
            logger.info(f"   📊 Found game: {game.away_team} @ {game.home_team}")

            # Get current total from market data
            if not game.totals:
                logger.info(f"   ⚠️ No totals market data available")
                continue

            # Find best current over line
            current_total = None
            best_over_odds = None

            for book_key, market in game.totals.items():
                for outcome in market.outcomes:
                    if outcome.name == "Over" and outcome.point:
                        if current_total is None or outcome.point < current_total:
                            current_total = outcome.point
                            best_over_odds = outcome.price

            if current_total is None:
                logger.info(f"   ⚠️ No Over line found in market data")
                continue

            # For now, estimate pregame total as current_total + small adjustment
            # In production, you'd want to store historical totals when injury first detected
            # Assumption: If we just detected injury, current_total reflects the drop
            pregame_total = current_total + 2.0  # Rough estimate - books typically move 1-3 points

            logger.info(f"   📉 Estimated pregame total: {pregame_total:.1f}")
            logger.info(f"   📊 Current total: {current_total:.1f}")

            # Use the cascade strategy to analyze
            from strategies.injury_cascade_strategy import cascade_strategy

            analysis = cascade_strategy.analyze_injury_impact(
                game_id=game_id,
                injury_player=injury.player_name,
                injury_team=injury.team,
                injured_team_ppg=110.0,  # NBA average - could be made dynamic
                opponent=game.home_team if injury.team == game.away_team else game.away_team,
                pregame_total=pregame_total,
                current_total=current_total,
                player_ppg=injury.ppg,
                player_impact=injury.impact_rating.value,
                position=injury.position
            )

            if analysis:
                # Store opportunity
                opportunity = CascadeOpportunity(
                    injury_report=injury,
                    game_id=game_id,
                    home_team=game.home_team,
                    away_team=game.away_team,
                    pregame_total=pregame_total,
                    current_total=current_total,
                    total_drop=analysis.actual_drop,
                    expected_drop=analysis.expected_drop,
                    overreaction=analysis.overreaction,
                    confidence=analysis.confidence,
                    recommendation=analysis.recommendation,
                    edge=analysis.edge,
                    reasoning="\n".join(analysis.reasoning),
                    timestamp=datetime.now()
                )

                self.opportunities.append(opportunity)

                logger.info(f"   ✅ CASCADE OPPORTUNITY STORED!")
                logger.info(f"   📈 Edge: {analysis.edge:.1f}% | Confidence: {analysis.confidence}")

                # Store in alert system
                await self._send_cascade_alert(opportunity, best_over_odds)

    async def _send_cascade_alert(self, opportunity: CascadeOpportunity, odds: float):
        """Send cascade opportunity alert to storage system"""
        if not self.alert_storage:
            logger.warning("⚠️ No alert storage configured - skipping alert")
            return

        try:
            # Create alert in storage
            tracked_alert = self.alert_storage.create_alert(
                alert_type='injury_cascade',
                game_id=opportunity.game_id,
                sport='basketball_nba',
                home_team=opportunity.home_team,
                away_team=opportunity.away_team,
                commence_time=opportunity.timestamp.isoformat(),
                market_type='totals',
                recommended_side=f"Over {opportunity.current_total}",
                recommended_odds=odds,
                recommended_bookmaker='Multiple books',
                edge_percent=opportunity.edge,
                profit_potential=None,
                expires_at=None,
                strategy_details={
                    'injury_player': opportunity.injury_report.player_name,
                    'injury_team': opportunity.injury_report.team,
                    'player_ppg': opportunity.injury_report.ppg,
                    'expected_drop': opportunity.expected_drop,
                    'actual_drop': opportunity.total_drop,
                    'overreaction': opportunity.overreaction,
                    'confidence': opportunity.confidence,
                    'reasoning': opportunity.reasoning
                }
            )

            logger.info(f"   💾 Alert stored with ID: {tracked_alert.id}")

        except Exception as e:
            logger.error(f"Error sending cascade alert: {e}")

    def get_active_opportunities(self) -> List[CascadeOpportunity]:
        """Get all active cascade opportunities"""
        return self.opportunities

    def get_injury_summary(self) -> Dict:
        """Get summary of current injuries"""
        return {
            'total_injuries': len(self.active_injuries),
            'superstars_out': len([i for i in self.active_injuries.values() if i.impact_rating == PlayerImpact.SUPERSTAR]),
            'stars_out': len([i for i in self.active_injuries.values() if i.impact_rating == PlayerImpact.STAR]),
            'opportunities_found': len(self.opportunities),
            'injuries': [
                {
                    'player': i.player_name,
                    'team': i.team,
                    'ppg': i.ppg,
                    'expected_drop': i.expected_total_drop,
                    'status': i.status.value
                }
                for i in self.active_injuries.values()
                if i.impact_rating in [PlayerImpact.SUPERSTAR, PlayerImpact.STAR]
            ]
        }

# Global instance - will be initialized in main.py with dependencies
injury_monitor = None
