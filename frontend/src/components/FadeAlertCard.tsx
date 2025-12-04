import React, { useState } from 'react';

interface FadeOpportunity {
  game_id: string;
  sport_key: string;
  home_team: string;
  away_team: string;
  favorite_team: string;
  pregame_odds: number;
  live_odds: number;
  tier: string;
  improvement_pct: number;
  time_left: string;
  time_left_seconds: number;
  quarter: string;
  plateau_detected: boolean;
  plateau_strength: number;
  base_ev: number;
  adjusted_ev: number;
  underdog_team: string;
  underdog_live_odds: number;
  recommended_hedge_trigger: number;
}

interface FadeAlertCardProps {
  opportunity: FadeOpportunity;
  onEnterPosition: (data: {
    stake: number;
    hedge_trigger: number;
  }) => void;
}

const TIER_COLORS = {
  GOLD: 'from-yellow-400 via-yellow-500 to-yellow-600',
  SILVER: 'from-gray-300 via-gray-400 to-gray-500',
  BRONZE: 'from-orange-700 via-orange-800 to-orange-900'
};

const TIER_BADGE_COLORS = {
  GOLD: 'bg-yellow-400 text-gray-900',
  SILVER: 'bg-gray-300 text-gray-900',
  BRONZE: 'bg-orange-700 text-white'
};

export const FadeAlertCard: React.FC<FadeAlertCardProps> = ({
  opportunity,
  onEnterPosition
}) => {
  const [stake, setStake] = useState(200);
  const [hedgeTrigger, setHedgeTrigger] = useState(opportunity.recommended_hedge_trigger);
  const [loading, setLoading] = useState(false);

  const handleEnter = async () => {
    setLoading(true);
    try {
      await onEnterPosition({ stake, hedge_trigger: hedgeTrigger });
    } finally {
      setLoading(false);
    }
  };

  const gradientClass = TIER_COLORS[opportunity.tier as keyof typeof TIER_COLORS] || TIER_COLORS.BRONZE;
  const badgeClass = TIER_BADGE_COLORS[opportunity.tier as keyof typeof TIER_BADGE_COLORS] || TIER_BADGE_COLORS.BRONZE;

  return (
    <div className={`bg-gradient-to-br ${gradientClass} border-4 border-opacity-70 rounded-lg p-4 mb-4 shadow-lg`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className={`${badgeClass} px-3 py-1 rounded-full font-bold text-sm`}>
            {opportunity.tier} FADE
          </span>
          {opportunity.plateau_detected && (
            <span className="bg-green-500 text-white px-2 py-1 rounded text-xs font-bold">
              PLATEAU
            </span>
          )}
        </div>
        <div className="text-right">
          <div className="text-white font-bold text-lg">
            +{opportunity.improvement_pct.toFixed(1)}% DISCOUNT
          </div>
          <div className="text-white text-xs opacity-90">
            {opportunity.adjusted_ev.toFixed(1)}% EV
          </div>
        </div>
      </div>

      {/* Favorite Info */}
      <div className="bg-black bg-opacity-30 rounded-lg p-3 mb-3">
        <div className="text-white font-bold text-lg mb-1">
          {opportunity.favorite_team}
        </div>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-gray-300 text-sm">Pregame</div>
            <div className="text-white font-bold text-xl">
              {opportunity.pregame_odds > 0 ? '+' : ''}{opportunity.pregame_odds}
            </div>
          </div>
          <div className="text-white text-2xl">→</div>
          <div>
            <div className="text-gray-300 text-sm">Live Now</div>
            <div className="text-green-400 font-bold text-xl">
              {opportunity.live_odds > 0 ? '+' : ''}{opportunity.live_odds}
            </div>
          </div>
        </div>
      </div>

      {/* Game State */}
      <div className="flex items-center justify-between text-white text-sm mb-3 opacity-90">
        <div>
          <span className="font-semibold">{opportunity.quarter}</span>
          <span className="mx-2">•</span>
          <span className="font-semibold">{opportunity.time_left}</span> left
        </div>
        {opportunity.plateau_strength > 0 && (
          <div className="text-xs">
            Plateau: {opportunity.plateau_strength.toFixed(0)}%
          </div>
        )}
      </div>

      {/* Entry Form */}
      <div className="bg-black bg-opacity-40 rounded-lg p-3 space-y-3">
        <div>
          <label className="block text-white text-sm font-semibold mb-1">
            Your Stake
          </label>
          <div className="flex items-center space-x-2">
            <span className="text-white font-bold text-lg">$</span>
            <input
              type="number"
              value={stake}
              onChange={(e) => setStake(Number(e.target.value))}
              className="flex-1 bg-gray-800 text-white px-3 py-2 rounded-lg border-2 border-gray-600 focus:border-white focus:outline-none"
              step="50"
              min="50"
            />
          </div>
        </div>

        <div>
          <label className="block text-white text-sm font-semibold mb-1">
            Hedge Trigger (Underdog Odds)
          </label>
          <div className="flex items-center space-x-2">
            <span className="text-white font-bold text-lg">+</span>
            <input
              type="number"
              value={hedgeTrigger}
              onChange={(e) => setHedgeTrigger(Number(e.target.value))}
              className="flex-1 bg-gray-800 text-white px-3 py-2 rounded-lg border-2 border-gray-600 focus:border-white focus:outline-none"
              step="10"
              min="200"
            />
          </div>
          <div className="text-gray-300 text-xs mt-1">
            Alert when {opportunity.underdog_team} hits +{hedgeTrigger}
          </div>
        </div>

        <button
          onClick={handleEnter}
          disabled={loading}
          className="w-full bg-white text-gray-900 font-bold py-3 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'ENTERING...' : `ENTER ${opportunity.tier} FADE - $${stake}`}
        </button>
      </div>

      {/* Expected Value Info */}
      <div className="mt-3 text-white text-xs opacity-75 text-center">
        Base EV: {opportunity.base_ev.toFixed(1)}% | Adjusted: {opportunity.adjusted_ev.toFixed(1)}%
        {opportunity.plateau_detected && ' | Plateau Confirmed'}
      </div>
    </div>
  );
};

export default FadeAlertCard;
