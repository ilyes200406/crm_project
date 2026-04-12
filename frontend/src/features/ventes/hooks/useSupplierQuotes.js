/**
 * SUPPLIER QUOTES HOOKS
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import { supplierQuotesApi } from '../api/supplierQuotesApi';
import { opportunitiesKeys } from './useOpportunities';

export function useCreateSupplierQuote(opportunityId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (formData) => supplierQuotesApi.create(formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: opportunitiesKeys.detail(opportunityId) });
      toast.success('Devis fournisseur enregistré');
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Erreur lors de la création du devis';
      toast.error(message);
    },
  });
}
