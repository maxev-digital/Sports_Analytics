/**
 * F5 Betting Table — Team-level F5 betting stats that ESPN doesn't show.
 * F5 records, home/away splits, scoring, tie rates, shutout rates.
 */

const EMERALD   = 'oklch(69.6% .17 162.48)';
const BRAND_RED = 'oklch(63.7% .237 25.331)';
const BLUE      = 'oklch(62.3% .214 259.815)';
const MUTED_FG  = 'oklch(70.8% 0 0)';
const BORDER    = 'oklch(100% 0 0 / .1)';
const FG        = 'oklch(98.5% 0 0)';

interface F5Team {
  team: string;
  games: number;
  f5_record: string;
  f5_win_pct: number;
  f5_tie_pct: number;
  home_f5_record: string;
  away_f5_record: string;
  f5_rpg: number;
  f5_rapg: number;
  f5_diff: number;
  home_f5_rpg: number;
  away_f5_rpg: number;
  home_f5_rapg: number;
  away_f5_rapg: number;
  f5_shutout_pct: number;
  f5_opp_shutout_pct: number;
  blowout_pct: number;
  f1_scoreless_pct: number;
  f5_under_5_pct: number;
}

const COLS: { key: string; label: string; align: 'left' | 'right'; format?: (v: any) => string; color?: (v: any) => string }[] = [
  { key: 'team', label: 'Team', align: 'left' },
  { key: 'games', label: 'GP', align: 'right' },
  { key: 'f5_record', label: 'F5 Record', align: 'right' },
  { key: 'f5_win_pct', label: 'F5 W%', align: 'right', format: v => `${v}%`, color: v => v > 48 ? EMERALD : v < 40 ? BRAND_RED : FG },
  { key: 'f5_tie_pct', label: 'Tie%', align: 'right', format: v => `${v}%`, color: v => v > 16 ? EMERALD : FG },
  { key: 'home_f5_record', label: 'Home F5', align: 'right' },
  { key: 'away_f5_record', label: 'Away F5', align: 'right' },
  { key: 'f5_rpg', label: 'F5 RPG', align: 'right', format: v => v.toFixed(2), color: v => v > 2.8 ? EMERALD : v < 2.2 ? BRAND_RED : FG },
  { key: 'f5_rapg', label: 'F5 RAPG', align: 'right', format: v => v.toFixed(2), color: v => v < 2.2 ? EMERALD : v > 2.8 ? BRAND_RED : FG },
  { key: 'f5_diff', label: 'F5 Diff', align: 'right', format: v => `${v > 0 ? '+' : ''}${v.toFixed(2)}`, color: v => v > 0 ? EMERALD : v < 0 ? BRAND_RED : FG },
  { key: 'home_f5_rpg', label: 'Home RPG', align: 'right', format: v => v.toFixed(2) },
  { key: 'away_f5_rpg', label: 'Away RPG', align: 'right', format: v => v.toFixed(2) },
  { key: 'f5_under_5_pct', label: 'U5%', align: 'right', format: v => `${v}%`, color: v => v > 52 ? EMERALD : FG },
  { key: 'blowout_pct', label: 'Blowout%', align: 'right', format: v => `${v}%`, color: v => v > 25 ? EMERALD : FG },
  { key: 'f5_shutout_pct', label: 'Shutout%', align: 'right', format: v => `${v}%`, color: v => v < 15 ? EMERALD : v > 25 ? BRAND_RED : FG },
  { key: 'f1_scoreless_pct', label: 'F1 0%', align: 'right', format: v => `${v}%` },
];

export function F5BettingTable({ teams }: { teams: F5Team[] }) {
  if (!teams.length) {
    return <div style={{ padding: 40, textAlign: 'center', color: MUTED_FG }}>No F5 betting data available</div>;
  }

  return (
    <div>
      <div style={{ marginBottom: 12, fontSize: '0.75rem', color: MUTED_FG }}>
        2026 First Half (Apr–Jul) · {teams.length} teams · Stats you won't find on ESPN: F5 records, tie rates, under rates, shutout frequency, home/away F5 splits
      </div>
      <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
          <thead>
            <tr>
              {COLS.map(c => (
                <th key={c.key} style={{
                  padding: '8px 8px', textAlign: c.align,
                  fontSize: '0.6rem', fontWeight: 700, color: MUTED_FG,
                  letterSpacing: '0.08em', textTransform: 'uppercase',
                  borderBottom: `1px solid ${BORDER}`, whiteSpace: 'nowrap',
                }}>{c.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {teams.map((t, idx) => (
              <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
                {COLS.map(c => {
                  const raw = (t as any)[c.key];
                  const display = c.format ? c.format(raw) : raw;
                  const color = c.color ? c.color(raw) : (c.key === 'team' ? FG : MUTED_FG);
                  return (
                    <td key={c.key} style={{
                      padding: '6px 8px', textAlign: c.align, whiteSpace: 'nowrap',
                      fontFamily: c.key === 'team' ? 'Nunito' : 'var(--d3-mono)',
                      fontWeight: c.key === 'team' || c.key === 'f5_win_pct' || c.key === 'f5_diff' ? 700 : 400,
                      color,
                    }}>{display}</td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default F5BettingTable;
