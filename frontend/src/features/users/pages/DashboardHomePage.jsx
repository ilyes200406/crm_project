
/**
 * DASHBOARD HOME PAGE
 * 
 * Router principal - redirige vers le bon dashboard selon le rôle
 */

import React from 'react';
import { useAuth } from '../../auth/hooks/useAuth';
import {
  CommercialDashboard,
  FinanceDashboard,
  TechDashboard,
} from '../../ventes/pages';

export function DashboardHomePage() {
  const { user } = useAuth();

  // Router selon le rôle
  switch (user?.role) {
    case 'COMMERCIAL':
      return <CommercialDashboard />;

    case 'FINANCE':
      return <FinanceDashboard />;

    case 'TECHNICIEN':
      return <TechDashboard />;

    case 'ADMIN':
      // Admin peut voir le dashboard commercial par défaut
      return <CommercialDashboard />;

    default:
      // Fallback si rôle inconnu
      return (
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Rôle inconnu
            </h1>
            <p className="text-gray-600">
              Votre rôle ({user?.role || 'non défini'}) n'est pas reconnu.
            </p>
            <p className="text-sm text-gray-500 mt-4">
              Contactez l'administrateur.
            </p>
          </div>
        </div>
      );
  }
}