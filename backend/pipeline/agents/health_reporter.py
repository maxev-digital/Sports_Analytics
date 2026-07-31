"""
Health reporting layer -- queries PostgreSQL using actual schema column names.
Fail-open: DB errors return empty/default structures, never crash the caller.
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

    # Ingestion stats -- columns: records_fetched, records_rejected, run_at_cst
    try:
        ing_rows = execute_query(
            """
            SELECT
                COALESCE(SUM(records_fetched), 0)::int                AS records_fetched,
                COALESCE(SUM(records_rejected), 0)::int               AS records_rejected,
                COALESCE(
                    EXTRACT(EPOCH FROM (NOW() - MAX(run_at_cst))) / 60,
                    999
                )::int                                                AS freshness_mins
            FROM ingestion_log
            WHERE run_at_cst::date = %(run_date)s
            """,
            {"run_date": date_cst},
        )
        row = ing_rows[0] if ing_rows else {}
        report["ingestion"] = {
            "records_ingested": int(row.get("records_fetched") or 0),
            "error_count": int(row.get("records_rejected") or 0),
            "freshness_mins": int(row.get("freshness_mins") or 999),
        }
    except Exception as exc:
        logger.error("compile_health_report: ingestion_log query failed: %s", exc)
        report["ingestion"] = {"error": str(exc)}

    # Predictions stats -- date filter via created_at_cst::date
    try:
        pred_rows = execute_query(
            """
            SELECT
                COUNT(*)                                    AS total_picks,
                COUNT(DISTINCT sport)                       AS sport_count,
                ROUND(AVG(edge_pct)::numeric, 2)            AS avg_edge_pct,
                ARRAY_AGG(DISTINCT sport ORDER BY sport)    AS sports
            FROM predictions
            WHERE created_at_cst::date = %(pred_date)s
            """,
            {"pred_date": date_cst},
        )
        row = pred_rows[0] if pred_rows else {}
        report["predictions"] = {
            "total_picks": int(row.get("total_picks") or 0),
            "sport_count": int(row.get("sport_count") or 0),
            "avg_edge_pct": float(row.get("avg_edge_pct") or 0.0),
            "sports": list(row.get("sports") or []),
        }
    except Exception as exc:
        logger.error("compile_health_report: predictions query failed: %s", exc)
        report["predictions"] = {"error": str(exc)}

    # Model performance stats -- columns: win_rate, roi_pct, total_picks, computed_at_cst
    try:
        mp_rows = execute_query(
            """
            SELECT
                ROUND(AVG(win_rate)::numeric, 4)        AS accuracy,
                ROUND(AVG(roi_pct)::numeric, 4)         AS roi,
                0.0::numeric                            AS brier_score,
                COALESCE(SUM(total_picks), 0)::int      AS sample_size
            FROM model_performance
            WHERE computed_at_cst::date = %(perf_date)s
            """,
            {"perf_date": date_cst},
        )
        row = mp_rows[0] if mp_rows else {}
        report["model_perf"] = {
            "accuracy": float(row.get("accuracy") or 0.0),
            "roi": float(row.get("roi") or 0.0),
            "brier_score": float(row.get("brier_score") or 0.0),
            "sample_size": int(row.get("sample_size") or 0),
        }
    except Exception as exc:
        logger.error("compile_health_report: model_performance query failed: %s", exc)
        report["model_perf"] = {"error": str(exc)}

    # Reflection report -- columns: model_health, flags_raised, action_items, opus_narrative
    try:
        ref_rows = execute_query(
            """
            SELECT
                model_health,
                flags_raised,
                action_items,
                opus_narrative  AS narrative
            FROM reflection_reports
            WHERE report_date = %(report_date)s
            ORDER BY run_at_cst DESC
            LIMIT 1
            """,
            {"report_date": date_cst},
        )

        def _parse_json(val: Any) -> list:
            if isinstance(val, list):
                return val
            if isinstance(val, str):
                try:
                    r = json.loads(val)
                    return r if isinstance(r, list) else []
                except (json.JSONDecodeError, ValueError):
                    return []
            return []

        if ref_rows:
            row = ref_rows[0]
            model_health = row.get("model_health", "warning")
            action_items = _parse_json(row.get("action_items"))
            flags_count = row.get("flags_raised", 0)
            report["reflection"] = {
                "proceed": model_health != "critical",
                "model_health": model_health,
                "narrative": str(row.get("narrative") or ""),
                "flags": [f"flags raised: {flags_count}"] if flags_count else [],
            }
            report["action_items"] = action_items
        else:
            report["reflection"] = {
                "proceed": True,
                "model_health": "warning",
                "narrative": "No reflection report found for this date.",
                "flags": [],
            }
    except Exception as exc:
        logger.error("compile_health_report: reflection_reports query failed: %s", exc)
        report["reflection"] = {"error": str(exc)}

    # Derive overall_status
    model_health = report.get("reflection", {}).get("model_health", "warning")
    error_count = report.get("ingestion", {}).get("error_count", 0)
    freshness_mins = report.get("ingestion", {}).get("freshness_mins", 0)

    if model_health == "critical" or (isinstance(error_count, int) and error_count > 20):
        report["overall_status"] = "critical"
    elif model_health == "warning" or (isinstance(freshness_mins, int) and freshness_mins > 120):
        report["overall_status"] = "warning"
    else:
        report["overall_status"] = "healthy"

    return report


def get_todays_picks(sport: str | None = None) -> list[dict[str, Any]]:
    """Return today's picks sorted by edge_pct descending."""
    today = now_cst().date()
    try:
        params: dict = {"today": today}
        sport_filter = ""
        if sport is not None:
            params["sport"] = sport.lower()
            sport_filter = "AND sport = %(sport)s"
        rows = execute_query(
            f"""
            SELECT *
            FROM predictions
            WHERE created_at_cst::date = %(today)s
              {sport_filter}
            ORDER BY edge_pct DESC
            """,
            params,
        )
        return rows
    except Exception as exc:
        logger.error("get_todays_picks failed (sport=%s): %s", sport or "ALL", exc)
        return []


def get_performance_history(sport: str, days: int = 30) -> list[dict[str, Any]]:
    """Return pick history for a sport over the past N days."""
    since = now_cst().date() - timedelta(days=days)
    try:
        rows = execute_query(
            """
            SELECT
                created_at_cst::date            AS date,
                sport,
                pick_type,
                COALESCE(result, 'pending')     AS result,
                COALESCE(pl_units, 0.0)::float  AS pl_units,
                edge_pct::float                 AS edge_pct
            FROM predictions
            WHERE sport = %(sport)s
              AND created_at_cst::date >= %(since)s
            ORDER BY created_at_cst DESC
            """,
            {"sport": sport.upper(), "since": since},
        )
        return rows
    except Exception as exc:
        logger.error("get_performance_history failed: %s", exc)
        return []
