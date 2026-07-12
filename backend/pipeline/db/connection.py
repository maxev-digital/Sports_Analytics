"""
Database connection utilities for the Sports Betting Analytics pipeline.

Provides:
- ``get_engine()``         – singleton SQLAlchemy engine.
- ``get_connection()``     – context manager for a raw psycopg2 connection.
- ``execute_query()``      – SELECT helper, returns list[dict].
- ``execute_write()``      – INSERT/UPDATE/DELETE helper, returns rowcount.
- ``execute_many()``       – bulk INSERT via executemany.
- ``table_exists()``       – boolean check for table presence.
"""

from __future__ import annotations

import contextlib
import logging
from collections.abc import Generator
from typing import Any

import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from pipeline import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton engine
# ---------------------------------------------------------------------------
_engine: Engine | None = None


def get_engine() -> Engine:
    """
    Return (or lazily create) the shared SQLAlchemy engine.

    Uses a connection pool with pool_size=5 and max_overflow=10 so the pipeline
    can handle moderate concurrency without exhausting database connections.
    ``pool_pre_ping=True`` transparently recycles stale connections after a
    server restart or idle timeout.
    """
    global _engine
    if _engine is None:
        _engine = create_engine(
            config.DB_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            future=True,
        )
        logger.debug("SQLAlchemy engine created: %s", config.DB_URL.split("@")[-1])
    return _engine


# ---------------------------------------------------------------------------
# Raw psycopg2 connection context manager
# ---------------------------------------------------------------------------
@contextlib.contextmanager
def get_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Yield a raw psycopg2 connection that is committed on clean exit and rolled
    back + closed on exception.

    Usage::

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    """
    # Parse the DSN from the SQLAlchemy URL (strip the dialect prefix)
    dsn = config.DB_URL
    if "://" in dsn:
        # psycopg2 accepts postgresql:// URIs directly
        if dsn.startswith("postgresql+psycopg2://"):
            dsn = dsn.replace("postgresql+psycopg2://", "postgresql://", 1)
        elif dsn.startswith("postgres://"):
            dsn = dsn.replace("postgres://", "postgresql://", 1)

    conn = psycopg2.connect(dsn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# SELECT helper
# ---------------------------------------------------------------------------
def execute_query(
    sql: str,
    params: dict[str, Any] | tuple[Any, ...] | None = None,
) -> list[dict[str, Any]]:
    """
    Execute a SELECT statement and return all rows as a list of dicts.

    Uses ``psycopg2.extras.RealDictCursor`` so column names are always
    available as dictionary keys.

    Args:
        sql:    SQL query string.  Use ``%(name)s`` placeholders for named
                params or ``%s`` for positional.
        params: Named dict or positional tuple of bind values.

    Returns:
        A (possibly empty) list of row dicts.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# INSERT / UPDATE / DELETE helper
# ---------------------------------------------------------------------------
def execute_write(
    sql: str,
    params: dict[str, Any] | tuple[Any, ...] | None = None,
) -> int:
    """
    Execute a single INSERT, UPDATE, or DELETE statement and commit.

    Args:
        sql:    SQL statement string.
        params: Named dict or positional tuple of bind values.

    Returns:
        ``cursor.rowcount`` – the number of rows affected.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rowcount: int = cur.rowcount
    return rowcount


# ---------------------------------------------------------------------------
# Bulk INSERT helper
# ---------------------------------------------------------------------------
def execute_many(
    sql: str,
    rows: list[dict[str, Any] | tuple[Any, ...]],
) -> int:
    """
    Execute a parameterised statement once per row using ``executemany``.

    Wraps the entire batch in a single transaction: all rows commit together
    or the whole batch rolls back on error.

    Args:
        sql:  SQL statement string (``%(name)s`` or ``%s`` placeholders).
        rows: Sequence of dicts or tuples, one per row to insert.

    Returns:
        Total number of rows inserted (``len(rows)`` on success).
    """
    if not rows:
        return 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, rows)
            # executemany sets rowcount to the last statement's rowcount in
            # psycopg2, so we return the input length as the definitive count.
    return len(rows)


# ---------------------------------------------------------------------------
# Table existence check
# ---------------------------------------------------------------------------
def table_exists(table_name: str) -> bool:
    """
    Return ``True`` if ``table_name`` exists in the ``public`` schema.

    Args:
        table_name: Unqualified table name (e.g. ``"predictions"``).

    Returns:
        ``True`` if the table is present, ``False`` otherwise.
    """
    sql = """
        SELECT EXISTS (
            SELECT 1
            FROM   information_schema.tables
            WHERE  table_schema = 'public'
            AND    table_name   = %(table_name)s
        )
    """
    rows = execute_query(sql, {"table_name": table_name})
    if rows:
        return bool(rows[0].get("exists", False))
    return False
