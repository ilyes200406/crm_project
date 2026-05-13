import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, Pencil, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

import { DataTable, Badge } from '../../../shared/components';
import { useDeleteClient } from '../hooks';

export function ClientsTable({ clients, loading }) {
  const navigate = useNavigate();
  const deleteMutation = useDeleteClient();
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const handleDelete = async (client) => {
    if (deleteConfirm !== client.id) {
      setDeleteConfirm(client.id);
      toast('Cliquez à nouveau pour confirmer la suppression', { duration: 3000 });
      setTimeout(() => setDeleteConfirm(null), 3000);
      return;
    }
    try {
      await deleteMutation.mutateAsync(client.id);
      setDeleteConfirm(null);
    } catch (error) {
      // Error handled by mutation
    }
  };

  const columns = [
    {
      header: 'Entreprise',
      render: (row) => (
        <div>
          <div className="font-medium text-gray-900">{row.company_name}</div>
          <div className="text-xs text-gray-500">{row.industry_display || row.industry}</div>
        </div>
      ),
    },
    {
      header: 'Email',
      render: (row) => <div className="text-sm text-gray-700">{row.email}</div>,
    },
    {
      header: 'Téléphone',
      render: (row) => <div className="text-sm text-gray-700">{row.phone || '-'}</div>,
    },
    {
      header: 'Assigné à',
      render: (row) => <div className="text-sm text-gray-700">{row.assigned_to_name || '-'}</div>,
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
        <div className="flex items-center gap-1">
          <button
            onClick={(e) => { e.stopPropagation(); navigate(`/app/clients/${row.id}`); }}
            className="p-1.5 rounded-lg hover:bg-blue-50 text-gray-400 hover:text-blue-600 transition-colors"
            title="Voir"
          >
            <Eye size={15} />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); navigate(`/app/clients/${row.id}/edit`); }}
            className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-700 transition-colors"
            title="Modifier"
          >
            <Pencil size={15} />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); handleDelete(row); }}
            disabled={deleteMutation.isPending}
            className={`p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-600 transition-colors disabled:opacity-50 ${
              deleteConfirm === row.id ? 'bg-red-100 text-red-600' : ''
            }`}
            title={deleteConfirm === row.id ? 'Confirmer suppression' : 'Supprimer'}
          >
            <Trash2 size={15} />
          </button>
        </div>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={clients}
      loading={loading}
      onRowClick={(client) => navigate(`/app/clients/${client.id}`)}
      emptyState={{
        message: 'Aucun client trouvé',
        action: { label: '+ Créer un client', onClick: () => navigate('/app/clients/new') },
      }}
    />
  );
}
