import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getApiUrl } from '../config';
import { BOOKMAKERS } from '../data/bookmakers';
import { useToast } from './Toast';
import { useSettings } from '../hooks/useSettings';

interface BookmakerBankroll {
  bookmaker: string;
  amount: number;
}

interface BankrollData {
  user_id: string;
  total_bankroll: number;
  bookmaker_bankrolls: BookmakerBankroll[];
  updated_at: string;
}

export function BankrollManager() {
  const { username } = useAuth();
  const { settings, loading: settingsLoading } = useSettings(username || 'default');
  const { showToast } = useToast();
  const [totalBankroll, setTotalBankroll] = useState(0);
  const [bookmakerBankrolls, setBookmakerBankrolls] = useState<Record<string, number>>({});
  const [showBookmakers, setShowBookmakers] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Kelly calculator state
  const [kellyEdge, setKellyEdge] = useState(5.0);
  const [kellyOdds, setKellyOdds] = useState(-110);

  // Get user's enabled bookmakers from settings (fallback to popular if none set)
  const displayBookmakers = settings && settings.enabled_bookmakers.length > 0
    ? Object.values(BOOKMAKERS)
        .filter(b => settings.enabled_bookmakers.includes(b.key))
        .sort((a, b) => a.name.localeCompare(b.name))
    : Object.values(BOOKMAKERS)
        .filter(b => b.popular)
        .sort((a, b) => a.name.localeCompare(b.name));

  useEffect(() => {
    fetchBankrollData();
  }, [username]);

  const fetchBankrollData = async () => {
    if (!username) {
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(getApiUrl(`bankroll/${username}`));
      if (response.ok) {
        const data: BankrollData = await response.json();
        setTotalBankroll(data.total_bankroll);

        // Convert array to record for easier access
        const bankrollMap: Record<string, number> = {};
        data.bookmaker_bankrolls.forEach(bb => {
          bankrollMap[bb.bookmaker] = bb.amount;
        });
        setBookmakerBankrolls(bankrollMap);
      } else if (response.status === 404) {
        // No bankroll data yet, use defaults
        setTotalBankroll(0);
        setBookmakerBankrolls({});
      }
    } catch (error) {
      console.error('Error fetching bankroll data:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateTotal = (bankrolls: Record<string, number>) => {
    return Object.values(bankrolls).reduce((sum, amount) => sum + (amount || 0), 0);
  };

  const calculateKelly = (edge: number, odds: number): { fullKelly: number; quarterKelly: number; halfKelly: number } => {
    if (totalBankroll === 0) return { fullKelly: 0, quarterKelly: 0, halfKelly: 0 };

    // Convert American odds to decimal
    const decimalOdds = odds > 0 ? (odds / 100) + 1 : (100 / Math.abs(odds)) + 1;

    // Calculate implied probability from odds
    const impliedProb = 1 / decimalOdds;

    // True probability = implied probability + edge (as decimal)
    const trueProb = impliedProb + (edge / 100);

    // Kelly formula: (b × p - q) / b
    // where b = decimal odds - 1, p = true win probability, q = 1 - p
    const b = decimalOdds - 1;
    const p = trueProb;
    const q = 1 - p;

    let kellyPercent = (b * p - q) / b;

    // Ensure non-negative
    kellyPercent = Math.max(0, kellyPercent);

    // Cap full Kelly at 10% for display purposes
    const fullKelly = Math.min(kellyPercent * 100, 10);
    const quarterKelly = fullKelly * 0.25;
    const halfKelly = fullKelly * 0.5;

    return { fullKelly, quarterKelly, halfKelly };
  };

  const handleBookmakerChange = (bookmakerKey: string, value: string) => {
    const amount = parseFloat(value) || 0;
    const updated = { ...bookmakerBankrolls, [bookmakerKey]: amount };
    setBookmakerBankrolls(updated);
    setTotalBankroll(calculateTotal(updated));
  };

  const handleSave = async () => {
    if (!username) return;

    setSaving(true);
    try {
      // Convert record back to array
      const bookmakerBankrollsArray = Object.entries(bookmakerBankrolls)
        .filter(([_, amount]) => amount > 0)
        .map(([bookmaker, amount]) => ({ bookmaker, amount }));

      const response = await fetch(getApiUrl(`bankroll/${username}`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          total_bankroll: totalBankroll,
          bookmaker_bankrolls: bookmakerBankrollsArray
        })
      });

      if (response.ok) {
        showToast('Bankroll saved successfully!', 'success');
      } else {
        showToast('Failed to save bankroll data', 'error');
      }
    } catch (error) {
      console.error('Error saving bankroll:', error);
      showToast('Error saving bankroll data', 'error');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-20">
        <div className="text-white text-xl">Loading bankroll...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-white mb-2">My Bankroll</h2>
        <p className="text-slate-400">
          Track your total bankroll across all sportsbooks for optimal Kelly Criterion bet sizing
        </p>
      </div>

      {/* Total Bankroll Card */}
      <div className="mb-6">
        <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-green-400 text-sm font-semibold mb-2">Total Bankroll</div>
              <div className="text-white text-5xl font-bold">
                ${totalBankroll.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className="text-green-300 text-sm mt-2">
                Across {Object.values(bookmakerBankrolls).filter(v => v > 0).length} bookmaker(s)
              </div>
            </div>
            <div className="text-6xl">💰</div>
          </div>
        </div>
      </div>

      {/* Reference Betting Units - Fixed Percentages */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-white mb-3">Reference Betting Units (Fixed)</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-4">
            <div className="text-xs text-slate-400 mb-1">Standard Unit</div>
            <div className="text-2xl font-bold text-blue-400">
              ${(totalBankroll * 0.01).toFixed(2)}
            </div>
            <div className="text-xs text-slate-400 mt-1">1% flat betting</div>
          </div>

          <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-4">
            <div className="text-xs text-slate-400 mb-1">Safety Cap</div>
            <div className="text-2xl font-bold text-purple-400">
              ${(totalBankroll * 0.05).toFixed(2)}
            </div>
            <div className="text-xs text-slate-400 mt-1">5% max (never exceed)</div>
          </div>

          <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-4">
            <div className="text-xs text-slate-400 mb-1">Conservative Unit</div>
            <div className="text-2xl font-bold text-amber-400">
              ${(totalBankroll * 0.005).toFixed(2)}
            </div>
            <div className="text-xs text-slate-400 mt-1">0.5% very safe</div>
          </div>
        </div>
      </div>

      {/* Bookmaker Toggle */}
      <div className="mb-4">
        <button
          onClick={() => setShowBookmakers(!showBookmakers)}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-lg text-white font-semibold transition-colors"
        >
          <span>{showBookmakers ? '▼' : '▶'}</span>
          <span>Bookmaker Balances</span>
          <span className="text-slate-400 text-sm">
            ({Object.values(bookmakerBankrolls).filter(v => v > 0).length} configured)
          </span>
        </button>
      </div>

      {/* Bookmaker Bankroll Inputs */}
      {showBookmakers && (
        <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6 mb-6">
          <h3 className="text-xl font-bold text-white mb-4">Individual Bookmaker Balances</h3>
          <p className="text-sm text-slate-400 mb-4">
            Enter your current balance at each sportsbook. Total bankroll is calculated automatically.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {displayBookmakers.map(bookmaker => (
              <div key={bookmaker.key} className="bg-slate-800 border border-slate-600 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-2">
                  <img
                    src={bookmaker.logo}
                    alt={bookmaker.name}
                    className="w-8 h-8 rounded"
                  />
                  <div className="text-white font-semibold">{bookmaker.name}</div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 text-lg">$</span>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={bookmakerBankrolls[bookmaker.key] || ''}
                    onChange={(e) => handleBookmakerChange(bookmaker.key, e.target.value)}
                    placeholder="0.00"
                    className="flex-1 bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white text-lg font-semibold focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Save Button */}
          <div className="mt-6 flex justify-end">
            <button
              id="save-bankroll-btn"
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-bold rounded-lg transition-colors"
            >
              {saving ? 'Saving...' : 'Save Bankroll'}
            </button>
          </div>
        </div>
      )}

      {/* Dynamic Kelly Calculator */}
      <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6 mb-6">
        <h3 className="text-xl font-bold text-white mb-3">📊 Kelly Criterion Calculator (Dynamic)</h3>
        <p className="text-sm text-slate-400 mb-4">
          Adjust edge and odds below to see how 1/4 Kelly adapts to different situations
        </p>

        {/* Input Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Your Edge (%)</label>
            <input
              type="number"
              step="0.1"
              value={kellyEdge}
              onChange={(e) => setKellyEdge(parseFloat(e.target.value) || 0)}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white text-lg font-semibold"
            />
            <div className="text-xs text-slate-500 mt-1">Difference between true probability and implied probability</div>
          </div>

          <div>
            <label className="text-xs text-slate-400 mb-1 block">Odds (American)</label>
            <input
              type="number"
              value={kellyOdds}
              onChange={(e) => setKellyOdds(parseInt(e.target.value) || -110)}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white text-lg font-semibold"
            />
            <div className="text-xs text-slate-500 mt-1">e.g., -110, +150, -200</div>
          </div>
        </div>

        {/* Kelly Results */}
        {(() => {
          const { fullKelly, quarterKelly, halfKelly } = calculateKelly(kellyEdge, kellyOdds);
          const quarterKellyDollars = (totalBankroll * quarterKelly) / 100;
          const cappedAmount = Math.min(quarterKellyDollars, totalBankroll * 0.05);
          const isCapped = quarterKellyDollars > totalBankroll * 0.05;

          return (
            <div className="bg-slate-800 border border-slate-600 rounded-lg p-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                <div className="text-center">
                  <div className="text-xs text-slate-400 mb-1">Full Kelly</div>
                  <div className="text-2xl font-bold text-red-400">{fullKelly.toFixed(2)}%</div>
                  <div className="text-sm text-slate-400">${(totalBankroll * fullKelly / 100).toFixed(2)}</div>
                </div>

                <div className="text-center">
                  <div className="text-xs text-slate-400 mb-1">1/2 Kelly</div>
                  <div className="text-2xl font-bold text-yellow-400">{halfKelly.toFixed(2)}%</div>
                  <div className="text-sm text-slate-400">${(totalBankroll * halfKelly / 100).toFixed(2)}</div>
                </div>

                <div className="text-center border border-green-600 rounded p-2">
                  <div className="text-xs text-green-400 mb-1 font-bold">1/4 Kelly (Recommended)</div>
                  <div className="text-3xl font-bold text-green-400">{quarterKelly.toFixed(2)}%</div>
                  <div className="text-lg text-green-300 font-semibold">${cappedAmount.toFixed(2)}</div>
                  {isCapped && (
                    <div className="text-xs text-red-400 mt-1">⚠️ Capped at 5% safety limit</div>
                  )}
                </div>
              </div>

              <div className="bg-blue-900/30 border border-blue-700 rounded p-3 text-xs text-blue-200">
                <strong>How this works:</strong> With a {kellyEdge}% edge at {kellyOdds} odds, full Kelly recommends betting {fullKelly.toFixed(2)}% of your bankroll.
                Using 1/4 Kelly for safety, you should bet <strong>{quarterKelly.toFixed(2)}%</strong> ({isCapped ? 'capped at $' + cappedAmount.toFixed(2) : '$' + cappedAmount.toFixed(2)}).
                This scales automatically with your edge and odds!
              </div>
            </div>
          );
        })()}
      </div>

      {/* Info Box */}
      <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
        <h4 className="text-blue-300 font-semibold mb-2">💡 Why Fractional Kelly?</h4>
        <p className="text-sm text-slate-300 mb-2">
          <strong>1/4 Kelly is a dynamic staking method</strong> that adapts based on your edge, odds, and bankroll:
        </p>
        <ul className="text-sm text-slate-300 space-y-1 ml-4 list-disc">
          <li><strong>Full Kelly</strong> maximizes geometric growth but with high volatility</li>
          <li><strong>1/2 Kelly</strong> reduces variance significantly while capturing most growth</li>
          <li><strong>1/4 Kelly</strong> (recommended) minimizes drawdowns while still scaling to edge</li>
          <li>Small edge (2-3%) → typically 0.5-1.5% of bankroll</li>
          <li>Medium edge (5%) → typically 1.5-2.5% of bankroll</li>
          <li>Large edge (8-10%) → typically 2.5-5% of bankroll (hits safety cap)</li>
          <li>System automatically caps all bets at <strong>5% max</strong> for risk management</li>
        </ul>
      </div>
    </div>
  );
}
