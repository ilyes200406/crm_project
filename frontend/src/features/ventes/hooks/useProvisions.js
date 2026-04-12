/**
 * PROVISIONS HOOKS
 * 
 * React Query hooks pour provisions
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import { provisionsApi } from '../api/provisionsApi';
import { opportunitiesKeys } from './useOpportunities';
import { subscriptionsKeys } from './useSubscriptions';

// ═══════════════════════════════════════════════════════════
// QUERY KEYS
// ═══════════════════════════════════════════════════════════

export const provisionsKeys = {
  all: ['provisions'],
  lists: () => [...provisionsKeys.all, 'list'],
  list: (params) => [...provisionsKeys.lists(), params],
  details: () => [...provisionsKeys.all, 'detail'],
  detail: (id) => [...provisionsKeys.details(), id],
};

// ═══════════════════════════════════════════════════════════
// QUERIES
// ═══════════════════════════════════════════════════════════

/**
 * Get all provisions
 * 
 * @param {Object} params - Query params
 * @param {Object} options - React Query options
 */
export function useProvisions(params = {}, options = {}) {
  return useQuery({
    queryKey: provisionsKeys.list(params),
    queryFn: async () => {
      const { data } = await provisionsApi.getAll(params);
      return data;
    },
    staleTime: 30000, // 30 seconds
    ...options,
  });
}

/**
 * Get provision by ID
 * 
 * @param {string} id - Provision UUID
 * @param {Object} options - React Query options
 */
export function useProvision(id, options = {}) {
  return useQuery({
    queryKey: provisionsKeys.detail(id),
    queryFn: async () => {
      const { data } = await provisionsApi.getById(id);
      return data;
    },
    enabled: !!id,
    staleTime: 30000,
    ...options,
  });
}

// ═══════════════════════════════════════════════════════════
// MUTATIONS
// ═══════════════════════════════════════════════════════════

/**
 * Start provisioning mutation
 */
export function useStartProvisioning() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => provisionsApi.start(id),
    onSuccess: ({ data }) => {
      // Invalidate provision
      queryClient.invalidateQueries({ queryKey: provisionsKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: provisionsKeys.lists() });

      toast.success('Provisioning démarré');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors du démarrage';
      toast.error(message);
    },
  });
}

/**
 * Complete provisioning mutation
 */
export function useCompleteProvisioning() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => provisionsApi.complete(id, data),
    onSuccess: ({ data }) => {
      // Invalidate provisions
      queryClient.invalidateQueries({ queryKey: provisionsKeys.detail(data.provision.id) });
      queryClient.invalidateQueries({ queryKey: provisionsKeys.lists() });

      // Invalidate subscriptions (new/updated)
      if (data.subscription) {
        queryClient.invalidateQueries({ queryKey: subscriptionsKeys.detail(data.subscription.id) });
        queryClient.invalidateQueries({ queryKey: subscriptionsKeys.lists() });
        queryClient.invalidateQueries({ queryKey: subscriptionsKeys.stats() });
      }

      // Invalidate opportunity
      const oppId = data.provision?.opportunity_line?.opportunity?.id;
      if (oppId) {
        queryClient.invalidateQueries({ queryKey: opportunitiesKeys.detail(oppId) });
        queryClient.invalidateQueries({ queryKey: opportunitiesKeys.lists() });
      }

      toast.success('Provisioning complété ✅');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la complétion';
      toast.error(message);
    },
  });
}

/**
 * Fail provisioning mutation
 */
export function useFailProvisioning() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, errorMessage }) => provisionsApi.fail(id, errorMessage),
    onSuccess: ({ data }) => {
      queryClient.invalidateQueries({ queryKey: provisionsKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: provisionsKeys.lists() });

      toast.error('Provisioning marqué en échec');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || "Erreur lors de l'échec";
      toast.error(message);
    },
  });
}

/**
 * Retry provisioning mutation (ERROR → PROVISIONING)
 */
export function useRetryProvisioning() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => provisionsApi.retry(id),
    onSuccess: ({ data }) => {
      queryClient.invalidateQueries({ queryKey: provisionsKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: provisionsKeys.lists() });

      toast.success('Provisioning relancé');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors du retry';
      toast.error(message);
    },
  });
}