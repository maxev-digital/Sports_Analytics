import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showFireRing, setShowFireRing] = useState(false);
  const { login, error, loading } = useAuth();
  const navigate = useNavigate();
  const audioRef = useRef<HTMLAudioElement>(null);
  const bullAudioRef = useRef<HTMLAudioElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const success = await login(username, password);
    if (success) {
      // Trigger fire ring animation
      setShowFireRing(true);

      // Play bull sound only
      if (bullAudioRef.current) {
        bullAudioRef.current.play().catch(err => console.log('Bull audio play failed:', err));
      }

      // Redirect after bull sound finishes (giving it time to play)
      setTimeout(() => {
        navigate('/live-games');
      }, 100); // PERF FIX: Instant redirect (was 5000ms)
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-black px-4 relative overflow-hidden">
      {/* Hidden audio elements for sound effects */}
      <audio
        ref={audioRef}
        src="/flame.mp3"
        preload="auto"
      />
      <audio
        ref={bullAudioRef}
        src="/bull.mp3"
        preload="auto"
      />

      <div className="max-w-md w-full space-y-6">
        <div className="text-center relative">
          <img 
            src="/logo2.png" 
            alt="Max EV Sports - Bull Market Betting" 
            className={`mx-auto h-64 w-auto mb-6 transition-all duration-500 ${showFireRing ? 'scale-110 brightness-125 drop-shadow-[0_0_30px_rgba(239,68,68,0.8)]' : 'drop-shadow-[0_10px_20px_rgba(0,0,0,0.5)]'}`}
          />
          <h2 className="text-center text-4xl font-bold text-white">
            Max-EV-Bettors Only
          </h2>
          <p className="mt-2 text-center text-sm text-slate-400">
            Authorized Access Required
          </p>
        </div>

        <div className="bg-gradient-to-br from-red-900 via-red-950 to-black border-4 border-red-800 rounded-lg shadow-xl p-8">
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
                className="appearance-none relative block w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
                  className="appearance-none relative block w-full px-4 py-3 pr-12 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
                  border-2 border-slate-700 rounded-lg text-white text-sm font-medium
                  ${loading
                    ? 'bg-slate-600 cursor-not-allowed'
                    : 'bg-black hover:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500'
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
                  'Sign in'
                )}
              </button>
            </div>
          </form>

          <div className="mt-6 text-center space-y-3">
            <p className="text-xs text-slate-500 mb-4">Protected access to betting analytics and arbitrage detection</p>
            <div className="flex items-center justify-center gap-2 text-sm">
              <span className="text-slate-400">Don't have an account?</span>
              <button
                onClick={() => navigate('/signup')}
                className="text-blue-400 hover:text-blue-300 font-semibold underline transition-colors"
              >
                Create Account
              </button>
            </div>

            {/* Partner Dashboard Link */}
            <div className="pt-3 mt-3 border-t border-slate-700/50">
              <p className="text-xs text-slate-500 mb-2">Partner Program (By Invitation Only)</p>
              <button
                onClick={() => navigate('/influencer-login')}
                className="flex items-center justify-center gap-2 text-sm text-red-400 hover:text-red-300 font-semibold transition-colors group"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4 group-hover:scale-110 transition-transform">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                </svg>
                Partner Login →
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
