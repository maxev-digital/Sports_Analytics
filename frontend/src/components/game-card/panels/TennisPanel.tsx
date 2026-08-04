import { GameState } from '../../../types';
import { formatTeamName } from '../../../utils/teamNames';

interface TennisPanelProps {
  state: GameState;
  round?: string | null;
  tournament?: string | null;
}

export function TennisPanel({ state, round, tournament }: TennisPanelProps) {
  const awayName = formatTeamName(state.away_team.name, state.sport_key);
  const homeName = formatTeamName(state.home_team.name, state.sport_key);

  return (
    <div className="bg-slate-800/60 rounded p-3 text-slate-300 text-sm space-y-2">
      {tournament && (
        <div className="text-center">
          <span className="text-yellow-400 font-bold text-base">{tournament}</span>
          {round && <span className="text-slate-400 ml-2">— {round}</span>}
        </div>
      )}
      <div className="flex justify-between items-center pt-1">
        <span className="font-bold text-white">{awayName}</span>
        <span className="text-slate-500 text-xs">vs</span>
        <span className="font-bold text-white">{homeName}</span>
      </div>
      {state.status === 'live' && state.away_team.score != null && state.home_team.score != null && (
        <div className="flex justify-between text-2xl font-bold text-center">
          <span className="text-blue-300">{state.away_team.score}</span>
          <span className="text-slate-600">—</span>
          <span className="text-blue-300">{state.home_team.score}</span>
        </div>
      )}
    </div>
  );
}
