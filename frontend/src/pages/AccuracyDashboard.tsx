import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';

const BG     = 'oklch(14.5% 0 0)';
const PANEL  = 'oklch(18% 0 0)';
const BORDER = 'oklch(100% 0 0 / .08)';
const FG     = 'oklch(98.5% 0 0)';
const MUTED  = 'oklch(60% 0 0)';
const GREEN  = 'oklch(69.6% .17 162.48)';
const RED    = 'oklch(63.2% .204 25.331)';
const YELLOW = 'oklch(79.5% .184 86.047)';
const BLUE   = 'oklch(62.3% .214 259.815)';

interface RecordRow {
  lean_level: string;
  sport: string;
  record: string;
  win_rate: string;
  graded: number;
  total: number;
}

interface ApiResponse {
  record: RecordRow[];
  days: number;
  generated_at: string;
}

const DAYS_OPTIONS = [
  { label: '14D', value: 14 },
  { label: '30D', value: 30 },
  { label: '90D', value: 90 },
  { label: 'ALL', value: 365 },
];

function parseRecord(rec: string): [number, number, number] {
  const [w = 0, l = 0, p = 0] = rec.split('-').map(Number);
  return [w, l, p];
}

function winRateColor(rate: string): string {
  if (rate === 'N/A') return MUTED;
  const n = parseFloat(rate);
  return n >= 55 ? GREEN : n >= 48 ? YELLOW : RED;
}

function StatCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 10, padding: '18px 22px', flex: 1, minWidth: 120 }}>
      <div style={{ fontSize: '0.6rem', color: MUTED, letterSpacing: '0.09em', marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: '1.6rem', fontWeight: 800, color: color ?? FG, fontFamily: 'Nunito', lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontSize: '0.62rem', color: MUTED, marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function LeanBadge({ level }: { level: string }) {
  const isStrong = level === 'strong_lean';
  return (
    <span style={{
      fontSize: '0.6rem', fontWeight: 700, letterSpacing: '0.07em',
      color: isStrong ? GREEN : BLUE,
      border: `1px solid ${isStrong ? GREEN : BLUE}`,
      borderRadius: 4, padding: '2px 7px',
    }}>
      {isStrong ? 'STRONG' : 'FAVORABLE'}
    </span>
  );
}

export function AccuracyDashboard() {
  const [days, setDays] = useState(30);
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(getApiUrl(`v1/evaluations/record?days=${days}`))
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [days]);

  const rows: RecordRow[] = data?.record ?? [];

  // Aggregate totals
  const totals = rows.reduce((acc, r) => {
    const [w, l, p] = parseRecord(r.record);
    return { w: acc.w + w, l: acc.l + l, p: acc.p + p, graded: acc.graded + r.graded, total: acc.total + r.total };
  }, { w: 0, l: 0, p: 0, graded: 0, total: 0 });

  const overallWR = totals.graded > 0 ? `${(totals.w / totals.graded * 100).toFixed(1)}%` : 'N/A';
  const pending   = totals.total - totals.graded;

  // Group by sport for display
  const sports = [...new Set(rows.map(r => r.sport))].sort();

  return (
    <div style={{ background: BG, minHeight: '100vh', padding: '32px 24px', color: FG }}>
      <div style={{ maxWidth: 900, margin: '0 auto' }}>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16, marginBottom: 28 }}>
          <div>
            <div style={{ fontSize: '0.6rem', color: MUTED, letterSpacing: '0.12em', marginBottom: 6 }}>
              HANDICAPPING AGENT · LIVE RECORD
            </div>
            <h1 style={{ fontSize: '1.9rem', fontWeight: 800, fontFamily: 'Nunito', margin: 0, lineHeight: 1.1 }}>
              Picks Record
            </h1>
            <p style={{ color: MUTED, marginTop: 6, fontSize: '0.8rem' }}>ATS results for FAVORABLE_LEAN and STRONG_LEAN evaluations. Graded automatically from ESPN final scores.</p>
          </div>
          {/* Days filter */}
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            {DAYS_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => setDays(opt.value)}
                style={{
                  padding: '6px 14px', borderRadius: 6, fontSize: '0.7rem', fontWeight: 700,
                  border: `1px solid ${days === opt.value ? BLUE : BORDER}`,
                  background: days === opt.value ? `${BLUE}22` : 'transparent',
                  color: days === opt.value ? BLUE : MUTED,
                  cursor: 'pointer',
                }}
              >{opt.label}</button>
            ))}
          </div>
        </div>

        {/* Hero stats */}
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 28 }}>
          <StatCard label="OVERALL RECORD" value={loading ? '—' : `${totals.w}-${totals.l}-${totals.p}`} sub="W-L-P (ATS)" />
          <StatCard label="WIN RATE" value={loading ? '—' : overallWR} sub="graded plays only" color={loading ? FG : winRateColor(overallWR)} />
          <StatCard label="GRADED" value={loading ? '—' : totals.graded.toString()} sub={`of ${totals.total} total evals`} color={BLUE} />
          <StatCard label="PENDING" value={loading ? '—' : pending.toString()} sub="awaiting final scores" color={pending > 0 ? YELLOW : MUTED} />
        </div>

        {/* Record table */}
        <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 12, overflow: 'hidden', marginBottom: 20 }}>
          <div style={{ padding: '14px 20px', borderBottom: `1px solid ${BORDER}` }}>
            <div style={{ fontWeight: 700, fontSize: '0.85rem', fontFamily: 'Nunito' }}>Breakdown by Sport & Lean Level</div>
          </div>

          {loading ? (
            <div style={{ padding: 48, textAlign: 'center', color: MUTED }}>Loading...</div>
          ) : rows.length === 0 ? (
            <div style={{ padding: 48, textAlign: 'center', color: MUTED }}>No graded evaluations in this window yet.</div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${BORDER}` }}>
                  {['Sport', 'Lean Level', 'Record', 'Win Rate', 'Graded', 'Pending'].map(h => (
                    <th key={h} style={{ padding: '10px 16px', textAlign: 'left', color: MUTED, fontWeight: 600, fontSize: '0.62rem', letterSpacing: '0.07em' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sports.flatMap(sport =>
                  rows.filter(r => r.sport === sport).map((r, i) => {
                    const [w, l, p] = parseRecord(r.record);
                    const pend = r.total - r.graded;
                    return (
                      <tr key={`${sport}-${r.lean_level}`} style={{ borderBottom: `1px solid ${BORDER}`, background: i % 2 === 0 ? 'transparent' : 'oklch(100% 0 0 / .02)' }}>
                        <td style={{ padding: '12px 16px', fontWeight: 700, color: FG, fontFamily: 'Nunito' }}>{sport}</td>
                        <td style={{ padding: '12px 16px' }}><LeanBadge level={r.lean_level} /></td>
                        <td style={{ padding: '12px 16px', fontWeight: 700, color: FG }}>{w}-{l}-{p}</td>
                        <td style={{ padding: '12px 16px', fontWeight: 700, color: winRateColor(r.win_rate) }}>{r.win_rate}</td>
                        <td style={{ padding: '12px 16px', color: MUTED }}>{r.graded}</td>
                        <td style={{ padding: '12px 16px', color: pend > 0 ? YELLOW : MUTED }}>{pend > 0 ? `${pend} pending` : '—'}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          )}
        </div>

        {/* Context note */}
        <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 10, padding: '16px 20px' }}>
          <div style={{ fontSize: '0.7rem', color: MUTED, lineHeight: 1.7 }}>
            <strong style={{ color: FG }}>How grading works:</strong> The result grader runs at midnight + 3am CST daily.
            It pulls final scores from ESPN and grades each evaluation against the lean_market (spread / moneyline / total).
            Games without final scores remain pending. A breakeven win rate is ~52.4% at standard juice (-110).
          </div>
        </div>

        {data?.generated_at && (
          <div style={{ fontSize: '0.6rem', color: MUTED, marginTop: 16, textAlign: 'right' }}>
            Updated: {new Date(data.generated_at).toLocaleString('en-US', { timeZone: 'America/Chicago', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })} CST
          </div>
        )}
      </div>
    </div>
  );
}

export default AccuracyDashboard;
