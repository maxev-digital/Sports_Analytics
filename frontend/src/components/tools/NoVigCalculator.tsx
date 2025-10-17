import { useState } from 'react';

export function NoVigCalculator() {
  const [oddsA, setOddsA] = useState<string>('');
  const [oddsB, setOddsB] = useState<string>('');
  const [result, setResult] = useState<{
    probA: number;
    probB: number;
    vig: number;
    fairOddsA: number;
    fairOddsB: number;
    impliedProbA: number;
    impliedProbB: number;
  } | null>(null);

  // Convert American odds to implied probability
  const americanToImpliedProb = (odds: number): number => {
    if (odds > 0) {
      return 100 / (odds + 100);
    } else {
      return Math.abs(odds) / (Math.abs(odds) + 100);
    }
  };

  // Convert probability to American odds
  const probToAmericanOdds = (prob: number): number => {
    if (prob >= 0.5) {
      return Math.round(-(prob * 100) / (1 - prob));
    } else {
      return Math.round(((1 - prob) * 100) / prob);
    }
  };

  const calculateNoVig = () => {
    const oddsANum = parseFloat(oddsA);
    const oddsBNum = parseFloat(oddsB);

    if (isNaN(oddsANum) || isNaN(oddsBNum)) {
      return;
    }

    // Get implied probabilities (with vig)
    const impliedProbA = americanToImpliedProb(oddsANum);
    const impliedProbB = americanToImpliedProb(oddsBNum);

    // Calculate overround (vig)
    const overround = impliedProbA + impliedProbB;
    const vig = ((overround - 1) * 100);

    // Calculate true probabilities (remove vig)
    const trueProbA = impliedProbA / overround;
    const trueProbB = impliedProbB / overround;

    // Convert back to fair odds
    const fairOddsA = probToAmericanOdds(trueProbA);
    const fairOddsB = probToAmericanOdds(trueProbB);

    setResult({
      probA: trueProbA * 100,
      probB: trueProbB * 100,
      vig: vig,
      fairOddsA: fairOddsA,
      fairOddsB: fairOddsB,
      impliedProbA: impliedProbA * 100,
      impliedProbB: impliedProbB * 100,
    });
  };

  const reset = () => {
    setOddsA('');
    setOddsB('');
    setResult(null);
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">No-Vig Calculator</h2>
      <p className="text-slate-400 text-sm mb-6">
        Remove bookmaker juice to find true fair odds and probabilities
      </p>

      <div className="space-y-4">
        {/* Input Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Side A Odds (American)
            </label>
            <input
              type="number"
              value={oddsA}
              onChange={(e) => setOddsA(e.target.value)}
              placeholder="e.g., -110"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Side B Odds (American)
            </label>
            <input
              type="number"
              value={oddsB}
              onChange={(e) => setOddsB(e.target.value)}
              placeholder="e.g., -110"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={calculateNoVig}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded font-medium transition-colors"
          >
            Calculate
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
            <div className="bg-slate-700 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-3">Bookmaker Juice</h3>
              <div className="text-2xl font-bold text-red-400">
                {result.vig.toFixed(2)}%
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Side A Results */}
              <div className="bg-slate-700 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-3">Side A</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">With Vig:</span>
                    <span className="text-white font-medium">{oddsA}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Implied Prob:</span>
                    <span className="text-white font-medium">{result.impliedProbA.toFixed(2)}%</span>
                  </div>
                  <div className="border-t border-slate-600 pt-2 mt-2">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Fair Odds:</span>
                      <span className="text-green-400 font-bold">
                        {result.fairOddsA > 0 ? '+' : ''}{result.fairOddsA}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">True Prob:</span>
                      <span className="text-green-400 font-bold">{result.probA.toFixed(2)}%</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Side B Results */}
              <div className="bg-slate-700 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-3">Side B</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">With Vig:</span>
                    <span className="text-white font-medium">{oddsB}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Implied Prob:</span>
                    <span className="text-white font-medium">{result.impliedProbB.toFixed(2)}%</span>
                  </div>
                  <div className="border-t border-slate-600 pt-2 mt-2">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Fair Odds:</span>
                      <span className="text-green-400 font-bold">
                        {result.fairOddsB > 0 ? '+' : ''}{result.fairOddsB}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">True Prob:</span>
                      <span className="text-green-400 font-bold">{result.probB.toFixed(2)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Explanation */}
            <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-blue-400 mb-2">What does this mean?</h4>
              <p className="text-sm text-slate-300">
                The bookmaker's {result.vig.toFixed(2)}% vig is their profit margin built into the odds.
                The fair odds show what the true market price should be without the bookmaker's edge.
                Use these fair odds to identify value bets when a bookmaker's line differs significantly.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
