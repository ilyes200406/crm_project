import React from 'react';
import { ClipboardList, Users, Package, Wrench, Search, Bell, User } from 'lucide-react';

/**
 * @param {React.ComponentType} Icon - Lucide icon component
 * @param {string} title
 * @param {string} message
 * @param {{ label: string, onClick: Function }} [action]
 */
export function EmptyState({ Icon, title, message, action }) {
  return (
    <div className="text-center py-12 px-4">
      {Icon && (
        <div className="flex justify-center mb-4">
          <Icon size={48} className="text-gray-300" />
        </div>
      )}
      {title && <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>}
      <p className="text-gray-500 text-sm mb-6 max-w-md mx-auto">{message}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}

export const EmptyStates = {
  NoOpportunities: () => (
    <EmptyState
      Icon={ClipboardList}
      title="Aucune opportunité"
      message="Créez votre première opportunité pour commencer à gérer vos ventes."
    />
  ),

  NoClients: () => (
    <EmptyState
      Icon={Users}
      title="Aucun client"
      message="Ajoutez vos clients pour commencer à créer des opportunités."
    />
  ),

  NoSubscriptions: () => (
    <EmptyState
      Icon={Package}
      title="Aucune subscription"
      message="Les subscriptions apparaîtront ici une fois les provisions complétées."
    />
  ),

  NoProvisions: () => (
    <EmptyState
      Icon={Wrench}
      title="Aucune provision"
      message="Les provisions en attente apparaîtront ici."
    />
  ),

  NoResults: () => (
    <EmptyState
      Icon={Search}
      title="Aucun résultat"
      message="Essayez de modifier vos filtres de recherche."
    />
  ),

  NoNotifications: () => (
    <EmptyState
      Icon={Bell}
      title="Aucune notification"
      message="Vous êtes à jour ! Aucune nouvelle notification."
    />
  ),
};
