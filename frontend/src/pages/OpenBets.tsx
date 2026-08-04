/**
 * Open Bets — Live bet tracker across books (Bovada, Kalshi, DraftKings, etc.)
 * Manual entry with localStorage persistence, exposure dashboard, hedge calculator.
 */
import { useState, useEffect, useCallback } from 'react';
import '../styles/analytics.css';

// ─── Types ───────────────────────────────────────────────────────────────────

type BetStatus = 'live' | 'pending' | 'won' | 'lost' | 'push';
type BetType   = 'single' | 'parlay' | 'teaser';
type Book      = 'bovada' | 'draftkings' | 'fanduel' | 'betmgm' | 'caesars' | 'kalshi' | 'other';
type Sport     = 'golf' | 'mlb' | 'nfl' | 'nba' | 'nhl' | 'ncaab' | 'soccer' | 'other';

interface ParlayLeg { pick: string; odds: number; status: BetStatus; }

interface Bet {
  id: string;
  placed_at: string;
  book: Book;
  type: BetType;
  sport: Sport;
  event: string;
  market: string;
  pick: string;
  odds: number;        // American: +200, -110
  stake: number;
  to_win: number;
  status: BetStatus;
  legs?: ParlayLeg[];
  cashout_available?: boolean;
  book_bet_id?: string;
  notes?: string;
}

// ─── Seed data (user's live bets 08/02/26) ───────────────────────────────────

const SEED: Bet[] = [
  { id:'b1', placed_at:'2026-08-02T13:35:00', book:'bovada', type:'single', sport:'golf',
    event:'Rocket Classic', market:'Tournament Winner Live', pick:'Michael Kim',
    odds:2000, stake:20, to_win:400, status:'live', book_bet_id:'26087406223190' },
  { id:'b2', placed_at:'2026-08-02T13:08:00', book:'bovada', type:'single', sport:'golf',
    event:'Rocket Classic', market:'Tournament Winner Live', pick:'Xander Schauffele',
    odds:700, stake:25, to_win:175, status:'live', book_bet_id:'26087406227732' },
  { id:'b3', placed_at:'2026-08-02T12:58:00', book:'bovada', type:'single', sport:'golf',
    event:'Rocket Classic', market:'Tournament Winner Live', pick:'Rasmus Hojgaard',
    odds:2500, stake:20, to_win:500, status:'live', book_bet_id:'26087406217967' },
  { id:'b4', placed_at:'2026-08-02T12:22:00', book:'bovada', type:'single', sport:'golf',
    event:'Rocket Classic', market:'Tournament Winner Live', pick:'Patrick Cantlay',
    odds:3500, stake:25, to_win:875, status:'live', book_bet_id:'26087406063329' },
  { id:'b5', placed_at:'2026-08-02T10:22:00', book:'bovada', type:'parlay', sport:'mlb',
    event:'Multi', market:'5-Inning 3-Way ML Parlay', pick:'Tie + Tie',
    odds:2815, stake:50, to_win:1407.50, status:'live', cashout_available:false,
    book_bet_id:'26087405912560',
    legs:[
      { pick:'Tie — Angels/Brewers F5 (+430)', odds:430, status:'live' },
      { pick:'Tie — Phillies/Orioles F5 (+450)', odds:450, status:'live' },
    ] },
  { id:'b6', placed_at:'2026-08-02T10:19:00', book:'bovada', type:'single', sport:'mlb',
    event:'Brewers @ Angels', market:'5-Inning 3-Way ML', pick:'Tie',
    odds:430, stake:20, to_win:86, status:'live', cashout_available:false,
    book_bet_id:'26087405837805' },
  { id:'b7', placed_at:'2026-08-02T07:36:00', book:'bovada', type:'single', sport:'golf',
    event:'Rocket Classic', market:'Tournament Winner Live', pick:'Rasmus Hojgaard',
    odds:1600, stake:25, to_win:400, status:'live', book_bet_id:'26087405587526' },
  { id:'b8', placed_at:'2026-08-02T07:36:00', book:'bovada', type:'single', sport:'golf',
    event:'Rocket Classic', market:'Tournament Winner Live', pick:'Rickie Fowler',
    odds:1200, stake:25, to_win:300, status:'live', book_bet_id:'26087405587525' },
  { id:'b9', placed_at:'2026-08-02T07:36:00', book:'bovada', type:'single', sport:'golf',
    event:'Rocket Classic', market:'Tournament Winner Live', pick:'Chris Kirk',
    odds:1400, stake:25, to_win:350, status:'live', book_bet_id:'26087405587524' },
];

