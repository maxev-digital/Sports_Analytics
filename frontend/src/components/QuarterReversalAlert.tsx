import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useQuarterReversalWebSocket } from '../hooks/useQuarterReversalWebSocket';

interface BetRecommendation {
  rank: number;
  label: string;
  odds: string;
  decimal_odds: number;
  probability: number;
  expected_value: number;
  bet_type: string;
  variance: number;
  score: number;
  kelly_size?: number;
  kelly_pct?: number;
  full_kelly_pct?: number;
  context?: string;
}

interface QuarterReversalOpportunity {
  game_id: string;
  matchup: string;
  strategy: 'Q1-Q2_to_Q3' | 'Q2-Q3_to_Q4' | 'Q3-Q4_to_OT' | 'COMBO' | 'HEDGE';
  hot_team: string;
  reversal_team: string;
  quarter: string;
  trigger: string;
  reversal_prob: string;
  expected_roi: string;
  alert_level: 'HIGH' | 'MEDIUM' | 'CRITICAL';
  reasoning: string;
  recommendations: BetRecommendation[];
  total_options: number;
  timestamp: string;
}

interface ColdTeamOpportunity {
  game_id: string;
  matchup: string;
  strategy: 'COLD_TEAM_Q4';
  cold_team: string;
  hot_team: string;
  quarter: string;
  trigger: string;
  confidence: number;
  expected_roi: string;
  alert_level: 'HIGH' | 'MEDIUM' | 'CRITICAL';
  reasoning: string;
  quality_differential: number | null;
  recommendations: BetRecommendation[];
  total_options: number;
  timestamp: string;
}

