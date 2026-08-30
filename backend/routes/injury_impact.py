"""
Injury Impact Engine — Cascading effects of player injuries on matchups and betting.
GET /api/f5/injury-impact
"""
import json, difflib, urllib.request
from pathlib import Path
from fastapi import APIRouter

router = APIRouter()
BACKTEST_DIR = Path(__file__).parent.parent / "f5_backtest"
MADDEN_JSON  = BACKTEST_DIR / "madden26_players.json"

# ── Position metadata ─────────────────────────────────────────────────────────
POSITION_META = {
    "QB":    {"side": "offense", "weight": 10, "label": "QB"},
    "OL":    {"side": "offense", "weight": 7,  "label": "OL"},
    "WR":    {"side": "offense", "weight": 5,  "label": "WR"},
    "TE":    {"side": "offense", "weight": 4,  "label": "TE"},
    "RB":    {"side": "offense", "weight": 4,  "label": "RB"},
    "LEDGE": {"side": "defense", "weight": 7,  "label": "EDGE"},
    "REDGE": {"side": "defense", "weight": 7,  "label": "EDGE"},
    "DB":    {"side": "defense", "weight": 6,  "label": "DB"},
    "DL":    {"side": "defense", "weight": 5,  "label": "DL"},
    "LB":    {"side": "defense", "weight": 4,  "label": "LB"},
    "WILL":  {"side": "defense", "weight": 4,  "label": "LB"},
    "SAM":   {"side": "defense", "weight": 4,  "label": "LB"},
    "K":     {"side": "special", "weight": 1,  "label": "K"},
    "P":     {"side": "special", "weight": 1,  "label": "P"},
    "LS":    {"side": "special", "weight": 0,  "label": "LS"},
}

