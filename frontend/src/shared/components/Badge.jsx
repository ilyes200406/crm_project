import React from 'react';
import {
  Circle, Mail, CheckCircle2, FileText, Clock,
  XCircle, Pause, RefreshCw,
} from 'lucide-react';

/**
 * @param {string} variant - 'red' | 'orange' | 'yellow' | 'green' | 'blue' | 'gray' | 'purple'
 * @param {string} size - 'sm' | 'md' | 'lg'
 * @param {React.ReactNode} icon - optional icon element
 */
export function Badge({ children, variant = 'gray', size = 'md', icon }) {
  const variants = {
    red:    'bg-red-100 text-red-800 border-red-200',
    orange: 'bg-orange-100 text-orange-800 border-orange-200',
    yellow: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    green:  'bg-green-100 text-green-800 border-green-200',
    blue:   'bg-blue-100 text-blue-800 border-blue-200',
    gray:   'bg-gray-100 text-gray-800 border-gray-200',
    purple: 'bg-purple-100 text-purple-800 border-purple-200',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  return (
    <span className={`inline-flex items-center gap-1 font-semibold rounded-full border ${variants[variant]} ${sizes[size]}`}>
      {icon && <span className="flex items-center shrink-0">{icon}</span>}
      {children}
    </span>
  );
}

/**
 * Status Badge — maps domain status strings to a styled badge with icon.
 */
export function StatusBadge({ status }) {
  const dot = (cls) => <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cls}`} />;

  const statusConfig = {
    // Opportunity statuses
    DRAFT:                    { variant: 'gray',   icon: <Circle size={11} />,       label: 'Brouillon' },
    SUPPLIER_QUOTE_REQUEST:   { variant: 'yellow', icon: <Mail size={11} />,         label: 'Devis demandé' },
    SUPPLIER_QUOTE_RECEIVED:  { variant: 'green',  icon: <CheckCircle2 size={11} />, label: 'Devis reçu' },
    INSOMEA_QUOTE_CREATED:    { variant: 'blue',   icon: <FileText size={11} />,     label: 'Devis créé' },
    CLIENT_PO_REQUEST:        { variant: 'yellow', icon: <Mail size={11} />,         label: 'BC demandé' },
    CLIENT_PO_RECIEVED:       { variant: 'orange', icon: <Clock size={11} />,        label: 'BC reçu' },
    APPROUVED:                { variant: 'green',  icon: <CheckCircle2 size={11} />, label: 'Approuvé' },
    INSOMEA_PO_SENT:          { variant: 'blue',   icon: <Mail size={11} />,         label: 'PO envoyé' },
    INSOMEA_PO_CONFIRMED:     { variant: 'green',  icon: <CheckCircle2 size={11} />, label: 'PO confirmé' },
    CANCELLED:                { variant: 'red',    icon: <XCircle size={11} />,      label: 'Annulé' },

    // Subscription statuses — keep as colored dots
    ACTIVE:          { variant: 'green',  icon: dot('bg-green-500'),  label: 'Active' },
    PENDING_RENEWAL: { variant: 'yellow', icon: dot('bg-yellow-500'), label: 'En renouvellement' },
    EXPIRED:         { variant: 'red',    icon: dot('bg-red-500'),    label: 'Expirée' },
    SUSPENDED:       { variant: 'orange', icon: <Pause size={11} />,  label: 'Suspendue' },

    // Provision statuses
    WAITING_PROVISION: { variant: 'yellow', icon: <Clock size={11} />,        label: 'En attente' },
    PROVISIONING:      { variant: 'blue',   icon: <RefreshCw size={11} />,    label: 'En cours' },
    PROVISIONED:       { variant: 'green',  icon: <CheckCircle2 size={11} />, label: 'Provisionné' },
    FAILED:            { variant: 'red',    icon: <XCircle size={11} />,      label: 'Échec' },
  };

  const config = statusConfig[status] || { variant: 'gray', label: status };

  return (
    <Badge variant={config.variant} icon={config.icon}>
      {config.label}
    </Badge>
  );
}
