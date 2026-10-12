import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';
import { MetaTags } from '../components/MetaTags';

interface CfbPlay {
  type: string;
  side: string;
  team: string;
  tier: number;
  edge_pts: number;
  sp_spread?: number;
  market_spread?: number;
  signal: string;
  home_sp?: number;
  away_sp?: number;
  home_rank?: number;
  away_rank?: number;
  home_tier?: string;
  away_tier?: string;
  sp_total?: number;
  market_total?: number;
}

interface CfbGame {
  home_team: string;
  away_team: string;
  commence_time: string;
  spread: number | null;
  total: number | null;
  home_ml: number | null;
  away_ml: number | null;
}

interface CfbRating {
  team?: string;
  sp_rating?: number;
  sp_offense?: number;
  sp_defense?: number;
  sp_rank?: number;
  tier?: string;
  conference?: string;
  ap_rank?: number;
  coaches_rank?: number;
  fpi?: number;
}

interface CfbResult {
  game: CfbGame;
  plays: CfbPlay[];
  has_plays: boolean;
  home_rating: CfbRating;
  away_rating: CfbRating;
}

interface CfbTodayData {
  date: string;
  games_scanned: number;
  qualifying_games: number;
  total_plays: number;
  credits_remaining: string;
  results: CfbResult[];
}

type Tab = 'edges' | 'ratings' | 'all';

const TIER_COLORS: Record<string, string> = {
  ELITE: 'text-yellow-400',
  CONTENDER: 'text-blue-400',
  AVERAGE: 'text-slate-400',
  BELOW: 'text-orange-400',
  WEAK: 'text-red-400',
};

const TIER_BG: Record<string, string> = {
  ELITE: 'bg-yellow-500/10 border-yellow-500/30',
  CONTENDER: 'bg-blue-500/10 border-blue-500/30',
  AVERAGE: 'bg-slate-500/10 border-slate-500/30',
  BELOW: 'bg-orange-500/10 border-orange-500/30',
  WEAK: 'bg-red-500/10 border-red-500/30',
};

function fmtSpread(n: number | null): string {
  if (n == null) return '—';
  return n > 0 ? `+${n}` : String(n);
}

function fmtOdds(n: number | null): string {
  if (n == null) return '—';
  return n > 0 ? `+${n}` : String(n);
}

function tierBadge(tier: string | undefined, rank: number | undefined) {
  if (!tier) return null;
  return (
    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${TIER_BG[tier] ?? ''} ${TIER_COLORS[tier] ?? 'text-slate-400'}`}>
      {rank ? `#${rank} ` : ''}{tier}
    </span>
  );
}