const STORAGE_KEY = 'maxev_open_bets';

function loadBets(): Bet[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Bet[]) : SEED;
  } catch { return SEED; }
}

function saveBets(bets: Bet[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(bets));
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function oddsToDecimal(american: number): number {
  return american > 0 ? american / 100 + 1 : 100 / Math.abs(american) + 1;
}

function hedgeStake(betStake: number, betOdds: number, hedgeOdds: number): number {
  const totalReturn = betStake * oddsToDecimal(betOdds);
  const hedgeDec    = oddsToDecimal(hedgeOdds);
  return Math.round((totalReturn / hedgeDec) * 100) / 100;
}

function guaranteedProfit(betStake: number, betOdds: number, hedgeOdds: number): number {
  const hs    = hedgeStake(betStake, betOdds, hedgeOdds);
  const total = betStake + hs;
  const returnIfBetWins   = betStake * oddsToDecimal(betOdds);
  const returnIfHedgeWins = hs * oddsToDecimal(hedgeOdds);
  return Math.round(Math.min(returnIfBetWins, returnIfHedgeWins) * 100 - total * 100) / 100;
}

function fmtOdds(o: number) { return o > 0 ? `+${o}` : `${o}`; }
function fmtMoney(n: number) { return `$${n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`; }

const STATUS_COLORS: Record<BetStatus, string> = {
  live:    '#3b82f6',
  pending: '#f59e0b',
  won:     '#10b981',
  lost:    '#ef4444',
  push:    '#6b7280',
};

const STATUS_BG: Record<BetStatus, string> = {
  live:    'rgba(59,130,246,.15)',
  pending: 'rgba(245,158,11,.15)',
  won:     'rgba(16,185,129,.15)',
  lost:    'rgba(239,68,68,.15)',
  push:    'rgba(107,114,128,.15)',
};

const BOOK_LABELS: Record<Book, string> = {
  bovada:'Bovada', draftkings:'DraftKings', fanduel:'FanDuel',
  betmgm:'BetMGM', caesars:'Caesars', kalshi:'Kalshi', other:'Other',
};

// ─── Blank form ───────────────────────────────────────────────────────────────

const BLANK: Omit<Bet,'id'> = {
  placed_at: new Date().toISOString().slice(0,16),
  book:'bovada', type:'single', sport:'golf',
  event:'', market:'', pick:'', odds:100, stake:0, to_win:0, status:'live',
};

// ─── Sub-components ───────────────────────────────────────────────────────────

function ExposureCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ background:'#111', border:`1px solid rgba(255,255,255,.08)`, borderRadius:8, padding:'14px 20px', minWidth:160 }}>
      <div style={{ fontSize:'0.62rem', fontWeight:700, color:'#64748b', letterSpacing:'0.1em', textTransform:'uppercase', marginBottom:4 }}>{label}</div>
      <div style={{ fontSize:'1.25rem', fontWeight:800, color, fontFamily:'var(--d3-mono,monospace)' }}>{value}</div>
    </div>
  );
}

function HedgeCell({ bet, onCalc }: { bet: Bet; onCalc: (b: Bet) => void }) {
  if (bet.status !== 'live' && bet.status !== 'pending') {
    return <td style={{ padding:'8px 10px', color:'#475569', fontSize:'0.72rem' }}>—</td>;
  }
  return (
    <td style={{ padding:'8px 10px' }}>
      <button
        onClick={() => onCalc(bet)}
        style={{ fontSize:'0.65rem', fontWeight:700, padding:'3px 8px', borderRadius:4,
          background:'rgba(99,102,241,.2)', color:'#818cf8', border:'1px solid rgba(99,102,241,.3)',
          cursor:'pointer', whiteSpace:'nowrap' }}
      >
        HEDGE CALC
      </button>
    </td>
  );
}

