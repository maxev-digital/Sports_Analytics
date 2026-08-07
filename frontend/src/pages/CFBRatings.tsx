import { useState, useEffect, useMemo } from 'react';
import { getApiUrl } from '../config';

interface CFBTeam {
  team: string;
  fpi: number | null;
  fpi_rank: number | null;
  sp_plus: number | null;
  sp_offense: number | null;
  sp_defense: number | null;
  coaches_rank: number | null;
  ap_rank: number | null;
  projected_wins: number | null;
  projected_losses: number | null;
  playoff_pct: number | null;
  win_conf_pct: number | null;
  sos_rank: number | null;
  tr_rating: number | null;
  tr_rank: number | null;
  // Efficiency (ESPN — agent signals)
  ypp_season: number | null;
  ypc_season: number | null;
  off_yds_per_game: number | null;
  plays_per_game: number | null;
  pass_rate: number | null;
  third_down_pct: number | null;
}

type SortKey = keyof CFBTeam;
type SortDir = 'asc' | 'desc';

const RATING_COLS: { key: SortKey; label: string; title: string; defaultDir: SortDir }[] = [
  { key: 'fpi_rank',       label: 'FPI#',      title: 'ESPN Football Power Index Rank',         defaultDir: 'asc'  },
  { key: 'team',           label: 'TEAM',       title: 'Team name',                              defaultDir: 'asc'  },
  { key: 'coaches_rank',   label: 'COACHES',    title: 'AFCA Coaches Poll rank',                 defaultDir: 'asc'  },
  { key: 'ap_rank',        label: 'AP',         title: 'AP Top 25 rank',                         defaultDir: 'asc'  },
  { key: 'fpi',            label: 'FPI',        title: 'ESPN Football Power Index score',        defaultDir: 'desc' },
  { key: 'sp_plus',        label: 'SP+',        title: 'SP+ composite rating (Bill Connelly)',   defaultDir: 'desc' },
  { key: 'sp_offense',     label: 'SP+ OFF',    title: 'SP+ offensive rating',                   defaultDir: 'desc' },
  { key: 'sp_defense',     label: 'SP+ DEF',    title: 'SP+ defensive rating (lower = better)',  defaultDir: 'asc'  },
  { key: 'projected_wins', label: 'PROJ W',     title: 'Projected wins this season',             defaultDir: 'desc' },
  { key: 'playoff_pct',    label: 'PLAYOFF%',   title: 'Playoff appearance probability %',       defaultDir: 'desc' },
  { key: 'win_conf_pct',   label: 'CONF W%',    title: 'Conference championship probability %',  defaultDir: 'desc' },
  { key: 'sos_rank',       label: 'SOS#',       title: 'Strength of Schedule rank (lower = harder)', defaultDir: 'asc' },
  { key: 'tr_rating',      label: 'TR RATING',  title: 'TeamRankings predictive power rating',  defaultDir: 'desc' },
  { key: 'tr_rank',        label: 'TR#',        title: 'TeamRankings predictive rank',           defaultDir: 'asc'  },
];

const EFF_COLS: { key: SortKey; label: string; title: string; defaultDir: SortDir }[] = [
  { key: 'team',            label: 'TEAM',      title: 'Team name',                                       defaultDir: 'asc'  },
  { key: 'fpi_rank',        label: 'FPI#',      title: 'FPI rank (reference)',                            defaultDir: 'asc'  },
  { key: 'ypp_season',      label: 'YPP',       title: 'Yards per play (offense) — primary agent signal', defaultDir: 'desc' },
  { key: 'ypc_season',      label: 'YPC',       title: 'Yards per carry (rushing efficiency)',            defaultDir: 'desc' },
  { key: 'off_yds_per_game',label: 'YDS/G',     title: 'Offensive yards per game',                       defaultDir: 'desc' },
  { key: 'plays_per_game',  label: 'PLAYS/G',   title: 'Total plays per game (pace indicator)',           defaultDir: 'desc' },
  { key: 'pass_rate',       label: 'PASS%',     title: 'Pass attempt rate (pass att / total plays)',      defaultDir: 'desc' },
  { key: 'third_down_pct',  label: '3RD%',      title: '3rd down conversion % — agent signal',           defaultDir: 'desc' },
];

function fmt(v: number | null | undefined, decimals = 1): string {
  if (v === null || v === undefined) return '—';
  return v.toFixed(decimals);
}
function fmtPct(v: number | null | undefined, asDecimal = false): string {
  if (v === null || v === undefined) return '—';
  return asDecimal ? `${(v * 100).toFixed(1)}%` : `${v.toFixed(1)}%`;
}
function fmtRank(v: number | null | undefined): string {
  if (v === null || v === undefined) return '—';
  return `#${v}`;
}

