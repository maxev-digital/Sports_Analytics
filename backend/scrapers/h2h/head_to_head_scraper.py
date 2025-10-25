"""
Head-to-Head Historical Data Scraper
Scrapes H2H matchup history from multiple sources (ESPN, NBA.com, Covers.com)
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os


class HeadToHeadScraper:
    """
    Scraper for historical head-to-head matchup data

    Data Sources:
    1. ESPN - Good for NBA, NFL, NHL, MLB
    2. Basketball-Reference - Best for detailed NBA history
    3. Hockey-Reference - Best for NHL history
    4. Covers.com - Good for betting trends and ATS records
    """

    def __init__(self, data_dir: str = "C:/Users/nashr/backend/data/historical/h2h"):
        """
        Initialize H2H scraper

        Args:
            data_dir: Directory to store H2H data
        """
        self.data_dir = data_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_nba_h2h_espn(
        self,
        team1_id: str,
        team2_id: str,
        seasons: int = 5
    ) -> List[Dict]:
        """
        Get NBA head-to-head history from ESPN

        Args:
            team1_id: ESPN team ID (e.g., 'lal' for Lakers)
            team2_id: ESPN team ID
            seasons: Number of past seasons to fetch

        Returns:
            List of game dictionaries
        """
        games = []
        current_year = datetime.now().year

        for season_offset in range(seasons):
            season_year = current_year - season_offset

            try:
                # ESPN schedule endpoint
                url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team1_id}/schedule"
                params = {
                    'season': season_year
                }

                response = self.session.get(url, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()

                    # Parse games
                    events = data.get('events', [])

                    for event in events:
                        competitions = event.get('competitions', [])

                        for comp in competitions:
                            competitors = comp.get('competitors', [])

                            # Check if this game involves team2
                            team_names = [c.get('team', {}).get('abbreviation', '') for c in competitors]

                            if team2_id.upper() in [t.upper() for t in team_names]:
                                # This is a H2H game
                                game_date = event.get('date', '')
                                game_status = comp.get('status', {}).get('type', {}).get('completed', False)

                                if game_status:  # Only completed games
                                    home_team = None
                                    away_team = None
                                    home_score = 0
                                    away_score = 0

                                    for competitor in competitors:
                                        team_abbr = competitor.get('team', {}).get('abbreviation', '')
                                        score = int(competitor.get('score', 0))
                                        is_home = competitor.get('homeAway', '') == 'home'

                                        if is_home:
                                            home_team = team_abbr
                                            home_score = score
                                        else:
                                            away_team = team_abbr
                                            away_score = score

                                    game = {
                                        'date': game_date[:10],  # YYYY-MM-DD
                                        'season': season_year,
                                        'home_team': home_team,
                                        'away_team': away_team,
                                        'home_score': home_score,
                                        'away_score': away_score,
                                        'total': home_score + away_score,
                                        'spread': home_score - away_score,
                                        'playoff': event.get('season', {}).get('type', 1) > 2
                                    }

                                    games.append(game)

                # Rate limiting
                time.sleep(0.5)

            except Exception as e:
                print(f"Error fetching season {season_year}: {str(e)}")
                continue

        return games

    def get_nhl_h2h_espn(
        self,
        team1_id: str,
        team2_id: str,
        seasons: int = 3
    ) -> List[Dict]:
        """
        Get NHL head-to-head history from ESPN

        Args:
            team1_id: ESPN team ID (e.g., 'tor' for Maple Leafs)
            team2_id: ESPN team ID
            seasons: Number of past seasons to fetch

        Returns:
            List of game dictionaries
        """
        games = []
        current_year = datetime.now().year

        for season_offset in range(seasons):
            # NHL seasons span two years (e.g., 2023-2024)
            season_start_year = current_year - season_offset

            try:
                url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/{team1_id}/schedule"
                params = {
                    'season': season_start_year
                }

                response = self.session.get(url, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    events = data.get('events', [])

                    for event in events:
                        competitions = event.get('competitions', [])

                        for comp in competitions:
                            competitors = comp.get('competitors', [])
                            team_names = [c.get('team', {}).get('abbreviation', '') for c in competitors]

                            if team2_id.upper() in [t.upper() for t in team_names]:
                                game_status = comp.get('status', {}).get('type', {}).get('completed', False)

                                if game_status:
                                    home_team = None
                                    away_team = None
                                    home_score = 0
                                    away_score = 0

                                    for competitor in competitors:
                                        team_abbr = competitor.get('team', {}).get('abbreviation', '')
                                        score = int(competitor.get('score', 0))
                                        is_home = competitor.get('homeAway', '') == 'home'

                                        if is_home:
                                            home_team = team_abbr
                                            home_score = score
                                        else:
                                            away_team = team_abbr
                                            away_score = score

                                    game = {
                                        'date': event.get('date', '')[:10],
                                        'season': f"{season_start_year}-{season_start_year+1}",
                                        'home_team': home_team,
                                        'away_team': away_team,
                                        'home_score': home_score,
                                        'away_score': away_score,
                                        'total': home_score + away_score,
                                        'spread': home_score - away_score,
                                        'playoff': event.get('season', {}).get('type', 1) > 2
                                    }

                                    games.append(game)

                time.sleep(0.5)

            except Exception as e:
                print(f"Error fetching NHL season {season_start_year}: {str(e)}")
                continue

        return games

    def save_h2h_data(
        self,
        sport: str,
        team1: str,
        team2: str,
        games: List[Dict]
    ) -> str:
        """
        Save H2H data to JSON file

        Args:
            sport: Sport name (nba, nhl, nfl, mlb)
            team1: First team abbreviation
            team2: Second team abbreviation
            games: List of game dictionaries

        Returns:
            Path to saved file
        """
        # Create sport directory if needed
        sport_dir = os.path.join(self.data_dir, sport.lower())
        os.makedirs(sport_dir, exist_ok=True)

        # Create filename (alphabetically ordered teams for consistency)
        teams_sorted = sorted([team1.lower(), team2.lower()])
        filename = f"{teams_sorted[0]}_vs_{teams_sorted[1]}.json"
        filepath = os.path.join(sport_dir, filename)

        # Sort games by date (most recent first)
        games_sorted = sorted(games, key=lambda x: x.get('date', ''), reverse=True)

        # Save data
        data = {
            'sport': sport,
            'team1': team1,
            'team2': team2,
            'last_updated': datetime.now().isoformat(),
            'total_games': len(games_sorted),
            'games': games_sorted
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Saved {len(games_sorted)} games to {filepath}")

        return filepath

    def load_h2h_data(
        self,
        sport: str,
        team1: str,
        team2: str
    ) -> Optional[Dict]:
        """
        Load H2H data from file

        Args:
            sport: Sport name
            team1: First team abbreviation
            team2: Second team abbreviation

        Returns:
            H2H data dictionary or None if not found
        """
        sport_dir = os.path.join(self.data_dir, sport.lower())
        teams_sorted = sorted([team1.lower(), team2.lower()])
        filename = f"{teams_sorted[0]}_vs_{teams_sorted[1]}.json"
        filepath = os.path.join(sport_dir, filename)

        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)

        return None

    def scrape_and_save_matchup(
        self,
        sport: str,
        team1_id: str,
        team2_id: str,
        seasons: int = 5,
        force_refresh: bool = False
    ) -> Dict:
        """
        Scrape H2H data and save to file (with caching)

        Args:
            sport: Sport name (nba, nhl)
            team1_id: First team ID
            team2_id: Second team ID
            seasons: Number of seasons to fetch
            force_refresh: Force re-scraping even if data exists

        Returns:
            H2H data dictionary
        """
        # Check if data already exists
        if not force_refresh:
            existing_data = self.load_h2h_data(sport, team1_id, team2_id)
            if existing_data:
                last_updated = datetime.fromisoformat(existing_data['last_updated'])
                age_days = (datetime.now() - last_updated).days

                if age_days < 7:  # Data less than 7 days old
                    print(f"Using cached data ({age_days} days old)")
                    return existing_data

        # Scrape fresh data
        print(f"Scraping {sport.upper()} H2H: {team1_id} vs {team2_id}")

        if sport.lower() == 'nba':
            games = self.get_nba_h2h_espn(team1_id, team2_id, seasons)
        elif sport.lower() == 'nhl':
            games = self.get_nhl_h2h_espn(team1_id, team2_id, seasons)
        else:
            raise ValueError(f"Sport '{sport}' not supported yet")

        # Save to file
        if games:
            self.save_h2h_data(sport, team1_id, team2_id, games)
            return self.load_h2h_data(sport, team1_id, team2_id)
        else:
            print(f"No games found for {team1_id} vs {team2_id}")
            return {'games': []}


# Example usage
if __name__ == "__main__":
    scraper = HeadToHeadScraper()

    # Example 1: NBA - Lakers vs Celtics
    print("="*70)
    print("Scraping NBA: Lakers vs Celtics")
    print("="*70)

    lakers_celtics = scraper.scrape_and_save_matchup(
        sport='nba',
        team1_id='lal',  # Lakers
        team2_id='bos',  # Celtics
        seasons=3
    )

    if lakers_celtics and lakers_celtics.get('games'):
        print(f"\nFound {len(lakers_celtics['games'])} games")
        print("\nLast 3 meetings:")
        for game in lakers_celtics['games'][:3]:
            print(f"  {game['date']}: {game['away_team']} @ {game['home_team']} - "
                  f"{game['away_score']}-{game['home_score']} (Total: {game['total']})")

    print("\n" + "="*70)
    print("Scraping NHL: Maple Leafs vs Bruins")
    print("="*70)

    # Example 2: NHL - Maple Leafs vs Bruins (fierce rivalry)
    leafs_bruins = scraper.scrape_and_save_matchup(
        sport='nhl',
        team1_id='tor',  # Maple Leafs
        team2_id='bos',  # Bruins
        seasons=3
    )

    if leafs_bruins and leafs_bruins.get('games'):
        print(f"\nFound {len(leafs_bruins['games'])} games")
        print("\nLast 3 meetings:")
        for game in leafs_bruins['games'][:3]:
            print(f"  {game['date']}: {game['away_team']} @ {game['home_team']} - "
                  f"{game['away_score']}-{game['home_score']} (Total: {game['total']})")

    print("\n" + "="*70)
    print("Data Storage Locations:")
    print("="*70)
    print(f"NBA H2H: C:/Users/nashr/backend/data/historical/h2h/nba/")
    print(f"NHL H2H: C:/Users/nashr/backend/data/historical/h2h/nhl/")
    print(f"Format: teamA_vs_teamB.json (alphabetically sorted)")
