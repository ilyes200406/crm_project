/*
import { createBrowserRouter, Navigate } from 'react-router-dom';

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
import { FeaturePlaceholderPage } from '../shared/components/FeaturePlaceholderPage';

// Import Clients pages
import {
  ClientsListPage,
  ClientDetailPage,
  CreateClientPage,
  EditClientPage,
} from '../features/clients/pages';

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
      
      // Clients (COMMERCIAL, ADMIN)
      {
        path: 'clients',
        element: (
          <ProtectedRoute allowedRoles={['COMMERCIAL', 'ADMIN']}>
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
          <ProtectedRoute allowedRoles={['COMMERCIAL', 'ADMIN']}>
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
      
      // Catalogue, Ventes (placeholders)
      { path: 'catalogue', element: <FeaturePlaceholderPage featureName="Catalogue" /> },
      { path: 'ventes', element: <FeaturePlaceholderPage featureName="Ventes" /> },
      
      // Notifications
      { path: 'notifications', element: <NotificationsPage /> },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/app" replace />,
  },
]);
*/
import { createBrowserRouter, Navigate } from 'react-router-dom';

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
import { FeaturePlaceholderPage } from '../shared/components/FeaturePlaceholderPage';

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
      
      // Clients (COMMERCIAL, ADMIN)
      {
        path: 'clients',
        element: (
          <ProtectedRoute allowedRoles={['COMMERCIAL', 'ADMIN']}>
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
          <ProtectedRoute allowedRoles={['COMMERCIAL', 'ADMIN']}>
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
      
      // Ventes (placeholder)
      { path: 'ventes', element: <FeaturePlaceholderPage featureName="Ventes" /> },
      
      // Notifications
      { path: 'notifications', element: <NotificationsPage /> },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/app" replace />,
  },
]);