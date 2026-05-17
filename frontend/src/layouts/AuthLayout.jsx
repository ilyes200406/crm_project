import { Navigate, Outlet } from 'react-router-dom';
import { Building2 } from 'lucide-react';

import { useAppStore } from '../app/store';

export function AuthLayout() {
  const isBootstrapped = useAppStore((state) => state.isBootstrapped);
  const isAuthenticated = useAppStore((state) => state.isAuthenticated());

  if (!isBootstrapped) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Chargement...
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
      <div className="w-full max-w-[460px]">
        {/* Brand header */}
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-2xl bg-slate-900 inline-flex items-center justify-center mb-3">
            <Building2 size={22} className="text-white" />
          </div>
          <p className="text-sm font-semibold text-gray-500 tracking-widest uppercase">Insomea CRM</p>
        </div>

        {/* Auth card */}
        <div className="bg-white rounded-2xl border border-gray-200 px-8 py-7 shadow-xl">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
