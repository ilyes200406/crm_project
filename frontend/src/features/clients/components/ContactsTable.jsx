/**
 * CONTACTS TABLE COMPONENT
 * 
 * Table for client contacts with CRUD actions
 */

import React, { useState } from 'react';
import toast from 'react-hot-toast';

import { DataTable, Badge } from '../../../shared/components';
import { useDeleteContact } from '../hooks';

/**
 * ContactsTable Component
 * 
 * @param {Object} props
 * @param {Array} props.contacts - Contacts data
 * @param {string} props.clientId - Client UUID
 * @param {boolean} props.loading - Loading state
 * @param {Function} props.onEdit - Edit handler
 */
export function ContactsTable({ contacts, clientId, loading, onEdit }) {
  const deleteMutation = useDeleteContact();
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  // Handle delete
  const handleDelete = async (contact) => {
    if (deleteConfirm !== contact.id) {
      setDeleteConfirm(contact.id);
      toast('Cliquez à nouveau pour confirmer la suppression', {
        icon: '⚠️',
        duration: 3000,
      });
      
      // Reset after 3 seconds
      setTimeout(() => setDeleteConfirm(null), 3000);
      return;
    }

    try {
      await deleteMutation.mutateAsync({ id: contact.id, clientId });
      setDeleteConfirm(null);
    } catch (error) {
      // Error handled by mutation
    }
  };

  // Columns definition
  const columns = [
    {
      header: 'Nom',
      render: (row) => (
        <div>
          <div className="font-medium text-gray-900">
            {row.full_name}
            {row.is_primary && (
              <Badge variant="blue" size="sm" className="ml-2">
                Principal
              </Badge>
            )}
          </div>
          <div className="text-xs text-gray-500">{row.position || '-'}</div>
        </div>
      ),
    },
    {
      header: 'Email',
      render: (row) => (
        <a
          href={`mailto:${row.email}`}
          className="text-sm text-blue-600 hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {row.email}
        </a>
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
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onEdit(row);
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
      data={contacts}
      loading={loading}
      emptyState={{
        message: 'Aucun contact trouvé',
      }}
    />
  );
}