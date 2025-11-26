/**
 * Hedge Alert Modal - Shows hedge opportunity details with action buttons
 */

import { DollarSign, TrendingUp, Lock, X } from 'lucide-react';

export interface HedgeAlertData {
  alert_id: string;
  user_id: string;
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  original_bet: {
    bet_id: string;
    side: string;
    stake: number;
    odds: number;
    bookmaker: string;
  };
  hedge_bet: {
    side: string;
    stake: number;
    odds: number;
    bookmaker: string;
  };
  profit: {
    guaranteed: number;
    roi_percent: number;
  };
  timestamp: string;
  message: string;
}

interface HedgeAlertModalProps {
  alert: HedgeAlertData | null;
  isOpen: boolean;
  onClose: () => void;
  onPlaceHedge?: (alert: HedgeAlertData) => void;
  onDismiss?: (alert: HedgeAlertData) => void;
}

export function HedgeAlertModal({ alert, isOpen, onClose, onPlaceHedge, onDismiss }: HedgeAlertModalProps) {
  if (!isOpen || !alert) return null;

  const handlePlaceHedge = () => {
    if (onPlaceHedge) {
      onPlaceHedge(alert);
    }
    onClose();
  };

  const handleDismiss = () => {
    if (onDismiss) {
      onDismiss(alert);
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 p-4">
      <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950 border-4 border-green-600 rounded-xl shadow-2xl max-w-2xl w-full p-6 relative">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
        >
          <X size={24} />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-green-900 rounded-lg">
            <Lock size={32} className="text-green-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Hedge Opportunity Detected!</h2>
            <p className="text-slate-400">{alert.home_team} vs {alert.away_team}</p>
          </div>
        </div>

        {/* Original Bet */}
        <div className="mb-4 p-4 bg-slate-800 rounded-lg border-2 border-slate-700">
          <h3 className="text-sm font-bold text-slate-400 mb-2 uppercase">Original Bet</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-slate-500">Side</p>
              <p className="text-white font-bold">{alert.original_bet.side}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Stake</p>
              <p className="text-white font-bold">${alert.original_bet.stake.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Odds</p>
              <p className="text-white font-bold">{alert.original_bet.odds > 0 ? '+' : ''}{alert.original_bet.odds}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Bookmaker</p>
              <p className="text-white font-bold capitalize">{alert.original_bet.bookmaker}</p>
            </div>
          </div>
        </div>

        {/* Hedge Bet */}
        <div className="mb-4 p-4 bg-gradient-to-br from-green-900 to-green-950 rounded-lg border-2 border-green-600">
          <h3 className="text-sm font-bold text-green-400 mb-2 uppercase">Recommended Hedge Bet</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-green-300">Side</p>
              <p className="text-white font-bold">{alert.hedge_bet.side}</p>
            </div>
            <div>
              <p className="text-xs text-green-300">Stake</p>
              <p className="text-white font-bold text-lg">${alert.hedge_bet.stake.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-xs text-green-300">Odds</p>
              <p className="text-white font-bold">{alert.hedge_bet.odds > 0 ? '+' : ''}{alert.hedge_bet.odds}</p>
            </div>
            <div>
              <p className="text-xs text-green-300">Bookmaker</p>
              <p className="text-white font-bold capitalize">{alert.hedge_bet.bookmaker}</p>
            </div>
          </div>
        </div>

        {/* Guaranteed Profit */}
        <div className="mb-6 p-6 bg-gradient-to-br from-yellow-900 to-yellow-950 rounded-lg border-4 border-yellow-600 text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <DollarSign size={32} className="text-yellow-400" />
            <h3 className="text-3xl font-bold text-white">
              ${alert.profit.guaranteed.toFixed(2)}
            </h3>
          </div>
          <p className="text-yellow-400 font-bold text-lg">Guaranteed Profit (Either Outcome)</p>
          <div className="flex items-center justify-center gap-2 mt-2">
            <TrendingUp size={20} className="text-green-400" />
            <p className="text-green-400 font-bold">{alert.profit.roi_percent.toFixed(1)}% ROI</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={handlePlaceHedge}
            className="flex-1 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-500 hover:to-green-600 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 shadow-lg"
          >
            Place Hedge Bet
          </button>
          <button
            onClick={handleDismiss}
            className="flex-1 bg-slate-700 hover:bg-slate-600 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200"
          >
            Dismiss
          </button>
        </div>

        {/* Timestamp */}
        <p className="text-xs text-slate-500 text-center mt-4">
          Detected at {new Date(alert.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}
