"""
Data Feed Routes — line movement history and injury log
GET /api/line-movement/{game_id}  — snapshots for a specific game
GET /api/line-movement            — latest snapshot for all active games
GET /api/injuries                 — injury log, filterable by sport/status/team
"""
import os, logging
from fastapi import APIRouter, Query
from typing import Optional
import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)
router = APIRouter()

DB_URL = os.getenv('DATABASE_URL', 'postgresql://maxev:maxev_sports@localhost:5432/maxev_sports')

def get_conn():
    return psycopg2.connect(DB_URL)


@router.get('/api/line-movement/{game_id}')
def line_movement_history(game_id: str):
    """Return all snapshots for a game to show how lines moved."""
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT game_id, sport, home_team, away_team, game_time,
                   spread_home, total_line, home_ml, away_ml,
                   books_sampled, snapshot_label, snapshot_at
            FROM line_snapshots
            WHERE game_id = %s
            ORDER BY snapshot_at ASC
        """, (game_id,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        if not rows:
            return {'game_id': game_id, 'snapshots': [], 'movement': {}}

        first = rows[0]
        last  = rows[-1]
        movement = {}
        for field in ('spread_home', 'total_line', 'home_ml', 'away_ml'):
            v0, v1 = first.get(field), last.get(field)
            if v0 is not None and v1 is not None and v0 != v1:
                movement[field] = {'open': v0, 'current': v1, 'delta': round(v1 - v0, 1)}

        return {'game_id': game_id, 'snapshots': rows, 'movement': movement}

    except Exception as e:
        logger.error(f'line-movement error: {e}')
        return {'error': str(e), 'snapshots': []}


@router.get('/api/line-movement')
def line_movement_latest(sport: Optional[str] = Query(None)):
    """Return most recent snapshot for all games (or filtered by sport)."""
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if sport:
            cur.execute("""
                SELECT DISTINCT ON (game_id)
                    game_id, sport, home_team, away_team, game_time,
                    spread_home, total_line, home_ml, away_ml,
                    books_sampled, snapshot_label, snapshot_at
                FROM line_snapshots WHERE sport = %s
                ORDER BY game_id, snapshot_at DESC
            """, (sport,))
        else:
            cur.execute("""
                SELECT DISTINCT ON (game_id)
                    game_id, sport, home_team, away_team, game_time,
                    spread_home, total_line, home_ml, away_ml,
                    books_sampled, snapshot_label, snapshot_at
                FROM line_snapshots
                ORDER BY game_id, snapshot_at DESC
            """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {'games': rows, 'count': len(rows)}
    except Exception as e:
        logger.error(f'line-movement-latest error: {e}')
        return {'error': str(e), 'games': []}


@router.get('/api/injuries')
def get_injuries(
    sport:  Optional[str] = Query(None, description='Filter by sport: nfl, mlb, nba, wnba'),
    status: Optional[str] = Query(None, description='Filter by status: Out, Doubtful, Questionable'),
    team:   Optional[str] = Query(None, description='Filter by team abbreviation'),
):
    """Return current injury log, optionally filtered."""
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        conditions, params = [], []
        if sport:
            conditions.append('sport = %s')
            params.append(sport.lower())
        if status:
            conditions.append('LOWER(status) = LOWER(%s)')
            params.append(status)
        if team:
            conditions.append('LOWER(team_abbr) = LOWER(%s)')
            params.append(team)

        where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''
        cur.execute(f"""
            SELECT player_id, player_name, team, team_abbr, sport,
                   status, injury_type, description, fetched_at
            FROM injury_log
            {where}
            ORDER BY sport, team, player_name
        """, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {'injuries': rows, 'count': len(rows)}
    except Exception as e:
        logger.error(f'injuries error: {e}')
        return {'error': str(e), 'injuries': []}
