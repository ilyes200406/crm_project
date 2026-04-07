/**
 * PRODUCTS HOOKS
 * 
 * React Query hooks pour produits (READ-ONLY)
 */

import { useQuery } from '@tanstack/react-query';

import { productsApi } from '../api/productsApi';

// ═══════════════════════════════════════════════════════════
// QUERY KEYS
// ═══════════════════════════════════════════════════════════

export const productsKeys = {
  all: ['products'],
  lists: () => [...productsKeys.all, 'list'],
  list: (params) => [...productsKeys.lists(), params],
  details: () => [...productsKeys.all, 'detail'],
  detail: (id) => [...productsKeys.details(), id],
  search: (query) => [...productsKeys.all, 'search', query],
};

// ═══════════════════════════════════════════════════════════
// QUERIES
// ═══════════════════════════════════════════════════════════

/**
 * Get all products
 * 
 * @param {Object} params - Query params
 * @param {Object} options - React Query options
 */
export function useProducts(params = {}, options = {}) {
  return useQuery({
    queryKey: productsKeys.list(params),
    queryFn: async () => {
      const { data } = await productsApi.getAll(params);
      return data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Get product by ID
 * 
 * @param {string} id - Product UUID
 * @param {Object} options - React Query options
 */
export function useProduct(id, options = {}) {
  return useQuery({
    queryKey: productsKeys.detail(id),
    queryFn: async () => {
      const { data } = await productsApi.getById(id);
      return data;
    },
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

/**
 * Search products
 * 
 * @param {string} query - Search query
 * @param {Object} options - React Query options
 */
export function useProductSearch(query, options = {}) {
  return useQuery({
    queryKey: productsKeys.search(query),
    queryFn: async () => {
      const { data } = await productsApi.search(query);
      return data;
    },
    enabled: !!query && query.length >= 2,
    staleTime: 2 * 60 * 1000, // 2 minutes
    ...options,
  });
}