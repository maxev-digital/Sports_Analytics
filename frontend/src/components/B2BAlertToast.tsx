import { useState } from 'react';

interface B2BAlertData {
  id: string;
  sport: string;
  homeTeam: string;
  awayTeam: string;
  homeRestDays: number;
  awayRestDays: number;
  restDifferential: number;
  fatigueEdge: 'HOME' | 'AWAY';
  edgePoints: number;
  timestamp: number;
}

interface B2BAlertToastProps {
  alert: B2BAlertData;
  onDismiss: () => void;
  position: number;
}

// Historical ATS by sport
const ATS_BY_SPORT: Record<string, number> = {
  'basketball_nba': 61,
  'icehockey_nhl': 59,
  'basketball_ncaab': 58,
};

export function B2BAlertToast({ alert, onDismiss, position }: B2BAlertToastProps) {
  const [isExiting, setIsExiting] = useState(false);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(onDismiss, 300);
  };

  // Get sport display name
  const getSportDisplay = (sportKey: string) => {
    if (sportKey.includes('nba')) return 'NBA';
    if (sportKey.includes('nhl')) return 'NHL';
    if (sportKey.includes('ncaab')) return 'NCAAB';
    return sportKey.toUpperCase();
  };

  // Get the rested team (team with edge)
  const restedTeam = alert.fatigueEdge === 'HOME' ? alert.homeTeam : alert.awayTeam;
  const fatiguedTeam = alert.fatigueEdge === 'HOME' ? alert.awayTeam : alert.homeTeam;
  const restedDays = alert.fatigueEdge === 'HOME' ? alert.homeRestDays : alert.awayRestDays;
  const fatiguedDays = alert.fatigueEdge === 'HOME' ? alert.awayRestDays : alert.homeRestDays;

  // Get ATS percentage
  const atsPercent = ATS_BY_SPORT[alert.sport] || 58;

  // Unit indicator (pts for basketball, goals for hockey)
  const unitLabel = alert.sport.includes('hockey') ? 'goals' : 'pts';

  // Bottom position for stacking
  const bottomPosition = position * 140 + 16;

  return (
    <div
      className={`
        fixed right-4 z-50 w-96
        bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900
        border-4 border-red-500 rounded-xl overflow-hidden
        shadow-2xl shadow-red-500/30
        transition-all duration-300 ease-out
        ${isExiting ? 'opacity-0 translate-x-full' : 'opacity-100 translate-x-0'}
      `}
      style={{ bottom: `${bottomPosition}px` }}
    >
      {/* Header */}
      <div className="flex items-center justify-between bg-gradient-to-r from-red-600 to-orange-600 px-4 py-2">
        <div className="flex items-center gap-2">
          <span className="text-xl">🏃</span>
          <div>
            <div className="font-bold text-white text-sm">B2B vs Rested Alert</div>
            <div className="text-xs text-white/80">{getSportDisplay(alert.sport)}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2 py-1 bg-green-500 text-white text-xs font-bold rounded">
            {atsPercent}% ATS
          </span>
        </div>
      </div>

      {/* Body */}
      <div className="p-4 space-y-3">
        {/* Matchup */}
        <div className="text-center">
          <div className="text-white/60 text-xs mb-1">MATCHUP</div>
          <div className="text-white font-bold text-lg">
            {alert.awayTeam} @ {alert.homeTeam}
          </div>
        </div>

        {/* Rest Comparison */}
        <div className="grid grid-cols-2 gap-3">
          {/* Fatigued Team */}
          <div className="bg-red-900/40 border border-red-500/50 rounded-lg p-3 text-center">
            <div className="text-red-400 text-xs font-semibold mb-1">FATIGUED</div>
            <div className="text-white font-bold text-sm truncate">{fatiguedTeam}</div>
            <div className="text-red-400 font-bold text-lg mt-1">
              {fatiguedDays === 0 ? 'B2B' : `${fatiguedDays}d rest`}
            </div>
          </div>

          {/* Rested Team */}
          <div className="bg-green-900/40 border border-green-500/50 rounded-lg p-3 text-center">
            <div className="text-green-400 text-xs font-semibold mb-1">RESTED</div>
            <div className="text-white font-bold text-sm truncate">{restedTeam}</div>
            <div className="text-green-400 font-bold text-lg mt-1">
              {restedDays}d rest
            </div>
          </div>
        </div>

        {/* Recommendation */}
        <div className="bg-slate-700/50 border border-slate-600 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-slate-400 text-xs mb-1">RECOMMENDATION</div>
              <div className="text-white font-bold">
                Bet {restedTeam} ({alert.fatigueEdge})
              </div>
            </div>
            <div className="text-right">
              <div className="text-green-400 font-bold text-lg">
                +{alert.edgePoints.toFixed(1)} {unitLabel}
              </div>
              <div className="text-slate-400 text-xs">estimated edge</div>
            </div>
          </div>
        </div>

        {/* Bet Types */}
        <div className="flex items-center justify-center gap-2 text-xs">
          <span className="text-slate-400">Best for:</span>
          <span className="px-2 py-1 bg-blue-600/50 text-blue-200 rounded">Spread</span>
          <span className="px-2 py-1 bg-purple-600/50 text-purple-200 rounded">Moneyline</span>
        </div>

        {/* Min Odds Warning */}
        <div className="text-center text-xs text-slate-500">
          Minimum odds: -115 | Low time decay - bet anytime before tip-off
        </div>
      </div>

      {/* Close Button */}
      <button
        onClick={handleDismiss}
        className="absolute top-2 right-2 text-white/60 hover:text-white transition-colors text-xl font-bold w-8 h-8 flex items-center justify-center hover:bg-white/10 rounded"
      >
        ×
      </button>
    </div>
  );
}

// Export the alert data type for use elsewhere
export type { B2BAlertData };