# ── Cascade rules per position ────────────────────────────────────────────────
CASCADE = {
    "QB": {
        "opposing_pos": [],
        "layer1": "Backup QB takes over — passing efficiency drops significantly. Average backup QBR is 12–15% lower.",
        "layer2": "Opposing pass rush becomes less relevant. A diminished QB neutralizes elite edge rushers by releasing the ball quicker.",
        "layer3": "Expect a conservative gameplan: more handoffs, shorter routes, no-risk checkdowns. The offensive ceiling collapses.",
        "bet_signals": ["↓ Team passing yards", "↓ Team total", "↑ Rush share", "↓ WR deep targets"],
    },
    "LT": {
        "opposing_pos": ["LEDGE"],
        "layer1": "Blindside protection drops — backup left tackle now faces the opposing team's best pass rusher one-on-one.",
        "layer2": "The left edge rusher (typically the team's best) no longer needs a double team. They can pin their ears back.",
        "layer3": "Expect sprint-outs away from the blind side, chip-and-release TE assignments, max protect looks. Deep ball frequency drops.",
        "bet_signals": ["↑ Blindside sacks", "↑ QB hurries", "↓ Downfield passing", "↑ QB scrambles"],
    },
    "RT": {
        "opposing_pos": ["REDGE"],
        "layer1": "Right tackle protection weakens — opposing right edge rusher gets a favorable matchup.",
        "layer2": "Opposing REDGE can now attack more aggressively without a quality blocker to slow them down.",
        "layer3": "Expect protection slide away from right side, bootleg plays to the left, RB assigned as a hot chip.",
        "bet_signals": ["↑ QB pressure right side", "↑ Sacks", "↓ Play-action frequency"],
    },
    "OL": {
        "opposing_pos": ["LEDGE", "REDGE", "DL"],
        "layer1": "Interior or generic OL depth drops — protection quality weakens across the board.",
        "layer2": "Opposing pass rush gets a free lane — specifically the player aligned over the backup.",
        "layer3": "Expect shorter route combinations, quicker release, more RB help on pass pro. Run game may shift to compensate.",
        "bet_signals": ["↑ QB pressure rate", "↑ Sacks", "↓ Deep passing volume", "↑ Rush attempts"],
    },
    "WR": {
        "opposing_pos": ["DB"],
        "layer1": "A key route runner is gone — target tree shrinks and the receiving hierarchy reshuffles.",
        "layer2": "If WR1 is out: Opposing CB1 now covers a lesser target, freeing bracket coverage elsewhere. Remaining WRs see more volume but face tighter coverage.",
        "layer3": "Expect more underneath routes, RB/TE becomes the primary safety valve. Props redistribute — volume up for the next WR, but against stiffer coverage.",
        "bet_signals": ["↑ Remaining WR targets", "↑ TE/RB receiving", "↓ Deep ball frequency", "↓ Team total if WR1"],
    },
    "TE": {
        "opposing_pos": ["LB", "SAM", "WILL"],
        "layer1": "Seam routes and red zone mismatch disappear — offense loses its most versatile receiving option.",
        "layer2": "Opposing LB/Safety no longer has to honor the TE threat over the middle — they can cheat toward the run or bracket WRs.",
        "layer3": "Expect the slot WR to absorb TE route concepts, more RB check-down usage as the new safety valve.",
        "bet_signals": ["↓ TE targets (backup)", "↑ Slot WR targets", "↓ Red zone passing"],
    },
    "RB": {
        "opposing_pos": ["LB"],
        "layer1": "Primary ball carrier out — rushing attack loses its most explosive option, forcing a committee approach.",
        "layer2": "Opposing run defense may realign resources toward pass defense, knowing the ground threat is diminished.",
        "layer3": "Expect more passing to offset the rushing drop, with shorter distribution serving as the new run game.",
        "bet_signals": ["↓ Rush yards", "↑ Pass attempts", "↓ Team rushing total"],
    },
    "LEDGE": {
        "opposing_pos": ["OL"],
        "layer1": "Elite blindside pass rusher is out — the opposing LT no longer has to prepare for the week's hardest assignment.",
        "layer2": "Opposing LT can use a lighter chip or no help at all, freeing the TE and RB for pass routes instead of protection.",
        "layer3": "Expect the opposing QB to have more time and confidence. Play-action, 7-step drops, and deep routes all become more viable.",
        "bet_signals": ["↓ QB pressure rate", "↑ QB passing yards", "↑ Deep targets", "↑ WR receiving yards"],
    },
    "REDGE": {
        "opposing_pos": ["OL"],
        "layer1": "Right-side pass rush weakens — opposing OL gets relief on that edge.",
        "layer2": "Opposing QB operates with a cleaner pocket — no longer has to feel pressure from the right side.",
        "layer3": "Expect longer developing routes, more play-action, a wider route tree than the matchup otherwise allows.",
        "bet_signals": ["↓ Sacks", "↑ QB passing yards", "↑ QB completion %"],
    },
    "DB": {
        "opposing_pos": ["WR", "TE"],
        "layer1": "Coverage unit loses a key defender — opposing offense gets a favorable matchup to exploit.",
        "layer2": "If CB1 is out: Opposing WR1 now faces the CB2 or a backup corner. If Safety is out: Middle-of-field routes open up for TEs and slot WRs.",
        "layer3": "Expect the opposing offense to target the weak coverage zone all game. Passing volume and efficiency should rise.",
        "bet_signals": ["↑ Opposing WR targets", "↑ Opposing WR yards", "↑ Team passing total"],
    },
    "DL": {
        "opposing_pos": ["OL", "RB"],
        "layer1": "Interior pass rush and run stuffing weakens — opposing OL gains leverage they didn't have on film.",
        "layer2": "Opposing interior linemen now have an easier assignment — gaps open for the run game.",
        "layer3": "Expect the opposing team to run more aggressively, especially between the tackles. QB also enjoys a cleaner pocket.",
        "bet_signals": ["↑ Opposing rush yards", "↑ Rush attempts", "↓ Interior pressure"],
    },
    "LB": {
        "opposing_pos": ["RB", "TE"],
        "layer1": "Linebacker run support and coverage weakens — opposing run game and underneath passing both improve.",
        "layer2": "Opposing RB receiving routes and TE seam concepts now face a lighter coverage player.",
        "layer3": "Expect screens, flare routes, and TE crossing routes to attack the vacated zones.",
        "bet_signals": ["↑ RB receiving yards", "↑ TE receiving yards", "↑ Short passing game"],
    },
    "WILL": {
        "opposing_pos": ["RB", "TE"],
        "layer1": "Weakside linebacker out — underneath pass coverage takes a hit.",
        "layer2": "Opposing RB/TE gets more space underneath on routes — screens become high-percentage calls.",
        "layer3": "Expect screen game exploitation, flare routes, quick TE underneath routes to attack the open area.",
        "bet_signals": ["↑ RB receiving", "↑ Short passing game"],
    },
    "SAM": {
        "opposing_pos": ["TE", "WR"],
        "layer1": "Strongside linebacker out — TE coverage in particular weakens significantly.",
        "layer2": "Opposing TE and slot WR now face a less experienced matchup in the intermediate zones.",
        "layer3": "Expect TE seam routes, slot crossing patterns, and mesh concepts to target the vacated area.",
        "bet_signals": ["↑ TE targets/yards", "↑ Slot WR targets"],
    },
}

