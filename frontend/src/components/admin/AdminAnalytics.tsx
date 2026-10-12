import { useState, useEffect } from 'react';
import { getApiUrl } from '../../config';
import { logger } from '../../utils/logger';

interface AnalyticsData {
  total_users: number;
  signups_7d: number;
  signups_30d: number;
  active_30d: number;
  tier_counts: Record<string, number>;
  daily_signups: Array<{ date: string; signups: number }>;
}

export function AdminAnalytics({ token }: { token: string | null }) {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(getApiUrl('admin/analytics'), {
      headers: { 'Authorization': `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setData(d); })
      .catch(e => logger.error('Analytics load failed:', e))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return <div className="text-center text-slate-500 py-12">Loading analytics...</div>;
  if (!data) return <div className="text-center text-red-400 py-12">Failed to load analytics</div>;

  const maxSignup = Math.max(...data.daily_signups.map(d => d.signups), 1);

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Users', value: data.total_users, color: 'text-white' },
          { label: 'Signups (7d)', value: data.signups_7d, color: 'text-emerald-400' },
          { label: 'Signups (30d)', value: data.signups_30d, color: 'text-blue-400' },
          { label: 'Active (30d)', value: data.active_30d, color: 'text-yellow-400' },
        ].map(kpi => (
          <div key={kpi.label} className="bg-slate-800/80 border border-slate-700 rounded-xl p-4">
            <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">{kpi.label}</div>
            <div className={`text-3xl font-black ${kpi.color}`}>{kpi.value}</div>
          </div>
        ))}
      </div>

      {/* Tier Distribution */}
      <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-5">
        <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">Tier Distribution</h3>
        <div className="flex gap-4">
          {Object.entries(data.tier_counts).map(([tier, count]) => {
            const pct = data.total_users > 0 ? Math.round((count / data.total_users) * 100) : 0;
            const colors: Record<string, string> = {
              free: 'bg-slate-600', member: 'bg-blue-600', pro: 'bg-emerald-600', admin: 'bg-purple-600',
            };
            return (
              <div key={tier} className="flex-1">
                <div className="flex items-end justify-between mb-1">
                  <span className="text-xs font-bold text-slate-300 uppercase">{tier}</span>
                  <span className="text-xs text-slate-500">{count}</span>
                </div>
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${colors[tier] ?? 'bg-slate-500'}`} style={{ width: `${pct}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Signup Chart (14 days) */}
      <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-5">
        <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">Signups — Last 14 Days</h3>
        <div className="flex items-end gap-1 h-32">
          {data.daily_signups.map(d => {
            const height = maxSignup > 0 ? (d.signups / maxSignup) * 100 : 0;
            const day = new Date(d.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'narrow' });
            return (
              <div key={d.date} className="flex-1 flex flex-col items-center gap-1">
                <span className="text-[10px] text-slate-500">{d.signups > 0 ? d.signups : ''}</span>
                <div className="w-full bg-slate-700 rounded-t" style={{ height: `${Math.max(height, 2)}%` }}>
                  <div className={`w-full h-full rounded-t ${d.signups > 0 ? 'bg-blue-500' : 'bg-slate-700'}`} />
                </div>
                <span className="text-[9px] text-slate-600">{day}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
