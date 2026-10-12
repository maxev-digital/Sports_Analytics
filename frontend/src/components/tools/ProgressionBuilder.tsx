import { useState, useMemo } from 'react';

// ── Types ────────────────────────────────────────────────────────────────────

interface ProgressionBuilderProps {
  baseBet: number;
  winRate: number; // 0-100
  juice: number;   // american odds, e.g. -110
}

interface ProformaRow {
  win: number;
  bet: number;
  payout: number;
  runningProfit: number;
}

interface RunData {
  index: number;
  base: number;
  target: number;
  proforma: ProformaRow[];
  profit: number;
  maxBet: number;
  cumulative: number;
  pHit: number;
  expectedFails: number;
  avgLoss: number;
  grindCost: number;
  netExpected: number;
  cumulativeNet: number;
}

// ── Math ─────────────────────────────────────────────────────────────────────

function payoutMult(juice: number): number {
  return juice > 0 ? juice / 100 : 100 / Math.abs(juice);
}

function buildProforma(base: number, target: number, pm: number): ProformaRow[] {
  const rows: ProformaRow[] = [];
  let running = 0;
  for (let w = 1; w <= target; w++) {
    const bet = base * Math.pow(2, w - 1);
    const payout = Math.round(bet * pm * 100) / 100;
    running += payout;
    rows.push({ win: w, bet, payout, runningProfit: Math.round(running * 100) / 100 });
  }
  return rows;
}

function lossAtStep(base: number, step: number, pm: number): number {
  let won = 0;
  for (let w = 1; w < step; w++) {
    won += base * Math.pow(2, w - 1) * pm;
  }
  return base * Math.pow(2, step - 1) - won;
}

function calcAvgLossPerFail(base: number, target: number, wr: number, pm: number): number {
  const pFail = 1 - Math.pow(wr, target);
  if (pFail <= 0) return 0;
  let weighted = 0;
  for (let step = 1; step <= target; step++) {
    const pFailHere = Math.pow(wr, step - 1) * (1 - wr);
    weighted += pFailHere * lossAtStep(base, step, pm);
  }
  return weighted / pFail;
}

// ── Formatting ───────────────────────────────────────────────────────────────

const fmt = (n: number) => {
  const abs = Math.abs(Math.round(n));
  const str = abs.toLocaleString('en-US');
  return n >= 0 ? `$${str}` : `-$${str}`;
};
const fmtPct = (n: number) => `${(n * 100).toFixed(1)}%`;

// ── Component ────────────────────────────────────────────────────────────────

