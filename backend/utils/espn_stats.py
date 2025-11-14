"""
ESPN Stats Fetcher for Live NCAAB Games
Calculates real-time possessions and pace from play-by-play data
"""
import requests
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def fetch_espn_game_stats(game_id: str = None, home_team: str = None, away_team: str = None) -> Optional[Dict]:
    """
    Fetch live game statistics from ESPN API

    Args:
        game_id: ESPN game ID (if known)
        home_team: Home team name (for fuzzy matching)
        away_team: Away team name (for fuzzy matching)

    Returns:
        Dict with possession data, pace, shooting stats
    """
    try:
        # If no game_id, search scoreboard
        if not game_id:
            scoreboard_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
            resp = requests.get(scoreboard_url, timeout=5)
            if resp.status_code != 200:
                return None

            data = resp.json()
            events = data.get('events', [])

            # Find matching game by team names
            for event in events:
                competitions = event.get('competitions', [])
                if not competitions:
                    continue

                comp = competitions[0]
                competitors = comp.get('competitors', [])
                if len(competitors) < 2:
                    continue

                home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                away = next((c for c in competitors if c.get('homeAway') == 'away'), None)

                if home and away:
                    home_name = home.get('team', {}).get('displayName', '')
                    away_name = away.get('team', {}).get('displayName', '')

                    # Fuzzy match
                    if (home_team and home_team.lower() in home_name.lower() and
                        away_team and away_team.lower() in away_name.lower()):
                        game_id = event.get('id')
                        break

        if not game_id:
            logger.warning(f"Could not find ESPN game for {away_team} @ {home_team}")
            return None

        # Fetch game summary
        summary_url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={game_id}"
        resp = requests.get(summary_url, timeout=5)
        if resp.status_code != 200:
            return None

        summary = resp.json()

        # Extract team statistics
        boxscore = summary.get('boxscore', {})
        teams = boxscore.get('teams', [])

        if len(teams) < 2:
            return None

        result = {
            'home': extract_team_stats(teams[1]),  # home is usually index 1
            'away': extract_team_stats(teams[0]),  # away is usually index 0
        }

        logger.info(f"✅ Fetched ESPN stats for game {game_id}")
        return result

    except Exception as e:
        logger.error(f"Error fetching ESPN stats: {e}")
        return None


def extract_team_stats(team_data: Dict) -> Dict:
    """Extract relevant stats from ESPN team data"""
    stats = {}

    statistics = team_data.get('statistics', [])

    for stat in statistics:
        name = stat.get('name')
        value = stat.get('displayValue', '0')

        # Convert to float, handle percentages
        try:
            if '%' in str(value):
                value = float(value.replace('%', '')) / 100.0
            else:
                value = float(value)
        except:
            value = 0.0

        stats[name] = value

    return stats


def calculate_live_possessions(
    fga: float,
    fta: float,
    turnovers: float
) -> float:
    """
    Calculate possessions using standard formula
    Possessions = FGA + (0.5 × FTA) + TO
    """
    return fga + (0.5 * fta) + turnovers


def calculate_live_pace(
    total_possessions: float,
    minutes_elapsed: float
) -> float:
    """
    Calculate pace (possessions per 40 minutes)
    """
    if minutes_elapsed <= 0:
        return 70.0  # Default NCAAB pace

    return (total_possessions / minutes_elapsed) * 40.0