interface HedgeModalProps { bet: Bet; onClose: () => void; }
function HedgeModal({ bet, onClose }: HedgeModalProps) {
  const [hedgeOdds, setHedgeOdds] = useState<number>(-110);
  const hs  = hedgeStake(bet.stake, bet.odds, hedgeOdds);
  const gp  = guaranteedProfit(bet.stake, bet.odds, hedgeOdds);

  return (
    <div style={{ position:'fixed', inset:0, background:'rgba(0,0,0,.7)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:999 }}
      onClick={onClose}>
      <div style={{ background:'#0f172a', border:'1px solid rgba(255,255,255,.12)', borderRadius:12, padding:28, minWidth:360, maxWidth:440 }}
        onClick={e => e.stopPropagation()}>
        <div style={{ fontSize:'0.75rem', fontWeight:800, color:'#818cf8', letterSpacing:'0.1em', marginBottom:12 }}>HEDGE CALCULATOR</div>
        <div style={{ fontSize:'0.95rem', fontWeight:700, color:'#e2e8f0', marginBottom:4 }}>{bet.pick}</div>
        <div style={{ fontSize:'0.72rem', color:'#64748b', marginBottom:16 }}>
          {fmtOdds(bet.odds)} · {fmtMoney(bet.stake)} at risk · to win {fmtMoney(bet.to_win)}
        </div>
        <label style={{ fontSize:'0.7rem', fontWeight:700, color:'#94a3b8', display:'block', marginBottom:6 }}>
          HEDGE ODDS (other side / opposing book)
        </label>
        <input
          type="number"
          value={hedgeOdds}
          onChange={e => setHedgeOdds(Number(e.target.value))}
          style={{ width:'100%', background:'#1e293b', border:'1px solid rgba(255,255,255,.15)', borderRadius:6,
            padding:'8px 12px', color:'#e2e8f0', fontSize:'0.9rem', marginBottom:16, boxSizing:'border-box' }}
        />
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:20 }}>
          <div style={{ background:'#1e293b', borderRadius:8, padding:'12px 14px' }}>
            <div style={{ fontSize:'0.6rem', fontWeight:700, color:'#64748b', textTransform:'uppercase', marginBottom:4 }}>Hedge Stake</div>
            <div style={{ fontSize:'1.1rem', fontWeight:800, color:'#e2e8f0', fontFamily:'monospace' }}>{fmtMoney(hs)}</div>
          </div>
          <div style={{ background: gp > 0 ? 'rgba(16,185,129,.1)' : 'rgba(239,68,68,.1)', borderRadius:8, padding:'12px 14px' }}>
            <div style={{ fontSize:'0.6rem', fontWeight:700, color:'#64748b', textTransform:'uppercase', marginBottom:4 }}>Guaranteed P&L</div>
            <div style={{ fontSize:'1.1rem', fontWeight:800, color: gp > 0 ? '#10b981' : '#ef4444', fontFamily:'monospace' }}>
              {gp > 0 ? '+' : ''}{fmtMoney(gp)}
            </div>
          </div>
        </div>
        <div style={{ fontSize:'0.65rem', color:'#475569', marginBottom:16, lineHeight:1.5 }}>
          Total action: {fmtMoney(bet.stake + hs)} · If bet wins: {fmtMoney(bet.stake * oddsToDecimal(bet.odds) - hs)} ·
          If hedge wins: {fmtMoney(hs * oddsToDecimal(hedgeOdds) - bet.stake)}
        </div>
        <button onClick={onClose} style={{ width:'100%', padding:'9px', borderRadius:6, background:'rgba(255,255,255,.05)',
          border:'1px solid rgba(255,255,255,.1)', color:'#94a3b8', fontSize:'0.8rem', cursor:'pointer' }}>
          Close
        </button>
      </div>
    </div>
  );
}

