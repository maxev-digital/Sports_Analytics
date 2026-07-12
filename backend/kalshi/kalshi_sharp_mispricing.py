"""
Sharp-book-vs-Kalshi moneyline mispricing detector, generalized across every
sport in series_discovery.SPORT_SERIES_MAP. Detect-only - logs candidate
edges to kalshi_candidate_edges, does not place trades (that's execution.py,
wired to HITL confirm now and auto-trading later).

Team/player matching uses Kalshi's own `yes_sub_title` field (the readable
short name each market's "yes" side refers to, e.g. "Minnesota", "Toronto",
"Sesko") matched as a substring against our sports pipeline's full team/
player names - confirmed present on every market checked across MLB, WNBA,
and tennis. This needs no hardcoded per-sport team dictionary at all, unlike
the first MLB-only pass, which hardcoded 30 MLB team codes by hand - that
approach doesn't scale to 5+ sports and was replaced before being copied
further.

Sharp-book source (checked live against The Odds API on 2026-07-12):
Circa and SuperBook return ZERO games across every sport we checked (MLB,
WNBA, NHL, NBA, NFL, tennis) - their bookmaker keys exist in the API but no
odds actually flow through for any of them right now, so they can't be used
today no matter how the code is written. Pinnacle DOES have real coverage
(15/15 MLB games checked). SHARP_BOOK_KEYS below is Pinnacle plus a short
fallback list of offshore low-vig books that are confirmed present in the
feed, used only to fill in when Pinnacle has no line for a specific game -
not averaged in to dilute Pinnacle when it IS available. Revisit if Circa/
SuperBook ever gain coverage through this API or a different source.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from kalshi.kalshi_client import get_events, kalshi_fee_cents
from kalshi.series_discovery import SPORT_SERIES_MAP, resolve_sport_key

logger = logging.getLogger(__name__)

MIN_NET_EDGE_PCT = 5.0  # conservative starting threshold, net of fees
DEFAULT_CONTRACTS = 1   # sized for the $20 test account
_MAX_GAME_TIME_DRIFT_HOURS = 12  # disambiguates multi-game series on different days
_MIN_SANE_VIG_PCT = 0.0
_MAX_SANE_VIG_PCT = 20.0

# Priority-ordered sharp/low-vig book keys (The Odds API bookmaker keys).
# Pinnacle is the real sharp anchor; the rest are coverage fallback only -
# see module docstring for why Circa/SuperBook aren't in this list.
SHARP_BOOK_KEYS: frozenset[str] = frozenset({"pinnacle", "lowvig", "betonlineag", "bovada"})
MIN_SHARP_BOOKS_SAMPLED = 1  # Pinnacle alone is enough; this just guards against zero coverage


def _sharp_filtered_game(game: dict) -> dict:
    """Return a shallow copy of `game` with its bookmakers list restricted to
    SHARP_BOOK_KEYS, so the shared extract_consensus_line/_find_outcome_price
    helpers only ever see sharp-book data for Kalshi purposes. Does not
    mutate the original game dict - the same game object is also used by the
    broad-retail-book consensus elsewhere in the pipeline."""
    sharp_books = [bk for bk in game.get("bookmakers", []) if bk.get("key") in SHARP_BOOK_KEYS]
    return {**game, "bookmakers": sharp_books}


def _game_already_started(game: dict) -> bool:
    """Mirrors mlb_predictor.py's own in-progress-game guard. Once a game
    starts, sharp consensus and Kalshi's price both track a rapidly-moving
    live win probability instead of a stable pre-game price - a "mispricing"
    between the two at that point reflects update-timing lag, not a real
    inefficiency. Confirmed directly: a candidate logged mid-detection
    showed a 30%+ edge that had evaporated to a normal, small gap on a
    re-check minutes later, for a game whose commence_time was right at the
    detection timestamp."""
    commence = game.get("commence_time")
    if not commence:
        return False
    try:
        game_start = datetime.fromisoformat(str(commence).replace("Z", "+00:00"))
        if game_start.tzinfo is None:
            game_start = game_start.replace(tzinfo=timezone.utc)
        return game_start <= datetime.now(timezone.utc)
    except ValueError:
        return False


def _match_game_and_side(games: list[dict], kalshi_short_name: str,
                          reference_time_iso: str | None) -> tuple[dict, str] | None:
    """Find which game + which side (home/away full team name) a Kalshi
    market's short name refers to. Matches by substring containment (Kalshi
    says "Minnesota", our pipeline says "Minnesota Lynx") rather than exact
    equality, and disambiguates multi-game-series-on-different-days by
    picking the game whose commence_time is nearest the Kalshi market's
    actual game time (expected_expiration_time) - matching by name alone
    breaks whenever the same two teams/players play more than once in a
    short window, which is routine in MLB and tennis."""
    short = kalshi_short_name.strip().lower()
    matches = []
    for g in games:
        for side, full_name in (("home", g.get("home_team", "")), ("away", g.get("away_team", ""))):
            if full_name and short in full_name.strip().lower():
                matches.append((g, full_name))

    if not matches:
        return None
    if not reference_time_iso:
        return matches[0] if len(matches) == 1 else None

    ref = datetime.fromisoformat(reference_time_iso.replace("Z", "+00:00"))
    best, best_name, best_drift = None, None, None
    for g, full_name in matches:
        commence = g.get("commence_time")
        if not commence:
            continue
        try:
            g_time = datetime.fromisoformat(str(commence).replace("Z", "+00:00"))
        except ValueError:
            continue
        drift_hours = abs((g_time - ref).total_seconds()) / 3600
        if best_drift is None or drift_hours < best_drift:
            best, best_name, best_drift = g, full_name, drift_hours

    if best is None or best_drift > _MAX_GAME_TIME_DRIFT_HOURS:
        return None
    return best, best_name


def _books_sampled_for_h2h(sharp_game: dict) -> int:
    """extract_consensus_line's h2h result does not include a books-sampled
    count, so it's computed directly here rather than modifying the shared
    pipeline module for this one caller. Expects a game dict already
    filtered to SHARP_BOOK_KEYS via _sharp_filtered_game."""
    from pipeline.ingestion.live_odds import _find_outcome_price

    home_team, away_team = sharp_game.get("home_team", ""), sharp_game.get("away_team", "")
    count = 0
    for bk in sharp_game.get("bookmakers", []):
        outcomes = bk.get("markets", {}).get("h2h", [])
        if (_find_outcome_price(outcomes, home_team) is not None
                and _find_outcome_price(outcomes, away_team) is not None):
            count += 1
    return count


def _consensus_prob_for_team(game: dict, full_team_name: str) -> tuple[float, int] | None:
    """Return (consensus_implied_prob, books_sampled) for `full_team_name`
    winning this game, computed from sharp books only (SHARP_BOOK_KEYS) -
    not the full retail-book set used elsewhere in the pipeline.

    Guards against a real bug found (and fixed) in extract_consensus_line:
    it used to average raw American odds across books arithmetically, which
    is mathematically invalid once books disagree on which side is favored
    (mixed positive/negative signs for the same team) - confirmed directly:
    one game showed vig_pct = -27.6% (a negative vig is impossible for a
    real two-way market) and produced a false 22%+ "edge" as a result. The
    shared function itself is fixed now, but the sanity check stays here too
    as a defense-in-depth guard in case of any future regression."""
    from pipeline.ingestion.live_odds import extract_consensus_line

    sharp_game = _sharp_filtered_game(game)
    h2h = extract_consensus_line(sharp_game, "h2h")
    if not h2h:
        return None
    vig_pct = h2h.get("vig_pct")
    if vig_pct is None or not (_MIN_SANE_VIG_PCT <= vig_pct <= _MAX_SANE_VIG_PCT):
        logger.warning(
            "[kalshi_sharp_mispricing] Rejecting consensus for %s vs %s - implausible vig_pct=%s",
            game.get("away_team"), game.get("home_team"), vig_pct,
        )
        return None
    is_home = game.get("home_team", "").strip() == full_team_name.strip()
    is_away = game.get("away_team", "").strip() == full_team_name.strip()
    if not is_home and not is_away:
        return None
    prob = h2h.get("home_implied_prob") if is_home else h2h.get("away_implied_prob")
    if prob is None:
        return None
    return prob, _books_sampled_for_h2h(sharp_game)


def detect_moneyline_mispricing(client, sport_key: str) -> list[dict]:
    """Compare Kalshi contract prices to sharp-book consensus win probability
    for the same game/team, for a single sport. Returns a list of
    candidate-edge dicts (not yet saved, not yet traded)."""
    from pipeline.ingestion.live_odds import fetch_live_odds

    series_cfg = SPORT_SERIES_MAP.get(sport_key)
    if not series_cfg or not series_cfg.get("moneyline"):
        raise ValueError(f"No Kalshi moneyline series configured for sport_key={sport_key!r}")

    games = fetch_live_odds(resolve_sport_key(sport_key))
    games = [g for g in games if not _game_already_started(g)]
    events = get_events(client, series_cfg["moneyline"], status="open")

    candidates = []
    for event in events:
        for market in event["markets"]:
            if market["yes_ask_cents"] is None:
                continue  # no live quote right now - skip, don't guess
            kalshi_name = market.get("yes_sub_title")
            if not kalshi_name:
                continue

            matched = _match_game_and_side(games, kalshi_name, market.get("expected_expiration_time"))
            if not matched:
                continue
            game, full_team_name = matched

            result = _consensus_prob_for_team(game, full_team_name)
            if not result:
                continue
            consensus_prob, books_sampled = result
            if books_sampled < MIN_SHARP_BOOKS_SAMPLED:
                continue  # no sharp-book coverage for this game right now

            kalshi_implied_prob = market["yes_ask_cents"] / 100.0
            raw_edge_pct = (consensus_prob - kalshi_implied_prob) * 100
            fee_cents = kalshi_fee_cents(DEFAULT_CONTRACTS, market["yes_ask_cents"])
            # Fee is charged on entry AND exit - approximate exit at the same
            # price for a conservative (worst-case) net edge estimate.
            fee_pct_of_notional = (fee_cents * 2) / (DEFAULT_CONTRACTS * 100) * 100 / 100
            net_edge_pct = raw_edge_pct - fee_pct_of_notional

            if net_edge_pct >= MIN_NET_EDGE_PCT:
                candidates.append({
                    "detector": f"kalshi_sharp_mispricing_{sport_key}_ml",
                    "market_ticker": market["ticker"],
                    "sport": sport_key,
                    "game_id": game.get("game_id") or game.get("id", ""),
                    "true_probability": round(consensus_prob, 4),
                    "kalshi_price_cents": market["yes_ask_cents"],
                    "raw_edge_pct": round(raw_edge_pct, 2),
                    "net_edge_pct": round(net_edge_pct, 2),
                    "books_sampled": books_sampled,
                })

    return candidates


def list_markets_for_sport(client, sport_key: str) -> list[dict]:
    """Return every open Kalshi market for one sport, regardless of whether
    it clears the edge threshold - a browse/overview view, unlike
    detect_moneyline_mispricing which only returns qualifying candidates.
    Still computes sharp consensus + edge where a game/team match exists,
    so the same row can show "no edge right now" instead of just omitting
    the game entirely."""
    from pipeline.ingestion.live_odds import fetch_live_odds

    series_cfg = SPORT_SERIES_MAP.get(sport_key)
    if not series_cfg or not series_cfg.get("moneyline"):
        raise ValueError(f"No Kalshi moneyline series configured for sport_key={sport_key!r}")

    games = fetch_live_odds(resolve_sport_key(sport_key))
    events = get_events(client, series_cfg["moneyline"], status="open")

    rows = []
    for event in events:
        for market in event["markets"]:
            kalshi_name = market.get("yes_sub_title")
            matched = _match_game_and_side(games, kalshi_name, market.get("expected_expiration_time")) if kalshi_name else None

            row = {
                "market_ticker": market["ticker"],
                "event_ticker": market.get("event_ticker"),
                "title": market.get("title"),
                "yes_sub_title": kalshi_name,
                "sport": sport_key,
                "kalshi_price_cents": market["yes_ask_cents"],
                "expected_expiration_time": market.get("expected_expiration_time"),
                "already_started": False,
                "matched": False,
                "true_probability": None,
                "raw_edge_pct": None,
                "net_edge_pct": None,
                "books_sampled": 0,
            }

            if matched:
                game, full_team_name = matched
                row["already_started"] = _game_already_started(game)
                row["game_id"] = game.get("game_id") or game.get("id", "")
                result = _consensus_prob_for_team(game, full_team_name)
                if result and market["yes_ask_cents"] is not None:
                    consensus_prob, books_sampled = result
                    kalshi_implied_prob = market["yes_ask_cents"] / 100.0
                    raw_edge_pct = (consensus_prob - kalshi_implied_prob) * 100
                    fee_cents = kalshi_fee_cents(DEFAULT_CONTRACTS, market["yes_ask_cents"])
                    fee_pct_of_notional = (fee_cents * 2) / (DEFAULT_CONTRACTS * 100) * 100 / 100
                    row["matched"] = True
                    row["true_probability"] = round(consensus_prob, 4)
                    row["raw_edge_pct"] = round(raw_edge_pct, 2)
                    row["net_edge_pct"] = round(raw_edge_pct - fee_pct_of_notional, 2)
                    row["books_sampled"] = books_sampled

            rows.append(row)

    return rows


def detect_all_sports(client) -> list[dict]:
    """Run detect_moneyline_mispricing across every configured sport. One
    sport's failure (bad data, series not active yet, etc.) doesn't block
    the others."""
    all_candidates = []
    for sport_key in SPORT_SERIES_MAP:
        try:
            found = detect_moneyline_mispricing(client, sport_key)
            if found:
                logger.info("[kalshi_sharp_mispricing] %s: %d candidate(s)", sport_key, len(found))
            all_candidates.extend(found)
        except Exception:
            logger.exception("[kalshi_sharp_mispricing] Detection failed for sport_key=%s", sport_key)
    return all_candidates


def log_candidate_edges(candidates: list[dict]) -> int:
    """Persist detected candidates to kalshi_candidate_edges. Detect-only -
    no orders are placed here."""
    from pipeline.db.connection import execute_write

    saved = 0
    for c in candidates:
        try:
            execute_write(
                """
                INSERT INTO kalshi_candidate_edges
                    (detector, market_ticker, sport, game_id, true_probability,
                     kalshi_price_cents, raw_edge_pct, net_edge_pct, books_sampled, detected_at)
                VALUES
                    (%(detector)s, %(market_ticker)s, %(sport)s, %(game_id)s, %(true_probability)s,
                     %(kalshi_price_cents)s, %(raw_edge_pct)s, %(net_edge_pct)s, %(books_sampled)s, %(now)s)
                """,
                {**c, "now": datetime.now(timezone.utc)},
            )
            saved += 1
        except Exception as exc:
            logger.error("[kalshi_sharp_mispricing] Failed to log candidate: %s", exc)
    return saved
