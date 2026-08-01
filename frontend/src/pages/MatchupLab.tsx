/**
 * Matchup Lab — Deep dive into any game.
 * Aggregates: odds, team stats, line movement, injuries, weather.
 * Navigated to from game cards or by game ID.
 */
import { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';
import { ArrowLeft } from 'lucide-react';
import { useLocation, Link } from 'react-router-dom';
import '../styles/analytics.css';
import { getApiUrl } from '../config';

const EMERALD   = 'oklch(69.6% .17 162.48)';
const BRAND_RED = 'oklch(63.7% .237 25.331)';
const BLUE      = 'oklch(62.3% .214 259.815)';
const YELLOW    = 'oklch(79.5% .184 86.047)';
const MUTED_FG  = 'oklch(70.8% 0 0)';
const BORDER    = 'oklch(100% 0 0 / .1)';
const SIDEBAR_BG = 'oklch(20.5% 0 0)';

function fmtOdds(n: number | null | undefined): string {
  if (n == null) return '—';
  return n >= 0 ? `+${n}` : `${n}`;
}

function DarkTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: SIDEBAR_BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: '10px 14px', fontSize: '0.78rem' }}>
      {label && <p style={{ color: 'oklch(98.5% 0 0)', fontWeight: 700, marginBottom: 4 }}>{label}</p>}
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color || MUTED_FG, margin: '2px 0' }}>
          {p.name}: <strong>{typeof p.value === 'number' ? p.value.toFixed(2) : p.value}</strong>
        </p>
      ))}
    </div>
  );
}

