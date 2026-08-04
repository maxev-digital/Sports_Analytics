import { NFLTeamStats, NFLMomentumStats, NFLLiveStats, GameState } from '../../../types';
import { formatTeamName } from '../../../utils/teamNames';

interface NFLPanelProps {
  state: GameState;
  homeStats: NFLTeamStats | null;
  awayStats: NFLTeamStats | null;
  homeMomentum: NFLMomentumStats | null;
  awayMomentum: NFLMomentumStats | null;
  homeLive: NFLLiveStats | null;
  awayLive: NFLLiveStats | null;
  isLive: boolean;
  isNCAAF: boolean;
}

function StatRow({ label, away, home, higherBetter = true }: {
  label: string; away: number | null | undefined; home: number | null | undefined; higherBetter?: boolean;
}) {
  if (away == null && home == null) return null;
  const awayBetter = away != null && home != null && (higherBetter ? away > home : away < home);
  const homeBetter = away != null && home != null && (higherBetter ? home > away : home < away);
  return (
    <div className="flex justify-between items-center text-xs py-0.5">
      <span className={`font-bold ${awayBetter ? 'text-green-400' : 'text-slate-300'}`}>{away?.toFixed(1) ?? '—'}</span>
      <span className="text-slate-500 text-center flex-1 px-2">{label}</span>
      <span className={`font-bold ${homeBetter ? 'text-green-400' : 'text-slate-300'}`}>{home?.toFixed(1) ?? '—'}</span>
    </div>
  );
}

export function NFLPanel({ state, homeStats, awayStats, homeMomentum, awayMomentum, homeLive, awayLive, isLive, isNCAAF }: NFLPanelProps) {
  const awayName = formatTeamName(state.away_team.name, state.sport_key).split(' ').pop() ?? '';
  const homeName = formatTeamName(state.home_team.name, state.sport_key).split(' ').pop() ?? '';
  const league = isNCAAF ? 'NCAAF' : 'NFL';

  return (
    <div className="space-y-3 text-slate-300">
      {/* Live Momentum */}
      {isLive && (awayMomentum || homeMomentum) && (
        <div className="bg-green-900/20 border border-green-600/20 rounded p-2">
          <div className="text-xs font-bold text-green-400 mb-2 uppercase tracking-wide">Drive Momentum</div>
          <div className="grid grid-cols-2 gap-4 text-xs">
            {[{ m: awayMomentum, name: awayName }, { m: homeMomentum, name: homeName }].map(({ m, name }) => m && (
              <div key={name}>
                <div className="text-slate-400 font-semibold mb-1">{name}</div>
                <div className="flex justify-between"><span className="text-slate-500">Yds/Play</span><span className="font-bold">{m.yards_per_play.toFixed(1)}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Pts</span><span className="font-bold">{m.recent_points}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">RZ</span><span className="font-bold">{m.red_zone_efficiency}</span></div>
                {m.drive_state && (
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    m.drive_state === 'ATTACKING' ? 'bg-green-900/60 text-green-300' :
                    m.drive_state === 'DEFENDING' ? 'bg-red-900/60 text-red-300' : 'bg-slate-700 text-slate-400'
                  }`}>{m.drive_state}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Live Box Score */}
      {isLive && (awayLive || homeLive) && (
        <div className="bg-slate-800/60 rounded p-2">
          <div className="text-xs font-bold text-slate-400 mb-1 uppercase tracking-wide">Live Stats</div>
          <div className="grid grid-cols-3 text-xs gap-2">
            <span className="font-bold text-slate-300">{awayName}</span>
            <span className="text-center text-slate-500">Stat</span>
            <span className="font-bold text-slate-300 text-right">{homeName}</span>
          </div>
          {[
            { label: 'Pass Yds',  away: awayLive?.passing_yards,  home: homeLive?.passing_yards  },
            { label: 'Rush Yds',  away: awayLive?.rushing_yards,  home: homeLive?.rushing_yards  },
            { label: '3rd Dn',    away: awayLive?.third_down_eff, home: homeLive?.third_down_eff },
            { label: 'Red Zone',  away: awayLive?.red_zone,       home: homeLive?.red_zone       },
            { label: 'Turnovers', away: awayLive?.turnovers,      home: homeLive?.turnovers      },
          ].map(({ label, away, home }) => (away || home) ? (
            <div key={label} className="flex justify-between items-center text-xs py-0.5">
              <span className="text-slate-300 font-bold">{away ?? '—'}</span>
              <span className="text-slate-500 text-center flex-1 px-2">{label}</span>
              <span className="text-slate-300 font-bold text-right">{home ?? '—'}</span>
            </div>
          ) : null)}
        </div>
      )}

      {/* Season Stats */}
      {(homeStats || awayStats) && (
        <div className="bg-slate-800/60 rounded p-2">
          <div className="text-xs font-bold text-slate-400 mb-1 uppercase tracking-wide">{league} Season</div>
          <div className="grid grid-cols-3 text-xs mb-1">
            <span className="font-bold text-slate-300">{awayName}</span>
            <span className="text-center text-slate-500">Stat</span>
            <span className="font-bold text-slate-300 text-right">{homeName}</span>
          </div>
          <StatRow label="Pts/G"   away={awayStats?.points_per_game}         home={homeStats?.points_per_game} />
          <StatRow label="PA/G"    away={awayStats?.points_allowed_per_game}  home={homeStats?.points_allowed_per_game} higherBetter={false} />
          <StatRow label="Pass/G"  away={awayStats?.passing_yards_per_game}   home={homeStats?.passing_yards_per_game} />
          <StatRow label="Rush/G"  away={awayStats?.rushing_yards_per_game}   home={homeStats?.rushing_yards_per_game} />
          {(awayStats?.ats_wins != null || homeStats?.ats_wins != null) && (
            <div className="mt-1 pt-1 border-t border-slate-700">
              <div className="flex justify-between text-xs py-0.5">
                <span className="text-slate-300 font-bold">{awayStats ? `${awayStats.ats_wins}-${awayStats.ats_losses ?? 0}` : '—'}</span>
                <span className="text-slate-500 text-center flex-1 px-2">ATS</span>
                <span className="text-slate-300 font-bold">{homeStats ? `${homeStats.ats_wins}-${homeStats.ats_losses ?? 0}` : '—'}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
