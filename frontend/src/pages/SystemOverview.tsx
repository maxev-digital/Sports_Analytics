import { useState } from 'react';

type SportTab = 'mlb' | 'tennis' | 'wnba' | 'soccer' | 'nfl';

const SPORT_TABS: { key: SportTab; label: string; status: string }[] = [
  { key: 'mlb',    label: 'MLB',    status: 'Live' },
  { key: 'tennis', label: 'Tennis', status: 'Live' },
  { key: 'wnba',   label: 'WNBA',   status: 'Live' },
  { key: 'soccer', label: 'Soccer', status: 'Live' },
  { key: 'nfl',    label: 'NFL',    status: 'Sep 2026' },
];

const SHARED_INFRASTRUCTURE = [
  { name: 'Multi-Book Odds Feed',       desc: '15+ bookmakers sampled every 15 minutes. Consensus pricing computed as median across books.' },
  { name: 'No-Vig Fair Value',          desc: 'For each market we strip the bookmaker margin and compute the true implied probability. This is the baseline all edge calculations compare against.' },
  { name: 'Corroboration Filter',       desc: 'All sports: minimum 5 books, 2% edge, 2% cross-book divergence required before a pick generates.' },
  { name: 'Directional Guard',          desc: 'One pick per game maximum. If the model flags both sides, only the higher-edge side is kept.' },
  { name: 'Line Movement Tracker',      desc: 'Three daily snapshots per game (morning, midday, evening). Records how lines shift from open to close across all sports.' },
  { name: 'Injury Feed',               desc: 'League injury reports refreshed 2x daily for NFL, MLB, NBA, WNBA. Flagged players injected into pick reasoning.' },
  { name: 'Automated Grading',          desc: 'Results graded against official game scores within hours of final. Win/loss/push settled automatically with 3-day lookback for late results.' },
  { name: 'Model Performance Tracking', desc: 'Per-sport, per-bet-type win rates tracked from first pick. model_performance table refreshes after every grading run.' },
];

const MLB_CONTENT = {
  headline: 'Four trained ML models + statistical edge detection across moneyline, run line, and totals.',
  models: [
    { name: 'Random Forest',      id: 'RF',  desc: 'Handles non-linear feature interactions well. Strong on park factor + pitcher fatigue combinations.' },
    { name: 'XGBoost',            id: 'XGB', desc: 'Gradient-boosted trees. Best overall performer in backtesting for MLB totals.' },
    { name: 'LightGBM',           id: 'LGB', desc: 'Faster XGB variant. Useful when retraining on rolling 7-day windows.' },
    { name: 'Logistic Regression', id: 'LR', desc: 'Linear baseline. Surprisingly competitive on moneyline when features are engineered well.' },
  ],
  detectors: [
    { name: 'Moneyline Vig Detector', desc: 'Strips juice from all books, finds >2% edge vs fair price with 5+ book corroboration.' },
    { name: 'Run Line (-1.5) Detector', desc: 'Identifies run-line value when favorites are overpriced on ML — often sharper number.' },
    { name: 'Totals Detector', desc: 'Combines park factors, starting pitcher ERA/FIP, weather wind vector, and historical over/under splits.' },
    { name: 'Pitcher Strikeout Props', desc: 'K-rate vs opposing team strikeout %, factoring in weather, pitch count limits, home/away splits.' },
  ],
  features: [
    'Starting pitcher ERA, FIP, xFIP (last 10 starts)',
    'Bullpen ERA and recent usage load',
    'Team batting average, OBP, SLG vs RHP/LHP splits',
    'Park factor (run environment adjustment)',
    'Rest days (back-to-back suppresses offense)',
    'Weather: wind direction and speed relative to outfield',
    'Home/away splits (last 30 days)',
    'Advanced batted-ball metrics: estimated batting avg, wOBA for opposing hitters',
  ],
  training: 'Models auto-retrain at 500 settled picks. Currently accumulating — live at approximately 300+ games.',
  status: 'Live — MLB season April through October.',
};

