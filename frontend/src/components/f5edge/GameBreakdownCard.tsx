/**
 * Game breakdown card — full context for one game.
 * Shows pitchers, umpire, venue, weather, live odds, and play signals.
 */
import { Badge } from './Badge';
import { tierColor, tierLabel, MUTED_FG, BORDER, CARD_BG, FG, EMERALD, BRAND_RED, YELLOW, fmtOdds } from './tokens';
import type { F5Game, F5Play } from './types';

const HIGH_TIE_UMPS = new Set([
  'Bill Miller', 'Lance Barrett', 'Larry Vanover', 'CB Bucknor',
  'Gabe Morales', 'Will Little', 'Shane Livensparger', 'Alfonso Márquez',
  'Dan Merzel', 'Quinn Wolcott', 'Mark Wegner', 'Nestor Ceja',
  'Mike Muchlinski', 'D.J. Reyburn', 'Vic Carapazza', 'Phil Cuzzi',
  'Ryan Additon', 'Tripp Gibson', 'Adrian Johnson',
]);

const LOW_TIE_UMPS = new Set([
  'Edwin Jimenez', 'Mark Carlson', 'Hunter Wendelstedt', 'Erich Bacchus',
  'Roberto Ortiz', 'Paul Clemons', 'Chad Whitson', 'Jim Wolf',
]);

const UNDER_VENUES = new Set([
  'Globe Life Field', 'Kauffman Stadium', 'Comerica Park', 'Wrigley Field', 'Citi Field',
]);

interface PitcherStats {
  era?: number | null;
  k9?: number | null;
  bb9?: number | null;
  whip?: number | null;
  recent_era?: number | null;
  recent_avg_ip?: number | null;
  recent_k?: number | null;
  recent_starts?: number | null;
  season_gs?: number | null;
}

interface F5Odds {
  fg_total?: number | null;
  fg_under_odds?: number | null;
  fg_over_odds?: number | null;
  fg_ml_away?: number | null;
  fg_ml_home?: number | null;
  f5_total?: number | null;
  f5_under_odds?: number | null;
}

interface GameBreakdownCardProps {
  game: F5Game & { away_pitcher_stats?: PitcherStats; home_pitcher_stats?: PitcherStats };
  plays: F5Play[];
  odds?: F5Odds | null;
}

