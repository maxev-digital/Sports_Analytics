"""API routes for user bet tracking"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional

from models.user_bet import (
    UserBet,
    CreateBetRequest,
    ManualBetRequest,
    AddStakeRequest,
    SettleBetRequest
)
from storage.bet_storage import bet_storage

router = APIRouter(prefix="/api/bets", tags=["bets"])


@router.post("/track-click", response_model=UserBet)
async def track_bookmaker_click(request: CreateBetRequest):
    """
    Track when a user clicks a bookmaker deep link.
    Creates a pending bet that waits for stake entry.
    """
    try:
        # Check for duplicate pending/active bet
        existing_bet = bet_storage.check_for_duplicate(
            user_id=request.user_id,
            game_id=request.game_id,
            bet_type=request.bet_type,
            bet_side=request.bet_side,
            bookmaker=request.bookmaker
        )

        if existing_bet:
            # Return existing bet instead of creating duplicate
            return existing_bet

        # Create new pending bet
        bet = bet_storage.create_bet(request)
        return bet

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manual-entry", response_model=UserBet)
async def create_manual_bet(request: ManualBetRequest):
    """
    Manually add a complete bet entry with all details including stake.
    Creates an active bet immediately (not pending).
    """
    try:
        # Generate a unique game_id for manual entries
        game_id = f"manual_{request.sport}_{request.away_team}_{request.home_team}_{request.commence_time}".replace(" ", "_")

        # Create a CreateBetRequest first (without stake)
        create_request = CreateBetRequest(
            user_id=request.user_id,
            game_id=game_id,
            sport=request.sport,
            home_team=request.home_team,
            away_team=request.away_team,
            commence_time=request.commence_time,
            bet_type=request.bet_type,
            bet_side=request.bet_side,
            odds=request.odds,
            bookmaker=request.bookmaker,
            confidence=request.confidence,
            edge_percent=request.edge_percent,
            strategy="Manual Entry"
        )

        # Create the bet
        bet = bet_storage.create_bet(create_request)

        # Immediately add stake to make it active
        bet = bet_storage.add_stake(bet.id, request.stake)

        return bet

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending", response_model=List[UserBet])
async def get_pending_bets(user_id: str):
    """Get all pending bets for a user (clicked but no stake entered)"""
    try:
        bets = bet_storage.get_pending_bets(user_id)
        return bets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-bets", response_model=List[UserBet])
async def get_my_bets(
    user_id: str,
    status: Optional[str] = None,
    sport: Optional[str] = None
):
    """
    Get all bets for a user with optional filters.

    Args:
        user_id: User ID
        status: Filter by status (pending, active, won, lost, push, cancelled)
        sport: Filter by sport
    """
    try:
        bets = bet_storage.get_user_bets(user_id, status=status, sport=sport)
        return bets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{bet_id}", response_model=UserBet)
async def get_bet(bet_id: str):
    """Get a specific bet by ID"""
    bet = bet_storage.get_bet(bet_id)
    if not bet:
        raise HTTPException(status_code=404, detail="Bet not found")
    return bet


@router.put("/{bet_id}/add-stake", response_model=UserBet)
async def add_stake_to_bet(bet_id: str, request: AddStakeRequest):
    """
    Add stake amount to a pending bet and change status to active.

    Args:
        bet_id: ID of the pending bet
        request: Contains stake amount
    """
    try:
        bet = bet_storage.add_stake(bet_id, request.stake)
        if not bet:
            raise HTTPException(status_code=404, detail="Bet not found")
        return bet
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{bet_id}/settle", response_model=UserBet)
async def settle_bet(bet_id: str, request: SettleBetRequest):
    """
    Settle a bet with win/loss/push result.

    Args:
        bet_id: ID of the active bet
        request: Contains result (win/loss/push) and optional score
    """
    try:
        bet = bet_storage.settle_bet(bet_id, request.result)
        if not bet:
            raise HTTPException(status_code=404, detail="Bet not found")
        return bet
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{bet_id}")
async def delete_bet(bet_id: str):
    """Delete a bet (typically for pending bets user didn't actually place)"""
    success = bet_storage.delete_bet(bet_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bet not found")
    return {"message": "Bet deleted successfully"}


@router.get("/user/{user_id}/stats")
async def get_user_betting_stats(user_id: str):
    """Get betting statistics for a user"""
    try:
        all_bets = bet_storage.get_user_bets(user_id)

        # Calculate stats
        total_bets = len([b for b in all_bets if b.stake is not None])
        active_bets = len([b for b in all_bets if b.status == 'active'])
        pending_bets = len([b for b in all_bets if b.status == 'pending'])

        # Settled bets only
        settled_bets = [b for b in all_bets if b.status in ['won', 'lost', 'push']]
        won_bets = len([b for b in settled_bets if b.status == 'won'])
        lost_bets = len([b for b in settled_bets if b.status == 'lost'])
        push_bets = len([b for b in settled_bets if b.status == 'push'])

        # Financial stats
        total_wagered = sum(b.stake for b in all_bets if b.stake is not None)
        total_payout = sum(b.payout for b in settled_bets if b.payout is not None)
        total_profit_loss = sum(b.profit_loss for b in settled_bets if b.profit_loss is not None)

        win_rate = (won_bets / len(settled_bets) * 100) if settled_bets else 0
        roi = (total_profit_loss / total_wagered * 100) if total_wagered > 0 else 0

        # Find biggest win and loss
        biggest_win = max(
            (b.profit_loss for b in settled_bets if b.profit_loss and b.profit_loss > 0),
            default=0
        )
        biggest_loss = min(
            (b.profit_loss for b in settled_bets if b.profit_loss and b.profit_loss < 0),
            default=0
        )

        return {
            "total_bets": total_bets,
            "pending_bets": pending_bets,
            "active_bets": active_bets,
            "settled_bets": len(settled_bets),
            "won_bets": won_bets,
            "lost_bets": lost_bets,
            "push_bets": push_bets,
            "win_rate": round(win_rate, 1),
            "total_wagered": round(total_wagered, 2),
            "total_returned": round(total_payout, 2),
            "net_profit_loss": round(total_profit_loss, 2),
            "roi_percent": round(roi, 1),
            "biggest_win": round(biggest_win, 2),
            "biggest_loss": round(abs(biggest_loss), 2)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
