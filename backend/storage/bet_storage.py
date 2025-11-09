"""Storage layer for user bets using JSON file database"""
import json
import os
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import uuid

from models.user_bet import UserBet, CreateBetRequest, calculate_profit_loss
from storage.alert_storage import alert_storage


class BetStorage:
    """Manages storage of user bets in JSON file"""

    def __init__(self, data_dir: str = "data/bets"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.bets_file = self.data_dir / "user_bets.json"

        # Initialize file if it doesn't exist
        if not self.bets_file.exists():
            self._write_bets([])

    def _read_bets(self) -> List[dict]:
        """Read all bets from file"""
        try:
            with open(self.bets_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _write_bets(self, bets: List[dict]):
        """Write all bets to file"""
        with open(self.bets_file, 'w') as f:
            json.dump(bets, f, indent=2)

    def create_bet(self, request: CreateBetRequest) -> UserBet:
        """Create a new pending bet from a click event"""
        bet = UserBet(
            id=str(uuid.uuid4()),
            user_id=request.user_id,
            game_id=request.game_id,
            sport=request.sport,
            home_team=request.home_team,
            away_team=request.away_team,
            commence_time=request.commence_time,
            bet_type=request.bet_type,
            bet_side=request.bet_side,
            odds=request.odds,
            bookmaker=request.bookmaker,
            alert_id=request.alert_id,
            confidence=request.confidence,
            edge_percent=request.edge_percent,
            strategy=request.strategy,
            clicked_at=datetime.utcnow().isoformat(),
            status='pending'
        )

        # Save to file
        bets = self._read_bets()
        bets.append(bet.dict())
        self._write_bets(bets)

        return bet

    def get_bet(self, bet_id: str) -> Optional[UserBet]:
        """Get a specific bet by ID"""
        bets = self._read_bets()
        for bet_data in bets:
            if bet_data['id'] == bet_id:
                return UserBet(**bet_data)
        return None

    def get_user_bets(
        self,
        user_id: str,
        status: Optional[str] = None,
        sport: Optional[str] = None
    ) -> List[UserBet]:
        """Get all bets for a user with optional filters"""
        bets = self._read_bets()
        user_bets = []

        for bet_data in bets:
            if bet_data['user_id'] == user_id:
                # Apply filters
                if status and bet_data['status'] != status:
                    continue
                if sport and bet_data['sport'] != sport:
                    continue
                user_bets.append(UserBet(**bet_data))

        # Sort by clicked_at (most recent first)
        user_bets.sort(key=lambda b: b.clicked_at, reverse=True)
        return user_bets

    def get_pending_bets(self, user_id: str) -> List[UserBet]:
        """Get all pending bets for a user"""
        return self.get_user_bets(user_id, status='pending')

    def add_stake(self, bet_id: str, stake: float) -> Optional[UserBet]:
        """Add stake to a pending bet and change status to active"""
        bets = self._read_bets()

        for i, bet_data in enumerate(bets):
            if bet_data['id'] == bet_id:
                if bet_data['status'] != 'pending':
                    raise ValueError(f"Cannot add stake to bet with status {bet_data['status']}")

                # Update bet
                bet_data['stake'] = stake
                bet_data['status'] = 'active'
                bet_data['logged_at'] = datetime.utcnow().isoformat()

                # Save changes
                bets[i] = bet_data
                self._write_bets(bets)

                return UserBet(**bet_data)

        return None

    def settle_bet(self, bet_id: str, result: str) -> Optional[UserBet]:
        """Settle a bet with win/loss/push result"""
        bets = self._read_bets()

        for i, bet_data in enumerate(bets):
            if bet_data['id'] == bet_id:
                if bet_data['status'] != 'active':
                    raise ValueError(f"Cannot settle bet with status {bet_data['status']}")

                if not bet_data.get('stake'):
                    raise ValueError("Cannot settle bet without stake")

                # Calculate payout and profit/loss
                payout, profit_loss = calculate_profit_loss(
                    bet_data['stake'],
                    bet_data['odds'],
                    result
                )

                # Update bet
                bet_data['result'] = result
                bet_data['payout'] = payout
                bet_data['profit_loss'] = profit_loss
                bet_data['settled_at'] = datetime.utcnow().isoformat()
                bet_data['status'] = result  # 'won', 'lost', or 'push'

                # If bet was from an alert, settle the alert too
                alert_id = bet_data.get('alert_id')
                if alert_id:
                    try:
                        alert_storage.settle_alert(
                            alert_id=alert_id,
                            outcome='win' if result == 'won' else result,
                            actual_result=f"Bet settled: {result}"
                        )
                    except Exception as e:
                        # Log but don't fail bet settlement if alert update fails
                        import logging
                        logging.error(f"Failed to settle alert {alert_id}: {e}")

                # Save changes
                bets[i] = bet_data
                self._write_bets(bets)

                return UserBet(**bet_data)

        return None

    def update_bet(self, bet_id: str, updates: dict) -> Optional[UserBet]:
        """
        Update bet details (bet_side, odds, stake, bookmaker, confidence, edge_percent)

        Args:
            bet_id: ID of the bet to update
            updates: Dictionary of fields to update

        Returns:
            Updated UserBet if found, None otherwise
        """
        bets = self._read_bets()

        for i, bet_data in enumerate(bets):
            if bet_data['id'] == bet_id:
                # Only allow updating certain fields
                allowed_fields = ['bet_side', 'odds', 'stake', 'bookmaker', 'confidence', 'edge_percent']

                for key, value in updates.items():
                    if key in allowed_fields and value is not None:
                        bet_data[key] = value

                # If stake was added/updated and bet was pending, change status to active
                if 'stake' in updates and updates['stake'] is not None:
                    if bet_data['status'] == 'pending':
                        bet_data['status'] = 'active'
                        bet_data['logged_at'] = datetime.utcnow().isoformat()

                # If odds or stake changed on a settled bet, recalculate profit/loss
                if bet_data.get('status') in ['win', 'loss', 'push']:
                    if ('odds' in updates or 'stake' in updates) and bet_data.get('stake') and bet_data.get('result'):
                        payout, profit_loss = calculate_profit_loss(
                            bet_data['stake'],
                            bet_data['odds'],
                            bet_data['result']
                        )
                        bet_data['payout'] = payout
                        bet_data['profit_loss'] = profit_loss

                # Save changes
                bets[i] = bet_data
                self._write_bets(bets)

                return UserBet(**bet_data)

        return None

    def delete_bet(self, bet_id: str) -> bool:
        """Delete a bet (typically for pending bets user didn't place)"""
        bets = self._read_bets()
        original_length = len(bets)

        bets = [b for b in bets if b['id'] != bet_id]

        if len(bets) < original_length:
            self._write_bets(bets)
            return True
        return False

    def check_for_duplicate(
        self,
        user_id: str,
        game_id: str,
        bet_type: str,
        bet_side: str,
        bookmaker: str
    ) -> Optional[UserBet]:
        """
        Check if user already has a pending or active bet on this exact play

        Returns existing bet if found, None otherwise
        """
        bets = self._read_bets()

        for bet_data in bets:
            if (bet_data['user_id'] == user_id and
                bet_data['game_id'] == game_id and
                bet_data['bet_type'] == bet_type and
                bet_data['bet_side'] == bet_side and
                bet_data['bookmaker'] == bookmaker and
                bet_data['status'] in ['pending', 'active']):
                return UserBet(**bet_data)

        return None


# Global storage instance
bet_storage = BetStorage()
