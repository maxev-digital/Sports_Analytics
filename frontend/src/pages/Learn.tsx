import { Link } from 'react-router-dom';

interface Article {
  id: string;
  title: string;
  description: string;
  category: string;
  readTime: string;
}

const articles: Article[] = [
  // Section 1: Understanding Live Betting Fundamentals
  {
    id: 'what-is-live-betting',
    title: 'What is Live Betting and Why It Matters',
    description: 'Learn the fundamentals of live betting, how odds move during games, and why live betting offers more opportunities than pregame wagering.',
    category: 'Fundamentals',
    readTime: '8 min'
  },
  {
    id: 'reading-live-odds',
    title: 'Reading Live Odds: A Complete Guide',
    description: 'Master American odds, implied probability, juice/vig, and why odds differ between sportsbooks.',
    category: 'Fundamentals',
    readTime: '10 min'
  },
  {
    id: 'expected-value',
    title: 'What is Expected Value (EV)?',
    description: 'Understanding the EV formula, positive vs negative EV betting, and why long-term thinking matters in sports betting.',
    category: 'Fundamentals',
    readTime: '12 min'
  },
  {
    id: 'projections-vs-market',
    title: 'Understanding Projections vs Market Lines',
    description: 'Learn what projections represent, why they differ from odds, and when they are most reliable.',
    category: 'Fundamentals',
    readTime: '9 min'
  },
  {
    id: 'pace-based-projections',
    title: 'Pace-Based Projections Explained',
    description: 'How pace affects total points, early vs late game differences, and adjusting for game script and blowouts.',
    category: 'Fundamentals',
    readTime: '11 min'
  },

  // Section 2: Using the Dashboard
  {
    id: 'dashboard-overview',
    title: 'Dashboard Overview: Your Command Center',
    description: 'Navigate the dashboard, understand game cards, color coding, filtering options, and customize your view.',
    category: 'Dashboard',
    readTime: '7 min'
  },
  {
    id: 'reading-game-card',
    title: 'Reading a Game Card',
    description: 'Understand live scores, projections, edge calculations, bookmaker comparisons, and recommendation badges.',
    category: 'Dashboard',
    readTime: '8 min'
  },
  {
    id: 'edge-indicator-system',
    title: 'The Edge Indicator System',
    description: 'What is an edge, minimum thresholds, edge vs confidence relationship, and when to trust large edges.',
    category: 'Dashboard',
    readTime: '10 min'
  },
  {
    id: 'confidence-levels',
    title: 'Confidence Levels: LOW, MEDIUM, HIGH',
    description: 'How confidence is calculated, quarter-by-quarter progression, and factors that increase confidence.',
    category: 'Dashboard',
    readTime: '9 min'
  },

  // Section 3: Betting Models & Strategy
  {
    id: 'pace-model-deep-dive',
    title: 'The Pace-Based Model Deep Dive',
    description: 'How current pace is calculated, weighting pregame vs live pace, and model limitations.',
    category: 'Strategy',
    readTime: '14 min'
  },
  {
    id: 'momentum-model',
    title: 'Momentum Model: Riding Hot Quarters',
    description: 'Recent scoring trends, quarter momentum indicators, and combining momentum with pace.',
    category: 'Strategy',
    readTime: '11 min'
  },
  {
    id: 'regression-to-mean',
    title: 'Regression to the Mean',
    description: 'What is regression, identifying outlier performances, and balancing regression with momentum.',
    category: 'Strategy',
    readTime: '10 min'
  },
  {
    id: 'garbage-time',
    title: 'Garbage Time: Friend or Foe?',
    description: 'Detecting garbage time scenarios, how blowouts affect totals, and late game fouling impact.',
    category: 'Strategy',
    readTime: '9 min'
  },
  {
    id: 'back-to-back-vs-rested',
    title: 'Back-to-Back vs Rested: The Ultimate Fatigue Edge',
    description: 'NBA and NHL teams on back-to-backs lose 61% ATS against rested opponents. Learn the science of fatigue, rest differential analysis, and why this edge has persisted for decades.',
    category: 'Strategy',
    readTime: '18 min'
  },
  {
    id: 'reverse-line-movement',
    title: 'Reverse Line Movement (RLM): Following Sharp Money',
    description: 'When the line moves opposite of public betting percentages, sharps are in action. 59% win rate following RLM. Learn to identify and exploit these opportunities.',
    category: 'Strategy',
    readTime: '16 min'
  },
  {
    id: 'fade-the-public',
    title: 'Fade the Public: The Contrarian Edge',
    description: 'Betting against teams with 70%+ public support wins 57% of the time. Understand why the public loses, when to fade, and how to profit from market inefficiencies.',
    category: 'Strategy',
    readTime: '15 min'
  },
  {
    id: 'situational-betting',
    title: 'Situational Betting: Revenge, Letdown, and Lookahead Spots',
    description: 'Teams after blowout losses, emotional wins, or before big games perform predictably. Learn to identify and exploit these high-value situational spots.',
    category: 'Strategy',
    readTime: '20 min'
  },

  // Section 4: Bankroll Management
  {
    id: 'bankroll-management-101',
    title: 'Bankroll Management 101',
    description: 'What is a bankroll, the 1-5% rule per bet, tracking your bets, and managing variance.',
    category: 'Bankroll',
    readTime: '12 min'
  },
  {
    id: 'unit-sizing',
    title: 'Unit Sizing Based on Edge',
    description: 'What is a unit, edge-based recommendations, Kelly Criterion basics, and when to bet more vs less.',
    category: 'Bankroll',
    readTime: '13 min'
  },
  {
    id: 'kelly-criterion',
    title: 'The Kelly Criterion Explained',
    description: 'Full Kelly formula, why full Kelly is too aggressive, quarter/half Kelly strategies.',
    category: 'Bankroll',
    readTime: '15 min'
  },
  {
    id: 'win-rate-vs-roi',
    title: 'Win Rate vs ROI',
    description: 'Why 50% win rate can be profitable, understanding ROI, closing line value, and sample size.',
    category: 'Bankroll',
    readTime: '10 min'
  },

  // Section 5: Market Dynamics
  {
    id: 'how-books-set-lines',
    title: 'How Sportsbooks Set Live Lines',
    description: 'Traders vs algorithms, sharp vs public money, line movement speed, and why lines differ.',
    category: 'Markets',
    readTime: '11 min'
  },
  {
    id: 'line-shopping',
    title: 'Line Shopping: The Easiest Edge',
    description: 'Comparing odds across sportsbooks, half-point differences, and how line shopping adds to ROI.',
    category: 'Markets',
    readTime: '8 min'
  },
  {
    id: 'steam-moves',
    title: 'Steam Moves and Why They Matter',
    description: 'What is a steam move, identifying sharp money, reverse line movement, and following the market.',
    category: 'Markets',
    readTime: '12 min'
  },
  {
    id: 'beating-closing-line',
    title: 'Beating the Closing Line',
    description: 'What is CLV, why it predicts long-term success, timing bets for best CLV.',
    category: 'Markets',
    readTime: '13 min'
  },

  // Section 6: Advanced Strategies
  {
    id: 'nhl-goalie-pull-strategy',
    title: 'NHL Goalie Pull Strategy: Winning with 48% Success Rate',
    description: 'Master the most profitable NHL betting strategy. Learn how positive expected value (EV) makes you profitable even with a 48% win rate. Real-world examples, full math breakdowns, and why this beats the closing line 90%+ of the time.',
    category: 'Advanced',
    readTime: '25 min'
  },
  {
    id: 'nba-favorite-comeback-strategy',
    title: 'NBA Favorite Comeback Strategy: Profiting from Regression to the Mean',
    description: 'When favorites trail underdogs after hot starts, regression creates value. Historical data: 60.3% ATS at halftime. Learn the regression scoring system, when to bet 2H spreads, and why underdogs shooting 15% above average always regress.',
    category: 'Advanced',
    readTime: '22 min'
  },
  {
    id: 'middling-opportunities',
    title: 'Middling Opportunities',
    description: 'What is a middle, live betting scenarios, risk vs reward, and real NBA examples.',
    category: 'Advanced',
    readTime: '11 min'
  },
  {
    id: 'hedging-bets',
    title: 'Hedging Your Bets',
    description: 'What is hedging, when to hedge (and when not to), guaranteed profit scenarios.',
    category: 'Advanced',
    readTime: '10 min'
  },
  {
    id: 'arbitrage-betting',
    title: 'Arbitrage Betting: Guaranteed Profit Strategy',
    description: 'Master arbitrage betting with REAL LIVE data from our monitoring system. Learn how to guarantee profit using live opportunities across 11+ sportsbooks, including our ARB Auto Bettor™ extension.',
    category: 'Advanced',
    readTime: '20 min'
  },

  // Section 7: Psychology & Discipline
  {
    id: 'emotional-control',
    title: 'Emotional Control in Live Betting',
    description: 'The fast-paced nature of live betting, avoiding tilt, managing FOMO, and sticking to strategy.',
    category: 'Psychology',
    readTime: '9 min'
  },
  {
    id: 'chasing-losses',
    title: 'The Danger of Chasing Losses',
    description: 'What is loss chasing, why it destroys bankrolls, setting loss limits.',
    category: 'Psychology',
    readTime: '8 min'
  },
  {
    id: 'patience',
    title: 'Patience: The Bettor\'s Virtue',
    description: 'Not every game has an edge, waiting for high-quality spots, quality over quantity.',
    category: 'Psychology',
    readTime: '7 min'
  },

  // Section 8: NBA-Specific Knowledge
  {
    id: 'nba-pace-statistics',
    title: 'NBA Pace Statistics',
    description: 'What is pace in basketball, league averages, fastest and slowest teams, pace changes mid-game.',
    category: 'NBA',
    readTime: '10 min'
  },
  {
    id: 'quarter-trends',
    title: 'Quarter-by-Quarter Trends',
    description: 'First quarter totals, third quarter scoring spikes, fourth quarter variance, overtime implications.',
    category: 'NBA',
    readTime: '11 min'
  },
  {
    id: 'rest-and-back-to-backs',
    title: 'Rest and Back-to-Backs',
    description: 'NBA scheduling quirks, fatigue impact on totals, rest advantage quantified.',
    category: 'NBA',
    readTime: '9 min'
  },

  // Section 9: Legal & Responsible Gaming
  {
    id: 'legal-sports-betting',
    title: 'Legal Sports Betting: Know Your State',
    description: 'Legal states for online betting, age requirements, offshore vs regulated books, tax implications.',
    category: 'Legal',
    readTime: '10 min'
  },
  {
    id: 'responsible-gaming',
    title: 'Responsible Gaming Resources',
    description: 'Recognizing problem gambling signs, setting limits, self-exclusion programs. National helpline: 1-800-GAMBLER.',
    category: 'Legal',
    readTime: '8 min'
  },
  {
    id: 'understanding-odds-reality',
    title: 'Understanding the Odds (Reality Check)',
    description: 'Long-term expectation vs short-term luck, realistic ROI expectations, why most bettors lose.',
    category: 'Legal',
    readTime: '9 min'
  },
];

