/**
 * Signal performance dashboard — shows all proven/promising signals
 * with their historical stats.
 */
import { Badge } from './Badge';
import { EMERALD, BLUE, BRAND_RED, YELLOW, MUTED_FG, BORDER, CARD_BG, FG, fmtPct, plColor } from './tokens';
import type { SignalStats } from './types';

const SIGNALS: SignalStats[] = [
  {
    name: 'F5 Tie + Under SGP',
    description: 'Same-game parlay on qualifying ace matchups. 1.51x correlation.',
    bets: 292, wins: 53, win_rate: 18.2, roi: 94.2, pl: 6873,
    p_value: null, status: 'proven',
  },
  {
    name: 'F1 Tie + FG Under SGP',
    description: 'Bovada SGP. FG total ≤ 8.0, both ERA < 4.50.',
    bets: 612, wins: 229, win_rate: 37.4, roi: 50.3, pl: 7699,
    p_value: null, status: 'proven',
  },
  {
    name: 'F5 Tie (Ace vs Ace)',
    description: 'Both starters ERA < 3.50. Bet at BetMGM.',
    bets: 187, wins: 41, win_rate: 21.9, roi: 22.0, pl: 4110,
    p_value: 0.10, status: 'promising',
  },
  {
    name: 'F5 Fav ML (ERA diff ≥ 1.5 + Hitter Park)',
    description: 'Heavy mismatch at a hitter park.',
    bets: 284, wins: 187, win_rate: 65.8, roi: 17.0, pl: 4842,
    p_value: 0.0002, status: 'proven',
  },
  {
    name: 'F5 Fav ML (ERA diff ≥ 1.0)',
    description: 'Pitching mismatch — favorite leads after 5.',
    bets: 1159, wins: 693, win_rate: 59.8, roi: 6.4, pl: 7374,
    p_value: 0.0004, status: 'proven',
  },
  {
    name: 'F5 Under (Both ERA < 3.50)',
    description: 'Ace matchup — scoring suppressed through 5.',
    bets: 182, wins: 107, win_rate: 58.8, roi: 10.7, pl: 1952,
    p_value: 0.009, status: 'proven',
  },
  {
    name: 'F5 Under (Both ERA < 4.50)',
    description: 'Decent pitching matchup — broadest under filter.',
    bets: 1144, wins: 629, win_rate: 55.0, roi: 3.2, pl: 3675,
    p_value: 0.0004, status: 'proven',
  },
];

function statusColor(s: string): string {
  if (s === 'proven') return EMERALD;
  if (s === 'promising') return YELLOW;
  return BRAND_RED;
}

export function SignalTable() {
  return (
    <div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {SIGNALS.map((s) => (
          <div key={s.name} className="data-table-wrap" style={{
            padding: '14px 18px',
            borderLeft: `3px solid ${statusColor(s.status)}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Badge color={statusColor(s.status)} label={s.status} />
                <span style={{ fontWeight: 800, fontSize: '0.82rem', color: FG }}>{s.name}</span>
              </div>
              <span style={{ fontWeight: 800, fontSize: '1rem', color: plColor(s.pl), fontFamily: 'var(--d3-mono)' }}>
                +${s.pl.toLocaleString()}
              </span>
            </div>

            <div style={{ fontSize: '0.72rem', color: MUTED_FG, marginBottom: 8 }}>{s.description}</div>

            <div style={{ display: 'flex', gap: 20, fontSize: '0.72rem' }}>
              <StatPill label="Bets" value={s.bets.toLocaleString()} />
              <StatPill label="Wins" value={s.wins.toString()} />
              <StatPill label="Win %" value={`${s.win_rate}%`} color={s.win_rate > 50 ? EMERALD : FG} />
              <StatPill label="ROI" value={fmtPct(s.roi)} color={plColor(s.roi)} />
              {s.p_value !== null && (
                <StatPill
                  label="P-value"
                  value={s.p_value < 0.001 ? '<0.001' : s.p_value.toFixed(3)}
                  color={s.p_value < 0.05 ? EMERALD : YELLOW}
                />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatPill({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <span>
      <span style={{ color: MUTED_FG }}>{label}: </span>
      <span style={{ color: color ?? FG, fontWeight: 700, fontFamily: 'var(--d3-mono)' }}>{value}</span>
    </span>
  );
}
