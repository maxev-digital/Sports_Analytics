/**
 * Betting Rankings — FG + F5 team betting stats.
 * Data you can't find on ESPN: F5 records, tie rates, home/away splits,
 * scoring differentials at both full-game and first-5 level.
 */
import { useState, useEffect } from 'react';
import '../styles/analytics.css';
import { getApiUrl } from '../config';

const EMERALD   = 'oklch(69.6% .17 162.48)';
const BRAND_RED = 'oklch(63.7% .237 25.331)';
const BLUE      = 'oklch(62.3% .214 259.815)';
const MUTED_FG  = 'oklch(70.8% 0 0)';
const BORDER    = 'oklch(100% 0 0 / .1)';
const FG        = 'oklch(98.5% 0 0)';

type View = 'full_game' | 'first_5' | 'splits';

export function BettingRankings() {
  const [teams, setTeams] = useState<any[]>([]);
  const [view, setView] = useState<View>('full_game');
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState('fg_win_pct');
  const [sortDesc, setSortDesc] = useState(true);

  useEffect(() => {
    fetch(getApiUrl('f5/team-rankings'))
      .then(r => r.json())
      .then(d => setTeams(d.teams ?? []))
      .catch(() => setTeams([]))
      .finally(() => setLoading(false));
  }, []);

  const handleSort = (key: string) => {
    if (sortKey === key) setSortDesc(!sortDesc);
    else { setSortKey(key); setSortDesc(true); }
  };

  const sorted = [...teams].sort((a, b) => {
    const av = a[sortKey] ?? 0;
    const bv = b[sortKey] ?? 0;
    return sortDesc ? bv - av : av - bv;
  });

  const VIEWS: { key: View; label: string }[] = [
    { key: 'full_game', label: 'FULL GAME' },
    { key: 'first_5', label: 'FIRST 5 INNINGS' },
    { key: 'splits', label: 'HOME / AWAY SPLITS' },
  ];

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1>Betting Rankings</h1>
        <p className="subtitle">
          MLB team betting analytics — full-game and first-5 records, scoring splits, and trends you won't find on ESPN
        </p>
        <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
          {VIEWS.map(v => (
            <button key={v.key} className={`filter-pill ${view === v.key ? 'active' : ''}`} onClick={() => {
              setView(v.key);
              setSortKey(v.key === 'full_game' ? 'fg_win_pct' : v.key === 'first_5' ? 'f5_win_pct' : 'fg_home_rpg');
            }}>
              {v.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ padding: '8px 24px', fontSize: '0.72rem', color: MUTED_FG }}>
        2026 First Half (Apr–Jul) · {teams.length} teams · Click column headers to sort
      </div>

      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: MUTED_FG }}>Loading...</div>
      ) : (
        <div style={{ padding: '0 24px 24px', maxWidth: 1400 }}>
          {view === 'full_game' && <FullGameTable teams={sorted} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} />}
          {view === 'first_5' && <F5Table teams={sorted} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} />}
          {view === 'splits' && <SplitsTable teams={sorted} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} />}
        </div>
      )}
    </div>
  );
}

function SortHeader({ label, field, sortKey, sortDesc, onSort }: {
  label: string; field: string; sortKey: string; sortDesc: boolean; onSort: (k: string) => void;
}) {
  return (
    <th onClick={() => onSort(field)} style={{
      padding: '8px 8px', textAlign: field === 'team' ? 'left' : 'right',
      fontSize: '0.6rem', fontWeight: 700, color: sortKey === field ? EMERALD : MUTED_FG,
      letterSpacing: '0.08em', textTransform: 'uppercase', cursor: 'pointer',
      borderBottom: `1px solid ${BORDER}`, whiteSpace: 'nowrap', userSelect: 'none',
    }}>
      {label} {sortKey === field ? (sortDesc ? '▼' : '▲') : ''}
    </th>
  );
}

function Cell({ value, format, color, bold }: { value: any; format?: (v: any) => string; color?: string; bold?: boolean }) {
  const display = format ? format(value) : value;
  return (
    <td style={{
      padding: '6px 8px', textAlign: 'right', whiteSpace: 'nowrap',
      fontFamily: 'var(--d3-mono)', fontWeight: bold ? 700 : 400,
      color: color ?? MUTED_FG,
    }}>{display}</td>
  );
}

function diffColor(v: number): string { return v > 0 ? EMERALD : v < 0 ? BRAND_RED : MUTED_FG; }
function pctColor(v: number, good: number, bad: number): string { return v > good ? EMERALD : v < bad ? BRAND_RED : FG; }
function fmtDiff(v: number): string { return `${v > 0 ? '+' : ''}${v.toFixed(2)}`; }

