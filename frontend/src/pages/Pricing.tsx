import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export function Pricing() {
  const { username, isAuthenticated } = useAuth();
  const [loading, setLoading] = useState<string | null>(null);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');

  // Stripe Price IDs (from backend .env)
  const STRIPE_PRICE_IDS = {
    pro: 'price_1QR5WiGp5HWb2tPk7YVf5xHa',
    elite: 'price_1QR5WrGp5HWb2tPkZtZGc4rL',
  };

  const handleSubscribe = async (tier: 'pro' | 'elite') => {
    if (!isAuthenticated || !username) {
      alert('Please log in to subscribe');
      return;
    }

    setLoading(tier);

    try {
      const response = await fetch('http://localhost:8000/api/stripe/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          price_id: STRIPE_PRICE_IDS[tier],
          user_id: username,
          user_email: `${username}@example.com`, // Replace with actual email from user profile
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
      name: 'Free',
      price: 0,
      period: 'forever',
      description: 'Perfect for getting started with sports betting analytics',
      edge: '0-1%',
      edgeColor: 'slate',
      features: [
        'Live game odds from 10+ books',
        'Basic totals projections',
        'Real-time line updates',
        'NFL, NBA, NHL, NCAAF coverage',
        'Game momentum tracking',
        '5-second refresh rate',
        'Community Discord access',
      ],
      limitations: [
        'No advanced tools',
        'No bet tracking',
        'No props',
        'No historical data',
        'Limited sports coverage',
      ],
      cta: 'Get Started',
      popular: false,
      color: 'slate',
      annualPrice: null,
    },
    {
      name: 'Starter',
      price: 29,
      period: 'month',
      description: 'Essential tools for recreational bettors',
      edge: '2-4%',
      edgeColor: 'green',
      features: [
        'Everything in Free, plus:',
        'No-Vig Calculator',
        'Expected Value Calculator',
        'Basic Line Movement Tracker',
        'All major sports coverage',
        '2-second refresh rate',
        'Historical data (7 days)',
        'Email alerts',
        'Bet tracking (up to 50 bets/month)',
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
      name: 'Pro',
      price: 79,
      period: 'month',
      description: 'For serious bettors who want every edge',
      edge: '4-6%',
      edgeColor: 'blue',
      features: [
        'Everything in Starter, plus:',
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
        'Bankroll management tools',
      ],
      limitations: [],
      cta: 'Start 7-Day Trial',
      popular: true,
      color: 'blue',
      annualPrice: 758,
      annualSavings: 190,
    },
    {
      name: 'Elite',
      price: 149,
      period: 'month',
      description: 'Maximum firepower for sharp bettors',
      edge: '6-8%',
      edgeColor: 'purple',
      features: [
        'Everything in Pro, plus:',
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
      name: 'Professional',
      price: 299,
      period: 'month',
      description: 'For syndicates and professional operations',
      edge: '8-10%',
      edgeColor: 'amber',
      features: [
        'Everything in Elite, plus:',
        'Full API access (unlimited calls)',
        'Multi-user accounts (up to 10 seats)',
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
        'Everything in Professional, plus:',
        'Offshore server access (millisecond advantage)',
        'Direct sportsbook API connections',
        'Fastest AI prediction engine',
        'Real-time ML model updates',
        'Geographically distributed servers',
        'Sub-50ms line detection',
        'Dedicated GPU processing',
        'Proprietary sharp action alerts',
        'Private syndicate data feeds',
        'Unlimited seats (up to 25 users)',
        'Personal trading desk support',
        'Custom algorithm development',
        'Institutional-grade infrastructure',
        'Reserved server capacity',
        'VIP hotline (direct access)',
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
      a: 'Yes! Save 20% when you pay annually. Pro: $470/year (save $118), Elite: $950/year (save $238)'
    },
    {
      q: 'Do you have an API?',
      a: 'API access is included with Elite plans. Pro users can add API access for $20/month.'
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

          <div className="inline-flex items-center gap-3 bg-green-900/30 border border-green-700 rounded-lg px-6 py-3">
            <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
            </svg>
            <span className="text-green-300 font-semibold">
              Launch Special: 50% OFF first 3 months with code LAUNCH50
            </span>
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

                <div className="flex items-baseline justify-center gap-1 mb-1">
                  {billingCycle === 'monthly' ? (
                    <>
                      <span className="text-3xl font-bold text-slate-100">${plan.price}</span>
                      {plan.price > 0 && (
                        <span className="text-slate-400 text-xs">/ month</span>
                      )}
                    </>
                  ) : (
                    <>
                      {plan.annualPrice ? (
                        <>
                          <span className="text-3xl font-bold text-slate-100">${plan.annualPrice}</span>
                          <span className="text-slate-400 text-xs">/ year</span>
                        </>
                      ) : (
                        <span className="text-3xl font-bold text-slate-100">Free</span>
                      )}
                    </>
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
                  if (plan.name === 'Pro') {
                    handleSubscribe('pro');
                  } else if (plan.name === 'Elite') {
                    handleSubscribe('elite');
                  } else {
                    alert(`${plan.name} tier coming soon!`);
                  }
                }}
                disabled={loading === 'pro' || loading === 'elite'}
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
                {plan.features.slice(0, 8).map((feature, idx) => (
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
                  <div className="text-xs text-blue-400 font-semibold pt-1">
                    + {plan.features.length - 8} more features
                  </div>
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-bold text-slate-100 mb-2">API Access</h3>
              <div className="text-3xl font-bold text-slate-100 mb-3">$29<span className="text-sm text-slate-400">/month</span></div>
              <p className="text-sm text-slate-300 mb-4">Full REST API access for custom integrations. Included free with Professional tier.</p>
              <ul className="space-y-2 text-xs text-slate-400">
                <li>• 10,000 requests/day</li>
                <li>• Real-time odds data</li>
                <li>• Historical data access</li>
                <li>• Webhook support</li>
              </ul>
            </div>
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-bold text-slate-100 mb-2">Additional Seats</h3>
              <div className="text-3xl font-bold text-slate-100 mb-3">$49<span className="text-sm text-slate-400">/seat/month</span></div>
              <p className="text-sm text-slate-300 mb-4">Add team members to your Professional account.</p>
              <ul className="space-y-2 text-xs text-slate-400">
                <li>• Shared workspace</li>
                <li>• Individual logins</li>
                <li>• Role-based permissions</li>
                <li>• Activity tracking</li>
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
            <div className="text-2xl font-bold text-slate-100 mb-1">10+</div>
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
