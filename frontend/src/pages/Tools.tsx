import { useState } from 'react';
import { NoVigCalculator } from '../components/tools/NoVigCalculator';
import { ExpectedValueCalculator } from '../components/tools/ExpectedValueCalculator';
import { KellyCriterionCalculator } from '../components/tools/KellyCriterionCalculator';
import { ParlayCalculator } from '../components/tools/ParlayCalculator';
import { HedgeCalculator } from '../components/tools/HedgeCalculator';
import { DerivativeMarketsCalculator } from '../components/tools/DerivativeMarketsCalculator';
import { LineMovementTracker } from '../components/tools/LineMovementTracker';
import { SteamMoveDetector } from '../components/tools/SteamMoveDetector';
import { MarketConsensusLine } from '../components/tools/MarketConsensusLine';
import { ClosingLineValueTracker } from '../components/tools/ClosingLineValueTracker';
import { ArbitrageFinder } from '../components/tools/ArbitrageFinder';
import { WeatherImpactTool } from '../components/tools/WeatherImpactTool';

type ToolId = 'novig' | 'ev' | 'kelly' | 'parlay' | 'hedge' | 'derivative' | 'linetracker' | 'steam' | 'consensus' | 'clv' | 'arbitrage' | 'weather' | null;

export function Tools() {
  const [activeTool, setActiveTool] = useState<ToolId>(null);

  const tools = [
    {
      id: 'novig' as ToolId,
      name: 'No-Vig Calculator',
      description: 'Remove bookmaker juice to find true fair odds',
      status: 'Active',
      category: 'Odds Analysis',
      component: NoVigCalculator
    },
    {
      id: 'ev' as ToolId,
      name: 'Expected Value Calculator',
      description: 'Calculate true +EV for every bet opportunity',
      status: 'Active',
      category: 'Odds Analysis',
      component: ExpectedValueCalculator
    },
    {
      id: 'parlay' as ToolId,
      name: 'Parlay Calculator',
      description: 'Calculate true parlay odds and +EV',
      status: 'Active',
      category: 'Odds Analysis',
      component: ParlayCalculator
    },
    {
      id: 'derivative' as ToolId,
      name: 'Derivative Markets Calculator',
      description: 'Calculate fair 1H/1Q lines from full game',
      status: 'Active',
      category: 'Odds Analysis',
      component: DerivativeMarketsCalculator
    },
    {
      id: 'linetracker' as ToolId,
      name: 'Line Movement Tracker',
      description: 'Monitor how lines move across all sportsbooks',
      status: 'Active',
      category: 'Market Analysis',
      component: LineMovementTracker
    },
    {
      id: 'steam' as ToolId,
      name: 'Steam Move Detector',
      description: 'Alert when sharp money hits the market',
      status: 'Active',
      category: 'Market Analysis',
      component: SteamMoveDetector
    },
    {
      id: 'consensus' as ToolId,
      name: 'Market Consensus Line',
      description: 'Sharp line consensus from market makers',
      status: 'Active',
      category: 'Market Analysis',
      component: MarketConsensusLine
    },
    {
      id: 'clv' as ToolId,
      name: 'Closing Line Value Tracker',
      description: 'Track your bets vs closing lines to measure skill',
      status: 'Active',
      category: 'Performance',
      component: ClosingLineValueTracker
    },
    {
      id: 'arbitrage' as ToolId,
      name: 'Arbitrage Finder',
      description: 'Find guaranteed profit opportunities across books',
      status: 'Active',
      category: 'Opportunities',
      component: ArbitrageFinder
    },
    {
      id: 'hedge' as ToolId,
      name: 'Hedge Calculator',
      description: 'Calculate optimal hedge bet sizing',
      status: 'Active',
      category: 'Bankroll',
      component: HedgeCalculator
    },
    {
      id: 'kelly' as ToolId,
      name: 'Kelly Criterion Calculator',
      description: 'Optimal bet sizing based on edge and bankroll',
      status: 'Active',
      category: 'Bankroll',
      component: KellyCriterionCalculator
    },
    {
      id: 'weather' as ToolId,
      name: 'Weather Impact Tool',
      description: 'Adjust totals based on weather conditions',
      status: 'Active',
      category: 'Game Analysis',
      component: WeatherImpactTool
    },
  ];

  const categories = [...new Set(tools.map(t => t.category))];

  const activeToolData = tools.find(t => t.id === activeTool);

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <div className="flex items-center gap-4 mb-4">
            {activeTool && (
              <button
                onClick={() => setActiveTool(null)}
                className="text-blue-400 hover:text-blue-300 flex items-center gap-2 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to All Tools
              </button>
            )}
          </div>
          <h1 className="text-4xl font-bold text-slate-100 mb-4">
            {activeTool ? activeToolData?.name : 'Betting Tools'}
          </h1>
          <p className="text-lg text-slate-400">
            {activeTool
              ? activeToolData?.description
              : 'Professional-grade calculators and analytics to give you the edge'
            }
          </p>
        </div>

        {/* Active Tool View */}
        {activeTool && activeToolData?.component && (
          <div className="mb-12">
            <activeToolData.component />
          </div>
        )}

        {/* Tools Grid View */}
        {!activeTool && categories.map(category => (
          <div key={category} className="mb-12">
            <h2 className="text-2xl font-bold text-slate-100 mb-6 flex items-center gap-3">
              <div className="h-1 w-8 bg-blue-600 rounded"></div>
              {category}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {tools.filter(t => t.category === category).map((tool) => (
                <div
                  key={tool.name}
                  onClick={() => tool.id && setActiveTool(tool.id)}
                  className={`bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6 transition-all ${
                    tool.id
                      ? 'hover:border-blue-600 hover:shadow-lg hover:shadow-blue-600/20 cursor-pointer group'
                      : 'opacity-60 cursor-not-allowed'
                  }`}
                >
                  <h3 className={`text-xl font-bold text-slate-100 mb-3 transition-colors ${
                    tool.id ? 'group-hover:text-blue-400' : ''
                  }`}>
                    {tool.name}
                  </h3>
                  <p className="text-slate-400 mb-4 text-sm leading-relaxed">
                    {tool.description}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className={`text-xs px-3 py-1.5 rounded-md border ${
                      tool.status === 'Active'
                        ? 'bg-green-900/50 text-green-200 border-green-700/50'
                        : 'bg-amber-900/50 text-amber-200 border-amber-700/50'
                    }`}>
                      {tool.status}
                    </span>
                    {tool.id && (
                      <svg className="w-5 h-5 text-slate-500 group-hover:text-blue-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        {/* CTA - Only show when not viewing a tool */}
        {!activeTool && (
          <div className="text-center mt-16 p-8 bg-gradient-to-br from-blue-900/20 to-purple-900/20 border border-blue-800/50 rounded-lg">
            <h3 className="text-2xl font-bold text-slate-100 mb-4">
              All tools are now active!
            </h3>
            <p className="text-slate-400 mb-6 max-w-2xl mx-auto">
              Complete suite of professional betting tools to help you find edges, manage risk, and track performance.
              All calculators work instantly with no backend needed.
            </p>
            <div className="flex items-center justify-center gap-2 text-sm text-slate-500">
              <div className="flex items-center gap-2">
                <span className="inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                12 Tools Active
              </div>
              <span className="text-slate-600">•</span>
              <div className="flex items-center gap-2">
                <span className="inline-block w-2 h-2 bg-blue-500 rounded-full"></span>
                0 Coming Soon
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
