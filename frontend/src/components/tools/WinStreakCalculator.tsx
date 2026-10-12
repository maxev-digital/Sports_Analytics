import { useState, useMemo, useEffect, useCallback } from 'react';
import { ProgressionBuilder } from './ProgressionBuilder';
import { getApiUrl } from '../../config';

// ── Types ────────────────────────────────────────────────────────────────────

type BetType = 'spread' | 'moneyline' | 'custom';
type TabId = 'tracker' | 'ladder' | 'simulate' | 'builder' | 'history';

interface DbSequence {
  id: number;
  username: string;
  base_bet: number;
  target_streak: number;
  bet_type: string;
  juice: number;
  status: string;
  total_payout: number;
  net_profit: number;
  created_at: string;
  completed_at: string | null;
}

interface DbBet {
  id: number;
  sequence_id: number;
  bet_number: number;
  game_description: string;
  pick: string;
  odds: number;
  bet_amount: number;
  potential_payout: number;
  result: string;
  actual_payout: number;
  bet_category: string;
  notes: string | null;
  placed_at: string;
  graded_at: string | null;
}

interface HistoryStats {
  total_bets: number;
  record: string;
  net_pnl: number;
  balance_curve: BalancePoint[];
  core_record: string;
  flier_record: string;
  current_streak: number;
  best_streak: number;
  deposits: number;
}

interface BalancePoint {
  date: string;
  time: string;
  balance: number;
  type: string;
  game: string;
}

interface ParsedTx {
  date: string;
  time: string;
  type: string;
  game: string;
  pick: string;
  odds: string;
  amount: number;
  balance: number;
  result: string;
  reward_points: number;
}

// ── Math helpers ─────────────────────────────────────────────────────────────

function americanToDecimal(odds: number): number {
  return odds > 0 ? (odds / 100) + 1 : (100 / Math.abs(odds)) + 1;
}

function streakPayout(baseBet: number, wins: number, multiplier: number): number {
  return baseBet * Math.pow(multiplier, wins);
}

function streakProfit(baseBet: number, wins: number, multiplier: number): number {
  return streakPayout(baseBet, wins, multiplier) - baseBet;
}

function streakProb(winRate: number, length: number): number {
  return Math.pow(winRate, length);
}

function avgAttemptsToHit(winRate: number, length: number): number {
  const p = streakProb(winRate, length);
  return p > 0 ? Math.ceil(1 / p) : Infinity;
}

function runMonteCarlo(
  baseBet: number, targetStreak: number, winRate: number,
  bankroll: number, multiplier: number, sims: number
) {
  const results: number[] = [];
  let totalHits = 0;
  let totalBusts = 0;
  let totalAttempts = 0;

  for (let s = 0; s < sims; s++) {
    let bank = bankroll;
    let streak = 0;
    let attempts = 0;
    let hit = false;
    const maxAttempts = 500;

    while (attempts < maxAttempts && bank >= baseBet) {
      if (streak === 0) {
        attempts++;
        if (Math.random() < winRate) {
          streak = 1;
        } else {
          bank -= baseBet;
        }
      } else {
        if (Math.random() < winRate) {
          streak++;
          if (streak >= targetStreak) {
            const profit = streakProfit(baseBet, targetStreak, multiplier);
            bank += profit;
            hit = true;
            totalHits++;
            break;
          }
        } else {
          bank -= baseBet;
          streak = 0;
        }
      }
    }

    if (!hit && bank < baseBet) totalBusts++;
    totalAttempts += attempts;
    results.push(bank - bankroll);
  }

  results.sort((a, b) => a - b);
  return {
    avgProfit: results.reduce((a, b) => a + b, 0) / sims,
    hitRate: totalHits / sims,
    avgAttempts: totalAttempts / sims,
    bustRate: totalBusts / sims,
    medianProfit: results[Math.floor(sims / 2)],
  };
}

// ── Formatting ───────────────────────────────────────────────────────────────

const fmtMoney = (n: number) => {
  const abs = Math.abs(Math.round(n * 100) / 100);
  const str = abs.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
  return n >= 0 ? `$${str}` : `-$${str}`;
};
const fmtPct = (n: number) => `${(n * 100).toFixed(1)}%`;

// ── Transaction Parser ───────────────────────────────────────────────────────

