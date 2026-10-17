import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { NotFound } from '../pages/NotFound';
const FamilyAccess = lazy(() => import('../pages/FamilyAccess'));
import { ProtectedRoute } from './ProtectedRoute';

const Odds             = lazy(() => import('../pages/Odds').then(m => ({ default: m.Odds })));
const MaxEvEdges       = lazy(() => import('../pages/MaxEvEdges').then(m => ({ default: m.MaxEvEdges })));
const Tools            = lazy(() => import('../pages/Tools').then(m => ({ default: m.Tools })));
const Analytics        = lazy(() => import('../pages/Analytics').then(m => ({ default: m.Analytics })));
const Props            = lazy(() => import('../pages/Props').then(m => ({ default: m.Props })));
const ModelPerformance = lazy(() => import('../pages/ModelPerformance').then(m => ({ default: m.ModelPerformance })));
const PredictionsDatabase = lazy(() => import('../pages/PredictionsDatabase'));
const Settings         = lazy(() => import('../pages/Settings').then(m => ({ default: m.Settings })));
const ContestTracker   = lazy(() => import('../pages/ContestTracker').then(m => ({ default: m.ContestTracker })));
const AdminDashboard   = lazy(() => import('../pages/AdminDashboard').then(m => ({ default: m.AdminDashboard })));
const SystemHealth     = lazy(() => import('../pages/SystemHealth').then(m => ({ default: m.SystemHealth })));
const Picks            = lazy(() => import('../pages/Picks').then(m => ({ default: m.Picks })));
const ModelProjections = lazy(() => import('../pages/ModelProjections').then(m => ({ default: m.ModelProjections })));
const F5Edge           = lazy(() => import('../pages/F5Edge').then(m => ({ default: m.F5Edge })));
const TodaysPlays      = lazy(() => import('../pages/TodaysPlays').then(m => ({ default: m.TodaysPlays })));
const LineMovement     = lazy(() => import('../pages/LineMovement').then(m => ({ default: m.LineMovement })));
const Statcast         = lazy(() => import('../pages/Statcast').then(m => ({ default: m.Statcast })));
const PowerRankings    = lazy(() => import('../pages/PowerRankings').then(m => ({ default: m.PowerRankings })));
const BettingRankings  = lazy(() => import('../pages/BettingRankings').then(m => ({ default: m.BettingRankings })));
const TrackRecord      = lazy(() => import('../pages/TrackRecord').then(m => ({ default: m.TrackRecord })));
const DailyRecap       = lazy(() => import('../pages/DailyRecap').then(m => ({ default: m.DailyRecap })));
const Survivor         = lazy(() => import('../pages/Survivor').then(m => ({ default: m.Survivor })));
const MatchupDetail    = lazy(() => import('../pages/MatchupDetail').then(m => ({ default: m.MatchupDetail })));
const ConfidencePool   = lazy(() => import('../pages/ConfidencePool').then(m => ({ default: m.ConfidencePool })));
const OpenBets         = lazy(() => import('../pages/OpenBets').then(m => ({ default: m.OpenBets })));
const InjuryImpact     = lazy(() => import('../pages/InjuryImpact').then(m => ({ default: m.InjuryImpact })));
const InjuryHeatmap    = lazy(() => import('../pages/InjuryHeatmap').then(m => ({ default: m.InjuryHeatmap })));
const RefereeTracker   = lazy(() => import('../pages/RefereeTracker').then(m => ({ default: m.RefereeTracker })));
const DataPoints       = lazy(() => import('../pages/DataPoints').then(m => ({ default: m.DataPoints })));
const ModelResearch    = lazy(() => import('../pages/ModelResearch').then(m => ({ default: m.ModelResearch })));
const TrendsDashboard  = lazy(() => import('../pages/TrendsDashboard').then(m => ({ default: m.TrendsDashboard })));
const NFLTrends        = lazy(() => import('../pages/NFLTrends').then(m => ({ default: m.NFLTrends })));
const CFBRatings       = lazy(() => import('../pages/CFBRatings').then(m => ({ default: m.CFBRatings })));
const CFBTrends        = lazy(() => import('../pages/CFBTrends'));
const NFLTeamStats     = lazy(() => import('../pages/NFLTeamStats').then(m => ({ default: m.NFLTeamStats })));
const ForgotPassword   = lazy(() => import('../pages/ForgotPassword').then(m => ({ default: m.ForgotPassword })));
const ResetPassword    = lazy(() => import('../pages/ResetPassword').then(m => ({ default: m.ResetPassword })));
const LiveGames        = lazy(() => import('../pages/LiveGames').then(m => ({ default: m.LiveGames })));

const PageLoader = () => (
  <div className="flex items-center justify-center py-20 text-slate-400 text-sm">Loading...</div>
);

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
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* ── Free — no login required ──────────────────────────────────── */}
        <Route path="/family"          element={<FamilyAccess />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password"  element={<ResetPassword />} />

        {/* ── Member — free signup required ─────────────────────────────── */}
        <Route path="/odds"            element={<M><Odds /></M>} />
        <Route path="/live-games"      element={<M><LiveGames /></M>} />
        <Route path="/alerts"          element={<Navigate to="/todays-plays" replace />} />
        <Route path="/todays-plays"    element={<M><TodaysPlays /></M>} />
        <Route path="/picks"           element={<P><Picks /></P>} />
        <Route path="/power-rankings"  element={<M><PowerRankings /></M>} />
        <Route path="/track-record"    element={<M><TrackRecord /></M>} />
        <Route path="/survivor"         element={<Survivor />} />
        <Route path="/confidence-pool"  element={<M><ConfidencePool /></M>} />
        <Route path="/contests"         element={<M><ContestTracker /></M>} />
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
        <Route path="/cfb-trends"      element={<M><CFBTrends /></M>} />
        <Route path="/nfl-team-stats"  element={<M><NFLTeamStats /></M>} />
        <Route path="/rankings"        element={<Navigate to="/power-rankings" replace />} />

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

        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}
