import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getApiUrl } from '../config';

// ── Design tokens (matching MaxEvEdges.tsx / SystemHealth.tsx) ─────────────
const BRAND_RED  = 'oklch(63.7% .237 25.331)';
const EMERALD    = 'oklch(69.6% .17 162.48)';
const BLUE       = 'oklch(62.3% .214 259.815)';
const YELLOW     = 'oklch(79.5% .184 86.047)';
const MUTED_FG   = 'oklch(70.8% 0 0)';
const BORDER     = 'oklch(100% 0 0 / .1)';
const SURFACE    = 'oklch(15.6% 0 0)';

// ── Types ──────────────────────────────────────────────────────────────────
interface Candidate {
  id: number;
  detector: string;
  market_ticker: string;
  sport: string;
  game_id: string | null;
  true_probability: number;
  kalshi_price_cents: number;
  raw_edge_pct: number;
  net_edge_pct: number;
  books_sampled: number;
  detected_at: string;
  order_status: string | null;   // null = never executed
  order_contracts: number | null;
}

interface MarketRow {
  market_ticker: string;
  event_ticker: string | null;
  title: string | null;
  yes_sub_title: string | null;
  sport: string;
  kalshi_price_cents: number | null;
  expected_expiration_time: string | null;
  already_started: boolean;
  matched: boolean;
  true_probability: number | null;
  raw_edge_pct: number | null;
  net_edge_pct: number | null;
  books_sampled: number;
}

interface Position {
  ticker: string;
  contracts: number;
  exposure_cents: number;
  realized_pnl_cents: number;
  fees_paid_cents: number;
  last_updated_ts: string;
}

const SPORT_LABELS: Record<string, string> = {
  baseball_mlb: 'MLB',
  basketball_wnba: 'WNBA',
  basketball_nba: 'NBA',
  icehockey_nhl: 'NHL',
  americanfootball_nfl: 'NFL',
  tennis_atp: 'ATP',
  tennis_wta: 'WTA',
};

function sportLabel(sport: string): string {
  return SPORT_LABELS[sport] ?? sport.toUpperCase();
}