const categories = ['All', 'Fundamentals', 'Dashboard', 'Strategy', 'Bankroll', 'Markets', 'Advanced', 'Psychology', 'NBA', 'Legal'];

export function Learn() {
  const [selectedCategory, setSelectedCategory] = React.useState('All');

  const filteredArticles = selectedCategory === 'All'
    ? articles
    : articles.filter(a => a.category === selectedCategory);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">Sports Betting Education</h1>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto">
            Master live betting with our comprehensive educational resources. From fundamentals to advanced strategies,
            learn everything you need to become a successful sports bettor.
          </p>
        </div>

        {/* Category Filter */}
        <div className="flex flex-wrap justify-center gap-2 mb-10">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-5 py-2 rounded-lg font-semibold transition-all text-sm ${
                selectedCategory === cat
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Articles Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredArticles.map(article => (
            <Link
              key={article.id}
              to={`/learn/${article.id}`}
              className="group bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6 hover:bg-slate-800 hover:border-blue-500/50 transition-all duration-300"
            >
              {/* Category Badge */}
              <div className="flex items-center justify-between mb-3">
                <span className="px-3 py-1 bg-blue-600/20 text-blue-400 text-xs font-semibold rounded-full border border-blue-500/30">
                  {article.category}
                </span>
                <span className="text-slate-400 text-sm">{article.readTime}</span>
              </div>

              {/* Title */}
              <h3 className="text-xl font-bold text-white mb-3 group-hover:text-blue-400 transition-colors">
                {article.title}
              </h3>

              {/* Description */}
              <p className="text-slate-300 text-sm leading-relaxed mb-4">
                {article.description}
              </p>

              {/* Read More */}
              <div className="flex items-center text-blue-400 font-semibold text-sm group-hover:text-blue-300">
                Read Article
                <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </Link>
          ))}
        </div>

        {/* SEO Footer Section */}
        <div className="mt-16 bg-slate-800/30 border border-slate-700 rounded-xl p-8">
          <h2 className="text-3xl font-bold text-white mb-4">Why Learn Sports Betting?</h2>
          <div className="grid md:grid-cols-2 gap-6 text-slate-300">
            <div>
              <h3 className="text-xl font-bold text-blue-400 mb-2">Knowledge is Profit</h3>
              <p>
                Successful sports betting isn't about luck—it's about making informed decisions based on data,
                probability, and sound bankroll management. Our educational resources teach you the skills
                professional bettors use to gain an edge.
              </p>
            </div>
            <div>
              <h3 className="text-xl font-bold text-blue-400 mb-2">Avoid Costly Mistakes</h3>
              <p>
                Most bettors lose money because they don't understand key concepts like expected value, variance,
                and proper unit sizing. Learn these fundamentals to protect your bankroll and bet smarter.
              </p>
            </div>
            <div>
              <h3 className="text-xl font-bold text-blue-400 mb-2">Master Live Betting</h3>
              <p>
                Live betting offers unique opportunities not available pregame, but requires quick thinking
                and deep understanding of how games unfold. Our guides teach you to identify +EV spots in real-time.
              </p>
            </div>
            <div>
              <h3 className="text-xl font-bold text-blue-400 mb-2">Responsible Gaming</h3>
              <p>
                We emphasize responsible gambling practices, bankroll management, and recognizing warning signs
                of problem gambling. Sports betting should be entertainment, not a source of financial stress.
              </p>
            </div>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="mt-8 bg-red-900/20 border border-red-700/50 rounded-xl p-6">
          <p className="text-red-300 text-sm">
            <strong>Responsible Gaming Disclaimer:</strong> Sports betting involves risk. Never bet more than you can afford to lose.
            If you or someone you know has a gambling problem, call the National Problem Gambling Helpline at 1-800-GAMBLER.
            Must be 21+ to participate in sports betting. Check your local laws before betting.
          </p>
        </div>
      </div>
    </div>
  );
}

// Add React import at the top
import React from 'react';
