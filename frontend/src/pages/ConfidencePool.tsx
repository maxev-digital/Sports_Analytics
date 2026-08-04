/**
 * NFL Confidence Pool — Week-by-week game ranker.
 * Model assigns confidence points 1–16 using Walters power rating differential,
 * ATS trends, and situational flags. Users copy rankings into their pool entry.
 */
import { useState, useEffect, useCallback } from 'react';
import '../styles/analytics.css';

const F5_BASE = import.meta.env.DEV ? 'http://localhost:8889/api/f5' : '/api/f5';

const EMERALD   = 'oklch(69.6% .17 162.48)';
const BRAND_RED = 'oklch(63.7% .237 25.331)';
const BLUE      = 'oklch(62.3% .214 259.815)';
const YELLOW    = 'oklch(79.5% .184 86.047)';
const MUTED_FG  = 'oklch(70.8% 0 0)';
const BORDER    = 'oklch(100% 0 0 / .1)';
const CARD_BG   = 'oklch(22% 0 0)';
const FG        = 'oklch(95% 0 0)';

const NFL_WEEKS = Array.from({ length: 18 }, (_, i) => i + 1);

interface ModelPick {
  pick: string;
  side: 'HOME' | 'AWAY';
  reasoning: string;
}

interface PoolGame {
  home: string;
  away: string;
  home_name: string;
  away_name: string;
  date: string;
  home_rating: number;
  away_rating: number;
  rating_diff: number;
  home_ats_pct: number;
  away_ats_pct: number;
  home_ats_record: string;
  away_ats_record: string;
  situational_flags: string[];
  raw_score: number;
  confidence_points: number;
  model_pick: ModelPick;
}

interface PoolData {
  week: number;
  game_count: number;
  week_start: string;
  week_end: string;
  method: string;
  games: PoolGame[];
}

function confidenceColor(pts: number, total: number): string {
  const pct = pts / total;
  if (pct >= 0.75) return EMERALD;
  if (pct >= 0.5)  return BLUE;
  if (pct >= 0.25) return YELLOW;
  return BRAND_RED;
}

function ConfidenceBadge({ pts, total }: { pts: number; total: number }) {
  const color = confidenceColor(pts, total);
  return (
    <div style={{
      width: 44, height: 44, borderRadius: '50%',
      background: `color-mix(in oklch, ${color} 18%, transparent)`,
      border: `2px solid ${color}`,
      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
    }}>
      <span style={{ fontSize: '0.9rem', fontWeight: 900, color, fontFamily: 'monospace' }}>{pts}</span>
    </div>
  );
}

