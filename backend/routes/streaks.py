"""Win streak sequence tracker — press tracking, transaction import, history stats"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

from streaks_database import streaks_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/streaks", tags=["streaks"])


# ── Request Models ────────────────────────────────────────────

class CreateSequenceRequest(BaseModel):
    base_bet: float
    target_streak: int = 5
    bet_type: str = "spread"
    juice: int = -110


class AddBetRequest(BaseModel):
    game_description: str
    pick: str
    odds: int = -110
    bet_category: str = "core"
    notes: Optional[str] = None


class GradeBetRequest(BaseModel):
    result: str  # win, loss, push


class ImportTransaction(BaseModel):
    date: str
    time: Optional[str] = None
    type: str  # placed, win, loss, void, deposit
    game: Optional[str] = None
    pick: Optional[str] = None
    odds: Optional[str] = None
    amount: float
    balance: Optional[float] = None
    result: Optional[str] = None
    reward_points: Optional[float] = None


class ImportRequest(BaseModel):
    transactions: List[ImportTransaction]


class RecordBalanceRequest(BaseModel):
    balance: float
    note: Optional[str] = None


# ── Sequence Endpoints ────────────────────────────────────────

@router.get("/sequences")
async def list_sequences():
    seqs = streaks_db.list_sequences()
    return {"sequences": seqs}


@router.post("/sequences")
async def create_sequence(req: CreateSequenceRequest):
    try:
        seq = streaks_db.create_sequence(
            base_bet=req.base_bet,
            target_streak=req.target_streak,
            bet_type=req.bet_type,
            juice=req.juice,
        )
        return seq
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sequences/{seq_id}")
async def get_sequence(seq_id: int):
    seq = streaks_db.get_sequence(seq_id)
    if not seq:
        raise HTTPException(status_code=404, detail="Sequence not found")
    return seq


@router.delete("/sequences/{seq_id}")
async def cancel_sequence(seq_id: int):
    streaks_db.delete_sequence(seq_id)
    return {"status": "cancelled"}


# ── Bet Endpoints ─────────────────────────────────────────────

@router.post("/sequences/{seq_id}/bets")
async def add_bet(seq_id: int, req: AddBetRequest):
    try:
        bet = streaks_db.add_bet(
            seq_id=seq_id,
            game_description=req.game_description,
            pick=req.pick,
            odds=req.odds,
            bet_category=req.bet_category,
            notes=req.notes,
        )
        return bet
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/bets/{bet_id}/grade")
async def grade_bet(bet_id: int, req: GradeBetRequest):
    if req.result not in ("win", "loss", "push"):
        raise HTTPException(status_code=400, detail="Invalid result")
    try:
        seq = streaks_db.grade_bet(bet_id, req.result)
        return seq
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/sequences/{seq_id}/cashout")
async def cashout_sequence(seq_id: int):
    try:
        seq = streaks_db.cashout_sequence(seq_id)
        return seq
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Stats ─────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats():
    return streaks_db.get_stats()


# ── Transaction Import & History ──────────────────────────────

@router.post("/import")
async def import_transactions(req: ImportRequest):
    result = streaks_db.import_transactions(
        [tx.model_dump() for tx in req.transactions]
    )
    logger.info(f"Imported {result['inserted']} transactions")
    return result


@router.get("/transactions")
async def get_transactions(limit: int = 200, offset: int = 0):
    txs = streaks_db.get_transactions(limit=limit, offset=offset)
    return {"transactions": txs}


@router.get("/history")
async def get_history_stats():
    return streaks_db.get_history_stats()


# ── Balance ───────────────────────────────────────────────────

@router.post("/balance")
async def record_balance(req: RecordBalanceRequest):
    streaks_db.record_balance(balance=req.balance, note=req.note)
    return {"status": "recorded"}


@router.get("/balance/history")
async def get_balance_history():
    history = streaks_db.get_balance_history()
    return {"snapshots": history}
