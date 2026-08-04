import { useEffect, useState } from 'react';
import { getApiUrl } from '../../config';
import type { MaddenPlayer } from './MaddenPlayerTable';

const POSITIONS = [
  { group: 'QB', label: 'Quarterbacks' },
  { group: 'RB', label: 'Running Backs' },
  { group: 'WR', label: 'Wide Receivers' },
  { group: 'TE', label: 'Tight Ends' },
  { group: 'OL', label: 'O-Line' },
  { group: 'DL', label: 'D-Line' },
  { group: 'LB', label: 'Linebackers' },
  { group: 'DB', label: 'Defensive Backs' },
  { group: 'K',  label: 'Kickers' },
  { group: 'P',  label: 'Punters' },
] as const;

function ovrBadge(ovr: number) {
  const cls = ovr >= 90 ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40'
    : ovr >= 80 ? 'bg-green-500/20 text-green-400 border-green-500/40'
    : 'bg-blue-500/20 text-blue-400 border-blue-500/40';
  return (
    <span className={`text-xs font-bold px-1.5 py-0.5 rounded border ${cls}`}>{ovr}</span>
  );
}

interface TopData {
  players: MaddenPlayer[];
}

export function MaddenPositionLeaders() {
  const [data, setData] = useState<Record<string, MaddenPlayer[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const limit = 5;
    Promise.all(
      POSITIONS.map(p =>
        fetch(getApiUrl(`f5/madden/top?pos=${p.group}&limit=${limit}`))
          .then(r => r.json() as Promise<TopData>)
          .then(d => ({ group: p.group, players: d.players ?? [] }))
          .catch(() => ({ group: p.group, players: [] }))
      )
    ).then(results => {
      const map: Record<string, MaddenPlayer[]> = {};
      results.forEach(r => { map[r.group] = r.players; });
      setData(map);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {POSITIONS.map(p => (
          <div key={p.group} className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 animate-pulse h-40" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
      {POSITIONS.map(pos => {
        const players = data[pos.group] ?? [];
        return (
          <div key={pos.group} className="bg-slate-800/50 border border-slate-700 rounded-lg p-3">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 pb-2 border-b border-slate-700">
              {pos.label}
            </div>
            <ol className="space-y-1.5">
              {players.map((p, i) => (
                <li key={p.id ?? `${p.name}-${i}`} className="flex items-center justify-between gap-1">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="text-[10px] text-slate-600 w-3 flex-shrink-0">{i + 1}.</span>
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-white truncate">{p.last_name}</div>
                      <div className="text-[10px] text-slate-500">{p.team} · {p.position}</div>
                    </div>
                  </div>
                  {ovrBadge(p.ovr)}
                </li>
              ))}
              {players.length === 0 && (
                <li className="text-xs text-slate-600 italic">No data</li>
              )}
            </ol>
          </div>
        );
      })}
    </div>
  );
}
