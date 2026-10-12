import { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useBetSlip } from '../contexts/BetSlipContext';
import { useAuth } from '../contexts/AuthContext';
import { getSportStyle } from '../utils/sportDetection';
import { getApiUrl } from '../config';
import { logger } from '../utils/logger';

type SlipType = 'straight' | 'parlay' | 'teaser' | 'same_game_parlay';

interface Leg {
  sport: string;
  event: string;
  market: string;
  pick: string;
  line: string;
  odds: string;
}

const EMPTY_LEG: Leg = { sport: '', event: '', market: 'spread', pick: '', line: '', odds: '-110' };

const BOOKS = [
  { value: 'draftkings', label: 'DraftKings' },
  { value: 'fanduel', label: 'FanDuel' },
  { value: 'betmgm', label: 'BetMGM' },
  { value: 'caesars', label: 'Caesars' },
  { value: 'bovada', label: 'Bovada' },
  { value: 'bet365', label: 'Bet365' },
  { value: 'barstool', label: 'ESPN Bet' },
  { value: 'pinnacle', label: 'Pinnacle' },
  { value: 'other', label: 'Other' },
];

const MARKETS = [
  { value: 'spread', label: 'Spread' },
  { value: 'total', label: 'Total (O/U)' },
  { value: 'moneyline', label: 'Moneyline' },
  { value: 'prop', label: 'Prop' },
  { value: 'alt_spread', label: 'Alt Spread' },
  { value: 'alt_total', label: 'Alt Total' },
  { value: 'team_total', label: 'Team Total' },
  { value: 'first_half', label: '1H Line' },
];

const TEASER_POINTS: Record<string, number[]> = {
  nfl: [6, 6.5, 7, 10, 13],
  ncaaf: [6, 6.5, 7, 10, 13],
  nba: [4, 4.5, 5, 5.5, 6],
  ncaab: [4, 4.5, 5, 5.5, 6],
};

function computeToWin(stake: number, odds: number): number {
  if (odds > 0) return parseFloat(((stake * odds) / 100).toFixed(2));
  return parseFloat(((stake * 100) / Math.abs(odds)).toFixed(2));
}

