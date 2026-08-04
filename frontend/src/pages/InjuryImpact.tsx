import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';

// ── Types ─────────────────────────────────────────────────────────────────────
interface Cascade { layer1: string; layer2: string; layer3: string; }

interface Beneficiary { name: string; position: string; ovr: number; }

interface Alert {
  team: string; opponent: string;
  player_name: string; position: string; pos_group: string; status: string;
  injury_note: string;
  starter_ovr: number | null; backup_name: string | null; backup_ovr: number | null;
  ovr_gap: number; impact_tier: 'HIGH' | 'MEDIUM' | 'LOW' | 'IGNORE';
  cascade: Cascade;
  opposing_beneficiary: Beneficiary | null;
  bet_signals: string[];
}

interface Game {
  game_id: string; name: string; date: string; week: number | null;
  home_team: string; away_team: string;
  home_team_name: string; away_team_name: string;
  alerts: Alert[];
  high_count: number; medium_count: number; low_count: number;
}

interface InjuryData {
  available: boolean; games: Game[];
  total_alerts: number; madden_season: string | null; week: number | null;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
const TIER_STYLE = {
  HIGH:   { border: 'border-red-500/40',    bg: 'bg-red-500/10',    badge: 'bg-red-500 text-white',    dot: 'bg-red-500',    label: 'HIGH IMPACT'   },
  MEDIUM: { border: 'border-yellow-500/40', bg: 'bg-yellow-500/10', badge: 'bg-yellow-500 text-black', dot: 'bg-yellow-400', label: 'MEDIUM IMPACT' },
  LOW:    { border: 'border-slate-600/40',  bg: 'bg-slate-800/30',  badge: 'bg-slate-600 text-white',  dot: 'bg-slate-500',  label: 'MONITOR'       },
};

const STATUS_COLOR: Record<string, string> = {
  'Out':            'text-red-400 bg-red-500/10 border-red-500/30',
  'Injured Reserve':'text-red-500 bg-red-600/10 border-red-600/30',
  'Doubtful':       'text-orange-400 bg-orange-500/10 border-orange-500/30',
  'Questionable':   'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
};

function ovrBadge(ovr: number | null) {
  if (ovr === null) return <span className="text-slate-500 text-xs">—</span>;
  const cls = ovr >= 90 ? 'text-yellow-400 font-black' : ovr >= 80 ? 'text-green-400 font-bold' : ovr >= 70 ? 'text-blue-400 font-semibold' : 'text-slate-400';
  return <span className={`font-mono text-sm ${cls}`}>{ovr}</span>;
}

function logoUrl(abbr: string) {
  const map: Record<string,string> = { LA:'lar', WAS:'wsh', JAX:'jax' };
  return `https://a.espncdn.com/i/teamlogos/nfl/500/${map[abbr] ?? abbr.toLowerCase()}.png`;
}

// ── How It Works panel ────────────────────────────────────────────────────────
function HowItWorks() {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-slate-800/50 border border-blue-700/30 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full px-5 py-4 flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-3">
          <span className="text-blue-400 text-lg">💡</span>
          <div>
            <div className="font-bold text-white text-sm">How the Cascading Impact Engine Works</div>
            <div className="text-slate-400 text-xs mt-0.5">Learn to read the 3-layer analysis and bet signals</div>
          </div>
        </div>
        <svg className={`w-5 h-5 text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="px-5 pb-5 border-t border-slate-700 space-y-5 pt-4">
          <p className="text-slate-300 text-sm leading-relaxed">
            Most injury analysis stops at "Player X is OUT." This engine goes three layers deeper — because the real betting edge lives in the chain reaction, not the headline.
          </p>

          <div className="grid md:grid-cols-3 gap-4">
            {[
              {
                num: '01', color: 'text-blue-400 border-blue-500/30 bg-blue-500/5',
                title: 'The Replacement Gap',
                body: 'We compare the starter\'s Madden OVR rating to their backup\'s. A 15-point gap is significant. A 3-point gap is noise. A WR3 going to WR4 rarely matters — an LT dropping from 83 to 68 OVR changes the entire play-calling structure.',
              },
              {
                num: '02', color: 'text-purple-400 border-purple-500/30 bg-purple-500/5',
                title: 'The Opposing Matchup',
                body: 'Who on the other team specifically benefits? If your starting LT is out, we find the opposing team\'s best edge rusher and show you their OVR. If he\'s an 87 OVR who was getting doubled — he\'s now one-on-one with a backup.',
              },
              {
                num: '03', color: 'text-green-400 border-green-500/30 bg-green-500/5',
                title: 'The Play Calling Constraint',
                body: 'This is where the bet angle lives. A QB under blindside pressure doesn\'t just get sacked more — he throws shorter, quicker, and more conservatively. Downfield targets drop. Rush share rises. These are the real betting implications.',
              },
            ].map(s => (
              <div key={s.num} className={`border rounded-xl p-4 ${s.color}`}>
                <div className={`text-3xl font-black ${s.color.split(' ')[0]} opacity-30 mb-2`}>{s.num}</div>
                <div className={`font-bold text-sm mb-2 ${s.color.split(' ')[0]}`}>{s.title}</div>
                <p className="text-slate-400 text-xs leading-relaxed">{s.body}</p>
              </div>
            ))}
          </div>

          <div className="bg-slate-900/60 border border-slate-700 rounded-xl p-4 space-y-3">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Impact Tiers</div>
            <div className="grid md:grid-cols-3 gap-3">
              {([
                { tier: 'HIGH', desc: 'OVR gap ≥ 10 at a critical position (QB, LT, CB1, Elite EDGE). High-confidence bet signal.' },
                { tier: 'MEDIUM', desc: 'OVR gap 5-9, or important position at moderate gap. Context-dependent — read the full cascade.' },
                { tier: 'LOW', desc: 'Small gap or low-impact position. May matter in certain game scripts. Monitor for line movement.' },
              ] as const).map(({ tier, desc }) => (
                <div key={tier} className="flex items-start gap-3">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-black ${TIER_STYLE[tier].badge} flex-shrink-0 mt-0.5`}>{tier}</span>
                  <p className="text-slate-400 text-xs leading-relaxed">{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Alert Card ────────────────────────────────────────────────────────────────
function AlertCard({ alert }: { alert: Alert }) {
  const [expanded, setExpanded] = useState(alert.impact_tier === 'HIGH');
  const style = TIER_STYLE[alert.impact_tier] ?? TIER_STYLE.LOW;

  return (
    <div className={`border rounded-xl overflow-hidden ${style.border} ${style.bg}`}>
      {/* Header row */}
      <button
        onClick={() => setExpanded(o => !o)}
        className="w-full px-4 py-3 flex items-center gap-3 text-left"
      >
        <span className={`w-2 h-2 rounded-full flex-shrink-0 ${style.dot}`} />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-bold text-white text-sm">{alert.player_name}</span>
            <span className="text-slate-500 text-xs font-mono">{alert.position}</span>
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${STATUS_COLOR[alert.status] ?? 'text-slate-400'}`}>
              {alert.status.toUpperCase()}
            </span>
          </div>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className="text-slate-500 text-xs">{alert.team}</span>
            {alert.starter_ovr !== null && (
              <span className="text-slate-500 text-xs">
                OVR {ovrBadge(alert.starter_ovr)}
                {alert.backup_ovr !== null && (
                  <span className="text-slate-600"> → {ovrBadge(alert.backup_ovr)}</span>
                )}
                {alert.ovr_gap > 0 && (
                  <span className="text-red-400 ml-1">(-{alert.ovr_gap})</span>
                )}
              </span>
            )}
            {alert.opposing_beneficiary && (
              <>
                <span className="text-slate-700 text-xs">·</span>
                <span className="text-slate-500 text-xs">Benefits:</span>
                <img
                  src={logoUrl(alert.opponent)} alt=""
                  className="w-3.5 h-3.5 object-contain inline-block"
                  onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
                <span className="text-slate-200 text-xs font-semibold">{alert.opposing_beneficiary.name}</span>
                <span className="text-slate-500 text-xs font-mono">{alert.opposing_beneficiary.position}</span>
                <span className={`text-xs font-bold font-mono ${alert.opposing_beneficiary.ovr >= 85 ? 'text-yellow-400' : alert.opposing_beneficiary.ovr >= 75 ? 'text-green-400' : 'text-slate-400'}`}>
                  {alert.opposing_beneficiary.ovr}
                </span>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <span className={`text-[10px] font-black px-2 py-0.5 rounded ${style.badge}`}>{style.label}</span>
          <svg className={`w-4 h-4 text-slate-500 transition-transform ${expanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Expanded cascade detail */}
      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-slate-700/50 pt-3">

          {/* Backup info */}
          {alert.backup_name && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-500 font-semibold">BACKUP:</span>
              <span className="text-white font-semibold">{alert.backup_name}</span>
              <span className="text-slate-400">(OVR {alert.backup_ovr ?? '?'})</span>
            </div>
          )}

          {/* Three layers */}
          <div className="space-y-2.5">
            {[
              { num: '01', label: 'REPLACEMENT GAP', text: alert.cascade.layer1, color: 'text-blue-400' },
              { num: '02', label: 'MATCHUP IMPACT',  text: alert.cascade.layer2, color: 'text-purple-400' },
              { num: '03', label: 'PLAYCALLING CONSTRAINT', text: alert.cascade.layer3, color: 'text-green-400' },
            ].map(l => l.text ? (
              <div key={l.num} className="flex gap-3">
                <span className={`text-[10px] font-black ${l.color} opacity-60 flex-shrink-0 mt-0.5 w-5`}>{l.num}</span>
                <div>
                  <div className={`text-[10px] font-bold uppercase tracking-wider ${l.color} mb-0.5`}>{l.label}</div>
                  <p className="text-slate-300 text-xs leading-relaxed">{l.text}</p>
                </div>
              </div>
            ) : null)}
          </div>

          {/* Opposing beneficiary */}
          {alert.opposing_beneficiary && (
            <div className="bg-slate-900/60 border border-slate-700 rounded-lg p-3 flex items-center gap-3">
              <div className="text-slate-500 text-xs font-bold uppercase tracking-wider flex-shrink-0">Benefits</div>
              <div className="flex items-center gap-2">
                <img
                  src={logoUrl(alert.opponent)} alt=""
                  className="w-5 h-5 object-contain"
                  onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
                <span className="text-white font-bold text-sm">{alert.opposing_beneficiary.name}</span>
                <span className="text-slate-500 text-xs">{alert.opposing_beneficiary.position}</span>
                <span className={`font-mono text-sm font-bold ${alert.opposing_beneficiary.ovr >= 85 ? 'text-yellow-400' : alert.opposing_beneficiary.ovr >= 75 ? 'text-green-400' : 'text-slate-300'}`}>
                  OVR {alert.opposing_beneficiary.ovr}
                </span>
              </div>
            </div>
          )}

          {/* Bet signals */}
          {alert.bet_signals.length > 0 && (
            <div>
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">BET SIGNALS</div>
              <div className="flex flex-wrap gap-1.5">
                {alert.bet_signals.map(sig => (
                  <span
                    key={sig}
                    className={`text-[11px] font-semibold px-2 py-0.5 rounded border ${
                      sig.startsWith('↑') ? 'text-green-400 bg-green-500/10 border-green-500/20' :
                      sig.startsWith('↓') ? 'text-red-400 bg-red-500/10 border-red-500/20' :
                      'text-slate-300 bg-slate-700/50 border-slate-600/30'
                    }`}
                  >{sig}</span>
                ))}
              </div>
            </div>
          )}

          {/* Injury note */}
          {alert.injury_note && (
            <p className="text-slate-500 text-xs italic border-t border-slate-700/50 pt-2">{alert.injury_note}</p>
          )}
        </div>
      )}
    </div>
  );
}