def analyze_live_game_factors(
    espn_stats: Dict,
    season_stats: Dict,
    minutes_elapsed: float
) -> Dict:
    """
    Analyze live game vs season baselines
    Returns pace factor, shooting factors, and projection weights

    Args:
        espn_stats: {home: {...}, away: {...}} from ESPN
        season_stats: {home: {pace, fg_pct, ...}, away: {...}} from KenPom
        minutes_elapsed: Minutes played so far

    Returns:
        Dict with analysis factors
    """
    # Extract ESPN stats (cumulative for game)
    home_stats = espn_stats.get('home', {})
    away_stats = espn_stats.get('away', {})

    # Get FGA, FTA, TO from ESPN
    home_fga = home_stats.get('fieldGoalsAttempted', 0)
    away_fga = away_stats.get('fieldGoalsAttempted', 0)

    home_fta = home_stats.get('freeThrowsAttempted', 0)
    away_fta = away_stats.get('freeThrowsAttempted', 0)

    home_to = home_stats.get('avgTotalTurnovers', 0)
    away_to = away_stats.get('avgTotalTurnovers', 0)

    # Calculate live possessions
    home_poss = calculate_live_possessions(home_fga, home_fta, home_to)
    away_poss = calculate_live_possessions(away_fga, away_fta, away_to)
    total_poss = (home_poss + away_poss) / 2.0

    # Calculate live pace
    live_pace = calculate_live_pace(total_poss, minutes_elapsed)

    # Get season pace from KenPom
    season_pace_home = season_stats.get('home', {}).get('pace', 70.0)
    season_pace_away = season_stats.get('away', {}).get('pace', 70.0)
    season_pace_avg = (season_pace_home + season_pace_away) / 2.0

    # Pace factor
    pace_factor = live_pace / season_pace_avg if season_pace_avg > 0 else 1.0

    # Shooting efficiency analysis
    home_fg_pct = home_stats.get('fieldGoalPct', 0)
    away_fg_pct = away_stats.get('fieldGoalPct', 0)
    live_fg_pct = (home_fg_pct + away_fg_pct) / 2.0

    # Estimate season FG% from efficiency (rough approximation)
    season_fg_pct = 0.45  # NCAAB average

    shooting_diff = live_fg_pct - season_fg_pct

    # Determine projection strategy
    projection_weight = calculate_projection_weight(
        pace_factor,
        shooting_diff,
        minutes_elapsed
    )

    return {
        'live_pace': live_pace,
        'season_pace': season_pace_avg,
        'pace_factor': pace_factor,
        'live_fg_pct': live_fg_pct,
        'shooting_diff': shooting_diff,
        'projection_weight': projection_weight,
        'total_possessions': total_poss,
        'minutes_elapsed': minutes_elapsed,
        'explanation': generate_explanation(pace_factor, shooting_diff, projection_weight)
    }


def calculate_projection_weight(
    pace_factor: float,
    shooting_diff: float,
    minutes_elapsed: float
) -> float:
    """
    Calculate how much to trust current game pace vs season average

    Returns: 0.0 to 1.0 (1.0 = fully trust current pace)
    """
    # More data = more trust
    data_confidence = min(minutes_elapsed / 30.0, 1.0)  # Full confidence at 30 mins

    # Analyze game state
    if pace_factor > 1.3:
        # Extreme pace (fouling/fast game) - trust it
        pace_trust = 0.9
    elif pace_factor > 1.15:
        # Moderately fast - likely sustainable
        pace_trust = 0.75
    elif pace_factor < 0.85:
        # Slow grind - likely sustainable
        pace_trust = 0.75
    else:
        # Near season average - trust season data more
        pace_trust = 0.5

    # Adjust for shooting variance
    if abs(shooting_diff) > 0.10:
        # Extreme shooting (hot/cold) - expect regression
        pace_trust *= 0.7
    elif abs(shooting_diff) > 0.05:
        # Moderate shooting variance
        pace_trust *= 0.85

    # Combine factors
    final_weight = pace_trust * data_confidence

    return min(max(final_weight, 0.2), 0.95)  # Clamp between 20% and 95%


def generate_explanation(pace_factor: float, shooting_diff: float, weight: float) -> str:
    """Generate human-readable explanation of projection logic"""
    pace_desc = "Fast pace" if pace_factor > 1.1 else "Slow pace" if pace_factor < 0.9 else "Normal pace"
    shoot_desc = "Hot shooting" if shooting_diff > 0.05 else "Cold shooting" if shooting_diff < -0.05 else "Normal shooting"
    trust_desc = "High trust" if weight > 0.7 else "Moderate trust" if weight > 0.4 else "Low trust"

    return f"{pace_desc} ({pace_factor:.2f}x), {shoot_desc} ({shooting_diff:+.1%}), {trust_desc} in current pace ({weight:.0%})"