export const QuarterReversalAlerts: React.FC = () => {
  // Use WebSocket for real-time updates
  const {
    opportunities: wsOpportunities,
    coldTeamOpportunities: wsColdTeamOpportunities,
    connected: wsConnected,
    error: wsError
  } = useQuarterReversalWebSocket('default');
  const [opportunities, setOpportunities] = useState<QuarterReversalOpportunity[]>([]);
  const [coldTeamOpportunities, setColdTeamOpportunities] = useState<ColdTeamOpportunity[]>([]);
  const { subscriptionTier } = useAuth();

  // Mock bankroll for demo - in production, get from user settings
  const bankroll = subscriptionTier === 'elite' ? 10000 : subscriptionTier === 'pro' ? 5000 : null;
  const riskProfile = 'balanced';

  // Update opportunities from WebSocket
  useEffect(() => {
    if (wsOpportunities.length > 0) {
      setOpportunities(wsOpportunities);
    }
  }, [wsOpportunities]);

  // Update cold team opportunities from WebSocket
  useEffect(() => {
    if (wsColdTeamOpportunities.length > 0) {
      setColdTeamOpportunities(wsColdTeamOpportunities);
    }
  }, [wsColdTeamOpportunities]);

  if (!wsConnected) {
    return (
      <div className="bg-slate-800 border-4 border-slate-700 rounded-lg p-12 text-center">
        <div className="flex items-center justify-center gap-3 mb-3">
          <span className="inline-block w-3 h-3 rounded-full bg-red-500 animate-pulse" />
          <div className="text-slate-400 text-lg">Connecting to real-time alerts...</div>
        </div>
        {wsError && (
          <div className="text-red-400 text-sm mt-2">{wsError}</div>
        )}
      </div>
    );
  }

  if (opportunities.length === 0 && coldTeamOpportunities.length === 0) {
    return (
      <div className="bg-slate-800 border-4 border-slate-700 rounded-lg p-12 text-center">
        <div className="flex items-center justify-center gap-3 mb-3">
          <span className="inline-block w-3 h-3 rounded-full bg-green-500" />
          <div className="text-slate-400 text-lg">No quarter-based strategies detected</div>
        </div>
        <div className="text-slate-500 text-sm">Monitoring live NBA games via WebSocket (5s refresh)...</div>
        <div className="text-slate-600 text-xs mt-4 space-y-2">
          <div>🔄 <strong>Quarter Reversal:</strong> When team wins Q1 & Q2 → Bet opponent Q3 (56% WR, +26% ROI)</div>
          <div>❄️ <strong>Cold Team Bounce-Back:</strong> When team loses Q1, Q2 & Q3 → Bet them Q4 (64% WR, +44% ROI)</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {opportunities.map((opp, idx) => {
        const isCritical = opp.alert_level === 'CRITICAL';
        const isHigh = opp.alert_level === 'HIGH';
        const isCombo = opp.strategy === 'COMBO';
        const isHedge = opp.strategy === 'HEDGE';
        const topRec = opp.recommendations[0];

        // Special styling for combo alerts (Q3 + OT double trigger - extremely rare)
        const comboStyle = isCombo
          ? 'bg-gradient-to-br from-purple-900 via-pink-800 to-purple-900 border-pink-500 shadow-lg shadow-pink-600/50 animate-pulse'
          : '';

        // Special styling for hedge alerts (anti-reversal when pattern weak)
        const hedgeStyle = isHedge
          ? 'bg-gradient-to-br from-slate-800 via-slate-700 to-slate-800 border-slate-500'
          : '';

        const cardStyle = isCombo
          ? comboStyle
          : isHedge
          ? hedgeStyle
          : isCritical
          ? 'bg-gradient-to-br from-red-900 via-yellow-800 to-red-900 border-yellow-500 shadow-lg shadow-yellow-600/30'
          : isHigh
          ? 'bg-gradient-to-br from-green-900 via-green-800 to-green-900 border-green-500 shadow-lg shadow-green-600/30'
          : 'bg-gradient-to-br from-blue-900 via-blue-800 to-blue-900 border-blue-500';

        return (
          <div
            key={`${opp.game_id}-${idx}`}
            className={`rounded-lg p-6 border-4 ${cardStyle}`}
          >
            {/* Alert Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3 flex-wrap">
                <span
                  className={`px-4 py-2 rounded-lg font-bold text-white text-sm tracking-wide ${
                    isCombo
                      ? 'bg-purple-600 border-2 border-pink-400 animate-pulse'
                      : isHedge
                      ? 'bg-slate-600 border-2 border-slate-400'
                      : isCritical
                      ? 'bg-red-600 border-2 border-yellow-400 animate-pulse'
                      : isHigh
                      ? 'bg-green-600 border-2 border-green-400'
                      : 'bg-blue-600 border-2 border-blue-400'
                  }`}
                >
                  {isCombo ? '💎' : isHedge ? '🛡️' : isCritical ? '🚨' : isHigh ? '🔥' : '📈'} {isCombo ? 'COMBO' : isHedge ? 'HEDGE' : opp.alert_level} ALERT
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold text-white border-2 bg-orange-500 border-orange-300">
                  NBA
                </span>
                <span className={`px-3 py-1 rounded-full text-xs font-bold text-white border-2 ${
                  isCombo ? 'bg-pink-500 border-pink-300 animate-pulse' : isHedge ? 'bg-slate-500 border-slate-300' : 'bg-purple-500 border-purple-300'
                }`}>
                  {isCombo ? 'DOUBLE REVERSAL' : isHedge ? 'ANTI-REVERSAL HEDGE' : 'QUARTER REVERSAL'}
                </span>
                {isCritical && !isCombo && (
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-yellow-500 text-black border-2 border-yellow-300 animate-pulse">
                    +35.2% ROI
                  </span>
                )}
                {isCombo && (
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-pink-500 text-white border-2 border-pink-300 animate-pulse">
                    ULTRA RARE
                  </span>
                )}
              </div>
              <div className="text-right">
                <div className="text-xs text-slate-300">
                  {new Date(opp.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>

            {/* Game Info */}
            <div className="bg-black/40 border-4 border-slate-700 rounded-lg p-4 mb-4">
              <h4 className="font-bold text-white text-2xl mb-3">
                {opp.matchup}
              </h4>

              {/* Trigger Info */}
              <div className="bg-slate-900/70 rounded-lg p-4 mb-3 border-2 border-slate-600">
                <div className="text-xs text-slate-400 mb-1">TRIGGER</div>
                <div className="text-white font-bold text-lg">{opp.trigger}</div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-slate-400">Hot Team:</span>
                  <span className="ml-2 font-bold text-red-400 text-lg">{opp.hot_team}</span>
                </div>
                <div>
                  <span className="text-slate-400">Reversal Team:</span>
                  <span className="ml-2 font-bold text-green-400 text-lg">{opp.reversal_team}</span>
                </div>
                <div>
                  <span className="text-slate-400">Quarter:</span>
                  <span className="ml-2 font-bold text-white text-lg">{opp.quarter}</span>
                </div>
                <div>
                  <span className="text-slate-400">Strategy:</span>
                  <span className="ml-2 font-bold text-white text-lg">{opp.strategy}</span>
                </div>
              </div>
            </div>

            {/* Reasoning */}
            <div className="bg-black/40 border-4 border-slate-700 rounded-lg p-4 mb-4">
              <h5 className="font-bold text-white mb-3 text-lg flex items-center gap-2">
                🧠 WHY THIS WORKS
              </h5>
              <div className="text-slate-200 text-sm leading-relaxed">
                {opp.reasoning}
              </div>
            </div>

            {/* Statistics */}
            <div className="bg-black/40 border-4 border-slate-700 rounded-lg p-4 mb-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-slate-900/70 rounded-lg p-3 border-2 border-green-600">
                  <div className="text-xs text-slate-300 mb-1">REVERSAL PROBABILITY</div>
                  <div className="font-bold text-green-400 text-2xl">{opp.reversal_prob}</div>
                </div>
                <div className="bg-slate-900/70 rounded-lg p-3 border-2 border-blue-600">
                  <div className="text-xs text-slate-300 mb-1">EXPECTED ROI</div>
                  <div className="font-bold text-blue-400 text-2xl">{opp.expected_roi}</div>
                </div>
              </div>
            </div>

            {/* Betting Recommendations */}
            <div className={`rounded-lg p-5 border-4 ${
              isCombo
                ? 'bg-gradient-to-br from-purple-700 via-pink-600 to-purple-700 border-pink-400'
                : isHedge
                ? 'bg-gradient-to-br from-slate-700 via-slate-600 to-slate-700 border-slate-400'
                : isCritical
                ? 'bg-gradient-to-br from-red-700 via-yellow-600 to-red-700 border-yellow-400'
                : isHigh
                ? 'bg-gradient-to-br from-green-700 via-green-600 to-green-700 border-green-400'
                : 'bg-gradient-to-br from-blue-700 via-blue-600 to-blue-700 border-blue-400'
            }`}>
              <h5 className="font-bold text-white mb-3 text-2xl flex items-center gap-2">
                💰 BETTING RECOMMENDATIONS
              </h5>

              {bankroll && (
                <div className="bg-black/30 rounded-lg p-3 mb-4 border-2 border-slate-600">
                  <div className="text-xs text-slate-300">
                    Bankroll: ${bankroll.toLocaleString()} | Risk Profile: {riskProfile.charAt(0).toUpperCase() + riskProfile.slice(1)}
                  </div>
                </div>
              )}

              <div className="space-y-3">
                {opp.recommendations.map((rec, ridx) => (
                  <div
                    key={ridx}
                    className={`rounded-lg p-4 border-3 ${
                      rec.rank === 1
                        ? 'bg-gradient-to-r from-yellow-700 via-yellow-600 to-yellow-700 border-yellow-400'
                        : 'bg-slate-900/80 border-slate-600'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        {rec.rank === 1 && (
                          <span className="text-2xl">⭐</span>
                        )}
                        <span className={`font-bold ${rec.rank === 1 ? 'text-black text-xl' : 'text-white text-lg'}`}>
                          #{rec.rank} - {rec.label}
                        </span>
                      </div>
                      <span className={`font-bold text-lg ${rec.rank === 1 ? 'text-black' : 'text-green-400'}`}>
                        {rec.odds}
                      </span>
                    </div>

                    {rec.context && (
                      <div className={`text-xs mb-3 ${rec.rank === 1 ? 'text-black/80' : 'text-slate-300'}`}>
                        {rec.context}
                      </div>
                    )}

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                      <div>
                        <div className={`text-xs ${rec.rank === 1 ? 'text-black/70' : 'text-slate-400'}`}>Win Probability</div>
                        <div className={`font-bold ${rec.rank === 1 ? 'text-black' : 'text-white'}`}>
                          {(rec.probability * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div>
                        <div className={`text-xs ${rec.rank === 1 ? 'text-black/70' : 'text-slate-400'}`}>Expected Value</div>
                        <div className={`font-bold ${rec.rank === 1 ? 'text-black' : rec.expected_value > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {rec.expected_value > 0 ? '+' : ''}{(rec.expected_value * 100).toFixed(1)}%
                        </div>
                      </div>
                      {rec.kelly_size && (
                        <>
                          <div>
                            <div className={`text-xs ${rec.rank === 1 ? 'text-black/70' : 'text-slate-400'}`}>Kelly Bet</div>
                            <div className={`font-bold ${rec.rank === 1 ? 'text-black' : 'text-yellow-400'}`}>
                              ${rec.kelly_size.toFixed(2)}
                            </div>
                          </div>
                          <div>
                            <div className={`text-xs ${rec.rank === 1 ? 'text-black/70' : 'text-slate-400'}`}>Bankroll %</div>
                            <div className={`font-bold ${rec.rank === 1 ? 'text-black' : 'text-yellow-400'}`}>
                              {(rec.kelly_pct! * 100).toFixed(2)}%
                            </div>
                          </div>
                        </>
                      )}
                    </div>

                    {rec.rank === 1 && (
                      <div className="mt-3 pt-3 border-t-2 border-black/30">
                        <div className="text-black font-bold text-center text-sm">
                          🎯 RECOMMENDED BET
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {isCritical && !isCombo && (
                <div className="mt-4 bg-yellow-500 border-3 border-yellow-300 rounded-lg p-4 animate-pulse">
                  <p className="text-black font-bold text-center text-lg">
                    🚨 CRITICAL ALERT! OT Reversal = 60.7% Win Rate, +35.2% ROI! STRIKE NOW!
                  </p>
                </div>
              )}
              {isCombo && (
                <div className="mt-4 bg-gradient-to-r from-purple-600 via-pink-500 to-purple-600 border-3 border-pink-300 rounded-lg p-4 animate-pulse">
                  <p className="text-white font-bold text-center text-lg mb-2">
                    💎 ULTRA RARE COMBO ALERT! 💎
                  </p>
                  <p className="text-white text-center text-sm">
                    Multiple reversal patterns detected in same game! Expected ROI: {opp.expected_roi}
                  </p>
                </div>
              )}
              {isHedge && (
                <div className="mt-4 bg-slate-700 border-3 border-slate-500 rounded-lg p-4">
                  <p className="text-white font-bold text-center text-lg mb-2">
                    🛡️ HEDGE OPPORTUNITY
                  </p>
                  <p className="text-slate-300 text-center text-sm">
                    Pattern shows weakness - consider anti-reversal bet to hedge
                  </p>
                </div>
              )}
            </div>
          </div>
        );
      })}

      {/* Cold Team Bounce-Back Opportunities */}
      {coldTeamOpportunities.map((opp, idx) => {
        const isHigh = opp.alert_level === 'HIGH';
        const topRec = opp.recommendations[0];

        const cardStyle = isHigh
          ? 'bg-gradient-to-br from-cyan-900 via-cyan-800 to-cyan-900 border-cyan-500 shadow-lg shadow-cyan-600/30'
          : 'bg-gradient-to-br from-blue-900 via-blue-800 to-blue-900 border-blue-500';

        return (
          <div
            key={`cold-${opp.game_id}-${idx}`}
            className={`rounded-lg p-6 border-4 ${cardStyle}`}
          >
            {/* Alert Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3 flex-wrap">
                <span
                  className={`px-4 py-2 rounded-lg font-bold text-white text-sm tracking-wide ${
                    isHigh
                      ? 'bg-cyan-600 border-2 border-cyan-400'
                      : 'bg-blue-600 border-2 border-blue-400'
                  }`}
                >
                  ❄️ {opp.alert_level} ALERT
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold text-white border-2 bg-orange-500 border-orange-300">
                  NBA
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold text-white border-2 bg-cyan-500 border-cyan-300">
                  COLD TEAM BOUNCE-BACK
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-cyan-500 text-white border-2 border-cyan-300">
                  +43.9% ROI
                </span>
              </div>
              <div className="text-right">
                <div className="text-xs text-slate-300">
                  {new Date(opp.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>

            {/* Game Info */}
            <div className="bg-black/40 border-4 border-slate-700 rounded-lg p-4 mb-4">
              <h4 className="font-bold text-white text-2xl mb-3">
                {opp.matchup}
              </h4>

              {/* Trigger Info */}
              <div className="bg-slate-900/70 rounded-lg p-4 mb-3 border-2 border-slate-600">
                <div className="text-xs text-slate-400 mb-1">TRIGGER</div>
                <div className="text-white font-bold text-lg">{opp.trigger}</div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-slate-400">Hot Team:</span>
                  <span className="ml-2 font-bold text-red-400 text-lg">{opp.hot_team}</span>
                </div>
                <div>
                  <span className="text-slate-400">Cold Team (Bet):</span>
                  <span className="ml-2 font-bold text-cyan-400 text-lg">{opp.cold_team}</span>
                </div>
                <div>
                  <span className="text-slate-400">Quarter:</span>
                  <span className="ml-2 font-bold text-white text-lg">{opp.quarter}</span>
                </div>
                <div>
                  <span className="text-slate-400">Strategy:</span>
                  <span className="ml-2 font-bold text-white text-lg">{opp.strategy}</span>
                </div>
              </div>
            </div>

            {/* Reasoning */}
            <div className="bg-black/40 border-4 border-slate-700 rounded-lg p-4 mb-4">
              <h5 className="font-bold text-white mb-3 text-lg flex items-center gap-2">
                🧠 WHY THIS WORKS
              </h5>
              <div className="text-slate-200 text-sm leading-relaxed">
                {opp.reasoning}
              </div>
            </div>

            {/* Statistics */}
            <div className="bg-black/40 border-4 border-slate-700 rounded-lg p-4 mb-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-slate-900/70 rounded-lg p-3 border-2 border-cyan-600">
                  <div className="text-xs text-slate-300 mb-1">WIN RATE</div>
                  <div className="font-bold text-cyan-400 text-2xl">{(opp.confidence * 100).toFixed(1)}%</div>
                </div>
                <div className="bg-slate-900/70 rounded-lg p-3 border-2 border-blue-600">
                  <div className="text-xs text-slate-300 mb-1">EXPECTED ROI</div>
                  <div className="font-bold text-blue-400 text-2xl">{opp.expected_roi}</div>
                </div>
              </div>
            </div>

            {/* Betting Recommendations */}
            <div className={`rounded-lg p-5 border-4 ${
              isHigh
                ? 'bg-gradient-to-br from-cyan-700 via-cyan-600 to-cyan-700 border-cyan-400'
                : 'bg-gradient-to-br from-blue-700 via-blue-600 to-blue-700 border-blue-400'
            }`}>
              <h5 className="font-bold text-white mb-3 text-2xl flex items-center gap-2">
                💰 BETTING RECOMMENDATIONS
              </h5>

              {bankroll && (
                <div className="bg-black/30 rounded-lg p-3 mb-4 border-2 border-slate-600">
                  <div className="text-xs text-slate-300">
                    Bankroll: ${bankroll.toLocaleString()} | Risk Profile: {riskProfile.charAt(0).toUpperCase() + riskProfile.slice(1)}
                  </div>
                </div>
              )}

              <div className="space-y-3">
                {opp.recommendations.map((rec, ridx) => (
                  <div
                    key={ridx}
                    className={`rounded-lg p-4 border-3 ${
                      rec.rank === 1
                        ? 'bg-gradient-to-r from-yellow-700 via-yellow-600 to-yellow-700 border-yellow-400'
                        : 'bg-slate-900/80 border-slate-600'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        {rec.rank === 1 && (
                          <span className="text-2xl">⭐</span>
                        )}
                        <span className={`font-bold ${rec.rank === 1 ? 'text-black text-xl' : 'text-white text-lg'}`}>
                          #{rec.rank} - {rec.label}
                        </span>
                      </div>
                      <span className={`font-bold text-lg ${rec.rank === 1 ? 'text-black' : 'text-green-400'}`}>
                        {rec.odds}
                      </span>
                    </div>

                    {rec.context && (
                      <div className={`text-xs mb-3 ${rec.rank === 1 ? 'text-black/80' : 'text-slate-300'}`}>
                        {rec.context}
                      </div>
                    )}

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                      <div>
                        <div className={`text-xs ${rec.rank === 1 ? 'text-black/70' : 'text-slate-400'}`}>Win Probability</div>
                        <div className={`font-bold ${rec.rank === 1 ? 'text-black' : 'text-white'}`}>
                          {(rec.probability * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div>
                        <div className={`text-xs ${rec.rank === 1 ? 'text-black/70' : 'text-slate-400'}`}>Expected Value</div>
                        <div className={`font-bold ${rec.rank === 1 ? 'text-black' : rec.expected_value > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {rec.expected_value > 0 ? '+' : ''}{(rec.expected_value * 100).toFixed(1)}%
                        </div>
                      </div>
                      {rec.kelly_size && (
                        <>
                          <div>
                            <div className={`text-xs ${rec.rank === 1 ? 'text-black/70' : 'text-slate-400'}`}>Kelly Bet</div>
                            <div className={`font-bold ${rec.rank === 1 ? 'text-black' : 'text-yellow-400'}`}>
                              ${rec.kelly_size.toFixed(2)}
                            </div>
                          </div>
                          <div>
                            <div className={`text-xs ${rec.rank === 1 ? 'text-black/70' : 'text-slate-400'}`}>Bankroll %</div>
                            <div className={`font-bold ${rec.rank === 1 ? 'text-black' : 'text-yellow-400'}`}>
                              {(rec.kelly_pct! * 100).toFixed(2)}%
                            </div>
                          </div>
                        </>
                      )}
                    </div>

                    {rec.rank === 1 && (
                      <div className="mt-3 pt-3 border-t-2 border-black/30">
                        <div className="text-black font-bold text-center text-sm">
                          🎯 RECOMMENDED BET
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="mt-4 bg-gradient-to-r from-cyan-600 via-cyan-500 to-cyan-600 border-3 border-cyan-300 rounded-lg p-4">
                <p className="text-white font-bold text-center text-lg mb-2">
                  ❄️ DESPERATION PLAY
                </p>
                <p className="text-white text-center text-sm">
                  Team lost Q1, Q2, Q3 - professional pride kicks in Q4! Historical: 63.97% WR, +43.9% ROI
                </p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
