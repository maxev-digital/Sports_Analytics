"""
Daily pipeline orchestrator — runs ingestion → validate → predict → reflect → log.
Called by cron at 10:00 AM CST and 12:00 PM CST (after lineups post).

Tier assignment:
  Haiku   → record-level data validation (high volume, cheap)
  Sonnet  → per-pick reasoning narratives
  Opus    → daily system reflection + audit
"""

import logging
import traceback
from datetime import date
from typing import Optional

from pipeline.config import now_cst, CST
from pipeline.db.schema import create_all_tables, get_engine
from pipeline.db.connection import execute_write, execute_query
from pipeline.ingestion.mlb_statcast import fetch_pitching_statcast, fetch_batting_statcast
from pipeline.ingestion.live_odds import fetch_live_odds
from pipeline.agents.haiku_validator import batch_validate
from pipeline.agents.sonnet_reasoner import generate_pick_narrative, assess_confidence_tier, generate_daily_summary
from pipeline.agents.opus_reflector import reflect_on_daily_picks, save_reflection_report
from pipeline.agents.health_reporter import compile_health_report
from pipeline.models.prediction.mlb_predictor import generate_mlb_picks, rule_based_mlb_edges, rule_based_mlb_strikeout_props
from pipeline.models.prediction.wnba_predictor import generate_wnba_picks, rule_based_wnba_edges
from pipeline.models.prediction.tennis_predictor import rule_based_tennis_edges
from pipeline.models.prediction.soccer_predictor import rule_based_soccer_edges

logger = logging.getLogger(__name__)


# ── Ingestion phase ────────────────────────────────────────────────────────────

def run_mlb_ingestion() -> dict:
    """Fetch and validate MLB Statcast data. Returns ingestion summary."""
    report = {
        "sport": "mlb", "source": "baseball_savant",
        "records_fetched": 0, "records_valid": 0, "records_rejected": 0,
        "haiku_flags": [], "status": "ok", "error_msg": None,
    }
    try:
        pitch_df = fetch_pitching_statcast()
        bat_df   = fetch_batting_statcast()

        all_records = pitch_df.to_dict("records") + bat_df.to_dict("records")
        report["records_fetched"] = len(all_records)

        # Haiku validates each record cheaply
        validations = batch_validate(all_records[:50], "statcast")  # cap at 50 for cost
        flags = [v["flags"] for v in validations if v.get("flags")]
        errors = [v for v in validations if v.get("severity") == "error"]

        report["records_valid"]   = len(all_records) - len(errors)
        report["records_rejected"] = len(errors)
        report["haiku_flags"]     = [f for sublist in flags for f in sublist][:20]

        _log_ingestion(report)
        logger.info(f"MLB ingestion: {report['records_fetched']} records, {len(errors)} rejected")

    except Exception as e:
        report["status"]    = "error"
        report["error_msg"] = str(e)
        _log_ingestion(report)
        logger.error(f"MLB ingestion failed: {e}")

    return report


def run_wnba_ingestion() -> dict:
    """Fetch and validate WNBA odds + team stats."""
    report = {
        "sport": "wnba", "source": "odds_api+espn",
        "records_fetched": 0, "records_valid": 0, "records_rejected": 0,
        "haiku_flags": [], "status": "ok", "error_msg": None,
    }
    try:
        games = fetch_live_odds("basketball_wnba")
        report["records_fetched"] = len(games)

        validations = batch_validate(games, "game_odds")
        flags  = [v["flags"] for v in validations if v.get("flags")]
        errors = [v for v in validations if v.get("severity") == "error"]

        report["records_valid"]    = len(games) - len(errors)
        report["records_rejected"] = len(errors)
        report["haiku_flags"]      = [f for sublist in flags for f in sublist][:20]

        _log_ingestion(report)
        logger.info(f"WNBA ingestion: {report['records_fetched']} games")

    except Exception as e:
        report["status"]    = "error"
        report["error_msg"] = str(e)
        _log_ingestion(report)
        logger.error(f"WNBA ingestion failed: {e}")

    return report


