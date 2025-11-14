"""
Fetch NBA Injury Data

Creates injury tracking system for "Player Injury Prop Cascade" bets.

When a star player goes down:
- Identify backup players who will get more minutes
- Recalculate their projected stats based on increased usage
- Generate high-value betting opportunities

Data sources (in order of preference):
1. BallDontLie API - Free injury data
2. ESPN API - Unofficial but reliable
3. NBA.com injury report
"""

import requests
import sqlite3
import json
import time
from datetime import datetime, date
from typing import List, Dict, Optional


class InjuryDataFetcher:
    """
    Fetches and tracks NBA player injuries
    """

    def __init__(self, db_path: str = "D:/backend/data/player_props.db"):
        self.db_path = db_path
        self.balldontlie_base = "https://api.balldontlie.io/v1"
        self.injuries = []

    def create_injuries_table(self):
        """
        Create table to track player injuries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_injuries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                team TEXT NOT NULL,
                injury_status TEXT,
                injury_type TEXT,
                injury_body_part TEXT,
                expected_return_date TEXT,
                games_missed INTEGER DEFAULT 0,
                last_updated TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Also create cascade opportunities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS injury_cascade_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                injured_player_id TEXT NOT NULL,
                injured_player_name TEXT NOT NULL,
                beneficiary_player_id TEXT NOT NULL,
                beneficiary_player_name TEXT NOT NULL,
                team TEXT NOT NULL,
                projected_minutes_increase REAL,
                projected_ppg_increase REAL,
                projected_rpg_increase REAL,
                projected_apg_increase REAL,
                confidence_score REAL,
                opportunity_created_date TEXT,
                opportunity_expires_date TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

        print("[OK] Injury tracking tables created\n")

    def fetch_injuries_from_balldontlie(self) -> List[Dict]:
        """
        Try to fetch injury data from BallDontLie API
        Note: BallDontLie might not have dedicated injury endpoint
        """
        print("[1/3] Attempting to fetch from BallDontLie API...")

        try:
            # BallDontLie doesn't have injury endpoint in v1
            # Will need to use alternative source
            print("  [WARN] BallDontLie v1 doesn't have injury data\n")
            return []

        except Exception as e:
            print(f"  [ERROR] BallDontLie failed: {e}\n")
            return []

    def fetch_injuries_from_espn(self) -> List[Dict]:
        """
        Fetch injury data from ESPN's unofficial API
        """
        print("[2/3] Fetching from ESPN API...")

        try:
            # ESPN has injury data in their scoreboard endpoint
            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            injuries = []

            # ESPN provides team rosters with injury status
            for team in data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', []):
                team_info = team.get('team', {})
                team_name = team_info.get('abbreviation', 'UNK')

                # Get roster with injuries
                team_id = team_info.get('id')
                if team_id:
                    roster_url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster"

                    roster_response = requests.get(roster_url, timeout=10)
                    if roster_response.ok:
                        roster_data = roster_response.json()

                        for athlete in roster_data.get('athletes', []):
                            injury_status = athlete.get('injuries', [])

                            if injury_status:
                                for injury in injury_status:
                                    injuries.append({
                                        'player_id': str(athlete.get('id', '')),
                                        'player_name': athlete.get('displayName', ''),
                                        'team': team_name,
                                        'injury_status': injury.get('status', 'Unknown'),
                                        'injury_type': injury.get('type', ''),
                                        'injury_body_part': injury.get('details', {}).get('location', ''),
                                        'last_updated': datetime.now().isoformat()
                                    })

                    time.sleep(0.5)  # Rate limiting

            print(f"  [OK] Found {len(injuries)} injured players from ESPN\n")
            return injuries

        except Exception as e:
            print(f"  [ERROR] ESPN fetch failed: {e}\n")
            return []

    def fetch_injuries_from_nba_dot_com(self) -> List[Dict]:
        """
        Fetch from official NBA.com injury report
        """
        print("[3/3] Fetching from NBA.com injury report...")

        try:
            # NBA.com has injury report
            url = "https://www.nba.com/stats/js/data/widgets/home_injury.json"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.nba.com/'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            injuries = []

            # Parse NBA.com injury format
            for injury_entry in data.get('payload', {}).get('injury', []):
                injuries.append({
                    'player_id': injury_entry.get('player_id', ''),
                    'player_name': injury_entry.get('player_name', ''),
                    'team': injury_entry.get('team_abbr', ''),
                    'injury_status': injury_entry.get('injury_status', ''),
                    'injury_type': injury_entry.get('injury_type', ''),
                    'injury_body_part': injury_entry.get('injury_description', ''),
                    'last_updated': datetime.now().isoformat()
                })

            print(f"  [OK] Found {len(injuries)} injured players from NBA.com\n")
            return injuries

        except Exception as e:
            print(f"  [ERROR] NBA.com fetch failed: {e}\n")
            return []

    def save_injuries_to_db(self, injuries: List[Dict]):
        """
        Save injury data to database
        """
        if not injuries:
            print("[SKIP] No injuries to save\n")
            return 0

        print(f"[4/4] Saving {len(injuries)} injuries to database...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        saved_count = 0

        for injury in injuries:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO player_injuries
                    (player_id, player_name, team, injury_status, injury_type,
                     injury_body_part, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    injury['player_id'],
                    injury['player_name'],
                    injury['team'],
                    injury['injury_status'],
                    injury['injury_type'],
                    injury['injury_body_part'],
                    injury['last_updated']
                ))

                saved_count += 1

            except Exception as e:
                print(f"  [ERROR] Failed to save {injury.get('player_name', 'Unknown')}: {e}")

        conn.commit()
        conn.close()

        print(f"  [OK] Saved {saved_count} injuries\n")
        return saved_count

    def identify_cascade_opportunities(self):
        """
        Identify players who will benefit from injured teammates

        Logic:
        1. Find injured starters (high minutes players)
        2. Identify their backups (same position, lower minutes)
        3. Calculate expected minutes/stats increase for backups
        4. Generate betting opportunities
        """
        print("[BONUS] Identifying injury cascade opportunities...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get current injuries
        cursor.execute("""
            SELECT player_id, player_name, team, injury_status
            FROM player_injuries
            WHERE injury_status IN ('Out', 'Doubtful', 'OUT', 'DOUBTFUL')
        """)

        injuries = cursor.fetchall()

        if not injuries:
            print("  [INFO] No significant injuries found\n")
            conn.close()
            return

        opportunities = []

        for injured_id, injured_name, team, status in injuries:
            # Get injured player's stats
            cursor.execute("""
                SELECT minutes_per_game, points_per_game, rebounds_per_game, assists_per_game
                FROM player_stats_cache
                WHERE player_id = ? OR player_name = ?
            """, (injured_id, injured_name))

            injured_stats = cursor.fetchone()

            if not injured_stats:
                continue

            injured_mpg, injured_ppg, injured_rpg, injured_apg = injured_stats

            # Only process if injured player plays significant minutes
            if injured_mpg < 20:
                continue

            # Find potential beneficiaries (same team, lower minutes)
            cursor.execute("""
                SELECT player_id, player_name, minutes_per_game,
                       points_per_game, rebounds_per_game, assists_per_game
                FROM player_stats_cache
                WHERE team = ?
                  AND minutes_per_game < ?
                  AND minutes_per_game > 10
                  AND player_id != ?
                ORDER BY minutes_per_game DESC
                LIMIT 3
            """, (team, injured_mpg, injured_id))

            beneficiaries = cursor.fetchall()

            for benef_id, benef_name, benef_mpg, benef_ppg, benef_rpg, benef_apg in beneficiaries:
                # Estimate minutes increase (conservative)
                minutes_increase = min(injured_mpg * 0.3, 10)  # Max 10 min increase

                # Calculate per-minute production for beneficiary
                if benef_mpg > 0:
                    ppg_per_min = benef_ppg / benef_mpg
                    rpg_per_min = benef_rpg / benef_mpg
                    apg_per_min = benef_apg / benef_mpg

                    # Project increases
                    ppg_increase = ppg_per_min * minutes_increase
                    rpg_increase = rpg_per_min * minutes_increase
                    apg_increase = apg_per_min * minutes_increase

                    # Confidence based on injured player importance
                    confidence = min(injured_mpg / 40 * 100, 95)

                    opportunities.append({
                        'injured_player_id': injured_id,
                        'injured_player_name': injured_name,
                        'beneficiary_player_id': benef_id,
                        'beneficiary_player_name': benef_name,
                        'team': team,
                        'projected_minutes_increase': minutes_increase,
                        'projected_ppg_increase': ppg_increase,
                        'projected_rpg_increase': rpg_increase,
                        'projected_apg_increase': apg_increase,
                        'confidence_score': confidence
                    })

        # Save opportunities
        for opp in opportunities:
            cursor.execute("""
                INSERT INTO injury_cascade_opportunities
                (injured_player_id, injured_player_name, beneficiary_player_id,
                 beneficiary_player_name, team, projected_minutes_increase,
                 projected_ppg_increase, projected_rpg_increase, projected_apg_increase,
                 confidence_score, opportunity_created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                opp['injured_player_id'],
                opp['injured_player_name'],
                opp['beneficiary_player_id'],
                opp['beneficiary_player_name'],
                opp['team'],
                opp['projected_minutes_increase'],
                opp['projected_ppg_increase'],
                opp['projected_rpg_increase'],
                opp['projected_apg_increase'],
                opp['confidence_score'],
                date.today().isoformat()
            ))

        conn.commit()
        conn.close()

        print(f"  [OK] Identified {len(opportunities)} cascade opportunities\n")

        # Print top opportunities
        if opportunities:
            print("Top Cascade Opportunities:")
            for opp in sorted(opportunities, key=lambda x: x['confidence_score'], reverse=True)[:5]:
                print(f"  • {opp['beneficiary_player_name']} ({opp['team']})")
                print(f"    Injured: {opp['injured_player_name']}")
                print(f"    Projected: +{opp['projected_minutes_increase']:.1f} MIN, "
                      f"+{opp['projected_ppg_increase']:.1f} PTS")
                print(f"    Confidence: {opp['confidence_score']:.0f}%\n")

        return len(opportunities)

    def run_full_update(self):
        """
        Run complete injury data update
        """
        print(f"\n{'='*70}")
        print("NBA INJURY DATA UPDATE")
        print(f"{'='*70}\n")

        # Create tables
        self.create_injuries_table()

        # Try all sources
        injuries = []

        # 1. Try BallDontLie (will fail for now)
        bdl_injuries = self.fetch_injuries_from_balldontlie()
        injuries.extend(bdl_injuries)

        # 2. Try ESPN
        espn_injuries = self.fetch_injuries_from_espn()
        injuries.extend(espn_injuries)

        # 3. Try NBA.com (if still need more)
        if len(injuries) < 10:
            nba_injuries = self.fetch_injuries_from_nba_dot_com()
            injuries.extend(nba_injuries)

        # Save to database
        saved = self.save_injuries_to_db(injuries)

        # Identify cascade opportunities
        opportunities = self.identify_cascade_opportunities()

        # Summary
        print(f"{'='*70}")
        print("INJURY UPDATE COMPLETE")
        print(f"{'='*70}")
        print(f"Injuries tracked: {saved}")
        print(f"Cascade opportunities: {opportunities}")
        print(f"Database: {self.db_path}")
        print(f"{'='*70}\n")

        return {
            'injuries': saved,
            'opportunities': opportunities
        }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Fetch NBA injury data')
    parser.add_argument('--db-path', type=str, default='D:/backend/data/player_props.db',
                       help='Path to player props database')

    args = parser.parse_args()

    fetcher = InjuryDataFetcher(db_path=args.db_path)
    result = fetcher.run_full_update()

    if result['injuries'] > 0:
        print(f"[SUCCESS] Tracked {result['injuries']} injuries!")
        print(f"[SUCCESS] Found {result['opportunities']} cascade betting opportunities!")
        print(f"\nNow you can:")
        print(f"1. Auto-adjust props for players getting more minutes")
        print(f"2. Generate alerts for high-value cascade bets")
        print(f"3. Track injury impact on team dynamics")
    else:
        print(f"[WARN] No injury data was collected")


if __name__ == "__main__":
    main()
