#!/usr/bin/env python3
"""
Build NCAAB KenPom-style efficiency ratings from existing betting rankings data.
Uses PPG, PAPG, avg_total (pace proxy) to compute:
  - ORtg proxy = PPG / (avg_total/2) * 100
  - DRtg proxy = PAPG / (avg_total/2) * 100
  - Conference SOS bonus — hard-coded tier weights since raw data lacks SOS

Formula:
  composite = 0.30*win_pct + 0.30*diff_norm + 0.20*away_win_pct + 0.10*pythag + 0.10*conf_sos
  AdjEM = (composite - 0.5) * 40   → roughly -20 to +20 range

Conference tiers:
  Tier 1 (Big12, SEC, BigTen, ACC): SOS = 1.0  → +0.10 composite bonus
  Tier 2 (BigEast, American):       SOS = 0.60 → +0.06 composite bonus
  Tier 3 (mid-major):               SOS = 0.0  → no bonus

Outputs: ncaab_efficiency.json
"""
import json
import math
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent

# Conference tiers — values are SOS weight (0-1 scale)
CONF_TIERS = {
    'Big12':   1.0,
    'SEC':     1.0,
    'BigTen':  1.0,
    'ACC':     1.0,
    'BigEast': 0.6,
    'American': 0.3,
}

# Conference membership — team names normalized to match data format:
# data uses underscores-as-spaces, "st." abbreviation, lowercase
POWER_CONFERENCES = {
    'ACC': [
        'duke', 'north carolina', 'virginia', 'wake forest', 'florida state',
        'pittsburgh', 'clemson', 'notre dame', 'miami fl', 'georgia tech',
        'boston college', 'nc state', 'virginia tech', 'louisville', 'syracuse',
        'stanford', 'cal', 'smu',
    ],
    'Big12': [
        'kansas', 'baylor', 'houston', 'texas tech', 'iowa state', 'kansas state',
        'tcu', 'oklahoma state', 'west virginia', 'cincinnati', 'arizona',
        'arizona state', 'byu', 'ucf', 'utah', 'colorado',
    ],
    'BigTen': [
        'purdue', 'illinois', 'michigan state', 'indiana', 'michigan', 'ohio state',
        'penn state', 'wisconsin', 'nebraska', 'minnesota', 'iowa', 'maryland',
        'rutgers', 'northwestern', 'oregon', 'usc', 'ucla', 'washington',
    ],
    'SEC': [
        'auburn', 'tennessee', 'alabama', 'kentucky', 'florida', 'texas a&m',
        'missouri', 'arkansas', 'mississippi', 'mississippi state', 'south carolina',
        'lsu', 'georgia', 'vanderbilt', 'oklahoma', 'texas',
    ],
    'BigEast': [
        'connecticut', 'marquette', "st. john's", 'creighton', 'villanova',
        'xavier', 'seton hall', 'butler', 'depaul', 'providence', 'georgetown',
    ],
    'American': [
        'memphis', 'tulsa', 'temple', 'smu', 'houston', 'cincinnati',
    ],
}

# Build lookup: normalized team name → conference
_CONF_LOOKUP: dict[str, str] = {}
for _conf, _members in POWER_CONFERENCES.items():
    for _m in _members:
        _CONF_LOOKUP[_m] = _conf


def _normalize_team(raw: str) -> str:
    """Convert data team name format to conference lookup format."""
    s = raw.replace('_', ' ')
    # Expand common abbreviations
    s = s.replace(' st.', ' state').replace(' a&m', ' a&m')
    return s.strip().lower()


def get_conference(team: str) -> str | None:
    """Return conference for a team, or None if not in a tracked conference."""
    normalized = _normalize_team(team)
    return _CONF_LOOKUP.get(normalized)


def pythagorean_winpct(ppg: float, papg: float, exp: float = 11.5) -> float:
    """Pythagorean win expectancy using point differential."""
    if ppg <= 0 or papg <= 0:
        return 0.5
    return ppg ** exp / (ppg ** exp + papg ** exp)


