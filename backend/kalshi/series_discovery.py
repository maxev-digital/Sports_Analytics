"""
Maps our sports pipeline's sport keys to Kalshi's series tickers.

This is intentionally a small, hand-maintained config, not a per-team
dictionary - league-level series tickers are stable identifiers Kalshi
controls (they don't change like team rosters do), confirmed directly
against Kalshi's live catalog via get_series(status='active') filtered to
category=='Sports' (2,335 active sports series today). That call is how you
discover *whether new series exist* if this list ever needs extending -
don't guess new tickers, look them up the same way.

Soccer (KXMLSGAME/KXEPLGAME) is deliberately excluded for now: those events
have a three-way (home/away/tie) market structure, not the two-way yes/no
structure every other sport here has, and the mispricing math hasn't been
extended to handle a draw outcome yet. Adding it later means adding a new
entry here plus draw-aware probability handling in the detector - not a
redo of anything already built.
"""

from __future__ import annotations

# our sport_key -> {"moneyline": series_ticker, "totals": series_ticker | None}
# Keys here are the FINAL sport_key passed to fetch_live_odds(), after
# resolve_sport_key() below (tennis needs resolving; everything else is a
# stable identity string).
SPORT_SERIES_MAP: dict[str, dict[str, str | None]] = {
    "baseball_mlb": {"moneyline": "KXMLBGAME", "totals": "KXMLBTOTAL"},
    "basketball_wnba": {"moneyline": "KXWNBAGAME", "totals": "KXWNBATOTAL"},
    "tennis_atp": {"moneyline": "KXATPMATCH", "totals": None},
    "tennis_wta": {"moneyline": "KXWTAMATCH", "totals": None},
    "icehockey_nhl": {"moneyline": "KXNHLGAME", "totals": "KXNHLTOTAL"},
    "basketball_nba": {"moneyline": "KXNBAGAME", "totals": None},  # off-season; ready for when it resumes
    "americanfootball_nfl": {"moneyline": "KXNFLGAME", "totals": None},  # off-season; verify ticker when season nears
}


def resolve_sport_key(sport_key: str) -> str:
    """Resolve our stable sport_key to whatever fetch_live_odds() actually
    needs right now.

    Tennis is the one exception: The Odds API keys tennis by tournament
    ("tennis_atp_wimbledon"), not by tour, and tennis_predictor.py already
    hardcodes the current tournament in its own SPORT_KEYS dict rather than
    resolving it dynamically - that's an existing, accepted limitation of
    the live pipeline, not something introduced here. Importing that dict
    directly (instead of hardcoding the same tournament string a second
    time) means this stays correct automatically whenever that dict is
    updated for the next tournament - no separate Kalshi-side edit needed.
    """
    if sport_key == "tennis_atp":
        from pipeline.models.prediction.tennis_predictor import SPORT_KEYS
        return SPORT_KEYS["atp"]
    if sport_key == "tennis_wta":
        from pipeline.models.prediction.tennis_predictor import SPORT_KEYS
        return SPORT_KEYS["wta"]
    return sport_key
