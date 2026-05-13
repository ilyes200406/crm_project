import React from 'react';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import {
  FileText, RefreshCw, Upload, CheckCircle2,
  AlertTriangle, XCircle, Wrench, Bell,
} from 'lucide-react';

import { Badge } from '../../../shared/components';
import { useMarkAsRead } from '../hooks';

export function NotificationItem({ notification, onClose }) {
  const navigate = useNavigate();
  const markAsReadMutation = useMarkAsRead();

  const config = getNotificationConfig(notification);

  const handleClick = async () => {
    if (!notification.is_read) {
      try {
        await markAsReadMutation.mutateAsync(notification.id);
      } catch (error) {
        // Error handled by mutation
      }
    }
    if (config.link) {
      navigate(config.link);
      onClose?.();
    }
  };

  const { Icon, iconBg, iconFg } = config;

  return (
    <div
      onClick={handleClick}
      className={`p-4 border-b border-gray-200 last:border-0 hover:bg-gray-50 cursor-pointer transition-colors ${
        !notification.is_read ? 'bg-blue-50' : 'bg-white'
      }`}
    >
      {/* Header: Icon + unread dot + time */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2.5">
          <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 ${iconBg}`}>
            <Icon size={16} className={iconFg} />
          </div>
          {!notification.is_read && (
            <div className="w-2 h-2 bg-blue-600 rounded-full shrink-0" />
          )}
        </div>
        <div className="text-xs text-gray-400">
          {formatDistanceToNow(new Date(notification.created_at), {
            addSuffix: true,
            locale: fr,
          })}
        </div>
      </div>

      {/* Title */}
      <div className="font-semibold text-gray-900 mb-1 text-sm">{notification.title}</div>

      {/* Message */}
      <div className="text-sm text-gray-600 mb-2">{notification.message}</div>

      {/* Level badge */}
      {notification.level && notification.level !== 'info' && (
        <Badge variant={getLevelVariant(notification.level)} size="sm">
          {getLevelLabel(notification.level)}
        </Badge>
      )}
    </div>
  );
}

function getNotificationConfig(notification) {
  const { notification_type, related_object_id } = notification;

  const configs = {
    'opportunity.created':            { Icon: FileText,     iconBg: 'bg-blue-50',   iconFg: 'text-blue-600',   link: `/app/ventes/opportunities/${related_object_id}` },
    'opportunity.status_changed':     { Icon: RefreshCw,    iconBg: 'bg-blue-50',   iconFg: 'text-blue-600',   link: `/app/ventes/opportunities/${related_object_id}` },
    'opportunity.client_po_uploaded': { Icon: Upload,       iconBg: 'bg-orange-50', iconFg: 'text-orange-600', link: `/app/ventes/opportunities/${related_object_id}` },
    'opportunity.approved':           { Icon: CheckCircle2, iconBg: 'bg-green-50',  iconFg: 'text-green-600',  link: `/app/ventes/opportunities/${related_object_id}` },
    'opportunity.po_confirmed':       { Icon: CheckCircle2, iconBg: 'bg-green-50',  iconFg: 'text-green-600',  link: `/app/ventes/opportunities/${related_object_id}` },
    'subscription.expiring_soon':     { Icon: AlertTriangle,iconBg: 'bg-amber-50',  iconFg: 'text-amber-600',  link: `/app/ventes/subscriptions/${related_object_id}` },
    'subscription.renewed':           { Icon: RefreshCw,    iconBg: 'bg-blue-50',   iconFg: 'text-blue-600',   link: `/app/ventes/subscriptions/${related_object_id}` },
    'subscription.cancelled':         { Icon: XCircle,      iconBg: 'bg-red-50',    iconFg: 'text-red-600',    link: `/app/ventes/subscriptions/${related_object_id}` },
    'provision.created':              { Icon: Wrench,       iconBg: 'bg-purple-50', iconFg: 'text-purple-600', link: `/app/ventes/provisions/${related_object_id}` },
    'provision.completed':            { Icon: CheckCircle2, iconBg: 'bg-green-50',  iconFg: 'text-green-600',  link: `/app/ventes/provisions/${related_object_id}` },
    'provision.failed':               { Icon: XCircle,      iconBg: 'bg-red-50',    iconFg: 'text-red-600',    link: `/app/ventes/provisions/${related_object_id}` },
    'finance.approval_required':      { Icon: AlertTriangle,iconBg: 'bg-amber-50',  iconFg: 'text-amber-600',  link: `/app/ventes/opportunities/${related_object_id}?tab=approval` },
    default:                          { Icon: Bell,         iconBg: 'bg-gray-100',  iconFg: 'text-gray-500',   link: null },
  };

  return configs[notification_type] || configs.default;
}

function getLevelVariant(level) {
  const variants = { success: 'green', warning: 'orange', error: 'red', info: 'blue' };
  return variants[level] || 'gray';
}

function getLevelLabel(level) {
  const labels = { success: 'Succès', warning: 'Attention', error: 'Erreur', info: 'Info' };
  return labels[level] || level;
}
