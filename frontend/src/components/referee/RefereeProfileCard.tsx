import { X } from 'lucide-react';
import type { RefereeProfile } from '../../types/referee';
import { RefereeTrendBadge } from './RefereeTrendBadge';

interface Props {
  profile: RefereeProfile | undefined;
  loading: boolean;
  onClose: () => void;
}

function pct(val: number | null | undefined): string {
  return val != null ? `${(val * 100).toFixed(1)}%` : '—';
}
function num(val: number | null | undefined, decimals = 1): string {
  return val != null ? val.toFixed(decimals) : '—';
}

function StatBox({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="bg-slate-800/60 border border-slate-700 rounded-lg p-3 text-center">
      <div className={`text-lg font-black ${accent ?? 'text-white'}`}>{value}</div>
      <div className="text-xs text-slate-500 mt-0.5">{label}</div>
    </div>
  );
}

const NFL_AVG_FLAGS = 14.5;

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
          {/* Core betting stats */}
          <div className="grid grid-cols-4 gap-3">
            <StatBox label="GAMES"     value={String(profile.summary.games)} />
            <StatBox label="AVG TOTAL" value={num(profile.summary.avg_total)} />
            <StatBox label="OVER%"     value={pct(profile.summary.over_rate)}
              accent={profile.summary.over_rate != null && profile.summary.over_rate >= 0.58 ? 'text-orange-400' :
                      profile.summary.over_rate != null && profile.summary.over_rate <= 0.42 ? 'text-blue-400' : undefined}
            />
            <StatBox label="HOME CVR%" value={pct(profile.summary.home_cover_pct)}
              accent={profile.summary.home_cover_pct != null && profile.summary.home_cover_pct >= 0.58 ? 'text-green-400' : undefined}
            />
          </div>

          {/* Penalty stats row — only when data is available */}
          {profile.summary.flags_per_game != null && (
            <div>
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Penalty Profile</h3>
              <div className="grid grid-cols-3 gap-3">
                <StatBox label="FLAGS/GAME" value={num(profile.summary.flags_per_game, 1)}
                  accent={profile.summary.flags_per_game > NFL_AVG_FLAGS + 2 ? 'text-red-400' :
                          profile.summary.flags_per_game < NFL_AVG_FLAGS - 2 ? 'text-green-400' : undefined}
                />
                <StatBox label="PEN YDS/G" value={num(profile.summary.yards_per_game, 0)} />
                <StatBox label="HOME BIAS" value={pct(profile.summary.home_bias)}
                  accent={profile.summary.home_bias != null && profile.summary.home_bias > 0.54 ? 'text-yellow-400' : undefined}
                />
              </div>
            </div>
          )}

          {/* Environment row */}
          {(profile.summary.ot_rate != null || profile.summary.dome_pct != null) && (
            <div>
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Environment</h3>
              <div className="grid grid-cols-4 gap-3">
                <StatBox label="OT RATE"    value={pct(profile.summary.ot_rate)} />
                <StatBox label="DOME%"      value={pct(profile.summary.dome_pct)} />
                <StatBox label="PRIMETIME%" value={pct(profile.summary.primetime_pct)} />
                <StatBox label="DIV GAME%"  value={pct(profile.summary.div_game_pct)} />
              </div>
            </div>
          )}

          {/* Season splits */}
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
                      <td className="py-2 text-right text-slate-300 font-mono text-xs">{num(s.avg_total)}</td>
                      <td className="py-2 text-right font-mono text-xs text-slate-300">{pct(s.over_rate)}</td>
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
