import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import { Odds } from '../pages/Odds';
import { MaxEvEdges } from '../pages/MaxEvEdges';
import { Kalshi } from '../pages/Kalshi';
import { Tools } from '../pages/Tools';
import { Analytics } from '../pages/Analytics';
import { Props } from '../pages/Props';
import { StrategyResults } from '../pages/StrategyResults';
import { PreGameStrategyResults } from '../pages/PreGameStrategyResults';
import { ModelPerformance } from '../pages/ModelPerformance';
import PredictionsDatabase from '../pages/PredictionsDatabase';
import { TeamRankings } from '../pages/TeamRankings';
import { AdvancedMetrics } from '../pages/AdvancedMetrics';
import { PlayerLeaders } from '../pages/PlayerLeaders';
import { Settings } from '../pages/Settings';
import { AdminDashboard } from '../pages/AdminDashboard';
import { SystemHealth } from '../pages/SystemHealth';
import { Picks } from '../pages/Picks';
import { ModelProjections } from '../pages/ModelProjections';
import { AccuracyDashboard } from '../pages/AccuracyDashboard';
import { NFLSystem } from '../pages/NFLSystem';
import { SystemOverview } from '../pages/SystemOverview';
import { F5Edge } from '../pages/F5Edge';
import { TodaysPlays } from '../pages/TodaysPlays';
import { LineMovement } from '../pages/LineMovement';
import { Statcast } from '../pages/Statcast';
import { TrendsDashboard } from '../pages/TrendsDashboard';
import { PowerRankings } from '../pages/PowerRankings';
import { BettingRankings } from '../pages/BettingRankings';
import { TrackRecord } from '../pages/TrackRecord';
import { DailyRecap } from '../pages/DailyRecap';
import { Survivor } from '../pages/Survivor';
import { MatchupDetail } from '../pages/MatchupDetail';
import { NFLSchedule } from '../pages/NFLSchedule';
import { MatchupLab } from '../pages/MatchupLab';
import { ConfidencePool } from '../pages/ConfidencePool';
import { OpenBets } from '../pages/OpenBets';
import { MaddenRatings } from '../pages/MaddenRatings';
import { NFLTrends } from '../pages/NFLTrends';
import { InjuryImpact } from '../pages/InjuryImpact';
import { InjuryHeatmap } from '../pages/InjuryHeatmap';
import { RefereeTracker } from '../pages/RefereeTracker';
import { ModelResearch } from '../pages/ModelResearch';
import { DataPoints } from '../pages/DataPoints';
import { CFBRatings } from '../pages/CFBRatings';
import { MLBTeamStats } from '../pages/MLBTeamStats';
import { NFLTeamStats } from '../pages/NFLTeamStats';
import { ForgotPassword } from '../pages/ForgotPassword';
import { ResetPassword } from '../pages/ResetPassword';
import { LiveGames } from '../pages/LiveGames';

const M = ({ children }: { children: React.ReactNode }) => (
  <ProtectedRoute tier="member">{children}</ProtectedRoute>
);
const P = ({ children }: { children: React.ReactNode }) => (
  <ProtectedRoute tier="pro">{children}</ProtectedRoute>
);
const A = ({ children }: { children: React.ReactNode }) => (
  <ProtectedRoute tier="admin">{children}</ProtectedRoute>
);

export function AppRoutes() {
  return (
    <Routes>
      {/* ── Free — no login required ──────────────────────────────────── */}
      <Route path="/odds"            element={<Odds />} />
      <Route path="/live-games"      element={<LiveGames />} />
      <Route path="/alerts"          element={<Navigate to="/todays-plays" replace />} />
      <Route path="/todays-plays"    element={<TodaysPlays />} />
      <Route path="/picks"           element={<Picks />} />
      <Route path="/accuracy"        element={<AccuracyDashboard />} />
      <Route path="/power-rankings"  element={<PowerRankings />} />
      <Route path="/team-rankings"   element={<TeamRankings />} />
      <Route path="/track-record"    element={<TrackRecord />} />
      <Route path="/system-overview" element={<SystemOverview />} />
      <Route path="/system-nfl"      element={<NFLSystem />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password"  element={<ResetPassword />} />

      {/* ── Member — free signup required ─────────────────────────────── */}
      <Route path="/nfl-schedule"     element={<M><NFLSchedule /></M>} />
      <Route path="/survivor"         element={<M><Survivor /></M>} />
      <Route path="/confidence-pool"  element={<M><ConfidencePool /></M>} />
      <Route path="/matchup-lab"      element={<M><MatchupLab /></M>} />
      <Route path="/trends"           element={<M><TrendsDashboard /></M>} />
      <Route path="/nfl-trends"       element={<M><NFLTrends /></M>} />
      <Route path="/cfb-ratings"      element={<M><CFBRatings /></M>} />
      <Route path="/mlb-team-stats"   element={<M><MLBTeamStats /></M>} />
      <Route path="/nfl-team-stats"   element={<M><NFLTeamStats /></M>} />
      <Route path="/recap"            element={<M><DailyRecap /></M>} />
      <Route path="/data-points"      element={<M><DataPoints /></M>} />
      <Route path="/model-research"   element={<M><ModelResearch /></M>} />
      <Route path="/line-movement"    element={<M><LineMovement /></M>} />
      <Route path="/madden-ratings"   element={<M><MaddenRatings /></M>} />
      <Route path="/statcast"         element={<M><Statcast /></M>} />
      <Route path="/betting-rankings" element={<M><BettingRankings /></M>} />
      <Route path="/open-bets"        element={<M><OpenBets /></M>} />
      <Route path="/settings"         element={<M><Settings /></M>} />

      {/* ── Pro — $99/year ────────────────────────────────────────────── */}
      <Route path="/model-projections"    element={<P><ModelProjections /></P>} />
      <Route path="/model-performance"    element={<P><ModelPerformance /></P>} />
      <Route path="/predictions-database" element={<P><PredictionsDatabase /></P>} />
      <Route path="/f5-edge"              element={<P><F5Edge /></P>} />
      <Route path="/max-ev-edges"         element={<P><MaxEvEdges /></P>} />
      <Route path="/advanced-metrics"     element={<P><AdvancedMetrics /></P>} />
      <Route path="/player-leaders"       element={<P><PlayerLeaders /></P>} />
      <Route path="/referee-trends"       element={<P><RefereeTracker /></P>} />
      <Route path="/injury-impact"        element={<P><InjuryImpact /></P>} />
      <Route path="/injury-heatmap"       element={<P><InjuryHeatmap /></P>} />
      <Route path="/tools"                element={<P><Tools /></P>} />
      <Route path="/kalshi"               element={<P><Kalshi /></P>} />
      <Route path="/analytics"            element={<P><Analytics /></P>} />
      <Route path="/props"                element={<P><Props /></P>} />
      <Route path="/strategy-results"         element={<P><StrategyResults /></P>} />
      <Route path="/pre-game-strategy-results" element={<P><PreGameStrategyResults /></P>} />
      <Route path="/matchup/:eventId"          element={<M><MatchupDetail /></M>} />

      {/* ── Admin only ────────────────────────────────────────────────── */}
      <Route path="/admin-dashboard" element={<A><AdminDashboard /></A>} />
      <Route path="/system-health"   element={<A><SystemHealth /></A>} />

      <Route path="*" element={<Navigate to="/todays-plays" replace />} />
    </Routes>
  );
}
