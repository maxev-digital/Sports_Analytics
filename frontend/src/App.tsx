import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Navigation } from './components/Navigation';
import { Login } from './pages/Login';
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
import { Settings } from './pages/Settings';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public route - Login page */}
          <Route path="/login" element={<Login />} />

          {/* Protected routes - require authentication */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
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
                    <Route path="/settings" element={<Settings />} />
                    <Route path="/learn" element={<Learn />} />
                    <Route path="/learn/:articleId" element={<ArticleDetail />} />
                    <Route path="/getting-started" element={<GettingStarted />} />
                    <Route path="/pricing" element={<Pricing />} />
                  </Routes>
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
