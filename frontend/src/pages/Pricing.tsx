import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getApiUrl } from '../config';

export function Pricing() {
  const { username, isAuthenticated } = useAuth();
  const [loading, setLoading] = useState<string | null>(null);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');
  const [showFeatureComparison, setShowFeatureComparison] = useState(false);
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());

  // Beta launch promotion - flat 50% off for all early members
  const discountPercent = 50;

  const toggleCardExpansion = (planName: string) => {
    setExpandedCards(prev => {
      const newSet = new Set(prev);
      if (newSet.has(planName)) {
        newSet.delete(planName);
      } else {
        newSet.add(planName);
      }
      return newSet;
    });
  };

  // Stripe Price IDs (from backend .env) - Original prices
  // Using promo code for 50% OFF FOR LIFE discount
  const STRIPE_PRICE_IDS = {
    starter: 'price_1SL6DfR4L082TOJBCtBGFXgA',
    semipro: 'price_1SL6D2R4L082TOJBUP6iO2g7',
    professional: 'price_1SL6E4R4L082TOJBLphpsfhx',
    elite: 'price_1SL6ERR4L082TOJBz91Q9hBM',
    elitepro: 'price_1SL6EtR4L082TOJB2Pzx9Mgq',
  };

  const handleSubscribe = async (tier: 'starter' | 'semipro' | 'professional' | 'elite' | 'elitepro') => {
    if (!isAuthenticated || !username) {
      alert('Please log in to subscribe');
      return;
    }

    setLoading(tier);

    try {
      const response = await fetch('/api/stripe/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          price_id: STRIPE_PRICE_IDS[tier],
          user_id: username,
          user_email: `${username.replace(/\s+/g, '.')}@max-ev-sports.com`,
          apply_beta_discount: true, // Automatically apply 50% OFF promo code
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Redirect to Stripe checkout
        window.location.href = data.url;
      } else {
        alert(data.detail || 'Failed to create checkout session');
        setLoading(null);
      }
    } catch (error) {
      console.error('Checkout error:', error);
      alert('Network error. Please try again.');
      setLoading(null);
    }
  };

  const plans = [
    {
      name: 'Starter',
      price: 29,
      period: 'month',
      description: 'Essential tools for recreational bettors',
      edge: '2-4%',
      edgeColor: 'green',
      features: [
        'Live game odds from 60+ sportsbooks',
        'Basic totals projections',
        'Game momentum tracking',
        'No-Vig Calculator',
        'Expected Value Calculator',
        'Basic Line Movement Tracker',
        'All major sports coverage',
        '10 Second Refresh',
        'Historical data (7 days)',
        'Email Notifications',
        'Advanced Bet Tracker 100 Bets a month',
        'Export to CSV',
      ],
      limitations: [
        'No props module',
        'No advanced models',
        'No API access',
      ],
      cta: 'Start 7-Day Trial',
      popular: false,
      color: 'green',
      annualPrice: 278,
      annualSavings: 70,
    },
    {
      name: 'Semi Pro',
      price: 79,
      period: 'month',
      description: 'For serious bettors who want every edge',
      edge: '4-6%',
      edgeColor: 'blue',
      features: [
        'Everything in Starter, plus:',
        'Advanced Analytics Dashboard',
        'Advanced Line Movement Tracker',
        'Steam Move Alerts (real-time)',
        'Market Consensus Line',
        'Arbitrage Finder',
        'Middle Finder',
        'Advanced Bet Tracking (unlimited)',
        'CLV Tracker',
        'ROI Dashboard with analytics',
        'All sports + international markets',
        '1-second refresh rate',
        'Historical line data (90 days)',
        'SMS + Push notifications',
        'Position sizing calculator',
      ],
      limitations: [],
      cta: 'Start 7-Day Trial',
      popular: true,
      color: 'blue',
      annualPrice: 758,
      annualSavings: 190,
    },
    {
      name: 'Professional',
      price: 149,
      period: 'month',
      description: 'Maximum firepower for sharp bettors',
      edge: '6-8%',
      edgeColor: 'purple',
      features: [
        'Everything in Semi Pro, plus:',
        'Tech Stack: OpticOdds API, Cloud ML, Redis Cache, Sub-30s WebSocket',
        'Browser Extension Tool',
        'Player Props Module (all sports)',
        'SGP Builder with correlation analysis',
        'PrizePicks/Underdog/Sleeper comparison',
        'Advanced projection models',
        'Weather impact analysis',
        'Injury/news alerts (real-time)',
        'Kelly Criterion optimizer',
        'Hedge calculator',
        'Derivative markets calculator',
        'Closing line value predictor',
        'Historical line data (unlimited)',
        'Priority support (24/7)',
        'Custom alerts & automation',
        'White-label reporting',
        'Multi-account tracking',
      ],
      limitations: [],
      cta: 'Start 7-Day Trial',
      popular: false,
      color: 'purple',
      annualPrice: 1430,
      annualSavings: 358,
    },
    {
      name: 'Elite',
      price: 299,
      period: 'month',
      description: 'For professional operations and serious bettors',
      edge: '8-10%',
      edgeColor: 'amber',
      features: [
        'Everything in Professional, plus:',
        'Tech Stack: Sportradar Full, GPU ML, PostgreSQL + Redis, Sub-1s Push',
        'Downloadable Desktop Client',
        'Full API access (unlimited calls)',
        'Custom model integration',
        'Dedicated account manager',
        'Custom sportsbook integrations',
        'Advanced backtesting engine',
        'Machine learning models',
        'Automated bet placement (via API)',
        'Custom data feeds',
        'White-glove onboarding',
        'Priority feature requests',
        'SLA guarantee (99.9% uptime)',
        'Custom dashboards',
        'Offshore book support',
        'Private Slack/Discord channel',
      ],
      limitations: [],
      cta: 'Contact Sales',
      popular: false,
      color: 'amber',
      annualPrice: 2870,
      annualSavings: 718,
      enterprise: false,
    },
    {
      name: 'Elite Pro',
      price: 799,
      period: 'month',
      description: 'Ultra-premium tier for the top 2% of bettors',
      edge: '10-15%',
      edgeColor: 'red',
      features: [
        'Everything in Elite, plus:',
        'Tech Stack: Sportradar Elite, Dedicated GPU, Distributed DB + Redis, Sub-50ms',
        'Enhanced Desktop Client (Windows/Mac/Linux)',
        'Offshore server access (millisecond advantage)',
        'Direct sportsbook API connections',
        'Fastest AI prediction engine',
        'Real-time ML model updates',
        'Geographically distributed servers',
        'Sub-50ms line detection',
        'Dedicated GPU processing',
        'Proprietary sharp action alerts',
        'Private syndicate data feeds',
        'Personal trading desk support',
        'Custom algorithm development',
        'Institutional-grade infrastructure',
        'Reserved server capacity',
        'Annual VIP Invitation to Circa Survivor Week 1 Party',
      ],
      limitations: [],
      cta: 'Apply for Access',
      popular: false,
      color: 'red',
      annualPrice: 7670,
      annualSavings: 1918,
      enterprise: true,
      exclusive: true,
    },
  ];

  const faqs = [
    {
      q: 'Can I cancel anytime?',
      a: 'Yes! Cancel anytime with no penalties. Your access continues until the end of your billing period.'
    },
    {
      q: 'Do you offer refunds?',
      a: 'We offer a 7-day money-back guarantee. If you\'re not satisfied, we\'ll refund your purchase in full.'
    },
    {
      q: 'What payment methods do you accept?',
      a: 'We accept all major credit cards, PayPal, and cryptocurrency.'
    },
    {
      q: 'Is there a discount for annual plans?',
      a: 'Yes! Save 20% when you pay annually. Semi Pro: $758/year (save $190), Professional: $1,430/year (save $358), Elite: $2,870/year (save $718), Elite Pro: $7,670/year (save $1,918)'
    },
    {
      q: 'Do you have an API?',
      a: 'Full REST API access is available for Professional, Elite, and Elite Pro plans for $99/month. Includes 10,000 requests/day, real-time odds data, historical data access, and webhook support.'
    },
    {
      q: 'Can I upgrade or downgrade later?',
      a: 'Absolutely! Upgrade anytime to unlock more features. Downgrades take effect at the next billing cycle.'
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-slate-100 mb-4">
            Choose Your Plan
          </h1>
          <p className="text-xl text-slate-300 mb-6">
            Get the tools you need to win at sports betting
          </p>

          {/* Billing Cycle Toggle */}
          <div className="flex justify-center mb-6">
            <div className="inline-flex items-center bg-slate-800/50 border border-slate-700 rounded-lg p-1">
              <button
                onClick={() => setBillingCycle('monthly')}
                className={`px-6 py-2 rounded-md font-semibold text-sm transition-all ${
                  billingCycle === 'monthly'
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'text-slate-300 hover:text-slate-100'
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingCycle('annual')}
                className={`px-6 py-2 rounded-md font-semibold text-sm transition-all relative ${
                  billingCycle === 'annual'
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'text-slate-300 hover:text-slate-100'
                }`}
              >
                Annual
                <span className="absolute -top-2 -right-2 bg-green-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
                  Save 20%
                </span>
              </button>
            </div>
          </div>

          {/* Beta Launch Promotion Banner */}
          <div className="inline-flex items-center gap-3 bg-gradient-to-r from-green-900/40 to-blue-900/40 border border-green-500 rounded-lg px-6 py-4 shadow-lg shadow-green-500/20">
            <svg className="w-7 h-7 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
            </svg>
            <div>
              <span className="text-green-300 font-bold text-xl">
                🎉 Beta Launch Special: 50% OFF FOR LIFE 🎉
              </span>
              <p className="text-green-400 text-sm mt-1">Lock in this price forever! Join our early members and help us build the future of sports betting analytics!</p>
            </div>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-16">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative bg-slate-800/50 backdrop-blur-sm border rounded-2xl p-5 flex flex-col ${
                plan.popular
                  ? 'border-blue-500 shadow-2xl shadow-blue-500/20 lg:scale-105'
                  : plan.exclusive
                  ? 'border-red-500 shadow-2xl shadow-red-500/30 bg-gradient-to-br from-red-900/20 to-slate-800/50'
                  : plan.enterprise
                  ? 'border-amber-500/50 shadow-xl shadow-amber-500/10'
                  : 'border-slate-700'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <div className="bg-gradient-to-r from-blue-600 to-blue-400 text-white text-xs font-bold px-4 py-1 rounded-full shadow-lg">
                    MOST POPULAR
                  </div>
                </div>
              )}
              {plan.exclusive && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <div className="bg-gradient-to-r from-red-600 to-red-400 text-white text-xs font-bold px-4 py-1 rounded-full shadow-lg animate-pulse">
                    TOP 2% ONLY
                  </div>
                </div>
              )}
              {plan.enterprise && !plan.exclusive && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <div className="bg-gradient-to-r from-amber-600 to-amber-400 text-white text-xs font-bold px-4 py-1 rounded-full shadow-lg">
                    BEST VALUE
                  </div>
                </div>
              )}

              <div className="text-center mb-5">
                <h3 className="text-lg font-bold text-slate-100 mb-1">{plan.name}</h3>

                {/* Edge Badge */}
                <div className={`inline-block px-3 py-1 rounded-full text-xs font-bold mb-2 ${
                  plan.edgeColor === 'red' ? 'bg-red-500/20 text-red-300 border border-red-500/50' :
                  plan.edgeColor === 'amber' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50' :
                  plan.edgeColor === 'purple' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/50' :
                  plan.edgeColor === 'blue' ? 'bg-blue-500/20 text-blue-300 border border-blue-500/50' :
                  plan.edgeColor === 'green' ? 'bg-green-500/20 text-green-300 border border-green-500/50' :
                  'bg-slate-500/20 text-slate-300 border border-slate-500/50'
                }`}>
                  {plan.edge} Edge
                </div>

                <div className="mb-1">
                  {billingCycle === 'monthly' ? (
                    <div className="flex flex-col items-center gap-1">
                      {plan.price > 0 ? (
                        <>
                          {/* Original price struck through */}
                          <div className="text-slate-500 text-sm line-through">
                            ${plan.price}/mo
                          </div>
                          {/* Discounted price */}
                          <div className="flex items-baseline gap-1">
                            <span className="text-4xl font-bold text-green-400">
                              ${Math.round(plan.price * (1 - discountPercent / 100))}
                            </span>
                            <span className="text-slate-400 text-xs">/ month</span>
                          </div>
                          {/* Discount badge */}
                          <div className="text-xs font-bold px-2 py-0.5 rounded-full bg-green-500 text-white">
                            {discountPercent}% OFF FOR LIFE
                          </div>
                        </>
                      ) : (
                        <span className="text-3xl font-bold text-slate-100">Free</span>
                      )}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center gap-1">
                      {plan.annualPrice ? (
                        <>
                          {/* Original annual price struck through */}
                          <div className="text-slate-500 text-sm line-through">
                            ${plan.annualPrice}/yr
                          </div>
                          {/* Discounted annual price */}
                          <div className="flex items-baseline gap-1">
                            <span className="text-4xl font-bold text-green-400">
                              ${Math.round(plan.annualPrice * (1 - discountPercent / 100))}
                            </span>
                            <span className="text-slate-400 text-xs">/ year</span>
                          </div>
                          {/* Discount badge */}
                          <div className="text-xs font-bold px-2 py-0.5 rounded-full bg-green-500 text-white">
                            {discountPercent}% OFF FOR LIFE
                          </div>
                        </>
                      ) : (
                        <span className="text-3xl font-bold text-slate-100">Free</span>
                      )}
                    </div>
                  )}
                </div>
                {billingCycle === 'annual' && plan.annualPrice && (
                  <div className="text-xs text-green-400 font-semibold mb-1">
                    Save ${plan.annualSavings}/year vs monthly
                  </div>
                )}
                {billingCycle === 'monthly' && plan.annualPrice && (
                  <div className="text-xs text-slate-500 mb-1">
                    Or ${plan.annualPrice}/year (save ${plan.annualSavings})
                  </div>
                )}
                <p className="text-xs text-slate-400">{plan.description}</p>
              </div>

              <button
                onClick={() => {
                  if (plan.name === 'Starter') {
                    handleSubscribe('starter');
                  } else if (plan.name === 'Semi Pro') {
                    handleSubscribe('semipro');
                  } else if (plan.name === 'Professional') {
                    handleSubscribe('professional');
                  } else if (plan.name === 'Elite') {
                    handleSubscribe('elite');
                  } else if (plan.name === 'Elite Pro') {
                    handleSubscribe('elitepro');
                  }
                }}
                disabled={loading !== null}
                className={`w-full py-3 rounded-lg font-bold text-xs mb-5 transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                  plan.exclusive
                    ? 'bg-gradient-to-r from-red-600 to-red-500 hover:from-red-700 hover:to-red-600 text-white shadow-lg shadow-red-600/30'
                    : plan.popular
                    ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-600/30'
                    : plan.color === 'amber'
                    ? 'bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-700 hover:to-amber-600 text-white shadow-lg shadow-amber-600/30'
                    : plan.color === 'purple'
                    ? 'bg-purple-600 hover:bg-purple-700 text-white'
                    : plan.color === 'green'
                    ? 'bg-green-600 hover:bg-green-700 text-white'
                    : 'bg-slate-700 hover:bg-slate-600 text-slate-200'
                }`}
              >
                {loading === plan.name.toLowerCase() ? 'Loading...' : plan.cta}
              </button>

              <div className="space-y-2 flex-grow">
                <div className="font-semibold text-slate-200 mb-2 text-sm">Features:</div>
                {(expandedCards.has(plan.name) ? plan.features : plan.features.slice(0, 8)).map((feature, idx) => (
                  <div key={idx} className="flex items-start gap-2">
                    <svg className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className={`text-xs ${feature.startsWith('Everything in') ? 'font-semibold text-slate-200' : 'text-slate-300'}`}>
                      {feature}
                    </span>
                  </div>
                ))}
                {plan.features.length > 8 && (
                  <button
                    onClick={() => toggleCardExpansion(plan.name)}
                    className="text-xs text-blue-400 hover:text-blue-300 font-semibold pt-1 flex items-center gap-1 transition-colors"
                  >
                    {expandedCards.has(plan.name) ? (
                      <>
                        Show less
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                        </svg>
                      </>
                    ) : (
                      <>
                        + {plan.features.length - 8} more features
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </>
                    )}
                  </button>
                )}

                {plan.limitations.length > 0 && (
                  <div className="pt-3 mt-3 border-t border-slate-700">
                    <div className="font-semibold text-slate-400 mb-2 text-xs">Not included:</div>
                    {plan.limitations.map((limit, idx) => (
                      <div key={idx} className="flex items-start gap-2">
                        <svg className="w-3 h-3 text-slate-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                        <span className="text-xs text-slate-500">{limit}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Add-ons Section */}
        <div className="mb-16 bg-slate-800/30 border border-slate-700 rounded-2xl p-8">
          <h2 className="text-2xl font-bold text-slate-100 mb-6 text-center">
            Premium Add-Ons
          </h2>
          <div className="grid grid-cols-1 gap-6 max-w-2xl mx-auto">
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-bold text-slate-100 mb-2">API Access</h3>
              <div className="text-3xl font-bold text-slate-100 mb-3">$99<span className="text-sm text-slate-400">/month</span></div>
              <p className="text-sm text-slate-300 mb-4">Full REST API access for custom integrations. Available for Professional, Elite, and Elite Pro plans.</p>
              <ul className="space-y-2 text-xs text-slate-400">
                <li>• 10,000 requests/day</li>
                <li>• Real-time odds data</li>
                <li>• Historical data access</li>
                <li>• Webhook support</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Trust Indicators */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-16">
          <div className="text-center p-6 bg-slate-800/30 rounded-lg border border-slate-700/50">
            <div className="text-2xl font-bold text-slate-100 mb-1">1M+</div>
            <div className="text-sm text-slate-400 font-medium">Odds analyzed daily</div>
          </div>
          <div className="text-center p-6 bg-slate-800/30 rounded-lg border border-slate-700/50">
            <div className="text-2xl font-bold text-slate-100 mb-1">60+</div>
            <div className="text-sm text-slate-400 font-medium">Sportsbooks tracked</div>
          </div>
          <div className="text-center p-6 bg-slate-800/30 rounded-lg border border-slate-700/50">
            <div className="text-2xl font-bold text-slate-100 mb-1">5K+</div>
            <div className="text-sm text-slate-400 font-medium">Active users</div>
          </div>
          <div className="text-center p-6 bg-slate-800/30 rounded-lg border border-slate-700/50">
            <div className="text-2xl font-bold text-slate-100 mb-1">4.9/5</div>
            <div className="text-sm text-slate-400 font-medium">User rating</div>
          </div>
        </div>

        {/* Competitor Comparison */}
        <div className="mb-16 bg-gradient-to-br from-blue-900/20 via-slate-800/50 to-purple-900/20 border-2 border-blue-700/50 rounded-2xl p-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-slate-100 mb-3">
              Why Max EV Sports Beats The Competition
            </h2>
            <p className="text-lg text-slate-300 max-w-3xl mx-auto">
              We deliver more features, faster data, and better value than any competitor in the market
            </p>
          </div>

          {/* Comparison Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-base">
              <thead>
                <tr className="border-b-2 border-blue-600">
                  <th className="text-left py-4 px-4 text-slate-100 font-bold">Feature</th>
                  <th className="text-center py-4 px-4 bg-blue-900/30">
                    <div className="font-bold text-blue-300 text-xl">Max EV Sports</div>
                    <div className="text-sm text-blue-200 mt-1">Semi Pro $79/mo</div>
                  </th>
                  <th className="text-center py-4 px-4 text-slate-300">
                    <div className="font-bold text-slate-100 text-lg">OddsJam</div>
                    <div className="text-sm text-slate-400 mt-1">Premium $99/mo</div>
                  </th>
                  <th className="text-center py-4 px-4 text-slate-300">
                    <div className="font-bold text-slate-100 text-lg">Action Network</div>
                    <div className="text-sm text-slate-400 mt-1">Pro $149/mo</div>
                  </th>
                  <th className="text-center py-4 px-4 text-slate-300">
                    <div className="font-bold text-slate-100 text-lg">Unabated</div>
                    <div className="text-sm text-slate-400 mt-1">Elite $99/mo</div>
                  </th>
                  <th className="text-center py-4 px-4 text-slate-300">
                    <div className="font-bold text-slate-100 text-lg">BetQL</div>
                    <div className="text-sm text-slate-400 mt-1">Premium $49/mo</div>
                  </th>
                </tr>
              </thead>
              <tbody>
                {/* Price Row */}
                <tr className="border-b border-slate-700/50">
                  <td className="py-4 px-4 font-semibold text-slate-100 text-base">Monthly Price</td>
                  <td className="text-center py-4 px-4 bg-blue-900/10">
                    <span className="text-green-400 font-bold text-xl">$79</span>
                  </td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">$99</td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">$149</td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">$99</td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">$49</td>
                </tr>

                {/* Sportsbooks Tracked */}
                <tr className="border-b border-slate-700/50 hover:bg-slate-700/20">
                  <td className="py-4 px-4 text-slate-100 text-base">Sportsbooks Tracked</td>
                  <td className="text-center py-4 px-4 bg-blue-900/10">
                    <span className="text-green-400 font-bold text-lg">60+</span>
                  </td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">40+</td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">25+</td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">35+</td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">20+</td>
                </tr>

                {/* Refresh Speed */}
                <tr className="border-b border-slate-700/50 hover:bg-slate-700/20">
                  <td className="py-4 px-4 text-slate-100 text-base">Refresh Speed</td>
                  <td className="text-center py-4 px-4 bg-blue-900/10">
                    <span className="text-green-400 font-bold text-base">&lt;1s WebSocket</span>
                  </td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">5-10s polling</td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">15-30s polling</td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">10-15s polling</td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">30-60s polling</td>
                </tr>

                {/* Arbitrage Finder */}
                <tr className="border-b border-slate-700/50 hover:bg-slate-700/20">
                  <td className="py-4 px-4 text-slate-100 text-base">Arbitrage Finder</td>
                  <td className="text-center py-4 px-4 bg-blue-900/10">
                    <svg className="w-7 h-7 text-green-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="text-center py-4 px-4">
                    <svg className="w-7 h-7 text-green-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="text-center py-4 px-4">
                    <svg className="w-6 h-6 text-red-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </td>
                  <td className="text-center py-4 px-4">
                    <svg className="w-6 h-6 text-red-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </td>
                  <td className="text-center py-4 px-4">
                    <svg className="w-6 h-6 text-red-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </td>
                </tr>

                {/* Middle Finder */}
                <tr className="border-b border-slate-700/50 hover:bg-slate-700/20">
                  <td className="py-4 px-4 text-slate-100 text-base">Middle Finder</td>
                  <td className="text-center py-4 px-4 bg-blue-900/10">
                    <svg className="w-7 h-7 text-green-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="text-center py-4 px-4">
                    <svg className="w-6 h-6 text-red-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </td>
                  <td className="text-center py-4 px-4">
                    <svg className="w-6 h-6 text-red-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </td>
                  <td className="text-center py-4 px-4">
                    <svg className="w-6 h-6 text-red-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </td>
                  <td className="text-center py-4 px-4">
                    <svg className="w-6 h-6 text-red-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </td>
                </tr>

                {/* Steam Move Alerts */}
                <tr className="border-b border-slate-700/50 hover:bg-slate-700/20">
                  <td className="py-4 px-4 text-slate-100 text-base">Steam Move Alerts (Real-time)</td>
                  <td className="text-center py-4 px-4 bg-blue-900/10">
                    <svg className="w-7 h-7 text-green-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="text-center py-4 px-4">
                    <span className="text-sm text-slate-300">Limited</span>
                  </td>
                  <td className="text-center py-4 px-4">
                    <svg className="w-7 h-7 text-green-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="text-center py-4 px-4">
                    <span className="text-sm text-slate-300">Limited</span>
                  </td>
                  <td className="text-center py-4 px-4">
                    <svg className="w-6 h-6 text-red-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </td>
                </tr>

                {/* Advanced Analytics */}
                <tr className="border-b border-slate-700/50 hover:bg-slate-700/20">
                  <td className="py-4 px-4 text-slate-100 text-base">Advanced Analytics Dashboard</td>
                  <td className="text-center py-4 px-4 bg-blue-900/10">
                    <svg className="w-7 h-7 text-green-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="text-center py-4 px-4">
                    <span className="text-sm text-slate-300">Basic</span>
                  </td>
                  <td className="text-center py-4 px-4">
                    <svg className="w-7 h-7 text-green-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="text-center py-4 px-4">
                    <svg className="w-7 h-7 text-green-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="text-center py-4 px-4">
                    <span className="text-sm text-slate-300">Basic</span>
                  </td>
                </tr>

                {/* ROI Tracking */}
                <tr className="border-b border-slate-700/50 hover:bg-slate-700/20">
                  <td className="py-4 px-4 text-slate-100 text-base">ROI & CLV Tracking (Unlimited)</td>
                  <td className="text-center py-4 px-4 bg-blue-900/10">
                    <svg className="w-7 h-7 text-green-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="text-center py-4 px-4">
                    <span className="text-sm text-slate-300">Limited</span>
                  </td>
                  <td className="text-center py-4 px-4">
                    <svg className="w-7 h-7 text-green-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="text-center py-4 px-4">
                    <svg className="w-6 h-6 text-red-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </td>
                  <td className="text-center py-4 px-4">
                    <span className="text-sm text-slate-300">Limited</span>
                  </td>
                </tr>

                {/* Historical Data */}
                <tr className="border-b border-slate-700/50 hover:bg-slate-700/20">
                  <td className="py-4 px-4 text-slate-100 text-base">Historical Line Data</td>
                  <td className="text-center py-4 px-4 bg-blue-900/10">
                    <span className="text-green-400 font-bold text-lg">90 days</span>
                  </td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">30 days</td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">14 days</td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">30 days</td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">7 days</td>
                </tr>

                {/* Betting Strategies */}
                <tr className="hover:bg-slate-700/20">
                  <td className="py-4 px-4 text-slate-100 text-base">Pre-Built Betting Strategies</td>
                  <td className="text-center py-4 px-4 bg-blue-900/10">
                    <span className="text-green-400 font-bold text-lg">20+</span>
                  </td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">5</td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">8</td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">12</td>
                  <td className="text-center py-4 px-4 text-slate-200 text-base">3</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Value Proposition Callout */}
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-green-900/30 border-2 border-green-600 rounded-xl p-6 text-center">
              <div className="text-3xl font-bold text-green-400 mb-2">$20-70</div>
              <div className="text-sm text-green-300 font-semibold">CHEAPER per month than competitors</div>
              <div className="text-xs text-slate-400 mt-2">Same tier features at lower cost</div>
            </div>
            <div className="bg-blue-900/30 border-2 border-blue-600 rounded-xl p-6 text-center">
              <div className="text-3xl font-bold text-blue-400 mb-2">50-75%</div>
              <div className="text-sm text-blue-300 font-semibold">MORE sportsbooks tracked</div>
              <div className="text-xs text-slate-400 mt-2">60+ vs 20-40 for competitors</div>
            </div>
            <div className="bg-purple-900/30 border-2 border-purple-600 rounded-xl p-6 text-center">
              <div className="text-3xl font-bold text-purple-400 mb-2">10-100x</div>
              <div className="text-sm text-purple-300 font-semibold">FASTER data refresh</div>
              <div className="text-xs text-slate-400 mt-2">Sub-1s WebSocket vs 5-60s polling</div>
            </div>
          </div>

          {/* Bottom CTA */}
          <div className="mt-8 text-center">
            <p className="text-lg text-slate-300 mb-4">
              <span className="font-bold text-blue-400">Bottom Line:</span> Get more features, faster data, and better support — all for less money.
            </p>
            <p className="text-sm text-slate-400">
              Our Semi Pro tier at $79/mo beats OddsJam Premium ($99), Unabated Elite ($99), and BetQL Premium ($49) on every metric that matters.
            </p>
          </div>
        </div>

        {/* Feature Comparison Table */}
        <div className="mb-16">
          <div className="text-center mb-6">
            <button
              onClick={() => setShowFeatureComparison(!showFeatureComparison)}
              className="inline-flex items-center gap-3 px-8 py-4 bg-slate-800/70 hover:bg-slate-800 border border-slate-600 hover:border-blue-500 rounded-xl transition-all group"
            >
              <span className="text-lg font-semibold text-slate-100">
                {showFeatureComparison ? 'Hide' : 'Show'} Detailed Feature Comparison
              </span>
              <svg
                className={`w-5 h-5 text-slate-400 transition-transform ${showFeatureComparison ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>

          {showFeatureComparison && (
            <div className="bg-slate-800/30 border border-slate-700 rounded-2xl p-6 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-600">
                    <th className="text-left py-4 px-4 text-slate-300 font-bold">Tier</th>
                    <th className="text-left py-4 px-4 text-slate-300 font-bold">Price</th>
                    <th className="text-left py-4 px-4 text-slate-300 font-bold">Data Source / Speed</th>
                    <th className="text-left py-4 px-4 text-slate-300 font-bold">Key Features Unlocked</th>
                    <th className="text-left py-4 px-4 text-slate-300 font-bold">Not Included</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Trial Tier */}
                  <tr className="border-b border-slate-700/50 hover:bg-slate-700/20">
                    <td className="py-4 px-4">
                      <span className="font-bold text-slate-100">Trial</span>
                    </td>
                    <td className="py-4 px-4 text-slate-300">$0</td>
                    <td className="py-4 px-4 text-slate-300 text-xs">
                      The Odds API Free<br />
                      <span className="text-slate-500">(45-60s polling)</span>
                    </td>
                    <td className="py-4 px-4 text-slate-300 text-xs">
                      Basic odds (60+ books), totals, lines, NFL/NBA/NHL/NCAAF/NCAAB, Basic Bet Tracker, 15s updates, 5 strategies
                    </td>
                    <td className="py-4 px-4 text-slate-400 text-xs">
                      ML, props, injuries, historical, push alerts
                    </td>
                  </tr>

                  {/* Starter Tier */}
                  <tr className="border-b border-slate-700/50 hover:bg-slate-700/20">
                    <td className="py-4 px-4">
                      <span className="font-bold text-green-400">Starter</span>
                    </td>
                    <td className="py-4 px-4 text-slate-300">$19.99/mo</td>
                    <td className="py-4 px-4 text-slate-300 text-xs">
                      The Odds API Starter<br />
                      <span className="text-slate-500">(30-45s polling)</span>
                    </td>
                    <td className="py-4 px-4 text-slate-300 text-xs">
                      Trial + EV/No-Vig Calc, line tracker, all sports, 10s refresh, Advanced Bet Tracker (100 bets/mo), Email Notifications, 7-day historical, 10 strategies
                    </td>
                    <td className="py-4 px-4 text-slate-400 text-xs">
                      Advanced ML, props, sub-1s alerts
                    </td>
                  </tr>

                  {/* Semi Pro Tier */}
                  <tr className="border-b border-slate-700/50 hover:bg-slate-700/20 bg-blue-900/10">
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-blue-400">Semi Pro</span>
                        <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full">Most Popular</span>
                      </div>
                    </td>
                    <td className="py-4 px-4 text-slate-300">$59.99/mo</td>
                    <td className="py-4 px-4 text-slate-300 text-xs">
                      SportsGameOdds<br />
                      <span className="text-slate-500">(&lt;1s WebSocket option)</span>
                    </td>
                    <td className="py-4 px-4 text-slate-300 text-xs">
                      Starter + Advanced Analytics Dashboard, steam alerts (&lt;1s), arbitrage/middle finder, consensus line, 20 strategies, full Kelly, 15 articles
                    </td>
                    <td className="py-4 px-4 text-slate-400 text-xs">
                      Full props, injuries, dedicated API
                    </td>
                  </tr>

                  {/* Professional Tier */}
                  <tr className="border-b border-slate-700/50 hover:bg-slate-700/20">
                    <td className="py-4 px-4">
                      <span className="font-bold text-purple-400">Professional</span>
                    </td>
                    <td className="py-4 px-4 text-slate-300">$129.99/mo</td>
                    <td className="py-4 px-4 text-slate-300 text-xs">
                      OpticOdds<br />
                      <span className="text-slate-500">(Sub-30s WebSocket)</span>
                    </td>
                    <td className="py-4 px-4 text-slate-300 text-xs">
                      Semi Pro + Tech: OpticOdds API/Cloud ML/Redis/Sub-30s WebSocket, Browser Extension, props module, SGP builder, ML true odds, injury/weather alerts, 30+ strategies, 30+ articles
                    </td>
                    <td className="py-4 px-4 text-slate-400 text-xs">
                      Sub-50ms, offshore servers
                    </td>
                  </tr>

                  {/* Elite Tier */}
                  <tr className="border-b border-slate-700/50 hover:bg-slate-700/20">
                    <td className="py-4 px-4">
                      <span className="font-bold text-amber-400">Elite</span>
                    </td>
                    <td className="py-4 px-4 text-slate-300">$249.99/mo</td>
                    <td className="py-4 px-4 text-slate-300 text-xs">
                      Sportradar Full<br />
                      <span className="text-slate-500">(Sub-1s push)</span>
                    </td>
                    <td className="py-4 px-4 text-slate-300 text-xs">
                      Professional + Tech: Sportradar Full/GPU ML/PostgreSQL+Redis/Sub-1s, Browser Extension, Desktop Client, API access (10K calls/day), custom models, backtesting, ML arbitrage
                    </td>
                    <td className="py-4 px-4 text-slate-400 text-xs">
                      Sub-50ms, dedicated GPUs
                    </td>
                  </tr>

                  {/* Elite Pro Tier */}
                  <tr className="hover:bg-slate-700/20">
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-red-400">Elite Pro</span>
                        <span className="text-xs bg-red-500/20 text-red-300 px-2 py-0.5 rounded-full">Invite-only</span>
                      </div>
                    </td>
                    <td className="py-4 px-4 text-slate-300">$599.99/mo</td>
                    <td className="py-4 px-4 text-slate-300 text-xs">
                      Sportradar Elite<br />
                      <span className="text-slate-500">(Sub-50ms)</span>
                    </td>
                    <td className="py-4 px-4 text-slate-300 text-xs">
                      Elite + Tech: Sportradar Elite/Dedicated GPU/Distributed DB+Redis/Sub-50ms, Browser Extension, Enhanced Desktop Client (Win/Mac/Linux), direct sportsbook APIs, fastest AI, offshore servers, premium consultation
                    </td>
                    <td className="py-4 px-4 text-slate-400 text-xs">
                      Invite-only
                    </td>
                  </tr>
                </tbody>
              </table>

              {/* Additional Info */}
              <div className="mt-6 p-4 bg-blue-900/20 border border-blue-700/50 rounded-lg">
                <p className="text-xs text-blue-300">
                  <strong>💡 Pro Tip:</strong> Higher tiers use faster data sources giving you a competitive edge. Sub-second speeds are crucial for arbitrage and live betting opportunities.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* FAQs */}
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-slate-100 mb-8 text-center">
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            {faqs.map((faq, idx) => (
              <div key={idx} className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
                <h3 className="text-lg font-bold text-slate-100 mb-3">{faq.q}</h3>
                <p className="text-slate-300">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>

        {/* CTA Footer */}
        <div className="text-center mt-16 p-12 bg-gradient-to-br from-blue-900/30 to-purple-900/30 border border-blue-800 rounded-2xl">
          <h3 className="text-3xl font-bold text-slate-100 mb-4">
            Ready to start winning?
          </h3>
          <p className="text-lg text-slate-300 mb-8 max-w-2xl mx-auto">
            Join thousands of profitable bettors using our platform to gain an edge
          </p>
          <button className="px-12 py-4 bg-blue-600 hover:bg-blue-700 text-white text-lg font-bold rounded-lg transition-colors shadow-lg shadow-blue-600/30">
            Start Free Trial
          </button>
          <p className="text-sm text-slate-400 mt-4">No credit card required • Cancel anytime</p>
        </div>
      </div>
    </div>
  );
}
