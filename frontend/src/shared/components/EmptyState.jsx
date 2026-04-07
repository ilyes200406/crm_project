/**
 * EMPTY STATE COMPONENT
 * 
 * État vide avec message et action
 */

import React from 'react';

/**
 * EmptyState Component
 * 
 * @param {Object} props
 * @param {string} props.icon - Emoji icon
 * @param {string} props.title - Title
 * @param {string} props.message - Message
 * @param {Object} props.action - Action button config (optional)
 * @param {string} props.action.label - Button label
 * @param {Function} props.action.onClick - Button click handler
 */
export function EmptyState({ icon, title, message, action }) {
  return (
    <div className="text-center py-12">
      {/* Icon */}
      {icon && <div className="text-6xl mb-4">{icon}</div>}

      {/* Title */}
      {title && <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>}

      {/* Message */}
      <p className="text-gray-500 text-sm mb-6 max-w-md mx-auto">{message}</p>

      {/* Action */}
      {action && (
        <button
          onClick={action.onClick}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}

/**
 * Predefined empty states
 */
export const EmptyStates = {
  NoOpportunities: () => (
    <EmptyState
      icon="📋"
      title="Aucune opportunité"
      message="Créez votre première opportunité pour commencer à gérer vos ventes."
    />
  ),

  NoClients: () => (
    <EmptyState
      icon="👥"
      title="Aucun client"
      message="Ajoutez vos clients pour commencer à créer des opportunités."
    />
  ),

  NoSubscriptions: () => (
    <EmptyState
      icon="📦"
      title="Aucune subscription"
      message="Les subscriptions apparaîtront ici une fois les provisions complétées."
    />
  ),

  NoProvisions: () => (
    <EmptyState
      icon="🔧"
      title="Aucune provision"
      message="Les provisions en attente apparaîtront ici."
    />
  ),

  NoResults: () => (
    <EmptyState
      icon="🔍"
      title="Aucun résultat"
      message="Essayez de modifier vos filtres de recherche."
    />
  ),

  NoNotifications: () => (
    <EmptyState
      icon="🔔"
      title="Aucune notification"
      message="Vous êtes à jour ! Aucune nouvelle notification."
    />
  ),
};