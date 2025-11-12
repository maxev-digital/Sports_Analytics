import React, { useEffect } from 'react';
import { HeroSection } from '../components/future/HeroSection';
import { PerformanceComparisonTable } from '../components/future/PerformanceComparisonTable';
import { StrategyMatrixSection } from '../components/future/StrategyMatrixSection';
import { ROICalculatorSection } from '../components/future/ROICalculatorSection';
import { TimelineSection } from '../components/future/TimelineSection';

/**
 * MLAdvantage Page
 *
 * Marketing showcase for ML-enhanced platform features.
 * Displays roadmap, strategy enhancements, performance projections,
 * and interactive ROI calculator.
 *
 * Purpose: Enable marketing while development happens in background.
 * Status: "Eye candy" that will become real platform functions.
 */
export const MLAdvantage: React.FC = () => {
  useEffect(() => {
    // Scroll to top on page load
    window.scrollTo(0, 0);

    // Track page view
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'page_view', {
        page_title: 'ML Advantage - Future Features',
        page_path: '/ml-advantage'
      });
    }
  }, []);

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Hero Section with Model Comparison */}
      <HeroSection />

      {/* Performance Comparison Table */}
      <PerformanceComparisonTable />

      {/* Strategy Enhancement Matrix */}
      <StrategyMatrixSection />

      {/* Interactive ROI Calculator */}
      <ROICalculatorSection />

      {/* Development Timeline */}
      <TimelineSection />

      {/* Early Access CTA Section */}
      <section id="early-access" className="py-20 px-4 bg-gradient-to-br from-blue-900 via-slate-900 to-green-900">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Get Early Access
          </h2>
          <p className="text-xl text-slate-300 mb-8 max-w-2xl mx-auto">
            Be among the first to access ML-enhanced features as they launch.
            Join our priority waitlist for Q1 2025 releases.
          </p>

          {/* Waitlist Form */}
          <div className="max-w-md mx-auto mb-8">
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="email"
                placeholder="Enter your email"
                className="flex-1 px-6 py-4 rounded-lg bg-slate-800 border-2 border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 transition-colors"
              />
              <button className="px-8 py-4 bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-500 hover:to-green-500 text-white font-bold rounded-lg transition-all transform hover:scale-105 whitespace-nowrap">
                Join Waitlist
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-3">
              No spam. Unsubscribe anytime. Priority access for early supporters.
            </p>
          </div>

          {/* Benefits Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
              <div className="text-3xl mb-3">🎯</div>
              <h3 className="text-lg font-bold text-white mb-2">Priority Access</h3>
              <p className="text-sm text-slate-400">
                Get access to new ML features before general release
              </p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
              <div className="text-3xl mb-3">💰</div>
              <h3 className="text-lg font-bold text-white mb-2">Special Pricing</h3>
              <p className="text-sm text-slate-400">
                Lock in discounted rates as an early supporter
              </p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
              <div className="text-3xl mb-3">📊</div>
              <h3 className="text-lg font-bold text-white mb-2">Beta Testing</h3>
              <p className="text-sm text-slate-400">
                Help shape features with your feedback
              </p>
            </div>
          </div>

          {/* Social Proof */}
          <div className="mt-12 pt-8 border-t border-slate-700">
            <div className="flex flex-wrap justify-center items-center gap-8 text-slate-400">
              <div className="text-center">
                <div className="text-2xl font-bold text-white">87</div>
                <div className="text-sm">ML Models</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white">5</div>
                <div className="text-sm">Sports Covered</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white">25</div>
                <div className="text-sm">Strategies</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white">54+</div>
                <div className="text-sm">Features Per Sport</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer Note */}
      <section className="py-12 px-4 bg-slate-950 border-t border-slate-800">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-sm text-slate-500 mb-4">
            <strong className="text-slate-400">Disclaimer:</strong> Performance projections are based on
            historical backtests and ML model improvements. Past performance does not guarantee future results.
            All betting involves risk. Please bet responsibly.
          </p>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-slate-400">
            <a href="/learn" className="hover:text-white transition-colors">
              Learn More
            </a>
            <a href="/analytics" className="hover:text-white transition-colors">
              View Analytics
            </a>
            <a href="/settings" className="hover:text-white transition-colors">
              Settings
            </a>
          </div>
        </div>
      </section>
    </div>
  );
};
