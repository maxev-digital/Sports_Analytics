import { useState } from 'react';

export interface ATSRow {
  team: string; season: number; situation: string;
  games: number; ats_wins: number; ats_losses: number; ats_pushes: number;
  ats_pct: number | null;
  ou_over: number; ou_under: number; ou_pushes: number; over_pct: number | null;
  avg_spread: number | null; avg_total: number | null;
  avg_pts_scored: number | null; avg_pts_allowed: number | null;
}

const SITUATIONS = [
  { key: 'overall',      label: 'OVERALL'     },
  { key: 'home',         label: 'HOME'        },
  { key: 'away',         label: 'AWAY'        },
  { key: 'divisional',   label: 'DIVISIONAL'  },
  { key: 'as_favorite',  label: 'FAVORITE'    },
  { key: 'as_underdog',  label: 'UNDERDOG'    },
] as const;

type Situation = (typeof SITUATIONS)[number]['key'];
type SortKey = 'ats_pct' | 'ats_wins' | 'avg_pts_scored' | 'avg_pts_allowed' | 'avg_spread';

function atsBadge(pct: number | null) {
  if (pct === null) return <span className="text-slate-500">—</span>;
  const cls = pct >= 0.6 ? 'text-green-400 font-bold' : pct <= 0.4 ? 'text-red-400 font-bold' : 'text-slate-300';
  return <span className={cls}>{(pct * 100).toFixed(1)}%</span>;
}

interface Props {
  rows: ATSRow[];
  loading: boolean;
  onSelectTeam: (team: string) => void;
  selectedTeam: string | null;
}

export function ATSLeaderboard({ rows, loading, onSelectTeam, selectedTeam }: Props) {
  const [situation, setSituation] = useState<Situation>('overall');
  const [sortKey, setSortKey] = useState<SortKey>('ats_pct');
  const [sortDesc, setSortDesc] = useState(true);

  const filtered = rows.filter(r => r.situation === situation);
  const sorted = [...filtered].sort((a, b) => {
    const av = (a[sortKey] as number | null) ?? -999;
    const bv = (b[sortKey] as number | null) ?? -999;
    return sortDesc ? bv - av : av - bv;
  });

  function toggleSort(k: SortKey) {
    if (k === sortKey) setSortDesc(d => !d);
    else { setSortKey(k); setSortDesc(true); }
  }

  const th = (k: SortKey, label: string, right = true) => (
    <th
      key={k}
      onClick={() => toggleSort(k)}
      className={`px-3 py-2.5 text-xs font-bold text-slate-400 cursor-pointer hover:text-white select-none whitespace-nowrap ${right ? 'text-right' : 'text-left'}`}
    >
      {label}{sortKey === k ? (sortDesc ? ' ↓' : ' ↑') : ''}
    </th>
  );

  return (
    <div className="space-y-3">
      {/* Situation pills */}
      <div className="flex flex-wrap gap-2">
        {SITUATIONS.map(s => (
          <button
            key={s.key}
            onClick={() => setSituation(s.key)}
            className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${
              situation === s.key ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
        {loading ? (
          <div className="py-12 text-center text-slate-500 animate-pulse">Loading ATS data…</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700 bg-slate-800/80">
                  <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400 w-8">#</th>
                  <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400">TEAM</th>
                  <th className="px-3 py-2.5 text-right text-xs font-bold text-slate-400">G</th>
                  <th className="px-3 py-2.5 text-right text-xs font-bold text-slate-400">ATS W-L</th>
                  {th('ats_pct', 'ATS%')}
                  {th('avg_spread', 'AVG LINE')}
                  {th('avg_pts_scored', 'PTS/G')}
                  {th('avg_pts_allowed', 'OPP PTS/G')}
                </tr>
              </thead>
              <tbody>
                {sorted.map((row, i) => (
                  <tr
                    key={row.team}
                    onClick={() => onSelectTeam(row.team === selectedTeam ? '' : row.team)}
                    className={`border-b border-slate-800 cursor-pointer transition-colors ${
                      selectedTeam === row.team ? 'bg-blue-900/30 border-blue-700/50' : 'hover:bg-slate-800/40'
                    }`}
                  >
                    <td className="px-3 py-2.5 text-slate-500 text-xs">{i + 1}</td>
                    <td className="px-3 py-2.5">
                      <span className="font-bold text-white text-sm">{row.team}</span>
                    </td>
                    <td className="px-3 py-2.5 text-right text-slate-400 text-xs">{row.games}</td>
                    <td className="px-3 py-2.5 text-right text-xs font-mono text-slate-300">
                      {row.ats_wins}-{row.ats_losses}{row.ats_pushes > 0 ? `-${row.ats_pushes}` : ''}
                    </td>
                    <td className="px-3 py-2.5 text-right">{atsBadge(row.ats_pct)}</td>
                    <td className="px-3 py-2.5 text-right text-xs text-slate-400">
                      {row.avg_spread !== null ? (row.avg_spread > 0 ? `+${row.avg_spread}` : row.avg_spread) : '—'}
                    </td>
                    <td className="px-3 py-2.5 text-right text-xs text-slate-300">{row.avg_pts_scored ?? '—'}</td>
                    <td className="px-3 py-2.5 text-right text-xs text-slate-300">{row.avg_pts_allowed ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
