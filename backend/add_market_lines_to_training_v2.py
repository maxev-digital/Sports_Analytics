#!/usr/bin/env python3
"""
Add Historical Market Lines to Training Data - V2
Handles UTC to CST conversion and team name mapping
"""
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
from fuzzywuzzy import fuzz

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

BACKEND_PATH = Path('/root/sporttrader/backend')
TRAINING_DB = BACKEND_PATH / 'ml' / 'predictions.db'
ODDS_ARCHIVE = Path('/root/sporttrader/backups/odds_archive/daily')

# Sport key mappings
SPORT_MAPPING = {
    'nba': 'basketball_nba',
    'ncaab': 'basketball_ncaab',
    'nhl': 'icehockey_nhl',
    'nfl': 'americanfootball_nfl',
    'ncaaf': 'americanfootball_ncaaf'
}

# NBA team abbreviation to full name mapping
NBA_TEAM_MAP = {
    'ATL': 'Atlanta Hawks', 'BOS': 'Boston Celtics', 'BKN': 'Brooklyn Nets',
    'CHA': 'Charlotte Hornets', 'CHI': 'Chicago Bulls', 'CLE': 'Cleveland Cavaliers',
    'DAL': 'Dallas Mavericks', 'DEN': 'Denver Nuggets', 'DET': 'Detroit Pistons',
    'GSW': 'Golden State Warriors', 'HOU': 'Houston Rockets', 'IND': 'Indiana Pacers',
    'LAC': 'Los Angeles Clippers', 'LAL': 'Los Angeles Lakers', 'MEM': 'Memphis Grizzlies',
    'MIA': 'Miami Heat', 'MIL': 'Milwaukee Bucks', 'MIN': 'Minnesota Timberwolves',
    'NOP': 'New Orleans Pelicans', 'NYK': 'New York Knicks', 'OKC': 'Oklahoma City Thunder',
    'ORL': 'Orlando Magic', 'PHI': 'Philadelphia 76ers', 'PHX': 'Phoenix Suns',
    'POR': 'Portland Trail Blazers', 'SAC': 'Sacramento Kings', 'SAS': 'San Antonio Spurs',
    'TOR': 'Toronto Raptors', 'UTA': 'Utah Jazz', 'WAS': 'Washington Wizards'
}

def convert_utc_to_cst_date(utc_date_str):
    """Convert UTC date to CST date (games after 6am UTC are next day in CST)"""
    try:
        # Parse the date string
        if isinstance(utc_date_str, str):
            utc_date = pd.to_datetime(utc_date_str)
        else:
            utc_date = utc_date_str

        # Subtract 6 hours to convert UTC to CST
        cst_date = utc_date - timedelta(hours=6)
        return cst_date.date()
    except:
        return None

def fuzzy_match_team(team_abbr, odds_teams, threshold=60):
    """Fuzzy match team abbreviation to full name"""
    # Try direct mapping first
    if team_abbr in NBA_TEAM_MAP:
        return NBA_TEAM_MAP[team_abbr]

    # Fuzzy match as fallback
    best_match = None
    best_score = 0

    for odds_team in odds_teams:
        score = fuzz.partial_ratio(team_abbr.upper(), odds_team.upper())
        if score > best_score and score >= threshold:
            best_score = score
            best_match = odds_team

    return best_match

def add_odds_columns_to_table(conn, table_name):
    """Add market line columns to training table"""
    columns_to_add = [
        ('market_total', 'REAL'),
        ('market_spread', 'REAL'),
        ('market_home_ml', 'INTEGER'),
        ('market_away_ml', 'INTEGER'),
        ('over_odds', 'INTEGER'),
        ('under_odds', 'INTEGER'),
        ('spread_odds', 'INTEGER'),
        ('has_market_data', 'INTEGER DEFAULT 0')
    ]

    cursor = conn.cursor()
    existing_cols = [row[1] for row in cursor.execute(f'PRAGMA table_info({table_name})').fetchall()]

    for col_name, col_type in columns_to_add:
        if col_name not in existing_cols:
            logger.info(f"  Adding column {col_name} to {table_name}")
            cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}')

    conn.commit()

def get_all_odds_teams(odds_dbs, sport_key):
    """Get all unique team names from odds databases for fuzzy matching"""
    teams = set()
    for db_path in odds_dbs[:1]:  # Just check first db
        try:
            conn = sqlite3.connect(db_path)
            df = pd.read_sql(f"SELECT DISTINCT home_team, away_team FROM game_odds_pregame WHERE sport = ? LIMIT 100",
                           conn, params=(sport_key,))
            teams.update(df['home_team'].tolist())
            teams.update(df['away_team'].tolist())
            conn.close()
            break
        except:
            continue
    return list(teams)

