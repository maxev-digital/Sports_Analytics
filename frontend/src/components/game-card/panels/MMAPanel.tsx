import { MMAFighterStats, GameState } from '../../../types';
import { formatTeamName } from '../../../utils/teamNames';

interface MMAPanelProps {
  state: GameState;
  homeStats: MMAFighterStats | null;
  awayStats: MMAFighterStats | null;
}

function Row({ label, away, home }: { label: string; away: string | number | null | undefined; home: string | number | null | undefined }) {
  if (away == null && home == null) return null;
  return (
    <div className="flex justify-between items-center text-xs py-0.5">
      <span className="text-slate-300 font-bold">{away ?? '—'}</span>
      <span className="text-slate-500 text-center flex-1 px-2">{label}</span>
      <span className="text-slate-300 font-bold text-right">{home ?? '—'}</span>
    </div>
  );
}

export function MMAPanel({ state, homeStats, awayStats }: MMAPanelProps) {
  const awayName = formatTeamName(state.away_team.name, state.sport_key);
  const homeName = formatTeamName(state.home_team.name, state.sport_key);

  if (!homeStats && !awayStats) {
    return <div className="text-slate-500 text-sm italic text-center py-4">No fighter stats available</div>;
  }

  return (
    <div className="bg-slate-800/60 rounded p-2 text-slate-300">
      <div className="text-xs font-bold text-slate-400 mb-2 uppercase tracking-wide">Tale of the Tape</div>
      <div className="grid grid-cols-3 text-xs mb-2">
        <span className="font-bold text-slate-200 truncate">{awayName}</span>
        <span className="text-center"></span>
        <span className="font-bold text-slate-200 text-right truncate">{homeName}</span>
      </div>
      <Row label="Height"  away={awayStats?.height}         home={homeStats?.height} />
      <Row label="Weight"  away={awayStats?.weight}         home={homeStats?.weight} />
      <Row label="Reach"   away={awayStats?.reach}          home={homeStats?.reach} />
      <Row label="Stance"  away={awayStats?.stance}         home={homeStats?.stance} />
      <Row label="Style"   away={awayStats?.fighting_style} home={homeStats?.fighting_style} />
      {(awayStats?.tko_wins != null || homeStats?.tko_wins != null) && (
        <div className="mt-1 pt-1 border-t border-slate-700">
          <Row label="TKO W/L" away={awayStats ? `${awayStats.tko_wins ?? 0}-${awayStats.tko_losses ?? 0}` : null} home={homeStats ? `${homeStats.tko_wins ?? 0}-${homeStats.tko_losses ?? 0}` : null} />
          <Row label="Sub W/L" away={awayStats ? `${awayStats.sub_wins ?? 0}-${awayStats.sub_losses ?? 0}` : null} home={homeStats ? `${homeStats.sub_wins ?? 0}-${homeStats.sub_losses ?? 0}` : null} />
        </div>
      )}
    </div>
  );
}
