/**
 * CONTACTS HOOKS
 * 
 * React Query hooks pour contacts
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import { contactsApi } from '../api/contactsApi';
import { clientsKeys } from './useClients';

// ═══════════════════════════════════════════════════════════
// QUERY KEYS
// ═══════════════════════════════════════════════════════════

export const contactsKeys = {
  all: ['contacts'],
  lists: () => [...contactsKeys.all, 'list'],
  list: (clientId) => [...contactsKeys.lists(), clientId],
  details: () => [...contactsKeys.all, 'detail'],
  detail: (id) => [...contactsKeys.details(), id],
};

// ═══════════════════════════════════════════════════════════
// QUERIES
// ═══════════════════════════════════════════════════════════

/**
 * Get contacts for a client
 * 
 * @param {string} clientId - Client UUID
 * @param {Object} params - Query params
 * @param {Object} options - React Query options
 */
export function useContacts(clientId, params = {}, options = {}) {
  return useQuery({
    queryKey: contactsKeys.list(clientId),
    queryFn: async () => {
      const { data } = await contactsApi.getByClient(clientId, params);
      return data;
    },
    enabled: !!clientId,
    staleTime: 30000, // 30 seconds
    ...options,
  });
}

/**
 * Get contact by ID
 * 
 * @param {string} id - Contact UUID
 * @param {Object} options - React Query options
 */
export function useContact(id, options = {}) {
  return useQuery({
    queryKey: contactsKeys.detail(id),
    queryFn: async () => {
      const { data } = await contactsApi.getById(id);
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
 * Create contact mutation
 */
export function useCreateContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ clientId, data }) => contactsApi.create(clientId, data),
    onSuccess: ({ data }) => {
      // Invalidate client detail (to refresh contacts list)
      queryClient.invalidateQueries({ 
        queryKey: clientsKeys.detail(data.client) 
      });
      
      // Invalidate contacts list
      queryClient.invalidateQueries({ 
        queryKey: contactsKeys.list(data.client) 
      });

      toast.success('Contact créé avec succès');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la création';
      toast.error(message);
    },
  });
}

/**
 * Update contact mutation
 */
export function useUpdateContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => contactsApi.update(id, data),
    onSuccess: ({ data }) => {
      // Invalidate detail
      queryClient.invalidateQueries({ queryKey: contactsKeys.detail(data.id) });
      
      // Invalidate client detail
      queryClient.invalidateQueries({ 
        queryKey: clientsKeys.detail(data.client) 
      });
      
      // Invalidate contacts list
      queryClient.invalidateQueries({ 
        queryKey: contactsKeys.list(data.client) 
      });

      toast.success('Contact mis à jour');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la mise à jour';
      toast.error(message);
    },
  });
}

/**
 * Delete contact mutation
 */
export function useDeleteContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, clientId }) => contactsApi.delete(id),
    onSuccess: (_, { id, clientId }) => {
      // Invalidate client detail
      queryClient.invalidateQueries({ 
        queryKey: clientsKeys.detail(clientId) 
      });
      
      // Invalidate contacts list
      queryClient.invalidateQueries({ 
        queryKey: contactsKeys.list(clientId) 
      });
      
      // Remove from cache
      queryClient.removeQueries({ queryKey: contactsKeys.detail(id) });

      toast.success('Contact supprimé');
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la suppression';
      toast.error(message);
    },
  });
}