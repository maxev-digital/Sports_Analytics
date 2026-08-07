/**
 * Statcast — MLB agent signal verification table.
 * Shows the exact stats the handicapping agent uses: xERA, ERA gap, K%, BB%, wOBA, xwOBA.
 * Sortable by any column. Pulls from DB-backed endpoints with full K%/BB% coverage.
 */
import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getApiUrl } from '../config';

type Tab = 'pitching' | 'batting';
type SortDir = 'asc' | 'desc';

interface PitcherRow {
  name: string; pa: number;
  era: number | null; xera: number | null; era_gap: number | null;
  k_pct: number | null; bb_pct: number | null; k_bb_pct: number | null;
}
interface BatterRow {
  name: string; pa: number;
  woba: number | null; xwoba: number | null; woba_gap: number | null;
}

const N = (v: number | null, dec = 3) => v == null ? '—' : v.toFixed(dec);
const Pct = (v: number | null) => v == null ? '—' : `${(v * 100).toFixed(1)}%`;

function gapColor(gap: number | null, invert = false): string {
  if (gap == null) return 'text-slate-400';
  const pos = invert ? gap < 0 : gap > 0;
  const neg = invert ? gap > 0 : gap < 0;
  if (pos) return 'text-emerald-400';
  if (neg) return 'text-red-400';
  return 'text-slate-400';
}

function eraColor(v: number | null): string {
  if (v == null) return 'text-slate-400';
  if (v <= 3.00) return 'text-emerald-400';
  if (v <= 4.00) return 'text-blue-400';
  return 'text-red-400';
}
function wobaColor(v: number | null): string {
  if (v == null) return 'text-slate-400';
  if (v >= 0.380) return 'text-emerald-400';
  if (v >= 0.330) return 'text-blue-400';
  return 'text-red-400';
}
function kbbColor(v: number | null): string {
  if (v == null) return 'text-slate-400';
  if (v >= 0.20) return 'text-emerald-400';
  if (v >= 0.12) return 'text-blue-400';
  return 'text-red-400';
}

type PitchCol = keyof PitcherRow;
type BatCol   = keyof BatterRow;

function SortTh({ label, col, sortCol, sortDir, onClick, right = true, title }: {
  label: string; col: string; sortCol: string; sortDir: SortDir;
  onClick: (c: string) => void; right?: boolean; title?: string;
}) {
  const active = sortCol === col;
  return (
    <th
      title={title}
      onClick={() => onClick(col)}
      className={`px-3 py-2 cursor-pointer select-none text-xs font-bold tracking-wider uppercase whitespace-nowrap
        ${right ? 'text-right' : 'text-left'}
        ${active ? 'text-blue-400' : 'text-slate-400 hover:text-slate-200'}`}
    >
      {label}{active ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}
    </th>
  );
}

