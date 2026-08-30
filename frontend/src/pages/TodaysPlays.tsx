/**
 * Today's Plays — Pregame Handicapping Expert Agent
 *
 * Surfaces FAVORABLE_LEAN and STRONG_LEAN evaluations for today's games.
 * Best Bet of the day gets a highlighted hero card at the top.
 * Game scripts are written in first-person expert handicapper voice.
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { RefreshCw, Star, Trophy, TrendingUp, BookOpen, Zap } from 'lucide-react';
import { fetchTodayEvaluations, fetchEvaluationRecord, fetchPersonaLeans } from '../api/evaluations';
import type { Evaluation, AtsRecord, PersonaLean } from '../api/evaluations';
import '../styles/analytics.css';

const F5_BASE = import.meta.env.DEV ? 'http://localhost:8889/api/f5' : '/api/f5';

// ── Design tokens (matches analytics.css palette) ────────────────────────────
const EMERALD   = 'oklch(69.6% .17 162.48)';
const GOLD      = 'oklch(79.5% .184 86.047)';
const BLUE      = 'oklch(62.3% .214 259.815)';
const BRAND_RED = 'oklch(63.7% .237 25.331)';
const MUTED     = 'oklch(70.8% 0 0)';
const CARD_BG   = 'oklch(24% 0 0)';
const BORDER    = 'oklch(100% 0 0 / .1)';

const SPORTS = ['ALL', 'NFL', 'CFB', 'MLB', 'NBA', 'NHL', 'NCAAB'];

function leanColor(level: string): string {
  if (level === 'strong_lean')    return GOLD;
  if (level === 'favorable_lean') return EMERALD;
  return MUTED;
}

function leanLabel(level: string): string {
  if (level === 'strong_lean')    return 'STRONG LEAN';
  if (level === 'favorable_lean') return 'FAVORABLE LEAN';
  if (level === 'slight_lean')    return 'SLIGHT LEAN';
  return 'NO EDGE';
}

function fmtOdds(odds: number | null): string {
  if (odds == null) return '—';
  return odds >= 0 ? `+${odds}` : `${odds}`;
}

function fmtTime(iso: string | null): string {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleTimeString('en-US', {
      hour: 'numeric', minute: '2-digit', timeZone: 'America/Chicago',
    }) + ' CST';
  } catch { return ''; }
}

function fmtBook(book: string | null): string {
  if (!book) return '';
  return book.replace(/([A-Z])/g, ' $1').trim().toUpperCase();
}

// ── Stat chip ─────────────────────────────────────────────────────────────────
function Chip({ label, value, color = MUTED }: { label: string; value: string; color?: string }) {
  return (
    <span style={{
      display: 'inline-flex', flexDirection: 'column', alignItems: 'center',
      background: 'oklch(30% 0 0)', borderRadius: 5, padding: '4px 10px', gap: 1,
      border: `1px solid ${BORDER}`,
    }}>
      <span style={{ fontSize: '0.75rem', fontWeight: 800, color, fontFamily: 'monospace' }}>{value}</span>
      <span style={{ fontSize: '0.55rem', color: MUTED, letterSpacing: '0.06em' }}>{label}</span>
    </span>
  );
}

// ── Persona convergence bar ───────────────────────────────────────────────────
const PERSONA_LABELS: Record<string, string> = {
  the_sharp:            'SHARP',
  the_statistician:     'STATS',
  the_situationalist:   'SPOT',
  the_matchup_analyst:  'MATCHUP',
  the_totals_specialist:'TOTALS',
};

function PersonaBar({ lean }: { lean: PersonaLean }) {
  const fired = lean.persona_results.filter(p => p.fired && p.lean_level !== 'no_edge');
  if (!fired.length) return null;

  return (
    <div style={{ marginTop: 14 }}>
      <div style={{
        fontSize: '0.62rem', fontWeight: 800, letterSpacing: '0.08em',
        color: MUTED, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6,
      }}>
        <Zap size={10} /> PERSONA CONSENSUS ({lean.convergence_count}/5 agree)
      </div>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
        {lean.persona_results.map(p => {
          const hasLean = p.fired && p.lean_level !== 'no_edge';
          const agreesWithConsensus = hasLean
            && p.lean_side === lean.consensus_side
            && p.lean_market === lean.consensus_market;
          const dotColor = !p.fired ? 'oklch(30% 0 0)'
            : agreesWithConsensus ? EMERALD
            : hasLean ? GOLD
            : MUTED;
          return (
            <div key={p.persona} title={p.reasoning} style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3,
              cursor: 'default',
            }}>
              <div style={{
                width: 10, height: 10, borderRadius: '50%',
                background: dotColor,
                border: agreesWithConsensus ? `1px solid ${EMERALD}` : '1px solid oklch(40% 0 0)',
              }} />
              <span style={{ fontSize: '0.5rem', color: MUTED, fontWeight: 700 }}>
                {PERSONA_LABELS[p.persona] ?? p.persona.toUpperCase().replace('THE_', '')}
              </span>
            </div>
          );
        })}
        {lean.dissent_flag && (
          <span style={{
            fontSize: '0.6rem', color: GOLD, fontStyle: 'italic',
            display: 'flex', alignItems: 'center', marginLeft: 4,
          }}>
            ⚠ split
          </span>
        )}
      </div>
      {lean.convergence_note && (
        <div style={{ fontSize: '0.72rem', color: MUTED, fontStyle: 'italic' }}>
          {lean.convergence_note}
        </div>
      )}
    </div>
  );
}

// ── Single evaluation card ────────────────────────────────────────────────────
function EvalCard({ ev, isBestBet, personaLean }: {
  ev: Evaluation;
  isBestBet: boolean;
  personaLean?: PersonaLean;
}) {
  const [expanded, setExpanded] = useState(isBestBet);
  const [matchupLoading, setMatchupLoading] = useState(false);
  const navigate = useNavigate();
  const color  = leanColor(ev.lean_level);
  const border = isBestBet
    ? `2px solid ${GOLD}`
    : `1px solid ${ev.lean_level === 'strong_lean' ? color + ' / .4' : BORDER}`;

  return (
    <div
      onClick={() => setExpanded(e => !e)}
      style={{
        background: isBestBet ? 'oklch(26% 0.015 86)' : CARD_BG,
        border,
        borderRadius: 10,
        padding: '16px 20px',
        cursor: 'pointer',
        transition: 'border-color 0.15s',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Best bet badge */}
      {isBestBet && (
        <div style={{
          position: 'absolute', top: 0, right: 0,
          background: GOLD, color: 'oklch(15% 0 0)',
          fontSize: '0.62rem', fontWeight: 900, letterSpacing: '0.08em',
          padding: '3px 10px', borderBottomLeftRadius: 8,
        }}>
          ★ BEST BET
        </div>
      )}

      {/* Header */}
      <div>
        {/* Sport + lean label + time badges */}
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4, flexWrap: 'wrap' }}>
          <span style={{
            fontSize: '0.62rem', fontWeight: 800, letterSpacing: '0.1em',
            color: 'oklch(15% 0 0)', background: color,
            padding: '2px 7px', borderRadius: 4,
          }}>
            {ev.sport}
          </span>
          <span style={{
            fontSize: '0.62rem', fontWeight: 700, letterSpacing: '0.06em',
            color, background: `${color} / .12`, border: `1px solid ${color} / .3`,
            padding: '2px 7px', borderRadius: 4,
          }}>
            {leanLabel(ev.lean_level)}
          </span>
          {ev.opus_verdict === 'PASS' && ev.lean_level === 'strong_lean' && (
            <span style={{
              fontSize: '0.62rem', fontWeight: 800, letterSpacing: '0.06em',
              color: EMERALD, border: `1px solid ${EMERALD} / .4`,
              padding: '2px 7px', borderRadius: 4,
            }}>
              ✓ OPUS VERIFIED
            </span>
          )}
          {ev.game_time_cst && (
            <span style={{ fontSize: '0.65rem', color: MUTED, marginLeft: 2 }}>
              {fmtTime(ev.game_time_cst)}
            </span>
          )}
        </div>

        {/* Matchup */}
        <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--foreground)', lineHeight: 1.2 }}>
          {ev.away_team} @ {ev.home_team}
        </div>

        {/* Lean side */}
        {ev.lean_side && (
          <div style={{ fontSize: '0.9rem', fontWeight: 700, color, marginTop: 4 }}>
            {ev.lean_side.toUpperCase()}
          </div>
        )}

        {/* Stats chips — own row below matchup, never overlaps */}
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginTop: 12 }}>
          <Chip label="UNITS"  value={ev.unit_rec > 0 ? `${ev.unit_rec}u` : '—'} color={color} />
          {ev.best_book && (
            <Chip label="BEST BOOK" value={fmtBook(ev.best_book)} color={BLUE} />
          )}
          {ev.best_odds != null && (
            <Chip label="ODDS" value={fmtOdds(ev.best_odds)} color={ev.best_odds > 0 ? EMERALD : MUTED} />
          )}
          {ev.best_line != null && (
            <Chip label="LINE" value={ev.best_line > 0 ? `+${ev.best_line}` : `${ev.best_line}`} />
          )}
        </div>

        {/* Matchup Center link — NFL only */}
        {ev.sport === 'NFL' && (
          <div style={{ marginTop: 10 }}>
            <button
              disabled={matchupLoading}
              onClick={async (e) => {
                e.stopPropagation();
                setMatchupLoading(true);
                try {
                  const res = await fetch(
                    `${F5_BASE}/matchup-lookup?home=${encodeURIComponent(ev.home_team)}&away=${encodeURIComponent(ev.away_team)}`
                  );
                  if (res.ok) {
                    const data = await res.json();
                    navigate(`/matchup/${data.event_id}`);
                  }
                } finally {
                  setMatchupLoading(false);
                }
              }}
              style={{
                background: 'transparent',
                border: `1px solid ${BLUE}55`,
                color: BLUE,
                borderRadius: 4,
                padding: '3px 10px',
                cursor: matchupLoading ? 'wait' : 'pointer',
                fontSize: '0.62rem',
                fontWeight: 800,
                letterSpacing: '0.06em',
                opacity: matchupLoading ? 0.6 : 1,
              }}
            >
              {matchupLoading ? 'LOADING…' : 'MATCHUP CENTER →'}
            </button>
          </div>
        )}
      </div>

      {/* Expandable body */}
      {expanded && (
        <div style={{ marginTop: 16, borderTop: `1px solid ${BORDER}`, paddingTop: 14 }}>
          {/* Game script */}
          {ev.game_script && (
            <div style={{ marginBottom: 12 }}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 6,
                fontSize: '0.65rem', fontWeight: 800, letterSpacing: '0.08em',
                color: MUTED, marginBottom: 6,
              }}>
                <BookOpen size={11} /> EXPERT ANALYSIS
              </div>
              <p style={{
                fontSize: '0.88rem', lineHeight: 1.6, color: 'var(--foreground)',
                margin: 0, fontStyle: 'italic',
              }}>
                "{ev.game_script}"
              </p>
            </div>
          )}

          {/* Signals used */}
          {ev.signals_used.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{
                fontSize: '0.62rem', fontWeight: 800, letterSpacing: '0.08em',
                color: MUTED, marginBottom: 6,
              }}>
                SIGNALS
              </div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {ev.signals_used.map(s => (
                  <span key={s} style={{
                    fontSize: '0.65rem', fontWeight: 700,
                    background: 'oklch(30% 0 0)', border: `1px solid ${BORDER}`,
                    borderRadius: 4, padding: '2px 8px', color: 'var(--foreground)',
                  }}>
                    {s.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Confidence note */}
          {ev.confidence_note && (
            <div style={{ fontSize: '0.75rem', color: MUTED, fontStyle: 'italic' }}>
              ⚠ {ev.confidence_note}
            </div>
          )}

          {/* Persona convergence */}
          {personaLean && <PersonaBar lean={personaLean} />}
        </div>
      )}

      {/* Expand indicator */}
      {!expanded && ev.game_script && (
        <div style={{ marginTop: 8, fontSize: '0.65rem', color: MUTED }}>
          Click to read full analysis →
        </div>
      )}
    </div>
  );
}

