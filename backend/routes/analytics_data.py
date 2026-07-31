"""
Analytics Data Routes
Free data sources: ESPN (all sports), Baseball Savant/Statcast (MLB),
NBA.com stats API, BartTorvik T-Rank (NCAAB)
No paid API keys required.
"""
from fastapi import APIRouter, HTTPException, Query
import httpx
import csv
import io
import time
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics-data", tags=["analytics-data"])

# ── Simple in-process TTL cache ────────────────────────────────────────────
_cache: Dict[str, tuple] = {}

def _get_cache(key: str) -> Optional[Any]:
    entry = _cache.get(key)
    if entry and time.time() < entry[1]:
        return entry[0]
    return None

def _set_cache(key: str, data: Any, ttl: int = 300) -> None:
    _cache[key] = (data, time.time() + ttl)

# ── ESPN config ────────────────────────────────────────────────────────────
ESPN_SPORT_PATHS = {
    'mlb':   'baseball/mlb',
    'nba':   'basketball/nba',
    'wnba':  'basketball/wnba',
    'nfl':   'football/nfl',
    'nhl':   'hockey/nhl',
    'ncaab': 'basketball/mens-college-basketball',
    'ncaaf': 'football/college-football',
}

ESPN_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}

def _parse_espn_stats(stats: list) -> dict:
    """Convert ESPN stats[] array → flat {name: {value, display, label}} dict."""
    result = {}
    for s in stats:
        name = s.get('name') or s.get('abbreviation')
        if name:
            result[name] = {
                'value':   s.get('value'),
                'display': s.get('displayValue', ''),
                'label':   s.get('shortDisplayName', s.get('displayName', '')),
            }
    return result

def _sv(stats: dict, key: str, default=0):
    return stats.get(key, {}).get('value', default) or default

def _sd(stats: dict, key: str, default='') -> str:
    return str(stats.get(key, {}).get('display', default) or default)


# ── Standings ──────────────────────────────────────────────────────────────

@router.get("/standings/{sport}")
async def get_standings(sport: str):
    """
    Live standings from ESPN for mlb | nba | wnba | nfl | nhl | ncaab | ncaaf.
    Cached 5 minutes.
    """
    sport = sport.lower()
    if sport not in ESPN_SPORT_PATHS:
        raise HTTPException(400, f"Unsupported sport. Options: {list(ESPN_SPORT_PATHS)}")

    cached = _get_cache(f"standings:{sport}")
    if cached:
        return cached

    url = f"https://site.api.espn.com/apis/v2/sports/{ESPN_SPORT_PATHS[sport]}/standings"
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(url, headers=ESPN_HEADERS)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.error(f"ESPN standings {sport}: {e}")
        raise HTTPException(502, "ESPN unavailable")

    teams = []
    children = data.get('children', []) or [data]

    for division in children:
        division_name = division.get('name', '')
        entries = division.get('standings', {}).get('entries', [])

        for entry in entries:
            team = entry.get('team', {})
            stats = _parse_espn_stats(entry.get('stats', []))

            wins   = int(_sv(stats, 'wins', 0))
            losses = int(_sv(stats, 'losses', 0))
            ties   = int(_sv(stats, 'ties', 0))
            total  = wins + losses + ties

            raw_pct = _sv(stats, 'winPercent', None)
            pct = round(float(raw_pct), 3) if raw_pct is not None else (
                round(wins / total, 3) if total > 0 else 0.0
            )

            logos = team.get('logos', [])
            logo  = logos[0].get('href', '') if logos else ''

            teams.append({
                'rank':            len(teams) + 1,
                'team':            team.get('displayName', ''),
                'abbr':            team.get('abbreviation', ''),
                'logo':            logo,
                'color':           '#' + team.get('color', '333') if team.get('color') else '#333',
                'altColor':        '#' + team.get('alternateColor', '555') if team.get('alternateColor') else '#555',
                'division':        division_name,
                'wins':            wins,
                'losses':          losses,
                'ties':            ties,
                'pct':             pct,
                'gamesBehind':     round(float(_sv(stats, 'gamesBehind', 0)), 1),
                'pointsFor':       round(float(_sv(stats, 'pointsFor', 0)), 2),
                'pointsAgainst':   round(float(_sv(stats, 'pointsAgainst', 0)), 2),
                'differential':    round(float(_sv(stats, 'differential', 0)), 2),
                'homeRecord':      _sd(stats, 'homeRecord'),
                'awayRecord':      _sd(stats, 'awayRecord'),
                'divisionRecord':  _sd(stats, 'divisionRecord'),
                'conferenceRecord':_sd(stats, 'conferenceRecord'),
                'streak':          _sd(stats, 'streak'),
                'last10':          _sd(stats, 'Last Ten Games') or _sd(stats, 'L10'),
            })

    teams.sort(key=lambda t: (-t['pct'], -t['wins']))
    for i, t in enumerate(teams):
        t['rank'] = i + 1

    result = {'sport': sport, 'teams': teams, 'count': len(teams), 'source': 'ESPN'}
    _set_cache(f"standings:{sport}", result, 300)
    return result


