import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';

const BG      = 'oklch(14.5% 0 0)';
const PANEL   = 'oklch(18% 0 0)';
const BORDER  = 'oklch(100% 0 0 / .08)';
const FG      = 'oklch(98.5% 0 0)';
const MUTED   = 'oklch(60% 0 0)';
const EMERALD = 'oklch(69.6% .17 162.48)';
const RED     = 'oklch(63.2% .204 25.331)';
const YELLOW  = 'oklch(79.5% .184 86.047)';
const BLUE    = 'oklch(62.3% .214 259.815)';
const PURPLE  = 'oklch(65% .22 295)';

// ── Model picks types ────────────────────────────────────────────────────────

interface ModelPick {
  id: number;
  sport: string;
  home_team: string;
  away_team: string;
  game_time_cst: string | null;
  pick_side: string;
  pick_type: string;
  edge_pct: number;
  confidence_tier: string;
  market_odds: number;
  our_probability: number;
  detector: string;
  status: string;
  pl_units: number | null;
  sonnet_narrative: string | null;
  home_pitcher: string | null;
  away_pitcher: string | null;
  home_pitcher_era: number | null;
  away_pitcher_era: number | null;
}

interface ModelRecapSummary {
  total: number;
  wins: number;
  losses: number;
  pushes: number;
  pending: number;
  graded: number;
  win_rate: number | null;
  total_pl: number;
}

interface ModelRecapData {
  date: string;
  picks: ModelPick[];
  summary: ModelRecapSummary;
}

// ── F5 types ─────────────────────────────────────────────────────────────────

interface SignalResult {
  name: string;
  tier: 'STRONG' | 'GOOD' | 'WEAK';
  won: boolean;
  pl: number;
  result: string;
}

interface GameRecord {
  away_team: string;
  home_team: string;
  away_pitcher: string;
  home_pitcher: string;
  away_era: number | null;
  home_era: number | null;
  venue: string;
  hp_umpire: string | null;
  hi_ump: boolean;
  lo_ump: boolean;
  away_r5: number;
  home_r5: number;
  f5_total: number;
  f5_tied: boolean;
  f5_leader: string;
  f1_away: number;
  f1_home: number;
  away_final: number;
  home_final: number;
  signals: SignalResult[];
}

interface RecapData {
  date: string;
  games: GameRecord[];
  total_games: number;
  ties_today: number;
  tie_rate: number;
  summary: {
    total_bets: number;
    wins: number;
    losses: number;
    win_rate: number;
    total_pl: number;
  };
}

const TIER_COLOR: Record<string, string> = { STRONG: EMERALD, GOOD: YELLOW, WEAK: MUTED };

