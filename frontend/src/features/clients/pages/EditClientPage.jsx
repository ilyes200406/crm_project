/**
 * EDIT CLIENT PAGE
 * 
 * Page for editing existing client
 */

import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { Card } from '../../../shared/components';
import { ClientForm } from '../components';
import { useClient, useUpdateClient } from '../hooks';

export function EditClientPage() {
  const navigate = useNavigate();
  const { id } = useParams();

  // Fetch client
  const { data: client, isLoading } = useClient(id);

  // Update mutation
  const updateMutation = useUpdateClient();

  // Handle submit
  const handleSubmit = async (data) => {
    try {
      await updateMutation.mutateAsync({ id, data });
      navigate(`/app/clients/${id}`);
    } catch (error) {
      // Error handled by mutation
    }
  };

  // Handle cancel
  const handleCancel = () => {
    navigate(`/app/clients/${id}`);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Chargement...</div>
      </div>
    );
  }

  // Not found
  if (!client) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Client non trouvé</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <button
          onClick={() => navigate(`/app/clients/${id}`)}
          className="text-sm text-blue-600 hover:text-blue-800 mb-2"
        >
          ← Retour au client
        </button>
        <h1 className="text-2xl font-bold text-gray-900">
          Modifier {client.company_name}
        </h1>
        <p className="text-sm text-gray-600 mt-1">
          Mettez à jour les informations du client
        </p>
      </div>

      {/* Form */}
      <Card>
        <ClientForm
          defaultValues={{
            company_name: client.company_name,
            industry: client.industry,
            email: client.email,
            phone: client.phone || '',
            website: client.website || '',
            address: client.address || '',
            tenant_microsoft: client.tenant_microsoft || '',
            notes: client.notes || '',
          }}
          onSubmit={handleSubmit}
          isSubmitting={updateMutation.isPending}
          onCancel={handleCancel}
        />
      </Card>
    </div>
  );
}