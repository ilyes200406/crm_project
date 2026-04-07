/**
 * SUBSCRIPTIONS HOOKS
 * 
 * React Query hooks pour subscriptions
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import { subscriptionsApi } from '../api/subscriptionsApi';
import { opportunitiesKeys } from './useOpportunities';

// ═══════════════════════════════════════════════════════════
// QUERY KEYS
// ═══════════════════════════════════════════════════════════

export const subscriptionsKeys = {
  all: ['subscriptions'],
  lists: () => [...subscriptionsKeys.all, 'list'],
  list: (params) => [...subscriptionsKeys.lists(), params],
  details: () => [...subscriptionsKeys.all, 'detail'],
  detail: (id) => [...subscriptionsKeys.details(), id],
  stats: () => [...subscriptionsKeys.all, 'stats'],
  active: (params) => [...subscriptionsKeys.all, 'active', params],
  expiring: (days, params) => [...subscriptionsKeys.all, 'expiring', days, params],
  pendingRenewal: (params) => [...subscriptionsKeys.all, 'pending-renewal', params],
  renewalData: (id) => [...subscriptionsKeys.all, 'renewal-data', id],
};

// ═══════════════════════════════════════════════════════════
// QUERIES
// ═══════════════════════════════════════════════════════════

/**
 * Get all subscriptions
 * 
 * @param {Object} params - Query params
 * @param {Object} options - React Query options
 */
export function useSubscriptions(params = {}, options = {}) {
  return useQuery({
    queryKey: subscriptionsKeys.list(params),
    queryFn: async () => {
      const { data } = await subscriptionsApi.getAll(params);
      return data;
    },
    staleTime: 30000, // 30 seconds
    ...options,
  });
}

/**
 * Get subscription by ID
 * 
 * @param {string} id - Subscription UUID
 * @param {Object} options - React Query options
 */
export function useSubscription(id, options = {}) {
  return useQuery({
    queryKey: subscriptionsKeys.detail(id),
    queryFn: async () => {
      const { data } = await subscriptionsApi.getById(id);
      return data;
    },
    enabled: !!id,
    staleTime: 30000,
    ...options,
  });
}

/**
 * Get subscriptions stats
 * 
 * @param {Object} options - React Query options
 */
export function useSubscriptionsStats(options = {}) {
  return useQuery({
    queryKey: subscriptionsKeys.stats(),
    queryFn: async () => {
      const { data } = await subscriptionsApi.getStats();
      return data;
    },
    staleTime: 60000, // 1 minute
    ...options,
  });
}

/**
 * Get active subscriptions
 * 
 * @param {Object} params - Query params
 * @param {Object} options - React Query options
 */
export function useActiveSubscriptions(params = {}, options = {}) {
  return useQuery({
    queryKey: subscriptionsKeys.active(params),
    queryFn: async () => {
      const { data } = await subscriptionsApi.getActive(params);
      return data;
    },
    staleTime: 30000,
    ...options,
  });
}

/**
 * Get expiring subscriptions
 * 
 * @param {number} days - Days until expiration
 * @param {Object} params - Query params
 * @param {Object} options - React Query options
 */
export function useExpiringSubscriptions(days = 30, params = {}, options = {}) {
  return useQuery({
    queryKey: subscriptionsKeys.expiring(days, params),
    queryFn: async () => {
      const { data } = await subscriptionsApi.getExpiring(days, params);
      return data;
    },
    staleTime: 30000,
    refetchInterval: 60000, // Refetch every minute for expiring subs
    ...options,
  });
}

/**
 * Get pending renewal subscriptions
 * 
 * @param {Object} params - Query params
 * @param {Object} options - React Query options
 */
export function usePendingRenewalSubscriptions(params = {}, options = {}) {
  return useQuery({
    queryKey: subscriptionsKeys.pendingRenewal(params),
    queryFn: async () => {
      const { data } = await subscriptionsApi.getPendingRenewal(params);
      return data;
    },
    staleTime: 30000,
    ...options,
  });
}

/**
 * Get renewal data for subscription
 * 
 * @param {string} id - Subscription UUID
 * @param {Object} options - React Query options
 */
export function useRenewalData(id, options = {}) {
  return useQuery({
    queryKey: subscriptionsKeys.renewalData(id),
    queryFn: async () => {
      const { data } = await subscriptionsApi.getRenewalData(id);
      return data;
    },
    enabled: !!id,
    staleTime: 300000, // 5 minutes (doesn't change often)
    ...options,
  });
}

// ═══════════════════════════════════════════════════════════
// MUTATIONS
// ═══════════════════════════════════════════════════════════

/**
 * Update subscription mutation
 */
export function useUpdateSubscription() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => subscriptionsApi.update(id, data),
    onSuccess: ({ data }) => {
      // Invalidate detail and lists
      queryClient.invalidateQueries({ queryKey: subscriptionsKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: subscriptionsKeys.lists() });

      toast.success('Subscription mise à jour');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la mise à jour';
      toast.error(message);
    },
  });
}

/**
 * Create renewal opportunity mutation
 */
export function useCreateRenewal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => subscriptionsApi.createRenewal(id, data),
    onSuccess: ({ data }) => {
      // Invalidate subscriptions
      queryClient.invalidateQueries({ queryKey: subscriptionsKeys.detail(data.opportunity.id) });
      queryClient.invalidateQueries({ queryKey: subscriptionsKeys.lists() });

      // Invalidate opportunities (new one created)
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.lists() });
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.renewals({}) });

      toast.success('Opportunité renewal créée');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la création';
      toast.error(message);
    },
  });
}

/**
 * Cancel subscription mutation
 */
export function useCancelSubscription() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reason }) => subscriptionsApi.cancel(id, reason),
    onSuccess: ({ data }) => {
      queryClient.invalidateQueries({ queryKey: subscriptionsKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: subscriptionsKeys.lists() });
      queryClient.invalidateQueries({ queryKey: subscriptionsKeys.stats() });

      toast.success('Subscription annulée');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || "Erreur lors de l'annulation";
      toast.error(message);
    },
  });
}