# ── ESPN scoreboard (live scores) ──────────────────────────────────────────

@router.get("/scoreboard/{sport}")
async def get_scoreboard(sport: str):
    """Today's games + live scores from ESPN. Cached 60 s."""
    sport = sport.lower()
    if sport not in ESPN_SPORT_PATHS:
        raise HTTPException(400, "Unsupported sport")

    cached = _get_cache(f"scoreboard:{sport}")
    if cached:
        return cached

    url = f"https://site.api.espn.com/apis/site/v2/sports/{ESPN_SPORT_PATHS[sport]}/scoreboard"
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(url, headers=ESPN_HEADERS)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.error(f"ESPN scoreboard {sport}: {e}")
        raise HTTPException(502, "ESPN unavailable")

    games = []
    for event in data.get('events', []):
        comp        = event.get('competitions', [{}])[0]
        competitors = comp.get('competitors', [])
        home = next((c for c in competitors if c.get('homeAway') == 'home'), {})
        away = next((c for c in competitors if c.get('homeAway') == 'away'), {})
        status_obj  = comp.get('status', {})
        status_type = status_obj.get('type', {})

        # Embedded odds from ESPN
        odds_list = comp.get('odds', [{}])
        odds_data = odds_list[0] if odds_list else {}

        games.append({
            'id':           event.get('id'),
            'name':         event.get('name'),
            'date':         event.get('date'),
            'status':       status_type.get('state', ''),
            'statusDetail': status_type.get('detail', ''),
            'period':       status_obj.get('period', 0),
            'clock':        status_obj.get('displayClock', ''),
            'home': {
                'team':       home.get('team', {}).get('abbreviation', ''),
                'teamName':   home.get('team', {}).get('displayName', ''),
                'score':      home.get('score', ''),
                'record':     home.get('records', [{}])[0].get('summary', '') if home.get('records') else '',
                'linescores': [ls.get('value', 0) for ls in home.get('linescores', [])],
            },
            'away': {
                'team':       away.get('team', {}).get('abbreviation', ''),
                'teamName':   away.get('team', {}).get('displayName', ''),
                'score':      away.get('score', ''),
                'record':     away.get('records', [{}])[0].get('summary', '') if away.get('records') else '',
                'linescores': [ls.get('value', 0) for ls in away.get('linescores', [])],
            },
            'venue':        comp.get('venue', {}).get('fullName', ''),
            'broadcast':    comp.get('broadcasts', [{}])[0].get('names', [''])[0] if comp.get('broadcasts') else '',
            'odds': {
                'spread':     odds_data.get('details', ''),
                'overUnder':  odds_data.get('overUnder', ''),
            },
        })

    result = {'sport': sport, 'games': games, 'count': len(games), 'source': 'ESPN'}
    _set_cache(f"scoreboard:{sport}", result, 60)
    return result


# ── ESPN stat leaders ──────────────────────────────────────────────────────

