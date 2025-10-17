import { useState } from 'react';

export function HedgeCalculator() {
  const [originalStake, setOriginalStake] = useState<string>('100');
  const [originalOdds, setOriginalOdds] = useState<string>('');
  const [hedgeOdds, setHedgeOdds] = useState<string>('');
  const [hedgeGoal, setHedgeGoal] = useState<'guarantee' | 'maximize'>('guarantee');
  const [result, setResult] = useState<{
    hedgeStake: number;
    originalWinProfit: number;
    hedgeWinProfit: number;
    guaranteedProfit: number;
    originalPayout: number;
    hedgePayout: number;
  } | null>(null);

  // Convert American odds to decimal
  const americanToDecimal = (odds: number): number => {
    if (odds > 0) {
      return (odds / 100) + 1;
    } else {
      return (100 / Math.abs(odds)) + 1;
    }
  };

  const calculateHedge = () => {
    const originalStakeNum = parseFloat(originalStake);
    const originalOddsNum = parseFloat(originalOdds);
    const hedgeOddsNum = parseFloat(hedgeOdds);

    if (isNaN(originalStakeNum) || isNaN(originalOddsNum) || isNaN(hedgeOddsNum)) {
      alert('Please enter all values');
      return;
    }

    // Convert to decimal odds
    const originalDecimal = americanToDecimal(originalOddsNum);
    const hedgeDecimal = americanToDecimal(hedgeOddsNum);

    // Calculate original potential payout
    const originalPayout = originalStakeNum * originalDecimal;
    const originalProfit = originalPayout - originalStakeNum;

    let hedgeStake: number;
    let guaranteedProfit: number;

    if (hedgeGoal === 'guarantee') {
      // Goal: Equal profit on both outcomes
      // Formula: Hedge Stake = (Original Payout) / (Hedge Decimal Odds)
      hedgeStake = originalPayout / hedgeDecimal;

      // If original bet wins: Original Profit - Hedge Stake
      const originalWinProfit = originalProfit - hedgeStake;

      // If hedge bet wins: Hedge Profit - Original Stake
      const hedgePayout = hedgeStake * hedgeDecimal;
      const hedgeProfit = hedgePayout - hedgeStake;
      const hedgeWinProfit = hedgeProfit - originalStakeNum;

      // These should be equal (or very close)
      guaranteedProfit = Math.min(originalWinProfit, hedgeWinProfit);
    } else {
      // Goal: Maximize profit if original wins, break even if hedge wins
      // Formula: Hedge Stake = Original Stake
      hedgeStake = originalStakeNum;

      const originalWinProfit = originalProfit - hedgeStake;
      const hedgePayout = hedgeStake * hedgeDecimal;
      const hedgeProfit = hedgePayout - hedgeStake;
      const hedgeWinProfit = hedgeProfit - originalStakeNum;

      guaranteedProfit = Math.min(originalWinProfit, hedgeWinProfit);
    }

    // Calculate outcomes
    const originalWinProfit = originalProfit - hedgeStake;
    const hedgePayout = hedgeStake * hedgeDecimal;
    const hedgeWinProfit = (hedgePayout - hedgeStake) - originalStakeNum;

    setResult({
      hedgeStake: hedgeStake,
      originalWinProfit: originalWinProfit,
      hedgeWinProfit: hedgeWinProfit,
      guaranteedProfit: guaranteedProfit,
      originalPayout: originalPayout,
      hedgePayout: hedgePayout,
    });
  };

  const reset = () => {
    setOriginalStake('100');
    setOriginalOdds('');
    setHedgeOdds('');
    setHedgeGoal('guarantee');
    setResult(null);
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">Hedge Calculator</h2>
      <p className="text-slate-400 text-sm mb-6">
        Calculate how much to bet on the opposite side to guarantee profit or minimize risk
      </p>

      <div className="space-y-4">
        {/* Input Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Original Stake ($)
            </label>
            <input
              type="number"
              value={originalStake}
              onChange={(e) => setOriginalStake(e.target.value)}
              placeholder="100"
              min="0"
              step="0.01"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Original Odds (American)
            </label>
            <input
              type="number"
              value={originalOdds}
              onChange={(e) => setOriginalOdds(e.target.value)}
              placeholder="e.g., +200"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Hedge Odds (American)
            </label>
            <input
              type="number"
              value={hedgeOdds}
              onChange={(e) => setHedgeOdds(e.target.value)}
              placeholder="e.g., -150"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Hedge Strategy */}
        <div className="bg-slate-700 rounded-lg p-4">
          <label className="block text-sm font-medium text-slate-300 mb-3">
            Hedge Strategy
          </label>
          <div className="flex gap-4">
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                value="guarantee"
                checked={hedgeGoal === 'guarantee'}
                onChange={(e) => setHedgeGoal(e.target.value as 'guarantee')}
                className="mr-2"
              />
              <span className="text-white">Guarantee Equal Profit</span>
            </label>
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                value="maximize"
                checked={hedgeGoal === 'maximize'}
                onChange={(e) => setHedgeGoal(e.target.value as 'maximize')}
                className="mr-2"
              />
              <span className="text-white">Maximize Original Win</span>
            </label>
          </div>
          <p className="text-xs text-slate-400 mt-2">
            {hedgeGoal === 'guarantee'
              ? 'Locks in the same profit regardless of outcome'
              : 'Maximizes profit if original wins, minimizes loss if hedge wins'}
          </p>
        </div>

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={calculateHedge}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded font-medium transition-colors"
          >
            Calculate Hedge
          </button>
          <button
            onClick={reset}
            className="bg-slate-700 hover:bg-slate-600 text-white px-6 py-2 rounded font-medium transition-colors"
          >
            Reset
          </button>
        </div>

        {/* Results Section */}
        {result && (
          <div className="mt-6 space-y-4">
            {/* Hedge Stake */}
            <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-2">Recommended Hedge Bet</h3>
              <div className="text-3xl font-bold text-blue-400">
                ${result.hedgeStake.toFixed(2)}
              </div>
              <p className="text-sm text-slate-400 mt-1">
                Bet this amount at {hedgeOdds} to hedge your position
              </p>
            </div>

            {/* Outcomes Comparison */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Original Bet Wins */}
              <div className="bg-slate-700 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-slate-300 mb-3">
                  If Original Bet Wins
                </h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Original Payout:</span>
                    <span className="text-green-400 font-medium">
                      ${result.originalPayout.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Hedge Loss:</span>
                    <span className="text-red-400 font-medium">
                      -${result.hedgeStake.toFixed(2)}
                    </span>
                  </div>
                  <div className="border-t border-slate-600 pt-2 mt-2">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Net Profit:</span>
                      <span className={`font-bold text-lg ${result.originalWinProfit > 0 ? 'text-green-400' : 'text-red-400'}`}>
                        ${result.originalWinProfit.toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Hedge Bet Wins */}
              <div className="bg-slate-700 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-slate-300 mb-3">
                  If Hedge Bet Wins
                </h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Hedge Payout:</span>
                    <span className="text-green-400 font-medium">
                      ${result.hedgePayout.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Original Loss:</span>
                    <span className="text-red-400 font-medium">
                      -${originalStake}
                    </span>
                  </div>
                  <div className="border-t border-slate-600 pt-2 mt-2">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Net Profit:</span>
                      <span className={`font-bold text-lg ${result.hedgeWinProfit > 0 ? 'text-green-400' : 'text-red-400'}`}>
                        ${result.hedgeWinProfit.toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Summary */}
            <div className={`rounded-lg p-4 ${result.guaranteedProfit > 0 ? 'bg-green-900/30 border border-green-700/50' : 'bg-yellow-900/30 border border-yellow-700/50'}`}>
              <h4 className={`text-sm font-semibold mb-2 ${result.guaranteedProfit > 0 ? 'text-green-400' : 'text-yellow-400'}`}>
                {hedgeGoal === 'guarantee' ? 'Guaranteed Profit' : 'Hedge Summary'}
              </h4>
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-slate-300">
                    {hedgeGoal === 'guarantee'
                      ? `You'll profit $${Math.abs(result.guaranteedProfit).toFixed(2)} regardless of outcome`
                      : `Original win: $${result.originalWinProfit.toFixed(2)} | Hedge win: $${result.hedgeWinProfit.toFixed(2)}`
                    }
                  </p>
                </div>
                <div className={`text-2xl font-bold ${result.guaranteedProfit > 0 ? 'text-green-400' : 'text-yellow-400'}`}>
                  {result.guaranteedProfit > 0 ? '+' : ''}${result.guaranteedProfit.toFixed(2)}
                </div>
              </div>
            </div>

            {/* Total Risk */}
            <div className="bg-slate-700 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-slate-300 mb-3">Total Investment</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-400">Original Stake:</span>
                  <span className="text-white font-medium">${originalStake}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Hedge Stake:</span>
                  <span className="text-white font-medium">${result.hedgeStake.toFixed(2)}</span>
                </div>
                <div className="border-t border-slate-600 pt-2 mt-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Total at Risk:</span>
                    <span className="text-red-400 font-bold text-lg">
                      ${(parseFloat(originalStake) + result.hedgeStake).toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Info Box */}
            <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-blue-400 mb-2">When to Hedge?</h4>
              <ul className="text-sm text-slate-300 space-y-1">
                <li>• Your original bet has moved significantly in your favor</li>
                <li>• You want to lock in guaranteed profit (parlay last leg, futures, etc.)</li>
                <li>• You need to reduce exposure or manage bankroll risk</li>
                <li>• Market conditions have changed (injuries, weather, etc.)</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
