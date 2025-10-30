import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Navigation } from './components/Navigation';
import { Footer } from './components/Footer';
import { ElectronWindowControls } from './components/ElectronWindowControls';
import { Login } from './pages/Login';
import { SignUp } from './pages/SignUp';
import { LiveGames } from './pages/LiveGames';
import { Tools } from './pages/Tools';
import { Analytics } from './pages/Analytics';
import { AnalyticsSample } from './pages/AnalyticsSample';
import { Props } from './pages/Props';
import { Pricing } from './pages/Pricing';
import { Alerts } from './pages/Alerts';
import { Learn } from './pages/Learn';
import { ArticleDetail } from './pages/ArticleDetail';
import { GettingStarted } from './pages/GettingStarted';
import { OddsExplained } from './pages/OddsExplained';
import { MultiSport } from './pages/MultiSport';
import { Odds } from './pages/Odds';
import { HandicapperPicks } from './pages/HandicapperPicks';
import { Settings } from './pages/Settings';
import { StrategySettings } from './pages/StrategySettings';
import SoundPreview from './pages/SoundPreview';
import SubscriptionSuccess from './pages/SubscriptionSuccess';
import SubscriptionCancel from './pages/SubscriptionCancel';

function App() {
  return (
    <Router>
      <AuthProvider>
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

          {/* Root redirect to login */}
          <Route path="/" element={<Navigate to="/login" replace />} />

          {/* Auth-only routes - require login but NOT subscription (for subscribing) */}
          <Route
            path="/pricing"
            element={
              <ProtectedRoute requireSubscription={false}>
                <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
                  <Navigation />
                  <Pricing />
                  <Footer />
                </div>
              </ProtectedRoute>
            }
          />
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
                      <Route path="/multi-sport" element={<MultiSport />} />
                      <Route path="/odds" element={<Odds />} />
                      <Route path="/handicapper-picks" element={<HandicapperPicks />} />
                      <Route path="/settings" element={<Settings />} />
                      <Route path="/strategy-settings" element={<StrategySettings />} />
                      <Route path="/learn" element={<Learn />} />
                      <Route path="/learn/:articleId" element={<ArticleDetail />} />
                      <Route path="/getting-started" element={<GettingStarted />} />
                      <Route path="/odds-explained" element={<OddsExplained />} />
                      <Route path="/sound-preview" element={<SoundPreview />} />
                    </Routes>
                  </div>
                  <Footer />
                </div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