@router.get("/leaders/{sport}")
async def get_leaders(sport: str, limit: int = Query(25, ge=5, le=100)):
    """Season statistical leaders via ESPN. Cached 10 minutes."""
    sport = sport.lower()
    if sport not in ESPN_SPORT_PATHS:
        raise HTTPException(400, "Unsupported sport")

    cache_key = f"leaders:{sport}:{limit}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    url = f"https://site.api.espn.com/apis/site/v2/sports/{ESPN_SPORT_PATHS[sport]}/leaders"
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(url, headers=ESPN_HEADERS)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.error(f"ESPN leaders {sport}: {e}")
        raise HTTPException(502, "ESPN leaders unavailable")

    categories = []
    for cat in data.get('categories', []):
        leaders = []
        for entry in cat.get('leaders', [])[:limit]:
            athlete = entry.get('athlete', {})
            team    = entry.get('team', {})
            leaders.append({
                'name':         athlete.get('displayName', ''),
                'shortName':    athlete.get('shortName', ''),
                'headshot':     athlete.get('headshot', {}).get('href', '') if isinstance(athlete.get('headshot'), dict) else '',
                'team':         team.get('abbreviation', ''),
                'teamName':     team.get('displayName', ''),
                'teamColor':    '#' + team.get('color', '333') if team.get('color') else '#333',
                'value':        entry.get('value', 0),
                'displayValue': entry.get('displayValue', ''),
            })
        if leaders:
            categories.append({
                'name':        cat.get('name', ''),
                'displayName': cat.get('displayName', ''),
                'shortName':   cat.get('shortDisplayName', cat.get('abbreviation', '')),
                'leaders':     leaders,
            })

    result = {'sport': sport, 'categories': categories, 'source': 'ESPN'}
    _set_cache(cache_key, result, 600)
    return result


# ── Baseball Savant / Statcast ─────────────────────────────────────────────

SAVANT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer':    'https://baseballsavant.mlb.com/',
    'Accept':     'text/csv, application/json',
}

async def _fetch_savant_csv(url: str, params: dict) -> list:
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        r = await client.get(url, params=params, headers=SAVANT_HEADERS)
        r.raise_for_status()
        # Strip UTF-8 BOM — Baseball Savant CSVs start with ﻿ which corrupts the first column key
        text = r.text.lstrip('﻿')
        reader = csv.DictReader(io.StringIO(text))
        return list(reader)

def _safe_float(val, default=0.0) -> float:
    try:
        return float(val) if val not in (None, '', 'null') else default
    except (ValueError, TypeError):
        return default

def _safe_int(val, default=0) -> int:
    try:
        return int(float(val)) if val not in (None, '', 'null') else default
    except (ValueError, TypeError):
        return default


@router.get("/statcast/batting")
async def get_statcast_batting(
    min_pa:  int = Query(50, ge=1),
    year:    int = Query(2026, ge=2015),
):
    """MLB Statcast expected stats (xBA, xSLG, xwOBA) for hitters. Cached 1 hour."""
    cache_key = f"statcast:batting:{year}:{min_pa}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    try:
        rows = await _fetch_savant_csv(
            "https://baseballsavant.mlb.com/leaderboard/expected_statistics",
            {'type': 'batter', 'year': year, 'min': min_pa, 'csv': 'true'},
        )
    except Exception as e:
        logger.error(f"Baseball Savant batting: {e}")
        raise HTTPException(502, "Baseball Savant unavailable")

    players = []
    for row in rows:
        name = row.get('last_name, first_name', '')
        if ', ' in name:
            parts = name.split(', ', 1)
            name = f'{parts[1]} {parts[0]}'
        name = name.strip()
        players.append({
            'name':      name,
            'team':      row.get('team_name', row.get('team_abbrev', row.get('team', ''))),
            'pa':        _safe_int(row.get('pa')),
            'ba':        _safe_float(row.get('ba')),
            'xBA':       _safe_float(row.get('est_ba')),
            'xBADiff':   _safe_float(row.get('est_ba_minus_ba_diff')),
            'slg':       _safe_float(row.get('slg')),
            'xSLG':      _safe_float(row.get('est_slg')),
            'xSLGDiff':  _safe_float(row.get('est_slg_minus_slg_diff')),
            'woba':      _safe_float(row.get('woba')),
            'xwOBA':     _safe_float(row.get('est_woba')),
            'xwOBADiff': _safe_float(row.get('est_woba_minus_woba_diff')),
        })

    players.sort(key=lambda p: -p['xwOBA'])
    result = {
        'players': players, 'count': len(players),
        'source': 'Baseball Savant / Statcast', 'year': year, 'min_pa': min_pa,
    }
    _set_cache(cache_key, result, 3600)
    return result


