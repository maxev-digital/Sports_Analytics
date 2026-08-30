import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config';

export function ForgotPassword() {
  const [email, setEmail]       = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading]   = useState(false);
  const navigate                = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await fetch(`${API_BASE_URL}/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
    } finally {
      setLoading(false);
      setSubmitted(true);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
      <div className="max-w-md w-full space-y-6">
        <div className="text-center">
          <img src="/3DMaxLogo.png" alt="Max EV Sports" className="mx-auto h-32 w-auto mb-4 mix-blend-screen" />
          <h2 className="text-3xl font-bold text-white">Forgot Password</h2>
          <p className="mt-2 text-sm text-slate-400">
            Enter your account email and we'll send a reset link.
          </p>
        </div>

        <div className="bg-gradient-to-br from-red-900 via-red-950 to-black border-4 border-red-800 rounded-lg shadow-xl p-8">
          {submitted ? (
            <div className="text-center space-y-4">
              <div className="text-4xl">✉️</div>
              <p className="text-white font-semibold">Check your email</p>
              <p className="text-slate-400 text-sm">
                If <strong className="text-slate-200">{email}</strong> is registered, a reset link is on its way. Check your spam folder if you don't see it.
              </p>
              <button
                onClick={() => navigate('/login')}
                className="w-full mt-4 py-3 px-4 bg-black hover:bg-slate-900 border-2 border-slate-700 rounded-lg text-white text-sm font-medium transition-colors"
              >
                Back to Login
              </button>
            </div>
          ) : (
            <form className="space-y-5" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                  Email Address
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="you@example.com"
                  disabled={loading}
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className={`w-full py-3 px-4 border-2 border-slate-700 rounded-lg text-white text-sm font-medium transition-all ${
                  loading ? 'bg-slate-600 cursor-not-allowed' : 'bg-black hover:bg-slate-900'
                }`}
              >
                {loading ? 'Sending...' : 'Send Reset Link'}
              </button>

              <div className="text-center">
                <button
                  type="button"
                  onClick={() => navigate('/login')}
                  className="text-sm text-slate-400 hover:text-slate-200 transition-colors"
                >
                  ← Back to Login
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
