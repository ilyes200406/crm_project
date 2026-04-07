/**
 * CLIENT DETAIL PAGE
 * 
 * Page showing client details with tabs (Informations, Contacts, Activités)
 * Includes Contact CRUD functionality
 */

import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

import { Card, Badge, EmptyState, Modal } from '../../../shared/components';
import { ClientCard, ContactsTable, ContactForm } from '../components';
import { 
  useClient, 
  useDeleteClient,
  useCreateContact,
  useUpdateContact,
} from '../hooks';

export function ClientDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams();

  // Active tab
  const [activeTab, setActiveTab] = useState('info');

  // Modal state
  const [isContactModalOpen, setIsContactModalOpen] = useState(false);
  const [editingContact, setEditingContact] = useState(null);

  // Fetch client
  const { data: client, isLoading } = useClient(id);

  // Mutations
  const deleteMutation = useDeleteClient();
  const createContactMutation = useCreateContact();
  const updateContactMutation = useUpdateContact();

  // Handle delete client
  const handleDelete = async () => {
    if (!confirm(`Êtes-vous sûr de vouloir supprimer ${client.company_name} ?`)) {
      return;
    }

    try {
      await deleteMutation.mutateAsync(id);
      navigate('/app/clients');
    } catch (error) {
      // Error handled by mutation
    }
  };

  // Handle open create contact modal
  const handleCreateContact = () => {
    setEditingContact(null);
    setIsContactModalOpen(true);
  };

  // Handle open edit contact modal
  const handleEditContact = (contact) => {
    setEditingContact(contact);
    setIsContactModalOpen(true);
  };

  // Handle close modal
  const handleCloseModal = () => {
    setIsContactModalOpen(false);
    setEditingContact(null);
  };

  // Handle contact form submit
  const handleContactSubmit = async (data) => {
    try {
      if (editingContact) {
        // Update existing contact
        await updateContactMutation.mutateAsync({
          id: editingContact.id,
          data,
        });
      } else {
        // Create new contact
        await createContactMutation.mutateAsync({
          clientId: id,
          data,
        });
      }
      handleCloseModal();
    } catch (error) {
      // Error handled by mutation
    }
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
        <div className="text-center">
          <div className="text-gray-500 mb-4">Client non trouvé</div>
          <button
            onClick={() => navigate('/app/clients')}
            className="text-blue-600 hover:text-blue-800"
          >
            ← Retour aux clients
          </button>
        </div>
      </div>
    );
  }

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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {client.company_name}
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Créé {formatDistanceToNow(new Date(client.created_at), { addSuffix: true, locale: fr })}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate(`/app/clients/${id}/edit`)}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              ✏️ Modifier
            </button>
            <button
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
            >
              🗑️ Supprimer
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('info')}
            className={`
              px-4 py-2 border-b-2 font-medium text-sm transition-colors
              ${activeTab === 'info'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
              }
            `}
          >
            Informations
          </button>
          <button
            onClick={() => setActiveTab('contacts')}
            className={`
              px-4 py-2 border-b-2 font-medium text-sm transition-colors
              ${activeTab === 'contacts'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
              }
            `}
          >
            Contacts ({client.contacts?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('activities')}
            className={`
              px-4 py-2 border-b-2 font-medium text-sm transition-colors
              ${activeTab === 'activities'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
              }
            `}
          >
            Activités ({client.recent_activities?.length || 0})
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'info' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ClientCard client={client} />
          </div>
          <div>
            <Card title="Notes">
              {client.notes ? (
                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                  {client.notes}
                </p>
              ) : (
                <p className="text-sm text-gray-500 italic">Aucune note</p>
              )}
            </Card>
          </div>
        </div>
      )}

      {activeTab === 'contacts' && (
        <div className="space-y-4">
          {/* Actions Bar */}
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              {client.contacts?.length || 0} contact(s)
            </div>
            <button
              onClick={handleCreateContact}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm"
            >
              + Ajouter un contact
            </button>
          </div>

          {/* Contacts Table */}
          <Card noPadding>
            {client.contacts && client.contacts.length > 0 ? (
              <ContactsTable
                contacts={client.contacts}
                clientId={id}
                loading={false}
                onEdit={handleEditContact}
              />
            ) : (
              <EmptyState
                icon="👤"
                title="Aucun contact"
                message="Ce client n'a pas encore de contacts enregistrés."
                action={{
                  label: '+ Ajouter un contact',
                  onClick: handleCreateContact,
                }}
              />
            )}
          </Card>
        </div>
      )}

      {activeTab === 'activities' && (
        <Card noPadding>
          {client.recent_activities && client.recent_activities.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {client.recent_activities.map((activity) => (
                <div key={activity.id} className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="text-2xl">
                      {getActivityIcon(activity.activity_type)}
                    </div>
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">
                        {activity.activity_type_display}
                      </div>
                      {activity.description && (
                        <div className="text-sm text-gray-600 mt-1">
                          {activity.description}
                        </div>
                      )}
                      <div className="text-xs text-gray-500 mt-1">
                        {activity.user_name || 'Système'} •{' '}
                        {formatDistanceToNow(new Date(activity.created_at), {
                          addSuffix: true,
                          locale: fr,
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon="📋"
              title="Aucune activité"
              message="Aucune activité enregistrée pour ce client."
            />
          )}
        </Card>
      )}

      {/* Contact Modal */}
      <Modal
        isOpen={isContactModalOpen}
        onClose={handleCloseModal}
        title={editingContact ? 'Modifier le contact' : 'Nouveau contact'}
        size="md"
      >
        <ContactForm
          defaultValues={editingContact ? {
            first_name: editingContact.first_name,
            last_name: editingContact.last_name,
            position: editingContact.position || '',
            email: editingContact.email,
            phone: editingContact.phone || '',
            is_primary: editingContact.is_primary,
            notes: editingContact.notes || '',
          } : undefined}
          onSubmit={handleContactSubmit}
          isSubmitting={createContactMutation.isPending || updateContactMutation.isPending}
          onCancel={handleCloseModal}
        />
      </Modal>
    </div>
  );
}

/**
 * Get activity icon
 */
function getActivityIcon(activityType) {
  const icons = {
    CREATED: '✨',
    UPDATED: '✏️',
    DELETED: '🗑️',
    RESTORED: '♻️',
    ASSIGNED: '👤',
  };
  return icons[activityType] || '📝';
}