const TENNIS_CONTENT = {
  headline: 'Multi-book vig removal across ATP and WTA markets. Currently live for Wimbledon.',
  models: [],
  detectors: [
    { name: 'ATP Moneyline Vig Detector', desc: 'Strips juice from 8+ books covering ATP events. Flags when consensus no-vig price diverges >2% from best available.' },
    { name: 'WTA Moneyline Vig Detector', desc: 'Same logic applied to WTA. Surface adjustments not yet applied — clay/grass specialization in roadmap.' },
  ],
  features: [
    'No-vig fair value from 8+ books',
    'Cross-book spread: how far books disagree on price',
    'Best available price vs fair value gap',
    'Tournament stage (early rounds vs quarters/semis)',
  ],
  training: 'Rule-based vig detector — no ML training required. Applies statistical edge detection directly.',
  status: 'Live — ATP and WTA Wimbledon. Expands to all tournaments when odds coverage broadens.',
};

const WNBA_CONTENT = {
  headline: 'Moneyline ML detector running the same vig-removal pipeline as tennis, with WNBA-specific odds coverage.',
  models: [],
  detectors: [
    { name: 'WNBA Moneyline Detector', desc: 'Multi-book vig removal for WNBA ML. Books are fewer and lines softer than NBA — creates more edge opportunities.' },
  ],
  features: [
    'No-vig fair value across available books',
    'Market inefficiency score (books rarely agree on WNBA lines)',
    'Home/away historical splits',
  ],
  training: 'Rule-based. WNBA ML model planned once 200+ settled picks accumulated.',
  status: 'Live — WNBA season May through September.',
};

const SOCCER_CONTENT = {
  headline: 'MLS and EPL moneyline vig detection. Activates automatically when games fall within the 48-hour prediction window.',
  models: [],
  detectors: [
    { name: 'MLS Vig Detector', desc: 'Covers MLS regular season. 1X2 (home/draw/away) market analysis with draw-adjusted no-vig pricing.' },
    { name: 'EPL Vig Detector', desc: 'English Premier League when in season. Higher book coverage = sharper lines, requires higher divergence threshold.' },
  ],
  features: [
    'Three-way market: home / draw / away',
    'Draw probability adjustment (soccer-specific)',
    'No-vig across 6+ books covering soccer',
    '48-hour game window filter (no premature picks)',
  ],
  training: 'Rule-based vig detection. Xg-based ML model in roadmap.',
  status: 'Live — activates when MLS or EPL games within 48h window.',
};

const NFL_CONTENT = {
  headline: 'Full AI handicapper stack — situational rules + ML ensemble + LLM evaluator. Activates September 2026.',
  models: [
    { name: 'Situational Rules Engine', id: 'RULES', desc: 'Pre-computed ATS% by rest, travel, home/away, spread range. Fires from Week 1.' },
    { name: 'Elo Power Ratings',        id: 'ELO',   desc: 'Prior season Elo regressed 35% toward mean. Updates each game.' },
    { name: 'ML Ensemble (RF/XGB/LGB)', id: 'ML',    desc: 'Trained on 3 seasons. Low weight early, dominant by Week 12.' },
    { name: 'LLM Evaluator',            id: 'LLM',   desc: 'Reads per-game context doc, outputs structured pick with reasoning.' },
  ],
  detectors: [
    { name: 'ATS Spread Detector', desc: 'Against-the-spread picks using 4-layer ensemble with situational weighting.' },
    { name: 'Totals Detector', desc: 'Weather-adjusted totals using wind/temp suppressors plus situational over/under trends.' },
    { name: 'Player Props', desc: 'QB passing yards, RB rushing, WR receiving — using projected usage vs matchup quality.' },
  ],
  features: [
    'Rest days (short week, bye advantage)',
    'Travel distance and timezone cross',
    'Home/away and divisional flags',
    'DVOA offensive and defensive efficiency',
    'Elo power ratings with weekly update',
    'Injury report status (Out/Doubtful/Questionable)',
    'Weather: temp, wind, precipitation (outdoor stadiums)',
    'Line movement direction and magnitude',
    'Primetime public money adjustment',
    'Revenge game and back-to-back road flags',
  ],
  training: 'Training on 3 seasons NFL/NCAAF historical data (2022–2024). Models lock before Week 1.',
  status: 'In development — NFL season opens September 4, 2026.',
};

