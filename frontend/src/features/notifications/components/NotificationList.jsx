/**
 * NOTIFICATION LIST COMPONENT
 * 
 * Liste déroulante des notifications
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, ChevronRight } from 'lucide-react';

import { NotificationItem } from './NotificationItem';
import { useNotifications, useMarkAllAsRead } from '../hooks';

/**
 * NotificationList Component
 * 
 * @param {Object} props
 * @param {Function} props.onClose - Close dropdown callback
 */
export function NotificationList({ onClose }) {
  const navigate = useNavigate();

  // Fetch notifications (last 10)
  const { data, isLoading } = useNotifications({ limit: 10 });

  // Mark all as read mutation
  const markAllAsReadMutation = useMarkAllAsRead();

  // Handle mark all as read
  const handleMarkAllAsRead = async () => {
    try {
      await markAllAsReadMutation.mutateAsync();
    } catch (error) {
      // Error handled by mutation
    }
  };

  // Handle view all
  const handleViewAll = () => {
    navigate('/notifications');
    onClose?.();
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="w-96 max-h-96 overflow-y-auto bg-white rounded-lg shadow-lg border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <div className="h-6 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="divide-y divide-gray-200">
          {[...Array(3)].map((_, idx) => (
            <div key={idx} className="p-4">
              <div className="h-4 bg-gray-200 rounded mb-2 animate-pulse" />
              <div className="h-3 bg-gray-200 rounded w-3/4 animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Empty state
  if (!data?.results || data.results.length === 0) {
    return (
      <div className="w-96 bg-white rounded-lg shadow-lg border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900">Notifications</h3>
        </div>
        <div className="p-8 text-center">
          <div className="flex justify-center mb-4"><Bell size={48} className="text-gray-300" /></div>
          <p className="text-gray-500 text-sm">
            Aucune notification
          </p>
          <p className="text-gray-400 text-xs mt-1">
            Vous êtes à jour !
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-96 max-h-96 bg-white rounded-lg shadow-lg border border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">
          Notifications ({data.count || 0})
        </h3>
        {data.results.some(n => !n.is_read) && (
          <button
            onClick={handleMarkAllAsRead}
            disabled={markAllAsReadMutation.isPending}
            className="text-xs text-blue-600 hover:text-blue-800 font-medium disabled:opacity-50"
          >
            Tout marquer lu
          </button>
        )}
      </div>

      {/* Notifications list */}
      <div className="max-h-80 overflow-y-auto">
        {data.results.map((notification) => (
          <NotificationItem
            key={notification.id}
            notification={notification}
            onClose={onClose}
          />
        ))}
      </div>

      {/* Footer */}
      {data.count > 10 && (
        <div className="p-3 border-t border-gray-200 bg-gray-50">
          <button
            onClick={handleViewAll}
            className="w-full text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Voir tout ({data.count}) →
          </button>
        </div>
      )}
    </div>
  );
}