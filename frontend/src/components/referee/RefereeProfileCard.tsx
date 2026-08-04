import { X } from 'lucide-react';
import type { RefereeProfile } from '../../types/referee';
import { RefereeTrendBadge } from './RefereeTrendBadge';

interface Props {
  profile: RefereeProfile | undefined;
  loading: boolean;
  onClose: () => void;
}

function pct(val: number | null): string {
  return val !== null ? `${(val * 100).toFixed(1)}%` : '—';
}

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-slate-800/60 border border-slate-700 rounded-lg p-3 text-center">
      <div className="text-lg font-black text-white">{value}</div>
      <div className="text-xs text-slate-500 mt-0.5">{label}</div>
    </div>
  );
}

export function RefereeProfileCard({ profile, loading, onClose }: Props) {
  return (
    <div className="bg-slate-800/70 border border-slate-600 rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          {loading && <div className="text-slate-400 animate-pulse">Loading profile…</div>}
          {profile && (
            <>
              <h2 className="text-xl font-black text-white">{profile.name}</h2>
              <div className="mt-1"><RefereeTrendBadge tendency={profile.summary.tendency} /></div>
            </>
          )}
        </div>
        <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors p-1">
          <X size={18} />
        </button>
      </div>

      {profile && (
        <>
          <div className="grid grid-cols-4 gap-3">
            <StatBox label="GAMES" value={String(profile.summary.games)} />
            <StatBox label="AVG TOTAL" value={profile.summary.avg_total !== null ? profile.summary.avg_total.toFixed(1) : '—'} />
            <StatBox label="OVER%" value={pct(profile.summary.over_rate)} />
            <StatBox label="HOME CVR%" value={pct(profile.summary.home_cover_pct)} />
          </div>

          <div>
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Season Splits</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="py-2 text-left text-xs text-slate-500">SEASON</th>
                    <th className="py-2 text-right text-xs text-slate-500">GAMES</th>
                    <th className="py-2 text-right text-xs text-slate-500">AVG TOTAL</th>
                    <th className="py-2 text-right text-xs text-slate-500">OVER%</th>
                    <th className="py-2 text-right text-xs text-slate-500">HOME CVR%</th>
                  </tr>
                </thead>
                <tbody>
                  {profile.season_splits.map(s => (
                    <tr key={s.season} className="border-b border-slate-800">
                      <td className="py-2 text-white font-bold">{s.season}</td>
                      <td className="py-2 text-right text-slate-300 font-mono text-xs">{s.games}</td>
                      <td className="py-2 text-right text-slate-300 font-mono text-xs">
                        {s.avg_total !== null ? s.avg_total.toFixed(1) : '—'}
                      </td>
                      <td className="py-2 text-right font-mono text-xs font-bold
                        text-slate-300">{pct(s.over_rate)}</td>
                      <td className="py-2 text-right font-mono text-xs text-slate-300">{pct(s.home_cover_pct)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
