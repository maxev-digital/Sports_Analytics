import { useState, useEffect, useMemo } from 'react';
import { getApiUrl } from '../config';

interface MLBTeam {
  team: string;
  abbr?: string;
  division?: string;
  wins?: number;
  losses?: number;
  pct?: number;
  differential?: number;
  streak?: string;
  last10?: string;
  // F5 stats
  games?: number;
  fg_record?: string;
  fg_win_pct?: number;
  fg_rpg?: number;
  fg_rapg?: number;
  fg_diff?: number;
  f5_record?: string;
  f5_win_pct?: number;
  f5_rpg?: number;
  f5_rapg?: number;
  f5_diff?: number;
  f5_under_5_pct?: number;
  blowout_pct?: number;
  // Efficiency stats (ESPN — what the agents use per game)
  era?: number | null;
  whip?: number | null;
  ops?: number | null;
  batting_avg?: number | null;
  runs_per_game?: number | null;
  opp_ops_allowed?: number | null;
}

type SortKey = keyof MLBTeam;
type SortDir = 'asc' | 'desc';

const COLS: { key: SortKey; label: string; title: string; defaultDir: SortDir }[] = [
  { key: 'wins',            label: 'W-L',          title: 'Wins and losses',                          defaultDir: 'desc' },
  { key: 'team',            label: 'TEAM',          title: 'Team name',                                defaultDir: 'asc'  },
  { key: 'division',        label: 'DIV',           title: 'Division',                                 defaultDir: 'asc'  },
  { key: 'pct',             label: 'W%',            title: 'Win percentage',                           defaultDir: 'desc' },
  { key: 'differential',    label: 'RD/G',          title: 'Run differential per game',                defaultDir: 'desc' },
  { key: 'streak',          label: 'STREAK',        title: 'Current streak',                           defaultDir: 'asc'  },
  { key: 'last10',          label: 'L10',           title: 'Last 10 games record',                     defaultDir: 'asc'  },
  { key: 'fg_rpg',          label: 'RPG',           title: 'Runs per game (full game)',                defaultDir: 'desc' },
  { key: 'fg_rapg',         label: 'RA/G',          title: 'Runs allowed per game (full game)',        defaultDir: 'asc'  },
  { key: 'fg_diff',         label: 'FG DIFF',       title: 'Full game run differential per game',      defaultDir: 'desc' },
  { key: 'fg_win_pct',      label: 'FG ATS%',       title: 'Full game ATS win percentage',             defaultDir: 'desc' },
  { key: 'f5_rpg',          label: 'F5 RPG',        title: 'Runs per game (first 5 innings)',          defaultDir: 'desc' },
  { key: 'f5_rapg',         label: 'F5 RA/G',       title: 'Runs allowed per game (first 5 innings)',  defaultDir: 'asc'  },
  { key: 'f5_diff',         label: 'F5 DIFF',       title: 'F5 run differential per game',             defaultDir: 'desc' },
  { key: 'f5_win_pct',      label: 'F5 W%',         title: 'F5 innings ATS win percentage',            defaultDir: 'desc' },
  { key: 'f5_under_5_pct',  label: 'F5 U5%',        title: 'F5 under 5 runs total percentage',         defaultDir: 'desc' },
  { key: 'blowout_pct',     label: 'BLOWOUT%',      title: 'Games won/lost by 5+ runs',                defaultDir: 'desc' },
  // Pitching cols
  { key: 'era',             label: 'ERA',           title: 'Team ERA — agent uses for run projection', defaultDir: 'asc'  },
  { key: 'whip',            label: 'WHIP',          title: 'Walks+Hits per inning pitched',            defaultDir: 'asc'  },
  { key: 'opp_ops_allowed', label: 'OPP OPS',       title: 'Opponent OPS allowed (pitching quality)',  defaultDir: 'asc'  },
  // Batting cols
  { key: 'ops',             label: 'OPS',           title: 'On-base + slugging (offensive power)',     defaultDir: 'desc' },
  { key: 'batting_avg',     label: 'AVG',           title: 'Team batting average',                     defaultDir: 'desc' },
  { key: 'runs_per_game',   label: 'R/G',           title: 'Runs scored per game',                     defaultDir: 'desc' },
];

