/**
 * Hedge Alert Toast
 * Small popup notification that appears in top-right corner when hedge opportunity is detected
 * Clicking opens full modal with hedge details
 */

import { Lock, X, DollarSign } from 'lucide-react';
import { HedgeToastData } from '../services/hedgeAlertService';

interface HedgeAlertToastProps {
  toast: HedgeToastData;
  onClick: () => void;
  onDismiss: () => void;
}

export function HedgeAlertToast({ toast, onClick, onDismiss }: HedgeAlertToastProps) {
  return (
    <div
      className="fixed top-20 right-4 z-50 w-96 animate-slide-in-right cursor-pointer"
      onClick={onClick}
    >
      <div className="bg-gradient-to-br from-green-700 via-green-800 to-green-900 border-4 border-green-600 rounded-xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-600 to-green-700 px-4 py-3 border-b-2 border-green-500 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Lock size={24} className="text-white" />
            <div>
              <div className="font-bold text-white text-base">Hedge Opportunity!</div>
              <div className="text-xs text-green-100">Lock in guaranteed profit</div>
            </div>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDismiss();
            }}
            className="text-white/60 hover:text-white transition-colors text-2xl font-bold w-8 h-8 flex items-center justify-center"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {/* Game Info */}
          <div className="mb-3">
            <div className="text-white font-bold text-lg mb-1">
              {toast.alert.home_team} vs {toast.alert.away_team}
            </div>
            <div className="text-green-200 text-sm">
              {toast.alert.sport.replace('basketball_', '').replace('americanfootball_', '').replace('icehockey_', '').toUpperCase()}
            </div>
          </div>

          {/* Profit Display */}
          <div className="bg-gradient-to-br from-yellow-700 to-yellow-900 rounded-lg p-3 border-2 border-yellow-500 mb-3">
            <div className="flex items-center justify-center gap-2">
              <DollarSign size={28} className="text-yellow-400" />
              <div className="text-center">
                <div className="text-2xl font-bold text-white">
                  ${toast.alert.profit.guaranteed.toFixed(2)}
                </div>
                <div className="text-xs text-yellow-300">
                  Guaranteed Profit ({toast.alert.profit.roi_percent.toFixed(1)}% ROI)
                </div>
              </div>
            </div>
          </div>

          {/* Hedge Details Summary */}
          <div className="bg-slate-900/50 rounded-lg p-3 border border-green-600/30">
            <div className="text-xs text-green-300 font-semibold mb-2">HEDGE BET RECOMMENDATION:</div>
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-slate-300">Side:</span>
                <span className="text-white font-bold">{toast.alert.hedge_bet.side}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-300">Stake:</span>
                <span className="text-white font-bold">${toast.alert.hedge_bet.stake.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-300">Odds:</span>
                <span className="text-white font-bold">
                  {toast.alert.hedge_bet.odds > 0 ? '+' : ''}{toast.alert.hedge_bet.odds}
                </span>
              </div>
            </div>
          </div>

          {/* Click for details */}
          <div className="mt-3 text-center">
            <div className="text-xs text-green-300 font-semibold animate-pulse">
              👆 Click for full details
            </div>
          </div>
        </div>

        {/* Footer timestamp */}
        <div className="px-4 py-2 bg-black/20 border-t border-green-700">
          <p className="text-xs text-green-300 text-center">
            Detected at {new Date(toast.timestamp).toLocaleTimeString()}
          </p>
        </div>
      </div>
    </div>
  );
}
