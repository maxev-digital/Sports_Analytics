"""API routes for user bet tracking"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from models.user_bet import (
    UserBet,
    CreateBetRequest,
    ManualBetRequest,
    AddStakeRequest,
    UpdateBetRequest,
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


@router.put("/{bet_id}/update", response_model=UserBet)
async def update_bet(bet_id: str, request: UpdateBetRequest):
    """
    Update bet details (odds, stake, bet_side, bookmaker, etc.)

    Args:
        bet_id: ID of the bet to update
        request: Contains fields to update
    """
    try:
        # Convert request to dict, excluding None values
        updates = {k: v for k, v in request.dict().items() if v is not None}

        bet = bet_storage.update_bet(bet_id, updates)
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
        settled_wagered = sum(b.stake for b in settled_bets if b.stake is not None)
        total_payout = sum(b.payout for b in settled_bets if b.payout is not None)
        total_profit_loss = sum(b.profit_loss for b in settled_bets if b.profit_loss is not None)

        win_rate = (won_bets / len(settled_bets) * 100) if settled_bets else 0
        # ROI should only use settled bets in denominator
        roi = (total_profit_loss / settled_wagered * 100) if settled_wagered > 0 else 0

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
            "settled_wagered": round(settled_wagered, 2),
            "total_returned": round(total_payout, 2),
            "net_profit_loss": round(total_profit_loss, 2),
            "roi_percent": round(roi, 1),
            "biggest_win": round(biggest_win, 2),
            "biggest_loss": round(abs(biggest_loss), 2)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/performance")
async def get_user_performance_data(user_id: str, days: Optional[int] = None):
    """
    Get detailed performance data for charts and analytics.

    Args:
        user_id: User ID
        days: Number of days to look back (7, 30, 90, or None for all time)
    """
    try:
        all_bets = bet_storage.get_user_bets(user_id)

        # Filter by time range if specified
        cutoff_date = None
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get settled bets only, filtered by time
        settled_bets = []
        for b in all_bets:
            if b.status not in ['won', 'lost', 'push']:
                continue
            if cutoff_date and b.settled_at:
                try:
                    settled_time = datetime.fromisoformat(b.settled_at.replace('Z', '+00:00').replace('+00:00', ''))
                    if settled_time < cutoff_date:
                        continue
                except:
                    pass
            settled_bets.append(b)

        # Calculate basic stats
        total_settled = len(settled_bets)
        won_bets = len([b for b in settled_bets if b.status == 'won'])
        lost_bets = len([b for b in settled_bets if b.status == 'lost'])
        push_bets = len([b for b in settled_bets if b.status == 'push'])

        total_wagered = sum(b.stake for b in settled_bets if b.stake)
        total_profit_loss = sum(b.profit_loss for b in settled_bets if b.profit_loss is not None)

        win_rate = (won_bets / total_settled * 100) if total_settled > 0 else 0
        roi = (total_profit_loss / total_wagered * 100) if total_wagered > 0 else 0

        avg_stake = (total_wagered / total_settled) if total_settled > 0 else 0

        # Daily performance history for charts
        daily_data = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pushes': 0, 'profit_loss': 0.0, 'wagered': 0.0})

        for bet in settled_bets:
            if bet.settled_at:
                try:
                    date_str = bet.settled_at[:10]  # YYYY-MM-DD
                    if bet.status == 'won':
                        daily_data[date_str]['wins'] += 1
                    elif bet.status == 'lost':
                        daily_data[date_str]['losses'] += 1
                    else:
                        daily_data[date_str]['pushes'] += 1
                    daily_data[date_str]['profit_loss'] += bet.profit_loss or 0
                    daily_data[date_str]['wagered'] += bet.stake or 0
                except:
                    pass

        # Convert to sorted list with cumulative P/L
        history = []
        cumulative_pl = 0.0
        cumulative_wagered = 0.0
        for date in sorted(daily_data.keys()):
            day = daily_data[date]
            cumulative_pl += day['profit_loss']
            cumulative_wagered += day['wagered']
            history.append({
                'date': date,
                'wins': day['wins'],
                'losses': day['losses'],
                'pushes': day['pushes'],
                'daily_pl': round(day['profit_loss'], 2),
                'cumulative_pl': round(cumulative_pl, 2),
                'daily_wagered': round(day['wagered'], 2),
                'cumulative_wagered': round(cumulative_wagered, 2)
            })

        # Performance by sport
        sport_data = defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0, 'pushes': 0, 'profit_loss': 0.0, 'wagered': 0.0})
        for bet in settled_bets:
            sport = bet.sport or 'Unknown'
            sport_data[sport]['total'] += 1
            if bet.status == 'won':
                sport_data[sport]['wins'] += 1
            elif bet.status == 'lost':
                sport_data[sport]['losses'] += 1
            else:
                sport_data[sport]['pushes'] += 1
            sport_data[sport]['profit_loss'] += bet.profit_loss or 0
            sport_data[sport]['wagered'] += bet.stake or 0

        by_sport = []
        for sport, data in sorted(sport_data.items()):
            win_rate_sport = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            roi_sport = (data['profit_loss'] / data['wagered'] * 100) if data['wagered'] > 0 else 0
            by_sport.append({
                'sport': sport,
                'total': data['total'],
                'wins': data['wins'],
                'losses': data['losses'],
                'pushes': data['pushes'],
                'win_rate': round(win_rate_sport, 1),
                'profit_loss': round(data['profit_loss'], 2),
                'roi': round(roi_sport, 1)
            })

        # Performance by bet type
        bet_type_data = defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0, 'pushes': 0, 'profit_loss': 0.0, 'wagered': 0.0})
        for bet in settled_bets:
            bet_type = bet.bet_type or 'Unknown'
            bet_type_data[bet_type]['total'] += 1
            if bet.status == 'won':
                bet_type_data[bet_type]['wins'] += 1
            elif bet.status == 'lost':
                bet_type_data[bet_type]['losses'] += 1
            else:
                bet_type_data[bet_type]['pushes'] += 1
            bet_type_data[bet_type]['profit_loss'] += bet.profit_loss or 0
            bet_type_data[bet_type]['wagered'] += bet.stake or 0

        by_bet_type = []
        for bet_type, data in sorted(bet_type_data.items()):
            win_rate_type = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            roi_type = (data['profit_loss'] / data['wagered'] * 100) if data['wagered'] > 0 else 0
            by_bet_type.append({
                'bet_type': bet_type,
                'total': data['total'],
                'wins': data['wins'],
                'losses': data['losses'],
                'pushes': data['pushes'],
                'win_rate': round(win_rate_type, 1),
                'profit_loss': round(data['profit_loss'], 2),
                'roi': round(roi_type, 1)
            })

        # Performance by bookmaker
        bookmaker_data = defaultdict(lambda: {'total': 0, 'wins': 0, 'profit_loss': 0.0})
        for bet in settled_bets:
            book = bet.bookmaker or 'Unknown'
            bookmaker_data[book]['total'] += 1
            if bet.status == 'won':
                bookmaker_data[book]['wins'] += 1
            bookmaker_data[book]['profit_loss'] += bet.profit_loss or 0

        by_bookmaker = []
        for book, data in sorted(bookmaker_data.items(), key=lambda x: x[1]['total'], reverse=True)[:10]:
            by_bookmaker.append({
                'bookmaker': book,
                'total': data['total'],
                'wins': data['wins'],
                'profit_loss': round(data['profit_loss'], 2)
            })

        return {
            'summary': {
                'total_bets': total_settled,
                'wins': won_bets,
                'losses': lost_bets,
                'pushes': push_bets,
                'win_rate': round(win_rate, 1),
                'total_wagered': round(total_wagered, 2),
                'net_profit_loss': round(total_profit_loss, 2),
                'roi': round(roi, 1),
                'avg_stake': round(avg_stake, 2)
            },
            'history': history,
            'by_sport': by_sport,
            'by_bet_type': by_bet_type,
            'by_bookmaker': by_bookmaker,
            'time_range': f'{days}d' if days else 'all'
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
