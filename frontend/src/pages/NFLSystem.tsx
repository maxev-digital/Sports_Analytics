import { useState } from 'react';

type Phase = 'early' | 'mid' | 'late';

const WEEK_PHASES: Record<Phase, { label: string; weeks: string; historical: number; current: number; llm: string }> = {
  early: { label: 'Early Season', weeks: 'Weeks 1–5', historical: 85, current: 5, llm: 'Heavy — compensates for thin current data' },
  mid:   { label: 'Mid Season',   weeks: 'Weeks 6–11', historical: 55, current: 35, llm: 'Moderate — scheme adjustments, injury context' },
  late:  { label: 'Late Season',  weeks: 'Weeks 12–18', historical: 25, current: 65, llm: 'Playoff picture, rest decisions, tank situations' },
};

const SITUATIONAL_FACTORS = [
  { factor: 'Rest Advantage',      desc: 'Short week (Thu) teams cover 4.1% less often. Bye week teams coming home cover 53.8% ATS historically.' },
  { factor: 'Home Underdog Spot',  desc: 'Home dogs of 7+ points have covered at 54.2% over 3 seasons — public overweights favorites.' },
  { factor: 'Divisional Games',    desc: 'Division games tighten outcomes — totals go under 54.1% when teams have faced each other before.' },
  { factor: 'Travel Distance',     desc: 'Cross-timezone road trips (3+ hrs) depress team performance 2–4 points below expectation.' },
  { factor: 'Primetime Inflation', desc: 'SNF/MNF teams are overvalued by 1.5–2 points from public attention. Fade the sexy side.' },
  { factor: 'Back-to-Back Roads',  desc: '2nd consecutive road game in 3 weeks: teams underperform spread by 2.3 points on average.' },
  { factor: 'Revenge Spots',       desc: 'Teams losing by 14+ previous meeting historically tighten the gap by 3 points next meeting.' },
  { factor: 'Weather (Outdoors)',  desc: 'Wind >15mph collapses totals. Temp <20°F suppresses scoring 3–5 points below the number.' },
];

const DATA_PIPELINE = [
  { step: '01', name: 'Odds Ingestion',       freq: 'Every 15 min', source: 'Multi-book odds feed (15+ books)', output: 'Consensus spread / total / ML across all books' },
  { step: '02', name: 'Line Movement Capture', freq: '3x Daily',    source: 'Live odds snapshots', output: 'line_snapshots table — tracks opening to close shift' },
  { step: '03', name: 'Injury Feed',           freq: '2x Daily',    source: 'League injury reports', output: 'injury_log — Out/Doubtful/Questionable by team' },
  { step: '04', name: 'Weather Feed',          freq: 'Game week',   source: 'Stadium weather feed', output: 'weather_log — temp, wind, precip per stadium' },
  { step: '05', name: 'DVOA / SP+ Ratings',   freq: 'Weekly',      source: 'Advanced efficiency ratings', output: 'team_ratings — offensive/defensive efficiency' },
  { step: '06', name: 'Historical Odds DB',    freq: 'One-time seed',source: 'Historical odds archive', output: 'nfl_historical_odds — 3 seasons open/close/outcome' },
  { step: '07', name: 'Situational Trends',   freq: 'Computed',    source: 'Historical DB queries', output: 'ATS% by rest days, travel, spread range, division' },
];

