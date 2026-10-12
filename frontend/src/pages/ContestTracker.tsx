import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getApiUrl } from '../config';
import { MetaTags } from '../components/MetaTags';
import { logo, wpColor, COLORS, withAlpha } from './survivorUtils';
import '../styles/analytics.css';

const { EMERALD, RED, YELLOW, BLUE } = COLORS;

interface SurvivorGame {
  home: string; away: string; home_wp: number; away_wp: number;
  home_label: string; away_label: string;
}
type WeeksData = Record<number, SurvivorGame[]>;

interface NflMatchup {
  home: string; away: string; homeAbbr: string; awayAbbr: string;
  spread: number | null; total: number | null; time: string;
}

type ContestType = 'survivor' | 'pickem' | 'confidence';
type PickResult = 'win' | 'loss' | 'push' | 'pending';

interface ContestEntry {
  id: number; contest_name: string; contest_type: ContestType;
  entry_name: string; entry_fee: number; status: string; season: number;
}
interface ContestPick {
  id: number; entry_id: number; week: string; team: string;
  opponent: string | null; spread: number | null; confidence_rank: number | null;
  result: PickResult; game_score: string | null;
}
interface Summary {
  total_entries: number; alive: number; eliminated: number;
  total_picks: number; wins: number; losses: number; pushes: number; pending: number;
  total_invested: number;
}

// ── NFL team data ────────────────────────────────────────────────────────────

interface NflTeam { abbr: string; name: string; city: string; espn: string; }

const NFL_TEAMS: NflTeam[] = [
  { abbr:'ARI', name:'Cardinals',   city:'Arizona',         espn:'ari' },
  { abbr:'ATL', name:'Falcons',     city:'Atlanta',         espn:'atl' },
  { abbr:'BAL', name:'Ravens',      city:'Baltimore',       espn:'bal' },
  { abbr:'BUF', name:'Bills',       city:'Buffalo',         espn:'buf' },
  { abbr:'CAR', name:'Panthers',    city:'Carolina',        espn:'car' },
  { abbr:'CHI', name:'Bears',       city:'Chicago',         espn:'chi' },
  { abbr:'CIN', name:'Bengals',     city:'Cincinnati',      espn:'cin' },
  { abbr:'CLE', name:'Browns',      city:'Cleveland',       espn:'cle' },
  { abbr:'DAL', name:'Cowboys',     city:'Dallas',          espn:'dal' },
  { abbr:'DEN', name:'Broncos',     city:'Denver',          espn:'den' },
  { abbr:'DET', name:'Lions',       city:'Detroit',         espn:'det' },
  { abbr:'GB',  name:'Packers',     city:'Green Bay',       espn:'gb'  },
  { abbr:'HOU', name:'Texans',      city:'Houston',         espn:'hou' },
  { abbr:'IND', name:'Colts',       city:'Indianapolis',    espn:'ind' },
  { abbr:'JAX', name:'Jaguars',     city:'Jacksonville',    espn:'jax' },
  { abbr:'KC',  name:'Chiefs',      city:'Kansas City',     espn:'kc'  },
  { abbr:'LAC', name:'Chargers',    city:'Los Angeles',     espn:'lac' },
  { abbr:'LAR', name:'Rams',        city:'Los Angeles',     espn:'lar' },
  { abbr:'LV',  name:'Raiders',     city:'Las Vegas',       espn:'lv'  },
  { abbr:'MIA', name:'Dolphins',    city:'Miami',           espn:'mia' },
  { abbr:'MIN', name:'Vikings',     city:'Minnesota',       espn:'min' },
  { abbr:'NE',  name:'Patriots',    city:'New England',     espn:'ne'  },
  { abbr:'NO',  name:'Saints',      city:'New Orleans',     espn:'no'  },
  { abbr:'NYG', name:'Giants',      city:'New York',        espn:'nyg' },
  { abbr:'NYJ', name:'Jets',        city:'New York',        espn:'nyj' },
  { abbr:'PHI', name:'Eagles',      city:'Philadelphia',    espn:'phi' },
  { abbr:'PIT', name:'Steelers',    city:'Pittsburgh',      espn:'pit' },
  { abbr:'SF',  name:'49ers',       city:'San Francisco',   espn:'sf'  },
  { abbr:'SEA', name:'Seahawks',    city:'Seattle',         espn:'sea' },
  { abbr:'TB',  name:'Buccaneers',  city:'Tampa Bay',       espn:'tb'  },
  { abbr:'TEN', name:'Titans',      city:'Tennessee',       espn:'ten' },
  { abbr:'WAS', name:'Commanders',  city:'Washington',      espn:'wsh' },
];

const teamByAbbr = (abbr: string) => NFL_TEAMS.find(t => t.abbr === abbr);
const teamLogo = (espn: string) => `https://a.espncdn.com/i/teamlogos/nfl/500/${espn}.png`;

