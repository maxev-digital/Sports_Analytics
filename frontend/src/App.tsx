import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Navigation } from './components/Navigation';
import { Footer } from './components/Footer';
import { ElectronWindowControls } from './components/ElectronWindowControls';
import { ToastProvider } from './components/Toast';
import { Login } from './pages/Login';
import { SignUp } from './pages/SignUp';
import { LiveGames } from './pages/LiveGames';
import { Tools } from './pages/Tools';
import { Analytics } from './pages/Analytics';
import { AnalyticsSample } from './pages/AnalyticsSample';
import { Props } from './pages/Props';
import { StrategyResults } from './pages/StrategyResults';
import { PreGameStrategyResults } from './pages/PreGameStrategyResults';
import { Pricing } from './pages/Pricing';
import { Alerts } from './pages/Alerts';
import { Learn } from './pages/Learn';
import { ArticleDetail } from './pages/ArticleDetail';
import { GettingStarted } from './pages/GettingStarted';
import { OddsExplained } from './pages/OddsExplained';
import { Odds } from './pages/Odds';
import { HandicapperPicks } from './pages/HandicapperPicks';
import { Settings } from './pages/Settings';
import { StrategySettings } from './pages/StrategySettings';
import SoundPreview from './pages/SoundPreview';
import SubscriptionSuccess from './pages/SubscriptionSuccess';
import SubscriptionCancel from './pages/SubscriptionCancel';
import { Terms } from './pages/Terms';
import { Privacy } from './pages/Privacy';
import { Disclaimer } from './pages/Disclaimer';
import { FloatingFeedbackButton } from './components/FloatingFeedbackButton';
import { AdminDashboard } from './pages/AdminDashboard';
import { MyFeedback } from './pages/MyFeedback';
import { isElectron } from './utils/isElectron';

function App() {
  // Check if running in desktop (Electron) mode
  const isDesktop = isElectron();

  return (
    <Router>
      <AuthProvider>
        <ToastProvider>
        <Routes>
          {/* Public routes - Login and SignUp pages */}
          <Route path="/login" element={
            <>
              <Login />
              <Footer />
            </>
          } />
          <Route path="/signup" element={
            <>
              <SignUp />
              <Footer />
            </>
          } />

          {/* Root redirect to pricing page (public landing) */}
          <Route path="/" element={<Navigate to="/pricing" replace />} />

          {/* Pricing page - public, no auth required */}
          <Route
            path="/pricing"
            element={
              <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
                <Navigation />
                <Pricing />
                <Footer />
              </div>
            }
          />

          {/* Strategy Results - public for testing */}
          <Route
            path="/strategy-results"
            element={
              <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
                <Navigation />
                <StrategyResults />
                <Footer />
                {/* Floating Feedback & Chat - visible on Strategy Results page (hidden in desktop) */}
                {!isDesktop && (
                  <>
                    <FloatingFeedbackButton />
                  </>
                )}
              </div>
            }
          />

          {/* Pre-Game Strategy Results - public for testing */}
          <Route
            path="/pre-game-strategy-results"
            element={
              <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
                <Navigation />
                <PreGameStrategyResults />
                <Footer />
                {/* Floating Feedback & Chat - visible on Pre-Game Strategy Results page (hidden in desktop) */}
                {!isDesktop && (
                  <>
                    <FloatingFeedbackButton />
                  </>
                )}
              </div>
            }
          />

          {/* Legal pages - public */}
          <Route path="/terms" element={<Terms />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/disclaimer" element={<Disclaimer />} />

          <Route
            path="/subscription/success"
            element={
              <ProtectedRoute requireSubscription={false}>
                <>
                  <SubscriptionSuccess />
                  <Footer />
                </>
              </ProtectedRoute>
            }
          />
          <Route
            path="/subscription/cancel"
            element={
              <ProtectedRoute requireSubscription={false}>
                <>
                  <SubscriptionCancel />
                  <Footer />
                </>
              </ProtectedRoute>
            }
          />

          {/* Protected routes - require BOTH login AND paid subscription */}
          <Route
            path="/*"
            element={
              <ProtectedRoute requireSubscription={true}>
                <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
                  <Navigation />
                  <ElectronWindowControls />
                  <div className="flex-grow">
                    <Routes>
                      <Route path="/dashboard" element={<Navigate to="/live-games" replace />} />
                      <Route path="/live-games" element={<LiveGames />} />
                      <Route path="/tools" element={<Tools />} />
                      <Route path="/analytics" element={<Analytics />} />
                      <Route path="/analytics-sample" element={<AnalyticsSample />} />
                      <Route path="/props" element={<Props />} />

                      <Route path="/alerts" element={<Alerts />} />
                      <Route path="/odds" element={<Odds />} />
                      <Route path="/handicapper-picks" element={<HandicapperPicks />} />
                      <Route path="/settings" element={<Settings />} />
                      <Route path="/strategy-settings" element={<StrategySettings />} />
                      <Route path="/my-feedback" element={<MyFeedback />} />
                      {/* Learn pages - redirect to home in desktop mode */}
                      <Route path="/learn" element={isDesktop ? <Navigate to="/live-games" replace /> : <Learn />} />
                      <Route path="/learn/:articleId" element={isDesktop ? <Navigate to="/live-games" replace /> : <ArticleDetail />} />
                      <Route path="/getting-started" element={isDesktop ? <Navigate to="/live-games" replace /> : <GettingStarted />} />
                      <Route path="/odds-explained" element={isDesktop ? <Navigate to="/live-games" replace /> : <OddsExplained />} />
                      {/* Admin and sample pages - redirect to home in desktop mode */}
                      <Route path="/sound-preview" element={<SoundPreview />} />
                      <Route path="/admin-dashboard" element={isDesktop ? <Navigate to="/live-games" replace /> : <AdminDashboard />} />
                    </Routes>
                  </div>
                  <Footer />
                  {/* Floating Feedback Button - visible on all protected pages (hidden in desktop) */}
                  {!isDesktop && (
                    <>
                      <FloatingFeedbackButton />
                    </>
                  )}
                </div>
              </ProtectedRoute>
            }
          />
        </Routes>
        </ToastProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
