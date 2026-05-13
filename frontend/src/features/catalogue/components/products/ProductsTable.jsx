import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye } from 'lucide-react';

import { DataTable, Badge } from '../../../../shared/components';

export function ProductsTable({ products, loading }) {
  const navigate = useNavigate();

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
      render: (row) => <div className="text-sm text-gray-700">{row.category_display || row.category || '-'}</div>,
    },
    {
      header: 'Éditeur',
      render: (row) => <div className="text-sm text-gray-700">{row.publisher || '-'}</div>,
    },
    {
      header: 'Statut',
      render: (row) => (
        <div className="flex flex-col gap-1">
          <Badge variant={row.is_active ? 'green' : 'red'} size="sm">
            {row.is_active ? 'Actif' : 'Inactif'}
          </Badge>
          {row.is_deprecated && <Badge variant="yellow" size="sm">Obsolète</Badge>}
        </div>
      ),
    },
    {
      header: 'Actions',
      render: (row) => (
        <button
          onClick={(e) => { e.stopPropagation(); navigate(`/app/catalogue/products/${row.id}`); }}
          className="p-1.5 rounded-lg hover:bg-blue-50 text-gray-400 hover:text-blue-600 transition-colors"
          title="Voir"
        >
          <Eye size={15} />
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
      emptyState={{ message: 'Aucun produit trouvé' }}
    />
  );
}
