import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiUrl } from '../config';

interface Influencer {
  username: string;
  referral_code: string;
  full_name: string;
  email: string;
  social_media_handle: string;
  platform: string;
  follower_count: number;
  total_referrals: number;
}

interface Referral {
  referred_username: string;
  subscription_tier: string;
  signup_date: string;
  status: string;
  monthly_commission: number;
}

interface Earnings {
  total_monthly_commission: number;
  active_referrals: number;
  total_referrals: number;
  annual_projection: number;
  breakdown_by_tier: {
    [tier: string]: {
      count: number;
      commission: number;
    };
  };
}

export function InfluencerDashboard() {
  const [influencer, setInfluencer] = useState<Influencer | null>(null);
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [earnings, setEarnings] = useState<Earnings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    const token = localStorage.getItem('influencer_token');
    if (!token) {
      navigate('/influencer-login');
      return;
    }

    try {
      const response = await fetch(getApiUrl('/influencer/dashboard'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        localStorage.removeItem('influencer_token');
        navigate('/influencer-login');
        return;
      }

      const data = await response.json();

      if (data.success) {
        setInfluencer(data.influencer);
        setReferrals(data.referrals);
        setEarnings(data.earnings);
      } else {
        setError('Failed to load dashboard');
      }
    } catch (err) {
      console.error('Dashboard error:', err);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    const token = localStorage.getItem('influencer_token');
    if (token) {
      try {
        await fetch(getApiUrl('/influencer/logout'), {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      } catch (err) {
        console.error('Logout error:', err);
      }
    }
    localStorage.removeItem('influencer_token');
    localStorage.removeItem('influencer_username');
    localStorage.removeItem('influencer_code');
    navigate('/influencer-login');
  };

  const copyReferralCode = () => {
    if (influencer?.referral_code) {
      navigator.clipboard.writeText(influencer.referral_code);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  const copyReferralLink = () => {
    if (influencer?.referral_code) {
      const link = `${window.location.origin}/signup?ref=${influencer.referral_code}`;
      navigator.clipboard.writeText(link);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const getTierDisplayName = (tier: string) => {
    const tierNames: { [key: string]: string } = {
      'beta': 'Beta ($9.99/mo)',
      'starter': 'Starter ($29.99/mo)',
      'semipro': 'Semi-Pro ($49.99/mo)',
      'professional': 'Professional ($99.99/mo)',
      'elite': 'Elite ($199.99/mo)',
      'elitepro': 'Elite Pro ($299.99/mo)',
    };
    return tierNames[tier] || tier;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-900 via-slate-900 to-black flex items-center justify-center">
        <div className="text-center">
          <svg className="animate-spin h-12 w-12 text-red-500 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="text-slate-300">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error || !influencer || !earnings) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-900 via-slate-900 to-black flex items-center justify-center p-4">
        <div className="bg-red-900/50 border-2 border-red-600 rounded-lg p-6 max-w-md">
          <p className="text-red-200">{error || 'Failed to load dashboard'}</p>
          <button
            onClick={() => navigate('/influencer-login')}
            className="mt-4 px-4 py-2 bg-red-700 hover:bg-red-600 rounded text-white font-medium transition-colors"
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-900 via-slate-900 to-black text-white">
      {/* Header */}
      <header className="bg-black/30 border-b border-red-700/30 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <img src="/logo2.png" alt="Max EV Sports" className="h-12 w-auto" />
              <div>
                <h1 className="text-2xl font-bold text-red-300">MAX-EV Partner Dashboard</h1>
                <p className="text-sm text-slate-400">Welcome back, {influencer.full_name}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-sm font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gradient-to-br from-blue-900/40 to-blue-950/60 border-2 border-blue-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-blue-300">Total Referrals</h3>
              <svg className="h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <p className="text-3xl font-bold text-white">{earnings.total_referrals}</p>
            <p className="text-xs text-slate-400 mt-1">Lifetime signups</p>
          </div>

          <div className="bg-gradient-to-br from-green-900/40 to-green-950/60 border-2 border-green-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-green-300">Active Referrals</h3>
              <svg className="h-8 w-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-3xl font-bold text-white">{earnings.active_referrals}</p>
            <p className="text-xs text-slate-400 mt-1">Paying subscribers</p>
          </div>

          <div className="bg-gradient-to-br from-red-900/40 to-red-950/60 border-2 border-red-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-red-300">Monthly Earnings</h3>
              <svg className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-3xl font-bold text-white">{formatCurrency(earnings.total_monthly_commission)}</p>
            <p className="text-xs text-slate-400 mt-1">Recurring income</p>
          </div>

          <div className="bg-gradient-to-br from-orange-900/40 to-orange-950/60 border-2 border-orange-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-orange-300">Annual Projection</h3>
              <svg className="h-8 w-8 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <p className="text-3xl font-bold text-white">{formatCurrency(earnings.annual_projection)}</p>
            <p className="text-xs text-slate-400 mt-1">Projected yearly</p>
          </div>
        </div>

        {/* Referral Code Section */}
        <div className="bg-gradient-to-br from-red-900/30 via-slate-900/50 to-black border-4 border-red-700 rounded-xl p-8">
          <h2 className="text-2xl font-bold text-red-300 mb-4">Your Referral Code</h2>
          <div className="bg-black/50 rounded-lg p-6 border-2 border-red-600">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-sm text-slate-400 mb-1">Share this code with your followers:</p>
                <p className="text-4xl font-bold text-red-300 tracking-wider">{influencer.referral_code}</p>
              </div>
              <button
                onClick={copyReferralCode}
                className="px-6 py-3 bg-red-600 hover:bg-red-700 rounded-lg transition-colors font-medium flex items-center gap-2"
              >
                {copySuccess ? (
                  <>
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Copied!
                  </>
                ) : (
                  <>
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copy Code
                  </>
                )}
              </button>
            </div>
            <div className="flex gap-2">
              <button
                onClick={copyReferralLink}
                className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-sm font-medium"
              >
                Copy Signup Link
              </button>
              <button
                className="flex-1 px-4 py-2 bg-blue-700 hover:bg-blue-600 rounded-lg transition-colors text-sm font-medium"
                onClick={() => window.open(`https://twitter.com/intent/tweet?text=Check out MAX EV Sports - the best sports betting analytics platform! Use code ${influencer.referral_code} to get 50% off for 2 months!&url=${window.location.origin}/signup?ref=${influencer.referral_code}`, '_blank')}
              >
                Share on Twitter
              </button>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-3 gap-4 text-center">
            <div className="bg-red-900/20 rounded-lg p-3 border border-red-700/30">
              <p className="text-xs text-slate-400">Your Followers Get</p>
              <p className="text-lg font-bold text-red-300">50% OFF</p>
              <p className="text-xs text-slate-400">First 2 Months</p>
            </div>
            <div className="bg-red-900/20 rounded-lg p-3 border border-red-700/30">
              <p className="text-xs text-slate-400">You Earn</p>
              <p className="text-lg font-bold text-red-300">20%</p>
              <p className="text-xs text-slate-400">Recurring Forever</p>
            </div>
            <div className="bg-red-900/20 rounded-lg p-3 border border-red-700/30">
              <p className="text-xs text-slate-400">Commission On</p>
              <p className="text-lg font-bold text-red-300">Full Price</p>
              <p className="text-xs text-slate-400">Not Discounted</p>
            </div>
          </div>
        </div>

        {/* Earnings Breakdown by Tier */}
        {Object.keys(earnings.breakdown_by_tier).length > 0 && (
          <div className="bg-gradient-to-br from-slate-900/50 to-black border-2 border-slate-700 rounded-xl p-6">
            <h2 className="text-xl font-bold text-slate-200 mb-4">Earnings by Tier</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {Object.entries(earnings.breakdown_by_tier).map(([tier, data]) => (
                <div key={tier} className="bg-slate-800/50 rounded-lg p-4 border border-slate-600">
                  <p className="text-xs text-slate-400 mb-1">{getTierDisplayName(tier)}</p>
                  <p className="text-2xl font-bold text-white">{data.count}</p>
                  <p className="text-sm text-red-300 mt-1">{formatCurrency(data.commission)}/mo</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Referrals Table */}
        <div className="bg-gradient-to-br from-slate-900/50 to-black border-2 border-slate-700 rounded-xl p-6">
          <h2 className="text-xl font-bold text-slate-200 mb-4">Your Referrals ({referrals.length})</h2>
          {referrals.length === 0 ? (
            <div className="text-center py-12">
              <svg className="h-16 w-16 text-slate-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <p className="text-slate-400 text-lg mb-2">No referrals yet</p>
              <p className="text-slate-500 text-sm">Start sharing your code to earn commissions!</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">User</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Tier</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Signup Date</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Status</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-slate-400">Commission</th>
                  </tr>
                </thead>
                <tbody>
                  {referrals.map((referral, index) => (
                    <tr key={index} className="border-b border-slate-800 hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4 text-sm text-white">{referral.referred_username}</td>
                      <td className="py-3 px-4 text-sm text-slate-300">{getTierDisplayName(referral.subscription_tier)}</td>
                      <td className="py-3 px-4 text-sm text-slate-300">{formatDate(referral.signup_date)}</td>
                      <td className="py-3 px-4 text-sm">
                        <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                          referral.status === 'active'
                            ? 'bg-green-900/50 text-green-300 border border-green-700'
                            : 'bg-red-900/50 text-red-300 border border-red-700'
                        }`}>
                          {referral.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-right font-bold text-red-300">
                        {formatCurrency(referral.monthly_commission)}/mo
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      <footer className="bg-black/30 border-t border-red-700/30 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-slate-500 text-sm">
          <p>© 2025 Max EV Holdings, LLC. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