function FullGameTable({ teams, sortKey, sortDesc, onSort }: any) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortHeader label="Team" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="GP" field="games" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="Record" field="fg_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="Win%" field="fg_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="RPG" field="fg_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="RAPG" field="fg_rapg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="Diff" field="fg_diff" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="Home" field="fg_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="Away" field="fg_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="F5 W%" field="f5_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="F5 Diff" field="f5_diff" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="Tie%" field="f5_tie_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => (
            <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
              <td style={{ padding: '6px 8px', fontWeight: 700, color: FG, fontFamily: 'Nunito' }}>{t.team}</td>
              <Cell value={t.games} />
              <Cell value={t.fg_record} color={FG} />
              <Cell value={`${t.fg_win_pct}%`} color={pctColor(t.fg_win_pct, 52, 45)} bold />
              <Cell value={t.fg_rpg.toFixed(2)} color={pctColor(t.fg_rpg, 4.5, 3.5)} />
              <Cell value={t.fg_rapg.toFixed(2)} color={pctColor(-t.fg_rapg, -3.5, -4.5)} />
              <Cell value={fmtDiff(t.fg_diff)} color={diffColor(t.fg_diff)} bold />
              <Cell value={t.fg_home_rpg.toFixed(2)} />
              <Cell value={t.fg_away_rpg.toFixed(2)} />
              <Cell value={`${t.f5_win_pct}%`} color={pctColor(t.f5_win_pct, 48, 40)} />
              <Cell value={fmtDiff(t.f5_diff)} color={diffColor(t.f5_diff)} />
              <Cell value={`${t.f5_tie_pct}%`} color={t.f5_tie_pct > 16 ? BLUE : MUTED_FG} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function F5Table({ teams, sortKey, sortDesc, onSort }: any) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortHeader label="Team" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="F5 Record" field="f5_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="F5 W%" field="f5_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="Tie%" field="f5_tie_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="F5 RPG" field="f5_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="F5 RAPG" field="f5_rapg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="F5 Diff" field="f5_diff" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="Home F5" field="f5_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="Away F5" field="f5_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="U5%" field="f5_under_5_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="Blowout%" field="blowout_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="Shutout%" field="f5_shutout_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="F1 0%" field="f1_scoreless_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => (
            <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
              <td style={{ padding: '6px 8px', fontWeight: 700, color: FG, fontFamily: 'Nunito' }}>{t.team}</td>
              <Cell value={t.f5_record} color={FG} />
              <Cell value={`${t.f5_win_pct}%`} color={pctColor(t.f5_win_pct, 48, 40)} bold />
              <Cell value={`${t.f5_tie_pct}%`} color={t.f5_tie_pct > 16 ? BLUE : MUTED_FG} />
              <Cell value={t.f5_rpg.toFixed(2)} color={pctColor(t.f5_rpg, 2.8, 2.2)} />
              <Cell value={t.f5_rapg.toFixed(2)} color={pctColor(-t.f5_rapg, -2.2, -2.8)} />
              <Cell value={fmtDiff(t.f5_diff)} color={diffColor(t.f5_diff)} bold />
              <Cell value={t.f5_home_rpg.toFixed(2)} />
              <Cell value={t.f5_away_rpg.toFixed(2)} />
              <Cell value={`${t.f5_under_5_pct}%`} color={t.f5_under_5_pct > 52 ? EMERALD : MUTED_FG} />
              <Cell value={`${t.blowout_pct}%`} color={t.blowout_pct > 25 ? EMERALD : MUTED_FG} />
              <Cell value={`${t.f5_shutout_pct}%`} color={t.f5_shutout_pct > 25 ? BRAND_RED : MUTED_FG} />
              <Cell value={`${t.f1_scoreless_pct}%`} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SplitsTable({ teams, sortKey, sortDesc, onSort }: any) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortHeader label="Team" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="FG Home" field="fg_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="FG Away" field="fg_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="FG H-A Gap" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="F5 Home" field="f5_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="F5 Away" field="f5_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="F5 H-A Gap" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="Home FG Rec" field="fg_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="Away FG Rec" field="fg_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="Home F5 Rec" field="f5_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortHeader label="Away F5 Rec" field="f5_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => {
            const fgGap = t.fg_home_rpg - t.fg_away_rpg;
            const f5Gap = t.f5_home_rpg - t.f5_away_rpg;
            return (
              <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
                <td style={{ padding: '6px 8px', fontWeight: 700, color: FG, fontFamily: 'Nunito' }}>{t.team}</td>
                <Cell value={t.fg_home_rpg.toFixed(2)} color={pctColor(t.fg_home_rpg, 4.5, 3.5)} />
                <Cell value={t.fg_away_rpg.toFixed(2)} color={pctColor(t.fg_away_rpg, 4.5, 3.5)} />
                <Cell value={fmtDiff(fgGap)} color={diffColor(fgGap)} bold />
                <Cell value={t.f5_home_rpg.toFixed(2)} color={pctColor(t.f5_home_rpg, 2.8, 2.2)} />
                <Cell value={t.f5_away_rpg.toFixed(2)} color={pctColor(t.f5_away_rpg, 2.8, 2.2)} />
                <Cell value={fmtDiff(f5Gap)} color={diffColor(f5Gap)} bold />
                <Cell value={t.fg_home_record} color={FG} />
                <Cell value={t.fg_away_record} color={FG} />
                <Cell value={t.f5_home_record} color={FG} />
                <Cell value={t.f5_away_record} color={FG} />
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default BettingRankings;
