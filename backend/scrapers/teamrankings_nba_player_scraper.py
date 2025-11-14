"""
TeamRankings NBA Player Stats Scraper - COMPREHENSIVE
Scrapes ALL available player statistics from TeamRankings.com

URLs to scrape:
- Points per game: /nba/player-stats/points-per-game
- Rebounds per game: /nba/player-stats/rebounds-per-game
- Assists per game: /nba/player-stats/assists-per-game
- Steals per game: /nba/player-stats/steals-per-game
- Blocks per game: /nba/player-stats/blocks-per-game
- Turnovers per game: /nba/player-stats/turnovers-per-game
- Field goal percentage: /nba/player-stats/field-goal-pct
- Three point percentage: /nba/player-stats/three-point-pct
- Free throw percentage: /nba/player-stats/free-throw-pct
- Minutes per game: /nba/player-stats/minutes-per-game
- Plus/minus: /nba/player-stats/plus-minus-per-game
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import time
from datetime import date, datetime
from typing import Dict, List, Optional
import json
import os

class TeamRankingsNBAPlayerScraper:
    """Scrapes ALL NBA player stats from TeamRankings"""

    BASE_URL = "https://www.teamrankings.com/nba/player-stats"

    # All available stat pages
    STAT_PAGES = {
        'points-per-game': 'ppg',
        'rebounds-per-game': 'rpg',
        'assists-per-game': 'apg',
        'steals-per-game': 'spg',
        'blocks-per-game': 'bpg',
        'turnovers-per-game': 'tpg',
        'field-goal-pct': 'fg_pct',
        'three-point-pct': 'fg3_pct',
        'free-throw-pct': 'ft_pct',
        'minutes-per-game': 'mpg',
        'plus-minus-per-game': 'plus_minus',
        'offensive-rebounds-per-game': 'orpg',
        'defensive-rebounds-per-game': 'drpg',
        'three-pointers-made-per-game': 'fg3m',
        'three-pointers-attempted-per-game': 'fg3a',
        'field-goals-made-per-game': 'fgm',
        'field-goals-attempted-per-game': 'fga',
        'free-throws-made-per-game': 'ftm',
        'free-throws-attempted-per-game': 'fta',
        'personal-fouls-per-game': 'pf',
    }

    def __init__(self, db_path: str = "data/player_props.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        self.all_player_stats = {}  # player_name -> {stat: value}

    def scrape_stat_page(self, stat_url_suffix: str, stat_key: str) -> Dict[str, float]:
        """
        Scrape a single stat page and return player_name -> value mapping
        """
        url = f"{self.BASE_URL}/{stat_url_suffix}"

        try:
            print(f"  Scraping {stat_key} from {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the stats table
            table = soup.find('table', {'class': 'tr-table'})
            if not table:
                print(f"    [WARN] No table found for {stat_key}")
                return {}

            player_stats = {}
            rows = table.find('tbody').find_all('tr')

            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    # Column 0: Rank
                    # Column 1: Player name
                    # Column 2: Team
                    # Column 3: Stat value
                    player_name = cells[1].get_text(strip=True)
                    team = cells[2].get_text(strip=True)
                    stat_value_text = cells[3].get_text(strip=True)

                    # Parse stat value
                    try:
                        # Remove commas and convert to float
                        stat_value = float(stat_value_text.replace(',', ''))
                        player_stats[player_name] = {
                            'value': stat_value,
                            'team': team
                        }
                    except ValueError:
                        continue

            print(f"    [OK] Found {len(player_stats)} players")
            return player_stats

        except Exception as e:
            print(f"    [ERROR] Failed to scrape {stat_key}: {e}")
            return {}

    def scrape_all_stats(self):
        """
        Scrape ALL stat pages and build comprehensive player database
        """
        print(f"\n{'='*70}")
        print("SCRAPING ALL NBA PLAYER STATS FROM TEAMRANKINGS")
        print(f"{'='*70}\n")

        print(f"[1/2] Scraping {len(self.STAT_PAGES)} stat categories...\n")

        stat_count = 0
        for stat_url, stat_key in self.STAT_PAGES.items():
            stat_count += 1
            print(f"[{stat_count}/{len(self.STAT_PAGES)}] {stat_key}")

            player_data = self.scrape_stat_page(stat_url, stat_key)

            # Merge into all_player_stats
            for player_name, data in player_data.items():
                if player_name not in self.all_player_stats:
                    self.all_player_stats[player_name] = {
                        'team': data['team']
                    }

                self.all_player_stats[player_name][stat_key] = data['value']

            # Rate limiting
            time.sleep(1)

        print(f"\n[2/2] Collected stats for {len(self.all_player_stats)} players")
        print(f"  Stats per player: {len(self.STAT_PAGES)} categories\n")

        return self.all_player_stats

    def save_to_database(self):
        """
        Save all player stats to database
        """
        print(f"\n{'='*70}")
        print("SAVING TO DATABASE")
        print(f"{'='*70}\n")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        saved_count = 0
        errors = 0

        for player_name, stats in self.all_player_stats.items():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO player_stats_cache
                    (player_id, player_name, team, date, games_played, minutes_per_game,
                     points_per_game, rebounds_per_game, assists_per_game, fg3_per_game,
                     blocks_per_game, steals_per_game, fg_pct, last_10_ppg, last_10_rpg,
                     last_10_apg, trend_direction)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    player_name.replace(' ', '_'),  # Use name as ID
                    player_name,
                    stats.get('team', 'UNK'),
                    date.today().isoformat(),
                    0,  # games_played - not available from TeamRankings
                    stats.get('mpg', 0),
                    stats.get('ppg', 0),
                    stats.get('rpg', 0),
                    stats.get('apg', 0),
                    stats.get('fg3m', 0),
                    stats.get('bpg', 0),
                    stats.get('spg', 0),
                    stats.get('fg_pct', 0),
                    stats.get('ppg', 0),  # Use season avg as last 10
                    stats.get('rpg', 0),
                    stats.get('apg', 0),
                    'STABLE'
                ))
                saved_count += 1

            except Exception as e:
                print(f"  [ERROR] Failed to save {player_name}: {e}")
                errors += 1

        conn.commit()
        conn.close()

        print(f"[OK] Saved {saved_count} players to database")
        if errors > 0:
            print(f"[WARN] {errors} errors occurred")

        return saved_count

    def export_to_json(self, output_file: str):
        """
        Export all stats to JSON for backup
        """
        print(f"\n{'='*70}")
        print("EXPORTING TO JSON BACKUP")
        print(f"{'='*70}\n")

        backup_data = {
            'scraped_date': date.today().isoformat(),
            'scraped_time': datetime.now().isoformat(),
            'total_players': len(self.all_player_stats),
            'stat_categories': list(self.STAT_PAGES.keys()),
            'players': self.all_player_stats
        }

        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(backup_data, f, indent=2)

        file_size = os.path.getsize(output_file) / 1024  # KB
        print(f"[OK] Exported to {output_file}")
        print(f"  File size: {file_size:.1f} KB")
        print(f"  Players: {len(self.all_player_stats)}")
        print(f"  Stats: {len(self.STAT_PAGES)} categories per player")

        return output_file


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Scrape ALL NBA player stats from TeamRankings')
    parser.add_argument('--db-path', type=str, default='data/player_props.db',
                       help='Path to database')
    parser.add_argument('--backup-path', type=str,
                       default='D:/backend/data/backups/teamrankings_nba_players.json',
                       help='Path for JSON backup')

    args = parser.parse_args()

    scraper = TeamRankingsNBAPlayerScraper(db_path=args.db_path)

    # Scrape all stats
    all_stats = scraper.scrape_all_stats()

    if not all_stats:
        print("\n[ERROR] No stats were scraped!")
        return

    # Save to database
    saved_count = scraper.save_to_database()

    # Export JSON backup
    backup_file = scraper.export_to_json(args.backup_path)

    # Summary
    print(f"\n{'='*70}")
    print("COMPLETE")
    print(f"{'='*70}")
    print(f"Players scraped: {len(all_stats)}")
    print(f"Stats per player: {len(scraper.STAT_PAGES)}")
    print(f"Database records: {saved_count}")
    print(f"Backup location: {backup_file}")
    print(f"{'='*70}\n")

    print("[SUCCESS] All NBA player stats scraped and backed up!")


if __name__ == "__main__":
    main()
