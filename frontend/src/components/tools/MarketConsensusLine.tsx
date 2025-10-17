import { useState } from 'react';

interface BookOdds {
  id: number;
  bookmaker: string;
  line: string;
  isSharp: boolean;
}

export function MarketConsensusLine() {
  const [marketType, setMarketType] = useState<'spread' | 'total' | 'moneyline'>('spread');
  const [bookOdds, setBookOdds] = useState<BookOdds[]>([]);
  const [newBookmaker, setNewBookmaker] = useState<string>('');
  const [newLine, setNewLine] = useState<string>('');
  const [isSharpBook, setIsSharpBook] = useState<boolean>(false);

  const sharpBooks = ['Pinnacle', 'Bookmaker.eu', 'Heritage', 'CRIS', 'Circa'];

  const addOdds = () => {
    if (!newBookmaker || !newLine) {
      alert('Please enter bookmaker and line');
      return;
    }

    const entry: BookOdds = {
      id: Date.now(),
      bookmaker: newBookmaker,
      line: newLine,
      isSharp: isSharpBook || sharpBooks.some(sharp =>
        newBookmaker.toLowerCase().includes(sharp.toLowerCase())
      ),
    };

    setBookOdds([...bookOdds, entry]);
    setNewBookmaker('');
    setNewLine('');
    setIsSharpBook(false);
  };

  const removeOdds = (id: number) => {
    setBookOdds(bookOdds.filter(odds => odds.id !== id));
  };

  const calculateConsensus = () => {
    if (bookOdds.length === 0) return null;

    const allLines = bookOdds
      .map(odds => parseFloat(odds.line))
      .filter(line => !isNaN(line));

    const sharpLines = bookOdds
      .filter(odds => odds.isSharp)
      .map(odds => parseFloat(odds.line))
      .filter(line => !isNaN(line));

    if (allLines.length === 0) return null;

    // Calculate market consensus (all books)
    const marketMean = allLines.reduce((a, b) => a + b, 0) / allLines.length;
    const marketMedian = [...allLines].sort((a, b) => a - b)[Math.floor(allLines.length / 2)];

    // Calculate sharp consensus (sharp books only)
    const sharpMean = sharpLines.length > 0
      ? sharpLines.reduce((a, b) => a + b, 0) / sharpLines.length
      : null;

    // Calculate line variance
    const variance = allLines.reduce((sum, line) =>
      sum + Math.pow(line - marketMean, 2), 0
    ) / allLines.length;
    const stdDev = Math.sqrt(variance);

    // Find outliers (more than 1.5 std dev from mean)
    const outliers = bookOdds.filter(odds => {
      const line = parseFloat(odds.line);
      return !isNaN(line) && Math.abs(line - marketMean) > stdDev * 1.5;
    });

    // Determine sharp vs public disagreement
    const sharpPublicDiff = sharpMean !== null ? Math.abs(sharpMean - marketMean) : 0;

    return {
      marketMean,
      marketMedian,
      sharpMean,
      sharpCount: sharpLines.length,
      totalBooks: allLines.length,
      stdDev,
      outliers,
      sharpPublicDiff,
      consensus: sharpMean !== null ? sharpMean : marketMean,
    };
  };

  const reset = () => {
    setMarketType('spread');
    setBookOdds([]);
    setNewBookmaker('');
    setNewLine('');
    setIsSharpBook(false);
  };

  const consensus = calculateConsensus();

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">Market Consensus Line</h2>
      <p className="text-slate-400 text-sm mb-6">
        Find the true sharp line by aggregating odds from market-making sportsbooks
      </p>

      <div className="space-y-4">
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

        {/* Add Bookmaker Odds */}
        <div className="bg-slate-700 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">Add Sportsbook Odds</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <input
              type="text"
              value={newBookmaker}
              onChange={(e) => setNewBookmaker(e.target.value)}
              placeholder="Bookmaker"
              list="sharp-books"
              className="bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
            <datalist id="sharp-books">
              {sharpBooks.map(book => (
                <option key={book} value={book} />
              ))}
            </datalist>
            <input
              type="text"
              value={newLine}
              onChange={(e) => setNewLine(e.target.value)}
              placeholder={marketType === 'spread' ? '-3.5' : marketType === 'total' ? '225.5' : '-150'}
              className="bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
            <label className="flex items-center gap-2 text-white cursor-pointer">
              <input
                type="checkbox"
                checked={isSharpBook}
                onChange={(e) => setIsSharpBook(e.target.checked)}
                className="w-4 h-4"
              />
              Sharp Book
            </label>
            <button
              onClick={addOdds}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium transition-colors"
            >
              Add
            </button>
          </div>
          <p className="text-xs text-slate-400 mt-2">
            Sharp books: {sharpBooks.join(', ')}
          </p>
        </div>

        {/* Current Odds */}
        {bookOdds.length > 0 && (
          <div className="bg-slate-700 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">
              Current Odds ({bookOdds.length} books, {bookOdds.filter(b => b.isSharp).length} sharp)
            </h3>
            <div className="space-y-2">
              {bookOdds.map(entry => (
                <div key={entry.id} className="flex items-center justify-between bg-slate-600 rounded px-4 py-2">
                  <div className="flex items-center gap-4">
                    <span className={`text-white font-medium w-40 ${
                      entry.isSharp ? 'flex items-center gap-2' : ''
                    }`}>
                      {entry.bookmaker}
                      {entry.isSharp && (
                        <span className="text-xs px-2 py-0.5 bg-green-900/50 text-green-300 rounded">
                          SHARP
                        </span>
                      )}
                    </span>
                    <span className={`font-bold text-lg ${
                      entry.isSharp ? 'text-green-400' : 'text-blue-400'
                    }`}>
                      {entry.line}
                    </span>
                  </div>
                  <button
                    onClick={() => removeOdds(entry.id)}
                    className="text-red-400 hover:text-red-300 text-sm"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Consensus Analysis */}
        {consensus && bookOdds.length >= 3 && (
          <div className="space-y-4">
            {/* Main Consensus */}
            <div className="bg-gradient-to-br from-green-900/30 to-blue-900/30 border-2 border-green-600 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-2">True Market Line</h3>
              <div className="text-5xl font-bold text-green-400 mb-2">
                {consensus.consensus.toFixed(1)}
              </div>
              <p className="text-sm text-slate-300">
                {consensus.sharpMean !== null
                  ? `Based on ${consensus.sharpCount} sharp book${consensus.sharpCount > 1 ? 's' : ''}`
                  : `Based on all ${consensus.totalBooks} books (no sharp books added)`
                }
              </p>
            </div>

            {/* Statistics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-700 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Market Mean</div>
                <div className="text-2xl font-bold text-white">{consensus.marketMean.toFixed(2)}</div>
                <div className="text-xs text-slate-400 mt-1">All {consensus.totalBooks} books</div>
              </div>

              {consensus.sharpMean !== null && (
                <div className="bg-slate-700 rounded-lg p-4">
                  <div className="text-sm text-slate-400 mb-1">Sharp Mean</div>
                  <div className="text-2xl font-bold text-green-400">{consensus.sharpMean.toFixed(2)}</div>
                  <div className="text-xs text-slate-400 mt-1">{consensus.sharpCount} sharp books</div>
                </div>
              )}

              <div className="bg-slate-700 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Market Median</div>
                <div className="text-2xl font-bold text-white">{consensus.marketMedian.toFixed(2)}</div>
                <div className="text-xs text-slate-400 mt-1">Middle value</div>
              </div>
            </div>

            {/* Sharp vs Public Disagreement */}
            {consensus.sharpMean !== null && consensus.sharpPublicDiff > 0.5 && (
              <div className="bg-amber-900/30 border border-amber-700/50 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-amber-400 mb-2">
                  ⚠️ Sharp/Public Disagreement
                </h4>
                <p className="text-sm text-slate-300">
                  Sharp books differ from public market by{' '}
                  <span className="font-bold">{consensus.sharpPublicDiff.toFixed(1)} points</span>.
                  This indicates sharp money on the {consensus.sharpMean > consensus.marketMean ? 'over/favorite' : 'under/dog'}.
                </p>
              </div>
            )}

            {/* Outlier Books */}
            {consensus.outliers.length > 0 && (
              <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-blue-400 mb-2">
                  📊 Outlier Books (Potential Value)
                </h4>
                <div className="space-y-2">
                  {consensus.outliers.map(outlier => {
                    const line = parseFloat(outlier.line);
                    const diff = line - consensus.consensus;
                    return (
                      <div key={outlier.id} className="flex items-center justify-between">
                        <span className="text-white font-medium">{outlier.bookmaker}</span>
                        <div className="flex items-center gap-3">
                          <span className="text-blue-400 font-bold">{outlier.line}</span>
                          <span className={`text-sm ${diff > 0 ? 'text-green-400' : 'text-red-400'}`}>
                            ({diff > 0 ? '+' : ''}{diff.toFixed(1)})
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Recommendation */}
            <div className="bg-green-900/30 border border-green-700/50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-green-400 mb-2">💡 How to use this:</h4>
              <ul className="text-sm text-slate-300 space-y-1">
                <li>• The consensus line ({consensus.consensus.toFixed(1)}) is the "true" market price</li>
                <li>• Compare your local sportsbook's line to the consensus</li>
                <li>• If your book is 1.5+ points different, you may have value</li>
                <li>• Trust sharp books (Pinnacle, etc.) over public books (DraftKings, FanDuel)</li>
                {consensus.outliers.length > 0 && (
                  <li>• Outlier books above may offer +EV opportunities</li>
                )}
              </ul>
            </div>
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
        {bookOdds.length < 3 && (
          <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-blue-400 mb-2">What is market consensus?</h4>
            <p className="text-sm text-slate-300 mb-3">
              The market consensus line represents the "true" odds by aggregating lines from
              sharp sportsbooks that set efficient markets. Use this to find value at recreational books.
            </p>
            <h5 className="text-sm font-semibold text-blue-400 mb-2">How to use:</h5>
            <ul className="text-sm text-slate-300 space-y-1">
              <li>1. Add lines from at least 3-5 sportsbooks</li>
              <li>2. Mark sharp books (Pinnacle, Circa, Heritage, etc.)</li>
              <li>3. The tool will calculate the consensus line weighted toward sharp books</li>
              <li>4. Compare your local book's line to find discrepancies</li>
              <li>5. Bet when your book is 1.5+ points off the consensus</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