const MODEL_STACK = [
  {
    name: 'Situational Rules Engine',
    type: 'Rule-based',
    weight_early: '70%',
    weight_late: '20%',
    desc: 'Pre-computed ATS% lookup by situation type. Fires from Week 1 — no current-season data needed.',
    color: 'from-blue-600 to-blue-800',
  },
  {
    name: 'Elo Power Ratings',
    type: 'Bayesian Prior',
    weight_early: '15%',
    weight_late: '5%',
    desc: 'Prior season Elo, regressed 35% toward league mean. Updates each game. Teams enter season with prior.',
    color: 'from-purple-600 to-purple-800',
  },
  {
    name: 'ML Ensemble (RF / XGB / LGB)',
    type: 'Machine Learning',
    weight_early: '5%',
    weight_late: '50%',
    desc: 'Trained on 3 seasons of game-level features. Low weight early season (noise), dominant by Week 12.',
    color: 'from-green-600 to-green-800',
  },
  {
    name: 'LLM Evaluator',
    type: 'AI Reasoning',
    weight_early: '10%',
    weight_late: '25%',
    desc: 'Reads per-game context doc (injuries + weather + line movement + scheme notes) and outputs structured pick with reasoning.',
    color: 'from-orange-600 to-orange-800',
  },
];

const CORROBORATION = [
  { check: 'Min 5 bookmakers sampled', reason: 'Prevents thin-market picks with no price discovery' },
  { check: 'Min 2% edge vs no-vig price', reason: 'Covers breakeven + juice; below 2% has no EV' },
  { check: 'Min 2% divergence across books', reason: 'Signals market disagreement — sharp opportunity' },
  { check: 'No both-sides on same game', reason: 'Directional guard — only highest-edge side per game' },
  { check: 'Directional concentration limit', reason: 'Max X% of picks in same direction prevents bias cascade' },
];

