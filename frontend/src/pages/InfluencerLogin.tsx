import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiUrl } from '../config';

export function InfluencerLogin() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [isSnorting, setIsSnorting] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await fetch(getApiUrl('/influencer/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Store influencer token
        localStorage.setItem('influencer_token', data.token);
        localStorage.setItem('influencer_username', username);
        localStorage.setItem('influencer_code', data.influencer.referral_code);

        // Redirect to influencer dashboard
        navigate('/influencer-dashboard');
      } else {
        setError(data.detail || 'Login failed');
        setLoading(false);
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('Network error. Please try again.');
      setLoading(false);
    }
  };

  const playSnort = () => {
    // Trigger animation
    setIsSnorting(true);

    // Play snort sound
    const audio = new Audio('/snort.mp3');
    audio.volume = 0.3;
    audio.play().catch(err => console.log('Audio play failed:', err));

    // Reset animation after 600ms
    setTimeout(() => {
      setIsSnorting(false);
    }, 600);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-900 via-slate-900 to-black px-4 relative overflow-hidden">
      <div className="max-w-md w-full space-y-6">
        <div className="text-center relative">
          <img
            src="/logo2.png"
            alt="Max EV Sports - MAX-EV Partner Dashboard"
            className={`mx-auto h-48 w-auto mb-6 drop-shadow-[0_10px_20px_rgba(0,0,0,0.5)] cursor-pointer transition-all duration-200 ${
              isSnorting
                ? 'animate-bounce scale-110 drop-shadow-[0_0_30px_rgba(239,68,68,0.8)]'
                : 'hover:scale-105'
            }`}
            onClick={playSnort}
          />
          <h2 className={`text-center text-4xl font-bold text-white transition-all duration-200 ${
            isSnorting ? 'text-red-400 scale-105' : ''
          }`}>
            MAX-EV Partner Dashboard
          </h2>
          <p className={`mt-2 text-center text-sm text-red-300 transition-all duration-200 ${
            isSnorting ? 'text-red-200 font-semibold' : ''
          }`}>
            Invitation-Only Partner Program
          </p>
          <p className="mt-1 text-center text-xs text-slate-500">
            Track your referrals and earnings
          </p>
        </div>

        <div className="bg-gradient-to-br from-red-900/40 via-slate-900/80 to-black border-4 border-red-700 rounded-lg shadow-xl p-8">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-900/50 border-2 border-red-600 rounded-lg p-3 text-red-200 text-sm">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="username" className="block text-sm font-medium text-slate-300 mb-2">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                placeholder="Enter your username"
                disabled={loading}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none relative block w-full px-4 py-3 pr-12 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  placeholder="Enter your password"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-200 transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                    </svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className={`
                  group relative w-full flex justify-center py-3 px-4
                  border-2 border-red-700 rounded-lg text-white text-sm font-medium
                  ${loading
                    ? 'bg-slate-600 cursor-not-allowed'
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
                    Signing in...
                  </span>
                ) : (
                  'Sign in to Dashboard'
                )}
              </button>
            </div>
          </form>

          <div className="mt-6 text-center">
            <p className="text-xs text-slate-400 mb-4">Access your partner dashboard to track earnings</p>
            <div className="flex flex-col items-center gap-2">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-slate-400">Invited partner?</span>
                <button
                  onClick={() => navigate('/influencer-register')}
                  className="text-red-400 hover:text-red-300 font-semibold underline transition-colors"
                >
                  Apply Now
                </button>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Minimum 10,000+ followers required
              </p>
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
