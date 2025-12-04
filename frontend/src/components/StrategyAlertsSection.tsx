import React from 'react';
import { LiveGame } from '../types';

interface StrategyAlertsSectionProps {
  game: LiveGame;
}

// Strategy definitions with historical performance
const STRATEGY_CONFIG = {
  b2b_vs_rested: {
    name: 'B2B vs Rested',
    badge: 'B2B',
    color: 'from-red-600 to-orange-600',
    borderColor: 'border-red-500',
    ats: {
      nba: 61,
      nhl: 59,
      ncaab: 58
    },
    minOdds: -115,
    betTypes: ['Spread', 'ML']
  },
  favorite_comeback: {
    name: 'Favorite Comeback',
    badge: 'COMEBACK',
    color: 'from-blue-600 to-cyan-600',
    borderColor: 'border-blue-500',
    ats: { nba: 60, nhl: 58, ncaab: 58 },
    minOdds: -110,
    betTypes: ['2H Spread', 'Live ML']
  },
  quarter_reversal: {
    name: 'Quarter Reversal',
    badge: 'Q-REV',
    color: 'from-purple-600 to-pink-600',
    borderColor: 'border-purple-500',
    ats: { nba: 55, nhl: 54, ncaab: 54 },
    minOdds: -110,
    betTypes: ['Next Q Spread']
  }
};

export const StrategyAlertsSection: React.FC<StrategyAlertsSectionProps> = ({ game }) => {
  const alerts: Array<{
    type: string;
    config: typeof STRATEGY_CONFIG.b2b_vs_rested;
    betSide: string;
    details: string;
    edge?: number;
  }> = [];

  // Get sport for ATS lookup
  const sportKey = game.state?.sport_key || '';
  const sport = sportKey.includes('nba') ? 'nba' : sportKey.includes('nhl') ? 'nhl' : 'ncaab';

  // Check for B2B vs Rested situation
  if (game.fatigue_edge && game.rest_differential && game.rest_differential >= 2) {
    const fatigued = game.fatigue_edge === 'HOME' ? game.state.away_team.name : game.state.home_team.name;
    const rested = game.fatigue_edge === 'HOME' ? game.state.home_team.name : game.state.away_team.name;
    const fatigueRest = game.fatigue_edge === 'HOME' ? game.away_rest_days : game.home_rest_days;
    const restedRest = game.fatigue_edge === 'HOME' ? game.home_rest_days : game.away_rest_days;

    alerts.push({
      type: 'b2b_vs_rested',
      config: STRATEGY_CONFIG.b2b_vs_rested,
      betSide: `${rested} (${game.fatigue_edge})`,
      details: `${fatigued} ${fatigueRest}d rest vs ${rested} ${restedRest}d rest`,
      edge: game.fatigue_edge_points || undefined
    });
  }

  // Check for strategy_alerts from backend (Favorite Comeback, Quarter Reversal, etc.)
  if (game.strategy_alerts && game.strategy_alerts.length > 0) {
    game.strategy_alerts.forEach(alert => {
      if (alert.strategy_id === 'favorite_comeback' && STRATEGY_CONFIG.favorite_comeback) {
        alerts.push({
          type: 'favorite_comeback',
          config: STRATEGY_CONFIG.favorite_comeback,
          betSide: alert.recommendation || 'Favorite',
          details: alert.reasoning || '2H regression opportunity',
          edge: alert.edge_percentage
        });
      }
      if (alert.strategy_id === 'quarter_reversal' && STRATEGY_CONFIG.quarter_reversal) {
        alerts.push({
          type: 'quarter_reversal',
          config: STRATEGY_CONFIG.quarter_reversal,
          betSide: alert.recommendation || 'Trailing Team',
          details: alert.reasoning || 'Quarter reversal detected',
          edge: alert.edge_percentage
        });
      }
    });
  }

  // Don't render if no alerts
  if (alerts.length === 0) {
    return null;
  }

  return (
    <div className="px-4 pb-4">
      <div className="bg-slate-900/80 border border-slate-700 rounded-lg overflow-hidden">
        {/* Header */}
        <div className="px-3 py-2 bg-gradient-to-r from-slate-800 to-slate-700 border-b border-slate-600 flex items-center gap-2">
          <svg className="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
          </svg>
          <span className="text-sm font-bold text-white">Strategy Alerts</span>
          <span className="px-1.5 py-0.5 bg-green-600 text-white text-xs font-bold rounded">
            {alerts.length}
          </span>
        </div>

        {/* Alerts */}
        <div className="divide-y divide-slate-700/50">
          {alerts.map((alert, idx) => (
            <div key={idx} className="p-3">
              <div className="flex items-start justify-between gap-3">
                {/* Left: Badge + Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {/* Strategy Badge */}
                    <span className={`px-2 py-0.5 text-xs font-bold text-white rounded bg-gradient-to-r ${alert.config.color}`}>
                      {alert.config.badge}
                    </span>
                    {/* ATS % */}
                    <span className="text-green-400 text-xs font-bold">
                      {alert.config.ats[sport as keyof typeof alert.config.ats]}% ATS
                    </span>
                  </div>

                  {/* Bet Recommendation */}
                  <div className="text-white text-sm font-semibold">
                    {alert.betSide}
                  </div>

                  {/* Details */}
                  <div className="text-slate-400 text-xs mt-0.5 truncate">
                    {alert.details}
                  </div>
                </div>

                {/* Right: Edge + Min Odds */}
                <div className="flex flex-col items-end text-right flex-shrink-0">
                  {alert.edge && (
                    <div className="text-green-400 text-sm font-bold">
                      +{alert.edge.toFixed(1)} {sport === 'nhl' ? 'goals' : 'pts'}
                    </div>
                  )}
                  <div className="text-slate-500 text-xs">
                    Min: {alert.config.minOdds}
                  </div>
                  <div className="text-slate-500 text-xs">
                    {alert.config.betTypes.join(', ')}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
