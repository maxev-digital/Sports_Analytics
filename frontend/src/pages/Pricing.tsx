export function Pricing() {
  const plans = [
    {
      name: 'Free',
      price: 0,
      period: 'forever',
      description: 'Perfect for getting started with sports betting analytics',
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
      ],
      cta: 'Get Started',
      popular: false,
      color: 'slate'
    },
    {
      name: 'Pro',
      price: 49,
      period: 'month',
      description: 'For serious bettors who want every edge',
      features: [
        'Everything in Free, plus:',
        'No-Vig Calculator',
        'Expected Value Calculator',
        'Line Movement Tracker',
        'Steam Move Alerts',
        'Market Consensus Line',
        'Arbitrage Finder',
        'Bet Tracking & ROI Dashboard',
        'CLV Tracker',
        'All sports (NFL, NBA, NHL, MLB, PGA, ATP, MMA, WNBA, NASCAR)',
        '1-second refresh rate',
        'Historical line data (30 days)',
        'Export data to CSV',
        'Email alerts',
      ],
      limitations: [],
      cta: 'Start 7-Day Trial',
      popular: true,
      color: 'blue'
    },
    {
      name: 'Elite',
      price: 99,
      period: 'month',
      description: 'Maximum firepower for professional bettors',
      features: [
        'Everything in Pro, plus:',
        'Player Props Module',
        'SGP Builder with correlation',
        'PrizePicks/Underdog comparison',
        'Advanced projection models',
        'Weather impact analysis',
        'Injury/news alerts',
        'Kelly Criterion optimizer',
        'Hedge calculator',
        'Derivative markets calculator',
        'Historical line data (unlimited)',
        'API access',
        'Priority support',
        'Custom alerts & notifications',
        'White-label reporting',
      ],
      limitations: [],
      cta: 'Start 7-Day Trial',
      popular: false,
      color: 'purple'
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-slate-100 mb-4">
            Choose Your Plan
          </h1>
          <p className="text-xl text-slate-300 mb-6">
            Get the tools you need to win at sports betting
          </p>
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
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-16">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative bg-slate-800/50 backdrop-blur-sm border rounded-2xl p-8 ${
                plan.popular
                  ? 'border-blue-500 shadow-2xl shadow-blue-500/20 scale-105'
                  : 'border-slate-700'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <div className="bg-gradient-to-r from-blue-600 to-blue-400 text-white text-sm font-bold px-6 py-2 rounded-full shadow-lg">
                    MOST POPULAR
                  </div>
                </div>
              )}

              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-slate-100 mb-2">{plan.name}</h3>
                <div className="flex items-baseline justify-center gap-2 mb-3">
                  <span className="text-5xl font-bold text-slate-100">${plan.price}</span>
                  {plan.price > 0 && (
                    <span className="text-slate-400">/ {plan.period}</span>
                  )}
                </div>
                <p className="text-sm text-slate-400">{plan.description}</p>
              </div>

              <button
                className={`w-full py-4 rounded-lg font-bold text-lg mb-8 transition-all ${
                  plan.popular
                    ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-600/30'
                    : plan.color === 'purple'
                    ? 'bg-purple-600 hover:bg-purple-700 text-white'
                    : 'bg-slate-700 hover:bg-slate-600 text-slate-200'
                }`}
              >
                {plan.cta}
              </button>

              <div className="space-y-4">
                <div className="font-semibold text-slate-200 mb-3">Features:</div>
                {plan.features.map((feature, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className={`text-sm ${feature.startsWith('Everything in') ? 'font-semibold text-slate-200' : 'text-slate-300'}`}>
                      {feature}
                    </span>
                  </div>
                ))}

                {plan.limitations.length > 0 && (
                  <div className="pt-4 mt-4 border-t border-slate-700">
                    <div className="font-semibold text-slate-400 mb-3 text-sm">Not included:</div>
                    {plan.limitations.map((limit, idx) => (
                      <div key={idx} className="flex items-start gap-3">
                        <svg className="w-5 h-5 text-slate-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                        <span className="text-sm text-slate-500">{limit}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
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
