"""
Persistent storage for win streak sequences and bets.
Tracks pressing strategies, multi-bet game attacks, core vs flier separation.
"""
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import contextmanager

DATABASE_PATH = "streaks.db"


class StreaksDatabase:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_database(self):
        with self.get_connection() as conn:
            c = conn.cursor()

            c.execute("""
                CREATE TABLE IF NOT EXISTS sequences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL DEFAULT 'default',
                    base_bet REAL NOT NULL,
                    target_streak INTEGER NOT NULL DEFAULT 5,
                    bet_type TEXT NOT NULL DEFAULT 'spread',
                    juice INTEGER NOT NULL DEFAULT -110,
                    status TEXT NOT NULL DEFAULT 'active',
                    total_payout REAL NOT NULL DEFAULT 0,
                    net_profit REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS bets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sequence_id INTEGER NOT NULL,
                    bet_number INTEGER NOT NULL,
                    game_description TEXT NOT NULL,
                    pick TEXT NOT NULL,
                    odds INTEGER NOT NULL,
                    bet_amount REAL NOT NULL,
                    potential_payout REAL NOT NULL,
                    result TEXT NOT NULL DEFAULT 'pending',
                    actual_payout REAL NOT NULL DEFAULT 0,
                    bet_category TEXT NOT NULL DEFAULT 'core',
                    notes TEXT,
                    placed_at TEXT NOT NULL,
                    graded_at TEXT,
                    FOREIGN KEY (sequence_id) REFERENCES sequences(id)
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL DEFAULT 'default',
                    tx_date TEXT NOT NULL,
                    tx_time TEXT,
                    tx_type TEXT NOT NULL,
                    game_description TEXT,
                    pick TEXT,
                    odds TEXT,
                    amount REAL NOT NULL,
                    balance REAL,
                    result TEXT,
                    bet_category TEXT NOT NULL DEFAULT 'core',
                    reward_points REAL,
                    imported_at TEXT NOT NULL
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS balance_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL DEFAULT 'default',
                    balance REAL NOT NULL,
                    note TEXT,
                    recorded_at TEXT NOT NULL
                )
            """)

    # ── Sequences ─────────────────────────────────────────────

    def create_sequence(
        self, base_bet: float, target_streak: int,
        bet_type: str, juice: int, username: str = "default"
    ) -> Dict:
        with self.get_connection() as conn:
            active = conn.execute(
                "SELECT id FROM sequences WHERE username=? AND status='active'",
                (username,)
            ).fetchone()
            if active:
                raise ValueError("Already have an active sequence")

            now = datetime.utcnow().isoformat()
            c = conn.execute(
                """INSERT INTO sequences
                   (username, base_bet, target_streak, bet_type, juice, status, created_at)
                   VALUES (?,?,?,?,?,'active',?)""",
                (username, base_bet, target_streak, bet_type, juice, now)
            )
            return self.get_sequence(c.lastrowid)

    def get_sequence(self, seq_id: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM sequences WHERE id=?", (seq_id,)
            ).fetchone()
            if not row:
                return None
            bets = conn.execute(
                "SELECT * FROM bets WHERE sequence_id=? ORDER BY bet_number",
                (seq_id,)
            ).fetchall()
            return {**dict(row), "bets": [dict(b) for b in bets]}

    def list_sequences(self, username: str = "default") -> List[Dict]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM sequences WHERE username=? ORDER BY id DESC",
                (username,)
            ).fetchall()
            return [dict(r) for r in rows]

    def delete_sequence(self, seq_id: int):
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE sequences SET status='cancelled', completed_at=? WHERE id=?",
                (datetime.utcnow().isoformat(), seq_id)
            )

    # ── Bets ──────────────────────────────────────────────────

    def _american_to_decimal(self, odds: int) -> float:
        return (odds / 100) + 1 if odds > 0 else (100 / abs(odds)) + 1

    def add_bet(
        self, seq_id: int, game_description: str, pick: str,
        odds: int, bet_category: str = "core", notes: str = None
    ) -> Dict:
        with self.get_connection() as conn:
            seq = conn.execute(
                "SELECT * FROM sequences WHERE id=? AND status='active'",
                (seq_id,)
            ).fetchone()
            if not seq:
                raise ValueError("Sequence not found or not active")

            pending = conn.execute(
                "SELECT id FROM bets WHERE sequence_id=? AND result='pending'",
                (seq_id,)
            ).fetchone()
            if pending:
                raise ValueError("Grade the pending bet first")

            wins = conn.execute(
                "SELECT COUNT(*) as c FROM bets WHERE sequence_id=? AND result='win'",
                (seq_id,)
            ).fetchone()["c"]

            mult = self._american_to_decimal(seq["juice"])
            bet_amount = seq["base_bet"] * (mult ** wins)
            potential_payout = bet_amount * self._american_to_decimal(odds)

            bet_number = conn.execute(
                "SELECT COALESCE(MAX(bet_number),0)+1 FROM bets WHERE sequence_id=?",
                (seq_id,)
            ).fetchone()[0]

            now = datetime.utcnow().isoformat()
            c = conn.execute(
                """INSERT INTO bets
                   (sequence_id, bet_number, game_description, pick, odds,
                    bet_amount, potential_payout, result, bet_category, notes, placed_at)
                   VALUES (?,?,?,?,?,?,?,'pending',?,?,?)""",
                (seq_id, bet_number, game_description, pick, odds,
                 round(bet_amount, 2), round(potential_payout, 2),
                 bet_category, notes, now)
            )
            return dict(conn.execute(
                "SELECT * FROM bets WHERE id=?", (c.lastrowid,)
            ).fetchone())

    def grade_bet(self, bet_id: int, result: str) -> Dict:
        with self.get_connection() as conn:
            bet = conn.execute(
                "SELECT * FROM bets WHERE id=?", (bet_id,)
            ).fetchone()
            if not bet:
                raise ValueError("Bet not found")
            if bet["result"] != "pending":
                raise ValueError("Bet already graded")

            now = datetime.utcnow().isoformat()
            actual_payout = bet["potential_payout"] if result == "win" else 0.0

            conn.execute(
                "UPDATE bets SET result=?, actual_payout=?, graded_at=? WHERE id=?",
                (result, actual_payout, now, bet_id)
            )

            seq_id = bet["sequence_id"]
            seq = conn.execute(
                "SELECT * FROM sequences WHERE id=?", (seq_id,)
            ).fetchone()

            if result == "loss":
                total_payout = 0.0
                net_profit = -seq["base_bet"]
                conn.execute(
                    """UPDATE sequences SET status='lost',
                       total_payout=?, net_profit=?, completed_at=?
                       WHERE id=?""",
                    (total_payout, net_profit, now, seq_id)
                )
            elif result == "win":
                wins = conn.execute(
                    "SELECT COUNT(*) as c FROM bets WHERE sequence_id=? AND result='win'",
                    (seq_id,)
                ).fetchone()["c"]
                if wins >= seq["target_streak"]:
                    mult = self._american_to_decimal(seq["juice"])
                    total_payout = seq["base_bet"] * (mult ** wins)
                    net_profit = total_payout - seq["base_bet"]
                    conn.execute(
                        """UPDATE sequences SET status='won',
                           total_payout=?, net_profit=?, completed_at=?
                           WHERE id=?""",
                        (round(total_payout, 2), round(net_profit, 2), now, seq_id)
                    )

            return self.get_sequence(seq_id)

    def cashout_sequence(self, seq_id: int) -> Dict:
        with self.get_connection() as conn:
            seq = conn.execute(
                "SELECT * FROM sequences WHERE id=? AND status='active'",
                (seq_id,)
            ).fetchone()
            if not seq:
                raise ValueError("No active sequence")

            wins = conn.execute(
                "SELECT COUNT(*) as c FROM bets WHERE sequence_id=? AND result='win'",
                (seq_id,)
            ).fetchone()["c"]

            mult = self._american_to_decimal(seq["juice"])
            total_payout = seq["base_bet"] * (mult ** wins) if wins > 0 else 0
            net_profit = total_payout - seq["base_bet"]
            now = datetime.utcnow().isoformat()

            conn.execute(
                """UPDATE sequences SET status='cashed_out',
                   total_payout=?, net_profit=?, completed_at=?
                   WHERE id=?""",
                (round(total_payout, 2), round(net_profit, 2), now, seq_id)
            )
            return self.get_sequence(seq_id)

    # ── Stats ─────────────────────────────────────────────────

    def get_stats(self, username: str = "default") -> Dict:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM sequences WHERE username=? AND status != 'active'",
                (username,)
            ).fetchall()
            total = len(rows)
            wins = sum(1 for r in rows if r["status"] == "won")
            losses = sum(1 for r in rows if r["status"] == "lost")
            cashouts = sum(1 for r in rows if r["status"] == "cashed_out")
            total_profit = sum(r["net_profit"] for r in rows)
            best = max((r["net_profit"] for r in rows), default=0)
            worst = min((r["net_profit"] for r in rows), default=0)
            return {
                "total_sequences": total, "wins": wins, "losses": losses,
                "cashouts": cashouts, "total_profit": round(total_profit, 2),
                "best_sequence": round(best, 2),
                "worst_sequence": round(worst, 2),
            }

    # ── Transaction Import ────────────────────────────────────

    def import_transactions(
        self, transactions: List[Dict], username: str = "default"
    ) -> Dict:
        inserted = 0
        skipped = 0
        with self.get_connection() as conn:
            now = datetime.utcnow().isoformat()
            for tx in transactions:
                existing = conn.execute(
                    """SELECT id FROM transactions
                       WHERE username=? AND tx_date=? AND tx_time=?
                       AND amount=? AND COALESCE(pick,'')=COALESCE(?,'')""",
                    (username, tx["date"], tx.get("time"),
                     tx["amount"], tx.get("pick"))
                ).fetchone()
                if existing:
                    skipped += 1
                    continue

                odds_str = tx.get("odds", "")
                cat = self._classify_bet_category(
                    odds_str, tx.get("amount", 0)
                )

                conn.execute(
                    """INSERT INTO transactions
                       (username, tx_date, tx_time, tx_type,
                        game_description, pick, odds, amount, balance,
                        result, bet_category, reward_points, imported_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (username, tx["date"], tx.get("time"), tx["type"],
                     tx.get("game"), tx.get("pick"), odds_str,
                     tx["amount"], tx.get("balance"),
                     tx.get("result"), cat,
                     tx.get("reward_points"), now)
                )
                inserted += 1
        return {"inserted": inserted, "skipped": skipped}

    def _classify_bet_category(self, odds_str: str, amount: float) -> str:
        if not odds_str:
            return "core"
        try:
            odds_val = int(odds_str.replace("+", ""))
        except (ValueError, AttributeError):
            return "core"
        if odds_val >= 300 and abs(amount) <= 30:
            return "flier"
        return "core"

    def get_transactions(
        self, username: str = "default",
        limit: int = 200, offset: int = 0
    ) -> List[Dict]:
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM transactions WHERE username=?
                   ORDER BY tx_date DESC, tx_time DESC
                   LIMIT ? OFFSET ?""",
                (username, limit, offset)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_history_stats(self, username: str = "default") -> Dict:
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM transactions
                   WHERE username=? AND tx_type IN ('win','loss','void','placed')
                   ORDER BY tx_date, tx_time""",
                (username,)
            ).fetchall()
            if not rows:
                return {
                    "total_bets": 0, "record": "0-0-0",
                    "net_pnl": 0, "balance_curve": [],
                    "core_record": "0-0", "flier_record": "0-0",
                    "current_streak": 0, "best_streak": 0,
                    "deposits": 0, "phases": [],
                }

            wins = sum(1 for r in rows if r["result"] == "win")
            losses = sum(1 for r in rows if r["result"] == "loss")
            voids = sum(1 for r in rows if r["result"] == "void")
            core_w = sum(
                1 for r in rows
                if r["result"] == "win" and r["bet_category"] == "core"
            )
            core_l = sum(
                1 for r in rows
                if r["result"] == "loss" and r["bet_category"] == "core"
            )
            flier_w = sum(
                1 for r in rows
                if r["result"] == "win" and r["bet_category"] == "flier"
            )
            flier_l = sum(
                1 for r in rows
                if r["result"] == "loss" and r["bet_category"] == "flier"
            )

            balance_curve = []
            for r in rows:
                if r["balance"] is not None:
                    balance_curve.append({
                        "date": r["tx_date"],
                        "time": r["tx_time"],
                        "balance": r["balance"],
                        "type": r["tx_type"],
                        "game": r["game_description"],
                    })

            streak = 0
            best_streak = 0
            for r in reversed(rows):
                if r["result"] == "win":
                    streak += 1
                    best_streak = max(best_streak, streak)
                elif r["result"] == "loss":
                    break

            net_pnl = sum(r["amount"] for r in rows if r["result"] in ("win", "loss"))
            deposits = sum(
                r["amount"] for r in rows if r["tx_type"] == "deposit"
            )

            return {
                "total_bets": wins + losses + voids,
                "record": f"{wins}-{losses}-{voids}",
                "net_pnl": round(net_pnl, 2),
                "balance_curve": balance_curve,
                "core_record": f"{core_w}-{core_l}",
                "flier_record": f"{flier_w}-{flier_l}",
                "current_streak": streak,
                "best_streak": best_streak,
                "deposits": round(deposits, 2),
            }

    # ── Balance snapshots ─────────────────────────────────────

    def record_balance(
        self, balance: float, note: str = None,
        username: str = "default"
    ):
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO balance_snapshots
                   (username, balance, note, recorded_at)
                   VALUES (?,?,?,?)""",
                (username, balance, note, datetime.utcnow().isoformat())
            )

    def get_balance_history(self, username: str = "default") -> List[Dict]:
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM balance_snapshots
                   WHERE username=? ORDER BY recorded_at""",
                (username,)
            ).fetchall()
            return [dict(r) for r in rows]


streaks_db = StreaksDatabase()