const SPORT_CONTENT: Record<SportTab, typeof MLB_CONTENT> = {
  mlb:    MLB_CONTENT,
  tennis: TENNIS_CONTENT,
  wnba:   WNBA_CONTENT,
  soccer: SOCCER_CONTENT,
  nfl:    NFL_CONTENT,
};

const GRADING_METHOD = [
  { step: '1', desc: 'Game finalizes — official scoreboard returns final score.' },
  { step: '2', desc: 'Grader matches our pick (game_id + side + sport) against the result.' },
  { step: '3', desc: 'Win/loss/push calculated against the spread or total we picked at.' },
  { step: '4', desc: 'P&L in units recorded. model_performance table refreshes for that sport/bet_type.' },
  { step: '5', desc: '3-day lookback runs at each grading cycle — catches any delayed results.' },
];

export function SystemOverview() {
  const [activeSport, setActiveSport] = useState<SportTab>('mlb');
  const content = SPORT_CONTENT[activeSport];

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black text-white">
      <div className="max-w-6xl mx-auto px-4 py-10">

        {/* Header */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-xs font-bold tracking-widest uppercase text-green-400 bg-green-900/30 px-3 py-1 rounded-full border border-green-700/40">System Transparency</span>
            <span className="text-xs text-slate-500">All Sports</span>
          </div>
          <h1 className="text-4xl font-black text-white mb-3">How We Pick Every Sport</h1>
          <p className="text-slate-400 text-lg max-w-3xl">
            Every model, every data source, every filter. Full transparency into the Max EV Sports prediction system across all active sports.
          </p>
        </div>

        {/* Shared Infrastructure */}
        <div className="mb-10">
          <h2 className="text-xl font-bold text-white mb-4">Shared Infrastructure — Applies to All Sports</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {SHARED_INFRASTRUCTURE.map(item => (
              <div key={item.name} className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-4">
                <div className="text-blue-400 font-semibold text-sm mb-1">{item.name}</div>
                <div className="text-slate-400 text-sm">{item.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Sport Tabs */}
        <div className="mb-6">
          <h2 className="text-xl font-bold text-white mb-4">Sport-Specific Models & Detectors</h2>
          <div className="flex gap-2 flex-wrap">
            {SPORT_TABS.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveSport(tab.key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  activeSport === tab.key
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                }`}
              >
                {tab.label}
                <span className={`text-xs px-1.5 py-0.5 rounded ${
                  tab.status === 'Live' ? 'bg-green-900 text-green-400' : 'bg-slate-600 text-slate-400'
                }`}>
                  {tab.status}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Sport Content */}
        <div className="bg-slate-800/40 border border-slate-700 rounded-xl p-6 mb-6">
          <p className="text-slate-300 text-base mb-6">{content.headline}</p>

          {/* ML Models (if any) */}
          {content.models.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">ML Models</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {content.models.map(m => (
                  <div key={m.id} className="bg-slate-900/50 border border-slate-700 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono bg-blue-900/50 text-blue-400 px-2 py-0.5 rounded">{m.id}</span>
                      <span className="text-white font-semibold text-sm">{m.name}</span>
                    </div>
                    <p className="text-slate-500 text-xs">{m.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Detectors */}
          <div className="mb-6">
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">Detection Logic</h3>
            <div className="space-y-2">
              {content.detectors.map(d => (
                <div key={d.name} className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-green-500 mt-1.5 shrink-0" />
                  <div>
                    <span className="text-white text-sm font-semibold">{d.name}</span>
                    <span className="text-slate-500 text-sm"> — {d.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Features */}
          <div className="mb-6">
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">Input Features</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-1">
              {content.features.map(f => (
                <div key={f} className="flex items-center gap-2 text-sm text-slate-400">
                  <div className="w-1 h-1 rounded-full bg-slate-600 shrink-0" />
                  {f}
                </div>
              ))}
            </div>
          </div>

          {/* Training + Status */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-900/40 rounded-lg p-3">
              <div className="text-xs text-slate-500 uppercase font-bold mb-1">Training / Methodology</div>
              <div className="text-sm text-slate-300">{content.training}</div>
            </div>
            <div className="bg-slate-900/40 rounded-lg p-3">
              <div className="text-xs text-slate-500 uppercase font-bold mb-1">Current Status</div>
              <div className="text-sm text-slate-300">{content.status}</div>
            </div>
          </div>
        </div>

        {/* Grading Methodology */}
        <div className="bg-slate-800/40 border border-slate-700 rounded-xl p-6 mb-8">
          <h2 className="text-xl font-bold text-white mb-4">How We Grade Results</h2>
          <div className="space-y-3">
            {GRADING_METHOD.map(g => (
              <div key={g.step} className="flex items-start gap-4">
                <div className="w-6 h-6 rounded-full bg-slate-700 border border-slate-600 flex items-center justify-center text-xs font-bold text-slate-400 shrink-0 mt-0.5">
                  {g.step}
                </div>
                <div className="text-slate-400 text-sm">{g.desc}</div>
              </div>
            ))}
          </div>
          <div className="mt-4 bg-yellow-900/20 border border-yellow-700/30 rounded-lg p-3 text-sm text-yellow-300">
            Props picks (strikeout K-props) are currently marked "needs_review" — pitcher boxscore grading requires Baseball Savant integration in progress.
          </div>
        </div>

        {/* Track Record */}
        <div className="bg-slate-800/40 border border-slate-700 rounded-xl p-6 mb-8">
          <h2 className="text-xl font-bold text-white mb-3">Track Record</h2>
          <p className="text-slate-400 text-sm mb-4">
            All picks logged to the database with timestamp, edge%, tier, and pick details before any game starts.
            Results graded automatically — no manual selection or cherry-picking.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'All picks timestamped pre-game', icon: '🔒' },
              { label: 'Automated result grading', icon: '⚡' },
              { label: 'Full pick history in DB page', icon: '📊' },
              { label: 'No picks removed or edited', icon: '✓' },
            ].map(item => (
              <div key={item.label} className="text-center bg-slate-900/40 rounded-lg p-3">
                <div className="text-2xl mb-1">{item.icon}</div>
                <div className="text-xs text-slate-400">{item.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* What We Don't Do */}
        <div className="bg-red-900/10 border border-red-700/30 rounded-xl p-6 mb-8">
          <h2 className="text-xl font-bold text-white mb-3">What We Don't Do</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[
              { bad: 'Cherry-pick results',    good: 'Every pick logged before game time, all tracked' },
              { bad: '"Sharp action" rumors',  good: 'Our own model output — no repackaged tipster claims' },
              { bad: 'Guaranteed winners',     good: 'Transparent edge % and confidence tier only' },
              { bad: 'Lock of the day hype',   good: 'Unit sizing by tier — no manufactured urgency' },
            ].map(item => (
              <div key={item.bad} className="flex items-start gap-3">
                <div className="text-red-500 text-lg mt-0.5">✗</div>
                <div>
                  <div className="text-red-400 text-sm font-semibold line-through">{item.bad}</div>
                  <div className="text-green-400 text-sm">{item.good}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="text-center text-slate-600 text-xs">
          System in continuous development. Model weights and detectors updated as new data accumulates.
          Questions? Contact us via the feedback button.
        </div>
      </div>
    </div>
  );
}
