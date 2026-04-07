/**
 * PRODUCTS LIST PAGE
 *
 * Page listing all products with search and filters (READ-ONLY)
 */

import React, { useState } from 'react';

import { Card } from '../../../../shared/components';
import { ProductsTable, ProductFilters } from '../../components';
import { useProducts } from '../../hooks';

// Static categories from backend ProductCategory choices
const PRODUCT_CATEGORIES = [
  { value: 'OFFICE_365', label: 'Office 365' },
  { value: 'MICROSOFT_365', label: 'Microsoft 365' },
  { value: 'WINDOWS', label: 'Windows' },
  { value: 'AZURE', label: 'Azure' },
  { value: 'DYNAMICS', label: 'Dynamics 365' },
  { value: 'POWER_PLATFORM', label: 'Power Platform' },
  { value: 'SECURITY', label: 'Sécurité' },
  { value: 'OTHER', label: 'Autre' },
];

export function ProductsListPage() {
  // State for filters
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');

  // Build query params
  const params = {
    ...(search && { search }),
    ...(category && { category }),
  };

  // Fetch products
  const { data: productsData, isLoading: productsLoading } = useProducts(params);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">📦 Catalogue Produits</h1>
          <p className="text-sm text-gray-600 mt-1">
            Consultez le catalogue complet des produits disponibles
          </p>
        </div>
      </div>

      {/* Filters */}
      <ProductFilters
        search={search}
        onSearchChange={setSearch}
        category={category}
        onCategoryChange={setCategory}
        categories={PRODUCT_CATEGORIES}
      />

      {/* Results Count */}
      {!productsLoading && productsData && (
        <div className="text-sm text-gray-600">
          {productsData.count || 0} produit(s) trouvé(s)
        </div>
      )}

      {/* Products Table */}
      <Card noPadding>
        <ProductsTable
          products={productsData?.results || []}
          loading={productsLoading}
        />
      </Card>
    </div>
  );
}