// ── Game Card ─────────────────────────────────────────────────────────────────
function GameCard({ game, tierFilter }: { game: Game; tierFilter: string }) {
  const visible = game.alerts.filter(a =>
    tierFilter === 'ALL' ? a.impact_tier !== 'IGNORE'
    : a.impact_tier === tierFilter
  );

  if (visible.length === 0 && tierFilter !== 'ALL') return null;

  const gameDate = game.date ? new Date(game.date).toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
  }) : '';

  return (
    <div className="bg-slate-800/30 border border-slate-700 rounded-xl overflow-hidden">
      {/* Game header */}
      <div className="px-5 py-3 border-b border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <img src={logoUrl(game.away_team)} alt={game.away_team} className="w-8 h-8 object-contain"
              onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
            <span className="font-black text-white">{game.away_team}</span>
            <span className="text-slate-500 text-xs font-bold">@</span>
            <span className="font-black text-white">{game.home_team}</span>
            <img src={logoUrl(game.home_team)} alt={game.home_team} className="w-8 h-8 object-contain"
              onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
          </div>
          {gameDate && <span className="text-slate-500 text-xs">{gameDate}</span>}
        </div>
        <div className="flex items-center gap-2 text-xs">
          {game.high_count > 0   && <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-400 font-bold">{game.high_count} HIGH</span>}
          {game.medium_count > 0 && <span className="px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-400 font-bold">{game.medium_count} MED</span>}
          {game.low_count > 0    && <span className="px-2 py-0.5 rounded bg-slate-700 text-slate-400 font-bold">{game.low_count} LOW</span>}
        </div>
      </div>

      {/* Alerts */}
      <div className="p-4 space-y-3">
        {visible.length === 0 ? (
          <p className="text-slate-500 text-sm text-center py-4">No significant injury impacts for this game.</p>
        ) : (
          visible.map((alert, i) => <AlertCard key={`${alert.player_name}-${i}`} alert={alert} />)
        )}
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export function InjuryImpact() {
  const [data, setData]           = useState<InjuryData | null>(null);
  const [loading, setLoading]     = useState(true);
  const [tierFilter, setTierFilter] = useState<string>('ALL');

  useEffect(() => {
    fetch(getApiUrl('f5/injury-impact'))
      .then(r => r.json())
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  const tierBtns = ['ALL', 'HIGH', 'MEDIUM', 'LOW'] as const;

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black italic tracking-tight">
              INJURY <span className="text-red-400">IMPACT</span> ENGINE
            </h1>
            <p className="text-slate-400 mt-1">
              Cascading effects analysis — how injuries reshape matchups, play-calling, and betting lines
            </p>
          </div>
          {data?.available && (
            <div className="text-sm text-slate-400 flex items-center gap-3 flex-shrink-0">
              {data.week && <span>Week <span className="text-white font-bold">{data.week}</span></span>}
              <span><span className="text-white font-bold">{data.total_alerts}</span> alerts</span>
              {data.madden_season && <span className="text-slate-600">· Madden {data.madden_season}</span>}
            </div>
          )}
        </div>

        {/* How It Works */}
        <HowItWorks />

        {/* Loading */}
        {loading && (
          <div className="py-16 text-center text-slate-500 animate-pulse">
            Analyzing injury reports and depth charts…
          </div>
        )}

        {/* No data */}
        {!loading && (!data?.available || data.games.length === 0) && (
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-8 text-center">
            <div className="text-slate-400 font-bold mb-2">No games currently scheduled</div>
            <p className="text-slate-500 text-sm">
              This tool activates during the NFL season (September–February). Check back when the
              weekly schedule is released — injury reports lock Thursday and the analysis updates automatically.
            </p>
          </div>
        )}

        {/* Active content */}
        {!loading && data?.available && data.games.length > 0 && (
          <>
            {/* Tier filter */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Filter:</span>
              {tierBtns.map(t => (
                <button
                  key={t}
                  onClick={() => setTierFilter(t)}
                  className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${
                    tierFilter === t
                      ? t === 'HIGH'   ? 'bg-red-500 text-white'
                      : t === 'MEDIUM' ? 'bg-yellow-500 text-black'
                      : t === 'LOW'    ? 'bg-slate-600 text-white'
                      : 'bg-blue-600 text-white'
                      : 'bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>

            {/* Games */}
            <div className="space-y-6">
              {data.games.map(g => (
                <GameCard key={g.game_id} game={g} tierFilter={tierFilter} />
              ))}
            </div>
          </>
        )}

      </div>
    </div>
  );
}
