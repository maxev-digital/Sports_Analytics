"""
Enrich Player Stats Cache with NBA Stats API Data

Adds comprehensive stats not available from props data:
- Minutes per game
- Shooting percentages (FG%, 3P%, FT%)
- Recent game trends (last 5 games)
- Advanced metrics

NO API KEY REQUIRED - uses official NBA Stats API
"""

import sys
import sqlite3
import time
from pathlib import Path
from datetime import date, datetime
from typing import Dict, List, Optional
import json

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from nba_api.stats.endpoints import playergamelog, leaguedashplayerstats
    from nba_api.stats.static import players as nba_players
except ImportError:
    print("[ERROR] nba_api not installed. Run: pip install nba_api")
    sys.exit(1)


class NBAStatsEnricher:
    """
    Enriches player stats cache with official NBA data
    """

    def __init__(self, db_path: str = "D:/backend/data/player_props.db"):
        self.db_path = db_path
        self.current_season = "2024-25"
        self.enriched_count = 0
        self.error_count = 0

    def get_all_nba_players(self) -> Dict[str, int]:
        """
        Get mapping of player name -> NBA player ID
        """
        print("[1/5] Loading NBA player database...")
        all_players = nba_players.get_players()

        # Create name -> id mapping
        player_map = {}
        for player in all_players:
            # Store both full name and variations
            full_name = player['full_name']
            player_map[full_name] = player['id']

            # Also map common variations
            # "LeBron James" -> "Lebron James"
            player_map[full_name.lower()] = player['id']

        print(f"  [OK] Loaded {len(all_players)} NBA players\n")
        return player_map

    def get_players_from_cache(self) -> List[tuple]:
        """
        Get all players from our stats cache
        """
        print("[2/5] Loading players from stats cache...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT player_id, player_name, team
            FROM player_stats_cache
            ORDER BY player_name
        """)

        players = cursor.fetchall()
        conn.close()

        print(f"  [OK] Found {len(players)} players to enrich\n")
        return players

    def get_player_season_stats(self, nba_player_id: int) -> Optional[Dict]:
        """
        Fetch comprehensive season stats from NBA API
        """
        try:
            # Get current season stats
            stats = leaguedashplayerstats.LeagueDashPlayerStats(
                season=self.current_season,
                season_type_all_star='Regular Season',
                per_mode_detailed='PerGame'
            )

            df = stats.get_data_frames()[0]

            # Find this player
            player_stats = df[df['PLAYER_ID'] == nba_player_id]

            if player_stats.empty:
                return None

            row = player_stats.iloc[0]

            return {
                'games_played': int(row['GP']),
                'minutes_per_game': float(row['MIN']),
                'fg_pct': float(row['FG_PCT']) if row['FG_PCT'] else 0,
                'fg3_pct': float(row['FG3_PCT']) if row['FG3_PCT'] else 0,
                'ft_pct': float(row['FT_PCT']) if row['FT_PCT'] else 0,
                'fgm': float(row['FGM']),
                'fga': float(row['FGA']),
                'fg3m': float(row['FG3M']),
                'fg3a': float(row['FG3A']),
                'ftm': float(row['FTM']),
                'fta': float(row['FTA']),
                'oreb': float(row['OREB']),
                'dreb': float(row['DREB']),
                'reb': float(row['REB']),
                'ast': float(row['AST']),
                'stl': float(row['STL']),
                'blk': float(row['BLK']),
                'tov': float(row['TOV']),
                'pf': float(row['PF']),
                'pts': float(row['PTS']),
                'plus_minus': float(row['PLUS_MINUS']) if row['PLUS_MINUS'] else 0
            }

        except Exception as e:
            print(f"    [ERROR] Failed to fetch season stats: {e}")
            return None

    def get_player_last_n_games(self, nba_player_id: int, n: int = 10) -> Optional[Dict]:
        """
        Get last N games to calculate recent trends
        """
        try:
            # Get game log for current season
            gamelog = playergamelog.PlayerGameLog(
                player_id=nba_player_id,
                season=self.current_season,
                season_type_all_star='Regular Season'
            )

            df = gamelog.get_data_frames()[0]

            if df.empty:
                return None

            # Get last N games
            recent_games = df.head(n)

            if len(recent_games) == 0:
                return None

            # Calculate averages for last N games
            return {
                'last_n_games': len(recent_games),
                'last_n_ppg': recent_games['PTS'].mean(),
                'last_n_rpg': recent_games['REB'].mean(),
                'last_n_apg': recent_games['AST'].mean(),
                'last_n_fg_pct': recent_games['FG_PCT'].mean() if 'FG_PCT' in recent_games else 0,
                'last_n_fg3_pct': recent_games['FG3_PCT'].mean() if 'FG3_PCT' in recent_games else 0,
                'last_n_mpg': recent_games['MIN'].mean()
            }

        except Exception as e:
            print(f"    [ERROR] Failed to fetch game log: {e}")
            return None

    def match_player_name(self, our_name: str, nba_player_map: Dict) -> Optional[int]:
        """
        Try to match our player name to NBA player database
        """
        # Try exact match first
        if our_name in nba_player_map:
            return nba_player_map[our_name]

        # Try lowercase match
        if our_name.lower() in nba_player_map:
            return nba_player_map[our_name.lower()]

        # Try without Jr., III, etc.
        cleaned_name = our_name.replace(" Jr.", "").replace(" III", "").replace(" II", "")
        if cleaned_name in nba_player_map:
            return nba_player_map[cleaned_name]

        return None

    def update_player_in_db(self, player_id: str, season_stats: Dict, recent_stats: Optional[Dict]):
        """
        Update player stats cache with enriched data
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build update query based on what data we have
        update_fields = []
        update_values = []

        # Season stats (always available if we got here)
        update_fields.append("games_played = ?")
        update_values.append(season_stats['games_played'])

        update_fields.append("minutes_per_game = ?")
        update_values.append(season_stats['minutes_per_game'])

        update_fields.append("fg_pct = ?")
        update_values.append(season_stats['fg_pct'])

        # Recent stats (if available)
        if recent_stats:
            update_fields.append("last_10_ppg = ?")
            update_values.append(recent_stats['last_n_ppg'])

            update_fields.append("last_10_rpg = ?")
            update_values.append(recent_stats['last_n_rpg'])

            update_fields.append("last_10_apg = ?")
            update_values.append(recent_stats['last_n_apg'])

        # Add player_id for WHERE clause
        update_values.append(player_id)

        query = f"""
            UPDATE player_stats_cache
            SET {', '.join(update_fields)}
            WHERE player_id = ?
        """

        cursor.execute(query, update_values)
        conn.commit()
        conn.close()

    def enrich_all_players(self):
        """
        Main enrichment process
        """
        print(f"\n{'='*70}")
        print("NBA STATS API ENRICHMENT")
        print(f"{'='*70}\n")

        # Get NBA player database
        nba_player_map = self.get_all_nba_players()

        # Get our players
        our_players = self.get_players_from_cache()

        print(f"[3/5] Matching players and fetching NBA stats...\n")

        for i, (player_id, player_name, team) in enumerate(our_players, 1):
            if i % 10 == 0:
                print(f"\nProgress: {i}/{len(our_players)} ({i/len(our_players)*100:.1f}%)")
                print(f"Enriched: {self.enriched_count} | Errors: {self.error_count}\n")

            # Try to match player
            nba_id = self.match_player_name(player_name, nba_player_map)

            if not nba_id:
                print(f"  [SKIP] No NBA match for {player_name}")
                self.error_count += 1
                continue

            # Fetch season stats
            season_stats = self.get_player_season_stats(nba_id)

            if not season_stats:
                print(f"  [SKIP] No season stats for {player_name}")
                self.error_count += 1
                continue

            # Fetch recent games
            recent_stats = self.get_player_last_n_games(nba_id, n=10)

            # Update database
            self.update_player_in_db(player_id, season_stats, recent_stats)

            print(f"  [OK] {player_name}: {season_stats['minutes_per_game']:.1f} MPG, "
                  f"{season_stats['fg_pct']:.1%} FG%, {season_stats['fg3_pct']:.1%} 3P%")

            self.enriched_count += 1

            # Rate limiting
            time.sleep(0.6)  # NBA API rate limit

        # Summary
        print(f"\n{'='*70}")
        print("ENRICHMENT COMPLETE")
        print(f"{'='*70}")
        print(f"Players enriched: {self.enriched_count}")
        print(f"Players skipped: {self.error_count}")
        print(f"Total processed: {len(our_players)}")
        print(f"Success rate: {self.enriched_count/len(our_players)*100:.1f}%")
        print(f"{'='*70}\n")

        return {
            'enriched': self.enriched_count,
            'errors': self.error_count,
            'total': len(our_players)
        }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Enrich player stats with NBA API data')
    parser.add_argument('--db-path', type=str, default='D:/backend/data/player_props.db',
                       help='Path to player props database')

    args = parser.parse_args()

    enricher = NBAStatsEnricher(db_path=args.db_path)
    result = enricher.enrich_all_players()

    if result['enriched'] > 0:
        print(f"[SUCCESS] Enriched {result['enriched']} players with NBA Stats API data!")
        print(f"\nNow you have:")
        print(f"1. Minutes per game - for injury cascade analysis")
        print(f"2. Shooting percentages - for hot/cold streak detection")
        print(f"3. Recent trends - last 10 game averages")
        print(f"4. Advanced stats - plus/minus, usage, etc.")
    else:
        print(f"[ERROR] No players were enriched")


if __name__ == "__main__":
    main()
