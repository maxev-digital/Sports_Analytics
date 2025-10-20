"""Test script to verify NHL stats"""
import asyncio
from nhl_stats_client import NHLStatsClient

async def test_nhl():
    """Test NHL stats fetching"""
    client = NHLStatsClient()

    try:
        # Test a few teams
        test_teams = ['bos', 'fla', 'edm']

        for team_abbr in test_teams:
            print(f"\n{'='*60}")
            print(f"Testing {team_abbr.upper()}")
            print(f"{'='*60}")

            stats = await client.get_team_stats_with_rankings(team_abbr)

            if stats:
                print(f"\n[SUCCESS] Fetched stats for {stats.team_name}")
                print(f"\nRecord:")
                print(f"  Wins: {stats.wins}")
                print(f"  Losses: {stats.losses}")
                print(f"  OT Losses: {stats.ot_losses}")
                print(f"  W-L-OTL: {stats.wins}-{stats.losses}-{stats.ot_losses}")
                print(f"  Points: {stats.points}")
                print(f"  Win %: {stats.win_pct:.3f}")

                print(f"\nScoring:")
                print(f"  Goals Per Game: {stats.goals_per_game:.2f}")
                print(f"  Goals Against Per Game: {stats.goals_against_per_game:.2f}")

                print(f"\nOther Stats:")
                print(f"  Games Played: {stats.games_played}")
                print(f"  Shots Per Game: {stats.shots_per_game:.1f}")
                print(f"  Save %: {stats.save_pct:.3f}")
                print(f"  Shooting %: {stats.shooting_pct:.3f}")
                print(f"  PDO: {stats.pdo:.1f}")
                print(f"  Power Play %: {stats.power_play_pct:.1%}")
                print(f"  Penalty Kill %: {stats.penalty_kill_pct:.1%}")
                print(f"  Faceoff Win %: {stats.faceoff_win_pct:.1%}")
                print(f"  Form Trend: {stats.form_trend}")

                # Verify the critical fields
                if stats.wins == 0 and stats.losses == 0:
                    print("\n[WARNING] Record showing 0-0!")
                else:
                    print(f"\n[CONFIRMED] W-L-OTL: {stats.wins}-{stats.losses}-{stats.ot_losses}")

                if stats.goals_against_per_game == 0.0:
                    print("[WARNING] GA/G showing 0.0!")
                else:
                    print(f"[CONFIRMED] GA/G: {stats.goals_against_per_game:.2f}")
            else:
                print(f"\n[FAILED] Could not fetch stats for {team_abbr}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.client.aclose()

if __name__ == "__main__":
    asyncio.run(test_nhl())