function GameRow({ game, total, rank }: { game: PoolGame; total: number; rank: number }) {
  const [expanded, setExpanded] = useState(false);
  const pick = game.model_pick;
  const pickIsHome = pick.side === 'HOME';
  const gameDate = game.date ? new Date(game.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }) : '';

  return (
    <div style={{ background: CARD_BG, border: `1px solid ${BORDER}`, borderRadius: 6, overflow: 'hidden' }}>
      <div
        onClick={() => setExpanded(e => !e)}
        style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', cursor: 'pointer', userSelect: 'none' }}
      >
        {/* Confidence badge */}
        <ConfidenceBadge pts={game.confidence_points} total={total} />

        {/* Matchup */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span style={{
              fontSize: '0.85rem', fontWeight: 800, color: pickIsHome ? MUTED_FG : FG,
            }}>
              {game.away_name}
            </span>
            <span style={{ fontSize: '0.7rem', color: MUTED_FG }}>@</span>
            <span style={{
              fontSize: '0.85rem', fontWeight: 800, color: pickIsHome ? FG : MUTED_FG,
            }}>
              {game.home_name}
            </span>
          </div>
          <div style={{ fontSize: '0.68rem', color: MUTED_FG, marginTop: 2 }}>{gameDate}</div>
        </div>

        {/* Model pick */}
        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <div style={{
            fontSize: '0.7rem', fontWeight: 800, color: EMERALD,
            background: 'color-mix(in oklch, oklch(69.6% .17 162.48) 12%, transparent)',
            border: `1px solid color-mix(in oklch, oklch(69.6% .17 162.48) 30%, transparent)`,
            borderRadius: 4, padding: '2px 8px', display: 'inline-block',
          }}>
            {pick.pick} {pick.side}
          </div>
          <div style={{ fontSize: '0.62rem', color: MUTED_FG, marginTop: 3 }}>
            Model pick
          </div>
        </div>

        {/* Situational flags */}
        {game.situational_flags.length > 0 && (
          <div style={{
            fontSize: '0.6rem', color: YELLOW, fontWeight: 700,
            background: 'color-mix(in oklch, oklch(79.5% .184 86.047) 10%, transparent)',
            border: `1px solid color-mix(in oklch, oklch(79.5% .184 86.047) 25%, transparent)`,
            borderRadius: 4, padding: '2px 6px', flexShrink: 0,
          }}>
            {game.situational_flags[0]}
          </div>
        )}

        <span style={{ color: MUTED_FG, fontSize: '0.75rem', flexShrink: 0 }}>{expanded ? '▲' : '▼'}</span>
      </div>

      {expanded && (
        <div style={{ borderTop: `1px solid ${BORDER}`, padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {/* Rating detail */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: 8, alignItems: 'center' }}>
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: '0.65rem', color: MUTED_FG, marginBottom: 2 }}>{game.away_name}</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 900, color: !pickIsHome ? EMERALD : MUTED_FG, fontFamily: 'monospace' }}>
                {game.away_rating > 0 ? '+' : ''}{game.away_rating.toFixed(1)}
              </div>
              <div style={{ fontSize: '0.62rem', color: MUTED_FG }}>ATS {game.away_ats_record}</div>
            </div>
            <div style={{ textAlign: 'center', fontSize: '0.65rem', color: MUTED_FG }}>
              <div>WALTERS</div>
              <div style={{ fontSize: '0.7rem', color: BLUE, fontWeight: 700 }}>
                {Math.abs(game.rating_diff).toFixed(1)} pt edge
              </div>
              <div>+2.5 HFA</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.65rem', color: MUTED_FG, marginBottom: 2 }}>{game.home_name}</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 900, color: pickIsHome ? EMERALD : MUTED_FG, fontFamily: 'monospace' }}>
                {game.home_rating > 0 ? '+' : ''}{game.home_rating.toFixed(1)}
              </div>
              <div style={{ fontSize: '0.62rem', color: MUTED_FG }}>ATS {game.home_ats_record}</div>
            </div>
          </div>

          {/* Reasoning */}
          <div style={{
            fontSize: '0.72rem', color: MUTED_FG, padding: '8px 12px',
            background: 'oklch(18% 0 0)', borderRadius: 4, lineHeight: 1.5,
          }}>
            <span style={{ color: EMERALD, fontWeight: 700 }}>Model: </span>{pick.reasoning}
          </div>

          {/* All situational flags */}
          {game.situational_flags.length > 0 && (
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {game.situational_flags.map((f, i) => (
                <span key={i} style={{
                  fontSize: '0.62rem', color: YELLOW, fontWeight: 700,
                  background: 'color-mix(in oklch, oklch(79.5% .184 86.047) 10%, transparent)',
                  border: `1px solid color-mix(in oklch, oklch(79.5% .184 86.047) 25%, transparent)`,
                  borderRadius: 4, padding: '2px 8px',
                }}>
                  ⚑ {f}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function CopyButton({ games }: { games: PoolGame[] }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const lines = games.map(g =>
      `${g.confidence_points} pts — ${g.model_pick.pick} (${g.away_name} @ ${g.home_name})`
    ).join('\n');
    const text = `MAX EV NFL Confidence Pool Picks\n${'─'.repeat(40)}\n${lines}`;
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <button
      onClick={handleCopy}
      style={{
        padding: '6px 14px', borderRadius: 6, fontSize: '0.75rem', fontWeight: 700,
        background: copied
          ? 'color-mix(in oklch, oklch(69.6% .17 162.48) 15%, transparent)'
          : 'oklch(28% 0 0)',
        border: `1px solid ${copied ? EMERALD : BORDER}`,
        color: copied ? EMERALD : MUTED_FG, cursor: 'pointer', transition: 'all 0.15s',
      }}
    >
      {copied ? '✓ COPIED' : 'COPY PICKS'}
    </button>
  );
}

export function ConfidencePool() {
  const [week, setWeek] = useState(1);
  const [data, setData] = useState<PoolData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWeek = useCallback(async (w: number) => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`${F5_BASE}/confidence-pool?week=${w}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setData(await r.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchWeek(week); }, [week, fetchWeek]);

  const games = data?.games ?? [];

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1>NFL Confidence Pool</h1>
            <p className="subtitle">
              Model-ranked picks for Week {week} — assign the top games your highest confidence points
            </p>
          </div>
          {data && games.length > 0 && <CopyButton games={games} />}
        </div>

        {/* Method note */}
        <div style={{
          fontSize: '0.68rem', color: MUTED_FG, marginBottom: 12,
          padding: '6px 12px', background: 'oklch(20% 0 0)', borderRadius: 4,
          border: `1px solid ${BORDER}`, display: 'inline-block',
        }}>
          Ranked by: Walters power rating differential (11 seasons) + 2.5 pt home field + ATS trend + situational flags
        </div>

        {/* Week selector */}
        <div className="sport-tabs" style={{ flexWrap: 'wrap' }}>
          {NFL_WEEKS.map(w => (
            <button
              key={w}
              className={`sport-tab ${week === w ? 'active' : ''}`}
              onClick={() => setWeek(w)}
            >
              WK {w}
            </button>
          ))}
        </div>
      </div>

      <div style={{ padding: '16px 24px', maxWidth: 900 }}>
        {/* Legend */}
        <div style={{ display: 'flex', gap: 16, marginBottom: 16, flexWrap: 'wrap' }}>
          {[
            { range: '13–16', color: EMERALD, label: 'High confidence' },
            { range: '9–12',  color: BLUE,    label: 'Medium-high' },
            { range: '5–8',   color: YELLOW,  label: 'Toss-up' },
            { range: '1–4',   color: BRAND_RED, label: 'Low — risky assignment' },
          ].map(l => (
            <div key={l.range} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: l.color }} />
              <span style={{ fontSize: '0.68rem', color: MUTED_FG }}>
                <span style={{ color: l.color, fontWeight: 700 }}>{l.range} pts</span> — {l.label}
              </span>
            </div>
          ))}
        </div>

        {/* Week date range */}
        {data && (
          <div style={{ fontSize: '0.72rem', color: MUTED_FG, marginBottom: 12 }}>
            {data.game_count} games &nbsp;·&nbsp;
            {data.week_start && new Date(data.week_start).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            {data.week_end && data.week_end !== data.week_start &&
              ` – ${new Date(data.week_end).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`
            }
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{
            padding: '12px 16px', borderRadius: 6, marginBottom: 16,
            background: 'color-mix(in oklch, oklch(63.7% .237 25.331) 12%, transparent)',
            border: `1px solid color-mix(in oklch, oklch(63.7% .237 25.331) 35%, transparent)`,
            fontSize: '0.8rem', color: BRAND_RED,
          }}>
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div style={{ textAlign: 'center', padding: 40, color: MUTED_FG, fontSize: '0.85rem' }}>
            Loading Week {week} games...
          </div>
        )}

        {/* Games list */}
        {!loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {games.map((game, i) => (
              <GameRow key={`${game.home}-${game.away}`} game={game} total={games.length} rank={i + 1} />
            ))}
          </div>
        )}

        {/* How to use */}
        {!loading && games.length > 0 && (
          <div style={{
            marginTop: 20, padding: '12px 16px', borderRadius: 6,
            background: 'oklch(20% 0 0)', border: `1px solid ${BORDER}`,
            fontSize: '0.7rem', color: MUTED_FG, lineHeight: 1.7,
          }}>
            <span style={{ color: FG, fontWeight: 700 }}>How to use: </span>
            The model assigns 16 points to the game it's most confident about and 1 point to the least certain.
            Copy these into your pool entry as-is, or adjust based on your own knowledge.
            <span style={{ color: YELLOW }}> Yellow flags</span> indicate situational factors that affect confidence (home dog spot, short week, etc.).
            Ratings update weekly using the Walters method — 90% prior + 10% new game result.
          </div>
        )}
      </div>
    </div>
  );
}

export default ConfidencePool;
