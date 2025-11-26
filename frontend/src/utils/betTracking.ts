/**
 * Bet Tracking Utilities
 * Functions for tracking user bets when they click bookmaker deep links
 */

import { getApiUrl } from '../config';

interface TrackBetClickParams {
  userId: string;
  gameId: string;
  sport: string;
  homeTeam: string;
  awayTeam: string;
  commenceTime: string;
  betType: 'spread' | 'total' | 'moneyline' | 'prop';
  betSide: string;  // "OVER", "UNDER", team name, etc.
  odds: number;
  bookmaker: string;
  alertId?: string;
  confidence?: 'HIGH' | 'MEDIUM' | 'LOW' | 'CRITICAL';
  edgePercent?: number;
  strategy?: string;
}

interface UserBet {
  id: string;
  status: 'pending' | 'active' | 'won' | 'lost' | 'push' | 'cancelled';
  stake?: number;
  // ... other fields from backend model
}

/**
 * Track a bookmaker click and create a pending bet
 */
export async function trackBetClick(params: TrackBetClickParams): Promise<UserBet | null> {
  try {
    const response = await fetch(getApiUrl('/bets/track-click'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: params.userId,
        game_id: params.gameId,
        sport: params.sport,
        home_team: params.homeTeam,
        away_team: params.awayTeam,
        commence_time: params.commenceTime,
        bet_type: params.betType,
        bet_side: params.betSide,
        odds: params.odds,
        bookmaker: params.bookmaker,
        alert_id: params.alertId,
        confidence: params.confidence,
        edge_percent: params.edgePercent,
        strategy: params.strategy,
      }),
    });

    if (!response.ok) {
      console.error('Failed to track bet click:', await response.text());
      return null;
    }

    const bet = await response.json();
    return bet;
  } catch (error) {
    console.error('Error tracking bet click:', error);
    return null;
  }
}

/**
 * Get all pending bets for a user
 */
export async function getPendingBets(userId: string): Promise<UserBet[]> {
  try {
    const response = await fetch(getApiUrl(`/bets/pending?user_id=${userId}`));
    if (!response.ok) {
      console.error('Failed to fetch pending bets');
      return [];
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching pending bets:', error);
    return [];
  }
}

/**
 * Get all bets for a user with optional filters
 */
export async function getUserBets(
  userId: string,
  status?: string,
  sport?: string
): Promise<UserBet[]> {
  try {
    const params = new URLSearchParams({ user_id: userId });
    if (status) params.append('status', status);
    if (sport) params.append('sport', sport);

    const response = await fetch(getApiUrl(`/bets/my-bets?${params}`));
    if (!response.ok) {
      console.error('Failed to fetch user bets');
      return [];
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching user bets:', error);
    return [];
  }
}

/**
 * Add stake to a pending bet
 */
export async function addStakeToBet(betId: string, stake: number): Promise<UserBet | null> {
  try {
    const response = await fetch(getApiUrl(`/bets/${betId}/add-stake`), {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ stake }),
    });

    if (!response.ok) {
      console.error('Failed to add stake to bet');
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error('Error adding stake to bet:', error);
    return null;
  }
}

/**
 * Update bet details (odds, stake, bet_side, bookmaker, etc.)
 */
export async function updateBet(
  betId: string,
  updates: {
    betSide?: string;
    odds?: number;
    stake?: number;
    bookmaker?: string;
    confidence?: 'HIGH' | 'MEDIUM' | 'LOW' | 'CRITICAL';
    edgePercent?: number;
  }
): Promise<UserBet | null> {
  try {
    const response = await fetch(getApiUrl(`/bets/${betId}/update`), {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        bet_side: updates.betSide,
        odds: updates.odds,
        stake: updates.stake,
        bookmaker: updates.bookmaker,
        confidence: updates.confidence,
        edge_percent: updates.edgePercent,
      }),
    });

    if (!response.ok) {
      console.error('Failed to update bet');
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error('Error updating bet:', error);
    return null;
  }
}

