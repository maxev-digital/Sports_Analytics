/**
 * Single play card — one bet recommendation on one game.
 */
import { Badge } from './Badge';
import { tierColor, tierLabel, MUTED_FG, BORDER, CARD_BG, FG, EMERALD, fmtOdds } from './tokens';
import type { F5Play, F5Game } from './types';

interface F5Odds {
  fg_total?: number | null;
  fg_under_odds?: number | null;
  fg_over_odds?: number | null;
  fg_ml_away?: number | null;
  fg_ml_home?: number | null;
  f5_total?: number | null;
  f5_under_odds?: number | null;
}

interface PlayCardProps {
  game: F5Game;
  play: F5Play;
  odds?: F5Odds | null;
}

function OddsChip({ label, value }: { label: string; value: number }) {
  const formatted = fmtOdds(value);
  const color = value > 0 ? EMERALD : MUTED_FG;
  return (
    <span style={{
      display: 'inline-flex', flexDirection: 'column', alignItems: 'center',
      background: 'oklch(30% 0 0)', borderRadius: 4, padding: '3px 8px', gap: 1,
    }}>
      <span style={{ fontSize: '0.7rem', fontWeight: 800, color, fontFamily: 'monospace' }}>{formatted}</span>
      <span style={{ fontSize: '0.55rem', color: MUTED_FG, letterSpacing: '0.05em' }}>{label}</span>
    </span>
  );
}

export function PlayCard({ game, play, odds }: PlayCardProps) {
  const color = tierColor(play.tier);
  const playType = play.type.toLowerCase();

  // Pick relevant odds chips based on play type
  const oddsChips: { label: string; value: number }[] = [];
  if (odds) {
    const isUnder = playType.includes('under');
    const isOver  = playType.includes('over');
    const isMl    = playType.includes('ml') || playType.includes('moneyline');
    const isSgp   = playType.includes('sgp');

    if ((isUnder || isSgp) && odds.fg_total != null)
      oddsChips.push({ label: 'FG TOTAL', value: Number(odds.fg_total) });
    if ((isUnder || isSgp) && odds.fg_under_odds != null)
      oddsChips.push({ label: 'UNDER', value: Number(odds.fg_under_odds) });
    if (isOver && odds.fg_over_odds != null)
      oddsChips.push({ label: 'OVER', value: Number(odds.fg_over_odds) });
    if (isMl && odds.fg_ml_away != null)
      oddsChips.push({ label: game.away_team.split(' ').pop() ?? 'AWAY', value: Number(odds.fg_ml_away) });
    if (isMl && odds.fg_ml_home != null)
      oddsChips.push({ label: game.home_team.split(' ').pop() ?? 'HOME', value: Number(odds.fg_ml_home) });

    // Fallback: always show FG ML + total so cards are never blank
    if (oddsChips.length === 0) {
      if (odds.fg_ml_away != null) oddsChips.push({ label: game.away_team.split(' ').pop() ?? 'AWAY', value: Number(odds.fg_ml_away) });
      if (odds.fg_ml_home != null) oddsChips.push({ label: game.home_team.split(' ').pop() ?? 'HOME', value: Number(odds.fg_ml_home) });
      if (odds.fg_total != null)   oddsChips.push({ label: 'TOTAL', value: Number(odds.fg_total) });
    }
  }

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
          <span style={{ fontWeight: 800, fontSize: '0.85rem', color: FG }}>{play.type}</span>
        </div>
        <span style={{ fontWeight: 800, fontSize: '1rem', color: EMERALD }}>${play.unit}</span>
      </div>

      {/* Game info */}
      <div style={{ fontSize: '0.78rem', color: FG, fontWeight: 700, marginBottom: 4 }}>
        {game.away_team} @ {game.home_team}
      </div>
      <div style={{ fontSize: '0.72rem', color: MUTED_FG, marginBottom: 4 }}>
        {game.away_pitcher} ({game.away_era?.toFixed(2) ?? 'TBD'}) vs {game.home_pitcher} ({game.home_era?.toFixed(2) ?? 'TBD'})
      </div>

      {/* Signal */}
      <div style={{ fontSize: '0.72rem', color: MUTED_FG, marginBottom: 8 }}>
        Signal: {play.signal}
      </div>

      {/* Live odds chips */}
      {oddsChips.length > 0 && (
        <div style={{ display: 'flex', gap: 6, marginBottom: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          {oddsChips.map((c, i) => <OddsChip key={i} label={c.label} value={c.value} />)}
          {play.needs_f5_odds && (
            <span style={{ fontSize: '0.6rem', color: MUTED_FG, fontStyle: 'italic' }}>
              · F5 line: check Bovada/DraftKings
            </span>
          )}
        </div>
      )}

      {/* Footer */}
      <div style={{ display: 'flex', gap: 16, fontSize: '0.68rem', borderTop: `1px solid ${BORDER}`, paddingTop: 8 }}>
        <span style={{ color: MUTED_FG }}>Book: <span style={{ color: FG, fontWeight: 700 }}>{play.book}</span></span>
        <span style={{ color: MUTED_FG }}>Hit: <span style={{ color: EMERALD, fontWeight: 700 }}>{play.expected_hit}</span></span>
        <span style={{ color: MUTED_FG }}>ROI: <span style={{ color: EMERALD, fontWeight: 700 }}>{play.historical_roi}</span></span>
      </div>
    </div>
  );
}
