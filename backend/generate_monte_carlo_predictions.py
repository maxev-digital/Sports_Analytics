"""
Generate pregame predictions using Monte Carlo simulation
Provides probability distributions, EV calculations, and Kelly sizing
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import random

# Add simulation directory to path
sys.path.insert(0, str(Path(__file__).parent / "simulation"))

from monte_carlo_totals import (
    PossessionMonteCarloSimulator,
    GameState,
    TeamStats
)

# Sport configurations
SPORT_CONFIG = {
    'NBA': {
        'quarter_time': '12:00',
        'quarters': 4,
        'default_pace': 100.0,
        'default_off_rating': 115.0,
        'default_def_rating': 112.0
    },
    'NCAAB': {
        'quarter_time': '20:00',  # Two 20-min halves
        'quarters': 2,
        'default_pace': 70.0,
        'default_off_rating': 105.0,
        'default_def_rating': 102.0
    },
    'NFL': {
        'quarter_time': '15:00',
        'quarters': 4,
        'default_pace': 65.0,  # Possessions per game
        'default_off_rating': 110.0,
        'default_def_rating': 108.0
    },
    'NCAAF': {
        'quarter_time': '15:00',
        'quarters': 4,
        'default_pace': 75.0,
        'default_off_rating': 112.0,
        'default_def_rating': 110.0
    },
    'NHL': {
        'quarter_time': '20:00',  # Periods
        'quarters': 3,
        'default_pace': 55.0,  # Shots per game
        'default_off_rating': 108.0,
        'default_def_rating': 105.0
    }
}

# Sample matchups for each sport with realistic team stats
sample_games = {
    'NBA': [
        {
            'away': 'Los Angeles Lakers',
            'home': 'Boston Celtics',
            'market_total': 228.5,
            'home_stats': {'pace': 98.5, 'off_rating': 118.2, 'def_rating': 110.5},
            'away_stats': {'pace': 101.2, 'off_rating': 116.8, 'def_rating': 112.3}
        },
        {
            'away': 'Golden State Warriors',
            'home': 'Phoenix Suns',
            'market_total': 225.5,
            'home_stats': {'pace': 102.1, 'off_rating': 117.5, 'def_rating': 111.8},
            'away_stats': {'pace': 99.8, 'off_rating': 115.2, 'def_rating': 109.4}
        },
        {
            'away': 'Miami Heat',
            'home': 'Milwaukee Bucks',
            'market_total': 221.0,
            'home_stats': {'pace': 97.5, 'off_rating': 119.1, 'def_rating': 108.9},
            'away_stats': {'pace': 96.3, 'off_rating': 113.4, 'def_rating': 111.2}
        },
        {
            'away': 'Dallas Mavericks',
            'home': 'Denver Nuggets',
            'market_total': 230.0,
            'home_stats': {'pace': 100.8, 'off_rating': 120.3, 'def_rating': 110.1},
            'away_stats': {'pace': 99.2, 'off_rating': 118.7, 'def_rating': 111.5}
        },
    ],
    'NCAAB': [
        {
            'away': 'Duke',
            'home': 'North Carolina',
            'market_total': 145.5,
            'home_stats': {'pace': 72.5, 'off_rating': 108.2, 'def_rating': 98.5},
            'away_stats': {'pace': 71.8, 'off_rating': 106.8, 'def_rating': 99.3}
        },
        {
            'away': 'Kansas',
            'home': 'Kentucky',
            'market_total': 152.0,
            'home_stats': {'pace': 69.5, 'off_rating': 110.5, 'def_rating': 96.8},
            'away_stats': {'pace': 68.3, 'off_rating': 109.2, 'def_rating': 97.4}
        },
        {
            'away': 'Gonzaga',
            'home': 'UCLA',
            'market_total': 148.5,
            'home_stats': {'pace': 73.1, 'off_rating': 107.5, 'def_rating': 99.8},
            'away_stats': {'pace': 70.8, 'off_rating': 111.2, 'def_rating': 98.4}
        },
        {
            'away': 'Villanova',
            'home': 'Georgetown',
            'market_total': 141.0,
            'home_stats': {'pace': 67.5, 'off_rating': 104.4, 'def_rating': 100.2},
            'away_stats': {'pace': 68.2, 'off_rating': 105.8, 'def_rating': 101.1}
        },
    ],
    'NFL': [
        {
            'away': 'Kansas City Chiefs',
            'home': 'Buffalo Bills',
            'market_total': 52.5,
            'home_stats': {'pace': 64.5, 'off_rating': 118.2, 'def_rating': 105.5},
            'away_stats': {'pace': 66.2, 'off_rating': 120.8, 'def_rating': 107.3}
        },
        {
            'away': 'Philadelphia Eagles',
            'home': 'Dallas Cowboys',
            'market_total': 48.5,
            'home_stats': {'pace': 62.1, 'off_rating': 112.5, 'def_rating': 108.8},
            'away_stats': {'pace': 63.8, 'off_rating': 115.2, 'def_rating': 106.4}
        },
        {
            'away': 'San Francisco 49ers',
            'home': 'Seattle Seahawks',
            'market_total': 45.0,
            'home_stats': {'pace': 61.5, 'off_rating': 110.1, 'def_rating': 109.9},
            'away_stats': {'pace': 60.3, 'off_rating': 108.4, 'def_rating': 111.2}
        },
    ],
    'NCAAF': [
        {
            'away': 'Alabama',
            'home': 'Georgia',
            'market_total': 56.5,
            'home_stats': {'pace': 74.5, 'off_rating': 115.2, 'def_rating': 95.5},
            'away_stats': {'pace': 76.2, 'off_rating': 118.8, 'def_rating': 98.3}
        },
        {
            'away': 'Ohio State',
            'home': 'Michigan',
            'market_total': 54.0,
            'home_stats': {'pace': 72.1, 'off_rating': 112.5, 'def_rating': 97.8},
            'away_stats': {'pace': 73.8, 'off_rating': 116.2, 'def_rating': 96.4}
        },
        {
            'away': 'Clemson',
            'home': 'Florida State',
            'market_total': 51.5,
            'home_stats': {'pace': 71.5, 'off_rating': 110.1, 'def_rating': 99.9},
            'away_stats': {'pace': 70.3, 'off_rating': 113.4, 'def_rating': 98.2}
        },
    ],
    'NHL': [
        {
            'away': 'Toronto Maple Leafs',
            'home': 'Montreal Canadiens',
            'market_total': 6.5,
            'home_stats': {'pace': 58.5, 'off_rating': 105.2, 'def_rating': 102.5},
            'away_stats': {'pace': 61.2, 'off_rating': 108.8, 'def_rating': 104.3}
        },
        {
            'away': 'Boston Bruins',
            'home': 'New York Rangers',
            'market_total': 6.0,
            'home_stats': {'pace': 57.1, 'off_rating': 106.5, 'def_rating': 101.8},
            'away_stats': {'pace': 56.8, 'off_rating': 107.2, 'def_rating': 103.4}
        },
        {
            'away': 'Colorado Avalanche',
            'home': 'Vegas Golden Knights',
            'market_total': 6.5,
            'home_stats': {'pace': 59.5, 'off_rating': 109.1, 'def_rating': 103.9},
            'away_stats': {'pace': 60.3, 'off_rating': 110.4, 'def_rating': 102.2}
        },
    ]
}


def run_pregame_monte_carlo(sport, game_data, n_simulations=5000):
    """Run Monte Carlo simulation for a pregame matchup"""

    config = SPORT_CONFIG[sport]

    # Set up initial game state (start of game)
    game_state = GameState(
        quarter=1,
        time_remaining=config['quarter_time'],
        home_score=0,
        away_score=0
    )

    # Get team stats
    home_stats = TeamStats(
        pace=game_data['home_stats']['pace'],
        off_rating=game_data['home_stats']['off_rating'],
        def_rating=game_data['home_stats']['def_rating']
    )

    away_stats = TeamStats(
        pace=game_data['away_stats']['pace'],
        off_rating=game_data['away_stats']['off_rating'],
        def_rating=game_data['away_stats']['def_rating']
    )

    # Run simulation
    simulator = PossessionMonteCarloSimulator()
    result = simulator.run_monte_carlo(
        game_state=game_state,
        home_stats=home_stats,
        away_stats=away_stats,
        market_total=game_data['market_total'],
        n_simulations=n_simulations
    )

    return result


def main():
    print("=" * 80)
    print("GENERATING PREGAME MONTE CARLO PREDICTIONS")
    print("=" * 80)

    predictions = []
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    game_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    for sport, games in sample_games.items():
        print(f"\n[{sport}] Running Monte Carlo simulations...")

        for game_data in games:
            away_team = game_data['away']
            home_team = game_data['home']
            market_total = game_data['market_total']

            print(f"  Simulating: {away_team} @ {home_team} (O/U {market_total})")

            # Run Monte Carlo simulation
            mc_result = run_pregame_monte_carlo(sport, game_data, n_simulations=5000)

            # Extract results
            predicted_total = mc_result['mean']
            edge = predicted_total - market_total
            over_prob = mc_result['over_probability']
            under_prob = mc_result['under_probability']
            over_ev = mc_result['over_ev']
            under_ev = mc_result['under_ev']
            kelly_pct = mc_result['kelly_pct']

            # Determine recommendation based on EV
            if over_ev > 0 and over_ev > under_ev:
                recommendation = 'OVER'
                ev = over_ev
                probability = over_prob
            elif under_ev > 0:
                recommendation = 'UNDER'
                ev = under_ev
                probability = under_prob
            else:
                recommendation = 'NO BET'
                ev = 0
                probability = 0.5

            # Determine confidence based on EV and probability
            if ev >= 0.15 or abs(edge) >= 5.0:
                confidence = 'HIGH'
                bet_placed = 'YES'
            elif ev >= 0.08 or abs(edge) >= 3.0:
                confidence = 'MEDIUM'
                bet_placed = 'YES'
            elif ev >= 0.04 or abs(edge) >= 2.0:
                confidence = 'LOW'
                bet_placed = 'YES'
            else:
                confidence = 'NONE'
                bet_placed = 'NO'

            # Game time
            game_time = f"{random.choice(['07:00', '07:30', '08:00', '10:00'])} PM"
            pred_id = f"{sport}_{game_date.replace('-', '')}_{away_team.replace(' ', '_')}_{home_team.replace(' ', '_')}"

            # Create enriched prediction
            prediction = {
                'prediction_id': pred_id,
                'date_predicted': timestamp,
                'game_date': game_date,
                'game_time': game_time,
                'away_team': away_team,
                'home_team': home_team,
                'predicted_total': round(predicted_total, 1),
                'market_total': market_total,
                'edge': round(edge, 1),
                'recommendation': recommendation,
                'confidence': confidence,
                'bet_placed': bet_placed,
                # Monte Carlo enrichments
                'over_probability': round(over_prob, 3),
                'under_probability': round(under_prob, 3),
                'expected_value': round(ev, 3),
                'kelly_pct': round(kelly_pct, 2),
                'std_dev': round(mc_result['std_dev'], 1),
                'percentile_5': round(mc_result['percentiles']['5th'], 1),
                'percentile_25': round(mc_result['percentiles']['25th'], 1),
                'percentile_50': round(mc_result['percentiles']['50th'], 1),
                'percentile_75': round(mc_result['percentiles']['75th'], 1),
                'percentile_95': round(mc_result['percentiles']['95th'], 1),
            }

            predictions.append(prediction)

            print(f"    Predicted: {predicted_total:.1f} | Edge: {edge:+.1f} | {recommendation} ({confidence})")
            print(f"    EV: {ev:.3f} | Kelly: {kelly_pct:.1f}% | Prob: {probability:.1%}")

    # Save to predictions_log.csv
    tracking_dir = Path(__file__).parent / "data" / "tracking"
    tracking_dir.mkdir(parents=True, exist_ok=True)
    tracking_file = tracking_dir / "predictions_log.csv"

    # Load existing if exists
    if tracking_file.exists():
        existing = pd.read_csv(tracking_file)
        existing['game_date'] = pd.to_datetime(existing['game_date'], format='mixed')
        today = pd.Timestamp.now().normalize()
        existing = existing[existing['game_date'] >= today]
    else:
        existing = pd.DataFrame()

    # Combine and save
    new_df = pd.DataFrame(predictions)
    combined = pd.concat([existing, new_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=['prediction_id'], keep='last')
    combined.to_csv(tracking_file, index=False)

    print(f"\n{'=' * 80}")
    print(f"[OK] Generated {len(predictions)} Monte Carlo predictions")
    print(f"[OK] Saved to {tracking_file}")
    print(f"[OK] Total predictions in log: {len(combined)}")

    # Breakdown by sport
    print(f"\nBreakdown by sport:")
    for sport in ['NBA', 'NCAAB', 'NFL', 'NCAAF', 'NHL']:
        count = len([p for p in predictions if p['prediction_id'].startswith(sport)])
        high_conf = len([p for p in predictions if p['prediction_id'].startswith(sport) and p['confidence'] == 'HIGH'])
        print(f"  {sport}: {count} predictions ({high_conf} HIGH confidence)")

    print(f"\n{'=' * 80}")
    print("[OK] COMPLETE - Monte Carlo predictions ready for Max EV Edges page")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