@router.get("/statcast/pitching")
async def get_statcast_pitching(
    min_pa: int = Query(50, ge=1),
    year:   int = Query(2026, ge=2015),
):
    """MLB Statcast expected stats (xERA, xwOBA against) for pitchers. Cached 1 hour."""
    cache_key = f"statcast:pitching:{year}:{min_pa}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    try:
        rows = await _fetch_savant_csv(
            "https://baseballsavant.mlb.com/leaderboard/expected_statistics",
            {'type': 'pitcher', 'year': year, 'min': min_pa, 'csv': 'true'},
        )
    except Exception as e:
        logger.error(f"Baseball Savant pitching: {e}")
        raise HTTPException(502, "Baseball Savant unavailable")

    pitchers = []
    for row in rows:
        # CSV column is literally "last_name, first_name" as one combined key
        name = row.get('last_name, first_name', '') or row.get('player_name', row.get('name', ''))
        if ', ' in name:
            parts = name.split(', ', 1)
            name = f"{parts[1]} {parts[0]}"
        name = name.strip()
        pitchers.append({
            'name':         name,
            'team':         row.get('team_name', row.get('team_abbrev', row.get('team', ''))),
            'pa':           _safe_int(row.get('pa')),
            'era':          _safe_float(row.get('era')),
            'xERA':         _safe_float(row.get('xera')),
            'xERADiff':     _safe_float(row.get('era_minus_xera_diff')),
            'wobaAgainst':  _safe_float(row.get('woba')),
            'xwobaAgainst': _safe_float(row.get('est_woba')),
            'xwobaDiff':    _safe_float(row.get('est_woba_minus_woba_diff')),
        })

    pitchers = [p for p in pitchers if p['name'] and p['pa'] >= 30]
    pitchers.sort(key=lambda p: p['xERA'] if p['xERA'] > 0 else 99)
    result = {
        'pitchers': pitchers, 'count': len(pitchers),
        'source': 'Baseball Savant / Statcast', 'year': year, 'min_pa': min_pa,
    }
    _set_cache(cache_key, result, 3600)
    return result


@router.get("/statcast/hard-hit")
async def get_statcast_hard_hit(
    min_bbe: int = Query(25, ge=1),
    year:    int = Query(2026, ge=2015),
):
    """Exit velocity, barrel%, and hard-hit% leaderboard from Baseball Savant."""
    cache_key = f"statcast:hardhit:{year}:{min_bbe}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    try:
        rows = await _fetch_savant_csv(
            "https://baseballsavant.mlb.com/leaderboard/statcast",
            {'type': 'batter', 'year': year, 'min': min_bbe, 'csv': 'true'},
        )
    except Exception as e:
        logger.error(f"Baseball Savant hard-hit: {e}")
        raise HTTPException(502, "Baseball Savant unavailable")

    players = []
    for row in rows:
        name = row.get('last_name, first_name', '') or row.get('player_name', row.get('name', ''))
        # some endpoints return "last, first" format
        if ', ' in name:
            parts = name.split(', ', 1)
            name = f"{parts[1]} {parts[0]}"
        players.append({
            'name':          name.strip(),
            'team':          row.get('team_name', row.get('team_abbrev', '')),
            'pa':            _safe_int(row.get('attempts', row.get('pa'))),
            'exitVeloAvg':   _safe_float(row.get('avg_hit_speed', row.get('exit_velocity_avg'))),
            'launchAngleAvg':_safe_float(row.get('avg_hit_angle', row.get('launch_angle_avg'))),
            'sweetSpotPct':  _safe_float(row.get('anglesweetspotpercent', row.get('sweet_spot_percent'))),
            'barrelPct':     _safe_float(row.get('brl_percent', row.get('barrel_batted_rate'))),
            'hardHitPct':    _safe_float(row.get('ev95percent', row.get('hard_hit_percent'))),
            'xBA':           _safe_float(row.get('xba')),
            'xSLG':          _safe_float(row.get('xslg')),
            'xwOBA':         _safe_float(row.get('xwobacon', row.get('xwoba'))),
        })

    players = [p for p in players if p['exitVeloAvg'] > 0]
    players.sort(key=lambda p: -p['exitVeloAvg'])
    result = {
        'players': players, 'count': len(players),
        'source': 'Baseball Savant / Statcast', 'year': year,
    }
    _set_cache(cache_key, result, 3600)
    return result


