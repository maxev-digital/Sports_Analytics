"""Storage layer for user bankroll data using JSON file database"""
import json
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

from models.bankroll import BankrollData, BookmakerBankroll


class BankrollStorage:
    """Manages storage of user bankroll data in JSON file"""

    def __init__(self, data_dir: str = "data/bankroll"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.bankroll_file = self.data_dir / "user_bankrolls.json"

        # Initialize file if it doesn't exist
        if not self.bankroll_file.exists():
            self._write_bankrolls({})

    def _read_bankrolls(self) -> dict:
        """Read all bankroll data from file"""
        try:
            with open(self.bankroll_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_bankrolls(self, bankrolls: dict):
        """Write all bankroll data to file"""
        with open(self.bankroll_file, 'w') as f:
            json.dump(bankrolls, f, indent=2)

    def get_bankroll(self, user_id: str) -> Optional[BankrollData]:
        """
        Get bankroll data for a user

        Args:
            user_id: Username/ID of the user

        Returns:
            BankrollData if found, None otherwise
        """
        bankrolls = self._read_bankrolls()

        if user_id in bankrolls:
            return BankrollData(**bankrolls[user_id])

        return None

    def update_bankroll(
        self,
        user_id: str,
        total_bankroll: float,
        bookmaker_bankrolls: list
    ) -> BankrollData:
        """
        Update or create bankroll data for a user

        Args:
            user_id: Username/ID of the user
            total_bankroll: Total bankroll amount
            bookmaker_bankrolls: List of bookmaker bankroll dicts

        Returns:
            Updated BankrollData
        """
        bankrolls = self._read_bankrolls()

        # Create new bankroll data
        bankroll_data = {
            'user_id': user_id,
            'total_bankroll': total_bankroll,
            'bookmaker_bankrolls': bookmaker_bankrolls,
            'updated_at': datetime.utcnow().isoformat()
        }

        # Save to file
        bankrolls[user_id] = bankroll_data
        self._write_bankrolls(bankrolls)

        return BankrollData(**bankroll_data)

    def delete_bankroll(self, user_id: str) -> bool:
        """
        Delete bankroll data for a user

        Args:
            user_id: Username/ID of the user

        Returns:
            True if deleted, False if not found
        """
        bankrolls = self._read_bankrolls()

        if user_id in bankrolls:
            del bankrolls[user_id]
            self._write_bankrolls(bankrolls)
            return True

        return False


# Global instance
bankroll_storage = BankrollStorage()
