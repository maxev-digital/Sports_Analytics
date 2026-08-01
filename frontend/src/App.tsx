import { HashRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Navigation } from './components/Navigation';
import { Footer } from './components/Footer';
import { ToastProvider } from './components/Toast';
import { BetAlertNotificationProvider } from './contexts/BetAlertNotificationContext';
import { BetSlipProvider } from './contexts/BetSlipContext';
import { BetSlipToast } from './components/BetSlipToast';
import { QuarterStrategyAlertMonitor } from './components/QuarterStrategyAlertMonitor';
import { GoaliePullMonitor } from './components/GoaliePullMonitor';
import { HedgeAlertMonitor } from './components/HedgeAlertMonitor';
import { FloatingFeedbackButton } from './components/FloatingFeedbackButton';

import { LandingPage } from './pages/LandingPage';
import { Login } from './pages/Login';
import { SignUp } from './pages/SignUp';
import { LiveGames } from './pages/LiveGames';
import { Odds } from './pages/Odds';
import { MaxEvEdges } from './pages/MaxEvEdges';
import { Kalshi } from './pages/Kalshi';
import { Tools } from './pages/Tools';
import { Analytics } from './pages/Analytics';
import { Props } from './pages/Props';
import { StrategyResults } from './pages/StrategyResults';
import { PreGameStrategyResults } from './pages/PreGameStrategyResults';
import { Alerts } from './pages/Alerts';
import AlertPreferences from './pages/AlertPreferences';
import { ModelPerformance } from './pages/ModelPerformance';
import PredictionsDatabase from './pages/PredictionsDatabase';
import { TeamRankings } from './pages/TeamRankings';
import { AdvancedMetrics } from './pages/AdvancedMetrics';
import { PlayerLeaders } from './pages/PlayerLeaders';
import { Settings } from './pages/Settings';
import { AdminDashboard } from './pages/AdminDashboard';
import { Pricing } from './pages/Pricing';
import { SystemHealth } from './pages/SystemHealth';
import { Picks } from './pages/Picks';
import SubscriptionSuccess from './pages/SubscriptionSuccess';
import SubscriptionCancel from './pages/SubscriptionCancel';
import { Terms } from './pages/Terms';
import { Privacy } from './pages/Privacy';
import { Disclaimer } from './pages/Disclaimer';
import { NFLSystem } from './pages/NFLSystem';
import { SystemOverview } from './pages/SystemOverview';
import { F5Edge } from './pages/F5Edge';
import { LineMovement } from './pages/LineMovement';
import { Statcast } from './pages/Statcast';
import { TrendsDashboard } from './pages/TrendsDashboard';
import { PowerRankings } from './pages/PowerRankings';

const bg = 'min-h-screen flex flex-col' /* dark matte via body bg */;

function AppContent() {
  const location = useLocation();
  const excludedPaths = ['/login', '/signup', '/pricing', '/terms', '/privacy', '/disclaimer'];
  const needsAlerts = location.pathname !== '/' && !excludedPaths.some(path => location.pathname.startsWith(path));

  return (
    <AuthProvider>
      <ToastProvider>
        <BetSlipProvider>
          <BetAlertNotificationProvider>
            <BetSlipToast />

            <QuarterStrategyAlertMonitor enabled={needsAlerts} />
            <GoaliePullMonitor enabled={needsAlerts} pollInterval={3000} />
            <HedgeAlertMonitor enabled={needsAlerts} pollInterval={10000} />

            <Routes>
              {/* Public auth */}
              <Route path="/login" element={<><Login /><Footer /></>} />
              <Route path="/signup" element={<><SignUp /><Footer /></>} />

              {/* Public legal */}
              <Route path="/terms" element={<Terms />} />
              <Route path="/privacy" element={<Privacy />} />
              <Route path="/disclaimer" element={<Disclaimer />} />

              {/* Public marketing */}
              <Route path="/pricing" element={
                <div className={bg}>
                  <Navigation />
                  <Pricing />
                  <Footer />
                </div>
              } />

              {/* Landing page (public) */}
              <Route path="/" element={
                <div className={bg}>
                  <Navigation />
                  <div className="flex-grow">
                    <LandingPage />
                  </div>
                  <Footer />
                </div>
              } />
              <Route path="/dashboard" element={<Navigate to="/" replace />} />

              {/* Subscription callbacks */}
              <Route path="/subscription/success" element={
                <ProtectedRoute requireSubscription={false}>
                  <><SubscriptionSuccess /><Footer /></>
                </ProtectedRoute>
              } />
              <Route path="/subscription/cancel" element={
                <ProtectedRoute requireSubscription={false}>
                  <><SubscriptionCancel /><Footer /></>
                </ProtectedRoute>
              } />

              {/* App shell — public pages accessible to all, sensitive pages require login */}
              <Route path="/*" element={
                <div className={bg}>
                  <Navigation />
                  <div className="flex-grow">
                    <Routes>
                      {/* Public pages — no login required */}
                      <Route path="/live-games" element={<LiveGames />} />
                      <Route path="/odds" element={<Odds />} />
                      <Route path="/max-ev-edges" element={<MaxEvEdges />} />
                      <Route path="/team-rankings" element={<TeamRankings />} />
                      <Route path="/picks" element={<Picks />} />
                      <Route path="/system-nfl" element={<NFLSystem />} />
                      <Route path="/system-overview" element={<SystemOverview />} />

                      {/* Login-required pages */}
                      <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
                      <Route path="/alerts" element={<ProtectedRoute><Alerts /></ProtectedRoute>} />
                      <Route path="/alert-preferences" element={<ProtectedRoute><AlertPreferences /></ProtectedRoute>} />
                      <Route path="/admin-dashboard" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />
                      <Route path="/system-health" element={<ProtectedRoute><SystemHealth /></ProtectedRoute>} />
                      <Route path="/kalshi" element={<ProtectedRoute><Kalshi /></ProtectedRoute>} />
                      <Route path="/tools" element={<ProtectedRoute><Tools /></ProtectedRoute>} />
                      <Route path="/f5-edge" element={<F5Edge />} />
                      <Route path="/line-movement" element={<LineMovement />} />
                      <Route path="/statcast" element={<Statcast />} />
                      <Route path="/trends" element={<TrendsDashboard />} />
                      <Route path="/power-rankings" element={<PowerRankings />} />
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
                  </div>
                  <Footer />
                  <FloatingFeedbackButton />
                </div>
              } />
            </Routes>
          </BetAlertNotificationProvider>
        </BetSlipProvider>
      </ToastProvider>
    </AuthProvider>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
