import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import { LiveGames } from '../pages/LiveGames';
import { Odds } from '../pages/Odds';
import { MaxEvEdges } from '../pages/MaxEvEdges';
import { Kalshi } from '../pages/Kalshi';
import { Tools } from '../pages/Tools';
import { Analytics } from '../pages/Analytics';
import { Props } from '../pages/Props';
import { StrategyResults } from '../pages/StrategyResults';
import { PreGameStrategyResults } from '../pages/PreGameStrategyResults';
import { Alerts } from '../pages/Alerts';
import AlertPreferences from '../pages/AlertPreferences';
import { ModelPerformance } from '../pages/ModelPerformance';
import PredictionsDatabase from '../pages/PredictionsDatabase';
import { TeamRankings } from '../pages/TeamRankings';
import { AdvancedMetrics } from '../pages/AdvancedMetrics';
import { PlayerLeaders } from '../pages/PlayerLeaders';
import { Settings } from '../pages/Settings';
import { AdminDashboard } from '../pages/AdminDashboard';
import { SystemHealth } from '../pages/SystemHealth';
import { Picks } from '../pages/Picks';
import { NFLSystem } from '../pages/NFLSystem';
import { SystemOverview } from '../pages/SystemOverview';
import { F5Edge } from '../pages/F5Edge';
import { LineMovement } from '../pages/LineMovement';
import { Statcast } from '../pages/Statcast';
import { TrendsDashboard } from '../pages/TrendsDashboard';
import { PowerRankings } from '../pages/PowerRankings';
import { BettingRankings } from '../pages/BettingRankings';
import { TrackRecord } from '../pages/TrackRecord';
import { DailyRecap } from '../pages/DailyRecap';
import { Survivor } from '../pages/Survivor';
import { MatchupLab } from '../pages/MatchupLab';
import { ConfidencePool } from '../pages/ConfidencePool';
import { OpenBets } from '../pages/OpenBets';
import { MaddenRatings } from '../pages/MaddenRatings';
import { NFLTrends } from '../pages/NFLTrends';
import { InjuryImpact } from '../pages/InjuryImpact';
import { RefereeTracker } from '../pages/RefereeTracker';

export function AppRoutes() {
  return (
    <Routes>
      {/* Public pages — no login required */}
      <Route path="/live-games" element={<LiveGames />} />
      <Route path="/odds" element={<Odds />} />
      <Route path="/max-ev-edges" element={<MaxEvEdges />} />
      <Route path="/team-rankings" element={<TeamRankings />} />
      <Route path="/picks" element={<Picks />} />
      <Route path="/system-nfl" element={<NFLSystem />} />
      <Route path="/system-overview" element={<SystemOverview />} />
      <Route path="/f5-edge" element={<F5Edge />} />
      <Route path="/line-movement" element={<LineMovement />} />
      <Route path="/statcast" element={<Statcast />} />
      <Route path="/trends" element={<TrendsDashboard />} />
      <Route path="/power-rankings" element={<PowerRankings />} />
      <Route path="/matchup-lab" element={<MatchupLab />} />
      <Route path="/betting-rankings" element={<BettingRankings />} />
      <Route path="/track-record" element={<TrackRecord />} />
      <Route path="/recap" element={<DailyRecap />} />
      <Route path="/survivor" element={<Survivor />} />
      <Route path="/confidence-pool" element={<ConfidencePool />} />
      <Route path="/madden-ratings" element={<MaddenRatings />} />
      <Route path="/nfl-trends" element={<NFLTrends />} />
      <Route path="/injury-impact" element={<InjuryImpact />} />
      <Route path="/referee-trends" element={<RefereeTracker />} />

      {/* Login-required pages */}
      <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
      <Route path="/alerts" element={<ProtectedRoute><Alerts /></ProtectedRoute>} />
      <Route path="/alert-preferences" element={<ProtectedRoute><AlertPreferences /></ProtectedRoute>} />
      <Route path="/admin-dashboard" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />
      <Route path="/system-health" element={<ProtectedRoute><SystemHealth /></ProtectedRoute>} />
      <Route path="/kalshi" element={<ProtectedRoute><Kalshi /></ProtectedRoute>} />
      <Route path="/tools" element={<ProtectedRoute><Tools /></ProtectedRoute>} />
      <Route path="/open-bets" element={<ProtectedRoute><OpenBets /></ProtectedRoute>} />
      <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
      <Route path="/props" element={<ProtectedRoute><Props /></ProtectedRoute>} />
      <Route path="/strategy-results" element={<ProtectedRoute><StrategyResults /></ProtectedRoute>} />
      <Route path="/pre-game-strategy-results" element={<ProtectedRoute><PreGameStrategyResults /></ProtectedRoute>} />
      <Route path="/model-performance" element={<ProtectedRoute><ModelPerformance /></ProtectedRoute>} />
      <Route path="/predictions-database" element={<ProtectedRoute><PredictionsDatabase /></ProtectedRoute>} />
      <Route path="/advanced-metrics" element={<ProtectedRoute><AdvancedMetrics /></ProtectedRoute>} />
      <Route path="/player-leaders" element={<ProtectedRoute><PlayerLeaders /></ProtectedRoute>} />

      <Route path="*" element={<Navigate to="/live-games" replace />} />
    </Routes>
  );
}
