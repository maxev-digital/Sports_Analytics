import { useEffect, useState } from 'react';
import { getApiUrl } from '../../config';
import type { ATSRow } from './ATSLeaderboard';

interface Game {
  week: number; gameday: string; opponent: string; location: string;
  team_score: number; opp_score: number; result: number;
  spread_line: number | null; total_line: number | null;
  team_covered: boolean | null; went_over: boolean | null;
  team_qb: string | null;
}

interface TeamProfile {
  team: string; season: number;
  summary: ATSRow | null;
  epa: { total_off_epa: number; pass_epa: number; rush_epa: number; pts_per_game: number; pts_allowed_per_game: number } | null;
  ats_by_situation: ATSRow[];
  games: Game[];
}

const SIT_LABELS: Record<string, string> = {
  overall: 'Overall', home: 'Home', away: 'Away',
  divisional: 'Divisional', as_favorite: 'Fav', as_underdog: 'Dog',
};

function AtsCell({ wins, losses, pct }: { wins: number; losses: number; pct: number | null }) {
  const color = pct !== null && pct >= 0.6 ? 'text-green-400' : pct !== null && pct <= 0.4 ? 'text-red-400' : 'text-slate-300';
  return (
    <div className="text-center">
      <div className={`text-sm font-bold ${color}`}>{wins}-{losses}</div>
      <div className={`text-xs ${color}`}>{pct !== null ? `${(pct * 100).toFixed(0)}%` : '—'}</div>
    </div>
  );
}

interface Props { team: string; season: number; onClose: () => void; }

export function TeamTrendsProfile({ team, season, onClose }: Props) {
  const [profile, setProfile] = useState<TeamProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(getApiUrl(`f5/nfl/team/${team}?season=${season}`))
      .then(r => r.json() as Promise<TeamProfile>)
      .then(setProfile)
      .catch(() => setProfile(null))
      .finally(() => setLoading(false));
  }, [team, season]);

  return (
    <div className="bg-slate-800/80 border border-blue-700/40 rounded-xl p-5 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-black italic text-white">{team}</h2>
          <p className="text-slate-400 text-sm">{season} Season Trends</p>
        </div>
        <button onClick={onClose} className="text-slate-500 hover:text-white text-xl transition-colors">✕</button>
      </div>

      {loading && <div className="py-6 text-center text-slate-500 animate-pulse">Loading {team} profile…</div>}

      {!loading && profile && (
        <>
          {/* ATS by Situation grid */}
          <div>
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">ATS by Situation</div>
            <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
              {profile.ats_by_situation.map(sit => (
                <div key={sit.situation} className="bg-slate-900/60 border border-slate-700 rounded-lg p-2 text-center">
                  <div className="text-[10px] font-bold text-slate-500 uppercase mb-1">{SIT_LABELS[sit.situation] ?? sit.situation}</div>
                  <AtsCell wins={sit.ats_wins} losses={sit.ats_losses} pct={sit.ats_pct} />
                  <div className="text-[10px] text-slate-600 mt-1">{sit.games}g</div>
                </div>
              ))}
            </div>
          </div>

          {/* EPA row */}
          {profile.epa && (
            <div>
              <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Efficiency</div>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                {[
                  { label: 'OFF EPA', val: profile.epa.total_off_epa, color: 'text-green-400' },
                  { label: 'PASS EPA', val: profile.epa.pass_epa, color: 'text-blue-400' },
                  { label: 'RUSH EPA', val: profile.epa.rush_epa, color: 'text-yellow-400' },
                  { label: 'PTS/G', val: profile.epa.pts_per_game, color: 'text-white', decimal: 1 },
                  { label: 'OPP PTS/G', val: profile.epa.pts_allowed_per_game, color: 'text-red-400', decimal: 1 },
                ].map(m => (
                  <div key={m.label} className="bg-slate-900/60 border border-slate-700 rounded-lg p-2 text-center">
                    <div className="text-[10px] font-bold text-slate-500 uppercase mb-1">{m.label}</div>
                    <div className={`text-sm font-bold ${m.color}`}>
                      {m.val !== null ? (m.decimal ? m.val.toFixed(m.decimal) : (m.val > 0 ? '+' : '') + m.val.toFixed(0)) : '—'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Game log */}
          <div>
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Game Log</div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-700 text-slate-500">
                    <th className="px-2 py-1.5 text-left">WK</th>
                    <th className="px-2 py-1.5 text-left">OPP</th>
                    <th className="px-2 py-1.5 text-left">LOC</th>
                    <th className="px-2 py-1.5 text-right">SCORE</th>
                    <th className="px-2 py-1.5 text-right">LINE</th>
                    <th className="px-2 py-1.5 text-right">ATS</th>
                    <th className="px-2 py-1.5 text-right">O/U</th>
                  </tr>
                </thead>
                <tbody>
                  {profile.games.slice(-17).map(g => (
                    <tr key={g.week} className="border-b border-slate-800/50">
                      <td className="px-2 py-1.5 text-slate-500">{g.week}</td>
                      <td className="px-2 py-1.5 font-semibold text-white">{g.opponent}</td>
                      <td className="px-2 py-1.5 text-slate-500">{g.location === 'HOME' ? 'H' : 'A'}</td>
                      <td className="px-2 py-1.5 text-right font-mono">
                        <span className={g.result > 0 ? 'text-green-400' : g.result < 0 ? 'text-red-400' : 'text-slate-400'}>
                          {g.team_score}-{g.opp_score}
                        </span>
                      </td>
                      <td className="px-2 py-1.5 text-right text-slate-400">
                        {g.spread_line !== null ? (g.spread_line > 0 ? `+${g.spread_line}` : g.spread_line) : '—'}
                      </td>
                      <td className="px-2 py-1.5 text-right">
                        {g.team_covered === null ? <span className="text-slate-500">P</span>
                          : g.team_covered ? <span className="text-green-400 font-bold">W</span>
                          : <span className="text-red-400 font-bold">L</span>}
                      </td>
                      <td className="px-2 py-1.5 text-right">
                        {g.went_over === null ? <span className="text-slate-500">P</span>
                          : g.went_over ? <span className="text-orange-400">O</span>
                          : <span className="text-blue-400">U</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
      {!loading && !profile && (
        <div className="py-6 text-center text-slate-500">No data found for {team} in {season}.</div>
      )}
    </div>
  );
}