function fmtPct(v: number): string {
  return `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
}

function fmtCents(c: number): string {
  return `${(c / 100).toFixed(2)}¢`.replace('¢', 'c');
}

function fmtDollars(c: number): string {
  const sign = c < 0 ? '-' : '';
  return `${sign}$${(Math.abs(c) / 100).toFixed(2)}`;
}

function fmtTime(ts: string | null): string {
  if (!ts) return '—';
  try {
    const dt = new Date(ts);
    if (isNaN(dt.getTime())) return ts;
    return dt.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true });
  } catch {
    return ts;
  }
}

async function authedFetch(path: string, token: string | null, init?: RequestInit) {
  const resp = await fetch(getApiUrl(path), {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  return resp;
}

export function Kalshi() {
  const { token } = useAuth();

  const [connected, setConnected] = useState<boolean | null>(null);
  const [balanceCents, setBalanceCents] = useState<number | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [allGames, setAllGames] = useState<MarketRow[]>([]);
  const [loadingGames, setLoadingGames] = useState(false);
  const [supportedSports, setSupportedSports] = useState<string[]>([]);
  const [sportFilter, setSportFilter] = useState<string>('all');
  const [onlyOurPicks, setOnlyOurPicks] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [executingId, setExecutingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Connect form
  const [apiKeyId, setApiKeyId] = useState('');
  const [privateKeyPem, setPrivateKeyPem] = useState('');
  const [connecting, setConnecting] = useState(false);

  const loadAccount = useCallback(async () => {
    if (!token) return;
    try {
      const balResp = await authedFetch('kalshi/balance', token);
      if (balResp.status === 404) { setConnected(false); return; }
      if (!balResp.ok) { setConnected(false); return; }
      const bal = await balResp.json();
      setBalanceCents(bal.balance_cents);
      setConnected(true);
      const posResp = await authedFetch('kalshi/positions', token);
      if (posResp.ok) {
        const pos = await posResp.json();
        setPositions(pos.positions ?? []);
      }
    } catch {
      setConnected(false);
    }
  }, [token]);

  const loadCandidates = useCallback(async () => {
    if (!token) return;
    const params = new URLSearchParams();
    if (sportFilter !== 'all') params.set('sport', sportFilter);
    if (onlyOurPicks) params.set('only_our_picks', 'true');
    try {
      const resp = await authedFetch(`kalshi/candidates?${params.toString()}`, token);
      if (resp.ok) {
        const data = await resp.json();
        setCandidates(data.candidates ?? []);
      }
    } catch {
      // leave existing candidates in place on transient failure
    }
  }, [token, sportFilter, onlyOurPicks]);

  const loadAllGames = useCallback(async () => {
    if (!token || sportFilter === 'all') { setAllGames([]); return; }
    setLoadingGames(true);
    try {
      const resp = await authedFetch(`kalshi/markets?sport=${encodeURIComponent(sportFilter)}`, token);
      if (resp.ok) {
        const data = await resp.json();
        setAllGames(data.markets ?? []);
      } else {
        setAllGames([]);
      }
    } catch {
      setAllGames([]);
    } finally {
      setLoadingGames(false);
    }
  }, [token, sportFilter]);

  const loadSports = useCallback(async () => {
    if (!token) return;
    try {
      const resp = await authedFetch('kalshi/sports', token);
      if (resp.ok) {
        const data = await resp.json();
        setSupportedSports(data.sports ?? []);
      }
    } catch {
      // non-critical - filter just won't list every sport
    }
  }, [token]);

  useEffect(() => {
    loadAccount();
    loadSports();
  }, [loadAccount, loadSports]);

  useEffect(() => {
    loadCandidates();
  }, [loadCandidates]);

  useEffect(() => {
    loadAllGames();
  }, [loadAllGames]);

  async function handleConnect(e: React.FormEvent) {
    e.preventDefault();
    setConnecting(true);
    setError(null);
    try {
      const resp = await authedFetch('kalshi/connect', token, {
        method: 'POST',
        body: JSON.stringify({ api_key_id: apiKeyId, private_key_pem: privateKeyPem, demo_mode: false }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        setError(data.detail ?? 'Could not connect Kalshi account');
      } else {
        setApiKeyId('');
        setPrivateKeyPem('');
        await loadAccount();
      }
    } catch {
      setError('Network error while connecting');
    } finally {
      setConnecting(false);
    }
  }

  async function handleScan() {
    setScanning(true);
    setError(null);
    try {
      await authedFetch('kalshi/detect', token, { method: 'POST' });
      // Detection runs in the background (a full scan takes longer than the
      // proxy timeout) - poll a few times rather than assume it's instant.
      for (let i = 0; i < 6; i++) {
        await new Promise(r => setTimeout(r, 5000));
        await loadCandidates();
      }
    } finally {
      setScanning(false);
    }
  }

  async function handleExecute(candidateId: number) {
    setExecutingId(candidateId);
    setError(null);
    try {
      const resp = await authedFetch('kalshi/execute', token, {
        method: 'POST',
        body: JSON.stringify({ candidate_edge_id: candidateId, contracts: 1 }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        setError(data.detail ?? 'Execution failed');
      } else {
        await Promise.all([loadCandidates(), loadAccount()]);
      }
    } catch {
      setError('Network error while executing');
    } finally {
      setExecutingId(null);
    }
  }

  return (
    <div style={{ padding: '24px 20px', maxWidth: 1200, margin: '0 auto' }}>
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ color: 'oklch(98.5% 0 0)', fontSize: '1.4rem', fontWeight: 900, margin: 0, letterSpacing: '-0.02em' }}>
            KALSHI
          </h1>
          <p style={{ color: MUTED_FG, fontSize: '0.78rem', margin: '4px 0 0' }}>
            Sharp-book vs Kalshi mispricing — every trade requires your confirmation
          </p>
        </div>
        {connected && (
          <div style={{ textAlign: 'right' }}>
            <div style={{ color: EMERALD, fontWeight: 800, fontSize: '1.1rem' }}>
              {balanceCents !== null ? fmtDollars(balanceCents) : '—'}
            </div>
            <div style={{ color: MUTED_FG, fontSize: '0.72rem' }}>account balance</div>
          </div>
        )}
      </div>

      {error && (
        <div style={{
          background: 'oklch(25% .08 25 / .4)', border: `1px solid ${BRAND_RED}`,
          borderRadius: 8, padding: '10px 14px', marginBottom: 16, color: BRAND_RED, fontSize: '0.85rem',
        }}>
          {error}
        </div>
      )}

      {/* ── Connect form (only if not connected) ──────────────────────── */}
      {connected === false && (
        <div className="data-table-wrap" style={{ padding: '20px', marginBottom: 20 }}>
          <p className="section-title" style={{ marginBottom: 12 }}>Connect Your Kalshi Account</p>
          <p style={{ color: MUTED_FG, fontSize: '0.8rem', marginBottom: 16 }}>
            Your API Key ID and private key are encrypted (AES-256-GCM) before being stored — never kept in plaintext.
          </p>
          <form onSubmit={handleConnect} style={{ display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 480 }}>
            <input
              type="text"
              placeholder="Kalshi API Key ID"
              value={apiKeyId}
              onChange={e => setApiKeyId(e.target.value)}
              required
              style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '10px 12px', color: 'oklch(98.5% 0 0)' }}
            />
            <textarea
              placeholder="-----BEGIN RSA PRIVATE KEY-----&#10;...&#10;-----END RSA PRIVATE KEY-----"
              value={privateKeyPem}
              onChange={e => setPrivateKeyPem(e.target.value)}
              required
              rows={6}
              style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '10px 12px', color: 'oklch(98.5% 0 0)', fontFamily: 'monospace', fontSize: '0.78rem' }}
            />
            <button
              type="submit"
              disabled={connecting}
              style={{
                background: connecting ? SURFACE : BRAND_RED, border: 'none', borderRadius: 8,
                padding: '10px 16px', color: '#fff', fontWeight: 700, cursor: connecting ? 'not-allowed' : 'pointer',
              }}
            >
              {connecting ? 'Verifying…' : 'Connect Account'}
            </button>
          </form>
        </div>
      )}

      {connected && (
        <>
          {/* ── Filter bar + scan button ───────────────────────────────── */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
              <button
                onClick={() => setSportFilter('all')}
                className={`filter-pill${sportFilter === 'all' ? ' active' : ''}`}
              >
                All
              </button>
              {supportedSports.map(s => (
                <button
                  key={s}
                  onClick={() => setSportFilter(s)}
                  className={`filter-pill${sportFilter === s ? ' active' : ''}`}
                >
                  {sportLabel(s)}
                </button>
              ))}
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 12, color: MUTED_FG, fontSize: '0.82rem', cursor: 'pointer' }}>
                <input type="checkbox" checked={onlyOurPicks} onChange={e => setOnlyOurPicks(e.target.checked)} />
                Only games we have picks for
              </label>
            </div>
            <button
              onClick={handleScan}
              disabled={scanning}
              style={{
                background: scanning ? SURFACE : BRAND_RED, border: `1px solid ${scanning ? BORDER : BRAND_RED}`,
                color: scanning ? MUTED_FG : '#fff', padding: '8px 16px', borderRadius: 8,
                fontSize: '0.8rem', fontWeight: 700, cursor: scanning ? 'not-allowed' : 'pointer',
              }}
            >
              {scanning ? 'Scanning…' : 'Scan for Edges'}
            </button>
          </div>

          {/* ── Key / how to read this page ─────────────────────────────── */}
          <div className="data-table-wrap" style={{ marginBottom: 24, padding: '14px 18px' }}>
            <p className="section-title" style={{ marginBottom: 10 }}>Key — How to Read This Page</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px 24px', fontSize: '0.8rem', color: MUTED_FG }}>
              <div><strong style={{ color: 'oklch(98.5% 0 0)' }}>Kalshi Price</strong> — cost right now to buy 1 YES contract on that team winning.</div>
              <div><strong style={{ color: 'oklch(98.5% 0 0)' }}>Sharp Prob</strong> — vig-removed consensus win probability from sharp books (Pinnacle primary; LowVig/BetOnline/Bovada as fallback coverage).</div>
              <div><strong style={{ color: 'oklch(98.5% 0 0)' }}>Edge</strong> — Sharp Prob minus Kalshi Price. <span style={{ color: EMERALD }}>Positive</span> = Kalshi underprices that team (buy it). <span style={{ color: BRAND_RED }}>Negative</span> = Kalshi overprices it (skip this row).</div>
              <div><strong style={{ color: 'oklch(98.5% 0 0)' }}>Two rows per game</strong> — Kalshi lists each side (each team) as its own separate YES contract, so every game appears twice: one row per team.</div>
              <div><strong style={{ color: 'oklch(98.5% 0 0)' }}>Pick</strong> — the team to buy YES on to exploit the edge, only shown when this row's edge is positive.</div>
              <div><strong style={{ color: 'oklch(98.5% 0 0)' }}>Books</strong> — how many sharp books had a usable line for this game (max 4).</div>
              <div><strong style={{ color: 'oklch(98.5% 0 0)' }}>All Games vs Candidate Edges</strong> — All Games shows every open market, edge or no edge. Candidate Edges only shows rows clearing our minimum net edge (5%, after Kalshi's fee) — that's the actionable, worth-trading list.</div>
            </div>
          </div>

          {/* ── All games table ─────────────────────────────────────────── */}
          <div className="data-table-wrap" style={{ marginBottom: 24 }}>
            <p className="section-title" style={{ padding: '14px 18px 0' }}>All Games</p>
            {sportFilter === 'all' ? (
              <div className="empty-state" style={{ padding: '20px 18px' }}>
                <p>Pick a sport above to browse every open Kalshi market for it — this view isn't fetched across all sports at once.</p>
              </div>
            ) : loadingGames ? (
              <div className="empty-state" style={{ padding: '20px 18px' }}>
                <p>Loading {sportLabel(sportFilter)} markets…</p>
              </div>
            ) : allGames.length === 0 ? (
              <div className="empty-state" style={{ padding: '20px 18px' }}>
                <p>No open Kalshi markets found for {sportLabel(sportFilter)} right now.</p>
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Market</th>
                    <th>Kalshi Price</th>
                    <th>Sharp Prob</th>
                    <th>Edge</th>
                    <th>Pick</th>
                    <th>Books</th>
                    <th>Game Time</th>
                  </tr>
                </thead>
                <tbody>
                  {allGames.map(g => {
                    const exploitable = g.net_edge_pct !== null && g.net_edge_pct > 0;
                    const clearsThreshold = g.net_edge_pct !== null && g.net_edge_pct >= 5.0;
                    return (
                      <tr key={g.market_ticker}>
                        <td style={{ fontWeight: 700, color: 'oklch(98.5% 0 0)', fontSize: '0.82rem' }}>
                          {g.title ?? g.yes_sub_title ?? g.market_ticker}
                          {g.already_started && (
                            <span style={{ marginLeft: 8, color: YELLOW, fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase' }}>live</span>
                          )}
                        </td>
                        <td style={{ textAlign: 'center' }}>{g.kalshi_price_cents !== null ? fmtCents(g.kalshi_price_cents) : '—'}</td>
                        <td style={{ textAlign: 'center' }}>{g.true_probability !== null ? `${(g.true_probability * 100).toFixed(1)}%` : '—'}</td>
                        <td style={{
                          textAlign: 'center', fontWeight: 700,
                          color: g.net_edge_pct === null ? MUTED_FG : (g.net_edge_pct >= 0 ? EMERALD : BRAND_RED),
                        }}>
                          {g.net_edge_pct !== null ? fmtPct(g.net_edge_pct) : 'no sharp match'}
                        </td>
                        <td style={{ textAlign: 'center' }}>
                          {exploitable ? (
                            <span style={{ color: clearsThreshold ? EMERALD : YELLOW, fontWeight: 700, fontSize: '0.78rem' }}>
                              BUY {g.yes_sub_title ?? '—'}
                              {!clearsThreshold && <span style={{ display: 'block', color: MUTED_FG, fontWeight: 500, fontSize: '0.68rem' }}>below 5% threshold</span>}
                            </span>
                          ) : (
                            <span style={{ color: MUTED_FG, fontSize: '0.78rem' }}>—</span>
                          )}
                        </td>
                        <td style={{ textAlign: 'center' }}>{g.books_sampled}</td>
                        <td style={{ textAlign: 'center', fontSize: '0.74rem', color: MUTED_FG }}>{fmtTime(g.expected_expiration_time)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>

          {/* ── Candidates table ────────────────────────────────────────── */}
          <div className="data-table-wrap" style={{ marginBottom: 24 }}>
            <p className="section-title" style={{ padding: '14px 18px 0' }}>Candidate Edges</p>
            {candidates.length === 0 ? (
              <div className="empty-state" style={{ padding: '20px 18px' }}>
                <p>No candidates right now — click "Scan for Edges" to check, or wait for one of the scheduled scans.</p>
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Market</th>
                    <th>Sport</th>
                    <th>Net Edge</th>
                    <th>Kalshi Price</th>
                    <th>True Prob</th>
                    <th>Books</th>
                    <th>Detected</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {candidates.map(c => (
                    <tr key={c.id}>
                      <td style={{ fontWeight: 700, color: 'oklch(98.5% 0 0)', fontSize: '0.82rem' }}>{c.market_ticker}</td>
                      <td style={{ textAlign: 'center' }}>{sportLabel(c.sport)}</td>
                      <td style={{ textAlign: 'center', fontWeight: 700, color: c.net_edge_pct >= 0 ? EMERALD : BRAND_RED }}>
                        {fmtPct(c.net_edge_pct)}
                      </td>
                      <td style={{ textAlign: 'center' }}>{fmtCents(c.kalshi_price_cents)}</td>
                      <td style={{ textAlign: 'center' }}>{(c.true_probability * 100).toFixed(1)}%</td>
                      <td style={{ textAlign: 'center' }}>{c.books_sampled}</td>
                      <td style={{ textAlign: 'center', fontSize: '0.74rem', color: MUTED_FG }}>{fmtTime(c.detected_at)}</td>
                      <td style={{ textAlign: 'center' }}>
                        {c.order_status ? (
                          <span style={{ color: c.order_status === 'placed' ? EMERALD : YELLOW, fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase' }}>
                            {c.order_status} ({c.order_contracts ?? 1})
                          </span>
                        ) : (
                          <button
                            onClick={() => handleExecute(c.id)}
                            disabled={executingId === c.id}
                            style={{
                              background: executingId === c.id ? SURFACE : EMERALD, border: 'none', borderRadius: 6,
                              padding: '6px 12px', color: executingId === c.id ? MUTED_FG : '#000', fontWeight: 700,
                              fontSize: '0.74rem', cursor: executingId === c.id ? 'not-allowed' : 'pointer',
                            }}
                          >
                            {executingId === c.id ? 'Placing…' : 'Execute (1 contract)'}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* ── Positions table ─────────────────────────────────────────── */}
          <div className="data-table-wrap">
            <p className="section-title" style={{ padding: '14px 18px 0' }}>Open Positions</p>
            {positions.length === 0 ? (
              <div className="empty-state" style={{ padding: '20px 18px' }}>
                <p>No open positions.</p>
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Market</th>
                    <th>Contracts</th>
                    <th>Exposure</th>
                    <th>Fees Paid</th>
                    <th>Realized P&amp;L</th>
                    <th>Last Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map(p => (
                    <tr key={p.ticker}>
                      <td style={{ fontWeight: 700, color: 'oklch(98.5% 0 0)', fontSize: '0.82rem' }}>{p.ticker}</td>
                      <td style={{ textAlign: 'center' }}>{p.contracts}</td>
                      <td style={{ textAlign: 'center' }}>{fmtDollars(p.exposure_cents)}</td>
                      <td style={{ textAlign: 'center', color: MUTED_FG }}>{fmtDollars(p.fees_paid_cents)}</td>
                      <td style={{ textAlign: 'center', fontWeight: 700, color: p.realized_pnl_cents >= 0 ? EMERALD : BRAND_RED }}>
                        {fmtDollars(p.realized_pnl_cents)}
                      </td>
                      <td style={{ textAlign: 'center', fontSize: '0.74rem', color: MUTED_FG }}>{fmtTime(p.last_updated_ts)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  );
}
