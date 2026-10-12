import { useState } from 'react';
import { getApiUrl } from '../../config';
import { logger } from '../../utils/logger';

type SendMode = 'single' | 'broadcast';

export function AdminEmail({ token }: { token: string | null }) {
  const [mode, setMode] = useState<SendMode>('single');
  const [to, setTo] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [tier, setTier] = useState('all');
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);
  const [testing, setTesting] = useState(false);

  const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  const sendEmail = async () => {
    setSending(true);
    setResult(null);
    try {
      const endpoint = mode === 'single' ? 'admin/email/send' : 'admin/email/broadcast';
      const payload = mode === 'single'
        ? { to, subject, body }
        : { subject, body, tier };

      const resp = await fetch(getApiUrl(endpoint), {
        method: 'POST', headers, body: JSON.stringify(payload),
      });
      const data = await resp.json();

      if (resp.ok) {
        const msg = mode === 'single'
          ? `Sent to ${to}`
          : `Sent: ${data.sent}, Failed: ${data.failed}`;
        setResult({ success: true, message: msg });
        setSubject('');
        setBody('');
        setTo('');
      } else {
        setResult({ success: false, message: data.detail || 'Send failed' });
      }
    } catch (e) {
      logger.error('Email send failed:', e);
      setResult({ success: false, message: 'Network error' });
    } finally {
      setSending(false);
    }
  };

  const testSmtp = async () => {
    setTesting(true);
    setResult(null);
    try {
      const resp = await fetch(getApiUrl('admin/email/test'), {
        method: 'POST', headers,
      });
      const data = await resp.json();
      if (resp.ok) {
        setResult({ success: true, message: `Test email sent to ${data.sent_to}` });
      } else {
        setResult({ success: false, message: data.detail || 'SMTP test failed' });
      }
    } catch (e) {
      setResult({ success: false, message: 'Connection failed' });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      {/* Mode toggle + SMTP test */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <button onClick={() => setMode('single')}
            className={`px-4 py-2 rounded-lg text-sm font-bold ${mode === 'single' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'}`}>
            Single Email
          </button>
          <button onClick={() => setMode('broadcast')}
            className={`px-4 py-2 rounded-lg text-sm font-bold ${mode === 'broadcast' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'}`}>
            Broadcast
          </button>
        </div>
        <button onClick={testSmtp} disabled={testing}
          className="px-3 py-1.5 text-xs bg-slate-800 text-slate-400 rounded border border-slate-700 hover:bg-slate-700 disabled:opacity-50">
          {testing ? 'Testing...' : 'Test SMTP'}
        </button>
      </div>

      {/* Result banner */}
      {result && (
        <div className={`px-4 py-3 rounded-lg text-sm font-semibold ${
          result.success ? 'bg-emerald-900/30 text-emerald-400 border border-emerald-700/40' : 'bg-red-900/30 text-red-400 border border-red-700/40'
        }`}>
          {result.success ? '✓' : '✗'} {result.message}
        </div>
      )}

      {/* To field (single mode) or Tier selector (broadcast) */}
      {mode === 'single' ? (
        <div>
          <label className="block text-xs text-slate-500 uppercase tracking-wider mb-1">To</label>
          <input value={to} onChange={e => setTo(e.target.value)} placeholder="user@example.com"
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white text-sm outline-none focus:border-blue-500" />
        </div>
      ) : (
        <div>
          <label className="block text-xs text-slate-500 uppercase tracking-wider mb-1">Send To Tier</label>
          <select value={tier} onChange={e => setTier(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white text-sm">
            <option value="all">All Users</option>
            <option value="user">Members Only</option>
            <option value="admin">Admins Only</option>
          </select>
        </div>
      )}

      {/* Subject */}
      <div>
        <label className="block text-xs text-slate-500 uppercase tracking-wider mb-1">Subject</label>
        <input value={subject} onChange={e => setSubject(e.target.value)} placeholder="Email subject line"
          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white text-sm outline-none focus:border-blue-500" />
      </div>

      {/* Body */}
      <div>
        <label className="block text-xs text-slate-500 uppercase tracking-wider mb-1">Body (HTML supported)</label>
        <textarea value={body} onChange={e => setBody(e.target.value)} rows={8}
          placeholder="Email body content — HTML tags supported"
          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white text-sm outline-none focus:border-blue-500 font-mono" />
      </div>

      {/* Send */}
      <button onClick={sendEmail} disabled={sending || !subject || !body || (mode === 'single' && !to)}
        className="w-full py-3 bg-blue-600 text-white rounded-lg font-bold text-sm hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
        {sending ? 'Sending...' : mode === 'single' ? `Send to ${to || '...'}` : `Broadcast to ${tier === 'all' ? 'All Users' : tier}`}
      </button>
    </div>
  );
}
