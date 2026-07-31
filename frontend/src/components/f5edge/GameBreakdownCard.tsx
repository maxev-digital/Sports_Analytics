/**
 * Game breakdown card — full context for one game.
 * Shows pitchers, umpire, venue, weather, signals, and pass/play status.
 */
import { Badge } from './Badge';
import { tierColor, tierLabel, MUTED_FG, BORDER, CARD_BG, FG, EMERALD, BRAND_RED, YELLOW } from './tokens';
import type { F5Game, F5Play } from './types';

const HIGH_TIE_UMPS = new Set([
  'Bill Miller', 'Lance Barrett', 'Larry Vanover', 'CB Bucknor',
  'Gabe Morales', 'Will Little', 'Shane Livensparger', 'Alfonso Márquez',
  'Dan Merzel', 'Quinn Wolcott', 'Mark Wegner',
]);

const UNDER_VENUES = new Set([
  'Globe Life Field', 'Kauffman Stadium', 'Comerica Park', 'Wrigley Field', 'Citi Field',
]);

interface GameBreakdownCardProps {
  game: F5Game;
  plays: F5Play[];
  fgTotal?: number | null;
}

export function GameBreakdownCard({ game, plays, fgTotal }: GameBreakdownCardProps) {
  const hasPlays = plays.length > 0;
  const borderColor = hasPlays ? EMERALD : BORDER;

  return (
    <div style={{
      background: CARD_BG,
      border: `1px solid ${borderColor}`,
      borderRadius: 6,
      padding: '14px 18px',
      opacity: hasPlays ? 1 : 0.6,
    }}>
      {/* Teams */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <span style={{ fontWeight: 800, fontSize: '0.85rem', color: FG }}>
          {game.away_team} @ {game.home_team}
        </span>
        {hasPlays
          ? <Badge color={EMERALD} label={`${plays.length} PLAY${plays.length > 1 ? 'S' : ''}`} />
          : <Badge color={MUTED_FG} label="PASS" />
        }
      </div>

      {/* Context grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 16px', fontSize: '0.72rem', marginBottom: 8 }}>
        <ContextRow label="Pitchers" value={`${game.away_pitcher} (${game.away_era?.toFixed(2) ?? '?'}) vs ${game.home_pitcher} (${game.home_era?.toFixed(2) ?? '?'})`} />
        <ContextRow label="ERA Diff" value={game.era_diff?.toFixed(2) ?? '—'} highlight={game.era_diff !== null && game.era_diff >= 1.5} />
        <ContextRow
          label="Umpire"
          value={game.hp_umpire ?? 'TBD'}
          highlight={game.hp_umpire !== null && HIGH_TIE_UMPS.has(game.hp_umpire)}
          highlightLabel="HIGH TIE"
        />
        <ContextRow
          label="Venue"
          value={game.venue}
          highlight={UNDER_VENUES.has(game.venue)}
          highlightLabel="UNDER VENUE"
        />
        {fgTotal && <ContextRow label="FG Total" value={fgTotal.toString()} />}
        {game.temp && <ContextRow label="Weather" value={`${game.temp}°F ${game.wind ?? ''}`} />}
      </div>

      {/* Signals */}
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

function ContextRow({ label, value, highlight, highlightLabel }: {
  label: string;
  value: string;
  highlight?: boolean;
  highlightLabel?: string;
}) {
  return (
    <div>
      <span style={{ color: MUTED_FG }}>{label}: </span>
      <span style={{ color: FG, fontWeight: 600 }}>{value}</span>
      {highlight && highlightLabel && (
        <span style={{ marginLeft: 6, color: YELLOW, fontWeight: 700, fontSize: '0.65rem' }}>
          {highlightLabel}
        </span>
      )}
    </div>
  );
}
