/**
 * OPPORTUNITY LINES HOOKS
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import { linesApi } from '../api/linesApi';
import { opportunitiesKeys } from './useOpportunities';

export const linesKeys = {
  all:    ['lines'],
  lists:  ()       => [...linesKeys.all, 'list'],
  list:   (params) => [...linesKeys.lists(), params],
  detail: (id)     => [...linesKeys.all, 'detail', id],
};

export function useOpportunityLines(opportunityId, options = {}) {
  return useQuery({
    queryKey: linesKeys.list({ opportunity: opportunityId }),
    queryFn: async () => {
      const { data } = await linesApi.getAll(opportunityId);
      return data;
    },
    enabled: !!opportunityId,
    staleTime: 15000,
    ...options,
  });
}

export function useAddLine(opportunityId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => linesApi.create(opportunityId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.detail(opportunityId) });
      toast.success('Ligne ajoutée');
    },
    onError: (error) => {
      const d = error.response?.data;
      const message =
        d?.detail ||
        d?.product?.[0] ||
        Object.values(d || {})?.[0]?.[0] ||
        "Erreur lors de l'ajout";
      toast.error(message);
    },
  });
}

export function useUpdateLine(opportunityId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => linesApi.update(opportunityId, id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.detail(opportunityId) });
      toast.success('Ligne mise à jour');
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la mise à jour';
      toast.error(message);
    },
  });
}

export function useDeleteLine(opportunityId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => linesApi.delete(opportunityId, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.detail(opportunityId) });
      toast.success('Ligne supprimée');
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la suppression';
      toast.error(message);
    },
  });
}

export function useCancelLine(opportunityId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reason }) => linesApi.cancel(opportunityId, id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.detail(opportunityId) });
      toast.success('Ligne annulée');
    },
    onError: (error) => {
      const message = error.response?.data?.detail || "Erreur lors de l'annulation";
      toast.error(message);
    },
  });
}

export function useConfirmLinePO(opportunityId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (lineId) => linesApi.confirmPO(opportunityId, lineId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.detail(opportunityId) });
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la confirmation';
      toast.error(message);
    },
  });
}