def build_efficiency(teams: list) -> list:
    """
    Compute efficiency metrics for each team.

    Composite score weights win%, score margin, away performance, pythag, and
    conference SOS tier. NOT fully SOS-adjusted — conference tier is a hard-coded
    proxy. Results for mid-majors reflect raw dominance; power conference teams
    are boosted to reflect schedule difficulty.
    """
    # Population stats for normalization
    all_diffs = [t.get('diff', 0) for t in teams if t.get('games', 0) >= 20]
    max_diff = max(abs(d) for d in all_diffs) if all_diffs else 30

    results = []
    for t in teams:
        ppg = t.get('ppg', 0)
        papg = t.get('papg', 0)
        avg_total = t.get('avg_total', ppg + papg)
        win_pct = t.get('win_pct', 50) / 100
        away_win_pct = t.get('away_win_pct', 50) / 100
        games = t.get('games', 0)
        diff = t.get('diff', ppg - papg)

        if ppg <= 0 or papg <= 0 or avg_total <= 0:
            continue

        # Raw efficiency metrics (pace proxy = avg_total/2 possessions per team)
        half_total = avg_total / 2
        ortg = round((ppg / half_total) * 100, 1) if half_total > 0 else 0
        drtg = round((papg / half_total) * 100, 1) if half_total > 0 else 0

        # Pythagorean win expectancy
        pyth_pct = pythagorean_winpct(ppg, papg)
        luck = round(win_pct - pyth_pct, 3)

        # Conference SOS bonus
        conf = get_conference(t['team'])
        conf_tier = CONF_TIERS.get(conf, 0.0) if conf else 0.0

        # Composite score (weights sum to 1.0):
        # 30% win%  30% score diff  20% away win%  10% pythag  10% conf SOS
        diff_normalized = diff / max_diff  # -1 to +1
        composite = (
            0.30 * win_pct
            + 0.30 * ((diff_normalized + 1) / 2)
            + 0.20 * away_win_pct
            + 0.10 * pyth_pct
            + 0.10 * conf_tier
        )
        # Scale to -20 to +20 range (similar to KenPom AdjEM scale)
        adj_em = round((composite - 0.5) * 40, 1)

        if adj_em >= 10:
            tier = 'ELITE'
        elif adj_em >= 4:
            tier = 'CONTENDER'
        elif adj_em >= -2:
            tier = 'AVERAGE'
        elif adj_em >= -8:
            tier = 'BELOW'
        else:
            tier = 'BOTTOM'

        results.append({
            'team': t['team'],
            'team_display': t['team'].replace('_', ' ').replace('.', '').title(),
            'conference': conf,
            'games': games,
            'record': t.get('record', ''),
            'win_pct': round(win_pct * 100, 1),
            'away_win_pct': round(away_win_pct * 100, 1),
            'ppg': ppg,
            'papg': papg,
            'diff': round(diff, 1),
            'avg_total': avg_total,
            'ortg': ortg,
            'drtg': drtg,
            'adj_em': adj_em,
            'pyth_pct': round(pyth_pct * 100, 1),
            'luck': luck,
            'tier': tier,
            'home_ppg': t.get('home_ppg'),
            'away_ppg': t.get('away_ppg'),
            'home_papg': t.get('home_papg'),
            'away_papg': t.get('away_papg'),
        })

    results.sort(key=lambda x: -x['adj_em'])
    for i, t in enumerate(results):
        t['rank'] = i + 1

    return results


def main():
    seasons = ['2023', '2024', '2025']
    all_seasons: dict = {}

    for season in seasons:
        f = OUTPUT_DIR / f'ncaab_betting_rankings_{season}.json'
        if not f.exists():
            print(f'Missing: {f.name}')
            continue
        with open(f) as fh:
            teams = json.load(fh)

        teams = [t for t in teams if t.get('games', 0) >= 20]
        results = build_efficiency(teams)
        all_seasons[season] = results
        print(f"\n{season}: {len(results)} teams")
        print(f"  Top: {results[0]['team_display']} {results[0]['adj_em']:+.1f}")
        print(f"  Bottom: {results[-1]['team_display']} {results[-1]['adj_em']:+.1f}")

        print('  Top 15 AdjEM:')
        for t in results[:15]:
            conf_label = f"[{t['conference']}]" if t['conference'] else '[mid]'
            print(f"    #{t['rank']:3d} {t['team_display']:28s} {conf_label:10s} {t['adj_em']:+5.1f}  ORtg:{t['ortg']} DRtg:{t['drtg']} Luck:{t['luck']:+.3f}")

        # Spot-check major programs
        majors = {'duke', 'kansas', 'houston', 'auburn', 'kentucky', 'purdue',
                  'connecticut', 'marquette', 'tennessee', 'baylor', 'iowa_st.'}
        print('  Major program check:')
        for t in results:
            if t['team'] in majors:
                conf_label = f"[{t['conference']}]" if t['conference'] else '[mid]'
                print(f"    #{t['rank']:3d} {t['team_display']:28s} {conf_label:10s} {t['adj_em']:+5.1f}  {t['record']}")

    output = {
        'seasons': all_seasons,
        'current_season': '2025',
        'method': 'composite_conf_sos',
        'formula': (
            'composite = 0.30*win_pct + 0.30*diff_norm + 0.20*away_win_pct '
            '+ 0.10*pythag + 0.10*conf_sos | AdjEM = (composite-0.5)*40'
        ),
        'note': (
            'Conference SOS bonus applied: Big12/SEC/BigTen/ACC tier=1.0, '
            'BigEast tier=0.6, American tier=0.3. Mid-majors reflect raw dominance.'
        ),
    }

    out = OUTPUT_DIR / 'ncaab_efficiency.json'
    with open(out, 'w') as f:
        json.dump(output, f, indent=2)
    print(f'\nSaved → {out.name}')


if __name__ == '__main__':
    main()