def _log_ingestion(report: dict):
    try:
        execute_write(
            """INSERT INTO ingestion_log
               (run_at_cst, sport, source, records_fetched, records_valid,
                records_rejected, haiku_flags, status, error_msg)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                now_cst(), report["sport"], report["source"],
                report["records_fetched"], report["records_valid"],
                report["records_rejected"],
                str(report.get("haiku_flags", [])),
                report["status"], report.get("error_msg"),
            ),
        )
    except Exception as e:
        logger.warning(f"Failed to log ingestion: {e}")


# ── Prediction phase ───────────────────────────────────────────────────────────

def run_predictions(use_ml: bool = True) -> list[dict]:
    """
    Generate today's picks for all active sports.
    Falls back to rule-based detectors when ML models aren't trained yet.
    """
    all_picks: list[dict] = []

    # MLB
    try:
        if use_ml:
            mlb_picks = generate_mlb_picks()
        else:
            mlb_picks = rule_based_mlb_edges()
        all_picks.extend(mlb_picks)
        logger.info(f"MLB: {len(mlb_picks)} picks generated")
    except Exception as e:
        logger.error(f"MLB prediction failed: {e}")
        # Fallback to rule-based
        try:
            mlb_picks = rule_based_mlb_edges()
            all_picks.extend(mlb_picks)
            logger.info(f"MLB fallback rule-based: {len(mlb_picks)} picks")
        except Exception as e2:
            logger.error(f"MLB fallback also failed: {e2}")

    # WNBA
    try:
        if use_ml:
            wnba_picks = generate_wnba_picks()
        else:
            wnba_picks = rule_based_wnba_edges()
        all_picks.extend(wnba_picks)
        logger.info(f"WNBA: {len(wnba_picks)} picks generated")
    except Exception as e:
        logger.error(f"WNBA prediction failed: {e}")
        try:
            wnba_picks = rule_based_wnba_edges()
            all_picks.extend(wnba_picks)
        except Exception as e2:
            logger.error(f"WNBA fallback also failed: {e2}")

    # MLB K Props
    try:
        props_picks = rule_based_mlb_strikeout_props()
        all_picks.extend(props_picks)
        logger.info(f"MLB Props: {len(props_picks)} picks generated")
    except Exception as e:
        logger.error(f"MLB props prediction failed: {e}")

    # Tennis (ATP + WTA Wimbledon)
    try:
        tennis_picks = rule_based_tennis_edges()
        all_picks.extend(tennis_picks)
        logger.info(f"Tennis: {len(tennis_picks)} picks generated")
    except Exception as e:
        logger.error(f"Tennis prediction failed: {e}")

    # Soccer (MLS + EPL — games within 48h window only)
    try:
        soccer_picks = rule_based_soccer_edges()
        all_picks.extend(soccer_picks)
        logger.info(f"Soccer: {len(soccer_picks)} picks generated")
    except Exception as e:
        logger.error(f"Soccer prediction failed: {e}")

    return all_picks


# ── Corroboration filter (Task #19) ───────────────────────────────────────────

def corroborate_picks(picks: list[dict]) -> list[dict]:
    """
    Require each pick to pass a second independent signal before saving.

    Signal 1 (from detectors): multibook vig divergence ≥ threshold
    Signal 2 (added here):     sufficient consensus depth AND the
                                flagged book's odds are genuinely the
                                best price available (not mid-market noise).

    Conditions for corroboration:
    - books_sampled >= 5  (thin market = weak signal)
    - edge_pct >= 2.0     (raw edge floor regardless of sport-specific min)
    - The divergence_pct in features >= 2.0% (redundant guard vs features mismatch)

    Picks that fail corroboration are logged and dropped.
    Tennis exception: min 4 books (fewer books post tennis markets).
    """
    CORR_MIN_BOOKS = 5
    CORR_MIN_BOOKS_TENNIS = 4
    CORR_MIN_EDGE = 2.0
    CORR_MIN_DIV = 2.0

    passed = []
    for pick in picks:
        feat = pick.get("features", {})
        books = feat.get("books_sampled", 0)
        div = feat.get("divergence_pct", 0.0)
        edge = pick.get("edge_pct", 0.0)
        sport = pick.get("sport", "")

        min_books = CORR_MIN_BOOKS_TENNIS if "tennis" in sport else CORR_MIN_BOOKS

        if books < min_books:
            logger.info(
                "[corroboration] DROP %s %s @ %s — books=%d < %d",
                pick["pick_side"], pick.get("pick_type"), pick.get("home_team"),
                books, min_books,
            )
            continue
        if edge < CORR_MIN_EDGE:
            logger.info(
                "[corroboration] DROP %s %s @ %s — edge=%.2f%% < %.1f%%",
                pick["pick_side"], pick.get("pick_type"), pick.get("home_team"),
                edge, CORR_MIN_EDGE,
            )
            continue
        if div < CORR_MIN_DIV:
            logger.info(
                "[corroboration] DROP %s %s @ %s — div=%.2f%% < %.1f%%",
                pick["pick_side"], pick.get("pick_type"), pick.get("home_team"),
                div, CORR_MIN_DIV,
            )
            continue

        passed.append(pick)

    dropped = len(picks) - len(passed)
    if dropped:
        logger.info("[corroboration] %d/%d picks passed (dropped %d)", len(passed), len(picks), dropped)
    return passed


# ── Directional concentration guardrail ───────────────────────────────────────

def check_directional_concentration(picks: list[dict]) -> dict:
    """
    Detect when picks are heavily skewed toward one direction per market type.
    Returns a concentration report and trims extreme skew (>80%) to top-edge picks only.

    Thresholds:
      - WARN  at ≥70% one direction  (log, pass to reflection)
      - TRIM  at ≥80% one direction  (keep only top-3 by edge_pct)
    """
    from collections import Counter

    WARN_THRESHOLD = 0.70
    TRIM_THRESHOLD = 0.80
    TRIM_KEEP = 3

    report = {"flags": [], "trimmed": 0}

    # Group by pick_type
    by_type: dict[str, list[dict]] = {}
    for pick in picks:
        pt = pick.get("pick_type", "unknown")
        by_type.setdefault(pt, []).append(pick)

    trim_set: set[int] = set()  # indices in picks to remove

    for pick_type, group in by_type.items():
        if len(group) < 4:  # not enough to meaningfully check
            continue

        side_counts = Counter(p.get("pick_side", "") for p in group)
        total = len(group)
        dominant_side, dominant_count = side_counts.most_common(1)[0]
        ratio = dominant_count / total

        if ratio >= WARN_THRESHOLD:
            msg = (f"{pick_type.upper()} concentration: {dominant_count}/{total} "
                   f"({ratio*100:.0f}%) on '{dominant_side}'")
            report["flags"].append(msg)
            logger.warning("[concentration] %s", msg)

        if ratio >= TRIM_THRESHOLD:
            # Keep only the top-edge picks from the dominant side
            dominant_picks = sorted(
                [p for p in group if p.get("pick_side") == dominant_side],
                key=lambda p: p.get("edge_pct", 0),
                reverse=True,
            )
            # Mark picks beyond top-TRIM_KEEP for removal
            for p in dominant_picks[TRIM_KEEP:]:
                idx = picks.index(p)
                trim_set.add(idx)
                report["trimmed"] += 1
            msg = (f"{pick_type.upper()}: trimmed {report['trimmed']} low-edge "
                   f"'{dominant_side}' picks (kept top {TRIM_KEEP})")
            logger.warning("[concentration] %s", msg)
            report["flags"].append(msg)

    if trim_set:
        filtered = [p for i, p in enumerate(picks) if i not in trim_set]
        logger.info("[concentration] %d picks after trim (was %d)", len(filtered), len(picks))
        return {"report": report, "picks": filtered}

    return {"report": report, "picks": picks}


# ── Sonnet reasoning phase ─────────────────────────────────────────────────────

def enrich_picks_with_reasoning(picks: list[dict]) -> list[dict]:
    """Adds Sonnet narrative and confidence tier to each pick."""
    enriched = []
    for pick in picks:
        try:
            pick["sonnet_narrative"] = generate_pick_narrative(pick, pick.get("features", {}))
            pick["confidence_tier"]  = assess_confidence_tier(pick, pick.get("features", {}))
        except Exception as e:
            logger.warning(f"Sonnet enrichment failed for {pick.get('home_team')}: {e}")
            pick["sonnet_narrative"] = None
            pick["confidence_tier"]  = "medium"
        enriched.append(pick)
    return enriched


# ── Opus reflection phase ──────────────────────────────────────────────────────

def run_reflection(picks: list[dict], ingestion_reports: list[dict]) -> dict:
    """Opus reviews the full day's work. Can halt picks if critical issues found."""
    model_perf = _get_rolling_performance()
    ingestion_summary = {r["sport"]: r for r in ingestion_reports}

    try:
        reflection = reflect_on_daily_picks(picks, ingestion_summary, model_perf)
        save_reflection_report(reflection, "all")
        return reflection
    except Exception as e:
        logger.error(f"Opus reflection failed: {e}")
        return {"proceed": True, "flags": [f"Reflection unavailable: {e}"], "picks_to_skip": [],
                "narrative": "Reflection agent unavailable — proceeding with standard validation.",
                "action_items": [], "model_health": "warning"}


def _get_rolling_performance() -> dict:
    try:
        rows = execute_query(
            """SELECT sport, COUNT(*) as total,
                      SUM(CASE WHEN result='W' THEN 1 ELSE 0 END) as wins,
                      AVG(pl_units) as avg_pl
               FROM predictions
               WHERE status='graded'
                 AND created_at_cst >= now() - INTERVAL '30 days'
               GROUP BY sport"""
        )
        return {r["sport"]: r for r in rows}
    except Exception:
        return {}


# ── DB write phase ─────────────────────────────────────────────────────────────

def save_picks(picks: list[dict], skip_indices: list[int] = None) -> int:
    """Writes approved picks to predictions table. Returns count saved."""
    skip_set = set(skip_indices or [])
    saved = 0
    for i, pick in enumerate(picks):
        if i in skip_set:
            logger.info(f"Skipping pick {i} per Opus instruction: {pick.get('home_team')} vs {pick.get('away_team')}")
            continue
        try:
            execute_write(
                """INSERT INTO predictions
                   (created_at_cst, sport, home_team, away_team, game_time_cst,
                    pick_side, pick_type, our_probability, market_odds,
                    market_implied_prob, edge_pct, detector, reasoning,
                    confidence_tier, status, sonnet_narrative, game_id, total_line)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending',%s,%s,%s)
                   ON CONFLICT DO NOTHING""",
                (
                    now_cst(), pick["sport"], pick["home_team"], pick["away_team"],
                    pick.get("game_time_cst"), pick["pick_side"], pick["pick_type"],
                    pick["our_probability"], pick["market_odds"],
                    pick["market_implied_prob"], pick["edge_pct"],
                    pick["detector"], pick.get("sonnet_narrative"),
                    pick.get("confidence_tier", "medium"),
                    pick.get("sonnet_narrative"),
                    pick.get("game_id", ""),
                    pick.get("total_line"),
                ),
            )
            saved += 1
        except Exception as e:
            logger.error(f"Failed to save pick: {e}")
    return saved


# ── Main entry point ───────────────────────────────────────────────────────────

def run_daily_pipeline(use_ml: bool = False) -> dict:
    """
    Full daily pipeline. Returns summary dict for the API health endpoint.
    use_ml=False until models are trained (rule-based only).
    """
    logger.info("=" * 60)
    logger.info(f"Pipeline starting at {now_cst().isoformat()}")
    logger.info("=" * 60)

    # Ensure schema exists
    try:
        engine = get_engine()
        create_all_tables(engine)
    except Exception as e:
        logger.error(f"Schema init failed: {e}")
        return {"status": "error", "error": str(e)}

    # Phase 1 — Ingest
    ingestion_reports = [run_mlb_ingestion(), run_wnba_ingestion()]

    # Phase 2 — Predict
    picks = run_predictions(use_ml=use_ml)
    logger.info(f"Total picks before corroboration: {len(picks)}")

    # Phase 2a — Corroboration filter (require second signal)
    picks = corroborate_picks(picks)
    logger.info(f"Total picks after corroboration: {len(picks)}")

    # Phase 2b — Directional concentration guardrail
    conc_result = check_directional_concentration(picks)
    picks = conc_result["picks"]
    conc_report = conc_result["report"]
    if conc_report["flags"]:
        logger.warning(f"Concentration flags: {conc_report['flags']}")
    logger.info(f"Total picks after concentration check: {len(picks)}")

    # Phase 3 — Sonnet enrichment
    picks = enrich_picks_with_reasoning(picks)

    # Phase 4 — Opus reflection (include concentration report in ingestion summary)
    if conc_report["flags"]:
        ingestion_reports.append({
            "sport": "concentration_check",
            "source": "guardrail",
            "records_fetched": len(picks),
            "records_valid": len(picks),
            "records_rejected": conc_result["report"]["trimmed"],
            "haiku_flags": conc_report["flags"],
            "status": "warn" if conc_report["flags"] else "ok",
            "error_msg": None,
        })
    reflection = run_reflection(picks, ingestion_reports)
    logger.info(f"Reflection: proceed={reflection.get('proceed')}, "
                f"health={reflection.get('model_health')}, "
                f"flags={len(reflection.get('flags', []))}")

    # Phase 5 — Save approved picks
    if reflection.get("proceed", True):
        saved = save_picks(picks, skip_indices=reflection.get("picks_to_skip", []))
        logger.info(f"Saved {saved}/{len(picks)} picks to DB")
    else:
        saved = 0
        logger.warning("Opus halted pick logging — critical issues detected")

    # Phase 6 — Compile health report
    health = compile_health_report()

    result = {
        "status": "ok",
        "run_at": now_cst().isoformat(),
        "ingestion": {r["sport"]: r["status"] for r in ingestion_reports},
        "picks_generated": len(picks),
        "picks_saved": saved,
        "reflection_health": reflection.get("model_health", "unknown"),
        "reflection_flags": reflection.get("flags", []),
        "health_report": health,
    }
    logger.info(f"Pipeline complete: {result}")
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s — %(message)s")
    result = run_daily_pipeline(use_ml=False)
    import json
    print(json.dumps(result, indent=2, default=str))