export function BetSlipToast() {
  const { isOpen, betData, closeBetSlip } = useBetSlip();
  const { username, token } = useAuth();
  const queryClient = useQueryClient();

  const [slipType, setSlipType] = useState<SlipType>('straight');
  const [legs, setLegs] = useState<Leg[]>([{ ...EMPTY_LEG }]);
  const [combinedOdds, setCombinedOdds] = useState('');
  const [stake, setStake] = useState('');
  const [bookmaker, setBookmaker] = useState('draftkings');
  const [teaserPoints, setTeaserPoints] = useState(6);
  const [notes, setNotes] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Pre-fill from betData (when clicking a line on a game card)
  useEffect(() => {
    if (!betData) return;
    const leg: Leg = {
      sport: betData.sport || '',
      event: [betData.awayTeam, betData.homeTeam].filter(Boolean).join(' @ '),
      market: betData.betType || 'spread',
      pick: betData.betSide || '',
      line: betData.line?.toString() || '',
      odds: betData.odds?.toString() || '-110',
    };
    setLegs([leg]);
    if (betData.bookmaker) setBookmaker(betData.bookmaker);
    if (betData.strategy) setNotes(`Strategy: ${betData.strategy}`);
  }, [betData]);

  const updateLeg = (idx: number, field: keyof Leg, value: string) => {
    setLegs(prev => prev.map((l, i) => i === idx ? { ...l, [field]: value } : l));
  };

  const addLeg = () => setLegs(prev => [...prev, { ...EMPTY_LEG }]);
  const removeLeg = (idx: number) => setLegs(prev => prev.filter((_, i) => i !== idx));

  const isMultiLeg = slipType !== 'straight';
  const toWin = stake && combinedOdds
    ? computeToWin(parseFloat(stake), parseInt(combinedOdds))
    : stake && legs[0]?.odds
      ? computeToWin(parseFloat(stake), parseInt(legs[0].odds))
      : 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) { setError('Please log in to track bets'); return; }

    const validLegs = legs.filter(l => l.pick.trim());
    if (validLegs.length === 0) { setError('Enter at least one pick'); return; }

    setIsSubmitting(true);
    setError(null);

    // Build the pick string
    const pickStr = isMultiLeg
      ? validLegs.map(l => `${l.pick}${l.line ? ' ' + l.line : ''}`).join(' / ')
      : `${validLegs[0].pick}${validLegs[0].line ? ' ' + validLegs[0].line : ''}`;

    const eventStr = isMultiLeg
      ? validLegs.map(l => l.event).filter(Boolean).join(' | ')
      : validLegs[0].event;

    const marketStr = isMultiLeg
      ? slipType
      : validLegs[0].market;

    const finalOdds = isMultiLeg
      ? (combinedOdds ? parseInt(combinedOdds) : null)
      : (validLegs[0].odds ? parseInt(validLegs[0].odds) : null);

    const teaserNote = slipType === 'teaser' ? `${teaserPoints}pt teaser` : '';
    const fullNotes = [teaserNote, notes].filter(Boolean).join(' · ');

    try {
      const resp = await fetch(getApiUrl('v1/bets/manual'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          book: bookmaker,
          bet_type: slipType,
          sport: validLegs[0].sport || null,
          event: eventStr,
          market: marketStr,
          pick: pickStr,
          odds: finalOdds,
          stake: stake ? parseFloat(stake) : null,
          to_win: stake && finalOdds ? computeToWin(parseFloat(stake), finalOdds) : null,
          notes: fullNotes || null,
        }),
      });

      if (resp.ok) {
        setSuccess(true);
        queryClient.invalidateQueries({ queryKey: ['user-bets'] });
        setTimeout(() => { closeBetSlip(); setSuccess(false); resetForm(); }, 2000);
      } else {
        const msg = await resp.text();
        setError(`Failed to track bet: ${msg}`);
      }
    } catch (err) {
      setError('Error tracking bet. Please try again.');
      logger.error('Bet tracking error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setSlipType('straight');
    setLegs([{ ...EMPTY_LEG }]);
    setCombinedOdds('');
    setStake('');
    setNotes('');
    setError(null);
  };

  const handleClose = () => {
    closeBetSlip();
    setTimeout(() => { setError(null); setSuccess(false); }, 300);
  };

  if (!isOpen) return null;

  const sportStyle = getSportStyle((legs[0]?.sport || 'NFL') as any);

  return (
    <div className={`fixed left-4 bottom-4 z-50 w-[420px] bg-gradient-to-br from-slate-800 via-slate-900 to-slate-800 border-2 ${sportStyle.borderColor} rounded-xl overflow-hidden shadow-2xl transition-all duration-300 ease-out ${isOpen ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-full'}`}>

      {/* Header */}
      <div className="bg-gradient-to-r from-slate-800 to-slate-700 px-4 py-3 border-b border-slate-600 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl">📝</span>
          <div>
            <div className="font-bold text-white text-sm">Track Bet</div>
            <div className="text-[10px] text-slate-400">Saved to your account</div>
          </div>
        </div>
        <button onClick={handleClose} className="text-slate-400 hover:text-white transition-colors text-xl font-bold w-7 h-7 flex items-center justify-center">×</button>
      </div>

      {success && <div className="p-3 bg-green-600 text-white text-center font-bold text-sm">Bet Tracked!</div>}

      <form onSubmit={handleSubmit} className="max-h-[70vh] overflow-y-auto">

        {/* Slip Type Tabs */}
        <div className="flex border-b border-slate-700">
          {([
            { key: 'straight' as SlipType, label: 'Straight' },
            { key: 'parlay' as SlipType, label: 'Parlay' },
            { key: 'teaser' as SlipType, label: 'Teaser' },
            { key: 'same_game_parlay' as SlipType, label: 'SGP' },
          ]).map(t => (
            <button key={t.key} type="button" onClick={() => {
              setSlipType(t.key);
              if (t.key === 'straight' && legs.length > 1) setLegs([legs[0]]);
              if (t.key !== 'straight' && legs.length < 2) addLeg();
            }}
              className={`flex-1 py-2.5 text-xs font-bold transition-all ${
                slipType === t.key ? 'text-blue-400 border-b-2 border-blue-400 bg-blue-900/20' : 'text-slate-500 hover:text-slate-300'
              }`}
            >{t.label}</button>
          ))}
        </div>

        {error && <div className="mx-4 mt-3 p-2 bg-red-900/30 border border-red-500 rounded text-red-200 text-xs">{error}</div>}

        {/* Teaser Points Selector */}
        {slipType === 'teaser' && (
          <div className="px-4 pt-3">
            <label className="text-[10px] text-yellow-400 font-bold uppercase tracking-wider block mb-1.5">Teaser Points</label>
            <div className="flex gap-1.5">
              {(TEASER_POINTS[legs[0]?.sport?.includes('nfl') || legs[0]?.sport?.includes('ncaaf') ? 'nfl' : 'nba'] || TEASER_POINTS.nfl).map(pts => (
                <button key={pts} type="button" onClick={() => setTeaserPoints(pts)}
                  className={`flex-1 py-1.5 rounded text-xs font-bold transition-all ${
                    teaserPoints === pts ? 'bg-yellow-600 text-white' : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                  }`}
                >{pts}pt</button>
              ))}
            </div>
          </div>
        )}

        {/* Legs */}
        <div className="p-4 space-y-3">
          {legs.map((leg, idx) => (
            <div key={idx} className="bg-slate-800/80 rounded-lg p-3 border border-slate-700 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  {isMultiLeg ? `Leg ${idx + 1}` : 'Bet Details'}
                </span>
                {isMultiLeg && legs.length > 2 && (
                  <button type="button" onClick={() => removeLeg(idx)} className="text-red-400 hover:text-red-300 text-xs font-bold">Remove</button>
                )}
              </div>

              {/* Sport + Market */}
              <div className="grid grid-cols-2 gap-2">
                <select value={leg.sport} onChange={e => updateLeg(idx, 'sport', e.target.value)}
                  className="bg-slate-700 text-white rounded px-2 py-1.5 text-xs border border-slate-600 focus:border-blue-500 focus:outline-none">
                  <option value="">Sport</option>
                  <option value="americanfootball_nfl">NFL</option>
                  <option value="americanfootball_ncaaf">NCAAF</option>
                  <option value="basketball_nba">NBA</option>
                  <option value="basketball_ncaab">NCAAB</option>
                  <option value="baseball_mlb">MLB</option>
                  <option value="icehockey_nhl">NHL</option>
                </select>
                <select value={leg.market} onChange={e => updateLeg(idx, 'market', e.target.value)}
                  className="bg-slate-700 text-white rounded px-2 py-1.5 text-xs border border-slate-600 focus:border-blue-500 focus:outline-none">
                  {MARKETS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                </select>
              </div>

              {/* Game */}
              <input type="text" placeholder="Game (e.g. Falcons @ Steelers)" value={leg.event}
                onChange={e => updateLeg(idx, 'event', e.target.value)}
                className="w-full bg-slate-700 text-white rounded px-2 py-1.5 text-xs border border-slate-600 focus:border-blue-500 focus:outline-none" />

              {/* Pick + Line */}
              <div className="grid grid-cols-2 gap-2">
                <input type="text" placeholder="Pick (e.g. Steelers -4.5)" value={leg.pick}
                  onChange={e => updateLeg(idx, 'pick', e.target.value)} required
                  className="bg-slate-700 text-white rounded px-2 py-1.5 text-xs border border-slate-600 focus:border-blue-500 focus:outline-none font-semibold" />
                {!isMultiLeg && (
                  <input type="number" step="1" placeholder="Odds (-110)" value={leg.odds}
                    onChange={e => updateLeg(idx, 'odds', e.target.value)}
                    className="bg-slate-700 text-white rounded px-2 py-1.5 text-xs border border-slate-600 focus:border-blue-500 focus:outline-none font-semibold text-center" />
                )}
                {isMultiLeg && (
                  <input type="text" placeholder="Line (e.g. -4.5)" value={leg.line}
                    onChange={e => updateLeg(idx, 'line', e.target.value)}
                    className="bg-slate-700 text-white rounded px-2 py-1.5 text-xs border border-slate-600 focus:border-blue-500 focus:outline-none text-center" />
                )}
              </div>
            </div>
          ))}

          {/* Add Leg Button (multi-leg only) */}
          {isMultiLeg && (
            <button type="button" onClick={addLeg}
              className="w-full py-2 rounded-lg border-2 border-dashed border-slate-600 text-slate-400 hover:border-blue-500 hover:text-blue-400 text-xs font-bold transition-colors">
              + Add Leg
            </button>
          )}
        </div>

        {/* Bookmaker + Combined Odds + Stake */}
        <div className="px-4 pb-3 space-y-2">
          <div className={`grid ${isMultiLeg ? 'grid-cols-3' : 'grid-cols-2'} gap-2`}>
            <div>
              <label className="text-[10px] text-slate-400 font-bold uppercase block mb-1">Book</label>
              <select value={bookmaker} onChange={e => setBookmaker(e.target.value)}
                className="w-full bg-slate-700 text-white rounded px-2 py-2 text-xs border border-slate-600 focus:border-blue-500 focus:outline-none">
                {BOOKS.map(b => <option key={b.value} value={b.value}>{b.label}</option>)}
              </select>
            </div>
            {isMultiLeg && (
              <div>
                <label className="text-[10px] text-slate-400 font-bold uppercase block mb-1">Combined Odds</label>
                <input type="number" step="1" value={combinedOdds} onChange={e => setCombinedOdds(e.target.value)}
                  placeholder="+450" required
                  className="w-full bg-slate-700 text-white rounded px-2 py-2 text-xs border border-slate-600 focus:border-blue-500 focus:outline-none font-bold text-center" />
              </div>
            )}
            <div>
              <label className="text-[10px] text-slate-400 font-bold uppercase block mb-1">Stake ($)</label>
              <input type="number" step="0.01" value={stake} onChange={e => setStake(e.target.value)}
                placeholder="25" required
                className="w-full bg-slate-700 text-white rounded px-2 py-2 text-xs border border-slate-600 focus:border-blue-500 focus:outline-none font-bold text-center" />
            </div>
          </div>

          {/* To Win Preview */}
          {toWin > 0 && (
            <div className="flex items-center justify-between bg-emerald-900/20 border border-emerald-700/40 rounded-lg px-3 py-2">
              <span className="text-xs text-emerald-400 font-bold">To Win</span>
              <span className="text-lg font-black text-emerald-300">${toWin.toFixed(2)}</span>
            </div>
          )}

          {/* Notes */}
          <input type="text" value={notes} onChange={e => setNotes(e.target.value)}
            placeholder="Notes (optional)"
            className="w-full bg-slate-700 text-white rounded px-2 py-1.5 text-xs border border-slate-600 focus:border-blue-500 focus:outline-none" />

          {/* Submit */}
          <button type="submit" disabled={isSubmitting || success}
            className={`w-full py-2.5 rounded-lg font-bold text-white text-sm transition-all ${
              isSubmitting || success ? 'bg-slate-600 cursor-not-allowed' : 'bg-gradient-to-r from-emerald-600 to-blue-600 hover:from-emerald-500 hover:to-blue-500 shadow-lg'
            }`}>
            {isSubmitting ? 'Tracking...' : success ? 'Tracked!' : `Track ${slipType === 'straight' ? 'Bet' : slipType === 'same_game_parlay' ? 'SGP' : slipType.charAt(0).toUpperCase() + slipType.slice(1)}`}
          </button>
        </div>
      </form>

      <div className="px-4 py-1.5 bg-black/20 border-t border-slate-700">
        <p className="text-[10px] text-slate-500 text-center">
          View tracked bets at <span className="text-blue-400">Open Bets</span> · Import slips in <span className="text-blue-400">AI Analyst</span>
        </p>
      </div>
    </div>
  );
}
