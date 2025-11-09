import { StrategyAlert } from '../types';
import { openSportsbook } from '../utils/deepLinking';

interface StrategyAlertDetailProps {
  alert: StrategyAlert;
  onClose: () => void;
}

export function StrategyAlertDetail({ alert, onClose }: StrategyAlertDetailProps) {
  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'CRITICAL': return 'text-red-400';
      case 'HIGH': return 'text-orange-400';
      case 'MEDIUM': return 'text-yellow-400';
      default: return 'text-blue-400';
    }
  };

  const getConfidenceIcon = (confidence: string) => {
    switch (confidence) {
      case 'CRITICAL': return '🚨';
      case 'HIGH': return '🔥';
      case 'MEDIUM': return '⚡';
      default: return '💡';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border-4 border-slate-700 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-slate-800 to-slate-900 border-b-2 border-slate-700 p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-3xl">{getConfidenceIcon(alert.confidence)}</span>
                <h2 className="text-2xl font-bold text-white">{alert.strategy_name}</h2>
              </div>
              <div className={`text-sm font-semibold ${getConfidenceColor(alert.confidence)}`}>
                {alert.confidence} CONFIDENCE ALERT
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white text-2xl font-bold transition ml-4"
            >
              ×
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Trigger & Recommendation */}
          <div className="space-y-3">
            <div>
              <div className="text-sm font-semibold text-slate-400 mb-1">TRIGGER</div>
              <div className="text-white text-lg">{alert.trigger}</div>
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-400 mb-1">RECOMMENDATION</div>
              <div className="text-white text-lg font-semibold">{alert.recommendation}</div>
            </div>
          </div>

          {/* Key Stats */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-green-900 to-green-950 border-2 border-green-700 rounded-lg p-3 text-center">
              <div className="text-xs text-green-300 font-semibold mb-1">EDGE</div>
              <div className="text-2xl font-bold text-green-200">+{alert.edge_percentage.toFixed(1)}%</div>
            </div>
            <div className="bg-gradient-to-br from-blue-900 to-blue-950 border-2 border-blue-700 rounded-lg p-3 text-center">
              <div className="text-xs text-blue-300 font-semibold mb-1">ROI</div>
              <div className="text-2xl font-bold text-blue-200">+{alert.expected_roi.toFixed(1)}%</div>
            </div>
            <div className="bg-gradient-to-br from-purple-900 to-purple-950 border-2 border-purple-700 rounded-lg p-3 text-center">
              <div className="text-xs text-purple-300 font-semibold mb-1">WIN RATE</div>
              <div className="text-2xl font-bold text-purple-200">{(alert.win_probability * 100).toFixed(1)}%</div>
            </div>
            <div className="bg-gradient-to-br from-orange-900 to-orange-950 border-2 border-orange-700 rounded-lg p-3 text-center">
              <div className="text-xs text-orange-300 font-semibold mb-1">UNITS</div>
              <div className="text-2xl font-bold text-orange-200">{alert.stake_recommendation.toFixed(1)}u</div>
            </div>
          </div>

          {/* Bet Options */}
          {alert.bet_options && alert.bet_options.length > 0 && (
            <div>
              <div className="text-sm font-semibold text-slate-400 mb-3">BET OPTIONS</div>
              <div className="space-y-3">
                {alert.bet_options.map((option, idx) => (
                  <div key={idx} className="bg-gradient-to-br from-slate-800 to-slate-900 border-2 border-slate-700 rounded-lg p-4">
                    {/* Option Header */}
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <div className="text-white font-bold text-lg">{option.label}</div>
                        <div className="text-slate-400 text-sm">{option.market_type.toUpperCase()} • {option.bet_side}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-white font-bold text-xl">{option.odds > 0 ? `+${option.odds}` : option.odds}</div>
                        <div className="text-green-400 text-sm font-semibold">EV: +{(option.expected_value * 100).toFixed(1)}%</div>
                      </div>
                    </div>

                    {/* Option Stats */}
                    <div className="flex items-center justify-between text-sm mb-3 pb-3 border-b border-slate-700">
                      <div>
                        <span className="text-slate-400">Win Prob:</span>
                        <span className="text-white font-semibold ml-1">{(option.probability * 100).toFixed(1)}%</span>
                      </div>
                      {option.kelly_size && (
                        <div>
                          <span className="text-slate-400">Kelly:</span>
                          <span className="text-white font-semibold ml-1">{option.kelly_size.toFixed(1)}u</span>
                        </div>
                      )}
                    </div>

                    {/* Primary Bookmaker Button */}
                    <button
                      onClick={() => openSportsbook(option.bookmaker, option.bookmaker_title || option.bookmaker)}
                      className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white font-bold py-3 px-4 rounded-lg transition-all transform hover:scale-105 mb-2"
                    >
                      Place Bet at {option.bookmaker_title || option.bookmaker.toUpperCase()} →
                    </button>

                    {/* Alternative Bookmakers */}
                    {option.alt_bookmakers && option.alt_bookmakers.length > 0 && (
                      <div>
                        <div className="text-xs text-slate-400 mb-2">Also available at:</div>
                        <div className="flex flex-wrap gap-2">
                          {option.alt_bookmakers.map((alt, altIdx) => (
                            <button
                              key={altIdx}
                              onClick={() => openSportsbook(alt.bookmaker, alt.bookmaker_title || alt.bookmaker)}
                              className="bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold py-1.5 px-3 rounded transition"
                            >
                              {alt.bookmaker_title || alt.bookmaker.toUpperCase()} ({alt.odds > 0 ? `+${alt.odds}` : alt.odds})
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Reasoning */}
          {alert.reasoning && (
            <div>
              <div className="text-sm font-semibold text-slate-400 mb-2">WHY THIS WORKS</div>
              <div className="bg-gradient-to-br from-slate-800 to-slate-900 border-2 border-slate-700 rounded-lg p-4">
                <div className="text-slate-300 text-sm leading-relaxed whitespace-pre-line">
                  {alert.reasoning}
                </div>
              </div>
            </div>
          )}

          {/* Urgency Notice */}
          {alert.expires_in && alert.expires_in < 600 && (
            <div className="bg-gradient-to-r from-red-900 to-red-950 border-2 border-red-700 rounded-lg p-4">
              <div className="flex items-center gap-2 text-red-200">
                <span className="text-2xl animate-pulse">⚠️</span>
                <div>
                  <div className="font-bold">ACT FAST!</div>
                  <div className="text-sm">
                    This opportunity expires in {Math.floor(alert.expires_in / 60)}:{(alert.expires_in % 60).toString().padStart(2, '0')} minutes
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
