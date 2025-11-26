import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiUrl } from '../config';
import { PartnerImageSlider } from '../components/PartnerImageSlider';

export function Partners() {
  const navigate = useNavigate();
  const [followerCount, setFollowerCount] = useState(10000);
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
    const followers = followerCount;
    const conversionRate = 0.02; // 2% conversion rate (conservative)
    const avgSubscription = 19.99; // Average $19.99/month plan
    const commission = 0.25; // 25% commission (25% of user's monthly subscription)

    const expectedSignups = Math.floor(followers * conversionRate);
    const monthlyRevenue = expectedSignups * avgSubscription * commission;
    const yearlyRevenue = monthlyRevenue * 12;

    return {
      signups: expectedSignups,
      monthly: monthlyRevenue,
      yearly: yearlyRevenue
    };
  }, [followerCount]);

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
      <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black flex items-center justify-center p-4" style={{ fontFamily: 'Rubik, sans-serif' }}>
        <div className="max-w-2xl w-full bg-slate-800/50 border-2 border-green-600 rounded-lg p-12 text-center">
          <h2 className="text-4xl font-bold italic text-green-400 mb-4" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>PARTNER APPROVED</h2>
          <p className="text-slate-300 text-xl mb-6">
            Redirecting to complete setup...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black py-8 px-4" style={{ fontFamily: 'Rubik, sans-serif' }}>
      <div className="max-w-7xl mx-auto">
        {/* Logo + Header */}
        <div className="text-center mb-12">
          <img
            src="/logo2.png"
            alt="Max EV Sports"
            className="mx-auto h-48 w-auto mb-8"
          />
          <h1 className="text-5xl md:text-6xl font-bold italic text-slate-100 mb-4" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>
            PARTNER PROGRAM
          </h1>
          <p className="text-xl text-slate-400">
            Turn Your Audience Into Recurring Revenue
          </p>
        </div>

        {/* Revenue Calculator - Front and Center */}
        <div className="max-w-4xl mx-auto mb-12">
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-8">
            <h2 className="text-3xl font-bold italic text-slate-100 mb-6 text-center" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>
              REVENUE CALCULATOR
            </h2>

            {/* Interactive Slider */}
            <div className="mb-8">
              <label className="block text-lg font-medium text-slate-300 mb-4 text-center">
                Adjust Your Follower Count: <span className="text-blue-400 font-bold">{followerCount.toLocaleString()}</span>
              </label>
              <input
                type="range"
                min="1000"
                max="500000"
                step="1000"
                value={followerCount}
                onChange={(e) => setFollowerCount(parseInt(e.target.value))}
                className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((followerCount - 1000) / (500000 - 1000)) * 100}%, #334155 ${((followerCount - 1000) / (500000 - 1000)) * 100}%, #334155 100%)`
                }}
              />
              <div className="flex justify-between text-xs text-slate-500 mt-2">
                <span>1,000</span>
                <span>500,000</span>
              </div>
            </div>

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

            <div className="bg-black/40 rounded-lg p-4 border border-slate-700">
              <div className="text-sm text-slate-400 mb-2 text-center font-semibold">
                Calculations based on average user subscription at <span className="text-green-400">$19.99/month</span>
              </div>
              <div className="text-xs text-slate-500 mb-2 uppercase tracking-wide text-center">2% conversion rate • 25% commission per subscriber</div>
              <div className="grid grid-cols-3 gap-4 text-center text-xs text-slate-400">
                <div>Recurring Monthly</div>
                <div>Free Elite Access ($199/mo)</div>
                <div>Real-Time Dashboard</div>
              </div>
            </div>
          </div>
        </div>

        {/* Partner Dashboard Preview */}
        <div className="max-w-4xl mx-auto mb-12">
          <h2 className="text-3xl font-bold italic text-slate-100 mb-6 text-center" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>
            YOUR PARTNER PORTAL
          </h2>
          <PartnerImageSlider />
        </div>

        {/* Application Form */}
        <div className="max-w-3xl mx-auto bg-slate-800/50 border border-slate-700 rounded-lg p-10">
          <h2 className="text-3xl font-bold italic text-slate-100 text-center mb-2" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>
            START EARNING TODAY
          </h2>
          <p className="text-center text-slate-400 mb-8">Fill out the form below to get instant access</p>

          {error && (
            <div className="bg-red-900/50 border border-red-500 rounded-lg p-4 mb-6 text-red-200 font-bold">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid md:grid-cols-2 gap-5">
              <div>
                <label className="block text-slate-300 font-medium mb-2 text-sm">Full Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full px-4 py-3 bg-black text-white border border-slate-600 rounded-lg focus:border-blue-500 focus:outline-none transition-all"
                  placeholder="John Doe"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-2 text-sm">Email</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full px-4 py-3 bg-black text-white border border-slate-600 rounded-lg focus:border-blue-500 focus:outline-none transition-all"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-5">
              <div>
                <label className="block text-slate-300 font-medium mb-2 text-sm">X/Twitter Handle</label>
                <input
                  type="text"
                  required
                  value={formData.handle}
                  onChange={(e) => setFormData({...formData, handle: e.target.value})}
                  className="w-full px-4 py-3 bg-black text-white border border-slate-600 rounded-lg focus:border-blue-500 focus:outline-none transition-all"
                  placeholder="@yourusername"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-2 text-sm">Followers</label>
                <input
                  type="number"
                  required
                  value={formData.followers}
                  onChange={(e) => setFormData({...formData, followers: e.target.value})}
                  className="w-full px-4 py-3 bg-black text-white border border-slate-600 rounded-lg focus:border-blue-500 focus:outline-none transition-all"
                  placeholder="10000"
                />
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-5">
              <div>
                <label className="block text-slate-300 font-medium mb-2 text-sm">Platform</label>
                <select
                  value={formData.platform}
                  onChange={(e) => setFormData({...formData, platform: e.target.value})}
                  className="w-full px-4 py-3 bg-black text-white border border-slate-600 rounded-lg focus:border-blue-500 focus:outline-none transition-all"
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
                <label className="block text-slate-300 font-medium mb-2 text-sm">Niche</label>
                <select
                  value={formData.niche}
                  onChange={(e) => setFormData({...formData, niche: e.target.value})}
                  className="w-full px-4 py-3 bg-black text-white border border-slate-600 rounded-lg focus:border-blue-500 focus:outline-none transition-all"
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
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 px-8 rounded-lg transition-all border border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-lg uppercase"
            >
              {loading ? 'Processing...' : 'Become a Partner'}
            </button>
          </form>

          <p className="text-slate-500 text-xs text-center mt-6">
            Instant approval • No minimum followers • Start earning immediately
          </p>
        </div>

        {/* Why Partner With Us */}
        <div className="mt-16 max-w-5xl mx-auto">
          <h2 className="text-4xl font-bold italic text-slate-100 text-center mb-12" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>
            WHY MAX EV SPORTS?
          </h2>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 hover:border-green-500 transition-all">
              <h3 className="text-xl font-bold text-green-400 mb-3">Highest Payouts</h3>
              <p className="text-slate-300">
                25% recurring commission - one of the highest in the industry. Average partners earn $500-2k/month.
              </p>
            </div>

            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 hover:border-blue-500 transition-all">
              <h3 className="text-xl font-bold text-blue-400 mb-3">Premium Product</h3>
              <p className="text-slate-300">
                Elite sports betting analytics that actually work. High retention = recurring income for life.
              </p>
            </div>

            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 hover:border-purple-500 transition-all">
              <h3 className="text-xl font-bold text-purple-400 mb-3">Real-Time Portal</h3>
              <p className="text-slate-300">
                Track every click, signup, and dollar earned. Full transparency with instant payout reports.
              </p>
            </div>
          </div>

          {/* Bottom CTA */}
          <div className="mt-12 text-center bg-slate-800/50 border border-slate-700 rounded-lg p-8">
            <p className="text-slate-300 text-lg mb-4">
              Questions? Email us at <a href="mailto:partners@max-ev-sports.com" className="text-blue-400 font-bold hover:text-blue-300">partners@max-ev-sports.com</a>
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
