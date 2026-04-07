/**
 * BADGE COMPONENT
 * 
 * Badge de statut avec couleurs configurables
 */

import React from 'react';

/**
 * Badge Component
 * 
 * @param {Object} props
 * @param {string} props.children - Badge text
 * @param {string} props.variant - Color variant: 'red', 'orange', 'yellow', 'green', 'blue', 'gray', 'purple'
 * @param {string} props.size - Size: 'sm', 'md', 'lg' (default: 'md')
 * @param {string} props.icon - Emoji icon (optional)
 */
export function Badge({ children, variant = 'gray', size = 'md', icon }) {
  const variants = {
    red: 'bg-red-100 text-red-800 border-red-200',
    orange: 'bg-orange-100 text-orange-800 border-orange-200',
    yellow: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    green: 'bg-green-100 text-green-800 border-green-200',
    blue: 'bg-blue-100 text-blue-800 border-blue-200',
    gray: 'bg-gray-100 text-gray-800 border-gray-200',
    purple: 'bg-purple-100 text-purple-800 border-purple-200',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  return (
    <span
      className={`
        inline-flex items-center gap-1 font-semibold rounded-full border
        ${variants[variant]}
        ${sizes[size]}
      `}
    >
      {icon && <span>{icon}</span>}
      {children}
    </span>
  );
}

/**
 * Status Badge - Predefined status badges
 */
export function StatusBadge({ status }) {
  const statusConfig = {
    // Opportunity statuses
    DRAFT: { variant: 'gray', icon: '🔵', label: 'Brouillon' },
    SUPPLIER_QUOTE_REQUEST: { variant: 'yellow', icon: '📧', label: 'Devis demandé' },
    SUPPLIER_QUOTE_RECEIVED: { variant: 'green', icon: '✅', label: 'Devis reçu' },
    INSOMEA_QUOTE_CREATED: { variant: 'blue', icon: '📄', label: 'Devis créé' },
    CLIENT_PO_REQUEST: { variant: 'yellow', icon: '📧', label: 'BC demandé' },
    CLIENT_PO_RECIEVED: { variant: 'orange', icon: '⏳', label: 'BC reçu' },
    APPROUVED: { variant: 'green', icon: '✅', label: 'Approuvé' },
    INSOMEA_PO_SENT: { variant: 'blue', icon: '📧', label: 'PO envoyé' },
    INSOMEA_PO_CONFIRMED: { variant: 'green', icon: '✅', label: 'PO confirmé' },
    CANCELLED: { variant: 'red', icon: '❌', label: 'Annulé' },

    // Subscription statuses
    ACTIVE: { variant: 'green', icon: '🟢', label: 'Active' },
    PENDING_RENEWAL: { variant: 'yellow', icon: '🟡', label: 'En renouvellement' },
    EXPIRED: { variant: 'red', icon: '🔴', label: 'Expirée' },
    SUSPENDED: { variant: 'orange', icon: '⏸️', label: 'Suspendue' },

    // Provision statuses
    WAITING_PROVISION: { variant: 'yellow', icon: '⏳', label: 'En attente' },
    PROVISIONING: { variant: 'blue', icon: '🔄', label: 'En cours' },
    PROVISIONED: { variant: 'green', icon: '✅', label: 'Provisionné' },
    FAILED: { variant: 'red', icon: '❌', label: 'Échec' },
  };

  const config = statusConfig[status] || {
    variant: 'gray',
    label: status,
  };

  return (
    <Badge variant={config.variant} icon={config.icon}>
      {config.label}
    </Badge>
  );
}