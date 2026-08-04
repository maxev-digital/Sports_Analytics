import { useState } from 'react';

export interface MaddenPlayer {
  id: number;
  name: string;
  first_name: string;
  last_name: string;
  position: string;
  pos_group: string;
  ovr: number;
  rating_overall?: number;
  team: string;
  team_name?: string;
  age?: number;
  years_pro?: number;
  rating_speed?: number;
  rating_strength?: number;
  rating_awareness?: number;
  rating_agility?: number;
  rating_acceleration?: number;
  rating_throw_power?: number;
  rating_throw_accuracy_short?: number;
  rating_catching?: number;
  rating_tackle?: number;
  rating_man_coverage?: number;
  rating_zone_coverage?: number;
}

type SortKey = 'ovr' | 'age' | 'rating_speed' | 'rating_strength' | 'rating_awareness'
  | 'rating_agility' | 'rating_acceleration';

interface Props {
  players: MaddenPlayer[];
  showTeam?: boolean;
  showPos?: boolean;
  compact?: boolean;
}

const ATTR_COLS: { key: SortKey; label: string }[] = [
  { key: 'rating_speed',        label: 'SPD' },
  { key: 'rating_strength',     label: 'STR' },
  { key: 'rating_awareness',    label: 'AWR' },
  { key: 'rating_agility',      label: 'AGI' },
  { key: 'rating_acceleration', label: 'ACC' },
];

function ovrColor(ovr: number): string {
  if (ovr >= 90) return 'text-yellow-400 font-bold';
  if (ovr >= 80) return 'text-green-400 font-semibold';
  if (ovr >= 70) return 'text-blue-400';
  return 'text-slate-400';
}

function attrCell(val: number | undefined): React.ReactNode {
  if (val === undefined) return <span className="text-slate-600">—</span>;
  const color = val >= 90 ? 'text-yellow-400' : val >= 80 ? 'text-green-400' : val >= 70 ? 'text-blue-300' : 'text-slate-400';
  return <span className={color}>{val}</span>;
}

export function MaddenPlayerTable({ players, showTeam = true, showPos = true, compact = false }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('ovr');
  const [sortDir, setSortDir] = useState<'desc' | 'asc'>('desc');

  const sorted = [...players].sort((a, b) => {
    const av = (a[sortKey] as number | undefined) ?? 0;
    const bv = (b[sortKey] as number | undefined) ?? 0;
    return sortDir === 'desc' ? bv - av : av - bv;
  });

  function toggleSort(key: SortKey) {
    if (key === sortKey) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortKey(key); setSortDir('desc'); }
  }

  const th = (key: SortKey, label: string) => (
    <th
      key={key}
      onClick={() => toggleSort(key)}
      className="px-3 py-2 text-right text-xs font-semibold text-slate-400 cursor-pointer hover:text-white select-none whitespace-nowrap"
    >
      {label}{sortKey === key ? (sortDir === 'desc' ? ' ↓' : ' ↑') : ''}
    </th>
  );

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-700">
            <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">#</th>
            <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">PLAYER</th>
            {showPos && <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">POS</th>}
            {showTeam && <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">TEAM</th>}
            {th('ovr', 'OVR')}
            {!compact && ATTR_COLS.map(c => th(c.key, c.label))}
            {!compact && <th className="px-3 py-2 text-right text-xs font-semibold text-slate-400">AGE</th>}
          </tr>
        </thead>
        <tbody>
          {sorted.map((p, i) => (
            <tr key={p.id ?? `${p.name}-${i}`} className="border-b border-slate-800 hover:bg-slate-800/40 transition-colors">
              <td className="px-3 py-2 text-slate-500 text-xs">{i + 1}</td>
              <td className="px-3 py-2">
                <span className="font-semibold text-white">{p.name}</span>
              </td>
              {showPos && <td className="px-3 py-2 text-slate-400 text-xs font-mono">{p.position}</td>}
              {showTeam && <td className="px-3 py-2"><span className="text-xs font-bold text-slate-300 bg-slate-700 px-1.5 py-0.5 rounded">{p.team}</span></td>}
              <td className={`px-3 py-2 text-right ${ovrColor(p.ovr)}`}>{p.ovr}</td>
              {!compact && ATTR_COLS.map(c => (
                <td key={c.key} className="px-3 py-2 text-right text-xs">{attrCell(p[c.key] as number | undefined)}</td>
              ))}
              {!compact && <td className="px-3 py-2 text-right text-xs text-slate-400">{p.age ?? '—'}</td>}
            </tr>
          ))}
        </tbody>
      </table>
      {sorted.length === 0 && (
        <div className="py-8 text-center text-slate-500">No players match the current filters.</div>
      )}
    </div>
  );
}