function parseBovadaTransactions(raw: string): ParsedTx[] {
  const txs: ParsedTx[] = [];
  const lines = raw.split('\n').map(l => l.trim()).filter(Boolean);

  let i = 0;
  while (i < lines.length) {
    // Look for date pattern: "Sep 19, 2026"
    const dateMatch = lines[i].match(/^((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4})$/);
    if (!dateMatch) { i++; continue; }

    const txDate = dateMatch[1];
    i++;
    if (i >= lines.length) break;

    // Time: "02:52 PM"
    const timeMatch = lines[i].match(/^(\d{1,2}:\d{2}\s+[AP]M)$/);
    if (!timeMatch) continue;
    const txTime = timeMatch[1];
    i++;

    // Collect remaining lines until next date or end
    const block: string[] = [];
    while (i < lines.length && !lines[i].match(/^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}$/)) {
      block.push(lines[i]);
      i++;
    }

    const blockText = block.join(' ');

    // Skip non-bet transactions we don't care about
    if (blockText.includes('Cashout - Tournament') || blockText.includes('Table Buy In')) continue;

    // Deposit
    if (blockText.includes('Deposit') || blockText.includes('Bitcoin')) {
      const amtMatch = blockText.match(/\+?\$?([\d,]+\.?\d*)/);
      const balMatch = blockText.match(/\$([\d,]+\.?\d*)\s*$/);
      if (amtMatch) {
        txs.push({
          date: txDate, time: txTime, type: 'deposit',
          game: '', pick: '', odds: '',
          amount: parseFloat(amtMatch[1].replace(',', '')),
          balance: balMatch ? parseFloat(balMatch[1].replace(',', '')) : 0,
          result: '', reward_points: 0,
        });
      }
      continue;
    }

    // Parse bet: look for WIN/LOSS/VOID/PLACED
    let result = '';
    let txType = '';
    if (blockText.includes('WIN') || blockText.includes('Win')) { result = 'win'; txType = 'win'; }
    else if (blockText.includes('LOSS') || blockText.includes('Loss')) { result = 'loss'; txType = 'loss'; }
    else if (blockText.includes('VOID') || blockText.includes('Push')) { result = 'void'; txType = 'void'; }
    else if (blockText.includes('PLACED')) { txType = 'placed'; }
    else continue;

    // Extract odds from parentheses: (-110), (+750), (-125)
    const oddsMatch = blockText.match(/\(([+-]\d+)\)/);
    const odds = oddsMatch ? oddsMatch[1] : '';

    // Extract amount: +$450.00 or -$250.00 or $0.00
    const amtMatch = blockText.match(/([+-])?\$([\d,]+\.?\d*)\s+\$([\d,]+\.?\d*)$/);
    let amount = 0;
    let balance = 0;
    if (amtMatch) {
      const sign = amtMatch[1] === '-' ? -1 : 1;
      amount = sign * parseFloat(amtMatch[2].replace(',', ''));
      balance = parseFloat(amtMatch[3].replace(',', ''));
    } else {
      // Fallback: find last dollar amounts
      const allAmounts = [...blockText.matchAll(/([+-])?\$([\d,]+\.?\d*)/g)];
      if (allAmounts.length >= 1) {
        const last = allAmounts[allAmounts.length - 1];
        balance = parseFloat(last[2].replace(',', ''));
        if (allAmounts.length >= 2) {
          const prev = allAmounts[allAmounts.length - 2];
          const sign = prev[1] === '-' ? -1 : 1;
          amount = sign * parseFloat(prev[2].replace(',', ''));
        }
      }
    }

    // Extract game and pick from block
    // "Texas State -2.5 (-125) Win North Texas @ Texas State"
    const gameMatch = blockText.match(/(\w[\w\s]+?)\s+@\s+(\w[\w\s]+?)(?:\s|$)/);
    const game = gameMatch ? `${gameMatch[1].trim()} @ ${gameMatch[2].trim()}` : '';

    // Pick: everything before the odds in parens, after WIN/LOSS/PLACED
    const pickMatch = blockText.match(/(?:WIN|LOSS|VOID|PLACED)\s+(?:TO WIN \$[\d.]+\s+)?(.+?)\s+\([+-]\d+\)/i);
    const pick = pickMatch ? pickMatch[1].trim() : '';

    // Reward points
    const rpMatch = block.join(' ').match(/([\d,]+\.?\d*)\s+[\d,]+\.?\d*\s+[+-]?\$?/);
    const rewardPoints = rpMatch ? parseFloat(rpMatch[1].replace(',', '')) : 0;

    txs.push({
      date: txDate, time: txTime, type: txType,
      game, pick, odds, amount, balance,
      result, reward_points: rewardPoints,
    });
  }

  return txs;
}

// ── Component ────────────────────────────────────────────────────────────────

