import { useState } from 'react';

export function ExpectedValueCalculator() {
  const [bookmakerOdds, setBookmakerOdds] = useState<string>('');
  const [fairOdds, setFairOdds] = useState<string>('');
  const [stake, setStake] = useState<string>('100');
  const [result, setResult] = useState<{
    expectedValue: number;
    expectedValuePercent: number;
    impliedProbability: number;
    fairProbability: number;
    edgePercent: number;
    longTermProfit: number;
  } | null>(null);

  // Convert American odds to decimal
  const americanToDecimal = (odds: number): number => {
    if (odds > 0) {
      return (odds / 100) + 1;
    } else {
      return (100 / Math.abs(odds)) + 1;
    }
  };

  // Convert American odds to implied probability
  const americanToImpliedProb = (odds: number): number => {
    if (odds > 0) {
      return 100 / (odds + 100);
    } else {
      return Math.abs(odds) / (Math.abs(odds) + 100);
    }
  };

  const calculateEV = () => {
    const bookmakerOddsNum = parseFloat(bookmakerOdds);
    const fairOddsNum = parseFloat(fairOdds);
    const stakeNum = parseFloat(stake);

    if (isNaN(bookmakerOddsNum) || isNaN(fairOddsNum) || isNaN(stakeNum)) {
      return;
    }

    // Calculate implied probability from bookmaker odds
    const impliedProb = americanToImpliedProb(bookmakerOddsNum);

    // Calculate fair probability from fair odds
    const fairProb = americanToImpliedProb(fairOddsNum);

    // Calculate edge (fair probability - implied probability)
    const edge = fairProb - impliedProb;
    const edgePercent = edge * 100;

    // Calculate decimal odds and payout
    const decimalOdds = americanToDecimal(bookmakerOddsNum);
    const payout = stakeNum * decimalOdds;
    const profit = payout - stakeNum;

    // Calculate EV: (Fair Win Probability × Profit) - (Fair Loss Probability × Stake)
    const ev = (fairProb * profit) - ((1 - fairProb) * stakeNum);
    const evPercent = (ev / stakeNum) * 100;

    // Long-term profit per 100 bets
    const longTermProfit = ev * 100;

    setResult({
      expectedValue: ev,
      expectedValuePercent: evPercent,
      impliedProbability: impliedProb * 100,
      fairProbability: fairProb * 100,
      edgePercent: edgePercent,
      longTermProfit: longTermProfit,
    });
  };

  const reset = () => {
    setBookmakerOdds('');
    setFairOdds('');
    setStake('100');
    setResult(null);
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">Expected Value (EV) Calculator</h2>
      <p className="text-slate-400 text-sm mb-6">
        Compare bookmaker odds vs fair/true odds to find positive EV betting opportunities
      </p>

      <div className="space-y-4">
        {/* Input Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Bookmaker Odds
            </label>
            <input
              type="number"
              value={bookmakerOdds}
              onChange={(e) => setBookmakerOdds(e.target.value)}
              placeholder="e.g., -110"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
            <p className="text-xs text-slate-500 mt-1">Odds you can bet at</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Fair/True Odds
            </label>
            <input
              type="number"
              value={fairOdds}
              onChange={(e) => setFairOdds(e.target.value)}
              placeholder="e.g., +100"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
            <p className="text-xs text-slate-500 mt-1">No-vig fair market price</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Stake ($) <span className="text-slate-500 font-normal">(optional)</span>
            </label>
            <input
              type="number"
              value={stake}
              onChange={(e) => setStake(e.target.value)}
              placeholder="100"
              min="0"
              step="0.01"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
            <p className="text-xs text-slate-500 mt-1">For dollar amount display</p>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={calculateEV}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded font-medium transition-colors"
          >
            Calculate EV
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
            {/* Main EV Result */}
            <div className={`rounded-lg p-4 ${result.expectedValue > 0 ? 'bg-green-900/30 border border-green-700/50' : result.expectedValue < 0 ? 'bg-red-900/30 border border-red-700/50' : 'bg-slate-700'}`}>
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-1">Expected Value</h3>
                  <p className="text-sm text-slate-400">Per ${stake} bet</p>
                </div>
                <div className="text-right">
                  <div className={`text-3xl font-bold ${result.expectedValue > 0 ? 'text-green-400' : result.expectedValue < 0 ? 'text-red-400' : 'text-slate-400'}`}>
                    ${result.expectedValue.toFixed(2)}
                  </div>
                  <div className={`text-lg ${result.expectedValuePercent > 0 ? 'text-green-400' : result.expectedValuePercent < 0 ? 'text-red-400' : 'text-slate-400'}`}>
                    {result.expectedValuePercent > 0 ? '+' : ''}{result.expectedValuePercent.toFixed(2)}%
                  </div>
                </div>
              </div>
            </div>

            {/* Detailed Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-700 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-slate-300 mb-3">Probability Analysis</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Bookmaker Implied:</span>
                    <span className="text-white font-medium">{result.impliedProbability.toFixed(2)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Fair Probability:</span>
                    <span className="text-white font-medium">{result.fairProbability.toFixed(2)}%</span>
                  </div>
                  <div className="border-t border-slate-600 pt-2 mt-2">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Your Edge:</span>
                      <span className={`font-bold ${result.edgePercent > 0 ? 'text-green-400' : result.edgePercent < 0 ? 'text-red-400' : 'text-slate-400'}`}>
                        {result.edgePercent > 0 ? '+' : ''}{result.edgePercent.toFixed(2)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-slate-700 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-slate-300 mb-3">Long-Term Projection</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Per Bet EV:</span>
                    <span className={`font-medium ${result.expectedValue > 0 ? 'text-green-400' : result.expectedValue < 0 ? 'text-red-400' : 'text-slate-400'}`}>
                      ${result.expectedValue.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Per 100 Bets:</span>
                    <span className={`font-bold text-lg ${result.longTermProfit > 0 ? 'text-green-400' : result.longTermProfit < 0 ? 'text-red-400' : 'text-slate-400'}`}>
                      ${result.longTermProfit.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendation */}
            <div className={`rounded-lg p-4 ${result.expectedValue > 0 ? 'bg-green-900/30 border border-green-700/50' : 'bg-red-900/30 border border-red-700/50'}`}>
              <h4 className={`text-sm font-semibold mb-2 ${result.expectedValue > 0 ? 'text-green-400' : 'text-red-400'}`}>
                {result.expectedValue > 0 ? '✓ Positive EV - Good Bet' : '✗ Negative EV - Avoid'}
              </h4>
              <p className="text-sm text-slate-300">
                {result.expectedValue > 0
                  ? `The bookmaker odds imply ${result.impliedProbability.toFixed(2)}% probability, but the fair probability is ${result.fairProbability.toFixed(2)}%. This gives you a ${result.edgePercent.toFixed(2)}% edge! Over 100 identical $${stake} bets, you'd expect to profit $${result.longTermProfit.toFixed(2)}.`
                  : `The bookmaker odds are worse than the fair price. The fair odds give you a ${Math.abs(result.edgePercent).toFixed(2)}% disadvantage. Pass on this bet or shop for better lines.`
                }
              </p>
            </div>

            {/* Formula Explanation */}
            <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-blue-400 mb-2">How to use this calculator</h4>
              <p className="text-sm text-slate-300 mb-3">
                <strong>Bookmaker Odds:</strong> The odds you can actually bet at<br/>
                <strong>Fair Odds:</strong> The true market price (from no-vig calculator, Pinnacle closing line, or your models)
              </p>
              <p className="text-sm text-slate-300 mb-2">
                <span className="font-mono text-xs bg-slate-700 px-2 py-1 rounded">
                  EV = (Fair Probability × Profit) - (Loss Probability × Stake)
                </span>
              </p>
              <p className="text-sm text-slate-300">
                If your bookmaker odds are better than fair odds, you have +EV. The EV% is the same regardless of stake amount - a 5% edge is 5% whether you bet $10 or $1000.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
