import React from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import {
  BarChart3, Users, Package, Factory, Briefcase,
  ClipboardList, Wrench, Bell, User, LogOut,
} from 'lucide-react';

import { useAppStore } from '../app/store';
import { NotificationBell } from '../features/notifications/components';

export function DashboardLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  const user = useAppStore((state) => state.user);
  const clearSession = useAppStore((state) => state.clearSession);

  const handleLogout = () => {
    clearSession();
    navigate('/login');
  };

  const getNavItems = () => {
    const baseItems = [
      {
        path: '/app',
        label: 'Dashboard',
        Icon: BarChart3,
        roles: ['COMMERCIAL', 'FINANCE', 'TECHNICIEN', 'ADMIN'],
      },
    ];

    const commercialItems = [
      { path: '/app/clients',              label: 'Clients',        Icon: Users,         roles: ['COMMERCIAL', 'FINANCE', 'TECHNICIEN', 'ADMIN'] },
      { path: '/app/catalogue',            label: 'Produits',       Icon: Package,       roles: ['COMMERCIAL', 'FINANCE', 'TECHNICIEN', 'ADMIN'] },
      { path: '/app/catalogue/suppliers',  label: 'Fournisseurs',   Icon: Factory,       roles: ['COMMERCIAL', 'FINANCE', 'TECHNICIEN', 'ADMIN'] },
      { path: '/app/ventes',               label: 'Ventes',         Icon: Briefcase,     roles: ['COMMERCIAL', 'FINANCE', 'ADMIN'] },
      { path: '/app/ventes/subscriptions', label: 'Abonnements',    Icon: ClipboardList, roles: ['COMMERCIAL', 'FINANCE', 'TECHNICIEN', 'ADMIN'] },
    ];

    const techItems = [
      { path: '/app/ventes/provisions', label: 'Provisions', Icon: Wrench, roles: ['TECHNICIEN', 'ADMIN'] },
    ];

    const notificationItems = [
      { path: '/app/notifications', label: 'Notifications', Icon: Bell, roles: ['COMMERCIAL', 'FINANCE', 'TECHNICIEN', 'ADMIN'] },
    ];

    return [...baseItems, ...commercialItems, ...techItems, ...notificationItems].filter((item) =>
      item.roles.includes(user?.role)
    );
  };

  const navItems = getNavItems();

  return (
    <div className="min-h-screen bg-gray-100 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-200">
          <h1 className="text-2xl font-bold text-blue-600">Insomea CRM</h1>
          <p className="text-xs text-gray-500 mt-1">Gestion commerciale</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <item.Icon
                  size={18}
                  className={isActive ? 'text-blue-600' : 'text-gray-400'}
                />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* User section */}
        <div className="p-4 border-t border-gray-200">
          <div className="mb-3">
            <div className="text-sm font-medium text-gray-900">
              {user?.first_name ? `${user.first_name} ${user.last_name}`.trim() : user?.email}
            </div>
            <div className="text-xs text-gray-500">{user?.role}</div>
          </div>
          <div className="space-y-1 mb-3">
            <Link
              to="/app/profile"
              className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-lg transition-colors"
            >
              <User size={15} className="text-gray-400" />
              <span>Mon profil</span>
            </Link>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <LogOut size={15} className="text-red-500" />
            <span>Déconnexion</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Bienvenue, <span className="font-medium text-gray-900">{user?.email}</span>
            </div>
            <NotificationBell />
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
