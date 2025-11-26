"""
Storage layer for user bets - SQLite backed

This module provides backward-compatible access to bet storage.
The implementation has been migrated from JSON files to SQLite for:
- Better concurrent access handling
- Faster queries with indexes
- Support for 1,000-10,000+ users
- Built-in data integrity

The JSON file (user_bets.json) is automatically migrated on first run.
"""

# Import everything from the SQLite implementation
from storage.bet_storage_sqlite import (
    BetStorageSQLite as BetStorage,
    bet_storage
)

# Re-export for backward compatibility
__all__ = ['BetStorage', 'bet_storage']