# ESPN position abbr → Madden pos_group
ESPN_POS_TO_MADDEN = {
    "QB": "QB",
    "RB": "RB", "HB": "RB", "FB": "RB",
    "WR": "WR",
    "TE": "TE",
    "LT": "OL", "RT": "OL", "LG": "OL", "RG": "OL", "C": "OL",
    "T": "OL", "G": "OL", "OT": "OL", "OG": "OL",
    "DE": "LEDGE",
    "DT": "DL", "NT": "DL",
    "MLB": "LB", "OLB": "LB", "ILB": "LB", "LB": "LB",
    "CB": "DB", "FS": "DB", "SS": "DB", "S": "DB", "DB": "DB",
    "K": "K", "P": "P", "LS": "LS",
}

OL_LT = {"LT"}
OL_RT = {"RT"}

ESPN_ABBR_TO_NFLVERSE = {"LAR": "LA", "WSH": "WAS", "JAC": "JAX"}


def _norm(name: str) -> str:
    import re
    n = name.lower().strip()
    n = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", n)
    n = re.sub(r"['.,-]", "", n)
    return re.sub(r"\s+", " ", n).strip()


def _find_player(name: str, team: str, pos_group: str, by_team: dict) -> dict | None:
    candidates = [p for p in by_team.get(team, []) if p.get("pos_group") == pos_group]
    if not candidates:
        candidates = by_team.get(team, [])
    nt = _norm(name)
    best, score = None, 0.0
    for p in candidates:
        s = difflib.SequenceMatcher(None, nt, _norm(p.get("name", ""))).ratio()
        if s > score:
            score, best = s, p
    return best if score > 0.65 else None


def _depth(team: str, pos_group: str, by_team: dict) -> list[dict]:
    return sorted(
        [p for p in by_team.get(team, []) if p.get("pos_group") == pos_group],
        key=lambda x: -(x.get("ovr") or 0),
    )


def _best_at(team: str, groups: list[str], by_team: dict) -> dict | None:
    candidates = []
    for g in groups:
        d = _depth(team, g, by_team)
        if d:
            candidates.append(d[0])
    return max(candidates, key=lambda x: x.get("ovr") or 0) if candidates else None


def _tier(gap: int, weight: int, starter_ovr: int | None) -> str:
    if gap < 2 or weight == 0:
        return "IGNORE"
    score = gap * 1.0 + weight * 1.5
    if starter_ovr:
        score *= 1.3 if starter_ovr >= 90 else (1.1 if starter_ovr >= 80 else 1.0)
    if score >= 25:
        return "HIGH"
    if score >= 12:
        return "MEDIUM"
    if score >= 5:
        return "LOW"
    return "IGNORE"


def _get_injuries() -> dict[str, list]:
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
    except Exception:
        return {}
    result: dict[str, list] = {}
    for team_entry in data.get("injuries", []):
        for inj in team_entry.get("injuries", []):
            if inj.get("status") == "Active":
                continue
            ath = inj.get("athlete", {})
            abbr = ESPN_ABBR_TO_NFLVERSE.get(
                ath.get("team", {}).get("abbreviation", ""),
                ath.get("team", {}).get("abbreviation", ""),
            )
            if not abbr:
                continue
            result.setdefault(abbr, []).append({
                "name": ath.get("displayName", ""),
                "position": ath.get("position", {}).get("abbreviation", ""),
                "status": inj.get("status", ""),
                "comment": inj.get("shortComment", ""),
            })
    return result


