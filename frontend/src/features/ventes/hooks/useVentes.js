/**
import { useQuery } from '@tanstack/react-query';
import { ventesApi } from '../api/ventesApi';

export function useOpportunityStatsQuery() {
  return useQuery({
    queryKey: ['opportunity-stats'],
    queryFn: async () => {
      const { data } = await ventesApi.getOpportunityStats();
      return data;
    },
  });
}

export function useOpportunityPipelineQuery() {
  return useQuery({
    queryKey: ['opportunity-pipeline'],
    queryFn: async () => {
      const { data } = await ventesApi.getOpportunityPipeline();
      return data;
    },
  });
}

export function useOpportunitiesQuery(params) {
  return useQuery({
    queryKey: ['opportunities', params],
    queryFn: async () => {
      const { data } = await ventesApi.getOpportunities(params);
      return data;
    },
    enabled: params !== false,
  });
}

export function useProvisionsQuery(params) {
  return useQuery({
    queryKey: ['provisions', params],
    queryFn: async () => {
      const { data } = await ventesApi.getProvisions(params);
      return data;
    },
    enabled: params !== false,
  });
}

export function useSubscriptionStatsQuery() {
  return useQuery({
    queryKey: ['subscription-stats'],
    queryFn: async () => {
      const { data } = await ventesApi.getSubscriptionStats();
      return data;
    },
  });
}
 */