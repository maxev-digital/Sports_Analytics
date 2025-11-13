export function MLModelsExplained() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black" style={{ fontFamily: 'Rubik, sans-serif' }}>
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-5xl font-bold italic text-slate-100 mb-4" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>
            MAX-EV MODELS EXPLAINED
          </h1>
          <p className="text-lg text-slate-400">
            Understanding our machine learning advantage: How 87 automated models deliver superior predictions
          </p>
        </div>

        {/* Status Banner */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 mb-8">
          <div className="flex items-start gap-4">
            <div className="text-4xl">✅</div>
            <div>
              <h3 className="text-3xl font-extrabold text-green-400 mb-2">System Status: FULLY OPERATIONAL</h3>
              <p className="text-lg font-medium text-slate-300 mb-2">
                All 87 ML models (independent training pipelines across 6 model types, 5 sports, and 3 bet types) are running via automated prediction and data pipelines, generating daily predictions
              </p>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-4">
                <div className="bg-black/40 rounded p-2 text-center">
                  <div className="text-slate-300 font-extrabold text-lg">NBA</div>
                  <div className="text-green-400 text-base font-medium">Active</div>
                </div>
                <div className="bg-black/40 rounded p-2 text-center">
                  <div className="text-slate-300 font-extrabold text-lg">NCAAB</div>
                  <div className="text-green-400 text-base font-medium">Active</div>
                </div>
                <div className="bg-black/40 rounded p-2 text-center">
                  <div className="text-slate-300 font-extrabold text-lg">NHL</div>
                  <div className="text-green-400 text-base font-medium">Active</div>
                </div>
                <div className="bg-black/40 rounded p-2 text-center">
                  <div className="text-slate-300 font-extrabold text-lg">NFL</div>
                  <div className="text-green-400 text-base font-medium">Active</div>
                </div>
                <div className="bg-black/40 rounded p-2 text-center">
                  <div className="text-slate-300 font-extrabold text-lg">NCAAF</div>
                  <div className="text-green-400 text-base font-medium">Active</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Navigation */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 mb-8">
          <h3 className="text-xl font-bold italic text-slate-300 mb-4">Quick Navigation</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <a href="#ml-vs-traditional" className="text-lg font-semibold text-slate-300 hover:text-blue-300 flex items-center gap-2">
              <span>→</span> ML vs Traditional Models
            </a>
            <a href="#model-types" className="text-lg font-semibold text-slate-300 hover:text-blue-300 flex items-center gap-2">
              <span>→</span> 6 Model Types Explained
            </a>
            <a href="#current-system" className="text-lg font-semibold text-slate-300 hover:text-blue-300 flex items-center gap-2">
              <span>→</span> Current System Architecture
            </a>
            <a href="#strategy-integration" className="text-lg font-semibold text-slate-300 hover:text-blue-300 flex items-center gap-2">
              <span>→</span> Strategy Integration (Coming Soon)
            </a>
            <a href="#performance" className="text-lg font-semibold text-slate-300 hover:text-blue-300 flex items-center gap-2">
              <span>→</span> Performance Metrics
            </a>
            <a href="#roadmap" className="text-lg font-semibold text-slate-300 hover:text-blue-300 flex items-center gap-2">
              <span>→</span> Development Roadmap
            </a>
          </div>
        </div>

        {/* ML vs Traditional Models */}
        <section id="ml-vs-traditional" className="mb-12">
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
            <h2 className="text-3xl font-bold italic text-slate-100 mb-6" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>ML Models vs Traditional Systems</h2>

            <div className="overflow-x-auto mb-6">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="py-3 px-4 text-lg text-slate-400 font-bold">Feature</th>
                    <th className="py-3 px-4 text-lg text-slate-400 font-bold">Traditional Models</th>
                    <th className="py-3 px-4 text-lg text-slate-400 font-bold">Our ML Models</th>
                  </tr>
                </thead>
                <tbody className="text-lg text-slate-300">
                  <tr className="border-b border-slate-700/50">
                    <td className="py-3 px-4 font-bold">Inputs</td>
                    <td className="py-3 px-4 font-medium">1-3 variables (public-facing models: ELO, basic power ratings)</td>
                    <td className="py-3 px-4 font-semibold text-green-400">20-54+ variables per sport</td>
                  </tr>
                  <tr className="border-b border-slate-700/50">
                    <td className="py-3 px-4 font-bold">Adaptability</td>
                    <td className="py-3 px-4 font-medium">Fixed formulas, manual updates</td>
                    <td className="py-3 px-4 font-semibold text-green-400">Learns automatically, retrains weekly</td>
                  </tr>
                  <tr className="border-b border-slate-700/50">
                    <td className="py-3 px-4 font-bold">Context Awareness</td>
                    <td className="py-3 px-4 font-medium">Limited (win/loss history only)</td>
                    <td className="py-3 px-4 font-semibold text-green-400">High (rest, injuries, pace, matchups)</td>
                  </tr>
                  <tr className="border-b border-slate-700/50">
                    <td className="py-3 px-4 font-bold">Prediction Type</td>
                    <td className="py-3 px-4 font-medium">Single point estimate</td>
                    <td className="py-3 px-4 font-semibold text-green-400">Probabilistic with confidence levels</td>
                  </tr>
                  <tr className="border-b border-slate-700/50">
                    <td className="py-3 px-4 font-bold">Improvement</td>
                    <td className="py-3 px-4 font-medium">Requires human intervention</td>
                    <td className="py-3 px-4 font-semibold text-green-400">Self-improving via automated retraining</td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 font-bold">Model Diversity</td>
                    <td className="py-3 px-4 font-medium">Single approach</td>
                    <td className="py-3 px-4 font-semibold text-green-400">Ensemble of 6 model types</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 mb-6">
              <p className="text-slate-300">
                <strong className="text-blue-400">Key Advantage:</strong> While public-facing traditional models like ELO use 1 variable (team rating),
                our ML models consider 30-54+ variables simultaneously including pace, efficiency, rest days, matchup history,
                injury impacts, and much more. Our advantage isn't that sportsbooks can't do this — it's that we tailor models specifically
                for live betting angles and situational edges that books under-adjust for. This comprehensive approach delivers significantly
                more accurate predictions for these specific scenarios.
              </p>
            </div>

            {/* Traditional Models Detailed */}
            <h3 className="text-2xl font-bold italic text-slate-100 mb-4">Common Traditional Models</h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* ELO Rating System */}
              <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-5">
                <h4 className="text-2xl font-extrabold text-slate-300 mb-3">1. ELO Rating System</h4>
                <p className="text-slate-300 text-base font-medium mb-3">
                  <strong>What it is:</strong> Originally designed for chess in the 1960s, adapted for sports. Assigns each team a single rating number (e.g., 1500).
                  After each game, winner's rating goes up, loser's goes down based on expected outcome.
                </p>
                <p className="text-slate-400 text-base font-medium mb-2"><strong>Used by:</strong> FiveThirtyEight (NBA, NFL), Chess.com</p>
                <p className="text-slate-300 text-base font-medium mb-1"><strong>Strengths:</strong> Simple, self-correcting, works over long periods</p>
                <p className="text-slate-300 text-base font-medium"><strong>Limitations:</strong> Only considers wins/losses, no context (injuries, rest), treats all wins equally</p>
              </div>

              {/* Power Rankings */}
              <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-5">
                <h4 className="text-2xl font-extrabold text-slate-300 mb-3">2. Power Rankings</h4>
                <p className="text-slate-300 text-base font-medium mb-3">
                  <strong>What it is:</strong> Ordered list of teams from best to worst. Can be expert-based (subjective) or formula-based.
                  Often uses simple metrics: wins, losses, point differential.
                </p>
                <p className="text-slate-400 text-base font-medium mb-2"><strong>Used by:</strong> ESPN, CBS Sports, Sports Illustrated</p>
                <p className="text-slate-300 text-base font-medium mb-1"><strong>Strengths:</strong> Easy to understand, can incorporate expert knowledge</p>
                <p className="text-slate-300 text-base font-medium"><strong>Limitations:</strong> Often subjective, simple formulas, no predictive modeling with confidence</p>
              </div>

              {/* KenPom Ratings */}
              <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-5">
                <h4 className="text-2xl font-extrabold text-slate-300 mb-3">3. KenPom Ratings (NCAAB)</h4>
                <p className="text-slate-300 text-base font-medium mb-3">
                  <strong>What it is:</strong> Efficiency-based rating (points per 100 possessions). Adjusts for opponent strength and tempo.
                  Uses fixed formulas to calculate AdjOffEff, AdjDefEff, AdjTempo.
                </p>
                <p className="text-slate-400 text-base font-medium mb-2"><strong>Used by:</strong> kenpom.com, college basketball analysts</p>
                <p className="text-slate-300 text-base font-medium mb-1"><strong>Strengths:</strong> Accounts for pace/efficiency, adjusts for opponents, very accurate for NCAAB</p>
                <p className="text-slate-300 text-base font-medium"><strong>Limitations:</strong> Fixed formulas (not ML), doesn't discover non-linear patterns, limited to efficiency metrics</p>
              </div>

              {/* Pythagorean Expectation */}
              <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-5">
                <h4 className="text-2xl font-extrabold text-slate-300 mb-3">4. Pythagorean Win Expectation</h4>
                <p className="text-slate-300 text-base font-medium mb-3">
                  <strong>What it is:</strong> Formula predicting win % based on points scored vs allowed: Win% = Points²/(Points² + PointsAllowed²).
                  Originated in baseball (Bill James), adapted for basketball, football.
                </p>
                <p className="text-slate-400 text-base font-medium mb-2"><strong>Used by:</strong> Basketball-Reference, advanced stats sites</p>
                <p className="text-slate-300 text-base font-medium mb-1"><strong>Strengths:</strong> Simple, effective baseline, identifies over/underperforming teams</p>
                <p className="text-slate-300 text-base font-medium"><strong>Limitations:</strong> Only 2 variables, no schedule/pace/situational factors, backward-looking</p>
              </div>

              {/* Sagarin Ratings */}
              <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-5">
                <h4 className="text-2xl font-extrabold text-slate-300 mb-3">5. Sagarin Ratings</h4>
                <p className="text-slate-300 text-base font-medium mb-3">
                  <strong>What it is:</strong> Ratings system using iterative least squares method. Accounts for strength of schedule and margin of victory.
                  Widely used for college football and basketball.
                </p>
                <p className="text-slate-400 text-base font-medium mb-2"><strong>Used by:</strong> USA Today, college sports rankings</p>
                <p className="text-slate-300 text-base font-medium mb-1"><strong>Strengths:</strong> Accounts for schedule strength, considers margin of victory</p>
                <p className="text-slate-300 text-base font-medium"><strong>Limitations:</strong> Proprietary formula, fixed calculations, no adaptation to changing patterns</p>
              </div>

              {/* RPI */}
              <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-5">
                <h4 className="text-2xl font-extrabold text-slate-300 mb-3">6. RPI (Ratings Percentage Index)</h4>
                <p className="text-slate-300 text-base font-medium mb-3">
                  <strong>What it is:</strong> Combines team's win%, opponents' win%, and opponents' opponents' win%. Historically used by NCAA for tournament selection.
                </p>
                <p className="text-slate-400 text-base font-medium mb-2"><strong>Used by:</strong> NCAA (historically), conference rankings</p>
                <p className="text-slate-300 text-base font-medium mb-1"><strong>Strengths:</strong> Simple, transparent calculation, accounts for schedule</p>
                <p className="text-slate-300 text-base font-medium"><strong>Limitations:</strong> Ignores margin of victory, criticized for inaccuracy, no longer used by NCAA</p>
              </div>

              {/* BPI/FPI (ESPN) */}
              <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-5">
                <h4 className="text-2xl font-extrabold text-slate-300 mb-3">7. BPI/FPI (ESPN)</h4>
                <p className="text-slate-300 text-base font-medium mb-3">
                  <strong>What it is:</strong> Basketball Power Index (BPI) and Football Power Index (FPI). ESPN's proprietary metrics
                  combining game results, efficiency, strength of schedule. More advanced than ELO but still fixed formulas.
                </p>
                <p className="text-slate-400 text-base font-medium mb-2"><strong>Used by:</strong> ESPN rankings and predictions</p>
                <p className="text-slate-300 text-base font-medium mb-1"><strong>Strengths:</strong> More sophisticated than simple rankings, considers multiple factors</p>
                <p className="text-slate-300 text-base font-medium"><strong>Limitations:</strong> Proprietary (can't verify), fixed formulas, no continuous learning</p>
              </div>

              {/* SRS (Simple Rating System) */}
              <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-5">
                <h4 className="text-2xl font-extrabold text-slate-300 mb-3">8. SRS (Simple Rating System)</h4>
                <p className="text-slate-300 text-base font-medium mb-3">
                  <strong>What it is:</strong> Point differential adjusted for strength of schedule. Rating = average point differential + strength of schedule adjustment.
                  Used across multiple sports.
                </p>
                <p className="text-slate-400 text-base font-medium mb-2"><strong>Used by:</strong> Sports-Reference sites (Basketball-Reference, Pro-Football-Reference)</p>
                <p className="text-slate-300 text-base font-medium mb-1"><strong>Strengths:</strong> Accounts for schedule, uses point differential (not just W/L)</p>
                <p className="text-slate-300 text-base font-medium"><strong>Limitations:</strong> Linear formula, doesn't capture complex interactions, no context awareness</p>
              </div>
            </div>
          </div>
        </section>

        {/* The 6 Model Types */}
        <section id="model-types" className="mb-12">
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
            <h2 className="text-3xl font-bold italic text-slate-100 mb-6" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>The 6 Model Types</h2>
            <p className="text-slate-300 mb-6">
              Unlike traditional models with fixed formulas, our machine learning models learn patterns from data automatically and improve over time.
            </p>

            <div className="space-y-6">
              {/* XGBoost */}
              <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-5">
                <div className="flex items-center gap-3 mb-3">
                  <span className="bg-green-700 text-white px-3 py-1 rounded-full text-base font-medium font-bold">✓ ACTIVE</span>
                  <h3 className="text-2xl font-extrabold text-slate-300">1. XGBoost (Extreme Gradient Boosting)</h3>
                </div>
                <p className="text-slate-300 mb-3">
                  <strong>What it is:</strong> Creates thousands of decision trees sequentially, where each new tree corrects errors from previous trees.
                  Industry-leading performance for structured data.
                </p>
                <p className="text-slate-300 mb-3">
                  <strong>How it works:</strong> Tree 1 might say "If team pace {">"} 100, predict OVER by 5 points", then Tree 2 says
                  "Actually, if opponent defense is strong, reduce by 3 points", continuing for 100-1000 trees.
                </p>
                <p className="text-slate-400 text-sm">
                  <strong>Why it's better than ELO:</strong> Considers 30-50+ features simultaneously (vs 1 rating), discovers complex interactions automatically
                </p>
              </div>

              {/* LightGBM */}
              <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-5">
                <div className="flex items-center gap-3 mb-3">
                  <span className="bg-green-700 text-white px-3 py-1 rounded-full text-base font-medium font-bold">✓ ACTIVE</span>
                  <h3 className="text-2xl font-extrabold text-slate-300">2. LightGBM (Light Gradient Boosting Machine)</h3>
                </div>
                <p className="text-slate-300 mb-3">
                  <strong>What it is:</strong> Similar to XGBoost but optimized for speed using histogram-based learning.
                  Excellent for large datasets and real-time predictions.
                </p>
                <p className="text-slate-400 text-sm">
                  <strong>Advantage:</strong> Can process 1000s of games in seconds, balances accuracy with computational efficiency
                </p>
              </div>

              {/* Random Forest */}
              <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-5">
                <div className="flex items-center gap-3 mb-3">
                  <span className="bg-green-700 text-white px-3 py-1 rounded-full text-base font-medium font-bold">✓ ACTIVE</span>
                  <h3 className="text-2xl font-extrabold text-slate-300">3. Random Forest</h3>
                </div>
                <p className="text-slate-300 mb-3">
                  <strong>What it is:</strong> Creates hundreds of independent decision trees where each tree votes on the prediction.
                  Final prediction is the average of all trees.
                </p>
                <p className="text-slate-300 mb-3">
                  <strong>Example:</strong> If Tree 1 predicts 225 points, Tree 2 predicts 230, Tree 3 predicts 220... and Tree 100 predicts 228,
                  the final prediction is 226.5 (average). If trees mostly agree = HIGH confidence.
                </p>
                <p className="text-slate-400 text-sm">
                  <strong>Why it's better:</strong> Quantifies uncertainty, robust to outliers, captures non-linear relationships
                </p>
              </div>

              {/* Linear Regression */}
              <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-5">
                <div className="flex items-center gap-3 mb-3">
                  <span className="bg-green-700 text-white px-3 py-1 rounded-full text-base font-medium font-bold">✓ ACTIVE</span>
                  <h3 className="text-2xl font-extrabold text-slate-300">4. Linear Regression</h3>
                </div>
                <p className="text-slate-300 mb-3">
                  <strong>What it is:</strong> Predicts continuous values (totals, spreads) by finding weighted combinations of features.
                  Similar to traditional formulas but weights learned from thousands of games.
                </p>
                <p className="text-slate-300 mb-3">
                  <strong>Example:</strong> Predicted Total = 100 (baseline) + 0.8×(team_pace) + 0.6×(opponent_pace) + 1.2×(offensive_efficiency)
                  - 1.1×(defensive_efficiency) + 2.5×(home_court) - 2.0×(back_to_back) + ...30 more features
                </p>
                <p className="text-slate-400 text-sm">
                  <strong>Advantage:</strong> Weights optimized from data, not guessed. Can include as many features as needed.
                </p>
              </div>

              {/* Logistic Regression */}
              <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-5">
                <div className="flex items-center gap-3 mb-3">
                  <span className="bg-green-700 text-white px-3 py-1 rounded-full text-base font-medium font-bold">✓ ACTIVE</span>
                  <h3 className="text-2xl font-extrabold text-slate-300">5. Logistic Regression</h3>
                </div>
                <p className="text-slate-300 mb-3">
                  <strong>What it is:</strong> Predicts probabilities for binary outcomes (win/loss). Used exclusively for moneyline bets.
                  Outputs percentage chance of each team winning.
                </p>
                <p className="text-slate-300 mb-3">
                  <strong>Example:</strong> Model predicts Team A has 67% chance to win. Market odds show Team A -150 (60% implied probability).
                  Edge = +7% → BET TEAM A
                </p>
                <p className="text-slate-400 text-sm">
                  <strong>Why it's better than ELO:</strong> Considers 20-30+ contextual factors vs just team rating. Can identify mispriced odds.
                </p>
              </div>

              {/* Ensemble */}
              <div className="bg-slate-800/50 border border-green-700 rounded-lg p-5">
                <div className="flex items-center gap-3 mb-3">
                  <span className="bg-green-700 text-white px-3 py-1 rounded-full text-base font-medium font-bold">✓ ACTIVE</span>
                  <h3 className="text-2xl font-extrabold text-slate-300">6. Ensemble (Meta-Model)</h3>
                </div>
                <p className="text-slate-300 mb-3">
                  <strong>What it is:</strong> Combines predictions from all 4 base models (XGBoost, LightGBM, Random Forest, Linear)
                  using weighted averaging based on each model's historical accuracy. "Wisdom of crowds" approach.
                </p>
                <p className="text-slate-300 mb-3">
                  <strong>Example:</strong> XGBoost predicts 225 (weight: 30%), LightGBM predicts 228 (25%), Random Forest predicts 223 (25%),
                  Linear Regression predicts 230 (20%) → Ensemble prediction: 226.15
                </p>
                <p className="text-slate-400 text-sm">
                  <strong>Why it's best:</strong> Reduces overfitting, captures different patterns, typically 2-5% more accurate than any single model
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Current System Architecture */}
        <section id="current-system" className="mb-12">
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
            <h2 className="text-3xl font-bold italic text-slate-100 mb-6" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>Current System Architecture</h2>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* 87 Active Models */}
              <div className="bg-gradient-to-br from-green-900/30 to-blue-900/30 border-2 border-slate-600/50 rounded-lg p-6">
                <h3 className="text-3xl font-extrabold text-slate-300 mb-4">87 Active ML Models</h3>
                <div className="space-y-3 text-slate-300">
                  <p className="flex items-start gap-2">
                    <span className="text-blue-400">✓</span>
                    <span><strong>6 model types</strong> × 5 sports × 3 bet types (totals, spreads, moneyline)</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-blue-400">✓</span>
                    <span><strong>Sports covered:</strong> NBA, NCAAB, NHL, NFL, NCAAF</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-blue-400">✓</span>
                    <span><strong>Daily predictions:</strong> Generated 9-11am CST automatically</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-blue-400">✓</span>
                    <span><strong>Weekly retraining:</strong> Models improve every Monday 4-9am CST</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-blue-400">✓</span>
                    <span><strong>Live alerts:</strong> In-game opportunities detected 6-11pm CST</span>
                  </p>
                </div>
              </div>

              {/* Data Sources */}
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
                <h3 className="text-2xl font-bold italic text-blue-400 mb-4">Data Sources</h3>
                <div className="space-y-3 text-slate-300">
                  <p className="flex items-start gap-2">
                    <span className="text-slate-300">→</span>
                    <span><strong>NBA:</strong> Official NBA API (32-42 features)</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-slate-300">→</span>
                    <span><strong>NCAAB:</strong> KenPom ratings via licensed or internal ingestion (25-34 features)</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-slate-300">→</span>
                    <span><strong>NHL:</strong> MoneyPuck + MoreHockeyStats via licensed or internal ingestion (44-59 features)</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-slate-300">→</span>
                    <span><strong>NFL:</strong> SportsDataIO (21-29 features)</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-slate-300">→</span>
                    <span><strong>NCAAF:</strong> TeamRankings via licensed or internal ingestion (24-33 features)</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-slate-300">→</span>
                    <span><strong>Odds:</strong> The Odds API (real-time lines from 20+ books)</span>
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
              <p className="text-slate-300">
                <strong className="text-blue-400">Fully Automated:</strong> The entire system runs without human intervention.
                Models automatically pull data, generate predictions, retrain with new results, and deploy improved versions every Monday.
              </p>
            </div>
          </div>
        </section>

        {/* Strategy Integration - Coming Soon */}
        <section id="strategy-integration" className="mb-12">
          <div className="bg-slate-900 border-2 border-slate-600/50 rounded-lg p-6">
            <div className="flex items-start gap-4 mb-6">
              <span className="text-5xl">🚧</span>
              <div>
                <h2 className="text-3xl font-bold text-orange-400 mb-2">ML + Strategy Integration</h2>
                <p className="text-orange-400 font-bold">Coming Soon - Next Major Feature</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* The Opportunity */}
              <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-5">
                <h3 className="text-2xl font-extrabold text-slate-200 mb-3">The Opportunity</h3>
                <div className="space-y-2 text-slate-300">
                  <p>Currently, our 25 betting strategies and 87 ML models run <strong>independently</strong>.</p>
                  <p className="text-slate-300 font-semibold">Integration will combine their strengths:</p>
                  <ul className="list-disc list-inside space-y-1 text-sm">
                    <li>Strategies identify WHEN to bet (situational triggers)</li>
                    <li>ML models identify HOW MUCH edge exists (quantitative prediction)</li>
                    <li>Combined system = Better timing + Better accuracy = Higher ROI</li>
                  </ul>
                </div>
              </div>

              {/* Expected Impact */}
              <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-5">
                <h3 className="text-xl font-bold italic text-slate-300 mb-3">Expected Impact (Based on Internal Backtests)</h3>
                <div className="space-y-3 text-slate-300 text-sm">
                  <p className="text-slate-200 font-semibold mb-2">
                    ⚠️ Internal backtests suggest ML integration may improve strategy calibration and reduce false positives.
                    Actual performance will vary based on market conditions.
                  </p>
                  <p>
                    <strong>Potential Improvements:</strong> Our historical testing indicates ML models may help refine
                    edge detection by ~3-5%, though results depend on sport, strategy type, and market efficiency.
                  </p>
                  <p>
                    <strong>False Positive Reduction:</strong> ML filtering may reduce low-quality alerts by helping
                    identify genuine edges versus statistical noise.
                  </p>
                  <p>
                    <strong>Confidence Calibration:</strong> Probabilistic predictions may provide better bankroll
                    sizing guidance compared to fixed strategy thresholds.
                  </p>
                </div>
              </div>
            </div>

            {/* Examples of Integration */}
            <div className="space-y-4">
              <h3 className="text-xl font-bold italic text-slate-300">Integration Examples:</h3>

              <div className="bg-slate-800/30 border border-slate-700 rounded p-4">
                <h4 className="font-bold text-slate-200 mb-2">B2B vs Rested Strategy + ML</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-base font-medium text-slate-300">
                  <div>
                    <p className="text-slate-400 font-semibold mb-1">Current (Strategy Only):</p>
                    <p>Fixed formula: Rest difference × 1.5 = edge<br/>
                    3 days rest difference = 4.5 point edge<br/>
                    Confidence: MEDIUM</p>
                  </div>
                  <div>
                    <p className="text-slate-300 font-semibold mb-1">With ML Integration:</p>
                    <p>ML detects actual fatigue impact for THIS matchup<br/>
                    Lakers B2B vs Celtics = 6.2 point edge (not 4.5)<br/>
                    Confidence: HIGH (models agree)</p>
                  </div>
                </div>
              </div>

              <div className="bg-slate-800/30 border border-slate-700 rounded p-4">
                <h4 className="font-bold text-slate-200 mb-2">Favorite Comeback Strategy + ML</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-base font-medium text-slate-300">
                  <div>
                    <p className="text-slate-400 font-semibold mb-1">Current (Strategy Only):</p>
                    <p>5-factor regression score<br/>
                    Score 17/20 = 65% expected win rate<br/>
                    Historical baseline from backtests</p>
                  </div>
                  <div>
                    <p className="text-slate-300 font-semibold mb-1">With ML Integration:</p>
                    <p>ML analyzes live game shooting variance<br/>
                    Predicts 68% comeback probability (not 65%)<br/>
                    Higher confidence when ML + strategy agree</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 bg-yellow-900/30 border border-slate-600/50 rounded-lg p-4">
              <p className="text-slate-300">
                <strong className="text-yellow-400">Development Timeline:</strong> Integration planned for Phase 2 development (Weeks 3-4 of implementation roadmap).
                Will start with top 5 strategies: B2B vs Rested, Favorite Comeback, Pace Mismatch, Quarter Reversal, and Injury Cascade.
              </p>
            </div>
          </div>
        </section>

        {/* Current Performance */}
        <section id="performance" className="mb-12">
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
            <h2 className="text-3xl font-bold italic text-slate-100 mb-6" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>Current Performance Metrics</h2>

            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 mb-6">
              <p className="text-slate-300">
                <strong className="text-blue-400">Live Data:</strong> View real-time model performance on the Model Performance page.
                System tracks every prediction, grades results automatically, and displays cumulative performance metrics.
              </p>
            </div>

            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 mb-6">
              <p className="text-red-400 font-semibold mb-2">⚠️ Performance Disclaimers:</p>
              <ul className="text-slate-300 text-base font-medium space-y-1">
                <li>• Past performance does not guarantee future results</li>
                <li>• Results based on simulated unit tracking with standardized bet sizing</li>
                <li>• Actual results will vary based on bet sizing, timing, and market conditions</li>
                <li>• Early sample sizes (especially NHL: 132 bets) require additional data for statistical reliability</li>
              </ul>
            </div>

            {/* Performance Overview - Last 3 Days */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              <div className="bg-slate-800/50 border border-slate-600/50 rounded-lg p-5">
                <h3 className="text-2xl font-extrabold text-slate-300 mb-4">Overall Performance (Last 3 Days)</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center pb-2 border-b border-slate-700">
                    <span className="text-slate-300">Total Predictions:</span>
                    <span className="text-white font-bold text-xl">1,155</span>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-slate-700">
                    <span className="text-slate-300">Record:</span>
                    <span className="text-white font-bold">592W - 477L</span>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-slate-700">
                    <span className="text-slate-300">Win Rate:</span>
                    <span className="text-green-400 font-bold text-xl">55.4%</span>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-slate-700">
                    <span className="text-slate-300">ROI:</span>
                    <span className="text-green-400 font-bold text-xl">+5.34%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-300">Profit:</span>
                    <span className="text-green-400 font-bold text-xl">+61.72 units</span>
                  </div>
                </div>
              </div>

              <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-5">
                <h3 className="text-xl font-bold italic text-slate-300 mb-4">Best Performing Sports</h3>
                <div className="space-y-3">
                  <div className="bg-green-900/30 border border-slate-600/50 rounded p-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-bold text-slate-300">NHL</span>
                      <span className="text-green-400 font-bold">65.3% WR</span>
                    </div>
                    <div className="text-sm text-slate-400">132 predictions • +23.3% ROI • +30.71 units</div>
                  </div>
                  <div className="bg-blue-900/30 border border-blue-600/50 rounded p-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-bold text-slate-300">NFL</span>
                      <span className="text-blue-400 font-bold">80.0% WR</span>
                    </div>
                    <div className="text-sm text-slate-400">15 predictions • Small sample</div>
                  </div>
                  <div className="bg-slate-700/30 border border-slate-600 rounded p-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-bold text-slate-300">NCAAB</span>
                      <span className="text-slate-300 font-bold">53.7% WR</span>
                    </div>
                    <div className="text-sm text-slate-400">867 predictions • Largest sample</div>
                  </div>
                  <div className="bg-slate-700/30 border border-slate-600 rounded p-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-bold text-slate-300">NBA</span>
                      <span className="text-slate-300 font-bold">53.2% WR</span>
                    </div>
                    <div className="text-sm text-slate-400">141 predictions • Consistent</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4">
              <p className="text-slate-300 text-base font-medium">
                <strong>Note:</strong> System tracking started November 10, 2025. Performance will become more statistically significant as more data accumulates.
                We expect increased statistical stability after 30-60 days of predictions across varied market conditions.
              </p>
            </div>
          </div>
        </section>

        {/* Understanding Model Performance */}
        <section className="mb-12">
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
            <h2 className="text-3xl font-bold italic text-slate-100 mb-6" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>Understanding Model Performance</h2>

            <div className="space-y-6">
              {/* What Good Performance Looks Like */}
              <div>
                <h3 className="text-2xl font-extrabold text-slate-300 mb-3">What Good Performance Looks Like</h3>
                <div className="bg-slate-800/50 rounded-lg p-4 space-y-3 text-slate-300">
                  <p>
                    <strong className="text-green-400">Win Rate Above 52.4%:</strong> The breakeven point for betting against standard -110 odds is 52.4%.
                    Any win rate above this is profitable long-term.
                  </p>
                  <p>
                    <strong className="text-green-400">Positive ROI:</strong> Return on investment measures profit per dollar wagered.
                    Even a +3-5% ROI is excellent for sports betting, where most bettors lose money.
                  </p>
                  <p>
                    <strong className="text-blue-400">Consistency Over Time:</strong> It's normal for performance to fluctuate day-to-day.
                    What matters is the cumulative trend over weeks and months.
                  </p>
                  <p>
                    <strong className="text-slate-200">Sample Size Matters:</strong> 50-100 bets is a minimum for statistical significance.
                    1,000+ bets provides reliable performance metrics. Our current 1,155 predictions is a solid start.
                  </p>
                </div>
              </div>

              {/* Interpreting Confidence Levels */}
              <div>
                <h3 className="text-2xl font-extrabold text-slate-300 mb-3">Interpreting Confidence Levels</h3>
                <div className="space-y-3">
                  <div className="bg-green-900/30 border border-slate-600/50 rounded-lg p-4">
                    <h4 className="font-bold text-green-400 mb-2">HIGH Confidence</h4>
                    <p className="text-slate-300 text-base font-medium">
                      Edge ≥ 5.0 points • All models agree • Historical accuracy 58%+ • Recommended bet size: 3-5% of bankroll
                    </p>
                  </div>
                  <div className="bg-yellow-900/30 border border-slate-600/50 rounded-lg p-4">
                    <h4 className="font-bold text-yellow-400 mb-2">MEDIUM Confidence</h4>
                    <p className="text-slate-300 text-base font-medium">
                      Edge 3.0-4.9 points • Most models agree • Historical accuracy 54-58% • Recommended bet size: 2-3% of bankroll
                    </p>
                  </div>
                  <div className="bg-red-900/30 border border-red-600/50 rounded-lg p-4">
                    <h4 className="font-bold text-slate-300 mb-2">LOW Confidence</h4>
                    <p className="text-slate-300 text-base font-medium">
                      Edge 2.0-2.9 points • Models disagree or uncertainty • Historical accuracy 52-54% • Recommended bet size: 1-2% of bankroll
                    </p>
                  </div>
                </div>
              </div>

              {/* Why Models Improve Over Time */}
              <div>
                <h3 className="text-2xl font-extrabold text-slate-300 mb-3">Why Models Improve Over Time</h3>
                <div className="bg-slate-800/50 rounded-lg p-4 space-y-3 text-slate-300">
                  <p>
                    <strong className="text-slate-300">1. Automated Learning:</strong> Every Monday at 4am CST, models automatically retrain with the previous week's results.
                    They learn which patterns worked and which didn't.
                  </p>
                  <p>
                    <strong className="text-slate-300">2. More Data = Better Predictions:</strong> As the season progresses, models have more games to learn from.
                    A model trained on 1,000 games is more accurate than one trained on 100 games.
                  </p>
                  <p>
                    <strong className="text-slate-300">3. Adaptation to Market:</strong> Betting lines change as the season progresses.
                    Models adapt to find edges that remain profitable even as the market adjusts.
                  </p>
                  <p>
                    <strong className="text-slate-300">4. Ensemble Refinement:</strong> The ensemble model continuously adjusts weights given to each base model
                    based on recent accuracy. Better models get more weight over time.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Development Roadmap */}
        <section id="roadmap" className="mb-12">
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
            <h2 className="text-3xl font-bold italic text-slate-100 mb-6" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>Development Roadmap</h2>

            <div className="space-y-6">
              {/* Phase 1: Current - Fully Operational */}
              <div className="bg-slate-800/50 border-2 border-slate-600 rounded-lg p-5">
                <div className="flex items-center gap-3 mb-4">
                  <span className="bg-slate-700 text-white px-4 py-2 rounded-full font-bold">PHASE 1: COMPLETE</span>
                  <h3 className="text-3xl font-extrabold text-slate-300">Automated ML System</h3>
                </div>
                <div className="space-y-2 text-slate-300">
                  <p className="flex items-start gap-2">
                    <span className="text-blue-400">✓</span>
                    <span>87 ML models operational across 5 sports</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-blue-400">✓</span>
                    <span>Daily predictions automated (9-11am CST)</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-blue-400">✓</span>
                    <span>Weekly retraining automated (Mondays 4-9am CST)</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-blue-400">✓</span>
                    <span>Live alert system running (6-11pm CST)</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-blue-400">✓</span>
                    <span>Performance tracking and reporting live</span>
                  </p>
                </div>
              </div>

              {/* Phase 2: Next - Strategy Integration */}
              <div className="bg-slate-800/50 border-2 border-slate-600 rounded-lg p-5">
                <div className="flex items-center gap-3 mb-4">
                  <span className="bg-yellow-600 text-black px-4 py-2 rounded-full font-bold">PHASE 2: NEXT</span>
                  <h3 className="text-3xl font-extrabold text-slate-200">ML + Strategy Integration</h3>
                </div>
                <div className="space-y-2 text-slate-300">
                  <p className="flex items-start gap-2">
                    <span className="text-slate-200">→</span>
                    <span>Enhanced data features (rolling stats, opponent adjustments)</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-slate-200">→</span>
                    <span>Fatigue index and injury impact quantification</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-slate-200">→</span>
                    <span>Top 5 strategies enhanced with ML (B2B, Comeback, Pace, Quarter Reversal, Injury)</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-slate-200">→</span>
                    <span>Expected: +3-5% ROI improvement across strategies</span>
                  </p>
                </div>
              </div>

              {/* Phase 3: Future - Advanced Features */}
              <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-5">
                <div className="flex items-center gap-3 mb-4">
                  <span className="bg-slate-600 text-white px-4 py-2 rounded-full font-bold">PHASE 3: FUTURE</span>
                  <h3 className="text-2xl font-bold italic text-slate-100">Advanced ML Features</h3>
                </div>
                <div className="space-y-2 text-slate-400">
                  <p className="flex items-start gap-2">
                    <span className="text-slate-500">○</span>
                    <span>Probability calibration and confidence intervals</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-slate-500">○</span>
                    <span>CLV tracking and odds microstructure analysis</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-slate-500">○</span>
                    <span>Live game shooting variance detection</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-slate-500">○</span>
                    <span>Market efficiency scoring and bet sizing optimization</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-slate-500">○</span>
                    <span>All 25 strategies ML-enhanced</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
