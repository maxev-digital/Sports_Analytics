import { useState, useEffect } from 'react';
import { useBetSlip } from '../contexts/BetSlipContext';
import { useAuth } from '../contexts/AuthContext';
import { addManualBet } from '../utils/betTracking';
import { getSportStyle } from '../utils/sportDetection';

export function BetSlipToast() {
  const { isOpen, betData, closeBetSlip } = useBetSlip();
  const { username } = useAuth();

  // Form state
  const [sport, setSport] = useState('');
  const [homeTeam, setHomeTeam] = useState('');
  const [awayTeam, setAwayTeam] = useState('');
  const [betType, setBetType] = useState<'spread' | 'total' | 'moneyline' | 'prop'>('total');
  const [betSide, setBetSide] = useState('');
  const [line, setLine] = useState('');
  const [odds, setOdds] = useState('');
  const [stake, setStake] = useState('');
  const [bookmaker, setBookmaker] = useState('draftkings');
  const [confidence, setConfidence] = useState<'HIGH' | 'MEDIUM' | 'LOW' | 'CRITICAL'>('MEDIUM');
  const [edgePercent, setEdgePercent] = useState('');
  const [notes, setNotes] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Pre-fill form when bet data is provided
  useEffect(() => {
    if (betData) {
      if (betData.sport) setSport(betData.sport);
      if (betData.homeTeam) setHomeTeam(betData.homeTeam);
      if (betData.awayTeam) setAwayTeam(betData.awayTeam);
      if (betData.betType) setBetType(betData.betType);
      if (betData.betSide) setBetSide(betData.betSide);
      if (betData.line !== undefined) setLine(betData.line.toString());
      if (betData.odds !== undefined) setOdds(betData.odds.toString());
      if (betData.bookmaker) setBookmaker(betData.bookmaker);
      if (betData.confidence) setConfidence(betData.confidence);
      if (betData.edgePercent !== undefined) setEdgePercent(betData.edgePercent.toString());
      if (betData.strategy) setNotes(`Strategy: ${betData.strategy}`);
    }
  }, [betData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!username) {
      setError('Please log in to track bets');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const result = await addManualBet({
        userId: username,
        sport: sport,
        homeTeam: homeTeam,
        awayTeam: awayTeam,
        commenceTime: betData?.commenceTime || new Date().toISOString(),
        betType: betType,
        betSide: betSide,
        odds: parseFloat(odds),
        stake: parseFloat(stake),
        bookmaker: bookmaker,
        confidence: confidence,
        edgePercent: edgePercent ? parseFloat(edgePercent) : undefined,
        notes: notes || undefined
      });

      if (result) {
        setSuccess(true);
        // Auto-close after 2 seconds
        setTimeout(() => {
          closeBetSlip();
          setSuccess(false);
        }, 2000);
      } else {
        setError('Failed to track bet. Please try again.');
      }
    } catch (err) {
      setError('Error tracking bet. Please try again.');
      console.error('Bet tracking error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    closeBetSlip();
    // Reset form
    setTimeout(() => {
      setError(null);
      setSuccess(false);
    }, 300);
  };

  if (!isOpen) return null;

  const sportStyle = getSportStyle(sport as any);
  const hasPrefilledData = !!(betData && betData.sport);

  return (
    <div
      className={`
        fixed left-4 bottom-4 z-50 w-96
        bg-gradient-to-br from-slate-800 via-slate-900 to-slate-800
        border-4 ${sportStyle.borderColor}
        rounded-xl overflow-hidden shadow-2xl
        transition-all duration-300 ease-out
        ${isOpen ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-full'}
      `}
    >
      {/* Header */}
      <div className={`bg-gradient-to-r ${sportStyle.gradientFrom} ${sportStyle.gradientTo} px-4 py-3 border-b-2 border-white/20 flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <span className="text-2xl">📝</span>
          <div>
            <div className="font-bold text-white text-base">Track Bet</div>
            <div className="text-xs text-white/80">Quick bet entry</div>
          </div>
        </div>
        <button
          onClick={handleClose}
          className="text-white/60 hover:text-white transition-colors text-2xl font-bold w-8 h-8 flex items-center justify-center"
        >
          ×
        </button>
      </div>

      {/* Success Message */}
      {success && (
        <div className="p-4 bg-green-600 text-white text-center font-bold">
          ✅ Bet Tracked Successfully!
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="p-4 space-y-3 max-h-[600px] overflow-y-auto">
        {/* Error Message */}
        {error && (
          <div className="p-2 bg-red-900/30 border border-red-500 rounded text-red-200 text-sm">
            {error}
          </div>
        )}

        {/* Game Info Summary Card (when pre-filled from alert) */}
        {hasPrefilledData && (
          <div className={`bg-gradient-to-br ${sportStyle.gradientFrom} ${sportStyle.gradientTo} rounded-lg p-3 border-2 ${sportStyle.borderColor}`}>
            <div className="text-xs font-semibold text-white/70 mb-2">GAME INFO</div>
            <div className="space-y-1">
              <div className="text-white font-bold text-sm">{awayTeam} @ {homeTeam}</div>
              <div className="text-white/80 text-xs">
                {betType.charAt(0).toUpperCase() + betType.slice(1)} • {bookmaker.toUpperCase()}
              </div>
              {notes && <div className="text-white/70 text-xs italic">{notes}</div>}
            </div>
          </div>
        )}

        {/* Manual Entry Fields (collapsed when pre-filled) */}
        {!hasPrefilledData ? (
          <div className="space-y-3">
            {/* Game Info */}
            <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs text-slate-400 font-semibold block mb-1">Sport</label>
            <select
              value={sport}
              onChange={(e) => setSport(e.target.value)}
              className="w-full bg-slate-700 text-white rounded px-2 py-1.5 text-sm border border-slate-600 focus:border-blue-500 focus:outline-none"
              required
            >
              <option value="">Select Sport</option>
              <option value="basketball_nba">NBA</option>
              <option value="basketball_ncaab">NCAAB</option>
              <option value="americanfootball_nfl">NFL</option>
              <option value="americanfootball_ncaaf">NCAAF</option>
              <option value="icehockey_nhl">NHL</option>
              <option value="baseball_mlb">MLB</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-400 font-semibold block mb-1">Bet Type</label>
            <select
              value={betType}
              onChange={(e) => setBetType(e.target.value as any)}
              className="w-full bg-slate-700 text-white rounded px-2 py-1.5 text-sm border border-slate-600 focus:border-blue-500 focus:outline-none"
              required
            >
              <option value="total">Total (O/U)</option>
              <option value="spread">Spread</option>
              <option value="moneyline">Moneyline</option>
              <option value="prop">Prop</option>
            </select>
          </div>
        </div>

        {/* Teams */}
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs text-slate-400 font-semibold block mb-1">Away Team</label>
            <input
              type="text"
              value={awayTeam}
              onChange={(e) => setAwayTeam(e.target.value)}
              placeholder="Lakers"
              className="w-full bg-slate-700 text-white rounded px-2 py-1.5 text-sm border border-slate-600 focus:border-blue-500 focus:outline-none"
              required
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 font-semibold block mb-1">Home Team</label>
            <input
              type="text"
              value={homeTeam}
              onChange={(e) => setHomeTeam(e.target.value)}
              placeholder="Warriors"
              className="w-full bg-slate-700 text-white rounded px-2 py-1.5 text-sm border border-slate-600 focus:border-blue-500 focus:outline-none"
              required
            />
          </div>
        </div>

            {/* Bet Details */}
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs text-slate-400 font-semibold block mb-1">Bet Side</label>
                <input
                  type="text"
                  value={betSide}
                  onChange={(e) => setBetSide(e.target.value)}
                  placeholder="OVER"
                  className="w-full bg-slate-700 text-white rounded px-2 py-1.5 text-sm border border-slate-600 focus:border-blue-500 focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 font-semibold block mb-1">Line (optional)</label>
                <input
                  type="number"
                  step="0.5"
                  value={line}
                  onChange={(e) => setLine(e.target.value)}
                  placeholder="225.5"
                  className="w-full bg-slate-700 text-white rounded px-2 py-1.5 text-sm border border-slate-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>


        {/* Bookmaker & Confidence */}
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs text-slate-400 font-semibold block mb-1">Bookmaker</label>
            <select
              value={bookmaker}
              onChange={(e) => setBookmaker(e.target.value)}
              className="w-full bg-slate-700 text-white rounded px-2 py-1.5 text-sm border border-slate-600 focus:border-blue-500 focus:outline-none"
              required
            >
              <option value="draftkings">DraftKings</option>
              <option value="fanduel">FanDuel</option>
              <option value="betmgm">BetMGM</option>
              <option value="caesars">Caesars</option>
              <option value="bet365">Bet365</option>
              <option value="pinnacle">Pinnacle</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-400 font-semibold block mb-1">Confidence</label>
            <select
              value={confidence}
              onChange={(e) => setConfidence(e.target.value as any)}
              className="w-full bg-slate-700 text-white rounded px-2 py-1.5 text-sm border border-slate-600 focus:border-blue-500 focus:outline-none"
            >
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        </div>


            {/* Notes (optional) */}
            <div>
              <label className="text-xs text-slate-400 font-semibold block mb-1">Notes (optional)</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Strategy, reasoning, etc."
                rows={2}
                className="w-full bg-slate-700 text-white rounded px-2 py-1.5 text-sm border border-slate-600 focus:border-blue-500 focus:outline-none resize-none"
              />
            </div>
          </div>
        ) : (
          <details className="bg-slate-800 rounded-lg border border-slate-700">
            <summary className="px-3 py-2 cursor-pointer text-slate-400 text-sm font-semibold hover:text-white">
              ⚙️ Advanced Options (click to expand)
            </summary>
            <div className="p-3 space-y-2 border-t border-slate-700">
              {/* Edge % */}
              <div>
                <label className="text-xs text-slate-400 font-semibold block mb-1">Edge % (optional)</label>
                <input
                  type="number"
                  step="0.1"
                  value={edgePercent}
                  onChange={(e) => setEdgePercent(e.target.value)}
                  placeholder="5.5"
                  className="w-full bg-slate-700 text-white rounded px-2 py-1.5 text-sm border border-slate-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
              {/* Notes */}
              <div>
                <label className="text-xs text-slate-400 font-semibold block mb-1">Additional Notes</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Extra details..."
                  rows={2}
                  className="w-full bg-slate-700 text-white rounded px-2 py-1.5 text-sm border border-slate-600 focus:border-blue-500 focus:outline-none resize-none"
                />
              </div>
            </div>
          </details>
        )}

        {/* Toggle Buttons for Bet Side */}
        <div className={`bg-gradient-to-br ${sportStyle.gradientFrom} ${sportStyle.gradientTo} rounded-lg p-3 border-2 ${sportStyle.borderColor}`}>
          <div className="text-xs font-semibold text-white/70 mb-2">YOUR BET</div>
          <div className="flex items-center gap-2 mb-2">
            {betType === 'total' ? (
              <>
                <button
                  type="button"
                  onClick={() => setBetSide('OVER')}
                  className={`flex-1 py-3 px-4 rounded-lg font-bold transition-all text-base ${
                    betSide === 'OVER'
                      ? 'bg-green-600 text-white border-2 border-green-400 shadow-lg scale-105'
                      : 'bg-slate-700 text-slate-300 border border-slate-600 hover:bg-slate-600'
                  }`}
                >
                  OVER {line ? parseFloat(line).toFixed(1) : ''}
                </button>
                <button
                  type="button"
                  onClick={() => setBetSide('UNDER')}
                  className={`flex-1 py-3 px-4 rounded-lg font-bold transition-all text-base ${
                    betSide === 'UNDER'
                      ? 'bg-red-600 text-white border-2 border-red-400 shadow-lg scale-105'
                      : 'bg-slate-700 text-slate-300 border border-slate-600 hover:bg-slate-600'
                  }`}
                >
                  UNDER {line ? parseFloat(line).toFixed(1) : ''}
                </button>
              </>
            ) : betType === 'spread' || betType === 'moneyline' ? (
              <>
                <button
                  type="button"
                  onClick={() => setBetSide(awayTeam || 'AWAY')}
                  className={`flex-1 py-3 px-3 rounded-lg font-bold text-sm transition-all ${
                    betSide === awayTeam || betSide === 'AWAY'
                      ? 'bg-blue-600 text-white border-2 border-blue-400 shadow-lg scale-105'
                      : 'bg-slate-700 text-slate-300 border border-slate-600 hover:bg-slate-600'
                  }`}
                >
                  {awayTeam || 'AWAY'}
                </button>
                <button
                  type="button"
                  onClick={() => setBetSide(homeTeam || 'HOME')}
                  className={`flex-1 py-3 px-3 rounded-lg font-bold text-sm transition-all ${
                    betSide === homeTeam || betSide === 'HOME'
                      ? 'bg-green-600 text-white border-2 border-green-400 shadow-lg scale-105'
                      : 'bg-slate-700 text-slate-300 border border-slate-600 hover:bg-slate-600'
                  }`}
                >
                  {homeTeam || 'HOME'}
                </button>
              </>
            ) : (
              <input
                type="text"
                value={betSide}
                onChange={(e) => setBetSide(e.target.value)}
                placeholder="Enter bet side"
                className="w-full bg-slate-700 text-white rounded-lg px-3 py-3 text-base border-2 border-slate-600 focus:border-blue-500 focus:outline-none font-bold text-center"
                required
              />
            )}
          </div>
        </div>

        {/* Odds & Stake - Enhanced */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-slate-400 font-semibold block mb-1">Odds</label>
            <input
              type="number"
              step="1"
              value={odds}
              onChange={(e) => setOdds(e.target.value)}
              placeholder="-110"
              required
              className="w-full bg-slate-700 text-white rounded-lg px-3 py-3 text-lg border-2 border-slate-600 focus:border-blue-500 focus:outline-none font-bold text-center"
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 font-semibold block mb-1">Stake ($)</label>
            <input
              type="number"
              step="0.01"
              value={stake}
              onChange={(e) => setStake(e.target.value)}
              placeholder="100"
              required
              className="w-full bg-slate-700 text-white rounded-lg px-3 py-3 text-lg border-2 border-slate-600 focus:border-blue-500 focus:outline-none font-bold text-center"
            />
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isSubmitting || success}
          className={`
            w-full py-3 rounded-lg font-bold text-white transition-all
            ${isSubmitting || success
              ? 'bg-slate-600 cursor-not-allowed'
              : 'bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 shadow-lg hover:shadow-xl'
            }
          `}
        >
          {isSubmitting ? 'Tracking...' : success ? '✅ Tracked!' : '📊 Track Bet'}
        </button>
      </form>

      {/* Footer Tip */}
      <div className="px-4 py-2 bg-black/20 border-t border-white/10">
        <p className="text-xs text-slate-400 text-center">
          View all tracked bets in <span className="text-blue-400 font-semibold">My Bets</span> section
        </p>
      </div>
    </div>
  );
}
