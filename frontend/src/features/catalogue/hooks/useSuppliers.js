/**
 * SUPPLIERS HOOKS
 * 
 * React Query hooks pour fournisseurs (READ-ONLY)
 */

import { useQuery } from '@tanstack/react-query';

import { suppliersApi } from '../api/suppliersApi';

// ═══════════════════════════════════════════════════════════
// QUERY KEYS
// ═══════════════════════════════════════════════════════════

export const suppliersKeys = {
  all: ['suppliers'],
  lists: () => [...suppliersKeys.all, 'list'],
  list: (params) => [...suppliersKeys.lists(), params],
  details: () => [...suppliersKeys.all, 'detail'],
  detail: (id) => [...suppliersKeys.details(), id],
  products: (id) => [...suppliersKeys.detail(id), 'products'],
  stats: () => [...suppliersKeys.all, 'stats'],
};

// ═══════════════════════════════════════════════════════════
// QUERIES
// ═══════════════════════════════════════════════════════════

/**
 * Get all suppliers
 * 
 * @param {Object} params - Query params
 * @param {Object} options - React Query options
 */
export function useSuppliers(params = {}, options = {}) {
  return useQuery({
    queryKey: suppliersKeys.list(params),
    queryFn: async () => {
      const { data } = await suppliersApi.getAll(params);
      return data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Get supplier by ID
 * 
 * @param {string} id - Supplier UUID
 * @param {Object} options - React Query options
 */
export function useSupplier(id, options = {}) {
  return useQuery({
    queryKey: suppliersKeys.detail(id),
    queryFn: async () => {
      const { data } = await suppliersApi.getById(id);
      return data;
    },
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

/**
 * Get supplier products
 * 
 * @param {string} id - Supplier UUID
 * @param {Object} params - Query params
 * @param {Object} options - React Query options
 */
export function useSupplierProducts(id, params = {}, options = {}) {
  return useQuery({
    queryKey: suppliersKeys.products(id),
    queryFn: async () => {
      const { data } = await suppliersApi.getProducts(id, params);
      return data;
    },
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

/**
 * Get supplier stats
 * 
 * @param {Object} options - React Query options
 */
export function useSupplierStats(options = {}) {
  return useQuery({
    queryKey: suppliersKeys.stats(),
    queryFn: async () => {
      const { data } = await suppliersApi.getStats();
      return data;
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
    ...options,
  });
}