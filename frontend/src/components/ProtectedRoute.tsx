import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getUserTier, canAccessRoute, AccessTier } from '../lib/accessMap';

interface ProtectedRouteProps {
  children: React.ReactNode;
  tier?: AccessTier;
  /** Legacy prop — ignored, kept for compatibility */
  requireSubscription?: boolean;
}

export function ProtectedRoute({ children, tier = 'member' }: ProtectedRouteProps) {
  const { isAuthenticated, subscriptionTier, role, loading } = useAuth();

  // Wait for token verification before making any redirect decisions
  if (loading) return null;

  const userTier = getUserTier(isAuthenticated, subscriptionTier, role);

  if (!canAccessRoute(userTier, tier)) {
    if (!isAuthenticated) return <Navigate to="/login" replace />;
    return <Navigate to="/pricing" replace />;
  }

  return <>{children}</>;
}
