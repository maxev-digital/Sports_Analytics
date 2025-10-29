/**
 * Odds Explained - Comprehensive Guide
 * Details all odds types tracked by The Odds API
 */

export function OddsExplained() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-12 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-block px-4 py-1 bg-blue-600/20 border border-blue-500/50 rounded-full mb-4">
            <span className="text-sm font-semibold text-blue-400 uppercase tracking-wider">Betting Education</span>
          </div>
          <h1 className="text-5xl font-bold text-slate-100 mb-4">
            Understanding Sports Betting Odds
          </h1>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
            A comprehensive guide to all betting markets tracked by MAX-EV Sports.
            Learn what each odds type means and how to use them strategically.
          </p>
        </div>

        {/* Introduction */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8 mb-8">
          <h2 className="text-2xl font-bold text-slate-100 mb-4">What Are Betting Odds?</h2>
          <p className="text-slate-300 mb-4">
            Betting odds represent the probability of an outcome and determine how much you can win.
            The Odds API tracks odds from <strong>60+ sportsbooks</strong> across multiple regions,
            giving you the power to find the best lines and maximize your edge.
          </p>
          <p className="text-slate-300">
            MAX-EV Sports currently displays the most popular markets, but we're tracking <strong>ALL</strong> available
            odds types behind the scenes. This page covers everything you need to know about each market type.
          </p>
        </div>

        {/* Core Markets Section */}
        <div className="mb-12">
          <div className="border-l-4 border-blue-500 pl-4 mb-8">
            <h2 className="text-3xl font-bold text-slate-100 mb-2">
              Core Markets
            </h2>
            <p className="text-slate-400">Primary betting options available across all major sports</p>
          </div>

          {/* H2H - Moneyline */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-2xl font-bold text-green-400 mb-2">Moneyline (H2H)</h3>
                <span className="text-xs bg-green-900/30 text-green-300 px-3 py-1 rounded-full">
                  Head-to-Head
                </span>
              </div>
              <span className="text-sm bg-slate-700 text-slate-300 px-3 py-1 rounded-lg">
                API Key: <code className="text-blue-400">h2h</code>
              </span>
            </div>
            <p className="text-slate-300 mb-4">
              Bet on which team will win the game outright. No point spreads involved.
            </p>
            <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-2">Example:</p>
              <div className="flex gap-6 text-sm">
                <div>
                  <span className="text-slate-300">Lakers:</span> <span className="text-green-400 font-bold">-150</span>
                  <span className="text-xs text-slate-400 ml-2">(Favorite - bet $150 to win $100)</span>
                </div>
                <div>
                  <span className="text-slate-300">Warriors:</span> <span className="text-blue-400 font-bold">+130</span>
                  <span className="text-xs text-slate-400 ml-2">(Underdog - bet $100 to win $130)</span>
                </div>
              </div>
            </div>
            <div className="mt-4 p-4 bg-blue-900/20 border-l-4 border-blue-500 rounded">
              <p className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-1">Strategy Insight</p>
              <p className="text-sm text-blue-300">
                Great for games with a clear favorite. Look for underdog value when the spread is close but moneyline odds are inflated.
              </p>
            </div>
          </div>

          {/* Spreads */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-2xl font-bold text-blue-400 mb-2">Point Spreads</h3>
                <span className="text-xs bg-blue-900/30 text-blue-300 px-3 py-1 rounded-full">
                  Most Popular
                </span>
              </div>
              <span className="text-sm bg-slate-700 text-slate-300 px-3 py-1 rounded-lg">
                API Key: <code className="text-blue-400">spreads</code>
              </span>
            </div>
            <p className="text-slate-300 mb-4">
              Bet on the margin of victory. The favorite must win by more than the spread;
              the underdog must lose by less than the spread or win outright.
            </p>
            <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-2">Example:</p>
              <div className="flex gap-6 text-sm">
                <div>
                  <span className="text-slate-300">Lakers:</span> <span className="text-red-400 font-bold">-7.5</span> <span className="text-slate-400">(-110)</span>
                  <span className="text-xs text-slate-400 ml-2">(Must win by 8+ points)</span>
                </div>
                <div>
                  <span className="text-slate-300">Warriors:</span> <span className="text-green-400 font-bold">+7.5</span> <span className="text-slate-400">(-110)</span>
                  <span className="text-xs text-slate-400 ml-2">(Can lose by 7 or less)</span>
                </div>
              </div>
            </div>
            <div className="mt-4 p-4 bg-blue-900/20 border-l-4 border-blue-500 rounded">
              <p className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-1">Strategy Insight</p>
              <p className="text-sm text-blue-300">
                Watch for line movement. If the spread moves from -7 to -6.5, sharp money may be on the underdog. Track our steam move alerts for real-time notifications.
              </p>
            </div>
          </div>

          {/* Totals */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-2xl font-bold text-purple-400 mb-2">Totals (Over/Under)</h3>
                <span className="text-xs bg-purple-900/30 text-purple-300 px-3 py-1 rounded-full">
                  Getting Max EV Through Analytics
                </span>
              </div>
              <span className="text-sm bg-slate-700 text-slate-300 px-3 py-1 rounded-lg">
                API Key: <code className="text-blue-400">totals</code>
              </span>
            </div>
            <p className="text-slate-300 mb-4">
              Bet on whether the combined score of both teams will be over or under a specific number.
            </p>
            <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-2">Example:</p>
              <div className="flex gap-6 text-sm">
                <div>
                  <span className="text-slate-300">Total:</span> <span className="text-amber-400 font-bold">225.5</span>
                </div>
                <div>
                  <span className="text-green-400 font-bold">Over 225.5</span> <span className="text-slate-400">(-110)</span>
                  <span className="text-xs text-slate-400 ml-2">(Combined score 226+)</span>
                </div>
                <div>
                  <span className="text-red-400 font-bold">Under 225.5</span> <span className="text-slate-400">(-110)</span>
                  <span className="text-xs text-slate-400 ml-2">(Combined score 225 or less)</span>
                </div>
              </div>
            </div>
            <div className="mt-4 p-4 bg-purple-900/20 border-l-4 border-purple-500 rounded">
              <p className="text-xs font-semibold text-purple-400 uppercase tracking-wider mb-1">MAX-EV Advantage</p>
              <p className="text-sm text-purple-300">
                Our pace-based models excel at predicting totals. Live totals are especially profitable when pace shifts dramatically during the game.
              </p>
            </div>
          </div>
        </div>

        {/* Player Props Section */}
        <div className="mb-12">
          <div className="border-l-4 border-yellow-500 pl-4 mb-8">
            <h2 className="text-3xl font-bold text-slate-100 mb-2">
              Player Props
            </h2>
            <p className="text-slate-400">Individual player performance betting markets</p>
          </div>

          {/* Player Points */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-2xl font-bold text-yellow-400 mb-2">Player Points</h3>
                <span className="text-xs bg-yellow-900/30 text-yellow-300 px-3 py-1 rounded-full">
                  High Volume
                </span>
              </div>
              <span className="text-sm bg-slate-700 text-slate-300 px-3 py-1 rounded-lg">
                API Key: <code className="text-blue-400">player_points</code>
              </span>
            </div>
            <p className="text-slate-300 mb-4">
              Bet on whether a specific player will score over or under a set number of points.
            </p>
            <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-2">Example:</p>
              <div className="text-sm">
                <span className="text-slate-300">LeBron James Points:</span> <span className="text-amber-400 font-bold">25.5</span>
                <div className="mt-2 flex gap-6">
                  <span className="text-green-400">Over 25.5 (-115)</span>
                  <span className="text-red-400">Under 25.5 (-105)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Player Rebounds */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-2xl font-bold text-orange-400 mb-2">Player Rebounds</h3>
              </div>
              <span className="text-sm bg-slate-700 text-slate-300 px-3 py-1 rounded-lg">
                API Key: <code className="text-blue-400">player_rebounds</code>
              </span>
            </div>
            <p className="text-slate-300 mb-4">
              Bet on total rebounds (offensive + defensive) for a specific player.
            </p>
          </div>

          {/* Player Assists */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-2xl font-bold text-cyan-400 mb-2">Player Assists</h3>
              </div>
              <span className="text-sm bg-slate-700 text-slate-300 px-3 py-1 rounded-lg">
                API Key: <code className="text-blue-400">player_assists</code>
              </span>
            </div>
            <p className="text-slate-300 mb-4">
              Bet on the number of assists a player will record.
            </p>
          </div>

          {/* Player Threes */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-2xl font-bold text-green-400 mb-2">Player Threes Made</h3>
              </div>
              <span className="text-sm bg-slate-700 text-slate-300 px-3 py-1 rounded-lg">
                API Key: <code className="text-blue-400">player_threes</code>
              </span>
            </div>
            <p className="text-slate-300 mb-4">
              Bet on how many three-pointers a player will make. Popular for sharpshooters.
            </p>
          </div>

          {/* Other Player Props */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 mb-6">
            <h3 className="text-xl font-bold text-slate-100 mb-4">Additional Player Props</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-3">
                <p className="text-slate-200 font-semibold mb-1">Steals</p>
                <code className="text-xs text-blue-400">player_steals</code>
              </div>
              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-3">
                <p className="text-slate-200 font-semibold mb-1">Blocks</p>
                <code className="text-xs text-blue-400">player_blocks</code>
              </div>
              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-3">
                <p className="text-slate-200 font-semibold mb-1">Turnovers</p>
                <code className="text-xs text-blue-400">player_turnovers</code>
              </div>
              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-3">
                <p className="text-slate-200 font-semibold mb-1">Steals + Blocks</p>
                <code className="text-xs text-blue-400">player_blocks_steals</code>
              </div>
              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-3">
                <p className="text-slate-200 font-semibold mb-1">Points + Rebounds + Assists</p>
                <code className="text-xs text-blue-400">player_points_rebounds_assists</code>
              </div>
              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-3">
                <p className="text-slate-200 font-semibold mb-1">Points + Rebounds</p>
                <code className="text-xs text-blue-400">player_points_rebounds</code>
              </div>
              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-3">
                <p className="text-slate-200 font-semibold mb-1">Points + Assists</p>
                <code className="text-xs text-blue-400">player_points_assists</code>
              </div>
              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-3">
                <p className="text-slate-200 font-semibold mb-1">Rebounds + Assists</p>
                <code className="text-xs text-blue-400">player_rebounds_assists</code>
              </div>
              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-3">
                <p className="text-slate-200 font-semibold mb-1">Double Double</p>
                <code className="text-xs text-blue-400">player_double_double</code>
              </div>
              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-3">
                <p className="text-slate-200 font-semibold mb-1">Triple Double</p>
                <code className="text-xs text-blue-400">player_triple_double</code>
              </div>
            </div>
          </div>
        </div>

        {/* Team Props Section */}
        <div className="mb-12">
          <div className="border-l-4 border-indigo-500 pl-4 mb-8">
            <h2 className="text-3xl font-bold text-slate-100 mb-2">
              Team Props & Derivatives
            </h2>
            <p className="text-slate-400">Team-specific and time-based betting markets</p>
          </div>

          {/* Team Totals */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-2xl font-bold text-indigo-400 mb-2">Team Totals</h3>
                <span className="text-xs bg-indigo-900/30 text-indigo-300 px-3 py-1 rounded-full">
                  Arbitrage Friendly
                </span>
              </div>
              <span className="text-sm bg-slate-700 text-slate-300 px-3 py-1 rounded-lg">
                API Key: <code className="text-blue-400">team_totals</code>
              </span>
            </div>
            <p className="text-slate-300 mb-4">
              Bet on whether a single team will score over or under a specific point total.
            </p>
            <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-2">Example:</p>
              <div className="text-sm">
                <span className="text-slate-300">Lakers Team Total:</span> <span className="text-amber-400 font-bold">115.5</span>
                <div className="mt-2 flex gap-6">
                  <span className="text-green-400">Over 115.5 (-110)</span>
                  <span className="text-red-400">Under 115.5 (-110)</span>
                </div>
              </div>
            </div>
            <div className="mt-4 p-4 bg-indigo-900/20 border-l-4 border-indigo-500 rounded">
              <p className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-1">Arbitrage Opportunity</p>
              <p className="text-sm text-indigo-300">
                Team totals can create middle opportunities when paired with game totals. If Lakers team total is 115.5 and game total is 225.5, there's potential value.
              </p>
            </div>
          </div>

          {/* 1st Half / 2nd Half / Quarter Markets */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 mb-6">
            <h3 className="text-2xl font-bold text-pink-400 mb-4">Derivative Markets</h3>
            <p className="text-slate-300 mb-4">
              Bet on specific periods of the game rather than the full game result.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-4">
                <p className="text-slate-200 font-semibold mb-2">1st Half</p>
                <p className="text-xs text-slate-400 mb-1">Spread, Total, Moneyline for first half only</p>
                <code className="text-xs text-blue-400">h2h_1st_half, spreads_1st_half, totals_1st_half</code>
              </div>
              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-4">
                <p className="text-slate-200 font-semibold mb-2">2nd Half</p>
                <p className="text-xs text-slate-400 mb-1">Spread, Total, Moneyline for second half only</p>
                <code className="text-xs text-blue-400">h2h_2nd_half, spreads_2nd_half, totals_2nd_half</code>
              </div>
              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-4">
                <p className="text-slate-200 font-semibold mb-2">1st Quarter</p>
                <p className="text-xs text-slate-400 mb-1">Spread, Total, Moneyline for Q1</p>
                <code className="text-xs text-blue-400">h2h_1st_quarter, spreads_1st_quarter, totals_1st_quarter</code>
              </div>
              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-4">
                <p className="text-slate-200 font-semibold mb-2">Other Quarters</p>
                <p className="text-xs text-slate-400 mb-1">2nd, 3rd, 4th quarter markets</p>
                <code className="text-xs text-blue-400">*_2nd_quarter, *_3rd_quarter, *_4th_quarter</code>
              </div>
            </div>
          </div>
        </div>

        {/* Advanced Markets Section */}
        <div className="mb-12">
          <div className="border-l-4 border-teal-500 pl-4 mb-8">
            <h2 className="text-3xl font-bold text-slate-100 mb-2">
              Advanced & Exotic Markets
            </h2>
            <p className="text-slate-400">Specialized betting options for experienced bettors</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Alternate Lines */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <h3 className="text-xl font-bold text-teal-400 mb-3">Alternate Lines</h3>
              <p className="text-slate-300 text-sm mb-3">
                Buy or sell points to get better odds at different spreads and totals.
              </p>
              <code className="text-xs text-blue-400 block mb-2">alternate_spreads</code>
              <code className="text-xs text-blue-400 block">alternate_totals</code>
              <div className="mt-3 p-2 bg-slate-900/50 rounded text-xs text-slate-400">
                Example: Instead of -7.5 (-110), take -3.5 (+150) or -10.5 (-180)
              </div>
            </div>

            {/* First Basket */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <h3 className="text-xl font-bold text-lime-400 mb-3">First Basket</h3>
              <p className="text-slate-300 text-sm mb-3">
                Bet on which player scores the first basket of the game.
              </p>
              <code className="text-xs text-blue-400 block">player_first_basket</code>
              <div className="mt-3 p-2 bg-slate-900/50 rounded text-xs text-slate-400">
                Popular NBA prop with high variance and big payouts
              </div>
            </div>

            {/* Last Basket */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <h3 className="text-xl font-bold text-amber-400 mb-3">Last Basket</h3>
              <p className="text-slate-300 text-sm mb-3">
                Bet on which player scores the last basket of the game.
              </p>
              <code className="text-xs text-blue-400 block">player_last_basket</code>
            </div>

            {/* Anytime Basket */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <h3 className="text-xl font-bold text-rose-400 mb-3">Anytime Basket</h3>
              <p className="text-slate-300 text-sm mb-3">
                Bet on whether a player scores at any point during the game.
              </p>
              <code className="text-xs text-blue-400 block">player_anytime_basket</code>
            </div>

            {/* First/Last TD (NFL) */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <h3 className="text-xl font-bold text-orange-400 mb-3">Touchdown Scorers (NFL)</h3>
              <p className="text-slate-300 text-sm mb-3">
                Bet on first, last, or anytime touchdown scorer in NFL games.
              </p>
              <code className="text-xs text-blue-400 block mb-1">player_first_td</code>
              <code className="text-xs text-blue-400 block mb-1">player_last_td</code>
              <code className="text-xs text-blue-400 block">player_anytime_td</code>
            </div>

            {/* Pass/Rush/Rec Yards (NFL) */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <h3 className="text-xl font-bold text-blue-400 mb-3">NFL Player Yards</h3>
              <p className="text-slate-300 text-sm mb-3">
                Passing, rushing, and receiving yard props for NFL players.
              </p>
              <code className="text-xs text-blue-400 block mb-1">player_pass_yds</code>
              <code className="text-xs text-blue-400 block mb-1">player_rush_yds</code>
              <code className="text-xs text-blue-400 block">player_reception_yds</code>
            </div>

            {/* Goals/Shots (NHL) */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <h3 className="text-xl font-bold text-cyan-400 mb-3">NHL Player Props</h3>
              <p className="text-slate-300 text-sm mb-3">
                Goals, assists, shots, and goalie saves for NHL games.
              </p>
              <code className="text-xs text-blue-400 block mb-1">player_goal</code>
              <code className="text-xs text-blue-400 block mb-1">player_assists</code>
              <code className="text-xs text-blue-400 block mb-1">player_shots_on_goal</code>
              <code className="text-xs text-blue-400 block">goalie_saves</code>
            </div>

            {/* Pitcher Props (MLB) */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <h3 className="text-xl font-bold text-red-400 mb-3">MLB Pitcher Props</h3>
              <p className="text-slate-300 text-sm mb-3">
                Strikeouts, earned runs, hits allowed, and more.
              </p>
              <code className="text-xs text-blue-400 block mb-1">pitcher_strikeouts</code>
              <code className="text-xs text-blue-400 block mb-1">pitcher_hits_allowed</code>
              <code className="text-xs text-blue-400 block">pitcher_earned_runs</code>
            </div>

            {/* Batter Props (MLB) */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <h3 className="text-xl font-bold text-yellow-400 mb-3">MLB Batter Props</h3>
              <p className="text-slate-300 text-sm mb-3">
                Hits, home runs, RBIs, total bases for MLB hitters.
              </p>
              <code className="text-xs text-blue-400 block mb-1">batter_hits</code>
              <code className="text-xs text-blue-400 block mb-1">batter_home_runs</code>
              <code className="text-xs text-blue-400 block mb-1">batter_rbis</code>
              <code className="text-xs text-blue-400 block">batter_total_bases</code>
            </div>
          </div>
        </div>

        {/* American Odds Primer */}
        <div className="mb-12 bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-blue-700/50 rounded-2xl p-8">
          <div className="border-l-4 border-green-500 pl-4 mb-8">
            <h2 className="text-3xl font-bold text-slate-100 mb-2">
              Understanding American Odds
            </h2>
            <p className="text-slate-400">Learn how to read and calculate American odds format</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Negative Odds */}
            <div className="bg-slate-800/70 border border-slate-700 rounded-xl p-6">
              <h3 className="text-2xl font-bold text-red-400 mb-3">Negative Odds (Favorites)</h3>
              <p className="text-slate-300 mb-4">
                Negative odds like <span className="text-red-400 font-bold">-150</span> tell you how much you need to bet to win $100.
              </p>
              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-4">
                <p className="text-sm mb-2 text-slate-300">Example: <span className="text-red-400 font-bold">-150</span></p>
                <p className="text-xs text-slate-400 mb-1">• Bet $150 to win $100</p>
                <p className="text-xs text-slate-400 mb-1">• Total return: $250 (your $150 + $100 profit)</p>
                <p className="text-xs text-slate-400">• Implied probability: 60%</p>
              </div>
            </div>

            {/* Positive Odds */}
            <div className="bg-slate-800/70 border border-slate-700 rounded-xl p-6">
              <h3 className="text-2xl font-bold text-green-400 mb-3">Positive Odds (Underdogs)</h3>
              <p className="text-slate-300 mb-4">
                Positive odds like <span className="text-green-400 font-bold">+130</span> tell you how much you win if you bet $100.
              </p>
              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-4">
                <p className="text-sm mb-2 text-slate-300">Example: <span className="text-green-400 font-bold">+130</span></p>
                <p className="text-xs text-slate-400 mb-1">• Bet $100 to win $130</p>
                <p className="text-xs text-slate-400 mb-1">• Total return: $230 (your $100 + $130 profit)</p>
                <p className="text-xs text-slate-400">• Implied probability: 43.5%</p>
              </div>
            </div>
          </div>

          {/* Quick Reference Table */}
          <div className="bg-slate-800/70 border border-slate-700 rounded-xl p-6">
            <h3 className="text-xl font-bold text-slate-100 mb-4">Quick Conversion Reference</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="text-center p-3 bg-slate-900/50 rounded">
                <p className="text-red-400 font-bold">-200</p>
                <p className="text-xs text-slate-400">66.7% prob</p>
              </div>
              <div className="text-center p-3 bg-slate-900/50 rounded">
                <p className="text-red-400 font-bold">-150</p>
                <p className="text-xs text-slate-400">60% prob</p>
              </div>
              <div className="text-center p-3 bg-slate-900/50 rounded">
                <p className="text-slate-300 font-bold">-110</p>
                <p className="text-xs text-slate-400">52.4% prob</p>
              </div>
              <div className="text-center p-3 bg-slate-900/50 rounded">
                <p className="text-slate-300 font-bold">+100</p>
                <p className="text-xs text-slate-400">50% prob</p>
              </div>
              <div className="text-center p-3 bg-slate-900/50 rounded">
                <p className="text-green-400 font-bold">+150</p>
                <p className="text-xs text-slate-400">40% prob</p>
              </div>
              <div className="text-center p-3 bg-slate-900/50 rounded">
                <p className="text-green-400 font-bold">+200</p>
                <p className="text-xs text-slate-400">33.3% prob</p>
              </div>
              <div className="text-center p-3 bg-slate-900/50 rounded">
                <p className="text-green-400 font-bold">+300</p>
                <p className="text-xs text-slate-400">25% prob</p>
              </div>
              <div className="text-center p-3 bg-slate-900/50 rounded">
                <p className="text-green-400 font-bold">+500</p>
                <p className="text-xs text-slate-400">16.7% prob</p>
              </div>
            </div>
          </div>
        </div>

        {/* Juice/Vig Explanation */}
        <div className="mb-12 bg-slate-800/50 border border-slate-700 rounded-2xl p-8">
          <div className="border-l-4 border-amber-500 pl-4 mb-6">
            <h2 className="text-3xl font-bold text-slate-100 mb-2">Understanding Juice (Vig)</h2>
            <p className="text-slate-400">How sportsbooks build in their commission</p>
          </div>
          <p className="text-slate-300 mb-4">
            The "juice" or "vigorish" is the sportsbook's commission built into the odds.
            Standard juice is <strong>-110</strong> on both sides of a bet.
          </p>

          <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-6 mb-4">
            <h3 className="text-lg font-bold text-slate-100 mb-3">Example: Standard Line</h3>
            <div className="flex gap-8 text-sm">
              <div>
                <p className="text-slate-300">Lakers -7.5 <span className="text-red-400 font-bold">(-110)</span></p>
                <p className="text-xs text-slate-400">Bet $110 to win $100</p>
              </div>
              <div>
                <p className="text-slate-300">Warriors +7.5 <span className="text-red-400 font-bold">(-110)</span></p>
                <p className="text-xs text-slate-400">Bet $110 to win $100</p>
              </div>
            </div>
            <div className="mt-4 p-4 bg-amber-900/20 border-l-4 border-amber-500 rounded">
              <p className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-1">Key Concept</p>
              <p className="text-sm text-amber-300">
                The sportsbook collects $220 in bets but only pays out $210 (original $110 + $100 win).
                The $10 difference is the juice—their guaranteed profit.
              </p>
            </div>
          </div>

          <div className="p-4 bg-blue-900/20 border-l-4 border-blue-500 rounded">
            <p className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-1">MAX-EV Advantage</p>
            <p className="text-sm text-blue-300">
              Our No-Vig Calculator removes the juice to show true fair odds. Line shopping across 60+ books helps you find the lowest juice and maximize your edge.
            </p>
          </div>
        </div>

        {/* Future Markets Section */}
        <div className="mb-12">
          <div className="border-l-4 border-purple-500 pl-4 mb-8">
            <h2 className="text-3xl font-bold text-slate-100 mb-2">
              Futures & Outrights
            </h2>
            <p className="text-slate-400">Long-term betting markets for season outcomes</p>
          </div>

          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
            <p className="text-slate-300 mb-6">
              Long-term bets on season outcomes like championship winners, division winners, MVP awards, and season win totals.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-4">
                <h3 className="text-lg font-bold text-yellow-400 mb-2">Championship Futures</h3>
                <p className="text-xs text-slate-400 mb-2">Bet on NBA Champion, Super Bowl Winner, Stanley Cup, etc.</p>
                <code className="text-xs text-blue-400">outrights</code>
              </div>

              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-4">
                <h3 className="text-lg font-bold text-green-400 mb-2">Season Win Totals</h3>
                <p className="text-xs text-slate-400 mb-2">Over/under on total wins for the season</p>
                <code className="text-xs text-blue-400">team_win_totals</code>
              </div>

              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-4">
                <h3 className="text-lg font-bold text-purple-400 mb-2">Awards</h3>
                <p className="text-xs text-slate-400 mb-2">MVP, Rookie of the Year, Coach of the Year, etc.</p>
                <code className="text-xs text-blue-400">player_futures</code>
              </div>
            </div>

            <div className="mt-6 p-4 bg-purple-900/20 border-l-4 border-purple-500 rounded">
              <p className="text-xs font-semibold text-purple-400 uppercase tracking-wider mb-1">Coming Soon</p>
              <p className="text-sm text-purple-300">
                MAX-EV Sports will be adding futures tracking and value identification for championship bets, win totals, and award markets.
              </p>
            </div>
          </div>
        </div>

        {/* Call to Action */}
        <div className="bg-gradient-to-r from-green-900/30 to-blue-900/30 border border-green-700/50 rounded-2xl p-12 text-center">
          <div className="inline-block px-4 py-1 bg-green-600/20 border border-green-500/50 rounded-full mb-4">
            <span className="text-xs font-semibold text-green-400 uppercase tracking-wider">Get Started</span>
          </div>
          <h2 className="text-4xl font-bold text-slate-100 mb-4">
            Ready to Find Your Edge?
          </h2>
          <p className="text-lg text-slate-300 mb-8 max-w-2xl mx-auto leading-relaxed">
            MAX-EV Sports tracks all these markets across 60+ sportsbooks in real-time.
            Find the best lines, identify arbitrage opportunities, and maximize your expected value.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/live-games"
              className="px-10 py-4 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg transition-all shadow-xl uppercase tracking-wide text-sm"
            >
              Start Live Betting
            </a>
            <a
              href="/pricing"
              className="px-10 py-4 bg-slate-700 hover:bg-slate-600 border border-slate-600 text-white font-bold rounded-lg transition-all shadow-xl uppercase tracking-wide text-sm"
            >
              View Pricing
            </a>
          </div>
        </div>

        {/* Footer Note */}
        <div className="mt-12 p-6 bg-slate-800/30 border border-slate-700 rounded-lg text-center">
          <p className="text-sm text-slate-400">
            <strong className="text-slate-300">Important Notice:</strong> Not all markets are available for all sports or all bookmakers.
            Availability varies by sportsbook, region, and sport. MAX-EV Sports is continually adding new markets as they become available.
          </p>
        </div>
      </div>
    </div>
  );
}
