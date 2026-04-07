/**
 * CREATE CLIENT PAGE
 * 
 * Page for creating a new client
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';

import { Card } from '../../../shared/components';
import { ClientForm } from '../components';
import { useCreateClient } from '../hooks';

export function CreateClientPage() {
  const navigate = useNavigate();
  const createMutation = useCreateClient();

  // Handle submit
  const handleSubmit = async (data) => {
    try {
      const result = await createMutation.mutateAsync(data);
      navigate(`/app/clients/${result.data.id}`);
    } catch (error) {
      // Error handled by mutation
    }
  };

  // Handle cancel
  const handleCancel = () => {
    navigate('/app/clients');
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <button
          onClick={() => navigate('/app/clients')}
          className="text-sm text-blue-600 hover:text-blue-800 mb-2"
        >
          ← Retour aux clients
        </button>
        <h1 className="text-2xl font-bold text-gray-900">Nouveau Client</h1>
        <p className="text-sm text-gray-600 mt-1">
          Créez une fiche client complète
        </p>
      </div>

      {/* Form */}
      <Card>
        <ClientForm
          onSubmit={handleSubmit}
          isSubmitting={createMutation.isPending}
          onCancel={handleCancel}
        />
      </Card>
    </div>
  );
}