export function WinStreakCalculator() {
  // Inputs
  const [baseBet, setBaseBet] = useState(25);
  const [winRate, setWinRate] = useState(55);
  const [bankroll, setBankroll] = useState(728);
  const [targetStreak, setTargetStreak] = useState(5);
  const [betType, setBetType] = useState<BetType>('spread');
  const [customJuice, setCustomJuice] = useState(-110);
  const [mlOdds, setMlOdds] = useState(-150);
  const [activeTab, setActiveTab] = useState<TabId>('tracker');

  // DB-backed tracker
  const [sequences, setSequences] = useState<DbSequence[]>([]);
  const [activeSeq, setActiveSeq] = useState<DbSequence | null>(null);
  const [activeBets, setActiveBets] = useState<DbBet[]>([]);
  const [stats, setStats] = useState<Record<string, number>>({});
  const [historyStats, setHistoryStats] = useState<HistoryStats | null>(null);
  const [loading, setLoading] = useState(false);

  // Bet form
  const [betGame, setBetGame] = useState('');
  const [betPick, setBetPick] = useState('');
  const [betOdds, setBetOdds] = useState(-110);
  const [betCategory, setBetCategory] = useState<'core' | 'flier'>('core');
  const [betNotes, setBetNotes] = useState('');

  // Import
  const [importText, setImportText] = useState('');
  const [importResult, setImportResult] = useState<string | null>(null);

  // Sim
  const [simResults, setSimResults] = useState<ReturnType<typeof runMonteCarlo> | null>(null);
  const [simming, setSimming] = useState(false);

  // Derived
  const wr = winRate / 100;
  const juice = betType === 'spread' ? -110 : betType === 'moneyline' ? mlOdds : customJuice;
  const multiplier = americanToDecimal(juice);

  const authHeaders = (): HeadersInit => {
    const token = localStorage.getItem('auth_token');
    return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  };

  const fetchSequences = useCallback(async () => {
    try {
      const r = await fetch(getApiUrl('f5/streaks/sequences'), { headers: authHeaders() });
      if (!r.ok) return;
      const d = await r.json();
      const all: DbSequence[] = d.sequences ?? [];
      setSequences(all.filter(s => s.status !== 'active'));
      const active = all.find(s => s.status === 'active');
      if (active) {
        setActiveSeq(active);
        const dr = await fetch(getApiUrl(`f5/streaks/sequences/${active.id}`), { headers: authHeaders() });
        if (dr.ok) {
          const dd = await dr.json();
          setActiveBets(dd.bets ?? []);
        }
      } else {
        setActiveSeq(null);
        setActiveBets([]);
      }
    } catch { /* API not available yet */ }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const r = await fetch(getApiUrl('f5/streaks/stats'), { headers: authHeaders() });
      if (r.ok) setStats(await r.json());
    } catch { /* */ }
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      const r = await fetch(getApiUrl('f5/streaks/history'), { headers: authHeaders() });
      if (r.ok) setHistoryStats(await r.json());
    } catch { /* */ }
  }, []);

  useEffect(() => { fetchSequences(); fetchStats(); fetchHistory(); }, [fetchSequences, fetchStats, fetchHistory]);

  // ── Payout ladder ────────────────────────────────────────────────────────
  const ladder = useMemo(() => {
    const rows = [];
    for (let w = 1; w <= 10; w++) {
      const payout = streakPayout(baseBet, w, multiplier);
      const profit = payout - baseBet;
      const prob = streakProb(wr, w);
      const att = avgAttemptsToHit(wr, w);
      const costToGet = (att - 1) * baseBet;
      const expectedNet = profit - costToGet;
      rows.push({ wins: w, payout, profit, prob, attempts: att, costToGet, expectedNet });
    }
    return rows;
  }, [baseBet, wr, multiplier]);

  const phases = useMemo(() => [
    { name: 'Phase 1: Foundation', target: 2, color: '#6ee7b7',
      desc: `Grind 2-win streaks (${fmtPct(streakProb(wr, 2))} hit rate). Build bankroll.` },
    { name: 'Phase 2: Accelerate', target: 3, color: '#93c5fd',
      desc: `Press into 3-win streaks (${fmtPct(streakProb(wr, 3))} hit rate). Use Phase 1 profits.` },
    { name: 'Phase 3: Big Run', target: targetStreak, color: '#c4b5fd',
      desc: `House money for ${targetStreak}+ win streaks. ${fmtMoney(streakPayout(baseBet, targetStreak, multiplier))} payout.` },
  ].map(p => {
    const att = avgAttemptsToHit(wr, p.target);
    const payout = streakPayout(baseBet, p.target, multiplier);
    const profit = payout - baseBet;
    return { ...p, prob: streakProb(wr, p.target), attempts: att, payout, profit, expectedCost: (att - 1) * baseBet, netExpected: profit - (att - 1) * baseBet };
  }), [baseBet, wr, multiplier, targetStreak]);

  // ── API-backed tracker ───────────────────────────────────────────────────
  async function startNewSequence() {
    setLoading(true);
    try {
      const r = await fetch(getApiUrl('f5/streaks/sequences'), {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ base_bet: baseBet, target_streak: targetStreak, bet_type: betType, juice }),
      });
      if (!r.ok) { const e = await r.json(); alert(e.detail || 'Error'); return; }
      await fetchSequences(); await fetchStats();
    } finally { setLoading(false); }
  }

  async function addBet() {
    if (!activeSeq || !betGame.trim() || !betPick.trim()) return;
    setLoading(true);
    try {
      const r = await fetch(getApiUrl(`f5/streaks/sequences/${activeSeq.id}/bets`), {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({
          game_description: betGame, pick: betPick, odds: betOdds,
          bet_category: betCategory, notes: betNotes || undefined,
        }),
      });
      if (!r.ok) { const e = await r.json(); alert(e.detail || 'Error'); return; }
      setBetGame(''); setBetPick(''); setBetNotes(''); setBetOdds(-110);
      await fetchSequences();
    } finally { setLoading(false); }
  }

  async function gradeBet(betId: number, result: string) {
    setLoading(true);
    try {
      const r = await fetch(getApiUrl(`f5/streaks/bets/${betId}/grade`), {
        method: 'PATCH', headers: authHeaders(),
        body: JSON.stringify({ result }),
      });
      if (!r.ok) { const e = await r.json(); alert(e.detail || 'Error'); return; }
      await fetchSequences(); await fetchStats(); await fetchHistory();
    } finally { setLoading(false); }
  }

  async function cashOutSeq() {
    if (!activeSeq) return;
    setLoading(true);
    try {
      await fetch(getApiUrl(`f5/streaks/sequences/${activeSeq.id}/cashout`), {
        method: 'PATCH', headers: authHeaders(),
      });
      await fetchSequences(); await fetchStats();
    } finally { setLoading(false); }
  }

  async function cancelSeq() {
    if (!activeSeq) return;
    setLoading(true);
    try {
      await fetch(getApiUrl(`f5/streaks/sequences/${activeSeq.id}`), {
        method: 'DELETE', headers: authHeaders(),
      });
      await fetchSequences(); await fetchStats();
    } finally { setLoading(false); }
  }

  async function handleImport() {
    if (!importText.trim()) return;
    setLoading(true);
    try {
      const parsed = parseBovadaTransactions(importText);
      if (parsed.length === 0) {
        setImportResult('No transactions found. Make sure you pasted the full Bovada transaction page.');
        return;
      }
      const r = await fetch(getApiUrl('f5/streaks/import'), {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ transactions: parsed }),
      });
      if (r.ok) {
        const d = await r.json();
        setImportResult(`Imported ${d.inserted} transactions (${d.skipped} duplicates skipped)`);
        setImportText('');
        await fetchHistory();
      }
    } finally { setLoading(false); }
  }

  const pendingBet = activeBets.find(b => b.result === 'pending');
  const gradedBets = activeBets.filter(b => b.result !== 'pending');
  const activeWins = activeBets.filter(b => b.result === 'win').length;
  const runway = Math.floor(bankroll / baseBet);

  const runSim = () => {
    setSimming(true);
    setTimeout(() => {
      const result = runMonteCarlo(baseBet, targetStreak, wr, bankroll, multiplier, 10000);
      setSimResults(result);
      setSimming(false);
    }, 50);
  };

  // ── Hardcoded current run data (from Bovada paste) ─────────────────────
  const currentRun = {
    startBalance: 0.76,
    currentBalance: 727.79,
    multiplier: 958,
    bets: [
      { game: 'Bills -5.5', odds: -110, risk: 159, result: 'win', pnl: 144.55, balance: 304.31, pressPercent: 99, category: 'core' as const },
      { game: 'Under 53.5 MIA/WF', odds: -115, risk: 200, result: 'win', pnl: 173.91, balance: 527.79, pressPercent: 66, category: 'core' as const },
      { game: 'Under 59.5 MIA/WF', odds: -115, risk: 80, result: 'win', pnl: 69.57, balance: 527.79, pressPercent: 26, category: 'core' as const },
      { game: 'Wake Forest ML', odds: 750, risk: 20, result: 'loss', pnl: -20, balance: 4.31, pressPercent: 7, category: 'flier' as const },
      { game: 'Texas State -2.5', odds: -125, risk: 250, result: 'win', pnl: 200, balance: 727.79, pressPercent: 47, category: 'core' as const },
    ],
    coreRecord: '4-0',
    flierRecord: '0-1',
    phases: [
      { label: 'All-in send', balance: 0.76, date: 'Sep 17' },
      { label: 'Bills WIN', balance: 304.31, date: 'Sep 17' },
      { label: 'Wake unders WIN', balance: 527.79, date: 'Sep 18' },
      { label: 'Texas State WIN', balance: 727.79, date: 'Sep 19' },
    ],
  };

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6">

      {/* ── STREAK BANNER ── */}
      <div className="bg-gradient-to-r from-emerald-900/60 via-emerald-800/40 to-slate-900 border border-emerald-500/30 rounded-xl p-5 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl" />
        <div className="relative flex items-center justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-3xl font-black text-emerald-400">4-0</span>
              <span className="text-sm font-bold text-emerald-300 bg-emerald-500/20 px-2.5 py-1 rounded-full">CORE STREAK</span>
              <span className="text-xs text-slate-400 bg-slate-700/50 px-2 py-1 rounded-full">0-1 fliers</span>
            </div>
            <div className="text-sm text-slate-300">
              <span className="text-emerald-400 font-bold">{fmtMoney(currentRun.currentBalance)}</span>
              <span className="text-slate-500 mx-2">from</span>
              <span className="text-slate-400">{fmtMoney(currentRun.startBalance)}</span>
              <span className="text-slate-500 mx-2">=</span>
              <span className="text-emerald-300 font-bold">{currentRun.multiplier}x return</span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-slate-400 font-bold uppercase tracking-wider mb-1">Sep 17-19 Run</div>
            <div className="text-2xl font-black text-emerald-400">+{fmtMoney(currentRun.currentBalance - currentRun.startBalance)}</div>
          </div>
        </div>

        {/* Balance curve mini-chart */}
        <div className="mt-4 flex items-end gap-1 h-12">
          {currentRun.phases.map((phase, i) => {
            const maxBal = Math.max(...currentRun.phases.map(p => p.balance));
            const h = Math.max(4, (phase.balance / maxBal) * 48);
            return (
              <div key={i} className="flex-1 flex flex-col items-center gap-1">
                <div
                  className="w-full rounded-t transition-all bg-emerald-500/60 hover:bg-emerald-400/80 relative group"
                  style={{ height: `${h}px` }}
                >
                  <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 text-emerald-300 text-[10px] font-bold px-2 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                    {fmtMoney(phase.balance)}
                  </div>
                </div>
                <span className="text-[9px] text-slate-500">{phase.date}</span>
              </div>
            );
          })}
        </div>

        {/* Press taper visualization */}
        <div className="mt-3 pt-3 border-t border-emerald-700/30">
          <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-2 font-bold">Press Taper</div>
          <div className="flex gap-2">
            {currentRun.bets.filter(b => b.category === 'core').map((bet, i) => (
              <div key={i} className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-slate-400 truncate">{bet.game.split(' ').slice(0, 2).join(' ')}</span>
                  <span className="text-[10px] text-emerald-400 font-bold">{bet.pressPercent}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-slate-700 overflow-hidden">
                  <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${bet.pressPercent}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Tab Navigation ── */}
      <div className="flex gap-1 bg-slate-800/50 rounded-lg p-1">
        {([
          { id: 'tracker' as TabId, label: 'Tracker' },
          { id: 'ladder' as TabId, label: 'Ladder & Strategy' },
          { id: 'simulate' as TabId, label: 'Simulator' },
          { id: 'builder' as TabId, label: 'Progression Builder' },
          { id: 'history' as TabId, label: 'History' },
        ]).map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 px-4 py-2 rounded-md text-sm font-bold transition-all ${
              activeTab === tab.id
                ? 'bg-blue-600 text-white shadow-lg'
                : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Bet Type + Inputs (always visible) ── */}
      <div className="space-y-4">
        <div className="flex gap-2">
          {([
            { key: 'spread' as BetType, label: 'Spreads / Totals', sub: '-110' },
            { key: 'moneyline' as BetType, label: 'Moneyline', sub: 'Variable' },
            { key: 'custom' as BetType, label: 'Custom Juice', sub: 'Any odds' },
          ]).map(tab => (
            <button
              key={tab.key}
              onClick={() => setBetType(tab.key)}
              className={`px-4 py-2.5 rounded-lg text-sm font-bold transition-all ${
                betType === tab.key
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              {tab.label}
              <span className={`block text-[10px] mt-0.5 ${betType === tab.key ? 'text-blue-200' : 'text-slate-600'}`}>{tab.sub}</span>
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Base Bet</label>
            <div className="flex items-center gap-1">
              <span className="text-slate-500">$</span>
              <input type="number" value={baseBet} onChange={e => setBaseBet(Number(e.target.value) || 0)}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2.5 text-white font-bold text-lg focus:border-blue-500 focus:outline-none" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Win Rate %</label>
            <input type="number" value={winRate} onChange={e => setWinRate(Number(e.target.value) || 0)} min={40} max={75}
              className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2.5 text-white font-bold text-lg focus:border-blue-500 focus:outline-none" />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Bankroll</label>
            <div className="flex items-center gap-1">
              <span className="text-slate-500">$</span>
              <input type="number" value={bankroll} onChange={e => setBankroll(Number(e.target.value) || 0)}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2.5 text-white font-bold text-lg focus:border-blue-500 focus:outline-none" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Target Streak</label>
            <select value={targetStreak} onChange={e => setTargetStreak(Number(e.target.value))}
              className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2.5 text-white font-bold text-lg focus:border-blue-500 focus:outline-none">
              {[3, 4, 5, 6, 7, 8].map(n => <option key={n} value={n}>{n} wins</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
              {betType === 'spread' ? 'Juice (fixed)' : betType === 'moneyline' ? 'ML Odds' : 'Custom Odds'}
            </label>
            {betType === 'spread' ? (
              <div className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-slate-400 font-bold text-lg">-110</div>
            ) : betType === 'moneyline' ? (
              <input type="number" value={mlOdds} onChange={e => setMlOdds(Number(e.target.value) || -110)}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2.5 text-white font-bold text-lg focus:border-blue-500 focus:outline-none" />
            ) : (
              <input type="number" value={customJuice} onChange={e => setCustomJuice(Number(e.target.value) || -110)}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2.5 text-white font-bold text-lg focus:border-blue-500 focus:outline-none" />
            )}
            <div className="text-[10px] text-slate-600 mt-1">Multiplier: {multiplier.toFixed(3)}x per win</div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-emerald-900/30 border border-emerald-700/40 rounded-lg p-4 text-center">
            <div className="text-xs text-emerald-400 font-bold uppercase mb-1">{targetStreak}-Win Payout</div>
            <div className="text-2xl font-black text-emerald-300">{fmtMoney(streakPayout(baseBet, targetStreak, multiplier))}</div>
            <div className="text-xs text-emerald-500 mt-1">+{fmtMoney(streakProfit(baseBet, targetStreak, multiplier))} profit</div>
          </div>
          <div className="bg-blue-900/30 border border-blue-700/40 rounded-lg p-4 text-center">
            <div className="text-xs text-blue-400 font-bold uppercase mb-1">Hit Probability</div>
            <div className="text-2xl font-black text-blue-300">{fmtPct(streakProb(wr, targetStreak))}</div>
            <div className="text-xs text-blue-500 mt-1">per attempt</div>
          </div>
          <div className="bg-purple-900/30 border border-purple-700/40 rounded-lg p-4 text-center">
            <div className="text-xs text-purple-400 font-bold uppercase mb-1">Avg Attempts</div>
            <div className="text-2xl font-black text-purple-300">{avgAttemptsToHit(wr, targetStreak)}</div>
            <div className="text-xs text-purple-500 mt-1">to hit streak</div>
          </div>
          <div className="bg-slate-800 border border-slate-700/40 rounded-lg p-4 text-center">
            <div className="text-xs text-slate-400 font-bold uppercase mb-1">Bankroll Runway</div>
            <div className="text-2xl font-black text-slate-200">{runway} bets</div>
            <div className="text-xs text-slate-500 mt-1">{runway >= avgAttemptsToHit(wr, targetStreak) ? 'Sufficient' : 'May bust'}</div>
          </div>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════════════ */}
      {/* TAB: TRACKER                                                      */}
      {/* ══════════════════════════════════════════════════════════════════ */}
      {activeTab === 'tracker' && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-700 flex items-center justify-between flex-wrap gap-3">
            <div>
              <h3 className="text-lg font-bold text-white">Sequence Tracker</h3>
              <p className="text-xs text-slate-400 mt-1">Log bets as core plays or fliers. Grade results. Track your press.</p>
            </div>
            <div className="flex gap-2">
              {!activeSeq ? (
                <button onClick={startNewSequence} disabled={loading}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm rounded-lg transition-colors disabled:opacity-50">
                  {loading ? 'Starting...' : 'Start New Sequence'}
                </button>
              ) : (
                <div className="flex gap-2">
                  {activeWins > 0 && (
                    <button onClick={cashOutSeq} disabled={loading}
                      className="px-4 py-2 bg-yellow-600 hover:bg-yellow-500 text-white font-bold text-sm rounded-lg transition-colors disabled:opacity-50">
                      Cash Out ({fmtMoney(streakPayout(activeSeq.base_bet, activeWins, americanToDecimal(activeSeq.juice)))})
                    </button>
                  )}
                  <button onClick={cancelSeq} disabled={loading}
                    className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm rounded-lg transition-colors disabled:opacity-50">
                    Cancel
                  </button>
                </div>
              )}
            </div>
          </div>

          {activeSeq && (
            <div className="border-b border-blue-700/30">
              <div className="px-5 pt-4 pb-2">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-bold text-blue-400">Sequence #{activeSeq.id}</span>
                  <span className="text-sm font-bold text-white">
                    {activeWins}/{activeSeq.target_streak} wins · Value: {fmtMoney(
                      activeWins > 0 ? streakPayout(activeSeq.base_bet, activeWins, americanToDecimal(activeSeq.juice)) : activeSeq.base_bet
                    )}
                  </span>
                </div>
                <div className="h-2 rounded-full bg-slate-700 overflow-hidden">
                  <div className="h-full bg-emerald-500 transition-all" style={{ width: `${(activeWins / activeSeq.target_streak) * 100}%` }} />
                </div>
                <div className="mt-2 text-xs text-slate-500">
                  Base: {fmtMoney(activeSeq.base_bet)} · {activeSeq.bet_type} ({activeSeq.juice}) · {americanToDecimal(activeSeq.juice).toFixed(3)}x/win
                </div>
              </div>

              {gradedBets.length > 0 && (
                <div className="px-5 py-2 space-y-1.5">
                  {gradedBets.map(b => (
                    <div key={b.id} className="flex items-center justify-between text-sm bg-slate-900/40 rounded-lg px-3 py-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className={`text-xs font-bold px-2 py-0.5 rounded flex-shrink-0 ${
                          b.result === 'win' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                        }`}>{b.result.toUpperCase()}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold flex-shrink-0 ${
                          b.bet_category === 'core' ? 'bg-blue-500/20 text-blue-400' : 'bg-amber-500/20 text-amber-400'
                        }`}>{b.bet_category.toUpperCase()}</span>
                        <span className="text-slate-300 font-semibold truncate">{b.game_description}</span>
                        <span className="text-slate-500 text-xs flex-shrink-0">{b.pick}</span>
                      </div>
                      <div className="flex items-center gap-3 flex-shrink-0">
                        <span className="text-xs text-slate-500">{fmtMoney(b.bet_amount)} → {fmtMoney(b.actual_payout)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {pendingBet && (
                <div className="px-5 py-3 bg-yellow-900/10 border-y border-yellow-700/30">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-bold text-yellow-400">Pending: {pendingBet.game_description}</div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        {pendingBet.pick} · {pendingBet.bet_category.toUpperCase()} · Bet: {fmtMoney(pendingBet.bet_amount)} → Potential: {fmtMoney(pendingBet.potential_payout)}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => gradeBet(pendingBet.id, 'win')} disabled={loading}
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm rounded-lg disabled:opacity-50">WIN</button>
                      <button onClick={() => gradeBet(pendingBet.id, 'loss')} disabled={loading}
                        className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white font-bold text-sm rounded-lg disabled:opacity-50">LOSS</button>
                      <button onClick={() => gradeBet(pendingBet.id, 'push')} disabled={loading}
                        className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm rounded-lg disabled:opacity-50">PUSH</button>
                    </div>
                  </div>
                </div>
              )}

              {!pendingBet && activeSeq.status === 'active' && (
                <div className="px-5 py-4 bg-slate-900/40">
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                    Add Bet #{activeBets.length + 1}
                    {activeWins > 0 && ` · Pressing: ${fmtMoney(streakPayout(activeSeq.base_bet, activeWins, americanToDecimal(activeSeq.juice)))}`}
                    {activeWins === activeSeq.target_streak - 1 && ' · FINAL BET FOR TARGET!'}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-6 gap-3">
                    <input type="text" placeholder="Game (e.g. Steelers vs Falcons)" value={betGame} onChange={e => setBetGame(e.target.value)}
                      className="md:col-span-2 bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none" />
                    <input type="text" placeholder="Pick (e.g. Steelers -6)" value={betPick} onChange={e => setBetPick(e.target.value)}
                      className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none" />
                    <div className="flex gap-2">
                      <input type="number" placeholder="Odds" value={betOdds} onChange={e => setBetOdds(Number(e.target.value) || -110)}
                        className="w-20 bg-slate-800 border border-slate-600 rounded-lg px-2 py-2 text-white text-sm focus:border-blue-500 focus:outline-none" />
                      <select value={betCategory} onChange={e => setBetCategory(e.target.value as 'core' | 'flier')}
                        className="bg-slate-800 border border-slate-600 rounded-lg px-2 py-2 text-white text-sm focus:border-blue-500 focus:outline-none">
                        <option value="core">Core</option>
                        <option value="flier">Flier</option>
                      </select>
                    </div>
                    <input type="text" placeholder="Notes (optional)" value={betNotes} onChange={e => setBetNotes(e.target.value)}
                      className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none" />
                    <button onClick={addBet} disabled={loading || !betGame.trim() || !betPick.trim()}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm rounded-lg transition-colors disabled:opacity-50">
                      {loading ? 'Adding...' : 'Place Bet'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Completed sequences + stats */}
          {(stats.total_sequences ?? 0) > 0 && (
            <div className="divide-y divide-slate-700/50">
              <div className="px-5 py-3 flex items-center gap-6 text-sm bg-slate-900/40 flex-wrap">
                <span className="font-bold text-white">Record: {stats.wins ?? 0}W-{stats.losses ?? 0}L</span>
                {(stats.cashouts ?? 0) > 0 && <span className="text-yellow-400 font-bold">{stats.cashouts} cashouts</span>}
                <span className={`font-bold ${(stats.total_profit ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  Net: {(stats.total_profit ?? 0) >= 0 ? '+' : ''}{fmtMoney(stats.total_profit ?? 0)}
                </span>
                {(stats.best_sequence ?? 0) > 0 && <span className="text-emerald-500 text-xs">Best: +{fmtMoney(stats.best_sequence ?? 0)}</span>}
                <span className="text-slate-500">{stats.total_sequences ?? 0} total sequences</span>
              </div>
              {sequences.slice(0, 20).map(s => (
                <div key={s.id} className="px-5 py-2.5 flex items-center justify-between text-sm">
                  <div className="flex items-center gap-3">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                      s.status === 'won' ? 'bg-emerald-500/20 text-emerald-400' :
                      s.status === 'cashed_out' ? 'bg-yellow-500/20 text-yellow-400' :
                      s.status === 'cancelled' ? 'bg-slate-700 text-slate-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>{s.status === 'cashed_out' ? 'CASHED' : s.status.toUpperCase()}</span>
                    <span className="text-slate-400 text-xs">{fmtMoney(s.base_bet)} base · {s.target_streak}-streak · {s.juice}</span>
                    <span className="text-slate-600 text-xs">{new Date(s.created_at).toLocaleDateString()}</span>
                  </div>
                  <span className={`font-bold ${s.net_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {s.net_profit >= 0 ? '+' : ''}{fmtMoney(s.net_profit)}
                  </span>
                </div>
              ))}
            </div>
          )}

          {!activeSeq && (stats.total_sequences ?? 0) === 0 && (
            <div className="px-5 py-8 text-center text-slate-500 text-sm">
              Start a new sequence to begin tracking your win streak bets.
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════ */}
      {/* TAB: LADDER & STRATEGY                                            */}
      {/* ══════════════════════════════════════════════════════════════════ */}
      {activeTab === 'ladder' && (
        <div className="space-y-6">
          {/* Payout Ladder */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-700">
              <h3 className="text-lg font-bold text-white">Win Streak Payout Ladder</h3>
              <p className="text-xs text-slate-400 mt-1">
                {betType === 'spread' ? 'Standard -110 juice' : betType === 'moneyline' ? `Moneyline ${mlOdds}` : `Custom ${customJuice}`}
                {' · '}{multiplier.toFixed(3)}x per win · Lose = flat {fmtMoney(baseBet)} reset
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-slate-400 uppercase tracking-wider border-b border-slate-700">
                    <th className="px-4 py-3 text-left">Wins</th>
                    <th className="px-4 py-3 text-right">Bet Size</th>
                    <th className="px-4 py-3 text-right">Total Payout</th>
                    <th className="px-4 py-3 text-right">Net Profit</th>
                    <th className="px-4 py-3 text-right">Hit Rate</th>
                    <th className="px-4 py-3 text-right">Avg Attempts</th>
                    <th className="px-4 py-3 text-right">Expected Net</th>
                  </tr>
                </thead>
                <tbody>
                  {ladder.map(row => (
                    <tr key={row.wins} className={`border-b border-slate-700/50 ${row.wins === targetStreak ? 'bg-blue-900/20' : 'hover:bg-slate-700/30'}`}>
                      <td className="px-4 py-3">
                        <span className={`font-bold ${row.wins === targetStreak ? 'text-blue-400' : 'text-white'}`}>{row.wins}x</span>
                        {row.wins === targetStreak && <span className="ml-2 text-[10px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded font-bold">TARGET</span>}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-300">{fmtMoney(streakPayout(baseBet, row.wins - 1, multiplier))}</td>
                      <td className="px-4 py-3 text-right font-bold text-emerald-400">{fmtMoney(row.payout)}</td>
                      <td className="px-4 py-3 text-right font-bold text-emerald-300">+{fmtMoney(row.profit)}</td>
                      <td className="px-4 py-3 text-right text-slate-300">{fmtPct(row.prob)}</td>
                      <td className="px-4 py-3 text-right text-slate-300">{row.attempts}</td>
                      <td className={`px-4 py-3 text-right font-bold ${row.expectedNet >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {row.expectedNet >= 0 ? '+' : ''}{fmtMoney(row.expectedNet)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Ladder Strategy Phases */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-700">
              <h3 className="text-lg font-bold text-white">Ladder Strategy — Build Up with House Money</h3>
              <p className="text-xs text-slate-400 mt-1">Start short, press winnings into bigger runs.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-5">
              {phases.map((phase, i) => (
                <div key={i} className="rounded-lg p-4" style={{ background: `${phase.color}11`, border: `1px solid ${phase.color}44` }}>
                  <div className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: phase.color }}>{phase.name}</div>
                  <div className="text-xs text-slate-400 mb-3">{phase.desc}</div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-slate-500">Target</span><span className="text-white font-bold">{phase.target}-win streak</span></div>
                    <div className="flex justify-between"><span className="text-slate-500">Hit Rate</span><span className="text-white font-bold">{fmtPct(phase.prob)}</span></div>
                    <div className="flex justify-between"><span className="text-slate-500">Avg Attempts</span><span className="text-white font-bold">{phase.attempts}</span></div>
                    <div className="flex justify-between"><span className="text-slate-500">Payout</span><span className="text-emerald-400 font-bold">{fmtMoney(phase.payout)}</span></div>
                    <div className="flex justify-between"><span className="text-slate-500">Cost to get there</span><span className="text-red-400 font-bold">{fmtMoney(phase.expectedCost)}</span></div>
                    <div className="flex justify-between border-t border-slate-700/50 pt-2">
                      <span className="text-slate-400 font-semibold">Expected Net</span>
                      <span className={`font-black ${phase.netExpected >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {phase.netExpected >= 0 ? '+' : ''}{fmtMoney(phase.netExpected)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Comparison Table */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-700">
              <h3 className="text-lg font-bold text-white">Starting Amount Comparison</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-slate-400 uppercase tracking-wider border-b border-slate-700">
                    <th className="px-4 py-3 text-left">Base Bet</th>
                    <th className="px-4 py-3 text-right">3-Streak</th>
                    <th className="px-4 py-3 text-right">5-Streak</th>
                    <th className="px-4 py-3 text-right">6-Streak</th>
                    <th className="px-4 py-3 text-right">7-Streak</th>
                    <th className="px-4 py-3 text-right">Per Loss</th>
                  </tr>
                </thead>
                <tbody>
                  {[10, 25, 50, 100, 250, 500].map(bet => (
                    <tr key={bet} className={`border-b border-slate-700/50 ${bet === baseBet ? 'bg-blue-900/20' : 'hover:bg-slate-700/30'}`}>
                      <td className="px-4 py-3 font-bold text-white">
                        ${bet}
                        {bet === baseBet && <span className="ml-2 text-[10px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded font-bold">YOU</span>}
                      </td>
                      <td className="px-4 py-3 text-right text-emerald-400 font-bold">{fmtMoney(streakPayout(bet, 3, multiplier))}</td>
                      <td className="px-4 py-3 text-right text-emerald-400 font-bold">{fmtMoney(streakPayout(bet, 5, multiplier))}</td>
                      <td className="px-4 py-3 text-right text-emerald-400 font-bold">{fmtMoney(streakPayout(bet, 6, multiplier))}</td>
                      <td className="px-4 py-3 text-right text-emerald-400 font-bold">{fmtMoney(streakPayout(bet, 7, multiplier))}</td>
                      <td className="px-4 py-3 text-right text-red-400">{fmtMoney(bet)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════ */}
      {/* TAB: SIMULATOR                                                    */}
      {/* ══════════════════════════════════════════════════════════════════ */}
      {activeTab === 'simulate' && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-700 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-white">Monte Carlo Simulation</h3>
              <p className="text-xs text-slate-400 mt-1">10,000 runs · {betType === 'spread' ? '-110 juice' : betType === 'moneyline' ? `ML ${mlOdds}` : `${customJuice} odds`} · {winRate}% win rate</p>
            </div>
            <button onClick={runSim} disabled={simming}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm rounded-lg transition-colors disabled:opacity-50">
              {simming ? 'Running...' : 'Run Simulation'}
            </button>
          </div>
          {simResults && (
            <div className="p-5 grid grid-cols-2 md:grid-cols-5 gap-3">
              <div className="bg-slate-900/60 rounded-lg p-3 text-center">
                <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Hit Rate</div>
                <div className="text-xl font-black text-emerald-400">{fmtPct(simResults.hitRate)}</div>
              </div>
              <div className="bg-slate-900/60 rounded-lg p-3 text-center">
                <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Avg Attempts</div>
                <div className="text-xl font-black text-blue-400">{simResults.avgAttempts.toFixed(0)}</div>
              </div>
              <div className="bg-slate-900/60 rounded-lg p-3 text-center">
                <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Avg Profit</div>
                <div className={`text-xl font-black ${simResults.avgProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {simResults.avgProfit >= 0 ? '+' : ''}{fmtMoney(simResults.avgProfit)}
                </div>
              </div>
              <div className="bg-slate-900/60 rounded-lg p-3 text-center">
                <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Median Profit</div>
                <div className={`text-xl font-black ${simResults.medianProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {simResults.medianProfit >= 0 ? '+' : ''}{fmtMoney(simResults.medianProfit)}
                </div>
              </div>
              <div className="bg-slate-900/60 rounded-lg p-3 text-center">
                <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Bust Rate</div>
                <div className={`text-xl font-black ${simResults.bustRate > 0.3 ? 'text-red-400' : simResults.bustRate > 0.1 ? 'text-yellow-400' : 'text-emerald-400'}`}>
                  {fmtPct(simResults.bustRate)}
                </div>
              </div>
            </div>
          )}
          {!simResults && (
            <div className="p-8 text-center text-slate-500 text-sm">
              Run the simulation to see expected outcomes across 10,000 trials.
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════ */}
      {/* TAB: PROGRESSION BUILDER                                          */}
      {/* ══════════════════════════════════════════════════════════════════ */}
      {activeTab === 'builder' && (
        <ProgressionBuilder baseBet={baseBet} winRate={winRate} juice={juice} />
      )}

      {/* ══════════════════════════════════════════════════════════════════ */}
      {/* TAB: HISTORY (Import + Balance Curve + Record)                    */}
      {/* ══════════════════════════════════════════════════════════════════ */}
      {activeTab === 'history' && (
        <div className="space-y-6">

          {/* History stats */}
          {historyStats && historyStats.total_bets > 0 && (
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-700">
                <h3 className="text-lg font-bold text-white">Imported History</h3>
              </div>
              <div className="p-5 grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-slate-900/60 rounded-lg p-3 text-center">
                  <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Record</div>
                  <div className="text-xl font-black text-white">{historyStats.record}</div>
                </div>
                <div className="bg-slate-900/60 rounded-lg p-3 text-center">
                  <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Net P&L</div>
                  <div className={`text-xl font-black ${historyStats.net_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {historyStats.net_pnl >= 0 ? '+' : ''}{fmtMoney(historyStats.net_pnl)}
                  </div>
                </div>
                <div className="bg-slate-900/60 rounded-lg p-3 text-center">
                  <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Core</div>
                  <div className="text-xl font-black text-blue-400">{historyStats.core_record}</div>
                </div>
                <div className="bg-slate-900/60 rounded-lg p-3 text-center">
                  <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Fliers</div>
                  <div className="text-xl font-black text-amber-400">{historyStats.flier_record}</div>
                </div>
              </div>
              <div className="px-5 pb-4 grid grid-cols-2 md:grid-cols-3 gap-3">
                <div className="bg-slate-900/60 rounded-lg p-3 text-center">
                  <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Current Streak</div>
                  <div className="text-xl font-black text-emerald-400">{historyStats.current_streak}W</div>
                </div>
                <div className="bg-slate-900/60 rounded-lg p-3 text-center">
                  <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Best Streak</div>
                  <div className="text-xl font-black text-purple-400">{historyStats.best_streak}W</div>
                </div>
                <div className="bg-slate-900/60 rounded-lg p-3 text-center">
                  <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Deposited</div>
                  <div className="text-xl font-black text-slate-300">{fmtMoney(historyStats.deposits)}</div>
                </div>
              </div>

              {/* Balance Curve */}
              {historyStats.balance_curve.length > 0 && (
                <div className="px-5 pb-5">
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Balance Curve</div>
                  <div className="flex items-end gap-0.5 h-24 bg-slate-900/40 rounded-lg p-3">
                    {historyStats.balance_curve.map((pt, i) => {
                      const maxBal = Math.max(...historyStats.balance_curve.map(p => p.balance));
                      const h = Math.max(2, (pt.balance / maxBal) * 72);
                      const isGreen = i === 0 || pt.balance >= (historyStats.balance_curve[i - 1]?.balance ?? 0);
                      return (
                        <div key={i} className="flex-1 relative group" style={{ minWidth: '3px' }}>
                          <div
                            className={`w-full rounded-t transition-all ${isGreen ? 'bg-emerald-500/70' : 'bg-red-500/70'}`}
                            style={{ height: `${h}px` }}
                          />
                          <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-slate-800 text-white text-[9px] font-bold px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                            {fmtMoney(pt.balance)} · {pt.date}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Import from Bovada */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-700">
              <h3 className="text-lg font-bold text-white">Import Bovada Transactions</h3>
              <p className="text-xs text-slate-400 mt-1">
                Paste your Bovada Transactions page text. We'll parse dates, bets, results, and balances automatically.
                Core plays vs fliers are auto-classified (longshots under $30 at +300 or higher = flier).
              </p>
            </div>
            <div className="p-5 space-y-3">
              <textarea
                value={importText}
                onChange={e => setImportText(e.target.value)}
                placeholder="Paste your Bovada transaction history here..."
                rows={8}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white text-sm font-mono focus:border-blue-500 focus:outline-none resize-y"
              />
              <div className="flex items-center gap-3">
                <button onClick={handleImport} disabled={loading || !importText.trim()}
                  className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm rounded-lg transition-colors disabled:opacity-50">
                  {loading ? 'Importing...' : 'Import Transactions'}
                </button>
                {importResult && (
                  <span className="text-sm text-emerald-400 font-bold">{importResult}</span>
                )}
              </div>
            </div>
          </div>

          {/* Full bet log from current run (hardcoded from paste analysis) */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-700">
              <h3 className="text-lg font-bold text-white">Current Run — Sep 17-19</h3>
              <p className="text-xs text-slate-400 mt-1">$0.76 → $727.79 · 958x return</p>
            </div>
            <div className="divide-y divide-slate-700/50">
              {currentRun.bets.map((bet, i) => (
                <div key={i} className="px-5 py-3 flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                      bet.result === 'win' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                    }`}>{bet.result.toUpperCase()}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                      bet.category === 'core' ? 'bg-blue-500/20 text-blue-400' : 'bg-amber-500/20 text-amber-400'
                    }`}>{bet.category.toUpperCase()}</span>
                    <span className="text-white font-semibold">{bet.game}</span>
                    <span className="text-slate-500 text-xs">({bet.odds > 0 ? '+' : ''}{bet.odds})</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-slate-400 text-xs">{fmtMoney(bet.risk)} risked</span>
                    <span className="text-xs text-slate-500">{bet.pressPercent}% pressed</span>
                    <span className={`font-bold ${bet.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {bet.pnl >= 0 ? '+' : ''}{fmtMoney(bet.pnl)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
