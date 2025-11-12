import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiUrl } from '../config';

export function Partners() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    handle: '',
    followers: '',
    platform: 'twitter',
    niche: 'sports_betting'
  });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Calculate potential earnings based on followers
  const revenueProjection = useMemo(() => {
    const followers = parseInt(formData.followers) || 0;
    const conversionRate = 0.02; // 2% conversion rate (conservative)
    const avgSubscription = 99; // Average $99/month plan
    const commission = 0.25; // 25% commission

    const expectedSignups = Math.floor(followers * conversionRate);
    const monthlyRevenue = expectedSignups * avgSubscription * commission;
    const yearlyRevenue = monthlyRevenue * 12;

    return {
      signups: expectedSignups,
      monthly: monthlyRevenue,
      yearly: yearlyRevenue
    };
  }, [formData.followers]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(getApiUrl('influencer/apply'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        setSubmitted(true);
        // Redirect to signup with pre-filled email and partner flag
        setTimeout(() => {
          navigate(`/signup?email=${encodeURIComponent(formData.email)}&partner=true&code=${data.referral_code}`);
        }, 2000);
      } else {
        throw new Error(data.message || 'Failed to submit application');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center p-4">
        <div className="max-w-2xl w-full bg-gradient-to-br from-green-600 to-green-900 rounded-xl shadow-2xl p-12 text-center border-4 border-green-500 animate-pulse">
          <div className="text-6xl mb-6">🔥</div>
          <h2 className="text-4xl font-bold text-white mb-4">PARTNER APPROVED!</h2>
          <p className="text-green-100 text-xl mb-6">
            Redirecting to complete setup...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black py-8 px-4 overflow-hidden relative">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 via-black to-green-900/20"></div>
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl"></div>
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-green-600/10 rounded-full blur-3xl"></div>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Logo + Header */}
        <div className="text-center mb-12">
          <img
            src="/logo2.png"
            alt="Max EV Sports"
            className="mx-auto h-48 w-auto mb-8 drop-shadow-[0_0_30px_rgba(59,130,246,0.6)]"
          />
          <h1 className="text-6xl md:text-7xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-green-400 to-blue-400 mb-4 tracking-tight">
            PARTNER PROGRAM
          </h1>
          <p className="text-2xl text-slate-400 font-bold">
            Turn Your Audience Into <span className="text-green-400">Recurring Revenue</span>
          </p>
        </div>

        {/* Revenue Calculator - Front and Center */}
        <div className="max-w-4xl mx-auto mb-12">
          <div className="bg-gradient-to-br from-slate-900 to-black border-4 border-blue-500 rounded-2xl p-8 shadow-2xl">
            <h2 className="text-3xl font-bold text-white mb-6 text-center">
              💰 REVENUE CALCULATOR
            </h2>

            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <div className="text-center">
                <div className="text-5xl font-black text-green-400 mb-2">
                  ${revenueProjection.monthly.toLocaleString()}
                </div>
                <div className="text-sm text-slate-400 uppercase tracking-wider">Monthly Income</div>
              </div>

              <div className="text-center">
                <div className="text-5xl font-black text-blue-400 mb-2">
                  ${revenueProjection.yearly.toLocaleString()}
                </div>
                <div className="text-sm text-slate-400 uppercase tracking-wider">Yearly Income</div>
              </div>

              <div className="text-center">
                <div className="text-5xl font-black text-purple-400 mb-2">
                  {revenueProjection.signups}
                </div>
                <div className="text-sm text-slate-400 uppercase tracking-wider">Expected Signups</div>
              </div>
            </div>

            <div className="bg-slate-950/50 rounded-lg p-4 border-2 border-slate-800">
              <div className="text-xs text-slate-500 mb-2 uppercase tracking-wide">Based on 2% conversion rate • 25% commission</div>
              <div className="grid grid-cols-3 gap-4 text-center text-xs text-slate-400">
                <div>
                  <span className="text-green-400 font-bold">✓</span> Recurring Monthly
                </div>
                <div>
                  <span className="text-blue-400 font-bold">✓</span> Free Elite Access ($199/mo)
                </div>
                <div>
                  <span className="text-purple-400 font-bold">✓</span> Real-Time Dashboard
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Application Form */}
        <div className="max-w-3xl mx-auto bg-gradient-to-br from-slate-900 to-black border-4 border-green-500 rounded-2xl p-10 shadow-2xl">
          <h2 className="text-4xl font-black text-center mb-2 text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-400">
            START EARNING TODAY
          </h2>
          <p className="text-center text-slate-400 mb-8">Fill out the form below to get instant access</p>

          {error && (
            <div className="bg-red-900/50 border-2 border-red-500 rounded-lg p-4 mb-6 text-red-200 font-bold">
              ⚠️ {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid md:grid-cols-2 gap-5">
              <div>
                <label className="block text-blue-400 font-bold mb-2 uppercase text-sm tracking-wider">Full Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full px-4 py-3 bg-black text-white border-2 border-blue-600 rounded-lg focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 transition-all"
                  placeholder="John Doe"
                />
              </div>

              <div>
                <label className="block text-blue-400 font-bold mb-2 uppercase text-sm tracking-wider">Email</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full px-4 py-3 bg-black text-white border-2 border-blue-600 rounded-lg focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 transition-all"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-5">
              <div>
                <label className="block text-blue-400 font-bold mb-2 uppercase text-sm tracking-wider">X/Twitter Handle</label>
                <input
                  type="text"
                  required
                  value={formData.handle}
                  onChange={(e) => setFormData({...formData, handle: e.target.value})}
                  className="w-full px-4 py-3 bg-black text-white border-2 border-blue-600 rounded-lg focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 transition-all"
                  placeholder="@yourusername"
                />
              </div>

              <div>
                <label className="block text-blue-400 font-bold mb-2 uppercase text-sm tracking-wider">
                  Followers {formData.followers && <span className="text-green-400">• ${revenueProjection.monthly.toLocaleString()}/mo</span>}
                </label>
                <input
                  type="number"
                  required
                  value={formData.followers}
                  onChange={(e) => setFormData({...formData, followers: e.target.value})}
                  className="w-full px-4 py-3 bg-black text-white border-2 border-blue-600 rounded-lg focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 transition-all"
                  placeholder="10000"
                />
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-5">
              <div>
                <label className="block text-blue-400 font-bold mb-2 uppercase text-sm tracking-wider">Platform</label>
                <select
                  value={formData.platform}
                  onChange={(e) => setFormData({...formData, platform: e.target.value})}
                  className="w-full px-4 py-3 bg-black text-white border-2 border-blue-600 rounded-lg focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 transition-all"
                >
                  <option value="twitter">Twitter/X</option>
                  <option value="youtube">YouTube</option>
                  <option value="tiktok">TikTok</option>
                  <option value="instagram">Instagram</option>
                  <option value="twitch">Twitch</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-blue-400 font-bold mb-2 uppercase text-sm tracking-wider">Niche</label>
                <select
                  value={formData.niche}
                  onChange={(e) => setFormData({...formData, niche: e.target.value})}
                  className="w-full px-4 py-3 bg-black text-white border-2 border-blue-600 rounded-lg focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 transition-all"
                >
                  <option value="sports_betting">Sports Betting</option>
                  <option value="nba">NBA</option>
                  <option value="nfl">NFL</option>
                  <option value="nhl">NHL</option>
                  <option value="mlb">MLB</option>
                  <option value="ncaa">NCAA</option>
                  <option value="fantasy_sports">Fantasy Sports</option>
                  <option value="sports_analytics">Sports Analytics</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-green-600 via-green-500 to-blue-600 hover:from-green-500 hover:via-green-600 hover:to-blue-500 text-white font-black py-5 px-8 rounded-xl transition-all border-2 border-green-400 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-green-500/50 text-xl uppercase tracking-wider"
            >
              {loading ? '⏳ Processing...' : '🚀 Become a Partner'}
            </button>
          </form>

          <p className="text-slate-500 text-xs text-center mt-6">
            Instant approval • No minimum followers • Start earning immediately
          </p>
        </div>

        {/* Why Partner With Us */}
        <div className="mt-16 max-w-5xl mx-auto">
          <h2 className="text-5xl font-black text-center mb-12 text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-400">
            WHY MAX EV SPORTS?
          </h2>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-gradient-to-br from-green-900/50 to-black border-2 border-green-600 rounded-xl p-6 hover:border-green-400 transition-all">
              <div className="text-4xl mb-4">💵</div>
              <h3 className="text-2xl font-bold text-green-400 mb-3">Highest Payouts</h3>
              <p className="text-slate-300">
                25% recurring commission - one of the highest in the industry. Average partners earn $500-2k/month.
              </p>
            </div>

            <div className="bg-gradient-to-br from-blue-900/50 to-black border-2 border-blue-600 rounded-xl p-6 hover:border-blue-400 transition-all">
              <div className="text-4xl mb-4">🎯</div>
              <h3 className="text-2xl font-bold text-blue-400 mb-3">Premium Product</h3>
              <p className="text-slate-300">
                Elite sports betting analytics that actually work. High retention = recurring income for life.
              </p>
            </div>

            <div className="bg-gradient-to-br from-purple-900/50 to-black border-2 border-purple-600 rounded-xl p-6 hover:border-purple-400 transition-all">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-2xl font-bold text-purple-400 mb-3">Real-Time Portal</h3>
              <p className="text-slate-300">
                Track every click, signup, and dollar earned. Full transparency with instant payout reports.
              </p>
            </div>
          </div>

          {/* Bottom CTA */}
          <div className="mt-12 text-center bg-gradient-to-r from-green-600/20 to-blue-600/20 border-2 border-green-500 rounded-xl p-8">
            <p className="text-slate-300 text-lg mb-4">
              Questions? Email us at <a href="mailto:partners@max-ev-sports.com" className="text-green-400 font-bold hover:text-green-300">partners@max-ev-sports.com</a>
            </p>
            <p className="text-slate-500 text-sm">
              Instant approval • No hidden fees • Paid monthly via PayPal or bank transfer
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
