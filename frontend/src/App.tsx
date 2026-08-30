import { HashRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Navigation } from './components/Navigation';
import { Footer } from './components/Footer';
import { ToastProvider } from './components/Toast';
import { BetAlertNotificationProvider } from './contexts/BetAlertNotificationContext';
import { BetSlipProvider } from './contexts/BetSlipContext';
import { BetSlipToast } from './components/BetSlipToast';
import { AgentChatWidget } from './components/agent/AgentChatWidget';
import { AgentProvider, useAgentContext } from './contexts/AgentContext';
import { AppRoutes } from './components/AppRoutes';

import { LandingPage } from './pages/LandingPage';
import { Login } from './pages/Login';
import { SignUp } from './pages/SignUp';
import { Pricing } from './pages/Pricing';
import { Terms } from './pages/Terms';
import { Privacy } from './pages/Privacy';
import { Disclaimer } from './pages/Disclaimer';
import SubscriptionSuccess from './pages/SubscriptionSuccess';
import SubscriptionCancel from './pages/SubscriptionCancel';

const bg = 'min-h-screen flex flex-col';
const queryClient = new QueryClient();

function AppContent() {
  const location = useLocation();
  const { isOpen, panelWidth } = useAgentContext();
  const excludedPaths = ['/login', '/signup', '/pricing', '/terms', '/privacy', '/disclaimer'];
  return (
    <AuthProvider>
      <ToastProvider>
        <BetSlipProvider>
          <BetAlertNotificationProvider>
            <BetSlipToast />

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

              {/* Landing page */}
              <Route path="/" element={
                <div className={bg}>
                  <Navigation />
                  <div className="flex-grow"><LandingPage /></div>
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

              {/* App shell */}
              <Route path="/*" element={
                <div className={bg}>
                  <Navigation />
                  {/* Shift content right when panel is open so it doesn't overlay */}
                  <div
                    className="flex flex-col flex-grow transition-[padding-right] duration-300 ease-in-out"
                    style={{ paddingRight: isOpen ? panelWidth : 0 }}
                  >
                    <div className="flex-grow"><AppRoutes /></div>
                    <Footer />
                  </div>
                  <AgentChatWidget />
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
    <QueryClientProvider client={queryClient}>
      <Router>
        <AgentProvider>
          <AppContent />
        </AgentProvider>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
