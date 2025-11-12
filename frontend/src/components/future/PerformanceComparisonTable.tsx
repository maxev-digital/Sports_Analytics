import React from 'react';
import { MODEL_COMPARISONS } from '../../data/futureFeatures';

export const PerformanceComparisonTable: React.FC = () => {
  return (
    <section className="py-20 px-4 bg-gradient-to-br from-slate-800 to-slate-900">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            How We Compare
          </h2>
          <p className="text-lg text-slate-400 max-w-3xl mx-auto">
            See how ML-enhanced models stack up against traditional betting systems.
            More features, better context, higher accuracy.
          </p>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b-2 border-slate-700">
                <th className="text-left p-4 text-slate-400 font-semibold">System</th>
                <th className="text-center p-4 text-slate-400 font-semibold">Type</th>
                <th className="text-center p-4 text-slate-400 font-semibold">Features</th>
                <th className="text-center p-4 text-slate-400 font-semibold">Win Rate</th>
                <th className="text-center p-4 text-slate-400 font-semibold">ROI</th>
                <th className="text-center p-4 text-slate-400 font-semibold">Self-Learning</th>
                <th className="text-center p-4 text-slate-400 font-semibold">Context Aware</th>
              </tr>
            </thead>
            <tbody>
              {MODEL_COMPARISONS.map((model, idx) => {
                const isML = model.type === 'ml_enhanced';
                const isCurrent = model.type === 'basic';
                const rowClass = isML
                  ? 'bg-gradient-to-r from-green-900/20 to-blue-900/20 border-l-4 border-green-500'
                  : isCurrent
                  ? 'bg-blue-900/10 border-l-4 border-blue-500'
                  : 'bg-slate-800/30';

                return (
                  <tr key={idx} className={`border-b border-slate-700 ${rowClass}`}>
                    {/* System Name */}
                    <td className="p-4">
                      <div className="font-semibold text-white">{model.name}</div>
                      <div className="text-xs text-slate-400 mt-1">{model.description}</div>
                    </td>

                    {/* Type */}
                    <td className="p-4 text-center">
                      <span
                        className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
                          isML
                            ? 'bg-green-500 text-white'
                            : isCurrent
                            ? 'bg-blue-500 text-white'
                            : 'bg-slate-700 text-slate-300'
                        }`}
                      >
                        {model.type.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>

                    {/* Features Count */}
                    <td className="p-4 text-center">
                      <span
                        className={`text-2xl font-bold ${
                          isML ? 'text-green-400' : isCurrent ? 'text-blue-400' : 'text-slate-400'
                        }`}
                      >
                        {model.features_count}
                        {isML && '+'}
                      </span>
                    </td>

                    {/* Win Rate */}
                    <td className="p-4 text-center">
                      <span
                        className={`text-xl font-bold ${
                          isML ? 'text-green-400' : isCurrent ? 'text-blue-400' : 'text-slate-400'
                        }`}
                      >
                        {(model.win_rate * 100).toFixed(1)}%
                      </span>
                    </td>

                    {/* ROI */}
                    <td className="p-4 text-center">
                      <span
                        className={`text-xl font-bold ${
                          isML ? 'text-green-400' : isCurrent ? 'text-blue-400' : 'text-slate-400'
                        }`}
                      >
                        {(model.typical_roi * 100).toFixed(1)}%
                      </span>
                    </td>

                    {/* Self-Learning */}
                    <td className="p-4 text-center">
                      {model.self_improving ? (
                        <span className="text-green-400 font-semibold">✓ Yes</span>
                      ) : (
                        <span className="text-red-400">✗ No</span>
                      )}
                    </td>

                    {/* Context Awareness */}
                    <td className="p-4 text-center">
                      <span className="text-sm text-slate-300">{model.context_awareness}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Key Takeaways */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <div className="text-3xl mb-2">📊</div>
            <h3 className="text-lg font-bold text-white mb-2">More Features</h3>
            <p className="text-sm text-slate-400">
              ML models use 54+ features vs 1-5 for traditional systems. More data = better predictions.
            </p>
          </div>

          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <div className="text-3xl mb-2">🧠</div>
            <h3 className="text-lg font-bold text-white mb-2">Self-Improving</h3>
            <p className="text-sm text-slate-400">
              Autonomous weekly retraining means models get smarter every Monday without human intervention.
            </p>
          </div>

          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <div className="text-3xl mb-2">🎯</div>
            <h3 className="text-lg font-bold text-white mb-2">Context Aware</h3>
            <p className="text-sm text-slate-400">
              Factors in rest, fatigue, matchups, trends, injuries - everything that matters for accurate predictions.
            </p>
          </div>
        </div>

        {/* Technical Deep Dive Link */}
        <div className="mt-12 text-center">
          <a
            href="/learn"
            className="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 font-semibold transition-colors"
          >
            <span>Read the technical deep dive</span>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </a>
        </div>
      </div>
    </section>
  );
};
