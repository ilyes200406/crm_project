/**
 * PRODUCTS TABLE COMPONENT
 *
 * Table listing all products (READ-ONLY)
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';

import { DataTable, Badge } from '../../../../shared/components';

/**
 * ProductsTable Component
 *
 * @param {Object} props
 * @param {Array} props.products - Products data
 * @param {boolean} props.loading - Loading state
 */
export function ProductsTable({ products, loading }) {
  const navigate = useNavigate();

  // Columns definition
  const columns = [
    {
      header: 'Produit',
      render: (row) => (
        <div>
          <div className="font-medium text-gray-900">{row.title}</div>
          <div className="text-xs text-gray-500">SKU: {row.sku || 'N/A'}</div>
        </div>
      ),
    },
    {
      header: 'Catégorie',
      render: (row) => (
        <div className="text-sm text-gray-700">
          {row.category_display || row.category || '-'}
        </div>
      ),
    },
    {
      header: 'Éditeur',
      render: (row) => (
        <div className="text-sm text-gray-700">
          {row.publisher || '-'}
        </div>
      ),
    },
    {
      header: 'Statut',
      render: (row) => (
        <div className="flex flex-col gap-1">
          <Badge
            variant={row.is_active ? 'green' : 'red'}
            size="sm"
          >
            {row.is_active ? 'Actif' : 'Inactif'}
          </Badge>
          {row.is_deprecated && (
            <Badge variant="yellow" size="sm">
              Obsolète
            </Badge>
          )}
        </div>
      ),
    },
    {
      header: 'Actions',
      render: (row) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/app/catalogue/products/${row.id}`);
          }}
          className="p-1 text-blue-600 hover:bg-blue-50 rounded"
          title="Voir"
        >
          👁️
        </button>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={products}
      loading={loading}
      onRowClick={(product) => navigate(`/app/catalogue/products/${product.id}`)}
      emptyState={{
        message: 'Aucun produit trouvé',
      }}
    />
  );
}