// ─── Add/Edit form modal ──────────────────────────────────────────────────────

interface BetFormProps { initial?: Bet | null; onSave: (b: Bet) => void; onClose: () => void; }
function BetForm({ initial, onSave, onClose }: BetFormProps) {
  const [form, setForm] = useState<Omit<Bet,'id'>>(initial
    ? { ...initial }
    : { ...BLANK, placed_at: new Date().toISOString().slice(0,16) }
  );

  function field(key: keyof typeof form, value: unknown) {
    setForm(f => ({ ...f, [key]: value }));
  }

  function handleStakeChange(stake: number) {
    const odds = form.odds;
    const toWin = odds > 0 ? Math.round(stake * (odds / 100) * 100) / 100
                           : Math.round(stake * (100 / Math.abs(odds)) * 100) / 100;
    setForm(f => ({ ...f, stake, to_win: toWin }));
  }

  function handleSubmit() {
    if (!form.pick || !form.event || form.stake <= 0) return;
    onSave({ ...form, id: initial?.id ?? crypto.randomUUID() });
  }

  const inp = (style?: object) => ({
    background:'#1e293b', border:'1px solid rgba(255,255,255,.12)', borderRadius:6,
    padding:'7px 10px', color:'#e2e8f0', fontSize:'0.82rem', width:'100%', boxSizing:'border-box' as const,
    ...style,
  });

  const lbl = { fontSize:'0.6rem', fontWeight:700, color:'#64748b', textTransform:'uppercase' as const,
    display:'block', marginBottom:4, letterSpacing:'0.08em' };

  return (
    <div style={{ position:'fixed', inset:0, background:'rgba(0,0,0,.75)', display:'flex', alignItems:'center',
      justifyContent:'center', zIndex:998, overflowY:'auto' }} onClick={onClose}>
      <div style={{ background:'#0f172a', border:'1px solid rgba(255,255,255,.12)', borderRadius:12,
        padding:24, width:480, maxWidth:'95vw', margin:'20px auto' }} onClick={e => e.stopPropagation()}>
        <div style={{ fontSize:'0.75rem', fontWeight:800, color:'#3b82f6', letterSpacing:'0.1em', marginBottom:16 }}>
          {initial ? 'EDIT BET' : 'ADD BET'}
        </div>

        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:12 }}>
          <div>
            <label style={lbl}>Book</label>
            <select style={inp()} value={form.book} onChange={e => field('book', e.target.value as Book)}>
              {(Object.keys(BOOK_LABELS) as Book[]).map(b => <option key={b} value={b}>{BOOK_LABELS[b]}</option>)}
            </select>
          </div>
          <div>
            <label style={lbl}>Sport</label>
            <select style={inp()} value={form.sport} onChange={e => field('sport', e.target.value as Sport)}>
              {(['golf','mlb','nfl','nba','nhl','ncaab','soccer','other'] as Sport[]).map(s =>
                <option key={s} value={s}>{s.toUpperCase()}</option>)}
            </select>
          </div>
        </div>

        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:12 }}>
          <div>
            <label style={lbl}>Type</label>
            <select style={inp()} value={form.type} onChange={e => field('type', e.target.value as BetType)}>
              <option value="single">Single</option>
              <option value="parlay">Parlay</option>
              <option value="teaser">Teaser</option>
            </select>
          </div>
          <div>
            <label style={lbl}>Status</label>
            <select style={inp()} value={form.status} onChange={e => field('status', e.target.value as BetStatus)}>
              <option value="live">Live</option>
              <option value="pending">Pending</option>
              <option value="won">Won</option>
              <option value="lost">Lost</option>
              <option value="push">Push</option>
            </select>
          </div>
        </div>

        <div style={{ marginBottom:12 }}>
          <label style={lbl}>Event</label>
          <input style={inp()} value={form.event} onChange={e => field('event', e.target.value)} placeholder="Rocket Classic, Brewers @ Angels…" />
        </div>

        <div style={{ marginBottom:12 }}>
          <label style={lbl}>Market</label>
          <input style={inp()} value={form.market} onChange={e => field('market', e.target.value)} placeholder="Tournament Winner, F5 ML, Spread…" />
        </div>

        <div style={{ marginBottom:12 }}>
          <label style={lbl}>Pick / Selection</label>
          <input style={inp()} value={form.pick} onChange={e => field('pick', e.target.value)} placeholder="Michael Kim, Tie, Over 4.5…" />
        </div>

        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:12, marginBottom:12 }}>
          <div>
            <label style={lbl}>Odds (American)</label>
            <input type="number" style={inp()} value={form.odds}
              onChange={e => { field('odds', Number(e.target.value)); handleStakeChange(form.stake); }} />
          </div>
          <div>
            <label style={lbl}>Stake ($)</label>
            <input type="number" style={inp()} value={form.stake}
              onChange={e => handleStakeChange(Number(e.target.value))} />
          </div>
          <div>
            <label style={lbl}>To Win ($)</label>
            <input type="number" style={inp()} value={form.to_win}
              onChange={e => field('to_win', Number(e.target.value))} />
          </div>
        </div>

        <div style={{ marginBottom:16 }}>
          <label style={lbl}>Book Bet ID (optional)</label>
          <input style={inp()} value={form.book_bet_id ?? ''} onChange={e => field('book_bet_id', e.target.value)} />
        </div>

        <div style={{ display:'flex', gap:10 }}>
          <button onClick={handleSubmit} style={{ flex:1, padding:'9px', borderRadius:6, background:'#3b82f6',
            color:'#fff', fontWeight:700, fontSize:'0.82rem', border:'none', cursor:'pointer' }}>
            {initial ? 'Save Changes' : 'Add Bet'}
          </button>
          <button onClick={onClose} style={{ padding:'9px 16px', borderRadius:6, background:'rgba(255,255,255,.05)',
            border:'1px solid rgba(255,255,255,.1)', color:'#94a3b8', fontSize:'0.82rem', cursor:'pointer' }}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function OpenBets() {
  const [bets, setBets]             = useState<Bet[]>(loadBets);
  const [bookFilter, setBookFilter] = useState<Book | 'all'>('all');
  const [sportFilter, setSportFilter] = useState<Sport | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<BetStatus | 'all'>('live');
  const [hedgeBet, setHedgeBet]     = useState<Bet | null>(null);
  const [editBet, setEditBet]       = useState<Bet | null | 'new'>('new' as never);
  const [showForm, setShowForm]     = useState(false);
  const [expandedLegs, setExpandedLegs] = useState<Set<string>>(new Set());

  // Persist on every change
  useEffect(() => { saveBets(bets); }, [bets]);

  const saveBet = useCallback((b: Bet) => {
    setBets(prev => {
      const idx = prev.findIndex(x => x.id === b.id);
      return idx >= 0 ? prev.map((x, i) => i === idx ? b : x) : [b, ...prev];
    });
    setShowForm(false);
    setEditBet(null);
  }, []);

  const deleteBet = useCallback((id: string) => {
    if (confirm('Remove this bet?')) setBets(prev => prev.filter(b => b.id !== id));
  }, []);

  const setStatus = useCallback((id: string, status: BetStatus) => {
    setBets(prev => prev.map(b => b.id === id ? { ...b, status } : b));
  }, []);

  const toggleLegs = (id: string) =>
    setExpandedLegs(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n; });

  // Filter
  const filtered = bets.filter(b =>
    (bookFilter  === 'all' || b.book   === bookFilter) &&
    (sportFilter === 'all' || b.sport  === sportFilter) &&
    (statusFilter === 'all' || b.status === statusFilter)
  );

  // Exposure calcs (on open/live/pending only)
  const openBets = bets.filter(b => b.status === 'live' || b.status === 'pending');
  const totalAtRisk  = openBets.reduce((s, b) => s + b.stake, 0);
  const totalToWin   = openBets.reduce((s, b) => s + b.to_win, 0);
  const todayPnl     = bets.reduce((s, b) =>
    b.status === 'won' ? s + b.to_win : b.status === 'lost' ? s - b.stake : s, 0);
  const wonCount  = bets.filter(b => b.status === 'won').length;
  const lostCount = bets.filter(b => b.status === 'lost').length;

  // Books and sports present
  const presentBooks  = Array.from(new Set(bets.map(b => b.book))) as Book[];
  const presentSports = Array.from(new Set(bets.map(b => b.sport))) as Sport[];

  const pillBtn = (active: boolean) => ({
    padding:'5px 12px', borderRadius:20, fontSize:'0.68rem', fontWeight:700, cursor:'pointer',
    border:`1px solid ${active ? '#3b82f6' : 'rgba(255,255,255,.1)'}`,
    background: active ? 'rgba(59,130,246,.2)' : 'transparent',
    color: active ? '#93c5fd' : '#64748b',
  } as const);

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1>Open Bets</h1>
        <p className="subtitle">
          Track live exposure across books · Manual entry · Hedge calculator
        </p>
      </div>

      <div style={{ padding:'0 24px 24px' }}>

        {/* ── Exposure dashboard ──────────────────────────────── */}
        <div style={{ display:'flex', gap:12, flexWrap:'wrap', marginBottom:20 }}>
          <ExposureCard label="Open at Risk" value={fmtMoney(totalAtRisk)} color="#f59e0b" />
          <ExposureCard label="Max Potential" value={fmtMoney(totalToWin)} color="#3b82f6" />
          <ExposureCard label="Today P&L" value={(todayPnl >= 0 ? '+' : '') + fmtMoney(todayPnl)}
            color={todayPnl >= 0 ? '#10b981' : '#ef4444'} />
          <ExposureCard label="Open Bets" value={`${openBets.length}`} color="#e2e8f0" />
          <ExposureCard label="W / L" value={`${wonCount} / ${lostCount}`}
            color={wonCount >= lostCount ? '#10b981' : '#ef4444'} />
        </div>

        {/* ── Filters + Add button ─────────────────────────────── */}
        <div style={{ display:'flex', flexWrap:'wrap', gap:8, alignItems:'center', marginBottom:16 }}>

          <div style={{ display:'flex', gap:4, alignItems:'center', flexWrap:'wrap' }}>
            <span style={{ fontSize:'0.62rem', fontWeight:700, color:'#475569', marginRight:4 }}>STATUS</span>
            {(['live','pending','won','lost','push','all'] as const).map(s => (
              <button key={s} style={pillBtn(statusFilter === s)} onClick={() => setStatusFilter(s)}>
                {s.toUpperCase()}
              </button>
            ))}
          </div>

          <div style={{ width:1, height:20, background:'rgba(255,255,255,.08)', margin:'0 4px' }} />

          <div style={{ display:'flex', gap:4, alignItems:'center', flexWrap:'wrap' }}>
            <span style={{ fontSize:'0.62rem', fontWeight:700, color:'#475569', marginRight:4 }}>BOOK</span>
            <button style={pillBtn(bookFilter === 'all')} onClick={() => setBookFilter('all')}>ALL</button>
            {presentBooks.map(b => (
              <button key={b} style={pillBtn(bookFilter === b)} onClick={() => setBookFilter(b)}>
                {BOOK_LABELS[b].toUpperCase()}
              </button>
            ))}
          </div>

          <div style={{ width:1, height:20, background:'rgba(255,255,255,.08)', margin:'0 4px' }} />

          <div style={{ display:'flex', gap:4, alignItems:'center', flexWrap:'wrap' }}>
            <span style={{ fontSize:'0.62rem', fontWeight:700, color:'#475569', marginRight:4 }}>SPORT</span>
            <button style={pillBtn(sportFilter === 'all')} onClick={() => setSportFilter('all')}>ALL</button>
            {presentSports.map(s => (
              <button key={s} style={pillBtn(sportFilter === s)} onClick={() => setSportFilter(s)}>
                {s.toUpperCase()}
              </button>
            ))}
          </div>

          <div style={{ marginLeft:'auto' }}>
            <button
              onClick={() => { setEditBet(null); setShowForm(true); }}
              style={{ padding:'8px 18px', borderRadius:8, background:'#3b82f6', color:'#fff',
                fontWeight:700, fontSize:'0.78rem', border:'none', cursor:'pointer' }}
            >
              + ADD BET
            </button>
          </div>
        </div>

        {/* ── Bets table ───────────────────────────────────────── */}
        <div className="data-table-wrap" style={{ overflowX:'auto' }}>
          <table style={{ width:'100%', borderCollapse:'collapse', fontSize:'0.78rem' }}>
            <thead>
              <tr>
                {['Time','Book','Sport','Event · Market','Pick','Odds','Stake','To Win','Status','Hedge',''].map(h => (
                  <th key={h} style={{
                    padding:'8px 10px', textAlign: ['Stake','To Win','Odds'].includes(h) ? 'right' : 'left',
                    fontSize:'0.62rem', fontWeight:700, color:'#64748b',
                    letterSpacing:'0.1em', textTransform:'uppercase',
                    borderBottom:'1px solid rgba(255,255,255,.08)', whiteSpace:'nowrap',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={11} style={{ padding:'32px', textAlign:'center', color:'#475569' }}>
                    No bets match filters.
                  </td>
                </tr>
              )}
              {filtered.map(bet => {
                const sc = STATUS_COLORS[bet.status];
                const sbg = STATUS_BG[bet.status];
                const hasLegs = bet.legs && bet.legs.length > 0;
                const legsOpen = expandedLegs.has(bet.id);
                return (
                  <>
                    <tr key={bet.id} style={{ borderBottom:'1px solid rgba(255,255,255,.06)' }}>
                      <td style={{ padding:'8px 10px', color:'#475569', fontSize:'0.68rem', whiteSpace:'nowrap' }}>
                        {new Date(bet.placed_at).toLocaleTimeString('en-US', { hour:'numeric', minute:'2-digit' })}
                      </td>
                      <td style={{ padding:'8px 10px', fontWeight:600, color:'#94a3b8', fontSize:'0.72rem' }}>
                        {BOOK_LABELS[bet.book]}
                      </td>
                      <td style={{ padding:'8px 10px' }}>
                        <span style={{ fontSize:'0.65rem', fontWeight:700, padding:'2px 7px', borderRadius:12,
                          background:'rgba(255,255,255,.06)', color:'#94a3b8', textTransform:'uppercase' }}>
                          {bet.sport}
                        </span>
                      </td>
                      <td style={{ padding:'8px 10px', maxWidth:200 }}>
                        <div style={{ fontWeight:600, color:'#e2e8f0', fontSize:'0.78rem' }}>{bet.event}</div>
                        <div style={{ fontSize:'0.65rem', color:'#64748b' }}>{bet.market}</div>
                      </td>
                      <td style={{ padding:'8px 10px' }}>
                        <div style={{ display:'flex', alignItems:'center', gap:6 }}>
                          <span style={{ fontWeight:700, color:'#e2e8f0' }}>{bet.pick}</span>
                          {bet.type === 'parlay' && (
                            <button onClick={() => toggleLegs(bet.id)} style={{
                              fontSize:'0.6rem', padding:'1px 6px', borderRadius:10, border:'1px solid rgba(99,102,241,.4)',
                              background:'rgba(99,102,241,.15)', color:'#818cf8', cursor:'pointer',
                            }}>{bet.legs?.length}L {legsOpen ? '▲' : '▼'}</button>
                          )}
                        </div>
                      </td>
                      <td style={{ padding:'8px 10px', textAlign:'right', fontFamily:'monospace', fontWeight:700,
                        color: bet.odds > 0 ? '#10b981' : '#e2e8f0' }}>
                        {fmtOdds(bet.odds)}
                      </td>
                      <td style={{ padding:'8px 10px', textAlign:'right', fontFamily:'monospace', color:'#e2e8f0' }}>
                        {fmtMoney(bet.stake)}
                      </td>
                      <td style={{ padding:'8px 10px', textAlign:'right', fontFamily:'monospace', fontWeight:700, color:'#3b82f6' }}>
                        {fmtMoney(bet.to_win)}
                      </td>
                      <td style={{ padding:'8px 10px' }}>
                        <select
                          value={bet.status}
                          onChange={e => setStatus(bet.id, e.target.value as BetStatus)}
                          style={{ background:sbg, border:`1px solid ${sc}40`, borderRadius:12,
                            color:sc, fontSize:'0.65rem', fontWeight:700, padding:'3px 8px', cursor:'pointer',
                            textTransform:'uppercase' }}
                        >
                          {(['live','pending','won','lost','push'] as BetStatus[]).map(s =>
                            <option key={s} value={s}>{s.toUpperCase()}</option>)}
                        </select>
                      </td>
                      <HedgeCell bet={bet} onCalc={setHedgeBet} />
                      <td style={{ padding:'8px 6px' }}>
                        <div style={{ display:'flex', gap:4 }}>
                          <button onClick={() => { setEditBet(bet); setShowForm(true); }}
                            style={{ fontSize:'0.62rem', padding:'3px 7px', borderRadius:4, border:'1px solid rgba(255,255,255,.1)',
                              background:'transparent', color:'#64748b', cursor:'pointer' }}>✎</button>
                          <button onClick={() => deleteBet(bet.id)}
                            style={{ fontSize:'0.62rem', padding:'3px 7px', borderRadius:4, border:'1px solid rgba(239,68,68,.3)',
                              background:'rgba(239,68,68,.08)', color:'#ef4444', cursor:'pointer' }}>✕</button>
                        </div>
                      </td>
                    </tr>
                    {hasLegs && legsOpen && bet.legs!.map((leg, i) => (
                      <tr key={`${bet.id}-leg-${i}`} style={{ background:'rgba(99,102,241,.04)', borderBottom:'1px solid rgba(255,255,255,.04)' }}>
                        <td colSpan={3} />
                        <td colSpan={2} style={{ padding:'5px 10px 5px 22px', fontSize:'0.68rem', color:'#818cf8' }}>
                          ↳ Leg {i+1}: {leg.pick}
                        </td>
                        <td style={{ padding:'5px 10px', textAlign:'right', fontSize:'0.68rem', fontFamily:'monospace', color:'#818cf8' }}>
                          {fmtOdds(leg.odds)}
                        </td>
                        <td colSpan={5} />
                      </tr>
                    ))}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* ── Notes / roadmap ─────────────────────────────────── */}
        <div style={{ marginTop:20, padding:'14px 18px', borderRadius:8, background:'rgba(255,255,255,.03)',
          border:'1px solid rgba(255,255,255,.06)', fontSize:'0.68rem', color:'#475569', lineHeight:1.7 }}>
          <strong style={{ color:'#64748b', display:'block', marginBottom:4 }}>ROADMAP</strong>
          Phase 1 (now) — Manual entry, localStorage persistence, exposure dashboard, hedge calculator<br />
          Phase 2 — Kalshi API integration (auto-pull open positions)<br />
          Phase 3 — Live odds feed for hedge side (Odds API), one-click hedge suggestion on live bets<br />
          Phase 4 — Middle finder: cross-book line shopping to identify middle opportunities across open bets
        </div>

      </div>

      {/* ── Modals ─────────────────────────────────────────────── */}
      {hedgeBet && <HedgeModal bet={hedgeBet} onClose={() => setHedgeBet(null)} />}
      {showForm && (
        <BetForm
          initial={editBet instanceof Object && editBet !== null && 'id' in editBet ? editBet as Bet : null}
          onSave={saveBet}
          onClose={() => { setShowForm(false); setEditBet(null); }}
        />
      )}
    </div>
  );
}

export default OpenBets;
