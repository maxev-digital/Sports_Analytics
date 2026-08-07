import { useState, useEffect, useMemo } from 'react';
import { getApiUrl } from '../config';

interface NFLTeam {
  team: string;
  // ATS data from f5
  ats_record?: string;
  ats_cover_pct?: number;
  home_ats?: string;
  home_ats_pct?: number;
  away_ats?: string;
  away_ats_pct?: number;
  fav_ats?: string;
  fav_cover_pct?: number;
  dog_ats?: string;
  dog_cover_pct?: number;
  ou_record?: string;
  over_pct?: number;
  avg_total?: number;
  record?: string;
  win_pct?: number;
  division_record?: string;
  primetime_record?: string;
  primetime_win_pct?: number;
  short_rest_record?: string;
  short_rest_win_pct?: number;
  // Power ratings from league-data
  sp_rating?: number | null;
  sp_offense?: number | null;
  sp_defense?: number | null;
  dvoa_total?: number | null;
  // Efficiency stats (ESPN — what the agents use per game)
  ypp_season?: number | null;
  ypc_season?: number | null;
  off_yds_per_game?: number | null;
  plays_per_game?: number | null;
  pass_rate?: number | null;
  red_zone_pct?: number | null;
  third_down_pct?: number | null;
}

type SortKey = keyof NFLTeam;
type SortDir = 'asc' | 'desc';

const COLS: { key: SortKey; label: string; title: string; defaultDir: SortDir }[] = [
  { key: 'team',             label: 'TEAM',          title: 'Team',                                    defaultDir: 'asc'  },
  { key: 'record',           label: 'RECORD',         title: 'Win-loss record',                         defaultDir: 'desc' },
  { key: 'ats_record',       label: 'ATS',            title: 'Against the spread record',               defaultDir: 'asc'  },
  { key: 'ats_cover_pct',    label: 'ATS%',           title: 'ATS cover percentage',                    defaultDir: 'desc' },
  { key: 'home_ats_pct',     label: 'HOME ATS%',      title: 'Home ATS cover percentage',               defaultDir: 'desc' },
  { key: 'away_ats_pct',     label: 'AWAY ATS%',      title: 'Away ATS cover percentage',               defaultDir: 'desc' },
  { key: 'fav_cover_pct',    label: 'FAV ATS%',       title: 'ATS cover % as favorite',                 defaultDir: 'desc' },
  { key: 'dog_cover_pct',    label: 'DOG ATS%',       title: 'ATS cover % as underdog',                 defaultDir: 'desc' },
  { key: 'over_pct',         label: 'OVER%',          title: 'Over/under over percentage',              defaultDir: 'desc' },
  { key: 'avg_total',        label: 'AVG TOT',        title: 'Average game total',                      defaultDir: 'desc' },
  { key: 'primetime_win_pct',label: 'PRIME%',         title: 'Primetime game win percentage',           defaultDir: 'desc' },
  { key: 'short_rest_win_pct',label:'SHORT REST%',    title: 'Short rest game win percentage',          defaultDir: 'desc' },
  { key: 'sp_rating',        label: 'POWER RTG',      title: 'SP+ power rating (efficiency-based)',     defaultDir: 'desc' },
  { key: 'sp_offense',       label: 'OFF RTG',        title: 'SP+ offensive efficiency rating',         defaultDir: 'desc' },
  { key: 'sp_defense',       label: 'DEF RTG',        title: 'SP+ defensive efficiency rating',         defaultDir: 'asc'  },
  // Efficiency cols
  { key: 'ypp_season',       label: 'YPP',            title: 'Yards per play (offense) — agent signal', defaultDir: 'desc' },
  { key: 'ypc_season',       label: 'YPC',            title: 'Yards per carry (rushing)',               defaultDir: 'desc' },
  { key: 'off_yds_per_game', label: 'YDS/G',          title: 'Offensive yards per game',                defaultDir: 'desc' },
  { key: 'plays_per_game',   label: 'PLAYS/G',        title: 'Total offensive plays per game (pace)',   defaultDir: 'desc' },
  { key: 'pass_rate',        label: 'PASS%',          title: 'Pass attempt rate (pass att / total plays)', defaultDir: 'desc' },
  { key: 'red_zone_pct',     label: 'RZ%',            title: 'Red zone scoring % — agent signal',       defaultDir: 'desc' },
  { key: 'third_down_pct',   label: '3RD%',           title: '3rd down conversion % — agent signal',    defaultDir: 'desc' },
];

