/**
 * NOTIFICATIONS HOOKS
 * 
 * React hooks pour notifications avec WebSocket
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import { notificationsApi } from '../api/notificationsApi';
import { websocketService } from '../../../services/websocket';
import { useAppStore } from '../../../app/store'; // ← UTILISER VOTRE STORE

// ═══════════════════════════════════════════════════════════
// QUERY KEYS
// ═══════════════════════════════════════════════════════════

export const notificationsKeys = {
  all: ['notifications'],
  lists: () => [...notificationsKeys.all, 'list'],
  list: (params) => [...notificationsKeys.lists(), params],
  details: () => [...notificationsKeys.all, 'detail'],
  detail: (id) => [...notificationsKeys.details(), id],
  unreadCount: () => [...notificationsKeys.all, 'unread-count'],
};

// ═══════════════════════════════════════════════════════════
// WEBSOCKET HOOK
// ═══════════════════════════════════════════════════════════

/**
 * Use WebSocket notifications
 * 
 * Manages WebSocket connection and real-time notifications
 */
export function useWebSocketNotifications() {
  const accessToken = useAppStore((state) => state.accessToken);
  const [isConnected, setIsConnected] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [latestNotification, setLatestNotification] = useState(null);

  useEffect(() => {
    if (!accessToken) return;

    websocketService.connect(accessToken);

    const unsubConnected = websocketService.on('connected', () => {
      setIsConnected(true);
    });

    const unsubDisconnected = websocketService.on('disconnected', () => {
      setIsConnected(false);
    });

    // Count events from backend (on connect, on mark-read, on heartbeat)
    // This is the single source of truth for the bell badge
    const unsubCount = websocketService.on('count', (data) => {
      setUnreadCount(data.count ?? 0);
    });

    // New notification events — update state + toast, no REST refetch
    const unsubMessage = websocketService.on('message', (data) => {
      if (data.notification) {
        setLatestNotification(data.notification);
        setUnreadCount((prev) => prev + 1);
        showNotificationToast(data.notification);
      }
    });

    return () => {
      unsubConnected();
      unsubDisconnected();
      unsubCount();
      unsubMessage();
      websocketService.disconnect();
    };
  }, [accessToken]);

  return { isConnected, unreadCount, latestNotification };
}

/**
 * Show toast notification
 */
function showNotificationToast(notification) {
  const { title, message, level } = notification;

  const toastConfig = {
    duration: 4000,
    position: 'top-right',
  };

  switch (level) {
    case 'success':
      toast.success(`${title}\n${message}`, toastConfig);
      break;
    case 'warning':
      toast(`${title}\n${message}`, toastConfig);
      break;
    case 'error':
      toast.error(`${title}\n${message}`, toastConfig);
      break;
    default:
      toast(`${title}\n${message}`, toastConfig);
  }
}

// ═══════════════════════════════════════════════════════════
// QUERIES
// ═══════════════════════════════════════════════════════════

/**
 * Get all notifications
 * 
 * @param {Object} params - Query params
 * @param {Object} options - React Query options
 */
export function useNotifications(params = {}, options = {}) {
  return useQuery({
    queryKey: notificationsKeys.list(params),
    queryFn: async () => {
      const { data } = await notificationsApi.getAll(params);
      return data;
    },
    staleTime: 10000, // 10 seconds (fresh from WebSocket updates)
    ...options,
  });
}

/**
 * Get notification by ID
 * 
 * @param {string} id - Notification UUID
 * @param {Object} options - React Query options
 */
export function useNotification(id, options = {}) {
  return useQuery({
    queryKey: notificationsKeys.detail(id),
    queryFn: async () => {
      const { data } = await notificationsApi.getById(id);
      return data;
    },
    enabled: !!id,
    staleTime: 30000,
    ...options,
  });
}

/**
 * Get unread count
 * 
 * @param {Object} options - React Query options
 */
export function useUnreadCount(options = {}) {
  return useQuery({
    queryKey: notificationsKeys.unreadCount(),
    queryFn: async () => {
      const { data } = await notificationsApi.getUnreadCount();
      return data;
    },
    staleTime: 10000,
    ...options,
  });
}

// ═══════════════════════════════════════════════════════════
// MUTATIONS
// ═══════════════════════════════════════════════════════════

/**
 * Mark notification as read mutation
 */
export function useMarkAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => notificationsApi.markAsRead(id),
    onSuccess: ({ data }) => {
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: notificationsKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: notificationsKeys.lists() });
      queryClient.invalidateQueries({ queryKey: notificationsKeys.unreadCount() });
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors du marquage';
      toast.error(message);
    },
  });
}

/**
 * Mark all as read mutation
 */
export function useMarkAllAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => notificationsApi.markAllAsRead(),
    onSuccess: () => {
      // Invalidate all notification queries
      queryClient.invalidateQueries({ queryKey: notificationsKeys.all });

      toast.success('Toutes les notifications marquées comme lues');
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors du marquage';
      toast.error(message);
    },
  });
}

/**
 * Delete notification mutation
 */
export function useDeleteNotification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => notificationsApi.delete(id),
    onSuccess: (_, id) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: notificationsKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: notificationsKeys.lists() });
      queryClient.invalidateQueries({ queryKey: notificationsKeys.unreadCount() });

      toast.success('Notification supprimée');
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la suppression';
      toast.error(message);
    },
  });
}