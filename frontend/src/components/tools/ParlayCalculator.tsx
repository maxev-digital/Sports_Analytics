import { useState } from 'react';

interface Leg {
  id: number;
  odds: string;
  description: string;
}

export function ParlayCalculator() {
  const [legs, setLegs] = useState<Leg[]>([
    { id: 1, odds: '', description: '' },
    { id: 2, odds: '', description: '' },
  ]);
  const [stake, setStake] = useState<string>('100');
  const [result, setResult] = useState<{
    parlayOdds: number;
    totalPayout: number;
    totalProfit: number;
    impliedProbability: number;
    trueProbability: number;
    breakEvenProbability: number;
  } | null>(null);

  // Convert American odds to decimal
  const americanToDecimal = (odds: number): number => {
    if (odds > 0) {
      return (odds / 100) + 1;
    } else {
      return (100 / Math.abs(odds)) + 1;
    }
  };

  // Convert decimal odds to American
  const decimalToAmerican = (decimal: number): number => {
    if (decimal >= 2.0) {
      return Math.round((decimal - 1) * 100);
    } else {
      return Math.round(-100 / (decimal - 1));
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

  const addLeg = () => {
    const newId = legs.length > 0 ? Math.max(...legs.map(l => l.id)) + 1 : 1;
    setLegs([...legs, { id: newId, odds: '', description: '' }]);
  };

  const removeLeg = (id: number) => {
    if (legs.length > 2) {
      setLegs(legs.filter(leg => leg.id !== id));
    }
  };

  const updateLeg = (id: number, field: 'odds' | 'description', value: string) => {
    setLegs(legs.map(leg =>
      leg.id === id ? { ...leg, [field]: value } : leg
    ));
  };

  const calculateParlay = () => {
    const stakeNum = parseFloat(stake);

    if (isNaN(stakeNum) || stakeNum <= 0) {
      alert('Please enter a valid stake');
      return;
    }

    // Filter legs with valid odds
    const validLegs = legs.filter(leg => {
      const oddsNum = parseFloat(leg.odds);
      return !isNaN(oddsNum);
    });

    if (validLegs.length < 2) {
      alert('Please enter at least 2 legs with valid odds');
      return;
    }

    // Calculate parlay odds by multiplying decimal odds
    let parlayDecimalOdds = 1;
    let trueProbability = 1;
    let impliedProbability = 1;

    validLegs.forEach(leg => {
      const oddsNum = parseFloat(leg.odds);
      const decimalOdds = americanToDecimal(oddsNum);
      parlayDecimalOdds *= decimalOdds;

      // Calculate probabilities
      const legImpliedProb = americanToImpliedProb(oddsNum);
      impliedProbability *= legImpliedProb;

      // For true probability, remove vig (assume ~5% vig per leg)
      const legTrueProb = legImpliedProb / 1.05;
      trueProbability *= legTrueProb;
    });

    // Convert parlay decimal odds to American
    const parlayAmericanOdds = decimalToAmerican(parlayDecimalOdds);

    // Calculate payout and profit
    const totalPayout = stakeNum * parlayDecimalOdds;
    const totalProfit = totalPayout - stakeNum;

    // Break-even probability (probability needed to break even)
    const breakEvenProb = 1 / parlayDecimalOdds;

    setResult({
      parlayOdds: parlayAmericanOdds,
      totalPayout: totalPayout,
      totalProfit: totalProfit,
      impliedProbability: impliedProbability * 100,
      trueProbability: trueProbability * 100,
      breakEvenProbability: breakEvenProb * 100,
    });
  };

  const reset = () => {
    setLegs([
      { id: 1, odds: '', description: '' },
      { id: 2, odds: '', description: '' },
    ]);
    setStake('100');
    setResult(null);
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">Parlay Calculator</h2>
      <p className="text-slate-400 text-sm mb-6">
        Calculate parlay odds and payout for multiple legs
      </p>

      <div className="space-y-4">
        {/* Stake Input */}
        <div className="bg-slate-700 rounded-lg p-4">
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
            className="w-full bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Legs Section */}
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold text-white">Parlay Legs</h3>
            <button
              onClick={addLeg}
              className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors"
            >
              + Add Leg
            </button>
          </div>

          {legs.map((leg, index) => (
            <div key={leg.id} className="bg-slate-700 rounded-lg p-4">
              <div className="flex justify-between items-center mb-3">
                <span className="text-sm font-semibold text-slate-300">Leg {index + 1}</span>
                {legs.length > 2 && (
                  <button
                    onClick={() => removeLeg(leg.id)}
                    className="text-red-400 hover:text-red-300 text-sm"
                  >
                    Remove
                  </button>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Odds (American)</label>
                  <input
                    type="number"
                    value={leg.odds}
                    onChange={(e) => updateLeg(leg.id, 'odds', e.target.value)}
                    placeholder="e.g., -110"
                    className="w-full bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Description (optional)</label>
                  <input
                    type="text"
                    value={leg.description}
                    onChange={(e) => updateLeg(leg.id, 'description', e.target.value)}
                    placeholder="e.g., Lakers ML"
                    className="w-full bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={calculateParlay}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded font-medium transition-colors"
          >
            Calculate Parlay
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
            {/* Main Result */}
            <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-blue-700/50 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-3">Parlay Results</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <div className="text-sm text-slate-400 mb-1">Parlay Odds</div>
                  <div className="text-2xl font-bold text-white">
                    {result.parlayOdds > 0 ? '+' : ''}{result.parlayOdds}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-1">Total Payout</div>
                  <div className="text-2xl font-bold text-green-400">
                    ${result.totalPayout.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-1">Total Profit</div>
                  <div className="text-2xl font-bold text-green-400">
                    ${result.totalProfit.toFixed(2)}
                  </div>
                </div>
              </div>
            </div>

            {/* Probability Analysis */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-700 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-slate-300 mb-3">Probability Analysis</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Implied Prob (with vig):</span>
                    <span className="text-white font-medium">{result.impliedProbability.toFixed(2)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">True Prob (est.):</span>
                    <span className="text-white font-medium">{result.trueProbability.toFixed(2)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Break-Even Prob:</span>
                    <span className="text-white font-medium">{result.breakEvenProbability.toFixed(2)}%</span>
                  </div>
                </div>
              </div>

              <div className="bg-slate-700 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-slate-300 mb-3">Parlay Summary</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Number of Legs:</span>
                    <span className="text-white font-medium">{legs.filter(l => l.odds).length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Risk:</span>
                    <span className="text-red-400 font-medium">${stake}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">To Win:</span>
                    <span className="text-green-400 font-medium">${result.totalProfit.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Legs Breakdown */}
            <div className="bg-slate-700 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-slate-300 mb-3">Legs Breakdown</h4>
              <div className="space-y-2">
                {legs.filter(leg => leg.odds).map((leg, index) => {
                  const oddsNum = parseFloat(leg.odds);
                  const prob = americanToImpliedProb(oddsNum) * 100;
                  return (
                    <div key={leg.id} className="flex justify-between items-center">
                      <div className="flex-1">
                        <span className="text-white font-medium">Leg {index + 1}</span>
                        {leg.description && (
                          <span className="text-slate-400 ml-2">- {leg.description}</span>
                        )}
                      </div>
                      <div className="text-right">
                        <span className="text-white font-medium mr-3">
                          {oddsNum > 0 ? '+' : ''}{oddsNum}
                        </span>
                        <span className="text-slate-400 text-sm">
                          ({prob.toFixed(1)}%)
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Warning */}
            <div className="bg-yellow-900/30 border border-yellow-700/50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-yellow-400 mb-2">⚠️ Parlay Warning</h4>
              <p className="text-sm text-slate-300">
                Parlays have a higher house edge than single bets. With {legs.filter(l => l.odds).length} legs,
                ALL must win for a payout. The true probability of winning this parlay is approximately {result.trueProbability.toFixed(2)}%.
                Consider betting legs individually for better long-term value.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
