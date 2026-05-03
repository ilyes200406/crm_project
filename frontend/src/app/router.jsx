import { createBrowserRouter, Navigate } from 'react-router-dom';
// import { useAppStore } from './store';

import { AuthLayout } from '../layouts/AuthLayout';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { ProtectedRoute } from '../routes/ProtectedRoute';
import { LoginPage } from '../features/auth/pages/LoginPage';
import { SetupAccountPage } from '../features/auth/pages/SetupAccountPage';
import { ForgotPasswordPage } from '../features/auth/pages/ForgotPasswordPage';
import { ResetPasswordPage } from '../features/auth/pages/ResetPasswordPage';
import { ChangePasswordPage } from '../features/auth/pages/ChangePasswordPage';
import { DashboardHomePage } from '../features/users/pages/DashboardHomePage';
import { MePage } from '../features/users/pages/MePage';
import { UsersListPage } from '../features/users/pages/UsersListPage';
import { CreateUserPage } from '../features/users/pages/CreateUserPage';
import { NotificationsPage } from '../features/notifications/pages';

// Import Clients pages
import {
  ClientsListPage,
  ClientDetailPage,
  CreateClientPage,
  EditClientPage,
} from '../features/clients/pages';

// Import Catalogue pages
import {
  ProductsListPage,
  ProductDetailPage,
  SuppliersListPage,
  SupplierDetailPage,
} from '../features/catalogue/pages';

// Import Ventes pages
import {
  // CommercialDashboard,
  // FinanceDashboard,
  // TechDashboard,
  OpportunitiesListPage,
  CreateOpportunityPage,
  OpportunityDetailPage,
  ProvisionsListPage,
  ProvisionDetailPage,
  SubscriptionsListPage,
  SubscriptionDetailPage,
} from '../features/ventes/pages';

/** Route to the correct dashboard based on the authenticated user's role. */
// function VentesDashboardRoute() {
//   const user = useAppStore((state) => state.user);
//   const role = user?.role;
//   if (role === 'FINANCE') return <FinanceDashboard />;
//   if (role === 'TECHNICIEN') return <TechDashboard />;
//   return <CommercialDashboard />;
// }

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/app" replace />,
  },
  {
    element: <AuthLayout />,
    children: [
      { path: '/login', element: <LoginPage /> },
      { path: '/setup', element: <SetupAccountPage /> },
      { path: '/forgot-password', element: <ForgotPasswordPage /> },
      { path: '/reset-password', element: <ResetPasswordPage /> },
    ],
  },
  {
    path: '/app',
    element: (
      <ProtectedRoute>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <DashboardHomePage /> },
      { path: 'profile', element: <MePage /> },
      { path: 'change-password', element: <ChangePasswordPage /> },
      
      // Users (ADMIN only)
      {
        path: 'users',
        element: (
          <ProtectedRoute allowedRoles={['ADMIN']}>
            <UsersListPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'users/new',
        element: (
          <ProtectedRoute allowedRoles={['ADMIN']}>
            <CreateUserPage />
          </ProtectedRoute>
        ),
      },
      
      // Clients (COMMERCIAL, FINANCE, TECHNICIEN, ADMIN — read; create/edit gated in page UI)
      {
        path: 'clients',
        element: (
          <ProtectedRoute allowedRoles={['COMMERCIAL', 'FINANCE', 'TECHNICIEN', 'ADMIN']}>
            <ClientsListPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'clients/new',
        element: (
          <ProtectedRoute allowedRoles={['COMMERCIAL', 'ADMIN']}>
            <CreateClientPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'clients/:id',
        element: (
          <ProtectedRoute allowedRoles={['COMMERCIAL', 'FINANCE', 'TECHNICIEN', 'ADMIN']}>
            <ClientDetailPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'clients/:id/edit',
        element: (
          <ProtectedRoute allowedRoles={['COMMERCIAL', 'ADMIN']}>
            <EditClientPage />
          </ProtectedRoute>
        ),
      },

      // Catalogue - Products (Tous les rôles - READ-ONLY)
      {
        path: 'catalogue',
        element: <ProductsListPage />,
      },
      {
        path: 'catalogue/products/:id',
        element: <ProductDetailPage />,
      },
      
      // Catalogue - Suppliers (Tous les rôles - READ-ONLY)
      {
        path: 'catalogue/suppliers',
        element: <SuppliersListPage />,
      },
      {
        path: 'catalogue/suppliers/:id',
        element: <SupplierDetailPage />,
      },
      
      // Ventes — redirect to opportunities list
      { path: 'ventes', element: <Navigate to="/app/ventes/opportunities" replace /> },
      
      // Opportunities
      {
        path: 'ventes/opportunities',
        element: (
          <ProtectedRoute allowedRoles={['COMMERCIAL', 'FINANCE', 'ADMIN']}>
            <OpportunitiesListPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'ventes/opportunities/new',
        element: (
          <ProtectedRoute allowedRoles={['COMMERCIAL', 'ADMIN']}>
            <CreateOpportunityPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'ventes/opportunities/:id',
        element: (
          <ProtectedRoute allowedRoles={['COMMERCIAL', 'FINANCE', 'ADMIN']}>
            <OpportunityDetailPage />
          </ProtectedRoute>
        ),
      },

      // Provisions
      {
        path: 'ventes/provisions',
        element: (
          <ProtectedRoute allowedRoles={['TECHNICIEN', 'ADMIN']}>
            <ProvisionsListPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'ventes/provisions/:id',
        element: (
          <ProtectedRoute allowedRoles={['COMMERCIAL', 'FINANCE', 'TECHNICIEN', 'ADMIN']}>
            <ProvisionDetailPage />
          </ProtectedRoute>
        ),
      },

      // Subscriptions
      {
        path: 'ventes/subscriptions',
        element: <SubscriptionsListPage />,
      },
      {
        path: 'ventes/subscriptions/:id',
        element: <SubscriptionDetailPage />,
      },
      
      // Notifications
      { path: 'notifications', element: <NotificationsPage /> },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/app" replace />,
  },
]);