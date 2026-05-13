/**
 * NOTIFICATIONS PAGE
 * 
 * Page complète listant toutes les notifications
 */

import React, { useState } from 'react';
import { Bell, CheckCheck } from 'lucide-react';

import { Card, Badge } from '../../../shared/components';
import { NotificationItem } from '../components';
import { useNotifications, useMarkAllAsRead } from '../hooks';

export function NotificationsPage() {
  const [filter, setFilter] = useState('all'); // 'all', 'unread'

  // Fetch notifications
  const params = filter === 'unread' ? { unread_only: true } : {};
  const { data, isLoading } = useNotifications(params);

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

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center">
            <Bell size={18} className="text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Toutes vos notifications en temps réel
            </p>
          </div>
        </div>

        <button
          onClick={handleMarkAllAsRead}
          disabled={markAllAsReadMutation.isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
        >
          Tout marquer lu
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`
            px-4 py-2 rounded-lg text-sm font-medium transition-colors
            ${filter === 'all' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'}
          `}
        >
          Toutes ({data?.count || 0})
        </button>
        <button
          onClick={() => setFilter('unread')}
          className={`
            px-4 py-2 rounded-lg text-sm font-medium transition-colors
            ${filter === 'unread' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'}
          `}
        >
          Non lues
        </button>
      </div>

      {/* Notifications list */}
      <Card noPadding>
        {isLoading ? (
          <div className="divide-y divide-gray-200">
            {[...Array(5)].map((_, idx) => (
              <div key={idx} className="p-4">
                <div className="h-4 bg-gray-200 rounded mb-2 animate-pulse" />
                <div className="h-3 bg-gray-200 rounded w-3/4 animate-pulse" />
              </div>
            ))}
          </div>
        ) : !data?.results || data.results.length === 0 ? (
          <div className="p-12 text-center">
            <div className="flex justify-center mb-4"><Bell size={48} className="text-gray-300" /></div>
            <p className="text-gray-500 text-sm">
              {filter === 'unread' ? 'Aucune notification non lue' : 'Aucune notification'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {data.results.map((notification) => (
              <NotificationItem key={notification.id} notification={notification} />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}