/* v2 — fixed NFL sort crash */
/**
 * Betting Rankings — Multi-sport betting analytics.
 * Sport tabs at top, sport-specific view pills below.
 * MLB: Full Game, First 5 Innings, Home/Away Splits
 * NFL: (coming soon) ATS, Totals, Situational
 */
import { useState, useEffect, useCallback } from 'react';
import '../styles/analytics.css';
import { getApiUrl } from '../config';

function exportCSV(rows: Record<string, unknown>[], filename: string) {
  if (!rows.length) return;
  const keys = Object.keys(rows[0]);
  const header = keys.join(',');
  const body = rows.map(r =>
    keys.map(k => {
      const v = r[k] ?? '';
      const s = String(v);
      return s.includes(',') || s.includes('"') || s.includes('\n')
        ? `"${s.replace(/"/g, '""')}"` : s;
    }).join(',')
  ).join('\n');
  const blob = new Blob([`${header}\n${body}`], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

const EMERALD   = 'oklch(69.6% .17 162.48)';
const RED       = 'oklch(63.2% .204 25.331)';
const BRAND_RED = 'oklch(63.7% .237 25.331)';
const BLUE      = 'oklch(62.3% .214 259.815)';
const YELLOW    = 'oklch(79.5% .184 86.047)';
const MUTED_FG  = 'oklch(70.8% 0 0)';
const BORDER    = 'oklch(100% 0 0 / .1)';
const FG        = 'oklch(98.5% 0 0)';

type Sport = 'mlb' | 'nfl' | 'nba' | 'nhl' | 'ncaaf' | 'ncaab';

const SPORTS: { key: Sport; label: string; active: boolean }[] = [
  { key: 'mlb',   label: 'MLB',   active: true },
  { key: 'nfl',   label: 'NFL',   active: true },
  { key: 'ncaaf', label: 'NCAAF', active: true },
  { key: 'ncaab', label: 'NCAAB', active: true },
  { key: 'nba',   label: 'NBA',   active: true },
  { key: 'nhl',   label: 'NHL',   active: true },
];

const SPORT_VIEWS: Record<Sport, { key: string; label: string }[]> = {
  mlb:   [{ key: 'full_game', label: 'FULL GAME' }, { key: 'first_5', label: 'FIRST 5 INNINGS' }, { key: 'splits', label: 'HOME / AWAY SPLITS' }],
  nfl:   [{ key: 'full_game', label: 'FULL GAME' }, { key: 'first_half', label: 'FIRST HALF' }, { key: 'ats', label: 'ATS RECORD' }, { key: 'totals', label: 'TOTALS' }, { key: 'situational', label: 'SITUATIONAL' }],
  ncaaf: [{ key: 'full_game', label: 'FULL GAME' }, { key: 'ats', label: 'ATS RECORD' }, { key: 'totals', label: 'TOTALS' }],
  nba:   [{ key: 'full_game', label: 'FULL GAME' }, { key: 'efficiency', label: 'PACE & EFFICIENCY' }, { key: 'splits', label: 'HOME / AWAY SPLITS' }],
  nhl:   [{ key: 'full_game', label: 'FULL GAME' }, { key: 'goalie', label: 'GOALIE MATCHUP' }, { key: 'special_teams', label: 'SPECIAL TEAMS' }],
  ncaab: [{ key: 'full_game', label: 'FULL GAME' }, { key: 'efficiency', label: 'ADJEM RATINGS' }, { key: 'splits', label: 'HOME / AWAY SPLITS' }],
};

export function BettingRankings() {
  const [sport, setSport] = useState<Sport>('mlb');
  const [view, setView] = useState('full_game');
  const [teams, setTeams] = useState<any[]>([]);
  const [atsTeams, setAtsTeams] = useState<any[]>([]);
  const [fhTeams, setFhTeams] = useState<any[]>([]);
  const [nbaEffTeams, setNbaEffTeams] = useState<any[]>([]);
  const [nhlTeams, setNhlTeams] = useState<any[]>([]);
  const [ncaabEffTeams, setNcaabEffTeams] = useState<any[]>([]);
  const [ncaabEffSeasons, setNcaabEffSeasons] = useState<{ key: string; label: string; current: boolean }[]>([]);
  const [seasons, setSeasons] = useState<{ key: string; label: string; current: boolean }[]>([]);
  const [atsSeasons, setAtsSeasons] = useState<{ key: string; label: string; current: boolean }[]>([]);
  const [fhSeasons, setFhSeasons] = useState<{ key: string; label: string; current: boolean }[]>([]);
  const [selectedSeason, setSelectedSeason] = useState('');
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState('win_pct');
  const [sortDesc, setSortDesc] = useState(true);

  useEffect(() => {
    setTeams([]);
    setAtsTeams([]);
    setFhTeams([]);
    setNbaEffTeams([]);
    setNhlTeams([]);
    setNcaabEffTeams([]);
    setView('full_game');
    setSortKey(sport === 'mlb' ? 'fg_win_pct' : 'win_pct');
    setSelectedSeason('');
    setLoading(true);

    const fetches: Promise<any>[] = [
      fetch(getApiUrl(`f5/team-rankings?sport=${sport}`)).then(r => r.json()),
    ];
    if (sport === 'nfl') {
      fetches.push(fetch(getApiUrl(`f5/ats-rankings?sport=nfl`)).then(r => r.json()).catch(() => ({ teams: [] })));
      fetches.push(fetch(getApiUrl(`f5/firsthalf-rankings?sport=nfl`)).then(r => r.json()).catch(() => ({ teams: [] })));
    }
    if (sport === 'nba') {
      fetches.push(fetch(getApiUrl('f5/nba-efficiency')).then(r => r.json()).catch(() => ({ teams: [] })));
    }
    if (sport === 'nhl') {
      fetches.push(fetch(getApiUrl('f5/nhl-goalie-rankings')).then(r => r.json()).catch(() => ({ teams: [] })));
    }
    if (sport === 'ncaab') {
      fetches.push(fetch(getApiUrl('f5/ncaab-efficiency?season=2025')).then(r => r.json()).catch(() => ({ teams: [], seasons: [] })));
    }

    Promise.all(fetches).then((results) => {
      const [main, second, third] = results;
      setTeams(main.teams ?? []);
      setSeasons(main.seasons ?? []);
      setSelectedSeason(main.season ?? '');
      if (sport === 'nfl') {
        if (second) { setAtsTeams(second.teams ?? []); setAtsSeasons(second.seasons ?? []); }
        if (third)  { setFhTeams(third.teams ?? []);   setFhSeasons(third.seasons ?? []); }
      }
      if (sport === 'nba' && second) {
        setNbaEffTeams(second.teams ?? []);
      }
      if (sport === 'nhl' && second) {
        setNhlTeams(second.teams ?? []);
      }
      if (sport === 'ncaab' && second) {
        setNcaabEffTeams(second.teams ?? []);
        setNcaabEffSeasons(second.seasons ?? []);
      }
    })
    .catch(() => setTeams([]))
    .finally(() => setLoading(false));
  }, [sport]);

  const changeSeason = (key: string) => {
    setSelectedSeason(key);
    setLoading(true);

    let endpoint: string;
    if (view === 'ats' || view === 'totals') {
      endpoint = `f5/ats-rankings?sport=${sport}&season=${key}`;
    } else if (view === 'first_half') {
      endpoint = `f5/firsthalf-rankings?sport=${sport}&season=${key}`;
    } else if (view === 'efficiency' && sport === 'ncaab') {
      endpoint = `f5/ncaab-efficiency?season=${key}`;
    } else {
      endpoint = `f5/team-rankings?sport=${sport}&season=${key}`;
    }

    fetch(getApiUrl(endpoint))
      .then(r => r.json())
      .then(d => {
        if (view === 'ats' || view === 'totals') setAtsTeams(d.teams ?? []);
        else if (view === 'first_half') setFhTeams(d.teams ?? []);
        else if (view === 'efficiency' && sport === 'ncaab') setNcaabEffTeams(d.teams ?? []);
        else setTeams(d.teams ?? []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  const switchToAtsView = (v: string) => {
    setView(v);
    if ((v === 'ats' || v === 'totals') && atsTeams.length === 0 && sport === 'nfl') {
      setLoading(true);
      fetch(getApiUrl(`f5/ats-rankings?sport=nfl&season=${selectedSeason || '2025'}`))
        .then(r => r.json())
        .then(d => {
          setAtsTeams(d.teams ?? []);
          setAtsSeasons(d.seasons ?? []);
          if (d.season) setSelectedSeason(d.season);
        })
        .catch(() => {})
        .finally(() => setLoading(false));
    }
    if (v === 'first_half' && fhTeams.length === 0 && sport === 'nfl') {
      setLoading(true);
      fetch(getApiUrl(`f5/firsthalf-rankings?sport=nfl&season=${selectedSeason || '2025'}`))
        .then(r => r.json())
        .then(d => {
          setFhTeams(d.teams ?? []);
          setFhSeasons(d.seasons ?? []);
        })
        .catch(() => {})
        .finally(() => setLoading(false));
    }
    const sortMap: Record<string, string> = {
      ats: 'ats_cover_pct', totals: 'over_pct', situational: 'division_win_pct',
      first_half: 'avg_h1_margin', first_5: 'f5_win_pct',
      efficiency: sport === 'ncaab' ? 'adj_em' : 'ortg_proxy', goalie: 'sv_pct', special_teams: 'pp_pct',
      splits: sport === 'mlb' ? 'fg_home_rpg' : 'home_ppg',
      full_game: sport === 'mlb' ? 'fg_win_pct' : 'win_pct',
    };
    setSortKey(sortMap[v] ?? 'win_pct');
  };

  const handleSort = (key: string) => {
    if (sortKey === key) setSortDesc(!sortDesc);
    else { setSortKey(key); setSortDesc(true); }
  };

  const sortFn = (list: any[]) => [...list].sort((a, b) => {
    const av = a[sortKey] ?? 0;
    const bv = b[sortKey] ?? 0;
    if (typeof av === 'string' && typeof bv === 'string') {
      return sortDesc ? bv.localeCompare(av) : av.localeCompare(bv);
    }
    return sortDesc ? (Number(bv) || 0) - (Number(av) || 0) : (Number(av) || 0) - (Number(bv) || 0);
  });

  const sorted = sortFn(teams);

  const activeSeasons = (sport === 'ncaab' && view === 'efficiency') ? ncaabEffSeasons : (view === 'ats' || view === 'totals') ? atsSeasons : view === 'first_half' ? fhSeasons : seasons;
  const views = SPORT_VIEWS[sport] ?? [];
  const sportActive = SPORTS.find(s => s.key === sport)?.active ?? false;

  // Determine which data array is currently being rendered for CSV export
  const activeData: Record<string, unknown>[] = (() => {
    if (view === 'ats' || view === 'totals') return sortFn(atsTeams) as Record<string, unknown>[];
    if (view === 'first_half') return sortFn(fhTeams) as Record<string, unknown>[];
    if (sport === 'nba' && view === 'efficiency') return sortFn(nbaEffTeams) as Record<string, unknown>[];
    if (sport === 'nhl' && (view === 'goalie' || view === 'special_teams')) return sortFn(nhlTeams) as Record<string, unknown>[];
    if (sport === 'ncaab' && view === 'efficiency') return sortFn(ncaabEffTeams) as Record<string, unknown>[];
    return sorted as Record<string, unknown>[];
  })();

  const handleExportCSV = useCallback(() => {
    const label = `${sport.toUpperCase()}_${view}_${selectedSeason || 'current'}`;
    exportCSV(activeData, `maxev_${label}.csv`);
  }, [activeData, sport, view, selectedSeason]);

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1>Betting Rankings</h1>
        <p className="subtitle">
          Team betting analytics across all sports — records, scoring splits, and trends you won't find on ESPN
        </p>

        {/* Sport tabs */}
        <div className="sport-tabs" style={{ marginTop: 12 }}>
          {SPORTS.map(s => (
            <button
              key={s.key}
              className={`sport-tab ${sport === s.key ? 'active' : ''}`}
              onClick={() => setSport(s.key)}
              style={{ opacity: s.active ? 1 : 0.5 }}
            >
              {s.label} {!s.active && '(SOON)'}
            </button>
          ))}
        </div>
      </div>

      {/* View pills — sport specific */}
      {views.length > 0 && (
        <div className="filter-bar">
          {views.map(v => (
            <button
              key={v.key}
              className={`filter-pill ${view === v.key ? 'active' : ''}`}
              onClick={() => switchToAtsView(v.key)}
              disabled={!sportActive && v.key !== 'full_game'}
            >
              {v.label}
            </button>
          ))}
          {((sport === 'ncaab' && view === 'efficiency') ? ncaabEffSeasons : (view === 'ats' || view === 'totals') ? atsSeasons : view === 'first_half' ? fhSeasons : seasons).length > 1 && (
            <>
              <span style={{ marginLeft: 16, fontSize: '0.68rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em' }}>SEASON</span>
              {((sport === 'ncaab' && view === 'efficiency') ? ncaabEffSeasons : (view === 'ats' || view === 'totals') ? atsSeasons : view === 'first_half' ? fhSeasons : seasons).map(s => (
                <button
                  key={s.key}
                  className={`filter-pill ${selectedSeason === s.key ? 'active' : ''}`}
                  onClick={() => changeSeason(s.key)}
                  style={s.current ? { borderColor: EMERALD } : {}}
                >
                  {s.label} {s.current ? '●' : ''}
                </button>
              ))}
            </>
          )}
          <span style={{ marginLeft: 'auto', fontSize: '0.72rem', color: MUTED_FG }}>
            {teams.length > 0 ? `${teams.length} teams · ${selectedSeason || ''}` : ''}
          </span>
          {activeData.length > 0 && (
            <button
              onClick={handleExportCSV}
              title="Download as CSV"
              style={{
                marginLeft: 8, padding: '4px 10px', borderRadius: 5,
                background: 'oklch(25% 0 0)', border: `1px solid ${BORDER}`,
                color: MUTED_FG, fontSize: '0.68rem', fontWeight: 700,
                cursor: 'pointer', letterSpacing: '0.05em',
                display: 'flex', alignItems: 'center', gap: 5,
              }}
            >
              ↓ CSV
            </button>
          )}
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: MUTED_FG }}>Loading...</div>
      ) : teams.length === 0 ? (
        <ComingSoon sport={sport} />
      ) : (
        <div style={{ padding: '0 24px 24px', maxWidth: 1400 }}>
          {sport === 'mlb' && view === 'full_game' && <MLBFullGame teams={sorted} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} sport={sport} />}
          {sport === 'mlb' && view === 'first_5' && <MLBF5 teams={sorted} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} sport={sport} />}
          {sport === 'mlb' && view === 'splits' && <MLBSplits teams={sorted} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} sport={sport} />}
          {sport !== 'mlb' && view === 'full_game' && <GenericFullGame teams={sorted} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} sport={sport} />}
          {sport !== 'mlb' && view === 'splits' && <GenericSplits teams={sorted} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} sport={sport} />}
          {sport === 'nfl' && view === 'ats' && <NFLAtsTable teams={sortFn(atsTeams)} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} sport={sport} />}
          {sport === 'nfl' && view === 'totals' && <NFLTotalsTable teams={sortFn(atsTeams)} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} sport={sport} />}
          {sport === 'nfl' && view === 'situational' && <NFLSituationalTable teams={sorted} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} sport={sport} />}
          {sport === 'nfl' && view === 'first_half' && <NFLFirstHalfTable teams={sortFn(fhTeams)} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} sport={sport} />}
          {sport === 'nba' && view === 'efficiency' && <NBAEfficiencyTable teams={sortFn(nbaEffTeams)} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} sport={sport} />}
          {sport === 'nhl' && (view === 'goalie' || view === 'special_teams') && <NHLGoalieTable teams={sortFn(nhlTeams)} view={view} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} sport={sport} />}
          {sport === 'ncaab' && view === 'efficiency' && <NCAABEfficiencyTable teams={sortFn(ncaabEffTeams)} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} />}
          {sport !== 'mlb' && !['full_game','splits','ats','totals','situational','first_half','efficiency','goalie','special_teams'].includes(view) && sport !== 'ncaab' && (
            <div style={{ padding: 40, textAlign: 'center', color: MUTED_FG }}>
              {view.replace('_', ' ').toUpperCase()} data coming soon for {sport.toUpperCase()}.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ComingSoon({ sport }: { sport: string }) {
  const labels: Record<string, string> = {
    nfl: 'NFL betting rankings will include ATS records, totals trends, first-half splits, and situational stats (home favorites, road dogs, divisional games, short rest).',
    ncaaf: 'College football rankings with ATS records, totals, and conference matchup data.',
    nba: 'NBA rankings with first-half splits, ATS records, and pace-adjusted metrics.',
    nhl: 'NHL rankings with goalie matchup data, special teams efficiency, and totals trends.',
  };
  return (
    <div style={{ padding: '60px 24px', textAlign: 'center' }}>
      <div style={{ fontSize: '1.2rem', fontWeight: 800, color: FG, marginBottom: 8 }}>{sport.toUpperCase()} — Coming Soon</div>
      <div style={{ fontSize: '0.85rem', color: MUTED_FG, maxWidth: 500, margin: '0 auto' }}>
        {labels[sport] ?? 'Betting rankings for this sport are in development.'}
      </div>
      <div style={{ fontSize: '0.75rem', color: MUTED_FG, marginTop: 16 }}>
        Season data will populate automatically when the {sport.toUpperCase()} season begins.
      </div>
    </div>
  );
}

/* ─── Shared Components ─── */

function SortTh({ label, field, sortKey, sortDesc, onSort }: {
  label: string; field: string; sortKey: string; sortDesc: boolean; onSort: (k: string) => void;
}) {
  return (
    <th onClick={() => onSort(field)} style={{
      padding: '8px 8px', textAlign: field === 'team' ? 'left' : 'right',
      fontSize: '0.6rem', fontWeight: 700, color: sortKey === field ? EMERALD : MUTED_FG,
      letterSpacing: '0.08em', textTransform: 'uppercase', cursor: 'pointer',
      borderBottom: `1px solid ${BORDER}`, whiteSpace: 'nowrap', userSelect: 'none',
    }}>
      {label} {sortKey === field ? (sortDesc ? '▼' : '▲') : ''}
    </th>
  );
}

function Td({ value, format, color, bold, align }: {
  value: any; format?: (v: any) => string; color?: string; bold?: boolean; align?: 'left' | 'right';
}) {
  let display: string;
  try {
    display = format ? format(value) : (value ?? '—');
  } catch {
    display = '—';
  }
  return (
    <td style={{
      padding: '6px 8px', textAlign: align ?? 'right', whiteSpace: 'nowrap',
      fontFamily: 'var(--d3-mono)', fontWeight: bold ? 700 : 400, color: color ?? MUTED_FG,
    }}>{display}</td>
  );
}

const ESPN_LOGO_MAP: Record<string, Record<string, string>> = {
  nfl: {
    ARI:'crd',ATL:'atl',BAL:'bal',BUF:'buf',CAR:'car',CHI:'chi',CIN:'cin',CLE:'cle',
    DAL:'dal',DEN:'den',DET:'det',GB:'gb',HOU:'hou',IND:'ind',JAX:'jax',KC:'kc',
    LA:'lar',LAC:'lac',LAR:'lar',LV:'lv',MIA:'mia',MIN:'min',NE:'ne',NO:'no',NYG:'nyg',
    NYJ:'nyj',PHI:'phi',PIT:'pit',SEA:'sea',SF:'sf',TB:'tb',TEN:'ten',WAS:'wsh',
  },
  nhl: {
    ana:'ana',ari:'ari',bos:'bos',buf:'buf',car:'car',cbj:'cbj',cgy:'cgy',chi:'chi',
    col:'col',dal:'dal',det:'det',edm:'edm',fla:'fla',lak:'la',min:'min',mtl:'mtl',
    njd:'njd',nsh:'nsh',nyi:'nyi',nyr:'nyr',ott:'ott',phi:'phi',pit:'pit',sea:'sea',
    sjs:'sj',stl:'stl',tbl:'tb',tor:'tor',van:'van',vgk:'vgs',wpg:'wpg',wsh:'wsh',
  },
};

const MLB_ABBR: Record<string, string> = {
  'Arizona Diamondbacks':'ari','Atlanta Braves':'atl','Baltimore Orioles':'bal',
  'Boston Red Sox':'bos','Chicago Cubs':'chc','Chicago White Sox':'chw',
  'Cincinnati Reds':'cin','Cleveland Guardians':'cle','Colorado Rockies':'col',
  'Detroit Tigers':'det','Houston Astros':'hou','Kansas City Royals':'kc',
  'Los Angeles Angels':'laa','Los Angeles Dodgers':'lad','Miami Marlins':'mia',
  'Milwaukee Brewers':'mil','Minnesota Twins':'min','New York Mets':'nym',
  'New York Yankees':'nyy','Oakland Athletics':'oak','Athletics':'oak',
  'Philadelphia Phillies':'phi','Pittsburgh Pirates':'pit','San Diego Padres':'sd',
  'San Francisco Giants':'sf','Seattle Mariners':'sea','St. Louis Cardinals':'stl',
  'Tampa Bay Rays':'tb','Texas Rangers':'tex','Toronto Blue Jays':'tor',
  'Washington Nationals':'wsh',
};

function getLogoUrl(team: string, sport: Sport): string | null {
  if (sport === 'mlb') {
    const abbr = MLB_ABBR[team];
    return abbr ? `https://a.espncdn.com/i/teamlogos/mlb/500/${abbr}.png` : null;
  }
  if (sport === 'nfl') {
    const abbr = ESPN_LOGO_MAP.nfl[team] ?? team.toLowerCase();
    return `https://a.espncdn.com/i/teamlogos/nfl/500/${abbr}.png`;
  }
  if (sport === 'nhl') {
    const abbr = ESPN_LOGO_MAP.nhl[team] ?? team.toLowerCase();
    return `https://a.espncdn.com/i/teamlogos/nhl/500/${abbr}.png`;
  }
  if (sport === 'nba') {
    const abbr = team.toLowerCase();
    return `https://a.espncdn.com/i/teamlogos/nba/500/${abbr}.png`;
  }
  if (sport === 'ncaaf') {
    const NCAAF_IDS: Record<string, string> = {
      'Air Force':'2005','Alabama':'6','Appalachian State':'2026','Boise State':'68',
      'Cincinnati':'2132','Clemson':'228','Coastal Carolina':'324','Florida State':'52',
      'Georgia':'59','Kansas State':'2306','LSU':'99','Louisiana Tech':'2348',
      'Memphis':'235','Miami':'193','Michigan':'128','Ohio State':'194','Oklahoma':'199',
      'Oregon':'204','Penn State':'213','San Diego State':'21','Texas':'251',
      'Texas Tech':'2641','Toledo':'2649','UCF':'2116','UCLA':'26','USC':'30',
      'UTSA':'2636','Washington':'265','Western Michigan':'2711',
    };
    const id = NCAAF_IDS[team];
    return id ? `https://a.espncdn.com/i/teamlogos/ncaa/500/${id}.png` : null;
  }
  // NCAAB — 364 schools, skip for now
  return null;
}

function TeamTd({ name, sport }: { name: string; sport?: Sport }) {
  const logo = sport ? getLogoUrl(name, sport) : null;
  return (
    <td style={{ padding: '6px 8px', fontWeight: 700, color: FG, fontFamily: 'Nunito' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {logo && <img src={logo} alt="" style={{ width: 20, height: 20 }} onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />}
        {name}
      </div>
    </td>
  );
}

function diffColor(v: any): string { return (v ?? 0) > 0 ? EMERALD : (v ?? 0) < 0 ? BRAND_RED : MUTED_FG; }
function pctGood(v: any, good: number, bad: number): string { const n = Number(v) || 0; return n > good ? EMERALD : n < bad ? BRAND_RED : FG; }
function fmtDiff(v: any): string { const n = Number(v) || 0; return `${n > 0 ? '+' : ''}${n.toFixed(2)}`; }

/* ─── MLB Tables ─── */

function MLBFullGame({ teams, sortKey, sortDesc, onSort, sport }: any) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortTh label="Team" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="GP" field="games" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Record" field="fg_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Win%" field="fg_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="RPG" field="fg_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="RAPG" field="fg_rapg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Diff" field="fg_diff" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Home RPG" field="fg_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Away RPG" field="fg_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 W%" field="f5_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 Diff" field="f5_diff" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Tie%" field="f5_tie_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => (
            <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
              <TeamTd name={t.team} sport={sport} />
              <Td value={t.games} />
              <Td value={t.fg_record} color={FG} />
              <Td value={`${t.fg_win_pct}%`} color={pctGood(t.fg_win_pct, 52, 45)} bold />
              <Td value={t.fg_rpg.toFixed(2)} color={pctGood(t.fg_rpg, 4.5, 3.5)} />
              <Td value={t.fg_rapg.toFixed(2)} color={pctGood(-t.fg_rapg, -3.5, -4.5)} />
              <Td value={fmtDiff(t.fg_diff)} color={diffColor(t.fg_diff)} bold />
              <Td value={t.fg_home_rpg.toFixed(2)} />
              <Td value={t.fg_away_rpg.toFixed(2)} />
              <Td value={`${t.f5_win_pct}%`} color={pctGood(t.f5_win_pct, 48, 40)} />
              <Td value={fmtDiff(t.f5_diff)} color={diffColor(t.f5_diff)} />
              <Td value={`${t.f5_tie_pct}%`} color={t.f5_tie_pct > 16 ? BLUE : MUTED_FG} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MLBF5({ teams, sortKey, sortDesc, onSort, sport }: any) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortTh label="Team" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 Record" field="f5_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 W%" field="f5_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Tie%" field="f5_tie_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 RPG" field="f5_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 RAPG" field="f5_rapg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 Diff" field="f5_diff" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Home F5 RPG" field="f5_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Away F5 RPG" field="f5_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="U5%" field="f5_under_5_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Blowout%" field="blowout_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Shutout%" field="f5_shutout_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F1 0%" field="f1_scoreless_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => (
            <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
              <TeamTd name={t.team} sport={sport} />
              <Td value={t.f5_record} color={FG} />
              <Td value={`${t.f5_win_pct}%`} color={pctGood(t.f5_win_pct, 48, 40)} bold />
              <Td value={`${t.f5_tie_pct}%`} color={t.f5_tie_pct > 16 ? BLUE : MUTED_FG} />
              <Td value={t.f5_rpg.toFixed(2)} color={pctGood(t.f5_rpg, 2.8, 2.2)} />
              <Td value={t.f5_rapg.toFixed(2)} color={pctGood(-t.f5_rapg, -2.2, -2.8)} />
              <Td value={fmtDiff(t.f5_diff)} color={diffColor(t.f5_diff)} bold />
              <Td value={t.f5_home_rpg.toFixed(2)} />
              <Td value={t.f5_away_rpg.toFixed(2)} />
              <Td value={`${t.f5_under_5_pct}%`} color={t.f5_under_5_pct > 52 ? EMERALD : MUTED_FG} />
              <Td value={`${t.blowout_pct}%`} color={t.blowout_pct > 25 ? EMERALD : MUTED_FG} />
              <Td value={`${t.f5_shutout_pct}%`} color={t.f5_shutout_pct > 25 ? BRAND_RED : MUTED_FG} />
              <Td value={`${t.f1_scoreless_pct}%`} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MLBSplits({ teams, sortKey, sortDesc, onSort, sport }: any) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortTh label="Team" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="FG Home Rec" field="fg_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="FG Home RPG" field="fg_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="FG Away Rec" field="fg_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="FG Away RPG" field="fg_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="FG H-A Gap" field="fg_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 Home Rec" field="f5_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 Home RPG" field="f5_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 Away Rec" field="f5_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 Away RPG" field="f5_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 H-A Gap" field="f5_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => {
            const fgGap = t.fg_home_rpg - t.fg_away_rpg;
            const f5Gap = t.f5_home_rpg - t.f5_away_rpg;
            return (
              <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
                <TeamTd name={t.team} sport={sport} />
                <Td value={t.fg_home_record} color={FG} />
                <Td value={t.fg_home_rpg.toFixed(2)} color={pctGood(t.fg_home_rpg, 4.5, 3.5)} />
                <Td value={t.fg_away_record} color={FG} />
                <Td value={t.fg_away_rpg.toFixed(2)} color={pctGood(t.fg_away_rpg, 4.5, 3.5)} />
                <Td value={fmtDiff(fgGap)} color={diffColor(fgGap)} bold />
                <Td value={t.f5_home_record} color={FG} />
                <Td value={t.f5_home_rpg.toFixed(2)} color={pctGood(t.f5_home_rpg, 2.8, 2.2)} />
                <Td value={t.f5_away_record} color={FG} />
                <Td value={t.f5_away_rpg.toFixed(2)} color={pctGood(t.f5_away_rpg, 2.8, 2.2)} />
                <Td value={fmtDiff(f5Gap)} color={diffColor(f5Gap)} bold />
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function GenericFullGame({ teams, sortKey, sortDesc, onSort, sport }: any) {
  const scoringLabel = sport === 'nhl' ? 'GPG' : 'PPG';
  const allowedLabel = sport === 'nhl' ? 'GAPG' : 'PAPG';
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortTh label="Team" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="GP" field="games" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Record" field="win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Win%" field="win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label={scoringLabel} field="ppg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label={allowedLabel} field="papg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Diff" field="diff" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Avg Total" field="avg_total" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Home W%" field="home_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Away W%" field="away_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => (
            <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
              <TeamTd name={t.team} sport={sport} />
              <Td value={t.games} />
              <Td value={t.record} color={FG} />
              <Td value={`${t.win_pct}%`} color={pctGood(t.win_pct, 55, 45)} bold />
              <Td value={(t.ppg ?? 0).toFixed(1)} color={pctGood(t.ppg, t.ppg > 50 ? 110 : 3.2, t.ppg > 50 ? 100 : 2.5)} />
              <Td value={(t.papg ?? 0).toFixed(1)} />
              <Td value={fmtDiff(t.diff)} color={diffColor(t.diff)} bold />
              <Td value={(t.avg_total ?? 0).toFixed(1)} color={BLUE} />
              <Td value={`${t.home_win_pct ?? 0}%`} color={pctGood(t.home_win_pct, 60, 40)} />
              <Td value={`${t.away_win_pct ?? 0}%`} color={pctGood(t.away_win_pct, 55, 40)} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function GenericSplits({ teams, sortKey, sortDesc, onSort, sport }: any) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortTh label="Team" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Home Rec" field="home_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Home PPG" field="home_ppg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Home PAPG" field="home_papg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Away Rec" field="away_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Away PPG" field="away_ppg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Away PAPG" field="away_papg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="H-A Gap" field="home_ppg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => {
            const gap = Number(t.home_ppg || 0) - Number(t.away_ppg || 0);
            return (
              <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
                <TeamTd name={t.team} sport={sport} />
                <Td value={t.home_record ?? '—'} color={FG} />
                <Td value={Number(t.home_ppg || 0).toFixed(1)} />
                <Td value={Number(t.home_papg || 0).toFixed(1)} />
                <Td value={t.away_record ?? '—'} color={FG} />
                <Td value={Number(t.away_ppg || 0).toFixed(1)} />
                <Td value={Number(t.away_papg || 0).toFixed(1)} />
                <Td value={fmtDiff(gap)} color={diffColor(gap)} bold />
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function NFLAtsTable({ teams, sortKey, sortDesc, onSort, sport }: any) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortTh label="Team" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="GP" field="games" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="ATS Record" field="ats_cover_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="ATS %" field="ats_cover_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Home ATS" field="home_ats_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Away ATS" field="away_ats_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="As Fav" field="fav_cover_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="As Dog" field="dog_cover_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => (
            <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
              <TeamTd name={t.team} sport={sport} />
              <Td value={t.games} />
              <Td value={t.ats_record ?? '—'} color={FG} />
              <Td value={`${t.ats_cover_pct ?? 0}%`} color={pctGood(t.ats_cover_pct, 55, 45)} bold />
              <Td value={t.home_ats ?? '—'} color={FG} />
              <Td value={t.away_ats ?? '—'} color={FG} />
              <Td value={t.fav_ats ?? '—'} color={FG} />
              <Td value={t.dog_ats ?? '—'} color={FG} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function NFLTotalsTable({ teams, sortKey, sortDesc, onSort, sport }: any) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortTh label="Team" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="GP" field="games" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="O/U Record" field="over_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Over %" field="over_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Avg Total" field="avg_total" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => (
            <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
              <TeamTd name={t.team} sport={sport} />
              <Td value={t.games} />
              <Td value={t.ou_record ?? '—'} color={FG} />
              <Td value={`${t.over_pct ?? 0}%`} color={pctGood(t.over_pct, 55, 45)} bold />
              <Td value={(t.avg_total ?? 0).toFixed(1)} color={BLUE} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function NFLSituationalTable({ teams, sortKey, sortDesc, onSort, sport }: any) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortTh label="Team" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Division Rec" field="division_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Div W%" field="division_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Primetime Rec" field="primetime_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="PT W%" field="primetime_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Short Rest" field="short_rest_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="SR W%" field="short_rest_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Cold Weather" field="cold_weather_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="CW W%" field="cold_weather_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => (
            <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
              <TeamTd name={t.team} sport={sport} />
              <Td value={t.division_record ?? '—'} color={FG} />
              <Td value={`${t.division_win_pct ?? 0}%`} color={pctGood(t.division_win_pct, 60, 40)} bold />
              <Td value={t.primetime_record ?? '—'} color={FG} />
              <Td value={`${t.primetime_win_pct ?? 0}%`} color={pctGood(t.primetime_win_pct, 60, 40)} bold />
              <Td value={t.short_rest_record ?? '—'} color={FG} />
              <Td value={`${t.short_rest_win_pct ?? 0}%`} color={pctGood(t.short_rest_win_pct, 55, 40)} />
              <Td value={t.cold_weather_record ?? '—'} color={FG} />
              <Td value={`${t.cold_weather_win_pct ?? 0}%`} color={pctGood(t.cold_weather_win_pct, 55, 40)} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function NHLGoalieTable({ teams, view, sortKey, sortDesc, onSort, sport }: any) {
  const NHL_LOGOS: Record<string, string> = {
    ANA:'ana',ARI:'ari',BOS:'bos',BUF:'buf',CGY:'cgy',CAR:'car',CHI:'chi',COL:'col',
    CBJ:'cbj',DAL:'dal',DET:'det',EDM:'edm',FLA:'fla',LAK:'la',MIN:'min',MTL:'mtl',
    NSH:'nsh',NJD:'njd',NYI:'nyi',NYR:'nyr',OTT:'ott',PHI:'phi',PIT:'pit',SEA:'sea',
    SJS:'sj',STL:'stl',TBL:'tb',TOR:'tor',UTA:'utah',VAN:'van',VGK:'vgs',WSH:'wsh',WPG:'wpg',
  };

  const sortedTeams = [...teams].sort((a, b) => {
    const av = a[sortKey] ?? 0;
    const bv = b[sortKey] ?? 0;
    return sortDesc ? (Number(bv) || 0) - (Number(av) || 0) : (Number(av) || 0) - (Number(bv) || 0);
  });

  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <div style={{ padding: '8px 0 12px', fontSize: '0.7rem', color: MUTED_FG }}>
        {view === 'goalie'
          ? '2024–25 regular season. Starter = goalie with most games started on current roster.'
          : '2024–25 regular season. Power play and penalty kill effectiveness.'}
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead>
          <tr>
            <SortTh label="Team" field="team_name" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
            <SortTh label="Pts%" field="point_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
            <SortTh label="GF/G" field="gf_pg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
            <SortTh label="GA/G" field="ga_pg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
            <SortTh label="Net" field="net_goals" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
            {view === 'goalie' ? <>
              <SortTh label="Starter" field="sv_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
              <SortTh label="SV%" field="sv_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
              <SortTh label="GAA" field="gaa" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
              <SortTh label="SO" field="shutouts" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
              <SortTh label="SF/G" field="sf_pg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
              <SortTh label="SA/G" field="sa_pg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
            </> : <>
              <SortTh label="PP%" field="pp_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
              <SortTh label="PK%" field="pk_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
              <SortTh label="FO%" field="faceoff_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
              <SortTh label="Shutouts" field="shutouts" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
            </>}
          </tr>
        </thead>
        <tbody>
          {sortedTeams.map((t: any) => {
            const logoAbbr = NHL_LOGOS[t.team] ?? t.team.toLowerCase();
            const logoUrl = `https://a.espncdn.com/i/teamlogos/nhl/500/${logoAbbr}.png`;
            const starter = t.starter ?? {};
            // Attach sv_pct/gaa from starter to team row for sorting
            const svPct = starter.sv_pct;
            const gaa = starter.gaa;
            return (
              <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
                <td style={{ padding: '6px 8px', fontWeight: 700, color: FG, fontFamily: 'Nunito' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <img src={logoUrl} alt="" style={{ width: 20, height: 20 }} onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                    {t.team_name}
                  </div>
                </td>
                <Td value={`${(t.point_pct * 100).toFixed(1)}%`} color={pctGood(t.point_pct * 100, 65, 45)} bold />
                <Td value={t.gf_pg.toFixed(2)} color={pctGood(t.gf_pg, 3.3, 2.8)} />
                <Td value={t.ga_pg.toFixed(2)} color={pctGood(-t.ga_pg, -2.8, -3.3)} />
                <Td value={`${t.net_goals >= 0 ? '+' : ''}${t.net_goals.toFixed(2)}`} color={diffColor(t.net_goals)} bold />
                {view === 'goalie' ? <>
                  <td style={{ padding: '6px 8px', color: FG, fontSize: '0.7rem', fontFamily: 'Nunito' }}>{starter.name ?? '—'}</td>
                  <Td value={svPct != null ? svPct.toFixed(4) : '—'} color={pctGood(svPct != null ? svPct * 100 : 0, 91.5, 90)} bold />
                  <Td value={gaa != null ? gaa.toFixed(2) : '—'} color={pctGood(gaa != null ? -gaa : 0, -2.5, -3.2)} />
                  <Td value={starter.shutouts ?? '—'} />
                  <Td value={t.sf_pg.toFixed(1)} color={pctGood(t.sf_pg, 31, 27)} />
                  <Td value={t.sa_pg.toFixed(1)} color={pctGood(-t.sa_pg, -27, -31)} />
                </> : <>
                  <Td value={`${t.pp_pct.toFixed(1)}%`} color={pctGood(t.pp_pct, 26, 18)} bold />
                  <Td value={`${t.pk_pct.toFixed(1)}%`} color={pctGood(t.pk_pct, 81, 75)} bold />
                  <Td value={`${t.faceoff_pct.toFixed(1)}%`} color={pctGood(t.faceoff_pct, 52, 48)} />
                  <Td value={t.shutouts ?? 0} />
                </>}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function NBAEfficiencyTable({ teams, sortKey, sortDesc, onSort, sport }: any) {
  const NBA_LOGOS: Record<string, string> = {
    ATL:'atl',BOS:'bos',BKN:'bkn',CHA:'cha',CHI:'chi',CLE:'cle',DAL:'dal',DEN:'den',
    DET:'det',GS:'gs',HOU:'hou',IND:'ind',LAC:'lac',LAL:'lal',MEM:'mem',MIA:'mia',
    MIL:'mil',MIN:'min',NO:'no',NY:'ny',OKC:'okc',ORL:'orl',PHI:'phi',PHX:'phx',
    POR:'por',SAC:'sac',SA:'sa',TOR:'tor',UTA:'uta',WSH:'wsh',
  };
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <div style={{ padding: '8px 0 12px', fontSize: '0.7rem', color: MUTED_FG }}>
        2024–25 regular season. Pace proxy = FGA + 0.44×FTA − OR + TOV. ORtg = PPG/Pace×100.
        League avg pace: ~101.2 · avg ORtg: ~112.5
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortTh label="Team" field="team_name" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="W-L" field="win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="PPG" field="ppg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Pace" field="pace" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="ORtg" field="ortg_proxy" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="FG%" field="fg_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="3P%" field="three_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="3P Rate" field="three_rate" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="FT%" field="ft_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="AST" field="ast" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="TOV" field="tov" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="A/TO" field="ast_to" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="REB" field="reb" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => {
            const logoAbbr = NBA_LOGOS[t.team] ?? t.team.toLowerCase();
            const logoUrl = `https://a.espncdn.com/i/teamlogos/nba/500/${logoAbbr}.png`;
            return (
              <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
                <td style={{ padding: '6px 8px', fontWeight: 700, color: FG, fontFamily: 'Nunito' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <img src={logoUrl} alt="" style={{ width: 20, height: 20 }} onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                    {t.team_name}
                  </div>
                </td>
                <Td value={`${t.wins}-${t.losses}`} color={FG} />
                <Td value={t.ppg.toFixed(1)} color={pctGood(t.ppg, 118, 110)} bold />
                <Td value={t.pace.toFixed(1)} color={t.pace > 103 ? YELLOW : t.pace < 99 ? BLUE : MUTED_FG} />
                <Td value={t.ortg_proxy?.toFixed(1) ?? '—'} color={pctGood(t.ortg_proxy, 116, 110)} bold />
                <Td value={`${t.fg_pct.toFixed(1)}%`} color={pctGood(t.fg_pct, 48, 44)} />
                <Td value={`${t.three_pct.toFixed(1)}%`} color={pctGood(t.three_pct, 38, 33)} />
                <Td value={`${t.three_rate.toFixed(1)}%`} color={t.three_rate > 42 ? YELLOW : MUTED_FG} />
                <Td value={`${t.ft_pct.toFixed(1)}%`} color={pctGood(t.ft_pct, 80, 72)} />
                <Td value={t.ast.toFixed(1)} color={pctGood(t.ast, 28, 22)} />
                <Td value={t.tov.toFixed(1)} color={pctGood(-t.tov, -12, -16)} />
                <Td value={t.ast_to.toFixed(2)} color={pctGood(t.ast_to, 2.0, 1.5)} />
                <Td value={t.reb.toFixed(1)} />
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function NFLFirstHalfTable({ teams, sortKey, sortDesc, onSort, sport }: any) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <div style={{ padding: '8px 0 12px', fontSize: '0.7rem', color: MUTED_FG }}>
        First-half scoring stats from ESPN game data (2015–2025 regular season).
        H1 Margin = avg points scored minus allowed in the first half.
        Q1 Lead W% = win rate when leading after Q1.
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortTh label="Team" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="GP" field="games" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="H1 Record" field="h1_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="H1 W%" field="h1_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="H1 Scored" field="avg_h1_scored" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="H1 Allowed" field="avg_h1_allowed" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="H1 Margin" field="avg_h1_margin" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Avg H1 Total" field="avg_h1_total" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Q1 Scored" field="avg_q1_scored" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Q1 Allowed" field="avg_q1_allowed" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Q1 Lead W%" field="q1_lead_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Comeback%" field="q1_trail_comeback_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Blowout%" field="blowout_rate" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => {
            const h1Rec = `${t.h1_wins}-${t.h1_losses}${t.h1_ties > 0 ? `-${t.h1_ties}` : ''}`;
            const margin = t.avg_h1_margin ?? 0;
            return (
              <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
                <TeamTd name={t.team} sport={sport} />
                <Td value={t.games} />
                <Td value={h1Rec} color={FG} />
                <Td value={`${((t.h1_win_pct ?? 0) * 100).toFixed(1)}%`} color={pctGood((t.h1_win_pct ?? 0) * 100, 55, 45)} bold />
                <Td value={(t.avg_h1_scored ?? 0).toFixed(1)} color={pctGood(t.avg_h1_scored, 14, 10)} />
                <Td value={(t.avg_h1_allowed ?? 0).toFixed(1)} color={pctGood(-(t.avg_h1_allowed ?? 0), -10, -14)} />
                <Td value={`${margin >= 0 ? '+' : ''}${margin.toFixed(1)}`} color={diffColor(margin)} bold />
                <Td value={(t.avg_h1_total ?? 0).toFixed(1)} color={BLUE} />
                <Td value={(t.avg_q1_scored ?? 0).toFixed(1)} />
                <Td value={(t.avg_q1_allowed ?? 0).toFixed(1)} />
                <Td value={t.q1_lead_win_pct != null ? `${((t.q1_lead_win_pct) * 100).toFixed(1)}%` : '—'} color={pctGood((t.q1_lead_win_pct ?? 0) * 100, 75, 60)} />
                <Td value={t.q1_trail_comeback_pct != null ? `${((t.q1_trail_comeback_pct) * 100).toFixed(1)}%` : '—'} color={pctGood((t.q1_trail_comeback_pct ?? 0) * 100, 40, 25)} />
                <Td value={`${((t.blowout_rate ?? 0) * 100).toFixed(1)}%`} color={(t.blowout_rate ?? 0) > 0.2 ? EMERALD : MUTED_FG} />
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}


function NCAABEfficiencyTable({ teams, sortKey, sortDesc, onSort }: any) {
  const TIER_COLORS: Record<string, string> = {
    ELITE:     'oklch(75% 0.18 150)',
    CONTENDER: 'oklch(75% 0.15 200)',
    AVERAGE:   'oklch(70% 0.05 250)',
    BELOW:     'oklch(70% 0.12 30)',
    BOTTOM:    'oklch(60% 0.15 20)',
  };
  const CONF_ABBR: Record<string, string> = {
    Big12: 'B12', SEC: 'SEC', BigTen: 'B10', ACC: 'ACC', BigEast: 'BE', American: 'AAC',
  };
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <div style={{ padding: '8px 0 12px', fontSize: '0.7rem', color: MUTED_FG }}>
        Composite AdjEM from points-for/against, win%, away performance, pythagorean expectancy, and conference SOS tier.
        Power conference bonus applied: SEC/Big12/BigTen/ACC +4 pts · BigEast/AAC proportional.
        Mid-majors ranked on raw dominance only. Not a BartTorvik/KenPom clone.
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortTh label="#" field="rank" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Team" field="team_display" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Conf" field="conference" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Record" field="win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="AdjEM" field="adj_em" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Tier" field="tier" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="ORtg" field="ortg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="DRtg" field="drtg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="PPG" field="ppg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="PAPG" field="papg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Diff" field="diff" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Avg Total" field="avg_total" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Win%" field="win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Away%" field="away_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Pythag" field="pyth_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Luck" field="luck" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => {
            const adjEm = t.adj_em ?? 0;
            const adjEmColor = adjEm >= 8 ? EMERALD : adjEm >= 3 ? YELLOW : adjEm >= -3 ? MUTED_FG : RED;
            const tierColor = TIER_COLORS[t.tier] ?? MUTED_FG;
            const confLabel = CONF_ABBR[t.conference] ?? (t.conference ?? '—');
            return (
              <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
                <td style={{ padding: '6px 8px', color: MUTED_FG, fontSize: '0.7rem', width: 36 }}>{t.rank}</td>
                <td style={{ padding: '6px 8px', fontWeight: 700, color: FG, fontFamily: 'Nunito', minWidth: 160 }}>
                  {t.team_display}
                </td>
                <td style={{ padding: '6px 8px', color: t.conference ? BLUE : MUTED_FG, fontSize: '0.7rem', fontWeight: t.conference ? 700 : 400 }}>
                  {confLabel}
                </td>
                <Td value={t.record} color={FG} />
                <Td value={`${adjEm >= 0 ? '+' : ''}${adjEm.toFixed(1)}`} color={adjEmColor} bold />
                <td style={{ padding: '6px 8px' }}>
                  <span style={{ color: tierColor, fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.04em' }}>{t.tier}</span>
                </td>
                <Td value={t.ortg?.toFixed(1) ?? '—'} color={pctGood(t.ortg, 108, 103)} />
                <Td value={t.drtg?.toFixed(1) ?? '—'} color={pctGood(-(t.drtg ?? 100), -92, -97)} />
                <Td value={t.ppg?.toFixed(1) ?? '—'} color={pctGood(t.ppg, 82, 72)} />
                <Td value={t.papg?.toFixed(1) ?? '—'} color={pctGood(-(t.papg ?? 75), -65, -75)} />
                <Td value={`${(t.diff ?? 0) >= 0 ? '+' : ''}${(t.diff ?? 0).toFixed(1)}`} color={diffColor(t.diff ?? 0)} bold />
                <Td value={t.avg_total?.toFixed(1) ?? '—'} color={BLUE} />
                <Td value={`${t.win_pct?.toFixed(1)}%`} color={pctGood(t.win_pct, 65, 50)} />
                <Td value={`${t.away_win_pct?.toFixed(1)}%`} color={pctGood(t.away_win_pct, 60, 45)} />
                <Td value={`${t.pyth_pct?.toFixed(1)}%`} color={pctGood(t.pyth_pct, 65, 50)} />
                <Td value={`${(t.luck ?? 0) >= 0 ? '+' : ''}${(t.luck ?? 0).toFixed(3)}`} color={(t.luck ?? 0) > 0.05 ? EMERALD : (t.luck ?? 0) < -0.05 ? RED : MUTED_FG} />
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default BettingRankings;
