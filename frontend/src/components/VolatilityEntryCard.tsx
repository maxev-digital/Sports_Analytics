/**
 * Volatility Arbitrage Entry Card
 *
 * Displays +EV entry opportunities for volatility arbitrage
 * Shows when a team is at +money odds with positive expected value
 */

import { useState } from 'react';
import { TrendingUp, Target, DollarSign, Info, ChevronDown, ChevronUp } from 'lucide-react';

export interface VolatilityEntryOpportunity {
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;

  // Entry details
  entry_team: string;
  entry_side: 'home' | 'away';
  entry_odds: number; // American odds (e.g., +200)

  // Edge calculation
  implied_prob: number;
  true_prob: number;
  edge: number;
  ev_percent: number;

  // Game state
  quarter: string;
  time_remaining: string;
  score_home: number;
  score_away: number;

  // Recommendations
  recommended_stake: number;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  suggested_trigger_odds: number;
  min_locked_profit: number;

  // Metadata
  bookmaker: string;
  bookmaker_title: string;
}

interface VolatilityEntryCardProps {
  opportunity: VolatilityEntryOpportunity;
  onEnterPosition?: (data: {
    stake: number;
    trigger_price: number;
  }) => void;
}

export function VolatilityEntryCard({ opportunity, onEnterPosition }: VolatilityEntryCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [stake, setStake] = useState(opportunity.recommended_stake);
  const [triggerPrice, setTriggerPrice] = useState(opportunity.suggested_trigger_odds);
  const [showInfo, setShowInfo] = useState(false);

  const handleEnter = () => {
    if (onEnterPosition) {
      onEnterPosition({ stake, trigger_price: triggerPrice });
    }
  };

  // Calculate potential outcomes
  const potentialWin = stake * (opportunity.entry_odds / 100);
  const evIfHold = stake * (opportunity.ev_percent / 100);
  const evIfHedge = stake * 0.157; // 15.7% from config

  // Confidence colors
  const getConfidenceColor = () => {
    switch (opportunity.confidence) {
      case 'HIGH':
        return 'text-emerald-400 bg-emerald-900/30 border-emerald-600';
      case 'MEDIUM':
        return 'text-blue-400 bg-blue-900/30 border-blue-600';
      default:
        return 'text-yellow-400 bg-yellow-900/30 border-yellow-600';
    }
  };

  return (
    <div className="mt-4 bg-gradient-to-br from-cyan-900 via-blue-900 to-indigo-900 border-4 border-cyan-600 rounded-lg shadow-xl overflow-hidden">
      {/* Header */}
      <div
        className="p-4 cursor-pointer hover:bg-white/5 transition-all"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-cyan-500/20 rounded-lg">
              <Target className="w-6 h-6 text-cyan-300" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-bold text-white">
                  VOLATILITY ARB ENTRY
                </h3>
                <span className={`px-2 py-0.5 rounded text-xs font-bold border ${getConfidenceColor()}`}>
                  {opportunity.confidence}
                </span>
              </div>
              <p className="text-cyan-200 text-sm">
                Two +money tickets strategy - Lock profit both sides
              </p>
            </div>
          </div>

          <button className="text-white/70 hover:text-white transition-colors">
            {isExpanded ? <ChevronUp className="w-6 h-6" /> : <ChevronDown className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-cyan-600/50 p-4 space-y-4 bg-black/20">
          {/* Opportunity Details */}
          <div className="grid grid-cols-2 gap-4">
            {/* Entry Side */}
            <div className="bg-white/5 rounded-lg p-3">
              <div className="text-cyan-300 text-sm mb-1">Entry Opportunity</div>
              <div className="text-white font-bold text-lg">
                {opportunity.entry_team}
              </div>
              <div className="text-emerald-300 font-bold text-2xl">
                {opportunity.entry_odds > 0 ? '+' : ''}{opportunity.entry_odds}
              </div>
              <div className="text-xs text-white/60 mt-1">
                {opportunity.bookmaker_title}
              </div>
            </div>

            {/* Edge Analysis */}
            <div className="bg-white/5 rounded-lg p-3">
              <div className="text-cyan-300 text-sm mb-1">Edge Analysis</div>
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-white/70">Market:</span>
                  <span className="text-white">{(opportunity.implied_prob * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-white/70">ML Model:</span>
                  <span className="text-white">{(opportunity.true_prob * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-sm border-t border-white/20 pt-1">
                  <span className="text-emerald-300 font-semibold">Edge:</span>
                  <span className="text-emerald-300 font-bold">+{(opportunity.edge * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Game State */}
          <div className="bg-white/5 rounded-lg p-3">
            <div className="text-cyan-300 text-sm mb-2">Current Game State</div>
            <div className="flex justify-between items-center">
              <div className="text-white text-sm">
                {opportunity.quarter} | {opportunity.time_remaining}
              </div>
              <div className="text-white font-semibold">
                {opportunity.away_team} {opportunity.score_away} - {opportunity.score_home} {opportunity.home_team}
              </div>
            </div>
          </div>

          {/* Entry Form */}
          <div className="bg-gradient-to-r from-blue-900/50 to-indigo-900/50 rounded-lg p-4 border border-blue-500/30">
            <h4 className="text-white font-bold mb-3 flex items-center gap-2">
              <DollarSign className="w-5 h-5" />
              Enter Position
            </h4>

            <div className="space-y-3">
              {/* Stake Input */}
              <div>
                <label className="text-cyan-300 text-sm block mb-1">
                  Stake Amount
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-white/70">$</span>
                  <input
                    type="number"
                    value={stake}
                    onChange={(e) => setStake(Number(e.target.value))}
                    className="w-full bg-black/30 border border-white/20 rounded-lg py-2 pl-8 pr-3 text-white focus:border-cyan-500 focus:outline-none"
                    placeholder="200"
                  />
                </div>
                <div className="text-xs text-white/50 mt-1">
                  Recommended: ${opportunity.recommended_stake}
                </div>
              </div>

              {/* Trigger Price Input */}
              <div>
                <label className="text-cyan-300 text-sm block mb-1">
                  Hedge Trigger Price
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-white/70">+</span>
                  <input
                    type="number"
                    value={triggerPrice}
                    onChange={(e) => setTriggerPrice(Number(e.target.value))}
                    className="w-full bg-black/30 border border-white/20 rounded-lg py-2 pl-8 pr-3 text-white focus:border-cyan-500 focus:outline-none"
                    placeholder="280"
                  />
                </div>
                <div className="text-xs text-white/50 mt-1">
                  Alert when opposite side hits +{triggerPrice} or better
                </div>
              </div>
            </div>

            {/* Projections */}
            <div className="mt-4 pt-4 border-t border-white/20 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-white/70">Potential Win (First Bet):</span>
                <span className="text-emerald-300 font-semibold">+${potentialWin.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-white/70">EV if Hold:</span>
                <span className="text-white">+${evIfHold.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-white/70">EV if Hedge Triggers:</span>
                <span className="text-cyan-300 font-semibold">+${evIfHedge.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm border-t border-white/20 pt-2">
                <span className="text-emerald-300 font-bold">Min Locked Profit Target:</span>
                <span className="text-emerald-300 font-bold">+${(stake * 0.10).toFixed(2)}</span>
              </div>
            </div>

            {/* Enter Button */}
            <button
              onClick={handleEnter}
              className="w-full mt-4 py-3 bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500 text-white font-bold rounded-lg shadow-lg transition-all transform hover:scale-105"
            >
              Enter Position - ${stake}
            </button>
          </div>

          {/* Info Section */}
          <button
            onClick={() => setShowInfo(!showInfo)}
            className="w-full flex items-center justify-center gap-2 text-cyan-300 hover:text-cyan-200 text-sm transition-colors"
          >
            <Info className="w-4 h-4" />
            <span>{showInfo ? 'Hide' : 'Show'} Strategy Info</span>
          </button>

          {showInfo && (
            <div className="bg-white/5 rounded-lg p-4 text-sm text-white/80 leading-relaxed">
              <h5 className="text-white font-bold mb-2">How Volatility Arbitrage Works:</h5>
              <ol className="list-decimal list-inside space-y-1">
                <li>Enter first position at +{opportunity.entry_odds} (underdog odds)</li>
                <li>System monitors game for opposite side to hit +{triggerPrice}</li>
                <li>If trigger hits: Lock profit by betting opposite side</li>
                <li>If trigger doesn't hit: Ride +{(opportunity.ev_percent).toFixed(1)}% EV position</li>
              </ol>
              <div className="mt-2 pt-2 border-t border-white/20">
                <div className="text-xs text-white/60">
                  Expected: 35% trigger rate | 15.7% avg EV | Higher variance than traditional arb
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Volatility Entry Badge (for collapsed view in game cards)
 */
export function VolatilityEntryBadge({ opportunity }: { opportunity: VolatilityEntryOpportunity }) {
  return (
    <div className="mt-2 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-lg p-3 border-2 border-cyan-400">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Target className="w-5 h-5 text-white" />
          <div>
            <div className="text-white font-bold text-sm">VOLATILITY ARB</div>
            <div className="text-cyan-100 text-xs">
              {opportunity.entry_team} {opportunity.entry_odds > 0 ? '+' : ''}{opportunity.entry_odds} |
              +{(opportunity.ev_percent).toFixed(1)}% EV
            </div>
          </div>
        </div>
        <div className="text-emerald-300 font-bold text-lg">
          ▶
        </div>
      </div>
    </div>
  );
}