// ── ATS record row ────────────────────────────────────────────────────────────
function RecordRow({ r }: { r: AtsRecord }) {
  const pct = parseFloat(r.win_rate) || 0;
  const color = pct >= 55 ? EMERALD : pct >= 50 ? GOLD : pct > 0 ? BRAND_RED : MUTED;
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '120px 60px 80px 70px 60px',
      gap: 8, padding: '8px 0', borderBottom: `1px solid ${BORDER}`,
      fontSize: '0.8rem', alignItems: 'center',
    }}>
      <span style={{ color: leanColor(r.lean_level), fontWeight: 700, fontSize: '0.7rem' }}>
        {leanLabel(r.lean_level)}
      </span>
      <span style={{ color: MUTED }}>{r.sport}</span>
      <span style={{ fontWeight: 800, fontFamily: 'monospace' }}>{r.record}</span>
      <span style={{ fontWeight: 800, color, fontFamily: 'monospace' }}>{r.win_rate}</span>
      <span style={{ color: MUTED }}>{r.graded}/{r.total}</span>
    </div>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────
export function TodaysPlays() {
  const [sport, setSport]           = useState('ALL');
  const [evals, setEvals]           = useState<Evaluation[]>([]);
  const [bestBetId, setBestBetId]   = useState<number | null>(null);
  const [record, setRecord]         = useState<AtsRecord[]>([]);
  const [personaMap, setPersonaMap] = useState<Record<string, PersonaLean>>({});
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState<string | null>(null);
  const [generatedAt, setGeneratedAt] = useState<string>('');
  const [activeTab, setActiveTab]   = useState<'plays' | 'record'>('plays');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const sportParam = sport === 'ALL' ? undefined : sport;
      const [evData, recData, personaData] = await Promise.all([
        fetchTodayEvaluations(sportParam, 'favorable_lean'),
        fetchEvaluationRecord(sportParam, 30),
        fetchPersonaLeans().catch(() => ({ date: '', count: 0, games: [] })),
      ]);
      setEvals(evData.evaluations);
      setBestBetId(evData.best_bet_id);
      setGeneratedAt(evData.generated_at);
      setRecord(recData.record);
      const pmap: Record<string, PersonaLean> = {};
      for (const g of personaData.games) pmap[g.game_id] = g;
      setPersonaMap(pmap);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load evaluations');
    } finally {
      setLoading(false);
    }
  }, [sport]);

  useEffect(() => { load(); }, [load]);

  const strongLeans    = evals.filter(e => e.lean_level === 'strong_lean');
  const favorableLeans = evals.filter(e => e.lean_level === 'favorable_lean');

  const tabBtn = (tab: 'plays' | 'record', label: string, icon: React.ReactNode) => (
    <button
      onClick={() => setActiveTab(tab)}
      style={{
        display: 'flex', alignItems: 'center', gap: 6,
        padding: '6px 14px', borderRadius: 6, border: 'none',
        background: activeTab === tab ? 'oklch(30% 0 0)' : 'transparent',
        color: activeTab === tab ? 'var(--foreground)' : MUTED,
        fontSize: '0.72rem', fontWeight: 800, letterSpacing: '0.06em',
        cursor: 'pointer',
      }}
    >
      {icon} {label}
    </button>
  );

  return (
    <div className="analytics-page">
      {/* Header */}
      <div className="analytics-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Star size={22} style={{ color: GOLD }} />
              Today's Plays
            </h1>
            <p className="subtitle">
              Expert pregame handicapping — Favorable & Strong lean plays only
            </p>
          </div>
          <button
            onClick={load}
            disabled={loading}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '7px 14px', borderRadius: 6,
              background: 'var(--muted)', border: '1px solid var(--border)',
              color: 'var(--foreground)', fontSize: '0.75rem', fontWeight: 700,
              cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.5 : 1,
            }}
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            {loading ? 'LOADING...' : 'REFRESH'}
          </button>
        </div>

        {/* Sport filter */}
        <div style={{ display: 'flex', gap: 6, marginTop: 12, flexWrap: 'wrap' }}>
          {SPORTS.map(s => (
            <button
              key={s}
              onClick={() => setSport(s)}
              style={{
                padding: '5px 12px', borderRadius: 5, border: 'none',
                background: sport === s ? GOLD : 'oklch(30% 0 0)',
                color: sport === s ? 'oklch(15% 0 0)' : MUTED,
                fontSize: '0.7rem', fontWeight: 800, letterSpacing: '0.06em',
                cursor: 'pointer',
              }}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Summary stats */}
        {!loading && !error && (
          <div style={{ display: 'flex', gap: 12, marginTop: 12, flexWrap: 'wrap' }}>
            {[
              { label: 'STRONG LEANS', value: strongLeans.length.toString(),    color: GOLD },
              { label: 'FAVORABLE',    value: favorableLeans.length.toString(), color: EMERALD },
              { label: 'TOTAL PLAYS',  value: evals.length.toString(),          color: BLUE },
            ].map(s => (
              <div key={s.label} style={{
                background: CARD_BG, border: `1px solid ${BORDER}`, borderRadius: 7,
                padding: '8px 16px', display: 'flex', flexDirection: 'column', gap: 2,
              }}>
                <span style={{ fontSize: '1.1rem', fontWeight: 900, color: s.color, fontFamily: 'monospace' }}>
                  {s.value}
                </span>
                <span style={{ fontSize: '0.6rem', color: MUTED, letterSpacing: '0.08em', fontWeight: 700 }}>
                  {s.label}
                </span>
              </div>
            ))}
            {generatedAt && (
              <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                <span style={{ fontSize: '0.65rem', color: MUTED }}>
                  Last run: {new Date(generatedAt).toLocaleTimeString('en-US', { timeZone: 'America/Chicago', hour: 'numeric', minute: '2-digit' })} CST
                </span>
              </div>
            )}
          </div>
        )}

        {/* Tab bar */}
        <div style={{ display: 'flex', gap: 4, marginTop: 14, borderBottom: `1px solid ${BORDER}`, paddingBottom: 8 }}>
          {tabBtn('plays',  "TODAY'S PLAYS",  <Zap size={12} />)}
          {tabBtn('record', 'ATS RECORD',     <Trophy size={12} />)}
        </div>
      </div>

      {/* Body */}
      {error && (
        <div style={{
          background: `${BRAND_RED} / .12`, border: `1px solid ${BRAND_RED} / .3`,
          borderRadius: 8, padding: '12px 16px', color: BRAND_RED, fontSize: '0.85rem',
        }}>
          {error}
        </div>
      )}

      {loading && (
        <div style={{ textAlign: 'center', color: MUTED, padding: 40 }}>
          <RefreshCw size={20} className="animate-spin" style={{ margin: '0 auto 8px' }} />
          <p style={{ margin: 0, fontSize: '0.85rem' }}>Loading evaluations...</p>
        </div>
      )}

      {!loading && !error && activeTab === 'plays' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {evals.length === 0 ? (
            <div style={{
              textAlign: 'center', padding: 48, color: MUTED,
              background: CARD_BG, border: `1px solid ${BORDER}`, borderRadius: 10,
            }}>
              <TrendingUp size={28} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
              <p style={{ margin: 0 }}>No qualifying plays today.</p>
              <p style={{ margin: '6px 0 0', fontSize: '0.8rem', opacity: 0.7 }}>
                The engine evaluates every game — most games are no-edge. Check back after 8am CST.
              </p>
            </div>
          ) : (
            <>
              {strongLeans.length > 0 && (
                <div>
                  <div style={{
                    fontSize: '0.65rem', fontWeight: 800, letterSpacing: '0.1em',
                    color: GOLD, marginBottom: 8,
                  }}>
                    STRONG LEANS
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {strongLeans.map(ev => (
                      <EvalCard key={ev.id} ev={ev} isBestBet={ev.id === bestBetId} personaLean={personaMap[ev.game_id]} />
                    ))}
                  </div>
                </div>
              )}

              {favorableLeans.length > 0 && (
                <div style={{ marginTop: strongLeans.length > 0 ? 16 : 0 }}>
                  <div style={{
                    fontSize: '0.65rem', fontWeight: 800, letterSpacing: '0.1em',
                    color: EMERALD, marginBottom: 8,
                  }}>
                    FAVORABLE LEANS
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {favorableLeans.map(ev => (
                      <EvalCard key={ev.id} ev={ev} isBestBet={ev.id === bestBetId} personaLean={personaMap[ev.game_id]} />
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {!loading && !error && activeTab === 'record' && (
        <div style={{ background: CARD_BG, border: `1px solid ${BORDER}`, borderRadius: 10, padding: '16px 20px' }}>
          <div style={{
            fontSize: '0.65rem', fontWeight: 800, letterSpacing: '0.1em',
            color: MUTED, marginBottom: 12,
          }}>
            ATS RECORD — LAST 30 DAYS (GRADED PLAYS ONLY)
          </div>
          {record.length === 0 ? (
            <p style={{ color: MUTED, fontSize: '0.85rem', margin: 0 }}>
              No graded plays yet. Record will populate as games conclude.
            </p>
          ) : (
            <>
              <div style={{
                display: 'grid', gridTemplateColumns: '120px 60px 80px 70px 60px',
                gap: 8, padding: '0 0 8px', borderBottom: `1px solid ${BORDER}`,
                fontSize: '0.62rem', color: MUTED, fontWeight: 800, letterSpacing: '0.06em',
              }}>
                <span>LEAN LEVEL</span>
                <span>SPORT</span>
                <span>RECORD</span>
                <span>WIN %</span>
                <span>GRADED</span>
              </div>
              {record.map((r, i) => <RecordRow key={i} r={r} />)}
            </>
          )}
        </div>
      )}
    </div>
  );
}
/* cache-bust Wed Aug  5 08:50:23 CDT 2026 */
