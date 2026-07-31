"""
Line Movement Tracker
Snapshots current consensus odds for all active games 3x daily.
Captures how spreads/totals/ML move from opening to close.
Run via: python3 line_movement_tracker.py
Scheduled: 8am, 2pm, 6pm UTC via cron (alongside nightly pipeline)
"""

import os
import sys
import logging
import psycopg2
import psycopg2.extras
import requests
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

DB_URL = os.getenv('DATABASE_URL', 'postgresql://maxev:maxev_sports@localhost:5432/maxev_sports')
API_BASE = 'http://127.0.0.1:8000'

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS line_snapshots (
    id          SERIAL PRIMARY KEY,
    game_id     VARCHAR NOT NULL,
    sport       VARCHAR(30) NOT NULL,
    home_team   VARCHAR(100),
    away_team   VARCHAR(100),
    game_time   TIMESTAMPTZ,
    spread_home FLOAT,
    total_line  FLOAT,
    home_ml     INT,
    away_ml     INT,
    books_sampled INT,
    snapshot_label VARCHAR(20),
    snapshot_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_line_snap_game  ON line_snapshots(game_id, snapshot_at DESC);
CREATE INDEX IF NOT EXISTS idx_line_snap_sport ON line_snapshots(sport, snapshot_at DESC);
"""

def get_snapshot_label() -> str:
    hour = datetime.now(timezone.utc).hour
    if hour < 12:
        return 'morning'
    elif hour < 17:
        return 'midday'
    elif hour < 22:
        return 'evening'
    return 'overnight'

def fetch_games():
    try:
        r = requests.get(f'{API_BASE}/api/games?user_id=default', timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f'Failed to fetch games: {e}')
        return []

def extract_consensus(game: dict) -> dict | None:
    """Pull best consensus spread/total/ML from the game's odds array."""
    odds_list = game.get('odds', [])
    if not odds_list:
        return None

    state = game.get('state', {})

    spreads, totals, home_mls, away_mls = [], [], [], []
    for o in odds_list:
        if o.get('home_spread') is not None:
            spreads.append(o['home_spread'])
        if o.get('total') is not None:
            totals.append(o['total'])
        if o.get('home_ml') is not None:
            home_mls.append(o['home_ml'])
        if o.get('away_ml') is not None:
            away_mls.append(o['away_ml'])

    def median(lst):
        if not lst:
            return None
        s = sorted(lst)
        n = len(s)
        return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2

    return {
        'game_id':      state.get('id', ''),
        'sport':        state.get('sport_key', ''),
        'home_team':    state.get('home_team', {}).get('name') if isinstance(state.get('home_team'), dict) else state.get('home_team', ''),
        'away_team':    state.get('away_team', {}).get('name') if isinstance(state.get('away_team'), dict) else state.get('away_team', ''),
        'game_time':    state.get('commence_time'),
        'spread_home':  median(spreads),
        'total_line':   median(totals),
        'home_ml':      int(median(home_mls)) if home_mls else None,
        'away_ml':      int(median(away_mls)) if away_mls else None,
        'books_sampled': len(odds_list),
    }

def run():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()

    # Ensure table exists
    cur.execute(CREATE_TABLE_SQL)

    games = fetch_games()
    if not games:
        logger.warning('No games returned — nothing to snapshot')
        conn.close()
        return

    label = get_snapshot_label()
    inserted = 0

    for game in games:
        row = extract_consensus(game)
        if not row or not row['game_id']:
            continue

        cur.execute("""
            INSERT INTO line_snapshots
                (game_id, sport, home_team, away_team, game_time,
                 spread_home, total_line, home_ml, away_ml, books_sampled, snapshot_label)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            row['game_id'], row['sport'], row['home_team'], row['away_team'],
            row['game_time'], row['spread_home'], row['total_line'],
            row['home_ml'], row['away_ml'], row['books_sampled'], label
        ))
        inserted += 1

    logger.info(f'Line snapshot complete — {inserted} games logged (label={label})')
    conn.close()

if __name__ == '__main__':
    run()
