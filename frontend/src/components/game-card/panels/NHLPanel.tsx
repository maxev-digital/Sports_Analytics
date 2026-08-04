import { NHLTeamStats, NHLMomentumStats, GameState } from '../../../types';
import { formatTeamName } from '../../../utils/teamNames';

interface NHLPanelProps {
  state: GameState;
  homeStats: NHLTeamStats | null;
  awayStats: NHLTeamStats | null;
  homeMomentum: NHLMomentumStats | null;
  awayMomentum: NHLMomentumStats | null;
  isLive: boolean;
}

function StatRow({ label, away, home, higherBetter = true, pct = false }: {
  label: string; away: number | null | undefined; home: number | null | undefined;
  higherBetter?: boolean; pct?: boolean;
}) {
  if (away == null && home == null) return null;
  const awayBetter = away != null && home != null && (higherBetter ? away > home : away < home);
  const homeBetter = away != null && home != null && (higherBetter ? home > away : home < away);
  const fmt = (n: number) => pct ? `${(n * 100).toFixed(1)}%` : n.toFixed(2);
  return (
    <div className="flex justify-between items-center text-xs py-0.5">
      <span className={`font-bold ${awayBetter ? 'text-green-400' : 'text-slate-300'}`}>{away != null ? fmt(away) : '—'}</span>
      <span className="text-slate-500 text-center flex-1 px-2">{label}</span>
      <span className={`font-bold ${homeBetter ? 'text-green-400' : 'text-slate-300'}`}>{home != null ? fmt(home) : '—'}</span>
    </div>
  );
}

export function NHLPanel({ state, homeStats, awayStats, homeMomentum, awayMomentum, isLive }: NHLPanelProps) {
  const awayName = formatTeamName(state.away_team.name, state.sport_key).split(' ').pop() ?? '';
  const homeName = formatTeamName(state.home_team.name, state.sport_key).split(' ').pop() ?? '';

  return (
    <div className="space-y-3 text-slate-300">
      {/* Live Momentum */}
      {isLive && (awayMomentum || homeMomentum) && (
        <div className="bg-orange-900/20 border border-orange-600/20 rounded p-2">
          <div className="text-xs font-bold text-orange-400 mb-2 uppercase tracking-wide">Live Momentum</div>
          <div className="grid grid-cols-2 gap-4 text-xs">
            {[{ m: awayMomentum, name: awayName }, { m: homeMomentum, name: homeName }].map(({ m, name }) => m && (
              <div key={name}>
                <div className="text-slate-400 font-semibold mb-1">{name}</div>
                <div className="flex justify-between"><span className="text-slate-500">Shots</span><span className="font-bold">{m.recent_shots}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Chances</span><span className="font-bold">{m.scoring_chances}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">OZ Events</span><span className={`font-bold ${m.offensive_zone_events > 3 ? 'text-green-400' : 'text-slate-300'}`}>{m.offensive_zone_events}</span></div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Season Stats */}
      {(homeStats || awayStats) && (
        <div className="bg-slate-800/60 rounded p-2">
          <div className="grid grid-cols-3 text-xs mb-1">
            <span className="font-bold text-slate-300">{awayName}</span>
            <span className="text-center text-slate-500">Stat</span>
            <span className="font-bold text-slate-300 text-right">{homeName}</span>
          </div>
          <StatRow label="GF/GP"   away={awayStats?.goals_per_game}         home={homeStats?.goals_per_game} />
          <StatRow label="GA/GP"   away={awayStats?.goals_against_per_game} home={homeStats?.goals_against_per_game} higherBetter={false} />
          <StatRow label="PP%"     away={awayStats?.power_play_pct}          home={homeStats?.power_play_pct} />
          <StatRow label="PK%"     away={awayStats?.penalty_kill_pct}        home={homeStats?.penalty_kill_pct} />
          <StatRow label="SV%"     away={awayStats?.save_pct}                home={homeStats?.save_pct} />
          <StatRow label="SH%"     away={awayStats?.shooting_pct}            home={homeStats?.shooting_pct} />
          <StatRow label="PDO"     away={awayStats?.pdo}                     home={homeStats?.pdo} />
          {(awayStats?.last_10_record || homeStats?.last_10_record) && (
            <div className="flex justify-between text-xs py-0.5">
              <span className="text-slate-300 font-bold">{awayStats?.last_10_record ?? '—'}</span>
              <span className="text-slate-500 text-center flex-1 px-2">Last 10</span>
              <span className="text-slate-300 font-bold">{homeStats?.last_10_record ?? '—'}</span>
            </div>
          )}
          {/* Empty Net edge */}
          {(awayStats?.en_differential != null || homeStats?.en_differential != null) && (
            <div className="mt-1 pt-1 border-t border-slate-700">
              <div className="text-xs text-slate-500 mb-0.5">Empty Net Diff</div>
              <StatRow label="EN Diff" away={awayStats?.en_differential} home={homeStats?.en_differential} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
