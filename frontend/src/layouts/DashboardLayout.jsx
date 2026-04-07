/**
 * DASHBOARD LAYOUT
 * 
 * Layout principal avec sidebar et header
 */

import React from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';

import { useAppStore } from '../app/store'; // ← UTILISER VOTRE STORE
import { NotificationBell } from '../features/notifications/components';

export function DashboardLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Adapter au store
  const user = useAppStore((state) => state.user);
  const clearSession = useAppStore((state) => state.clearSession);

  // Handle logout
  const handleLogout = () => {
    clearSession();
    navigate('/login');
  };

  // Navigation items by role
  const getNavItems = () => {
    const baseItems = [
      {
        path: '/app',
        label: 'Dashboard',
        icon: '📊',
        roles: ['COMMERCIAL', 'FINANCE', 'TECHNICIEN', 'ADMIN'],
      },
    ];

    const commercialItems = [
      { path: '/app/clients', label: 'Clients', icon: '👥', roles: ['COMMERCIAL', 'ADMIN'] },
      { path: '/app/catalogue', label: 'Catalogue', icon: '📦', roles: ['COMMERCIAL', 'ADMIN'] },
      { path: '/app/ventes', label: 'Ventes', icon: '💼', roles: ['COMMERCIAL', 'FINANCE', 'ADMIN'] },
    ];

    const techItems = [
      { path: '/app/provisions', label: 'Provisions', icon: '🔧', roles: ['TECHNICIEN', 'ADMIN'] },
    ];

    const notificationItems = [
      { path: '/app/notifications', label: 'Notifications', icon: '🔔', roles: ['COMMERCIAL', 'FINANCE', 'TECHNICIEN', 'ADMIN'] },
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
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors
                  ${
                    isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-50'
                  }
                `}
              >
                <span className="text-xl">{item.icon}</span>
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
              className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
            >
              <span>👤</span>
              <span>Mon profil</span>
            </Link>
          </div>
          <button
            onClick={handleLogout}
            className="w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            Déconnexion
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

            {/* Notification Bell */}
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