function fmtPct(v: number | null | undefined, asDecimal = false): string {
  if (v === null || v === undefined) return '—';
  return asDecimal ? `${(v * 100).toFixed(1)}%` : `${v.toFixed(1)}%`;
}
function fmt(v: number | null | undefined, dec = 1): string {
  if (v === null || v === undefined) return '—';
  return v.toFixed(dec);
}

export function NFLTeamStats() {
  const [teams, setTeams] = useState<NFLTeam[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('ats_cover_pct');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [search, setSearch] = useState('');
  const [view, setView] = useState<'ats' | 'situational' | 'power' | 'efficiency'>('ats');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(getApiUrl('f5/team-rankings?sport=nfl')).then(r => r.json()),
      fetch(getApiUrl('league-data/nfl/teams')).then(r => r.json()),
      fetch(getApiUrl('league-data/nfl/efficiency')).then(r => r.json()),
    ])
      .then(([f5, power, eff]) => {
        const powerMap: Record<string, NFLTeam> = {};
        for (const t of (power.teams || [])) powerMap[t.team] = t;

        const effMap: Record<string, NFLTeam> = {};
        for (const t of (eff.teams || [])) effMap[t.team] = t;

        // Build merged list — all 32 from efficiency, filled in with f5 and power where matched
        const allTeams = new Set<string>([
          ...(f5.teams || []).map((t: NFLTeam) => t.team),
          ...(eff.teams || []).map((t: NFLTeam) => t.team),
        ]);

        const merged: NFLTeam[] = Array.from(allTeams).map(teamName => {
          const f5t = (f5.teams || []).find((t: NFLTeam) => t.team === teamName) || {};
          return {
            ...f5t,
            sp_rating: powerMap[teamName]?.sp_rating ?? null,
            sp_offense: powerMap[teamName]?.sp_offense ?? null,
            sp_defense: powerMap[teamName]?.sp_defense ?? null,
            dvoa_total: powerMap[teamName]?.dvoa_total ?? null,
            ypp_season: effMap[teamName]?.ypp_season ?? null,
            ypc_season: effMap[teamName]?.ypc_season ?? null,
            off_yds_per_game: effMap[teamName]?.off_yds_per_game ?? null,
            plays_per_game: effMap[teamName]?.plays_per_game ?? null,
            pass_rate: effMap[teamName]?.pass_rate ?? null,
            red_zone_pct: effMap[teamName]?.red_zone_pct ?? null,
            third_down_pct: effMap[teamName]?.third_down_pct ?? null,
            team: teamName,
          };
        });

        setTeams(merged);
        setLoading(false);
      })
      .catch(() => { setError('Failed to load NFL stats'); setLoading(false); });
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

  const viewCols: Record<string, SortKey[]> = {
    ats:        ['team', 'record', 'ats_record', 'ats_cover_pct', 'home_ats_pct', 'away_ats_pct', 'fav_cover_pct', 'dog_cover_pct', 'over_pct', 'avg_total'],
    situational:['team', 'record', 'ats_record', 'ats_cover_pct', 'primetime_win_pct', 'short_rest_win_pct'],
    power:      ['team', 'record', 'sp_rating', 'sp_offense', 'sp_defense'],
    efficiency: ['team', 'ypp_season', 'ypc_season', 'off_yds_per_game', 'plays_per_game', 'pass_rate', 'red_zone_pct', 'third_down_pct'],
  };

  const activeCols = COLS.filter(c => viewCols[view].includes(c.key as SortKey));

  const renderCell = (t: NFLTeam, key: SortKey) => {
    const v = t[key];
    switch (key) {
      case 'team': return <span className="font-semibold text-white">{t.team}</span>;
      case 'record': return <span className="font-bold text-slate-300">{String(v || '—')}</span>;
      case 'ats_record': return <span className="text-slate-300">{String(v || '—')}</span>;
      case 'ats_cover_pct':
        return <span className={`font-bold ${(v as number) >= 60 ? 'text-emerald-400' : (v as number) >= 50 ? 'text-blue-400' : 'text-red-400'}`}>{fmtPct(v as number)}</span>;
      case 'home_ats_pct':
      case 'away_ats_pct':
      case 'fav_cover_pct':
      case 'dog_cover_pct':
        return <span className={`font-semibold ${(v as number) >= 60 ? 'text-emerald-400' : (v as number) >= 50 ? 'text-blue-400' : (v as number) >= 0 ? 'text-red-400' : 'text-slate-400'}`}>{fmtPct(v as number)}</span>;
      case 'over_pct':
        return <span className={`font-semibold ${(v as number) >= 60 ? 'text-amber-400' : (v as number) <= 40 ? 'text-blue-400' : 'text-slate-300'}`}>{fmtPct(v as number)}</span>;
      case 'avg_total':
        return <span className="text-slate-300">{fmt(v as number, 1)}</span>;
      case 'primetime_win_pct':
      case 'short_rest_win_pct':
        return <span className={`font-semibold ${(v as number) >= 65 ? 'text-emerald-400' : (v as number) >= 50 ? 'text-blue-400' : 'text-red-400'}`}>{fmtPct(v as number)}</span>;
      case 'sp_rating':
        return <span className={`font-bold ${v !== null && (v as number) > 5 ? 'text-emerald-400' : v !== null && (v as number) > 0 ? 'text-blue-400' : v !== null ? 'text-red-400' : 'text-slate-500'}`}>{fmt(v as number)}</span>;
      case 'sp_offense':
        return <span className={`font-semibold ${v !== null && (v as number) > 5 ? 'text-emerald-400' : v !== null && (v as number) > 0 ? 'text-blue-400' : 'text-slate-300'}`}>{fmt(v as number)}</span>;
      case 'sp_defense':
        return <span className={`font-semibold ${v !== null && (v as number) < 0 ? 'text-emerald-400' : v !== null && (v as number) > 5 ? 'text-red-400' : 'text-slate-300'}`}>{fmt(v as number)}</span>;
      // Efficiency cols
      case 'ypp_season':
        return <span className={`font-bold ${v !== null && (v as number) >= 5.8 ? 'text-emerald-400' : v !== null && (v as number) >= 5.2 ? 'text-blue-400' : v !== null ? 'text-red-400' : 'text-slate-500'}`}>{fmt(v as number, 2)}</span>;
      case 'ypc_season':
        return <span className={`font-semibold ${v !== null && (v as number) >= 4.5 ? 'text-emerald-400' : v !== null && (v as number) >= 4.0 ? 'text-blue-400' : 'text-slate-300'}`}>{fmt(v as number, 2)}</span>;
      case 'off_yds_per_game':
        return <span className={`font-semibold ${v !== null && (v as number) >= 370 ? 'text-emerald-400' : v !== null && (v as number) >= 320 ? 'text-blue-400' : 'text-red-400'}`}>{fmt(v as number, 1)}</span>;
      case 'plays_per_game':
        return <span className="text-slate-300">{fmt(v as number, 1)}</span>;
      case 'pass_rate':
        return <span className="text-slate-300">{fmtPct(v as number, true)}</span>;
      case 'red_zone_pct':
        return <span className={`font-bold ${v !== null && (v as number) >= 0.70 ? 'text-emerald-400' : v !== null && (v as number) >= 0.58 ? 'text-blue-400' : 'text-red-400'}`}>{fmtPct(v as number, true)}</span>;
      case 'third_down_pct':
        return <span className={`font-semibold ${v !== null && (v as number) >= 0.42 ? 'text-emerald-400' : v !== null && (v as number) >= 0.36 ? 'text-blue-400' : 'text-red-400'}`}>{fmtPct(v as number, true)}</span>;
      default: return <span className="text-slate-400">{String(v ?? '—')}</span>;
    }
  };

  const VIEW_LABELS: Record<string, string> = {
    ats: 'ATS SPLITS',
    situational: 'SITUATIONAL',
    power: 'POWER RATINGS',
    efficiency: 'EFFICIENCY',
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="max-w-[1400px] mx-auto px-4 py-8">

        <div className="mb-6">
          <h1 className="text-3xl font-black italic text-white mb-1">NFL TEAM STATS</h1>
          <p className="text-slate-400 text-sm">All 32 teams — ATS trends, situational records, power ratings, and the live efficiency metrics the agent uses per game. Click headers to sort.</p>
        </div>

        <div className="flex items-center gap-2 mb-4">
          {(['ats', 'situational', 'power', 'efficiency'] as const).map(v => (
            <button
              key={v}
              onClick={() => {
                setView(v);
                if (v === 'efficiency') { setSortKey('ypp_season'); setSortDir('desc'); }
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

        {view === 'efficiency' && (
          <div className="mb-3 bg-blue-950/30 border border-blue-800/50 rounded-lg px-4 py-2 text-xs text-blue-300">
            Live ESPN data — these are the exact metrics the handicapping agent pulls per game for NFL matchup analysis.
            YPP = yards per play (primary efficiency signal). RZ% = red zone scoring %. 3RD% = 3rd down conversion %.
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
                      } ${col.key === 'team' ? 'min-w-[180px]' : ''}`}
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
          <span>ATS = Against The Spread | SP+ = efficiency-based power rating | YPP = yards per play</span>
        </div>
      </div>
    </div>
  );
}
