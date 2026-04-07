import { Navigate, useLocation } from 'react-router-dom';

import { useAppStore } from '../app/store';

export function ProtectedRoute({ children, allowedRoles = [] }) {
  const location = useLocation();
  const isBootstrapped = useAppStore((state) => state.isBootstrapped);
  const isAuthenticated = useAppStore((state) => state.isAuthenticated());
  const hasRole = useAppStore((state) => state.hasRole(allowedRoles));

  if (!isBootstrapped) {
    return <div className="screen-center">Loading session...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!hasRole) {
    return <Navigate to="/app" replace />;
  }

  return children;
}
