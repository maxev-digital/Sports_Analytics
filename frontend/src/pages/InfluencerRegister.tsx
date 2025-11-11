import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiUrl } from '../config';

export function InfluencerRegister() {
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    socialMediaHandle: '',
    platform: 'Twitter',
    followerCount: '',
    customCode: '',
    paymentEmail: '',
  });
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [codeAvailable, setCodeAvailable] = useState<boolean | null>(null);
  const [checkingCode, setCheckingCode] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });

    // Check code availability when custom code changes
    if (e.target.name === 'customCode' && e.target.value.length >= 3) {
      checkCodeAvailability(e.target.value);
    } else if (e.target.name === 'customCode' && e.target.value.length < 3) {
      setCodeAvailable(null);
    }
  };

  const checkCodeAvailability = async (code: string) => {
    setCheckingCode(true);
    try {
      const response = await fetch(getApiUrl('/influencer/validate-code'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });
      const result = await response.json();
      setCodeAvailable(!result.valid); // Available if NOT valid (not already taken)
    } catch (err) {
      console.error('Error checking code:', err);
      setCodeAvailable(null);
    } finally {
      setCheckingCode(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    if (!agreedToTerms) {
      setError('You must agree to the Terms of Service and Privacy Policy to continue');
      return;
    }

    if (!formData.socialMediaHandle.startsWith('@')) {
      setError('Social media handle must start with @');
      return;
    }

    const followerCount = parseInt(formData.followerCount);
    if (isNaN(followerCount) || followerCount < 0) {
      setError('Please enter a valid follower count');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(getApiUrl('/influencer/register'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: formData.username,
          email: formData.email,
          password: formData.password,
          full_name: formData.fullName,
          social_media_handle: formData.socialMediaHandle,
          platform: formData.platform,
          follower_count: followerCount,
          custom_code: formData.customCode || undefined,
          payment_email: formData.paymentEmail || undefined,
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Show success and redirect to login
        alert(`Success! Your referral code is: ${data.data.referral_code}\n\nPlease save this code - your followers will use it to sign up and get 50% off for 2 months.`);
        navigate('/influencer-login');
      } else {
        setError(data.detail || data.message || 'Registration failed');
        setLoading(false);
      }
    } catch (err) {
      console.error('Registration error:', err);
      setError('Network error. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-900 via-slate-900 to-black px-4 relative overflow-hidden py-12">
      <div className="max-w-2xl w-full space-y-6">
        <div className="text-center relative">
          <img
            src="/logo2.png"
            alt="Max EV Sports - Partner Program Application"
            className="mx-auto h-48 w-auto mb-6 drop-shadow-[0_10px_20px_rgba(0,0,0,0.5)]"
          />
          <h2 className="text-center text-4xl font-bold text-white mb-2">
            MAX-EV Partner Program Application
          </h2>
          <p className="text-center text-lg text-red-300 mb-1">
            Earn 20% Recurring Commission on Every Referral
          </p>
          <p className="text-center text-sm text-slate-400 mb-2">
            Your followers get 50% off for 2 months • You earn passive income forever
          </p>
          <div className="flex items-center justify-center gap-2 text-xs text-yellow-400 bg-yellow-900/20 border border-yellow-700/30 rounded-lg px-4 py-2 max-w-md mx-auto">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4 flex-shrink-0">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
            <span className="font-semibold">Invitation Only: Minimum 10,000+ followers required • Subject to approval</span>
          </div>
        </div>

        <div className="bg-gradient-to-br from-red-900/40 via-slate-900/80 to-black border-4 border-red-700 rounded-lg shadow-xl p-8">
          <form className="space-y-5" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-900/50 border-2 border-red-600 rounded-lg p-3 text-red-200 text-sm">
                {error}
              </div>
            )}

            <div className="grid md:grid-cols-2 gap-5">
              {/* Full Name */}
              <div>
                <label htmlFor="fullName" className="block text-sm font-medium text-slate-300 mb-2">
                  Full Name *
                </label>
                <input
                  id="fullName"
                  name="fullName"
                  type="text"
                  required
                  value={formData.fullName}
                  onChange={handleChange}
                  className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  placeholder="John Doe"
                  disabled={loading}
                />
              </div>

              {/* Email */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                  Email Address *
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  placeholder="john@example.com"
                  disabled={loading}
                />
              </div>

              {/* Username */}
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-slate-300 mb-2">
                  Username *
                </label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  value={formData.username}
                  onChange={handleChange}
                  className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  placeholder="johndoe"
                  disabled={loading}
                />
              </div>

              {/* Social Media Handle */}
              <div>
                <label htmlFor="socialMediaHandle" className="block text-sm font-medium text-slate-300 mb-2">
                  Social Media Handle *
                </label>
                <input
                  id="socialMediaHandle"
                  name="socialMediaHandle"
                  type="text"
                  required
                  value={formData.socialMediaHandle}
                  onChange={handleChange}
                  className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  placeholder="@johndoe"
                  disabled={loading}
                />
              </div>

              {/* Platform */}
              <div>
                <label htmlFor="platform" className="block text-sm font-medium text-slate-300 mb-2">
                  Primary Platform *
                </label>
                <select
                  id="platform"
                  name="platform"
                  required
                  value={formData.platform}
                  onChange={handleChange}
                  className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  disabled={loading}
                >
                  <option value="Twitter">Twitter/X</option>
                  <option value="Instagram">Instagram</option>
                  <option value="YouTube">YouTube</option>
                  <option value="TikTok">TikTok</option>
                  <option value="Facebook">Facebook</option>
                  <option value="Twitch">Twitch</option>
                  <option value="Discord">Discord</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              {/* Follower Count */}
              <div>
                <label htmlFor="followerCount" className="block text-sm font-medium text-slate-300 mb-2">
                  Follower Count *
                </label>
                <input
                  id="followerCount"
                  name="followerCount"
                  type="number"
                  required
                  value={formData.followerCount}
                  onChange={handleChange}
                  className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  placeholder="10000"
                  disabled={loading}
                />
              </div>

              {/* Custom Referral Code */}
              <div>
                <label htmlFor="customCode" className="block text-sm font-medium text-slate-300 mb-2">
                  Custom Referral Code (Optional)
                </label>
                <div className="relative">
                  <input
                    id="customCode"
                    name="customCode"
                    type="text"
                    value={formData.customCode}
                    onChange={handleChange}
                    className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 uppercase"
                    placeholder="JOHNDOE"
                    disabled={loading}
                    maxLength={20}
                  />
                  {formData.customCode.length >= 3 && (
                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                      {checkingCode ? (
                        <svg className="animate-spin h-5 w-5 text-slate-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      ) : codeAvailable === true ? (
                        <svg className="h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : codeAvailable === false ? (
                        <svg className="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      ) : null}
                    </div>
                  )}
                </div>
                {formData.customCode.length >= 3 && codeAvailable === false && (
                  <p className="mt-1 text-xs text-red-400">Code already taken</p>
                )}
                {formData.customCode.length >= 3 && codeAvailable === true && (
                  <p className="mt-1 text-xs text-green-400">Code available!</p>
                )}
                {!formData.customCode && (
                  <p className="mt-1 text-xs text-slate-400">Leave blank to auto-generate from your name</p>
                )}
              </div>

              {/* Payment Email */}
              <div>
                <label htmlFor="paymentEmail" className="block text-sm font-medium text-slate-300 mb-2">
                  Payment Email (Optional)
                </label>
                <input
                  id="paymentEmail"
                  name="paymentEmail"
                  type="email"
                  value={formData.paymentEmail}
                  onChange={handleChange}
                  className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  placeholder="payments@example.com"
                  disabled={loading}
                />
                <p className="mt-1 text-xs text-slate-400">For receiving commission payments</p>
              </div>
            </div>

            {/* Password Fields */}
            <div className="grid md:grid-cols-2 gap-5 pt-2">
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                  Password *
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  placeholder="At least 6 characters"
                  disabled={loading}
                />
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-300 mb-2">
                  Confirm Password *
                </label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  required
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  placeholder="Confirm your password"
                  disabled={loading}
                />
              </div>
            </div>

            {/* Terms Agreement Checkbox */}
            <div className="pt-3">
              <label className="flex items-start space-x-3 cursor-pointer group">
                <div className="flex items-center h-5 mt-0.5">
                  <input
                    type="checkbox"
                    checked={agreedToTerms}
                    onChange={(e) => setAgreedToTerms(e.target.checked)}
                    disabled={loading}
                    className="w-5 h-5 border-2 border-slate-600 rounded bg-slate-700 text-red-600 focus:ring-2 focus:ring-red-500 focus:ring-offset-0 cursor-pointer disabled:opacity-50"
                  />
                </div>
                <span className="text-sm text-slate-300 leading-tight">
                  I agree to the Influencer Program{' '}
                  <a
                    href="/terms"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-red-400 hover:text-red-300 underline font-semibold"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Terms of Service
                  </a>
                  {' and understand that I will earn 20% recurring commission on all referred users.'}
                </span>
              </label>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={loading || !agreedToTerms}
                className={`
                  group relative w-full flex justify-center py-3 px-4
                  border-2 border-red-700 rounded-lg text-white text-sm font-bold
                  ${loading || !agreedToTerms
                    ? 'bg-slate-600 cursor-not-allowed opacity-60'
                    : 'bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500'
                  }
                  transition-all duration-200
                `}
              >
                {loading ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Creating your account...
                  </span>
                ) : (
                  'Join Influencer Program'
                )}
              </button>
            </div>
          </form>

          <div className="mt-6 text-center">
            <div className="text-xs text-slate-300 mb-4 space-y-1 bg-red-900/20 p-4 rounded-lg border border-red-700/30">
              <p className="font-bold text-red-300 text-sm mb-2">Program Benefits:</p>
              <p>✓ 20% recurring commission on all referrals</p>
              <p>✓ Your followers get 50% off for 2 months</p>
              <p>✓ Track all referrals in your dashboard</p>
              <p>✓ Real-time earnings updates</p>
              <p>✓ Monthly payouts</p>
            </div>
            <div className="flex items-center justify-center gap-2 text-sm pt-4 border-t border-slate-700">
              <span className="text-slate-400">Already registered?</span>
              <button
                onClick={() => navigate('/influencer-login')}
                className="text-red-400 hover:text-red-300 font-semibold underline transition-colors"
              >
                Sign In
              </button>
            </div>
          </div>
        </div>

        <div className="text-center text-xs text-slate-600 mt-4">
          <p>© 2025 Max EV Holdings, LLC. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}