function TeamChip({ abbr, size = 'sm', result }: { abbr: string; size?: 'sm' | 'md'; result?: string }) {
  const t = teamByAbbr(abbr);
  if (!t) return <span className="text-xs text-slate-500">{abbr}</span>;
  const dim = size === 'md' ? 'w-7 h-7' : 'w-5 h-5';
  const border = result === 'win' ? 'border-emerald-500/60' : result === 'loss' ? 'border-red-500/60' : result === 'push' ? 'border-yellow-500/60' : 'border-slate-600';
  const bg = result === 'win' ? 'bg-emerald-900/20' : result === 'loss' ? 'bg-red-900/20' : 'bg-slate-800/80';
  return (
    <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg ${bg} border ${border}`} title={`${t.city} ${t.name}`}>
      <img src={teamLogo(t.espn)} alt={t.abbr} className={`${dim} object-contain`} onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
      <span className={`font-bold ${size === 'md' ? 'text-xs' : 'text-[10px]'} text-white`}>{t.abbr}</span>
    </div>
  );
}

const RESULT_STYLE: Record<string, { bg: string; text: string }> = {
  win: { bg: 'bg-emerald-500/15', text: 'text-emerald-400' },
  loss: { bg: 'bg-red-500/15', text: 'text-red-400' },
  push: { bg: 'bg-yellow-500/15', text: 'text-yellow-400' },
  pending: { bg: 'bg-slate-700', text: 'text-slate-400' },
  alive: { bg: 'bg-emerald-500/15', text: 'text-emerald-400' },
  eliminated: { bg: 'bg-red-500/15', text: 'text-red-400' },
};

// ── Component ────────────────────────────────────────────────────────────────

export function ContestTracker() {
  const { token } = useAuth();
  const [entries, setEntries] = useState<ContestEntry[]>([]);
  const [picks, setPicks] = useState<Record<number, ContestPick[]>>({});
  const [usedTeams, setUsedTeams] = useState<Record<number, string[]>>({});
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<ContestType | 'all' | 'live'>('all');
  const [expandedEntry, setExpandedEntry] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [survivorWeeks, setSurvivorWeeks] = useState<WeeksData>({});
  const [gridSort, setGridSort] = useState<{ col: number; dir: 'desc' | 'asc' } | null>(null);
  const [weekMatchups, setWeekMatchups] = useState<NflMatchup[]>([]);
  // Staged picks for batch submission (pickem/confidence)
  const [stagedPicks, setStagedPicks] = useState<Record<string, { team: string; opp: string; spread: number | null; rank: number | null }>>({});

  // Pick form
  const [pickWeek, setPickWeek] = useState('1');
  const [pickTeam, setPickTeam] = useState('');
  const [pickOpponent, setPickOpponent] = useState('');
  const [pickSpread, setPickSpread] = useState('');
  const [pickConfidence, setPickConfidence] = useState('');

  // New entry form
  const [showNewEntry, setShowNewEntry] = useState(false);
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState<ContestType>('survivor');
  const [newEntryName, setNewEntryName] = useState('');
  const [newFee, setNewFee] = useState('');

  const headers = useCallback((): HeadersInit => ({
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }), [token]);

  const fetchAll = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [eR, sR] = await Promise.all([
        fetch(getApiUrl('contests/entries'), { headers: headers() }),
        fetch(getApiUrl('contests/summary'), { headers: headers() }),
      ]);
      if (eR.ok) { const d = await eR.json(); setEntries(d.entries ?? []); }
      if (sR.ok) setSummary(await sR.json());
    } catch {}
    setLoading(false);
  }, [token, headers]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // Fetch NFL matchups for pick'em/confidence — includes completed games from live-scores
  useEffect(() => {
    const hasPickem = entries.some(e => e.contest_type === 'pickem' || e.contest_type === 'confidence');
    if (!hasPickem) return;

    const nameToAbbr = (name: string) => NFL_TEAMS.find(t => name.includes(t.name) || name.includes(t.city))?.abbr ?? '';
    const DAY = 86400000;

    Promise.all([
      fetch(getApiUrl('games?user_id=default&sport_key=americanfootball_nfl')).then(r => r.ok ? r.json() : []),
      fetch(getApiUrl('f5/live-scores?sport=americanfootball_nfl&days=3')).then(r => r.ok ? r.json() : { games: [] }).catch(() => ({ games: [] })),
      fetch(getApiUrl('f5/game-results?sport=americanfootball_nfl&days=3')).then(r => r.ok ? r.json() : { games: [] }).catch(() => ({ games: [] })),
    ]).then(([oddsGames, scoresData, resultsData]: [any[], any, any]) => {
      const now = Date.now();
      // Find anchor = earliest upcoming game
      const upcomingTimes = oddsGames.map(g => new Date(g.state.commence_time).getTime()).filter(t => t > now - DAY);
      const anchor = upcomingTimes.length ? Math.min(...upcomingTimes) : now;
      const windowStart = anchor - 5 * DAY; // catch Thu/Wed games
      const windowEnd = anchor + 4 * DAY;

      // Build from odds API (upcoming games with spreads)
      const seen = new Set<string>();
      const matchups: NflMatchup[] = [];

      for (const g of oddsGames) {
        const t = new Date(g.state.commence_time).getTime();
        if (t < windowStart || t > windowEnd) continue;
        const ha = nameToAbbr(g.state.home_team.name);
        const aa = nameToAbbr(g.state.away_team.name);
        if (!ha || !aa) continue;
        const key = `${aa}@${ha}`;
        if (seen.has(key)) continue;
        seen.add(key);
        const odds = g.odds?.[0] ?? {};
        matchups.push({
          home: g.state.home_team.name, away: g.state.away_team.name,
          homeAbbr: ha, awayAbbr: aa,
          spread: odds.home_spread ?? null, total: odds.total ?? null,
          time: new Date(g.state.commence_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: 'America/Chicago' }),
        });
      }

      // Add completed/live games from live-scores and game-results
      const extraSources = [...(scoresData.games ?? []), ...(resultsData.games ?? [])];
      for (const sg of extraSources) {
        const ha = nameToAbbr(sg.home_team ?? '');
        const aa = nameToAbbr(sg.away_team ?? '');
        if (!ha || !aa) continue;
        const key = `${aa}@${ha}`;
        if (seen.has(key)) continue;
        const t = new Date(sg.commence_time).getTime();
        if (t < windowStart || t > windowEnd) continue;
        seen.add(key);
        matchups.push({
          home: sg.home_team, away: sg.away_team,
          homeAbbr: ha, awayAbbr: aa,
          spread: null, total: null,
          time: new Date(sg.commence_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: 'America/Chicago' }),
        });
      }

      // Also fill from survivor weeks data (has ALL weeks including completed games)
      if (Object.keys(survivorWeeks).length > 0) {
        // Find current NFL week from survivor data by matching anchor date
        for (const [wkStr, games] of Object.entries(survivorWeeks)) {
          for (const g of games) {
            const ha = g.home;
            const aa = g.away;
            const key = `${aa}@${ha}`;
            if (seen.has(key)) continue;
            seen.add(key);
            const ht = NFL_TEAMS.find(t => t.abbr === ha);
            const at = NFL_TEAMS.find(t => t.abbr === aa);
            if (!ht || !at) continue;
            // Only add Week 1 games (wk matches pickWeek)
            if (wkStr !== pickWeek) continue;
            matchups.push({
              home: `${ht.city} ${ht.name}`, away: `${at.city} ${at.name}`,
              homeAbbr: ha, awayAbbr: aa,
              spread: null, total: null, time: '',
            });
          }
        }
      }

      // Sort by time
      matchups.sort((a, b) => a.time.localeCompare(b.time));
      setWeekMatchups(matchups);
    }).catch(() => {});
  }, [entries, survivorWeeks, pickWeek]);

  // Fetch survivor weeks data for the full grid
  useEffect(() => {
    const hasSurvivor = entries.some(e => e.contest_type === 'survivor');
    if (!hasSurvivor || Object.keys(survivorWeeks).length > 0) return;
    fetch(getApiUrl('f5/survivor'))
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!d?.weeks) return;
        const parsed: WeeksData = {};
        for (const [wk, games] of Object.entries(d.weeks)) {
          parsed[Number(wk)] = games as SurvivorGame[];
        }
        setSurvivorWeeks(parsed);
      })
      .catch(() => {});
  }, [entries]);

  const fetchPicks = useCallback(async (entryId: number) => {
    try {
      const [pR, uR] = await Promise.all([
        fetch(getApiUrl(`contests/picks/${entryId}`), { headers: headers() }),
        fetch(getApiUrl(`contests/used-teams/${entryId}`), { headers: headers() }),
      ]);
      if (pR.ok) { const d = await pR.json(); setPicks(prev => ({ ...prev, [entryId]: d.picks ?? [] })); }
      if (uR.ok) { const d = await uR.json(); setUsedTeams(prev => ({ ...prev, [entryId]: d.used_teams ?? [] })); }
    } catch {}
  }, [headers]);

  // Auto-fetch picks for all entries on load
  useEffect(() => {
    entries.forEach(e => { if (!picks[e.id]) fetchPicks(e.id); });
  }, [entries, fetchPicks]);

  const toggleEntry = (id: number) => {
    setExpandedEntry(expandedEntry === id ? null : id);
  };

  const addPick = async (entryId: number) => {
    if (!pickTeam) return;
    setSubmitting(true);
    try {
      const body: Record<string, unknown> = { entry_id: entryId, week: pickWeek, team: pickTeam };
      if (pickOpponent) body.opponent = pickOpponent;
      if (pickSpread) body.spread = parseFloat(pickSpread);
      if (pickConfidence) body.confidence_rank = parseInt(pickConfidence);

      const r = await fetch(getApiUrl('contests/picks'), {
        method: 'POST', headers: headers(), body: JSON.stringify(body),
      });
      if (!r.ok) { const e = await r.json(); alert(e.detail || 'Error adding pick'); return; }

      // Clear cached picks and refetch
      setPicks(prev => { const c = { ...prev }; delete c[entryId]; return c; });
      setUsedTeams(prev => { const c = { ...prev }; delete c[entryId]; return c; });
      await fetchPicks(entryId);
      await fetchAll();
      setPickTeam(''); setPickOpponent(''); setPickSpread(''); setPickConfidence('');
    } finally { setSubmitting(false); }
  };

  const submitStagedPicks = async (entryId: number) => {
    const staged = Object.values(stagedPicks);
    if (staged.length === 0) return;
    setSubmitting(true);
    try {
      for (const pick of staged) {
        await fetch(getApiUrl('contests/picks'), {
          method: 'POST', headers: headers(),
          body: JSON.stringify({
            entry_id: entryId, week: pickWeek, team: pick.team,
            opponent: pick.opp, spread: pick.spread,
            ...(pick.rank != null ? { confidence_rank: pick.rank } : {}),
          }),
        });
      }
      setStagedPicks({});
      setPicks(prev => { const c = { ...prev }; delete c[entryId]; return c; });
      await fetchPicks(entryId);
      await fetchAll();
    } finally { setSubmitting(false); }
  };

  const addEntry = async () => {
    if (!newName || !newEntryName) return;
    setSubmitting(true);
    try {
      const r = await fetch(getApiUrl('contests/entries'), {
        method: 'POST', headers: headers(),
        body: JSON.stringify({ contest_name: newName, contest_type: newType, entry_name: newEntryName, entry_fee: newFee ? parseFloat(newFee) : 0 }),
      });
      if (!r.ok) { const e = await r.json(); alert(e.detail || 'Error'); return; }
      await fetchAll();
      setShowNewEntry(false); setNewName(''); setNewEntryName(''); setNewFee('');
    } finally { setSubmitting(false); }
  };

  const filteredEntries = activeTab === 'all' || activeTab === 'live' ? entries : entries.filter(e => e.contest_type === activeTab);

  // Current week picks across all entries for LIVE view
  const currentWeekPicks = entries.map(entry => {
    const ep = picks[entry.id] ?? [];
    const weekPicks = ep.filter(p => p.week === pickWeek);
    return { entry, picks: weekPicks };
  }).filter(e => e.picks.length > 0);

  return (
    <div className="analytics-page p-4">
      <MetaTags title="Contest Tracker" description="Track survivor pools, pick'em, and confidence pools." />

      {/* Header */}
      <div className="mb-6 flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-100 mb-1" style={{ letterSpacing: '-0.02em' }}>CONTEST TRACKER</h1>
          <p className="text-slate-400 text-sm">Manage survivor, pick'em, and confidence pool entries</p>
        </div>
        <button onClick={() => setShowNewEntry(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm rounded-lg transition-colors">
          + New Entry
        </button>
      </div>

      {/* Summary */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
          {[
            { label: 'Entries', val: summary.total_entries, sub: `${summary.alive} alive`, color: 'text-white' },
            { label: 'Picks', val: summary.total_picks, sub: `${summary.pending} pending`, color: 'text-white' },
            { label: 'Record', val: `${summary.wins}W-${summary.losses}L`, sub: summary.pushes > 0 ? `${summary.pushes} push` : '', color: 'text-emerald-400' },
            { label: 'Win Rate', val: summary.wins + summary.losses > 0 ? `${((summary.wins / (summary.wins + summary.losses)) * 100).toFixed(0)}%` : '—', sub: '', color: 'text-blue-400' },
            { label: 'Invested', val: `$${summary.total_invested?.toLocaleString()}`, sub: '', color: 'text-white' },
          ].map(c => (
            <div key={c.label} className="bg-slate-800/60 border border-slate-700 rounded-lg p-3 text-center">
              <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">{c.label}</div>
              <div className={`text-2xl font-black ${c.color}`}>{c.val}</div>
              {c.sub && <div className="text-xs text-slate-400">{c.sub}</div>}
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {/* LIVE tab */}
        <button onClick={() => setActiveTab('live')}
          className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
            activeTab === 'live' ? 'bg-red-600 text-white shadow-lg shadow-red-600/30' : 'bg-slate-800 text-slate-400 hover:bg-slate-700 border border-slate-700'
          }`}>
          <span className={`w-2 h-2 rounded-full ${activeTab === 'live' ? 'bg-white animate-pulse' : 'bg-red-500 animate-pulse'}`} />
          Live
        </button>
        {([
          { key: 'all' as const, label: 'All' },
          { key: 'survivor' as const, label: 'Survivor' },
          { key: 'pickem' as const, label: "Pick'em" },
          { key: 'confidence' as const, label: 'Confidence' },
        ]).map(tab => {
          const count = tab.key === 'all' ? entries.length : entries.filter(e => e.contest_type === tab.key).length;
          if (tab.key !== 'all' && count === 0) return null;
          return (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                activeTab === tab.key ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30' : 'bg-slate-800 text-slate-400 hover:bg-slate-700 border border-slate-700'
              }`}>{tab.label} ({count})</button>
          );
        })}
      </div>

      {/* LIVE VIEW — all picks for current week at a glance */}
      {activeTab === 'live' && !loading && (
        <div className="space-y-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
              <span className="text-sm font-bold text-white">Week {pickWeek} — All Contest Picks</span>
            </div>
            <select value={pickWeek} onChange={e => setPickWeek(e.target.value)}
              className="bg-slate-800 border border-slate-600 rounded px-2 py-1.5 text-white text-xs focus:border-blue-500 focus:outline-none">
              {Array.from({ length: 18 }, (_, i) => <option key={i + 1} value={String(i + 1)}>Week {i + 1}</option>)}
            </select>
          </div>

          {currentWeekPicks.length === 0 && (
            <div className="text-center py-12 text-slate-500 text-sm bg-slate-800/40 rounded-lg border border-slate-700">
              No picks made for Week {pickWeek} yet.
            </div>
          )}

          {currentWeekPicks.map(({ entry, picks: wp }) => {
            const typeColor = entry.contest_type === 'survivor' ? '#6ee7b7' : entry.contest_type === 'pickem' ? '#93c5fd' : '#c4b5fd';
            const typeLabel = entry.contest_type === 'pickem' ? "PICK'EM" : entry.contest_type.toUpperCase();
            const sortedPicks = [...wp].sort((a, b) => (b.confidence_rank ?? 0) - (a.confidence_rank ?? 0));

            return (
              <div key={entry.id} className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
                {/* Contest header */}
                <div className="px-4 py-2.5 border-b border-slate-700/50 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider"
                      style={{ background: typeColor + '22', color: typeColor }}>{typeLabel}</span>
                    <span className="text-sm font-bold text-white">{entry.contest_name}</span>
                    <span className="text-[10px] text-slate-500">{entry.entry_name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {wp.filter(p => p.result === 'win').length > 0 && (
                      <span className="text-[10px] font-bold text-emerald-400">{wp.filter(p => p.result === 'win').length}W</span>
                    )}
                    {wp.filter(p => p.result === 'loss').length > 0 && (
                      <span className="text-[10px] font-bold text-red-400">{wp.filter(p => p.result === 'loss').length}L</span>
                    )}
                    {wp.filter(p => p.result === 'pending').length > 0 && (
                      <span className="text-[10px] font-bold text-slate-400">{wp.filter(p => p.result === 'pending').length} pending</span>
                    )}
                  </div>
                </div>

                {/* Picks row */}
                <div className="px-4 py-3 flex flex-wrap gap-2">
                  {sortedPicks.map(p => {
                    const rs = RESULT_STYLE[p.result];
                    return (
                      <div key={p.id} className={`flex items-center gap-2 rounded-lg px-3 py-2 border ${rs.bg} ${p.result === 'pending' ? 'border-slate-600' : p.result === 'win' ? 'border-emerald-600/40' : 'border-red-600/40'}`}>
                        <img src={logo(p.team)} alt={p.team} className="w-8 h-8 object-contain"
                          onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-sm font-bold text-white">{p.team}</span>
                            {p.confidence_rank != null && (
                              <span className="text-xs font-black text-purple-400 bg-purple-500/15 px-1.5 py-0.5 rounded">{p.confidence_rank}pt</span>
                            )}
                          </div>
                          <div className="flex items-center gap-1.5 text-[10px]">
                            {p.opponent && <span className="text-slate-500">vs {p.opponent}</span>}
                            {p.spread != null && <span className="text-slate-500">({p.spread > 0 ? '+' : ''}{p.spread})</span>}
                            {p.game_score && <span className="text-slate-400 font-bold">{p.game_score}</span>}
                            <span className={`font-bold ${rs.text}`}>{p.result === 'pending' ? '•' : p.result.toUpperCase()}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {loading && <div className="text-center py-20 text-slate-400">Loading contests...</div>}

      {!loading && activeTab !== 'live' && filteredEntries.length === 0 && (
        <div className="text-center py-20 text-slate-500"><div className="text-4xl mb-3">🏆</div>No contest entries yet.</div>
      )}

      {/* Entries (hidden when LIVE tab is active) */}
      {activeTab !== 'live' && <div className="space-y-4">
        {filteredEntries.map(entry => {
          const isExpanded = expandedEntry === entry.id;
          const entryPicks = picks[entry.id] ?? [];
          const used = usedTeams[entry.id] ?? [];
          const available = NFL_TEAMS.filter(t => !used.includes(t.abbr));
          const wins = entryPicks.filter(p => p.result === 'win').length;
          const losses = entryPicks.filter(p => p.result === 'loss').length;
          const typeLabel = entry.contest_type === 'pickem' ? "PICK'EM" : entry.contest_type.toUpperCase();
          const typeColor = entry.contest_type === 'survivor' ? '#6ee7b7' : entry.contest_type === 'pickem' ? '#93c5fd' : '#c4b5fd';
          const st = RESULT_STYLE[entry.status] ?? RESULT_STYLE.pending;

          // Group picks by week for survivor row preview
          const picksByWeek = entryPicks.reduce<Record<string, ContestPick>>((acc, p) => { acc[p.week] = p; return acc; }, {});

          return (
            <div key={entry.id} className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
              {/* Entry Header — always visible */}
              <button onClick={() => toggleEntry(entry.id)}
                className="w-full px-5 py-3 flex items-center justify-between text-left hover:bg-slate-700/20 transition-colors">
                <div className="flex items-center gap-3 min-w-0">
                  <span className="text-[10px] font-bold px-2 py-1 rounded uppercase tracking-wider flex-shrink-0"
                    style={{ background: typeColor + '22', color: typeColor }}>{typeLabel}</span>
                  <div className="min-w-0">
                    <div className="text-white font-bold text-sm truncate">{entry.contest_name}</div>
                    <div className="text-[10px] text-slate-500">{entry.entry_name}{entry.entry_fee > 0 ? ` · $${entry.entry_fee}` : ''}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  {/* Survivor: show team chips inline when collapsed */}
                  {entry.contest_type === 'survivor' && !isExpanded && entryPicks.length > 0 && (
                    <div className="hidden md:flex items-center gap-1">
                      {Array.from({ length: 18 }, (_, i) => String(i + 1)).map(wk => {
                        const pick = picksByWeek[wk];
                        if (!pick) return <div key={wk} className="w-8 h-8 rounded bg-slate-800/60 border border-slate-700/40 flex items-center justify-center text-[8px] text-slate-600">{wk}</div>;
                        return <TeamChip key={wk} abbr={pick.team} size="sm" result={pick.result} />;
                      }).slice(0, 8)}
                      {entryPicks.length > 8 && <span className="text-[10px] text-slate-500">+{entryPicks.length - 8}</span>}
                    </div>
                  )}

                  {entryPicks.length > 0 && <span className="text-xs font-bold text-slate-300">{wins}W-{losses}L</span>}
                  <span className={`text-[10px] font-bold px-2 py-1 rounded ${st.bg} ${st.text}`}>{entry.status.toUpperCase()}</span>
                  <span className="text-slate-600 text-sm">{isExpanded ? '▲' : '▼'}</span>
                </div>
              </button>

              {/* Expanded */}
              {isExpanded && (
                <div className="border-t border-slate-700">

                  {/* Survivor: Full grid matching SurvivorPathBuilder style */}
                  {entry.contest_type === 'survivor' && (() => {
                    const weekNums = Object.keys(survivorWeeks).map(Number).sort((a, b) => a - b);
                    const teamWeekMap: Record<string, Record<number, { wp: number; opp: string; home: boolean; label: string }>> = {};
                    for (const [wkStr, games] of Object.entries(survivorWeeks)) {
                      const wk = Number(wkStr);
                      for (const g of games) {
                        if (!teamWeekMap[g.home]) teamWeekMap[g.home] = {};
                        if (!teamWeekMap[g.away]) teamWeekMap[g.away] = {};
                        teamWeekMap[g.home][wk] = { wp: g.home_wp, opp: g.away, home: true, label: g.home_label };
                        teamWeekMap[g.away][wk] = { wp: g.away_wp, opp: g.home, home: false, label: g.away_label };
                      }
                    }
                    const allTeams = Object.keys(teamWeekMap).sort();
                    const pickedTeamSet = new Set(used);

                    // Sort teams by WP in selected week column (click header to sort)
                    const sortedTeams = gridSort
                      ? [...allTeams].sort((a, b) => {
                          const aWp = teamWeekMap[a]?.[gridSort.col]?.wp ?? -1;
                          const bWp = teamWeekMap[b]?.[gridSort.col]?.wp ?? -1;
                          return gridSort.dir === 'desc' ? bWp - aWp : aWp - bWp;
                        })
                      : allTeams;

                    const cycleSort = (col: number) => {
                      if (!gridSort || gridSort.col !== col) setGridSort({ col, dir: 'desc' });
                      else if (gridSort.dir === 'desc') setGridSort({ col, dir: 'asc' });
                      else setGridSort(null);
                    };

                    if (weekNums.length === 0) return (
                      <div className="px-5 py-8 text-center text-[0.72rem]" style={{ color: 'oklch(70.8% 0 0)' }}>Loading survivor grid data...</div>
                    );

                    // CSS vars matching Survivor page dark theme
                    const cssVars: Record<string, string> = {
                      '--c-bg': 'oklch(22.5% 0 0)', '--c-panel': 'oklch(24% 0 0)',
                      '--c-border': 'oklch(100% 0 0 / .15)', '--c-fg': 'oklch(98.5% 0 0)',
                      '--c-muted': 'oklch(70.8% 0 0)', '--c-rowsel': 'oklch(100% 0 0 / .06)',
                    };

                    return (
                      <div className="p-3" style={cssVars as React.CSSProperties}>

                        {/* Picker ABOVE grid */}
                        {entry.status === 'alive' && (
                          <div className="mb-3 rounded-lg p-3" style={{ background: 'oklch(22.5% 0 0)', border: '1px solid oklch(100% 0 0 / .15)' }}>
                            <div className="text-[0.6rem] font-bold tracking-[0.06em] mb-2" style={{ color: 'oklch(70.8% 0 0)' }}>
                              ADD PICK — or click any cell in the grid below
                            </div>
                            <div className="flex flex-wrap gap-2 items-end">
                              <div>
                                <label className="text-[0.5rem] uppercase block mb-1" style={{ color: 'oklch(50% 0 0)' }}>Week</label>
                                <select value={pickWeek} onChange={e => setPickWeek(e.target.value)}
                                  className="rounded px-2 py-1.5 text-[0.68rem] font-bold w-20"
                                  style={{ background: 'oklch(24% 0 0)', border: '1px solid oklch(100% 0 0 / .15)', color: 'oklch(98.5% 0 0)' }}>
                                  {weekNums.map(w => <option key={w} value={String(w)}>Wk {w}</option>)}
                                </select>
                              </div>
                              <div className="min-w-[180px]">
                                <label className="text-[0.5rem] uppercase block mb-1" style={{ color: 'oklch(50% 0 0)' }}>Team</label>
                                <select value={pickTeam} onChange={e => setPickTeam(e.target.value)}
                                  className="rounded px-2 py-1.5 text-[0.68rem] font-bold w-full"
                                  style={{ background: 'oklch(24% 0 0)', border: '1px solid oklch(100% 0 0 / .15)', color: 'oklch(98.5% 0 0)' }}>
                                  <option value="">Select team...</option>
                                  {NFL_TEAMS.filter(t => !pickedTeamSet.has(t.abbr)).map(t => (
                                    <option key={t.abbr} value={t.abbr}>{t.city} {t.name} ({t.abbr})</option>
                                  ))}
                                </select>
                              </div>
                              <button onClick={() => addPick(entry.id)} disabled={!pickTeam || submitting}
                                className="px-4 py-1.5 rounded text-[0.68rem] font-bold disabled:opacity-40"
                                style={{ background: withAlpha(BLUE, 0.15), border: `1px solid ${BLUE}`, color: BLUE, cursor: !pickTeam ? 'default' : 'pointer' }}>
                                {submitting ? '...' : 'Add Pick'}
                              </button>
                              {pickTeam && (
                                <div className="flex items-center gap-1.5 ml-2">
                                  <img src={logo(pickTeam)} alt={pickTeam} className="w-6 h-6" onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                                  <span className="text-[0.72rem] font-bold" style={{ color: 'oklch(98.5% 0 0)' }}>{pickTeam}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Legend + info */}
                        <div className="flex items-center justify-between mb-2 px-1">
                          <div className="text-[0.6rem] font-bold tracking-[0.06em]" style={{ color: 'oklch(70.8% 0 0)' }}>
                            {entry.contest_name} — {used.length} used · {allTeams.length - used.length} available
                          </div>
                          <div className="flex gap-3 text-[0.55rem]" style={{ color: 'oklch(50% 0 0)' }}>
                            {[['73%+', EMERALD, 'GREAT'], ['58–72%', BLUE, 'GOOD'], ['45–57%', YELLOW, 'LEAN'], ['<45%', RED, 'TOUGH']].map(([range, color]) => (
                              <span key={String(range)} className="flex items-center gap-1">
                                <span className="w-1.5 h-1.5 rounded-sm inline-block" style={{ background: color as string }} />
                                {range}
                              </span>
                            ))}
                            <span className="ml-1">· Click header to sort</span>
                          </div>
                        </div>

                        {/* Grid */}
                        <div style={{ background: 'oklch(24% 0 0)', border: '1px solid oklch(100% 0 0 / .15)', borderRadius: 10, overflow: 'hidden' }}>
                          <div className="overflow-x-auto overflow-y-auto max-h-[70vh]">
                            <table className="border-collapse text-[0.68rem]" style={{ minWidth: 'max-content' }}>
                              <thead>
                                <tr>
                                  <th className="sticky left-0 top-0 z-[4] py-2 px-3 text-left text-[0.58rem] font-bold tracking-[0.06em] min-w-[90px]"
                                    style={{ background: 'oklch(24% 0 0)', borderRight: '1px solid oklch(100% 0 0 / .15)', borderBottom: '1px solid oklch(100% 0 0 / .15)', color: 'oklch(70.8% 0 0)' }}>
                                    TEAM
                                  </th>
                                  {weekNums.map(wk => {
                                    const colPick = picksByWeek[String(wk)];
                                    const isSorted = gridSort?.col === wk;
                                    const arrow = isSorted ? (gridSort!.dir === 'desc' ? ' ▼' : ' ▲') : '';
                                    return (
                                      <th key={wk} onClick={() => cycleSort(wk)}
                                        className="sticky top-0 z-[3] py-1.5 px-1 text-center text-[0.58rem] font-bold tracking-[0.04em] min-w-[58px] cursor-pointer select-none"
                                        style={{
                                          background: colPick ? withAlpha(BLUE, 0.13) : isSorted ? 'oklch(100% 0 0 / .06)' : 'oklch(24% 0 0)',
                                          borderBottom: `2px solid ${colPick ? BLUE : isSorted ? 'oklch(98.5% 0 0)' : 'oklch(100% 0 0 / .15)'}`,
                                          borderRight: '1px solid oklch(100% 0 0 / .15)',
                                          color: colPick ? BLUE : isSorted ? 'oklch(98.5% 0 0)' : 'oklch(70.8% 0 0)',
                                        }}>
                                        <div>WK{wk}{arrow}</div>
                                        {colPick && <img src={logo(colPick.team)} alt={colPick.team} className="w-[18px] h-[18px] mx-auto mt-0.5 block" onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />}
                                      </th>
                                    );
                                  })}
                                </tr>
                              </thead>
                              <tbody>
                                {sortedTeams.map((team, rowIdx) => {
                                  const isUsed = pickedTeamSet.has(team);
                                  const pickedWk = entryPicks.find(p => p.team === team);
                                  return (
                                    <tr key={team} className={isUsed ? 'opacity-50' : ''}
                                      style={{ background: rowIdx % 2 === 0 ? 'transparent' : 'oklch(100% 0 0 / .04)' }}>
                                      <td className="sticky left-0 z-[2] py-1 px-[10px] whitespace-nowrap"
                                        style={{ borderRight: '1px solid oklch(100% 0 0 / .15)', background: rowIdx % 2 === 0 ? 'oklch(24% 0 0)' : 'oklch(25% 0 0)' }}>
                                        <div className="flex items-center gap-[7px]">
                                          <img src={logo(team)} alt={team} className="w-[22px] h-[22px] shrink-0"
                                            style={{ filter: isUsed ? 'grayscale(80%)' : 'none' }}
                                            onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                                          <div>
                                            <div className="font-bold text-[0.72rem]" style={{ color: isUsed ? 'oklch(70.8% 0 0)' : 'oklch(98.5% 0 0)' }}>{team}</div>
                                            {isUsed && pickedWk && <div className="text-[0.5rem] font-bold" style={{ color: BLUE }}>WK{pickedWk.week} ✓</div>}
                                          </div>
                                        </div>
                                      </td>
                                      {weekNums.map(wk => {
                                        const game = teamWeekMap[team]?.[wk];
                                        const isThisTeamPicked = picksByWeek[String(wk)]?.team === team;
                                        const weekAlreadyPicked = !!picksByWeek[String(wk)];
                                        const isBlocked = isUsed && !isThisTeamPicked;

                                        if (!game) return (
                                          <td key={wk} className="p-0 text-center" style={{ borderRight: '1px solid oklch(100% 0 0 / .15)' }}>
                                            <div className="py-[10px] px-1 text-[0.5rem]" style={{ color: 'oklch(50% 0 0)' }}>—</div>
                                          </td>
                                        );

                                        const wpCol = wpColor(game.wp);
                                        const canClick = !isBlocked && !weekAlreadyPicked && entry.status === 'alive';

                                        return (
                                          <td key={wk} className="p-0 text-center"
                                            style={{
                                              borderRight: '1px solid oklch(100% 0 0 / .15)',
                                              background: isThisTeamPicked ? withAlpha(BLUE, 0.14) : 'transparent',
                                              borderBottom: isThisTeamPicked ? `2px solid ${BLUE}` : '2px solid transparent',
                                            }}>
                                            <button
                                              onClick={() => {
                                                if (!canClick && !isThisTeamPicked) return;
                                                if (isThisTeamPicked) return;
                                                setPickWeek(String(wk));
                                                setPickTeam(team);
                                                addPick(entry.id);
                                              }}
                                              disabled={isBlocked}
                                              title={`${team} ${game.home ? 'vs' : '@'} ${game.opp} · ${Math.round(game.wp * 100)}% · ${game.label}`}
                                              className="w-full h-full py-1.5 px-1 flex flex-col items-center gap-0.5"
                                              style={{ background: 'transparent', border: 'none', cursor: isBlocked || weekAlreadyPicked ? 'default' : 'pointer' }}>
                                              {isThisTeamPicked && <div className="text-[0.45rem] font-extrabold leading-none" style={{ color: BLUE }}>✓</div>}
                                              <div className="text-[0.65rem] font-bold" style={{ color: isThisTeamPicked ? BLUE : wpCol }}>
                                                {Math.round(game.wp * 100)}%
                                              </div>
                                              <div className="text-[0.45rem]" style={{ color: 'oklch(50% 0 0)' }}>
                                                {game.home ? 'vs' : '@'}{game.opp}
                                              </div>
                                            </button>
                                          </td>
                                        );
                                      })}
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </div>
                    );
                  })()}

                  {/* Pickem / Confidence: existing picks table */}
                  {entry.contest_type !== 'survivor' && entryPicks.length > 0 && (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-[10px] text-slate-500 uppercase tracking-wider border-b border-slate-700">
                            <th className="px-5 py-2 text-left">Week</th>
                            <th className="px-5 py-2 text-left">Pick</th>
                            <th className="px-5 py-2 text-left">Opponent</th>
                            {entry.contest_type === 'confidence' && <th className="px-5 py-2 text-center">Pts</th>}
                            <th className="px-5 py-2 text-center">Spread</th>
                            <th className="px-5 py-2 text-center">Score</th>
                            <th className="px-5 py-2 text-center">Result</th>
                          </tr>
                        </thead>
                        <tbody>
                          {entryPicks.map(p => {
                            const ps = RESULT_STYLE[p.result];
                            return (
                              <tr key={p.id} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                                <td className="px-5 py-2 font-bold text-slate-300 text-xs">Wk {p.week}</td>
                                <td className="px-5 py-2"><TeamChip abbr={p.team} size="md" result={p.result} /></td>
                                <td className="px-5 py-2">{p.opponent ? <TeamChip abbr={p.opponent} size="sm" /> : <span className="text-slate-600">—</span>}</td>
                                {entry.contest_type === 'confidence' && (
                                  <td className="px-5 py-2 text-center font-black text-purple-400 text-lg">{p.confidence_rank ?? '—'}</td>
                                )}
                                <td className="px-5 py-2 text-center text-slate-400 text-xs">{p.spread != null ? (p.spread > 0 ? `+${p.spread}` : p.spread) : '—'}</td>
                                <td className="px-5 py-2 text-center text-slate-400 text-xs">{p.game_score ?? '—'}</td>
                                <td className="px-5 py-2 text-center">
                                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${ps.bg} ${ps.text}`}>{p.result.toUpperCase()}</span>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* Matchup Picker for Pick'em / Confidence */}
                  {entry.contest_type !== 'survivor' && entry.status === 'alive' && (() => {
                    const maxPicks = entry.contest_name.includes('Lucky 7') ? 7 : entry.contest_type === 'confidence' ? 5 : 16;
                    const isConfidence = entry.contest_type === 'confidence';
                    const stagedCount = Object.keys(stagedPicks).length;
                    const alreadyPickedTeams = new Set(entryPicks.filter(p => p.week === pickWeek).map(p => p.team));
                    const usedRanks = new Set(Object.values(stagedPicks).map(p => p.rank).filter(Boolean));
                    const availRanks = Array.from({ length: maxPicks }, (_, i) => maxPicks - i).filter(r => !usedRanks.has(r));

                    return (
                      <div className="px-4 py-4 bg-slate-900/40 border-t border-slate-700/50">
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                              Make Picks — Week {pickWeek}
                              <span className="ml-2 text-slate-600">
                                {stagedCount}/{maxPicks} selected
                                {isConfidence && ` · ${availRanks.length} pts remaining`}
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <select value={pickWeek} onChange={e => { setPickWeek(e.target.value); setStagedPicks({}); }}
                              className="bg-slate-800 border border-slate-600 rounded px-2 py-1.5 text-white text-xs focus:border-blue-500 focus:outline-none">
                              {Array.from({ length: 18 }, (_, i) => <option key={i + 1} value={String(i + 1)}>Week {i + 1}</option>)}
                            </select>
                            {stagedCount > 0 && (
                              <button onClick={() => submitStagedPicks(entry.id)} disabled={submitting || (isConfidence && stagedCount !== maxPicks)}
                                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded transition-colors disabled:opacity-40">
                                {submitting ? 'Saving...' : `Submit ${stagedCount} Pick${stagedCount !== 1 ? 's' : ''}`}
                              </button>
                            )}
                          </div>
                        </div>

                        {/* Game cards grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {weekMatchups.map(game => {
                            const gameKey = `${game.awayAbbr}@${game.homeAbbr}`;
                            const staged = stagedPicks[gameKey];
                            const alreadyPicked = alreadyPickedTeams.has(game.homeAbbr) || alreadyPickedTeams.has(game.awayAbbr);
                            const awaySelected = staged?.team === game.awayAbbr;
                            const homeSelected = staged?.team === game.homeAbbr;
                            const isSelected = awaySelected || homeSelected;
                            const atMax = stagedCount >= maxPicks && !isSelected;

                            const selectTeam = (team: string, opp: string) => {
                              if (alreadyPicked) return;
                              const newStaged = { ...stagedPicks };
                              if (staged?.team === team) {
                                delete newStaged[gameKey]; // deselect
                              } else if (atMax && !isSelected) {
                                return; // at max picks
                              } else {
                                newStaged[gameKey] = { team, opp, spread: game.spread, rank: null };
                              }
                              setStagedPicks(newStaged);
                            };

                            const setRank = (rank: number) => {
                              if (!staged) return;
                              setStagedPicks(prev => ({ ...prev, [gameKey]: { ...prev[gameKey], rank } }));
                            };

                            return (
                              <div key={gameKey} className={`rounded-lg border p-3 transition-all ${
                                alreadyPicked ? 'border-slate-700/30 opacity-40' :
                                isSelected ? 'border-blue-500/50 bg-blue-900/10' :
                                'border-slate-700/50 bg-slate-800/40 hover:border-slate-600'
                              }`}>
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-[9px] text-slate-600">{game.time} CT</span>
                                  {game.spread != null && (
                                    <span className="text-[9px] text-slate-500">
                                      {game.spread < 0 ? `${game.homeAbbr} ${game.spread}` : `${game.awayAbbr} -${game.spread}`}
                                      {game.total && ` · o/u ${game.total}`}
                                    </span>
                                  )}
                                  {alreadyPicked && <span className="text-[9px] text-emerald-500 font-bold">PICKED</span>}
                                </div>

                                <div className="flex items-center gap-2">
                                  {/* Away team button */}
                                  <button onClick={() => selectTeam(game.awayAbbr, game.homeAbbr)}
                                    disabled={alreadyPicked || (atMax && !awaySelected)}
                                    className={`flex-1 flex items-center gap-2 rounded-lg py-2 px-3 transition-all ${
                                      awaySelected ? 'bg-blue-600/20 border-2 border-blue-500 shadow-lg' :
                                      'bg-slate-800/60 border border-slate-700 hover:border-slate-500'
                                    } ${alreadyPicked || (atMax && !awaySelected) ? 'cursor-default' : 'cursor-pointer'}`}>
                                    <img src={logo(game.awayAbbr)} alt={game.awayAbbr} className="w-7 h-7 object-contain"
                                      onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                                    <div className="text-left min-w-0">
                                      <div className={`text-xs font-bold truncate ${awaySelected ? 'text-blue-300' : 'text-white'}`}>
                                        {game.away.split(' ').pop()}
                                      </div>
                                      <div className="text-[9px] text-slate-500">{game.awayAbbr}</div>
                                    </div>
                                    {awaySelected && <span className="text-blue-400 font-black text-sm ml-auto">✓</span>}
                                  </button>

                                  <span className="text-[10px] text-slate-600 font-bold">@</span>

                                  {/* Home team button */}
                                  <button onClick={() => selectTeam(game.homeAbbr, game.awayAbbr)}
                                    disabled={alreadyPicked || (atMax && !homeSelected)}
                                    className={`flex-1 flex items-center gap-2 rounded-lg py-2 px-3 transition-all ${
                                      homeSelected ? 'bg-emerald-600/20 border-2 border-emerald-500 shadow-lg' :
                                      'bg-slate-800/60 border border-slate-700 hover:border-slate-500'
                                    } ${alreadyPicked || (atMax && !homeSelected) ? 'cursor-default' : 'cursor-pointer'}`}>
                                    <img src={logo(game.homeAbbr)} alt={game.homeAbbr} className="w-7 h-7 object-contain"
                                      onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                                    <div className="text-left min-w-0">
                                      <div className={`text-xs font-bold truncate ${homeSelected ? 'text-emerald-300' : 'text-white'}`}>
                                        {game.home.split(' ').pop()}
                                      </div>
                                      <div className="text-[9px] text-slate-500">{game.homeAbbr}</div>
                                    </div>
                                    {homeSelected && <span className="text-emerald-400 font-black text-sm ml-auto">✓</span>}
                                  </button>
                                </div>

                                {/* Spread adjuster (pickem/confidence only) */}
                                {isSelected && entry.contest_type !== 'survivor' && (
                                  <div className="mt-2 flex items-center gap-2">
                                    <span className="text-[9px] text-slate-500 font-bold uppercase">Line:</span>
                                    <button type="button"
                                      onClick={() => setStagedPicks(prev => ({ ...prev, [gameKey]: { ...prev[gameKey], spread: (prev[gameKey].spread ?? 0) - 0.5 } }))}
                                      className="w-6 h-6 bg-slate-700 hover:bg-slate-600 text-white rounded text-xs font-bold border border-slate-600">−</button>
                                    <input type="number" step="0.5"
                                      value={staged?.spread ?? ''}
                                      onChange={e => setStagedPicks(prev => ({ ...prev, [gameKey]: { ...prev[gameKey], spread: e.target.value ? parseFloat(e.target.value) : null } }))}
                                      className="w-16 bg-slate-800 border border-yellow-500/50 rounded px-2 py-1 text-white text-xs font-bold text-center focus:border-yellow-500 focus:outline-none"
                                    />
                                    <button type="button"
                                      onClick={() => setStagedPicks(prev => ({ ...prev, [gameKey]: { ...prev[gameKey], spread: (prev[gameKey].spread ?? 0) + 0.5 } }))}
                                      className="w-6 h-6 bg-slate-700 hover:bg-slate-600 text-white rounded text-xs font-bold border border-slate-600">+</button>
                                    <span className="text-[8px] text-slate-600 ml-1">
                                      {game.spread != null ? `Market: ${game.spread > 0 ? '+' : ''}${game.spread}` : ''}
                                    </span>
                                  </div>
                                )}

                                {/* Confidence rank selector */}
                                {isConfidence && isSelected && (
                                  <div className="mt-2 flex items-center gap-1.5">
                                    <span className="text-[9px] text-slate-500 font-bold uppercase mr-1">Points:</span>
                                    {Array.from({ length: maxPicks }, (_, i) => maxPicks - i).map(r => {
                                      const taken = usedRanks.has(r) && staged?.rank !== r;
                                      return (
                                        <button key={r} onClick={() => setRank(r)} disabled={taken}
                                          className={`w-7 h-7 rounded-md text-xs font-black transition-all ${
                                            staged?.rank === r ? 'bg-purple-600 text-white border-2 border-purple-400 scale-110' :
                                            taken ? 'bg-slate-800 text-slate-700 border border-slate-700 cursor-default' :
                                            'bg-slate-800 text-slate-400 border border-slate-600 hover:border-purple-500 cursor-pointer'
                                          }`}>
                                          {r}
                                        </button>
                                      );
                                    })}
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>

                        {weekMatchups.length === 0 && (
                          <div className="text-center py-8 text-slate-500 text-sm">No NFL games found for this week.</div>
                        )}
                      </div>
                    );
                  })()}
                </div>
              )}
            </div>
          );
        })}
      </div>}

      {/* New Entry Modal */}
      {showNewEntry && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowNewEntry(false)}>
          <div className="bg-slate-800 border border-slate-600 rounded-xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-white mb-4">New Contest Entry</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-slate-400 font-bold uppercase block mb-1">Contest Name</label>
                <input type="text" value={newName} onChange={e => setNewName(e.target.value)} placeholder="e.g. Circa Survivor 2026"
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none" />
              </div>
              <div>
                <label className="text-xs text-slate-400 font-bold uppercase block mb-1">Type</label>
                <select value={newType} onChange={e => setNewType(e.target.value as ContestType)}
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none">
                  <option value="survivor">Survivor</option>
                  <option value="pickem">Pick'em</option>
                  <option value="confidence">Confidence Pool</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-slate-400 font-bold uppercase block mb-1">Entry Name</label>
                <input type="text" value={newEntryName} onChange={e => setNewEntryName(e.target.value)} placeholder="e.g. Will - Entry 1"
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none" />
              </div>
              <div>
                <label className="text-xs text-slate-400 font-bold uppercase block mb-1">Entry Fee ($)</label>
                <input type="number" value={newFee} onChange={e => setNewFee(e.target.value)} placeholder="0"
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none" />
              </div>
              <div className="flex gap-2 pt-2">
                <button onClick={addEntry} disabled={!newName || !newEntryName || submitting}
                  className="flex-1 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm rounded-lg disabled:opacity-50">
                  {submitting ? 'Creating...' : 'Create Entry'}</button>
                <button onClick={() => setShowNewEntry(false)}
                  className="px-4 py-2.5 bg-slate-700 text-slate-300 font-bold text-sm rounded-lg hover:bg-slate-600">Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
