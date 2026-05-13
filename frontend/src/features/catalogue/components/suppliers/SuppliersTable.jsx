import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye } from 'lucide-react';

import { DataTable, Badge } from '../../../../shared/components';

export function SuppliersTable({ suppliers, loading }) {
  const navigate = useNavigate();

  const getTypeBadgeVariant = (type) => {
    const variants = { DIRECT: 'blue', DISTRIBUTOR: 'purple', RESELLER: 'green' };
    return variants[type] || 'gray';
  };

  const columns = [
    {
      header: 'Nom',
      render: (row) => <div className="font-medium text-gray-900">{row.name}</div>,
    },
    {
      header: 'Type',
      render: (row) => (
        <Badge variant={getTypeBadgeVariant(row.type)} size="sm">
          {row.type_display || row.type}
        </Badge>
      ),
    },
    {
      header: 'Email',
      render: (row) => <div className="text-sm text-gray-700">{row.support_email || '-'}</div>,
    },
    {
      header: 'Téléphone',
      render: (row) => <div className="text-sm text-gray-700">{row.support_phone || '-'}</div>,
    },
    {
      header: 'Statut',
      render: (row) => (
        <Badge variant={row.is_active ? 'green' : 'red'} size="sm">
          {row.is_active ? 'Actif' : 'Inactif'}
        </Badge>
      ),
    },
    {
      header: 'Actions',
      render: (row) => (
        <button
          onClick={(e) => { e.stopPropagation(); navigate(`/app/catalogue/suppliers/${row.id}`); }}
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
      data={suppliers}
      loading={loading}
      onRowClick={(supplier) => navigate(`/app/catalogue/suppliers/${supplier.id}`)}
      emptyState={{ message: 'Aucun fournisseur trouvé' }}
    />
  );
}
