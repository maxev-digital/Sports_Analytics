"""
Bankroll Tracker for Quarter Reversal Strategy
Tracks bets, P&L, ROI, and drawdown for $20K starting bankroll

Features:
- Track daily P&L
- Split metrics: Q3 vs OT vs COMBO bets
- ROI dashboard
- Max drawdown tracking
- Export to CSV
"""

import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, asdict
from enum import Enum

# Data directory
DATA_DIR = Path(__file__).parent / "data" / "bankroll_tracking"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class BetResult(Enum):
    """Bet outcome"""
    WIN = "win"
    LOSS = "loss"
    PUSH = "push"
    PENDING = "pending"


class StrategyType(Enum):
    """Quarter reversal strategy types"""
    Q1_Q2_TO_Q3 = "Q1-Q2_to_Q3"
    Q2_Q3_TO_Q4 = "Q2-Q3_to_Q4"
    Q3_Q4_TO_OT = "Q3-Q4_to_OT"
    COMBO = "COMBO"
    HEDGE = "HEDGE"


@dataclass
class Bet:
    """Individual bet record"""
    bet_id: str
    timestamp: str
    game_id: str
    matchup: str
    strategy: str  # StrategyType value
    bet_type: str  # spread, moneyline, total, etc.
    bet_label: str  # "Lakers Q3 Spread +4.5 @ -110"
    odds: str  # "-110", "+150", etc.
    decimal_odds: float
    stake: float  # Dollar amount bet
    kelly_fraction: float  # 0.25 for 1/4 Kelly, 0.5 for 1/2 Kelly
    kelly_pct: float  # % of bankroll
    expected_value: float  # Expected value %
    result: str  # BetResult value
    profit_loss: Optional[float] = None  # Actual P&L (None if pending)
    bankroll_before: Optional[float] = None
    bankroll_after: Optional[float] = None


@dataclass
class DailySummary:
    """Daily performance summary"""
    date: str
    starting_bankroll: float
    ending_bankroll: float
    total_bets: int
    bets_won: int
    bets_lost: int
    bets_pushed: int
    bets_pending: int
    total_staked: float
    profit_loss: float
    roi: float  # Daily ROI %
    win_rate: float  # Win %
    avg_bet_size: float
    largest_win: float
    largest_loss: float
    # Split by strategy
    q3_bets: int
    q4_bets: int
    ot_bets: int
    combo_bets: int
    hedge_bets: int


