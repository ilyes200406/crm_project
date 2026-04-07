/**
 * CLIENTS TABLE COMPONENT
 * 
 * Table listing all clients
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

import { DataTable, Badge } from '../../../shared/components';
import { useDeleteClient } from '../hooks';

/**
 * ClientsTable Component
 * 
 * @param {Object} props
 * @param {Array} props.clients - Clients data
 * @param {boolean} props.loading - Loading state
 */
export function ClientsTable({ clients, loading }) {
  const navigate = useNavigate();
  const deleteMutation = useDeleteClient();
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  // Handle delete
  const handleDelete = async (client) => {
    if (deleteConfirm !== client.id) {
      setDeleteConfirm(client.id);
      toast('Cliquez à nouveau pour confirmer la suppression', {
        icon: '⚠️',
        duration: 3000,
      });
      
      // Reset after 3 seconds
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

  // Columns definition
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
      render: (row) => (
        <div className="text-sm text-gray-700">{row.email}</div>
      ),
    },
    {
      header: 'Téléphone',
      render: (row) => (
        <div className="text-sm text-gray-700">
          {row.phone || '-'}
        </div>
      ),
    },
    {
      header: 'Assigné à',
      render: (row) => (
        <div className="text-sm text-gray-700">
          {row.assigned_to_name || '-'}
        </div>
      ),
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
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/app/clients/${row.id}`);
            }}
            className="p-1 text-blue-600 hover:bg-blue-50 rounded"
            title="Voir"
          >
            👁️
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/app/clients/${row.id}/edit`);
            }}
            className="p-1 text-gray-600 hover:bg-gray-50 rounded"
            title="Modifier"
          >
            ✏️
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleDelete(row);
            }}
            disabled={deleteMutation.isPending}
            className={`
              p-1 text-red-600 hover:bg-red-50 rounded disabled:opacity-50
              ${deleteConfirm === row.id ? 'bg-red-100' : ''}
            `}
            title={deleteConfirm === row.id ? 'Confirmer suppression' : 'Supprimer'}
          >
            🗑️
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
        action: {
          label: '+ Créer un client',
          onClick: () => navigate('/app/clients/new'),
        },
      }}
    />
  );
}