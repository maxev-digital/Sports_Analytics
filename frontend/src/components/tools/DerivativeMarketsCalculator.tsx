import { useState } from 'react';

export function DerivativeMarketsCalculator() {
  const [fullGameTotal, setFullGameTotal] = useState<string>('');
  const [sport, setSport] = useState<'nba' | 'nfl' | 'nhl'>('nba');
  const [result, setResult] = useState<{
    firstHalfTotal: number;
    firstQuarterTotal: number;
    thirdQuarterTotal: number;
    fullGameTotal: number;
  } | null>(null);

  // Sport-specific scoring distributions
  const getScoringDistribution = (sport: string) => {
    switch (sport) {
      case 'nba':
        return {
          firstHalf: 0.495,      // ~49.5% of points in 1H
          firstQuarter: 0.245,   // ~24.5% of points in 1Q
          thirdQuarter: 0.255,   // ~25.5% of points in 3Q (highest)
        };
      case 'nfl':
        return {
          firstHalf: 0.47,       // ~47% of points in 1H
          firstQuarter: 0.20,    // ~20% of points in 1Q
          thirdQuarter: 0.27,    // ~27% of points in 3Q
        };
      case 'nhl':
        return {
          firstHalf: 0.48,       // ~48% of goals in first 30 min
          firstQuarter: 0.31,    // ~31% in first period
          thirdQuarter: 0.35,    // ~35% in third period
        };
      default:
        return {
          firstHalf: 0.495,
          firstQuarter: 0.245,
          thirdQuarter: 0.255,
        };
    }
  };

  const calculateDerivatives = () => {
    const totalNum = parseFloat(fullGameTotal);

    if (isNaN(totalNum) || totalNum <= 0) {
      alert('Please enter a valid full game total');
      return;
    }

    const dist = getScoringDistribution(sport);

    // Calculate derivative totals
    const firstHalfTotal = totalNum * dist.firstHalf;
    const firstQuarterTotal = totalNum * dist.firstQuarter;
    const thirdQuarterTotal = totalNum * dist.thirdQuarter;

    setResult({
      firstHalfTotal: Math.round(firstHalfTotal * 2) / 2, // Round to nearest 0.5
      firstQuarterTotal: Math.round(firstQuarterTotal * 2) / 2,
      thirdQuarterTotal: Math.round(thirdQuarterTotal * 2) / 2,
      fullGameTotal: totalNum,
    });
  };

  const reset = () => {
    setFullGameTotal('');
    setSport('nba');
    setResult(null);
  };

  const getSportLabel = (sport: string) => {
    switch (sport) {
      case 'nba': return { q1: '1st Quarter', h1: '1st Half', q3: '3rd Quarter' };
      case 'nfl': return { q1: '1st Quarter', h1: '1st Half', q3: '3rd Quarter' };
      case 'nhl': return { q1: '1st Period', h1: 'First 30 Min', q3: '3rd Period' };
      default: return { q1: '1st Quarter', h1: '1st Half', q3: '3rd Quarter' };
    }
  };

  const labels = getSportLabel(sport);

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">Derivative Markets Calculator</h2>
      <p className="text-slate-400 text-sm mb-6">
        Calculate fair 1H/1Q totals from full game totals using historical scoring distributions
      </p>

      <div className="space-y-4">
        {/* Input Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Sport
            </label>
            <select
              value={sport}
              onChange={(e) => setSport(e.target.value as 'nba' | 'nfl' | 'nhl')}
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
            >
              <option value="nba">NBA Basketball</option>
              <option value="nfl">NFL Football</option>
              <option value="nhl">NHL Hockey</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Full Game Total
            </label>
            <input
              type="number"
              value={fullGameTotal}
              onChange={(e) => setFullGameTotal(e.target.value)}
              placeholder="e.g., 225.5"
              step="0.5"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={calculateDerivatives}
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
            {/* Full Game Reference */}
            <div className="bg-slate-700 rounded-lg p-4 border-l-4 border-blue-600">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Full Game Total</span>
                <span className="text-2xl font-bold text-white">{result.fullGameTotal}</span>
              </div>
            </div>

            {/* Derivative Totals Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* First Quarter/Period */}
              <div className="bg-gradient-to-br from-green-900/30 to-green-800/20 border border-green-700/50 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-green-400 mb-2">{labels.q1} Total</h3>
                <div className="text-3xl font-bold text-white mb-1">
                  {result.firstQuarterTotal}
                </div>
                <div className="text-xs text-slate-400">
                  {((result.firstQuarterTotal / result.fullGameTotal) * 100).toFixed(1)}% of full game
                </div>
              </div>

              {/* First Half */}
              <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 border border-blue-700/50 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-blue-400 mb-2">{labels.h1} Total</h3>
                <div className="text-3xl font-bold text-white mb-1">
                  {result.firstHalfTotal}
                </div>
                <div className="text-xs text-slate-400">
                  {((result.firstHalfTotal / result.fullGameTotal) * 100).toFixed(1)}% of full game
                </div>
              </div>

              {/* Third Quarter/Period */}
              <div className="bg-gradient-to-br from-purple-900/30 to-purple-800/20 border border-purple-700/50 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-purple-400 mb-2">{labels.q3} Total</h3>
                <div className="text-3xl font-bold text-white mb-1">
                  {result.thirdQuarterTotal}
                </div>
                <div className="text-xs text-slate-400">
                  {((result.thirdQuarterTotal / result.fullGameTotal) * 100).toFixed(1)}% of full game
                </div>
              </div>
            </div>

            {/* How to Use */}
            <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-blue-400 mb-2">How to find value:</h4>
              <ul className="text-sm text-slate-300 space-y-1">
                <li>• Compare these fair totals to actual sportsbook lines</li>
                <li>• If book's {labels.h1} line is significantly lower, consider Over</li>
                <li>• If book's {labels.h1} line is significantly higher, consider Under</li>
                <li>• Look for 2+ point discrepancies for meaningful edges</li>
              </ul>
            </div>

            {/* Scoring Distribution Info */}
            <div className="bg-slate-700 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-slate-300 mb-3">
                {sport.toUpperCase()} Historical Distribution
              </h4>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="text-slate-400">{labels.q1}</div>
                  <div className="text-white font-medium">
                    {(getScoringDistribution(sport).firstQuarter * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-slate-400">{labels.h1}</div>
                  <div className="text-white font-medium">
                    {(getScoringDistribution(sport).firstHalf * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-slate-400">{labels.q3}</div>
                  <div className="text-white font-medium">
                    {(getScoringDistribution(sport).thirdQuarter * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>

            {/* Example */}
            <div className="bg-amber-900/30 border border-amber-700/50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-amber-400 mb-2">Example:</h4>
              <p className="text-sm text-slate-300">
                If full game total is {result.fullGameTotal} and sportsbook has {labels.h1} at{' '}
                <span className="font-bold">{result.firstHalfTotal - 3}</span>, there's a{' '}
                <span className="text-green-400 font-bold">3-point edge on the Over</span>.
                {' '}If they have it at <span className="font-bold">{result.firstHalfTotal + 3}</span>,
                there's a <span className="text-red-400 font-bold">3-point edge on the Under</span>.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
