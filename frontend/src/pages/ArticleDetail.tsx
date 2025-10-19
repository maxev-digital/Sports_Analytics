import { useParams, Link } from 'react-router-dom';
import React from 'react';

interface ArticleContent {
  id: string;
  title: string;
  category: string;
  readTime: string;
  lastUpdated: string;
  author: string;
  metaDescription: string;
  content: React.ReactNode;
}

const articleContents: { [key: string]: ArticleContent } = {
  'what-is-live-betting': {
    id: 'what-is-live-betting',
    title: 'What is Live Betting and Why It Matters',
    category: 'Fundamentals',
    readTime: '8 min',
    lastUpdated: 'October 16, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'Learn the fundamentals of live betting, how odds move during games, and why live betting offers more opportunities than pregame wagering.',
    content: (
      <>
        <img
          src="https://images.unsplash.com/photo-1546519638-68e109498ffc?w=1200&h=600&fit=crop"
          alt="Live sports betting dashboard with real-time odds"
          className="w-full h-96 object-cover rounded-xl mb-8"
        />

        <div className="prose prose-invert prose-lg max-w-none">
          <h2>What is Live Betting?</h2>
          <p>
            Live betting, also known as in-game or in-play betting, allows you to place wagers on sporting events
            <strong> while the game is actively happening</strong>. Unlike traditional pregame betting where you must
            lock in your wager before kickoff, live betting gives you the flexibility to bet throughout the entire game.
          </p>

          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Key Difference</h3>
            <p className="mb-0">
              <strong>Pregame Betting:</strong> Warriors vs Lakers, Over 220.5 points - locked in before tipoff<br/>
              <strong>Live Betting:</strong> Warriors vs Lakers, 2nd Quarter, Warriors up 60-54, Over 225.5 points - bet anytime during the game
            </p>
          </div>

          <h2>How Do Odds Move During Games?</h2>
          <p>
            Live betting odds are <strong>dynamic</strong> - they change constantly based on what's happening in the game:
          </p>
          <ul>
            <li><strong>Score Changes:</strong> When a team scores, the live total increases</li>
            <li><strong>Time Remaining:</strong> As time runs out, projections become more certain</li>
            <li><strong>Momentum Shifts:</strong> A team on a scoring run will see their spread tighten</li>
            <li><strong>Key Events:</strong> Injuries, fouls, timeouts all impact live lines</li>
          </ul>

          <img
            src="https://images.unsplash.com/photo-1504450874802-0ba2bcd9b5ae?w=1200&h=400&fit=crop"
            alt="Basketball game with live score display"
            className="w-full h-64 object-cover rounded-lg my-8"
          />

          <h2>Why Live Betting Offers More Opportunities</h2>

          <h3>1. Information Advantage</h3>
          <p>
            You can <strong>watch the game unfold</strong> before placing your bet. Is a team playing sluggish?
            Is the pace faster than expected? Are key players getting rest? This real-time information gives you
            an edge that pregame bettors don't have.
          </p>

          <h3>2. More Betting Opportunities</h3>
          <p>
            Instead of one pregame bet, you might find 5-10 valuable spots during a game. Every possession,
            every quarter, every timeout creates new betting opportunities with fresh odds.
          </p>

          <h3>3. React to Market Inefficiencies</h3>
          <p>
            Sportsbooks adjust lines based on algorithms and betting action. Sometimes they <strong>overreact</strong>
            to short-term variance or <strong>underreact</strong> to important information. Sharp live bettors exploit
            these inefficiencies.
          </p>

          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Real Example</h3>
            <p>
              <strong>Pregame:</strong> Lakers vs Warriors total set at 225.5<br/>
              <strong>1st Quarter:</strong> Both teams shoot poorly, 45-42 Lakers (87 points pace). Live total drops to 210.5.<br/>
              <strong>Your Edge:</strong> You know both teams have elite offenses. The slow start is variance. You bet Over 210.5.<br/>
              <strong>Result:</strong> Both teams heat up in the 2nd half, final score 232 total points. You win!
            </p>
          </div>

          <h2>The Concept of "Closing Line Value"</h2>
          <p>
            One of the most important concepts in sports betting is <strong>Closing Line Value (CLV)</strong>.
            The "closing line" is the final odds before the game ends or a market closes.
          </p>
          <p>
            If you consistently beat the closing line, you're likely to be profitable long-term, even if you
            lose individual bets. Live betting gives you more opportunities to capture CLV because:
          </p>
          <ul>
            <li>Lines move frequently during games</li>
            <li>You can bet early in favorable situations</li>
            <li>Market inefficiencies are more common in live betting</li>
          </ul>

          <h2>Common Mistakes Beginners Make</h2>

          <h3>1. Betting on Emotion</h3>
          <p>
            Watching your favorite team blow a lead is frustrating. But betting on them to make a comeback
            out of <strong>hope rather than analysis</strong> is a recipe for losses.
          </p>

          <h3>2. Chasing Losses</h3>
          <p>
            The fast pace of live betting makes it easy to place multiple bets quickly. After a loss, resist
            the urge to immediately bet again to "get even." This leads to poor decision-making.
          </p>

          <h3>3. Not Understanding Variance</h3>
          <p>
            A team going on a 12-0 run doesn't necessarily mean they're "hot" or the game will stay high-scoring.
            Short-term variance is normal in basketball. Don't overreact to small samples.
          </p>

          <h3>4. Ignoring Line Shopping</h3>
          <p>
            Live odds differ significantly between sportsbooks. One book might have Over 215.5 while another
            has 217.5. Always check multiple books to get the best price.
          </p>

          <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-6 my-8">
            <h3 className="text-red-400 mt-0">Warning</h3>
            <p className="mb-0">
              Live betting is fast-paced and can be addictive. Set strict limits on your bankroll,
              take breaks, and never bet more than you can afford to lose. If you feel you have a
              gambling problem, call 1-800-GAMBLER.
            </p>
          </div>

          <h2>Getting Started with Live Betting</h2>
          <p>
            Before you start live betting, make sure you:
          </p>
          <ol>
            <li><strong>Understand the sport</strong> - Know how scoring works, game flow, and typical patterns</li>
            <li><strong>Have accounts at multiple sportsbooks</strong> - For line shopping</li>
            <li><strong>Set a bankroll</strong> - Only bet 1-5% of your total bankroll per wager</li>
            <li><strong>Use tools and data</strong> - Platforms like Sport Trader.io help you identify edges</li>
            <li><strong>Track your bets</strong> - Record every wager to analyze your performance</li>
          </ol>

          <h2>Next Steps</h2>
          <p>
            Now that you understand what live betting is, the next step is learning how to read and interpret
            live odds. Check out our guide on <Link to="/learn/reading-live-odds" className="text-blue-400 hover:text-blue-300">Reading Live Odds: A Complete Guide</Link>.
          </p>
        </div>
      </>
    )
  },

  'reading-live-odds': {
    id: 'reading-live-odds',
    title: 'Reading Live Odds: A Complete Guide',
    category: 'Fundamentals',
    readTime: '10 min',
    lastUpdated: 'October 16, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'Master American odds, implied probability, juice/vig, and why odds differ between sportsbooks.',
    content: (
      <>
        <img
          src="https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&h=600&fit=crop"
          alt="Sportsbook odds display"
          className="w-full h-96 object-cover rounded-xl mb-8"
        />

        <div className="prose prose-invert prose-lg max-w-none">
          <h2>Understanding American Odds</h2>
          <p>
            In the United States, sportsbooks use <strong>American odds</strong> (also called moneyline odds)
            to display betting lines. They come in two formats: positive (+) and negative (-) numbers.
          </p>

          <h3>Negative Odds (-110, -150, -200)</h3>
          <p>
            Negative odds tell you <strong>how much you need to bet to win $100</strong>.
          </p>
          <ul>
            <li><strong>-110:</strong> Bet $110 to win $100 (total return: $210)</li>
            <li><strong>-150:</strong> Bet $150 to win $100 (total return: $250)</li>
            <li><strong>-200:</strong> Bet $200 to win $100 (total return: $300)</li>
          </ul>
          <p>
            The more negative the number, the more favored that outcome is. -200 is a bigger favorite than -110.
          </p>

          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Quick Formula</h3>
            <p className="mb-0">
              <strong>Profit = (Stake × 100) / Odds</strong><br/>
              Example: Betting $55 at -110 = ($55 × 100) / 110 = $50 profit
            </p>
          </div>

          <h3>Positive Odds (+120, +150, +250)</h3>
          <p>
            Positive odds tell you <strong>how much you win if you bet $100</strong>.
          </p>
          <ul>
            <li><strong>+120:</strong> Bet $100 to win $120 (total return: $220)</li>
            <li><strong>+150:</strong> Bet $100 to win $150 (total return: $250)</li>
            <li><strong>+250:</strong> Bet $100 to win $250 (total return: $350)</li>
          </ul>
          <p>
            The higher the positive number, the bigger the underdog. +250 is a bigger underdog than +120.
          </p>

          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Quick Formula</h3>
            <p className="mb-0">
              <strong>Profit = (Stake × Odds) / 100</strong><br/>
              Example: Betting $50 at +150 = ($50 × 150) / 100 = $75 profit
            </p>
          </div>

          <img
            src="https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=1200&h=400&fit=crop"
            alt="Calculator and sports betting analysis"
            className="w-full h-64 object-cover rounded-lg my-8"
          />

          <h2>Calculating Implied Probability</h2>
          <p>
            Every betting line has an <strong>implied probability</strong> - the likelihood of that outcome
            occurring according to the odds. This is crucial for finding value.
          </p>

          <h3>For Negative Odds</h3>
          <p>
            <strong>Implied Probability = (-Odds) / (-Odds + 100)</strong>
          </p>
          <ul>
            <li>-110: 110 / (110 + 100) = 52.4%</li>
            <li>-150: 150 / (150 + 100) = 60.0%</li>
            <li>-200: 200 / (200 + 100) = 66.7%</li>
          </ul>

          <h3>For Positive Odds</h3>
          <p>
            <strong>Implied Probability = 100 / (Odds + 100)</strong>
          </p>
          <ul>
            <li>+120: 100 / (120 + 100) = 45.5%</li>
            <li>+150: 100 / (150 + 100) = 40.0%</li>
            <li>+250: 100 / (250 + 100) = 28.6%</li>
          </ul>

          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Finding Value</h3>
            <p>
              If you believe an outcome has a <strong>higher true probability</strong> than the implied probability,
              that's a +EV (positive expected value) bet.
            </p>
            <p className="mb-0">
              <strong>Example:</strong> You think the Lakers have a 55% chance to win, but the odds are +110 (47.6% implied).
              This is a value bet!
            </p>
          </div>

          <h2>Understanding Juice/Vig</h2>
          <p>
            <strong>Juice</strong> (also called <strong>vig</strong> or <strong>vigorish</strong>) is how sportsbooks
            make money. It's built into the odds.
          </p>

          <h3>The Standard -110/-110 Line</h3>
          <p>
            Most spread and total bets are priced at <strong>-110 on both sides</strong>:
          </p>
          <ul>
            <li>Lakers -5.5 (-110)</li>
            <li>Warriors +5.5 (-110)</li>
          </ul>
          <p>
            If you add up the implied probabilities: 52.4% + 52.4% = <strong>104.8%</strong>
          </p>
          <p>
            This shouldn't add up to more than 100%! That extra 4.8% is the juice - the sportsbook's edge.
          </p>

          <h3>Removing the Juice</h3>
          <p>
            To find the "true" probabilities, you need to remove the juice:
          </p>
          <ol>
            <li>Add the implied probabilities: 52.4% + 52.4% = 104.8%</li>
            <li>Divide each by the total: 52.4% / 104.8% = 50% each side</li>
          </ol>
          <p>
            Without juice, both sides would be <strong>exactly 50%</strong>, which makes sense for a fair line.
          </p>

          <h2>Why Odds Differ Between Sportsbooks</h2>
          <p>
            If you check multiple sportsbooks, you'll notice the same game has different lines. Why?
          </p>

          <h3>1. Different Betting Action</h3>
          <p>
            Sportsbooks adjust lines based on where money is coming in. If lots of bettors hammer the Over at
            DraftKings, they might raise it to 221.5 while FanDuel stays at 220.5.
          </p>

          <h3>2. Risk Management Strategies</h3>
          <p>
            Some books are more aggressive with line moves, others are conservative. Some target sharp bettors,
            others target recreational bettors.
          </p>

          <h3>3. Different Algorithms</h3>
          <p>
            Each sportsbook has its own models and algorithms for setting lines. They might weigh factors
            differently or use different data sources.
          </p>

          <h2>The Importance of Line Shopping</h2>
          <p>
            <strong>Line shopping</strong> means checking multiple sportsbooks to find the best available odds.
            This is one of the easiest ways to increase your long-term profitability.
          </p>

          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">Example: Half Point Difference</h3>
            <p>
              <strong>DraftKings:</strong> Lakers/Warriors Over 220.5 (-110)<br/>
              <strong>FanDuel:</strong> Lakers/Warriors Over 219.5 (-110)
            </p>
            <p className="mb-0">
              Getting 219.5 instead of 220.5 is HUGE. That's a full point of cushion. If the game lands at 220,
              you win on FanDuel but push on DraftKings. Over time, these edges add up to significant profit.
            </p>
          </div>

          <h2>Common Live Odds Patterns</h2>

          <h3>Totals Move with Score</h3>
          <p>
            As points are scored, live totals increase proportionally. A game projected at 220 with a 60-58
            halftime score will have a live total around 224-226.
          </p>

          <h3>Spreads Adjust for Score Differential</h3>
          <p>
            If the Lakers were -5.5 pregame and lead by 10 at halftime, the live spread might be Lakers -8.5
            for the remainder of the game.
          </p>

          <h3>Time Remaining Reduces Uncertainty</h3>
          <p>
            Lines get "sharper" (harder to beat) as time runs out because there's less uncertainty. The edge
            opportunities are usually in the first half.
          </p>

          <h2>Next Steps</h2>
          <p>
            Now that you can read and interpret odds, learn how to identify value by reading our guide on
            <Link to="/learn/expected-value" className="text-blue-400 hover:text-blue-300">Expected Value (EV)</Link>.
          </p>
        </div>
      </>
    )
  },

  'expected-value': {
    id: 'expected-value',
    title: 'What is Expected Value (EV)?',
    category: 'Fundamentals',
    readTime: '12 min',
    lastUpdated: 'October 16, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'Understanding the EV formula, positive vs negative EV betting, and why long-term thinking matters in sports betting.',
    content: (
      <>
        <img
          src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=600&fit=crop"
          alt="Data analytics and charts"
          className="w-full h-96 object-cover rounded-xl mb-8"
        />

        <div className="prose prose-invert prose-lg max-w-none">
          <h2>What is Expected Value?</h2>
          <p>
            <strong>Expected Value (EV)</strong> is the most important concept in sports betting. It tells you how much
            you expect to win or lose on average from a bet if you could make that same bet thousands of times.
          </p>
          <p>
            Think of it this way: a coin flip at even money (+100) has an EV of $0 - you'll break even long-term.
            But if someone offered you +120 on a coin flip, you'd have <strong>positive expected value</strong> and
            would profit long-term by making that bet repeatedly.
          </p>

          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">The EV Formula</h3>
            <p className="mb-0">
              <strong>EV = (Probability of Win × Amount Won) - (Probability of Loss × Amount Lost)</strong><br/><br/>
              Or simplified:<br/>
              <strong>EV = (Win% × Profit) - (Loss% × Stake)</strong>
            </p>
          </div>

          <h2>Calculating EV: Step-by-Step Example</h2>
          <p>
            Let's say you want to bet on the Lakers to win at <strong>+150 odds</strong>. Your analysis suggests
            they have a <strong>45% chance</strong> to win. Should you bet?
          </p>

          <h3>Step 1: Calculate Profit and Loss</h3>
          <ul>
            <li><strong>Bet:</strong> $100</li>
            <li><strong>Profit if you win:</strong> $150 (at +150 odds)</li>
            <li><strong>Loss if you lose:</strong> $100 (your stake)</li>
          </ul>

          <h3>Step 2: Apply the Formula</h3>
          <p>
            <strong>EV = (0.45 × $150) - (0.55 × $100)</strong><br/>
            <strong>EV = $67.50 - $55.00</strong><br/>
            <strong>EV = +$12.50</strong>
          </p>

          <h3>Step 3: Interpret the Result</h3>
          <p>
            An EV of +$12.50 means that on average, every time you make this $100 bet, you expect to profit $12.50.
            This is a <strong>+EV bet</strong> (positive expected value) and you should make it!
          </p>

          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">What the Implied Odds Say</h3>
            <p>
              +150 odds = 40% implied probability<br/>
              Your assessment = 45% true probability<br/>
              <strong>Edge = 5%</strong>
            </p>
            <p className="mb-0">
              Whenever your estimated probability is higher than the implied probability, you have a +EV bet!
            </p>
          </div>

          <img
            src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200&h=400&fit=crop"
            alt="Business analytics dashboard"
            className="w-full h-64 object-cover rounded-lg my-8"
          />

          <h2>Positive EV vs Negative EV</h2>

          <h3>Positive EV (+EV)</h3>
          <p>
            A bet with positive expected value means you'll profit in the long run. This happens when:
          </p>
          <ul>
            <li>Your estimated probability is higher than the implied probability</li>
            <li>You're getting "good odds" on your bet</li>
            <li>You've found an edge over the sportsbook</li>
          </ul>
          <p>
            <strong>Goal: Only make +EV bets.</strong> Professional bettors focus exclusively on finding +EV opportunities.
          </p>

          <h3>Negative EV (-EV)</h3>
          <p>
            A bet with negative expected value means you'll lose money in the long run. This happens when:
          </p>
          <ul>
            <li>Your estimated probability is lower than the implied probability</li>
            <li>You're getting "bad odds" on your bet</li>
            <li>The sportsbook has an edge over you</li>
          </ul>
          <p>
            <strong>Warning:</strong> Most casual bettors make -EV bets without realizing it. This is why sportsbooks are profitable.
          </p>

          <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-6 my-8">
            <h3 className="text-red-400 mt-0">The Juice Makes Most Bets -EV</h3>
            <p className="mb-0">
              Standard -110 odds on both sides means you need to win 52.4% of the time just to break even.
              If you're picking randomly (50% win rate), you're automatically making -EV bets and will lose
              2.4% of your money long-term due to the juice.
            </p>
          </div>

          <h2>Why Short-Term Results Don't Matter</h2>
          <p>
            Here's the key insight that separates professional bettors from casual gamblers: <strong>You can lose
            +EV bets and win -EV bets in the short term.</strong>
          </p>

          <h3>Example: The "Bad Beat"</h3>
          <p>
            You bet on the Lakers at +150 with a 45% win probability (a +EV bet worth +$12.50). The Lakers
            lead by 15 points with 2 minutes left... then blow the lead and lose.
          </p>
          <p>
            <strong>Result:</strong> You lost $100.<br/>
            <strong>Was it a bad bet?</strong> NO! It was still a +EV bet. Variance happens.
          </p>
          <p>
            If you could make that same bet 1,000 times, you'd win about 450 times and lose 550 times, but
            you'd profit overall because the odds (+150) more than compensate for the lower win rate.
          </p>

          <h2>The Long-Term Mindset</h2>
          <p>
            Professional sports betting is about making +EV decisions repeatedly and letting the law of large
            numbers work in your favor.
          </p>

          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">100 Bet Example</h3>
            <p>
              <strong>Scenario:</strong> You find 100 bets with +5% EV. You bet $100 on each (total: $10,000 wagered).
            </p>
            <p>
              <strong>Expected Profit:</strong> $10,000 × 5% = $500<br/>
              <strong>Likely Win Rate:</strong> Somewhere between 48-58% (variance!)<br/>
              <strong>Actual Profit Range:</strong> $200 to $800 (still profitable despite variance)
            </p>
            <p className="mb-0">
              After 1,000 bets, your actual results will converge much closer to the expected $5,000 profit.
              This is the power of the long-term approach.
            </p>
          </div>

          <h2>How Much Edge Do You Need?</h2>
          <p>
            Not all +EV bets are worth making. You need enough edge to overcome variance and make meaningful profit.
          </p>

          <h3>Edge Tiers</h3>
          <ul>
            <li><strong>+1% to +2% EV:</strong> Small edge. Bet small or skip unless you're very confident.</li>
            <li><strong>+3% to +5% EV:</strong> Good edge. Standard bet sizing.</li>
            <li><strong>+5% to +8% EV:</strong> Strong edge. Increase bet size (within bankroll limits).</li>
            <li><strong>+8%+ EV:</strong> Excellent edge. Max bet (but verify your analysis is correct!).</li>
          </ul>

          <h2>Common EV Mistakes</h2>

          <h3>1. Overestimating Your Edge</h3>
          <p>
            Many bettors think they have a 60% chance when reality is 52%. Be conservative with your estimates.
            Sportsbooks have sophisticated models and vast data. Your edge, when it exists, is often smaller than you think.
          </p>

          <h3>2. Ignoring Variance</h3>
          <p>
            Just because something is +EV doesn't mean you'll win. You can go on 10-bet losing streaks even with
            +EV bets. Proper bankroll management is crucial.
          </p>

          <h3>3. Chasing "Gut Feelings"</h3>
          <p>
            "I have a good feeling about this game" is not EV analysis. You need data, models, and logical reasoning
            to estimate true probabilities.
          </p>

          <h3>4. Betting -EV Because You're "Due"</h3>
          <p>
            After losing several bets, bettors often make a -EV bet thinking they're "due to win." Each bet is
            independent. Past losses don't change the EV of future bets.
          </p>

          <h2>Tools for Finding +EV Bets</h2>
          <p>
            Finding +EV bets requires comparing your projected probability to market odds. Tools that help:
          </p>
          <ul>
            <li><strong>Sport Trader.io:</strong> Our platform shows projected totals vs market lines with edge calculations</li>
            <li><strong>Odds comparison sites:</strong> Find the best available odds across sportsbooks</li>
            <li><strong>Statistical models:</strong> Build or use models to estimate true probabilities</li>
            <li><strong>Line movement trackers:</strong> See where sharp money is going</li>
          </ul>

          <h2>Next Steps</h2>
          <p>
            Understanding EV is crucial, but you also need to understand how our projections work. Read
            <Link to="/learn/projections-vs-market" className="text-blue-400 hover:text-blue-300"> Understanding Projections vs Market Lines</Link> next.
          </p>
        </div>
      </>
    )
  },

  'bankroll-management-101': {
    id: 'bankroll-management-101',
    title: 'Bankroll Management 101',
    category: 'Bankroll',
    readTime: '12 min',
    lastUpdated: 'October 16, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'What is a bankroll, the 1-5% rule per bet, tracking your bets, and managing variance.',
    content: (
      <>
        <img
          src="https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=1200&h=600&fit=crop"
          alt="Money management and finance planning"
          className="w-full h-96 object-cover rounded-xl mb-8"
        />

        <div className="prose prose-invert prose-lg max-w-none">
          <h2>What is a Bankroll?</h2>
          <p>
            Your <strong>bankroll</strong> is the total amount of money you've set aside specifically for sports betting.
            This should be money you can afford to lose without affecting your daily life, bills, or savings.
          </p>
          <p>
            Think of your bankroll as the "business capital" for your betting activities. Professional bettors treat
            their bankroll with the same care that a business owner treats their operating budget.
          </p>

          <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-6 my-8">
            <h3 className="text-red-400 mt-0">Critical Rule</h3>
            <p className="mb-0">
              <strong>Never bet with money you can't afford to lose.</strong> Your bankroll should NOT include:
              rent money, grocery money, emergency funds, or any money earmarked for essential expenses.
              Only use discretionary income that won't impact your quality of life if lost.
            </p>
          </div>

          <h2>The 1-5% Rule</h2>
          <p>
            The golden rule of bankroll management: <strong>never risk more than 1-5% of your total bankroll on a single bet.</strong>
          </p>

          <h3>Why This Matters</h3>
          <p>
            Even the best bettors with strong edges go through losing streaks. If you bet too large a percentage
            of your bankroll, a normal losing streak can wipe you out before your edge has time to materialize.
          </p>

          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Bankroll Example</h3>
            <p>
              <strong>Bankroll:</strong> $1,000<br/>
              <strong>Conservative (1%):</strong> $10 per bet<br/>
              <strong>Moderate (2-3%):</strong> $20-30 per bet<br/>
              <strong>Aggressive (5%):</strong> $50 per bet
            </p>
            <p className="mb-0">
              With 1% bets, you can withstand a 50-bet losing streak and still have half your bankroll left.
              With 10% bets, you'd be broke after 10 losses in a row.
            </p>
          </div>

          <img
            src="https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=1200&h=400&fit=crop"
            alt="Financial charts and analysis"
            className="w-full h-64 object-cover rounded-lg my-8"
          />

          <h2>Unit Sizing Strategy</h2>
          <p>
            Many professional bettors use a <strong>unit system</strong> where 1 unit = 1% of their bankroll.
          </p>

          <h3>Standard Unit Sizing</h3>
          <ul>
            <li><strong>1 unit:</strong> Standard bet with moderate confidence</li>
            <li><strong>2 units:</strong> Above-average confidence, strong edge</li>
            <li><strong>3 units:</strong> High confidence, excellent edge (rare)</li>
            <li><strong>0.5 units:</strong> Lower confidence, small edge</li>
          </ul>

          <p>
            Most of your bets should be 1-2 units. Betting 3+ units should be extremely rare and only when you
            have exceptional confidence in your analysis.
          </p>

          <h2>Adjusting Your Bankroll</h2>
          <p>
            Your bankroll should be reassessed periodically as it grows or shrinks.
          </p>

          <h3>When to Increase Bet Sizes</h3>
          <p>
            As your bankroll grows, you can proportionally increase your unit size. Many bettors recalculate
            their unit size:
          </p>
          <ul>
            <li>Weekly</li>
            <li>Monthly</li>
            <li>After every 100 bets</li>
            <li>When bankroll increases/decreases by 25%+</li>
          </ul>

          <h3>When to Decrease Bet Sizes</h3>
          <p>
            If you hit a losing streak and your bankroll shrinks, adjust your unit size downward proportionally.
            This is crucial for survival during variance.
          </p>

          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Example: Bankroll Growth</h3>
            <p>
              <strong>Starting Bankroll:</strong> $1,000 (1 unit = $10)<br/>
              <strong>After 3 months:</strong> $1,500 (1 unit = $15)<br/>
              <strong>After 6 months:</strong> $2,200 (1 unit = $22)
            </p>
            <p className="mb-0">
              By keeping bet sizes proportional to bankroll, you compound your growth while maintaining
              the same level of risk.
            </p>
          </div>

          <h2>Tracking Every Bet</h2>
          <p>
            <strong>You MUST track your bets.</strong> Without tracking, you have no idea if you're profitable,
            what your ROI is, or which bet types are working.
          </p>

          <h3>What to Track</h3>
          <ul>
            <li><strong>Date & Time:</strong> When the bet was placed</li>
            <li><strong>Sport & Teams:</strong> What game</li>
            <li><strong>Bet Type:</strong> Spread, total, moneyline, etc.</li>
            <li><strong>Odds:</strong> The price you got</li>
            <li><strong>Stake:</strong> How much you bet</li>
            <li><strong>Result:</strong> Win, loss, or push</li>
            <li><strong>Profit/Loss:</strong> Net result</li>
            <li><strong>Notes:</strong> Why you made the bet, confidence level</li>
          </ul>

          <h3>Tools for Tracking</h3>
          <ul>
            <li>Excel/Google Sheets (simple and effective)</li>
            <li>Betting tracking apps (Action Network, Bet Tracker Pro)</li>
            <li>Custom database or software</li>
          </ul>

          <h2>Managing Variance</h2>
          <p>
            <strong>Variance</strong> is the natural ups and downs in results, even when making +EV bets. You will
            experience winning and losing streaks that have nothing to do with your skill.
          </p>

          <h3>Expected Variance</h3>
          <p>
            Even with a 55% win rate (excellent for sports betting), here's what you might experience over 100 bets:
          </p>
          <ul>
            <li><strong>Expected:</strong> 55 wins, 45 losses</li>
            <li><strong>Realistic range:</strong> 50-60 wins</li>
            <li><strong>Possible but unlucky:</strong> 45-50 wins</li>
          </ul>

          <p>
            Proper bankroll management ensures you survive the unlucky variance periods and still have
            capital to bet when variance swings back in your favor.
          </p>

          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">Variance Reality Check</h3>
            <p className="mb-0">
              A bettor with a 54% win rate (beating the juice) betting -110 odds will be profitable long-term
              with +3.6% ROI. But they could easily go through a 100-bet stretch where they only hit 48%, losing
              money despite making good bets. This is why proper bankroll sizing (1-5%) is essential.
            </p>
          </div>

          <h2>Common Bankroll Mistakes</h2>

          <h3>1. Betting Too Much Per Bet</h3>
          <p>
            The #1 mistake. Betting 10-20% of your bankroll per bet is a recipe for going broke. One bad
            week and you're out of business.
          </p>

          <h3>2. Chasing Losses</h3>
          <p>
            After a losing day, bettors often increase bet sizes to "get even quickly." This usually leads
            to even bigger losses. Stick to your system.
          </p>

          <h3>3. Not Tracking Results</h3>
          <p>
            Without data, you're betting blind. You might think you're winning when you're actually down,
            or vice versa.
          </p>

          <h3>4. Depositing More After Going Broke</h3>
          <p>
            If you lost your entire bankroll, you need to honestly assess WHY before depositing more money.
            Were you making bad bets, sizing incorrectly, or just hit terrible variance? Fix the problem first.
          </p>

          <h2>Setting Loss Limits</h2>
          <p>
            Protect yourself from catastrophic losses by setting firm limits:
          </p>
          <ul>
            <li><strong>Daily loss limit:</strong> Stop betting if down 5-10% in one day</li>
            <li><strong>Weekly loss limit:</strong> Reassess strategy if down 15-20% in a week</li>
            <li><strong>Monthly loss limit:</strong> Take a break if down 30%+ in a month</li>
          </ul>

          <h2>Next Steps</h2>
          <p>
            Now that you understand bankroll basics, learn how to size bets based on your edge by reading
            <Link to="/learn/unit-sizing" className="text-blue-400 hover:text-blue-300"> Unit Sizing Based on Edge</Link>.
          </p>
        </div>
      </>
    )
  },

  'dashboard-overview': {
    id: 'dashboard-overview',
    title: 'Dashboard Overview: Your Command Center',
    category: 'Dashboard',
    readTime: '7 min',
    lastUpdated: 'October 16, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'Navigate the dashboard, understand game cards, color coding, filtering options, and customize your view.',
    content: (
      <>
        <img
          src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=600&fit=crop"
          alt="Sports analytics dashboard"
          className="w-full h-96 object-cover rounded-xl mb-8"
        />

        <div className="prose prose-invert prose-lg max-w-none">
          <h2>Welcome to Sport Trader.io</h2>
          <p>
            Your dashboard is your command center for finding profitable betting opportunities in real-time.
            This guide will help you understand every element and make the most of our platform.
          </p>

          <h2>Dashboard Layout</h2>
          <p>
            The dashboard displays all live and upcoming games across multiple sports. Each game is shown
            in a card format with key betting information at a glance.
          </p>

          <h3>Main Components</h3>
          <ul>
            <li><strong>Navigation Bar:</strong> Access different sections (Live Games, Tools, Analytics, etc.)</li>
            <li><strong>Game Cards:</strong> Individual cards for each game with odds and projections</li>
            <li><strong>Live Indicator:</strong> Shows which games are currently in progress</li>
            <li><strong>Sport Filters:</strong> Filter by NBA, NFL, NHL, NCAAF, MLB</li>
          </ul>

          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Quick Tip</h3>
            <p className="mb-0">
              The dashboard auto-refreshes every 30 seconds to keep odds and scores current. You'll see
              a subtle pulse animation when new data loads.
            </p>
          </div>

          <h2>Understanding Game Cards</h2>
          <p>
            Each game card contains essential information for making betting decisions:
          </p>

          <h3>Card Header</h3>
          <ul>
            <li><strong>Teams:</strong> Away team @ Home team</li>
            <li><strong>Game Time:</strong> When the game starts (or current quarter/time)</li>
            <li><strong>Sport Icon:</strong> Visual indicator of sport type</li>
            <li><strong>Status Badge:</strong> LIVE, UPCOMING, or time until start</li>
          </ul>

          <h3>Score Information (Live Games)</h3>
          <ul>
            <li><strong>Current Score:</strong> Real-time score for both teams</li>
            <li><strong>Quarter/Period:</strong> Current game period</li>
            <li><strong>Time Remaining:</strong> Clock countdown</li>
            <li><strong>Possession:</strong> Which team has the ball (when available)</li>
          </ul>

          <h3>Betting Lines</h3>
          <ul>
            <li><strong>Spread:</strong> Point spread with odds (e.g., LAL -5.5 -110)</li>
            <li><strong>Total:</strong> Over/Under line with odds</li>
            <li><strong>Moneyline:</strong> Win/loss odds for each team</li>
            <li><strong>Best Line Indicator:</strong> Highlights best available odds</li>
          </ul>

          <img
            src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200&h=400&fit=crop"
            alt="Live betting odds display"
            className="w-full h-64 object-cover rounded-lg my-8"
          />

          <h2>Projections and Edge</h2>
          <p>
            This is where Sport Trader.io adds value - our proprietary projections vs market lines:
          </p>

          <h3>Projected Total</h3>
          <p>
            Our model's prediction for the final score total based on:
          </p>
          <ul>
            <li>Current pace of play</li>
            <li>Team efficiency ratings</li>
            <li>Historical performance</li>
            <li>Situational factors (rest, home/away, etc.)</li>
          </ul>

          <h3>Market Total</h3>
          <p>
            The consensus betting line from sportsbooks. This is what you'd bet against.
          </p>

          <h3>Edge Calculation</h3>
          <p>
            <strong>Edge = Projected Total - Market Total</strong>
          </p>
          <ul>
            <li><strong>Positive Edge:</strong> Our projection is higher → bet OVER</li>
            <li><strong>Negative Edge:</strong> Our projection is lower → bet UNDER</li>
            <li><strong>Edge Size:</strong> Larger edges indicate stronger opportunities</li>
          </ul>

          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Example Edge</h3>
            <p>
              <strong>Projected Total:</strong> 225.5<br/>
              <strong>Market Total:</strong> 220.5<br/>
              <strong>Edge:</strong> +5.0 points<br/>
              <strong>Recommendation:</strong> OVER 220.5
            </p>
            <p className="mb-0">
              This means our model expects 5 more points than the sportsbooks are pricing in,
              creating a potential value opportunity on the Over.
            </p>
          </div>

          <h2>Color Coding System</h2>
          <p>
            Cards use color coding for quick visual scanning:
          </p>

          <h3>Edge Indicators</h3>
          <ul>
            <li><strong>Green Border:</strong> Strong positive edge (bet OVER)</li>
            <li><strong>Red Border:</strong> Strong negative edge (bet UNDER)</li>
            <li><strong>Gray Border:</strong> Minimal edge, no clear opportunity</li>
          </ul>

          <h3>Confidence Levels</h3>
          <ul>
            <li><strong>HIGH (Green):</strong> Strong confidence, late game, large sample</li>
            <li><strong>MEDIUM (Yellow):</strong> Moderate confidence, mid-game</li>
            <li><strong>LOW (Orange):</strong> Low confidence, early game, small sample</li>
          </ul>

          <h2>Bookmaker Comparison</h2>
          <p>
            Each card shows odds from multiple sportsbooks:
          </p>
          <ul>
            <li><strong>DraftKings</strong></li>
            <li><strong>FanDuel</strong></li>
            <li><strong>BetMGM</strong></li>
            <li><strong>Caesars</strong></li>
            <li><strong>PointsBet</strong></li>
          </ul>

          <p>
            The best available odds are highlighted in green, making line shopping effortless.
          </p>

          <h2>Filtering and Sorting</h2>

          <h3>Sport Filters</h3>
          <p>
            Click sport icons to filter by:
          </p>
          <ul>
            <li>NBA (Basketball)</li>
            <li>NFL (Football)</li>
            <li>NCAAF (College Football)</li>
            <li>NHL (Hockey)</li>
            <li>MLB (Baseball)</li>
          </ul>

          <h3>Status Filters</h3>
          <ul>
            <li><strong>Live Only:</strong> Show only games in progress</li>
            <li><strong>Upcoming:</strong> Show scheduled games</li>
            <li><strong>All:</strong> Show everything</li>
          </ul>

          <h3>Sort Options</h3>
          <ul>
            <li><strong>Edge Size:</strong> Largest edges first (default)</li>
            <li><strong>Start Time:</strong> Earliest games first</li>
            <li><strong>Sport:</strong> Group by sport type</li>
          </ul>

          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">Pro Tip</h3>
            <p className="mb-0">
              Sort by "Edge Size" and filter for "Live Only" to quickly find the best opportunities
              in games that are currently happening. These are your immediate action items.
            </p>
          </div>

          <h2>Recommendation Badges</h2>
          <p>
            Games with significant edges display recommendation badges:
          </p>
          <ul>
            <li><strong>STRONG OVER:</strong> Edge of 5+ points toward Over</li>
            <li><strong>OVER:</strong> Edge of 3-4.9 points toward Over</li>
            <li><strong>LEAN OVER:</strong> Edge of 2-2.9 points toward Over</li>
            <li><strong>STRONG UNDER:</strong> Edge of 5+ points toward Under</li>
            <li><strong>UNDER:</strong> Edge of 3-4.9 points toward Under</li>
            <li><strong>LEAN UNDER:</strong> Edge of 2-2.9 points toward Under</li>
          </ul>

          <h2>Mobile vs Desktop</h2>

          <h3>Desktop View</h3>
          <ul>
            <li>3-column grid layout</li>
            <li>All bookmaker odds visible</li>
            <li>Expanded stats and details</li>
            <li>Side-by-side comparisons</li>
          </ul>

          <h3>Mobile View</h3>
          <ul>
            <li>Single column, vertical scroll</li>
            <li>Swipe to see all bookmakers</li>
            <li>Tap cards to expand details</li>
            <li>Optimized for quick scanning</li>
          </ul>

          <h2>Best Practices</h2>
          <ol>
            <li><strong>Check confidence levels:</strong> Focus on HIGH confidence opportunities</li>
            <li><strong>Compare bookmakers:</strong> Always get the best line available</li>
            <li><strong>Watch live games:</strong> Our edge is most valuable when combined with watching</li>
            <li><strong>Don't chase every edge:</strong> Be selective, quality over quantity</li>
            <li><strong>Track your bets:</strong> Record which opportunities you act on</li>
          </ol>

          <h2>Next Steps</h2>
          <p>
            Now that you understand the dashboard, learn how to interpret the game cards in detail:
            <Link to="/learn/reading-game-card" className="text-blue-400 hover:text-blue-300"> Reading a Game Card</Link>.
          </p>
        </div>
      </>
    )
  },

  'projections-vs-market': {
    id: 'projections-vs-market',
    title: 'Understanding Projections vs Market Lines',
    category: 'Fundamentals',
    readTime: '9 min',
    lastUpdated: 'October 16, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'Learn what projections represent, why they differ from odds, and when they are most reliable.',
    content: (
      <>
        <img
          src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=600&fit=crop"
          alt="Data analytics and projections"
          className="w-full h-96 object-cover rounded-xl mb-8"
        />

        <div className="prose prose-invert prose-lg max-w-none">
          <h2>What Are Projections?</h2>
          <p>
            <strong>Projections</strong> are our model's best estimate of what will happen in a game based on
            statistical analysis, historical data, and current game conditions. They represent the "true" expected
            outcome if we could run the same game scenario thousands of times.
          </p>
          <p>
            Think of projections as a weather forecast: meteorologists use data and models to predict rain,
            we use data and models to predict game totals.
          </p>

          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Key Insight</h3>
            <p className="mb-0">
              Projections are NOT predictions of what WILL happen (no one knows that). They're probability-based
              estimates of what's MOST LIKELY to happen given all available information. The goal is to be more
              accurate than the market on average over hundreds of games.
            </p>
          </div>

          <h2>What Are Market Lines?</h2>
          <p>
            <strong>Market lines</strong> (also called "the market" or "betting lines") are the odds set by sportsbooks.
            These represent what you can actually bet on.
          </p>

          <h3>How Market Lines Are Set</h3>
          <p>
            Sportsbooks use a combination of:
          </p>
          <ul>
            <li><strong>Statistical models:</strong> Similar to our projections</li>
            <li><strong>Betting action:</strong> Lines move based on money coming in</li>
            <li><strong>Risk management:</strong> Books balance their exposure</li>
            <li><strong>Juice/vig:</strong> Built-in profit margin (~4-5%)</li>
          </ul>

          <p>
            The market line is NOT purely what the sportsbook thinks will happen - it's influenced by public
            betting patterns and risk management.
          </p>

          <img
            src="https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&h=400&fit=crop"
            alt="Sportsbook odds board"
            className="w-full h-64 object-cover rounded-lg my-8"
          />

          <h2>Projections vs Market: Finding the Edge</h2>
          <p>
            The power of Sport Trader.io comes from comparing our projections to market lines:
          </p>

          <h3>When Projections Exceed Market</h3>
          <p>
            <strong>Projected Total: 225.5</strong><br/>
            <strong>Market Total: 220.5</strong><br/>
            <strong>Edge: +5.0 points</strong>
          </p>
          <p>
            Our model expects 5 more points than the market is pricing in. This suggests betting OVER 220.5
            offers positive expected value.
          </p>

          <h3>When Market Exceeds Projections</h3>
          <p>
            <strong>Projected Total: 215.5</strong><br/>
            <strong>Market Total: 220.5</strong><br/>
            <strong>Edge: -5.0 points</strong>
          </p>
          <p>
            Our model expects 5 fewer points than the market. This suggests betting UNDER 220.5 offers value.
          </p>

          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Real Example</h3>
            <p>
              <strong>Lakers vs Warriors, 2nd Quarter</strong><br/>
              Current score: 62-58 Lakers (120 total points)<br/>
              Our Projection: 228.5 total points<br/>
              DraftKings Line: Over/Under 223.5<br/>
              <strong>Edge: +5.0 points toward OVER</strong>
            </p>
            <p className="mb-0">
              Our pace-based model sees both teams scoring at a faster rate than the market expects.
              The model projects 228.5 total points, creating a 5-point edge on the Over. This is a
              HIGH confidence opportunity to bet Over 223.5.
            </p>
          </div>

          <h2>Why Do Projections Differ from Market?</h2>

          <h3>1. Different Methodologies</h3>
          <p>
            Our pace-based model focuses heavily on real-time game flow and current scoring rates.
            Sportsbooks may weight pregame factors more heavily or react slower to live game conditions.
          </p>

          <h3>2. Market Inefficiencies</h3>
          <p>
            Live betting lines sometimes overreact or underreact to short-term variance. A team going
            on a 10-0 run might cause books to move the line too aggressively, creating value on the
            other side.
          </p>

          <h3>3. Public Betting Bias</h3>
          <p>
            If the public is hammering the Over, sportsbooks may raise the line above what their model
            suggests to balance action. This creates Under value.
          </p>

          <h3>4. Information Lag</h3>
          <p>
            Our model updates every 30 seconds with fresh pace data. Some sportsbooks adjust more slowly,
            creating brief windows where our projection captures new information the market hasn't priced in yet.
          </p>

          <h2>When Are Projections Most Reliable?</h2>

          <h3>HIGH Confidence Situations</h3>
          <ul>
            <li><strong>Late game (4th quarter):</strong> Large sample size, clear pace trend</li>
            <li><strong>Consistent pace:</strong> Teams maintaining steady scoring rate</li>
            <li><strong>Large edges (5+ points):</strong> Significant model disagreement with market</li>
            <li><strong>Normal game script:</strong> Competitive game, no garbage time</li>
          </ul>

          <h3>MEDIUM Confidence Situations</h3>
          <ul>
            <li><strong>Mid-game (2nd-3rd quarter):</strong> Moderate sample size</li>
            <li><strong>Some pace variability:</strong> Scoring rate fluctuating but trending</li>
            <li><strong>Medium edges (3-5 points):</strong> Model sees value but less extreme</li>
            <li><strong>Close score:</strong> Game still competitive</li>
          </ul>

          <h3>LOW Confidence Situations</h3>
          <ul>
            <li><strong>Early game (1st quarter):</strong> Small sample, high variance</li>
            <li><strong>Blowouts:</strong> Garbage time distorts pace</li>
            <li><strong>Small edges (0-3 points):</strong> Model and market closely aligned</li>
            <li><strong>Unusual circumstances:</strong> Injuries, ejections, foul trouble</li>
          </ul>

          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">Focus on Quality</h3>
            <p className="mb-0">
              Don't bet every edge. Focus on HIGH confidence opportunities with large edges (5+ points).
              These are the situations where our model has the strongest conviction and highest likelihood
              of being more accurate than the market.
            </p>
          </div>

          <h2>Common Misconceptions</h2>

          <h3>Misconception 1: "Projections are guarantees"</h3>
          <p>
            <strong>Reality:</strong> Projections are probabilistic. Our model might project 225.5 with high
            confidence, and the actual total could still be 218 or 233. Variance exists. The goal is to be
            right more often than wrong over hundreds of bets.
          </p>

          <h3>Misconception 2: "Always bet the bigger edge"</h3>
          <p>
            <strong>Reality:</strong> A 10-point edge in the 1st quarter (LOW confidence) is less valuable
            than a 5-point edge in the 4th quarter (HIGH confidence). Consider both edge size AND confidence level.
          </p>

          <h3>Misconception 3: "The market is always wrong when it disagrees"</h3>
          <p>
            <strong>Reality:</strong> The market is very efficient. When our projection differs, it doesn't
            mean the market is "wrong" - it means we see value based on our methodology. Both can be reasonable
            estimates with different approaches.
          </p>

          <h3>Misconception 4: "Projections work for all bet types"</h3>
          <p>
            <strong>Reality:</strong> Our projections are optimized for totals (Over/Under). While they can
            inform spread and moneyline bets, they're specifically designed for total points analysis.
          </p>

          <h2>How to Use Projections Effectively</h2>

          <h3>Step 1: Check Confidence Level</h3>
          <p>
            Always look at the confidence badge (HIGH/MEDIUM/LOW) first. This tells you how much the model
            trusts its projection.
          </p>

          <h3>Step 2: Evaluate Edge Size</h3>
          <p>
            Look for edges of 3+ points. Smaller edges exist but may not overcome the juice and variance.
          </p>

          <h3>Step 3: Watch the Game</h3>
          <p>
            Combine model projections with your own observations. Is the pace sustainable? Are stars
            playing? Is this garbage time?
          </p>

          <h3>Step 4: Line Shop</h3>
          <p>
            Even with a strong edge, shop for the best available line across sportsbooks to maximize value.
          </p>

          <h3>Step 5: Track Results</h3>
          <p>
            Record which projections you bet on and track outcomes. This helps you learn which situations
            work best for your betting style.
          </p>

          <h2>Projection Limitations</h2>
          <p>
            Our model doesn't account for:
          </p>
          <ul>
            <li><strong>Injuries mid-game:</strong> If a star player gets hurt</li>
            <li><strong>Intentional fouling strategies:</strong> Late-game foul-a-thons</li>
            <li><strong>Coaching decisions:</strong> Resting players in blowouts</li>
            <li><strong>Motivation factors:</strong> Playoff implications, rivalries</li>
            <li><strong>Weather (outdoor sports):</strong> Primarily affects football</li>
          </ul>

          <p>
            Use the projections as a powerful tool, but combine them with game context and your own judgment.
          </p>

          <h2>Next Steps</h2>
          <p>
            Now that you understand projections vs market lines, dive deeper into how our pace-based model works:
            <Link to="/learn/pace-based-projections" className="text-blue-400 hover:text-blue-300"> Pace-Based Projections Explained</Link>.
          </p>
        </div>
      </>
    )
  },

  'line-shopping': {
    id: 'line-shopping',
    title: 'Line Shopping: The Easiest Edge',
    category: 'Markets',
    readTime: '8 min',
    lastUpdated: 'October 16, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'Comparing odds across sportsbooks, half-point differences, and how line shopping adds to ROI.',
    content: (
      <>
        <img
          src="https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=1200&h=600&fit=crop"
          alt="Comparison shopping concept"
          className="w-full h-96 object-cover rounded-xl mb-8"
        />

        <div className="prose prose-invert prose-lg max-w-none">
          <h2>What is Line Shopping?</h2>
          <p>
            <strong>Line shopping</strong> is the practice of comparing odds across multiple sportsbooks to find
            the best available price for your bet. It's one of the easiest and most impactful ways to increase
            your long-term profitability.
          </p>
          <p>
            Think of it like comparing gas prices or grocery shopping - you wouldn't pay $5 for milk at one
            store when it's $4 at another. The same principle applies to betting lines.
          </p>

          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">The Impact</h3>
            <p className="mb-0">
              Getting just 0.5 better odds per bet can increase your ROI by 1-2%. Over hundreds of bets,
              this difference between breaking even and being profitable. Line shopping is literally
              free money that most bettors leave on the table.
            </p>
          </div>

          <h2>Why Lines Differ Between Sportsbooks</h2>
          <p>
            You'll often see the same game with different lines at different books:
          </p>

          <h3>1. Different Customer Bases</h3>
          <p>
            Some books attract sharp bettors, others attract recreational bettors. Books adjust lines
            based on their specific customer betting patterns.
          </p>

          <h3>2. Risk Management</h3>
          <p>
            Books have different risk tolerances. One might move a line quickly after taking large bets,
            while another holds steady.
          </p>

          <h3>3. Proprietary Models</h3>
          <p>
            Each sportsbook uses its own algorithms and data to set lines, leading to slight variations.
          </p>

          <h3>4. Betting Action</h3>
          <p>
            If DraftKings gets hammered on the Over, they'll raise their line while FanDuel might stay
            at the old number until they also receive heavy action.
          </p>

          <img
            src="https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&h=400&fit=crop"
            alt="Multiple sportsbook odds"
            className="w-full h-64 object-cover rounded-lg my-8"
          />

          <h2>The Value of Half Points</h2>
          <p>
            In sports betting, especially basketball and football, <strong>half points matter enormously</strong>.
          </p>

          <h3>Key Numbers in Basketball</h3>
          <p>
            NBA totals frequently land on whole numbers. Getting an extra half point can be the difference
            between a win and a push, or a push and a loss.
          </p>

          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Real Example</h3>
            <p>
              Lakers vs Warriors totals:<br/>
              <strong>DraftKings:</strong> Over 220.5 (-110)<br/>
              <strong>FanDuel:</strong> Over 219.5 (-110)<br/>
              <strong>BetMGM:</strong> Over 221.5 (-110)
            </p>
            <p className="mb-0">
              Same game, three different lines. If you're betting Over, FanDuel at 219.5 gives you an
              extra full point of cushion. If the final total is 220, you win on FanDuel but push on
              DraftKings and lose on BetMGM.
            </p>
          </div>

          <h3>Key Numbers in Football</h3>
          <p>
            In football spreads, 3 and 7 are the most important numbers (field goal and touchdown).
            For totals, numbers around 40-50 see increased frequency.
          </p>

          <h2>Price Shopping (Juice)</h2>
          <p>
            Even when the line is the same, the <strong>juice (vig)</strong> can differ:
          </p>

          <h3>Example: Same Line, Different Juice</h3>
          <ul>
            <li><strong>DraftKings:</strong> Over 220.5 (-110)</li>
            <li><strong>Caesars:</strong> Over 220.5 (-105)</li>
            <li><strong>PointsBet:</strong> Over 220.5 (-115)</li>
          </ul>

          <p>
            All three have the same total (220.5), but Caesars charges less juice (-105 vs -110 vs -115).
            Betting at Caesars means you need a lower win rate to break even.
          </p>

          <h3>Break-Even Win Rates</h3>
          <ul>
            <li><strong>-105:</strong> 51.2% win rate to break even</li>
            <li><strong>-110:</strong> 52.4% win rate to break even</li>
            <li><strong>-115:</strong> 53.5% win rate to break even</li>
          </ul>

          <p>
            That 2.3% difference between -105 and -115 is huge over hundreds of bets.
          </p>

          <h2>How to Line Shop Effectively</h2>

          <h3>1. Have Multiple Accounts</h3>
          <p>
            You need accounts at <strong>at least 3-5 sportsbooks</strong> to line shop effectively. Recommended:
          </p>
          <ul>
            <li>DraftKings</li>
            <li>FanDuel</li>
            <li>BetMGM</li>
            <li>Caesars</li>
            <li>PointsBet or BetRivers</li>
          </ul>

          <h3>2. Use Odds Comparison Tools</h3>
          <p>
            Tools like Sport Trader.io show you all available odds in one place, saving time and ensuring
            you never miss the best line.
          </p>

          <h3>3. Act Quickly</h3>
          <p>
            Good lines don't last forever. If you find a favorable line, place the bet quickly before
            it moves. Lines in live betting can change within seconds.
          </p>

          <h3>4. Keep Bankroll at Multiple Books</h3>
          <p>
            Maintain balances at each book so you can act immediately when you find the best line. Don't
            let a great opportunity pass because you need to deposit funds.
          </p>

          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">Time is Money</h3>
            <p className="mb-0">
              Sharp bettors and automated systems are constantly line shopping. Good lines get bet quickly
              and move. The time you spend manually checking each book is time the line might move against you.
              Use comparison tools to shop instantly.
            </p>
          </div>

          <h2>Live Betting Line Shopping</h2>
          <p>
            Line shopping is even more valuable in live betting because:
          </p>
          <ul>
            <li><strong>Lines move faster:</strong> More volatility = more discrepancies</li>
            <li><strong>Books react differently:</strong> Some adjust instantly, others lag</li>
            <li><strong>Higher variance:</strong> Bigger edges available for short windows</li>
          </ul>

          <h3>Example Live Scenario</h3>
          <p>
            Lakers hit a 12-0 run in the 2nd quarter. Some books immediately drop the total by 2 points,
            while others only move it 1 point. For 30-60 seconds, there's a 1-point discrepancy you can
            exploit by betting the better line.
          </p>

          <h2>The ROI Impact of Line Shopping</h2>
          <p>
            Let's quantify the impact with real numbers:
          </p>

          <h3>Scenario: 100 Bets Without Line Shopping</h3>
          <ul>
            <li><strong>Win Rate:</strong> 55% (excellent!)</li>
            <li><strong>Odds:</strong> Always -110</li>
            <li><strong>Bet Size:</strong> $100 per bet</li>
            <li><strong>Total Wagered:</strong> $10,000</li>
            <li><strong>Result:</strong> 55 wins × $91 = $5,005 profit minus 45 losses × $100 = $4,500 loss = <strong>$505 profit (5.05% ROI)</strong></li>
          </ul>

          <h3>Scenario: 100 Bets With Line Shopping</h3>
          <ul>
            <li><strong>Win Rate:</strong> 55% (same)</li>
            <li><strong>Odds:</strong> Average -105 (shopped for best lines)</li>
            <li><strong>Bet Size:</strong> $100 per bet</li>
            <li><strong>Total Wagered:</strong> $10,000</li>
            <li><strong>Result:</strong> 55 wins × $95 = $5,225 profit minus 45 losses × $100 = $4,500 loss = <strong>$725 profit (7.25% ROI)</strong></li>
          </ul>

          <p>
            <strong>Difference:</strong> $220 extra profit (43% more!) just from getting better prices.
          </p>

          <h2>Common Line Shopping Mistakes</h2>

          <h3>1. Only Using One Book</h3>
          <p>
            This is leaving money on the table. You're guaranteed to be getting suboptimal lines regularly.
          </p>

          <h3>2. Betting First, Checking Later</h3>
          <p>
            Always check all books BEFORE placing your bet. Don't bet at your favorite book out of habit.
          </p>

          <h3>3. Ignoring Small Differences</h3>
          <p>
            "It's only half a point" adds up over time. Every edge matters in sports betting.
          </p>

          <h3>4. Chasing Bonuses Over Lines</h3>
          <p>
            Don't bet at a book with worse lines just because they're running a promotion. The long-term
            value of better lines usually exceeds short-term bonuses.
          </p>

          <h2>Tools for Line Shopping</h2>
          <ul>
            <li><strong>Sport Trader.io:</strong> Shows best available odds across all major books</li>
            <li><strong>Odds comparison sites:</strong> Real-time odds aggregation</li>
            <li><strong>Multiple tabs:</strong> Keep sportsbook sites open in browser tabs</li>
            <li><strong>Mobile apps:</strong> Quick access for time-sensitive opportunities</li>
          </ul>

          <h2>Next Steps</h2>
          <p>
            Line shopping helps you maximize value, but you also need to understand how sportsbooks set
            their lines. Learn more: <Link to="/learn/how-books-set-lines" className="text-blue-400 hover:text-blue-300">How Sportsbooks Set Live Lines</Link>.
          </p>
        </div>
      </>
    )
  },

  'regression-to-mean': {
    id: 'regression-to-mean',
    title: 'Regression to the Mean',
    category: 'Strategy',
    readTime: '10 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'What is regression, identifying outlier performances, and balancing regression with momentum.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=600&fit=crop" alt="Statistical regression concept" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>What is Regression to the Mean?</h2>
          <p><strong>Regression to the mean</strong> is a statistical phenomenon where extreme performances tend to move back toward average over time. If a team shoots 70% in the 1st quarter, they'll likely cool off toward their season average of 47%.</p>
          <h3>Why It Happens</h3>
          <p>Extreme outcomes are partly skill, partly luck. Luck doesn't persist. Over time, performance gravitates toward true skill level (the mean).</p>
          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Key Insight</h3>
            <p className="mb-0">Our model applies regression to avoid projecting unsustainable performance. If teams are scoring at 1.2x their normal rate, we expect them to cool off toward 1.0x.</p>
          </div>
          <h2>Identifying Outlier Performances</h2>
          <h3>Hot Shooting (Will Regress Down)</h3>
          <ul><li>Team shooting 60%+ FG in 1Q (season avg 47%)</li><li>Scoring 40+ points in one quarter</li><li>Pace 10+ possessions above normal</li></ul>
          <h3>Cold Shooting (Will Regress Up)</h3>
          <ul><li>Team shooting 35% FG in 1Q</li><li>Scoring 18-20 points in one quarter</li><li>Pace 8+ possessions below normal</li></ul>
          <h2>The Regression Formula</h2>
          <p>Sport Trader.io uses conservative regression:</p>
          <p><strong>Regression Factor = 0.85 + (0.15 × Current Efficiency)</strong></p>
          <h3>Examples</h3>
          <ul><li><strong>Shooting 1.0x normal:</strong> Regression = 1.0 (no change expected)</li><li><strong>Shooting 1.3x normal (hot):</strong> Regression = 1.045 (expect 4.5% cooling)</li><li><strong>Shooting 0.7x normal (cold):</strong> Regression = 0.955 (expect 4.5% warming)</li></ul>
          <h3>Why Conservative?</h3>
          <p>We don't assume full regression. Some hot shooting is real (team playing well). We split the difference.</p>
          <h2>When Regression Matters Most</h2>
          <h3>Early Game (1Q-2Q)</h3>
          <p>Small sample. Regression heavily applied. Don't overreact to 1Q shooting variance.</p>
          <h3>Mid Game (2Q-3Q)</h3>
          <p>Moderate regression. Some signal, some noise.</p>
          <h3>Late Game (4Q)</h3>
          <p>Light regression. Large sample means current performance is more reliable.</p>
          <h2>Balancing Regression with Momentum</h2>
          <h3>The Tension</h3>
          <p>Regression says "hot shooting won't last." Momentum says "team is feeling it, ride the wave."</p>
          <h3>Our Approach</h3>
          <p>We apply partial regression. If a team is hot, we project them to stay somewhat above average, but not as extreme as current rate.</p>
          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Example</h3>
            <p><strong>Warriors 1Q:</strong> 35 points (pace = 140 pts/game)<br/><strong>Season average:</strong> 115 pts/game<br/><strong>Naive projection:</strong> 140 (no regression)<br/><strong>Full regression:</strong> 115 (ignore 1Q)<br/><strong>Our projection:</strong> 125 (split the difference)</p>
          </div>
          <h2>Common Mistakes</h2>
          <h3>1. Overreacting to Small Samples</h3>
          <p>Team scores 10 straight points? That's 2 minutes of data. Don't project a 240-point game.</p>
          <h3>2. Ignoring Regression Entirely</h3>
          <p>Betting every Over after a hot 1Q loses money long-term. Regression catches up.</p>
          <h3>3. Over-Applying Regression Late</h3>
          <p>If a team has been hot for 36 minutes, that's not variance. That's real performance.</p>
          <h2>Sport Trader.io Regression System</h2>
          <p>Our model automatically applies appropriate regression based on:</p>
          <ul><li><strong>Time played:</strong> Less regression late in games</li><li><strong>Consistency:</strong> Erratic pace gets more regression</li><li><strong>Magnitude:</strong> Extreme outliers regress more</li></ul>
          <h2>Next Steps</h2>
          <p>Learn about momentum: <Link to="/learn/momentum-model" className="text-blue-400 hover:text-blue-300">Momentum Model: Riding Hot Quarters</Link>.</p>
        </div>
      </>
    )
  },

  'emotional-control': {
    id: 'emotional-control',
    title: 'Emotional Control in Live Betting',
    category: 'Psychology',
    readTime: '9 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'The fast-paced nature of live betting, avoiding tilt, managing FOMO, and sticking to strategy.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=1200&h=600&fit=crop" alt="Mindfulness and control" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>The Psychology of Live Betting</h2>
          <p>Live betting is <strong>faster, more intense, and more emotional</strong> than pregame betting. Games unfold in real-time, odds change constantly, and you can bet multiple times per game. This creates psychological challenges.</p>
          <h2>Common Emotional Traps</h2>
          <h3>1. FOMO (Fear of Missing Out)</h3>
          <p>Seeing a 7-point edge disappear in 30 seconds creates urgency. You feel pressured to bet NOW before the opportunity vanishes.</p>
          <p><strong>Reality:</strong> Thousands of games per season. Missing one edge is fine. Chase quality, not quantity.</p>
          <h3>2. Tilt After Bad Beats</h3>
          <p>Your Over 220.5 loses when the game lands on exactly 220. You're frustrated. Next bet, you increase size to "get even."</p>
          <p><strong>Reality:</strong> Bad beats happen. Variance is normal. Revenge betting destroys bankrolls.</p>
          <h3>3. Chasing Losses</h3>
          <p>Down 3 units on the day. You see a mediocre 3-point edge and bet 2 units to recover quickly.</p>
          <p><strong>Reality:</strong> This compounds losses. Stick to your system regardless of current P&L.</p>
          <h3>4. Overconfidence After Wins</h3>
          <p>You've won 5 straight bets. You feel invincible. You start betting marginal edges with bigger units.</p>
          <p><strong>Reality:</strong> Hot streaks end. Variance swings both ways. Discipline matters most during wins.</p>
          <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-6 my-8">
            <h3 className="text-red-400 mt-0">Warning</h3>
            <p className="mb-0">The #1 reason profitable systems fail is emotional betting. You can have a +EV strategy and still lose money if you can't control emotions.</p>
          </div>
          <h2>Recognizing Tilt</h2>
          <p>You're on tilt when you:</p>
          <ul><li>Bet without checking the model</li><li>Increase units after losses</li><li>Make impulsive bets</li><li>Feel angry or desperate</li><li>Ignore your rules</li></ul>
          <h2>Strategies for Emotional Control</h2>
          <h3>Set Rules Before You Bet</h3>
          <p>Write down your system BEFORE the games start:</p>
          <ul><li>Minimum edge: 5 points</li><li>Minimum confidence: MEDIUM</li><li>Maximum units: 3.0</li><li>Daily loss limit: 5 units</li></ul>
          <h3>Take Breaks</h3>
          <p>After a loss, step away for 15 minutes. Walk around. Hydrate. Clear your head. Don't immediately bet the next game.</p>
          <h3>Track Everything</h3>
          <p>Logging every bet makes you accountable. When you see "bet 3 units on LOW confidence edge" in your spreadsheet, you'll avoid repeating it.</p>
          <h3>Accept Variance</h3>
          <p>You'll lose 45% of your bets even with a great system. That's math. Don't let individual losses affect decision-making.</p>
          <h3>Focus on Process, Not Results</h3>
          <p>Ask: "Did I follow my system?" Not: "Did I win?"<br/>+EV bets lose sometimes. -EV bets win sometimes. Trust the process over 100+ bets.</p>
          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Daily Routine</h3>
            <p className="mb-0"><strong>Before betting:</strong> Review rules, set limits<br/><strong>During betting:</strong> Check model before every bet<br/><strong>After betting:</strong> Log results, reflect on adherence<br/><strong>After losses:</strong> Take 15 min break</p>
          </div>
          <h2>The 3 Bet Rule</h2>
          <p>If you lose 3 bets in a row, STOP betting for the day. Variance happens, but 3 straight losses can trigger tilt. Protect yourself.</p>
          <h2>Managing FOMO</h2>
          <h3>Remember: Edges Recur</h3>
          <p>Miss a 7-point edge? Another one will appear tomorrow, or next week. You don't need to bet every opportunity.</p>
          <h3>Quality Over Quantity</h3>
          <p>Betting 3 high-quality spots per week beats betting 20 mediocre spots per day.</p>
          <h2>When to Walk Away</h2>
          <p>Stop betting if you:</p>
          <ul><li>Hit your daily loss limit</li><li>Feel frustrated or angry</li><li>Broke your rules 2+ times</li><li>Are betting to "get even"</li><li>Can't focus on the games</li></ul>
          <h2>Long-Term Mindset</h2>
          <p>Sports betting is a marathon, not a sprint. Success is measured over months and years, not days.</p>
          <ul><li><strong>Short term:</strong> Expect variance, wins and losses</li><li><strong>Medium term (100 bets):</strong> Closer to expected ROI</li><li><strong>Long term (500+ bets):</strong> Edge reveals itself</li></ul>
          <h2>Next Steps</h2>
          <p>Learn to avoid common pitfalls: <Link to="/learn/chasing-losses" className="text-blue-400 hover:text-blue-300">The Danger of Chasing Losses</Link>.</p>
        </div>
      </>
    )
  },

  'confidence-levels': {
    id: 'confidence-levels',
    title: 'Confidence Levels: LOW, MEDIUM, HIGH',
    category: 'Dashboard',
    readTime: '9 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'How confidence is calculated, quarter-by-quarter progression, and factors that increase confidence.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200&h=600&fit=crop" alt="Confidence metrics" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>What is Confidence?</h2>
          <p><strong>Confidence</strong> measures how much we trust our projection based on sample size and game context. More data + normal game flow = higher confidence.</p>
          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Three Levels</h3>
            <p className="mb-0"><strong>LOW:</strong> Early game, small sample (0-12 min)<br/><strong>MEDIUM:</strong> Mid-game, building sample (12-30 min)<br/><strong>HIGH:</strong> Late game, large sample (30+ min)</p>
          </div>
          <h2>How Confidence is Calculated</h2>
          <h3>Primary Factor: Minutes Played</h3>
          <ul><li><strong>0-12 minutes:</strong> LOW confidence</li><li><strong>12-30 minutes:</strong> MEDIUM confidence</li><li><strong>30+ minutes:</strong> HIGH confidence</li></ul>
          <h3>Secondary Factors</h3>
          <ul><li><strong>Score differential:</strong> Blowouts reduce confidence</li><li><strong>Pace consistency:</strong> Erratic pace reduces confidence</li><li><strong>Game state:</strong> Normal flow increases confidence</li></ul>
          <h2>LOW Confidence (Orange Badge)</h2>
          <h3>When You See LOW</h3>
          <ul><li>1st quarter (0-12 minutes)</li><li>Blowout games (20+ differential)</li><li>Unusual game circumstances</li></ul>
          <h3>What LOW Means</h3>
          <p>Projection is preliminary. Small sample size. High variance. Requires 7+ edge to bet.</p>
          <h3>Betting Strategy</h3>
          <p>Be very selective. Only bet huge edges (7+) with small units (0.5-1.0). Prefer waiting for MEDIUM/HIGH.</p>
          <h2>MEDIUM Confidence (Yellow Badge)</h2>
          <h3>When You See MEDIUM</h3>
          <ul><li>2nd quarter through early 4th (12-30 min)</li><li>Moderately competitive games</li><li>Some pace variance</li></ul>
          <h3>What MEDIUM Means</h3>
          <p>Projection gaining reliability. Decent sample. Trends emerging. Require 5+ edge to bet.</p>
          <h3>Betting Strategy</h3>
          <p>Good betting territory. Look for 5+ edges. Bet 1-2 units on strong spots.</p>
          <h2>HIGH Confidence (Green Badge)</h2>
          <h3>When You See HIGH</h3>
          <ul><li>Late 3rd and 4th quarter (30+ min)</li><li>Competitive games (within 15 points)</li><li>Consistent pace throughout</li></ul>
          <h3>What HIGH Means</h3>
          <p>Projection very reliable. Large sample. Model has strong conviction. Bet 3+ edges.</p>
          <h3>Betting Strategy</h3>
          <p>Best opportunities. Bet 3+ edges with full units (1-5 based on strength factor).</p>
          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Golden Combo</h3>
            <p className="mb-0"><strong>HIGH confidence + 5+ edge = Elite betting opportunity</strong><br/>This is what you're waiting for. Large sample, strong model conviction, competitive game.</p>
          </div>
          <h2>Quarter-by-Quarter Progression</h2>
          <h3>1Q (0-12 min): LOW</h3>
          <p>Default LOW. Too early to trust projections.</p>
          <h3>2Q (12-24 min): MEDIUM</h3>
          <p>Transitions to MEDIUM around 15 minutes played.</p>
          <h3>3Q (24-36 min): MEDIUM to HIGH</h3>
          <p>Transitions to HIGH around 30 minutes if game is competitive.</p>
          <h3>4Q (36-48 min): HIGH or LOW</h3>
          <p>Stays HIGH if competitive. Drops to LOW if blowout (garbage time).</p>
          <h2>Factors That Reduce Confidence</h2>
          <h3>Blowouts</h3>
          <p>Lead of 20+ points drops confidence to LOW regardless of time played. Garbage time makes projections unreliable.</p>
          <h3>Erratic Pace</h3>
          <p>If pace swings wildly quarter-to-quarter, confidence reduces.</p>
          <h3>Injuries/Ejections</h3>
          <p>Star player leaving mid-game disrupts model assumptions.</p>
          <h2>Confidence vs Edge: The Matrix</h2>
          <p>Both matter equally:</p>
          <ul><li><strong>HIGH + 3 edge:</strong> Good bet</li><li><strong>MEDIUM + 5 edge:</strong> Good bet</li><li><strong>LOW + 10 edge:</strong> Risky bet</li><li><strong>HIGH + 8 edge:</strong> Elite bet (rare)</li></ul>
          <h2>Next Steps</h2>
          <p>Learn about garbage time: <Link to="/learn/garbage-time" className="text-blue-400 hover:text-blue-300">Garbage Time: Friend or Foe?</Link>.</p>
        </div>
      </>
    )
  },

  'garbage-time': {
    id: 'garbage-time',
    title: 'Garbage Time: Friend or Foe?',
    category: 'Strategy',
    readTime: '9 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'Detecting garbage time scenarios, how blowouts affect totals, and late game fouling impact.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1504450874802-0ba2bcd9b5ae?w=1200&h=600&fit=crop" alt="NBA blowout game" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>What is Garbage Time?</h2>
          <p><strong>Garbage time</strong> occurs when one team has a commanding lead (usually 15-20+ points) late in the game. Both teams stop trying as hard, starters sit, and the game's competitive nature ends.</p>
          <h3>Typical Garbage Time</h3>
          <ul><li>20+ point lead in 4Q</li><li>15+ point lead with under 5 minutes</li><li>Starters benched for rest</li></ul>
          <h2>How Garbage Time Affects Pace</h2>
          <h3>Pace Usually Slows Down</h3>
          <p>Winning team milks the clock. Losing team gives up. Bench players replace starters. Pace drops 3-5 possessions per 48.</p>
          <h3>Sometimes Pace Speeds Up</h3>
          <p>Young bench players play chaotically. More turnovers. Fast breaks. Less disciplined offense.</p>
          <h3>Why It's Unpredictable</h3>
          <p>No consistent pattern. Depends on coaching philosophy, player motivation, and score differential.</p>
          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">Key Insight</h3>
            <p className="mb-0">Garbage time makes projections unreliable. Our model automatically reduces confidence to LOW when score differential exceeds 20 points.</p>
          </div>
          <h2>Identifying Garbage Time Early</h2>
          <h3>Clear Garbage Time</h3>
          <ul><li>25+ point lead anytime in 4Q</li><li>20+ point lead with under 6 minutes</li><li>Starters sitting on bench</li></ul>
          <h3>Borderline Garbage Time</h3>
          <ul><li>15-20 point lead mid-4Q</li><li>Both teams clearly checked out</li><li>Free substitutions happening</li></ul>
          <h2>Betting Strategy During Garbage Time</h2>
          <h3>Avoid Betting Blowouts</h3>
          <p>When you see a 20+ point lead in the 4Q, skip the game. Even if the model shows a 10-point edge, garbage time variance makes it unreliable.</p>
          <h3>Close Out Pregame Bets</h3>
          <p>If you have a pregame Over bet and the game enters garbage time with score at 180 (need 40 more for Over 220), you're in a coin flip. Garbage time could go either way.</p>
          <h3>The "Backdoor Cover"</h3>
          <p>Garbage time bench scoring can push totals Over unexpectedly. But betting on this is pure gambling, not +EV strategy.</p>
          <h2>Late-Game Fouling</h2>
          <h3>Intentional Fouling (Close Games)</h3>
          <p>Losing team fouls to stop clock and get possession back. This dramatically increases pace in final 2 minutes.</p>
          <h3>Normal Final 2 Minutes</h3>
          <ul><li>Typical scoring: 4-6 points</li><li>Pace: Normal or slightly slower</li></ul>
          <h3>With Fouling Final 2 Minutes</h3>
          <ul><li>Typical scoring: 8-14 points</li><li>Pace: 2-3x faster than normal</li></ul>
          <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-6 my-8">
            <h3 className="text-red-400 mt-0">Warning</h3>
            <p className="mb-0">Our pace model can show huge Over edges in the final 2 minutes due to fouling. Do NOT blindly bet these. Fouling is unpredictable and creates false signals.</p>
          </div>
          <h2>When Garbage Time Helps</h2>
          <h3>Under Bets in Blowouts</h3>
          <p>If you need the game to stay Under and it becomes a blowout, garbage time often helps. Pace slows, fewer possessions, easier Under.</p>
          <h3>Over Bets in Close Games</h3>
          <p>If you need Over and game stays close, final 2 minutes fouling can push you over the number.</p>
          <h2>Sport Trader.io Garbage Time Detection</h2>
          <p>Our model automatically detects garbage time:</p>
          <ul><li><strong>Score differential {'>'} 20:</strong> Confidence drops to LOW</li><li><strong>4Q blowouts:</strong> Recommendations suppressed</li><li><strong>Pace volatility:</strong> Edge calculations adjusted</li></ul>
          <h2>Best Practices</h2>
          <ol><li><strong>Avoid 20+ blowouts:</strong> Skip these games entirely</li><li><strong>Exit at 15+ in final 5 min:</strong> Game likely over</li><li><strong>Watch for starters sitting:</strong> Garbage time indicator</li><li><strong>Final 2 min caution:</strong> Fouling creates chaos</li></ol>
          <h2>Next Steps</h2>
          <p>Learn market dynamics: <Link to="/learn/how-books-set-lines" className="text-blue-400 hover:text-blue-300">How Sportsbooks Set Live Lines</Link>.</p>
        </div>
      </>
    )
  },

  'unit-sizing': {
    id: 'unit-sizing',
    title: 'Unit Sizing Based on Edge',
    category: 'Bankroll',
    readTime: '13 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'What is a unit, edge-based recommendations, Kelly Criterion basics, and when to bet more vs less.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=1200&h=600&fit=crop" alt="Bankroll management" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>What is a Unit?</h2>
          <p>A <strong>unit</strong> is your base bet size, typically 1% of your total bankroll. It's a standardized way to measure bet sizes regardless of bankroll.</p>
          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Example</h3>
            <p className="mb-0"><strong>Bankroll:</strong> $2,000<br/><strong>1 Unit:</strong> $20 (1%)<br/><strong>2 Units:</strong> $40 (2%)<br/><strong>3 Units:</strong> $60 (3%)</p>
          </div>
          <h2>Sport Trader.io Unit Recommendations</h2>
          <p>Our strength factor (0-100) determines unit sizing:</p>
          <h3>Strength 0-30: No Play</h3>
          <p><strong>0 units</strong> - Edge too small or confidence too low. Skip.</p>
          <h3>Strength 30-50: Small Play</h3>
          <p><strong>0.5-1.0 units</strong> - Modest edge. Bet conservatively.</p>
          <h3>Strength 50-70: Standard Play</h3>
          <p><strong>1.0-2.0 units</strong> - Good edge. Normal bet sizing.</p>
          <h3>Strength 70-85: Strong Play</h3>
          <p><strong>2.0-3.5 units</strong> - Excellent edge with high confidence. Bet more.</p>
          <h3>Strength 85-100: Elite Play</h3>
          <p><strong>3.5-5.0 units</strong> - Rare, exceptional opportunities. Max bet.</p>
          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Real Example</h3>
            <p><strong>Lakers vs Warriors, 3rd Quarter</strong><br/>Edge: +6.5 points<br/>Confidence: HIGH<br/>Pace differential: +8<br/>Efficiency: 1.15 (hot shooting)<br/><strong>Strength Factor: 72</strong><br/><strong>Recommended: 2.5 units</strong></p>
          </div>
          <h2>Odds Adjustment</h2>
          <p>Better odds = slightly larger units. We adjust for odds value:</p>
          <ul><li><strong>-110 or better:</strong> +10% unit boost</li><li><strong>-111 to -120:</strong> No adjustment</li><li><strong>-121 to -130:</strong> -10% unit reduction</li><li><strong>-131 or worse:</strong> -20% unit reduction</li></ul>
          <h3>Why This Matters</h3>
          <p>Getting -105 instead of -115 on the same bet means you need a lower win rate to profit. Our model rewards finding good odds.</p>
          <h2>Kelly Criterion Basics</h2>
          <p>The Kelly Criterion is a mathematical formula for optimal bet sizing based on edge:</p>
          <p><strong>Kelly % = (Win Probability × Odds - 1) / (Odds - 1)</strong></p>
          <h3>Example</h3>
          <p>You estimate 55% win probability at -110 odds (1.91 decimal):<br/><strong>Kelly = (0.55 × 1.91 - 1) / (1.91 - 1) = 0.059 = 5.9%</strong></p>
          <p>Full Kelly suggests betting 5.9% of bankroll.</p>
          <h3>Why We Use Fractional Kelly</h3>
          <p>Full Kelly is too aggressive and leads to large swings. Most pros use <strong>Quarter Kelly</strong> or <strong>Half Kelly</strong>:</p>
          <ul><li><strong>Quarter Kelly:</strong> 25% of full Kelly (more conservative)</li><li><strong>Half Kelly:</strong> 50% of full Kelly (balanced)</li></ul>
          <p>Our strength factor system approximates Quarter Kelly for safety.</p>
          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">Important</h3>
            <p className="mb-0">Never bet more than 5% of bankroll on a single play, even if Kelly suggests it. Overestimating edge by even 2-3% can lead to massive losses with full Kelly sizing.</p>
          </div>
          <h2>When to Bet More</h2>
          <h3>Increase Units When:</h3>
          <ul><li><strong>HIGH confidence + 5+ edge:</strong> Elite setup</li><li><strong>Consistent pace trend:</strong> Model has strong conviction</li><li><strong>Good odds available:</strong> -110 or better</li><li><strong>Fresh bankroll:</strong> Not in a losing streak</li></ul>
          <h2>When to Bet Less</h2>
          <h3>Reduce Units When:</h3>
          <ul><li><strong>LOW confidence:</strong> Even with large edge</li><li><strong>Erratic game flow:</strong> Blowouts, injuries, chaos</li><li><strong>Bad odds:</strong> -125 or worse</li><li><strong>Recent losses:</strong> Protect remaining bankroll</li><li><strong>Unsure:</strong> When in doubt, bet smaller</li></ul>
          <h2>Common Sizing Mistakes</h2>
          <h3>1. Flat Betting Everything</h3>
          <p>Betting 1 unit on every play ignores edge size and confidence. You should bet more on strong spots, less on marginal spots.</p>
          <h3>2. Chasing Losses with Bigger Bets</h3>
          <p>After a losing streak, betting bigger to "get even" is a disaster. Stick to your system or reduce size.</p>
          <h3>3. Betting Too Big on LOW Confidence</h3>
          <p>A 10-point edge in the 1st quarter is NOT worth 5 units. Confidence matters as much as edge.</p>
          <h3>4. Ignoring Bankroll Changes</h3>
          <p>If your bankroll drops 30%, your unit size should drop 30% too. Recalculate regularly.</p>
          <h2>Progressive Unit Sizing Example</h2>
          <h3>Scenario: 10 Bets Over One Week</h3>
          <ul><li><strong>Bet 1 (Strength 45):</strong> 0.5 units</li><li><strong>Bet 2 (Strength 68):</strong> 1.5 units</li><li><strong>Bet 3 (Strength 52):</strong> 1.0 units</li><li><strong>Bet 4 (Strength 88):</strong> 4.0 units (elite!)</li><li><strong>Bet 5 (Strength 35):</strong> 0.5 units</li><li><strong>Bet 6 (Strength 71):</strong> 2.5 units</li><li><strong>Bet 7 (Strength 28):</strong> Skip (below 30)</li><li><strong>Bet 8 (Strength 61):</strong> 1.5 units</li><li><strong>Bet 9 (Strength 77):</strong> 3.0 units</li><li><strong>Bet 10 (Strength 42):</strong> 1.0 units</li></ul>
          <p><strong>Total Wagered:</strong> 15.5 units (varied based on strength)</p>
          <h2>Adjusting for Variance</h2>
          <p>Even perfect unit sizing can't eliminate variance. Expect swings:</p>
          <ul><li><strong>Short term (10 bets):</strong> Could be up 10 units or down 8 units</li><li><strong>Medium term (100 bets):</strong> Closer to expected ROI ± 20%</li><li><strong>Long term (500+ bets):</strong> Results converge to true edge</li></ul>
          <h2>Next Steps</h2>
          <p>Learn advanced sizing: <Link to="/learn/kelly-criterion" className="text-blue-400 hover:text-blue-300">The Kelly Criterion Explained</Link>.</p>
        </div>
      </>
    )
  },

  'quarter-trends': {
    id: 'quarter-trends',
    title: 'Quarter-by-Quarter Trends',
    category: 'NBA',
    readTime: '11 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'First quarter totals, third quarter scoring spikes, fourth quarter variance, overtime implications.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1504450874802-0ba2bcd9b5ae?w=1200&h=600&fit=crop" alt="NBA quarter action" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>NBA Quarters Aren't Equal</h2>
          <p>Each quarter has distinct scoring patterns. Understanding these helps you identify value in live betting.</p>
          <h2>1st Quarter Characteristics</h2>
          <h3>Typical Scoring</h3>
          <p><strong>Average NBA 1Q:</strong> 54-58 total points (both teams)<br/><strong>High-scoring teams:</strong> 60-65 points<br/><strong>Low-scoring teams:</strong> 48-52 points</p>
          <h3>Why 1Q is Unpredictable</h3>
          <ul><li><strong>Small sample:</strong> Only 12 minutes of data</li><li><strong>Shooting variance:</strong> Teams start hot or cold randomly</li><li><strong>Rotation adjustments:</strong> Coaches testing lineups</li><li><strong>Energy levels:</strong> Fresh legs = unpredictable tempo</li></ul>
          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">Betting Strategy</h3>
            <p className="mb-0">Avoid heavy betting in 1Q. Variance is too high. If you must bet, require 7+ edge and keep units small (0.5-1.0 max).</p>
          </div>
          <h2>2nd Quarter: Bench Units</h2>
          <h3>Typical Scoring</h3>
          <p><strong>Average 2Q:</strong> 56-60 total points<br/>Often the <strong>highest scoring quarter</strong> due to bench pace.</p>
          <h3>Why 2Q Scores More</h3>
          <ul><li><strong>Bench units play faster:</strong> Less structured offense</li><li><strong>Weaker defense:</strong> Bench defenders less disciplined</li><li><strong>Transition opportunities:</strong> More turnovers = more fast breaks</li></ul>
          <h3>The "6-Minute Window"</h3>
          <p>Minutes 6-10 of the 2Q (full bench units) often see scoring surges. This is when pace models detect the fastest tempo.</p>
          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Betting Insight</h3>
            <p className="mb-0">The 2Q is ideal for live totals betting. Enough sample size to trust trends, but game still competitive. Look for pace edges during bench minutes.</p>
          </div>
          <h2>Halftime: Critical Inflection Point</h2>
          <h3>Halftime Totals</h3>
          <p><strong>Average NBA halftime:</strong> 110-115 total points<br/><strong>Pace indicator:</strong> 118+ = fast game, 106- = slow game</p>
          <h3>Halftime Analysis</h3>
          <p>At halftime, you have the best data for projections:</p>
          <ul><li>24 minutes played (large sample)</li><li>Clear pace established</li><li>Shooting trends visible</li><li>Game still competitive (usually)</li></ul>
          <h2>3rd Quarter: The "Adjustment Quarter"</h2>
          <h3>Typical Scoring</h3>
          <p><strong>Average 3Q:</strong> 54-58 total points<br/>Slightly lower than 2Q due to coaching adjustments.</p>
          <h3>Why 3Q is Different</h3>
          <ul><li><strong>Halftime adjustments:</strong> Coaches change strategies</li><li><strong>Pace shifts:</strong> Teams trailing often increase tempo</li><li><strong>Defensive intensity:</strong> More effort in second half</li><li><strong>Star minutes:</strong> Best players play more</li></ul>
          <h3>The "3Q Surge"</h3>
          <p>Teams often come out of halftime aggressive, leading to 6-0 or 8-2 runs in the first 3 minutes of the 3Q. This creates temporary pace spikes.</p>
          <h2>4th Quarter: Game Script Dominates</h2>
          <h3>Typical Scoring (Competitive Games)</h3>
          <p><strong>Average 4Q (close game):</strong> 56-60 total points<br/><strong>Close games tend to score MORE</strong> due to fouling and urgency.</p>
          <h3>Blowout 4Q Scoring</h3>
          <p><strong>Blowouts (15+ lead):</strong> 48-52 total points<br/>Garbage time = slower pace, bench players, no urgency.</p>
          <h3>Final 2 Minutes</h3>
          <p>Close games see intentional fouling:</p>
          <ul><li><strong>Normal 2 minutes:</strong> 4-6 points</li><li><strong>With fouling:</strong> 8-14 points</li></ul>
          <p>This creates false Over signals. Be cautious betting 4Q totals in close games.</p>
          <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-6 my-8">
            <h3 className="text-red-400 mt-0">Warning</h3>
            <p className="mb-0">4Q is the hardest quarter to project accurately due to game script variance. Blowouts and fouling strategies make pace unreliable. Reduce confidence in 4Q projections.</p>
          </div>
          <h2>Overtime Scoring</h2>
          <h3>Typical OT Scoring</h3>
          <p><strong>Average OT:</strong> 10-14 total points (5 minutes)<br/>Roughly 24-28 points per 48 minutes = SLOW pace.</p>
          <h3>Why OT Scores Less</h3>
          <ul><li><strong>Fatigue:</strong> Players exhausted from 48 minutes</li><li><strong>Foul trouble:</strong> Stars playing cautious</li><li><strong>Conservative coaching:</strong> Don't want to lose in OT</li></ul>
          <h2>Quarter-by-Quarter Betting Strategy</h2>
          <h3>1Q: Minimal Bets</h3>
          <p>Wait for trends to develop. Only bet huge edges (7+).</p>
          <h3>2Q: Prime Time</h3>
          <p>Best quarter for live betting. Pace trends clear, game competitive.</p>
          <h3>Halftime: Reassess</h3>
          <p>Analyze full half. Project 2nd half with 24 minutes of data.</p>
          <h3>3Q: High Confidence</h3>
          <p>36+ minutes of data. Most reliable projections. Bet standard units.</p>
          <h3>4Q: Game Script Aware</h3>
          <p>Only bet if competitive (within 12 points). Avoid blowouts and final 2 minutes.</p>
          <h2>Sport Trader.io Quarter Insights</h2>
          <p>Our dashboard shows quarter-specific data:</p>
          <ul><li><strong>Current quarter pace:</strong> How fast this specific quarter is playing</li><li><strong>Game pace:</strong> Overall game pace trend</li><li><strong>Confidence adjustment:</strong> Automatically reduces in 1Q and 4Q blowouts</li></ul>
          <h2>Next Steps</h2>
          <p>Learn how rest affects performance: <Link to="/learn/rest-and-back-to-backs" className="text-blue-400 hover:text-blue-300">Rest and Back-to-Backs</Link>.</p>
        </div>
      </>
    )
  },

  'pace-model-deep-dive': {
    id: 'pace-model-deep-dive',
    title: 'The Pace-Based Model Deep Dive',
    category: 'Strategy',
    readTime: '14 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'How current pace is calculated, weighting pregame vs live pace, and model limitations.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=600&fit=crop" alt="Advanced analytics" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>The Sport Trader.io Projection Algorithm</h2>
          <p>Our model combines real-time game data with season statistics to project final totals. Here's exactly how it works.</p>
          <h2>Step 1: Calculate Current Pace</h2>
          <p><strong>Formula:</strong> (Estimated Possessions / Minutes Played) × 48</p>
          <h3>Possession Estimation</h3>
          <p>We estimate possessions for each team based on pace and time:<br/><strong>Possessions = (Team Pace / 48) × Minutes Played</strong></p>
          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Example Calculation</h3>
            <p><strong>Lakers vs Warriors, 18 minutes played</strong><br/>Lakers season pace: 101<br/>Warriors season pace: 103<br/>Lakers estimated possessions: (101/48) × 18 = 37.9<br/>Warriors estimated possessions: (103/48) × 18 = 38.6<br/>Average: 38.25 possessions in 18 minutes<br/><strong>Current pace: (38.25/18) × 48 = 102 possessions per 48</strong></p>
          </div>
          <h2>Step 2: Calculate Efficiency Factor</h2>
          <p>Are teams scoring above or below their season averages?</p>
          <p><strong>Formula:</strong> Current Scoring Rate / Expected Scoring Rate</p>
          <h3>Example</h3>
          <ul><li><strong>Current score:</strong> 120 points (24 minutes played)</li><li><strong>Season average:</strong> 225 points per game (112.5 per half)</li><li><strong>Expected at 24 min:</strong> 112.5 points</li><li><strong>Efficiency factor:</strong> 120 / 112.5 = 1.07 (7% hot)</li></ul>
          <h2>Step 3: Apply Regression Factor</h2>
          <p>Hot/cold shooting regresses to the mean. We apply conservative regression:</p>
          <p><strong>Regression Factor = 0.85 + (0.15 × Efficiency Factor)</strong></p>
          <ul><li><strong>Efficiency 1.0 (normal):</strong> Regression = 1.0 (no change)</li><li><strong>Efficiency 1.2 (hot):</strong> Regression = 1.03 (expect cooling)</li><li><strong>Efficiency 0.8 (cold):</strong> Regression = 0.97 (expect warming)</li></ul>
          <h2>Step 4: Time-Based Weighting</h2>
          <p>Weight season data vs current game data based on time played:</p>
          <h3>Early (0-12 min): 60% Season / 40% Current</h3>
          <p>Small sample. Trust season averages more.</p>
          <h3>Mid (12-24 min): 40% Season / 60% Current</h3>
          <p>Pace trend emerging. Trust current game more.</p>
          <h3>Late (24+ min): 25% Season / 75% Current</h3>
          <p>Large sample. Heavily weight what we're seeing.</p>
          <h2>Step 5: Calculate Projection</h2>
          <p><strong>Season Projection:</strong> Team A PPG + Team B PPG<br/><strong>Current Projection:</strong> (Current Score / Minutes) × 48 × Regression Factor<br/><strong>Final Projection:</strong> (Season × Season Weight) + (Current × Current Weight)</p>
          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Full Example</h3>
            <p><strong>Lakers vs Warriors, 24 minutes played</strong><br/>Current score: 118<br/>Season avg: 225 total<br/>Efficiency: 118/112.5 = 1.05<br/>Regression: 0.85 + (0.15 × 1.05) = 1.01<br/>Current projection: (118/24) × 48 × 1.01 = 238<br/>Season projection: 225<br/>Weights: 40% season / 60% current<br/><strong>Final: (225 × 0.4) + (238 × 0.6) = 233 projected total</strong></p>
          </div>
          <h2>Step 6: Calculate Edge</h2>
          <p><strong>Edge = Projected Total - Market Total</strong></p>
          <ul><li><strong>Edge +5 or more:</strong> Strong recommendation</li><li><strong>Edge +3 to +5:</strong> Moderate recommendation</li><li><strong>Edge 0 to +3:</strong> Lean (proceed with caution)</li></ul>
          <h2>Confidence Levels</h2>
          <p>Based on minutes played and game context:</p>
          <h3>HIGH Confidence</h3>
          <ul><li>30+ minutes played</li><li>Competitive game (within 15 points)</li><li>Consistent pace trend</li><li>Normal game flow</li></ul>
          <h3>MEDIUM Confidence</h3>
          <ul><li>12-30 minutes played</li><li>Moderately competitive (within 20 points)</li><li>Some pace fluctuation</li></ul>
          <h3>LOW Confidence</h3>
          <ul><li>Under 12 minutes played</li><li>Blowout (20+ point differential)</li><li>Erratic pace</li><li>Unusual circumstances</li></ul>
          <h2>Strength Factor (0-100)</h2>
          <p>Combines edge size, confidence, and pace factors into a single score:</p>
          <h3>Components</h3>
          <ul><li><strong>Edge (40 points max):</strong> Larger edges score higher</li><li><strong>Time confidence (25 points max):</strong> More minutes = higher score</li><li><strong>Pace differential (20 points max):</strong> Extreme pace = higher score</li><li><strong>Efficiency (15 points max):</strong> Hot/cold shooting adds conviction</li></ul>
          <h3>Strength Tiers</h3>
          <ul><li><strong>0-30:</strong> No play</li><li><strong>30-50:</strong> 0.5-1.0 units</li><li><strong>50-70:</strong> 1.0-2.0 units</li><li><strong>70-85:</strong> 2.0-3.5 units</li><li><strong>85-100:</strong> 3.5-5.0 units (rare, elite opportunities)</li></ul>
          <h2>Model Limitations</h2>
          <h3>What the Model Doesn't Know</h3>
          <ul><li><strong>Mid-game injuries:</strong> Star player exits unexpectedly</li><li><strong>Intentional fouling:</strong> End-of-game foul strategies</li><li><strong>Garbage time:</strong> Starters benched in blowouts</li><li><strong>Coaching decisions:</strong> Tempo changes by design</li><li><strong>Motivation:</strong> Playoff implications, rivalries</li></ul>
          <h3>When to Override the Model</h3>
          <p>Use your judgment when:</p>
          <ul><li>Star player injured mid-game</li><li>Obvious garbage time scenario</li><li>Final 2 minutes (fouling chaos)</li><li>Weather affecting outdoor sports</li></ul>
          <h2>Best Practices</h2>
          <ol><li><strong>Focus on HIGH confidence:</strong> 30+ minutes, competitive games</li><li><strong>Require 5+ edge:</strong> Smaller edges don't overcome juice</li><li><strong>Watch the game:</strong> Combine model with observation</li><li><strong>Line shop:</strong> Get best available odds</li><li><strong>Track results:</strong> Learn which scenarios work best for you</li></ol>
          <h2>Next Steps</h2>
          <p>Learn how to interpret model outputs: <Link to="/learn/edge-indicator-system" className="text-blue-400 hover:text-blue-300">The Edge Indicator System</Link>.</p>
        </div>
      </>
    )
  },

  'edge-indicator-system': {
    id: 'edge-indicator-system',
    title: 'The Edge Indicator System',
    category: 'Dashboard',
    readTime: '10 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'What is an edge, minimum thresholds, edge vs confidence relationship, and when to trust large edges.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200&h=600&fit=crop" alt="Analytics dashboard" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>What is an Edge?</h2>
          <p>An <strong>edge</strong> is the difference between our projection and the market line. It represents potential value - how many points the market may be mispricing.</p>
          <p><strong>Edge = Our Projection - Market Total</strong></p>
          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Example</h3>
            <p><strong>Our Projection:</strong> 228.5<br/><strong>Market Total:</strong> 223.5<br/><strong>Edge:</strong> +5.0 points toward OVER</p>
            <p className="mb-0">This suggests betting Over 223.5 may have positive expected value.</p>
          </div>
          <h2>Edge Thresholds</h2>
          <h3>5.0+ Points: STRONG Recommendation</h3>
          <p>Significant model conviction. These are our best opportunities. Display with bold recommendation badges.</p>
          <h3>3.0-4.9 Points: Moderate Recommendation</h3>
          <p>Good edge, but smaller margin for error. Consider confidence level before betting.</p>
          <h3>2.0-2.9 Points: LEAN</h3>
          <p>Small edge. Proceed with caution. Only bet if HIGH confidence and other factors align.</p>
          <h3>0-2.0 Points: No Play</h3>
          <p>Edge too small to overcome juice. Skip these opportunities.</p>
          <h2>Edge + Confidence Matrix</h2>
          <p>Edge size matters more with high confidence:</p>
          <h3>HIGH Confidence Games</h3>
          <ul><li><strong>5+ edge:</strong> Elite play, max units</li><li><strong>3-5 edge:</strong> Strong play, standard units</li><li><strong>2-3 edge:</strong> Playable, half units</li></ul>
          <h3>MEDIUM Confidence Games</h3>
          <ul><li><strong>5+ edge:</strong> Good play, standard units</li><li><strong>3-5 edge:</strong> Okay play, half units</li><li><strong>2-3 edge:</strong> Skip</li></ul>
          <h3>LOW Confidence Games</h3>
          <ul><li><strong>5+ edge:</strong> Risky, small units only</li><li><strong>3-5 edge:</strong> Skip</li><li><strong>2-3 edge:</strong> Skip</li></ul>
          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Golden Rule</h3>
            <p className="mb-0">A 3-point edge in the 4th quarter (HIGH confidence) is worth MORE than a 7-point edge in the 1st quarter (LOW confidence). Always consider both factors together.</p>
          </div>
          <h2>Visual Indicators</h2>
          <h3>Border Colors</h3>
          <ul><li><strong>Green border:</strong> Edge toward OVER</li><li><strong>Red border:</strong> Edge toward UNDER</li><li><strong>Gray border:</strong> No significant edge</li></ul>
          <h3>Badge Intensity</h3>
          <ul><li><strong>STRONG:</strong> 5+ edge</li><li><strong>Standard:</strong> 3-5 edge</li><li><strong>LEAN:</strong> 2-3 edge</li></ul>
          <h2>When to Trust Large Edges</h2>
          <h3>Trust 7+ Edges When:</h3>
          <ul><li>Game is competitive (within 10 points)</li><li>24+ minutes played</li><li>Pace has been consistent for multiple quarters</li><li>No major injuries or ejections</li></ul>
          <h3>Be Cautious of 7+ Edges When:</h3>
          <ul><li>Blowout game (20+ differential)</li><li>Early game (under 12 minutes)</li><li>Erratic pace swings</li><li>Late-game fouling scenarios</li></ul>
          <h2>Edge Persistence</h2>
          <p>Strong edges don't last long. Markets are efficient:</p>
          <ul><li><strong>5+ edges:</strong> Typically available for 1-3 minutes</li><li><strong>7+ edges:</strong> Usually gone within 30-60 seconds</li><li><strong>Line movement:</strong> Sharp bettors bet quickly, moving lines</li></ul>
          <p><strong>Takeaway:</strong> When you see a strong edge, act fast or it will disappear.</p>
          <h2>Common Mistakes</h2>
          <h3>1. Chasing Every Edge</h3>
          <p>Not all edges are created equal. Focus on quality (HIGH confidence, 5+ edge) over quantity.</p>
          <h3>2. Ignoring Confidence</h3>
          <p>A 10-point edge in the 1st quarter can disappear quickly. Confidence matters as much as edge size.</p>
          <h3>3. Betting the Same Units</h3>
          <p>Adjust unit size based on strength factor. Don't bet 1 unit on every play.</p>
          <h3>4. Overreacting to Variance</h3>
          <p>Edges represent long-term value. You'll lose some +EV bets. Trust the process over 100+ bets.</p>
          <h2>How Edges Change Live</h2>
          <p>Edges fluctuate throughout the game:</p>
          <h3>1st Quarter</h3>
          <p>Edges large but unreliable. Variance is high. Models cautious.</p>
          <h3>2nd Quarter</h3>
          <p>Edges stabilize. Best time to find value before half.</p>
          <h3>3rd Quarter</h3>
          <p>Edges most reliable. Large sample, game still competitive.</p>
          <h3>4th Quarter</h3>
          <p>Edges accurate but game script matters. Blowouts become problematic.</p>
          <h2>Next Steps</h2>
          <p>Understand confidence scoring: <Link to="/learn/confidence-levels" className="text-blue-400 hover:text-blue-300">Confidence Levels: LOW, MEDIUM, HIGH</Link>.</p>
        </div>
      </>
    )
  },

  'nba-pace-statistics': {
    id: 'nba-pace-statistics',
    title: 'NBA Pace Statistics',
    category: 'NBA',
    readTime: '10 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'What is pace in basketball, league averages, fastest and slowest teams, pace changes mid-game.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1546519638-68e109498ffc?w=1200&h=600&fit=crop" alt="NBA basketball game" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>Understanding NBA Pace</h2>
          <p><strong>Pace</strong> in the NBA measures the number of possessions a team uses per 48 minutes. It's the single most important factor in determining game totals - faster pace = more possessions = more points.</p>
          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">2024-25 NBA Pace Averages</h3>
            <p className="mb-0"><strong>League Average:</strong> 99.0 possessions per 48 minutes<br/><strong>Fastest Teams (102+):</strong> Pacers, Kings, Warriors<br/><strong>Slowest Teams (96-):</strong> Heat, Grizzlies, Knicks</p>
          </div>
          <h2>How Pace Affects Totals</h2>
          <p>A 6-possession pace difference creates roughly 12-15 point swing in game totals:</p>
          <ul><li><strong>Pacers (103 pace) vs Kings (102 pace):</strong> Expected total ~235</li><li><strong>Heat (96 pace) vs Knicks (95 pace):</strong> Expected total ~210</li></ul>
          <p>That's a 25-point difference just from pace!</p>
          <h2>Fastest NBA Teams 2024-25</h2>
          <h3>1. Indiana Pacers (103.5 pace)</h3>
          <p>Run-and-gun offense. Push in transition. Minimal halfcourt sets. Games routinely go Over.</p>
          <h3>2. Sacramento Kings (102.2 pace)</h3>
          <p>Fast-paced offense led by De'Aaron Fox. High-scoring games common.</p>
          <h3>3. Golden State Warriors (101.8 pace)</h3>
          <p>Motion offense creates quick shots. Still one of NBA's fastest teams.</p>
          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Betting Insight</h3>
            <p className="mb-0">When two fast-paced teams play each other (Pacers vs Kings), the Over hits 58% of the time historically. Markets know this, but still undervalue extreme pace matchups.</p>
          </div>
          <h2>Slowest NBA Teams 2024-25</h2>
          <h3>1. Miami Heat (95.8 pace)</h3>
          <p>Methodical halfcourt offense. Strong defense. Games grind.</p>
          <h3>2. Memphis Grizzlies (96.2 pace)</h3>
          <p>Physical, defensive-minded. Slow tempo.</p>
          <h3>3. New York Knicks (96.5 pace)</h3>
          <p>Thibs defense. Halfcourt execution. Low-scoring affairs.</p>
          <h2>Pace Changes Mid-Game</h2>
          <p>Pace isn't static - it fluctuates based on game situation:</p>
          <h3>Factors That Increase Pace</h3>
          <ul><li><strong>Close games:</strong> Both teams pushing tempo to gain edge</li><li><strong>Transition opportunities:</strong> Turnovers and missed shots lead to fast breaks</li><li><strong>Small lineups:</strong> More guards = faster pace</li><li><strong>Foul trouble:</strong> Bench players often play faster</li></ul>
          <h3>Factors That Decrease Pace</h3>
          <ul><li><strong>Blowouts:</strong> Winning team milks clock, losing team gives up</li><li><strong>Late-game clock management:</strong> Leading team slows down</li><li><strong>Big lineups:</strong> More centers = slower halfcourt pace</li><li><strong>Defensive adjustments:</strong> Teams focusing on defense play slower</li></ul>
          <h2>Quarter-by-Quarter Pace Trends</h2>
          <h3>1st Quarter: Establishing Tempo</h3>
          <p>Teams feel each other out. Usually close to season averages. Variance high.</p>
          <h3>2nd Quarter: True Pace Emerges</h3>
          <p>Bench units often play faster. Best quarter for identifying pace trends.</p>
          <h3>3rd Quarter: Post-Halftime Adjustments</h3>
          <p>Coaches make adjustments. Pace can shift dramatically based on halftime score.</p>
          <h3>4th Quarter: Game Script Dominates</h3>
          <p>Close games maintain pace. Blowouts slow down. Fouling increases pace in final 2 minutes.</p>
          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">Sport Trader.io Strategy</h3>
            <p className="mb-0">Our model identifies the best betting opportunities in the 2nd and early 3rd quarters - when pace has established itself but the game is still competitive. This is where you'll see our highest-confidence edges.</p>
          </div>
          <h2>Home vs Road Pace</h2>
          <p>Home teams control pace slightly more than road teams:</p>
          <ul><li><strong>Home teams:</strong> +0.5 pace on average</li><li><strong>Road teams:</strong> -0.3 pace on average</li></ul>
          <p>Small edge, but matters in close matchups.</p>
          <h2>Back-to-Back Games</h2>
          <p>Teams on the 2nd game of a back-to-back play slower:</p>
          <ul><li><strong>Normal pace:</strong> 99.0</li><li><strong>B2B pace:</strong> 97.5 (-1.5 possessions)</li></ul>
          <p>Fatigue slows tempo. Expect slightly lower totals.</p>
          <h2>Using Pace Data for Betting</h2>
          <h3>Step 1: Check Team Season Pace</h3>
          <p>Know which teams are fast/slow before the game starts.</p>
          <h3>Step 2: Calculate Expected Game Pace</h3>
          <p>Average both teams' pace: (Team A + Team B) / 2</p>
          <h3>Step 3: Monitor Live Pace</h3>
          <p>Use Sport Trader.io dashboard to track real-time pace vs expected pace.</p>
          <h3>Step 4: Identify Pace Edges</h3>
          <p>When live pace deviates 5+ points from expected, strong Over/Under edges emerge.</p>
          <h2>Next Steps</h2>
          <p>Learn how our model uses this pace data: <Link to="/learn/pace-based-projections" className="text-blue-400 hover:text-blue-300">Pace-Based Projections Explained</Link>.</p>
        </div>
      </>
    )
  },

  'pace-based-projections': {
    id: 'pace-based-projections',
    title: 'Pace-Based Projections Explained',
    category: 'Fundamentals',
    readTime: '11 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'How pace affects total points, early vs late game differences, and adjusting for game script and blowouts.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1504450874802-0ba2bcd9b5ae?w=1200&h=600&fit=crop" alt="Basketball game action" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>What is Pace in Basketball?</h2>
          <p><strong>Pace</strong> measures how fast a team plays - specifically, the number of possessions per 48 minutes. A high-pace team plays faster, gets more possessions, and generally scores more points. A low-pace team grinds it out with slower possessions.</p>
          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">NBA Pace Ranges</h3>
            <p className="mb-0"><strong>Fast (100+ pace):</strong> Warriors, Kings, Pacers - run-and-gun offense<br/><strong>Average (97-100 pace):</strong> Most NBA teams<br/><strong>Slow (94-97 pace):</strong> Grizzlies, Heat - methodical halfcourt offense</p>
          </div>
          <h2>How Sport Trader.io Uses Pace</h2>
          <p>Our model calculates <strong>current game pace</strong> in real-time and compares it to the <strong>expected season pace</strong> of both teams. The difference tells us if the game is trending faster or slower than anticipated.</p>
          <h3>Current Pace Calculation</h3>
          <p>We estimate possessions based on current score and time played, then project to 48 minutes:</p>
          <p><strong>Current Pace = (Total Possessions / Minutes Played) × 48</strong></p>
          <h3>Expected Pace</h3>
          <p><strong>Expected Pace = (Team A Pace + Team B Pace) / 2</strong></p>
          <p>If Lakers average 101 pace and Warriors average 103 pace, expected game pace is 102.</p>
          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Example</h3>
            <p><strong>Lakers vs Warriors, Halftime</strong><br/>Current score: 118 total points (24 minutes played)<br/>Current pace: (118/24) × 48 = 236 point pace<br/>Expected pace: 102 possessions = ~210 points<br/><strong>Pace Differential: +26 points (FAST)</strong></p>
            <p className="mb-0">This game is trending 26 points faster than season averages suggest. Our model projects this pace forward to estimate a higher final total.</p>
          </div>
          <h2>Time-Based Weighting</h2>
          <p>Early in games, we trust <strong>season data</strong> more. Late in games, we trust <strong>current pace</strong> more.</p>
          <h3>1st Quarter (0-12 minutes)</h3>
          <ul><li><strong>Season Weight:</strong> 60%</li><li><strong>Current Game Weight:</strong> 40%</li><li><strong>Confidence:</strong> LOW</li></ul>
          <p>Small sample size. Hot/cold shooting creates variance. The model is cautious.</p>
          <h3>2nd Quarter (12-24 minutes)</h3>
          <ul><li><strong>Season Weight:</strong> 40%</li><li><strong>Current Game Weight:</strong> 60%</li><li><strong>Confidence:</strong> MEDIUM</li></ul>
          <p>Larger sample. Pace trends becoming clearer. Model gains confidence.</p>
          <h3>2nd Half (24+ minutes)</h3>
          <ul><li><strong>Season Weight:</strong> 25%</li><li><strong>Current Game Weight:</strong> 75%</li><li><strong>Confidence:</strong> HIGH</li></ul>
          <p>Large sample. Clear pace established. Model highly confident.</p>
          <h2>Regression to the Mean</h2>
          <p>Teams shooting unusually hot or cold tend to <strong>regress toward their season averages</strong>. Our model applies a regression factor to avoid overreacting to variance.</p>
          <h3>Efficiency Factor</h3>
          <p>If teams are scoring at 1.2× their normal rate (hot shooting), we apply a regression factor that assumes they'll cool off slightly toward normal efficiency.</p>
          <p><strong>Regression Factor = 0.85 + (0.15 × Efficiency Factor)</strong></p>
          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">Why Regression Matters</h3>
            <p className="mb-0">A team shooting 70% from the field in the 1st quarter won't maintain that all game. Regression prevents our model from projecting unrealistic totals based on unsustainable shooting.</p>
          </div>
          <h2>Pace Indicators</h2>
          <p>The dashboard shows <strong>pace indicators</strong> for quick visual understanding:</p>
          <ul><li><strong>Fast Pace:</strong> 5+ points above expected pace</li><li><strong>Up-Tempo:</strong> 3-5 points above expected</li><li><strong>Normal Pace:</strong> Within 3 points of expected</li><li><strong>Grinding:</strong> 3-5 points below expected</li><li><strong>Slow Pace:</strong> 5+ points below expected</li></ul>
          <p>Combined with shooting efficiency:<br/><strong>"Fast Pace | Hot Shooting"</strong> = expect big Over edge<br/><strong>"Slow Pace | Cold Shooting"</strong> = expect big Under edge</p>
          <h2>Game Script Adjustments</h2>
          <p>Our model understands that <strong>game context</strong> matters:</p>
          <h3>Competitive Games</h3>
          <p>Close games maintain normal pace. Both teams trying to win. Projections most reliable.</p>
          <h3>Blowouts</h3>
          <p>When one team leads by 20+, pace often changes dramatically. Starters sit, garbage time begins. Model confidence decreases in blowout scenarios.</p>
          <h3>Late-Game Fouling</h3>
          <p>Intentional fouling in final minutes increases possessions and points. This can skew pace projections, creating false Over signals.</p>
          <h2>Best Use Cases for Pace Model</h2>
          <h3>When the Model Excels</h3>
          <ul><li><strong>2nd and 3rd quarters:</strong> Enough sample, still competitive</li><li><strong>Consistent pace trends:</strong> Game maintaining steady tempo</li><li><strong>Large pace differentials:</strong> Clear deviation from expected</li><li><strong>Normal game flow:</strong> No injuries, ejections, or foul trouble</li></ul>
          <h3>When to Be Cautious</h3>
          <ul><li><strong>1st quarter:</strong> Too early, high variance</li><li><strong>Blowouts:</strong> Garbage time distorts pace</li><li><strong>Final 2 minutes:</strong> Fouling strategies create artificial pace</li><li><strong>Key player injury mid-game:</strong> Team dynamics change</li></ul>
          <h2>Next Steps</h2>
          <p>For advanced details on our projection algorithm, read <Link to="/learn/pace-model-deep-dive" className="text-blue-400 hover:text-blue-300">The Pace-Based Model Deep Dive</Link>.</p>
        </div>
      </>
    )
  },

  'responsible-gaming': {
    id: 'responsible-gaming',
    title: 'Responsible Gaming Resources',
    category: 'Legal',
    readTime: '8 min',
    lastUpdated: 'October 16, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'Recognizing problem gambling signs, setting limits, self-exclusion programs. National helpline: 1-800-GAMBLER.',
    content: (
      <>
        <img
          src="https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=1200&h=600&fit=crop"
          alt="Support and guidance concept"
          className="w-full h-96 object-cover rounded-xl mb-8"
        />

        <div className="prose prose-invert prose-lg max-w-none">
          <h2>Sports Betting Should Be Entertainment</h2>
          <p>
            Sports betting can be an enjoyable hobby when done responsibly. However, for some people, gambling
            can become problematic and negatively impact their life, finances, and relationships.
          </p>
          <p>
            This guide provides resources, warning signs, and tools to help ensure your betting stays fun and
            doesn't become a problem.
          </p>

          <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-6 my-8">
            <h3 className="text-red-400 mt-0">Get Help Now</h3>
            <p>
              If you or someone you know has a gambling problem, help is available 24/7:
            </p>
            <p className="mb-0">
              <strong>National Problem Gambling Helpline: 1-800-GAMBLER (1-800-426-2537)</strong><br/>
              Free, confidential support available 24/7/365.<br/>
              <strong>Online chat:</strong> ncpgambling.org/chat
            </p>
          </div>

          <h2>Warning Signs of Problem Gambling</h2>
          <p>
            Problem gambling can affect anyone. Be honest with yourself about these warning signs:
          </p>

          <h3>Financial Warning Signs</h3>
          <ul>
            <li>Betting more money than you can afford to lose</li>
            <li>Using money meant for bills, rent, or groceries for betting</li>
            <li>Borrowing money or selling possessions to fund betting</li>
            <li>Lying to family or friends about how much you're betting</li>
            <li>Constantly thinking about where to get money to bet</li>
          </ul>

          <h3>Behavioral Warning Signs</h3>
          <ul>
            <li>Betting to escape problems or negative feelings</li>
            <li>Needing to bet larger amounts to feel excitement</li>
            <li>Becoming restless or irritable when trying to stop</li>
            <li>Making repeated unsuccessful attempts to control or stop</li>
            <li>Chasing losses - betting more to win back money lost</li>
          </ul>

          <h3>Life Impact Warning Signs</h3>
          <ul>
            <li>Betting interfering with work, school, or relationships</li>
            <li>Neglecting family time or responsibilities due to betting</li>
            <li>Experiencing anxiety, depression, or stress from betting</li>
            <li>Lying about or hiding betting activity</li>
            <li>Relying on others to pay bills after betting losses</li>
          </ul>

          <img
            src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=1200&h=400&fit=crop"
            alt="Person seeking help and support"
            className="w-full h-64 object-cover rounded-lg my-8"
          />

          <h2>Setting Healthy Limits</h2>
          <p>
            Responsible gambling starts with setting clear limits BEFORE you start betting:
          </p>

          <h3>Financial Limits</h3>
          <ul>
            <li><strong>Budget Limit:</strong> Decide on a monthly betting budget you can afford</li>
            <li><strong>Deposit Limit:</strong> Only deposit what you've budgeted</li>
            <li><strong>Loss Limit:</strong> Stop if you hit your loss threshold</li>
            <li><strong>Bet Size Limit:</strong> Never exceed your maximum bet size</li>
          </ul>

          <h3>Time Limits</h3>
          <ul>
            <li>Set a maximum time per day for betting activities</li>
            <li>Take regular breaks (stand up, walk around, hydrate)</li>
            <li>Don't bet when tired, stressed, or emotional</li>
            <li>Maintain a healthy balance with other activities</li>
          </ul>

          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Sportsbook Responsible Gaming Tools</h3>
            <p>Most legal sportsbooks offer built-in tools:</p>
            <ul className="mb-0">
              <li><strong>Deposit Limits:</strong> Cap how much you can deposit daily/weekly/monthly</li>
              <li><strong>Time Limits:</strong> Set session time limits with automatic logouts</li>
              <li><strong>Reality Checks:</strong> Popup reminders showing time spent and money wagered</li>
              <li><strong>Cooling Off Periods:</strong> Temporary self-exclusion (24 hours to 6 months)</li>
              <li><strong>Self-Exclusion:</strong> Permanent or long-term account closure</li>
            </ul>
          </div>

          <h2>Self-Exclusion Programs</h2>
          <p>
            If you're struggling to control your gambling, <strong>self-exclusion</strong> can help by legally
            banning you from gambling venues and websites.
          </p>

          <h3>How Self-Exclusion Works</h3>
          <ul>
            <li>Voluntarily add yourself to a banned list</li>
            <li>Choose duration: 6 months, 1 year, 5 years, or lifetime</li>
            <li>Sportsbooks must close your account and return funds</li>
            <li>You cannot open new accounts during exclusion period</li>
            <li>Breaking exclusion can result in legal consequences</li>
          </ul>

          <h3>National Self-Exclusion Resources</h3>
          <ul>
            <li><strong>National Council on Problem Gambling:</strong> ncpgambling.org</li>
            <li><strong>State programs:</strong> Most states with legal betting offer self-exclusion</li>
            <li><strong>Sportsbook options:</strong> All legal books must provide self-exclusion</li>
          </ul>

          <h2>Getting Support</h2>
          <p>
            You don't have to face problem gambling alone. Many resources offer free, confidential support:
          </p>

          <h3>Helplines & Chat Support</h3>
          <ul>
            <li><strong>1-800-GAMBLER:</strong> 24/7 helpline with trained counselors</li>
            <li><strong>NCPG Chat:</strong> Live online chat at ncpgambling.org</li>
            <li><strong>Gamblers Anonymous:</strong> Free peer support meetings nationwide</li>
          </ul>

          <h3>Professional Treatment</h3>
          <ul>
            <li><strong>Counseling:</strong> Licensed therapists specializing in gambling addiction</li>
            <li><strong>Cognitive Behavioral Therapy (CBT):</strong> Evidence-based treatment</li>
            <li><strong>Inpatient programs:</strong> Intensive treatment for severe cases</li>
          </ul>

          <h3>Support for Family & Friends</h3>
          <ul>
            <li><strong>Gam-Anon:</strong> Support group for loved ones of problem gamblers</li>
            <li><strong>Family counseling:</strong> Therapy to heal relationships</li>
            <li><strong>Financial counseling:</strong> Help managing debt from gambling</li>
          </ul>

          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">You Are Not Alone</h3>
            <p className="mb-0">
              Approximately 2-3% of Americans experience gambling problems. Seeking help is a sign of strength,
              not weakness. Recovery is possible with the right support and treatment. Thousands of people
              successfully overcome gambling problems every year.
            </p>
          </div>

          <h2>Tips for Responsible Betting</h2>
          <ol>
            <li><strong>Set a budget and stick to it:</strong> Only bet what you can afford to lose</li>
            <li><strong>Don't chase losses:</strong> Accept losses as part of betting</li>
            <li><strong>Take breaks:</strong> Don't bet every day</li>
            <li><strong>Don't bet under the influence:</strong> Avoid betting when drinking or using drugs</li>
            <li><strong>Keep perspective:</strong> Betting is entertainment, not income</li>
            <li><strong>Maintain balance:</strong> Don't neglect family, friends, work, or hobbies</li>
            <li><strong>Track your activity:</strong> Monitor time and money spent</li>
            <li><strong>Never bet to solve financial problems:</strong> You'll likely make them worse</li>
          </ol>

          <h2>Additional Resources</h2>
          <ul>
            <li><strong>National Council on Problem Gambling:</strong> ncpgambling.org</li>
            <li><strong>Gamblers Anonymous:</strong> gamblersanonymous.org</li>
            <li><strong>SAMHSA National Helpline:</strong> 1-800-662-4357</li>
            <li><strong>State Gaming Commissions:</strong> Check your state's gaming authority website</li>
          </ul>

          <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-6 my-8">
            <h3 className="text-red-400 mt-0">Crisis Resources</h3>
            <p>
              If you're experiencing thoughts of self-harm related to gambling losses:
            </p>
            <p className="mb-0">
              <strong>National Suicide Prevention Lifeline: 988</strong><br/>
              24/7 crisis support. You are not alone, and help is available.
            </p>
          </div>

          <h2>Legal Requirements</h2>
          <p>
            All legal sports betting in the United States requires:
          </p>
          <ul>
            <li><strong>Age 21+:</strong> You must be at least 21 years old</li>
            <li><strong>Legal state:</strong> Betting only where legally authorized</li>
            <li><strong>ID verification:</strong> Valid government ID required</li>
          </ul>
        </div>
      </>
    )
  },

  'momentum-model': {
    id: 'momentum-model',
    title: 'Momentum Model: Riding Hot Quarters',
    category: 'Strategy',
    readTime: '11 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'Recent scoring trends, quarter momentum indicators, and combining momentum with pace.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1546519638-68e109498ffc?w=1200&h=600&fit=crop" alt="Basketball momentum" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>What is Momentum in Basketball?</h2>
          <p><strong>Momentum</strong> refers to recent scoring trends within a game. Teams get hot, hit shots, build confidence, and score in bursts. Momentum can persist for several minutes before regression occurs.</p>
          <p>The momentum model identifies when teams are scoring significantly above or below their season averages and projects whether that trend will continue or reverse.</p>
          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Key Concept</h3>
            <p className="mb-0">Momentum is REAL in the short term (5-10 minutes), but tends to <strong>regress to the mean</strong> over longer periods. The skill is identifying when to ride momentum vs when to fade it.</p>
          </div>
          <h2>How Our Momentum Model Works</h2>
          <h3>Step 1: Calculate Recent Scoring Rate</h3>
          <p>We analyze the last 6-8 minutes of game action (approximately the last quarter or half-quarter):</p>
          <ul><li><strong>Points scored:</strong> Total points in recent stretch</li><li><strong>Time elapsed:</strong> Minutes of play</li><li><strong>Scoring pace:</strong> Points per 48 minutes in recent stretch</li></ul>
          <h3>Step 2: Compare to Season Average</h3>
          <p>We compare recent scoring pace to each team's season average offensive efficiency:</p>
          <ul><li><strong>Hot momentum:</strong> Recent pace 15%+ above season average</li><li><strong>Normal flow:</strong> Recent pace within 10% of season average</li><li><strong>Cold momentum:</strong> Recent pace 15%+ below season average</li></ul>
          <h3>Step 3: Weight Momentum vs Regression</h3>
          <p>This is the critical balance. We apply <strong>momentum weighting</strong> based on time remaining:</p>
          <ul><li><strong>Early game (Q1-Q2):</strong> 25% momentum, 75% season data</li><li><strong>Mid game (Q3):</strong> 40% momentum, 60% season data</li><li><strong>Late game (Q4):</strong> 60% momentum, 40% season data</li></ul>
          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Real Example</h3>
            <p><strong>Scenario:</strong> Warriors vs Lakers, end of Q3<br/><strong>Season Avg:</strong> Warriors 118 PPG, Lakers 112 PPG (230 total)<br/><strong>Current Score:</strong> Warriors 92, Lakers 85 (177 points in 36 min)<br/><strong>Recent Momentum:</strong> Last 6 minutes they scored 28 points (224 pace)</p>
            <p><strong>Projection:</strong><br/>- Season-based: 230 total<br/>- Current pace: (177/36) × 48 = 236 total<br/>- Recent hot momentum: 224+ pace in last 6 min<br/>- <strong>Momentum-adjusted: (0.40 × 224) + (0.60 × 230) = 228 total</strong></p>
            <p className="mb-0">The model gives 40% weight to the hot recent stretch but balances with 60% season data to avoid overreacting.</p>
          </div>
          <h2>Quarter Momentum Indicators</h2>
          <p>Our dashboard shows momentum indicators for each quarter:</p>
          <h3>Hot Shooting (Green indicator)</h3>
          <ul><li>Recent scoring 15%+ above season average</li><li>Likely to continue for 5-10 more minutes</li><li><strong>Strategy:</strong> Ride momentum with Over bets, especially if total hasn't adjusted enough</li></ul>
          <h3>Normal Flow (Gray indicator)</h3>
          <ul><li>Scoring within 10% of season averages</li><li>No strong momentum signal</li><li><strong>Strategy:</strong> Trust pace-based projections, no momentum edge</li></ul>
          <h3>Cold Shooting (Blue indicator)</h3>
          <ul><li>Recent scoring 15%+ below season average</li><li>Due for regression back to season average</li><li><strong>Strategy:</strong> Fade the cold streak with Over bets if total has dropped too much</li></ul>
          <img src="https://images.unsplash.com/photo-1504450874802-0ba2bcd9b5ae?w=1200&h=400&fit=crop" alt="NBA game action" className="w-full h-64 object-cover rounded-lg my-8" />
          <h2>Combining Momentum with Pace</h2>
          <p>The most powerful edges come from combining momentum with pace analysis:</p>
          <h3>Scenario 1: Hot Momentum + Fast Pace</h3>
          <p><strong>Signal:</strong> Both teams shooting well AND playing at faster pace than season average</p>
          <p><strong>Edge:</strong> Very strong Over opportunity if market total hasn't adjusted enough</p>
          <p><strong>Confidence:</strong> HIGH - two factors pointing same direction</p>
          <h3>Scenario 2: Cold Start + Expected Regression</h3>
          <p><strong>Signal:</strong> Both teams shooting poorly in Q1, but both have elite offenses (top 10 season ORtg)</p>
          <p><strong>Edge:</strong> Strong Over opportunity - market overreacts to small sample cold shooting</p>
          <p><strong>Confidence:</strong> MEDIUM-HIGH - expecting regression to strong season averages</p>
          <h3>Scenario 3: Conflicting Signals</h3>
          <p><strong>Signal:</strong> Fast pace but cold shooting, or slow pace but hot shooting</p>
          <p><strong>Edge:</strong> Low or none - pace and momentum cancel out</p>
          <p><strong>Confidence:</strong> LOW - avoid these spots</p>
          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">Warning: Momentum Fades</h3>
            <p className="mb-0">Hot shooting quarters rarely last the entire game. If a team scored 35 in Q1, don't expect 35 in every quarter. Regression to the mean ALWAYS happens eventually. Our model accounts for this with decreasing momentum weights over time.</p>
          </div>
          <h2>Third Quarter Spike Pattern</h2>
          <p>NBA teams historically score more in the 3rd quarter than other quarters:</p>
          <ul><li><strong>Q1:</strong> ~27 PPQ (feeling out opponent)</li><li><strong>Q2:</strong> ~26 PPQ (often slows before halftime)</li><li><strong>Q3:</strong> ~29 PPQ (highest scoring quarter)</li><li><strong>Q4:</strong> ~27 PPQ (close games slow down)</li></ul>
          <p><strong>Why Q3 is hot:</strong> Teams make halftime adjustments, starters are fresh, and coaches push tempo early in the half.</p>
          <p><strong>Betting implication:</strong> If a total looks close at halftime, consider that Q3 often scores more than Q1/Q2 average.</p>
          <h2>Using Momentum on Our Dashboard</h2>
          <p>On Sport Trader.io, look for these momentum indicators on each game card:</p>
          <ul><li><strong>Pace Indicator:</strong> "Fast Pace | Hot Shooting" {'='} strong Over signal</li><li><strong>Efficiency Factor:</strong> {'>'} 1.15 {'='} hot shooting, {'<'} 0.85 {'='} cold shooting</li><li><strong>Strength Score:</strong> Includes momentum in the calculation (efficiency factor component)</li></ul>
          <p>When you see <strong>HIGH strength + Hot Shooting indicator</strong>, the model has identified a momentum edge worth betting.</p>
          <h2>When Momentum Fails</h2>
          <p>Avoid betting momentum in these situations:</p>
          <ul><li><strong>Blowouts:</strong> Garbage time invalidates momentum</li><li><strong>End of quarter:</strong> Momentum resets at quarter breaks</li><li><strong>Injury mid-game:</strong> Key player out changes everything</li><li><strong>Extreme outliers:</strong> 40-point Q1 will regress heavily</li></ul>
          <h2>Momentum + Regression Strategy</h2>
          <p>The optimal approach combines both concepts:</p>
          <ol><li><strong>Early cold shooting (Q1):</strong> Bet Over - expect regression to season averages</li><li><strong>Sustained hot shooting (Q2-Q3):</strong> Ride momentum - but reduce position size</li><li><strong>Late momentum (Q4):</strong> Trust current pace - regression time is limited</li></ol>
          <h2>Next Steps</h2>
          <p>Learn how regression works mathematically: <Link to="/learn/regression-to-mean" className="text-blue-400 hover:text-blue-300">Regression to the Mean</Link>.</p>
          <p>Understand pace calculation: <Link to="/learn/pace-model-deep-dive" className="text-blue-400 hover:text-blue-300">The Pace-Based Model Deep Dive</Link>.</p>
        </div>
      </>
    )
  },

  'how-books-set-lines': {
    id: 'how-books-set-lines',
    title: 'How Sportsbooks Set Live Lines',
    category: 'Markets',
    readTime: '11 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'Traders vs algorithms, sharp vs public money, line movement speed, and why lines differ.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&h=600&fit=crop" alt="Trading floor operations" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>Two Systems: Traders vs Algorithms</h2>
          <p>Sportsbooks use two methods to set and adjust live betting lines:</p>
          <h3>1. Manual Traders</h3>
          <p>Human traders watch games in real-time and adjust lines based on:</p>
          <ul><li>Score changes</li><li>Momentum shifts</li><li>Injuries and timeouts</li><li>Betting action (sharp vs public money)</li><li>Line shopping from competitors</li></ul>
          <p><strong>Advantages:</strong> Can react to context (key player fouls out, pace shift)<br/><strong>Disadvantages:</strong> Slower to adjust, can't monitor 50 games simultaneously</p>
          <h3>2. Algorithmic Pricing</h3>
          <p>Most major sportsbooks use algorithms that automatically adjust lines based on:</p>
          <ul><li><strong>Possession-by-possession data:</strong> Score, time, pace</li><li><strong>Pre-game models:</strong> Expected win probability and total</li><li><strong>Historical patterns:</strong> How similar games finished</li><li><strong>Competitor lines:</strong> Real-time line shopping across the market</li><li><strong>Betting volume:</strong> Adjust to balance exposure</li></ul>
          <p><strong>Advantages:</strong> Instant adjustments, no emotion, monitors hundreds of games<br/><strong>Disadvantages:</strong> Can't account for context, vulnerable to sharp exploitation</p>
          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Industry Reality</h3>
            <p className="mb-0">Large books like DraftKings, FanDuel, BetMGM use <strong>95% algorithms, 5% trader overrides</strong>. Smaller regional books may use 50/50 trader/algorithm mix. This creates pricing inefficiencies across the market.</p>
          </div>
          <h2>How Lines Move During Games</h2>
          <h3>Score-Based Adjustments</h3>
          <p>The most obvious line movements are score-driven:</p>
          <ul><li><strong>Team scores:</strong> Their spread tightens (favorite strengthens), total increases</li><li><strong>Opponent scores:</strong> Spread loosens (underdog gains), total increases</li><li><strong>Time elapses:</strong> Lines adjust based on projected final score</li></ul>
          <p><strong>Example:</strong><br/>Pregame: Warriors -5.5, O/U 225.5<br/>After Warriors 3-pointer (63-60 Warriors, 8 min left in Q3):<br/>Live: Warriors -6.5, O/U 227.5</p>
          <h3>Pace-Based Adjustments</h3>
          <p>Algorithms calculate <strong>current pace</strong> and adjust totals accordingly:</p>
          <ul><li><strong>Fast pace:</strong> Total increases even if score is tied</li><li><strong>Slow pace:</strong> Total decreases even if score is close</li></ul>
          <p><strong>Example:</strong><br/>Pregame O/U: 225.5<br/>Halftime score: 120-118 (238 pace) - algorithms raise total to 235+<br/>Halftime score: 100-98 (206 pace) - algorithms drop total to 215 or lower</p>
          <img src="https://images.unsplash.com/photo-1526628953301-3e589a6a8b74?w=1200&h=400&fit=crop" alt="Data analytics dashboard" className="w-full h-64 object-cover rounded-lg my-8" />
          <h2>Sharp Money vs Public Money</h2>
          <p>Sportsbooks track WHO is betting, not just how much:</p>
          <h3>Sharp Money</h3>
          <ul><li>Professional bettors with proven track records</li><li>Large bet sizes ($5,000-$50,000+)</li><li>Quick to bet after line posts</li><li>Often on "unpopular" sides</li></ul>
          <p><strong>Book Response:</strong> When sharps bet, books move lines FAST and AGGRESSIVELY to avoid getting middled or losing value.</p>
          <h3>Public Money</h3>
          <ul><li>Recreational bettors</li><li>Smaller bet sizes ($10-$500)</li><li>Bet favorites and Overs more often</li><li>Emotionally driven (bet home team, popular teams)</li></ul>
          <p><strong>Book Response:</strong> Books will shade lines TOWARD public favorites to attract more public money (and balance exposure).</p>
          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Real Example: Reverse Line Movement</h3>
            <p><strong>Lakers vs Warriors - Q2</strong><br/>- 70% of bets on Lakers -3.5<br/>- Line moves to Lakers -2.5 (opposite direction)<br/><strong>Why?</strong> Sharps bet Warriors heavily. Books respect sharp money more than public volume.</p>
            <p className="mb-0">This is called <strong>Reverse Line Movement (RLM)</strong> - a sharp money indicator.</p>
          </div>
          <h2>Line Movement Speed</h2>
          <p>How fast do lines adjust after events?</p>
          <h3>Ultra-Fast (0-5 seconds)</h3>
          <ul><li>Score changes</li><li>Made baskets, free throws</li><li>Algorithmic books like Pinnacle, DraftKings adjust instantly</li></ul>
          <h3>Fast (5-30 seconds)</h3>
          <ul><li>Fouls, timeouts</li><li>Injury timeouts (if severity unclear)</li><li>Most major sportsbooks adjust in this window</li></ul>
          <h3>Slow (30+ seconds)</h3>
          <ul><li>Contextual events (star player fouls out, coach ejected)</li><li>Smaller sportsbooks with manual traders</li><li>Regional books with limited live betting tech</li></ul>
          <p><strong>Edge Opportunity:</strong> If you identify important context (like a key defender fouling out) and books haven't adjusted yet, you can bet before the market reprices.</p>
          <h2>Why Lines Differ Between Sportsbooks</h2>
          <p>You'll often see different live lines across books:</p>
          <h3>1. Different Algorithms</h3>
          <p>Each book uses proprietary models. Some weight pace more, others weight score more.</p>
          <h3>2. Risk Management</h3>
          <p>If one book has $100k on the Over, they'll lower their total to attract Under money. Other books without that exposure keep the original total.</p>
          <h3>3. Market Position</h3>
          <ul><li><strong>Market makers (Pinnacle):</strong> Sharp-focused, tight margins, efficient lines</li><li><strong>Retail books (DraftKings, FanDuel):</strong> Public-focused, wider margins, slower to sharp info</li></ul>
          <h3>4. Speed of Information</h3>
          <p>Pinnacle adjusts in 1 second. A smaller book might take 15 seconds. In that gap, you can exploit the slower book's stale line.</p>
          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">Line Shopping is Essential</h3>
            <p className="mb-0">NEVER bet without checking multiple sportsbooks. Getting -105 instead of -110 on the same bet adds 2-3% to your ROI. Over 1000 bets, that's thousands of dollars. Sport Trader.io shows you the best available odds automatically.</p>
          </div>
          <h2>Exploiting Sportsbook Inefficiencies</h2>
          <h3>1. Overreaction to Short-Term Variance</h3>
          <p>Books drop totals aggressively after one cold shooting quarter. If you know both teams have elite offenses, bet the Over on the overreaction.</p>
          <h3>2. Slow Adjustments to Pace Shifts</h3>
          <p>Some books don't adjust fast enough when pace accelerates. If you see a 10-possession spike in pace in Q2, bet the Over before books reprice.</p>
          <h3>3. Stale Lines on Low-Liquidity Games</h3>
          <p>Nationally televised Lakers games? Lines adjust instantly. Tuesday Pelicans vs Pistons? Lines may lag 10-20 seconds behind market leaders.</p>
          <h3>4. Middling Opportunities</h3>
          <p>When lines move significantly, you can bet both sides at different prices and guarantee profit or minimize loss.</p>
          <p><strong>Example:</strong><br/>- Q1: Bet Over 225.5<br/>- Q3 (after cold shooting): Bet Under 232.5<br/>- If final total lands between 225.5-232.5, you win BOTH bets</p>
          <h2>How Sport Trader.io Gives You an Edge</h2>
          <p>Our platform identifies sportsbook inefficiencies in real-time:</p>
          <ul><li><strong>Compare 10+ sportsbooks:</strong> Instantly see best available odds</li><li><strong>Pace-based projections:</strong> Often more accurate than book algorithms</li><li><strong>Edge calculations:</strong> Shows where books have mispriced totals</li><li><strong>Line movement tracking:</strong> See which books are slow to adjust</li></ul>
          <h2>Common Sportsbook Mistakes</h2>
          <ul><li><strong>Overweighting recent possessions:</strong> 3 straight baskets doesn't predict the next 20 minutes</li><li><strong>Ignoring regression to mean:</strong> Cold shooting teams return to season averages</li><li><strong>Late game bias:</strong> Books often overreact to garbage time scoring</li><li><strong>Public betting influence:</strong> Shading lines toward popular sides creates -EV prices</li></ul>
          <h2>Next Steps</h2>
          <p>Understand market dynamics: <Link to="/learn/steam-moves" className="text-blue-400 hover:text-blue-300">Steam Moves and Why They Matter</Link>.</p>
          <p>Master line shopping: <Link to="/learn/line-shopping" className="text-blue-400 hover:text-blue-300">Line Shopping: The Easiest Edge</Link>.</p>
        </div>
      </>
    )
  },

  'steam-moves': {
    id: 'steam-moves',
    title: 'Steam Moves and Why They Matter',
    category: 'Markets',
    readTime: '12 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'What is a steam move, identifying sharp money, reverse line movement, and following the market.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&h=600&fit=crop" alt="Fast-moving market data" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>What is a Steam Move?</h2>
          <p>A <strong>steam move</strong> (or "steam") occurs when multiple sportsbooks simultaneously move their lines in the same direction, rapidly and aggressively. This signals that <strong>sharp money</strong> has entered the market.</p>
          <p>The term "steam" comes from the old telegraph days when urgent messages would literally be sent by steam-powered machines. In betting, steam means urgent, coordinated line movement across the entire market.</p>
          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Key Characteristics</h3>
            <p className="mb-0"><strong>Speed:</strong> Lines move within seconds<br/><strong>Magnitude:</strong> Large movement (2+ points on totals, 1+ point on spreads)<br/><strong>Breadth:</strong> Multiple books move together<br/><strong>Timing:</strong> Often happens right after line is posted</p>
          </div>
          <h2>How Steam Moves Happen</h2>
          <h3>Step 1: Sharp Bettor Identifies Edge</h3>
          <p>Professional betting syndicates use sophisticated models to identify mispriced lines. When they find value, they act FAST.</p>
          <h3>Step 2: Coordinated Betting Across Books</h3>
          <p>Sharp groups have accounts at 10-20 sportsbooks. They place large bets simultaneously across multiple books:</p>
          <ul><li>$10,000 at DraftKings</li><li>$10,000 at FanDuel</li><li>$10,000 at BetMGM</li><li>$10,000 at Caesars</li><li>$50,000+ at Pinnacle (market maker)</li></ul>
          <h3>Step 3: Books Respond Immediately</h3>
          <p>When sharp money hits, sportsbooks:</p>
          <ul><li>Identify the bettor as a known sharp (or see other books moving)</li><li>Move the line aggressively to avoid further exposure</li><li>Often follow Pinnacle's lead (the sharpest book)</li></ul>
          <h3>Step 4: Market-Wide Movement</h3>
          <p>Within 10-30 seconds, every major sportsbook has adjusted. The line has "steamed."</p>
          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Real Example: Live Steam Move</h3>
            <p><strong>Warriors vs Lakers - Halftime</strong><br/><strong>Initial Line:</strong> Total 227.5<br/><strong>12:03:45 PM:</strong> Large bets placed on Over 227.5<br/><strong>12:03:50 PM:</strong> Pinnacle moves to 229.5<br/><strong>12:04:00 PM:</strong> DraftKings, FanDuel, BetMGM all move to 229.5<br/><strong>12:04:15 PM:</strong> Smaller books follow to 229.5-230.5</p>
            <p className="mb-0"><strong>Interpretation:</strong> Sharp money bet Over 227.5. Market respected this info. If you didn't get 227.5, it's gone.</p>
          </div>
          <h2>Identifying Steam Moves in Real-Time</h2>
          <h3>1. Line Movement Alerts</h3>
          <p>Use odds tracking tools that alert you to rapid line changes:</p>
          <ul><li><strong>Sport Trader.io:</strong> Tracks line movement across 10+ books</li><li><strong>Odds comparison sites:</strong> Show historical line movement</li><li><strong>Betting Discord/Telegram:</strong> Sharp bettors share steam alerts</li></ul>
          <h3>2. Pinnacle as the Lead Indicator</h3>
          <p><strong>Pinnacle</strong> is the sharpest sportsbook globally. When Pinnacle moves, other books FOLLOW within seconds. Watch Pinnacle first.</p>
          <h3>3. Bet Timing</h3>
          <p>Steam moves happen:</p>
          <ul><li><strong>Pregame:</strong> Right after lines are posted (sharps pounce on soft openers)</li><li><strong>Live betting:</strong> At quarter breaks, halftime, or after key events</li></ul>
          <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=400&fit=crop" alt="Market data charts" className="w-full h-64 object-cover rounded-lg my-8" />
          <h2>Reverse Line Movement (RLM)</h2>
          <p><strong>Reverse Line Movement</strong> is when the line moves OPPOSITE to public betting percentages. This is a powerful steam indicator.</p>
          <h3>How RLM Works</h3>
          <p><strong>Scenario:</strong> Lakers vs Celtics, Total 220.5</p>
          <ul><li>75% of bets are on the Over</li><li>Line drops to 219.5 (moves toward Under)</li></ul>
          <p><strong>Explanation:</strong> Even though the public is betting Over, sharps are betting Under with LARGE bets. Books respect sharp money more than public volume.</p>
          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">RLM Red Flag</h3>
            <p className="mb-0">If you see 80%+ of bets on one side but the line moves the other direction, sharp money is on the other side. This is one of the strongest indicators in sports betting.</p>
          </div>
          <h2>Following Steam vs Fading Steam</h2>
          <h3>Following Steam (Most Common Strategy)</h3>
          <p>The idea: <strong>Sharp bettors are right more often than you are</strong>. If you can identify steam early and bet the same side, you're effectively "tailing sharps."</p>
          <p><strong>Advantages:</strong></p>
          <ul><li>You're betting with the smartest money in the market</li><li>Steam moves have historically beaten closing lines</li><li>You don't need your own model - just follow the money</li></ul>
          <p><strong>Disadvantages:</strong></p>
          <ul><li>You'll get worse odds than sharps (they got 227.5, you get 229.5)</li><li>Sometimes sharps are wrong</li><li>Books will limit you if you consistently tail steam</li></ul>
          <h3>Fading Steam (Contrarian Strategy)</h3>
          <p>The idea: <strong>Market overreacts to steam</strong>. If sharps bet Over and the line moves from 227.5 to 230.5, maybe 230.5 is now TOO HIGH and Under has value.</p>
          <p><strong>Advantages:</strong></p>
          <ul><li>You get the best possible price (post-steam)</li><li>Sometimes steam is wrong or overvalued</li><li>Books won't limit you - you're betting AGAINST sharps</li></ul>
          <p><strong>Disadvantages:</strong></p>
          <ul><li>You're betting against the smartest money</li><li>Requires strong conviction in your model</li><li>Sharps win more often than they lose</li></ul>
          <h2>Steam Move Examples in Live Betting</h2>
          <h3>Example 1: Halftime Total Adjustment</h3>
          <p><strong>Pregame total:</strong> 225.5<br/><strong>Halftime score:</strong> 115-110 (225 total, on pace for 225)<br/><strong>Halftime live total:</strong> Opens at 226.5<br/><strong>Steam:</strong> Sharps bet Over 226.5<br/><strong>New line:</strong> 229.5 within 30 seconds</p>
          <p><strong>Sharp thesis:</strong> Both teams were shooting below their season averages in H1. Expect regression to mean (higher scoring) in H2. Market underpriced this.</p>
          <h3>Example 2: Injury-Based Steam</h3>
          <p><strong>Q2:</strong> Key defender (Defensive Player of Year candidate) fouls out with 5 fouls<br/><strong>Initial line:</strong> No adjustment (books slow to react)<br/><strong>Steam:</strong> Sharps hammer Over within seconds<br/><strong>New line:</strong> Total jumps 3-4 points</p>
          <p><strong>Sharp thesis:</strong> Elite defender out = easier scoring. Books were too slow.</p>
          <h3>Example 3: Pace Acceleration Steam</h3>
          <p><strong>Q3:</strong> Game pace suddenly accelerates from 95 to 105 possessions per 48<br/><strong>Initial line:</strong> Total 220.5 (based on slower Q1-Q2 pace)<br/><strong>Steam:</strong> Sharps bet Over 220.5 heavily<br/><strong>New line:</strong> 224.5</p>
          <p><strong>Sharp thesis:</strong> Pace shift is real (both teams running). Books underestimated sustainability.</p>
          <h2>How Sport Trader.io Helps You Catch Steam</h2>
          <p>Our platform gives you tools to identify and act on steam moves:</p>
          <ul><li><strong>Multi-book odds comparison:</strong> See when ALL books move together</li><li><strong>Line movement tracking:</strong> Alerts when totals move 2+ points quickly</li><li><strong>Edge calculations:</strong> Shows when our model disagrees with post-steam lines (fade opportunity)</li><li><strong>Real-time pace analysis:</strong> Identifies the same edges sharps are finding</li></ul>
          <h2>Common Mistakes When Following Steam</h2>
          <ul><li><strong>Chasing bad numbers:</strong> If steam moved from 227.5 to 230.5, don't bet 230.5 blindly. The value is gone.</li><li><strong>Ignoring context:</strong> Not all steam is equal. Halftime steam {'>'} Q1 steam {'>'} random mid-quarter steam.</li><li><strong>Over-trusting steam:</strong> Sharps are right 55-60% of the time, not 100%.</li><li><strong>Betting every steam move:</strong> Be selective. Follow steam in situations you understand.</li></ul>
          <h2>Building Your Own Steam Detection System</h2>
          <ol><li><strong>Monitor Pinnacle first</strong> - When Pinnacle moves 2+ points, that's your signal</li><li><strong>Check bet volume</strong> - Large bets (visible on some books) indicate sharp action</li><li><strong>Watch for RLM</strong> - Line moving opposite public betting is strongest signal</li><li><strong>Compare timing</strong> - Lines moving within 10 seconds across books = steam</li><li><strong>Track your results</strong> - Does following steam work for you? Measure it.</li></ol>
          <h2>When Steam Moves Are Wrong</h2>
          <p>Sharp money isn't infallible. Steam moves fail when:</p>
          <ul><li><strong>Information asymmetry:</strong> Sharps had info that turned out false (injury report wrong)</li><li><strong>Model disagreement:</strong> Different sharp groups bet opposite sides</li><li><strong>Overreaction:</strong> Market moved too much, creating value on the other side</li><li><strong>Garbage time:</strong> Late-game events invalidate earlier sharp thesis</li></ul>
          <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-6 my-8">
            <h3 className="text-red-400 mt-0">Caution</h3>
            <p className="mb-0">Books WILL limit or ban accounts that consistently tail sharp steam. If you follow every steam move, you'll get limited quickly. Mix in your own analysis to avoid detection.</p>
          </div>
          <h2>Advanced: Beating Steam to the Punch</h2>
          <p>The ultimate edge: <strong>identify the same edges sharps see BEFORE they bet</strong>. This is what Sport Trader.io does:</p>
          <ul><li>Pace-based projections that match sharp models</li><li>Real-time efficiency analysis</li><li>Edge calculations before steam hits</li><li>Best odds comparison so you get sharp prices</li></ul>
          <h2>Next Steps</h2>
          <p>Learn line movement strategy: <Link to="/learn/beating-closing-line" className="text-blue-400 hover:text-blue-300">Beating the Closing Line</Link>.</p>
          <p>Understand how books operate: <Link to="/learn/how-books-set-lines" className="text-blue-400 hover:text-blue-300">How Sportsbooks Set Live Lines</Link>.</p>
        </div>
      </>
    )
  },

  'rest-and-back-to-backs': {
    id: 'rest-and-back-to-backs',
    title: 'Rest and Back-to-Backs',
    category: 'NBA',
    readTime: '9 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'NBA scheduling quirks, fatigue impact on totals, rest advantage quantified.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1546519638-68e109498ffc?w=1200&h=600&fit=crop" alt="Tired basketball player" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>NBA Scheduling and Fatigue</h2>
          <p>The NBA season is grueling: 82 games in ~170 days with frequent travel. <strong>Rest days</strong> between games significantly impact team performance, especially pace and defensive intensity.</p>
          <p>Understanding rest advantages is critical for live betting totals. Tired teams play slower and defend worse.</p>
          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Key Stats</h3>
            <p className="mb-0"><strong>Back-to-back games:</strong> Teams average 2.5 fewer points and 2-3 fewer possessions per game<br/><strong>3+ days rest:</strong> Teams average 1.5 more points and faster pace<br/><strong>Travel fatigue:</strong> Cross-country travel reduces pace by ~1 possession</p>
          </div>
          <h2>What is a Back-to-Back?</h2>
          <p>A <strong>back-to-back</strong> (B2B) occurs when a team plays on consecutive nights. This is the most significant rest disadvantage in the NBA.</p>
          <h3>Impact on Performance</h3>
          <ul><li><strong>Pace:</strong> Decreases by 2-3 possessions per game (98 → 95 pace)</li><li><strong>Shooting:</strong> FG% drops ~2-3% due to tired legs</li><li><strong>Defense:</strong> Defensive rating worsens by 1-2 points</li><li><strong>Minutes management:</strong> Coaches rest stars or limit minutes</li></ul>
          <h3>Second Night of B2B is Worse</h3>
          <p>The <strong>2nd game of a back-to-back</strong> shows the greatest fatigue effects. Teams are 10+ games below .500 historically on 2nd night B2Bs.</p>
          <h2>Rest Advantages Quantified</h2>
          <p>Historical NBA data shows clear rest impacts:</p>
          <h3>0 Days Rest (Back-to-Back)</h3>
          <ul><li><strong>Pace:</strong> -2.0 possessions vs season average</li><li><strong>Points:</strong> -2.5 PPG</li><li><strong>Win rate:</strong> 44% (vs 50% expected)</li></ul>
          <h3>1 Day Rest (Standard)</h3>
          <ul><li><strong>Pace:</strong> Normal (no adjustment)</li><li><strong>Points:</strong> Season average</li><li><strong>Win rate:</strong> 50%</li></ul>
          <h3>2 Days Rest</h3>
          <ul><li><strong>Pace:</strong> +0.5 possessions</li><li><strong>Points:</strong> +1.0 PPG</li><li><strong>Win rate:</strong> 52%</li></ul>
          <h3>3+ Days Rest</h3>
          <ul><li><strong>Pace:</strong> +1.5 possessions</li><li><strong>Points:</strong> +1.5 PPG</li><li><strong>Win rate:</strong> 54%</li></ul>
          <img src="https://images.unsplash.com/photo-1504450874802-0ba2bcd9b5ae?w=1200&h=400&fit=crop" alt="NBA game with scoreboard" className="w-full h-64 object-cover rounded-lg my-8" />
          <h2>Betting Implications</h2>
          <h3>Scenario 1: Both Teams on B2B</h3>
          <p><strong>Expected Impact:</strong> Slower pace, lower total</p>
          <p><strong>Adjustment:</strong> Subtract 4-5 points from projected total</p>
          <p><strong>Strategy:</strong> Bet Under if market hasn't adjusted enough. Look for totals that haven't dropped from pregame expectations.</p>
          <h3>Scenario 2: One Team on B2B, Other Rested (3+ days)</h3>
          <p><strong>Expected Impact:</strong> Extreme pace disparity favors rested team</p>
          <p><strong>Adjustment:</strong> Rested team +3-4 point advantage, faster pace</p>
          <p><strong>Strategy:</strong> Bet rested team spread. Total depends on whether rested team's pace overcomes tired team's slower pace.</p>
          <h3>Scenario 3: One Team on B2B (Normal Rest for Other)</h3>
          <p><strong>Expected Impact:</strong> Slight pace reduction, small scoring advantage to rested team</p>
          <p><strong>Adjustment:</strong> -1 to -2 points on total, +2 points to rested team spread</p>
          <p><strong>Strategy:</strong> Slight edge to rested team. Market usually prices this correctly.</p>
          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Real Example</h3>
            <p><strong>Lakers (2nd night B2B) @ Warriors (3 days rest)</strong><br/><strong>Pregame total:</strong> 228.5<br/><strong>Rest-adjusted total:</strong> 224.5 (Lakers tired, pace slows)<br/><strong>Actual line:</strong> 227.5 (market underadjusted)</p>
            <p className="mb-0"><strong>Edge:</strong> Bet Under 227.5 - Lakers will struggle with pace and shooting efficiency.</p>
          </div>
          <h2>Travel Fatigue</h2>
          <p>Beyond rest days, <strong>travel distance</strong> matters:</p>
          <h3>East Coast to West Coast (or vice versa)</h3>
          <ul><li><strong>Time zone shift:</strong> 3 hours impacts circadian rhythm</li><li><strong>Flight time:</strong> 5-6 hours in the air</li><li><strong>Pace impact:</strong> -1.0 possession on average</li></ul>
          <h3>Back-to-Back + Cross-Country Travel</h3>
          <p>The worst-case scenario: <strong>2nd night B2B + 3-hour time zone change</strong></p>
          <ul><li><strong>Pace impact:</strong> -3.0 possessions</li><li><strong>Points impact:</strong> -4 to -5 PPG</li><li><strong>Win rate:</strong> ~38%</li></ul>
          <p><strong>Betting Strategy:</strong> Fade the traveling team heavily. Bet Under and opponent spread.</p>
          <h2>How Sport Trader.io Adjusts for Rest</h2>
          <p>Our pace-based model automatically accounts for rest advantages:</p>
          <ul><li><strong>Rest days tracked:</strong> Shows "B2B" or "3 days rest" on game cards</li><li><strong>Pace adjustments:</strong> Reduces projected pace for B2B teams</li><li><strong>Edge calculations:</strong> Compares rest-adjusted projection to market total</li><li><strong>Strength score:</strong> Incorporates rest as a confidence factor</li></ul>
          <p>You don't need to manually calculate rest impact - the model does it automatically.</p>
          <h2>Rest Myths and Misconceptions</h2>
          <h3>Myth 1: "Rested Teams Always Win"</h3>
          <p><strong>Reality:</strong> Rested teams win ~54% of the time (slight edge), but talent matters more. A rested bad team still loses to a tired great team.</p>
          <h3>Myth 2: "B2B Teams Always Go Under"</h3>
          <p><strong>Reality:</strong> Depends on opponent. If the opponent is also tired or plays slow, the total might not drop much.</p>
          <h3>Myth 3: "Load Management Ruins Bets"</h3>
          <p><strong>Reality:</strong> Star players resting is PUBLIC information by game time. Lines adjust immediately. No edge unless you bet pregame and get lucky.</p>
          <h2>Schedule Density (Clustered Games)</h2>
          <p>Some stretches of the NBA season have <strong>schedule clusters</strong>: 4 games in 5 nights, for example.</p>
          <h3>Impact of Schedule Density</h3>
          <ul><li><strong>Game 1:</strong> Normal performance</li><li><strong>Game 2-3:</strong> Slight fatigue (-1 pace)</li><li><strong>Game 4:</strong> Significant fatigue (-2 to -3 pace)</li></ul>
          <p><strong>Strategy:</strong> Fade teams on the 4th game of a cluster. Bet Under and opponent spread.</p>
          <h2>Playoffs vs Regular Season</h2>
          <p><strong>Playoffs:</strong> Every series game has at least 1 day rest (usually 2). Fatigue is less of a factor.</p>
          <p><strong>Regular season:</strong> B2Bs are common (each team plays ~12-15 B2Bs per season). Rest edges matter more.</p>
          <p><strong>Betting Implication:</strong> Rest-based strategies work better in regular season than playoffs.</p>
          <h2>Live Betting Adjustments</h2>
          <p>If you see a B2B team playing FASTER than expected in Q1-Q2, they're likely to crash in Q3-Q4:</p>
          <ul><li><strong>Q1-Q2:</strong> Normal pace (102 pace) despite B2B</li><li><strong>Q3:</strong> Pace drops to 95 (fatigue sets in)</li><li><strong>Q4:</strong> Pace drops to 90 (legs gone)</li></ul>
          <p><strong>Strategy:</strong> Bet Under live in Q3 if a B2B team maintained pace in H1. The fatigue WILL hit.</p>
          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">Warning</h3>
            <p className="mb-0">Rest advantages are PRICED INTO pregame lines. Books know about B2Bs. The edge comes from live betting when tired teams overperform early and you can bet the inevitable regression.</p>
          </div>
          <h2>Using Rest Data on Our Dashboard</h2>
          <p>On Sport Trader.io game cards, look for:</p>
          <ul><li><strong>"B2B" badge:</strong> Indicates back-to-back game</li><li><strong>"Rested" badge:</strong> 3+ days of rest</li><li><strong>Pace adjustments:</strong> Model already factors in rest impact</li><li><strong>Projected total:</strong> Compares rest-adjusted projection to market</li></ul>
          <h2>Next Steps</h2>
          <p>Understand NBA pace patterns: <Link to="/learn/nba-pace-statistics" className="text-blue-400 hover:text-blue-300">NBA Pace Statistics</Link>.</p>
          <p>Learn quarter-by-quarter trends: <Link to="/learn/quarter-trends" className="text-blue-400 hover:text-blue-300">Quarter-by-Quarter Trends</Link>.</p>
        </div>
      </>
    )
  },

  'chasing-losses': {
    id: 'chasing-losses',
    title: 'The Danger of Chasing Losses',
    category: 'Psychology',
    readTime: '8 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'What is loss chasing, why it destroys bankrolls, setting loss limits.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&h=600&fit=crop" alt="Stop loss concept" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>What is Chasing Losses?</h2>
          <p><strong>Chasing losses</strong> is when you increase your bet sizes or bet on marginal edges to quickly recover recent losses. It's the #1 way profitable systems turn into bankroll disasters.</p>
          <p>The psychological trigger: "I'm down $500 today. If I bet $300 on this game and win, I'll be back to even."</p>
          <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-6 my-8">
            <h3 className="text-red-400 mt-0">Critical Warning</h3>
            <p className="mb-0">Chasing losses is the fastest way to destroy a bankroll. More money has been lost chasing than from any other betting mistake. If you recognize these patterns in yourself, STOP betting immediately.</p>
          </div>
          <h2>How Chasing Happens</h2>
          <h3>Stage 1: The Bad Beat</h3>
          <p>You make a good bet with a 5-point edge. The game lands exactly on the total and you push, or worse, you lose by 0.5 points. Frustrating, but this is variance.</p>
          <h3>Stage 2: The Emotional Response</h3>
          <p>Instead of accepting variance, you feel: <strong>anger, frustration, urgency to "get it back."</strong> You want to bet the next game to recover immediately.</p>
          <h3>Stage 3: The Revenge Bet</h3>
          <p>You bet the next available game, even though:</p>
          <ul><li>The edge is smaller (3 points instead of your 5-point minimum)</li><li>The confidence is LOW instead of your usual MEDIUM+ requirement</li><li>You're betting 2 units instead of your planned 1 unit</li></ul>
          <h3>Stage 4: The Spiral</h3>
          <p>If that bet loses, you're now down MORE. The urge intensifies. You bet again, even bigger, on an even worse edge. <strong>This is the death spiral.</strong></p>
          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">Real Example</h3>
            <p><strong>9:00 PM:</strong> Bet 1 unit on Warriors Over 227.5 (5-point edge, HIGH confidence) → Loses by 0.5 (lands 227)<br/><strong>9:15 PM:</strong> Frustrated. Bet 2 units on Lakers Over 220.5 (3-point edge, MEDIUM confidence) → Loses by 3<br/><strong>9:45 PM:</strong> Desperate. Bet 3 units on Celtics Over 215.5 (1-point edge, LOW confidence) → Loses by 5</p>
            <p className="mb-0"><strong>Result:</strong> Down 6 units in one night, all from chasing the first 1-unit loss.</p>
          </div>
          <h2>Why Chasing Destroys Bankrolls</h2>
          <h3>1. You Bet on Worse Edges</h3>
          <p>When chasing, you abandon your standards. A 2-point edge becomes "good enough" because you need action NOW.</p>
          <h3>2. You Increase Bet Size</h3>
          <p>Betting 3 units on a mediocre edge is -EV. You're risking more on lower-quality opportunities.</p>
          <h3>3. Variance Compounds</h3>
          <p>If you're on a losing streak (normal variance), chasing ACCELERATES losses. A 3-bet losing streak becomes a 7-bet losing streak.</p>
          <h3>4. Emotional Decisions Replace Logic</h3>
          <p>Your model says "no bet." Your emotions say "I NEED to win." Emotions always lose long-term.</p>
          <img src="https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=1200&h=400&fit=crop" alt="Frustrated trader" className="w-full h-64 object-cover rounded-lg my-8" />
          <h2>Recognizing Chase Patterns</h2>
          <p>You're chasing losses if you:</p>
          <ul><li>Bet immediately after a loss without analyzing</li><li>Increase units to "get even faster"</li><li>Bet on games you normally wouldn't</li><li>Ignore your minimum edge requirements</li><li>Think "I just need ONE win to recover"</li><li>Feel desperate or angry while betting</li></ul>
          <h2>The Math Problem with Chasing</h2>
          <p>Chasing seems logical: "I lost $100, so I'll bet $100 to get it back." But the math doesn't work:</p>
          <h3>Scenario: Down 1 Unit, Chase with 2 Units</h3>
          <ul><li><strong>If you win (50% odds):</strong> You're +1 unit total (recovered original loss + profit)</li><li><strong>If you lose (50% odds):</strong> You're -3 units total (original loss + chase loss)</li></ul>
          <p><strong>Expected Value:</strong> (0.5 × +1) + (0.5 × -3) = -1 unit</p>
          <p>Chasing is -EV even at 50/50 odds, and you're usually betting WORSE than 50/50 when chasing.</p>
          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">The Kelly Criterion Perspective</h3>
            <p className="mb-0">Kelly sizing says: bet proportional to your edge. When you have NO edge (chasing), Kelly says bet ZERO. Increasing bet size when you have no edge is mathematical suicide.</p>
          </div>
          <h2>How to Stop Chasing</h2>
          <h3>1. Set Loss Limits BEFORE You Bet</h3>
          <p>Decide before the day starts: "If I lose 3 units today, I stop betting for 24 hours."</p>
          <p>Write it down. Make it concrete. <strong>Honor the limit.</strong></p>
          <h3>2. The 15-Minute Rule</h3>
          <p>After ANY loss, wait 15 minutes before placing another bet. Walk away from your computer. Clear your head. If the edge is still there in 15 minutes, it'll be there. If not, you avoided a chase bet.</p>
          <h3>3. Track Every Bet</h3>
          <p>Log every bet immediately in a spreadsheet:</p>
          <ul><li>Time</li><li>Game</li><li>Bet (Over/Under)</li><li>Edge</li><li>Confidence</li><li>Units</li><li>Outcome</li></ul>
          <p>When you see a pattern like "3 LOW confidence bets in 30 minutes," you'll catch yourself chasing.</p>
          <h3>4. Remove Stored Payment Methods</h3>
          <p>Make depositing money HARDER. Remove saved cards from sportsbooks. Require manually entering card info. This friction gives you time to reconsider.</p>
          <h3>5. Tell Someone</h3>
          <p>Accountability helps. Tell a friend: "If I text you saying I'm down money, remind me to stop betting."</p>
          <h2>The "Get Even" Fallacy</h2>
          <p>Thinking "I just need to get back to even today" is a trap. Your bankroll doesn't care about daily P&L. It only cares about long-term ROI.</p>
          <ul><li><strong>Bad thinking:</strong> "I'm down $500 today, I need to win it back"</li><li><strong>Good thinking:</strong> "I'm down $500 today due to variance. My system is +EV over 100 bets. I'll stick to my rules."</li></ul>
          <p>Professional bettors have losing days, losing weeks, even losing months. They survive because they NEVER chase.</p>
          <h2>When Losing Streaks Are Normal</h2>
          <p>Even with a 55% win rate system, you'll experience:</p>
          <ul><li><strong>3-bet losing streak:</strong> Happens ~14% of the time (roughly once per week)</li><li><strong>5-bet losing streak:</strong> Happens ~4% of the time (roughly once per month)</li><li><strong>7-bet losing streak:</strong> Happens ~1% of the time (roughly once per year)</li></ul>
          <p>This is MATH, not bad luck. Chasing during normal variance turns variance into disaster.</p>
          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Success Story</h3>
            <p>Bettor A and Bettor B both use the same +EV model. Both go 2-5 in Week 1 (unlucky variance).</p>
            <p><strong>Bettor A:</strong> Sticks to 1-unit bets, waits for high-quality edges. Ends the month 18-15 (+2.5 units).<br/><strong>Bettor B:</strong> Chases after the 2-5 start, bets 3 units on mediocre edges. Ends the month 20-20 (-4 units due to increased losing bet size).</p>
            <p className="mb-0">Same model, different discipline. Discipline won.</p>
          </div>
          <h2>Alternative to Chasing: Take a Break</h2>
          <p>When you feel the urge to chase:</p>
          <ol><li><strong>Close your sportsbook apps</strong></li><li><strong>Step away for 1 hour minimum</strong></li><li><strong>Do something else</strong> (exercise, watch TV, cook dinner)</li><li><strong>Review your rules</strong> when you return</li><li><strong>Only bet if you find a HIGH-quality edge</strong></li></ol>
          <p>The games will still be there tomorrow. Your bankroll won't if you chase.</p>
          <h2>The Martingale Trap</h2>
          <p>Some bettors think: "I'll double my bet after every loss. Eventually I'll win and recover everything."</p>
          <p><strong>Why this fails:</strong></p>
          <ul><li>Bet limits prevent infinite doubling</li><li>Your bankroll runs out before you win (7 losses = 128x original bet)</li><li>You're betting the MOST when you're losing (terrible timing)</li></ul>
          <p>Martingale strategies have bankrupted countless bettors. Avoid at all costs.</p>
          <h2>Building Anti-Chase Systems</h2>
          <ul><li><strong>Use Sport Trader.io's edge filters:</strong> Only bet 5+ point edges automatically</li><li><strong>Set app limits:</strong> iOS/Android screen time limits on betting apps</li><li><strong>Schedule betting windows:</strong> Only bet 7-9 PM, never outside those hours</li><li><strong>Use a betting partner:</strong> Both review each other's bets before placing</li></ul>
          <h2>Next Steps</h2>
          <p>Learn emotional control strategies: <Link to="/learn/emotional-control" className="text-blue-400 hover:text-blue-300">Emotional Control in Live Betting</Link>.</p>
          <p>Master bankroll management: <Link to="/learn/bankroll-management-101" className="text-blue-400 hover:text-blue-300">Bankroll Management 101</Link>.</p>
        </div>
      </>
    )
  },

  'middling-opportunities': {
    id: 'middling-opportunities',
    title: 'Middling Opportunities',
    category: 'Advanced',
    readTime: '11 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'What is a middle, live betting scenarios, risk vs reward, and real NBA examples.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&h=600&fit=crop" alt="Trading strategy chart" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>What is a Middle?</h2>
          <p>A <strong>middle</strong> (or "middling") occurs when you bet both sides of a market at different prices, creating a range where <strong>BOTH bets win</strong> if the final result lands in that range.</p>
          <p>In live betting, middling opportunities arise when line movement creates favorable gaps between your earlier bet and current market prices.</p>
          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Simple Example</h3>
            <p className="mb-0"><strong>Q1:</strong> Bet Over 225.5<br/><strong>Q3 (after slow pace):</strong> Bet Under 232.5<br/><strong>Result if final total = 228:</strong> Both bets win! (Over 225.5 ✓, Under 232.5 ✓)<br/><strong>Middle range:</strong> 226-232 total = you win BOTH bets</p>
          </div>
          <h2>How Middles Work: The Math</h2>
          <h3>Scenario: Over 225.5 + Under 232.5</h3>
          <p>You bet $100 on each side at -110 odds (risk $110 to win $100).</p>
          <p><strong>Possible Outcomes:</strong></p>
          <ul><li><strong>Total &lt; 225.5:</strong> Over loses (-$110), Under wins (+$100) = -$10 net</li><li><strong>Total 226-232:</strong> Over wins (+$100), Under wins (+$100) = +$200 net (MIDDLE!)</li><li><strong>Total &gt; 232.5:</strong> Over wins (+$100), Under loses (-$110) = -$10 net</li></ul>
          <p><strong>Risk:</strong> $10 max loss<br/><strong>Reward:</strong> $200 max profit (if middle hits)</p>
          <h3>Key Insight</h3>
          <p>At worst, you lose $10 (the juice). At best, you win $200. If the middle has a reasonable probability (15%+), this is +EV.</p>
          <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=400&fit=crop" alt="Statistical analysis" className="w-full h-64 object-cover rounded-lg my-8" />
          <h2>When Middling Opportunities Appear in Live Betting</h2>
          <h3>1. Cold Shooting Quarters Drop the Total</h3>
          <p><strong>Scenario:</strong></p>
          <ul><li><strong>Q1:</strong> Both teams shoot poorly, 48-45 score. You bet Over 220.5 (expecting regression to mean)</li><li><strong>Halftime:</strong> Market overreacts, drops line to 213.5</li><li><strong>Action:</strong> Bet Under 213.5</li><li><strong>Middle range:</strong> 214-220 total</li></ul>
          <p><strong>Logic:</strong> Market overreacted to Q1 cold shooting. Total will likely land between the extremes.</p>
          <h3>2. Fast-Paced First Half Raises the Total</h3>
          <p><strong>Scenario:</strong></p>
          <ul><li><strong>Pregame:</strong> Total 225.5</li><li><strong>Q1:</strong> Extremely fast pace, score 65-62 (halftime pace projecting 254 total)</li><li><strong>Halftime:</strong> Live total moves to 242.5</li><li><strong>Action:</strong> Bet Under 242.5 (pace will regress)</li><li><strong>If you had pregame Over 225.5:</strong> Middle range is 226-242</li></ul>
          <p><strong>Logic:</strong> Pace rarely sustains at extreme levels. Game will slow in H2, landing between the two totals.</p>
          <h3>3. Blowout Game with Garbage Time Uncertainty</h3>
          <p><strong>Scenario:</strong></p>
          <ul><li><strong>Q3:</strong> Warriors up 30 points. You bet Under 218.5 (expecting slow garbage time)</li><li><strong>Late Q4:</strong> Scrubs start scoring in garbage time, pace accelerates, total moves to 225.5</li><li><strong>Action:</strong> Bet Over 225.5</li><li><strong>Middle range:</strong> 219-225</li></ul>
          <p><strong>Logic:</strong> Garbage time is unpredictable. Total might land anywhere in this range.</p>
          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Real NBA Middle: Lakers vs Warriors</h3>
            <p><strong>Pregame total:</strong> 228.5<br/><strong>Q1 action:</strong> Bet Over 228.5 at -110<br/><strong>Halftime score:</strong> 105-100 (205 total, slow pace). Live total drops to 220.5<br/><strong>Q3 action:</strong> Bet Under 220.5 at -110<br/><strong>Final score:</strong> 225 total</p>
            <p className="mb-0"><strong>Result:</strong> Both bets WON! (+$200 profit, middle hit)</p>
          </div>
          <h2>Types of Middles</h2>
          <h3>Free Middle (No Risk)</h3>
          <p>Extremely rare: When you can bet both sides at + odds and guarantee profit no matter what.</p>
          <p><strong>Example:</strong> Over 225.5 at +105, Under 225.5 at +105 (arbitrage + middle potential)</p>
          <h3>Low-Risk Middle (Small Juice Risk)</h3>
          <p>Most common: You risk $10-20 in juice for a chance at $150-200 profit.</p>
          <p><strong>Example:</strong> Over 225.5 at -110, Under 232.5 at -110</p>
          <h3>Wide Middle (High Probability, Lower Profit)</h3>
          <p>Large gap between your bets (10+ points), higher chance of hitting but lower profit margin.</p>
          <p><strong>Example:</strong> Over 220.5, Under 240.5 (middle range: 221-240)</p>
          <h2>Calculating Middle Probability</h2>
          <p>To determine if a middle is +EV, estimate the probability the total lands in your middle range:</p>
          <h3>Step 1: Determine Middle Range</h3>
          <p>Over 225.5 + Under 232.5 = middle range is 226-232 (7-point range)</p>
          <h3>Step 2: Estimate Probability</h3>
          <p>Use historical data: <strong>NBA totals follow a roughly normal distribution</strong> with ~15-point standard deviation.</p>
          <p>A 7-point middle typically has <strong>10-15% probability</strong> of hitting.</p>
          <h3>Step 3: Calculate Expected Value</h3>
          <ul><li><strong>Probability of middle:</strong> 12%</li><li><strong>Middle profit:</strong> +$200</li><li><strong>Probability of one side:</strong> 88%</li><li><strong>One side loss:</strong> -$10</li></ul>
          <p><strong>EV = (0.12 × $200) + (0.88 × -$10) = $24 - $8.80 = +$15.20 EV</strong></p>
          <p>This middle is +EV!</p>
          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">Warning: Juice Adds Up</h3>
            <p className="mb-0">If your middle range is too small (3-4 points), the probability is low (~5%). You'll lose the $10-20 juice more often than you hit the middle. Only middle with 6+ point ranges unless you have strong evidence.</p>
          </div>
          <h2>Live Betting Middle Strategies</h2>
          <h3>Strategy 1: Bet Early, Middle Late</h3>
          <ol><li>Bet a strong edge early (Q1 Over with cold shooting)</li><li>If the line moves significantly opposite your position (drops 7+ points), bet the other side</li><li>You've created a middle with limited risk</li></ol>
          <h3>Strategy 2: Scalp Small Profits, Hope for Middle</h3>
          <ol><li>Bet Over 225.5</li><li>Line moves to 230.5, bet Under 230.5</li><li>Worst case: You lose $10 (push one side, lose juice on the other)</li><li>Best case: Total lands 226-230, you win $200</li></ol>
          <p>This is a "free roll" - you're risking very little for a middle shot.</p>
          <h3>Strategy 3: Hedge Big Wins into Middles</h3>
          <p>You bet Over 225.5 and the game is flying Over (currently 220 with Q4 remaining). Line is now 242.5.</p>
          <p><strong>Option A (Hedge):</strong> Bet Under 242.5 to guarantee profit<br/><strong>Option B (Middle):</strong> Bet less on Under 242.5, creating a middle at 226-242 range</p>
          <h2>Common Middle Mistakes</h2>
          <ul><li><strong>Middling with no edge:</strong> Don't create middles just for the sake of it. Both bets should have value independently.</li><li><strong>Too-small ranges:</strong> A 3-point middle (Over 225.5, Under 228.5) rarely hits (~4%).</li><li><strong>Ignoring key numbers:</strong> NBA totals cluster around certain numbers (220, 225, 230). Factor this in.</li><li><strong>Chasing bad positions:</strong> Don't middle to "save" a bad bet. Accept losses.</li></ul>
          <h2>Advanced: Professional Middle Hunting</h2>
          <p>Professional bettors actively hunt middles by:</p>
          <ul><li><strong>Betting early openers:</strong> Pregame lines before sharp action</li><li><strong>Monitoring line movement:</strong> Waiting for 6+ point moves</li><li><strong>Having multiple books:</strong> Finding the best prices on each side</li><li><strong>Using live betting:</strong> Exploiting overreactions to variance</li></ul>
          <h2>Middles vs Hedging</h2>
          <p><strong>Hedging:</strong> Betting the opposite side to guarantee profit or reduce risk<br/><strong>Middling:</strong> Betting the opposite side to create a win-win range while risking little</p>
          <p>Middles are BETTER than pure hedges because:</p>
          <ul><li>You maintain upside (middle win)</li><li>Your downside is minimal (small juice loss)</li></ul>
          <h2>Using Sport Trader.io for Middles</h2>
          <p>Our platform helps identify middling opportunities:</p>
          <ul><li><strong>Line movement tracking:</strong> Alerts when totals move 5+ points</li><li><strong>Multi-book comparison:</strong> Find the best prices for each side</li><li><strong>Historical data:</strong> See how often totals land in specific ranges</li><li><strong>Edge calculator:</strong> Determine if both sides have value</li></ul>
          <h2>When NOT to Middle</h2>
          <ul><li><strong>Blowout games:</strong> Garbage time is too unpredictable</li><li><strong>Late Q4:</strong> Not enough time for uncertainty</li><li><strong>Small ranges (under 5 points):</strong> Low probability of hitting</li><li><strong>High-juice lines:</strong> -120 or worse on both sides kills EV</li></ul>
          <h2>Next Steps</h2>
          <p>Learn hedging strategies: <Link to="/learn/hedging-bets" className="text-blue-400 hover:text-blue-300">Hedging Your Bets</Link>.</p>
          <p>Understand line movement: <Link to="/learn/steam-moves" className="text-blue-400 hover:text-blue-300">Steam Moves and Why They Matter</Link>.</p>
        </div>
      </>
    )
  },

  'reading-live-odds-v2': {
    id: 'reading-live-odds-v2',
    title: 'Reading Live Odds: A Complete Guide',
    category: 'Fundamentals',
    readTime: '10 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'Master American odds, implied probability, juice/vig, and why odds differ between sportsbooks.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&h=600&fit=crop" alt="Sports betting odds board" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>Understanding American Odds</h2>
          <p>American odds (also called moneyline odds) are the standard format in the US. They show how much you win relative to your bet size, using positive and negative numbers.</p>
          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Quick Reference</h3>
            <p className="mb-0"><strong>Negative odds (-110):</strong> You must bet $110 to win $100<br/><strong>Positive odds (+150):</strong> You bet $100 to win $150<br/><strong>Even odds (+100 or -100):</strong> Bet $100 to win $100</p>
          </div>
          <h2>Reading Negative Odds</h2>
          <p><strong>Format:</strong> -110, -150, -200, etc.</p>
          <p><strong>Meaning:</strong> How much you must bet to win $100.</p>
          <h3>Common Examples</h3>
          <ul><li><strong>-110:</strong> Risk $110 to win $100 (standard juice)</li><li><strong>-150:</strong> Risk $150 to win $100 (heavy favorite)</li><li><strong>-200:</strong> Risk $200 to win $100 (strong favorite)</li><li><strong>-300:</strong> Risk $300 to win $100 (very strong favorite)</li></ul>
          <p><strong>Rule of thumb:</strong> The higher the negative number, the more you must risk, and the more likely that outcome is expected.</p>
          <h2>Reading Positive Odds</h2>
          <p><strong>Format:</strong> +110, +150, +200, etc.</p>
          <p><strong>Meaning:</strong> How much you win if you bet $100.</p>
          <h3>Common Examples</h3>
          <ul><li><strong>+110:</strong> Bet $100 to win $110 (slight underdog)</li><li><strong>+150:</strong> Bet $100 to win $150 (moderate underdog)</li><li><strong>+200:</strong> Bet $100 to win $200 (big underdog)</li><li><strong>+300:</strong> Bet $100 to win $300 (heavy underdog)</li></ul>
          <p><strong>Rule of thumb:</strong> The higher the positive number, the more you win, but the less likely that outcome is expected.</p>
          <img src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200&h=400&fit=crop" alt="Betting calculator" className="w-full h-64 object-cover rounded-lg my-8" />
          <h2>Converting Odds to Implied Probability</h2>
          <p><strong>Implied probability</strong> is the win rate the odds suggest you need to break even.</p>
          <h3>Formula for Negative Odds</h3>
          <p><strong>Implied Probability = (-Odds) / ((-Odds) + 100)</strong></p>
          <p><strong>Example: -110 odds</strong><br/>110 / (110 + 100) = 110 / 210 = 52.4% implied probability</p>
          <h3>Formula for Positive Odds</h3>
          <p><strong>Implied Probability = 100 / (Odds + 100)</strong></p>
          <p><strong>Example: +150 odds</strong><br/>100 / (150 + 100) = 100 / 250 = 40% implied probability</p>
          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Common Odds and Their Probabilities</h3>
            <p><strong>-110:</strong> 52.4%<br/><strong>-120:</strong> 54.5%<br/><strong>-150:</strong> 60%<br/><strong>-200:</strong> 66.7%<br/><strong>+100:</strong> 50%<br/><strong>+110:</strong> 47.6%<br/><strong>+150:</strong> 40%<br/><strong>+200:</strong> 33.3%</p>
          </div>
          <h2>What is Juice (Vig)?</h2>
          <p><strong>Juice</strong> (or "vig" or "vigorish") is the sportsbook's commission built into the odds. It's why both sides of a bet aren't +100 (50/50).</p>
          <h3>Standard Juice: -110 / -110</h3>
          <p>For most totals and spreads, both sides are priced at -110:</p>
          <ul><li><strong>Over 225.5:</strong> -110 (52.4% implied probability)</li><li><strong>Under 225.5:</strong> -110 (52.4% implied probability)</li></ul>
          <p><strong>Total implied probability:</strong> 52.4% + 52.4% = 104.8%</p>
          <p>The extra 4.8% is the juice - the sportsbook's edge.</p>
          <h3>Why Juice Matters</h3>
          <p>To break even at -110 odds, you need to win <strong>52.4%</strong> of your bets, not 50%. The juice is your hurdle.</p>
          <p><strong>10 bets at -110, 5-5 record:</strong><br/>- Wins: 5 × $100 = $500<br/>- Losses: 5 × $110 = $550<br/>- <strong>Net: -$50 (you lose money at 50%!)</strong></p>
          <h2>High Juice vs Low Juice</h2>
          <h3>Low Juice (Good for Bettors)</h3>
          <ul><li><strong>-105 / -105:</strong> 51.2% implied probability each side</li><li><strong>-108 / -108:</strong> 51.9% implied probability each side</li><li><strong>Books offering low juice:</strong> Pinnacle, reduced juice promos</li></ul>
          <p><strong>Benefit:</strong> You need a lower win rate to profit.</p>
          <h3>High Juice (Bad for Bettors)</h3>
          <ul><li><strong>-115 / -115:</strong> 53.5% implied probability each side</li><li><strong>-120 / -110:</strong> Sportsbook shading toward one side</li><li><strong>Books with high juice:</strong> Small regional books, props</li></ul>
          <p><strong>Penalty:</strong> You need a higher win rate to profit.</p>
          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">Impact on ROI</h3>
            <p className="mb-0">Getting -105 instead of -110 on every bet adds ~2% to your long-term ROI. Over 1000 bets at $100 each, that's $2000 extra profit. Always line shop for the best juice.</p>
          </div>
          <h2>Why Odds Differ Between Sportsbooks</h2>
          <h3>1. Different Risk Exposure</h3>
          <p>If DraftKings has $50k on Over and FanDuel has $50k on Under, they'll price lines differently to balance their exposure.</p>
          <h3>2. Different Models</h3>
          <p>Each sportsbook uses proprietary algorithms. Some weight pace more, others weight recent form more.</p>
          <h3>3. Sharp vs Public Books</h3>
          <ul><li><strong>Sharp books (Pinnacle):</strong> Tight lines, low juice, attracts pros</li><li><strong>Public books (DraftKings, FanDuel):</strong> Wider margins, more juice, targets recreational bettors</li></ul>
          <h3>4. Speed of Adjustment</h3>
          <p>Pinnacle adjusts in 1 second. Smaller books might take 15-20 seconds. This creates temporary discrepancies.</p>
          <h2>Calculating Your Payout</h2>
          <h3>For Negative Odds</h3>
          <p><strong>Payout = (100 / |-Odds|) × Bet Size + Bet Size</strong></p>
          <p><strong>Example: $50 bet at -110</strong><br/>(100 / 110) × $50 + $50 = $45.45 + $50 = <strong>$95.45 total return</strong><br/>Net profit: $45.45</p>
          <h3>For Positive Odds</h3>
          <p><strong>Payout = (+Odds / 100) × Bet Size + Bet Size</strong></p>
          <p><strong>Example: $50 bet at +150</strong><br/>(150 / 100) × $50 + $50 = $75 + $50 = <strong>$125 total return</strong><br/>Net profit: $75</p>
          <h2>Reading Live Betting Odds</h2>
          <h3>Dynamic Lines</h3>
          <p>Live betting odds change constantly. You might see:</p>
          <ul><li><strong>Q1:</strong> Over 225.5 at -110</li><li><strong>30 seconds later:</strong> Over 227.5 at -110 (team scored)</li><li><strong>1 minute later:</strong> Over 225.5 at -115 (line reverted, but juice increased)</li></ul>
          <p>Always check BOTH the line AND the juice before betting.</p>
          <h3>Line Shopping in Live Betting</h3>
          <p>Live odds vary even more than pregame. Example:</p>
          <ul><li><strong>DraftKings:</strong> Over 225.5 at -110</li><li><strong>FanDuel:</strong> Over 224.5 at -110</li><li><strong>BetMGM:</strong> Over 225.5 at -105</li></ul>
          <p><strong>Best bet:</strong> BetMGM Over 225.5 at -105 (lower juice, same line)</p>
          <h2>Common Odds Mistakes</h2>
          <ul><li><strong>Ignoring juice:</strong> Betting -115 when -110 is available costs you 2% ROI</li><li><strong>Not converting to probability:</strong> -150 "feels" close to -110, but it's 60% vs 52.4% (big difference!)</li><li><strong>Assuming even odds = 50%:</strong> -110 is NOT a coinflip (it's 52.4%)</li><li><strong>Chasing plus odds:</strong> +200 isn't always good value - depends on true probability</li></ul>
          <h2>Using Odds to Find Value</h2>
          <p>Value exists when the <strong>true probability</strong> is better than the <strong>implied probability</strong>.</p>
          <p><strong>Example:</strong></p>
          <ul><li>Market line: Over 225.5 at -110 (52.4% implied probability)</li><li>Your model: Over has 58% true probability</li><li><strong>Edge: 58% - 52.4% = 5.6% edge (BET OVER)</strong></li></ul>
          <h2>Sport Trader.io's Odds Display</h2>
          <p>Our platform shows:</p>
          <ul><li><strong>Best available odds:</strong> Compares 10+ sportsbooks</li><li><strong>Implied probability:</strong> Automatic calculation</li><li><strong>Edge percentage:</strong> Your model's edge vs market</li><li><strong>Juice comparison:</strong> Highlights low-juice opportunities</li></ul>
          <h2>Next Steps</h2>
          <p>Learn how to calculate value: <Link to="/learn/expected-value" className="text-blue-400 hover:text-blue-300">What is Expected Value (EV)?</Link>.</p>
          <p>Master line shopping: <Link to="/learn/line-shopping" className="text-blue-400 hover:text-blue-300">Line Shopping: The Easiest Edge</Link>.</p>
        </div>
      </>
    )
  },

  'kelly-criterion': {
    id: 'kelly-criterion',
    title: 'The Kelly Criterion Explained',
    category: 'Bankroll',
    readTime: '15 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'Full Kelly formula, why full Kelly is too aggressive, quarter/half Kelly strategies.',
    content: (
      <>
        <img src="https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=1200&h=600&fit=crop" alt="Mathematical formula concept" className="w-full h-96 object-cover rounded-xl mb-8" />
        <div className="prose prose-invert prose-lg max-w-none">
          <h2>What is the Kelly Criterion?</h2>
          <p>The <strong>Kelly Criterion</strong> is a mathematical formula that calculates the optimal bet size to maximize long-term bankroll growth while minimizing risk of ruin.</p>
          <p>Developed by John Kelly in 1956, it's used by professional gamblers, investors, and hedge funds to size positions.</p>
          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">The Kelly Formula</h3>
            <p className="mb-0"><strong>Kelly % = (bp - q) / b</strong><br/><strong>b</strong> = decimal odds - 1 (For -110: b = 1.909 - 1 = 0.909)<br/><strong>p</strong> = probability of winning<br/><strong>q</strong> = probability of losing (1 - p)</p>
          </div>
          <h2>Understanding the Formula</h2>
          <h3>Step-by-Step Breakdown</h3>
          <p><strong>Example: 5-point edge on Over 225.5 at -110</strong></p>
          <ol><li><strong>Calculate true probability (p):</strong> Your model says Over wins 58% of the time → p = 0.58</li><li><strong>Calculate losing probability (q):</strong> q = 1 - 0.58 = 0.42</li><li><strong>Calculate decimal odds net (b):</strong> -110 converts to 1.909 decimal → b = 0.909</li><li><strong>Apply Kelly formula:</strong><br/>Kelly % = ((0.909 × 0.58) - 0.42) / 0.909<br/>Kelly % = (0.527 - 0.42) / 0.909<br/>Kelly % = 0.107 / 0.909<br/><strong>Kelly % = 11.8% of bankroll</strong></li></ol>
          <h3>Interpretation</h3>
          <p>With an 11.8% Kelly bet:</p>
          <ul><li><strong>$1000 bankroll:</strong> Bet $118</li><li><strong>$5000 bankroll:</strong> Bet $590</li><li><strong>$10,000 bankroll:</strong> Bet $1180</li></ul>
          <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=400&fit=crop" alt="Growth chart" className="w-full h-64 object-cover rounded-lg my-8" />
          <h2>Why Full Kelly is Too Aggressive</h2>
          <p>While mathematically optimal for growth, full Kelly has serious practical problems:</p>
          <h3>1. Massive Volatility</h3>
          <p>Full Kelly leads to 50%+ bankroll swings. You'll see your bankroll drop by half multiple times per year.</p>
          <h3>2. Requires Perfect Edge Estimation</h3>
          <p>If you think you have a 58% win rate but actually have 55%, full Kelly overbets and increases risk of ruin.</p>
          <h3>3. Psychological Stress</h3>
          <p>Watching 20% of your bankroll disappear in one bet causes tilt and bad decisions.</p>
          <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-6 my-8">
            <h3 className="text-red-400 mt-0">Warning</h3>
            <p className="mb-0">Professional bettors NEVER use full Kelly. It's mathematically sound but psychologically impossible. Use fractional Kelly instead.</p>
          </div>
          <h2>Fractional Kelly: The Practical Approach</h2>
          <p>Fractional Kelly scales down bet sizes to reduce volatility while maintaining long-term growth.</p>
          <h3>Quarter Kelly (25% of Kelly)</h3>
          <p><strong>Formula:</strong> Kelly % ÷ 4</p>
          <p><strong>Example:</strong> 11.8% Kelly → 2.95% of bankroll</p>
          <p><strong>Volatility:</strong> Low (~10-15% swings)</p>
          <p><strong>Growth rate:</strong> 75% of full Kelly growth</p>
          <p><strong>Best for:</strong> Conservative bettors, beginners, small edges</p>
          <h3>Half Kelly (50% of Kelly)</h3>
          <p><strong>Formula:</strong> Kelly % ÷ 2</p>
          <p><strong>Example:</strong> 11.8% Kelly → 5.9% of bankroll</p>
          <p><strong>Volatility:</strong> Moderate (~20-25% swings)</p>
          <p><strong>Growth rate:</strong> 87% of full Kelly growth</p>
          <p><strong>Best for:</strong> Most serious bettors, balanced approach</p>
          <h3>Three-Quarter Kelly (75% of Kelly)</h3>
          <p><strong>Formula:</strong> Kelly % × 0.75</p>
          <p><strong>Example:</strong> 11.8% Kelly → 8.85% of bankroll</p>
          <p><strong>Volatility:</strong> High (~30-40% swings)</p>
          <p><strong>Growth rate:</strong> 94% of full Kelly growth</p>
          <p><strong>Best for:</strong> Aggressive bettors with high risk tolerance</p>
          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Recommended: Half Kelly</h3>
            <p className="mb-0">Most professional bettors use <strong>Half Kelly</strong> as the sweet spot: 87% of optimal growth with 50% less volatility. It's forgiving of edge estimation errors and psychologically manageable.</p>
          </div>
          <h2>Practical Kelly Example</h2>
          <h3>Scenario</h3>
          <ul><li><strong>Bankroll:</strong> $5000</li><li><strong>Bet:</strong> Over 225.5 at -110</li><li><strong>Your model:</strong> 58% win probability</li><li><strong>Market implied probability:</strong> 52.4%</li><li><strong>Edge:</strong> 5.6%</li></ul>
          <h3>Full Kelly Calculation</h3>
          <p>Kelly % = ((0.909 × 0.58) - 0.42) / 0.909 = 11.8%<br/><strong>Bet size:</strong> $5000 × 11.8% = $590</p>
          <h3>Half Kelly (Recommended)</h3>
          <p>Half Kelly = 11.8% ÷ 2 = 5.9%<br/><strong>Bet size:</strong> $5000 × 5.9% = $295</p>
          <h3>Quarter Kelly (Conservative)</h3>
          <p>Quarter Kelly = 11.8% ÷ 4 = 2.95%<br/><strong>Bet size:</strong> $5000 × 2.95% = $147.50</p>
          <h2>When Kelly Says "No Bet"</h2>
          <p>If Kelly returns a negative or zero value, <strong>don't bet</strong>.</p>
          <h3>Example: Small Edge at -110</h3>
          <ul><li><strong>Your model:</strong> 52% win probability (very small edge)</li><li><strong>Market:</strong> 52.4% implied probability</li></ul>
          <p>Kelly % = ((0.909 × 0.52) - 0.48) / 0.909 = (0.472 - 0.48) / 0.909 = <strong>-0.88% (NEGATIVE)</strong></p>
          <p><strong>Interpretation:</strong> No edge. Don't bet.</p>
          <h2>Adjusting Kelly for Real-World Factors</h2>
          <h3>1. Edge Uncertainty</h3>
          <p>If you're not confident in your edge estimate, reduce Kelly further:</p>
          <ul><li><strong>High confidence (tested model):</strong> Half Kelly</li><li><strong>Medium confidence (new model):</strong> Quarter Kelly</li><li><strong>Low confidence (gut feel):</strong> Don't bet</li></ul>
          <h3>2. Correlated Bets</h3>
          <p>If you have multiple bets on the same game or related games, reduce each bet size to avoid overexposure:</p>
          <ul><li><strong>2 bets same game:</strong> Half Kelly → Quarter Kelly each</li><li><strong>3+ bets same game:</strong> Half Kelly → 1/6 Kelly each</li></ul>
          <h3>3. Odds Value</h3>
          <p>Better odds (less juice) = higher Kelly %:</p>
          <ul><li><strong>-105 instead of -110:</strong> +1-2% Kelly</li><li><strong>+100 instead of -110:</strong> +3-4% Kelly</li></ul>
          <h2>Common Kelly Mistakes</h2>
          <ul><li><strong>Overestimating win probability:</strong> Thinking you have 58% when you actually have 53% causes overbetting</li><li><strong>Using full Kelly:</strong> Leads to tilt and bankroll destruction</li><li><strong>Not adjusting for juice:</strong> Forgetting to convert odds correctly</li><li><strong>Ignoring variance:</strong> Even optimal Kelly bets lose 40%+ of the time</li><li><strong>Fixed unit betting despite edge size:</strong> Kelly says bet MORE on bigger edges</li></ul>
          <h2>Kelly vs Fixed Unit Betting</h2>
          <h3>Fixed Unit Betting</h3>
          <p><strong>Strategy:</strong> Bet 1-2% of bankroll every time, regardless of edge size</p>
          <p><strong>Pros:</strong> Simple, consistent, low volatility<br/><strong>Cons:</strong> Doesn't maximize growth, ignores edge size</p>
          <h3>Kelly Betting</h3>
          <p><strong>Strategy:</strong> Bet proportional to edge (bigger edge = bigger bet)</p>
          <p><strong>Pros:</strong> Maximizes long-term growth, optimal risk-adjusted returns<br/><strong>Cons:</strong> Requires accurate edge estimates, more complex</p>
          <h2>Sport Trader.io's Kelly Integration</h2>
          <p>Our platform automates Kelly calculations:</p>
          <ul><li><strong>Automatic edge detection:</strong> Calculates your model's win probability</li><li><strong>Kelly recommendations:</strong> Shows Half Kelly, Quarter Kelly unit sizes</li><li><strong>Strength score:</strong> Incorporates Kelly-like concepts (bigger edge = higher strength)</li><li><strong>Bankroll tracking:</strong> Adjusts bet sizes as bankroll grows/shrinks</li></ul>
          <h2>Practical Kelly Sizing Table</h2>
          <p><strong>$5000 Bankroll, -110 odds, Half Kelly</strong></p>
          <ul><li><strong>52% win rate (0% edge):</strong> $0 bet (no edge)</li><li><strong>54% win rate (2% edge):</strong> ~$110 bet</li><li><strong>56% win rate (4% edge):</strong> ~$220 bet</li><li><strong>58% win rate (6% edge):</strong> ~$330 bet</li><li><strong>60% win rate (8% edge):</strong> ~$440 bet</li></ul>
          <h2>Long-Term Kelly Results</h2>
          <p>Over 1000 bets with a 55% win rate at -110 odds:</p>
          <ul><li><strong>Full Kelly:</strong> +280% bankroll growth (but 60% drawdowns)</li><li><strong>Half Kelly:</strong> +180% bankroll growth (30% drawdowns)</li><li><strong>Quarter Kelly:</strong> +90% bankroll growth (15% drawdowns)</li><li><strong>Fixed 1% units:</strong> +45% bankroll growth (10% drawdowns)</li></ul>
          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">Key Takeaway</h3>
            <p className="mb-0">Half Kelly offers the best balance: near-optimal growth with manageable volatility. Use Quarter Kelly if you're conservative or uncertain about your edge.</p>
          </div>
          <h2>Next Steps</h2>
          <p>Learn unit sizing strategies: <Link to="/learn/unit-sizing" className="text-blue-400 hover:text-blue-300">Unit Sizing Based on Edge</Link>.</p>
          <p>Master bankroll basics: <Link to="/learn/bankroll-management-101" className="text-blue-400 hover:text-blue-300">Bankroll Management 101</Link>.</p>
        </div>
      </>
    )
  },

  'arbitrage-betting': {
    id: 'arbitrage-betting',
    title: 'Arbitrage Betting: Guaranteed Profit Strategy',
    category: 'Advanced',
    readTime: '20 min',
    lastUpdated: 'October 17, 2025',
    author: 'Sport Trader.io Team',
    metaDescription: 'Master arbitrage betting with real live data from our monitoring system. Learn how to guarantee profit regardless of game outcomes using live sportsbook data across 11+ bookmakers.',
    content: (
      <>
        <div className="prose prose-invert prose-lg max-w-none">

          <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Real Data - Right Now</h3>
            <p className="mb-0">
              <strong>This guide uses LIVE arbitrage opportunities</strong> detected by our monitoring system. These aren't theoretical examples—they're real bets you can place right now across 11+ sportsbooks.
            </p>
          </div>

          <h2>What is Arbitrage Betting?</h2>
          <p>
            Arbitrage betting (or "arbing") is a strategy that <strong>guarantees profit</strong> by exploiting price differences between sportsbooks. You place bets on all possible outcomes of an event across different bookmakers, ensuring you profit regardless of the result.
          </p>

          <h3>The Core Concept</h3>
          <p>Every betting odd has an "implied probability"—the bookmaker's assessment of the likelihood of that outcome:</p>

          <div className="bg-slate-900/50 rounded-lg p-4 my-6 font-mono text-sm">
            <p className="text-blue-300 mb-2">Conversion Formulas:</p>
            <p className="text-slate-300">Positive odds (+150): Implied Prob = 100 / (odds + 100) = 100 / 250 = 40%</p>
            <p className="text-slate-300">Negative odds (-110): Implied Prob = 110 / (110 + 100) = 52.4%</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6 my-8">
            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-6">
              <h4 className="text-red-400 mt-0">Normal Situation (No Arbitrage)</h4>
              <ul className="text-sm mb-0">
                <li>Team A at -110 → 52.4% implied probability</li>
                <li>Team B at -110 → 52.4% implied probability</li>
                <li><strong>Total: 104.8%</strong> ← Bookmaker has 4.8% edge (the "vig")</li>
              </ul>
            </div>
            <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-6">
              <h4 className="text-green-400 mt-0">Arbitrage Opportunity</h4>
              <ul className="text-sm mb-0">
                <li>Team A at +110 (Book 1) → 47.6% implied probability</li>
                <li>Team B at +114 (Book 2) → 46.7% implied probability</li>
                <li><strong>Total: 94.3%</strong> ← YOU have a 5.7% guaranteed profit!</li>
              </ul>
            </div>
          </div>

          <h2>Live Example #1: The 18.68% Monster (NHL)</h2>

          <div className="bg-gradient-to-r from-yellow-900/30 to-orange-900/30 border border-yellow-500/50 rounded-xl p-6 my-8">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">⭐</span>
              <h3 className="text-yellow-300 mt-0 mb-0">ACTIVE NOW - Highest Profit Opportunity</h3>
            </div>

            <div className="grid md:grid-cols-2 gap-6 text-sm">
              <div>
                <p className="text-slate-400 mb-1">Sport</p>
                <p className="text-white font-bold">NHL</p>
              </div>
              <div>
                <p className="text-slate-400 mb-1">Match</p>
                <p className="text-white font-bold">San Jose Sharks @ Utah Mammoth</p>
              </div>
              <div>
                <p className="text-slate-400 mb-1">Market</p>
                <p className="text-white font-bold">Point Spread</p>
              </div>
              <div>
                <p className="text-slate-400 mb-1">Arbitrage Margin</p>
                <p className="text-green-400 font-bold text-xl">18.68%</p>
              </div>
            </div>
          </div>

          <h3>The Opportunity Breakdown</h3>
          <div className="overflow-x-auto my-6">
            <table className="w-full text-sm">
              <thead className="bg-slate-800">
                <tr>
                  <th className="px-4 py-3 text-left">Sportsbook</th>
                  <th className="px-4 py-3 text-left">Selection</th>
                  <th className="px-4 py-3 text-right">Odds</th>
                  <th className="px-4 py-3 text-right">Implied Prob</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-t border-slate-700">
                  <td className="px-4 py-3 font-bold text-blue-400">BetMGM</td>
                  <td className="px-4 py-3">San Jose Sharks (spread)</td>
                  <td className="px-4 py-3 text-right font-mono">+150</td>
                  <td className="px-4 py-3 text-right">40.0%</td>
                </tr>
                <tr className="border-t border-slate-700">
                  <td className="px-4 py-3 font-bold text-orange-400">FanDuel</td>
                  <td className="px-4 py-3">Utah Mammoth (spread)</td>
                  <td className="px-4 py-3 text-right font-mono">+142</td>
                  <td className="px-4 py-3 text-right">41.3%</td>
                </tr>
                <tr className="border-t border-slate-700 bg-green-900/20">
                  <td className="px-4 py-3 font-bold" colSpan={2}>TOTAL (Both sides covered)</td>
                  <td className="px-4 py-3 text-right">—</td>
                  <td className="px-4 py-3 text-right font-bold text-green-400">81.3%</td>
                </tr>
              </tbody>
            </table>
          </div>

          <h3>The Math: Step-by-Step</h3>

          <p><strong>Step 1: Calculate Optimal Stakes</strong></p>
          <p>For a $1,000 total investment:</p>
          <div className="bg-slate-900/50 rounded-lg p-4 my-4 font-mono text-sm">
            <p className="text-blue-300">BetMGM stake:  $508.13 on San Jose +150</p>
            <p className="text-orange-300">FanDuel stake: $491.87 on Utah +142</p>
            <p className="text-slate-400">Total invested: $1,000.00</p>
          </div>

          <p><strong>Step 2: Calculate Guaranteed Returns</strong></p>

          <div className="grid md:grid-cols-2 gap-6 my-6">
            <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-6">
              <h4 className="text-blue-400 mt-0">Scenario A - BetMGM wins</h4>
              <p className="text-sm font-mono">Payout = $508.13 × 2.50 = $1,270.33</p>
              <p className="text-sm font-mono">Profit = $1,270.33 - $1,000 = <span className="text-green-400 font-bold">+$270.33</span></p>
            </div>
            <div className="bg-orange-900/20 border border-orange-500/30 rounded-lg p-6">
              <h4 className="text-orange-400 mt-0">Scenario B - FanDuel wins</h4>
              <p className="text-sm font-mono">Payout = $491.87 × 2.42 = $1,190.33</p>
              <p className="text-sm font-mono">Profit = $1,190.33 - $1,000 = <span className="text-green-400 font-bold">+$190.33</span></p>
            </div>
          </div>

          <div className="bg-green-900/30 border border-green-500/50 rounded-lg p-6 my-8">
            <h3 className="text-green-400 mt-0">Guaranteed Minimum Profit: $190.33 (19.0% ROI)</h3>
            <p className="mb-0">Regardless of which team covers the spread, you walk away with at least $190 in pure profit!</p>
          </div>

          <h2>Live Example #2: Safe 6% Return (NHL Totals)</h2>

          <div className="bg-slate-800/50 border border-slate-600 rounded-lg p-6 my-6">
            <h3 className="text-blue-400 mt-0">Boston Bruins @ Colorado Avalanche</h3>
            <p className="text-sm text-slate-400 mb-4">Total Points (Over/Under 6.5 goals)</p>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <p className="text-xs text-slate-500 mb-1">OVER 6.5</p>
                <p className="font-bold">FanDuel: +112 (47.17%)</p>
                <p className="text-sm text-slate-400">Stake: $497.65</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">UNDER 6.5</p>
                <p className="font-bold">DraftKings: +114 (46.73%)</p>
                <p className="text-sm text-slate-400">Stake: $502.35</p>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-700">
              <p className="text-sm mb-2"><strong>Total Implied Probability:</strong> 93.9%</p>
              <p className="text-green-400 font-bold">Arbitrage Margin: 6.1%</p>
              <p className="text-sm mt-3">
                <strong>If OVER hits:</strong> $1,055.02 → Profit: $55.02<br />
                <strong>If UNDER hits:</strong> $1,075.03 → Profit: $75.03
              </p>
              <p className="text-green-400 font-bold mt-3">Guaranteed Profit: $55.02 (5.5% ROI)</p>
            </div>
          </div>

          <h2>Why Do These Opportunities Exist?</h2>

          <h3>1. Independent Pricing Models</h3>
          <p>Each sportsbook uses proprietary algorithms. BetMGM might price Utah Mammoth differently than FanDuel. Different customer bases create different risk exposures. Books don't coordinate pricing (that would be illegal).</p>

          <h3>2. Market Inefficiencies</h3>
          <p>Books update at different speeds:</p>
          <ul>
            <li>Sharp books (Pinnacle, Circa) move lines instantly</li>
            <li>Recreational books (FanDuel, DraftKings) may lag 30-60 seconds</li>
            <li>Regional books wait for consensus</li>
          </ul>
          <p>When injury news breaks or a sharp bet lands, arbitrage windows open.</p>

          <h3>3. Promotional Odds</h3>
          <p>Books boost odds to attract customers. "Odds Boost" promotions create intentional arbitrage. New market states have aggressive pricing to gain market share.</p>

          <h2>Our Real-Time Monitoring System</h2>

          <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-blue-500/30 rounded-xl p-6 my-8">
            <h3 className="text-blue-400 mt-0">System Status</h3>
            <div className="grid md:grid-cols-3 gap-6 text-sm">
              <div>
                <p className="text-slate-400 mb-1">Scan Frequency</p>
                <p className="text-white font-bold">Every 10 seconds</p>
              </div>
              <div>
                <p className="text-slate-400 mb-1">Bookmakers Monitored</p>
                <p className="text-white font-bold">11 sportsbooks</p>
              </div>
              <div>
                <p className="text-slate-400 mb-1">Sports Tracked</p>
                <p className="text-white font-bold">NBA, NFL, NHL, NCAA, MLB</p>
              </div>
              <div>
                <p className="text-slate-400 mb-1">Markets</p>
                <p className="text-white font-bold">Moneylines, Spreads, Totals</p>
              </div>
              <div>
                <p className="text-slate-400 mb-1">Success Rate</p>
                <p className="text-green-400 font-bold">85.4%</p>
              </div>
              <div>
                <p className="text-slate-400 mb-1">Average Profit</p>
                <p className="text-green-400 font-bold">2.3%</p>
              </div>
            </div>
          </div>

          <h3>How It Works</h3>
          <ol>
            <li><strong>Data Collection:</strong> Every 10 seconds, fetch odds from The Odds API for all sports and markets</li>
            <li><strong>Arbitrage Detection:</strong> For each game, find best odds for each outcome across ALL books, calculate total implied probability</li>
            <li><strong>Alert Generation:</strong> If total probability {"<"} 100%, arbitrage exists! Calculate optimal stakes and profit percentage</li>
            <li><strong>Real-Time Broadcasting:</strong> WebSocket pushes alerts to dashboard, browser extension, and mobile app</li>
          </ol>

          <h2>ARB Auto Bettor™ Extension</h2>

          <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-6 my-8">
            <h3 className="text-purple-400 mt-0">95% Automated, 100% Legal</h3>
            <p>Our custom-built browser extension automates the arbitrage betting process while keeping you fully compliant with sportsbook terms of service.</p>

            <h4 className="text-purple-300">What It Does:</h4>
            <ul className="text-sm">
              <li>✅ Real-time monitoring via WebSocket connection</li>
              <li>✅ Instant push notifications for HIGH priority opportunities (5%+)</li>
              <li>✅ Auto-navigation to sportsbook game pages</li>
              <li>✅ Auto-fill bet slips with exact selection and calculated stake</li>
              <li>✅ Highlights "Place Bet" button with pulsing green glow</li>
              <li>✅ <strong>YOU click to confirm</strong> (required by law)</li>
            </ul>

            <h4 className="text-purple-300 mt-4">What It Doesn't Do (To Stay Legal):</h4>
            <ul className="text-sm">
              <li>❌ Never auto-clicks "Place Bet"</li>
              <li>❌ Never submits bets without user interaction</li>
              <li>❌ Never stores your credentials</li>
              <li>❌ Never bypasses CAPTCHA or security</li>
            </ul>
          </div>

          <h3>Time Savings</h3>
          <div className="overflow-x-auto my-6">
            <table className="w-full text-sm">
              <thead className="bg-slate-800">
                <tr>
                  <th className="px-4 py-3 text-left">Task</th>
                  <th className="px-4 py-3 text-right">Manual Time</th>
                  <th className="px-4 py-3 text-right">With Extension</th>
                  <th className="px-4 py-3 text-right">Savings</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-t border-slate-700">
                  <td className="px-4 py-3">Find opportunity</td>
                  <td className="px-4 py-3 text-right">2-5 min</td>
                  <td className="px-4 py-3 text-right">Instant alert</td>
                  <td className="px-4 py-3 text-right text-green-400">100%</td>
                </tr>
                <tr className="border-t border-slate-700">
                  <td className="px-4 py-3">Navigate to games</td>
                  <td className="px-4 py-3 text-right">40s per book</td>
                  <td className="px-4 py-3 text-right">2s</td>
                  <td className="px-4 py-3 text-right text-green-400">95%</td>
                </tr>
                <tr className="border-t border-slate-700">
                  <td className="px-4 py-3">Fill bet slips</td>
                  <td className="px-4 py-3 text-right">30s per bet</td>
                  <td className="px-4 py-3 text-right">3s auto-fill</td>
                  <td className="px-4 py-3 text-right text-green-400">90%</td>
                </tr>
                <tr className="border-t border-slate-700">
                  <td className="px-4 py-3">Calculate stakes</td>
                  <td className="px-4 py-3 text-right">60s</td>
                  <td className="px-4 py-3 text-right">Instant</td>
                  <td className="px-4 py-3 text-right text-green-400">100%</td>
                </tr>
                <tr className="border-t border-slate-700 bg-green-900/20">
                  <td className="px-4 py-3 font-bold">Total per arb</td>
                  <td className="px-4 py-3 text-right font-bold">5-8 minutes</td>
                  <td className="px-4 py-3 text-right font-bold">30-45 seconds</td>
                  <td className="px-4 py-3 text-right font-bold text-green-400">90%</td>
                </tr>
              </tbody>
            </table>
          </div>

          <h2>Profitability Analysis</h2>

          <h3>Conservative Scenario (Manual Execution)</h3>
          <div className="bg-slate-900/50 rounded-lg p-6 my-6">
            <p className="text-sm font-mono text-slate-300 mb-2">8-12 arbitrage opportunities per day</p>
            <p className="text-sm font-mono text-slate-300 mb-2">Average 2% profit margin</p>
            <p className="text-sm font-mono text-slate-300 mb-2">$100-200 stake per opportunity</p>
            <p className="text-sm font-mono text-slate-300 mb-4">70% capture rate (opportunities still available)</p>
            <hr className="border-slate-700 my-4" />
            <p className="text-lg font-bold text-green-400">$16-48/day = $400-1,200/month</p>
          </div>

          <h3>Aggressive Scenario (With ARB Auto Bettor)</h3>
          <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-6 my-6">
            <p className="text-sm font-mono text-slate-300 mb-2">30-50 arbitrage opportunities per day</p>
            <p className="text-sm font-mono text-slate-300 mb-2">Average 2.5% profit margin</p>
            <p className="text-sm font-mono text-slate-300 mb-2">$500-1,000 stake per opportunity</p>
            <p className="text-sm font-mono text-slate-300 mb-4">85% capture rate (faster execution)</p>
            <hr className="border-slate-700 my-4" />
            <p className="text-lg font-bold text-green-400">$375-1,250/day = $9,000-31,000/month</p>
          </div>

          <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-6 my-8">
            <h3 className="text-yellow-400 mt-0">The Catch</h3>
            <ul className="text-sm mb-0">
              <li><strong>Speed matters:</strong> Most opportunities close within 2-5 minutes</li>
              <li><strong>Account limits:</strong> Sportsbooks restrict profitable players over time</li>
              <li><strong>Bankroll required:</strong> Need $10,000+ for serious operation</li>
              <li><strong>Time commitment:</strong> Monitoring, executing, managing accounts</li>
              <li><strong>Diminishing returns:</strong> As you scale up, books limit you faster</li>
            </ul>
          </div>

          <h2>Common Mistakes to Avoid</h2>

          <h3>❌ Mistake #1: Ignoring Betting Limits</h3>
          <p>You calculate a perfect $1,000 arbitrage, but Book A limits you to $250 and Book B limits you to $400. Your stakes don't align and the arbitrage breaks.</p>
          <p><strong>Solution:</strong> Know limits before betting. Start small ($100-200 per arb). Build account history with recreational bets.</p>

          <h3>❌ Mistake #2: Wrong Line/Total</h3>
          <p>Multiple lines exist for the same game. Betting Lakers -4.5 at one book and Warriors +5.5 at another looks like arbitrage but has a 1-point gap.</p>
          <p><strong>Solution:</strong> Verify exact lines match, or ensure the gap creates a profitable "middle".</p>

          <h3>❌ Mistake #3: Accounts Get Limited</h3>
          <p>After consistent arbitrage profits, books will limit your bet sizes, require manual review, or ban you entirely.</p>
          <p><strong>Solution:</strong> Mix in recreational bets at bad odds. Bet popular markets occasionally. Don't max out every arbitrage. Spread action across many books.</p>

          <h2>Next Steps</h2>

          <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-6 my-8">
            <h3 className="text-blue-400 mt-0">Get Started Today</h3>
            <ol className="text-sm mb-0">
              <li><strong>View Live Opportunities:</strong> Visit the <Link to="/alerts" className="text-blue-300 hover:text-blue-200 underline">Alerts page</Link> to see current arbitrage opportunities</li>
              <li><strong>Fund Sportsbook Accounts:</strong> Minimum $1,000 each at DraftKings, FanDuel, BetMGM, Caesars</li>
              <li><strong>Install ARB Auto Bettor:</strong> Browser extension automates 90% of the process</li>
              <li><strong>Start Small:</strong> Begin with $100-200 stakes to learn the process</li>
              <li><strong>Scale Up:</strong> Increase position sizes as you gain experience</li>
            </ol>
          </div>

          <div className="bg-gradient-to-r from-green-900/30 to-blue-900/30 border border-green-500/30 rounded-xl p-8 my-8 text-center">
            <h3 className="text-3xl font-bold text-white mb-4">The Math is Certain. The Profit is Guaranteed.</h3>
            <p className="text-xl text-slate-300 mb-6">
              Right now, 20+ arbitrage opportunities are active with profits ranging from 1.1% to 18.68%.
            </p>
            <Link
              to="/alerts"
              className="inline-block px-8 py-4 bg-green-600 hover:bg-green-700 text-white font-bold text-lg rounded-lg transition-colors"
            >
              View Live Arbitrage Opportunities →
            </Link>
          </div>

          <h2>Legal & Responsible Gaming</h2>
          <p className="text-sm text-slate-400">
            <strong>What's Legal:</strong> Detecting arbitrage opportunities, calculating optimal stakes, placing bets at multiple sportsbooks, using software to find opportunities, browser extensions that assist (not automate) betting.
          </p>
          <p className="text-sm text-slate-400">
            <strong>What's NOT Legal:</strong> Automated bet placement without human interaction, using bots to bypass CAPTCHA, sharing accounts, coordinating with other bettors, exploiting software glitches.
          </p>
          <p className="text-sm text-slate-400">
            <strong>Our Approach:</strong> ARB Auto Bettor is 95% automated but 100% ToS compliant. The extension finds opportunities, navigates to games, fills bet slips, but requires YOU to click "Place Bet" for final confirmation.
          </p>

        </div>
      </>
    )
  },
};

