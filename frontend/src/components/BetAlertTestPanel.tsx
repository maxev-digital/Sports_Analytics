import { useBetAlertNotification } from '../contexts/BetAlertNotificationContext';
import { StrategyAlert } from '../types';

/**
 * Test panel for manually triggering bet alert notifications
 * Add this component to any page to test the notification system
 */
export function BetAlertTestPanel() {
  const { showBetAlert } = useBetAlertNotification();

  const triggerTestAlert = (type: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW') => {
    const testAlert: StrategyAlert = {
      strategy_id: `test-${Date.now()}`,
      strategy_name: type === 'CRITICAL' ? 'NBA Quarter Reversal' :
                     type === 'HIGH' ? 'Favorite Comeback' :
                     type === 'MEDIUM' ? 'Halftime Tracker' : 'Momentum Detector',
      confidence: type,
      trigger: type === 'CRITICAL' ? 'Q2 hot start reversal detected - Underdogs shooting 18% above average' :
               type === 'HIGH' ? 'Favorite trailing after Q1 - Strong regression opportunity' :
               type === 'MEDIUM' ? 'Halftime pace analysis shows significant value' :
               'Recent pace shift detected in last 5 minutes',
      recommendation: `Bet UNDER 2H ${(110.5 + Math.random() * 10).toFixed(1)}`,
      edge_percentage: type === 'CRITICAL' ? 12.5 :
                       type === 'HIGH' ? 9.2 :
                       type === 'MEDIUM' ? 6.8 : 4.2,
      expected_roi: type === 'CRITICAL' ? 15.2 :
                    type === 'HIGH' ? 11.5 :
                    type === 'MEDIUM' ? 8.1 : 5.3,
      win_probability: type === 'CRITICAL' ? 0.603 :
                       type === 'HIGH' ? 0.58 :
                       type === 'MEDIUM' ? 0.56 : 0.53,
      stake_recommendation: type === 'CRITICAL' ? 2.5 :
                            type === 'HIGH' ? 1.8 :
                            type === 'MEDIUM' ? 1.2 : 0.8,
      bet_options: [
        {
          label: 'Under 110.5',
          market_type: 'totals',
          bet_side: 'UNDER',
          line: 110.5,
          odds: -110,
          bookmaker: 'draftkings',
          bookmaker_title: 'DraftKings',
          probability: 0.58,
          expected_value: 0.09,
          kelly_size: 1.5
        },
        {
          label: 'Under 111.0',
          market_type: 'totals',
          bet_side: 'UNDER',
          line: 111.0,
          odds: -108,
          bookmaker: 'fanduel',
          bookmaker_title: 'FanDuel',
          probability: 0.58,
          expected_value: 0.09,
          kelly_size: 1.6
        },
        {
          label: 'Under 110.0',
          market_type: 'totals',
          bet_side: 'UNDER',
          line: 110.0,
          odds: -112,
          bookmaker: 'betmgm',
          bookmaker_title: 'BetMGM',
          probability: 0.58,
          expected_value: 0.09,
          kelly_size: 1.4
        }
      ],
      reasoning: 'Historical data shows 60.3% ATS performance when favorites trail underdogs at halftime after Q1 hot starts.',
      urgency: type,
      expires_in: type === 'CRITICAL' ? 180 : 300, // 3 or 5 minutes
      sound_alert: true,
      timestamp: new Date().toISOString()
    };

    showBetAlert(testAlert);
  };

  return (
    <div className="bg-slate-800 border-2 border-slate-700 rounded-lg p-6 mb-6">
      <h3 className="text-white font-bold text-lg mb-4">Test Bet Alert Notifications</h3>
      <p className="text-slate-300 text-sm mb-4">
        Click the buttons below to trigger test notifications at different urgency levels.
        Notifications will appear in the bottom right corner and automatically stack.
      </p>

      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => triggerTestAlert('CRITICAL')}
          className="bg-gradient-to-r from-red-600 to-red-800 hover:from-red-700 hover:to-red-900 text-white font-bold py-3 px-4 rounded-lg transition shadow-lg shadow-red-500/30"
        >
          🚨 CRITICAL Alert
        </button>

        <button
          onClick={() => triggerTestAlert('HIGH')}
          className="bg-gradient-to-r from-orange-600 to-orange-800 hover:from-orange-700 hover:to-orange-900 text-white font-bold py-3 px-4 rounded-lg transition shadow-lg shadow-orange-500/30"
        >
          🔥 HIGH Alert
        </button>

        <button
          onClick={() => triggerTestAlert('MEDIUM')}
          className="bg-gradient-to-r from-yellow-600 to-yellow-800 hover:from-yellow-700 hover:to-yellow-900 text-white font-bold py-3 px-4 rounded-lg transition shadow-lg shadow-yellow-500/30"
        >
          ⚡ MEDIUM Alert
        </button>

        <button
          onClick={() => triggerTestAlert('LOW')}
          className="bg-gradient-to-r from-blue-600 to-blue-800 hover:from-blue-700 hover:to-blue-900 text-white font-bold py-3 px-4 rounded-lg transition shadow-lg shadow-blue-500/30"
        >
          💡 LOW Alert
        </button>
      </div>

      <div className="mt-4 p-3 bg-slate-900 border border-slate-700 rounded-lg">
        <div className="text-xs text-slate-400">
          <strong className="text-slate-300">Features:</strong>
          <ul className="mt-2 space-y-1 ml-4 list-disc">
            <li>Notifications stack from bottom right</li>
            <li>Live countdown timer shows age/decay</li>
            <li>Displays game details, books, and odds</li>
            <li>Auto-dismisses based on urgency (20-60 seconds)</li>
            <li>Sound alerts for each confidence level</li>
            <li>Max 5 active notifications at once</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
