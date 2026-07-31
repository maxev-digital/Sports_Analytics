/**
 * Venue edge table — shows under/over/fav/tie rates by ballpark.
 */
import { EMERALD, BRAND_RED, MUTED_FG, BORDER, FG, plColor, fmtPct } from './tokens';
import type { VenueEdge } from './types';

const VENUE_DATA: VenueEdge[] = [
  { venue: 'Globe Life Field', games: 76, under_pct: 64, under_roi: 22.9, over_pct: 36, over_roi: -32.0, tie_pct: 20, fav_pct: 50, fav_roi: -7.1 },
  { venue: 'Kauffman Stadium', games: 77, under_pct: 62, under_roi: 16.5, over_pct: 38, over_roi: -28.6, tie_pct: 17, fav_pct: 53, fav_roi: -4.8 },
  { venue: 'Comerica Park', games: 85, under_pct: 61, under_roi: 12.8, over_pct: 39, over_roi: -24.1, tie_pct: 12, fav_pct: 61, fav_roi: 9.1 },
  { venue: 'Wrigley Field', games: 82, under_pct: 59, under_roi: 12.9, over_pct: 41, over_roi: -22.6, tie_pct: 15, fav_pct: 46, fav_roi: -17.4 },
  { venue: 'Citi Field', games: 84, under_pct: 59, under_roi: 12.0, over_pct: 41, over_roi: -21.2, tie_pct: 18, fav_pct: 43, fav_roi: -26.0 },
  { venue: 'Progressive Field', games: 86, under_pct: 39, under_roi: -28.9, over_pct: 61, over_roi: 17.6, tie_pct: 7, fav_pct: 62, fav_roi: 16.6 },
  { venue: 'loanDepot park', games: 81, under_pct: 37, under_roi: -30.3, over_pct: 63, over_roi: 20.0, tie_pct: 9, fav_pct: 54, fav_roi: -2.4 },
  { venue: 'Angel Stadium', games: 73, under_pct: 39, under_roi: -25.7, over_pct: 61, over_roi: 14.8, tie_pct: 16, fav_pct: 47, fav_roi: -17.3 },
  { venue: 'Chase Field', games: 77, under_pct: 41, under_roi: -21.9, over_pct: 59, over_roi: 13.3, tie_pct: 21, fav_pct: 51, fav_roi: 3.9 },
  { venue: 'Target Field', games: 83, under_pct: 42, under_roi: -21.0, over_pct: 58, over_roi: 10.9, tie_pct: 13, fav_pct: 53, fav_roi: 1.4 },
];

export function VenueTable() {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
        <thead>
          <tr>
            {['Venue', 'Games', 'U%', 'U ROI', 'O%', 'O ROI', 'Tie%', 'Fav%', 'F ROI'].map((h) => (
              <th key={h} style={{
                padding: '8px 10px', textAlign: h === 'Venue' ? 'left' : 'right',
                fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG,
                letterSpacing: '0.1em', textTransform: 'uppercase',
                borderBottom: `1px solid ${BORDER}`,
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {VENUE_DATA.map((v) => (
            <tr key={v.venue} style={{ borderBottom: `1px solid ${BORDER}` }}>
              <td style={{ padding: '8px 10px', fontWeight: 600, color: FG }}>{v.venue}</td>
              <td style={{ padding: '8px 10px', textAlign: 'right', color: MUTED_FG, fontFamily: 'var(--d3-mono)' }}>{v.games}</td>
              <td style={{ padding: '8px 10px', textAlign: 'right', color: v.under_pct > 55 ? EMERALD : FG, fontWeight: 700, fontFamily: 'var(--d3-mono)' }}>{v.under_pct}%</td>
              <td style={{ padding: '8px 10px', textAlign: 'right', color: plColor(v.under_roi), fontFamily: 'var(--d3-mono)' }}>{fmtPct(v.under_roi)}</td>
              <td style={{ padding: '8px 10px', textAlign: 'right', color: v.over_pct > 55 ? EMERALD : FG, fontWeight: 700, fontFamily: 'var(--d3-mono)' }}>{v.over_pct}%</td>
              <td style={{ padding: '8px 10px', textAlign: 'right', color: plColor(v.over_roi), fontFamily: 'var(--d3-mono)' }}>{fmtPct(v.over_roi)}</td>
              <td style={{ padding: '8px 10px', textAlign: 'right', color: v.tie_pct > 17 ? EMERALD : FG, fontFamily: 'var(--d3-mono)' }}>{v.tie_pct}%</td>
              <td style={{ padding: '8px 10px', textAlign: 'right', color: v.fav_pct > 58 ? EMERALD : FG, fontFamily: 'var(--d3-mono)' }}>{v.fav_pct}%</td>
              <td style={{ padding: '8px 10px', textAlign: 'right', color: plColor(v.fav_roi), fontFamily: 'var(--d3-mono)' }}>{fmtPct(v.fav_roi)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
