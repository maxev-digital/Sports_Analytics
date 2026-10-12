import { useState, useEffect } from 'react';
import { getApiUrl } from '../../config';
import { logger } from '../../utils/logger';

interface User {
  username: string;
  email: string;
  full_name: string;
  role: string;
  created_at: string;
  trial_start: string;
  trial_days: number;
  referral_code: string | null;
  active_sessions: number;
}

const TIERS = ['free', 'member', 'semipro', 'pro', 'elite', 'admin'];

export function AdminUsers({ token }: { token: string | null }) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState<{ type: 'tier' | 'password' | 'delete'; user: User } | null>(null);
  const [newTier, setNewTier] = useState('member');
  const [newPassword, setNewPassword] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  const loadUsers = async () => {
    try {
      const resp = await fetch(getApiUrl('admin/users'), { headers });
      if (resp.ok) {
        const data = await resp.json();
        setUsers(data.users || []);
      }
    } catch (e) {
      logger.error('Load users failed:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadUsers(); }, []);

  const filtered = users.filter(u =>
    u.username.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase()) ||
    u.full_name.toLowerCase().includes(search.toLowerCase())
  );

  const changeTier = async () => {
    if (!modal) return;
    setActionLoading(true);
    try {
      await fetch(getApiUrl(`admin/users/${modal.user.username}/tier`), {
        method: 'POST', headers, body: JSON.stringify({ tier: newTier }),
      });
      await loadUsers();
      setModal(null);
    } catch (e) { logger.error('Tier change failed:', e); }
    finally { setActionLoading(false); }
  };

  const resetPassword = async () => {
    if (!modal || newPassword.length < 6) return;
    setActionLoading(true);
    try {
      await fetch(getApiUrl(`admin/users/${modal.user.username}/reset-password`), {
        method: 'POST', headers, body: JSON.stringify({ password: newPassword }),
      });
      setModal(null);
      setNewPassword('');
    } catch (e) { logger.error('Password reset failed:', e); }
    finally { setActionLoading(false); }
  };

  const deleteUser = async () => {
    if (!modal) return;
    setActionLoading(true);
    try {
      await fetch(getApiUrl(`admin/users/${modal.user.username}`), {
        method: 'DELETE', headers,
      });
      await loadUsers();
      setModal(null);
    } catch (e) { logger.error('Delete failed:', e); }
    finally { setActionLoading(false); }
  };

  const fmtDate = (d: string) => {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }); }
    catch { return d; }
  };

  return (
    <div>
      {/* Search */}
      <div className="flex items-center gap-3 mb-4">
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search users..."
          className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white text-sm placeholder:text-slate-500 outline-none focus:border-blue-500"
        />
        <span className="text-slate-500 text-sm">{filtered.length} users</span>
      </div>

      {/* Table */}
      {loading ? (
        <div className="text-center text-slate-500 py-12">Loading users...</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400 uppercase">User</th>
                <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400 uppercase">Email</th>
                <th className="px-3 py-2.5 text-center text-xs font-bold text-slate-400 uppercase">Role</th>
                <th className="px-3 py-2.5 text-center text-xs font-bold text-slate-400 uppercase">Sessions</th>
                <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400 uppercase">Signed Up</th>
                <th className="px-3 py-2.5 text-center text-xs font-bold text-slate-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(u => (
                <tr key={u.username} className="border-b border-slate-800 hover:bg-slate-800/50">
                  <td className="px-3 py-3">
                    <div className="text-white font-semibold">{u.username}</div>
                    <div className="text-slate-500 text-xs">{u.full_name}</div>
                  </td>
                  <td className="px-3 py-3 text-slate-400">{u.email}</td>
                  <td className="px-3 py-3 text-center">
                    <span className={`text-xs font-bold px-2 py-1 rounded ${
                      u.role === 'admin' ? 'bg-purple-500/20 text-purple-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>{u.role}</span>
                  </td>
                  <td className="px-3 py-3 text-center">
                    <span className={u.active_sessions > 0 ? 'text-emerald-400 font-bold' : 'text-slate-600'}>{u.active_sessions}</span>
                  </td>
                  <td className="px-3 py-3 text-slate-400 text-xs">{fmtDate(u.created_at)}</td>
                  <td className="px-3 py-3 text-center">
                    <div className="flex gap-1 justify-center">
                      <button onClick={() => { setModal({ type: 'tier', user: u }); setNewTier(u.role); }}
                        className="px-2 py-1 text-xs bg-slate-700 text-slate-300 rounded hover:bg-slate-600">Tier</button>
                      <button onClick={() => { setModal({ type: 'password', user: u }); setNewPassword(''); }}
                        className="px-2 py-1 text-xs bg-slate-700 text-slate-300 rounded hover:bg-slate-600">Reset PW</button>
                      {u.role !== 'admin' && (
                        <button onClick={() => setModal({ type: 'delete', user: u })}
                          className="px-2 py-1 text-xs bg-red-900/50 text-red-400 rounded hover:bg-red-900">Delete</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {modal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setModal(null)}>
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 max-w-md w-full mx-4" onClick={e => e.stopPropagation()}>
            {modal.type === 'tier' && (
              <>
                <h3 className="text-lg font-bold text-white mb-4">Change Tier — {modal.user.username}</h3>
                <select value={newTier} onChange={e => setNewTier(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2.5 text-white mb-4">
                  {TIERS.map(t => <option key={t} value={t}>{t.toUpperCase()}</option>)}
                </select>
                <div className="flex gap-2 justify-end">
                  <button onClick={() => setModal(null)} className="px-4 py-2 text-sm bg-slate-700 text-slate-300 rounded-lg">Cancel</button>
                  <button onClick={changeTier} disabled={actionLoading}
                    className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg font-bold disabled:opacity-50">
                    {actionLoading ? 'Saving...' : 'Save'}
                  </button>
                </div>
              </>
            )}
            {modal.type === 'password' && (
              <>
                <h3 className="text-lg font-bold text-white mb-4">Reset Password — {modal.user.username}</h3>
                <input type="text" value={newPassword} onChange={e => setNewPassword(e.target.value)}
                  placeholder="New password (min 6 chars)"
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2.5 text-white mb-4" />
                <div className="flex gap-2 justify-end">
                  <button onClick={() => setModal(null)} className="px-4 py-2 text-sm bg-slate-700 text-slate-300 rounded-lg">Cancel</button>
                  <button onClick={resetPassword} disabled={actionLoading || newPassword.length < 6}
                    className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg font-bold disabled:opacity-50">
                    {actionLoading ? 'Resetting...' : 'Reset'}
                  </button>
                </div>
              </>
            )}
            {modal.type === 'delete' && (
              <>
                <h3 className="text-lg font-bold text-red-400 mb-4">Delete User — {modal.user.username}</h3>
                <p className="text-slate-400 mb-4">This permanently deletes the account and all sessions. This cannot be undone.</p>
                <div className="flex gap-2 justify-end">
                  <button onClick={() => setModal(null)} className="px-4 py-2 text-sm bg-slate-700 text-slate-300 rounded-lg">Cancel</button>
                  <button onClick={deleteUser} disabled={actionLoading}
                    className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg font-bold disabled:opacity-50">
                    {actionLoading ? 'Deleting...' : 'Delete Forever'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
