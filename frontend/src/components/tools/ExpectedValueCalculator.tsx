import { useState } from 'react';

export function ExpectedValueCalculator() {
  const [odds, setOdds] = useState<string>('');
  const [winProbability, setWinProbability] = useState<string>('');
  const [stake, setStake] = useState<string>('100');
  const [result, setResult] = useState<{
    expectedValue: number;
    expectedValuePercent: number;
    impliedProbability: number;
    edgePercent: number;
    longTermProfit: number;
    breakEvenProb: number;
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
    const oddsNum = parseFloat(odds);
    const probNum = parseFloat(winProbability) / 100;
    const stakeNum = parseFloat(stake);

    if (isNaN(oddsNum) || isNaN(probNum) || isNaN(stakeNum)) {
      return;
    }

    if (probNum < 0 || probNum > 1) {
      alert('Win probability must be between 0 and 100');
      return;
    }

    // Calculate decimal odds and payout
    const decimalOdds = americanToDecimal(oddsNum);
    const payout = stakeNum * decimalOdds;
    const profit = payout - stakeNum;

    // Calculate EV: (Win Probability × Profit) - (Loss Probability × Stake)
    const ev = (probNum * profit) - ((1 - probNum) * stakeNum);
    const evPercent = (ev / stakeNum) * 100;

    // Calculate implied probability and edge
    const impliedProb = americanToImpliedProb(oddsNum);
    const edge = probNum - impliedProb;
    const edgePercent = edge * 100;

    // Break-even probability (probability needed to break even)
    const breakEvenProb = impliedProb;

    // Long-term profit per 100 bets
    const longTermProfit = ev * 100;

    setResult({
      expectedValue: ev,
      expectedValuePercent: evPercent,
      impliedProbability: impliedProb * 100,
      edgePercent: edgePercent,
      longTermProfit: longTermProfit,
      breakEvenProb: breakEvenProb * 100,
    });
  };

  const reset = () => {
    setOdds('');
    setWinProbability('');
    setStake('100');
    setResult(null);
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">Expected Value (EV) Calculator</h2>
      <p className="text-slate-400 text-sm mb-6">
        Calculate the expected value of a bet based on your estimated win probability
      </p>

      <div className="space-y-4">
        {/* Input Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Odds (American)
            </label>
            <input
              type="number"
              value={odds}
              onChange={(e) => setOdds(e.target.value)}
              placeholder="e.g., +150 or -110"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Your Win Probability (%)
            </label>
            <input
              type="number"
              value={winProbability}
              onChange={(e) => setWinProbability(e.target.value)}
              placeholder="e.g., 55"
              min="0"
              max="100"
              step="0.1"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Stake ($)
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
                    <span className="text-slate-400">Your Win Prob:</span>
                    <span className="text-white font-medium">{winProbability}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Implied Prob:</span>
                    <span className="text-white font-medium">{result.impliedProbability.toFixed(2)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Break-Even Prob:</span>
                    <span className="text-white font-medium">{result.breakEvenProb.toFixed(2)}%</span>
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
                  ? `This bet has a ${result.edgePercent.toFixed(2)}% edge over the bookmaker. You're getting value! Over 100 identical bets, you'd expect to profit $${result.longTermProfit.toFixed(2)}.`
                  : `This bet has negative expected value. The bookmaker has a ${Math.abs(result.edgePercent).toFixed(2)}% edge over you. Pass on this bet or find better odds.`
                }
              </p>
            </div>

            {/* Formula Explanation */}
            <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-blue-400 mb-2">How is EV calculated?</h4>
              <p className="text-sm text-slate-300 mb-2">
                <span className="font-mono text-xs bg-slate-700 px-2 py-1 rounded">
                  EV = (Win Prob × Profit) - (Loss Prob × Stake)
                </span>
              </p>
              <p className="text-sm text-slate-300">
                Positive EV means the bet is profitable long-term. The higher the EV%, the better the value.
                Professional bettors only take bets with positive expected value.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
