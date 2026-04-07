/**
 * NOTIFICATION ITEM COMPONENT
 * 
 * Item de notification individuel
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

import { Badge } from '../../../shared/components';
import { useMarkAsRead } from '../hooks';

/**
 * NotificationItem Component
 * 
 * @param {Object} props
 * @param {Object} props.notification - Notification object
 * @param {Function} props.onClose - Close dropdown callback
 */
export function NotificationItem({ notification, onClose }) {
  const navigate = useNavigate();
  const markAsReadMutation = useMarkAsRead();

  // Get notification config
  const config = getNotificationConfig(notification);

  // Handle click
  const handleClick = async () => {
    // Mark as read if unread
    if (!notification.is_read) {
      try {
        await markAsReadMutation.mutateAsync(notification.id);
      } catch (error) {
        // Error handled by mutation
      }
    }

    // Navigate to related resource
    if (config.link) {
      navigate(config.link);
      onClose?.();
    }
  };

  return (
    <div
      onClick={handleClick}
      className={`
        p-4 border-b border-gray-200 last:border-0
        hover:bg-gray-50 cursor-pointer transition-colors
        ${!notification.is_read ? 'bg-blue-50' : 'bg-white'}
      `}
    >
      {/* Header: Icon + Badge + Time */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="text-2xl">{config.icon}</div>
          {!notification.is_read && (
            <div className="w-2 h-2 bg-blue-600 rounded-full" />
          )}
        </div>
        <div className="text-xs text-gray-500">
          {formatDistanceToNow(new Date(notification.created_at), {
            addSuffix: true,
            locale: fr,
          })}
        </div>
      </div>

      {/* Title */}
      <div className="font-semibold text-gray-900 mb-1">
        {notification.title}
      </div>

      {/* Message */}
      <div className="text-sm text-gray-600 mb-2">
        {notification.message}
      </div>

      {/* Level badge */}
      {notification.level && notification.level !== 'info' && (
        <Badge variant={getLevelVariant(notification.level)} size="sm">
          {getLevelLabel(notification.level)}
        </Badge>
      )}
    </div>
  );
}

/**
 * Get notification configuration (icon, link)
 */
function getNotificationConfig(notification) {
  const { notification_type, related_object_id } = notification;

  const configs = {
    // Opportunities
    'opportunity.created': {
      icon: '📝',
      link: `/ventes/opportunities/${related_object_id}`,
    },
    'opportunity.status_changed': {
      icon: '🔄',
      link: `/ventes/opportunities/${related_object_id}`,
    },
    'opportunity.client_po_uploaded': {
      icon: '📄',
      link: `/ventes/opportunities/${related_object_id}`,
    },
    'opportunity.approved': {
      icon: '✅',
      link: `/ventes/opportunities/${related_object_id}`,
    },
    'opportunity.po_confirmed': {
      icon: '✅',
      link: `/ventes/opportunities/${related_object_id}`,
    },

    // Subscriptions
    'subscription.expiring_soon': {
      icon: '⚠️',
      link: `/ventes/subscriptions/${related_object_id}`,
    },
    'subscription.renewed': {
      icon: '🔄',
      link: `/ventes/subscriptions/${related_object_id}`,
    },
    'subscription.cancelled': {
      icon: '❌',
      link: `/ventes/subscriptions/${related_object_id}`,
    },

    // Provisions
    'provision.created': {
      icon: '🔧',
      link: `/provisions/${related_object_id}`,
    },
    'provision.completed': {
      icon: '✅',
      link: `/provisions/${related_object_id}`,
    },
    'provision.failed': {
      icon: '❌',
      link: `/provisions/${related_object_id}`,
    },

    // Finance
    'finance.approval_required': {
      icon: '⚠️',
      link: `/ventes/opportunities/${related_object_id}?tab=approval`,
    },

    // Default
    default: {
      icon: '🔔',
      link: null,
    },
  };

  return configs[notification_type] || configs.default;
}

/**
 * Get level badge variant
 */
function getLevelVariant(level) {
  const variants = {
    success: 'green',
    warning: 'orange',
    error: 'red',
    info: 'blue',
  };
  return variants[level] || 'gray';
}

/**
 * Get level label
 */
function getLevelLabel(level) {
  const labels = {
    success: 'Succès',
    warning: 'Attention',
    error: 'Erreur',
    info: 'Info',
  };
  return labels[level] || level;
}