def get_closing_odds_for_game(odds_dbs, sport_key, home_team, away_team, game_date_obj):
    """Get closing odds with UTC to CST date handling"""

    # Try current date and +1 day (to handle timezone edge cases)
    dates_to_try = [
        game_date_obj,
        game_date_obj + timedelta(days=1),
        game_date_obj - timedelta(days=1)
    ]

    best_odds = {
        'total': None, 'spread': None, 'home_ml': None, 'away_ml': None,
        'over_odds': -110, 'under_odds': -110, 'spread_odds': -110
    }

    for db_path in odds_dbs:
        for date_to_try in dates_to_try:
            try:
                conn = sqlite3.connect(db_path)

                query = """
                    SELECT total_line, home_line, home_odds, away_odds, over_odds, under_odds,
                           hours_before_game, bookmaker, game_date
                    FROM game_odds_pregame
                    WHERE sport = ? AND home_team = ? AND away_team = ?
                      AND game_date = ?
                    ORDER BY hours_before_game ASC
                    LIMIT 5
                """

                df = pd.read_sql(query, conn, params=(sport_key, home_team, away_team, str(date_to_try)))
                conn.close()

                if len(df) > 0:
                    closest_row = df.iloc[0]

                    if pd.notna(closest_row['total_line']):
                        best_odds['total'] = closest_row['total_line']
                        best_odds['over_odds'] = closest_row['over_odds'] if pd.notna(closest_row['over_odds']) else -110
                        best_odds['under_odds'] = closest_row['under_odds'] if pd.notna(closest_row['under_odds']) else -110

                    if pd.notna(closest_row['home_line']):
                        best_odds['spread'] = closest_row['home_line']

                    if pd.notna(closest_row['home_odds']):
                        best_odds['home_ml'] = int(closest_row['home_odds'])
                    if pd.notna(closest_row['away_odds']):
                        best_odds['away_ml'] = int(closest_row['away_odds'])

                    return best_odds  # Found it!

            except Exception as e:
                continue

    return best_odds

def enrich_nba_training_data():
    """Special handling for NBA with abbreviations"""
    logger.info(f'\n{"="*80}')
    logger.info(f'ENRICHING NBA TRAINING DATA WITH MARKET LINES')
    logger.info(f'{"="*80}')

    conn = sqlite3.connect(TRAINING_DB)
    table_name = 'nba_training_data'

    add_odds_columns_to_table(conn, table_name)

    # Load training data
    df = pd.read_sql(f'SELECT rowid, * FROM {table_name}', conn)
    logger.info(f'Loaded {len(df):,} training records')

    odds_dbs = sorted(ODDS_ARCHIVE.glob('odds_history_*.db'))
    logger.info(f'Found {len(odds_dbs)} historical odds databases')

    # Get all odds teams for fuzzy matching
    odds_teams = get_all_odds_teams(odds_dbs, 'basketball_nba')
    logger.info(f'Found {len(odds_teams)} unique teams in odds data')

    matched = 0
    for idx, row in df.iterrows():
        if idx % 500 == 0:
            logger.info(f'  Processing game {idx+1}/{len(df)}...')

        # Convert team abbreviations to full names
        home_full = fuzzy_match_team(row['home_team'], odds_teams) if pd.notna(row['home_team']) else None
        away_full = fuzzy_match_team(row['away_team'], odds_teams) if pd.notna(row['away_team']) else None

        if not home_full or not away_full:
            continue

        # Parse date from season (e.g., "2022-23" -> use game_date if exists, else skip)
        game_date = None
        if 'game_date' in row and pd.notna(row['game_date']):
            game_date = pd.to_datetime(row['game_date']).date()

        if not game_date:
            continue

        odds = get_closing_odds_for_game(odds_dbs, 'basketball_nba', home_full, away_full, game_date)

        has_data = 0
        if odds['total'] or odds['spread'] or odds['home_ml']:
            has_data = 1
            matched += 1

        # Update
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE {table_name}
            SET market_total = ?, market_spread = ?, market_home_ml = ?, market_away_ml = ?,
                over_odds = ?, under_odds = ?, spread_odds = ?, has_market_data = ?
            WHERE rowid = ?
        """, (odds['total'], odds['spread'], odds['home_ml'], odds['away_ml'],
              odds['over_odds'], odds['under_odds'], odds['spread_odds'], has_data, row['rowid']))

    conn.commit()
    logger.info(f'✓ Matched {matched}/{len(df)} games ({matched/len(df)*100:.1f}%)')

    # Show sample
    df_updated = pd.read_sql(f'SELECT * FROM {table_name} WHERE has_market_data = 1 LIMIT 3', conn)
    if len(df_updated) > 0:
        logger.info(f'\nSample enriched data:')
        for _, r in df_updated.iterrows():
            logger.info(f'  {r["away_team"]} @ {r["home_team"]}: Total={r["market_total"]}, Spread={r["market_spread"]}, ML={r["market_home_ml"]}/{r["market_away_ml"]}')

    conn.close()

def main():
    logger.info('\n' + '='*80)
    logger.info('ADDING HISTORICAL MARKET LINES - V2 (UTC->CST + Team Mapping)')
    logger.info('='*80)

    # Start with NBA only for now
    try:
        enrich_nba_training_data()
    except Exception as e:
        logger.error(f'Error processing NBA: {e}', exc_info=True)

    logger.info('\n' + '='*80)
    logger.info('ENRICHMENT COMPLETE')
    logger.info('='*80)

if __name__ == '__main__':
    main()
