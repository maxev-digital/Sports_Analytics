import React, { useState, useCallback } from 'react';
import { getApiUrl } from '../config';

interface MarketData {
  away_odds: number;
  tie_odds: number;
  home_odds: number;
  away_decimal: number;
  tie_decimal: number;
  home_decimal: number;
  away_implied: number;
  tie_implied: number;
  home_implied: number;
  total_implied: number;
  book_vig: number;
  three_way_arb: boolean;
}

interface FadeTieStrategy {
  stake_away: number;
  stake_home: number;
  total_staked: number;
  payout_if_away_wins: number;
  payout_if_home_wins: number;
  profit_if_no_tie: number;
  loss_if_tie: number;
  roi_if_no_tie: number;
}

interface EdgeAnalysis {
  book_tie_implied_pct: number;
  estimated_tie_rate_pct: number;
  edge_pct: number;
  positive_ev: boolean;
  expected_value: number;
  ev_per_dollar: number;
  breakeven_tie_rate_pct: number;
  verdict: string;
}

interface ScalingRow {
  bankroll: number;
  stake_away: number;
  stake_home: number;
  total_staked: number;
  profit_if_win: number;
  loss_if_tie: number;
  expected_value: number;
}

interface TieRateFactor {
  factor: string;
  rate: number;
}

interface TieRateAnalysis {
  estimated_tie_rate: number;
  factors_applied: TieRateFactor[];
  base_rate: number;
}

interface AnalysisResult {
  market: MarketData;
  fade_tie_strategy: FadeTieStrategy;
  edge_analysis: EdgeAnalysis;
  scaling_table: ScalingRow[];
  tie_rate_analysis: TieRateAnalysis;
  game_info: {
    away_team: string;
    home_team: string;
    game_total: number | null;
    spread: number | null;
    park_type: string | null;
    pitcher_matchup: string | null;
  };
}

interface StrategyBet {
  team: string;
  stake: number;
  payout: number;
}

interface Strategy {
  name: string;
  description: string;
  bets: StrategyBet[];
  total_staked: number;
  profit_if_win?: number;
  profit_if_away?: number;
  profit_if_tie?: number;
  profit_if_home?: number;
  loss_if_tie?: number;
  expected_value: number;
  tie_risk_pct: number;
  roi_if_no_tie?: number;
  tag: string;
}

interface StrategiesResult {
  strategies: Strategy[];
  tie_rate_analysis: TieRateAnalysis;
  market: {
    away_odds: number;
    tie_odds: number;
    home_odds: number;
    book_tie_implied_pct: number;
  };
}

