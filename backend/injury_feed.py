"""
Injury Feed
Pulls NFL/MLB/NBA/WNBA injury reports from ESPN public API.
Upserts into injury_log table. Run daily via nightly pipeline.
"""
import os, re, logging
import psycopg2
import requests
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

DB_URL = os.getenv('DATABASE_URL', 'postgresql://maxev:maxev_sports@localhost:5432/maxev_sports')

SPORT_ENDPOINTS = {
    'nfl':  'https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries',
    'mlb':  'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/injuries',
    'nba':  'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries',
    'wnba': 'https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/injuries',
}

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS injury_log (
    id          SERIAL PRIMARY KEY,
    player_id   VARCHAR(50),
    player_name VARCHAR(150) NOT NULL,
    team        VARCHAR(100),
    team_abbr   VARCHAR(10),
    sport       VARCHAR(20) NOT NULL,
    status      VARCHAR(30),
    injury_type VARCHAR(100),
    description TEXT,
    fetched_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (player_id, sport)
);
CREATE INDEX IF NOT EXISTS idx_injury_sport  ON injury_log(sport);
CREATE INDEX IF NOT EXISTS idx_injury_status ON injury_log(status);
CREATE INDEX IF NOT EXISTS idx_injury_team   ON injury_log(team_abbr, sport);
"""

def extract_player_id(athlete: dict) -> str:
    for link in athlete.get('links', []):
        href = link.get('href', '')
        m = re.search(r'/id/(\d+)/', href)
        if m:
            return m.group(1)
    return ''

def fetch_injuries(sport: str, url: str) -> list:
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'MaxEV-Sports/1.0'})
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.error(f'[{sport}] ESPN injury fetch failed: {e}')
        return []

    rows = []
    for team_block in data.get('injuries', []):
        team_info = {'displayName': team_block.get('displayName',''), 'abbreviation': team_block.get('id','')}
        # Some blocks nest team separately
        if 'team' in team_block:
            team_info = team_block['team']

        for injury in team_block.get('injuries', []):
            athlete = injury.get('athlete', {})
            player_name = athlete.get('displayName', '')
            if not player_name:
                continue
            player_id = extract_player_id(athlete)

            rows.append({
                'player_id':   player_id,
                'player_name': player_name,
                'team':        team_info.get('displayName', ''),
                'team_abbr':   team_info.get('abbreviation', ''),
                'sport':       sport,
                'status':      injury.get('status', ''),
                'injury_type': injury.get('type', {}).get('description', '') if isinstance(injury.get('type'), dict) else '',
                'description': (injury.get('shortComment', '') or '')[:500],
            })
    return rows

def run():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)

    total = 0
    for sport, url in SPORT_ENDPOINTS.items():
        rows = fetch_injuries(sport, url)
        if not rows:
            logger.info(f'[{sport}] 0 players returned')
            continue
        for row in rows:
            if not row['player_name']:
                continue
            # Use player_id if found, else player_name+sport as fallback key
            pid = row['player_id'] or (row['player_name'].lower().replace(' ','_') + '_' + sport)
            cur.execute("""
                INSERT INTO injury_log
                    (player_id, player_name, team, team_abbr, sport,
                     status, injury_type, description, fetched_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                ON CONFLICT (player_id, sport) DO UPDATE SET
                    player_name  = EXCLUDED.player_name,
                    team         = EXCLUDED.team,
                    team_abbr    = EXCLUDED.team_abbr,
                    status       = EXCLUDED.status,
                    injury_type  = EXCLUDED.injury_type,
                    description  = EXCLUDED.description,
                    fetched_at   = NOW()
            """, (pid, row['player_name'], row['team'], row['team_abbr'],
                   row['sport'], row['status'], row['injury_type'], row['description']))
            total += 1
        logger.info(f'[{sport}] {len(rows)} players processed')

    logger.info(f'Injury feed complete — {total} total records upserted')
    conn.close()

if __name__ == '__main__':
    run()