# ── NBA.com Advanced Team Stats ────────────────────────────────────────────

NBA_HEADERS = {
    'Accept':              'application/json, text/plain, */*',
    'Accept-Language':     'en-US,en;q=0.9',
    'Origin':              'https://www.nba.com',
    'Referer':             'https://www.nba.com/stats/teams/advanced',
    'User-Agent':          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token':  'true',
}

def _nba_parse(data: dict, field_map: dict) -> list:
    """Parse NBA.com resultSets[0] → list of dicts using field_map."""
    rs = data.get('resultSets', [{}])[0]
    headers = rs.get('headers', [])
    rows    = rs.get('rowSet', [])
    result  = []
    for row in rows:
        d = dict(zip(headers, row))
        mapped = {}
        for out_key, src_key in field_map.items():
            mapped[out_key] = d.get(src_key)
        result.append(mapped)
    return result


@router.get("/nba/advanced")
async def get_nba_advanced(season: str = '2024-25'):
    """NBA team advanced metrics: ORtg, DRtg, NetRtg, TS%, Pace, etc. Cached 1 hour."""
    cache_key = f"nba:advanced:{season}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    params = {
        'MeasureType': 'Advanced', 'PerMode': 'PerGame',
        'Season': season, 'SeasonType': 'Regular Season',
        'LeagueID': '00', 'Conference': '', 'DateFrom': '', 'DateTo': '',
        'Division': '', 'GameScope': '', 'GameSegment': '',
        'LastNGames': 0, 'Location': '', 'Month': 0,
        'OpponentTeamID': 0, 'Outcome': '', 'PORound': 0,
        'PaceAdjust': 'N', 'Period': 0, 'PlayerExperience': '',
        'PlayerPosition': '', 'PlusMinus': 'N', 'Rank': 'N',
        'SeasonSegment': '', 'ShotClockRange': '',
        'StarterBench': '', 'TeamID': 0, 'TwoWay': 0,
        'VsConference': '', 'VsDivision': '',
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(
                'https://stats.nba.com/stats/leaguedashteamstats',
                params=params, headers=NBA_HEADERS,
            )
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.error(f"NBA.com advanced: {e}")
        raise HTTPException(502, "NBA.com stats API unavailable")

    FIELD_MAP = {
        'team':        'TEAM_NAME',
        'abbr':        'TEAM_ABBREVIATION',
        'gp':          'GP',
        'offRtg':      'OFF_RATING',
        'defRtg':      'DEF_RATING',
        'netRtg':      'NET_RATING',
        'astPct':      'AST_PCT',
        'astToRatio':  'AST_TO',
        'orebPct':     'OREB_PCT',
        'drebPct':     'DREB_PCT',
        'rebPct':      'REB_PCT',
        'tovPct':      'TM_TOV_PCT',
        'efgPct':      'EFG_PCT',
        'tsPct':       'TS_PCT',
        'pace':        'PACE',
        'ptsOffTov':   'PTS_OFF_TOV',
        'pts2nd':      'PTS_2ND_CHANCE',
        'ptsFB':       'PTS_FB',
        'ptsPaint':    'PTS_PAINT',
        'oppPtsOffTov':'OPP_PTS_OFF_TOV',
        'oppPts2nd':   'OPP_PTS_2ND_CHANCE',
        'oppPtsFB':    'OPP_PTS_FB',
        'oppPtsPaint': 'OPP_PTS_PAINT',
    }

    teams = _nba_parse(data, FIELD_MAP)
    teams.sort(key=lambda t: -(t.get('netRtg') or 0))

    result = {
        'teams': teams, 'count': len(teams),
        'source': 'NBA.com Stats', 'season': season,
    }
    _set_cache(cache_key, result, 3600)
    return result


