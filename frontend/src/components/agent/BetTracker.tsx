import { useState, useRef } from 'react';
import { useBetTracker, UserBet, BetLeg } from '../../hooks/useBetTracker';

interface BetTrackerProps {
  token: string | null;
}

const STATUS_STYLES: Record<string, string> = {
  pending: 'bg-yellow-900/40 text-yellow-300 border-yellow-700/50',
  won:     'bg-green-900/40 text-green-300 border-green-700/50',
  lost:    'bg-red-900/40 text-red-300 border-red-700/50',
  push:    'bg-slate-700/60 text-slate-300 border-slate-600/50',
  void:    'bg-slate-700/60 text-slate-400 border-slate-600/50',
};

const RESULT_DOT: Record<string, string> = {
  won:  'bg-green-400',
  lost: 'bg-red-400',
  push: 'bg-slate-400',
};

function formatOdds(odds: number | null): string {
  if (odds === null || odds === undefined) return '?';
  return odds > 0 ? `+${odds}` : `${odds}`;
}

function BetCard({ bet }: { bet: UserBet }) {
  const statusClass = STATUS_STYLES[bet.status] ?? STATUS_STYLES.pending;
  const isParlay = bet.legs.length > 1;

  return (
    <div className="border border-slate-700/60 rounded-lg p-3 bg-slate-800/40 space-y-2">
      {/* Header row */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 flex-wrap">
          {bet.book && (
            <span className="text-xs text-slate-500 font-medium">{bet.book}</span>
          )}
          <span className="text-xs text-slate-600">·</span>
          <span className="text-xs text-slate-400 capitalize">{bet.bet_type.replace(/_/g, ' ')}</span>
          {bet.game_date && (
            <>
              <span className="text-xs text-slate-600">·</span>
              <span className="text-xs text-slate-500">{bet.game_date}</span>
            </>
          )}
        </div>
        <span className={`text-xs font-bold px-2 py-0.5 rounded border capitalize flex-shrink-0 ${statusClass}`}>
          {bet.status}
        </span>
      </div>

      {/* Legs */}
      <div className="space-y-1.5">
        {bet.legs.map((leg: BetLeg, i: number) => (
          <div key={i} className="flex items-start gap-2">
            {isParlay && (
              <div className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${
                leg.result ? (RESULT_DOT[leg.result] ?? 'bg-yellow-400') : 'bg-yellow-400'
              }`} />
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-1">
                <span className="text-sm text-white font-medium truncate">{leg.pick ?? 'Unknown pick'}</span>
                <span className="text-xs text-slate-400 flex-shrink-0">{formatOdds(leg.odds)}</span>
              </div>
              {leg.game && (
                <p className="text-xs text-slate-500 truncate">{leg.game}</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Stake / payout row */}
      {(bet.stake !== null || bet.to_win !== null) && (
        <div className="flex items-center gap-3 pt-1 border-t border-slate-700/40 text-xs">
          {bet.stake !== null && (
            <span className="text-slate-400">
              Stake: <span className="text-white font-medium">${bet.stake.toFixed(2)}</span>
            </span>
          )}
          {bet.to_win !== null && (
            <span className="text-slate-400">
              To win: <span className={`font-medium ${bet.status === 'won' ? 'text-green-400' : 'text-white'}`}>
                ${bet.to_win.toFixed(2)}
              </span>
            </span>
          )}
          {bet.combined_odds !== null && (
            <span className="text-slate-500 ml-auto">{formatOdds(bet.combined_odds)}</span>
          )}
        </div>
      )}
    </div>
  );
}

export function BetTracker({ token }: BetTrackerProps) {
  const {
    bets, loadingBets, listError,
    importSlip, importing, importError, lastImported, clearConfirmation,
    refreshGrades, refreshing, gradeResult,
  } = useBetTracker(token);

  const [showImport, setShowImport] = useState(false);
  const [slipText, setSlipText] = useState('');
  const [filter, setFilter] = useState<string>('all');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleImport = () => {
    if (!slipText.trim() || importing) return;
    importSlip(slipText.trim());
    setSlipText('');
    setShowImport(false);
  };

  const filteredBets = filter === 'all'
    ? bets
    : bets.filter(b => b.status === filter);

  const stats = {
    pending: bets.filter(b => b.status === 'pending').length,
    won: bets.filter(b => b.status === 'won').length,
    lost: bets.filter(b => b.status === 'lost').length,
  };

  return (
    <div className="flex flex-col h-full">
      {/* Import area */}
      {showImport ? (
        <div className="flex-shrink-0 border-b border-slate-700 p-3 bg-slate-800/40 space-y-2">
          <p className="text-xs text-slate-400">
            Paste your full betslip text from DraftKings, FanDuel, BetMGM, Caesars, etc.
          </p>
          <textarea
            ref={textareaRef}
            value={slipText}
            onChange={e => setSlipText(e.target.value)}
            placeholder="Paste betslip here..."
            rows={5}
            className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 resize-none focus:outline-none focus:border-blue-500"
            autoFocus
          />
          <div className="flex gap-2">
            <button
              onClick={handleImport}
              disabled={!slipText.trim() || importing}
              className="flex-1 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-xs font-bold rounded-lg transition-colors"
            >
              {importing ? 'Parsing...' : 'Import Bet'}
            </button>
            <button
              onClick={() => { setShowImport(false); setSlipText(''); clearConfirmation(); }}
              className="px-3 py-2 text-slate-400 hover:text-white text-xs border border-slate-600 rounded-lg transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="flex-shrink-0 p-3 border-b border-slate-700 flex items-center justify-between">
          <div className="flex gap-3 text-xs">
            <span className="text-yellow-400">{stats.pending} live</span>
            <span className="text-green-400">{stats.won}W</span>
            <span className="text-red-400">{stats.lost}L</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={refreshGrades}
              disabled={refreshing}
              title="Poll ESPN for latest results and auto-grade open bets"
              className="flex items-center gap-1 text-xs text-slate-400 hover:text-white border border-slate-600 hover:border-slate-400 px-2 py-1.5 rounded-lg transition-colors disabled:opacity-40"
            >
              <svg
                className={`w-3 h-3 ${refreshing ? 'animate-spin' : ''}`}
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {refreshing ? 'Checking...' : 'Refresh'}
            </button>
            <button
              onClick={() => { setShowImport(true); clearConfirmation(); }}
              className="flex items-center gap-1.5 text-xs bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded-lg font-semibold transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Import Slip
            </button>
          </div>
        </div>
      )}

      {/* Confirmation / error toasts */}
      {gradeResult && !refreshing && (
        <div className="flex-shrink-0 mx-3 mt-2 px-3 py-2 bg-blue-900/40 border border-blue-700/50 rounded-lg text-xs text-blue-300">
          {gradeResult.graded > 0
            ? `Graded ${gradeResult.graded} bet${gradeResult.graded !== 1 ? 's' : ''} — results updated.`
            : 'No new results available yet.'}
        </div>
      )}
      {lastImported && (
        <div className="flex-shrink-0 mx-3 mt-2 px-3 py-2 bg-green-900/40 border border-green-700/50 rounded-lg text-xs text-green-300 flex items-start gap-2">
          <svg className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <span>{lastImported}</span>
        </div>
      )}
      {importError && (
        <div className="flex-shrink-0 mx-3 mt-2 px-3 py-2 bg-red-900/40 border border-red-700/50 rounded-lg text-xs text-red-300">
          {importError}
        </div>
      )}

      {/* Filter tabs */}
      {bets.length > 0 && (
        <div className="flex-shrink-0 flex border-b border-slate-700/60 px-3 pt-2 gap-1">
          {(['all', 'pending', 'won', 'lost'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`text-xs px-2 py-1 rounded-t capitalize transition-colors ${
                filter === f
                  ? 'text-blue-400 border-b-2 border-blue-400 font-semibold'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      )}

      {/* Bet list */}
      <div className="flex-1 overflow-y-auto min-h-0 p-3 space-y-2">
        {loadingBets && (
          <div className="flex items-center justify-center py-10">
            <div className="w-5 h-5 rounded-full border-2 border-blue-400 border-t-transparent animate-spin" />
          </div>
        )}
        {listError && !loadingBets && (
          <p className="text-center text-xs text-slate-500 py-6">{listError}</p>
        )}
        {!loadingBets && !listError && filteredBets.length === 0 && (
          <div className="py-8 text-center space-y-3">
            <p className="text-slate-400 text-sm font-medium">No bets yet</p>
            <p className="text-slate-500 text-xs">
              Paste a betslip from DraftKings, FanDuel, BetMGM, or any book — the analyst will parse and track it automatically.
            </p>
            <button
              onClick={() => setShowImport(true)}
              className="text-xs text-blue-400 hover:text-blue-300 underline transition-colors"
            >
              Import your first slip
            </button>
          </div>
        )}
        {filteredBets.map(bet => (
          <BetCard key={bet.id} bet={bet} />
        ))}
      </div>
    </div>
  );
}
