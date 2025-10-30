import { useState, useEffect } from 'react';
import { getApiUrl } from '../../config';

interface BookLine {
  id: number;
  bookmaker: string;
  line: string;
  timestamp: string;
}

interface LiveSteamMove {
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  market_type: string;
  side: string;
  original_line: number;
  new_line: number;
  movement: number;
  books_moved: number;
  consensus_percent: number;
  timestamp: string;
}

export function SteamMoveDetector() {
  const [gameInfo, setGameInfo] = useState<string>('');
  const [marketType, setMarketType] = useState<'spread' | 'total' | 'moneyline'>('spread');
  const [bookLines, setBookLines] = useState<BookLine[]>([]);
  const [newBookmaker, setNewBookmaker] = useState<string>('');
  const [newLine, setNewLine] = useState<string>('');
  const [liveSteamMoves, setLiveSteamMoves] = useState<LiveSteamMove[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    const fetchLiveSteamMoves = async () => {
      try {
        const response = await fetch(getApiUrl('alerts/steam-moves'));
        if (response.ok) {
          const data = await response.json();
          setLiveSteamMoves(data.alerts || []);
        }
      } catch (error) {
        console.error('Error fetching live steam moves:', error);
      }
    };

    fetchLiveSteamMoves();
    if (autoRefresh) {
      const interval = setInterval(fetchLiveSteamMoves, 10000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  const getSportBadge = (sport: string) => {
    const colors: Record<string, string> = {
      'basketball_nba': 'bg-orange-500',
      'americanfootball_nfl': 'bg-green-600',
      'icehockey_nhl': 'bg-blue-600',
    };
    const labels: Record<string, string> = {
      'basketball_nba': 'NBA',
      'americanfootball_nfl': 'NFL',
      'icehockey_nhl': 'NHL',
    };
    return <span className={`${colors[sport] || 'bg-gray-600'} text-white text-xs px-2 py-1 rounded font-semibold`}>{labels[sport] || sport}</span>;
  };

  const getMarketLabel = (marketType: string) => {
    const labels: Record<string, string> = {
      'h2h': 'Moneyline',
      'spreads': 'Spread',
      'totals': 'Total',
    };
    return labels[marketType] || marketType;
  };

  const addBookLine = () => {
    if (!newBookmaker || !newLine) {
      alert('Please enter bookmaker and line');
      return;
    }

    const entry: BookLine = {
      id: Date.now(),
      bookmaker: newBookmaker,
      line: newLine,
      timestamp: new Date().toLocaleTimeString(),
    };

    setBookLines([...bookLines, entry]);
    setNewBookmaker('');
    setNewLine('');
  };

  const removeBookLine = (id: number) => {
    setBookLines(bookLines.filter(line => line.id !== id));
  };

  const detectSteam = () => {
    if (bookLines.length < 3) return null;

    // Get all numeric lines
    const numericLines = bookLines
      .map(bl => parseFloat(bl.line))
      .filter(line => !isNaN(line));

    if (numericLines.length < 3) return null;

    // Calculate line variance
    const mean = numericLines.reduce((a, b) => a + b, 0) / numericLines.length;
    const variance = numericLines.reduce((sum, line) => sum + Math.pow(line - mean, 2), 0) / numericLines.length;
    const stdDev = Math.sqrt(variance);

    // Calculate line spread (max - min)
    const lineSpread = Math.max(...numericLines) - Math.min(...numericLines);

    // Detect if lines are moving in same direction rapidly
    const lineChanges = numericLines.slice(1).map((line, i) => line - numericLines[i]);
    const movingUp = lineChanges.filter(change => change > 0).length;
    const movingDown = lineChanges.filter(change => change < 0).length;
    const totalMoves = lineChanges.length;

    // Steam detected if:
    // 1. Lines are tightly clustered (low spread) AND
    // 2. Most books moving in same direction (70%+)
    const isSteam = lineSpread <= 1.5 && (
      (movingUp / totalMoves >= 0.7) || (movingDown / totalMoves >= 0.7)
    );

    const steamDirection = movingUp > movingDown ? 'up' : 'down';

    return {
      isSteam,
      lineSpread,
      stdDev,
      mean,
      steamDirection,
      consensus: ((Math.max(movingUp, movingDown) / totalMoves) * 100).toFixed(0),
      outliers: bookLines.filter(bl => {
        const line = parseFloat(bl.line);
        return !isNaN(line) && Math.abs(line - mean) > stdDev * 1.5;
      }),
    };
  };

  const reset = () => {
    setGameInfo('');
    setMarketType('spread');
    setBookLines([]);
    setNewBookmaker('');
    setNewLine('');
  };

  const steamAnalysis = detectSteam();

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-white">Steam Move Detector</h2>
          <p className="text-slate-400 text-sm mt-1">
            Detect when sharp money hits the market by tracking synchronized line moves across multiple books
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-slate-400">Live</span>
          </div>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
              autoRefresh
                ? 'bg-green-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          </button>
        </div>
      </div>

      {/* Live Steam Moves */}
      {liveSteamMoves.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-white mb-3">🔥 Live Steam Moves ({liveSteamMoves.length})</h3>
          <div className="space-y-3">
            {liveSteamMoves.slice(0, 5).map((move, index) => (
              <div key={index} className="bg-red-900/30 border-2 border-red-500 rounded-lg p-4 animate-pulse">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      {getSportBadge(move.sport)}
                      <span className="text-white font-semibold">
                        {move.away_team} @ {move.home_team}
                      </span>
                    </div>
                    <div className="text-sm text-slate-300">
                      {getMarketLabel(move.market_type)} • {move.side}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-slate-400">{formatTime(move.timestamp)}</div>
                    <div className="text-2xl mt-1">🚨</div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3 mt-3">
                  <div className="bg-slate-900/50 rounded p-2">
                    <div className="text-xs text-slate-400">Line Movement</div>
                    <div className="text-lg font-bold text-white">
                      {move.original_line} → {move.new_line}
                    </div>
                    <div className={`text-sm font-semibold ${move.movement > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {move.movement > 0 ? '+' : ''}{move.movement}
                    </div>
                  </div>

                  <div className="bg-slate-900/50 rounded p-2">
                    <div className="text-xs text-slate-400">Books Moved</div>
                    <div className="text-lg font-bold text-white">{move.books_moved}</div>
                    <div className="text-xs text-slate-400">sportsbooks</div>
                  </div>

                  <div className="bg-slate-900/50 rounded p-2">
                    <div className="text-xs text-slate-400">Consensus</div>
                    <div className="text-lg font-bold text-green-400">{move.consensus_percent}%</div>
                    <div className="text-xs text-slate-400">agreement</div>
                  </div>
                </div>

                <div className="mt-3 bg-green-900/30 border border-green-700/50 rounded p-2">
                  <div className="text-sm text-green-400 font-semibold">
                    💡 Sharp Money Alert: {move.consensus_percent}% of books moving {move.movement > 0 ? 'up' : 'down'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Manual Calculator Section */}
      <div className="border-t border-slate-700 pt-6">
        <h3 className="text-lg font-semibold text-white mb-4">Manual Calculator</h3>
        <div className="space-y-4">
        {/* Game Info */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Game Info (Optional)
          </label>
          <input
            type="text"
            value={gameInfo}
            onChange={(e) => setGameInfo(e.target.value)}
            placeholder="e.g., Lakers vs Celtics"
            className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Market Type */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Market Type
          </label>
          <div className="flex gap-3">
            {(['spread', 'total', 'moneyline'] as const).map(type => (
              <button
                key={type}
                onClick={() => setMarketType(type)}
                className={`px-4 py-2 rounded font-medium transition-colors capitalize ${
                  marketType === type
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        {/* Add Book Line */}
        <div className="bg-slate-700 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">Add Sportsbook Line</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <input
              type="text"
              value={newBookmaker}
              onChange={(e) => setNewBookmaker(e.target.value)}
              placeholder="Bookmaker"
              className="bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
            <input
              type="text"
              value={newLine}
              onChange={(e) => setNewLine(e.target.value)}
              placeholder={marketType === 'spread' ? '-3.5' : marketType === 'total' ? '225.5' : '-150'}
              className="bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
            <button
              onClick={addBookLine}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium transition-colors"
            >
              Add Line
            </button>
          </div>
        </div>

        {/* Current Lines */}
        {bookLines.length > 0 && (
          <div className="bg-slate-700 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">
              Current Lines ({bookLines.length} books)
            </h3>
            <div className="space-y-2">
              {bookLines.map(entry => (
                <div key={entry.id} className="flex items-center justify-between bg-slate-600 rounded px-4 py-2">
                  <div className="flex items-center gap-4">
                    <span className="text-white font-medium w-32">{entry.bookmaker}</span>
                    <span className="text-blue-400 font-bold text-lg">{entry.line}</span>
                    <span className="text-xs text-slate-400">{entry.timestamp}</span>
                  </div>
                  <button
                    onClick={() => removeBookLine(entry.id)}
                    className="text-red-400 hover:text-red-300 text-sm"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Steam Detection */}
        {steamAnalysis && bookLines.length >= 3 && (
          <div className="space-y-4">
            {/* Steam Alert */}
            <div className={`rounded-lg p-4 ${
              steamAnalysis.isSteam
                ? 'bg-red-900/30 border-2 border-red-500 animate-pulse'
                : 'bg-slate-700'
            }`}>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-white mb-1">
                    {steamAnalysis.isSteam ? '🚨 STEAM MOVE DETECTED!' : 'No Steam Detected'}
                  </h3>
                  {steamAnalysis.isSteam && (
                    <p className="text-sm text-slate-300">
                      {steamAnalysis.consensus}% of books moving {steamAnalysis.steamDirection}
                    </p>
                  )}
                </div>
                {steamAnalysis.isSteam && (
                  <div className="text-5xl">🔥</div>
                )}
              </div>
            </div>

            {/* Market Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-700 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Average Line</div>
                <div className="text-2xl font-bold text-white">{steamAnalysis.mean.toFixed(2)}</div>
              </div>

              <div className="bg-slate-700 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Line Spread</div>
                <div className={`text-2xl font-bold ${
                  steamAnalysis.lineSpread <= 1.0 ? 'text-green-400' :
                  steamAnalysis.lineSpread <= 2.0 ? 'text-yellow-400' : 'text-red-400'
                }`}>
                  {steamAnalysis.lineSpread.toFixed(1)}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {steamAnalysis.lineSpread <= 1.0 ? 'Tight' :
                   steamAnalysis.lineSpread <= 2.0 ? 'Normal' : 'Wide'}
                </div>
              </div>

              <div className="bg-slate-700 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Consensus</div>
                <div className={`text-2xl font-bold ${
                  parseInt(steamAnalysis.consensus) >= 70 ? 'text-green-400' : 'text-slate-300'
                }`}>
                  {steamAnalysis.consensus}%
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {steamAnalysis.steamDirection === 'up' ? '↑ Moving Up' : '↓ Moving Down'}
                </div>
              </div>
            </div>

            {/* Outlier Books */}
            {steamAnalysis.outliers.length > 0 && (
              <div className="bg-amber-900/30 border border-amber-700/50 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-amber-400 mb-2">
                  ⚠️ Outlier Books (Potential Value)
                </h4>
                <div className="space-y-2">
                  {steamAnalysis.outliers.map(outlier => (
                    <div key={outlier.id} className="flex items-center justify-between">
                      <span className="text-white font-medium">{outlier.bookmaker}</span>
                      <span className="text-amber-400 font-bold">{outlier.line}</span>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-slate-400 mt-2">
                  These books haven't moved yet - potential value before they adjust
                </p>
              </div>
            )}

            {/* Action Recommendation */}
            {steamAnalysis.isSteam && (
              <div className="bg-green-900/30 border border-green-700/50 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-green-400 mb-2">💡 Action Items</h4>
                <ul className="text-sm text-slate-300 space-y-1">
                  <li>• Sharp money is hitting the {steamAnalysis.steamDirection === 'up' ? 'over/favorite' : 'under/dog'}</li>
                  <li>• Books are adjusting lines rapidly in response</li>
                  <li>• Consider following the steam if you agree with sharp action</li>
                  <li>• Act quickly - outlier books will adjust soon</li>
                  {steamAnalysis.outliers.length > 0 && (
                    <li>• Best value at: <strong>{steamAnalysis.outliers[0].bookmaker}</strong></li>
                  )}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={reset}
            className="bg-slate-700 hover:bg-slate-600 text-white px-6 py-2 rounded font-medium transition-colors"
          >
            Reset
          </button>
        </div>

        {/* Instructions */}
        {bookLines.length < 3 && (
          <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-blue-400 mb-2">What is a steam move?</h4>
            <p className="text-sm text-slate-300 mb-3">
              A steam move occurs when sharp money hits the market and multiple sportsbooks
              simultaneously adjust their lines in the same direction.
            </p>
            <h5 className="text-sm font-semibold text-blue-400 mb-2">How to use:</h5>
            <ul className="text-sm text-slate-300 space-y-1">
              <li>1. Add current lines from at least 3-5 major sportsbooks</li>
              <li>2. Watch for tight line spreads (all books within 1-1.5 points)</li>
              <li>3. Look for 70%+ consensus movement in one direction</li>
              <li>4. Act on outlier books before they adjust</li>
            </ul>
          </div>
        )}
        </div>
      </div>
    </div>
  );
}
