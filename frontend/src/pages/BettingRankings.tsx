/* v2 — fixed NFL sort crash */
/**
 * Betting Rankings — Multi-sport betting analytics.
 * Sport tabs at top, sport-specific view pills below.
 * MLB: Full Game, First 5 Innings, Home/Away Splits
 * NFL: (coming soon) ATS, Totals, Situational
 */
import { useState, useEffect } from 'react';
import '../styles/analytics.css';
import { getApiUrl } from '../config';

const EMERALD   = 'oklch(69.6% .17 162.48)';
const BRAND_RED = 'oklch(63.7% .237 25.331)';
const BLUE      = 'oklch(62.3% .214 259.815)';
const YELLOW    = 'oklch(79.5% .184 86.047)';
const MUTED_FG  = 'oklch(70.8% 0 0)';
const BORDER    = 'oklch(100% 0 0 / .1)';
const FG        = 'oklch(98.5% 0 0)';

type Sport = 'mlb' | 'nfl' | 'nba' | 'nhl' | 'ncaaf';

const SPORTS: { key: Sport; label: string; active: boolean }[] = [
  { key: 'mlb',   label: 'MLB',   active: true },
  { key: 'nfl',   label: 'NFL',   active: true },
  { key: 'ncaaf', label: 'NCAAF', active: true },
  { key: 'nba',   label: 'NBA',   active: true },
  { key: 'nhl',   label: 'NHL',   active: true },
];

const SPORT_VIEWS: Record<Sport, { key: string; label: string }[]> = {
  mlb:   [{ key: 'full_game', label: 'FULL GAME' }, { key: 'first_5', label: 'FIRST 5 INNINGS' }, { key: 'splits', label: 'HOME / AWAY SPLITS' }],
  nfl:   [{ key: 'full_game', label: 'FULL GAME' }, { key: 'first_half', label: 'FIRST HALF' }, { key: 'ats', label: 'ATS RECORD' }, { key: 'totals', label: 'TOTALS' }, { key: 'situational', label: 'SITUATIONAL' }],
  ncaaf: [{ key: 'full_game', label: 'FULL GAME' }, { key: 'ats', label: 'ATS RECORD' }, { key: 'totals', label: 'TOTALS' }],
  nba:   [{ key: 'full_game', label: 'FULL GAME' }, { key: 'first_half', label: 'FIRST HALF' }, { key: 'ats', label: 'ATS RECORD' }],
  nhl:   [{ key: 'full_game', label: 'FULL GAME' }, { key: 'totals', label: 'TOTALS' }],
};

export function BettingRankings() {
  const [sport, setSport] = useState<Sport>('mlb');
  const [view, setView] = useState('full_game');
  const [teams, setTeams] = useState<any[]>([]);
  const [atsTeams, setAtsTeams] = useState<any[]>([]);
  const [seasons, setSeasons] = useState<{ key: string; label: string; current: boolean }[]>([]);
  const [atsSeasons, setAtsSeasons] = useState<{ key: string; label: string; current: boolean }[]>([]);
  const [selectedSeason, setSelectedSeason] = useState('');
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState('win_pct');
  const [sortDesc, setSortDesc] = useState(true);

  useEffect(() => {
    setTeams([]);
    setAtsTeams([]);
    setView('full_game');
    setSortKey(sport === 'mlb' ? 'fg_win_pct' : 'win_pct');
    setSelectedSeason('');
    setLoading(true);

    const fetches: Promise<any>[] = [
      fetch(getApiUrl(`f5/team-rankings?sport=${sport}`)).then(r => r.json()),
    ];
    if (sport === 'nfl') {
      fetches.push(fetch(getApiUrl(`f5/ats-rankings?sport=nfl`)).then(r => r.json()).catch(() => ({ teams: [] })));
    }

    Promise.all(fetches).then(([main, ats]) => {
      setTeams(main.teams ?? []);
      setSeasons(main.seasons ?? []);
      setSelectedSeason(main.season ?? '');
      if (ats) {
        setAtsTeams(ats.teams ?? []);
        setAtsSeasons(ats.seasons ?? []);
      }
    })
    .catch(() => setTeams([]))
    .finally(() => setLoading(false));
  }, [sport]);

  const changeSeason = (key: string) => {
    setTeams([]);
    setAtsTeams([]);
    setSelectedSeason(key);
    setLoading(true);

    const isAtsView = view === 'ats' || view === 'totals';
    const endpoint = isAtsView
      ? `f5/ats-rankings?sport=${sport}&season=${key}`
      : `f5/team-rankings?sport=${sport}&season=${key}`;

    fetch(getApiUrl(endpoint))
      .then(r => r.json())
      .then(d => {
        if (isAtsView) setAtsTeams(d.teams ?? []);
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
    setSortKey(v === 'ats' ? 'ats_cover_pct' : v === 'totals' ? 'over_pct' : v === 'first_5' ? 'f5_win_pct' : v === 'splits' ? (sport === 'mlb' ? 'fg_home_rpg' : 'home_ppg') : (sport === 'mlb' ? 'fg_win_pct' : 'win_pct'));
  };

  const handleSort = (key: string) => {
    if (sortKey === key) setSortDesc(!sortDesc);
    else { setSortKey(key); setSortDesc(true); }
  };

  const sorted = [...teams].sort((a, b) => {
    const av = a[sortKey] ?? 0;
    const bv = b[sortKey] ?? 0;
    return sortDesc ? bv - av : av - bv;
  });

  const views = SPORT_VIEWS[sport] ?? [];
  const sportActive = SPORTS.find(s => s.key === sport)?.active ?? false;

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
          {((view === 'ats' || view === 'totals') ? atsSeasons : seasons).length > 1 && (
            <>
              <span style={{ marginLeft: 16, fontSize: '0.68rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em' }}>SEASON</span>
              {((view === 'ats' || view === 'totals') ? atsSeasons : seasons).map(s => (
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
          {sport === 'nfl' && view === 'ats' && <NFLAtsTable teams={[...atsTeams].sort((a,b) => sortDesc ? (b[sortKey]??0)-(a[sortKey]??0) : (a[sortKey]??0)-(b[sortKey]??0))} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} sport={sport} />}
          {sport === 'nfl' && view === 'totals' && <NFLTotalsTable teams={[...atsTeams].sort((a,b) => sortDesc ? (b[sortKey]??0)-(a[sortKey]??0) : (a[sortKey]??0)-(b[sortKey]??0))} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} sport={sport} />}
          {sport !== 'mlb' && !['full_game','splits','ats','totals'].includes(view) && (
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
    LAC:'lac',LAR:'lar',LV:'lv',MIA:'mia',MIN:'min',NE:'ne',NO:'no',NYG:'nyg',
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

export default BettingRankings;