function fmt(v: number | null | undefined, dec = 2): string {
  if (v === null || v === undefined) return '—';
  return v.toFixed(dec);
}
function fmtPct(v: number | null | undefined): string {
  if (v === null || v === undefined) return '—';
  return `${v.toFixed(1)}%`;
}
function fmtDiff(v: number | null | undefined): string {
  if (v === null || v === undefined) return '—';
  return v >= 0 ? `+${v.toFixed(2)}` : v.toFixed(2);
}

export function MLBTeamStats() {
  const [teams, setTeams] = useState<MLBTeam[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('wins');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [search, setSearch] = useState('');
  const [view, setView] = useState<'standings' | 'fg' | 'f5' | 'pitching' | 'batting'>('standings');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(getApiUrl('analytics-data/standings/MLB')).then(r => r.json()),
      fetch(getApiUrl('f5/team-rankings?sport=mlb')).then(r => r.json()),
      fetch(getApiUrl('league-data/mlb/efficiency')).then(r => r.json()),
    ])
      .then(([standings, f5, eff]) => {
        const standMap: Record<string, MLBTeam> = {};
        for (const t of (standings.teams || [])) standMap[t.team] = t;

        const effMap: Record<string, MLBTeam> = {};
        for (const t of (eff.teams || [])) effMap[t.team] = t;

        // Start from f5 list, merge standings and efficiency
        const merged: MLBTeam[] = (f5.teams || []).map((f: MLBTeam) => ({
          ...standMap[f.team] || {},
          ...f,
          era: effMap[f.team]?.era ?? null,
          whip: effMap[f.team]?.whip ?? null,
          ops: effMap[f.team]?.ops ?? null,
          batting_avg: effMap[f.team]?.batting_avg ?? null,
          runs_per_game: effMap[f.team]?.runs_per_game ?? null,
          opp_ops_allowed: effMap[f.team]?.opp_ops_allowed ?? null,
        }));

        // Add any standings teams not in f5
        for (const t of (standings.teams || [])) {
          if (!merged.find(m => m.team === t.team)) {
            merged.push({
              ...t,
              era: effMap[t.team]?.era ?? null,
              whip: effMap[t.team]?.whip ?? null,
              ops: effMap[t.team]?.ops ?? null,
              batting_avg: effMap[t.team]?.batting_avg ?? null,
              runs_per_game: effMap[t.team]?.runs_per_game ?? null,
              opp_ops_allowed: effMap[t.team]?.opp_ops_allowed ?? null,
            });
          }
        }

        // Add any efficiency teams not yet in list
        for (const t of (eff.teams || [])) {
          if (!merged.find(m => m.team === t.team)) {
            merged.push({
              team: t.team,
              era: t.era,
              whip: t.whip,
              ops: t.ops,
              batting_avg: t.batting_avg,
              runs_per_game: t.runs_per_game,
              opp_ops_allowed: t.opp_ops_allowed,
            });
          }
        }

        setTeams(merged);
        setLoading(false);
      })
      .catch(() => { setError('Failed to load MLB stats'); setLoading(false); });
  }, []);

  const handleSort = (key: SortKey, defaultDir: SortDir) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir(defaultDir);
    }
  };

  const sorted = useMemo(() => {
    const filtered = search
      ? teams.filter(t => t.team?.toLowerCase().includes(search.toLowerCase()))
      : teams;
    return [...filtered].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av === null || av === undefined) return 1;
      if (bv === null || bv === undefined) return -1;
      const cmp = typeof av === 'string' ? av.localeCompare(bv as string) : (av as number) - (bv as number);
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [teams, sortKey, sortDir, search]);

  const arrow = (key: SortKey) => sortKey === key ? (sortDir === 'asc' ? ' ↑' : ' ↓') : '';

  const viewCols = {
    standings: ['wins', 'team', 'division', 'pct', 'differential', 'streak', 'last10'],
    fg:        ['wins', 'team', 'fg_rpg', 'fg_rapg', 'fg_diff', 'fg_win_pct', 'blowout_pct'],
    f5:        ['wins', 'team', 'f5_rpg', 'f5_rapg', 'f5_diff', 'f5_win_pct', 'f5_under_5_pct'],
    pitching:  ['team', 'era', 'whip', 'opp_ops_allowed'],
    batting:   ['team', 'ops', 'batting_avg', 'runs_per_game'],
  } as Record<string, string[]>;

  const activeCols = COLS.filter(c => viewCols[view].includes(c.key));

  const renderCell = (t: MLBTeam, key: SortKey) => {
    const v = t[key];
    switch (key) {
      case 'wins': return <span className="font-bold text-white">{t.wins !== undefined ? `${t.wins}-${t.losses}` : '—'}</span>;
      case 'team': return <span className="font-semibold text-white">{t.team}</span>;
      case 'division': return <span className="text-slate-400 text-xs">{t.division?.replace('League', '').trim() || '—'}</span>;
      case 'pct': return <span className={`font-bold ${(v as number) >= 0.550 ? 'text-emerald-400' : (v as number) >= 0.500 ? 'text-blue-400' : 'text-red-400'}`}>{v !== undefined && v !== null ? (v as number).toFixed(3) : '—'}</span>;
      case 'differential': return <span className={`font-bold ${(v as number) >= 0.5 ? 'text-emerald-400' : (v as number) < -0.5 ? 'text-red-400' : 'text-slate-300'}`}>{fmtDiff(v as number)}</span>;
      case 'streak': return <span className={`font-bold text-sm ${String(v).startsWith('W') ? 'text-emerald-400' : 'text-red-400'}`}>{String(v || '—')}</span>;
      case 'last10': return <span className="text-slate-300 text-sm">{String(v || '—')}</span>;
      case 'fg_rpg': return <span className={`font-semibold ${(v as number) >= 5.0 ? 'text-emerald-400' : (v as number) >= 4.0 ? 'text-blue-400' : 'text-slate-300'}`}>{fmt(v as number)}</span>;
      case 'fg_rapg': return <span className={`font-semibold ${(v as number) <= 3.5 ? 'text-emerald-400' : (v as number) >= 5.0 ? 'text-red-400' : 'text-slate-300'}`}>{fmt(v as number)}</span>;
      case 'fg_diff': return <span className={`font-bold ${(v as number) >= 0.5 ? 'text-emerald-400' : (v as number) <= -0.5 ? 'text-red-400' : 'text-slate-300'}`}>{fmtDiff(v as number)}</span>;
      case 'fg_win_pct': return <span className={`font-bold ${(v as number) >= 55 ? 'text-emerald-400' : (v as number) >= 50 ? 'text-blue-400' : 'text-red-400'}`}>{fmtPct(v as number)}</span>;
      case 'f5_rpg': return <span className={`font-semibold ${(v as number) >= 2.8 ? 'text-emerald-400' : (v as number) >= 2.2 ? 'text-blue-400' : 'text-slate-300'}`}>{fmt(v as number)}</span>;
      case 'f5_rapg': return <span className={`font-semibold ${(v as number) <= 1.8 ? 'text-emerald-400' : (v as number) >= 2.8 ? 'text-red-400' : 'text-slate-300'}`}>{fmt(v as number)}</span>;
      case 'f5_diff': return <span className={`font-bold ${(v as number) >= 0.5 ? 'text-emerald-400' : (v as number) <= -0.5 ? 'text-red-400' : 'text-slate-300'}`}>{fmtDiff(v as number)}</span>;
      case 'f5_win_pct': return <span className={`font-bold ${(v as number) >= 55 ? 'text-emerald-400' : (v as number) >= 50 ? 'text-blue-400' : 'text-red-400'}`}>{fmtPct(v as number)}</span>;
      case 'f5_under_5_pct': return <span className="text-slate-300">{fmtPct(v as number)}</span>;
      case 'blowout_pct': return <span className="text-slate-400">{fmtPct(v as number)}</span>;
      // Pitching
      case 'era':
        return <span className={`font-bold ${v !== null && (v as number) <= 3.50 ? 'text-emerald-400' : v !== null && (v as number) <= 4.20 ? 'text-blue-400' : 'text-red-400'}`}>{fmt(v as number, 3)}</span>;
      case 'whip':
        return <span className={`font-semibold ${v !== null && (v as number) <= 1.15 ? 'text-emerald-400' : v !== null && (v as number) <= 1.30 ? 'text-blue-400' : 'text-red-400'}`}>{fmt(v as number, 3)}</span>;
      case 'opp_ops_allowed':
        return <span className={`font-semibold ${v !== null && (v as number) <= 0.680 ? 'text-emerald-400' : v !== null && (v as number) <= 0.730 ? 'text-blue-400' : 'text-red-400'}`}>{fmt(v as number, 3)}</span>;
      // Batting
      case 'ops':
        return <span className={`font-bold ${v !== null && (v as number) >= 0.780 ? 'text-emerald-400' : v !== null && (v as number) >= 0.720 ? 'text-blue-400' : 'text-red-400'}`}>{fmt(v as number, 3)}</span>;
      case 'batting_avg':
        return <span className={`font-semibold ${v !== null && (v as number) >= 0.270 ? 'text-emerald-400' : v !== null && (v as number) >= 0.245 ? 'text-blue-400' : 'text-red-400'}`}>{fmt(v as number, 3)}</span>;
      case 'runs_per_game':
        return <span className={`font-bold ${v !== null && (v as number) >= 5.0 ? 'text-emerald-400' : v !== null && (v as number) >= 4.2 ? 'text-blue-400' : 'text-red-400'}`}>{fmt(v as number, 2)}</span>;
      default: return <span className="text-slate-400">{String(v ?? '—')}</span>;
    }
  };

  const VIEW_LABELS: Record<string, string> = {
    standings: 'STANDINGS',
    fg: 'FULL GAME',
    f5: 'F5 INNINGS',
    pitching: 'PITCHING',
    batting: 'BATTING',
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="max-w-[1400px] mx-auto px-4 py-8">

        <div className="mb-6">
          <h1 className="text-3xl font-black italic text-white mb-1">MLB TEAM STATS</h1>
          <p className="text-slate-400 text-sm">All 30 teams — standings, F5 splits, and the live ESPN metrics the agent uses for run projection (ERA, WHIP, OPS). Click headers to sort.</p>
        </div>

        <div className="flex flex-wrap items-center gap-2 mb-4">
          {(['standings', 'fg', 'f5', 'pitching', 'batting'] as const).map(v => (
            <button
              key={v}
              onClick={() => {
                setView(v);
                if (v === 'pitching') { setSortKey('era'); setSortDir('asc'); }
                if (v === 'batting') { setSortKey('ops'); setSortDir('desc'); }
              }}
              className={`px-4 py-2 rounded-lg text-sm font-bold italic transition-all ${
                view === v ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {VIEW_LABELS[v]}
            </button>
          ))}
          <div className="ml-auto flex items-center gap-3">
            <input
              type="text"
              placeholder="Search team..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 w-48 focus:outline-none focus:border-blue-500"
            />
            <span className="text-slate-500 text-sm">{sorted.length} teams</span>
          </div>
        </div>

        {(view === 'pitching' || view === 'batting') && (
          <div className="mb-3 bg-blue-950/30 border border-blue-800/50 rounded-lg px-4 py-2 text-xs text-blue-300">
            Live ESPN data — these are the exact metrics the handicapping agent pulls per game for MLB run projection.
            {view === 'pitching' && ' ERA + WHIP + Opp OPS are used to project runs allowed and determine game total lean.'}
            {view === 'batting' && ' OPS + batting avg + R/G are used to project offense output against tonight\'s starter.'}
          </div>
        )}

        {loading && <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" /></div>}
        {error && <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 text-red-400">{error}</div>}

        {!loading && !error && (
          <div className="overflow-x-auto rounded-xl border border-slate-700 shadow-2xl">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-900 border-b border-slate-700">
                  {activeCols.map(col => (
                    <th
                      key={col.key}
                      onClick={() => handleSort(col.key, col.defaultDir)}
                      title={col.title}
                      className={`px-3 py-3 text-left font-bold italic text-slate-300 cursor-pointer select-none whitespace-nowrap hover:text-white transition-colors ${
                        sortKey === col.key ? 'text-blue-400' : ''
                      } ${col.key === 'team' ? 'min-w-[160px]' : ''}`}
                    >
                      {col.label}{arrow(col.key)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sorted.map((t, i) => (
                  <tr key={t.team} className={`border-b border-slate-800 hover:bg-slate-800/40 transition-colors ${i % 2 === 0 ? 'bg-slate-900/30' : 'bg-black/20'}`}>
                    {activeCols.map(col => (
                      <td key={col.key} className="px-3 py-2.5">
                        {renderCell(t, col.key)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="mt-4 flex flex-wrap gap-4 text-xs text-slate-500">
          <span><span className="text-emerald-400">Green</span> = strong performance</span>
          <span><span className="text-red-400">Red</span> = weak performance</span>
          <span>F5 = First 5 Innings | ERA = Earned Run Average | OPS = On-base + Slugging | WHIP = Walks+Hits/IP</span>
        </div>
      </div>
    </div>
  );
}
