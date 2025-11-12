import React from 'react';
import { MODEL_COMPARISONS } from '../../data/futureFeatures';

export const HeroSection: React.FC = () => {
  const traditionalModel = MODEL_COMPARISONS.find(m => m.name === 'ELO Rating System');
  const currentModel = MODEL_COMPARISONS.find(m => m.name === 'Current System (Pace-Based)');
  const mlModel = MODEL_COMPARISONS.find(m => m.name === 'ML-Enhanced System');

  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 py-20 px-4">
      {/* Animated background pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGMzLjMxNCAwIDYgMi42ODYgNiA2cy0yLjY4NiA2LTYgNi02LTIuNjg2LTYtNiAyLjY4Ni02IDYtNnoiIHN0cm9rZT0iIzAwMCIgc3Ryb2tlLXdpZHRoPSIyIi8+PC9nPjwvc3ZnPg==')] animate-pulse"></div>
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-block mb-4">
            <span className="text-sm font-semibold text-blue-400 bg-blue-950 px-4 py-2 rounded-full border border-blue-500">
              PLATFORM ROADMAP 2025
            </span>
          </div>

          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
            The Future of Sports Betting
            <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-green-400">
              Intelligence
            </span>
          </h1>

          <p className="text-xl text-slate-300 max-w-3xl mx-auto mb-8">
            Discover how machine learning transforms traditional betting strategies into
            high-performance prediction systems. This roadmap shows what we're building.
          </p>

          <div className="flex flex-wrap justify-center gap-4 text-sm text-slate-400">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span>Live Now</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span>Beta Testing</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-purple-500"></div>
              <span>Q1 2025</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-orange-500"></div>
              <span>Q2 2025</span>
            </div>
          </div>
        </div>

        {/* Model Comparison Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {/* Traditional Models */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border-2 border-slate-700 hover:border-slate-600 transition-all">
            <div className="text-sm text-slate-400 mb-2">TRADITIONAL</div>
            <h3 className="text-2xl font-bold text-white mb-4">ELO & Power Rankings</h3>

            <div className="space-y-3 mb-6">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Features</span>
                <span className="text-white font-semibold">{traditionalModel?.features_count}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Win Rate</span>
                <span className="text-white font-semibold">
                  {((traditionalModel?.win_rate || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">ROI</span>
                <span className="text-white font-semibold">
                  {((traditionalModel?.typical_roi || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Self-Learning</span>
                <span className="text-red-400 font-semibold">No</span>
              </div>
            </div>

            <div className="text-sm text-slate-400">
              {traditionalModel?.description}
            </div>
          </div>

          {/* Current System */}
          <div className="bg-blue-900/30 backdrop-blur-sm rounded-xl p-6 border-2 border-blue-600 hover:border-blue-500 transition-all">
            <div className="text-sm text-blue-400 mb-2">CURRENT</div>
            <h3 className="text-2xl font-bold text-white mb-4">Our System Today</h3>

            <div className="space-y-3 mb-6">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Features</span>
                <span className="text-white font-semibold">{currentModel?.features_count}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Win Rate</span>
                <span className="text-blue-300 font-semibold">
                  {((currentModel?.win_rate || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">ROI</span>
                <span className="text-blue-300 font-semibold">
                  {((currentModel?.typical_roi || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Self-Learning</span>
                <span className="text-yellow-400 font-semibold">Partial</span>
              </div>
            </div>

            <div className="text-sm text-slate-400">
              {currentModel?.description}
            </div>
          </div>

          {/* ML-Enhanced Future */}
          <div className="bg-gradient-to-br from-green-900/40 to-blue-900/40 backdrop-blur-sm rounded-xl p-6 border-2 border-green-500 hover:border-green-400 transition-all relative overflow-hidden">
            <div className="absolute top-0 right-0 bg-green-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg">
              COMING SOON
            </div>

            <div className="text-sm text-green-400 mb-2">ML-ENHANCED</div>
            <h3 className="text-2xl font-bold text-white mb-4">Future System</h3>

            <div className="space-y-3 mb-6">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Features</span>
                <span className="text-green-300 font-semibold">{mlModel?.features_count}+</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Win Rate</span>
                <span className="text-green-300 font-semibold">
                  {((mlModel?.win_rate || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">ROI</span>
                <span className="text-green-300 font-semibold">
                  {((mlModel?.typical_roi || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Self-Learning</span>
                <span className="text-green-400 font-semibold">Yes</span>
              </div>
            </div>

            <div className="text-sm text-slate-400">
              {mlModel?.description}
            </div>
          </div>
        </div>

        {/* Key Improvements Banner */}
        <div className="bg-gradient-to-r from-blue-950/50 to-green-950/50 rounded-xl p-6 border border-blue-500/30">
          <h4 className="text-lg font-bold text-white mb-4 text-center">
            What ML Enhancement Brings
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-3xl font-bold text-green-400 mb-1">+44%</div>
              <div className="text-sm text-slate-400">ROI Increase</div>
              <div className="text-xs text-slate-500">8.3% → 12%</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-400 mb-1">+5.3%</div>
              <div className="text-sm text-slate-400">Win Rate Gain</div>
              <div className="text-xs text-slate-500">53.2% → 56%</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-purple-400 mb-1">-32%</div>
              <div className="text-sm text-slate-400">False Positives</div>
              <div className="text-xs text-slate-500">Better Quality</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-orange-400 mb-1">54</div>
              <div className="text-sm text-slate-400">Features Per Sport</div>
              <div className="text-xs text-slate-500">vs 1-5 traditional</div>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center mt-12">
          <a
            href="#early-access"
            className="inline-block bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-500 hover:to-green-500 text-white font-bold px-8 py-4 rounded-lg text-lg transition-all transform hover:scale-105 shadow-lg"
          >
            Get Early Access
          </a>
          <p className="text-sm text-slate-400 mt-3">
            Join the waitlist for ML-enhanced features
          </p>
        </div>
      </div>
    </section>
  );
};
