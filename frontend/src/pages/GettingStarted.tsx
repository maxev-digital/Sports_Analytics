export function GettingStarted() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-slate-100 mb-4">
            Getting Started Guide
          </h1>
          <p className="text-xl text-slate-300">
            Your complete roadmap to profitable sports betting
          </p>
        </div>

        {/* Quick Start Checklist */}
        <div className="bg-gradient-to-br from-blue-900/30 to-purple-900/30 border border-blue-800 rounded-2xl p-8 mb-12">
          <h2 className="text-2xl font-bold text-slate-100 mb-6 flex items-center gap-3">
            <svg className="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Quick Start Checklist
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              'Open accounts at 5-8 sportsbooks',
              'Set up bankroll tracking system',
              'Configure platform alerts and notifications',
              'Install mobile apps for quick bet placement',
              'Set up dual monitor workspace',
              'Join Discord community for tips',
              'Review daily workflow schedule',
              'Practice with small stakes first',
            ].map((item, idx) => (
              <div key={idx} className="flex items-start gap-3 bg-slate-800/50 rounded-lg p-4">
                <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-white text-sm font-bold">{idx + 1}</span>
                </div>
                <span className="text-slate-200">{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Daily Workflow */}
        <div className="mb-12">
          <h2 className="text-3xl font-bold text-slate-100 mb-6">Your Daily Workflow</h2>

          <div className="space-y-6">
            {/* Morning Routine */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-amber-600 px-3 py-1 rounded-full text-white text-sm font-bold">
                  9:00 AM - 11:00 AM
                </div>
                <h3 className="text-2xl font-bold text-slate-100">Morning Prep</h3>
              </div>
              <div className="space-y-3 text-slate-300">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div>
                    <strong>Check overnight line movements:</strong> Review which games saw significant line changes. These indicate sharp money action.
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div>
                    <strong>Review injury reports:</strong> Check our real-time injury alerts and adjust your betting card accordingly.
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div>
                    <strong>Scan arbitrage opportunities:</strong> Check the Arbitrage Finder for any guaranteed profit opportunities across books.
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div>
                    <strong>Set up alerts for the day:</strong> Configure steam move and line movement alerts for games you're targeting.
                  </div>
                </div>
              </div>
              <div className="mt-4 bg-blue-900/30 border border-blue-700 rounded-lg p-4">
                <p className="text-sm text-blue-200">
                  <strong>Pro Tip:</strong> The best lines are typically available in the morning before recreational bettors wake up. Set your alarm early to capture soft lines.
                </p>
              </div>
            </div>

            {/* Afternoon Session */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-orange-600 px-3 py-1 rounded-full text-white text-sm font-bold">
                  12:00 PM - 3:00 PM
                </div>
                <h3 className="text-2xl font-bold text-slate-100">Midday Analysis</h3>
              </div>
              <div className="space-y-3 text-slate-300">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div>
                    <strong>Monitor steam moves:</strong> Watch for sudden line movements indicating sharp action. These happen most frequently 2-3 hours before game time.
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div>
                    <strong>Review player props:</strong> Check the Props module for mispriced player totals, especially newly released lines.
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div>
                    <strong>Place value bets:</strong> Lock in bets where you've identified positive expected value before lines tighten.
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div>
                    <strong>Check for middles:</strong> Look for opportunities to bet both sides of a game at different books for middle potential.
                  </div>
                </div>
              </div>
            </div>

            {/* Evening Live Betting */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-red-600 px-3 py-1 rounded-full text-white text-sm font-bold flex items-center gap-2">
                  <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                  4:00 PM - 11:00 PM
                </div>
                <h3 className="text-2xl font-bold text-slate-100">Live Betting Session</h3>
              </div>
              <div className="space-y-3 text-slate-300">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div>
                    <strong>Monitor live games:</strong> Use our real-time momentum indicators to identify live betting opportunities as games unfold.
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div>
                    <strong>Hedge positions:</strong> Use the Hedge Calculator to lock in profits on winning pre-game bets.
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div>
                    <strong>Track results in real-time:</strong> Update your bet tracking system as games conclude.
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div>
                    <strong>Review closing lines:</strong> Compare your bet prices to closing lines to measure your CLV (Closing Line Value).
                  </div>
                </div>
              </div>
              <div className="mt-4 bg-red-900/30 border border-red-700 rounded-lg p-4">
                <p className="text-sm text-red-200">
                  <strong>Critical Time Window:</strong> Most profitable live betting opportunities occur in the first 5 minutes and last 5 minutes of quarters. Stay alert!
                </p>
              </div>
            </div>

            {/* Night Wrap-Up */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-indigo-600 px-3 py-1 rounded-full text-white text-sm font-bold">
                  11:00 PM - 12:00 AM
                </div>
                <h3 className="text-2xl font-bold text-slate-100">Daily Review</h3>
              </div>
              <div className="space-y-3 text-slate-300">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div>
                    <strong>Log all bets:</strong> Ensure every bet is recorded in the tracking system with entry price, stake, and result.
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div>
                    <strong>Review performance:</strong> Check your daily ROI and CLV metrics to assess edge quality.
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div>
                    <strong>Plan tomorrow's card:</strong> Review upcoming games and set alerts for tomorrow's opportunities.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Time Commitment */}
        <div className="mb-12 bg-slate-800/50 border border-slate-700 rounded-xl p-8">
          <h2 className="text-3xl font-bold text-slate-100 mb-6">Expected Time Commitment</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gradient-to-br from-green-900/30 to-green-800/20 border border-green-700 rounded-lg p-6">
              <h3 className="text-xl font-bold text-green-300 mb-3">Casual Bettor</h3>
              <div className="text-4xl font-bold text-slate-100 mb-2">5-10 hrs/week</div>
              <p className="text-sm text-slate-300 mb-4">Perfect for side income while working full-time</p>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>• Morning line shopping (30 min)</li>
                <li>• Lunch break analysis (30 min)</li>
                <li>• Evening live betting (2-3 hrs)</li>
                <li>• Weekend deep dives (2-3 hrs)</li>
              </ul>
            </div>
            <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 border border-blue-700 rounded-lg p-6">
              <h3 className="text-xl font-bold text-blue-300 mb-3">Serious Bettor</h3>
              <div className="text-4xl font-bold text-slate-100 mb-2">20-30 hrs/week</div>
              <p className="text-sm text-slate-300 mb-4">Semi-professional approach with consistent profits</p>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>• Daily morning prep (2 hrs)</li>
                <li>• Midday line monitoring (2 hrs)</li>
                <li>• Evening live sessions (4-5 hrs)</li>
                <li>• Weekend grind (10-12 hrs)</li>
              </ul>
            </div>
            <div className="bg-gradient-to-br from-purple-900/30 to-purple-800/20 border border-purple-700 rounded-lg p-6">
              <h3 className="text-xl font-bold text-purple-300 mb-3">Professional</h3>
              <div className="text-4xl font-bold text-slate-100 mb-2">40-60 hrs/week</div>
              <p className="text-sm text-slate-300 mb-4">Full-time betting operation treating it as a business</p>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>• Pre-market prep (3-4 hrs)</li>
                <li>• Continuous monitoring (6-8 hrs)</li>
                <li>• Live betting sessions (4-6 hrs)</li>
                <li>• Model development (4-6 hrs)</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Sportsbook Setup */}
        <div className="mb-12">
          <h2 className="text-3xl font-bold text-slate-100 mb-6">Sportsbook Account Strategy</h2>

          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-8 mb-6">
            <h3 className="text-2xl font-bold text-slate-100 mb-4">Recommended Sportsbooks</h3>
            <p className="text-slate-300 mb-6">
              Open accounts at 5-8 books to maximize line shopping opportunities and arbitrage plays. Each book has different strengths and weaknesses.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Sharp Books */}
              <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-6">
                <h4 className="text-lg font-bold text-blue-300 mb-4 flex items-center gap-2">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Sharp Books (Hardest to Beat)
                </h4>
                <div className="space-y-3 text-sm">
                  <div className="bg-slate-800/50 rounded p-3">
                    <div className="font-bold text-slate-100 mb-1">Pinnacle</div>
                    <div className="text-slate-400">Lowest margins, highest limits. Use for CLV comparison.</div>
                  </div>
                  <div className="bg-slate-800/50 rounded p-3">
                    <div className="font-bold text-slate-100 mb-1">Circa Sports</div>
                    <div className="text-slate-400">Sharp NFL lines. Great for middles and arbitrage.</div>
                  </div>
                  <div className="bg-slate-800/50 rounded p-3">
                    <div className="font-bold text-slate-100 mb-1">Bookmaker.eu</div>
                    <div className="text-slate-400">Reduced juice, high limits, won't limit winners.</div>
                  </div>
                </div>
              </div>

              {/* Soft Books */}
              <div className="bg-green-900/20 border border-green-700 rounded-lg p-6">
                <h4 className="text-lg font-bold text-green-300 mb-4 flex items-center gap-2">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Soft Books (Best Value)
                </h4>
                <div className="space-y-3 text-sm">
                  <div className="bg-slate-800/50 rounded p-3">
                    <div className="font-bold text-slate-100 mb-1">DraftKings</div>
                    <div className="text-slate-400">Slow to move lines, great promos. Best for SGPs.</div>
                  </div>
                  <div className="bg-slate-800/50 rounded p-3">
                    <div className="font-bold text-slate-100 mb-1">FanDuel</div>
                    <div className="text-slate-400">Weak player props, generous odds boosts.</div>
                  </div>
                  <div className="bg-slate-800/50 rounded p-3">
                    <div className="font-bold text-slate-100 mb-1">Caesars</div>
                    <div className="text-slate-400">Soft NBA lines, frequent free bets.</div>
                  </div>
                  <div className="bg-slate-800/50 rounded p-3">
                    <div className="font-bold text-slate-100 mb-1">BetMGM</div>
                    <div className="text-slate-400">Weak live lines, good for middle hunting.</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 bg-amber-900/30 border border-amber-700 rounded-lg p-6">
              <h4 className="text-lg font-bold text-amber-300 mb-3">Account Management Strategy</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-slate-300">
                <div className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span><strong>Round bet sizes:</strong> Always bet round numbers ($50, $100) to avoid detection algorithms</span>
                </div>
                <div className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span><strong>Mix in losing bets:</strong> Occasionally bet recreational favorites to appear less sharp</span>
                </div>
                <div className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span><strong>Use promos strategically:</strong> Hammer soft books during promo periods before getting limited</span>
                </div>
                <div className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span><strong>Keep multiple accounts:</strong> Use family/friend accounts (with permission) to extend lifespan</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Equipment Setup */}
        <div className="mb-12">
          <h2 className="text-3xl font-bold text-slate-100 mb-6">Optimal Equipment Setup</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Basic Setup */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <div className="bg-green-900/30 border border-green-700 rounded-lg px-4 py-2 inline-block mb-4">
                <span className="text-green-300 font-bold">$500-1,000 Budget</span>
              </div>
              <h3 className="text-2xl font-bold text-slate-100 mb-4">Basic Setup</h3>
              <div className="space-y-3 text-slate-300 text-sm">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <div>
                    <strong>Single 27" monitor</strong> (Dell S2722DC ~$300)
                    <div className="text-xs text-slate-400 mt-1">Good enough to start. Split screen between our platform and sportsbooks.</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  <div>
                    <strong>Smartphone</strong> (any modern phone)
                    <div className="text-xs text-slate-400 mt-1">Install sportsbook apps for quick bet placement on the go.</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                  </svg>
                  <div>
                    <strong>Reliable internet</strong> (100+ Mbps)
                    <div className="text-xs text-slate-400 mt-1">Critical for live betting. Consider backup mobile hotspot.</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Pro Setup */}
            <div className="bg-slate-800/50 border border-purple-700 rounded-xl p-6 shadow-lg shadow-purple-900/20">
              <div className="bg-purple-900/30 border border-purple-700 rounded-lg px-4 py-2 inline-block mb-4">
                <span className="text-purple-300 font-bold">$2,000-3,500 Budget</span>
              </div>
              <h3 className="text-2xl font-bold text-slate-100 mb-4">Professional Setup</h3>
              <div className="space-y-3 text-slate-300 text-sm">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-purple-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <div>
                    <strong>Dual 32" 4K monitors</strong> (LG 32UN880 ~$700 each)
                    <div className="text-xs text-slate-400 mt-1">Monitor 1: Our platform. Monitor 2: 4 sportsbook tabs for line comparison.</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-purple-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <div>
                    <strong>43" TV for live games</strong> (Samsung ~$400)
                    <div className="text-xs text-slate-400 mt-1">Watch live games while monitoring lines. Crucial for live betting feel.</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-purple-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  <div>
                    <strong>iPhone + iPad</strong> (~$1,200 total)
                    <div className="text-xs text-slate-400 mt-1">iPhone for alerts. iPad for quick line comparison while away from desk.</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-purple-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <div>
                    <strong>Mechanical keyboard</strong> (Keychron ~$100)
                    <div className="text-xs text-slate-400 mt-1">Fast bet entry matters. Programmable macros for common bet amounts.</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-purple-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                  </svg>
                  <div>
                    <strong>UPS backup power</strong> (~$150)
                    <div className="text-xs text-slate-400 mt-1">Never lose a live bet due to power outage. 30-min runtime minimum.</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 bg-blue-900/30 border border-blue-700 rounded-lg p-6">
            <h4 className="text-lg font-bold text-blue-300 mb-3">Why Multiple Monitors Matter</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-slate-300">
              <div className="bg-slate-800/50 rounded p-4">
                <div className="font-bold text-slate-100 mb-2">Speed Advantage</div>
                <div className="text-slate-400">See line movements across multiple books simultaneously. React 5-10 seconds faster than single-monitor bettors.</div>
              </div>
              <div className="bg-slate-800/50 rounded p-4">
                <div className="font-bold text-slate-100 mb-2">Reduce Errors</div>
                <div className="text-slate-400">No more alt-tabbing between windows. See our alerts, odds comparison, and bet slips all at once.</div>
              </div>
              <div className="bg-slate-800/50 rounded p-4">
                <div className="font-bold text-slate-100 mb-2">Professional Edge</div>
                <div className="text-slate-400">Monitor live stats, Twitter injury news, and line movements simultaneously during games.</div>
              </div>
            </div>
          </div>
        </div>

        {/* Bankroll Management */}
        <div className="mb-12 bg-gradient-to-br from-green-900/30 to-emerald-900/30 border border-green-700 rounded-2xl p-8">
          <h2 className="text-3xl font-bold text-slate-100 mb-6">Bankroll Management Essentials</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
              <h3 className="text-xl font-bold text-green-300 mb-4">Unit Sizing Rules</h3>
              <div className="space-y-3 text-sm text-slate-300">
                <div className="flex items-start gap-3">
                  <div className="bg-green-600 text-white px-2 py-1 rounded text-xs font-bold flex-shrink-0">1U</div>
                  <div>
                    <strong>1-2% of bankroll</strong> - Standard unit size for normal value bets
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="bg-blue-600 text-white px-2 py-1 rounded text-xs font-bold flex-shrink-0">2U</div>
                  <div>
                    <strong>2-3% of bankroll</strong> - Medium confidence, clear edge identified
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="bg-purple-600 text-white px-2 py-1 rounded text-xs font-bold flex-shrink-0">3U</div>
                  <div>
                    <strong>3-4% of bankroll</strong> - High confidence, significant mispricing
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="bg-amber-600 text-white px-2 py-1 rounded text-xs font-bold flex-shrink-0">MAX</div>
                  <div>
                    <strong>5% of bankroll</strong> - Reserve for arbitrage and guaranteed profit only
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
              <h3 className="text-xl font-bold text-green-300 mb-4">Recommended Starting Bankrolls</h3>
              <div className="space-y-4">
                <div className="bg-slate-900/50 rounded p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-slate-100 font-bold">Casual ($1,000)</span>
                    <span className="text-green-400 text-sm">$10-20 units</span>
                  </div>
                  <div className="text-xs text-slate-400">Supplement income. Low pressure environment to learn.</div>
                </div>
                <div className="bg-slate-900/50 rounded p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-slate-100 font-bold">Serious ($5,000)</span>
                    <span className="text-green-400 text-sm">$50-100 units</span>
                  </div>
                  <div className="text-xs text-slate-400">Part-time income potential. Access to better limits.</div>
                </div>
                <div className="bg-slate-900/50 rounded p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-slate-100 font-bold">Professional ($25,000+)</span>
                    <span className="text-green-400 text-sm">$250-500 units</span>
                  </div>
                  <div className="text-xs text-slate-400">Full-time income. Maximum book limits and promo access.</div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-red-900/30 border border-red-700 rounded-lg p-6">
            <h4 className="text-lg font-bold text-red-300 mb-3 flex items-center gap-2">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Cardinal Rules (Never Break These)
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-red-200">
              <div className="flex items-start gap-2">
                <span className="text-red-400 text-lg flex-shrink-0">×</span>
                <span>Never bet more than 5% of bankroll on a single play</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-red-400 text-lg flex-shrink-0">×</span>
                <span>Never chase losses by increasing unit size</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-red-400 text-lg flex-shrink-0">×</span>
                <span>Never bet with money you can't afford to lose</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-red-400 text-lg flex-shrink-0">×</span>
                <span>Never bet while intoxicated or emotionally compromised</span>
              </div>
            </div>
          </div>
        </div>

        {/* Success Metrics */}
        <div className="mb-12">
          <h2 className="text-3xl font-bold text-slate-100 mb-6">Measuring Your Success</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-blue-400 mb-2">ROI</div>
              <div className="text-sm text-slate-300 mb-3">Return on Investment</div>
              <div className="bg-slate-900/50 rounded p-3 text-left text-xs text-slate-400">
                <div className="mb-2"><strong className="text-green-400">Excellent:</strong> 8%+</div>
                <div className="mb-2"><strong className="text-blue-400">Good:</strong> 4-8%</div>
                <div className="mb-2"><strong className="text-amber-400">Average:</strong> 2-4%</div>
                <div><strong className="text-red-400">Poor:</strong> &lt;2%</div>
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-purple-400 mb-2">CLV</div>
              <div className="text-sm text-slate-300 mb-3">Closing Line Value</div>
              <div className="bg-slate-900/50 rounded p-3 text-left text-xs text-slate-400">
                <div className="mb-2"><strong className="text-green-400">Excellent:</strong> +4%</div>
                <div className="mb-2"><strong className="text-blue-400">Good:</strong> +2 to +4%</div>
                <div className="mb-2"><strong className="text-amber-400">Average:</strong> 0 to +2%</div>
                <div><strong className="text-red-400">Poor:</strong> Negative</div>
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-green-400 mb-2">Win %</div>
              <div className="text-sm text-slate-300 mb-3">Hit Rate</div>
              <div className="bg-slate-900/50 rounded p-3 text-left text-xs text-slate-400">
                <div className="mb-2"><strong className="text-green-400">Sharp:</strong> 54%+</div>
                <div className="mb-2"><strong className="text-blue-400">Good:</strong> 52-54%</div>
                <div className="mb-2"><strong className="text-amber-400">Break Even:</strong> ~52.4%</div>
                <div><strong className="text-red-400">Losing:</strong> &lt;52%</div>
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-amber-400 mb-2">Units</div>
              <div className="text-sm text-slate-300 mb-3">Units Won/Month</div>
              <div className="bg-slate-900/50 rounded p-3 text-left text-xs text-slate-400">
                <div className="mb-2"><strong className="text-green-400">Pro:</strong> +30U+</div>
                <div className="mb-2"><strong className="text-blue-400">Serious:</strong> +15-30U</div>
                <div className="mb-2"><strong className="text-amber-400">Casual:</strong> +5-15U</div>
                <div><strong className="text-red-400">Struggling:</strong> &lt;+5U</div>
              </div>
            </div>
          </div>
        </div>

        {/* Final CTA */}
        <div className="bg-gradient-to-br from-blue-900/30 to-purple-900/30 border border-blue-800 rounded-2xl p-12 text-center">
          <h2 className="text-4xl font-bold text-slate-100 mb-4">
            Ready to Start Your Journey?
          </h2>
          <p className="text-lg text-slate-300 mb-8 max-w-2xl mx-auto">
            You now have the complete roadmap. Start with our free tier, follow the daily workflow, and track your progress.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="px-10 py-4 bg-blue-600 hover:bg-blue-700 text-white text-lg font-bold rounded-lg transition-colors shadow-lg shadow-blue-600/30">
              Start Free Account
            </button>
            <button className="px-10 py-4 bg-slate-700 hover:bg-slate-600 text-slate-200 text-lg font-bold rounded-lg transition-colors">
              Join Discord Community
            </button>
          </div>
          <p className="text-sm text-slate-400 mt-6">
            Questions? Email us at support@platform.com or join our Discord for 24/7 community help
          </p>
        </div>
      </div>
    </div>
  );
}
