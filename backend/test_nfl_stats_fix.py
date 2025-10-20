"""Test script to verify NFL stats fix for W-L record and PA/G"""
import asyncio
from nfl_stats_client import NFLStatsClient

async def test_fix():
    """Test that we now get W-L record and PA/G correctly"""
    client = NFLStatsClient()

    try:
        # Test a few teams
        test_teams = ['ARI', 'KC', 'BUF']

        for team_abbr in test_teams:
            print(f"\n{'='*60}")
            print(f"Testing {team_abbr}")
            print(f"{'='*60}")

            stats = await client.get_team_season_stats(team_abbr, is_ncaaf=False)

            if stats:
                print(f"\n[SUCCESS] Fetched stats for {stats.team_name}")
                print(f"\nRecord:")
                print(f"  Wins: {stats.wins}")
                print(f"  Losses: {stats.losses}")
                print(f"  Ties: {stats.ties}")
                print(f"  W-L Record: {stats.wins}-{stats.losses}{f'-{stats.ties}' if stats.ties > 0 else ''}")
                print(f"  Win %: {stats.win_pct:.3f}")

                print(f"\nScoring:")
                print(f"  PPG (Points Per Game): {stats.points_per_game:.1f}")
                print(f"  PA/G (Points Allowed Per Game): {stats.points_allowed_per_game:.1f}")
                print(f"  Point Differential: {stats.point_differential:+.1f}")

                print(f"\nOther Stats:")
                print(f"  Games Played: {stats.games_played}")
                print(f"  Total Yards/G: {stats.total_yards_per_game:.1f}")
                print(f"  Passing Yards/G: {stats.passing_yards_per_game:.1f}")
                print(f"  Rushing Yards/G: {stats.rushing_yards_per_game:.1f}")
                print(f"  Turnover Diff: {stats.turnover_differential:+.1f}")
                print(f"  Form Trend: {stats.form_trend}")

                # Verify the critical fixes
                if stats.wins == 0 and stats.losses == 0:
                    print("\n[WARNING] Record still showing 0-0!")
                else:
                    print(f"\n[CONFIRMED] W-L RECORD FIX: {stats.wins}-{stats.losses}")

                if stats.points_allowed_per_game == 0.0:
                    print("[WARNING] PA/G still showing 0.0!")
                else:
                    print(f"[CONFIRMED] PA/G FIX: {stats.points_allowed_per_game:.1f}")
            else:
                print(f"\n[FAILED] Could not fetch stats for {team_abbr}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_fix())