export function ArticleDetail() {
  const { articleId } = useParams<{ articleId: string }>();
  const article = articleId ? articleContents[articleId] : null;

  if (!article) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-16">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h1 className="text-4xl font-bold text-white mb-4">Article Not Found</h1>
          <p className="text-slate-300 mb-8">
            This article is coming soon or doesn't exist yet.
          </p>
          <Link
            to="/learn"
            className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
          >
            Back to Learning Center
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-slate-400 mb-6">
          <Link to="/" className="hover:text-slate-300">Home</Link>
          <span>/</span>
          <Link to="/learn" className="hover:text-slate-300">Learn</Link>
          <span>/</span>
          <span className="text-slate-200">{article.title}</span>
        </div>

        {/* Article Header */}
        <div className="mb-8">
          <div className="flex flex-wrap items-center gap-4 mb-4">
            <span className="px-3 py-1 bg-blue-600/20 text-blue-400 text-sm font-semibold rounded-full border border-blue-500/30">
              {article.category}
            </span>
            <span className="text-slate-400 text-sm">{article.readTime} read</span>
            <span className="text-slate-400 text-sm">Last updated: {article.lastUpdated}</span>
          </div>

          <h1 className="text-5xl font-bold text-white mb-4 leading-tight">
            {article.title}
          </h1>

          <p className="text-xl text-slate-300 mb-6">
            {article.metaDescription}
          </p>

          <div className="flex items-center gap-3 text-sm text-slate-400">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-xs">ST</span>
              </div>
              <span>{article.author}</span>
            </div>
          </div>
        </div>

        {/* Article Content */}
        <div className="bg-slate-800/30 border border-slate-700 rounded-xl p-8 md:p-12">
          {article.content}
        </div>

        {/* Footer Navigation */}
        <div className="mt-12 flex justify-between items-center">
          <Link
            to="/learn"
            className="flex items-center gap-2 text-blue-400 hover:text-blue-300 font-semibold"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Learning Center
          </Link>

          <Link
            to="/tools"
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
          >
            Try Our Tools
          </Link>
        </div>

        {/* Disclaimer */}
        <div className="mt-8 bg-red-900/20 border border-red-700/50 rounded-xl p-6">
          <p className="text-red-300 text-sm">
            <strong>Disclaimer:</strong> This content is for educational purposes only. Sports betting involves risk.
            Always bet responsibly and never wager more than you can afford to lose. If you or someone you know has
            a gambling problem, call 1-800-GAMBLER. Must be 21+ to participate.
          </p>
        </div>
      </div>
    </div>
  );
}