export function CFBRatings() {
  const [teams, setTeams] = useState<CFBTeam[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('fpi_rank');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [search, setSearch] = useState('');
  const [season] = useState(2026);
  const [view, setView] = useState<'ratings' | 'efficiency'>('ratings');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(getApiUrl(`league-data/cfb/ratings?season=${season}`)).then(r => r.json()),
      fetch(getApiUrl(`league-data/cfb/efficiency?season=${season}`)).then(r => r.json()),
    ])
      .then(([ratings, eff]) => {
        const effMap: Record<string, Partial<CFBTeam>> = {};
        for (const t of (eff.teams || [])) effMap[t.team] = t;

        const merged: CFBTeam[] = (ratings.teams || []).map((t: CFBTeam) => ({
          ...t,
          ypp_season:       effMap[t.team]?.ypp_season       ?? null,
          ypc_season:       effMap[t.team]?.ypc_season       ?? null,
          off_yds_per_game: effMap[t.team]?.off_yds_per_game ?? null,
          plays_per_game:   effMap[t.team]?.plays_per_game   ?? null,
          pass_rate:        effMap[t.team]?.pass_rate        ?? null,
          third_down_pct:   effMap[t.team]?.third_down_pct   ?? null,
        }));

        setTeams(merged);
        setLoading(false);
      })
      .catch(() => { setError('Failed to load CFB ratings'); setLoading(false); });
  }, [season]);

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
      ? teams.filter(t => t.team.toLowerCase().includes(search.toLowerCase()))
      : teams;
    return [...filtered].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av === null && bv === null) return 0;
      if (av === null) return 1;
      if (bv === null) return -1;
      const cmp = typeof av === 'string' ? av.localeCompare(bv as string) : (av as number) - (bv as number);
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [teams, sortKey, sortDir, search]);

  const arrow = (key: SortKey) => sortKey === key ? (sortDir === 'asc' ? ' ↑' : ' ↓') : '';

  const activeCols = view === 'ratings' ? RATING_COLS : EFF_COLS;

  const renderCell = (t: CFBTeam, key: SortKey) => {
    switch (key) {
      case 'fpi_rank': return <span className="font-bold text-slate-400">{fmtRank(t.fpi_rank)}</span>;
      case 'team':
        return (
          <div className="flex items-center gap-2">
            <span className="font-semibold text-white">{t.team}</span>
            {t.coaches_rank !== null && t.coaches_rank <= 25 && (
              <span className="text-xs bg-amber-600/20 border border-amber-600/40 text-amber-400 px-1.5 py-0.5 rounded font-bold">C#{t.coaches_rank}</span>
            )}
            {t.ap_rank !== null && (
              <span className="text-xs bg-blue-600/20 border border-blue-600/40 text-blue-400 px-1.5 py-0.5 rounded font-bold">AP#{t.ap_rank}</span>
            )}
          </div>
        );
      case 'coaches_rank': return <span className={`font-semibold ${t.coaches_rank !== null && t.coaches_rank <= 10 ? 'text-amber-400' : 'text-slate-400'}`}>{t.coaches_rank !== null ? `#${t.coaches_rank}` : '—'}</span>;
      case 'ap_rank': return <span className={`font-semibold ${t.ap_rank !== null && t.ap_rank <= 10 ? 'text-blue-400' : 'text-slate-400'}`}>{t.ap_rank !== null ? `#${t.ap_rank}` : '—'}</span>;
      case 'fpi': return <span className={`font-bold ${t.fpi !== null && t.fpi >= 20 ? 'text-emerald-400' : t.fpi !== null && t.fpi >= 10 ? 'text-blue-400' : t.fpi !== null && t.fpi < 0 ? 'text-red-400' : 'text-slate-300'}`}>{fmt(t.fpi)}</span>;
      case 'sp_plus': return <span className={`font-bold ${t.sp_plus !== null && t.sp_plus >= 20 ? 'text-emerald-400' : t.sp_plus !== null && t.sp_plus >= 10 ? 'text-blue-400' : t.sp_plus !== null && t.sp_plus < 0 ? 'text-red-400' : 'text-slate-300'}`}>{fmt(t.sp_plus)}</span>;
      case 'sp_offense': return <span className="text-slate-300">{fmt(t.sp_offense)}</span>;
      case 'sp_defense': return <span className={`font-semibold ${t.sp_defense !== null && t.sp_defense <= 10 ? 'text-emerald-400' : t.sp_defense !== null && t.sp_defense >= 25 ? 'text-red-400' : 'text-slate-300'}`}>{fmt(t.sp_defense)}</span>;
      case 'projected_wins': return <span className={`font-bold ${t.projected_wins !== null && t.projected_wins >= 10 ? 'text-emerald-400' : t.projected_wins !== null && t.projected_wins >= 8 ? 'text-blue-400' : 'text-slate-300'}`}>{t.projected_wins !== null ? t.projected_wins.toFixed(1) : '—'}</span>;
      case 'playoff_pct': return <span className={`font-bold ${t.playoff_pct !== null && t.playoff_pct >= 50 ? 'text-emerald-400' : t.playoff_pct !== null && t.playoff_pct >= 20 ? 'text-yellow-400' : 'text-slate-400'}`}>{fmtPct(t.playoff_pct)}</span>;
      case 'win_conf_pct': return <span className="text-slate-400">{fmtPct(t.win_conf_pct)}</span>;
      case 'sos_rank': return <span className={`font-semibold ${t.sos_rank !== null && t.sos_rank <= 20 ? 'text-red-400' : t.sos_rank !== null && t.sos_rank >= 80 ? 'text-emerald-400' : 'text-slate-400'}`}>{fmtRank(t.sos_rank)}</span>;
      case 'tr_rating': return <span className="text-slate-400">{fmt(t.tr_rating)}</span>;
      case 'tr_rank': return <span className="text-slate-500">{fmtRank(t.tr_rank)}</span>;
      // Efficiency
      case 'ypp_season': return <span className={`font-bold ${t.ypp_season !== null && t.ypp_season >= 6.5 ? 'text-emerald-400' : t.ypp_season !== null && t.ypp_season >= 5.5 ? 'text-blue-400' : t.ypp_season !== null ? 'text-red-400' : 'text-slate-500'}`}>{fmt(t.ypp_season, 2)}</span>;
      case 'ypc_season': return <span className={`font-semibold ${t.ypc_season !== null && t.ypc_season >= 5.0 ? 'text-emerald-400' : t.ypc_season !== null && t.ypc_season >= 4.0 ? 'text-blue-400' : 'text-slate-300'}`}>{fmt(t.ypc_season, 2)}</span>;
      case 'off_yds_per_game': return <span className={`font-semibold ${t.off_yds_per_game !== null && t.off_yds_per_game >= 420 ? 'text-emerald-400' : t.off_yds_per_game !== null && t.off_yds_per_game >= 360 ? 'text-blue-400' : 'text-red-400'}`}>{fmt(t.off_yds_per_game, 1)}</span>;
      case 'plays_per_game': return <span className="text-slate-300">{fmt(t.plays_per_game, 1)}</span>;
      case 'pass_rate': return <span className="text-slate-300">{fmtPct(t.pass_rate, true)}</span>;
      case 'third_down_pct': return <span className={`font-semibold ${t.third_down_pct !== null && t.third_down_pct >= 0.46 ? 'text-emerald-400' : t.third_down_pct !== null && t.third_down_pct >= 0.38 ? 'text-blue-400' : 'text-red-400'}`}>{fmtPct(t.third_down_pct, true)}</span>;
      default: return <span className="text-slate-400">—</span>;
    }
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="max-w-[1600px] mx-auto px-4 py-8">

        <div className="mb-6">
          <h1 className="text-3xl font-black italic text-white mb-1">CFB TEAM RATINGS</h1>
          <p className="text-slate-400 text-sm">
            All 138 FBS teams — FPI, SP+, projected wins, playoff odds, strength of schedule, and live ESPN efficiency metrics.
            <span className="ml-2 text-blue-400">2026 Season Preseason</span>
          </p>
        </div>

        <div className="flex items-center gap-2 mb-4">
          {(['ratings', 'efficiency'] as const).map(v => (
            <button
              key={v}
              onClick={() => {
                setView(v);
                if (v === 'ratings') { setSortKey('fpi_rank'); setSortDir('asc'); }
                if (v === 'efficiency') { setSortKey('ypp_season'); setSortDir('desc'); }
              }}
              className={`px-4 py-2 rounded-lg text-sm font-bold italic transition-all ${
                view === v ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {v === 'ratings' ? 'POWER RATINGS' : 'EFFICIENCY'}
            </button>
          ))}
          <div className="ml-auto flex items-center gap-3">
            <input
              type="text"
              placeholder="Search team..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 w-56 focus:outline-none focus:border-blue-500"
            />
            <span className="text-slate-500 text-sm">{sorted.length} teams</span>
            {search && (
              <button onClick={() => setSearch('')} className="text-slate-400 hover:text-white text-xs">Clear</button>
            )}
          </div>
        </div>

        {view === 'efficiency' && (
          <div className="mb-3 bg-blue-950/30 border border-blue-800/50 rounded-lg px-4 py-2 text-xs text-blue-300">
            Live ESPN data — these are the exact metrics the CFB handicapping agent pulls per game.
            YPP (yards per play) is the primary efficiency signal. 3RD% = 3rd down conversion %. ~102 teams have ESPN data; FCS and low-coverage programs show —.
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
                      } ${col.key === 'team' ? 'min-w-[180px]' : 'min-w-[70px]'}`}
                    >
                      {col.label}{arrow(col.key)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sorted.map((t, i) => (
                  <tr
                    key={t.team}
                    className={`border-b border-slate-800 transition-colors hover:bg-slate-800/40 ${i % 2 === 0 ? 'bg-slate-900/30' : 'bg-black/20'}`}
                  >
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
          <span><span className="text-emerald-400 font-bold">Green</span> = elite tier</span>
          <span><span className="text-blue-400 font-bold">Blue</span> = above average</span>
          <span><span className="text-red-400 font-bold">Red</span> = weak/tough (context-dependent)</span>
          <span>SP+ DEF: lower = better defense | SOS#: lower = harder schedule</span>
          <span>YPP = yards per play | 3RD% = 3rd down conversion %</span>
          <span>Click column headers to sort</span>
        </div>
      </div>
    </div>
  );
}
