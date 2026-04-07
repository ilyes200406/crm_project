/**
 * SUPPLIERS LIST PAGE
 * 
 * Page listing all suppliers with search and filters (READ-ONLY)
 */

import React, { useState } from 'react';

import { Card } from '../../../../shared/components';
import { SuppliersTable, SupplierFilters } from '../../components/suppliers';
import { useSuppliers } from '../../hooks';

export function SuppliersListPage() {
  // State for filters
  const [search, setSearch] = useState('');
  const [type, setType] = useState('');
  const [isActive, setIsActive] = useState('true');

  // Build query params
  const params = {
    ...(search && { search }),
    ...(type && { type }),
    ...(isActive && { is_active: isActive }),
  };

  // Fetch suppliers
  const { data: suppliersData, isLoading } = useSuppliers(params);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">🏢 Fournisseurs</h1>
          <p className="text-sm text-gray-600 mt-1">
            Consultez la liste des fournisseurs partenaires
          </p>
        </div>
      </div>

      {/* Filters */}
      <SupplierFilters
        search={search}
        onSearchChange={setSearch}
        type={type}
        onTypeChange={setType}
        isActive={isActive}
        onIsActiveChange={setIsActive}
      />

      {/* Results Count */}
      {!isLoading && suppliersData && (
        <div className="text-sm text-gray-600">
          {suppliersData.count || 0} fournisseur(s) trouvé(s)
        </div>
      )}

      {/* Suppliers Table */}
      <Card noPadding>
        <SuppliersTable
          suppliers={suppliersData?.results || []}
          loading={isLoading}
        />
      </Card>
    </div>
  );
}