@router.get("/nba/player-leaders")
async def get_nba_player_leaders(
    season:    str = '2024-25',
    stat:      str = Query('PTS', description='PTS | REB | AST | STL | BLK | FG_PCT | FG3_PCT | FT_PCT'),
    per_mode:  str = Query('PerGame'),
    limit:     int = Query(25, ge=5, le=100),
):
    """NBA individual player stat leaders from NBA.com."""
    cache_key = f"nba:leaders:{season}:{stat}:{per_mode}:{limit}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    params = {
        'LeagueID': '00', 'PerMode': per_mode,
        'Scope': 'S', 'Season': season,
        'SeasonType': 'Regular Season', 'StatCategory': stat,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                'https://stats.nba.com/stats/leagueleaders',
                params=params, headers=NBA_HEADERS,
            )
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.error(f"NBA.com leaders: {e}")
        raise HTTPException(502, "NBA.com stats API unavailable")

    rs      = data.get('resultSet', {})
    headers = rs.get('headers', [])
    rows    = rs.get('rowSet', [])[:limit]

    players = []
    for row in rows:
        d = dict(zip(headers, row))
        players.append({
            'rank':   d.get('RANK'),
            'name':   d.get('PLAYER'),
            'team':   d.get('TEAM'),
            'gp':     d.get('GP'),
            'min':    d.get('MIN'),
            'value':  d.get(stat, 0),
            'pts':    d.get('PTS'),
            'reb':    d.get('REB'),
            'ast':    d.get('AST'),
            'stl':    d.get('STL'),
            'blk':    d.get('BLK'),
            'fgPct':  d.get('FG_PCT'),
            'fg3Pct': d.get('FG3_PCT'),
            'ftPct':  d.get('FT_PCT'),
        })

    result = {
        'players': players, 'count': len(players), 'stat': stat,
        'source': 'NBA.com Stats', 'season': season,
    }
    _set_cache(cache_key, result, 3600)
    return result


# ── BartTorvik T-Rank (NCAAB) ──────────────────────────────────────────────

@router.get("/ncaab/trank")
async def get_ncaab_trank(year: int = Query(2026, ge=2010)):
    """BartTorvik T-Rank advanced team metrics for NCAAB. Cached 2 hours."""
    cache_key = f"trank:{year}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(
                'https://barttorvik.com/trank.php',
                params={'year': year, 'json': 1},
                headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://barttorvik.com/'},
            )
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.error(f"BartTorvik: {e}")
        raise HTTPException(502, "BartTorvik unavailable")

    teams = []
    if isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, list):
                # Array format: [team, conf, record, adjOE, adjDE, adjTempo, barthag, eFG, eFGDef, tovPct, tovDef, orbPct, orbDef, ftRate, ftRateDef, ...]
                def gi(idx, default=None):
                    return item[idx] if len(item) > idx else default
                teams.append({
                    'rank':       i + 1,
                    'team':       gi(0, ''),
                    'conf':       gi(1, ''),
                    'record':     gi(2, ''),
                    'adjOE':      _safe_float(gi(3)),
                    'adjDE':      _safe_float(gi(4)),
                    'adjTempo':   _safe_float(gi(5)),
                    'barthag':    _safe_float(gi(6)),
                    'efgPct':     _safe_float(gi(7)),
                    'efgDef':     _safe_float(gi(8)),
                    'tovPct':     _safe_float(gi(9)),
                    'tovDef':     _safe_float(gi(10)),
                    'orbPct':     _safe_float(gi(11)),
                    'orbDef':     _safe_float(gi(12)),
                    'ftRate':     _safe_float(gi(13)),
                    'ftRateDef':  _safe_float(gi(14)),
                })
            elif isinstance(item, dict):
                teams.append({'rank': i + 1, **item})

    result = {
        'teams': teams, 'count': len(teams),
        'source': 'BartTorvik T-Rank', 'year': year,
    }
    _set_cache(cache_key, result, 7200)
    return result


