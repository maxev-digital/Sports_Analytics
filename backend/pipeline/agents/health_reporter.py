"""
Health reporting layer for the Sports Betting Analytics pipeline.

Provides a compiled pipeline health report, today's pick list, and historical
performance data by querying PostgreSQL. No Claude API calls — this module is
a pure database query and aggregation layer.

All public functions are fail-open: a DB error returns an empty/default
structure and logs an error rather than crashing the caller.
"""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import Any

from pipeline.config import now_cst
from pipeline.db.connection import execute_query

logger = logging.getLogger(__name__)


def compile_health_report(date_cst: date | None = None) -> dict[str, Any]:
    """
    Compile a structured health report for the pipeline as of a given date.

    Queries four tables:
    - ``ingestion_log``      – data ingestion run metadata
    - ``predictions``        – generated picks for the day
    - ``model_performance``  – model accuracy / calibration metrics
    - ``reflection_reports`` – daily Opus reflection output

    Derives ``overall_status`` from model_health and ingestion error signals.

    Args:
        date_cst: Target date in CST. Defaults to today (CST) if not supplied.

    Returns:
        dict with keys:
            overall_status   (str)   – 'healthy' | 'warning' | 'critical'
            ingestion        (dict)  – records_ingested, error_count, freshness_mins
            predictions      (dict)  – total_picks, sport_count, avg_edge_pct, sports
            model_perf       (dict)  – accuracy, roi, brier_score, sample_size
            reflection       (dict)  – proceed, model_health, narrative, flags
            action_items     (list)  – consolidated operator action list from reflection
            last_updated_cst (str)   – ISO-8601 timestamp of report generation
        On partial DB failures, affected sub-dicts contain an ``"error"`` key with
        the exception message so the caller can still render partial data.
    """
    if date_cst is None:
        date_cst = now_cst().date()

    report: dict[str, Any] = {
        "overall_status": "healthy",
        "ingestion": {},
        "predictions": {},
        "model_perf": {},
        "reflection": {},
        "action_items": [],
        "last_updated_cst": now_cst().isoformat(),
    }

    # ------------------------------------------------------------------
    # Ingestion stats
    # ------------------------------------------------------------------
    try:
        ing_rows = execute_query(
            """
            SELECT
                COALESCE(SUM(records_ingested), 0)::int             AS records_ingested,
                COALESCE(SUM(error_count), 0)::int                  AS error_count,
                COALESCE(
                    EXTRACT(EPOCH FROM (NOW() - MAX(completed_at))) / 60,
                    999
                )::int                                              AS freshness_mins
            FROM ingestion_log
            WHERE run_date = %(run_date)s
            """,
            {"run_date": date_cst},
        )
        if ing_rows:
            report["ingestion"] = {
                "records_ingested": int(ing_rows[0].get("records_ingested", 0)),
                "error_count": int(ing_rows[0].get("error_count", 0)),
                "freshness_mins": int(ing_rows[0].get("freshness_mins", 999)),
            }
        else:
            report["ingestion"] = {
                "records_ingested": 0,
                "error_count": 0,
                "freshness_mins": 999,
            }
    except Exception as exc:
        logger.error("compile_health_report: ingestion_log query failed: %s", exc)
        report["ingestion"] = {"error": str(exc)}

    # ------------------------------------------------------------------
    # Predictions stats
    # ------------------------------------------------------------------
    try:
        pred_rows = execute_query(
            """
            SELECT
                COUNT(*)                                    AS total_picks,
                COUNT(DISTINCT sport)                       AS sport_count,
                ROUND(AVG(edge_pct)::numeric, 2)            AS avg_edge_pct,
                ARRAY_AGG(DISTINCT sport ORDER BY sport)    AS sports
            FROM predictions
            WHERE prediction_date = %(pred_date)s
            """,
            {"pred_date": date_cst},
        )
        if pred_rows:
            row = pred_rows[0]
            report["predictions"] = {
                "total_picks": int(row.get("total_picks", 0)),
                "sport_count": int(row.get("sport_count", 0)),
                "avg_edge_pct": float(row.get("avg_edge_pct") or 0.0),
                "sports": list(row.get("sports") or []),
            }
        else:
            report["predictions"] = {
                "total_picks": 0,
                "sport_count": 0,
                "avg_edge_pct": 0.0,
                "sports": [],
            }
    except Exception as exc:
        logger.error("compile_health_report: predictions query failed: %s", exc)
        report["predictions"] = {"error": str(exc)}

    # ------------------------------------------------------------------
    # Model performance stats
    # ------------------------------------------------------------------
    try:
        mp_rows = execute_query(
            """
            SELECT
                ROUND(AVG(accuracy)::numeric, 4)    AS accuracy,
                ROUND(AVG(roi)::numeric, 4)          AS roi,
                ROUND(AVG(brier_score)::numeric, 4)  AS brier_score,
                COALESCE(SUM(sample_size), 0)::int   AS sample_size
            FROM model_performance
            WHERE perf_date = %(perf_date)s
            """,
            {"perf_date": date_cst},
        )
        if mp_rows:
            row = mp_rows[0]
            report["model_perf"] = {
                "accuracy": float(row.get("accuracy") or 0.0),
                "roi": float(row.get("roi") or 0.0),
                "brier_score": float(row.get("brier_score") or 0.0),
                "sample_size": int(row.get("sample_size") or 0),
            }
        else:
            report["model_perf"] = {
                "accuracy": 0.0,
                "roi": 0.0,
                "brier_score": 0.0,
                "sample_size": 0,
            }
    except Exception as exc:
        logger.error("compile_health_report: model_performance query failed: %s", exc)
        report["model_perf"] = {"error": str(exc)}

    # ------------------------------------------------------------------
    # Reflection report summary (most recent for the date)
    # ------------------------------------------------------------------
    try:
        ref_rows = execute_query(
            """
            SELECT
                proceed,
                model_health,
                flags,
                action_items,
                narrative
            FROM reflection_reports
            WHERE report_date = %(report_date)s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            {"report_date": date_cst},
        )

        def _parse_json_field(val: Any) -> list:
            """Safely parse a field that may be a JSON string or already a list."""
            if isinstance(val, list):
                return val
            if isinstance(val, str):
                try:
                    parsed = json.loads(val)
                    return parsed if isinstance(parsed, list) else []
                except (json.JSONDecodeError, ValueError):
                    return []
            return []

        if ref_rows:
            row = ref_rows[0]
            flags = _parse_json_field(row.get("flags"))
            action_items = _parse_json_field(row.get("action_items"))
            report["reflection"] = {
                "proceed": bool(row.get("proceed", True)),
                "model_health": row.get("model_health", "warning"),
                "narrative": str(row.get("narrative", "")),
                "flags": flags,
            }
            report["action_items"] = action_items
        else:
            report["reflection"] = {
                "proceed": True,
                "model_health": "warning",
                "narrative": "No reflection report found for this date.",
                "flags": [],
            }
            report["action_items"] = []

    except Exception as exc:
        logger.error("compile_health_report: reflection_reports query failed: %s", exc)
        report["reflection"] = {"error": str(exc)}

    # ------------------------------------------------------------------
    # Derive overall_status
    # ------------------------------------------------------------------
    model_health: str = report.get("reflection", {}).get("model_health", "warning")
    error_count: Any = report.get("ingestion", {}).get("error_count", 0)
    freshness_mins: Any = report.get("ingestion", {}).get("freshness_mins", 0)

    if model_health == "critical" or (
        isinstance(error_count, int) and error_count > 20
    ):
        report["overall_status"] = "critical"
    elif model_health == "warning" or (
        isinstance(freshness_mins, int) and freshness_mins > 120
    ):
        report["overall_status"] = "warning"
    else:
        report["overall_status"] = "healthy"

    return report


def get_todays_picks(sport: str | None = None) -> list[dict[str, Any]]:
    """
    Return today's picks sorted by edge_pct descending.

    Queries the ``predictions`` table for today's date in CST with an optional
    sport filter.

    Args:
        sport: Optional sport code filter (e.g. 'MLB', 'NBA', 'NFL').
               Case-insensitive — uppercased internally. If ``None``, returns
               all picks for today regardless of sport.

    Returns:
        List of row dicts from the ``predictions`` table, sorted by edge_pct
        descending. Returns an empty list on any query error.
    """
    today = now_cst().date()

    try:
        if sport is not None:
            rows = execute_query(
                """
                SELECT *
                FROM predictions
                WHERE prediction_date = %(today)s
                  AND sport = %(sport)s
                ORDER BY edge_pct DESC
                """,
                {"today": today, "sport": sport.upper()},
            )
        else:
            rows = execute_query(
                """
                SELECT *
                FROM predictions
                WHERE prediction_date = %(today)s
                ORDER BY edge_pct DESC
                """,
                {"today": today},
            )
        return rows

    except Exception as exc:
        logger.error(
            "get_todays_picks failed (sport=%s): %s", sport or "ALL", exc
        )
        return []


def get_performance_history(
    sport: str,
    days: int = 30,
) -> list[dict[str, Any]]:
    """
    Return graded prediction history for a sport over the past N days.

    Joins ``predictions`` with ``graded_results`` to produce a per-pick
    profit/loss record. Picks that have not yet been graded appear with
    result='pending' and pl_units=0.0.

    Args:
        sport: Sport code (e.g. 'MLB', 'NBA'). Case-insensitive.
        days:  Number of calendar days of history to return (default 30).

    Returns:
        List of dicts with keys:
            date      (date)  – Prediction date.
            sport     (str)   – Sport code.
            pick_type (str)   – Bet type (e.g. 'spread', 'total', 'ml').
            result    (str)   – 'win' | 'loss' | 'push' | 'pending'.
            pl_units  (float) – Profit/loss in units (+1.0 for a win to -1.0 for a loss).
            edge_pct  (float) – Model edge percentage at time of pick.
        Returns an empty list on any query error.
    """
    since = now_cst().date() - timedelta(days=days)

    try:
        rows = execute_query(
            """
            SELECT
                p.prediction_date                       AS date,
                p.sport,
                p.pick_type,
                COALESCE(r.result, 'pending')           AS result,
                COALESCE(r.pl_units, 0.0)::float        AS pl_units,
                p.edge_pct::float                       AS edge_pct
            FROM predictions p
            LEFT JOIN graded_results r
                   ON r.prediction_id = p.id
            WHERE p.sport = %(sport)s
              AND p.prediction_date >= %(since)s
            ORDER BY p.prediction_date DESC
            """,
            {"sport": sport.upper(), "since": since},
        )
        return rows

    except Exception as exc:
        logger.error(
            "get_performance_history failed (sport=%s, days=%d): %s",
            sport.upper(),
            days,
            exc,
        )
        return []