export function GameBreakdownCard({ game, plays, odds }: GameBreakdownCardProps) {
  const hasPlays = plays.length > 0;
  const borderColor = hasPlays ? EMERALD : BORDER;
  const fgTotal = odds?.fg_total;

  return (
    <div style={{
      background: CARD_BG,
      border: `1px solid ${borderColor}`,
      borderRadius: 6,
      padding: '14px 18px',
      opacity: hasPlays ? 1 : 0.6,
    }}>
      {/* Teams + badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <span style={{ fontWeight: 800, fontSize: '0.85rem', color: FG }}>
          {game.away_team} @ {game.home_team}
        </span>
        {hasPlays
          ? <Badge color={EMERALD} label={`${plays.length} PLAY${plays.length > 1 ? 'S' : ''}`} />
          : <Badge color={MUTED_FG} label="PASS" />
        }
      </div>

      {/* Live odds bar */}
      {odds && (odds.fg_ml_away != null || odds.fg_total != null) && (
        <div style={{
          display: 'flex', gap: 8, marginBottom: 10, padding: '6px 10px',
          background: 'oklch(20% 0 0)', borderRadius: 5, flexWrap: 'wrap', alignItems: 'center',
        }}>
          <span style={{ fontSize: '0.55rem', color: MUTED_FG, fontWeight: 700, letterSpacing: '0.08em' }}>LIVE ODDS</span>
          {odds.fg_ml_away != null && (
            <span style={{ fontSize: '0.7rem', color: MUTED_FG }}>
              {game.away_team.split(' ').pop()}
              <span style={{ marginLeft: 4, fontWeight: 800, color: odds.fg_ml_away > 0 ? EMERALD : FG, fontFamily: 'monospace' }}>
                {fmtOdds(Number(odds.fg_ml_away))}
              </span>
            </span>
          )}
          {odds.fg_ml_home != null && (
            <span style={{ fontSize: '0.7rem', color: MUTED_FG }}>
              {game.home_team.split(' ').pop()}
              <span style={{ marginLeft: 4, fontWeight: 800, color: odds.fg_ml_home > 0 ? EMERALD : FG, fontFamily: 'monospace' }}>
                {fmtOdds(Number(odds.fg_ml_home))}
              </span>
            </span>
          )}
          {odds.fg_total != null && (
            <span style={{ fontSize: '0.7rem', color: MUTED_FG }}>
              O/U <span style={{ fontWeight: 800, color: FG, fontFamily: 'monospace' }}>{odds.fg_total}</span>
              {odds.fg_under_odds != null && (
                <span style={{ marginLeft: 4, fontWeight: 700, color: MUTED_FG, fontFamily: 'monospace' }}>
                  ({fmtOdds(Number(odds.fg_under_odds))} under)
                </span>
              )}
            </span>
          )}
        </div>
      )}

      {/* Pitcher matchup */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 10 }}>
        {[
          { name: game.away_pitcher, team: game.away_team, stats: game.away_pitcher_stats, era: game.away_era },
          { name: game.home_pitcher, team: game.home_team, stats: game.home_pitcher_stats, era: game.home_era },
        ].map(({ name, team, stats, era }) => {
          const recentEra = stats?.recent_era;
          const trending = recentEra != null && era != null
            ? recentEra < era - 0.5 ? 'hot' : recentEra > era + 0.5 ? 'cold' : 'neutral'
            : 'neutral';
          const trendColor = trending === 'hot' ? EMERALD : trending === 'cold' ? BRAND_RED : MUTED_FG;
          return (
            <div key={team} style={{ background: 'oklch(18% 0 0)', borderRadius: 4, padding: '8px 10px', fontSize: '0.7rem' }}>
              <div style={{ fontWeight: 700, color: FG, marginBottom: 4 }}>{name}</div>
              <div style={{ color: MUTED_FG, fontSize: '0.65rem', marginBottom: 2 }}>{team}</div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {era != null && <StatPill label="ERA" value={era.toFixed(2)} color={era < 3.5 ? EMERALD : era > 4.5 ? BRAND_RED : YELLOW} />}
                {stats?.k9 != null && <StatPill label="K/9" value={stats.k9.toFixed(1)} color={stats.k9 > 9 ? EMERALD : MUTED_FG} />}
                {stats?.bb9 != null && <StatPill label="BB/9" value={stats.bb9.toFixed(1)} color={stats.bb9 < 2.5 ? EMERALD : stats.bb9 > 4 ? BRAND_RED : MUTED_FG} />}
                {stats?.whip != null && <StatPill label="WHIP" value={stats.whip.toFixed(2)} color={stats.whip < 1.15 ? EMERALD : stats.whip > 1.45 ? BRAND_RED : MUTED_FG} />}
              </div>
              {recentEra != null && (
                <div style={{ marginTop: 5, fontSize: '0.63rem' }}>
                  <span style={{ color: MUTED_FG }}>L{stats?.recent_starts ?? 3}: </span>
                  <span style={{ color: trendColor, fontWeight: 700 }}>{recentEra.toFixed(2)} ERA</span>
                  {stats?.recent_avg_ip != null && <span style={{ color: MUTED_FG }}> · {stats.recent_avg_ip.toFixed(1)} IP/start</span>}
                  {stats?.recent_k != null && <span style={{ color: MUTED_FG }}> · {stats.recent_k}K</span>}
                  <span style={{ marginLeft: 6, color: trendColor, fontWeight: 700 }}>
                    {trending === 'hot' ? '↑ HOT' : trending === 'cold' ? '↓ COLD' : ''}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Context grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 16px', fontSize: '0.72rem', marginBottom: 8 }}>
        <ContextRow label="ERA Diff" value={game.era_diff?.toFixed(2) ?? '—'} highlight={game.era_diff !== null && game.era_diff >= 1.5} highlightLabel="MISMATCH" />
        <ContextRow
          label="Umpire"
          value={game.hp_umpire ?? 'TBD'}
          highlight={game.hp_umpire != null && HIGH_TIE_UMPS.has(game.hp_umpire)}
          highlightLabel="HIGH TIE"
          highlightColor={YELLOW}
          lowlight={game.hp_umpire != null && LOW_TIE_UMPS.has(game.hp_umpire)}
          lowlightLabel="LOW TIE"
        />
        <ContextRow
          label="Venue"
          value={game.venue}
          highlight={UNDER_VENUES.has(game.venue)}
          highlightLabel="UNDER VENUE"
        />
        {fgTotal != null && <ContextRow label="FG Total" value={fgTotal.toString()} />}
        {game.temp && <ContextRow label="Weather" value={`${game.temp}°F ${game.wind ?? ''}`} />}
      </div>

      {/* Play signals */}
      {hasPlays && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {plays.map((p, i) => (
            <Badge key={i} color={tierColor(p.tier)} label={`${tierLabel(p.tier)}: ${p.type}`} />
          ))}
        </div>
      )}
    </div>
  );
}

function StatPill({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <span style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
      <span style={{ color, fontWeight: 700, fontFamily: 'var(--d3-mono)', fontSize: '0.72rem' }}>{value}</span>
      <span style={{ color: MUTED_FG, fontSize: '0.58rem', letterSpacing: '0.06em' }}>{label}</span>
    </span>
  );
}

function ContextRow({ label, value, highlight, highlightLabel, highlightColor, lowlight, lowlightLabel }: {
  label: string; value: string;
  highlight?: boolean; highlightLabel?: string; highlightColor?: string;
  lowlight?: boolean; lowlightLabel?: string;
}) {
  return (
    <div>
      <span style={{ color: MUTED_FG }}>{label}: </span>
      <span style={{ color: FG, fontWeight: 600 }}>{value}</span>
      {highlight && highlightLabel && (
        <span style={{ marginLeft: 6, color: highlightColor ?? YELLOW, fontWeight: 700, fontSize: '0.65rem' }}>{highlightLabel}</span>
      )}
      {!highlight && lowlight && lowlightLabel && (
        <span style={{ marginLeft: 6, color: BRAND_RED, fontWeight: 700, fontSize: '0.65rem' }}>{lowlightLabel}</span>
      )}
    </div>
  );
}