# ── Team Scoring Analytics (ESPN — works for all sports) ──────────────────

@router.get("/team-scoring/{sport}")
async def get_team_scoring(sport: str):
    """
    Per-game scoring analytics from ESPN standings.
    Returns ppg, papg, diff, home/road splits, streak, L10.
    Cached 5 minutes. Works for nba, nfl, mlb, nhl, ncaab, ncaaf, wnba.
    """
    sport = sport.lower()
    if sport not in ESPN_SPORT_PATHS:
        raise HTTPException(400, f"Unsupported sport")

    cache_key = f"team-scoring:{sport}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    url = f"https://site.api.espn.com/apis/v2/sports/{ESPN_SPORT_PATHS[sport]}/standings"
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(url, headers=ESPN_HEADERS)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.error(f"ESPN team-scoring {sport}: {e}")
        raise HTTPException(502, "ESPN unavailable")

    teams = []
    children = data.get('children', []) or [data]

    for division in children:
        division_name = division.get('name', '')
        entries = division.get('standings', {}).get('entries', [])

        for entry in entries:
            team  = entry.get('team', {})
            stats = _parse_espn_stats(entry.get('stats', []))

            wins   = int(_sv(stats, 'wins', 0))
            losses = int(_sv(stats, 'losses', 0))
            total  = wins + losses

            ppg  = round(float(_sv(stats, 'avgPointsFor',     0) or 0), 1)
            papg = round(float(_sv(stats, 'avgPointsAgainst', 0) or 0), 1)
            diff = round(ppg - papg, 1) if (ppg and papg) else round(float(_sv(stats, 'pointDifferential', 0) or 0), 1)

            logos = team.get('logos', [])
            logo  = logos[0].get('href', '') if logos else ''

            teams.append({
                'team':       team.get('displayName', ''),
                'abbr':       team.get('abbreviation', ''),
                'logo':       logo,
                'color':      '#' + team.get('color', '333') if team.get('color') else '#333',
                'division':   division_name,
                'wins':       wins,
                'losses':     losses,
                'pct':        round(wins / total, 3) if total > 0 else 0.0,
                'ppg':        ppg,
                'papg':       papg,
                'diff':       diff,
                'homeRecord': _sd(stats, 'Home'),
                'roadRecord': _sd(stats, 'Road'),
                'streak':     _sd(stats, 'streak'),
                'last10':     _sd(stats, 'Last Ten Games'),
                'confRecord': _sd(stats, 'vs. Conf.') or _sd(stats, 'conferenceRecord'),
            })

    teams.sort(key=lambda t: -t['diff'])
    result = {'sport': sport, 'teams': teams, 'count': len(teams), 'source': 'ESPN'}
    _set_cache(cache_key, result, 300)
    return result


# ── Cache control ──────────────────────────────────────────────────────────

@router.get("/cache/clear")
async def clear_cache():
    """Clear all cached analytics data (admin use)."""
    _cache.clear()
    return {'message': 'Cache cleared'}

@router.get("/cache/status")
async def cache_status():
    now = time.time()
    return {
        'entries': len(_cache),
        'keys': [
            {'key': k, 'expires_in': round(v[1] - now, 0)}
            for k, v in _cache.items()
        ],
    }
