import { Navigate } from 'react-router-dom';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireSubscription?: boolean;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const hasAccess = localStorage.getItem('mes_access_granted') === 'true';
  if (!hasAccess) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}