def _get_games() -> list[dict]:
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
    except Exception:
        return []
    games = []
    for event in data.get("events", []):
        comp = event.get("competitions", [{}])[0]
        comps = comp.get("competitors", [])
        if len(comps) < 2:
            continue
        home = next((c for c in comps if c.get("homeAway") == "home"), comps[0])
        away = next((c for c in comps if c.get("homeAway") == "away"), comps[1])
        ha = ESPN_ABBR_TO_NFLVERSE.get(home["team"]["abbreviation"], home["team"]["abbreviation"])
        aa = ESPN_ABBR_TO_NFLVERSE.get(away["team"]["abbreviation"], away["team"]["abbreviation"])
        games.append({
            "game_id": event.get("id", ""),
            "name": event.get("name", ""),
            "date": event.get("date", ""),
            "home_team": ha,
            "away_team": aa,
            "home_team_name": home["team"].get("displayName", ha),
            "away_team_name": away["team"].get("displayName", aa),
            "week": data.get("week", {}).get("number"),
            "season_type": data.get("season", {}).get("type"),
        })
    return games


@router.get("/injury-impact")
async def get_injury_impact():
    if not MADDEN_JSON.exists():
        return {"available": False, "reason": "Madden data not loaded", "games": []}

    madden_raw = json.loads(MADDEN_JSON.read_text())
    by_team    = madden_raw.get("by_team", {})
    injuries   = _get_injuries()
    games      = _get_games()

    result_games = []
    for game in games:
        home, away = game["home_team"], game["away_team"]
        alerts = []

        for team, opponent in [(home, away), (away, home)]:
            for inj in injuries.get(team, []):
                if inj["status"] not in ("Out", "Injured Reserve", "Questionable", "Doubtful"):
                    continue

                espn_pos  = inj["position"]
                pos_group = ESPN_POS_TO_MADDEN.get(espn_pos, "")
                if not pos_group:
                    continue

                meta   = POSITION_META.get(pos_group, {})
                weight = meta.get("weight", 0)

                # Resolve LEDGE vs REDGE for generic DE
                starter = _find_player(inj["name"], team, pos_group, by_team)
                if not starter and espn_pos == "DE":
                    s2 = _find_player(inj["name"], team, "REDGE", by_team)
                    if s2:
                        starter, pos_group = s2, "REDGE"
                        meta   = POSITION_META.get(pos_group, meta)
                        weight = meta.get("weight", weight)

                starter_ovr = starter.get("ovr") if starter else None

                # Depth chart backup
                depth  = _depth(team, pos_group, by_team)
                backup = next((p for p in depth if p.get("name") != (starter or {}).get("name")), None) \
                         if starter else (depth[1] if len(depth) > 1 else None)
                backup_ovr = backup.get("ovr") if backup else None

                # OVR gap
                gap = max(0, (starter_ovr or 70) - (backup_ovr or 60))

                # Specific OL subtype for cascade
                specific = pos_group
                if pos_group == "OL":
                    specific = "LT" if espn_pos in OL_LT else ("RT" if espn_pos in OL_RT else "OL")

                tier = _tier(gap, weight, starter_ovr)
                if tier == "IGNORE" and inj["status"] in ("Out", "Injured Reserve"):
                    tier = "LOW"

                rules    = CASCADE.get(specific, CASCADE.get(pos_group, {}))
                opp_pos  = rules.get("opposing_pos", [])
                opp_pl   = _best_at(opponent, opp_pos, by_team) if opp_pos else None

                alerts.append({
                    "team": team,
                    "opponent": opponent,
                    "player_name": inj["name"],
                    "position": espn_pos,
                    "pos_group": pos_group,
                    "status": inj["status"],
                    "injury_note": inj.get("comment", ""),
                    "starter_ovr": starter_ovr,
                    "backup_name": backup.get("name") if backup else None,
                    "backup_ovr": backup_ovr,
                    "ovr_gap": gap,
                    "impact_tier": tier,
                    "cascade": {
                        "layer1": rules.get("layer1", ""),
                        "layer2": rules.get("layer2", ""),
                        "layer3": rules.get("layer3", ""),
                    },
                    "opposing_beneficiary": {
                        "name": opp_pl.get("name"),
                        "position": opp_pl.get("position"),
                        "ovr": opp_pl.get("ovr"),
                    } if opp_pl else None,
                    "bet_signals": rules.get("bet_signals", []),
                })

        tier_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "IGNORE": 3}
        alerts.sort(key=lambda x: (tier_order.get(x["impact_tier"], 3), -x["ovr_gap"]))

        result_games.append({
            **game,
            "alerts": alerts,
            "high_count":   sum(1 for a in alerts if a["impact_tier"] == "HIGH"),
            "medium_count": sum(1 for a in alerts if a["impact_tier"] == "MEDIUM"),
            "low_count":    sum(1 for a in alerts if a["impact_tier"] == "LOW"),
        })

    return {
        "available": True,
        "games": result_games,
        "total_alerts": sum(len(g["alerts"]) for g in result_games),
        "madden_season": madden_raw.get("season"),
        "week": games[0].get("week") if games else None,
    }