const F5FadeTie: React.FC = () => {
  // Form state
  const [awayTeam, setAwayTeam] = useState('');
  const [homeTeam, setHomeTeam] = useState('');
  const [awayOdds, setAwayOdds] = useState('');
  const [tieOdds, setTieOdds] = useState('');
  const [homeOdds, setHomeOdds] = useState('');
  const [bankroll, setBankroll] = useState('500');
  const [gameTotal, setGameTotal] = useState('');
  const [spread, setSpread] = useState('');
  const [parkType, setParkType] = useState('');
  const [pitcherMatchup, setPitcherMatchup] = useState('');

  // Results state
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [strategies, setStrategies] = useState<StrategiesResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'analysis' | 'strategies' | 'historical'>('analysis');

  const analyzeGame = useCallback(async () => {
    if (!awayOdds || !tieOdds || !homeOdds) {
      setError('Enter all 3 odds (away, tie, home)');
      return;
    }

    setLoading(true);
    setError(null);

    const params = new URLSearchParams({
      away_odds: awayOdds.replace('+', ''),
      tie_odds: tieOdds.replace('+', ''),
      home_odds: homeOdds.replace('+', ''),
      bankroll: bankroll || '100',
    });

    if (awayTeam) params.append('away_team', awayTeam);
    if (homeTeam) params.append('home_team', homeTeam);
    if (gameTotal) params.append('game_total', gameTotal);
    if (spread) params.append('spread', spread);
    if (parkType) params.append('park_type', parkType);
    if (pitcherMatchup) params.append('pitcher_matchup', pitcherMatchup);

    try {
      const [analysisRes, strategiesRes] = await Promise.all([
        fetch(getApiUrl(`f5/analyze?${params}`)),
        fetch(getApiUrl(`f5/strategies?${params}`)),
      ]);

      if (!analysisRes.ok) {
        const err = await analysisRes.json();
        throw new Error(err.detail || 'Analysis failed');
      }

      const analysisData = await analysisRes.json();
      const strategiesData = strategiesRes.ok ? await strategiesRes.json() : null;

      setAnalysis(analysisData);
      setStrategies(strategiesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze');
    } finally {
      setLoading(false);
    }
  }, [awayOdds, tieOdds, homeOdds, bankroll, awayTeam, homeTeam, gameTotal, spread, parkType, pitcherMatchup]);

  const formatMoney = (n: number) => {
    const sign = n >= 0 ? '+' : '';
    return `${sign}$${Math.abs(n).toFixed(2)}`;
  };

  const formatOdds = (n: number) => (n > 0 ? `+${n}` : `${n}`);

  return (
    <div className="min-h-screen p-4 md:p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-white mb-1">
          F5 Fade the Tie
        </h1>
        <p className="text-slate-400 text-sm">
          Baseball First 5 Innings — 2-way coverage system. Bet both teams, fade the tie.
        </p>
      </div>

      {/* Input Form */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4 md:p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Game Setup</h2>

          {/* Teams Row */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Away Team</label>
              <input
                type="text"
                value={awayTeam}
                onChange={(e) => setAwayTeam(e.target.value)}
                placeholder="e.g. Miami Marlins"
                className="w-full bg-slate-900/60 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Home Team</label>
              <input
                type="text"
                value={homeTeam}
                onChange={(e) => setHomeTeam(e.target.value)}
                placeholder="e.g. New York Mets"
                className="w-full bg-slate-900/60 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Odds Row */}
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Away F5 ML</label>
              <input
                type="text"
                value={awayOdds}
                onChange={(e) => setAwayOdds(e.target.value)}
                placeholder="+136"
                className="w-full bg-slate-900/60 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm font-mono focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Tie F5 ML</label>
              <input
                type="text"
                value={tieOdds}
                onChange={(e) => setTieOdds(e.target.value)}
                placeholder="+460"
                className="w-full bg-slate-900/60 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm font-mono focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Home F5 ML</label>
              <input
                type="text"
                value={homeOdds}
                onChange={(e) => setHomeOdds(e.target.value)}
                placeholder="+108"
                className="w-full bg-slate-900/60 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm font-mono focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Context Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Bankroll ($)</label>
              <input
                type="number"
                value={bankroll}
                onChange={(e) => setBankroll(e.target.value)}
                placeholder="500"
                className="w-full bg-slate-900/60 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm font-mono focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Game Total</label>
              <input
                type="number"
                step="0.5"
                value={gameTotal}
                onChange={(e) => setGameTotal(e.target.value)}
                placeholder="8.5"
                className="w-full bg-slate-900/60 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm font-mono focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Park Type</label>
              <select
                value={parkType}
                onChange={(e) => setParkType(e.target.value)}
                className="w-full bg-slate-900/60 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
              >
                <option value="">-- Auto --</option>
                <option value="pitcher_park">Pitcher Park</option>
                <option value="neutral_park">Neutral</option>
                <option value="hitter_park">Hitter Park</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Pitcher Matchup</label>
              <select
                value={pitcherMatchup}
                onChange={(e) => setPitcherMatchup(e.target.value)}
                className="w-full bg-slate-900/60 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
              >
                <option value="">-- Auto --</option>
                <option value="ace_vs_ace">Ace vs Ace (ERA &lt; 3.50)</option>
                <option value="ace_vs_mid">Ace vs Mid</option>
                <option value="mid_vs_mid">Mid vs Mid</option>
                <option value="any_bad">Any Bad (ERA &gt; 4.50)</option>
              </select>
            </div>
          </div>

          {/* Analyze Button */}
          <button
            onClick={analyzeGame}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white font-semibold py-3 rounded-lg transition-colors"
          >
            {loading ? 'Analyzing...' : 'Analyze F5 Line'}
          </button>

          {error && (
            <div className="mt-3 bg-red-900/40 border border-red-700/50 rounded-lg p-3 text-red-300 text-sm">
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Results */}
      {analysis && (
        <div className="max-w-7xl mx-auto">
          {/* Tab Bar */}
          <div className="flex gap-1 mb-4 bg-slate-800/40 rounded-lg p-1 w-fit">
            {(['analysis', 'strategies', 'historical'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
                  activeTab === tab
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                {tab === 'analysis' ? 'Fade the Tie' : tab === 'strategies' ? 'Compare Strategies' : 'Historical Rates'}
              </button>
            ))}
          </div>

          {activeTab === 'analysis' && (
            <div className="space-y-4">
              {/* Verdict Banner */}
              <div className={`rounded-xl p-4 border ${
                analysis.edge_analysis.positive_ev
                  ? 'bg-emerald-900/30 border-emerald-700/50'
                  : 'bg-amber-900/30 border-amber-700/50'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-lg font-bold ${
                    analysis.edge_analysis.positive_ev ? 'text-emerald-400' : 'text-amber-400'
                  }`}>
                    {analysis.edge_analysis.positive_ev ? '+EV PLAY' : 'CAUTION'}
                  </span>
                  <span className="text-white font-mono text-lg">
                    EV: {formatMoney(analysis.edge_analysis.expected_value)}
                  </span>
                </div>
                <p className="text-slate-300 text-sm">{analysis.edge_analysis.verdict}</p>
              </div>

              {/* Market + Edge Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Market Odds */}
                <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">Market Odds</h3>
                  <div className="space-y-2">
                    {[
                      { label: analysis.game_info.away_team, odds: analysis.market.away_odds, imp: analysis.market.away_implied },
                      { label: 'Tie', odds: analysis.market.tie_odds, imp: analysis.market.tie_implied },
                      { label: analysis.game_info.home_team, odds: analysis.market.home_odds, imp: analysis.market.home_implied },
                    ].map((row) => (
                      <div key={row.label} className="flex justify-between items-center">
                        <span className="text-white text-sm">{row.label}</span>
                        <div className="flex gap-4">
                          <span className="text-emerald-400 font-mono text-sm">{formatOdds(row.odds)}</span>
                          <span className="text-slate-400 text-xs w-14 text-right">{row.imp}%</span>
                        </div>
                      </div>
                    ))}
                    <div className="border-t border-slate-700/50 pt-2 mt-2 flex justify-between">
                      <span className="text-slate-400 text-xs">Total Implied / Book Vig</span>
                      <span className="text-slate-300 text-xs font-mono">
                        {analysis.market.total_implied}% / {analysis.market.book_vig}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Edge Analysis */}
                <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">Edge Analysis</h3>
                  <div className="space-y-2">
                    {[
                      { label: 'Book Tie Implied', value: `${analysis.edge_analysis.book_tie_implied_pct}%`, color: 'text-red-400' },
                      { label: 'Est. Actual Tie Rate', value: `${analysis.edge_analysis.estimated_tie_rate_pct}%`, color: 'text-emerald-400' },
                      { label: 'Edge (Overpriced By)', value: `${analysis.edge_analysis.edge_pct}%`, color: analysis.edge_analysis.edge_pct > 0 ? 'text-emerald-400' : 'text-red-400' },
                      { label: 'Breakeven Tie Rate', value: `${analysis.edge_analysis.breakeven_tie_rate_pct}%`, color: 'text-blue-400' },
                      { label: 'EV per $1 Risked', value: `$${analysis.edge_analysis.ev_per_dollar.toFixed(4)}`, color: analysis.edge_analysis.ev_per_dollar > 0 ? 'text-emerald-400' : 'text-red-400' },
                    ].map((row) => (
                      <div key={row.label} className="flex justify-between items-center">
                        <span className="text-slate-300 text-sm">{row.label}</span>
                        <span className={`font-mono text-sm ${row.color}`}>{row.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Bet Sizing Card */}
              <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
                <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">
                  Bet Sizing — ${bankroll || '100'} Bankroll
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="bg-slate-900/60 rounded-lg p-3">
                    <div className="text-xs text-slate-400 mb-1">{analysis.game_info.away_team}</div>
                    <div className="text-xl font-bold text-white font-mono">${analysis.fade_tie_strategy.stake_away.toFixed(2)}</div>
                    <div className="text-xs text-emerald-400 mt-1">Pays ${analysis.fade_tie_strategy.payout_if_away_wins.toFixed(2)}</div>
                  </div>
                  <div className="bg-slate-900/60 rounded-lg p-3">
                    <div className="text-xs text-slate-400 mb-1">{analysis.game_info.home_team}</div>
                    <div className="text-xl font-bold text-white font-mono">${analysis.fade_tie_strategy.stake_home.toFixed(2)}</div>
                    <div className="text-xs text-emerald-400 mt-1">Pays ${analysis.fade_tie_strategy.payout_if_home_wins.toFixed(2)}</div>
                  </div>
                  <div className="bg-slate-900/60 rounded-lg p-3 col-span-2 md:col-span-1">
                    <div className="text-xs text-slate-400 mb-1">P&L Summary</div>
                    <div className="text-emerald-400 font-mono text-sm">Win: {formatMoney(analysis.fade_tie_strategy.profit_if_no_tie)} ({analysis.fade_tie_strategy.roi_if_no_tie}% ROI)</div>
                    <div className="text-red-400 font-mono text-sm mt-1">Tie: -${analysis.fade_tie_strategy.total_staked.toFixed(2)}</div>
                  </div>
                </div>
              </div>

              {/* Tie Rate Factors */}
              {analysis.tie_rate_analysis.factors_applied.length > 0 && (
                <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">Tie Rate Factors Applied</h3>
                  <div className="space-y-1">
                    {analysis.tie_rate_analysis.factors_applied.map((f, i) => (
                      <div key={i} className="flex justify-between text-sm">
                        <span className="text-slate-300">{f.factor}</span>
                        <span className="text-blue-400 font-mono">{(f.rate * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                    <div className="border-t border-slate-700/50 pt-2 mt-2 flex justify-between">
                      <span className="text-white font-semibold text-sm">Estimated Tie Rate</span>
                      <span className="text-emerald-400 font-mono font-semibold">
                        {(analysis.tie_rate_analysis.estimated_tie_rate * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Scaling Table */}
              <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4 overflow-x-auto">
                <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">Scaling Table</h3>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-slate-400 text-xs border-b border-slate-700/50">
                      <th className="text-left py-2 pr-4">Bankroll</th>
                      <th className="text-right py-2 px-2">Away Bet</th>
                      <th className="text-right py-2 px-2">Home Bet</th>
                      <th className="text-right py-2 px-2">Total</th>
                      <th className="text-right py-2 px-2">Profit (Win)</th>
                      <th className="text-right py-2 px-2">Loss (Tie)</th>
                      <th className="text-right py-2 pl-2">EV</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysis.scaling_table.map((row) => (
                      <tr key={row.bankroll} className="border-b border-slate-800/50 hover:bg-slate-700/20">
                        <td className="py-2 pr-4 text-white font-mono">${row.bankroll}</td>
                        <td className="py-2 px-2 text-slate-300 font-mono text-right">${row.stake_away.toFixed(2)}</td>
                        <td className="py-2 px-2 text-slate-300 font-mono text-right">${row.stake_home.toFixed(2)}</td>
                        <td className="py-2 px-2 text-slate-300 font-mono text-right">${row.total_staked.toFixed(2)}</td>
                        <td className="py-2 px-2 text-emerald-400 font-mono text-right">{formatMoney(row.profit_if_win)}</td>
                        <td className="py-2 px-2 text-red-400 font-mono text-right">-${Math.abs(row.loss_if_tie).toFixed(2)}</td>
                        <td className={`py-2 pl-2 font-mono text-right ${row.expected_value >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {formatMoney(row.expected_value)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'strategies' && strategies && (
            <div className="space-y-4">
              {strategies.strategies.map((strat) => (
                <div key={strat.name} className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-white font-semibold">{strat.name}</h3>
                    <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                      strat.tag === 'RECOMMENDED' ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-700/50' :
                      strat.tag === 'SAFE' ? 'bg-blue-900/50 text-blue-400 border border-blue-700/50' :
                      strat.tag === 'BALANCED' ? 'bg-purple-900/50 text-purple-400 border border-purple-700/50' :
                      strat.tag === 'NEGATIVE EV' ? 'bg-red-900/50 text-red-400 border border-red-700/50' :
                      'bg-amber-900/50 text-amber-400 border border-amber-700/50'
                    }`}>
                      {strat.tag}
                    </span>
                  </div>
                  <p className="text-slate-400 text-sm mb-3">{strat.description}</p>

                  <div className="grid grid-cols-3 gap-2 mb-3">
                    {strat.bets.map((bet) => (
                      <div key={bet.team} className="bg-slate-900/60 rounded-lg p-2 text-center">
                        <div className="text-xs text-slate-400">{bet.team}</div>
                        <div className="text-white font-mono font-semibold">${bet.stake.toFixed(2)}</div>
                        <div className="text-xs text-emerald-400">${bet.payout.toFixed(2)}</div>
                      </div>
                    ))}
                  </div>

                  <div className="flex gap-4 text-xs">
                    <span className="text-slate-400">
                      Staked: <span className="text-white font-mono">${strat.total_staked.toFixed(2)}</span>
                    </span>
                    <span className="text-slate-400">
                      EV: <span className={`font-mono ${strat.expected_value >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {formatMoney(strat.expected_value)}
                      </span>
                    </span>
                    {strat.tie_risk_pct > 0 && (
                      <span className="text-slate-400">
                        Tie Risk: <span className="text-amber-400 font-mono">{strat.tie_risk_pct}%</span>
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'historical' && (
            <div className="space-y-4">
              {/* Overall Rate */}
              <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
                <h3 className="text-white font-semibold mb-2">MLB F5 Tie Rate — 10 Year Average</h3>
                <div className="flex items-end gap-3 mb-2">
                  <span className="text-4xl font-bold text-emerald-400 font-mono">11.8%</span>
                  <span className="text-slate-400 text-sm pb-1">vs books pricing at 17-20%</span>
                </div>
                <p className="text-slate-400 text-sm">
                  243,000 games analyzed (2015-2024). The 5-8% gap between book implied and actual tie rate
                  is the structural edge this strategy exploits.
                </p>
              </div>

              {/* By Category */}
              {[
                { title: 'By Game Total', data: [
                  { label: 'Under 7.0 (Low)', rate: 14.2, color: 'text-red-400' },
                  { label: '7.0 - 8.5 (Medium)', rate: 11.5, color: 'text-yellow-400' },
                  { label: 'Over 8.5 (High)', rate: 9.4, color: 'text-emerald-400' },
                ]},
                { title: 'By Spread', data: [
                  { label: 'Close (1.0 or less)', rate: 13.6, color: 'text-red-400' },
                  { label: 'Moderate (1.5)', rate: 11.2, color: 'text-yellow-400' },
                  { label: 'Wide (2.0+)', rate: 8.9, color: 'text-emerald-400' },
                ]},
                { title: 'By Park Factor', data: [
                  { label: 'Pitcher Parks (Oracle, Dodger, Petco)', rate: 13.8, color: 'text-red-400' },
                  { label: 'Neutral Parks', rate: 11.6, color: 'text-yellow-400' },
                  { label: 'Hitter Parks (Coors, GAB, Globe Life)', rate: 9.1, color: 'text-emerald-400' },
                ]},
                { title: 'By Pitcher Matchup', data: [
                  { label: 'Ace vs Ace (both ERA < 3.50)', rate: 15.8, color: 'text-red-400' },
                  { label: 'Ace vs Mid', rate: 12.1, color: 'text-yellow-400' },
                  { label: 'Mid vs Mid (3.50-4.50)', rate: 11.2, color: 'text-yellow-400' },
                  { label: 'Any Bad Starter (ERA > 4.50)', rate: 8.8, color: 'text-emerald-400' },
                ]},
              ].map((section) => (
                <div key={section.title} className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">{section.title}</h3>
                  <div className="space-y-2">
                    {section.data.map((row) => (
                      <div key={row.label} className="flex justify-between items-center">
                        <span className="text-slate-300 text-sm">{row.label}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-24 bg-slate-700/50 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                row.rate > 13 ? 'bg-red-500' : row.rate > 10 ? 'bg-yellow-500' : 'bg-emerald-500'
                              }`}
                              style={{ width: `${(row.rate / 20) * 100}%` }}
                            />
                          </div>
                          <span className={`font-mono text-sm w-12 text-right ${row.color}`}>{row.rate}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}

              {/* Key Insight */}
              <div className="bg-blue-900/30 border border-blue-700/50 rounded-xl p-4">
                <h3 className="text-blue-400 font-semibold mb-2">Optimal F5 Fade Conditions</h3>
                <ul className="text-slate-300 text-sm space-y-1">
                  <li>High game total (8.5+) — tie rate drops to ~9.4%</li>
                  <li>Hitter-friendly park (Coors, GAB) — tie rate ~9.1%</li>
                  <li>At least one bad starter (ERA 4.50+) — tie rate ~8.8%</li>
                  <li>Wide spread (2.0+ run line) — tie rate ~8.9%</li>
                  <li>Best case (all factors aligned): tie rate under 8%, edge 10%+</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      {/* How It Works (show when no results) */}
      {!analysis && !loading && (
        <div className="max-w-7xl mx-auto">
          <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4">How F5 Fade the Tie Works</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
              <div>
                <div className="text-blue-400 font-semibold mb-2">1. Find the Setup</div>
                <p className="text-slate-400">
                  Look for F5 (First 5 Innings) 3-way moneylines where all 3 outcomes
                  — away, tie, and home — are priced at plus money (+100 or higher).
                </p>
              </div>
              <div>
                <div className="text-blue-400 font-semibold mb-2">2. The Edge</div>
                <p className="text-slate-400">
                  Books price the F5 tie at 17-20% implied probability, but historically
                  ties only occur ~11.8% of the time. That 5-8% gap is your edge.
                </p>
              </div>
              <div>
                <div className="text-blue-400 font-semibold mb-2">3. Size & Place</div>
                <p className="text-slate-400">
                  Bet both teams proportionally so payouts are equal regardless of winner.
                  You profit ~10% ROI whenever either team leads after 5. Only risk is a tie.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default F5FadeTie;
