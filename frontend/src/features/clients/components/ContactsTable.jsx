import React, { useState } from 'react';
import { Pencil, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

import { DataTable, Badge } from '../../../shared/components';
import { useDeleteContact } from '../hooks';

export function ContactsTable({ contacts, clientId, loading, onEdit }) {
  const deleteMutation = useDeleteContact();
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const handleDelete = async (contact) => {
    if (deleteConfirm !== contact.id) {
      setDeleteConfirm(contact.id);
      toast('Cliquez à nouveau pour confirmer la suppression', { duration: 3000 });
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

  const columns = [
    {
      header: 'Nom',
      render: (row) => (
        <div>
          <div className="font-medium text-gray-900">
            {row.full_name}
            {row.is_primary && (
              <Badge variant="blue" size="sm" className="ml-2">Principal</Badge>
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
      render: (row) => <div className="text-sm text-gray-700">{row.phone || '-'}</div>,
    },
    {
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center gap-1">
          <button
            onClick={(e) => { e.stopPropagation(); onEdit(row); }}
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
      data={contacts}
      loading={loading}
      emptyState={{ message: 'Aucun contact trouvé' }}
    />
  );
}