function PitchingTable({ rows }: { rows: PitcherRow[] }) {
  const [sortCol, setSortCol] = useState<PitchCol>('xera');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [minPA, setMinPA] = useState(100);

  const sorted = useMemo(() => {
    const filtered = rows.filter(r => r.pa >= minPA);
    return [...filtered].sort((a, b) => {
      const av = (a[sortCol] as number) ?? (sortDir === 'asc' ? Infinity : -Infinity);
      const bv = (b[sortCol] as number) ?? (sortDir === 'asc' ? Infinity : -Infinity);
      return sortDir === 'asc' ? av - bv : bv - av;
    });
  }, [rows, sortCol, sortDir, minPA]);

  function toggle(col: string) {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortCol(col as PitchCol); setSortDir(col === 'era_gap' ? 'desc' : 'asc'); }
  }

  const thProps = (col: string, label: string, title?: string) =>
    ({ col, label, sortCol, sortDir, onClick: toggle, title } as const);

  return (
    <div>
      <div className="flex items-center gap-4 mb-3">
        <span className="text-xs text-slate-400 uppercase tracking-wider font-bold">Min PA</span>
        {[50, 100, 200, 300].map(v => (
          <button key={v} onClick={() => setMinPA(v)}
            className={`px-3 py-1 rounded text-xs font-bold ${minPA === v ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}>
            {v}
          </button>
        ))}
        <span className="ml-auto text-xs text-slate-500">{sorted.length} pitchers</span>
      </div>
      <div className="overflow-x-auto rounded-lg border border-slate-700">
        <table className="w-full text-sm border-collapse">
          <thead className="bg-slate-900 border-b border-slate-700">
            <tr>
              <th className="px-3 py-2 text-xs font-bold text-slate-400 text-right w-10">#</th>
              <SortTh {...thProps('name','PLAYER')} right={false} />
              <SortTh {...thProps('pa','PA','Batters faced')} />
              <SortTh {...thProps('era','ERA','Earned run average (actual)')} />
              <SortTh {...thProps('xera','xERA','Expected ERA based on contact quality — agent primary anchor')} />
              <SortTh {...thProps('era_gap','ERA GAP','ERA minus xERA. Positive = pitching worse than expected (regression risk). Negative = pitching better than deserved (buy).')} />
              <SortTh {...thProps('k_pct','K%','Strikeout rate (K per batter faced)')} />
              <SortTh {...thProps('bb_pct','BB%','Walk rate (BB per batter faced)')} />
              <SortTh {...thProps('k_bb_pct','K-BB%','K% minus BB% — command quality metric. Agent uses ≥20% as elite.')} />
            </tr>
          </thead>
          <tbody>
            {sorted.map((p, i) => (
              <tr key={p.name} className="border-b border-slate-800 hover:bg-slate-800/40">
                <td className="px-3 py-2 text-right text-slate-500 text-xs font-mono">{i + 1}</td>
                <td className="px-3 py-2 font-semibold text-white whitespace-nowrap">{p.name}</td>
                <td className="px-3 py-2 text-right text-slate-400 font-mono text-xs">{p.pa}</td>
                <td className={`px-3 py-2 text-right font-mono font-bold ${eraColor(p.era)}`}>{N(p.era)}</td>
                <td className={`px-3 py-2 text-right font-mono font-bold ${eraColor(p.xera)}`}>{N(p.xera)}</td>
                <td className={`px-3 py-2 text-right font-mono font-bold ${gapColor(p.era_gap, true)}`}>
                  {p.era_gap != null ? (p.era_gap > 0 ? '+' : '') + p.era_gap.toFixed(2) : '—'}
                </td>
                <td className={`px-3 py-2 text-right font-mono ${p.k_pct != null && p.k_pct >= 0.26 ? 'text-emerald-400 font-bold' : 'text-slate-300'}`}>{Pct(p.k_pct)}</td>
                <td className={`px-3 py-2 text-right font-mono ${p.bb_pct != null && p.bb_pct >= 0.10 ? 'text-red-400' : 'text-slate-300'}`}>{Pct(p.bb_pct)}</td>
                <td className={`px-3 py-2 text-right font-mono font-bold ${kbbColor(p.k_bb_pct)}`}>{Pct(p.k_bb_pct)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function BattingTable({ rows }: { rows: BatterRow[] }) {
  const [sortCol, setSortCol] = useState<BatCol>('xwoba');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [minPA, setMinPA] = useState(100);

  const sorted = useMemo(() => {
    const filtered = rows.filter(r => r.pa >= minPA);
    return [...filtered].sort((a, b) => {
      const av = (a[sortCol] as number) ?? (sortDir === 'asc' ? Infinity : -Infinity);
      const bv = (b[sortCol] as number) ?? (sortDir === 'asc' ? Infinity : -Infinity);
      return sortDir === 'asc' ? av - bv : bv - av;
    });
  }, [rows, sortCol, sortDir, minPA]);

  function toggle(col: string) {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortCol(col as BatCol); setSortDir(col === 'woba_gap' ? 'asc' : 'desc'); }
  }

  const thProps = (col: string, label: string, title?: string) =>
    ({ col, label, sortCol, sortDir, onClick: toggle, title } as const);

  return (
    <div>
      <div className="flex items-center gap-4 mb-3">
        <span className="text-xs text-slate-400 uppercase tracking-wider font-bold">Min PA</span>
        {[50, 100, 200, 300].map(v => (
          <button key={v} onClick={() => setMinPA(v)}
            className={`px-3 py-1 rounded text-xs font-bold ${minPA === v ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}>
            {v}
          </button>
        ))}
        <span className="ml-auto text-xs text-slate-500">{sorted.length} batters</span>
      </div>
      <div className="overflow-x-auto rounded-lg border border-slate-700">
        <table className="w-full text-sm border-collapse">
          <thead className="bg-slate-900 border-b border-slate-700">
            <tr>
              <th className="px-3 py-2 text-xs font-bold text-slate-400 text-right w-10">#</th>
              <SortTh {...thProps('name','PLAYER')} right={false} />
              <SortTh {...thProps('pa','PA','Plate appearances')} />
              <SortTh {...thProps('woba','wOBA','Weighted on-base average (actual — includes luck)')} />
              <SortTh {...thProps('xwoba','xwOBA','Expected wOBA based on contact quality — agent primary anchor for offense')} />
              <SortTh {...thProps('woba_gap','GAP','wOBA minus xwOBA. Positive = lucky/hot streak. Negative = unlucky, due for positive regression.')} />
            </tr>
          </thead>
          <tbody>
            {sorted.map((p, i) => (
              <tr key={p.name} className="border-b border-slate-800 hover:bg-slate-800/40">
                <td className="px-3 py-2 text-right text-slate-500 text-xs font-mono">{i + 1}</td>
                <td className="px-3 py-2 font-semibold text-white whitespace-nowrap">{p.name}</td>
                <td className="px-3 py-2 text-right text-slate-400 font-mono text-xs">{p.pa}</td>
                <td className={`px-3 py-2 text-right font-mono ${wobaColor(p.woba)}`}>{N(p.woba)}</td>
                <td className={`px-3 py-2 text-right font-mono font-bold ${wobaColor(p.xwoba)}`}>{N(p.xwoba)}</td>
                <td className={`px-3 py-2 text-right font-mono font-bold ${gapColor(p.woba_gap)}`}>
                  {p.woba_gap != null ? (p.woba_gap > 0 ? '+' : '') + p.woba_gap.toFixed(3) : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function Statcast() {
  const [tab, setTab] = useState<Tab>('pitching');

  const { data: pitchData, isLoading: pitchLoading } = useQuery({
    queryKey: ['statcast-pitching-db'],
    queryFn: () => fetch(getApiUrl('analytics-data/statcast/pitching-db?min_pa=1&year=2025')).then(r => r.json()),
    staleTime: 6 * 60 * 60 * 1000,
  });
  const { data: batData, isLoading: batLoading } = useQuery({
    queryKey: ['statcast-batting-db'],
    queryFn: () => fetch(getApiUrl('analytics-data/statcast/batting-db?min_pa=1&year=2025')).then(r => r.json()),
    staleTime: 6 * 60 * 60 * 1000,
  });

  const pitchers: PitcherRow[] = pitchData?.pitchers ?? [];
  const batters: BatterRow[]   = batData?.batters ?? [];
  const loading = tab === 'pitching' ? pitchLoading : batLoading;

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-black italic text-white mb-1">STATCAST</h1>
          <p className="text-slate-400 text-sm">
            Exact MLB metrics the handicapping agent uses — xERA, ERA gap, K%, BB%, xwOBA, wOBA gap.
            Click any column header to sort. Color: <span className="text-emerald-400">green = elite</span> · <span className="text-blue-400">blue = solid</span> · <span className="text-red-400">red = weak</span>
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {(['pitching', 'batting'] as Tab[]).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-5 py-2 rounded-lg font-bold text-sm uppercase italic transition-all
                ${tab === t ? 'bg-blue-600 text-white shadow-lg' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}>
              {t}
            </button>
          ))}
        </div>

        {/* Agent signal legend */}
        <div className="mb-4 p-3 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-400 leading-relaxed">
          {tab === 'pitching'
            ? <><span className="text-blue-400 font-bold">xERA</span> = agent primary anchor (strips luck from ERA). <span className="text-blue-400 font-bold">ERA GAP</span> = ERA–xERA: negative means pitching better than deserved (buy); positive means regression risk (fade). <span className="text-blue-400 font-bold">K-BB%</span> ≥20% = elite command signal.</>
            : <><span className="text-blue-400 font-bold">xwOBA</span> = agent primary offensive anchor (contact quality). <span className="text-blue-400 font-bold">GAP</span> = wOBA–xwOBA: negative means unlucky, positive regression incoming; positive means hot streak above expected (fade risk).</>
          }
        </div>

        {loading ? (
          <div className="text-center py-20 text-slate-500">Loading Statcast data...</div>
        ) : tab === 'pitching' ? (
          <PitchingTable rows={pitchers} />
        ) : (
          <BattingTable rows={batters} />
        )}
      </div>
    </div>
  );
}

export default Statcast;