export function ProgressionBuilder({ baseBet: parentBase, winRate: parentWR, juice: parentJuice }: ProgressionBuilderProps) {
  // Builder-specific inputs
  const [streakTargets, setStreakTargets] = useState([5, 6, 7]);
  const [escalateBase, setEscalateBase] = useState(true);
  const [escalationRate, setEscalationRate] = useState(2);
  const [profitTarget, setProfitTarget] = useState(50000);
  const [expandedRun, setExpandedRun] = useState<number | null>(0);
  const [addingTarget, setAddingTarget] = useState(false);
  const [newTarget, setNewTarget] = useState(5);

  // Use parent values
  const wr = parentWR / 100;
  const pm = payoutMult(parentJuice);

  // ── Build runs until profit target ──
  const runs: RunData[] = useMemo(() => {
    const result: RunData[] = [];
    let cumulative = 0;
    let cumulativeNet = 0;
    let i = 0;

    while (cumulative < profitTarget && i < 30) {
      const target = streakTargets[i % streakTargets.length];
      const base = escalateBase
        ? parentBase * Math.pow(escalationRate, i)
        : parentBase;

      const proforma = buildProforma(base, target, pm);
      const profit = proforma[proforma.length - 1].runningProfit;
      const maxBet = base * Math.pow(2, target - 1);
      cumulative += profit;

      const pHit = Math.pow(wr, target);
      const expectedFails = pHit > 0 ? (1 / pHit) - 1 : Infinity;
      const avgLoss = calcAvgLossPerFail(base, target, wr, pm);
      const grindCost = expectedFails * avgLoss;
      const netExpected = profit - grindCost;
      cumulativeNet += netExpected;

      result.push({
        index: i, base, target, proforma, profit, maxBet, cumulative,
        pHit, expectedFails, avgLoss, grindCost, netExpected, cumulativeNet,
      });
      i++;
    }
    return result;
  }, [parentBase, streakTargets, escalateBase, escalationRate, profitTarget, wr, pm]);

  // ── Summary stats ──
  const totalClean = runs.length > 0 ? runs[runs.length - 1].cumulative : 0;
  const totalNet = runs.length > 0 ? runs[runs.length - 1].cumulativeNet : 0;
  const totalGrind = runs.reduce((s, r) => s + r.grindCost, 0);
  const totalWins = runs.reduce((s, r) => s + r.target, 0);
  const maxBet = runs.length > 0 ? Math.max(...runs.map(r => r.maxBet)) : 0;

  // Bankroll requirement: max shortfall at any point
  let bankrollNeeded = 0;
  let banked = 0;
  for (const run of runs) {
    const shortfall = run.grindCost - banked;
    if (shortfall > 0 && shortfall > bankrollNeeded) bankrollNeeded = shortfall;
    banked += run.netExpected;
  }

  // ── Scenario table ──
  const scenarios = useMemo(() => {
    if (runs.length === 0) return [];
    const totalGrindClean = runs.reduce((s, r) => s + r.grindCost, 0);
    return [
      { label: 'God mode (hit all first try)', failMult: 0, odds: '< 1%' },
      { label: 'Hot streak', failMult: 0.5, odds: '~15%' },
      { label: 'Expected (median)', failMult: 1, odds: '~50%' },
      { label: 'Cold grind', failMult: 1.5, odds: '~25%' },
      { label: 'Ice cold', failMult: 2, odds: '~10%' },
    ].map(s => ({
      ...s,
      grindCost: totalGrindClean * s.failMult,
      profit: totalClean - totalGrindClean * s.failMult,
    }));
  }, [runs, totalClean]);

  // ── Streak target management ──
  const addTarget = () => {
    setStreakTargets([...streakTargets, newTarget]);
    setAddingTarget(false);
  };
  const removeTarget = (idx: number) => {
    if (streakTargets.length <= 1) return;
    setStreakTargets(streakTargets.filter((_, i) => i !== idx));
  };

  return (
    <div className="space-y-6">

      {/* ── Builder Inputs ── */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-5 space-y-5">
        <div>
          <h3 className="text-lg font-bold text-white mb-1">Progression Builder</h3>
          <p className="text-xs text-slate-400">
            Design a custom positive progression system. Double bets within each streak, escalate the base after each completed run, reset on any loss.
          </p>
        </div>

        {/* Streak Targets */}
        <div>
          <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Streak Target Cycle</label>
          <div className="flex items-center gap-2 flex-wrap">
            {streakTargets.map((t, i) => (
              <div key={i} className="flex items-center gap-1 bg-blue-900/30 border border-blue-700/40 rounded-lg px-3 py-2">
                <span className="text-blue-300 font-bold text-sm">Run {i + 1}:</span>
                <span className="text-white font-black text-lg">{t}</span>
                <span className="text-blue-400 text-xs">wins</span>
                {streakTargets.length > 1 && (
                  <button onClick={() => removeTarget(i)}
                    className="ml-1 text-slate-500 hover:text-red-400 text-xs font-bold transition-colors">x</button>
                )}
              </div>
            ))}
            {addingTarget ? (
              <div className="flex items-center gap-2">
                <select value={newTarget} onChange={e => setNewTarget(Number(e.target.value))}
                  className="bg-slate-800 border border-slate-600 rounded-lg px-2 py-2 text-white text-sm focus:border-blue-500 focus:outline-none">
                  {[3, 4, 5, 6, 7, 8, 9, 10].map(n => <option key={n} value={n}>{n} wins</option>)}
                </select>
                <button onClick={addTarget} className="px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-lg">Add</button>
                <button onClick={() => setAddingTarget(false)} className="px-2 py-2 text-slate-500 hover:text-white text-xs">Cancel</button>
              </div>
            ) : (
              <button onClick={() => setAddingTarget(true)}
                className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 font-bold text-sm rounded-lg border border-slate-600 transition-colors">
                + Add Run
              </button>
            )}
          </div>
          <p className="text-[10px] text-slate-600 mt-1">Cycle repeats after last target. E.g. 5 → 6 → 7 → 5 → 6 → 7...</p>
        </div>

        {/* Escalation + Profit Target */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Escalate Base</label>
            <button
              onClick={() => setEscalateBase(!escalateBase)}
              className={`w-full px-4 py-2.5 rounded-lg text-sm font-bold transition-all ${
                escalateBase
                  ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/30'
                  : 'bg-slate-800 text-slate-400 border border-slate-700'
              }`}
            >
              {escalateBase ? 'ON — Base doubles' : 'OFF — Flat base'}
            </button>
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Escalation Rate</label>
            <select
              value={escalationRate}
              onChange={e => setEscalationRate(Number(e.target.value))}
              disabled={!escalateBase}
              className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2.5 text-white font-bold text-lg focus:border-blue-500 focus:outline-none disabled:opacity-40"
            >
              <option value={1.5}>1.5x</option>
              <option value={2}>2x (double)</option>
              <option value={3}>3x (triple)</option>
              <option value={4}>4x</option>
              <option value={5}>5x</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Profit Target</label>
            <div className="flex items-center gap-1">
              <span className="text-slate-500">$</span>
              <input type="number" value={profitTarget} onChange={e => setProfitTarget(Number(e.target.value) || 0)}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2.5 text-white font-bold text-lg focus:border-blue-500 focus:outline-none" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Using</label>
            <div className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-slate-300 text-sm">
              <div className="font-bold">{fmt(parentBase)} base · {parentJuice} juice</div>
              <div className="text-[10px] text-slate-500 mt-0.5">{parentWR}% win rate · {pm.toFixed(3)}x/win</div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Summary Cards ── */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="bg-emerald-900/30 border border-emerald-700/40 rounded-lg p-4 text-center">
          <div className="text-[10px] text-emerald-400 font-bold uppercase mb-1">Clean Path Profit</div>
          <div className="text-xl font-black text-emerald-300">{fmt(totalClean)}</div>
          <div className="text-[10px] text-emerald-500 mt-1">{runs.length} runs · {totalWins} wins</div>
        </div>
        <div className="bg-blue-900/30 border border-blue-700/40 rounded-lg p-4 text-center">
          <div className="text-[10px] text-blue-400 font-bold uppercase mb-1">Expected Net ({parentWR}%)</div>
          <div className="text-xl font-black text-blue-300">{fmt(totalNet)}</div>
          <div className="text-[10px] text-blue-500 mt-1">After grind losses</div>
        </div>
        <div className="bg-red-900/30 border border-red-700/40 rounded-lg p-4 text-center">
          <div className="text-[10px] text-red-400 font-bold uppercase mb-1">Expected Grind Cost</div>
          <div className="text-xl font-black text-red-300">{fmt(totalGrind)}</div>
          <div className="text-[10px] text-red-500 mt-1">Failed attempts</div>
        </div>
        <div className="bg-purple-900/30 border border-purple-700/40 rounded-lg p-4 text-center">
          <div className="text-[10px] text-purple-400 font-bold uppercase mb-1">Max Single Bet</div>
          <div className="text-xl font-black text-purple-300">{fmt(maxBet)}</div>
          <div className="text-[10px] text-purple-500 mt-1">Highest bet in system</div>
        </div>
        <div className="bg-slate-800 border border-slate-700/40 rounded-lg p-4 text-center">
          <div className="text-[10px] text-slate-400 font-bold uppercase mb-1">Reserve Capital</div>
          <div className="text-xl font-black text-slate-200">{fmt(bankrollNeeded)}</div>
          <div className="text-[10px] text-slate-500 mt-1">To survive grind</div>
        </div>
      </div>

      {/* ── Run-by-Run Scoreboard ── */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-700">
          <h3 className="text-lg font-bold text-white">Run-by-Run Roadmap</h3>
          <p className="text-xs text-slate-400 mt-1">Click any run to see the win-by-win breakdown. {escalateBase ? `Base escalates ${escalationRate}x after each completed run.` : 'Flat base — no escalation.'}</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-slate-400 uppercase tracking-wider border-b border-slate-700">
                <th className="px-4 py-3 text-left">Run</th>
                <th className="px-4 py-3 text-right">Base</th>
                <th className="px-4 py-3 text-right">Streak</th>
                <th className="px-4 py-3 text-right">Max Bet</th>
                <th className="px-4 py-3 text-right">Run Profit</th>
                <th className="px-4 py-3 text-right">Cumulative</th>
                <th className="px-4 py-3 text-right">Hit Odds</th>
                <th className="px-4 py-3 text-right">Grind Cost</th>
                <th className="px-4 py-3 text-right">Net Expected</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run, i) => {
                const isExpanded = expandedRun === i;
                const hitTarget = run.cumulative >= profitTarget && (i === 0 || runs[i - 1].cumulative < profitTarget);
                return (
                  <tbody key={i}>
                    <tr
                      onClick={() => setExpandedRun(isExpanded ? null : i)}
                      className={`border-b border-slate-700/50 cursor-pointer transition-colors ${
                        hitTarget ? 'bg-emerald-900/20' : isExpanded ? 'bg-blue-900/10' : 'hover:bg-slate-700/30'
                      }`}
                    >
                      <td className="px-4 py-3">
                        <span className="font-bold text-white">Run {run.index + 1}</span>
                        {hitTarget && <span className="ml-2 text-[10px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded font-bold">TARGET HIT</span>}
                        {(run.index % streakTargets.length === 0 && run.index > 0) && (
                          <span className="ml-2 text-[10px] bg-slate-700 text-slate-400 px-1.5 py-0.5 rounded">cycle reset</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-300 font-bold">{fmt(run.base)}</td>
                      <td className="px-4 py-3 text-right text-white font-bold">{run.target}-0</td>
                      <td className="px-4 py-3 text-right text-slate-300">{fmt(run.maxBet)}</td>
                      <td className="px-4 py-3 text-right text-emerald-400 font-bold">+{fmt(run.profit)}</td>
                      <td className="px-4 py-3 text-right font-black text-emerald-300">{fmt(run.cumulative)}</td>
                      <td className="px-4 py-3 text-right text-slate-300">{fmtPct(run.pHit)}</td>
                      <td className="px-4 py-3 text-right text-red-400">{fmt(run.grindCost)}</td>
                      <td className={`px-4 py-3 text-right font-bold ${run.netExpected >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {run.netExpected >= 0 ? '+' : ''}{fmt(run.netExpected)}
                      </td>
                    </tr>

                    {/* Expanded proforma */}
                    {isExpanded && (
                      <tr>
                        <td colSpan={9} className="p-0">
                          <div className="bg-slate-900/60 border-y border-slate-700/50">
                            <div className="px-6 py-3">
                              <div className="text-xs font-bold text-blue-400 uppercase tracking-wider mb-3">
                                Run {run.index + 1} — Win-by-Win Breakdown ({fmt(run.base)} base, {run.target} wins)
                              </div>
                              <table className="w-full text-sm">
                                <thead>
                                  <tr className="text-[10px] text-slate-500 uppercase tracking-wider">
                                    <th className="px-3 py-2 text-left">Win #</th>
                                    <th className="px-3 py-2 text-right">Bet Amount</th>
                                    <th className="px-3 py-2 text-right">Payout ({parentJuice})</th>
                                    <th className="px-3 py-2 text-right">Running Profit</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {run.proforma.map(row => (
                                    <tr key={row.win} className="border-t border-slate-800/50">
                                      <td className="px-3 py-1.5 text-slate-300 font-bold">{row.win}</td>
                                      <td className="px-3 py-1.5 text-right text-white">{fmt(row.bet)}</td>
                                      <td className="px-3 py-1.5 text-right text-emerald-400">+{fmt(row.payout)}</td>
                                      <td className="px-3 py-1.5 text-right text-emerald-300 font-bold">{fmt(row.runningProfit)}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>

                              {/* Failure cost table */}
                              <div className="mt-4 pt-3 border-t border-slate-700/50">
                                <div className="text-[10px] text-red-400 font-bold uppercase tracking-wider mb-2">If You Lose At Each Step</div>
                                <div className="flex flex-wrap gap-2">
                                  {run.proforma.map(row => {
                                    const loss = lossAtStep(run.base, row.win, pm);
                                    return (
                                      <div key={row.win} className="bg-slate-800/60 rounded px-3 py-1.5 text-xs">
                                        <span className="text-slate-500">Bet {row.win}:</span>
                                        <span className="text-red-400 font-bold ml-1">-{fmt(loss)}</span>
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>

                              {/* Run grind stats */}
                              <div className="mt-3 pt-3 border-t border-slate-700/50 flex flex-wrap gap-4 text-xs">
                                <span className="text-slate-400">Hit odds: <span className="text-white font-bold">{fmtPct(run.pHit)}</span></span>
                                <span className="text-slate-400">Avg attempts: <span className="text-white font-bold">{Math.ceil(run.expectedFails + 1)}</span></span>
                                <span className="text-slate-400">Avg loss/fail: <span className="text-red-400 font-bold">{fmt(run.avgLoss)}</span></span>
                                <span className="text-slate-400">Total grind cost: <span className="text-red-400 font-bold">{fmt(run.grindCost)}</span></span>
                                <span className="text-slate-400">Net expected: <span className={`font-bold ${run.netExpected >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>{run.netExpected >= 0 ? '+' : ''}{fmt(run.netExpected)}</span></span>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Scenario Outcomes ── */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-700">
          <h3 className="text-lg font-bold text-white">Scenario Outcomes at {parentWR}% Win Rate</h3>
          <p className="text-xs text-slate-400 mt-1">How variance affects your total profit across all {runs.length} runs.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-slate-400 uppercase tracking-wider border-b border-slate-700">
                <th className="px-4 py-3 text-left">Scenario</th>
                <th className="px-4 py-3 text-right">Grind Cost</th>
                <th className="px-4 py-3 text-right">Total Profit</th>
                <th className="px-4 py-3 text-right">Likelihood</th>
              </tr>
            </thead>
            <tbody>
              {scenarios.map((s, i) => (
                <tr key={i} className={`border-b border-slate-700/50 ${s.label.includes('Expected') ? 'bg-blue-900/10' : 'hover:bg-slate-700/30'}`}>
                  <td className="px-4 py-3 text-white font-semibold">{s.label}</td>
                  <td className="px-4 py-3 text-right text-red-400">{fmt(s.grindCost)}</td>
                  <td className={`px-4 py-3 text-right font-black ${s.profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {s.profit >= 0 ? '+' : ''}{fmt(s.profit)}
                  </td>
                  <td className="px-4 py-3 text-right text-slate-300">{s.odds}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Cumulative Balance Curve ── */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-700">
          <h3 className="text-lg font-bold text-white">Cumulative Profit Curve</h3>
          <p className="text-xs text-slate-400 mt-1">Clean path (green) vs expected with grind (blue)</p>
        </div>
        <div className="p-5">
          <div className="flex items-end gap-1 h-32">
            {runs.map((run, i) => {
              const maxVal = Math.max(totalClean, 1);
              const cleanH = Math.max(4, (run.cumulative / maxVal) * 120);
              const netH = Math.max(4, (Math.max(0, run.cumulativeNet) / maxVal) * 120);
              const hitTarget = run.cumulative >= profitTarget && (i === 0 || runs[i - 1].cumulative < profitTarget);
              return (
                <div key={i} className="flex-1 flex items-end gap-0.5 relative group">
                  <div
                    className="flex-1 rounded-t bg-emerald-500/40 transition-all"
                    style={{ height: `${cleanH}px` }}
                  />
                  <div
                    className="flex-1 rounded-t bg-blue-500/60 transition-all"
                    style={{ height: `${netH}px` }}
                  />
                  {hitTarget && (
                    <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[9px] text-emerald-400 font-bold whitespace-nowrap">
                      TARGET
                    </div>
                  )}
                  <div className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[9px] text-slate-600">
                    R{run.index + 1}
                  </div>
                  <div className="absolute -top-16 left-1/2 -translate-x-1/2 bg-slate-800 text-white text-[9px] font-bold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10 border border-slate-700">
                    <div className="text-emerald-400">Clean: {fmt(run.cumulative)}</div>
                    <div className="text-blue-400">Net: {fmt(run.cumulativeNet)}</div>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex justify-center gap-6 mt-8 text-[10px]">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded bg-emerald-500/40" />
              <span className="text-slate-400">Clean path</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded bg-blue-500/60" />
              <span className="text-slate-400">Expected ({parentWR}%)</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── The Rule ── */}
      <div className="bg-gradient-to-r from-emerald-900/30 via-slate-800/50 to-blue-900/30 border border-slate-700 rounded-lg p-5">
        <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2">The Rule</div>
        <p className="text-sm text-slate-300 leading-relaxed">
          One bet at a time. Only fire on high-conviction spreads and totals.
          Double up on wins, walk away on losses.
          {escalateBase && ` After each completed streak, the base escalates ${escalationRate}x — that's where the real money is.`}
          {' '}{fmt(parentBase)} base → {fmt(totalClean)} in {totalWins} wins across {runs.length} runs.
          {totalNet < totalClean && ` At ${parentWR}%, expect ${fmt(totalNet)} after the grind.`}
        </p>
      </div>
    </div>
  );
}