export function MatchupLab() {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const gameId = params.get('id') || location.hash?.split('id=')[1];

  const [games, setGames] = useState<any[]>([]);
  const [selectedGame, setSelectedGame] = useState<any>(null);
  const [injuries, setInjuries] = useState<any[]>([]);
  const [lineHistory, setLineHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(getApiUrl('games')).then(r => r.json()),
      fetch(getApiUrl('injuries')).then(r => r.json()).catch(() => ({ injuries: [] })),
    ]).then(([gamesData, injData]) => {
      setGames(gamesData);
      setInjuries(injData.injuries ?? []);

      if (gameId) {
        const found = gamesData.find((g: any) => g.state?.id === gameId);
        if (found) setSelectedGame(found);
      }
      setLoading(false);
    });
  }, [gameId]);

  useEffect(() => {
    if (!selectedGame?.state?.id) return;
    fetch(getApiUrl(`line-movement/${selectedGame.state.id}`))
      .then(r => r.json())
      .then(d => setLineHistory(d.snapshots ?? []))
      .catch(() => {});
  }, [selectedGame]);

  if (loading) {
    return <div className="analytics-page"><div style={{ padding: 40, textAlign: 'center', color: MUTED_FG }}>Loading games...</div></div>;
  }

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1>Matchup Lab</h1>
        <p className="subtitle">Deep dive into any game — odds, stats, injuries, line movement</p>
      </div>

      <div style={{ padding: '16px 24px', display: 'flex', gap: 16 }}>
        {/* Game selector */}
        <div style={{ width: 280, flexShrink: 0 }}>
          <GameSelector games={games} selected={selectedGame} onSelect={setSelectedGame} />
        </div>

        {/* Detail */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {selectedGame ? (
            <GameDetail game={selectedGame} injuries={injuries} lineHistory={lineHistory} />
          ) : (
            <div className="data-table-wrap" style={{ padding: 40, textAlign: 'center', color: MUTED_FG }}>
              Select a game from the left to analyze
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function GameSelector({ games, selected, onSelect }: { games: any[]; selected: any; onSelect: (g: any) => void }) {
  const [sportFilter, setSportFilter] = useState('all');
  const sports = [...new Set(games.map(g => g.state?.sport_key).filter(Boolean))].sort();

  const filtered = sportFilter === 'all' ? games : games.filter(g => g.state?.sport_key === sportFilter);

  const sportLabel = (s: string) => {
    const map: Record<string, string> = {
      baseball_mlb: 'MLB', basketball_wnba: 'WNBA', americanfootball_nfl: 'NFL',
      americanfootball_ncaaf: 'NCAAF', basketball_nba: 'NBA', icehockey_nhl: 'NHL',
    };
    return map[s] ?? s.split('_').pop()?.toUpperCase() ?? s;
  };

  return (
    <div>
      <select
        className="filter-select"
        value={sportFilter}
        onChange={e => setSportFilter(e.target.value)}
        style={{ width: '100%', marginBottom: 8 }}
      >
        <option value="all">ALL SPORTS ({games.length})</option>
        {sports.map(s => (
          <option key={s} value={s}>{sportLabel(s)} ({games.filter(g => g.state?.sport_key === s).length})</option>
        ))}
      </select>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 600, overflowY: 'auto' }}>
        {filtered.map((g: any) => {
          const s = g.state ?? {};
          const isSelected = selected?.state?.id === s.id;
          return (
            <button
              key={s.id}
              onClick={() => onSelect(g)}
              style={{
                background: isSelected ? 'oklch(28% 0 0)' : 'oklch(24% 0 0)',
                border: `1px solid ${isSelected ? EMERALD : BORDER}`,
                borderRadius: 6, padding: '8px 10px', cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--foreground)' }}>
                {s.away_team?.name} @ {s.home_team?.name}
              </div>
              <div style={{ fontSize: '0.62rem', color: MUTED_FG, marginTop: 2 }}>
                {sportLabel(s.sport_key)} — {s.status === 'completed' ? 'Final' : s.status === 'live' ? 'LIVE' : new Date(s.commence_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function GameDetail({ game, injuries, lineHistory }: { game: any; injuries: any[]; lineHistory: any[] }) {
  const s = game.state ?? {};
  const odds = game.odds ?? [];
  const proj = game.projection ?? {};
  const homeStats = game.home_mlb_stats ?? game.home_team_stats ?? {};
  const awayStats = game.away_mlb_stats ?? game.away_team_stats ?? {};

  const away = s.away_team ?? {};
  const home = s.home_team ?? {};

  // Match injuries to this game's teams
  const gameInjuries = injuries.filter(inj =>
    inj.team?.toLowerCase().includes(away.name?.split(' ').pop()?.toLowerCase() ?? '___') ||
    inj.team?.toLowerCase().includes(home.name?.split(' ').pop()?.toLowerCase() ?? '___')
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Header card */}
      <div className="data-table-wrap" style={{ padding: '18px 20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--foreground)' }}>
              {away.name} @ {home.name}
            </div>
            <div style={{ fontSize: '0.75rem', color: MUTED_FG, marginTop: 2 }}>
              {s.sport_key?.replace('_', ' ').toUpperCase()} — {new Date(s.commence_time).toLocaleString()}
            </div>
          </div>
          {s.status === 'live' && (
            <span style={{ padding: '4px 12px', borderRadius: 20, background: 'color-mix(in oklch, oklch(63.7% .237 25.331) 20%, transparent)', color: BRAND_RED, fontWeight: 700, fontSize: '0.72rem' }}>
              LIVE
            </span>
          )}
        </div>
      </div>

      {/* Odds comparison */}
      {odds.length > 0 && <OddsCard odds={odds} away={away.name} home={home.name} />}

      {/* Projection */}
      {proj.pregame_total && <ProjectionCard proj={proj} />}

      {/* Team stats comparison */}
      {(homeStats.wins || awayStats.wins) && (
        <StatsComparison away={away.name} home={home.name} awayStats={awayStats} homeStats={homeStats} />
      )}

      {/* Injuries */}
      {gameInjuries.length > 0 && <InjuryCard injuries={gameInjuries} />}

      {/* Line movement */}
      {lineHistory.length > 0 && <LineCard snapshots={lineHistory} />}
    </div>
  );
}

function OddsCard({ odds, away, home }: { odds: any[]; away: string; home: string }) {
  const best = odds[0] ?? {};
  return (
    <div className="data-table-wrap" style={{ padding: '14px 18px' }}>
      <div style={{ fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
        ODDS ({odds.length} BOOKS)
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
        <StatBox label={`${away} ML`} value={fmtOdds(best.away_ml)} color={best.away_ml && best.away_ml < 0 ? EMERALD : MUTED_FG} />
        <StatBox label={`${home} ML`} value={fmtOdds(best.home_ml)} color={best.home_ml && best.home_ml < 0 ? EMERALD : MUTED_FG} />
        <StatBox label="Total" value={best.total?.toString() ?? '—'} color={BLUE} />
        <StatBox label="Spread" value={best.home_spread ? `${home} ${best.home_spread > 0 ? '+' : ''}${best.home_spread}` : '—'} />
      </div>
      {best.total_movement && (
        <div style={{ marginTop: 8, fontSize: '0.72rem', color: MUTED_FG }}>
          Total moved: <span style={{ color: best.total_movement > 0 ? EMERALD : BRAND_RED, fontWeight: 700 }}>
            {best.total_movement > 0 ? '+' : ''}{best.total_movement}
          </span> from open ({best.opening_total})
        </div>
      )}
    </div>
  );
}

function ProjectionCard({ proj }: { proj: any }) {
  return (
    <div className="data-table-wrap" style={{ padding: '14px 18px' }}>
      <div style={{ fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
        PROJECTION
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
        <StatBox label="Pregame Total" value={proj.pregame_total?.toString() ?? '—'} />
        <StatBox label="Pregame Spread" value={proj.pregame_spread ? `${proj.pregame_spread > 0 ? '+' : ''}${proj.pregame_spread}` : '—'} />
        <StatBox label="Home ML" value={fmtOdds(proj.pregame_moneyline_home)} />
      </div>
    </div>
  );
}

function StatsComparison({ away, home, awayStats, homeStats }: { away: string; home: string; awayStats: any; homeStats: any }) {
  const metrics = [
    { key: 'wins', label: 'Wins', higher: true },
    { key: 'losses', label: 'Losses', higher: false },
    { key: 'win_pct', label: 'Win %', higher: true },
    { key: 'runs_per_game', label: 'RPG', higher: true },
    { key: 'batting_avg', label: 'AVG', higher: true },
    { key: 'on_base_pct', label: 'OBP', higher: true },
    { key: 'slugging_pct', label: 'SLG', higher: true },
    { key: 'pts_per_game', label: 'PPG', higher: true },
    { key: 'opp_pts_per_game', label: 'Opp PPG', higher: false },
    { key: 'off_rating', label: 'Off Rtg', higher: true },
    { key: 'def_rating', label: 'Def Rtg', higher: false },
    { key: 'pace', label: 'Pace', higher: true },
  ].filter(m => awayStats[m.key] != null || homeStats[m.key] != null);

  return (
    <div className="data-table-wrap" style={{ padding: '14px 18px' }}>
      <div style={{ fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
        TEAM COMPARISON
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
        <thead>
          <tr>
            <th style={{ padding: '6px 10px', textAlign: 'right', fontSize: '0.65rem', fontWeight: 700, color: BLUE, borderBottom: `1px solid ${BORDER}` }}>{away}</th>
            <th style={{ padding: '6px 10px', textAlign: 'center', fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, borderBottom: `1px solid ${BORDER}` }}>STAT</th>
            <th style={{ padding: '6px 10px', textAlign: 'left', fontSize: '0.65rem', fontWeight: 700, color: BRAND_RED, borderBottom: `1px solid ${BORDER}` }}>{home}</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map(m => {
            const av = awayStats[m.key];
            const hv = homeStats[m.key];
            const awayBetter = m.higher ? (av ?? 0) > (hv ?? 0) : (av ?? 999) < (hv ?? 999);
            const homeBetter = !awayBetter && av !== hv;
            const fmt = (v: any) => v == null ? '—' : typeof v === 'number' ? (v < 1 && v > 0 ? v.toFixed(3) : v.toFixed(1)) : v;

            return (
              <tr key={m.key} style={{ borderBottom: `1px solid ${BORDER}` }}>
                <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--d3-mono)', fontWeight: awayBetter ? 700 : 400, color: awayBetter ? EMERALD : 'var(--foreground)' }}>{fmt(av)}</td>
                <td style={{ padding: '6px 10px', textAlign: 'center', color: MUTED_FG, fontWeight: 600 }}>{m.label}</td>
                <td style={{ padding: '6px 10px', textAlign: 'left', fontFamily: 'var(--d3-mono)', fontWeight: homeBetter ? 700 : 400, color: homeBetter ? EMERALD : 'var(--foreground)' }}>{fmt(hv)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function InjuryCard({ injuries }: { injuries: any[] }) {
  return (
    <div className="data-table-wrap" style={{ padding: '14px 18px', borderLeft: `3px solid ${BRAND_RED}` }}>
      <div style={{ fontSize: '0.65rem', fontWeight: 700, color: BRAND_RED, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
        INJURIES ({injuries.length})
      </div>
      {injuries.slice(0, 10).map((inj, i) => (
        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', fontSize: '0.75rem' }}>
          <span style={{ color: 'var(--foreground)', fontWeight: 600 }}>{inj.player_name}</span>
          <span style={{ display: 'flex', gap: 8 }}>
            <span style={{ color: MUTED_FG }}>{inj.team_abbr}</span>
            <span style={{
              color: inj.status === 'Out' ? BRAND_RED : inj.status === 'Questionable' ? YELLOW : MUTED_FG,
              fontWeight: 700, fontSize: '0.68rem',
            }}>
              {inj.status}
            </span>
          </span>
        </div>
      ))}
    </div>
  );
}

function LineCard({ snapshots }: { snapshots: any[] }) {
  const first = snapshots[0];
  const last = snapshots[snapshots.length - 1];

  return (
    <div className="data-table-wrap" style={{ padding: '14px 18px' }}>
      <div style={{ fontSize: '0.65rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
        LINE HISTORY ({snapshots.length} snapshots)
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
        <StatBox label="Spread" value={last.spread_home != null ? (last.spread_home > 0 ? '+' : '') + last.spread_home : '—'} />
        <StatBox label="Total" value={last.total_line?.toString() ?? '—'} color={BLUE} />
        <StatBox label="Home ML" value={fmtOdds(last.home_ml)} />
        <StatBox label="Away ML" value={fmtOdds(last.away_ml)} />
      </div>
    </div>
  );
}

function StatBox({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{ background: 'oklch(22% 0 0)', borderRadius: 6, padding: '8px 12px' }}>
      <div style={{ fontSize: '0.62rem', fontWeight: 700, color: MUTED_FG, letterSpacing: '0.1em', textTransform: 'uppercase' }}>{label}</div>
      <div style={{ fontSize: '1rem', fontWeight: 800, fontFamily: 'var(--d3-mono)', color: color ?? 'var(--foreground)', marginTop: 2 }}>{value}</div>
    </div>
  );
}

export default MatchupLab;
