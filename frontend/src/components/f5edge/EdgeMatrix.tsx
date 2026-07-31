/**
 * Edge Matrix — interactive research data table.
 * Shows actual hit rates by condition vs book implied.
 */
import { useState } from 'react';
import { Badge } from './Badge';
import { EMERALD, BRAND_RED, MUTED_FG, BORDER, CARD_BG, FG, YELLOW, plColor, fmtPct } from './tokens';

interface MatrixRow {
  condition: string;
  games: number;
  tie_rate: number;
  under_rate: number;
  over_rate: number;
  fav_rate: number;
  fav_roi: number;
  tie_implied: number;
}

const MATRIX_DATA: MatrixRow[] = [
  { condition: 'All Games (baseline)', games: 2427, tie_rate: 14.1, under_rate: 50.0, over_rate: 50.0, fav_rate: 53.0, fav_roi: -3.4, tie_implied: 17.7 },
  { condition: 'Ace vs Ace (ERA < 3.50)', games: 187, tie_rate: 21.9, under_rate: 58.8, over_rate: 41.2, fav_rate: 42.5, fav_roi: -18.5, tie_implied: 18.4 },
  { condition: 'Both ERA < 4.00', games: 597, tie_rate: 17.3, under_rate: 55.9, over_rate: 44.1, fav_rate: 47.3, fav_roi: -3.4, tie_implied: 18.2 },
  { condition: 'Both ERA < 4.50', games: 1186, tie_rate: 16.6, under_rate: 55.0, over_rate: 45.0, fav_rate: 48.6, fav_roi: -6.9, tie_implied: 18.0 },
  { condition: 'ERA diff ≥ 1.0', games: 1159, tie_rate: 13.4, under_rate: 49.2, over_rate: 50.8, fav_rate: 59.8, fav_roi: 6.4, tie_implied: 17.5 },
  { condition: 'ERA diff ≥ 1.5', games: 756, tie_rate: 11.2, under_rate: 45.6, over_rate: 54.4, fav_rate: 63.4, fav_roi: 11.7, tie_implied: 17.4 },
  { condition: 'ERA diff ≥ 1.5 + Hitter Park', games: 284, tie_rate: 9.2, under_rate: 45.4, over_rate: 54.6, fav_rate: 65.8, fav_roi: 17.0, tie_implied: 17.1 },
  { condition: 'Pitcher Park', games: 937, tie_rate: 14.1, under_rate: 51.0, over_rate: 49.0, fav_rate: 52.3, fav_roi: -6.2, tie_implied: 18.1 },
  { condition: 'Chase Field', games: 77, tie_rate: 20.8, under_rate: 41.0, over_rate: 59.0, fav_rate: 51.0, fav_roi: 3.9, tie_implied: 17.0 },
  { condition: 'Globe Life Field', games: 76, tie_rate: 19.7, under_rate: 64.0, over_rate: 36.0, fav_rate: 50.0, fav_roi: -7.1, tie_implied: 17.5 },
  { condition: 'Coors Field', games: 78, tie_rate: 11.5, under_rate: 55.0, over_rate: 45.0, fav_rate: 56.0, fav_roi: -0.6, tie_implied: 15.1 },
  { condition: 'High-Tie Umpire (21 umps)', games: 574, tie_rate: 19.5, under_rate: 52.0, over_rate: 48.0, fav_rate: 51.0, fav_roi: -4.0, tie_implied: 17.6 },
  { condition: 'Low-Tie Umpire (13 umps)', games: 358, tie_rate: 7.5, under_rate: 48.0, over_rate: 52.0, fav_rate: 55.0, fav_roi: 2.0, tie_implied: 17.5 },
];

export function EdgeMatrix() {
  const [sortKey, setSortKey] = useState<keyof MatrixRow>('tie_rate');
  const [sortDesc, setSortDesc] = useState(true);

  const sorted = [...MATRIX_DATA].sort((a, b) => {
    const av = a[sortKey] as number;
    const bv = b[sortKey] as number;
    return sortDesc ? bv - av : av - bv;
  });

  const handleSort = (key: keyof MatrixRow) => {
    if (sortKey === key) setSortDesc(!sortDesc);
    else { setSortKey(key); setSortDesc(true); }
  };

  const th = (label: string, key: keyof MatrixRow) => (
    <th
      onClick={() => handleSort(key)}
      style={{ cursor: 'pointer', padding: '8px 10px', textAlign: 'right', fontSize: '0.65rem', fontWeight: 700,
               color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', borderBottom: `1px solid ${BORDER}`,
               userSelect: 'none' }}
    >
      {label} {sortKey === key ? (sortDesc ? '▼' : '▲') : ''}
    </th>
  );

  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
        <thead>
          <tr>
            <th style={{ padding: '8px 10px', textAlign: 'left', fontSize: '0.65rem', fontWeight: 700,
                         color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase',
                         borderBottom: `1px solid ${BORDER}` }}>
              Condition
            </th>
            {th('Games', 'games')}
            {th('Tie %', 'tie_rate')}
            {th('Implied', 'tie_implied')}
            {th('Under %', 'under_rate')}
            {th('Over %', 'over_rate')}
            {th('Fav %', 'fav_rate')}
            {th('Fav ROI', 'fav_roi')}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => {
            const tieEdge = row.tie_rate - row.tie_implied;
            return (
              <tr key={row.condition} style={{ borderBottom: `1px solid ${BORDER}` }}>
                <td style={{ padding: '8px 10px', fontWeight: 600, color: FG }}>{row.condition}</td>
                <td style={{ padding: '8px 10px', textAlign: 'right', color: MUTED_FG, fontFamily: 'var(--d3-mono)' }}>{row.games.toLocaleString()}</td>
                <td style={{ padding: '8px 10px', textAlign: 'right', color: tieEdge > 2 ? EMERALD : tieEdge < -2 ? BRAND_RED : FG, fontWeight: 700, fontFamily: 'var(--d3-mono)' }}>{row.tie_rate}%</td>
                <td style={{ padding: '8px 10px', textAlign: 'right', color: MUTED_FG, fontFamily: 'var(--d3-mono)' }}>{row.tie_implied}%</td>
                <td style={{ padding: '8px 10px', textAlign: 'right', color: row.under_rate > 54 ? EMERALD : FG, fontWeight: row.under_rate > 54 ? 700 : 400, fontFamily: 'var(--d3-mono)' }}>{row.under_rate}%</td>
                <td style={{ padding: '8px 10px', textAlign: 'right', color: row.over_rate > 54 ? EMERALD : FG, fontWeight: row.over_rate > 54 ? 700 : 400, fontFamily: 'var(--d3-mono)' }}>{row.over_rate}%</td>
                <td style={{ padding: '8px 10px', textAlign: 'right', color: row.fav_rate > 58 ? EMERALD : FG, fontFamily: 'var(--d3-mono)' }}>{row.fav_rate}%</td>
                <td style={{ padding: '8px 10px', textAlign: 'right', color: plColor(row.fav_roi), fontWeight: 700, fontFamily: 'var(--d3-mono)' }}>{fmtPct(row.fav_roi)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