# ── INJURY HEATMAP ────────────────────────────────────────────────────────────

import re as _re
import time as _time
from concurrent.futures import ThreadPoolExecutor as _TPE, as_completed as _as_completed
from pathlib import Path as _Path

_HEATMAP_CACHE_FILE = _Path(__file__).parent.parent / "f5_backtest" / "_injury_heatmap_cache.json"
_HEATMAP_CACHE_TTL  = 6 * 3600  # 6 hours

_ESPN_TEAMS: dict[int, tuple[str, str]] = {
    1:  ("ATL", "Atlanta Falcons"),    2:  ("BUF", "Buffalo Bills"),
    3:  ("CHI", "Chicago Bears"),      4:  ("CIN", "Cincinnati Bengals"),
    5:  ("CLE", "Cleveland Browns"),   6:  ("DAL", "Dallas Cowboys"),
    7:  ("DEN", "Denver Broncos"),     8:  ("DET", "Detroit Lions"),
    9:  ("GB",  "Green Bay Packers"),  10: ("TEN", "Tennessee Titans"),
    11: ("IND", "Indianapolis Colts"), 12: ("KC",  "Kansas City Chiefs"),
    13: ("LV",  "Las Vegas Raiders"),  14: ("LAR", "LA Rams"),
    15: ("MIA", "Miami Dolphins"),     16: ("MIN", "Minnesota Vikings"),
    17: ("NE",  "New England Patriots"), 18: ("NO", "New Orleans Saints"),
    19: ("NYG", "New York Giants"),    20: ("NYJ", "New York Jets"),
    21: ("PHI", "Philadelphia Eagles"), 22: ("ARI", "Arizona Cardinals"),
    23: ("PIT", "Pittsburgh Steelers"), 24: ("LAC", "LA Chargers"),
    25: ("SF",  "San Francisco 49ers"), 26: ("SEA", "Seattle Seahawks"),
    27: ("TB",  "Tampa Bay Buccaneers"), 28: ("WSH", "Washington Commanders"),
    29: ("CAR", "Carolina Panthers"),  30: ("JAX", "Jacksonville Jaguars"),
    33: ("BAL", "Baltimore Ravens"),   34: ("HOU", "Houston Texans"),
}

_HM_POS_GROUP: dict[str, str] = {
    "QB": "QB",
    "RB": "RB", "HB": "RB", "FB": "RB",
    "WR": "WR", "TE": "WR",
    "LT": "OL", "RT": "OL", "LG": "OL", "RG": "OL", "C": "OL",
    "T":  "OL", "G":  "OL", "OT": "OL", "OG": "OL",
    "DE": "DL", "DT": "DL", "NT": "DL", "DL": "DL",
    "MLB": "LB", "OLB": "LB", "ILB": "LB", "LB": "LB",
    "CB": "DB", "FS": "DB", "SS": "DB", "S": "DB", "DB": "DB",
}

_HM_STATUS_WEIGHT: dict[str, int] = {"Out": 3, "Doubtful": 2, "Questionable": 1, "Probable": 0}
_HM_HDRS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
_OFF_COLS = ["QB", "OL", "WR", "RB"]
_DEF_COLS = ["DL", "LB", "DB"]


def _hm_fetch(url: str) -> dict:
    try:
        import urllib.request as _ur
        req = _ur.Request(url, headers=_HM_HDRS)
        return json.loads(_ur.urlopen(req, timeout=8).read())
    except Exception:
        return {}


