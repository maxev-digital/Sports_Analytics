import { TeamStats, NBAMomentumStats, GameState } from '../../../types';
import { formatTeamName } from '../../../utils/teamNames';

interface NBAPanelProps {
  state: GameState;
  homeStats: TeamStats | null;
  awayStats: TeamStats | null;
  homeMomentum: NBAMomentumStats | null;
  awayMomentum: NBAMomentumStats | null;
  isLive: boolean;
}

function StatRow({ label, away, home, higherBetter = true, pct = false }: { label: string; away: number | null | undefined; home: number | null | undefined; higherBetter?: boolean; pct?: boolean }) {
  if (away == null && home == null) return null;
  const awayBetter = away != null && home != null && (higherBetter ? away > home : away < home);
  const homeBetter = away != null && home != null && (higherBetter ? home > away : home < away);
  const fmt = (n: number) => pct ? `${(n * 100).toFixed(1)}%` : n.toFixed(1);
  return (
    <div className="flex justify-between items-center text-xs py-0.5">
      <span className={`font-bold ${awayBetter ? 'text-green-400' : 'text-slate-300'}`}>{away != null ? fmt(away) : '—'}</span>
      <span className="text-slate-500 text-center flex-1 px-2">{label}</span>
      <span className={`font-bold ${homeBetter ? 'text-green-400' : 'text-slate-300'}`}>{home != null ? fmt(home) : '—'}</span>
    </div>
  );
}

function MomentumCol({ label, m, opp }: { label: string; m: NBAMomentumStats; opp: NBAMomentumStats | null }) {
  return (
    <div>
      <div className="text-xs text-slate-400 font-semibold mb-1">{label}</div>
      <div className="space-y-0.5 text-xs">
        <div className="flex justify-between">
          <span className="text-slate-500">Score</span>
          <span className={`font-bold ${opp && m.points_last_5min > opp.points_last_5min ? 'text-green-400' : 'text-slate-300'}`}>{m.points_last_5min}pts</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">FG%</span>
          <span className={`font-bold ${opp && m.fg_pct_recent > opp.fg_pct_recent ? 'text-green-400' : 'text-slate-300'}`}>{m.fg_pct_recent.toFixed(1)}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">TO</span>
          <span className={`font-bold ${opp && m.turnovers < opp.turnovers ? 'text-green-400' : 'text-slate-300'}`}>{m.turnovers}</span>
        </div>
        {m.possession_indicator && (
          <span className={`text-xs px-1.5 py-0.5 rounded ${
            m.possession_indicator === 'ATTACKING' ? 'bg-green-900/60 text-green-300' :
            m.possession_indicator === 'DEFENDING' ? 'bg-red-900/60 text-red-300' :
            'bg-slate-700 text-slate-400'
          }`}>{m.possession_indicator}</span>
        )}
      </div>
    </div>
  );
}

export function NBAPanel({ state, homeStats, awayStats, homeMomentum, awayMomentum, isLive }: NBAPanelProps) {
  const awayName = formatTeamName(state.away_team.name, state.sport_key).split(' ').pop() ?? '';
  const homeName = formatTeamName(state.home_team.name, state.sport_key).split(' ').pop() ?? '';

  return (
    <div className="space-y-3 text-slate-300">
      {/* Live Momentum */}
      {isLive && (awayMomentum || homeMomentum) && (
        <div className="bg-blue-900/20 border border-blue-600/20 rounded p-2">
          <div className="text-xs font-bold text-blue-400 mb-2 uppercase tracking-wide">Live Momentum (Last 5 min)</div>
          <div className="grid grid-cols-2 gap-4">
            {awayMomentum && <MomentumCol label={awayName} m={awayMomentum} opp={homeMomentum} />}
            {homeMomentum && <MomentumCol label={homeName} m={homeMomentum} opp={awayMomentum} />}
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
          <StatRow label="Off Rtg"  away={awayStats?.off_rating}   home={homeStats?.off_rating} />
          <StatRow label="Def Rtg"  away={awayStats?.def_rating}   home={homeStats?.def_rating} higherBetter={false} />
          <StatRow label="Net Rtg"  away={awayStats?.net_rating}   home={homeStats?.net_rating} />
          <StatRow label="Pace"     away={awayStats?.pace}         home={homeStats?.pace} />
          <StatRow label="FG%"      away={awayStats?.fg_pct}       home={homeStats?.fg_pct} pct />
          <StatRow label="3P%"      away={awayStats?.fg3_pct}      home={homeStats?.fg3_pct} pct />
          <StatRow label="W%"       away={awayStats?.win_pct}      home={homeStats?.win_pct} />
        </div>
      )}
    </div>
  );
}
