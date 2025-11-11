import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiUrl } from '../config';

export function SignUp() {
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    referralCode: '',
  });
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [showFireRing, setShowFireRing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [referralValidation, setReferralValidation] = useState<{valid: boolean, message: string} | null>(null);
  const [checkingCode, setCheckingCode] = useState(false);
  const navigate = useNavigate();
  const audioRef = useRef<HTMLAudioElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });

    // Validate referral code when it changes
    if (name === 'referralCode' && value.length >= 3) {
      validateReferralCode(value);
    } else if (name === 'referralCode' && value.length < 3) {
      setReferralValidation(null);
    }
  };

  const validateReferralCode = async (code: string) => {
    setCheckingCode(true);
    try {
      const response = await fetch(getApiUrl('/influencer/validate-code'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });
      const result = await response.json();
      setReferralValidation(result);
    } catch (err) {
      console.error('Error validating code:', err);
      setReferralValidation(null);
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

    setLoading(true);

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          full_name: formData.fullName,
          email: formData.email,
          username: formData.username,
          password: formData.password,
          referral_code: formData.referralCode || undefined,
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Store token and username
        localStorage.setItem('auth_token', data.token);
        localStorage.setItem('auth_username', data.username);

        // Trigger fire ring animation
        setShowFireRing(true);

        // Play bull snort sound (same as login)
        if (audioRef.current) {
          audioRef.current.play().catch(err => console.log('Audio play failed:', err));
        }

        // Redirect to pricing page after animation
        setTimeout(() => {
          window.location.href = '/pricing';
        }, 1500);
      } else {
        setError(data.detail || 'Registration failed');
        setLoading(false);
      }
    } catch (err) {
      console.error('Registration error:', err);
      setError('Network error. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-black px-4 relative overflow-hidden py-12">
      {/* Hidden audio element for bull snort sound */}
      <audio
        ref={audioRef}
        src="/bull.mp3"
        preload="auto"
      />
      
      {/* Fire Ring Animation Overlay */}
      {showFireRing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none">
          <div className="fire-ring animate-fire-ring"></div>
        </div>
      )}

      <div className="max-w-md w-full space-y-6">
        <div className="text-center relative">
          <img 
            src="/logo2.png" 
            alt="Max EV Sports - Bull Market Betting" 
            className={`mx-auto h-64 w-auto mb-6 transition-all duration-500 ${showFireRing ? 'scale-110 brightness-125 drop-shadow-[0_0_30px_rgba(59,130,246,0.8)]' : 'drop-shadow-[0_10px_20px_rgba(0,0,0,0.5)]'}`}
          />
          <h2 className="text-center text-4xl font-bold text-white">
            Sign Me up for Early Subscriber 50% Off for Life
          </h2>
          <p className="mt-2 text-center text-sm text-slate-400">
            Lock in 50% off forever • Cancel anytime
          </p>
        </div>

        <div className="bg-gradient-to-br from-blue-900 via-blue-950 to-black border-4 border-blue-800 rounded-lg shadow-xl p-8">
          <form className="space-y-5" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-900/50 border-2 border-red-600 rounded-lg p-3 text-red-200 text-sm">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="fullName" className="block text-sm font-medium text-slate-300 mb-2">
                Full Name
              </label>
              <input
                id="fullName"
                name="fullName"
                type="text"
                required
                value={formData.fullName}
                onChange={handleChange}
                className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="John Doe"
                disabled={loading}
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                Email Address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleChange}
                className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="john@example.com"
                disabled={loading}
              />
            </div>

            <div>
              <label htmlFor="username" className="block text-sm font-medium text-slate-300 mb-2">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                value={formData.username}
                onChange={handleChange}
                className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Choose a username"
                disabled={loading}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="At least 6 characters"
                disabled={loading}
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-300 mb-2">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                required
                value={formData.confirmPassword}
                onChange={handleChange}
                className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Confirm your password"
                disabled={loading}
              />
            </div>

            {/* Referral Code Field */}
            <div>
              <label htmlFor="referralCode" className="block text-sm font-medium text-slate-300 mb-2">
                Referral Code (Optional)
              </label>
              <div className="relative">
                <input
                  id="referralCode"
                  name="referralCode"
                  type="text"
                  value={formData.referralCode}
                  onChange={handleChange}
                  className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 uppercase"
                  placeholder="Enter influencer code"
                  disabled={loading}
                  maxLength={20}
                />
                {formData.referralCode.length >= 3 && (
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    {checkingCode ? (
                      <svg className="animate-spin h-5 w-5 text-slate-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    ) : referralValidation?.valid ? (
                      <svg className="h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : referralValidation && !referralValidation.valid ? (
                      <svg className="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    ) : null}
                  </div>
                )}
              </div>
              {referralValidation && (
                <p className={`mt-1 text-xs ${referralValidation.valid ? 'text-green-400' : 'text-red-400'}`}>
                  {referralValidation.message}
                </p>
              )}
            </div>

            {/* Terms Agreement Checkbox */}
            <div className="pt-2">
              <label className="flex items-start space-x-3 cursor-pointer group">
                <div className="flex items-center h-5 mt-0.5">
                  <input
                    type="checkbox"
                    checked={agreedToTerms}
                    onChange={(e) => setAgreedToTerms(e.target.checked)}
                    disabled={loading}
                    className="w-5 h-5 border-2 border-slate-600 rounded bg-slate-700 text-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 cursor-pointer disabled:opacity-50"
                  />
                </div>
                <span className="text-sm text-slate-300 leading-tight">
                  I am 21 years or older and agree to the{' '}
                  <a
                    href="/terms"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 underline font-semibold"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Terms of Service
                  </a>
                  {', '}
                  <a
                    href="/privacy"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 underline font-semibold"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Privacy Policy
                  </a>
                  {', and '}
                  <a
                    href="/disclaimer"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 underline font-semibold"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Disclaimer
                  </a>
                  .
                </span>
              </label>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={loading || !agreedToTerms}
                className={`
                  group relative w-full flex justify-center py-3 px-4
                  border-2 border-blue-700 rounded-lg text-white text-sm font-bold
                  ${loading || !agreedToTerms
                    ? 'bg-slate-600 cursor-not-allowed opacity-60'
                    : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
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
                  '🔥 Create Account & Get 50% Off'
                )}
              </button>
            </div>
          </form>

          <div className="mt-6 text-center">
            <div className="text-xs text-slate-400 mb-4 space-y-1">
              <p>✓ 50% off for life - locked in forever</p>
              <p>✓ Choose your plan after signup</p>
              <p>✓ Cancel anytime</p>
            </div>
            <div className="flex items-center justify-center gap-2 text-sm pt-4 border-t border-slate-700">
              <span className="text-slate-400">Already have an account?</span>
              <button
                onClick={() => navigate('/login')}
                className="text-blue-400 hover:text-blue-300 font-semibold underline transition-colors"
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
