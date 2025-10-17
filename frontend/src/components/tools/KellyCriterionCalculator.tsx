import { useState } from 'react';

export function KellyCriterionCalculator() {
  const [odds, setOdds] = useState<string>('');
  const [winProbability, setWinProbability] = useState<string>('');
  const [bankroll, setBankroll] = useState<string>('1000');
  const [kellyFraction, setKellyFraction] = useState<string>('0.25');
  const [result, setResult] = useState<{
    kellyPercent: number;
    fullKellyStake: number;
    fractionalKellyStake: number;
    expectedGrowth: number;
    riskOfRuin: number;
    recommendation: string;
  } | null>(null);

  // Convert American odds to decimal
  const americanToDecimal = (odds: number): number => {
    if (odds > 0) {
      return (odds / 100) + 1;
    } else {
      return (100 / Math.abs(odds)) + 1;
    }
  };

  const calculateKelly = () => {
    const oddsNum = parseFloat(odds);
    const probNum = parseFloat(winProbability) / 100;
    const bankrollNum = parseFloat(bankroll);
    const fractionNum = parseFloat(kellyFraction);

    if (isNaN(oddsNum) || isNaN(probNum) || isNaN(bankrollNum) || isNaN(fractionNum)) {
      return;
    }

    if (probNum < 0 || probNum > 1) {
      alert('Win probability must be between 0 and 100');
      return;
    }

    if (fractionNum <= 0 || fractionNum > 1) {
      alert('Kelly fraction must be between 0 and 1');
      return;
    }

    // Convert to decimal odds
    const decimalOdds = americanToDecimal(oddsNum);
    const netOdds = decimalOdds - 1; // Net odds (profit per $1)

    // Kelly Formula: f* = (bp - q) / b
    // where b = net odds, p = win probability, q = loss probability (1-p)
    const q = 1 - probNum;
    const kellyPercent = ((netOdds * probNum - q) / netOdds) * 100;

    // Calculate stakes
    const fullKellyStake = (kellyPercent / 100) * bankrollNum;
    const fractionalKellyStake = fullKellyStake * fractionNum;

    // Expected growth rate (simplified)
    const expectedGrowth = kellyPercent > 0 ? kellyPercent * probNum : 0;

    // Risk of ruin estimation (simplified)
    // Higher Kelly % = higher risk
    let riskOfRuin = 0;
    if (kellyPercent > 25) {
      riskOfRuin = 15;
    } else if (kellyPercent > 15) {
      riskOfRuin = 5;
    } else if (kellyPercent > 5) {
      riskOfRuin = 1;
    } else {
      riskOfRuin = 0.1;
    }

    // Adjust risk for fractional Kelly
    riskOfRuin = riskOfRuin * fractionNum;

    // Generate recommendation
    let recommendation = '';
    if (kellyPercent <= 0) {
      recommendation = 'Do not bet - negative Kelly suggests no edge';
    } else if (kellyPercent > 25) {
      recommendation = 'Very aggressive - consider fractional Kelly to reduce variance';
    } else if (kellyPercent > 10) {
      recommendation = 'Moderate Kelly - fractional Kelly (25-50%) recommended';
    } else if (kellyPercent > 2) {
      recommendation = 'Conservative Kelly - reasonable bet size';
    } else {
      recommendation = 'Minimal edge - small bet or pass';
    }

    setResult({
      kellyPercent: kellyPercent,
      fullKellyStake: fullKellyStake,
      fractionalKellyStake: fractionalKellyStake,
      expectedGrowth: expectedGrowth,
      riskOfRuin: riskOfRuin,
      recommendation: recommendation,
    });
  };

  const reset = () => {
    setOdds('');
    setWinProbability('');
    setBankroll('1000');
    setKellyFraction('0.25');
    setResult(null);
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">Kelly Criterion Calculator</h2>
      <p className="text-slate-400 text-sm mb-6">
        Calculate optimal bet size to maximize long-term bankroll growth
      </p>

      <div className="space-y-4">
        {/* Input Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
              Total Bankroll ($)
            </label>
            <input
              type="number"
              value={bankroll}
              onChange={(e) => setBankroll(e.target.value)}
              placeholder="1000"
              min="0"
              step="0.01"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Kelly Fraction (0.25 = Quarter Kelly)
            </label>
            <input
              type="number"
              value={kellyFraction}
              onChange={(e) => setKellyFraction(e.target.value)}
              placeholder="0.25"
              min="0.01"
              max="1"
              step="0.05"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={calculateKelly}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded font-medium transition-colors"
          >
            Calculate Kelly
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
            {/* Main Kelly Result */}
            <div className={`rounded-lg p-4 ${result.kellyPercent > 0 ? 'bg-blue-900/30 border border-blue-700/50' : 'bg-red-900/30 border border-red-700/50'}`}>
              <h3 className="text-lg font-semibold text-white mb-3">Recommended Bet Size</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-slate-400 mb-1">Full Kelly Stake</div>
                  <div className="text-2xl font-bold text-white">
                    ${result.fullKellyStake.toFixed(2)}
                  </div>
                  <div className="text-sm text-slate-400">
                    {result.kellyPercent.toFixed(2)}% of bankroll
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-1">Fractional Kelly ({(parseFloat(kellyFraction) * 100).toFixed(0)}%)</div>
                  <div className="text-2xl font-bold text-green-400">
                    ${result.fractionalKellyStake.toFixed(2)}
                  </div>
                  <div className="text-sm text-slate-400">
                    {(result.kellyPercent * parseFloat(kellyFraction)).toFixed(2)}% of bankroll
                  </div>
                </div>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-700 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-slate-300 mb-3">Kelly Statistics</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Kelly %:</span>
                    <span className="text-white font-medium">{result.kellyPercent.toFixed(2)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Expected Growth:</span>
                    <span className="text-green-400 font-medium">{result.expectedGrowth.toFixed(2)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Risk of Ruin:</span>
                    <span className={`font-medium ${result.riskOfRuin > 5 ? 'text-red-400' : result.riskOfRuin > 1 ? 'text-yellow-400' : 'text-green-400'}`}>
                      {result.riskOfRuin.toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-slate-700 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-slate-300 mb-3">Common Fractions</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Full Kelly (100%):</span>
                    <span className="text-white font-medium">${result.fullKellyStake.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Half Kelly (50%):</span>
                    <span className="text-white font-medium">${(result.fullKellyStake * 0.5).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Quarter Kelly (25%):</span>
                    <span className="text-green-400 font-medium">${(result.fullKellyStake * 0.25).toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendation */}
            <div className={`rounded-lg p-4 ${result.kellyPercent > 0 ? 'bg-blue-900/30 border border-blue-700/50' : 'bg-red-900/30 border border-red-700/50'}`}>
              <h4 className={`text-sm font-semibold mb-2 ${result.kellyPercent > 0 ? 'text-blue-400' : 'text-red-400'}`}>
                Recommendation
              </h4>
              <p className="text-sm text-slate-300">
                {result.recommendation}
              </p>
            </div>

            {/* Formula and Tips */}
            <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-blue-400 mb-2">Understanding Kelly Criterion</h4>
              <p className="text-sm text-slate-300 mb-3">
                <span className="font-mono text-xs bg-slate-700 px-2 py-1 rounded">
                  f* = (bp - q) / b
                </span>
              </p>
              <div className="space-y-2 text-sm text-slate-300">
                <p><strong>Full Kelly:</strong> Maximizes long-term growth but high variance</p>
                <p><strong>Fractional Kelly:</strong> Reduces variance while maintaining good growth</p>
                <p><strong>Quarter Kelly (0.25):</strong> Recommended for most bettors - good balance of growth and safety</p>
                <p><strong>Risk of Ruin:</strong> Probability of losing your entire bankroll. Keep this under 5%!</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
