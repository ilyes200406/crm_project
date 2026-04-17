/**
 * OPPORTUNITIES HOOKS
 * 
 * React Query hooks pour opportunités
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import { opportunitiesApi } from '../api/opportunitiesApi';

// ═══════════════════════════════════════════════════════════
// QUERY KEYS
// ═══════════════════════════════════════════════════════════

export const opportunitiesKeys = {
  all: ['opportunities'],
  lists: () => [...opportunitiesKeys.all, 'list'],
  list: (params) => [...opportunitiesKeys.lists(), params],
  details: () => [...opportunitiesKeys.all, 'detail'],
  detail: (id) => [...opportunitiesKeys.details(), id],
  stats: () => [...opportunitiesKeys.all, 'stats'],
  pipeline: () => [...opportunitiesKeys.all, 'pipeline'],
  revenueChart: (months) => [...opportunitiesKeys.all, 'revenue-chart', months],
  renewals: (params) => [...opportunitiesKeys.all, 'renewals', params],
  initials: (params) => [...opportunitiesKeys.all, 'initials', params],
  upsells: (params) => [...opportunitiesKeys.all, 'upsells', params],
};

// ═══════════════════════════════════════════════════════════
// QUERIES
// ═══════════════════════════════════════════════════════════

/**
 * Get all opportunities
 * 
 * @param {Object} params - Query params
 * @param {Object} options - React Query options
 */
export function useOpportunities(params = {}, options = {}) {
  return useQuery({
    queryKey: opportunitiesKeys.list(params),
    queryFn: async () => {
      const { data } = await opportunitiesApi.getAll(params);
      return data;
    },
    staleTime: 30000, // 30 seconds
    ...options,
  });
}

/**
 * Get opportunity by ID
 * 
 * @param {string} id - Opportunity UUID
 * @param {Object} options - React Query options
 */
export function useOpportunity(id, options = {}) {
  return useQuery({
    queryKey: opportunitiesKeys.detail(id),
    queryFn: async () => {
      const { data } = await opportunitiesApi.getById(id);
      return data;
    },
    enabled: !!id,
    staleTime: 30000,
    ...options,
  });
}

/**
 * Get opportunities stats
 * 
 * @param {Object} options - React Query options
 */
export function useOpportunitiesStats(options = {}) {
  return useQuery({
    queryKey: opportunitiesKeys.stats(),
    queryFn: async () => {
      const { data } = await opportunitiesApi.getStats();
      return data;
    },
    staleTime: 60000, // 1 minute
    ...options,
  });
}

/**
 * Get opportunities pipeline
 * 
 * @param {Object} options - React Query options
 */
export function useOpportunitiesPipeline(options = {}) {
  return useQuery({
    queryKey: opportunitiesKeys.pipeline(),
    queryFn: async () => {
      const { data } = await opportunitiesApi.getPipeline();
      return data;
    },
    staleTime: 60000,
    ...options,
  });
}

/**
 * Get revenue chart data
 * 
 * @param {number} months - Number of months
 * @param {Object} options - React Query options
 */
export function useRevenueChart(months = 6, options = {}) {
  return useQuery({
    queryKey: opportunitiesKeys.revenueChart(months),
    queryFn: async () => {
      const { data } = await opportunitiesApi.getRevenueChart(months);
      return data;
    },
    staleTime: 300000, // 5 minutes
    ...options,
  });
}

/**
 * Get renewals opportunities
 * 
 * @param {Object} params - Query params
 * @param {Object} options - React Query options
 */
export function useRenewalsOpportunities(params = {}, options = {}) {
  return useQuery({
    queryKey: opportunitiesKeys.renewals(params),
    queryFn: async () => {
      const { data } = await opportunitiesApi.getRenewals(params);
      return data;
    },
    staleTime: 30000,
    ...options,
  });
}

/**
 * Get initial opportunities
 * 
 * @param {Object} params - Query params
 * @param {Object} options - React Query options
 */
export function useInitialsOpportunities(params = {}, options = {}) {
  return useQuery({
    queryKey: opportunitiesKeys.initials(params),
    queryFn: async () => {
      const { data } = await opportunitiesApi.getInitials(params);
      return data;
    },
    staleTime: 30000,
    ...options,
  });
}

// ═══════════════════════════════════════════════════════════
// MUTATIONS
// ═══════════════════════════════════════════════════════════

/**
 * Create opportunity mutation
 */
