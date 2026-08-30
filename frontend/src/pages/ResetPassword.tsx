import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { API_BASE_URL } from '../config';

export function ResetPassword() {
  const [searchParams]          = useSearchParams();
  const token                   = searchParams.get('token') ?? '';
  const [password, setPassword] = useState('');
  const [confirm, setConfirm]   = useState('');
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);
  const [success, setSuccess]   = useState(false);
  const navigate                = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError((data as { detail?: string }).detail ?? 'Reset failed. The link may have expired.');
      } else {
        setSuccess(true);
      }
    } catch {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
        <div className="max-w-md w-full text-center space-y-4">
          <p className="text-red-400 text-lg font-semibold">Invalid reset link.</p>
          <button
            onClick={() => navigate('/forgot-password')}
            className="text-blue-400 hover:text-blue-300 underline text-sm"
          >
            Request a new one
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
      <div className="max-w-md w-full space-y-6">
        <div className="text-center">
          <img src="/3DMaxLogo.png" alt="Max EV Sports" className="mx-auto h-32 w-auto mb-4 mix-blend-screen" />
          <h2 className="text-3xl font-bold text-white">Reset Password</h2>
          <p className="mt-2 text-sm text-slate-400">Choose a new password for your account.</p>
        </div>

        <div className="bg-gradient-to-br from-red-900 via-red-950 to-black border-4 border-red-800 rounded-lg shadow-xl p-8">
          {success ? (
            <div className="text-center space-y-4">
              <div className="text-4xl">✅</div>
              <p className="text-white font-semibold">Password reset successfully!</p>
              <button
                onClick={() => navigate('/login')}
                className="w-full mt-4 py-3 px-4 bg-black hover:bg-slate-900 border-2 border-slate-700 rounded-lg text-white text-sm font-medium transition-colors"
              >
                Log In
              </button>
            </div>
          ) : (
            <form className="space-y-5" onSubmit={handleSubmit}>
              {error && (
                <div className="bg-red-900/50 border-2 border-red-600 rounded-lg p-3 text-red-200 text-sm">
                  {error}
                </div>
              )}

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                  New Password
                </label>
                <input
                  id="password"
                  type="password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="At least 8 characters"
                  disabled={loading}
                />
              </div>

              <div>
                <label htmlFor="confirm" className="block text-sm font-medium text-slate-300 mb-2">
                  Confirm New Password
                </label>
                <input
                  id="confirm"
                  type="password"
                  required
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  className="w-full px-4 py-3 border-2 border-slate-600 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Re-enter new password"
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
                {loading ? 'Resetting...' : 'Reset Password'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
