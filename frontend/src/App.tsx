import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Navigation } from './components/Navigation';
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
import { MultiSport } from './pages/MultiSport';
import { Odds } from './pages/Odds';
import { Settings } from './pages/Settings';
import { StrategySettings } from './pages/StrategySettings';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public routes - Login and SignUp pages */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<SignUp />} />

          {/* All routes - login disabled for now */}
          <Route
            path="/*"
            element={
              <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
                <Navigation />
                <Routes>
                  <Route path="/" element={<LiveGames />} />
                  <Route path="/tools" element={<Tools />} />
                  <Route path="/analytics" element={<Analytics />} />
                  <Route path="/analytics-sample" element={<AnalyticsSample />} />
                  <Route path="/props" element={<Props />} />
                  <Route path="/alerts" element={<Alerts />} />
                  <Route path="/multi-sport" element={<MultiSport />} />
                  <Route path="/odds" element={<Odds />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/strategy-settings" element={<StrategySettings />} />
                  <Route path="/learn" element={<Learn />} />
                  <Route path="/learn/:articleId" element={<ArticleDetail />} />
                  <Route path="/getting-started" element={<GettingStarted />} />
                  <Route path="/pricing" element={<Pricing />} />
                </Routes>
              </div>
            }
          />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