export function useCreateOpportunity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => opportunitiesApi.create(data),
    onSuccess: ({ data }) => {
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.lists() });
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.stats() });

      toast.success('Opportunité créée avec succès');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la création';
      toast.error(message);
    },
  });
}

/**
 * Update opportunity mutation
 */
export function useUpdateOpportunity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => opportunitiesApi.update(id, data),
    onSuccess: ({ data }) => {
      // Invalidate detail and lists
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.lists() });

      toast.success('Opportunité mise à jour');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la mise à jour';
      toast.error(message);
    },
  });
}

/**
 * Delete opportunity mutation
 */
export function useDeleteOpportunity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => opportunitiesApi.delete(id),
    onSuccess: (_, id) => {
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.lists() });
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.stats() });
      // Remove detail from cache
      queryClient.removeQueries({ queryKey: opportunitiesKeys.detail(id) });

      toast.success('Opportunité supprimée');
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la suppression';
      toast.error(message);
    },
  });
}

/**
 * Approve opportunity mutation (Finance)
 */
export function useApproveOpportunity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => opportunitiesApi.approve(id),
    onSuccess: ({ data }) => {
      // Invalidate all related queries
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.detail(data.opportunity.id) });
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.lists() });
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.stats() });
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.pipeline() });

      toast.success('Opportunité approuvée - BC fournisseurs envoyés');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || "Erreur lors de l'approbation";
      toast.error(message);
    },
  });
}

/**
 * Confirm all POs mutation
 */
export function useConfirmAllPOs() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => opportunitiesApi.confirmAllPOs(id),
    onSuccess: ({ data }) => {
      // Invalidate all related queries
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.detail(data.opportunity.id) });
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.lists() });
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.pipeline() });

      const message = data.provisions_created
        ? 'BC confirmés - Provisions créées ✅'
        : 'BC confirmés';
      toast.success(message);

      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la confirmation';
      toast.error(message);
    },
  });
}

/**
 * Request supplier quotes mutation
 */
export function useRequestSupplierQuotes() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => opportunitiesApi.requestSupplierQuotes(id),
    onSuccess: ({ data }) => {
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.lists() });

      toast.success('Demandes de devis envoyées aux fournisseurs');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || "Erreur lors de l'envoi";
      toast.error(message);
    },
  });
}

/**
 * Request client PO mutation
 */
export function useRequestClientPO() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => opportunitiesApi.requestClientPO(id),
    onSuccess: ({ data }) => {
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.lists() });

      toast.success('Devis envoyé au client');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || "Erreur lors de l'envoi";
      toast.error(message);
    },
  });
}

/**
 * Upload client PO mutation
 */
export function useUploadClientPO() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => opportunitiesApi.uploadClientPO(id, data),
    onSuccess: ({ data }) => {
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.detail(data.opportunity.id) });
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.lists() });

      toast.success('BC client uploadé - En attente approbation Finance');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || "Erreur lors de l'upload";
      toast.error(message);
    },
  });
}

/**
 * Create Insomea Quote mutation
 */
export function useCreateInsomeaQuote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => opportunitiesApi.createInsomeaQuote(id, data),
    onSuccess: ({ data }, { id }) => {
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.lists() });
      toast.success('Devis Insomea créé');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la création du devis';
      toast.error(message);
    },
  });
}

/**
 * Rollback Insomea Quote mutation
 * Transitions INSOMEA_QUOTE_CREATED → SUPPLIER_QUOTE_RECIEVED
 * so the commercial can re-enter sale prices and regenerate the quote.
 */
export function useRollbackInsomeaQuote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => opportunitiesApi.rollbackInsomeaQuote(id),
    onSuccess: ({ data }) => {
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.lists() });
      toast.success('Retour en modification du devis Insomea');
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors du retour en modification';
      toast.error(message);
    },
  });
}

/**
 * Regenerate InsomeaQuote PDF mutation
 */
export function useRegenerateQuotePdf() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => opportunitiesApi.regenerateQuotePdf(id),
    onSuccess: ({ data }) => {
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.detail(data.id) });
      toast.success('PDF régénéré avec succès');
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la génération du PDF';
      toast.error(message);
    },
  });
}

/**
 * Cancel opportunity mutation
 */
export function useCancelOpportunity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reason }) => opportunitiesApi.cancel(id, reason),
    onSuccess: ({ data }) => {
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.lists() });
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.stats() });

      toast.success('Opportunité annulée');
      return data;
    },
    onError: (error) => {
      const message = error.response?.data?.detail || "Erreur lors de l'annulation";
      toast.error(message);
    },
  });
}