/** Return today's date in CST as YYYY-MM-DD regardless of browser timezone. */
function todayCst(): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Chicago' }).format(new Date());
}
function prevDate(d: string): string {
  const dt = new Date(d + 'T12:00:00');
  dt.setDate(dt.getDate() - 1);
  return dt.toISOString().slice(0, 10);
}
function nextDate(d: string): string {
  const dt = new Date(d + 'T12:00:00');
  dt.setDate(dt.getDate() + 1);
  return dt.toISOString().slice(0, 10);
}
function yesterday(): string {
  const dt = new Date(todayCst() + 'T12:00:00');
  dt.setDate(dt.getDate() - 1);
  return dt.toISOString().slice(0, 10);
}
function fmtDate(d: string): string {
  return new Date(d + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
}

function EraTag({ era }: { era: number | null }) {
  if (era == null) return <span style={{ color: MUTED }}>—</span>;
  const color = era < 3.5 ? EMERALD : era < 4.5 ? YELLOW : RED;
  return <span style={{ color, fontWeight: 700 }}>{era.toFixed(2)}</span>;
}

function SignalChip({ sig }: { sig: SignalResult }) {
  const color = sig.won ? EMERALD : RED;
  const bg = sig.won ? 'oklch(69.6% .17 162.48 / .12)' : 'oklch(63.2% .204 25.331 / .12)';
  const tier = TIER_COLOR[sig.tier] ?? MUTED;
  return (
    <div style={{ background: bg, border: `1px solid ${color}20`, borderRadius: 8, padding: '8px 12px', marginBottom: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        <div>
          <span style={{ fontSize: '0.65rem', fontWeight: 700, color: tier, letterSpacing: '0.06em' }}>{sig.tier}</span>
          <div style={{ fontWeight: 600, color: FG, fontSize: '0.78rem', marginTop: 2 }}>{sig.name}</div>
          <div style={{ fontSize: '0.65rem', color: MUTED, marginTop: 2 }}>{sig.result}</div>
        </div>
        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <div style={{ fontWeight: 800, color, fontSize: '0.85rem' }}>
            {sig.pl >= 0 ? '+' : ''}${sig.pl.toFixed(0)}
          </div>
          <div style={{ fontSize: '0.65rem', color: sig.won ? EMERALD : RED }}>{sig.won ? 'WIN' : 'LOSS'}</div>
        </div>
      </div>
    </div>
  );
}

function GameCard({ g }: { g: GameRecord }) {
  const hasSignals = g.signals.length > 0;
  const signalPL = g.signals.reduce((s, x) => s + x.pl, 0);
  const f5Score = `${g.away_r5}–${g.home_r5}`;
  const finalScore = `${g.away_final}–${g.home_final}`;

  return (
    <div style={{
      background: PANEL, border: `1px solid ${hasSignals ? (signalPL >= 0 ? EMERALD + '30' : RED + '30') : BORDER}`,
      borderRadius: 12, padding: '16px 18px', marginBottom: 12,
    }}>
      {/* Teams + Score */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: '0.9rem', fontFamily: 'Nunito', color: FG }}>
            {g.away_team} <span style={{ color: MUTED, fontWeight: 400 }}>@</span> {g.home_team}
          </div>
          <div style={{ fontSize: '0.7rem', color: MUTED, marginTop: 2 }}>{g.venue}</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '0.65rem', color: MUTED, marginBottom: 1 }}>F5 · FINAL</div>
          <div style={{ fontWeight: 800, fontSize: '1.1rem', fontFamily: 'Nunito', color: g.f5_tied ? EMERALD : FG }}>
            {f5Score}
            <span style={{ color: MUTED, fontWeight: 400, fontSize: '0.85rem' }}> · {finalScore}</span>
          </div>
          {g.f5_tied && <div style={{ fontSize: '0.65rem', color: EMERALD, fontWeight: 700 }}>F5 TIE</div>}
        </div>
      </div>

      {/* Pitcher row */}
      <div style={{ display: 'flex', gap: 16, marginBottom: hasSignals ? 12 : 0, flexWrap: 'wrap' }}>
        <div style={{ fontSize: '0.72rem', color: MUTED }}>
          {g.away_team.split(' ').pop()}: <span style={{ color: FG }}>{g.away_pitcher}</span>{' '}
          <EraTag era={g.away_era} />
        </div>
        <div style={{ fontSize: '0.72rem', color: MUTED }}>
          {g.home_team.split(' ').pop()}: <span style={{ color: FG }}>{g.home_pitcher}</span>{' '}
          <EraTag era={g.home_era} />
        </div>
        {g.hp_umpire && (
          <div style={{ fontSize: '0.72rem', color: g.hi_ump ? YELLOW : g.lo_ump ? BLUE : MUTED }}>
            HP Ump: <span style={{ fontWeight: 600 }}>{g.hp_umpire}</span>
            {g.hi_ump && <span style={{ color: YELLOW, marginLeft: 4 }}>↑ HIGH TIE</span>}
            {g.lo_ump && <span style={{ color: BLUE, marginLeft: 4 }}>↓ LOW TIE</span>}
          </div>
        )}
      </div>

      {/* Signals */}
      {hasSignals && (
        <div style={{ borderTop: `1px solid ${BORDER}`, paddingTop: 10 }}>
          <div style={{ fontSize: '0.65rem', color: MUTED, letterSpacing: '0.07em', marginBottom: 8 }}>
            SIGNALS TRIGGERED ({g.signals.length}) · Net: <span style={{ color: signalPL >= 0 ? EMERALD : RED, fontWeight: 700 }}>{signalPL >= 0 ? '+' : ''}${signalPL.toFixed(0)}</span>
          </div>
          {g.signals.map((sig, i) => <SignalChip key={i} sig={sig} />)}
        </div>
      )}

      {!hasSignals && (
        <div style={{ fontSize: '0.7rem', color: MUTED, fontStyle: 'italic', marginTop: 4 }}>No signals triggered</div>
      )}
    </div>
  );
}

