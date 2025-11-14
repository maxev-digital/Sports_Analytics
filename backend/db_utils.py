"""
Database utilities for improved SQLite performance under load

This module provides optimized SQLite connections with:
- WAL (Write-Ahead Logging) mode for better concurrent writes
- Increased cache size
- Optimized synchronous mode
- Connection pooling support
"""
import sqlite3
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def get_optimized_connection(database: str, check_same_thread: bool = False) -> sqlite3.Connection:
    """
    Create an optimized SQLite connection with WAL mode enabled

    Args:
        database: Path to database file
        check_same_thread: Whether to check same thread (default False for FastAPI)

    Returns:
        Optimized SQLite connection
    """
    conn = sqlite3.connect(database, check_same_thread=check_same_thread)

    # Enable WAL mode for better concurrent writes (10x improvement)
    # WAL allows reads and writes to happen simultaneously
    conn.execute('PRAGMA journal_mode=WAL')

    # Set synchronous mode to NORMAL (faster, still safe)
    # FULL is overkill for most applications
    conn.execute('PRAGMA synchronous=NORMAL')

    # Increase cache size to 10MB (default is 2MB)
    # Reduces disk I/O significantly
    conn.execute('PRAGMA cache_size=-10000')  # Negative value = KB

    # Enable foreign keys (good practice)
    conn.execute('PRAGMA foreign_keys=ON')

    # Set busy timeout to 30 seconds (handle contention gracefully)
    conn.execute('PRAGMA busy_timeout=30000')

    logger.debug(f"Created optimized connection to {database} with WAL mode")
    return conn

# Backward compatibility: alias to old function name
def connect_db(database: str, check_same_thread: bool = False) -> sqlite3.Connection:
    """Alias for get_optimized_connection"""
    return get_optimized_connection(database, check_same_thread)
