#!/usr/bin/env python3
"""
Add Historical Market Lines to Training Data
Joins odds from historical databases with training data
"""
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging

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

def add_odds_columns_to_table(conn, table_name):
    """Add market line columns to training table"""
    columns_to_add = [
        ('market_total', 'REAL'),
        ('market_spread', 'REAL'),  # home team spread
        ('market_home_ml', 'INTEGER'),  # American odds
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

def get_closing_odds_for_game(odds_dbs, sport_key, home_team, away_team, game_date):
    """Get closing odds (closest to game time) for a specific game"""

    # Find the right odds database for this date
    target_date = pd.to_datetime(game_date).date()

    best_odds = {
        'total': None,
        'spread': None,
        'home_ml': None,
        'away_ml': None,
        'over_odds': -110,
        'under_odds': -110,
        'spread_odds': -110
    }

    for db_path in odds_dbs:
        try:
            conn = sqlite3.connect(db_path)

            # Query pregame odds for this game
            query = """
                SELECT total_line, home_line, home_odds, away_odds, over_odds, under_odds,
                       hours_before_game, bookmaker
                FROM game_odds_pregame
                WHERE sport = ? AND home_team = ? AND away_team = ?
                  AND game_date = ?
                ORDER BY hours_before_game ASC
                LIMIT 10
            """

            df = pd.read_sql(query, conn, params=(sport_key, home_team, away_team, str(target_date)))
            conn.close()

            if len(df) > 0:
                # Use the closest to game time (smallest hours_before_game)
                closest_row = df.iloc[0]

                if pd.notna(closest_row['total_line']):
                    best_odds['total'] = closest_row['total_line']
                    best_odds['over_odds'] = closest_row['over_odds'] if pd.notna(closest_row['over_odds']) else -110
                    best_odds['under_odds'] = closest_row['under_odds'] if pd.notna(closest_row['under_odds']) else -110

                if pd.notna(closest_row['home_line']):
                    best_odds['spread'] = closest_row['home_line']
                    best_odds['spread_odds'] = -110  # Default

                if pd.notna(closest_row['home_odds']):
                    best_odds['home_ml'] = int(closest_row['home_odds'])
                if pd.notna(closest_row['away_odds']):
                    best_odds['away_ml'] = int(closest_row['away_odds'])

                break  # Found odds, stop searching

        except Exception as e:
            continue

    return best_odds

def enrich_training_data(sport):
    """Add market lines to training data for a sport"""
    logger.info(f'\n{"="*80}')
    logger.info(f'ENRICHING {sport.upper()} TRAINING DATA WITH MARKET LINES')
    logger.info(f'{"="*80}')

    # Connect to training database
    conn = sqlite3.connect(TRAINING_DB)
    table_name = f'{sport}_training_data'

    # Add columns if they don't exist
    add_odds_columns_to_table(conn, table_name)

    # Load training data
    df = pd.read_sql(f'SELECT * FROM {table_name}', conn)
    logger.info(f'Loaded {len(df):,} training records')

    # Get all odds databases
    odds_dbs = sorted(ODDS_ARCHIVE.glob('odds_history_*.db'))
    logger.info(f'Found {len(odds_dbs)} historical odds databases')

    sport_key = SPORT_MAPPING.get(sport)
    if not sport_key:
        logger.error(f'Unknown sport: {sport}')
        return

    # Process each game
    matched = 0
    for idx, row in df.iterrows():
        if idx % 500 == 0:
            logger.info(f'  Processing game {idx+1}/{len(df)}...')

        odds = get_closing_odds_for_game(
            odds_dbs,
            sport_key,
            row['home_team'],
            row['away_team'],
            row['game_date']
        )

        has_data = 0
        if odds['total'] or odds['spread'] or odds['home_ml']:
            has_data = 1
            matched += 1

        # Update the row
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE {table_name}
            SET market_total = ?,
                market_spread = ?,
                market_home_ml = ?,
                market_away_ml = ?,
                over_odds = ?,
                under_odds = ?,
                spread_odds = ?,
                has_market_data = ?
            WHERE rowid = ?
        """, (
            odds['total'],
            odds['spread'],
            odds['home_ml'],
            odds['away_ml'],
            odds['over_odds'],
            odds['under_odds'],
            odds['spread_odds'],
            has_data,
            row.name + 1  # SQLite rowid is 1-indexed
        ))

    conn.commit()
    logger.info(f'✓ Matched {matched}/{len(df)} games ({matched/len(df)*100:.1f}%)')

    # Show sample
    df_updated = pd.read_sql(f'SELECT * FROM {table_name} WHERE has_market_data = 1 LIMIT 3', conn)
    if len(df_updated) > 0:
        logger.info(f'\nSample enriched data:')
        for _, row in df_updated.iterrows():
            logger.info(f'  {row["away_team"]} @ {row["home_team"]}: Total={row["market_total"]}, Spread={row["market_spread"]}, ML={row["market_home_ml"]}/{row["market_away_ml"]}')

    conn.close()

def main():
    logger.info('\n' + '='*80)
    logger.info('ADDING HISTORICAL MARKET LINES TO TRAINING DATA')
    logger.info('='*80)

    sports = ['nba', 'ncaab', 'nhl', 'nfl', 'ncaaf']

    for sport in sports:
        try:
            enrich_training_data(sport)
        except Exception as e:
            logger.error(f'Error processing {sport}: {e}', exc_info=True)

    logger.info('\n' + '='*80)
    logger.info('ENRICHMENT COMPLETE')
    logger.info('='*80)

if __name__ == '__main__':
    main()