/**
 * Settle a bet with win/loss/push result
 */
export async function settleBet(
  betId: string,
  result: 'win' | 'loss' | 'push'
): Promise<UserBet | null> {
  try {
    const response = await fetch(getApiUrl(`/bets/${betId}/settle`), {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ result: ({'win': 'won', 'loss': 'lost', 'push': 'push'}[result] || result) }),
    });

    if (!response.ok) {
      console.error('Failed to settle bet');
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error('Error settling bet:', error);
    return null;
  }
}

/**
 * Delete a pending bet (user didn't actually place it)
 */
export async function deleteBet(betId: string): Promise<boolean> {
  try {
    const response = await fetch(getApiUrl(`/bets/${betId}`), {
      method: 'DELETE',
    });

    return response.ok;
  } catch (error) {
    console.error('Error deleting bet:', error);
    return false;
  }
}

/**
 * Get user betting stats
 */
export async function getUserBettingStats(userId: string) {
  try {
    const response = await fetch(getApiUrl(`/bets/user/${userId}/stats`));
    if (!response.ok) {
      console.error('Failed to fetch betting stats');
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching betting stats:', error);
    return null;
  }
}

/**
 * Manually add a bet entry with all details
 */
export async function addManualBet(params: {
  userId: string;
  sport: string;
  homeTeam: string;
  awayTeam: string;
  commenceTime: string;
  betType: 'spread' | 'total' | 'moneyline' | 'prop';
  betSide: string;
  odds: number;
  stake: number;
  bookmaker: string;
  confidence?: 'HIGH' | 'MEDIUM' | 'LOW' | 'CRITICAL';
  edgePercent?: number;
  notes?: string;
}): Promise<UserBet | null> {
  try {
    const response = await fetch(getApiUrl('/bets/manual-entry'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: params.userId,
        sport: params.sport,
        home_team: params.homeTeam,
        away_team: params.awayTeam,
        commence_time: params.commenceTime,
        bet_type: params.betType,
        bet_side: params.betSide,
        odds: params.odds,
        stake: params.stake,
        bookmaker: params.bookmaker,
        confidence: params.confidence,
        edge_percent: params.edgePercent,
        notes: params.notes,
      }),
    });

    if (!response.ok) {
      console.error('Failed to add manual bet:', await response.text());
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error('Error adding manual bet:', error);
    return null;
  }
}

/**
 * Get detailed performance data for charts and analytics
 */
export interface PerformanceData {
  summary: {
    total_bets: number;
    wins: number;
    losses: number;
    pushes: number;
    win_rate: number;
    total_wagered: number;
    net_profit_loss: number;
    roi: number;
    avg_stake: number;
  };
  history: Array<{
    date: string;
    wins: number;
    losses: number;
    pushes: number;
    daily_pl: number;
    cumulative_pl: number;
    daily_wagered: number;
    cumulative_wagered: number;
  }>;
  by_sport: Array<{
    sport: string;
    total: number;
    wins: number;
    losses: number;
    pushes: number;
    win_rate: number;
    profit_loss: number;
    roi: number;
  }>;
  by_bet_type: Array<{
    bet_type: string;
    total: number;
    wins: number;
    losses: number;
    pushes: number;
    win_rate: number;
    profit_loss: number;
    roi: number;
  }>;
  by_bookmaker: Array<{
    bookmaker: string;
    total: number;
    wins: number;
    profit_loss: number;
  }>;
  time_range: string;
}

export async function getUserPerformanceData(userId: string, days?: number): Promise<PerformanceData | null> {
  try {
    const params = new URLSearchParams();
    if (days) params.append('days', days.toString());

    const url = getApiUrl(`/bets/user/${userId}/performance${params.toString() ? '?' + params.toString() : ''}`);
    const response = await fetch(url);
    if (!response.ok) {
      console.error('Failed to fetch performance data');
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching performance data:', error);
    return null;
  }
}

