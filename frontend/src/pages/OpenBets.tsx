/**
 * My Bets — Per-user bet tracker backed by Postgres.
 * Keeps the original table format, hedge calculator, and filter pills.
 * Data flows from /api/v1/bets/ (auth-gated) instead of localStorage.
 */
import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { getApiUrl } from '../config';
import '../styles/analytics.css';

// ─── Types ────────────────────────────────────────────────────────────────────

type BetStatus = 'live' | 'pending' | 'won' | 'lost' | 'push' | 'void';
type BetType   = 'straight' | 'parlay' | 'teaser' | 'same_game_parlay';

interface BetLeg { sport?: string; game?: string; pick?: string; odds?: number; game_time?: string; result?: string | null; }

interface UserBet {
  id: number;
  book: string | null;
  bet_type: BetType;
  legs: BetLeg[];
  stake: number | null;
  to_win: number | null;
  combined_odds: number | null;
  status: BetStatus;
  game_date: string | null;
  created_at: string | null;
  graded_at: string | null;
}

interface ManualForm {
  book: string; bet_type: BetType; sport: string; event: string;
  market: string; pick: string; odds: number; stake: number; to_win: number;
  status: BetStatus; game_date: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmtOdds(o: number | null | undefined) {
  if (o === null || o === undefined) return '—';
  return o > 0 ? `+${o}` : `${o}`;
}
function fmtMoney(n: number | null | undefined) {
  if (n === null || n === undefined) return '—';
  return `$${n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}
function oddsToDecimal(american: number) {
  return american > 0 ? american / 100 + 1 : 100 / Math.abs(american) + 1;
}
function hedgeStake(stake: number, odds: number, hedgeOdds: number) {
  return Math.round((stake * oddsToDecimal(odds)) / oddsToDecimal(hedgeOdds) * 100) / 100;
}
function guaranteedProfit(stake: number, odds: number, hedgeOdds: number) {
  const hs = hedgeStake(stake, odds, hedgeOdds);
  return Math.round(Math.min(stake * oddsToDecimal(odds), hs * oddsToDecimal(hedgeOdds)) * 100 - (stake + hs) * 100) / 100;
}

function buildHeaders(token: string | null): Record<string, string> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) h['Authorization'] = `Bearer ${token}`;
  return h;
}

const STATUS_COLORS: Record<string, string> = {
  live:'#3b82f6', pending:'#f59e0b', won:'#10b981', lost:'#ef4444', push:'#6b7280', void:'#6b7280',
};
const STATUS_BG: Record<string, string> = {
  live:'rgba(59,130,246,.15)', pending:'rgba(245,158,11,.15)', won:'rgba(16,185,129,.15)',
  lost:'rgba(239,68,68,.15)', push:'rgba(107,114,128,.15)', void:'rgba(107,114,128,.15)',
};

// ─── Sub-components ───────────────────────────────────────────────────────────

function ExposureCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ background:'#111', border:'1px solid rgba(255,255,255,.08)', borderRadius:8, padding:'14px 20px', minWidth:150 }}>
      <div style={{ fontSize:'0.62rem', fontWeight:700, color:'#64748b', letterSpacing:'0.1em', textTransform:'uppercase', marginBottom:4 }}>{label}</div>
      <div style={{ fontSize:'1.25rem', fontWeight:800, color, fontFamily:'monospace' }}>{value}</div>
    </div>
  );
}

function HedgeModal({ bet, onClose }: { bet: UserBet; onClose: () => void }) {
  const [hedgeOdds, setHedgeOdds] = useState(-110);
  const stake = bet.stake ?? 0;
  const odds  = bet.combined_odds ?? bet.legs[0]?.odds ?? 0;
  const hs = hedgeStake(stake, odds, hedgeOdds);
  const gp = guaranteedProfit(stake, odds, hedgeOdds);
  const pick = bet.legs[0]?.pick ?? 'this bet';

  return (
    <div style={{ position:'fixed', inset:0, background:'rgba(0,0,0,.7)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:999 }} onClick={onClose}>
      <div style={{ background:'#0f172a', border:'1px solid rgba(255,255,255,.12)', borderRadius:12, padding:28, minWidth:360, maxWidth:440 }} onClick={e => e.stopPropagation()}>
        <div style={{ fontSize:'0.75rem', fontWeight:800, color:'#818cf8', letterSpacing:'0.1em', marginBottom:12 }}>HEDGE CALCULATOR</div>
        <div style={{ fontSize:'0.95rem', fontWeight:700, color:'#e2e8f0', marginBottom:4 }}>{pick}</div>
        <div style={{ fontSize:'0.72rem', color:'#64748b', marginBottom:16 }}>{fmtOdds(odds)} · {fmtMoney(stake)} at risk · to win {fmtMoney(bet.to_win)}</div>
        <label style={{ fontSize:'0.7rem', fontWeight:700, color:'#94a3b8', display:'block', marginBottom:6 }}>HEDGE ODDS</label>
        <input type="number" value={hedgeOdds} onChange={e => setHedgeOdds(Number(e.target.value))}
          style={{ width:'100%', background:'#1e293b', border:'1px solid rgba(255,255,255,.15)', borderRadius:6, padding:'8px 12px', color:'#e2e8f0', fontSize:'0.9rem', marginBottom:16, boxSizing:'border-box' }} />
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:16 }}>
          <div style={{ background:'#1e293b', borderRadius:8, padding:'12px 14px' }}>
            <div style={{ fontSize:'0.6rem', fontWeight:700, color:'#64748b', textTransform:'uppercase', marginBottom:4 }}>Hedge Stake</div>
            <div style={{ fontSize:'1.1rem', fontWeight:800, color:'#e2e8f0', fontFamily:'monospace' }}>{fmtMoney(hs)}</div>
          </div>
          <div style={{ background: gp > 0 ? 'rgba(16,185,129,.1)' : 'rgba(239,68,68,.1)', borderRadius:8, padding:'12px 14px' }}>
            <div style={{ fontSize:'0.6rem', fontWeight:700, color:'#64748b', textTransform:'uppercase', marginBottom:4 }}>Guaranteed P&L</div>
            <div style={{ fontSize:'1.1rem', fontWeight:800, color: gp > 0 ? '#10b981' : '#ef4444', fontFamily:'monospace' }}>{gp > 0 ? '+' : ''}{fmtMoney(gp)}</div>
          </div>
        </div>
        <button onClick={onClose} style={{ width:'100%', padding:'9px', borderRadius:6, background:'rgba(255,255,255,.05)', border:'1px solid rgba(255,255,255,.1)', color:'#94a3b8', fontSize:'0.8rem', cursor:'pointer' }}>Close</button>
      </div>
    </div>
  );
}

const BLANK_FORM: ManualForm = {
  book:'', bet_type:'straight', sport:'', event:'', market:'', pick:'', odds:-110, stake:0, to_win:0,
  status:'pending', game_date: new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Chicago' }).format(new Date()),
};

function BetForm({ initial, onSave, onClose }: { initial?: ManualForm | null; onSave: (f: ManualForm) => void; onClose: () => void; }) {
  const [form, setForm] = useState<ManualForm>(initial ?? { ...BLANK_FORM });
  const field = (key: keyof ManualForm, value: unknown) => setForm(f => ({ ...f, [key]: value }));
  const handleStake = (stake: number) => {
    const toWin = form.odds > 0 ? Math.round(stake * (form.odds / 100) * 100) / 100 : Math.round(stake * (100 / Math.abs(form.odds)) * 100) / 100;
    setForm(f => ({ ...f, stake, to_win: toWin }));
  };
  const inp = { background:'#1e293b', border:'1px solid rgba(255,255,255,.12)', borderRadius:6, padding:'7px 10px', color:'#e2e8f0', fontSize:'0.82rem', width:'100%', boxSizing:'border-box' as const };
  const lbl = { fontSize:'0.6rem', fontWeight:700 as const, color:'#64748b', textTransform:'uppercase' as const, display:'block' as const, marginBottom:4, letterSpacing:'0.08em' };

  return (
    <div style={{ position:'fixed', inset:0, background:'rgba(0,0,0,.75)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:998, overflowY:'auto' }} onClick={onClose}>
      <div style={{ background:'#0f172a', border:'1px solid rgba(255,255,255,.12)', borderRadius:12, padding:24, width:480, maxWidth:'95vw', margin:'20px auto' }} onClick={e => e.stopPropagation()}>
        <div style={{ fontSize:'0.75rem', fontWeight:800, color:'#3b82f6', letterSpacing:'0.1em', marginBottom:16 }}>{initial ? 'EDIT BET' : 'ADD BET'}</div>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:12 }}>
          <div><label style={lbl}>Book</label><input style={inp} value={form.book} onChange={e => field('book', e.target.value)} placeholder="DraftKings, Bovada…" /></div>
          <div><label style={lbl}>Sport</label><input style={inp} value={form.sport} onChange={e => field('sport', e.target.value)} placeholder="MLB, NFL, Golf…" /></div>
        </div>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:12 }}>
          <div>
            <label style={lbl}>Type</label>
            <select style={inp} value={form.bet_type} onChange={e => field('bet_type', e.target.value as BetType)}>
              <option value="straight">Straight</option><option value="parlay">Parlay</option><option value="teaser">Teaser</option><option value="same_game_parlay">Same Game Parlay</option>
            </select>
          </div>
          <div>
            <label style={lbl}>Status</label>
            <select style={inp} value={form.status} onChange={e => field('status', e.target.value as BetStatus)}>
              {(['live','pending','won','lost','push','void'] as BetStatus[]).map(s => <option key={s} value={s}>{s.toUpperCase()}</option>)}
            </select>
          </div>
        </div>
        <div style={{ marginBottom:12 }}><label style={lbl}>Event</label><input style={inp} value={form.event} onChange={e => field('event', e.target.value)} placeholder="Rocket Classic, Cubs @ Brewers…" /></div>
        <div style={{ marginBottom:12 }}><label style={lbl}>Market</label><input style={inp} value={form.market} onChange={e => field('market', e.target.value)} placeholder="Tournament Winner, F5 ML, Spread…" /></div>
        <div style={{ marginBottom:12 }}><label style={lbl}>Pick</label><input style={inp} value={form.pick} onChange={e => field('pick', e.target.value)} placeholder="Michael Kim, Over 4.5, Cubs ML…" /></div>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:12, marginBottom:12 }}>
          <div><label style={lbl}>Odds</label><input type="number" style={inp} value={form.odds} onChange={e => field('odds', Number(e.target.value))} /></div>
          <div><label style={lbl}>Stake ($)</label><input type="number" style={inp} value={form.stake} onChange={e => handleStake(Number(e.target.value))} /></div>
          <div><label style={lbl}>To Win ($)</label><input type="number" style={inp} value={form.to_win} onChange={e => field('to_win', Number(e.target.value))} /></div>
        </div>
        <div style={{ marginBottom:16 }}><label style={lbl}>Game Date</label><input type="date" style={inp} value={form.game_date} onChange={e => field('game_date', e.target.value)} /></div>
        <div style={{ display:'flex', gap:10 }}>
          <button onClick={() => { if (form.pick) onSave(form); }} style={{ flex:1, padding:'9px', borderRadius:6, background:'#3b82f6', color:'#fff', fontWeight:700, fontSize:'0.82rem', border:'none', cursor:'pointer' }}>{initial ? 'Save Changes' : 'Add Bet'}</button>
          <button onClick={onClose} style={{ padding:'9px 16px', borderRadius:6, background:'rgba(255,255,255,.05)', border:'1px solid rgba(255,255,255,.1)', color:'#94a3b8', fontSize:'0.82rem', cursor:'pointer' }}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

function ImportModal({ token, onDone, onClose }: { token: string | null; onDone: () => void; onClose: () => void }) {
  const [slip, setSlip] = useState('');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const handleImport = async () => {
    if (!slip.trim() || loading) return;
    setLoading(true); setErr(null);
    try {
      const r = await fetch(getApiUrl('v1/bets/import'), { method:'POST', headers: buildHeaders(token), body: JSON.stringify({ raw_slip: slip.trim() }) });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail ?? `HTTP ${r.status}`);
      setMsg(d.message ?? 'Bet saved.');
      setSlip('');
      setTimeout(onDone, 1500);
    } catch (e) { setErr((e as Error).message); }
    finally { setLoading(false); }
  };

  return (
    <div style={{ position:'fixed', inset:0, background:'rgba(0,0,0,.75)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:998 }} onClick={onClose}>
      <div style={{ background:'#0f172a', border:'1px solid rgba(255,255,255,.12)', borderRadius:12, padding:24, width:520, maxWidth:'95vw' }} onClick={e => e.stopPropagation()}>
        <div style={{ fontSize:'0.75rem', fontWeight:800, color:'#3b82f6', letterSpacing:'0.1em', marginBottom:8 }}>IMPORT BETSLIP</div>
        <p style={{ fontSize:'0.72rem', color:'#64748b', marginBottom:12 }}>Paste the full betslip text from DraftKings, FanDuel, BetMGM, Bovada, Caesars, ESPN Bet, etc. Haiku will parse it automatically.</p>
        <textarea value={slip} onChange={e => setSlip(e.target.value)} rows={7} placeholder="Paste betslip here…"
          style={{ width:'100%', background:'#1e293b', border:'1px solid rgba(255,255,255,.15)', borderRadius:8, padding:'10px 12px', color:'#e2e8f0', fontSize:'0.8rem', resize:'vertical', boxSizing:'border-box', marginBottom:12 }} />
        {msg && <div style={{ marginBottom:10, padding:'8px 12px', borderRadius:6, background:'rgba(16,185,129,.15)', border:'1px solid rgba(16,185,129,.3)', color:'#10b981', fontSize:'0.72rem' }}>{msg}</div>}
        {err && <div style={{ marginBottom:10, padding:'8px 12px', borderRadius:6, background:'rgba(239,68,68,.15)', border:'1px solid rgba(239,68,68,.3)', color:'#ef4444', fontSize:'0.72rem' }}>{err}</div>}
        <div style={{ display:'flex', gap:10 }}>
          <button onClick={handleImport} disabled={!slip.trim() || loading}
            style={{ flex:1, padding:'9px', borderRadius:6, background:'#3b82f6', color:'#fff', fontWeight:700, fontSize:'0.82rem', border:'none', cursor:'pointer', opacity: (!slip.trim() || loading) ? 0.5 : 1 }}>
            {loading ? 'Parsing…' : 'Import Bet'}
          </button>
          <button onClick={onClose} style={{ padding:'9px 16px', borderRadius:6, background:'rgba(255,255,255,.05)', border:'1px solid rgba(255,255,255,.1)', color:'#94a3b8', fontSize:'0.82rem', cursor:'pointer' }}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────

type DatePreset = 'today' | '7d' | '30d' | 'all' | 'custom';
type SortKey    = 'date' | 'status' | 'sport' | 'pnl' | 'odds' | 'stake';
type SortDir    = 'asc' | 'desc';

function betDate(b: UserBet): string {
  return b.game_date ?? (b.created_at ? b.created_at.slice(0, 10) : '');
}
/** Today's date in CST as YYYY-MM-DD. */
function isoToday() {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Chicago' }).format(new Date());
}
function isoNDaysAgo(n: number) {
  const dt = new Date(isoToday() + 'T12:00:00');
  dt.setDate(dt.getDate() - n);
  return dt.toISOString().slice(0, 10);
}

export function OpenBets() {
  const { token } = useAuth();
  const qc = useQueryClient();

  const [statusFilter, setStatusFilter] = useState<BetStatus | 'all'>('all');
  const [bookFilter,   setBookFilter]   = useState<string>('all');
  const [sportFilter,  setSportFilter]  = useState<string>('all');
  const [datePreset,   setDatePreset]   = useState<DatePreset>('all');
  const [customFrom,   setCustomFrom]   = useState('');
  const [customTo,     setCustomTo]     = useState('');
  const [sortKey,      setSortKey]      = useState<SortKey>('date');
  const [sortDir,      setSortDir]      = useState<SortDir>('desc');
  const [hedgeBet,     setHedgeBet]     = useState<UserBet | null>(null);
  const [showForm,     setShowForm]     = useState(false);
  const [showImport,   setShowImport]   = useState(false);
  const [expandedLegs, setExpandedLegs] = useState<Set<number>>(new Set());

  const { data: bets = [], isLoading } = useQuery({
    queryKey: ['my-bets', token],
    queryFn: async (): Promise<UserBet[]> => {
      const r = await fetch(getApiUrl('v1/bets/'), { headers: buildHeaders(token) });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json() as { bets: UserBet[] };
      return d.bets;
    },
    enabled: !!token,
    refetchInterval: 60_000,
  });

  const mutateStatus = useMutation({
    mutationFn: async ({ id, status }: { id: number; status: string }) => {
      const r = await fetch(getApiUrl(`v1/bets/${id}/status`), { method:'PATCH', headers: buildHeaders(token), body: JSON.stringify({ status }) });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['my-bets', token] }),
  });

  const mutateDelete = useMutation({
    mutationFn: async (id: number) => {
      if (!confirm('Remove this bet?')) throw new Error('cancelled');
      const r = await fetch(getApiUrl(`v1/bets/${id}`), { method:'DELETE', headers: buildHeaders(token) });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['my-bets', token] }),
  });

  const mutateAdd = useMutation({
    mutationFn: async (form: ManualForm) => {
      const r = await fetch(getApiUrl('v1/bets/manual'), { method:'POST', headers: buildHeaders(token), body: JSON.stringify({ ...form }) });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['my-bets', token] }); setShowForm(false); },
  });

  const toggleLegs = useCallback((id: number) =>
    setExpandedLegs(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n; }), []);

  const cycleSort = useCallback((key: SortKey) => {
    if (sortKey === key) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortKey(key); setSortDir('desc'); }
  }, [sortKey]);

  // Date range bounds
  const dateFrom = datePreset === 'today'  ? isoToday()
                 : datePreset === '7d'     ? isoNDaysAgo(7)
                 : datePreset === '30d'    ? isoNDaysAgo(30)
                 : datePreset === 'custom' ? customFrom
                 : '';
  const dateTo   = datePreset === 'custom' ? customTo : isoToday();

  // Derived filter values
  const presentBooks  = Array.from(new Set(bets.map(b => b.book).filter(Boolean))) as string[];
  const presentSports = Array.from(new Set(bets.flatMap(b => b.legs.map(l => l.sport)).filter(Boolean))) as string[];

  const afterFilters = bets.filter(b => {
    const d = betDate(b);
    const inDateRange = !dateFrom || (d >= dateFrom && d <= dateTo);
    return inDateRange &&
      (statusFilter === 'all' || b.status === statusFilter) &&
      (bookFilter   === 'all' || (b.book ?? '').toLowerCase() === bookFilter) &&
      (sportFilter  === 'all' || b.legs.some(l => (l.sport ?? '').toUpperCase() === sportFilter.toUpperCase()));
  });

  const filtered = [...afterFilters].sort((a, b) => {
    let cmp = 0;
    if (sortKey === 'date')   cmp = betDate(a).localeCompare(betDate(b));
    if (sortKey === 'status') cmp = a.status.localeCompare(b.status);
    if (sortKey === 'sport')  cmp = (a.legs[0]?.sport ?? '').localeCompare(b.legs[0]?.sport ?? '');
    if (sortKey === 'odds')   cmp = ((a.combined_odds ?? a.legs[0]?.odds ?? 0) - (b.combined_odds ?? b.legs[0]?.odds ?? 0));
    if (sortKey === 'stake')  cmp = ((a.stake ?? 0) - (b.stake ?? 0));
    if (sortKey === 'pnl') {
      const pnl = (x: UserBet) => x.status === 'won' ? (x.to_win ?? 0) : x.status === 'lost' ? -(x.stake ?? 0) : 0;
      cmp = pnl(a) - pnl(b);
    }
    return sortDir === 'desc' ? -cmp : cmp;
  });

  // Exposure dashboard — open bets always all-time; P&L uses date filter
  const openBets    = bets.filter(b => b.status === 'live' || b.status === 'pending');
  const totalAtRisk = openBets.reduce((s, b) => s + (b.stake ?? 0), 0);
  const totalToWin  = openBets.reduce((s, b) => s + (b.to_win ?? 0), 0);
  const netPnL      = afterFilters.reduce((s, b) => b.status === 'won' ? s + (b.to_win ?? 0) : b.status === 'lost' ? s - (b.stake ?? 0) : s, 0);
  const wonCount    = afterFilters.filter(b => b.status === 'won').length;
  const lostCount   = afterFilters.filter(b => b.status === 'lost').length;

  const pill = (active: boolean): React.CSSProperties => ({
    padding:'5px 12px', borderRadius:20, fontSize:'0.68rem', fontWeight:700, cursor:'pointer',
    border:`1px solid ${active ? '#3b82f6' : 'rgba(255,255,255,.1)'}`,
    background: active ? 'rgba(59,130,246,.2)' : 'transparent',
    color: active ? '#93c5fd' : '#64748b',
  });

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1>My Bets</h1>
        <p className="subtitle">Personal bet tracker · Import slip or add manually · Auto-graded from results</p>
      </div>

      <div style={{ padding:'0 24px 24px' }}>

        {/* Exposure dashboard */}
        <div style={{ display:'flex', gap:12, flexWrap:'wrap', marginBottom:20 }}>
          <ExposureCard label="Open at Risk"   value={fmtMoney(totalAtRisk)} color="#f59e0b" />
          <ExposureCard label="Max Potential"  value={fmtMoney(totalToWin)}  color="#3b82f6" />
          <ExposureCard label="Net P&L"        value={(netPnL >= 0 ? '+' : '') + fmtMoney(netPnL)} color={netPnL >= 0 ? '#10b981' : '#ef4444'} />
          <ExposureCard label="Open"           value={`${openBets.length}`}  color="#e2e8f0" />
          <ExposureCard label="W / L"          value={`${wonCount} / ${lostCount}`} color={wonCount >= lostCount ? '#10b981' : '#ef4444'} />
        </div>

        {/* Filters + action buttons */}
        <div style={{ display:'flex', flexDirection:'column', gap:10, marginBottom:16 }}>

          {/* Row 1: Date filter + action buttons */}
          <div style={{ display:'flex', flexWrap:'wrap', gap:8, alignItems:'center' }}>
            <span style={{ fontSize:'0.62rem', fontWeight:700, color:'#475569', marginRight:2 }}>DATE</span>
            {(['today','7d','30d','all'] as const).map(p => (
              <button key={p} style={pill(datePreset === p)} onClick={() => setDatePreset(p)}>
                {p === 'today' ? 'TODAY' : p === '7d' ? 'LAST 7D' : p === '30d' ? 'LAST 30D' : 'ALL TIME'}
              </button>
            ))}
            <button style={pill(datePreset === 'custom')} onClick={() => setDatePreset('custom')}>CUSTOM</button>
            {datePreset === 'custom' && (
              <div style={{ display:'flex', gap:6, alignItems:'center' }}>
                <input type="date" value={customFrom} onChange={e => setCustomFrom(e.target.value)}
                  style={{ background:'#1e293b', border:'1px solid rgba(255,255,255,.15)', borderRadius:6, padding:'4px 8px', color:'#e2e8f0', fontSize:'0.72rem' }} />
                <span style={{ color:'#475569', fontSize:'0.72rem' }}>→</span>
                <input type="date" value={customTo} onChange={e => setCustomTo(e.target.value)}
                  style={{ background:'#1e293b', border:'1px solid rgba(255,255,255,.15)', borderRadius:6, padding:'4px 8px', color:'#e2e8f0', fontSize:'0.72rem' }} />
              </div>
            )}
            <div style={{ marginLeft:'auto', display:'flex', gap:8 }}>
              <button onClick={() => setShowImport(true)} style={{ padding:'7px 14px', borderRadius:8, background:'rgba(99,102,241,.2)', color:'#818cf8', fontWeight:700, fontSize:'0.75rem', border:'1px solid rgba(99,102,241,.3)', cursor:'pointer' }}>
                ⬇ IMPORT SLIP
              </button>
              <button onClick={() => setShowForm(true)} style={{ padding:'7px 16px', borderRadius:8, background:'#3b82f6', color:'#fff', fontWeight:700, fontSize:'0.75rem', border:'none', cursor:'pointer' }}>
                + ADD BET
              </button>
            </div>
          </div>

          {/* Row 2: Status / Book / Sport filters */}
          <div style={{ display:'flex', flexWrap:'wrap', gap:8, alignItems:'center' }}>
            <span style={{ fontSize:'0.62rem', fontWeight:700, color:'#475569', marginRight:2 }}>STATUS</span>
            {(['all','live','pending','won','lost','push'] as const).map(s => (
              <button key={s} style={pill(statusFilter === s)} onClick={() => setStatusFilter(s)}>{s.toUpperCase()}</button>
            ))}

            {presentBooks.length > 0 && (
              <>
                <div style={{ width:1, height:18, background:'rgba(255,255,255,.08)', margin:'0 4px' }} />
                <span style={{ fontSize:'0.62rem', fontWeight:700, color:'#475569', marginRight:2 }}>BOOK</span>
                <button style={pill(bookFilter === 'all')} onClick={() => setBookFilter('all')}>ALL</button>
                {presentBooks.map(b => (
                  <button key={b} style={pill(bookFilter === b.toLowerCase())} onClick={() => setBookFilter(b.toLowerCase())}>{b.toUpperCase()}</button>
                ))}
              </>
            )}

            {presentSports.length > 0 && (
              <>
                <div style={{ width:1, height:18, background:'rgba(255,255,255,.08)', margin:'0 4px' }} />
                <span style={{ fontSize:'0.62rem', fontWeight:700, color:'#475569', marginRight:2 }}>SPORT</span>
                <button style={pill(sportFilter === 'all')} onClick={() => setSportFilter('all')}>ALL</button>
                {presentSports.map(s => (
                  <button key={s} style={pill(sportFilter === s)} onClick={() => setSportFilter(s)}>{s.toUpperCase()}</button>
                ))}
              </>
            )}

            <div style={{ marginLeft:'auto', fontSize:'0.65rem', color:'#475569' }}>
              {filtered.length} bet{filtered.length !== 1 ? 's' : ''}
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="data-table-wrap" style={{ overflowX:'auto' }}>
          <table style={{ width:'100%', borderCollapse:'collapse', fontSize:'0.78rem' }}>
            <thead>
              <tr>
                {([
                  { label:'Date',          key:'date',   align:'left'  },
                  { label:'Book',          key:null,     align:'left'  },
                  { label:'Sport',         key:'sport',  align:'left'  },
                  { label:'Event / Market',key:null,     align:'left'  },
                  { label:'Pick',          key:null,     align:'left'  },
                  { label:'Odds',          key:'odds',   align:'right' },
                  { label:'Stake',         key:'stake',  align:'right' },
                  { label:'To Win',        key:null,     align:'right' },
                  { label:'Status',        key:'status', align:'left'  },
                  { label:'Hedge',         key:null,     align:'left'  },
                  { label:'',             key:null,     align:'left'  },
                ] as { label: string; key: SortKey | null; align: string }[]).map(({ label, key, align }) => (
                  <th key={label} onClick={() => key && cycleSort(key)}
                    style={{ padding:'8px 10px', textAlign: align as 'left' | 'right',
                      fontSize:'0.62rem', fontWeight:700, color: key && sortKey === key ? '#93c5fd' : '#64748b',
                      letterSpacing:'0.1em', textTransform:'uppercase', borderBottom:'1px solid rgba(255,255,255,.08)',
                      whiteSpace:'nowrap', cursor: key ? 'pointer' : 'default', userSelect:'none' }}>
                    {label}{key && sortKey === key ? (sortDir === 'desc' ? ' ↓' : ' ↑') : key ? ' ↕' : ''}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr><td colSpan={11} style={{ padding:'40px', textAlign:'center', color:'#475569' }}>Loading your bets…</td></tr>
              )}
              {!isLoading && filtered.length === 0 && (
                <tr><td colSpan={11} style={{ padding:'32px', textAlign:'center', color:'#475569' }}>
                  {bets.length === 0 ? 'No bets yet — import a slip or add one manually.' : 'No bets match filters.'}
                </td></tr>
              )}
              {filtered.map(bet => {
                const sc  = STATUS_COLORS[bet.status] ?? '#6b7280';
                const sbg = STATUS_BG[bet.status]     ?? 'rgba(107,114,128,.15)';
                const leg = bet.legs[0];
                const isParlay = bet.legs.length > 1;
                const legsOpen = expandedLegs.has(bet.id);
                const isOpen = bet.status === 'live' || bet.status === 'pending';

                return (
                  <>
                    <tr key={bet.id} style={{ borderBottom:'1px solid rgba(255,255,255,.06)' }}>
                      <td style={{ padding:'8px 10px', color:'#475569', fontSize:'0.68rem', whiteSpace:'nowrap' }}>
                        {bet.game_date ?? (bet.created_at ? bet.created_at.slice(0,10) : '—')}
                      </td>
                      <td style={{ padding:'8px 10px', fontWeight:600, color:'#94a3b8', fontSize:'0.72rem' }}>
                        {bet.book ?? '—'}
                      </td>
                      <td style={{ padding:'8px 10px' }}>
                        <span style={{ fontSize:'0.65rem', fontWeight:700, padding:'2px 7px', borderRadius:12, background:'rgba(255,255,255,.06)', color:'#94a3b8', textTransform:'uppercase' }}>
                          {leg?.sport ?? '—'}
                        </span>
                      </td>
                      <td style={{ padding:'8px 10px', maxWidth:200 }}>
                        <div style={{ fontWeight:600, color:'#e2e8f0', fontSize:'0.78rem' }}>{leg?.game ?? '—'}</div>
                        <div style={{ fontSize:'0.65rem', color:'#64748b' }}>{bet.bet_type.replace(/_/g,' ')}</div>
                      </td>
                      <td style={{ padding:'8px 10px' }}>
                        <div style={{ display:'flex', alignItems:'center', gap:6 }}>
                          <span style={{ fontWeight:700, color:'#e2e8f0' }}>{leg?.pick ?? '—'}</span>
                          {isParlay && (
                            <button onClick={() => toggleLegs(bet.id)} style={{ fontSize:'0.6rem', padding:'1px 6px', borderRadius:10, border:'1px solid rgba(99,102,241,.4)', background:'rgba(99,102,241,.15)', color:'#818cf8', cursor:'pointer' }}>
                              {bet.legs.length}L {legsOpen ? '▲' : '▼'}
                            </button>
                          )}
                        </div>
                      </td>
                      <td style={{ padding:'8px 10px', textAlign:'right', fontFamily:'monospace', fontWeight:700, color:(bet.combined_odds ?? 0) > 0 ? '#10b981' : '#e2e8f0' }}>
                        {fmtOdds(bet.combined_odds ?? leg?.odds ?? null)}
                      </td>
                      <td style={{ padding:'8px 10px', textAlign:'right', fontFamily:'monospace', color:'#e2e8f0' }}>{fmtMoney(bet.stake)}</td>
                      <td style={{ padding:'8px 10px', textAlign:'right', fontFamily:'monospace', fontWeight:700, color:'#3b82f6' }}>{fmtMoney(bet.to_win)}</td>
                      <td style={{ padding:'8px 10px' }}>
                        <select value={bet.status} onChange={e => mutateStatus.mutate({ id: bet.id, status: e.target.value })}
                          style={{ background:sbg, border:`1px solid ${sc}40`, borderRadius:12, color:sc, fontSize:'0.65rem', fontWeight:700, padding:'3px 8px', cursor:'pointer', textTransform:'uppercase' }}>
                          {(['live','pending','won','lost','push','void'] as BetStatus[]).map(s => <option key={s} value={s}>{s.toUpperCase()}</option>)}
                        </select>
                      </td>
                      <td style={{ padding:'8px 10px' }}>
                        {isOpen
                          ? <button onClick={() => setHedgeBet(bet)} style={{ fontSize:'0.65rem', fontWeight:700, padding:'3px 8px', borderRadius:4, background:'rgba(99,102,241,.2)', color:'#818cf8', border:'1px solid rgba(99,102,241,.3)', cursor:'pointer', whiteSpace:'nowrap' }}>HEDGE CALC</button>
                          : <span style={{ color:'#475569', fontSize:'0.72rem' }}>—</span>}
                      </td>
                      <td style={{ padding:'8px 6px' }}>
                        <button onClick={() => mutateDelete.mutate(bet.id)} style={{ fontSize:'0.62rem', padding:'3px 7px', borderRadius:4, border:'1px solid rgba(239,68,68,.3)', background:'rgba(239,68,68,.08)', color:'#ef4444', cursor:'pointer' }}>✕</button>
                      </td>
                    </tr>
                    {isParlay && legsOpen && bet.legs.map((l, i) => (
                      <tr key={`${bet.id}-leg-${i}`} style={{ background:'rgba(99,102,241,.04)', borderBottom:'1px solid rgba(255,255,255,.04)' }}>
                        <td colSpan={3} />
                        <td colSpan={2} style={{ padding:'5px 10px 5px 22px', fontSize:'0.68rem', color:'#818cf8' }}>↳ Leg {i+1}: {l.pick ?? '—'}</td>
                        <td style={{ padding:'5px 10px', textAlign:'right', fontSize:'0.68rem', fontFamily:'monospace', color:'#818cf8' }}>{fmtOdds(l.odds ?? null)}</td>
                        <td colSpan={5} />
                      </tr>
                    ))}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {hedgeBet && <HedgeModal bet={hedgeBet} onClose={() => setHedgeBet(null)} />}
      {showForm  && <BetForm onSave={f => mutateAdd.mutate(f)} onClose={() => setShowForm(false)} />}
      {showImport && <ImportModal token={token} onDone={() => { qc.invalidateQueries({ queryKey: ['my-bets', token] }); setShowImport(false); }} onClose={() => setShowImport(false)} />}
    </div>
  );
}

export default OpenBets;
