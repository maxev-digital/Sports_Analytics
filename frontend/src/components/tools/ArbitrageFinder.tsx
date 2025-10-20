import { useState, useEffect } from 'react';

interface BookOdds {
  id: number;
  bookmaker: string;
  oddsA: string;
  oddsB: string;
}

interface LiveArbitrage {
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  market_type: string;
  book_a: string;
  book_b: string;
  odds_a: number;
  odds_b: number;
  profit_percent: number;
  stake_a: number;
  stake_b: number;
  total_stake: number;
  guaranteed_profit: number;
  timestamp: string;
  expires_in: number;
}

interface PerformanceStats {
  total_alerts: number;
  successful_alerts: number;
  failed_alerts: number;
  pending_alerts: number;
  win_rate: number;
  avg_profit: number;
  total_profit: number;
}

export function ArbitrageFinder() {
  const [sideA, setSideA] = useState<string>('');
  const [sideB, setSideB] = useState<string>('');
  const [bookOdds, setBookOdds] = useState<BookOdds[]>([]);
  const [newBookmaker, setNewBookmaker] = useState<string>('');
  const [newOddsA, setNewOddsA] = useState<string>('');
  const [newOddsB, setNewOddsB] = useState<string>('');
  const [stake, setStake] = useState<string>('1000');
  const [liveOpportunities, setLiveOpportunities] = useState<LiveArbitrage[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [performanceStats, setPerformanceStats] = useState<PerformanceStats | null>(null);

  // Fetch live arbitrage opportunities
  useEffect(() => {
    const fetchLiveArbitrage = async () => {
      try {
        const response = await fetch('/api/alerts/arbitrage');
        if (response.ok) {
          const data = await response.json();
          setLiveOpportunities(data.alerts || []);
        }
      } catch (error) {
        console.error('Error fetching live arbitrage:', error);
      }
    };

    fetchLiveArbitrage();

    if (autoRefresh) {
      const interval = setInterval(fetchLiveArbitrage, 10000); // Refresh every 10s
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  // Fetch performance stats
  useEffect(() => {
    const fetchPerformance = async () => {
      try {
        const response = await fetch('/api/alerts/performance');
        if (response.ok) {
          const data = await response.json();
          setPerformanceStats(data.arbitrage);
        }
      } catch (error) {
        console.error('Error fetching performance stats:', error);
      }
    };

    fetchPerformance();
    const interval = setInterval(fetchPerformance, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  // Convert American odds to decimal
  const americanToDecimal = (odds: number): number => {
    if (odds > 0) {
      return (odds / 100) + 1;
    } else {
      return (100 / Math.abs(odds)) + 1;
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

  const addBookOdds = () => {
    if (!newBookmaker || !newOddsA || !newOddsB) {
      alert('Please enter bookmaker and both odds');
      return;
    }

    const entry: BookOdds = {
      id: Date.now(),
      bookmaker: newBookmaker,
      oddsA: newOddsA,
      oddsB: newOddsB,
    };

    setBookOdds([...bookOdds, entry]);
    setNewBookmaker('');
    setNewOddsA('');
    setNewOddsB('');
  };

  const removeBookOdds = (id: number) => {
    setBookOdds(bookOdds.filter(odds => odds.id !== id));
  };

  const findArbitrage = () => {
    if (bookOdds.length < 2) return null;

    // Find best odds for each side
    let bestOddsA = -Infinity;
    let bestBookA = '';
    let bestOddsB = -Infinity;
    let bestBookB = '';

    bookOdds.forEach(book => {
      const oddsANum = parseFloat(book.oddsA);
      const oddsBNum = parseFloat(book.oddsB);

      if (!isNaN(oddsANum) && oddsANum > bestOddsA) {
        bestOddsA = oddsANum;
        bestBookA = book.bookmaker;
      }
      if (!isNaN(oddsBNum) && oddsBNum > bestOddsB) {
        bestOddsB = oddsBNum;
        bestBookB = book.bookmaker;
      }
    });

    if (bestOddsA === -Infinity || bestOddsB === -Infinity) return null;

    // Calculate implied probabilities
    const impliedProbA = americanToImpliedProb(bestOddsA);
    const impliedProbB = americanToImpliedProb(bestOddsB);

    // Check for arbitrage (total implied probability < 1)
    const totalImpliedProb = impliedProbA + impliedProbB;
    const isArbitrage = totalImpliedProb < 1;

    if (!isArbitrage) {
      return {
        isArbitrage: false,
        bestOddsA,
        bestBookA,
        bestOddsB,
        bestBookB,
        totalImpliedProb,
        margin: ((totalImpliedProb - 1) * 100),
      };
    }

    // Calculate arbitrage profit
    const arbitragePercent = (1 - totalImpliedProb) * 100;
    const totalStake = parseFloat(stake);

    // Calculate optimal bet sizing
    const decimalA = americanToDecimal(bestOddsA);
    const decimalB = americanToDecimal(bestOddsB);

    const stakeA = (totalStake * impliedProbB) / totalImpliedProb;
    const stakeB = (totalStake * impliedProbA) / totalImpliedProb;

    // Calculate payouts
    const payoutA = stakeA * decimalA;
    const payoutB = stakeB * decimalB;

    // Calculate profit
    const guaranteedProfit = Math.min(payoutA, payoutB) - totalStake;
    const profitPercent = (guaranteedProfit / totalStake) * 100;

    return {
      isArbitrage: true,
      bestOddsA,
      bestBookA,
      bestOddsB,
      bestBookB,
      totalImpliedProb,
      arbitragePercent,
      stakeA,
      stakeB,
      payoutA,
      payoutB,
      guaranteedProfit,
      profitPercent,
    };
  };

  const reset = () => {
    setSideA('');
    setSideB('');
    setBookOdds([]);
    setStake('1000');
  };

  const arb = findArbitrage();

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  const formatExpiresIn = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h`;
  };

  const getSportBadge = (sport: string) => {
    if (sport.includes('nba')) return { color: 'bg-orange-500', label: 'NBA' };
    if (sport.includes('nfl')) return { color: 'bg-green-500', label: 'NFL' };
    if (sport.includes('nhl')) return { color: 'bg-blue-500', label: 'NHL' };
    if (sport.includes('ncaa')) return { color: 'bg-purple-500', label: 'NCAAB' };
    return { color: 'bg-gray-500', label: sport.toUpperCase() };
  };

  const getMarketLabel = (marketType: string) => {
    if (marketType === 'h2h') return 'Moneyline';
    if (marketType === 'spreads') return 'Spread';
    if (marketType === 'totals') return 'Total';
    return marketType;
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-white mb-1">Arbitrage Finder</h2>
          <p className="text-slate-400 text-sm">
            Find guaranteed profit opportunities by betting both sides across different sportsbooks
          </p>
        </div>
        {liveOpportunities.length > 0 && (
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              autoRefresh
                ? 'bg-green-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {autoRefresh ? '● Live' : 'Paused'}
          </button>
        )}
      </div>

      <div className="space-y-4">
        {/* Live Opportunities Section */}
        {liveOpportunities.length > 0 && (
          <div className="bg-gradient-to-r from-green-900/30 to-green-800/30 border-2 border-green-500/50 rounded-lg p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <h3 className="text-lg font-bold text-green-400">
                {liveOpportunities.length} Live Arbitrage Opportunit{liveOpportunities.length === 1 ? 'y' : 'ies'}
              </h3>
              <span className="text-xs text-slate-400">(Updates every 10s)</span>
            </div>

            <div className="space-y-3">
              {liveOpportunities.slice(0, 5).map((opp, idx) => {
                const badge = getSportBadge(opp.sport);
                return (
                  <div key={idx} className="bg-slate-800/50 rounded-lg p-4 border border-green-700/30">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-1 rounded text-xs font-bold text-white ${badge.color}`}>
                          {badge.label}
                        </span>
                        <span className="px-2 py-1 rounded text-xs font-bold bg-green-600 text-white">
                          {getMarketLabel(opp.market_type)}
                        </span>
                        <span className="text-white font-semibold">
                          {opp.away_team} @ {opp.home_team}
                        </span>
                      </div>
                      <div className="text-right">
                        <div className="text-xl font-bold text-green-400">
                          +{opp.profit_percent.toFixed(2)}%
                        </div>
                        <div className="text-xs text-slate-400">
                          Expires {formatExpiresIn(opp.expires_in)}
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3 mb-3">
                      <div className="bg-slate-900/50 rounded p-3">
                        <div className="text-xs text-slate-400 mb-1">{opp.book_a}</div>
                        <div className="text-lg font-bold text-white">
                          {opp.odds_a > 0 ? `+${opp.odds_a}` : opp.odds_a}
                        </div>
                        <div className="text-xs text-green-400">Stake: ${opp.stake_a.toFixed(2)}</div>
                      </div>
                      <div className="bg-slate-900/50 rounded p-3">
                        <div className="text-xs text-slate-400 mb-1">{opp.book_b}</div>
                        <div className="text-lg font-bold text-white">
                          {opp.odds_b > 0 ? `+${opp.odds_b}` : opp.odds_b}
                        </div>
                        <div className="text-xs text-green-400">Stake: ${opp.stake_b.toFixed(2)}</div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span>Total: ${opp.total_stake.toFixed(2)}</span>
                      <span className="text-green-400 font-bold">
                        Profit: ${opp.guaranteed_profit.toFixed(2)}
                      </span>
                      <span>{formatTime(opp.timestamp)}</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {liveOpportunities.length > 5 && (
              <div className="mt-3 text-center text-sm text-slate-400">
                +{liveOpportunities.length - 5} more opportunities - View all on Alerts page
              </div>
            )}
          </div>
        )}

        {liveOpportunities.length === 0 && (
          <div className="bg-slate-700/50 border border-slate-600 rounded-lg p-4 text-center">
            <div className="text-slate-400 text-sm">
              No live arbitrage opportunities detected. Scanning markets every 10 seconds...
            </div>
          </div>
        )}

        {/* Performance Stats */}
        {performanceStats && (
          <div className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 border border-blue-700/50 rounded-lg p-5">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              📊 Historical Performance
              <span className="text-xs text-slate-400 font-normal">(Track Record)</span>
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-800/50 rounded-lg p-3">
                <div className="text-xs text-slate-400 mb-1">Total Alerts</div>
                <div className="text-2xl font-bold text-white">{performanceStats.total_alerts}</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3">
                <div className="text-xs text-slate-400 mb-1">Win Rate</div>
                <div className="text-2xl font-bold text-green-400">{performanceStats.win_rate}%</div>
                <div className="text-xs text-slate-400 mt-1">
                  {performanceStats.successful_alerts} wins / {performanceStats.failed_alerts} losses
                </div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3">
                <div className="text-xs text-slate-400 mb-1">Avg Profit</div>
                <div className="text-2xl font-bold text-blue-400">${performanceStats.avg_profit}</div>
                <div className="text-xs text-slate-400 mt-1">per opportunity</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3">
                <div className="text-xs text-slate-400 mb-1">Total Profit</div>
                <div className="text-2xl font-bold text-purple-400">${performanceStats.total_profit.toFixed(2)}</div>
                <div className="text-xs text-slate-400 mt-1">{performanceStats.pending_alerts} pending</div>
              </div>
            </div>
            <div className="mt-3 text-xs text-slate-400 text-center">
              Performance tracking helps demonstrate the accuracy and profitability of our alerts
            </div>
          </div>
        )}

        {/* Calculator Section */}
        <div className="border-t border-slate-700 pt-6 mt-6">
          <h3 className="text-lg font-bold text-white mb-4">Manual Calculator</h3>
        {/* Side Labels */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Side A (e.g., Team/Over)
            </label>
            <input
              type="text"
              value={sideA}
              onChange={(e) => setSideA(e.target.value)}
              placeholder="Lakers/Over 225.5"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Side B (e.g., Team/Under)
            </label>
            <input
              type="text"
              value={sideB}
              onChange={(e) => setSideB(e.target.value)}
              placeholder="Celtics/Under 225.5"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Total Stake ($)
            </label>
            <input
              type="number"
              value={stake}
              onChange={(e) => setStake(e.target.value)}
              placeholder="1000"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Add Bookmaker Odds */}
        <div className="bg-slate-700 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">Add Bookmaker Odds</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <input
              type="text"
              value={newBookmaker}
              onChange={(e) => setNewBookmaker(e.target.value)}
              placeholder="Bookmaker"
              className="bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
            <input
              type="text"
              value={newOddsA}
              onChange={(e) => setNewOddsA(e.target.value)}
              placeholder={`${sideA || 'Side A'} odds`}
              className="bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
            <input
              type="text"
              value={newOddsB}
              onChange={(e) => setNewOddsB(e.target.value)}
              placeholder={`${sideB || 'Side B'} odds`}
              className="bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
            <button
              onClick={addBookOdds}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium transition-colors"
            >
              Add
            </button>
          </div>
        </div>

        {/* Current Odds */}
        {bookOdds.length > 0 && (
          <div className="bg-slate-700 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">
              Current Odds ({bookOdds.length} books)
            </h3>
            <div className="space-y-2">
              {bookOdds.map(entry => (
                <div key={entry.id} className="flex items-center justify-between bg-slate-600 rounded px-4 py-2">
                  <div className="flex items-center gap-4">
                    <span className="text-white font-medium w-32">{entry.bookmaker}</span>
                    <div className="flex gap-6">
                      <div>
                        <span className="text-xs text-slate-400 mr-2">{sideA || 'Side A'}:</span>
                        <span className="text-blue-400 font-medium">{entry.oddsA}</span>
                      </div>
                      <div>
                        <span className="text-xs text-slate-400 mr-2">{sideB || 'Side B'}:</span>
                        <span className="text-blue-400 font-medium">{entry.oddsB}</span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => removeBookOdds(entry.id)}
                    className="text-red-400 hover:text-red-300 text-sm"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Arbitrage Results */}
        {arb && bookOdds.length >= 2 && (
          <div className="space-y-4">
            {/* Arbitrage Alert */}
            <div className={`rounded-lg p-4 ${
              arb.isArbitrage
                ? 'bg-green-900/30 border-2 border-green-500'
                : 'bg-red-900/30 border border-red-700/50'
            }`}>
              <h3 className="text-2xl font-bold text-white mb-2">
                {arb.isArbitrage ? '✅ ARBITRAGE FOUND!' : '❌ No Arbitrage'}
              </h3>
              {arb.isArbitrage ? (
                <p className="text-green-400">
                  Guaranteed profit: <span className="text-2xl font-bold">
                    ${arb.guaranteedProfit?.toFixed(2)} ({arb.profitPercent?.toFixed(2)}%)
                  </span>
                </p>
              ) : (
                <p className="text-red-400">
                  Market has {arb.margin.toFixed(2)}% vig. No arbitrage opportunity.
                </p>
              )}
            </div>

            {/* Best Odds */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-700 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-slate-300 mb-3">
                  Best {sideA || 'Side A'} Odds
                </h4>
                <div className="text-2xl font-bold text-white mb-1">{arb.bestOddsA}</div>
                <div className="text-sm text-slate-400">{arb.bestBookA}</div>
                {arb.isArbitrage && (
                  <div className="mt-3 pt-3 border-t border-slate-600">
                    <div className="text-sm text-slate-400">Bet Amount</div>
                    <div className="text-xl font-bold text-green-400">
                      ${arb.stakeA?.toFixed(2)}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      Payout: ${arb.payoutA?.toFixed(2)}
                    </div>
                  </div>
                )}
              </div>

              <div className="bg-slate-700 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-slate-300 mb-3">
                  Best {sideB || 'Side B'} Odds
                </h4>
                <div className="text-2xl font-bold text-white mb-1">{arb.bestOddsB}</div>
                <div className="text-sm text-slate-400">{arb.bestBookB}</div>
                {arb.isArbitrage && (
                  <div className="mt-3 pt-3 border-t border-slate-600">
                    <div className="text-sm text-slate-400">Bet Amount</div>
                    <div className="text-xl font-bold text-green-400">
                      ${arb.stakeB?.toFixed(2)}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      Payout: ${arb.payoutB?.toFixed(2)}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Action Plan */}
            {arb.isArbitrage && (
              <div className="bg-green-900/30 border border-green-700/50 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-green-400 mb-2">💰 Action Plan</h4>
                <ol className="text-sm text-slate-300 space-y-1">
                  <li>1. Bet <strong>${arb.stakeA?.toFixed(2)}</strong> on <strong>{sideA || 'Side A'}</strong> at <strong>{arb.bestBookA}</strong> ({arb.bestOddsA})</li>
                  <li>2. Bet <strong>${arb.stakeB?.toFixed(2)}</strong> on <strong>{sideB || 'Side B'}</strong> at <strong>{arb.bestBookB}</strong> ({arb.bestOddsB})</li>
                  <li>3. Total invested: <strong>${stake}</strong></li>
                  <li>4. Guaranteed profit: <strong className="text-green-400">${arb.guaranteedProfit?.toFixed(2)}</strong> regardless of outcome</li>
                  <li>5. Act quickly - arbitrage opportunities close fast!</li>
                </ol>
              </div>
            )}

            {/* Market Stats */}
            <div className="bg-slate-700 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-slate-300 mb-3">Market Statistics</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-slate-400">Total Implied Probability</div>
                  <div className={`text-lg font-bold ${
                    arb.totalImpliedProb < 1 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {(arb.totalImpliedProb * 100).toFixed(2)}%
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-400">
                    {arb.isArbitrage ? 'Arbitrage %' : 'Market Vig'}
                  </div>
                  <div className={`text-lg font-bold ${
                    arb.isArbitrage ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {arb.isArbitrage
                      ? `${arb.arbitragePercent?.toFixed(2)}%`
                      : `${arb.margin.toFixed(2)}%`
                    }
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Buttons */}
        <div className="flex gap-3">
          {bookOdds.length > 0 && (
            <button
              onClick={reset}
              className="bg-slate-700 hover:bg-slate-600 text-white px-6 py-2 rounded font-medium transition-colors"
            >
              Reset
            </button>
          )}
        </div>

        {/* Instructions */}
        {bookOdds.length < 2 && (
          <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-blue-400 mb-2">What is arbitrage betting?</h4>
            <p className="text-sm text-slate-300 mb-3">
              Arbitrage (or "arbing") is betting on all possible outcomes of an event across different
              sportsbooks to guarantee a profit regardless of the result. This happens when sportsbooks
              disagree on odds.
            </p>
            <h5 className="text-sm font-semibold text-blue-400 mb-2">How to use:</h5>
            <ul className="text-sm text-slate-300 space-y-1">
              <li>1. Label the two sides of the market (Team A vs Team B, Over vs Under, etc.)</li>
              <li>2. Add odds from multiple sportsbooks for both sides</li>
              <li>3. The tool will find the best combination and calculate guaranteed profit</li>
              <li>4. Arbitrage opportunities are rare and close quickly - act fast!</li>
            </ul>
            <div className="mt-3 pt-3 border-t border-blue-800/50">
              <p className="text-xs text-slate-400">
                <strong>Warning:</strong> Some sportsbooks ban arbitrage bettors. Use at your own risk.
              </p>
            </div>
          </div>
        )}
        </div>
      </div>
    </div>
  );
}
