import { useState, useEffect, useCallback, useRef } from 'react';
import { getApiUrl } from '../config';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface NewsItem {
  id: number;
  source: string;
  headline: string;
  summary: string | null;
  url: string;
  sport: string;
  teams: string[];
  players: string[];
  injury_status: string | null;
  news_type: string;
  published_at: string | null;
  fetched_at: string;
  haiku_classification: Record<string, unknown> | null;
  sonnet_analysis: Record<string, unknown> | null;
  analyzed_at: string | null;
}

interface FeedStats {
  total_items: number;
  analyzed: number;
  injuries: number;
  bet_now_count: number;
  last_fetch: string | null;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const SPORT_COLORS: Record<string, string> = {
  mlb:  'bg-blue-900 text-blue-200 border-blue-700',
  nba:  'bg-orange-900 text-orange-200 border-orange-700',
  nfl:  'bg-green-900 text-green-200 border-green-700',
  nhl:  'bg-sky-900 text-sky-200 border-sky-700',
  wnba: 'bg-purple-900 text-purple-200 border-purple-700',
  other:'bg-gray-700 text-gray-300 border-gray-600',
};

const SEVERITY_BADGE: Record<string, string> = {
  out:         'bg-red-900 text-red-200 border border-red-700',
  limited:     'bg-yellow-900 text-yellow-200 border border-yellow-700',
  doubtful:    'bg-orange-900 text-orange-200 border border-orange-700',
  probable:    'bg-green-900 text-green-200 border border-green-700',
  day_to_day:  'bg-yellow-800 text-yellow-200 border border-yellow-700',
  none:        'bg-gray-700 text-gray-300',
};

const ACTION_BADGE: Record<string, string> = {
  'BET NOW':        'bg-green-500 text-white font-bold',
  'MONITOR':        'bg-yellow-500 text-black font-bold',
  'AVOID':          'bg-red-500 text-white font-bold',
  'WAIT FOR LINE':  'bg-blue-500 text-white font-bold',
};

const CONFIDENCE_DOT: Record<string, string> = {
  high:   'bg-green-400',
  medium: 'bg-yellow-400',
  low:    'bg-gray-400',
};

function timeAgo(iso: string | null): string {
  if (!iso) return '';
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60)  return `${Math.floor(diff)}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function sportLabel(s: string) {
  return s.toUpperCase();
}

// ---------------------------------------------------------------------------
// Analysis card
// ---------------------------------------------------------------------------

function AnalysisCard({ item, onAnalyze }: { item: NewsItem; onAnalyze: (id: number) => void }) {
  const [expanded, setExpanded] = useState(false);
  const cls = item.haiku_classification as Record<string, unknown> | null;
  const analysis = item.sonnet_analysis as Record<string, unknown> | null;
  const severity = (cls?.severity as string) || (item.injury_status ? 'day_to_day' : 'none');
  const action = analysis?.recommended_action as string | undefined;
  const confidence = analysis?.confidence as string | undefined;
  const isInjury = item.news_type === 'injury';

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start gap-3">
          {/* Sport badge */}
          <span className={`shrink-0 text-[10px] font-bold px-1.5 py-0.5 rounded border ${SPORT_COLORS[item.sport] || SPORT_COLORS.other}`}>
            {sportLabel(item.sport)}
          </span>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              {isInjury && item.injury_status && (
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${SEVERITY_BADGE[severity] || SEVERITY_BADGE.none}`}>
                  {item.injury_status}
                </span>
              )}
              {action && (
                <span className={`text-[10px] px-2 py-0.5 rounded-full ${ACTION_BADGE[action] || 'bg-gray-600 text-white'}`}>
                  {action}
                </span>
              )}
              {confidence && (
                <span className="flex items-center gap-1 text-[10px] text-gray-400">
                  <span className={`inline-block w-2 h-2 rounded-full ${CONFIDENCE_DOT[confidence] || 'bg-gray-400'}`} />
                  {confidence}
                </span>
              )}
              <span className="text-[10px] text-gray-500 ml-auto">
                {timeAgo(item.published_at || item.fetched_at)}
              </span>
            </div>

            {/* Headline */}
            <p className="text-sm font-medium text-white leading-snug">{item.headline}</p>

            {/* Players / teams */}
            {(item.players.length > 0 || item.teams.length > 0) && (
              <p className="text-xs text-gray-400 mt-1">
                {[...item.players, ...item.teams].filter(Boolean).slice(0, 3).join(' · ')}
              </p>
            )}
          </div>
        </div>

        {/* One-line betting hint from Haiku */}
        {cls?.one_line && (
          <p className="mt-2 text-xs text-yellow-300 italic">{cls.one_line as string}</p>
        )}
      </div>

      {/* Sonnet analysis panel */}
      {analysis ? (
        <div className="border-t border-gray-700 bg-gray-900">
          <button
            onClick={() => setExpanded(e => !e)}
            className="w-full px-4 py-2 text-xs text-left text-gray-400 hover:text-white flex items-center justify-between"
          >
            <span>Betting Analysis</span>
            <span>{expanded ? '▲' : '▼'}</span>
          </button>

          {expanded && (
            <div className="px-4 pb-4 space-y-3 text-sm">
              {/* Recommendation */}
              {analysis.reasoning && (
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Edge Reasoning</p>
                  <p className="text-gray-200">{analysis.reasoning as string}</p>
                </div>
              )}

              {/* Target + edge */}
              <div className="flex gap-4 text-xs">
                {analysis.target_team && (
                  <div>
                    <span className="text-gray-500">Target: </span>
                    <span className="text-white font-medium">{analysis.target_team as string}</span>
                  </div>
                )}
                {analysis.bet_type && (
                  <div>
                    <span className="text-gray-500">Market: </span>
                    <span className="text-white">{analysis.bet_type as string} / {analysis.direction as string}</span>
                  </div>
                )}
                {analysis.edge_estimate && (
                  <div>
                    <span className="text-gray-500">Edge: </span>
                    <span className="text-green-400">{analysis.edge_estimate as string}</span>
                  </div>
                )}
              </div>

              {/* Contrarian risk */}
              {analysis.contrarian_risk && (
                <div className="bg-red-950 border border-red-800 rounded p-2">
                  <p className="text-xs text-red-400 font-medium mb-0.5">Contrarian Risk</p>
                  <p className="text-xs text-red-200">{analysis.contrarian_risk as string}</p>
                </div>
              )}

              {/* Key factors */}
              {Array.isArray(analysis.key_factors) && (analysis.key_factors as string[]).length > 0 && (
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Key Factors</p>
                  <ul className="space-y-0.5">
                    {(analysis.key_factors as string[]).map((f, i) => (
                      <li key={i} className="text-xs text-gray-300 flex items-start gap-1">
                        <span className="text-yellow-500 mt-0.5">•</span> {f}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Time sensitivity */}
              {analysis.time_sensitivity && (
                <p className="text-xs text-gray-500">
                  Time sensitivity: <span className="text-gray-300">{analysis.time_sensitivity as string}</span>
                </p>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="border-t border-gray-700 px-4 py-2 flex items-center justify-between">
          <span className="text-xs text-gray-500">
            {item.analyzed_at === null && item.haiku_classification ? 'Analysis queued...' : 'Not yet analyzed'}
          </span>
          <button
            onClick={() => onAnalyze(item.id)}
            className="text-xs bg-blue-700 hover:bg-blue-600 text-white px-3 py-1 rounded transition-colors"
          >
            Analyze
          </button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

const SPORT_FILTERS = ['all', 'mlb', 'nba', 'nfl', 'nhl', 'wnba'];
const TYPE_FILTERS  = ['all', 'injury', 'general'];
const AUTO_REFRESH_MS = 5 * 60 * 1000; // 5 minutes

export function Alerts() {
  const [items, setItems]       = useState<NewsItem[]>([]);
  const [stats, setStats]       = useState<FeedStats | null>(null);
  const [loading, setLoading]   = useState(false);
  const [analyzing, setAnalyzing] = useState<Set<number>>(new Set());
  const [sport, setSport]       = useState('all');
  const [typeFilter, setType]   = useState('all');
  const [actionFilter, setAction] = useState('all');
  const [activeTab, setTab]     = useState<'feed' | 'insights'>('feed');
  const [lastFetch, setLastFetch] = useState<Date | null>(null);
  const [pollCountdown, setPollCountdown] = useState(AUTO_REFRESH_MS / 1000);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchFeed = useCallback(async () => {
    setLoading(true);
    try {
      const url = getApiUrl(`news/feed?sport=${sport}&limit=80`);
      const r = await fetch(url);
      if (!r.ok) throw new Error(await r.text());
      const d = await r.json();
      setItems(d.items || []);
      setLastFetch(new Date());
      setPollCountdown(AUTO_REFRESH_MS / 1000);
    } catch (e) {
      console.error('Feed fetch failed:', e);
    } finally {
      setLoading(false);
    }
  }, [sport]);

  const triggerRefresh = useCallback(async () => {
    // Fire-and-forget ESPN refresh in background, then reload feed after 8s
    try {
      await fetch(getApiUrl(`news/refresh?sport=${sport}`), { method: 'POST' });
      setTimeout(() => fetchFeed(), 8000);
    } catch (e) {
      console.error('Refresh trigger failed:', e);
    }
  }, [sport, fetchFeed]);

  const fetchStats = useCallback(async () => {
    try {
      const r = await fetch(getApiUrl('news/stats'));
      if (r.ok) setStats(await r.json());
    } catch {}
  }, []);

  const fetchInsights = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ sport, limit: '50' });
      if (actionFilter !== 'all') params.set('action', actionFilter);
      const r = await fetch(getApiUrl(`news/insights?${params}`));
      if (!r.ok) throw new Error(await r.text());
      const d = await r.json();
      setItems(d.insights || []);
    } catch (e) {
      console.error('Insights fetch failed:', e);
    } finally {
      setLoading(false);
    }
  }, [sport, actionFilter]);

  // Initial load + tab switch
  useEffect(() => {
    if (activeTab === 'feed')     { fetchFeed(); fetchStats(); }
    if (activeTab === 'insights') { fetchInsights(); }
  }, [activeTab, sport, actionFilter]);

  // Auto-refresh countdown (feed tab only)
  useEffect(() => {
    if (activeTab !== 'feed') return;
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setPollCountdown(c => {
        if (c <= 1) { fetchFeed(); return AUTO_REFRESH_MS / 1000; }
        return c - 1;
      });
    }, 1000);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [activeTab, fetchFeed]);

  const handleAnalyze = async (id: number) => {
    setAnalyzing(s => new Set(s).add(id));
    try {
      const r = await fetch(getApiUrl(`news/analyze/${id}`), { method: 'POST' });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      // Update haiku_classification immediately
      setItems(prev => prev.map(item =>
        item.id === id
          ? { ...item, haiku_classification: data.classification || item.haiku_classification }
          : item
      ));
      // Poll for sonnet result (up to 15s)
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        try {
          const pr = await fetch(getApiUrl(`news/item/${id}`));
          if (pr.ok) {
            const updated = await pr.json();
            if (updated.sonnet_analysis || attempts >= 10) {
              clearInterval(poll);
              setItems(prev => prev.map(item => item.id === id ? { ...item, ...updated } : item));
              setAnalyzing(s => { const n = new Set(s); n.delete(id); return n; });
            }
          }
        } catch {}
      }, 1500);
    } catch (e) {
      console.error('Analyze failed:', e);
      setAnalyzing(s => { const n = new Set(s); n.delete(id); return n; });
    }
  };

  // Client-side filter
  const displayed = items.filter(item => {
    if (typeFilter !== 'all' && item.news_type !== typeFilter) return false;
    return true;
  });

  const betNowCount = items.filter(
    i => (i.sonnet_analysis as Record<string,unknown> | null)?.recommended_action === 'BET NOW'
  ).length;

  return (
    <div className="min-h-screen bg-gray-950 text-white p-4 md:p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">Injury & News Intel</h1>
          <p className="text-sm text-gray-400 mt-1">
            Real-time injury and news feed — analyzed by AI for betting opportunities
          </p>
        </div>

        {/* Stats bar */}
        {stats && (
          <div className="flex gap-4 text-sm">
            <div className="text-center">
              <div className="text-xl font-bold text-white">{stats.injuries}</div>
              <div className="text-xs text-gray-500">Injuries</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-green-400">{betNowCount || stats.bet_now_count}</div>
              <div className="text-xs text-gray-500">Bet Now</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-blue-400">{stats.analyzed}</div>
              <div className="text-xs text-gray-500">Analyzed</div>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-5 border-b border-gray-700 pb-0">
        {(['feed', 'insights'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setTab(tab)}
            className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors -mb-px ${
              activeTab === tab
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}
          >
            {tab === 'feed' ? 'Live Feed' : 'AI Insights'}
            {tab === 'insights' && betNowCount > 0 && (
              <span className="ml-1.5 bg-green-600 text-white text-[10px] px-1.5 py-0.5 rounded-full">
                {betNowCount}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-5">
        {/* Sport filter */}
        <div className="flex gap-1 flex-wrap">
          {SPORT_FILTERS.map(s => (
            <button
              key={s}
              onClick={() => setSport(s)}
              className={`text-xs px-2.5 py-1 rounded border transition-colors ${
                sport === s
                  ? 'bg-blue-600 border-blue-500 text-white'
                  : 'border-gray-600 text-gray-400 hover:border-gray-500 hover:text-gray-300'
              }`}
            >
              {s === 'all' ? 'All Sports' : s.toUpperCase()}
            </button>
          ))}
        </div>

        {/* Type filter (feed tab) */}
        {activeTab === 'feed' && (
          <div className="flex gap-1">
            {TYPE_FILTERS.map(t => (
              <button
                key={t}
                onClick={() => setType(t)}
                className={`text-xs px-2.5 py-1 rounded border transition-colors ${
                  typeFilter === t
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'border-gray-600 text-gray-400 hover:border-gray-500 hover:text-gray-300'
                }`}
              >
                {t === 'all' ? 'All Types' : t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>
        )}

        {/* Action filter (insights tab) */}
        {activeTab === 'insights' && (
          <div className="flex gap-1">
            {['all', 'BET NOW', 'MONITOR', 'AVOID'].map(a => (
              <button
                key={a}
                onClick={() => setAction(a)}
                className={`text-xs px-2.5 py-1 rounded border transition-colors ${
                  actionFilter === a
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'border-gray-600 text-gray-400 hover:border-gray-500 hover:text-gray-300'
                }`}
              >
                {a === 'all' ? 'All Actions' : a}
              </button>
            ))}
          </div>
        )}

        {/* Refresh + countdown */}
        <div className="ml-auto flex items-center gap-2">
          {activeTab === 'feed' && (
            <span className="text-xs text-gray-500">
              Refresh in {pollCountdown}s
            </span>
          )}
          <button
            onClick={activeTab === 'feed' ? triggerRefresh : fetchInsights}
            disabled={loading}
            className="text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 px-3 py-1 rounded transition-colors disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Content */}
      {loading && items.length === 0 ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-gray-500 text-sm">Fetching news and injuries...</div>
        </div>
      ) : displayed.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-gray-500">
          <p className="text-sm">No items found.</p>
          <p className="text-xs mt-1">Try changing the filters or refreshing.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {displayed.map(item => (
            <div key={item.id} className="relative">
              {analyzing.has(item.id) && (
                <div className="absolute inset-0 bg-gray-900/70 rounded-lg flex items-center justify-center z-10">
                  <div className="text-xs text-blue-400 animate-pulse">Analyzing...</div>
                </div>
              )}
              <AnalysisCard item={item} onAnalyze={handleAnalyze} />
            </div>
          ))}
        </div>
      )}

      {lastFetch && (
        <p className="text-center text-xs text-gray-600 mt-6">
          Last fetched {lastFetch.toLocaleTimeString()}
        </p>
      )}
    </div>
  );
}