function ModelPickCard({ p }: { p: ModelPick }) {
  const status      = p.status ?? 'pending';
  const confTier    = p.confidence_tier ?? 'low';
  const statusColor = status === 'win' ? EMERALD : status === 'loss' ? RED : status === 'push' ? YELLOW : MUTED;
  const borderColor = status === 'win' ? EMERALD + '30' : status === 'loss' ? RED + '30' : BORDER;
  const confColor   = confTier === 'high' ? EMERALD : confTier === 'medium' ? YELLOW : MUTED;
  const pickLabel   = `${(p.pick_side ?? '').toUpperCase()} ${(p.pick_type ?? '').toUpperCase()}`.trim();
  const oddsStr     = p.market_odds != null ? (p.market_odds >= 0 ? `+${p.market_odds}` : `${p.market_odds}`) : '—';
  const gameTime    = p.game_time_cst ? new Date(p.game_time_cst).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: 'America/Chicago' }) : null;

  return (
    <div style={{ background: PANEL, border: `1px solid ${borderColor}`, borderRadius: 12, padding: '16px 18px', marginBottom: 12 }}>
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: '0.9rem', fontFamily: 'Nunito', color: FG }}>
            {p.away_team} <span style={{ color: MUTED, fontWeight: 400 }}>@</span> {p.home_team}
          </div>
          <div style={{ fontSize: '0.68rem', color: MUTED, marginTop: 2 }}>
            {p.sport.toUpperCase()}{gameTime ? ` · ${gameTime} CT` : ''}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '0.65rem', color: MUTED, marginBottom: 2 }}>STATUS</div>
          <div style={{ fontWeight: 800, fontSize: '0.95rem', color: statusColor }}>
            {status.toUpperCase()}
            {p.pl_units != null && (
              <span style={{ marginLeft: 6, fontSize: '0.8rem' }}>
                ({p.pl_units >= 0 ? '+' : ''}{p.pl_units.toFixed(2)}u)
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Pick details */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
        <span style={{ background: PURPLE + '20', border: `1px solid ${PURPLE}40`, borderRadius: 6, padding: '3px 8px', fontSize: '0.7rem', fontWeight: 700, color: PURPLE }}>
          {pickLabel} {oddsStr}
        </span>
        <span style={{ background: confColor + '15', border: `1px solid ${confColor}40`, borderRadius: 6, padding: '3px 8px', fontSize: '0.7rem', fontWeight: 700, color: confColor }}>
          {confTier.toUpperCase()}
        </span>
        <span style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '3px 8px', fontSize: '0.7rem', color: MUTED }}>
          Edge: <span style={{ color: FG, fontWeight: 700 }}>+{(p.edge_pct ?? 0).toFixed(1)}%</span>
        </span>
        <span style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '3px 8px', fontSize: '0.7rem', color: MUTED }}>
          {(p.detector ?? '').replace('rule_', '').replace(/_/g, ' ')}
        </span>
      </div>

      {/* Pitchers (MLB only) */}
      {(p.home_pitcher || p.away_pitcher) && (
        <div style={{ display: 'flex', gap: 16, marginBottom: 10, flexWrap: 'wrap' }}>
          {p.away_pitcher && (
            <div style={{ fontSize: '0.72rem', color: MUTED }}>
              {p.away_team.split(' ').pop()}: <span style={{ color: FG }}>{p.away_pitcher}</span>{' '}
              {p.away_pitcher_era != null && (
                <span style={{ color: p.away_pitcher_era < 3.5 ? EMERALD : p.away_pitcher_era < 4.5 ? YELLOW : RED, fontWeight: 700 }}>
                  {p.away_pitcher_era.toFixed(2)}
                </span>
              )}
            </div>
          )}
          {p.home_pitcher && (
            <div style={{ fontSize: '0.72rem', color: MUTED }}>
              {p.home_team.split(' ').pop()}: <span style={{ color: FG }}>{p.home_pitcher}</span>{' '}
              {p.home_pitcher_era != null && (
                <span style={{ color: p.home_pitcher_era < 3.5 ? EMERALD : p.home_pitcher_era < 4.5 ? YELLOW : RED, fontWeight: 700 }}>
                  {p.home_pitcher_era.toFixed(2)}
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {/* Narrative */}
      {p.sonnet_narrative && (
        <div style={{ fontSize: '0.72rem', color: MUTED, lineHeight: 1.6, borderTop: `1px solid ${BORDER}`, paddingTop: 10 }}>
          {p.sonnet_narrative.slice(0, 280)}{p.sonnet_narrative.length > 280 ? '…' : ''}
        </div>
      )}
    </div>
  );
}

export function DailyRecap() {
  const [date, setDate] = useState(yesterday());
  const [tab, setTab] = useState<'f5' | 'model'>('model');
  const [data, setData] = useState<RecapData | null>(null);
  const [modelData, setModelData] = useState<ModelRecapData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = (d: string) => {
    setDate(d);
    setLoading(true);
    setError('');
    setData(null);
    setModelData(null);

    Promise.all([
      fetch(getApiUrl(`f5/recap?date=${d}`)).then(r => r.json()).catch(() => null),
      fetch(getApiUrl(`predictions/recap?date=${d}`)).then(r => r.json()).catch(() => null),
    ]).then(([f5, model]) => {
      if (f5) setData(f5);
      if (model) setModelData(model);
      setLoading(false);
    }).catch(() => { setError('Failed to load recap data.'); setLoading(false); });
  };

  useEffect(() => { load(yesterday()); }, []);

  const gamesWithSignals = data?.games.filter(g => g.signals.length > 0) ?? [];
  const gamesNoSignals   = data?.games.filter(g => g.signals.length === 0) ?? [];
  const todayStr = todayCst();

  return (
    <div style={{ background: BG, minHeight: '100vh', padding: '32px 24px', color: FG }}>
      <div style={{ maxWidth: 900, margin: '0 auto' }}>

        {/* Header */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: '0.65rem', color: MUTED, letterSpacing: '0.12em', marginBottom: 8 }}>DAILY RECAP</div>
          <h1 style={{ fontSize: '1.9rem', fontWeight: 800, fontFamily: 'Nunito', margin: 0, lineHeight: 1.1 }}>Daily Results</h1>
        </div>

        {/* Tab switcher */}
        <div style={{ display: 'flex', gap: 4, marginBottom: 24, background: PANEL, borderRadius: 10, padding: 4, border: `1px solid ${BORDER}`, width: 'fit-content' }}>
          {([['model', 'MODEL PICKS'], ['f5', 'F5 SIGNALS']] as const).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              style={{
                background: tab === key ? (key === 'model' ? PURPLE : BLUE) : 'transparent',
                border: 'none', borderRadius: 7, padding: '7px 20px',
                color: tab === key ? '#fff' : MUTED, fontWeight: 700,
                fontSize: '0.72rem', letterSpacing: '0.07em', cursor: 'pointer', transition: 'all .15s',
              }}
            >{label}</button>
          ))}
        </div>

        {/* Date nav */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
          <button
            onClick={() => load(prevDate(date))}
            style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 8, padding: '8px 14px', color: FG, cursor: 'pointer', fontSize: '0.78rem' }}
          >← Prev</button>
          <div style={{ fontWeight: 700, fontFamily: 'Nunito', fontSize: '1rem', color: FG }}>{fmtDate(date)}</div>
          <button
            onClick={() => load(nextDate(date))}
            disabled={nextDate(date) > todayStr}
            style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 8, padding: '8px 14px', color: nextDate(date) > todayStr ? MUTED : FG, cursor: nextDate(date) > todayStr ? 'default' : 'pointer', fontSize: '0.78rem' }}
          >Next →</button>
          <button
            onClick={() => load(yesterday())}
            style={{ background: 'transparent', border: `1px solid ${BORDER}`, borderRadius: 8, padding: '8px 12px', color: MUTED, cursor: 'pointer', fontSize: '0.7rem', marginLeft: 'auto' }}
          >Yesterday</button>
        </div>

        {/* Loading */}
        {loading && (
          <div style={{ textAlign: 'center', padding: 60, color: MUTED }}>
            Loading results for {fmtDate(date)}...
          </div>
        )}

        {/* Error */}
        {error && <div style={{ textAlign: 'center', padding: 40, color: RED }}>{error}</div>}

        {/* ── MODEL PICKS TAB ──────────────────────────────────────────── */}
        {tab === 'model' && !loading && (
          <>
            {/* Summary bar */}
            {modelData && (
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 24 }}>
                {[
                  { label: 'PICKS', value: modelData.summary.total.toString(), color: FG },
                  { label: 'RECORD', value: modelData.summary.graded > 0 ? `${modelData.summary.wins}-${modelData.summary.losses}-${modelData.summary.pushes}` : '—', color: FG },
                  { label: 'WIN RATE', value: modelData.summary.win_rate != null ? `${modelData.summary.win_rate}%` : '—', color: (modelData.summary.win_rate ?? 0) >= 55 ? EMERALD : (modelData.summary.win_rate ?? 0) >= 40 ? YELLOW : modelData.summary.graded > 0 ? RED : MUTED },
                  { label: 'NET P&L', value: modelData.summary.graded > 0 ? `${modelData.summary.total_pl >= 0 ? '+' : ''}${modelData.summary.total_pl.toFixed(2)}u` : '—', color: modelData.summary.total_pl >= 0 ? EMERALD : RED },
                  { label: 'PENDING', value: modelData.summary.pending.toString(), color: modelData.summary.pending > 0 ? YELLOW : MUTED },
                ].map(s => (
                  <div key={s.label} style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 10, padding: '12px 18px', flex: 1, minWidth: 100 }}>
                    <div style={{ fontSize: '0.6rem', color: MUTED, letterSpacing: '0.08em', marginBottom: 4 }}>{s.label}</div>
                    <div style={{ fontWeight: 800, fontSize: '1.1rem', color: s.color, fontFamily: 'Nunito' }}>{s.value}</div>
                  </div>
                ))}
              </div>
            )}

            {modelData && modelData.picks.length > 0 && modelData.picks.map(p => (
              <ModelPickCard key={p.id} p={p} />
            ))}

            {modelData && modelData.picks.length === 0 && (
              <div style={{ textAlign: 'center', padding: 60, color: MUTED }}>
                No model picks found for {fmtDate(date)}.
              </div>
            )}

            {!modelData && !loading && (
              <div style={{ textAlign: 'center', padding: 60, color: MUTED }}>No data available.</div>
            )}
          </>
        )}

        {/* ── F5 SIGNALS TAB ───────────────────────────────────────────── */}
        {tab === 'f5' && !loading && (
          <>
            {/* Summary bar */}
            {data && (
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 24 }}>
                {[
                  { label: 'GAMES', value: data.total_games.toString(), color: FG },
                  { label: 'F5 TIES', value: `${data.ties_today} (${data.tie_rate}%)`, color: data.ties_today > 0 ? EMERALD : MUTED },
                  { label: 'SIGNALS FIRED', value: data.summary.total_bets.toString(), color: data.summary.total_bets > 0 ? YELLOW : MUTED },
                  { label: 'WIN RATE', value: data.summary.total_bets > 0 ? `${data.summary.win_rate}%` : '—', color: data.summary.win_rate >= 55 ? EMERALD : data.summary.win_rate >= 40 ? YELLOW : RED },
                  { label: 'NET P&L', value: data.summary.total_bets > 0 ? `${data.summary.total_pl >= 0 ? '+' : ''}$${data.summary.total_pl.toFixed(0)}` : '—', color: data.summary.total_pl >= 0 ? EMERALD : RED },
                ].map(s => (
                  <div key={s.label} style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 10, padding: '12px 18px', flex: 1, minWidth: 110 }}>
                    <div style={{ fontSize: '0.6rem', color: MUTED, letterSpacing: '0.08em', marginBottom: 4 }}>{s.label}</div>
                    <div style={{ fontWeight: 800, fontSize: '1.1rem', color: s.color, fontFamily: 'Nunito' }}>{s.value}</div>
                  </div>
                ))}
              </div>
            )}

            {data && gamesWithSignals.length > 0 && (
              <>
                <div style={{ fontSize: '0.65rem', color: YELLOW, letterSpacing: '0.1em', fontWeight: 700, marginBottom: 10 }}>
                  SIGNAL GAMES ({gamesWithSignals.length})
                </div>
                {gamesWithSignals.map((g, i) => <GameCard key={i} g={g} />)}
              </>
            )}

            {data && gamesNoSignals.length > 0 && (
              <>
                <div style={{ fontSize: '0.65rem', color: MUTED, letterSpacing: '0.1em', fontWeight: 700, margin: '20px 0 10px' }}>
                  OTHER GAMES ({gamesNoSignals.length})
                </div>
                {gamesNoSignals.map((g, i) => <GameCard key={i} g={g} />)}
              </>
            )}

            {data && data.total_games === 0 && (
              <div style={{ textAlign: 'center', padding: 60, color: MUTED }}>
                No completed MLB games found for {fmtDate(date)}.
              </div>
            )}
          </>
        )}

        {/* Disclaimer */}
        <div style={{ marginTop: 28, fontSize: '0.65rem', color: MUTED, lineHeight: 1.6, textAlign: 'center' }}>
          {tab === 'f5'
            ? 'Results are reconstructed from MLB Stats API final scores. Signal outcomes use estimated odds (+450 tie, -110 under, -130 ML fav).'
            : 'Model picks pulled from predictions pipeline. P&L shown in units.'
          }{' '}
          Past results do not guarantee future performance. Gamble responsibly.
        </div>

      </div>
    </div>
  );
}

export default DailyRecap;
