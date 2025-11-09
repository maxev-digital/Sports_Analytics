"""
QUICK START: Show Advanced Tab NOW with existing pace-based predictor

This uses your existing NCAABTotalsPredictor to populate the Advanced tab
while the XGBoost model is being developed.
"""

import sys
sys.path.append('C:/Users/nashr/backend')

from models.ncaab.totals_predictor import NCAABTotalsPredictor
import numpy as np


class QuickStartAnalytics:
    """Generate analytics for frontend using existing pace predictor"""

    def __init__(self, kenpom_data):
        self.predictor = NCAABTotalsPredictor(kenpom_data)
        self.std_dev_estimate = 10.0  # Typical NCAAB std dev

    def _clean_team_name(self, team_name):
        """Strip mascot names from team names (e.g. 'Duke Blue Devils' -> 'Duke')"""
        # Common mascots to remove
        mascots = [
            'Blue Devils', 'Tar Heels', 'Wildcats', 'Tigers', 'Bulldogs', 'Eagles',
            'Cardinals', 'Cavaliers', 'Demon Deacons', 'Yellow Jackets', 'Seminoles',
            'Hurricanes', 'Wolfpack', 'Panthers', 'Fighting Irish', 'Trojans', 'Bears',
            'Bruins', 'Ducks', 'Huskies', 'Cougars', 'Sun Devils', 'Utes', 'Buffaloes',
            'Beavers', 'Golden Bears', 'Cardinal', 'Crimson Tide', 'War Eagles', 'Aggies',
            'Volunteers', 'Gators', 'Gamecocks', 'Razorbacks', 'Rebels', 'Commodores',
            'Red Raiders', 'Longhorns', 'Sooners', 'Jayhawks', 'Cyclones', 'Mountaineers',
            'Terrapins', 'Spartans', 'Badgers', 'Cornhuskers', 'Hawkeyes', 'Boilermakers',
            'Hoosiers', 'Golden Gophers', 'Lions', 'Buckeyes', 'Nittany Lions', 'Scarlet Knights',
            'Roadrunners', 'Miners', 'Owls', 'Mean Green', 'Golden Hurricane', 'Mustangs',
            'Horned Frogs', 'Bearcats', 'Cougars', 'Knights', 'Bulls', 'Rams', 'Broncos',
            'Aztecs', 'Lobos', 'Rebels', 'Rainbow Warriors', 'Pilots', 'Zags', 'Gaels',
            'Dons', 'Waves', 'Anteaters', 'Highlanders', 'Tritons', 'Aggies', 'Titans',
            'Matadors', '49ers', 'Gauchos', 'Phoenix', 'Raiders', 'Mastodons', 'Penguins',
            'Vikings', 'Flames', 'Bison', 'Grizzlies', 'Bobcats', 'Golden Eagles', 'Retrievers',
            'Seawolves', 'River Hawks', 'Greyhounds', 'Terriers', 'Huskies', 'Catamounts',
            'Stags', 'Peacocks', 'Jaspers', 'Explorers', 'Minutemen', 'Flyers', 'Billikens',
            'Musketeers', 'Blue Jays', 'Hoyas', 'Friars', 'Pirates', 'Red Storm', 'Warriors',
            'Colonials', 'Dukes', 'Dragons', 'Spiders', 'Monarchs', 'Tribe', 'Pride', 'Hornets',
            'Lumberjacks', 'Red Wolves', 'Black Bears', 'Golden Panthers', 'Hatters'
        ]

        # Try removing full mascot names first
        for mascot in mascots:
            if team_name.endswith(mascot):
                cleaned = team_name[:-len(mascot)].strip()
                if cleaned:
                    return cleaned

        # If no mascot match, try removing last word (single-word mascot)
        parts = team_name.split()
        if len(parts) > 1:
            return ' '.join(parts[:-1])

        return team_name

    def generate_analytics(self, home_team, away_team, live_total, pregame_total=None):
        """
        Generate ncaab_analytics for a single game

        Returns dict ready for frontend or None if can't predict
        """
        # Clean team names (strip mascots)
        home_team_clean = self._clean_team_name(home_team)
        away_team_clean = self._clean_team_name(away_team)

        # Get prediction
        pred = self.predictor.predict_game(home_team_clean, away_team_clean)

        if not pred:
            return None

        model_total = pred['Model_Total']

        # Calculate deviation
        deviation = live_total - model_total
        z_score = deviation / self.std_dev_estimate
        edge_points = abs(deviation)

        # Direction
        direction = "UNDER" if deviation > 0 else "OVER"

        # Confidence based on edge
        if edge_points >= 5.0:
            confidence = 85
        elif edge_points >= 3.0:
            confidence = 70
        elif edge_points >= 1.5:
            confidence = 60
        else:
            confidence = 50

        # Simple Kelly (can be refined)
        kelly_pct = min(5.0, edge_points * 0.5)  # Conservative

        # Line movement
        line_movement = (live_total - pregame_total) if pregame_total else None

        return {
            # Top 5 Must-Have Metrics
            'direction': direction,
            'line': live_total,
            'z_score': round(z_score, 2),
            'edge_points': round(edge_points, 1),
            'model_prediction': model_total,
            'live_total': live_total,
            'kelly_percentage': round(kelly_pct, 1),
            'confidence': confidence,

            # Secondary Metrics
            'pregame_total': pregame_total,
            'line_movement': round(line_movement, 1) if line_movement else None,
            'standard_deviation': self.std_dev_estimate,
            'home_tempo': pred['Home_Tempo'],
            'away_tempo': pred['Away_Tempo'],
            'home_offensive_efficiency': pred['Home_OffEff'],
            'away_offensive_efficiency': pred['Away_OffEff'],
            'home_defensive_efficiency': None,  # Not in simple predictor
            'away_defensive_efficiency': None,
            'deviation_description': self._describe_deviation(abs(z_score)),
        }

    def _describe_deviation(self, abs_z_score):
        """Human-readable deviation description"""
        if abs_z_score >= 3.0:
            return "Very high deviation (3.0+ std devs)"
        elif abs_z_score >= 2.0:
            return "High deviation (2.0-3.0 std devs)"
        elif abs_z_score >= 1.0:
            return "Moderate deviation (1.0-2.0 std devs)"
        else:
            return "Low deviation (< 1.0 std dev)"


# Quick test with mock data
if __name__ == "__main__":
    import pandas as pd

    # Mock KenPom data for testing
    mock_kenpom = pd.DataFrame({
        'Team': ['Duke', 'North Carolina', 'Kansas', 'Kentucky'],
        'AdjTempo': [72.5, 70.2, 73.1, 71.5],
        'AdjOffEff': [118.2, 115.7, 120.1, 117.5],
        'AdjDefEff': [92.7, 93.6, 91.2, 94.1]
    })

    analyzer = QuickStartAnalytics(mock_kenpom)

    # Test prediction
    analytics = analyzer.generate_analytics(
        home_team='Duke',
        away_team='North Carolina',
        live_total=164.5,
        pregame_total=158.5
    )

    if analytics:
        print("✅ Frontend Analytics Generated:")
        import json
        print(json.dumps(analytics, indent=2))
        print("\n🟣 This will show the purple Advanced tab!")
    else:
        print("❌ Could not generate analytics (teams not found)")
