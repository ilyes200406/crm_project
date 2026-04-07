/**
 * CLIENTS HOOKS
 * 
 * React Query hooks pour clients
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import { clientsApi } from '../api/clientsApi';

// ═══════════════════════════════════════════════════════════
// QUERY KEYS
// ═══════════════════════════════════════════════════════════

export const clientsKeys = {
  all: ['clients'],
  lists: () => [...clientsKeys.all, 'list'],
  list: (params) => [...clientsKeys.lists(), params],
  details: () => [...clientsKeys.all, 'detail'],
  detail: (id) => [...clientsKeys.details(), id],
  opportunities: (id) => [...clientsKeys.detail(id), 'opportunities'],
  subscriptions: (id) => [...clientsKeys.detail(id), 'subscriptions'],
};

// ═══════════════════════════════════════════════════════════
// QUERIES
// ═══════════════════════════════════════════════════════════

/**
 * Get all clients
 * 
 * @param {Object} params - Query params
 * @param {Object} options - React Query options
 */
export function useClients(params = {}, options = {}) {
  return useQuery({
    queryKey: clientsKeys.list(params),
    queryFn: async () => {
      const { data } = await clientsApi.getAll(params);
      return data;
    },
    staleTime: 30000, // 30 seconds
    ...options,
  });
}

/**
 * Get client by ID
 * 
 * @param {string} id - Client UUID
 * @param {Object} options - React Query options
 */
export function useClient(id, options = {}) {
  return useQuery({
    queryKey: clientsKeys.detail(id),
    queryFn: async () => {
      const { data } = await clientsApi.getById(id);
      return data;
    },
    enabled: !!id,
    staleTime: 30000,
    ...options,
  });
}

/**
 * Get client opportunities
 * 
 * @param {string} id - Client UUID
 * @param {Object} params - Query params
 * @param {Object} options - React Query options
 */
export function useClientOpportunities(id, params = {}, options = {}) {
  return useQuery({
    queryKey: clientsKeys.opportunities(id),
    queryFn: async () => {
      const { data } = await clientsApi.getOpportunities(id, params);
      return data;
    },
    enabled: !!id,
    staleTime: 30000,
    ...options,
  });
}

/**
 * Get client subscriptions
 * 
 * @param {string} id - Client UUID
 * @param {Object} params - Query params
 * @param {Object} options - React Query options
 */
export function useClientSubscriptions(id, params = {}, options = {}) {
  return useQuery({
    queryKey: clientsKeys.subscriptions(id),
    queryFn: async () => {
      const { data } = await clientsApi.getSubscriptions(id, params);
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
 * Create client mutation
 */
export function useCreateClient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => clientsApi.create(data),
    onSuccess: ({ data }) => {
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: clientsKeys.lists() });

      toast.success('Client créé avec succès');
      return data;
    },
    onError: (error) => {
      const data = error.response?.data;
      let message = 'Erreur lors de la création';
      if (data) {
        if (data.detail) {
          message = data.detail;
        } else {
          const fieldErrors = Object.entries(data)
            .map(([field, errs]) => `${field}: ${[].concat(errs).join(', ')}`)
            .join(' | ');
          if (fieldErrors) message = fieldErrors;
        }
      }
      toast.error(message);
    },
  });
}

/**
 * Update client mutation
 */
export function useUpdateClient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => clientsApi.update(id, data),
    onSuccess: ({ data }) => {
      // Invalidate detail and lists
      queryClient.invalidateQueries({ queryKey: clientsKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: clientsKeys.lists() });

      toast.success('Client mis à jour');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la mise à jour';
      toast.error(message);
    },
  });
}

/**
 * Delete client mutation
 */
export function useDeleteClient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => clientsApi.delete(id),
    onSuccess: (_, id) => {
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: clientsKeys.lists() });
      // Remove detail from cache
      queryClient.removeQueries({ queryKey: clientsKeys.detail(id) });

      toast.success('Client supprimé');
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la suppression';
      
      // Check if it's a constraint error
      if (error.response?.status === 400 && message.includes('related')) {
        toast.error('Impossible de supprimer ce client car il a des opportunités ou subscriptions associées');
      } else {
        toast.error(message);
      }
    },
  });
}