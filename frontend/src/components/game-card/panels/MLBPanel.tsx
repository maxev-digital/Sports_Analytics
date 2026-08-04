import { MLBTeamStats, ProbablePitcher, GameState } from '../../../types';
import { formatTeamName } from '../../../utils/teamNames';

interface MLBPanelProps {
  state: GameState;
  homeStats: MLBTeamStats | null;
  awayStats: MLBTeamStats | null;
  homePitcher?: ProbablePitcher | null;
  awayPitcher?: ProbablePitcher | null;
  ballpark?: string | null;
  umpire?: string | null;
}

function StatRow({ label, away, home, higherBetter = true }: { label: string; away: number | null | undefined; home: number | null | undefined; higherBetter?: boolean }) {
  if (away == null && home == null) return null;
  const awayBetter = away != null && home != null && (higherBetter ? away > home : away < home);
  const homeBetter = away != null && home != null && (higherBetter ? home > away : home < away);
  return (
    <div className="flex justify-between items-center text-xs py-0.5">
      <span className={`font-bold ${awayBetter ? 'text-green-400' : 'text-slate-300'}`}>{away?.toFixed(2) ?? '—'}</span>
      <span className="text-slate-500 text-center flex-1 px-2">{label}</span>
      <span className={`font-bold ${homeBetter ? 'text-green-400' : 'text-slate-300'}`}>{home?.toFixed(2) ?? '—'}</span>
    </div>
  );
}

export function MLBPanel({ state, homeStats, awayStats, homePitcher, awayPitcher, ballpark, umpire }: MLBPanelProps) {
  const awayName = formatTeamName(state.away_team.name, state.sport_key);
  const homeName = formatTeamName(state.home_team.name, state.sport_key);

  return (
    <div className="space-y-3 text-slate-300">
      {/* Probable Starters */}
      {(homePitcher || awayPitcher) && (
        <div className="bg-slate-800/60 rounded p-2">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-2">Probable Starters</div>
          <div className="grid grid-cols-2 gap-3">
            {[{ pitcher: awayPitcher, team: awayName }, { pitcher: homePitcher, team: homeName }].map(({ pitcher, team }) => (
              <div key={team} className="text-xs">
                <div className="text-slate-400 mb-0.5">{team.split(' ').pop()}</div>
                {pitcher ? (
                  <>
                    <div className="font-bold text-white">{pitcher.name}</div>
                    {pitcher.record && <div className="text-slate-400">{pitcher.record}</div>}
                    {pitcher.era != null && <div className="text-slate-400">ERA {pitcher.era.toFixed(2)}</div>}
                  </>
                ) : <div className="text-slate-500 italic">TBD</div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Venue + Umpire */}
      {(ballpark || umpire) && (
        <div className="flex gap-3 text-xs text-slate-400">
          {ballpark && <span>⚾ {ballpark}</span>}
          {umpire && <span>👤 HP: {umpire}</span>}
        </div>
      )}

      {/* Season Stats */}
      {(homeStats || awayStats) && (
        <div className="bg-slate-800/60 rounded p-2">
          <div className="grid grid-cols-3 text-xs mb-1">
            <span className="font-bold text-slate-300">{awayName.split(' ').pop()}</span>
            <span className="text-center text-slate-500">Stat</span>
            <span className="font-bold text-slate-300 text-right">{homeName.split(' ').pop()}</span>
          </div>
          <StatRow label="R/G"       away={awayStats?.runs_per_game}         home={homeStats?.runs_per_game} />
          <StatRow label="RA/G"      away={awayStats?.runs_allowed_per_game} home={homeStats?.runs_allowed_per_game} higherBetter={false} />
          <StatRow label="AVG"       away={awayStats?.batting_avg}           home={homeStats?.batting_avg} />
          <StatRow label="OPS"       away={awayStats?.ops}                   home={homeStats?.ops} />
          <StatRow label="ERA"       away={awayStats?.era}                   home={homeStats?.era} higherBetter={false} />
          <StatRow label="WHIP"      away={awayStats?.whip}                  home={homeStats?.whip} higherBetter={false} />
          <StatRow label="K/9"       away={awayStats?.strikeouts_per_9}      home={homeStats?.strikeouts_per_9} />
          {(awayStats?.last_10_record || homeStats?.last_10_record) && (
            <div className="flex justify-between items-center text-xs py-0.5">
              <span className="text-slate-300 font-bold">{awayStats?.last_10_record ?? '—'}</span>
              <span className="text-slate-500 text-center flex-1 px-2">Last 10</span>
              <span className="text-slate-300 font-bold">{homeStats?.last_10_record ?? '—'}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
