/**
 * Single play card — one bet recommendation on one game.
 */
import { Badge } from './Badge';
import { tierColor, tierLabel, MUTED_FG, BORDER, CARD_BG, FG, EMERALD } from './tokens';
import type { F5Play, F5Game } from './types';

interface PlayCardProps {
  game: F5Game;
  play: F5Play;
}

export function PlayCard({ game, play }: PlayCardProps) {
  const color = tierColor(play.tier);

  return (
    <div style={{
      background: CARD_BG,
      border: `1px solid ${BORDER}`,
      borderLeft: `3px solid ${color}`,
      borderRadius: 6,
      padding: '14px 18px',
      marginBottom: 8,
    }}>
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Badge color={color} label={tierLabel(play.tier)} />
          <span style={{ fontWeight: 800, fontSize: '0.85rem', color: FG }}>
            {play.type}
          </span>
        </div>
        <span style={{ fontWeight: 800, fontSize: '1rem', color: EMERALD }}>
          ${play.unit}
        </span>
      </div>

      {/* Game info */}
      <div style={{ fontSize: '0.78rem', color: FG, fontWeight: 700, marginBottom: 4 }}>
        {game.away_team} @ {game.home_team}
      </div>
      <div style={{ fontSize: '0.72rem', color: MUTED_FG, marginBottom: 4 }}>
        {game.away_pitcher} ({game.away_era?.toFixed(2) ?? 'TBD'}) vs {game.home_pitcher} ({game.home_era?.toFixed(2) ?? 'TBD'})
      </div>

      {/* Signal */}
      <div style={{ fontSize: '0.72rem', color: MUTED_FG, marginBottom: 6 }}>
        Signal: {play.signal}
      </div>

      {/* Footer */}
      <div style={{ display: 'flex', gap: 16, fontSize: '0.68rem' }}>
        <span style={{ color: MUTED_FG }}>
          Book: <span style={{ color: FG, fontWeight: 700 }}>{play.book}</span>
        </span>
        <span style={{ color: MUTED_FG }}>
          Hit: <span style={{ color: EMERALD, fontWeight: 700 }}>{play.expected_hit}</span>
        </span>
        <span style={{ color: MUTED_FG }}>
          ROI: <span style={{ color: EMERALD, fontWeight: 700 }}>{play.historical_roi}</span>
        </span>
      </div>
    </div>
  );
}
