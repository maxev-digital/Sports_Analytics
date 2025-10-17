import { useState } from 'react';

interface BetRecord {
  id: number;
  game: string;
  date: string;
  betLine: string;
  closingLine: string;
  result: 'win' | 'loss' | 'push' | 'pending';
  stake: number;
}

export function ClosingLineValueTracker() {
  const [bets, setBets] = useState<BetRecord[]>([]);
  const [game, setGame] = useState<string>('');
  const [betLine, setBetLine] = useState<string>('');
  const [closingLine, setClosingLine] = useState<string>('');
  const [result, setResult] = useState<'win' | 'loss' | 'push' | 'pending'>('pending');
  const [stake, setStake] = useState<string>('100');

  const addBet = () => {
    if (!game || !betLine || !closingLine) {
      alert('Please enter game, bet line, and closing line');
      return;
    }

    const record: BetRecord = {
      id: Date.now(),
      game,
      date: new Date().toLocaleDateString(),
      betLine,
      closingLine,
      result,
      stake: parseFloat(stake),
    };

    setBets([...bets, record]);
    setGame('');
    setBetLine('');
    setClosingLine('');
    setResult('pending');
    setStake('100');
  };

  const removeBet = (id: number) => {
    setBets(bets.filter(bet => bet.id !== id));
  };

  const updateBetResult = (id: number, newResult: 'win' | 'loss' | 'push' | 'pending') => {
    setBets(bets.map(bet =>
      bet.id === id ? { ...bet, result: newResult } : bet
    ));
  };

  const calculateCLV = () => {
    if (bets.length === 0) return null;

    // Calculate CLV for each bet
    const clvBets = bets.map(bet => {
      const betNum = parseFloat(bet.betLine);
      const closeNum = parseFloat(bet.closingLine);

      if (isNaN(betNum) || isNaN(closeNum)) {
        return { ...bet, clv: 0, clvPct: 0, beatClosing: false };
      }

      const clv = closeNum - betNum;
      const clvPct = (clv / Math.abs(betNum)) * 100;
      const beatClosing = Math.abs(clv) >= 0.5; // Beat by at least 0.5 points

      return { ...bet, clv, clvPct, beatClosing };
    });

    // Calculate statistics
    const totalBets = clvBets.length;
    const betsBeatingClosing = clvBets.filter(b => b.beatClosing).length;
    const clvWinRate = (betsBeatingClosing / totalBets) * 100;

    const avgCLV = clvBets.reduce((sum, b) => sum + b.clv, 0) / totalBets;
    const avgCLVPct = clvBets.reduce((sum, b) => sum + b.clvPct, 0) / totalBets;

    // Calculate actual win rate
    const settledBets = clvBets.filter(b => b.result !== 'pending' && b.result !== 'push');
    const wins = settledBets.filter(b => b.result === 'win').length;
    const actualWinRate = settledBets.length > 0 ? (wins / settledBets.length) * 100 : 0;

    // Calculate profit/loss
    const totalStaked = clvBets.reduce((sum, b) => sum + b.stake, 0);
    const profit = clvBets.reduce((sum, b) => {
      if (b.result === 'win') return sum + (b.stake * 0.91); // Assuming -110 odds
      if (b.result === 'loss') return sum - b.stake;
      return sum;
    }, 0);
    const roi = totalStaked > 0 ? (profit / totalStaked) * 100 : 0;

    return {
      totalBets,
      betsBeatingClosing,
      clvWinRate,
      avgCLV,
      avgCLVPct,
      actualWinRate,
      settledCount: settledBets.length,
      wins,
      losses: settledBets.length - wins,
      profit,
      roi,
      clvBets,
    };
  };

  const reset = () => {
    setBets([]);
  };

  const stats = calculateCLV();

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">Closing Line Value (CLV) Tracker</h2>
      <p className="text-slate-400 text-sm mb-6">
        Track your bets vs closing lines to measure long-term betting skill
      </p>

      <div className="space-y-4">
        {/* Add Bet */}
        <div className="bg-slate-700 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">Add Bet</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
            <input
              type="text"
              value={game}
              onChange={(e) => setGame(e.target.value)}
              placeholder="Game (e.g., Lakers vs Celtics)"
              className="bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
            <input
              type="text"
              value={betLine}
              onChange={(e) => setBetLine(e.target.value)}
              placeholder="Your Bet Line (e.g., -3.5 or 225.5)"
              className="bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
            <input
              type="text"
              value={closingLine}
              onChange={(e) => setClosingLine(e.target.value)}
              placeholder="Closing Line"
              className="bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
            <input
              type="number"
              value={stake}
              onChange={(e) => setStake(e.target.value)}
              placeholder="Stake ($)"
              className="bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div className="flex gap-3 items-center">
            <label className="text-sm text-slate-300">Result:</label>
            <select
              value={result}
              onChange={(e) => setResult(e.target.value as any)}
              className="bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
            >
              <option value="pending">Pending</option>
              <option value="win">Win</option>
              <option value="loss">Loss</option>
              <option value="push">Push</option>
            </select>
            <button
              onClick={addBet}
              className="ml-auto bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded font-medium transition-colors"
            >
              Add Bet
            </button>
          </div>
        </div>

        {/* Statistics */}
        {stats && stats.totalBets > 0 && (
          <div className="space-y-4">
            {/* Main CLV Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className={`rounded-lg p-4 ${
                stats.clvWinRate >= 60 ? 'bg-green-900/30 border border-green-700/50' :
                stats.clvWinRate >= 50 ? 'bg-yellow-900/30 border border-yellow-700/50' :
                'bg-red-900/30 border border-red-700/50'
              }`}>
                <div className="text-sm text-slate-400 mb-1">CLV Win Rate</div>
                <div className={`text-3xl font-bold ${
                  stats.clvWinRate >= 60 ? 'text-green-400' :
                  stats.clvWinRate >= 50 ? 'text-yellow-400' : 'text-red-400'
                }`}>
                  {stats.clvWinRate.toFixed(1)}%
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {stats.betsBeatingClosing} of {stats.totalBets} beat closing
                </div>
              </div>

              <div className="bg-slate-700 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Avg CLV</div>
                <div className={`text-3xl font-bold ${
                  stats.avgCLV > 0 ? 'text-green-400' : stats.avgCLV < 0 ? 'text-red-400' : 'text-slate-300'
                }`}>
                  {stats.avgCLV > 0 ? '+' : ''}{stats.avgCLV.toFixed(2)}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {stats.avgCLVPct > 0 ? '+' : ''}{stats.avgCLVPct.toFixed(1)}% average
                </div>
              </div>

              <div className="bg-slate-700 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Actual Win Rate</div>
                <div className={`text-3xl font-bold ${
                  stats.actualWinRate >= 52.4 ? 'text-green-400' :
                  stats.actualWinRate >= 50 ? 'text-yellow-400' : 'text-red-400'
                }`}>
                  {stats.actualWinRate.toFixed(1)}%
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {stats.wins}-{stats.losses} ({stats.settledCount} settled)
                </div>
              </div>
            </div>

            {/* Profit/Loss */}
            <div className={`rounded-lg p-4 ${
              stats.roi > 0 ? 'bg-green-900/30 border border-green-700/50' :
              'bg-red-900/30 border border-red-700/50'
            }`}>
              <div className="flex justify-between items-center">
                <div>
                  <div className="text-sm text-slate-400 mb-1">Total Profit/Loss</div>
                  <div className={`text-3xl font-bold ${
                    stats.profit > 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {stats.profit > 0 ? '+' : ''}${stats.profit.toFixed(2)}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-slate-400 mb-1">ROI</div>
                  <div className={`text-2xl font-bold ${
                    stats.roi > 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {stats.roi > 0 ? '+' : ''}{stats.roi.toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>

            {/* Bet History */}
            <div className="bg-slate-700 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-300 mb-3">Bet History</h3>
              <div className="space-y-2">
                {stats.clvBets.map(bet => (
                  <div key={bet.id} className="bg-slate-600 rounded px-4 py-3">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="text-white font-medium">{bet.game}</div>
                        <div className="text-xs text-slate-400">{bet.date}</div>
                      </div>
                      <div className="flex gap-2">
                        <select
                          value={bet.result}
                          onChange={(e) => updateBetResult(bet.id, e.target.value as any)}
                          className="text-xs bg-slate-700 border border-slate-500 rounded px-2 py-1 text-white"
                        >
                          <option value="pending">Pending</option>
                          <option value="win">Win</option>
                          <option value="loss">Loss</option>
                          <option value="push">Push</option>
                        </select>
                        <button
                          onClick={() => removeBet(bet.id)}
                          className="text-red-400 hover:text-red-300 text-xs"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <div className="text-slate-400 text-xs">Your Line</div>
                        <div className="text-white font-medium">{bet.betLine}</div>
                      </div>
                      <div>
                        <div className="text-slate-400 text-xs">Closing Line</div>
                        <div className="text-white font-medium">{bet.closingLine}</div>
                      </div>
                      <div>
                        <div className="text-slate-400 text-xs">CLV</div>
                        <div className={`font-bold ${
                          bet.clv > 0 ? 'text-green-400' : bet.clv < 0 ? 'text-red-400' : 'text-slate-300'
                        }`}>
                          {bet.clv > 0 ? '+' : ''}{bet.clv.toFixed(1)}
                          {bet.beatClosing && ' ✓'}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Analysis */}
            <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-blue-400 mb-2">What does this mean?</h4>
              <ul className="text-sm text-slate-300 space-y-1">
                <li>
                  • <strong>CLV Win Rate:</strong> {stats.clvWinRate >= 60 ? 'Excellent! You consistently beat the closing line.' :
                    stats.clvWinRate >= 50 ? 'Good. You\'re finding value more often than not.' :
                    'Needs improvement. Focus on finding better lines earlier.'}
                </li>
                <li>
                  • <strong>Average CLV:</strong> {stats.avgCLV > 1 ? 'You\'re consistently getting great value!' :
                    stats.avgCLV > 0 ? 'You\'re getting value on average.' :
                    'You\'re betting into closing lines. Wait for better numbers.'}
                </li>
                <li>
                  • <strong>Win Rate vs CLV:</strong> {stats.actualWinRate > stats.clvWinRate ?
                    'You\'re running hot! Results better than expected.' :
                    stats.actualWinRate < stats.clvWinRate ?
                    'You\'re running cold. Keep betting - CLV predicts long-term success.' :
                    'Results align with CLV. Keep doing what you\'re doing!'}
                </li>
              </ul>
            </div>
          </div>
        )}

        {/* Buttons */}
        <div className="flex gap-3">
          {bets.length > 0 && (
            <button
              onClick={reset}
              className="bg-slate-700 hover:bg-slate-600 text-white px-6 py-2 rounded font-medium transition-colors"
            >
              Reset
            </button>
          )}
        </div>

        {/* Instructions */}
        {bets.length === 0 && (
          <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-blue-400 mb-2">Why track CLV?</h4>
            <p className="text-sm text-slate-300 mb-3">
              Closing Line Value is the #1 indicator of long-term betting success. If you consistently
              beat the closing line, you will be profitable long-term, even if you're currently losing.
            </p>
            <h5 className="text-sm font-semibold text-blue-400 mb-2">How to use:</h5>
            <ul className="text-sm text-slate-300 space-y-1">
              <li>1. Enter your bet line when you place the bet</li>
              <li>2. Enter the closing line (line right before game starts)</li>
              <li>3. Update the result after the game</li>
              <li>4. Aim for 55%+ CLV win rate</li>
              <li>5. Focus on CLV, not short-term results</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