class BankrollTracker:
    """
    Bankroll tracker for Quarter Reversal Strategy
    Tracks all bets, performance, and generates reports
    """

    def __init__(self, starting_bankroll: float = 20000.0):
        self.starting_bankroll = starting_bankroll
        self.current_bankroll = starting_bankroll
        self.all_time_high = starting_bankroll
        self.max_drawdown = 0.0
        self.max_drawdown_pct = 0.0

        # Load existing bets
        self.bets: List[Bet] = self._load_bets()

        # Calculate current bankroll from bet history
        if self.bets:
            self._recalculate_bankroll()

    def _load_bets(self) -> List[Bet]:
        """Load bets from JSON file"""
        bets_file = DATA_DIR / "bets.json"
        if not bets_file.exists():
            return []

        try:
            with open(bets_file, 'r', encoding='utf-8') as f:
                bets_data = json.load(f)
                return [Bet(**bet) for bet in bets_data]
        except Exception as e:
            print(f"Error loading bets: {e}")
            return []

    def _save_bets(self):
        """Save bets to JSON file"""
        bets_file = DATA_DIR / "bets.json"
        try:
            bets_data = [asdict(bet) for bet in self.bets]
            with open(bets_file, 'w', encoding='utf-8') as f:
                json.dump(bets_data, f, indent=2)
        except Exception as e:
            print(f"Error saving bets: {e}")

    def _recalculate_bankroll(self):
        """Recalculate current bankroll from bet history"""
        self.current_bankroll = self.starting_bankroll
        self.all_time_high = self.starting_bankroll

        for bet in self.bets:
            if bet.result != BetResult.PENDING.value and bet.profit_loss is not None:
                self.current_bankroll += bet.profit_loss

                # Update all-time high
                if self.current_bankroll > self.all_time_high:
                    self.all_time_high = self.current_bankroll

                # Update max drawdown
                drawdown = self.all_time_high - self.current_bankroll
                drawdown_pct = (drawdown / self.all_time_high) * 100
                if drawdown > self.max_drawdown:
                    self.max_drawdown = drawdown
                    self.max_drawdown_pct = drawdown_pct

    def place_bet(
        self,
        game_id: str,
        matchup: str,
        strategy: StrategyType,
        bet_type: str,
        bet_label: str,
        odds: str,
        decimal_odds: float,
        stake: float,
        kelly_fraction: float,
        kelly_pct: float,
        expected_value: float
    ) -> Bet:
        """
        Record a new bet placement

        Args:
            game_id: Unique game identifier
            matchup: "Lakers @ Warriors"
            strategy: StrategyType enum
            bet_type: "spread", "moneyline", "total", etc.
            bet_label: "Lakers Q3 Spread +4.5 @ -110"
            odds: "-110", "+150", etc.
            decimal_odds: 1.909, 2.5, etc.
            stake: Dollar amount bet (e.g., 142.50)
            kelly_fraction: 0.25 for 1/4 Kelly
            kelly_pct: % of bankroll (e.g., 1.425)
            expected_value: Expected value % (e.g., 3.2)

        Returns:
            Bet object
        """
        bet_id = f"{game_id}_{strategy.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        bet = Bet(
            bet_id=bet_id,
            timestamp=datetime.now().isoformat(),
            game_id=game_id,
            matchup=matchup,
            strategy=strategy.value,
            bet_type=bet_type,
            bet_label=bet_label,
            odds=odds,
            decimal_odds=decimal_odds,
            stake=stake,
            kelly_fraction=kelly_fraction,
            kelly_pct=kelly_pct,
            expected_value=expected_value,
            result=BetResult.PENDING.value,
            bankroll_before=self.current_bankroll,
            bankroll_after=None
        )

        self.bets.append(bet)
        self._save_bets()

        print(f"[BET PLACED] {bet_label} - Stake: ${stake:.2f} ({kelly_pct:.2f}% of ${self.current_bankroll:.2f})")

        return bet

    def settle_bet(
        self,
        bet_id: str,
        result: BetResult
    ) -> Optional[Bet]:
        """
        Settle a bet (mark as won/lost/pushed)

        Args:
            bet_id: Unique bet identifier
            result: BetResult.WIN, BetResult.LOSS, or BetResult.PUSH

        Returns:
            Updated Bet object or None if not found
        """
        # Find bet
        bet = next((b for b in self.bets if b.bet_id == bet_id), None)
        if not bet:
            print(f"[ERROR] Bet {bet_id} not found")
            return None

        # Calculate profit/loss
        if result == BetResult.WIN:
            # Win: Get stake back + winnings
            if bet.decimal_odds >= 2.0:
                profit_loss = bet.stake * (bet.decimal_odds - 1)
            else:
                profit_loss = bet.stake / abs(float(bet.odds)) * 100 if '-' in bet.odds else bet.stake * (bet.decimal_odds - 1)
        elif result == BetResult.LOSS:
            # Loss: Lose stake
            profit_loss = -bet.stake
        elif result == BetResult.PUSH:
            # Push: Get stake back (no profit/loss)
            profit_loss = 0.0
        else:
            print(f"[ERROR] Invalid result: {result}")
            return None

        # Update bet
        bet.result = result.value
        bet.profit_loss = profit_loss
        self.current_bankroll += profit_loss
        bet.bankroll_after = self.current_bankroll

        # Update all-time high and max drawdown
        if self.current_bankroll > self.all_time_high:
            self.all_time_high = self.current_bankroll

        drawdown = self.all_time_high - self.current_bankroll
        drawdown_pct = (drawdown / self.all_time_high) * 100
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
            self.max_drawdown_pct = drawdown_pct

        self._save_bets()

        print(f"[BET SETTLED] {bet.bet_label} - {result.value.upper()} - P&L: ${profit_loss:+.2f} - Bankroll: ${self.current_bankroll:.2f}")

        return bet

    def get_daily_summary(self, date: Optional[str] = None) -> DailySummary:
        """
        Get daily performance summary

        Args:
            date: Date string "YYYY-MM-DD" (defaults to today)

        Returns:
            DailySummary object
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        # Filter bets for this date
        day_bets = [b for b in self.bets if b.timestamp.startswith(date)]

        if not day_bets:
            return DailySummary(
                date=date,
                starting_bankroll=self.current_bankroll,
                ending_bankroll=self.current_bankroll,
                total_bets=0,
                bets_won=0,
                bets_lost=0,
                bets_pushed=0,
                bets_pending=0,
                total_staked=0.0,
                profit_loss=0.0,
                roi=0.0,
                win_rate=0.0,
                avg_bet_size=0.0,
                largest_win=0.0,
                largest_loss=0.0,
                q3_bets=0,
                q4_bets=0,
                ot_bets=0,
                combo_bets=0,
                hedge_bets=0
            )

        # Calculate metrics
        starting_bankroll = day_bets[0].bankroll_before or self.starting_bankroll
        ending_bankroll = day_bets[-1].bankroll_after or self.current_bankroll

        total_bets = len(day_bets)
        bets_won = len([b for b in day_bets if b.result == BetResult.WIN.value])
        bets_lost = len([b for b in day_bets if b.result == BetResult.LOSS.value])
        bets_pushed = len([b for b in day_bets if b.result == BetResult.PUSH.value])
        bets_pending = len([b for b in day_bets if b.result == BetResult.PENDING.value])

        total_staked = sum(b.stake for b in day_bets)
        profit_loss = sum(b.profit_loss or 0.0 for b in day_bets)
        roi = (profit_loss / total_staked) * 100 if total_staked > 0 else 0.0

        settled_bets = bets_won + bets_lost + bets_pushed
        win_rate = (bets_won / settled_bets) * 100 if settled_bets > 0 else 0.0

        avg_bet_size = total_staked / total_bets if total_bets > 0 else 0.0

        wins = [b.profit_loss for b in day_bets if b.result == BetResult.WIN.value and b.profit_loss]
        losses = [b.profit_loss for b in day_bets if b.result == BetResult.LOSS.value and b.profit_loss]
        largest_win = max(wins) if wins else 0.0
        largest_loss = min(losses) if losses else 0.0

        # Split by strategy
        q3_bets = len([b for b in day_bets if b.strategy == StrategyType.Q1_Q2_TO_Q3.value])
        q4_bets = len([b for b in day_bets if b.strategy == StrategyType.Q2_Q3_TO_Q4.value])
        ot_bets = len([b for b in day_bets if b.strategy == StrategyType.Q3_Q4_TO_OT.value])
        combo_bets = len([b for b in day_bets if b.strategy == StrategyType.COMBO.value])
        hedge_bets = len([b for b in day_bets if b.strategy == StrategyType.HEDGE.value])

        return DailySummary(
            date=date,
            starting_bankroll=starting_bankroll,
            ending_bankroll=ending_bankroll,
            total_bets=total_bets,
            bets_won=bets_won,
            bets_lost=bets_lost,
            bets_pushed=bets_pushed,
            bets_pending=bets_pending,
            total_staked=total_staked,
            profit_loss=profit_loss,
            roi=roi,
            win_rate=win_rate,
            avg_bet_size=avg_bet_size,
            largest_win=largest_win,
            largest_loss=largest_loss,
            q3_bets=q3_bets,
            q4_bets=q4_bets,
            ot_bets=ot_bets,
            combo_bets=combo_bets,
            hedge_bets=hedge_bets
        )

    def get_all_time_stats(self) -> Dict:
        """Get all-time performance statistics"""
        if not self.bets:
            return {
                'starting_bankroll': self.starting_bankroll,
                'current_bankroll': self.current_bankroll,
                'total_profit_loss': 0.0,
                'total_roi': 0.0,
                'total_bets': 0,
                'bets_won': 0,
                'bets_lost': 0,
                'bets_pushed': 0,
                'win_rate': 0.0,
                'all_time_high': self.all_time_high,
                'max_drawdown': 0.0,
                'max_drawdown_pct': 0.0,
                'q3_bets': 0,
                'q4_bets': 0,
                'ot_bets': 0,
                'combo_bets': 0,
                'hedge_bets': 0
            }

        total_bets = len(self.bets)
        bets_won = len([b for b in self.bets if b.result == BetResult.WIN.value])
        bets_lost = len([b for b in self.bets if b.result == BetResult.LOSS.value])
        bets_pushed = len([b for b in self.bets if b.result == BetResult.PUSH.value])

        settled_bets = bets_won + bets_lost + bets_pushed
        win_rate = (bets_won / settled_bets) * 100 if settled_bets > 0 else 0.0

        total_profit_loss = self.current_bankroll - self.starting_bankroll
        total_roi = (total_profit_loss / self.starting_bankroll) * 100

        # Split by strategy
        q3_bets = len([b for b in self.bets if b.strategy == StrategyType.Q1_Q2_TO_Q3.value])
        q4_bets = len([b for b in self.bets if b.strategy == StrategyType.Q2_Q3_TO_Q4.value])
        ot_bets = len([b for b in self.bets if b.strategy == StrategyType.Q3_Q4_TO_OT.value])
        combo_bets = len([b for b in self.bets if b.strategy == StrategyType.COMBO.value])
        hedge_bets = len([b for b in self.bets if b.strategy == StrategyType.HEDGE.value])

        return {
            'starting_bankroll': self.starting_bankroll,
            'current_bankroll': self.current_bankroll,
            'total_profit_loss': total_profit_loss,
            'total_roi': total_roi,
            'total_bets': total_bets,
            'bets_won': bets_won,
            'bets_lost': bets_lost,
            'bets_pushed': bets_pushed,
            'win_rate': win_rate,
            'all_time_high': self.all_time_high,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_pct': self.max_drawdown_pct,
            'q3_bets': q3_bets,
            'q4_bets': q4_bets,
            'ot_bets': ot_bets,
            'combo_bets': combo_bets,
            'hedge_bets': hedge_bets
        }

    def export_to_csv(self, filename: Optional[str] = None):
        """Export all bets to CSV file"""
        if filename is None:
            filename = f"bankroll_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        filepath = DATA_DIR / filename

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if not self.bets:
                    print("[INFO] No bets to export")
                    return

                writer = csv.DictWriter(f, fieldnames=asdict(self.bets[0]).keys())
                writer.writeheader()
                for bet in self.bets:
                    writer.writerow(asdict(bet))

            print(f"[SUCCESS] Exported {len(self.bets)} bets to {filepath}")
        except Exception as e:
            print(f"[ERROR] Failed to export bets: {e}")


# Example usage
if __name__ == "__main__":
    # Initialize tracker
    tracker = BankrollTracker(starting_bankroll=20000.0)

    print("\n" + "="*60)
    print("BANKROLL TRACKER - QUARTER REVERSAL STRATEGY")
    print("="*60)

    # Place a sample bet
    print("\n[TEST] Placing sample Q3 reversal bet...")
    bet = tracker.place_bet(
        game_id="401584844",
        matchup="Lakers @ Warriors",
        strategy=StrategyType.Q1_Q2_TO_Q3,
        bet_type="spread",
        bet_label="Warriors Q3 Spread +4.5 @ -110",
        odds="-110",
        decimal_odds=1.909,
        stake=142.50,
        kelly_fraction=0.25,
        kelly_pct=1.425,
        expected_value=3.2
    )

    # Settle the bet as a win
    print("\n[TEST] Settling bet as WIN...")
    tracker.settle_bet(bet.bet_id, BetResult.WIN)

    # Display all-time stats
    print("\n" + "="*60)
    print("ALL-TIME STATISTICS")
    print("="*60)
    stats = tracker.get_all_time_stats()
    print(f"Starting Bankroll: ${stats['starting_bankroll']:,.2f}")
    print(f"Current Bankroll: ${stats['current_bankroll']:,.2f}")
    print(f"Total P&L: ${stats['total_profit_loss']:+,.2f}")
    print(f"Total ROI: {stats['total_roi']:+.2f}%")
    print(f"Total Bets: {stats['total_bets']}")
    print(f"Win Rate: {stats['win_rate']:.1f}% ({stats['bets_won']}W-{stats['bets_lost']}L-{stats['bets_pushed']}P)")
    print(f"All-Time High: ${stats['all_time_high']:,.2f}")
    print(f"Max Drawdown: ${stats['max_drawdown']:,.2f} ({stats['max_drawdown_pct']:.2f}%)")
    print(f"\nStrategy Split: Q3={stats['q3_bets']}, Q4={stats['q4_bets']}, OT={stats['ot_bets']}, COMBO={stats['combo_bets']}, HEDGE={stats['hedge_bets']}")

    # Export to CSV
    print("\n[TEST] Exporting to CSV...")
    tracker.export_to_csv()

    print("\n" + "="*60)
    print("TRACKER TEST COMPLETE")
    print("="*60 + "\n")
