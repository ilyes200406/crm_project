/**
 * CREATE OPPORTUNITY PAGE
 *
 * Accessible by: COMMERCIAL, ADMIN
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Card } from '../../../shared/components';
import { useCreateOpportunity } from '../hooks';

// ── lazy-load clients list for the selector ──────────────────────
import { useClients } from '../../clients/hooks/useClients';

const TYPE_OPTIONS = [
  { value: 'INITIAL',   label: 'Initial — Nouvelle vente' },
  { value: 'RENEWAL',   label: 'Renewal — Renouvellement' },
  { value: 'UPSELL',    label: 'Upsell — Montée en gamme' },
  { value: 'DOWNGRADE', label: 'Downgrade — Révision à la baisse' },
];

export function CreateOpportunityPage() {
  const navigate = useNavigate();
  const createMutation = useCreateOpportunity();

  const { data: clientsData } = useClients({ page_size: 200 });
  const clients = clientsData?.results || [];

  const [form, setForm] = useState({
    name:   '',
    client: '',
    type:   'INITIAL',
    notes:  '',
  });
  const [errors, setErrors] = useState({});

  const set = (field) => (e) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const validate = () => {
    const err = {};
    if (!form.name.trim())   err.name   = 'Nom requis';
    if (!form.client)        err.client = 'Client requis';
    return err;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const err = validate();
    if (Object.keys(err).length) { setErrors(err); return; }

    const result = await createMutation.mutateAsync({
      name:   form.name.trim(),
      client: form.client,
      type:   form.type,
      notes:  form.notes.trim(),
    });

    navigate(`/app/ventes/opportunities/${result.data.id}`);
  };

  return (
    <div className="max-w-2xl">
      {/* Breadcrumb */}
      <div className="text-xs text-gray-500 mb-4">
        <button onClick={() => navigate('/app/ventes/opportunities')} className="hover:text-blue-600">
          Opportunités
        </button>
        {' / '}
        <span className="text-gray-800 font-medium">Nouvelle opportunité</span>
      </div>

      <h1 className="text-2xl font-bold text-gray-900 mb-6">➕ Nouvelle Opportunité</h1>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Name */}
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
              Nom de l'opportunité *
            </label>
            <input
              type="text"
              value={form.name}
              onChange={set('name')}
              placeholder="ex: Migration Office 365 ACME"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
          </div>

          {/* Client */}
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
              Client *
            </label>
            <select
              value={form.client}
              onChange={set('client')}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Sélectionner un client...</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>{c.company_name}</option>
              ))}
            </select>
            {errors.client && <p className="text-red-500 text-xs mt-1">{errors.client}</p>}
          </div>

          {/* Type */}
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
              Type *
            </label>
            <select
              value={form.type}
              onChange={set('type')}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {TYPE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
              Notes internes
            </label>
            <textarea
              value={form.notes}
              onChange={set('notes')}
              rows={3}
              placeholder="Contexte, remarques..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm disabled:opacity-50"
            >
              {createMutation.isPending ? 'Création...' : 'Créer l\'opportunité →'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/app/ventes/opportunities')}
              className="px-4 py-2 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 text-sm"
            >
              Annuler
            </button>
          </div>
        </form>
      </Card>

      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        ℹ️ Après création, vous pourrez ajouter les lignes produits (licences).
      </div>
    </div>
  );
}