export function CFBTrends() {
  const [data, setData] = useState<CfbTodayData | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>('edges');
  const [confFilter, setConfFilter] = useState<string>('all');

  useEffect(() => {
    fetch(getApiUrl('f5/today-cfb'))
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const results = data?.results ?? [];
  const edgeGames = results.filter(r => r.has_plays);
  const allGames = tab === 'edges' ? edgeGames : results;

  // Get unique conferences
  const conferences = Array.from(new Set(
    results.flatMap(r => [r.home_rating?.conference, r.away_rating?.conference]).filter(Boolean)
  )).sort() as string[];

  const filtered = confFilter === 'all'
    ? allGames
    : allGames.filter(r =>
        r.home_rating?.conference === confFilter || r.away_rating?.conference === confFilter
      );

  return (
    <div className="analytics-page p-4">
      <MetaTags title="CFB Trends" description="College football SP+ edge detection, power ratings comparison, and betting trends for every FBS matchup." />

      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-100 mb-1" style={{ letterSpacing: '-0.02em' }}>
            CFB EDGE FINDER
          </h1>
          <p className="text-slate-400 text-sm">
            SP+ power ratings vs market spreads · {data?.games_scanned ?? 0} games scanned · {data?.qualifying_games ?? 0} with edges
          </p>
        </div>
        {data && (
          <div className="text-right">
            <div className="text-xs text-slate-500">{data.date}</div>
            <div className="text-xs text-slate-600">{data.total_plays} total plays</div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        {([
          ['edges', `SP+ EDGES (${edgeGames.length})`],
          ['all', `ALL GAMES (${results.length})`],
        ] as [Tab, string][]).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-3 py-1.5 rounded text-xs font-semibold transition-all ${
              tab === key
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
            }`}
          >
            {label}
          </button>
        ))}

        {/* Conference filter */}
        <select
          value={confFilter}
          onChange={e => setConfFilter(e.target.value)}
          className="ml-auto px-2 py-1.5 rounded text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700"
        >
          <option value="all">All Conferences</option>
          {conferences.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-slate-400">Loading CFB data...</div>
      ) : (
        <div className="space-y-3">
          {filtered.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 gap-3">
              <span className="text-4xl">🏈</span>
              <p className="text-slate-400">No {tab === 'edges' ? 'SP+ edges' : 'games'} found{confFilter !== 'all' ? ` for ${confFilter}` : ''}.</p>
            </div>
          )}

          {filtered.map((r, i) => {
            const g = r.game;
            const hr = r.home_rating;
            const ar = r.away_rating;
            const gameTime = new Date(g.commence_time).toLocaleDateString('en-US', {
              weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
              timeZone: 'America/Chicago',
            });

            return (
              <div key={i} className="bg-slate-800/50 border border-slate-700/60 rounded-xl overflow-hidden">
                {/* Game header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/40">
                  <div className="flex items-center gap-3">
                    <div className="text-sm font-bold text-white">
                      {g.away_team.split(' ').slice(0, -1).join(' ')}
                      <span className="text-slate-500 mx-2">@</span>
                      {g.home_team.split(' ').slice(0, -1).join(' ')}
                    </div>
                    <div className="flex gap-1.5">
                      {tierBadge(ar?.tier, ar?.sp_rank)}
                      <span className="text-slate-600 text-xs">vs</span>
                      {tierBadge(hr?.tier, hr?.sp_rank)}
                    </div>
                  </div>
                  <div className="text-xs text-slate-500">{gameTime}</div>
                </div>

                {/* SP+ comparison + market odds */}
                <div className="px-4 py-3 flex flex-wrap gap-4 items-center">
                  {/* SP+ ratings */}
                  {ar?.sp_rating != null && hr?.sp_rating != null && (
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-slate-500 font-semibold">SP+:</span>
                      <span className="text-blue-300 font-bold">{ar.sp_rating}</span>
                      <span className="text-slate-600">vs</span>
                      <span className="text-emerald-300 font-bold">{hr.sp_rating}</span>
                      <span className="text-slate-600">(gap: {Math.abs(ar.sp_rating - hr.sp_rating).toFixed(1)})</span>
                    </div>
                  )}

                  {/* Market line */}
                  <div className="flex items-center gap-3 text-xs">
                    {g.spread != null && (
                      <span className="bg-slate-700/50 px-2 py-1 rounded text-slate-300">
                        Spread: <span className="font-bold text-white">{fmtSpread(g.spread)}</span>
                      </span>
                    )}
                    {g.total != null && (
                      <span className="bg-slate-700/50 px-2 py-1 rounded text-slate-300">
                        Total: <span className="font-bold text-white">{g.total}</span>
                      </span>
                    )}
                    {g.home_ml != null && (
                      <span className="bg-slate-700/50 px-2 py-1 rounded text-slate-300">
                        ML: <span className="text-blue-300">{fmtOdds(g.away_ml)}</span>
                        <span className="text-slate-600 mx-1">/</span>
                        <span className="text-emerald-300">{fmtOdds(g.home_ml)}</span>
                      </span>
                    )}
                  </div>

                  {/* Conference badges */}
                  <div className="flex gap-2 ml-auto">
                    {ar?.conference && <span className="text-[10px] text-slate-500 bg-slate-700/30 px-1.5 py-0.5 rounded">{ar.conference}</span>}
                    {hr?.conference && hr.conference !== ar?.conference && (
                      <span className="text-[10px] text-slate-500 bg-slate-700/30 px-1.5 py-0.5 rounded">{hr.conference}</span>
                    )}
                  </div>
                </div>

                {/* Edge plays */}
                {r.plays.length > 0 && (
                  <div className="border-t border-slate-700/40 px-4 py-2.5 space-y-1.5">
                    {r.plays.map((play, pi) => (
                      <div key={pi} className="flex items-center gap-3">
                        <span className={`text-[10px] font-black px-2 py-0.5 rounded-full ${
                          play.tier === 1 ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                          play.tier === 2 ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                          'bg-slate-500/20 text-slate-400 border border-slate-500/30'
                        }`}>
                          T{play.tier}
                        </span>
                        <span className="text-xs font-bold text-white">{play.type}</span>
                        <span className={`text-xs font-bold ${play.edge_pts >= 7 ? 'text-yellow-400' : play.edge_pts >= 5 ? 'text-emerald-400' : 'text-blue-400'}`}>
                          {play.edge_pts.toFixed(1)}pt edge
                        </span>
                        <span className="text-xs text-slate-500 flex-1 truncate">{play.signal}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-4 text-xs text-slate-600 text-center">
        SP+ ratings from CFBD API · Odds from The Odds API · Edge = SP+ projected spread vs market spread · Min 3pt edge
      </div>
    </div>
  );
}

export default CFBTrends;
