"""API routes for user bankroll management"""
from fastapi import APIRouter, HTTPException

from models.bankroll import BankrollData, UpdateBankrollRequest, calculate_kelly_bet_size
from storage.bankroll_storage import bankroll_storage

router = APIRouter(prefix="/api/bankroll", tags=["bankroll"])


@router.get("/{user_id}", response_model=BankrollData)
async def get_user_bankroll(user_id: str):
    """Get bankroll data for a user"""
    try:
        bankroll = bankroll_storage.get_bankroll(user_id)
        if not bankroll:
            raise HTTPException(status_code=404, detail="Bankroll data not found")
        return bankroll
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}", response_model=BankrollData)
async def update_user_bankroll(user_id: str, request: UpdateBankrollRequest):
    """Update or create bankroll data for a user"""
    try:
        # Convert Pydantic models to dicts for storage
        bookmaker_bankrolls = [bb.dict() for bb in request.bookmaker_bankrolls]

        bankroll = bankroll_storage.update_bankroll(
            user_id=user_id,
            total_bankroll=request.total_bankroll,
            bookmaker_bankrolls=bookmaker_bankrolls
        )
        return bankroll
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}")
async def delete_user_bankroll(user_id: str):
    """Delete bankroll data for a user"""
    success = bankroll_storage.delete_bankroll(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bankroll data not found")
    return {"message": "Bankroll deleted successfully"}


@router.get("/{user_id}/kelly-recommendation")
async def get_kelly_recommendation(
    user_id: str,
    edge: float,
    odds: float,
    kelly_fraction: float = 0.25
):
    """
    Get Kelly Criterion bet size recommendation

    Args:
        user_id: User ID
        edge: Edge as decimal (e.g., 0.05 for 5%)
        odds: American odds (e.g., -110, +150)
        kelly_fraction: Fraction of Kelly to use (default 0.25)

    Returns:
        Recommended bet size and related info
    """
    try:
        # Get user's bankroll
        bankroll = bankroll_storage.get_bankroll(user_id)
        if not bankroll:
            raise HTTPException(status_code=404, detail="Bankroll data not found. Please set up your bankroll first.")

        # Calculate Kelly bet size
        bet_size = calculate_kelly_bet_size(
            bankroll=bankroll.total_bankroll,
            edge=edge,
            odds=odds,
            kelly_fraction=kelly_fraction
        )

        return {
            "user_id": user_id,
            "total_bankroll": bankroll.total_bankroll,
            "edge": edge,
            "odds": odds,
            "kelly_fraction": kelly_fraction,
            "recommended_bet_size": round(bet_size, 2),
            "bet_size_percentage": round((bet_size / bankroll.total_bankroll) * 100, 2) if bankroll.total_bankroll > 0 else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
