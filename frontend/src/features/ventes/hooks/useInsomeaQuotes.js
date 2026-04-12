/**
 * INSOMEA QUOTES HOOKS
 */

import { useQuery } from '@tanstack/react-query';

import { insomeaQuotesApi } from '../api/insomeaQuotesApi';

export const insomeaQuotesKeys = {
  all:           ['insomea-quotes'],
  byOpportunity: (oppId) => [...insomeaQuotesKeys.all, 'by-opportunity', oppId],
  detail:        (id)    => [...insomeaQuotesKeys.all, 'detail', id],
};

export function useInsomeaQuoteByOpportunity(opportunityId, options = {}) {
  return useQuery({
    queryKey: insomeaQuotesKeys.byOpportunity(opportunityId),
    queryFn: async () => {
      const { data } = await insomeaQuotesApi.getByOpportunity(opportunityId);
      return data;
    },
    enabled: !!opportunityId,
    staleTime: 30000,
    ...options,
  });
}
