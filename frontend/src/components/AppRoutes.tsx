import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import { Odds } from '../pages/Odds';
import { MaxEvEdges } from '../pages/MaxEvEdges';
import { Tools } from '../pages/Tools';
import { Analytics } from '../pages/Analytics';
import { Props } from '../pages/Props';
import { ModelPerformance } from '../pages/ModelPerformance';
import PredictionsDatabase from '../pages/PredictionsDatabase';
import { Settings } from '../pages/Settings';
import { AdminDashboard } from '../pages/AdminDashboard';
import { SystemHealth } from '../pages/SystemHealth';
import { Picks } from '../pages/Picks';
import { ModelProjections } from '../pages/ModelProjections';
import { F5Edge } from '../pages/F5Edge';
import { TodaysPlays } from '../pages/TodaysPlays';
import { LineMovement } from '../pages/LineMovement';
import { Statcast } from '../pages/Statcast';
import { PowerRankings } from '../pages/PowerRankings';
import { BettingRankings } from '../pages/BettingRankings';
import { TrackRecord } from '../pages/TrackRecord';
import { DailyRecap } from '../pages/DailyRecap';
import { Survivor } from '../pages/Survivor';
import { MatchupDetail } from '../pages/MatchupDetail';
import { ConfidencePool } from '../pages/ConfidencePool';
import { OpenBets } from '../pages/OpenBets';
import { InjuryImpact } from '../pages/InjuryImpact';
import { InjuryHeatmap } from '../pages/InjuryHeatmap';
import { RefereeTracker } from '../pages/RefereeTracker';
import { DataPoints } from '../pages/DataPoints';
import { ModelResearch } from '../pages/ModelResearch';
import { TrendsDashboard } from '../pages/TrendsDashboard';
import { NFLTrends } from '../pages/NFLTrends';
import { CFBRatings } from '../pages/CFBRatings';
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
      <Route path="/power-rankings"  element={<PowerRankings />} />
      <Route path="/track-record"    element={<TrackRecord />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password"  element={<ResetPassword />} />

      {/* ── Member — free signup required ─────────────────────────────── */}
      <Route path="/survivor"         element={<Survivor />} />
      <Route path="/confidence-pool"  element={<M><ConfidencePool /></M>} />
      <Route path="/recap"            element={<M><DailyRecap /></M>} />
      <Route path="/line-movement"    element={<M><LineMovement /></M>} />
      <Route path="/statcast"         element={<M><Statcast /></M>} />
      <Route path="/betting-rankings" element={<M><BettingRankings /></M>} />
      <Route path="/open-bets"        element={<M><OpenBets /></M>} />
      <Route path="/settings"         element={<M><Settings /></M>} />
      <Route path="/matchup/:eventId" element={<M><MatchupDetail /></M>} />
      <Route path="/data-points"      element={<M><DataPoints /></M>} />
      <Route path="/model-research"   element={<M><ModelResearch /></M>} />
      <Route path="/trends"           element={<M><TrendsDashboard /></M>} />
      <Route path="/nfl-trends"       element={<M><NFLTrends /></M>} />
      <Route path="/cfb-ratings"      element={<M><CFBRatings /></M>} />

      {/* ── Pro — $99/year ────────────────────────────────────────────── */}
      <Route path="/model-projections"    element={<P><ModelProjections /></P>} />
      <Route path="/model-performance"    element={<P><ModelPerformance /></P>} />
      <Route path="/predictions-database" element={<P><PredictionsDatabase /></P>} />
      <Route path="/f5-edge"              element={<P><F5Edge /></P>} />
      <Route path="/max-ev-edges"         element={<P><MaxEvEdges /></P>} />
      <Route path="/referee-trends"       element={<P><RefereeTracker /></P>} />
      <Route path="/injury-impact"        element={<P><InjuryImpact /></P>} />
      <Route path="/injury-heatmap"       element={<P><InjuryHeatmap /></P>} />
      <Route path="/tools"                element={<P><Tools /></P>} />
      <Route path="/analytics"            element={<P><Analytics /></P>} />
      <Route path="/props"                element={<P><Props /></P>} />

      {/* ── Admin only ────────────────────────────────────────────────── */}
      <Route path="/admin-dashboard" element={<A><AdminDashboard /></A>} />
      <Route path="/system-health"   element={<A><SystemHealth /></A>} />

      <Route path="*" element={<Navigate to="/todays-plays" replace />} />
    </Routes>
  );
}
