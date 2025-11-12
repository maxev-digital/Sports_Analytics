import React, { useState } from 'react';
import { calculateProfitDifference } from '../../data/futureFeatures';

export const ROICalculatorSection: React.FC = () => {
  const [bankroll, setBankroll] = useState(10000);
  const [betsPerWeek, setBetsPerWeek] = useState(50);

  const TRADITIONAL_ROI = 0.02;
  const CURRENT_ROI = 0.083;
  const ML_ENHANCED_ROI = 0.12;

  const traditionalResults = calculateProfitDifference(bankroll, betsPerWeek, 0, TRADITIONAL_ROI);
  const currentResults = calculateProfitDifference(bankroll, betsPerWeek, 0, CURRENT_ROI);
  const mlResults = calculateProfitDifference(bankroll, betsPerWeek, 0, ML_ENHANCED_ROI);

  const vsTraditional = calculateProfitDifference(bankroll, betsPerWeek, TRADITIONAL_ROI, ML_ENHANCED_ROI);
  const vsCurrent = calculateProfitDifference(bankroll, betsPerWeek, CURRENT_ROI, ML_ENHANCED_ROI);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  return (
    <section className="py-20 px-4 bg-slate-900" id="roi-calculator">
      <div className="max-w-5xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Calculate Your Potential
          </h2>
          <p className="text-lg text-slate-400 max-w-3xl mx-auto">
            See how ML enhancement could impact your betting profits over one year.
            Adjust the sliders to match your bankroll and betting frequency.
          </p>
        </div>

        {/* Calculator Card */}
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 border-2 border-slate-700 shadow-2xl">
          {/* Input Controls */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
            {/* Bankroll Slider */}
            <div>
              <label className="block text-sm font-semibold text-slate-400 mb-3">
                Starting Bankroll
              </label>
              <div className="text-4xl font-bold text-white mb-4">
                {formatCurrency(bankroll)}
              </div>
              <input
                type="range"
                min="1000"
                max="100000"
                step="1000"
                value={bankroll}
                onChange={(e) => setBankroll(Number(e.target.value))}
                className="w-full h-3 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-xs text-slate-500 mt-2">
                <span>$1,000</span>
                <span>$100,000</span>
              </div>
            </div>

            {/* Bets Per Week Slider */}
            <div>
              <label className="block text-sm font-semibold text-slate-400 mb-3">
                Bets Per Week
              </label>
              <div className="text-4xl font-bold text-white mb-4">
                {betsPerWeek}
              </div>
              <input
                type="range"
                min="10"
                max="200"
                step="10"
                value={betsPerWeek}
                onChange={(e) => setBetsPerWeek(Number(e.target.value))}
                className="w-full h-3 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-xs text-slate-500 mt-2">
                <span>10</span>
                <span>200</span>
              </div>
            </div>
          </div>

          {/* Results Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {/* Traditional Models */}
            <div className="bg-slate-700/30 rounded-xl p-6 border border-slate-600">
              <div className="text-xs text-slate-400 uppercase mb-2">Traditional Models</div>
              <div className="text-sm text-slate-500 mb-3">ELO, Power Rankings</div>
              <div className="text-3xl font-bold text-white mb-1">
                {formatCurrency(traditionalResults.enhanced_profit)}
              </div>
              <div className="text-xs text-slate-400">Annual Profit ({TRADITIONAL_ROI * 100}% ROI)</div>
            </div>

            {/* Current System */}
            <div className="bg-blue-900/20 rounded-xl p-6 border-2 border-blue-600">
              <div className="text-xs text-blue-400 uppercase mb-2">Current System</div>
              <div className="text-sm text-slate-400 mb-3">Pace-Based Models</div>
              <div className="text-3xl font-bold text-blue-400 mb-1">
                {formatCurrency(currentResults.enhanced_profit)}
              </div>
              <div className="text-xs text-slate-400">Annual Profit ({(CURRENT_ROI * 100).toFixed(1)}% ROI)</div>
            </div>

            {/* ML-Enhanced */}
            <div className="bg-gradient-to-br from-green-900/30 to-blue-900/30 rounded-xl p-6 border-2 border-green-500 relative">
              <div className="absolute top-2 right-2 bg-green-500 text-white text-xs font-bold px-2 py-1 rounded">
                TARGET
              </div>
              <div className="text-xs text-green-400 uppercase mb-2">ML-Enhanced</div>
              <div className="text-sm text-slate-300 mb-3">Full ML System</div>
              <div className="text-3xl font-bold text-green-400 mb-1">
                {formatCurrency(mlResults.enhanced_profit)}
              </div>
              <div className="text-xs text-slate-400">Annual Profit ({ML_ENHANCED_ROI * 100}% ROI)</div>
            </div>
          </div>

          {/* Comparison Banners */}
          <div className="space-y-3">
            {/* vs Traditional */}
            <div className="bg-gradient-to-r from-green-900/20 to-transparent rounded-lg p-4 border-l-4 border-green-500">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-400">ML-Enhanced vs Traditional Models</div>
                  <div className="text-lg font-semibold text-white">
                    Extra profit: <span className="text-green-400">{formatCurrency(vsTraditional.difference)}</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-green-400">
                    +{vsTraditional.improvement_percent.toFixed(0)}%
                  </div>
                  <div className="text-xs text-slate-400">more profit</div>
                </div>
              </div>
            </div>

            {/* vs Current */}
            <div className="bg-gradient-to-r from-blue-900/20 to-transparent rounded-lg p-4 border-l-4 border-blue-500">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-400">ML-Enhanced vs Current System</div>
                  <div className="text-lg font-semibold text-white">
                    Extra profit: <span className="text-blue-400">{formatCurrency(vsCurrent.difference)}</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-blue-400">
                    +{vsCurrent.improvement_percent.toFixed(0)}%
                  </div>
                  <div className="text-xs text-slate-400">improvement</div>
                </div>
              </div>
            </div>
          </div>

          {/* Assumptions Note */}
          <div className="mt-6 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
            <div className="text-xs text-slate-400">
              <strong className="text-slate-300">Assumptions:</strong> 2% Kelly sizing per bet, 52 weeks/year,
              {' '}-110 odds (1.91 decimal). ROI based on backtests and projected ML improvements.
              Past performance does not guarantee future results.
            </div>
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="mt-8 text-center">
          <p className="text-slate-400 mb-4">
            These projections are based on backtested data and ML enhancement targets.
          </p>
          <a
            href="#early-access"
            className="inline-block bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-500 hover:to-blue-500 text-white font-bold px-8 py-3 rounded-lg transition-all transform hover:scale-105"
          >
            Get Notified When ML Features Launch
          </a>
        </div>
      </div>

      {/* Custom Slider Styles */}
      <style>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
          cursor: pointer;
          box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
        }

        .slider::-moz-range-thumb {
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
          cursor: pointer;
          border: none;
          box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
        }

        .slider:hover::-webkit-slider-thumb {
          box-shadow: 0 0 15px rgba(59, 130, 246, 0.8);
        }

        .slider:hover::-moz-range-thumb {
          box-shadow: 0 0 15px rgba(59, 130, 246, 0.8);
        }
      `}</style>
    </section>
  );
};
