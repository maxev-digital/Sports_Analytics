/**
 * Betting Rankings — Multi-sport betting analytics.
 * Sport tabs at top, sport-specific view pills below.
 * MLB: Full Game, First 5 Innings, Home/Away Splits
 * NFL: (coming soon) ATS, Totals, Situational
 */
import { useState, useEffect } from 'react';
import '../styles/analytics.css';
import { getApiUrl } from '../config';

const EMERALD   = 'oklch(69.6% .17 162.48)';
const BRAND_RED = 'oklch(63.7% .237 25.331)';
const BLUE      = 'oklch(62.3% .214 259.815)';
const YELLOW    = 'oklch(79.5% .184 86.047)';
const MUTED_FG  = 'oklch(70.8% 0 0)';
const BORDER    = 'oklch(100% 0 0 / .1)';
const FG        = 'oklch(98.5% 0 0)';

type Sport = 'mlb' | 'nfl' | 'nba' | 'nhl' | 'ncaaf';

const SPORTS: { key: Sport; label: string; active: boolean }[] = [
  { key: 'mlb',   label: 'MLB',   active: true },
  { key: 'nfl',   label: 'NFL',   active: true },
  { key: 'ncaaf', label: 'NCAAF', active: true },
  { key: 'nba',   label: 'NBA',   active: true },
  { key: 'nhl',   label: 'NHL',   active: true },
];

const SPORT_VIEWS: Record<Sport, { key: string; label: string }[]> = {
  mlb:   [{ key: 'full_game', label: 'FULL GAME' }, { key: 'first_5', label: 'FIRST 5 INNINGS' }, { key: 'splits', label: 'HOME / AWAY SPLITS' }],
  nfl:   [{ key: 'full_game', label: 'FULL GAME' }, { key: 'first_half', label: 'FIRST HALF' }, { key: 'ats', label: 'ATS RECORD' }, { key: 'totals', label: 'TOTALS' }, { key: 'situational', label: 'SITUATIONAL' }],
  ncaaf: [{ key: 'full_game', label: 'FULL GAME' }, { key: 'ats', label: 'ATS RECORD' }, { key: 'totals', label: 'TOTALS' }],
  nba:   [{ key: 'full_game', label: 'FULL GAME' }, { key: 'first_half', label: 'FIRST HALF' }, { key: 'ats', label: 'ATS RECORD' }],
  nhl:   [{ key: 'full_game', label: 'FULL GAME' }, { key: 'totals', label: 'TOTALS' }],
};

