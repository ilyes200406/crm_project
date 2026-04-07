import { Navigate, Outlet } from 'react-router-dom';

import { useAppStore } from '../app/store';

export function AuthLayout() {
  const isBootstrapped = useAppStore((state) => state.isBootstrapped);
  const isAuthenticated = useAppStore((state) => state.isAuthenticated());

  if (!isBootstrapped) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Loading session...
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/app" replace />;
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{ background: 'radial-gradient(circle at top, #e0f2fe 0%, #f8fafc 55%)' }}
    >
      <div className="w-full max-w-[460px] bg-white rounded-2xl border border-gray-200 p-6 shadow-xl">
        <Outlet />
      </div>
    </div>
  );
}