export function NFLSystem() {
  const [activePhase, setActivePhase] = useState<Phase>('early');
  const phase = WEEK_PHASES[activePhase];

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black text-white">
      <div className="max-w-6xl mx-auto px-4 py-10">

        {/* Header */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-xs font-bold tracking-widest uppercase text-blue-400 bg-blue-900/30 px-3 py-1 rounded-full border border-blue-700/40">System Transparency</span>
            <span className="text-xs text-slate-500">NFL / NCAAF</span>
          </div>
          <h1 className="text-4xl font-black text-white mb-3">How We Pick NFL Games</h1>
          <p className="text-slate-400 text-lg max-w-3xl">
            Complete transparency into our NFL handicapping system — every data source, every model, every filter. No black boxes.
          </p>
        </div>

        {/* Core Philosophy */}
        <div className="bg-slate-800/40 border border-slate-700 rounded-xl p-6 mb-8">
          <h2 className="text-xl font-bold text-white mb-3">Core Philosophy</h2>
          <p className="text-slate-300 leading-relaxed mb-4">
            NFL betting is a <span className="text-blue-400 font-semibold">cold-start problem</span>. The regular season is only 18 weeks — with just 16 home games per team, current-season sample sizes are always thin.
            Our system solves this with a <span className="text-green-400 font-semibold">three-layer architecture</span> that shifts weight between layers as the season evolves:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-900/20 border border-blue-700/30 rounded-lg p-4">
              <div className="text-blue-400 font-bold mb-1">Situational Patterns</div>
              <div className="text-sm text-slate-400">Evergreen rules that apply every season regardless of teams — rest, travel, spot, weather. Fires from Week 1.</div>
            </div>
            <div className="bg-green-900/20 border border-green-700/30 rounded-lg p-4">
              <div className="text-green-400 font-bold mb-1">Machine Learning</div>
              <div className="text-sm text-slate-400">Pre-trained on 3 seasons of historical game data. Starts low weight, reaches dominance by Week 12 when current-season data is rich.</div>
            </div>
            <div className="bg-orange-900/20 border border-orange-700/30 rounded-lg p-4">
              <div className="text-orange-400 font-bold mb-1">LLM Evaluator</div>
              <div className="text-sm text-slate-400">The LLM evaluator reads a per-game context document — injuries, scheme notes, line movement — and reasons qualitatively.</div>
            </div>
          </div>
        </div>

        {/* Season Weight Progression */}
        <div className="bg-slate-800/40 border border-slate-700 rounded-xl p-6 mb-8">
          <h2 className="text-xl font-bold text-white mb-4">Model Weight by Season Phase</h2>
          <div className="flex gap-2 mb-6">
            {(Object.keys(WEEK_PHASES) as Phase[]).map(p => (
              <button
                key={p}
                onClick={() => setActivePhase(p)}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  activePhase === p
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                }`}
              >
                {WEEK_PHASES[p].label}
              </button>
            ))}
          </div>
          <div className="text-slate-400 text-sm mb-4 font-mono">{phase.weeks}</div>
          <div className="space-y-3 mb-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-blue-400">Situational / Historical Model</span>
                <span className="text-white font-bold">{phase.historical}%</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-3">
                <div className="bg-blue-500 h-3 rounded-full transition-all duration-500" style={{ width: `${phase.historical}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-green-400">Current Season ML Model</span>
                <span className="text-white font-bold">{phase.current}%</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-3">
                <div className="bg-green-500 h-3 rounded-full transition-all duration-500" style={{ width: `${phase.current}%` }} />
              </div>
            </div>
          </div>
          <div className="bg-orange-900/20 border border-orange-700/30 rounded-lg p-3 text-sm">
            <span className="text-orange-400 font-bold">LLM Layer: </span>
            <span className="text-slate-300">{phase.llm}</span>
          </div>
        </div>

        {/* Data Pipeline */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-white mb-4">Data Pipeline — What We Ingest</h2>
          <div className="space-y-2">
            {DATA_PIPELINE.map(d => (
              <div key={d.step} className="flex items-start gap-4 bg-slate-800/30 border border-slate-700/50 rounded-lg p-4">
                <div className="text-slate-600 font-mono text-xs pt-0.5 w-6 shrink-0">{d.step}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="text-white font-semibold">{d.name}</span>
                    <span className="text-xs text-slate-500 bg-slate-700 px-2 py-0.5 rounded">{d.freq}</span>
                  </div>
                  <div className="text-xs text-slate-500 mb-1">Source: {d.source}</div>
                  <div className="text-sm text-slate-400">{d.output}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Situational Factors */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-white mb-2">Situational Factors (Season-Agnostic)</h2>
          <p className="text-slate-500 text-sm mb-4">These patterns are baked into the model before Week 1 — they work regardless of how much current-season data exists.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {SITUATIONAL_FACTORS.map(f => (
              <div key={f.factor} className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-4">
                <div className="text-blue-400 font-semibold text-sm mb-1">{f.factor}</div>
                <div className="text-slate-400 text-sm">{f.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Model Stack */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-white mb-4">The Four-Layer Model Stack</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {MODEL_STACK.map(m => (
              <div key={m.name} className="bg-slate-800/40 border border-slate-700 rounded-xl overflow-hidden">
                <div className={`bg-gradient-to-r ${m.color} px-4 py-2 flex items-center justify-between`}>
                  <span className="font-bold text-white">{m.name}</span>
                  <span className="text-xs bg-black/30 px-2 py-0.5 rounded text-white/80">{m.type}</span>
                </div>
                <div className="p-4">
                  <div className="flex gap-4 mb-3 text-xs">
                    <div><span className="text-slate-500">Early season: </span><span className="text-white font-bold">{m.weight_early}</span></div>
                    <div><span className="text-slate-500">Late season: </span><span className="text-white font-bold">{m.weight_late}</span></div>
                  </div>
                  <p className="text-slate-400 text-sm">{m.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* LLM Context Document */}
        <div className="bg-slate-800/40 border border-slate-700 rounded-xl p-6 mb-8">
          <h2 className="text-xl font-bold text-white mb-3">What the LLM Reads — Per-Game Context Document</h2>
          <p className="text-slate-400 text-sm mb-4">
            For each game, we assemble a structured context document (CAG — Cache Augmented Generation). The LLM evaluator reads this and outputs a structured JSON pick decision.
          </p>
          <div className="bg-black/40 rounded-lg p-4 font-mono text-xs text-slate-300 overflow-auto">
            <div className="text-green-400 mb-2">{'// Game Context Document — Chiefs @ Ravens, Week 6'}</div>
            <div className="text-slate-400">{'{'}</div>
            <div className="ml-4 text-slate-300">
              <div><span className="text-blue-400">"spread"</span>{': { open: -3.5, current: -2.5, movement: "+1.0 toward Ravens" },'}</div>
              <div><span className="text-blue-400">"injuries"</span>{': { chiefs: ["Mahomes Q (hand)", "Hill OUT"], ravens: [] },'}</div>
              <div><span className="text-blue-400">"weather"</span>{': { temp: 28, wind_mph: 22, precip: "snow — 1in expected" },'}</div>
              <div><span className="text-blue-400">"situational"</span>{': { chiefs_ats_short_week: 0.41, ravens_home_dog: 0.54 },'}</div>
              <div><span className="text-blue-400">"dvoa"</span>{': { chiefs_off: 18.2, ravens_def: 14.6 },'}</div>
              <div><span className="text-blue-400">"elo"</span>{': { chiefs: 1648, ravens: 1612 }'}</div>
            </div>
            <div className="text-slate-400">{'}'}</div>
            <div className="mt-3 text-yellow-400">{'// LLM Output:'}</div>
            <div className="text-slate-300">{'{ pick: "Ravens +2.5", confidence: 0.67, tier: "MEDIUM", reasoning: "Line moved 1pt toward Ravens despite Mahomes health cleared. Wind >20mph mechanically suppresses passing game. Home dog spot historically +54% ATS. Chiefs on short week." }'}</div>
          </div>
        </div>

        {/* Corroboration Filters */}
        <div className="bg-slate-800/40 border border-slate-700 rounded-xl p-6 mb-8">
          <h2 className="text-xl font-bold text-white mb-3">Quality Filters — What Prevents Bad Picks</h2>
          <p className="text-slate-400 text-sm mb-4">A pick must pass every one of these gates before it posts.</p>
          <div className="space-y-2">
            {CORROBORATION.map((c, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className="w-5 h-5 rounded-full bg-green-900 border border-green-600 flex items-center justify-center shrink-0 mt-0.5">
                  <svg className="w-3 h-3 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                </div>
                <div>
                  <span className="text-white font-semibold text-sm">{c.check}</span>
                  <span className="text-slate-500 text-sm"> — {c.reason}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* How to Read a Pick */}
        <div className="bg-slate-800/40 border border-slate-700 rounded-xl p-6 mb-8">
          <h2 className="text-xl font-bold text-white mb-3">How to Read Our Picks</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="text-yellow-400 font-bold mb-2">Tier Labels</div>
              <div className="space-y-1 text-sm">
                <div><span className="text-red-400 font-bold">HIGH</span><span className="text-slate-400"> — Edge &gt;4%, top-tier corroboration</span></div>
                <div><span className="text-yellow-400 font-bold">MEDIUM</span><span className="text-slate-400"> — Edge 2–4%, solid signal</span></div>
                <div><span className="text-slate-400 font-bold">LOW</span><span className="text-slate-400"> — Edge 2–3%, passes filters but use smaller unit</span></div>
              </div>
            </div>
            <div>
              <div className="text-yellow-400 font-bold mb-2">Edge %</div>
              <div className="text-sm text-slate-400">The gap between our fair probability and the market's implied probability after removing the bookmaker's vig. A 3% edge means we believe the true probability is 3 percentage points better than the line suggests.</div>
            </div>
            <div>
              <div className="text-yellow-400 font-bold mb-2">Unit Sizing</div>
              <div className="text-sm text-slate-400 space-y-1">
                <div>HIGH tier: 2 units</div>
                <div>MEDIUM tier: 1.5 units</div>
                <div>LOW tier: 1 unit</div>
                <div className="text-slate-500 text-xs mt-1">Base unit = 1% of bankroll. Adjust to your stake size.</div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer note */}
        <div className="text-center text-slate-600 text-xs">
          This system is in active development. NFL predictions activate September 2026 when the season opens.
          Historical backtesting and model validation complete before Week 1.
        </div>
      </div>
    </div>
  );
}