export function BettingRankings() {
  const [sport, setSport] = useState<Sport>('mlb');
  const [view, setView] = useState('full_game');
  const [teams, setTeams] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState('fg_win_pct');
  const [sortDesc, setSortDesc] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(getApiUrl(`f5/team-rankings?sport=${sport}`))
      .then(r => r.json())
      .then(d => setTeams(d.teams ?? []))
      .catch(() => setTeams([]))
      .finally(() => setLoading(false));
  }, [sport]);

  useEffect(() => {
    setView('full_game');
    setSortKey('fg_win_pct');
  }, [sport]);

  const handleSort = (key: string) => {
    if (sortKey === key) setSortDesc(!sortDesc);
    else { setSortKey(key); setSortDesc(true); }
  };

  const sorted = [...teams].sort((a, b) => {
    const av = a[sortKey] ?? 0;
    const bv = b[sortKey] ?? 0;
    return sortDesc ? bv - av : av - bv;
  });

  const views = SPORT_VIEWS[sport] ?? [];
  const sportActive = SPORTS.find(s => s.key === sport)?.active ?? false;

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1>Betting Rankings</h1>
        <p className="subtitle">
          Team betting analytics across all sports — records, scoring splits, and trends you won't find on ESPN
        </p>

        {/* Sport tabs */}
        <div className="sport-tabs" style={{ marginTop: 12 }}>
          {SPORTS.map(s => (
            <button
              key={s.key}
              className={`sport-tab ${sport === s.key ? 'active' : ''}`}
              onClick={() => setSport(s.key)}
              style={{ opacity: s.active ? 1 : 0.5 }}
            >
              {s.label} {!s.active && '(SOON)'}
            </button>
          ))}
        </div>
      </div>

      {/* View pills — sport specific */}
      {views.length > 0 && (
        <div className="filter-bar">
          {views.map(v => (
            <button
              key={v.key}
              className={`filter-pill ${view === v.key ? 'active' : ''}`}
              onClick={() => { setView(v.key); setSortKey(v.key === 'first_5' ? 'f5_win_pct' : v.key === 'splits' ? 'fg_home_rpg' : 'fg_win_pct'); }}
              disabled={!sportActive && v.key !== 'full_game'}
            >
              {v.label}
            </button>
          ))}
          <span style={{ marginLeft: 'auto', fontSize: '0.72rem', color: MUTED_FG }}>
            {teams.length > 0 ? `${teams.length} teams · 2026 First Half` : ''}
          </span>
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: MUTED_FG }}>Loading...</div>
      ) : teams.length === 0 ? (
        <ComingSoon sport={sport} />
      ) : (
        <div style={{ padding: '0 24px 24px', maxWidth: 1400 }}>
          {sport === 'mlb' && view === 'full_game' && <MLBFullGame teams={sorted} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} />}
          {sport === 'mlb' && view === 'first_5' && <MLBF5 teams={sorted} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} />}
          {sport === 'mlb' && view === 'splits' && <MLBSplits teams={sorted} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} />}
          {sport !== 'mlb' && view === 'full_game' && <GenericFullGame teams={sorted} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} sport={sport} />}
          {sport !== 'mlb' && view === 'splits' && <GenericSplits teams={sorted} sortKey={sortKey} sortDesc={sortDesc} onSort={handleSort} />}
          {sport !== 'mlb' && view !== 'full_game' && view !== 'splits' && (
            <div style={{ padding: 40, textAlign: 'center', color: MUTED_FG }}>
              {view.replace('_', ' ').toUpperCase()} data coming soon for {sport.toUpperCase()}. Full game stats available now.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ComingSoon({ sport }: { sport: string }) {
  const labels: Record<string, string> = {
    nfl: 'NFL betting rankings will include ATS records, totals trends, first-half splits, and situational stats (home favorites, road dogs, divisional games, short rest).',
    ncaaf: 'College football rankings with ATS records, totals, and conference matchup data.',
    nba: 'NBA rankings with first-half splits, ATS records, and pace-adjusted metrics.',
    nhl: 'NHL rankings with goalie matchup data, special teams efficiency, and totals trends.',
  };
  return (
    <div style={{ padding: '60px 24px', textAlign: 'center' }}>
      <div style={{ fontSize: '1.2rem', fontWeight: 800, color: FG, marginBottom: 8 }}>{sport.toUpperCase()} — Coming Soon</div>
      <div style={{ fontSize: '0.85rem', color: MUTED_FG, maxWidth: 500, margin: '0 auto' }}>
        {labels[sport] ?? 'Betting rankings for this sport are in development.'}
      </div>
      <div style={{ fontSize: '0.75rem', color: MUTED_FG, marginTop: 16 }}>
        Season data will populate automatically when the {sport.toUpperCase()} season begins.
      </div>
    </div>
  );
}

/* ─── Shared Components ─── */

function SortTh({ label, field, sortKey, sortDesc, onSort }: {
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

function Td({ value, format, color, bold, align }: {
  value: any; format?: (v: any) => string; color?: string; bold?: boolean; align?: 'left' | 'right';
}) {
  return (
    <td style={{
      padding: '6px 8px', textAlign: align ?? 'right', whiteSpace: 'nowrap',
      fontFamily: 'var(--d3-mono)', fontWeight: bold ? 700 : 400, color: color ?? MUTED_FG,
    }}>{format ? format(value) : value}</td>
  );
}

function TeamTd({ name }: { name: string }) {
  return <td style={{ padding: '6px 8px', fontWeight: 700, color: FG, fontFamily: 'Nunito' }}>{name}</td>;
}

function diffColor(v: number): string { return v > 0 ? EMERALD : v < 0 ? BRAND_RED : MUTED_FG; }
function pctGood(v: number, good: number, bad: number): string { return v > good ? EMERALD : v < bad ? BRAND_RED : FG; }
function fmtDiff(v: number): string { return `${v > 0 ? '+' : ''}${v.toFixed(2)}`; }

/* ─── MLB Tables ─── */

function MLBFullGame({ teams, sortKey, sortDesc, onSort }: any) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortTh label="Team" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="GP" field="games" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Record" field="fg_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Win%" field="fg_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="RPG" field="fg_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="RAPG" field="fg_rapg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Diff" field="fg_diff" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Home RPG" field="fg_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Away RPG" field="fg_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 W%" field="f5_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 Diff" field="f5_diff" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Tie%" field="f5_tie_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => (
            <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
              <TeamTd name={t.team} />
              <Td value={t.games} />
              <Td value={t.fg_record} color={FG} />
              <Td value={`${t.fg_win_pct}%`} color={pctGood(t.fg_win_pct, 52, 45)} bold />
              <Td value={t.fg_rpg.toFixed(2)} color={pctGood(t.fg_rpg, 4.5, 3.5)} />
              <Td value={t.fg_rapg.toFixed(2)} color={pctGood(-t.fg_rapg, -3.5, -4.5)} />
              <Td value={fmtDiff(t.fg_diff)} color={diffColor(t.fg_diff)} bold />
              <Td value={t.fg_home_rpg.toFixed(2)} />
              <Td value={t.fg_away_rpg.toFixed(2)} />
              <Td value={`${t.f5_win_pct}%`} color={pctGood(t.f5_win_pct, 48, 40)} />
              <Td value={fmtDiff(t.f5_diff)} color={diffColor(t.f5_diff)} />
              <Td value={`${t.f5_tie_pct}%`} color={t.f5_tie_pct > 16 ? BLUE : MUTED_FG} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MLBF5({ teams, sortKey, sortDesc, onSort }: any) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortTh label="Team" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 Record" field="f5_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 W%" field="f5_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Tie%" field="f5_tie_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 RPG" field="f5_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 RAPG" field="f5_rapg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 Diff" field="f5_diff" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Home F5 RPG" field="f5_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Away F5 RPG" field="f5_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="U5%" field="f5_under_5_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Blowout%" field="blowout_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Shutout%" field="f5_shutout_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F1 0%" field="f1_scoreless_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => (
            <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
              <TeamTd name={t.team} />
              <Td value={t.f5_record} color={FG} />
              <Td value={`${t.f5_win_pct}%`} color={pctGood(t.f5_win_pct, 48, 40)} bold />
              <Td value={`${t.f5_tie_pct}%`} color={t.f5_tie_pct > 16 ? BLUE : MUTED_FG} />
              <Td value={t.f5_rpg.toFixed(2)} color={pctGood(t.f5_rpg, 2.8, 2.2)} />
              <Td value={t.f5_rapg.toFixed(2)} color={pctGood(-t.f5_rapg, -2.2, -2.8)} />
              <Td value={fmtDiff(t.f5_diff)} color={diffColor(t.f5_diff)} bold />
              <Td value={t.f5_home_rpg.toFixed(2)} />
              <Td value={t.f5_away_rpg.toFixed(2)} />
              <Td value={`${t.f5_under_5_pct}%`} color={t.f5_under_5_pct > 52 ? EMERALD : MUTED_FG} />
              <Td value={`${t.blowout_pct}%`} color={t.blowout_pct > 25 ? EMERALD : MUTED_FG} />
              <Td value={`${t.f5_shutout_pct}%`} color={t.f5_shutout_pct > 25 ? BRAND_RED : MUTED_FG} />
              <Td value={`${t.f1_scoreless_pct}%`} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MLBSplits({ teams, sortKey, sortDesc, onSort }: any) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortTh label="Team" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="FG Home Rec" field="fg_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="FG Home RPG" field="fg_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="FG Away Rec" field="fg_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="FG Away RPG" field="fg_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="FG H-A Gap" field="fg_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 Home Rec" field="f5_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 Home RPG" field="f5_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 Away Rec" field="f5_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 Away RPG" field="f5_away_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="F5 H-A Gap" field="f5_home_rpg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => {
            const fgGap = t.fg_home_rpg - t.fg_away_rpg;
            const f5Gap = t.f5_home_rpg - t.f5_away_rpg;
            return (
              <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
                <TeamTd name={t.team} />
                <Td value={t.fg_home_record} color={FG} />
                <Td value={t.fg_home_rpg.toFixed(2)} color={pctGood(t.fg_home_rpg, 4.5, 3.5)} />
                <Td value={t.fg_away_record} color={FG} />
                <Td value={t.fg_away_rpg.toFixed(2)} color={pctGood(t.fg_away_rpg, 4.5, 3.5)} />
                <Td value={fmtDiff(fgGap)} color={diffColor(fgGap)} bold />
                <Td value={t.f5_home_record} color={FG} />
                <Td value={t.f5_home_rpg.toFixed(2)} color={pctGood(t.f5_home_rpg, 2.8, 2.2)} />
                <Td value={t.f5_away_record} color={FG} />
                <Td value={t.f5_away_rpg.toFixed(2)} color={pctGood(t.f5_away_rpg, 2.8, 2.2)} />
                <Td value={fmtDiff(f5Gap)} color={diffColor(f5Gap)} bold />
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function GenericFullGame({ teams, sortKey, sortDesc, onSort, sport }: any) {
  const scoringLabel = sport === 'nhl' ? 'GPG' : 'PPG';
  const allowedLabel = sport === 'nhl' ? 'GAPG' : 'PAPG';
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortTh label="Team" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="GP" field="games" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Record" field="win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Win%" field="win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label={scoringLabel} field="ppg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label={allowedLabel} field="papg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Diff" field="diff" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Avg Total" field="avg_total" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Home W%" field="home_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Away W%" field="away_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => (
            <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
              <TeamTd name={t.team} />
              <Td value={t.games} />
              <Td value={t.record} color={FG} />
              <Td value={`${t.win_pct}%`} color={pctGood(t.win_pct, 55, 45)} bold />
              <Td value={t.ppg.toFixed(1)} color={pctGood(t.ppg, t.ppg > 50 ? 110 : 3.2, t.ppg > 50 ? 100 : 2.5)} />
              <Td value={t.papg.toFixed(1)} />
              <Td value={fmtDiff(t.diff)} color={diffColor(t.diff)} bold />
              <Td value={t.avg_total.toFixed(1)} color={BLUE} />
              <Td value={`${t.home_win_pct}%`} color={pctGood(t.home_win_pct, 60, 40)} />
              <Td value={`${t.away_win_pct}%`} color={pctGood(t.away_win_pct, 55, 40)} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function GenericSplits({ teams, sortKey, sortDesc, onSort }: any) {
  return (
    <div className="data-table-wrap" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead><tr>
          <SortTh label="Team" field="team" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Home Rec" field="home_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Home PPG" field="home_ppg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Home PAPG" field="home_papg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Away Rec" field="away_win_pct" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Away PPG" field="away_ppg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="Away PAPG" field="away_papg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
          <SortTh label="H-A Gap" field="home_ppg" sortKey={sortKey} sortDesc={sortDesc} onSort={onSort} />
        </tr></thead>
        <tbody>
          {teams.map((t: any) => {
            const gap = (t.home_ppg || 0) - (t.away_ppg || 0);
            return (
              <tr key={t.team} style={{ borderBottom: `1px solid ${BORDER}` }}>
                <TeamTd name={t.team} />
                <Td value={t.home_record} color={FG} />
                <Td value={(t.home_ppg || 0).toFixed(1)} />
                <Td value={(t.home_papg || 0).toFixed(1)} />
                <Td value={t.away_record} color={FG} />
                <Td value={(t.away_ppg || 0).toFixed(1)} />
                <Td value={(t.away_papg || 0).toFixed(1)} />
                <Td value={fmtDiff(gap)} color={diffColor(gap)} bold />
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default BettingRankings;
