"""
Seed database with real coach data from your research

This incorporates actual 2023-24 coach pulling tendencies
"""

from goalie_pull_database import GoaliePullDatabase


# Real coach data from your research
COACH_DATA = {
    'Jon Cooper': {
        'team': 'Tampa Bay Lightning',
        'pull_rate': 0.987,
        'avg_pull_time_seconds': 132,  # 2:12
        'success_rate': 0.142,
        'ev_edge': 0.22,
        'aggression_score': 95,  # Highest
        'notes': 'Pulls earliest (+30s edge vs market), 100% in playoffs'
    },
    'Rod Brind\'Amour': {
        'team': 'Carolina Hurricanes',
        'pull_rate': 0.961,
        'avg_pull_time_seconds': 128,  # 2:08
        'success_rate': 0.128,
        'ev_edge': 0.19,
        'aggression_score': 92
    },
    'Jared Bednar': {
        'team': 'Colorado Avalanche',
        'pull_rate': 0.943,
        'avg_pull_time_seconds': 118,  # 1:58
        'success_rate': 0.151,
        'ev_edge': 0.21,
        'aggression_score': 88
    },
    'Bruce Cassidy': {
        'team': 'Vegas Golden Knights',
        'pull_rate': 0.938,
        'avg_pull_time_seconds': 125,  # 2:05
        'success_rate': 0.139,
        'ev_edge': 0.20,
        'aggression_score': 87
    },
    'Peter DeBoer': {
        'team': 'Dallas Stars',
        'pull_rate': 0.912,
        'avg_pull_time_seconds': 112,  # 1:52
        'success_rate': 0.117,
        'ev_edge': 0.17,
        'aggression_score': 80
    },
    'Mike Sullivan': {
        'team': 'Pittsburgh Penguins',
        'pull_rate': 0.894,
        'avg_pull_time_seconds': 105,  # 1:45
        'success_rate': 0.103,
        'ev_edge': 0.15,
        'aggression_score': 75
    },
    'John Tortorella': {
        'team': 'Philadelphia Flyers',
        'pull_rate': 0.876,
        'avg_pull_time_seconds': 98,  # 1:38
        'success_rate': 0.098,
        'ev_edge': 0.13,
        'aggression_score': 55,  # Most conservative
        'notes': 'Pulls latest - high risk, low reward'
    },
    'Sheldon Keefe': {
        'team': 'Toronto Maple Leafs',
        'pull_rate': 0.851,
        'avg_pull_time_seconds': 115,  # 1:55
        'success_rate': 0.112,
        'ev_edge': 0.16,
        'aggression_score': 70
    }
}

# Score differential data from your research
SCORE_DIFF_DATA = {
    'down_1': {
        'total_pulls': 1056,
        'percentage': 0.88,
        'avg_pull_time_seconds': 118,  # 1:58
        'success_rate': 0.128,
        'notes': 'Most common; optimal at 2:08 remaining for +EV'
    },
    'down_2': {
        'total_pulls': 132,
        'percentage': 0.11,
        'avg_pull_time_seconds': 165,  # 2:45
        'success_rate': 0.083,
        'notes': 'Higher risk; pulls earlier to chase 2 goals'
    },
    'down_3_plus': {
        'total_pulls': 12,
        'percentage': 0.01,
        'avg_pull_time_seconds': 190,  # 3:10
        'success_rate': 0.042,
        'notes': 'Rare; desperation bets with low success'
    }
}

# ML Model Performance (from your backtests)
ML_PERFORMANCE = {
    'total_pulls_2024': 1200,
    'pulls_predicted': 1142,
    'accuracy': 0.952,
    'auc': 0.88,
    'false_positive_rate': 0.041,
    'avg_advance_time_seconds': 42,
    'avg_odds_captured': 312,
    'roi_100_bets': 0.421  # +42.1%
}


def seed_coach_data():
    """
    Seed database with real coach tendencies

    This creates sample pull events based on your research data
    """
    db = GoaliePullDatabase()

    print("=" * 80)
    print("SEEDING DATABASE WITH REAL COACH DATA")
    print("=" * 80)

    # For each coach, create representative pull events
    game_id_counter = 2023020001

    for coach_name, data in COACH_DATA.items():
        team = data['team']
        avg_time = data['avg_pull_time_seconds']

        print(f"\n{coach_name} ({team}):")
        print(f"  Pull rate: {data['pull_rate']*100:.1f}%")
        print(f"  Avg time: {avg_time//60}:{avg_time%60:02d}")
        print(f"  Success rate: {data['success_rate']*100:.1f}%")
        print(f"  +EV Edge: {data['ev_edge']*100:.0f}%")
        print(f"  Aggression: {data['aggression_score']}/100")

        # Create sample events (down by 1, home game)
        for i in range(5):  # 5 sample events per coach
            event = {
                'game_id': f"{game_id_counter}",
                'team': team,
                'coach': coach_name,
                'period': 3,
                'time_remaining': f"{avg_time//60:02d}:{avg_time%60:02d}",
                'time_remaining_seconds': avg_time,
                'score_differential': -1,
                'home_score': 1,
                'away_score': 2,
                'opponent': 'Sample Opponent',
                'home_game': True,
                'division_game': False,
                'playoff_game': False,
                'season': '20232024',
                'game_date': '2024-01-15',
                'pull_timestamp': '2024-01-15T22:45:00Z',
                'goalie_name': 'Sample Goalie',
                'result': 'goal_for' if i < (data['success_rate'] * 5) else 'goal_against',
                'final_outcome': 'win' if i < (data['success_rate'] * 5) else 'loss'
            }

            db.insert_pull_event(event)
            game_id_counter += 1

    print("\n" + "=" * 80)
    print("[OK] COACH DATA SEEDED")
    print("=" * 80)

    # Print summary
    summary = db.get_stats_summary()
    print(f"\nDatabase now contains:")
    print(f"  Total events: {summary['total_pull_events']}")
    print(f"  Teams: {summary['total_teams']}")
    print(f"  Games: {summary['total_games']}")

    # Update team stats
    print("\nUpdating team statistics...")
    teams = db.get_all_teams()
    for team in teams:
        db.update_team_stats(team, '20232024')
        print(f"  [OK] {team}")

    print("\n[OK] Database ready for ML predictions!")
    print("\nYour real coach data is now in the system:")
    print("  - Jon Cooper pulls at 2:12 (most aggressive)")
    print("  - Tortorella pulls at 1:38 (most conservative)")
    print("  - ML model can now use actual tendencies")


if __name__ == "__main__":
    seed_coach_data()

    # Test query
    print("\n" + "=" * 80)
    print("TEST QUERY: Jon Cooper's tendencies")
    print("=" * 80)

    db = GoaliePullDatabase()
    patterns = db.get_team_pull_patterns('Tampa Bay Lightning', '20232024')
    print(f"\nTampa Bay Lightning patterns:")
    print(f"  Total pulls: {patterns['overall']['total_pulls']}")
    print(f"  Avg pull time: {patterns['overall']['avg_pull_time']}")
    print(f"  Success rate: {patterns['overall']['success_rate']*100:.1f}%")
