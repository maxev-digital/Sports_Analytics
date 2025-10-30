import { useState, useEffect } from 'react';
import { getApiUrl } from '../../config';

interface LineEntry {
  id: number;
  timestamp: string;
  line: string;
  bookmaker: string;
}

interface LiveLineMovement {
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  market_type: string;
  bookmaker: string;
  original_line: number;
  new_line: number;
  movement: number;
  movement_percent: number;
  timestamp: string;
}

export function LineMovementTracker() {
  const [gameInfo, setGameInfo] = useState<string>('');
  const [marketType, setMarketType] = useState<'spread' | 'total' | 'moneyline'>('spread');
  const [lines, setLines] = useState<LineEntry[]>([]);
  const [newLine, setNewLine] = useState<string>('');
  const [newBookmaker, setNewBookmaker] = useState<string>('');
  const [liveLineMovements, setLiveLineMovements] = useState<LiveLineMovement[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    const fetchLiveLineMovements = async () => {
      try {
        const response = await fetch(getApiUrl('alerts/line-movements'));
        if (response.ok) {
          const data = await response.json();
          setLiveLineMovements(data.alerts || []);
        }
      } catch (error) {
        console.error('Error fetching live line movements:', error);
      }
    };

    fetchLiveLineMovements();
    if (autoRefresh) {
      const interval = setInterval(fetchLiveLineMovements, 10000);
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

  const addLine = () => {
    if (!newLine || !newBookmaker) {
      alert('Please enter both line and bookmaker');
      return;
    }

    const entry: LineEntry = {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString(),
      line: newLine,
      bookmaker: newBookmaker,
    };

    setLines([...lines, entry]);
    setNewLine('');
    setNewBookmaker('');
  };

  const removeLine = (id: number) => {
    setLines(lines.filter(line => line.id !== id));
  };

  const reset = () => {
    setGameInfo('');
    setMarketType('spread');
    setLines([]);
    setNewLine('');
    setNewBookmaker('');
  };

  const getLineDirection = () => {
    if (lines.length < 2) return null;

    const firstLine = parseFloat(lines[0].line);
    const lastLine = parseFloat(lines[lines.length - 1].line);

    if (isNaN(firstLine) || isNaN(lastLine)) return null;

    const movement = lastLine - firstLine;
    return {
      direction: movement > 0 ? 'up' : movement < 0 ? 'down' : 'stable',
      amount: Math.abs(movement),
      percentage: ((movement / firstLine) * 100).toFixed(1),
    };
  };

  const getMarketAnalysis = () => {
    const direction = getLineDirection();
    if (!direction || !lines.length) return null;

    const analysis = [];

    if (marketType === 'spread') {
      if (direction.direction === 'down') {
        analysis.push('Line moving towards favorite (sharp money on favorite)');
        analysis.push('Public likely on underdog');
      } else if (direction.direction === 'up') {
        analysis.push('Line moving towards underdog (sharp money on underdog)');
        analysis.push('Public likely on favorite');
      } else {
        analysis.push('Balanced action on both sides');
      }
    } else if (marketType === 'total') {
      if (direction.direction === 'up') {
        analysis.push('Total rising (sharp money on Over)');
        analysis.push('Books adjusting to attract Under money');
      } else if (direction.direction === 'down') {
        analysis.push('Total falling (sharp money on Under)');
        analysis.push('Books adjusting to attract Over money');
      } else {
        analysis.push('Balanced action on Over/Under');
      }
    }

    return analysis;
  };

  const direction = getLineDirection();
  const analysis = getMarketAnalysis();

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-white">Line Movement Tracker</h2>
          <p className="text-slate-400 text-sm mt-1">
            Track how betting lines move across sportsbooks to identify sharp money
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

      {/* Live Line Movements */}
      {liveLineMovements.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-white mb-3">📊 Live Line Movements ({liveLineMovements.length})</h3>
          <div className="space-y-3">
            {liveLineMovements.slice(0, 5).map((movement, index) => (
              <div key={index} className={`rounded-lg p-4 border-2 ${
                Math.abs(movement.movement) >= 2
                  ? 'bg-amber-900/30 border-amber-500'
                  : 'bg-slate-700 border-slate-600'
              }`}>
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      {getSportBadge(movement.sport)}
                      <span className="text-white font-semibold">
                        {movement.away_team} @ {movement.home_team}
                      </span>
                    </div>
                    <div className="text-sm text-slate-300">
                      {getMarketLabel(movement.market_type)} • {movement.bookmaker}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-slate-400">{formatTime(movement.timestamp)}</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 mt-3">
                  <div className="bg-slate-900/50 rounded p-3">
                    <div className="text-xs text-slate-400 mb-1">Line Movement</div>
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-white">{movement.original_line}</span>
                      <span className="text-slate-500">→</span>
                      <span className="text-lg font-bold text-white">{movement.new_line}</span>
                    </div>
                    <div className={`text-sm font-semibold mt-1 ${
                      movement.movement > 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {movement.movement > 0 ? '+' : ''}{movement.movement}
                    </div>
                  </div>

                  <div className="bg-slate-900/50 rounded p-3">
                    <div className="text-xs text-slate-400 mb-1">Movement %</div>
                    <div className={`text-2xl font-bold ${
                      Math.abs(movement.movement_percent) >= 5 ? 'text-amber-400' : 'text-white'
                    }`}>
                      {movement.movement_percent > 0 ? '+' : ''}{movement.movement_percent}%
                    </div>
                    {Math.abs(movement.movement) >= 2 && (
                      <div className="text-xs text-amber-400 mt-1">Significant Move</div>
                    )}
                  </div>
                </div>

                {Math.abs(movement.movement) >= 2 && (
                  <div className="mt-3 bg-blue-900/30 border border-blue-700/50 rounded p-2">
                    <div className="text-sm text-blue-400 font-semibold">
                      💡 Sharp Money Indicator: {Math.abs(movement.movement)} point move detected
                    </div>
                  </div>
                )}
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
            placeholder="e.g., Lakers vs Celtics - Jan 15, 2025"
            className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Market Type */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Market Type
          </label>
          <div className="flex gap-3">
            <button
              onClick={() => setMarketType('spread')}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                marketType === 'spread'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Spread
            </button>
            <button
              onClick={() => setMarketType('total')}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                marketType === 'total'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Total
            </button>
            <button
              onClick={() => setMarketType('moneyline')}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                marketType === 'moneyline'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Moneyline
            </button>
          </div>
        </div>

        {/* Add Line Entry */}
        <div className="bg-slate-700 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">Add Line Reading</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <input
              type="text"
              value={newLine}
              onChange={(e) => setNewLine(e.target.value)}
              placeholder={marketType === 'spread' ? '-3.5' : marketType === 'total' ? '225.5' : '-150'}
              className="bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
            <input
              type="text"
              value={newBookmaker}
              onChange={(e) => setNewBookmaker(e.target.value)}
              placeholder="Bookmaker"
              className="bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
            <button
              onClick={addLine}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium transition-colors"
            >
              Add Reading
            </button>
          </div>
        </div>

        {/* Line History */}
        {lines.length > 0 && (
          <div className="bg-slate-700 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">Line History</h3>
            <div className="space-y-2">
              {lines.map((entry, index) => (
                <div key={entry.id} className="flex items-center justify-between bg-slate-600 rounded px-4 py-2">
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-slate-400 w-16">{entry.timestamp}</span>
                    <span className="text-white font-medium w-24">{entry.line}</span>
                    <span className="text-slate-300">{entry.bookmaker}</span>
                    {index > 0 && (
                      <span className={`text-xs px-2 py-1 rounded ${
                        parseFloat(entry.line) > parseFloat(lines[index - 1].line)
                          ? 'bg-green-900/50 text-green-300'
                          : parseFloat(entry.line) < parseFloat(lines[index - 1].line)
                          ? 'bg-red-900/50 text-red-300'
                          : 'bg-slate-700 text-slate-400'
                      }`}>
                        {parseFloat(entry.line) > parseFloat(lines[index - 1].line)
                          ? `↑ +${(parseFloat(entry.line) - parseFloat(lines[index - 1].line)).toFixed(1)}`
                          : parseFloat(entry.line) < parseFloat(lines[index - 1].line)
                          ? `↓ ${(parseFloat(entry.line) - parseFloat(lines[index - 1].line)).toFixed(1)}`
                          : '→ No change'
                        }
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => removeLine(entry.id)}
                    className="text-red-400 hover:text-red-300 text-sm"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Movement Analysis */}
        {direction && lines.length >= 2 && (
          <div className="space-y-4">
            <div className={`rounded-lg p-4 ${
              direction.direction === 'up'
                ? 'bg-green-900/30 border border-green-700/50'
                : direction.direction === 'down'
                ? 'bg-red-900/30 border border-red-700/50'
                : 'bg-slate-700'
            }`}>
              <h3 className="text-lg font-semibold text-white mb-2">Line Movement</h3>
              <div className="flex items-center gap-4">
                <div>
                  <div className="text-sm text-slate-400">Opening Line</div>
                  <div className="text-2xl font-bold text-white">{lines[0].line}</div>
                </div>
                <div className="text-3xl">→</div>
                <div>
                  <div className="text-sm text-slate-400">Current Line</div>
                  <div className="text-2xl font-bold text-white">{lines[lines.length - 1].line}</div>
                </div>
                <div className="ml-auto">
                  <div className={`text-2xl font-bold ${
                    direction.direction === 'up' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {direction.direction === 'up' ? '↑' : '↓'} {direction.amount}
                  </div>
                  <div className="text-sm text-slate-400">
                    {direction.direction === 'up' ? '+' : ''}{direction.percentage}%
                  </div>
                </div>
              </div>
            </div>

            {/* Analysis */}
            {analysis && (
              <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-blue-400 mb-2">Market Analysis</h4>
                <ul className="text-sm text-slate-300 space-y-1">
                  {analysis.map((point, index) => (
                    <li key={index}>• {point}</li>
                  ))}
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
        {lines.length === 0 && (
          <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-blue-400 mb-2">How to use:</h4>
            <ul className="text-sm text-slate-300 space-y-1">
              <li>1. Select market type (Spread, Total, or Moneyline)</li>
              <li>2. Add your first line reading with the bookmaker</li>
              <li>3. Continue adding readings as the line moves</li>
              <li>4. Watch for significant movement (2+ points for spreads/totals, 20+ for ML)</li>
              <li>5. Follow the sharp money - line movement against public betting indicates sharp action</li>
            </ul>
          </div>
        )}
        </div>
      </div>
    </div>
  );
}