def _hm_fetch_team(team_id: int, abbr: str, full_name: str) -> dict:
    """Fetch all injuries for one team. Returns per-position-group counts + players list."""
    base = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl"
    list_url = f"{base}/teams/{team_id}/injuries?limit=100"
    list_data = _hm_fetch(list_url)
    refs = [item.get("$ref", "") for item in list_data.get("items", []) if item.get("$ref")]

    if not refs:
        empty = {col: {"count": 0, "weight": 0, "players": []} for col in _OFF_COLS + _DEF_COLS}
        return {"team": abbr, "team_name": full_name, "groups": empty,
                "off_total": 0, "def_total": 0, "total_weight": 0, "players": []}

    # Resolve each injury ref to get status + athlete ref
    with _TPE(max_workers=20) as ex:
        futures = {ex.submit(_hm_fetch, ref): ref for ref in refs}
        inj_details = [f.result() for f in _as_completed(futures)]

    # Resolve unique athlete refs to get position
    ath_refs = {}
    for inj in inj_details:
        ath = inj.get("athlete", {})
        ref = ath.get("$ref", "") if isinstance(ath, dict) else ""
        if ref and ref not in ath_refs:
            ath_refs[ref] = None

    with _TPE(max_workers=20) as ex:
        futures = {ex.submit(_hm_fetch, ref): ref for ref in ath_refs}
        for f in _as_completed(futures):
            ref = futures[f]
            ath_refs[ref] = f.result()

    groups: dict[str, dict] = {col: {"count": 0, "weight": 0, "players": []} for col in _OFF_COLS + _DEF_COLS}
    all_players = []

    for inj in inj_details:
        status = inj.get("status", "")
        weight = _HM_STATUS_WEIGHT.get(status, 0)
        if weight == 0:
            continue
        ath_ref_url = inj.get("athlete", {}).get("$ref", "") if isinstance(inj.get("athlete"), dict) else ""
        ath_data = ath_refs.get(ath_ref_url, {}) or {}
        pos_raw = ath_data.get("position", {}).get("abbreviation", "") if isinstance(ath_data.get("position"), dict) else ""
        pos_group = _HM_POS_GROUP.get(pos_raw, "")
        name = ath_data.get("displayName", "Unknown")
        comment = inj.get("shortComment", "")

        player_entry = {"name": name, "pos": pos_raw, "group": pos_group, "status": status, "comment": comment}
        all_players.append(player_entry)

        if pos_group in groups:
            groups[pos_group]["count"] += 1
            groups[pos_group]["weight"] += weight
            groups[pos_group]["players"].append(player_entry)

    off_total = sum(groups[c]["count"] for c in _OFF_COLS)
    def_total = sum(groups[c]["count"] for c in _DEF_COLS)
    total_weight = sum(groups[c]["weight"] for c in _OFF_COLS + _DEF_COLS)

    return {
        "team": abbr,
        "team_name": full_name,
        "groups": groups,
        "off_total": off_total,
        "def_total": def_total,
        "total_weight": total_weight,
        "players": all_players,
    }


def _build_heatmap() -> dict:
    with _TPE(max_workers=8) as ex:
        futures = {
            ex.submit(_hm_fetch_team, tid, abbr, name): tid
            for tid, (abbr, name) in _ESPN_TEAMS.items()
        }
        teams = [f.result() for f in _as_completed(futures)]

    teams.sort(key=lambda t: -t["total_weight"])
    return {"teams": teams, "built_at": _time.time(), "columns": {"offense": _OFF_COLS, "defense": _DEF_COLS}}


@router.get("/injury-heatmap")
async def get_injury_heatmap(refresh: bool = False):
    """Per-team injury heatmap grouped by position (QB/OL/WR/RB offense, DL/LB/DB defense).
    Results cached 6h on disk. Pass ?refresh=true to force rebuild."""
    if not refresh and _HEATMAP_CACHE_FILE.exists():
        age = _time.time() - _HEATMAP_CACHE_FILE.stat().st_mtime
        if age < _HEATMAP_CACHE_TTL:
            return json.loads(_HEATMAP_CACHE_FILE.read_text())

    data = _build_heatmap()
    _HEATMAP_CACHE_FILE.write_text(json.dumps(data))
    return data
