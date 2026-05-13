/**
 * CREATE OPPORTUNITY PAGE
 *
 * Accessible by: COMMERCIAL, ADMIN
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';

import { Card } from '../../../shared/components';
import { useCreateOpportunity } from '../hooks';
import { useClients } from '../../clients/hooks/useClients';
import { useProducts } from '../../catalogue/hooks/useProducts';

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

  const { data: productsData } = useProducts({ page_size: 200 });
  const products = productsData?.results || [];

  const [form, setForm] = useState({
    name:   '',
    client: '',
    type:   'INITIAL',
    notes:  '',
  });
  const [errors, setErrors] = useState({});

  // Lines builder state
  const [lines, setLines] = useState([]);
  const [lineForm, setLineForm] = useState({ product: '', quantity: 1 });
  const [lineError, setLineError] = useState('');

  const set = (field) => (e) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const validate = () => {
    const err = {};
    if (!form.name.trim())   err.name   = 'Nom requis';
    if (!form.client)        err.client = 'Client requis';
    return err;
  };

  const handleAddLine = () => {
    if (!lineForm.product) { setLineError('Sélectionner un produit'); return; }
    const already = lines.some((l) => l.product === lineForm.product);
    if (already) { setLineError('Ce produit est déjà dans la liste'); return; }
    const product = products.find((p) => String(p.id) === String(lineForm.product));
    setLines((prev) => [
      ...prev,
      { product: lineForm.product, quantity: Number(lineForm.quantity), _label: product?.title || lineForm.product },
    ]);
    setLineForm({ product: '', quantity: 1 });
    setLineError('');
  };

  const handleRemoveLine = (productId) =>
    setLines((prev) => prev.filter((l) => l.product !== productId));

  const handleSubmit = async (e) => {
    e.preventDefault();
    const err = validate();
    if (Object.keys(err).length) { setErrors(err); return; }

    const payload = {
      name:   form.name.trim(),
      client: form.client,
      type:   form.type,
      notes:  form.notes.trim(),
    };

    if (lines.length > 0) {
      payload.lines = lines.map(({ product, quantity }) => ({ product, quantity }));
    }

    const result = await createMutation.mutateAsync(payload);
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

      <div className="flex items-center gap-3 mb-6">
        <div className="w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center">
          <Plus size={18} className="text-blue-600" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Nouvelle Opportunité</h1>
      </div>

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

          {/* Lines section */}
          <div className="border border-gray-200 rounded-lg p-4 space-y-3">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Lignes produits <span className="normal-case font-normal text-gray-400">(optionnel)</span>
            </p>

            {/* Add row */}
            <div className="flex gap-2 items-end">
              <div className="flex-1">
                <select
                  value={lineForm.product}
                  onChange={(e) => { setLineForm((p) => ({ ...p, product: e.target.value })); setLineError(''); }}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Produit...</option>
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>{p.title}</option>
                  ))}
                </select>
              </div>
              <div className="w-20">
                <input
                  type="number"
                  min={1}
                  max={10000}
                  value={lineForm.quantity}
                  onChange={(e) => setLineForm((p) => ({ ...p, quantity: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <button
                type="button"
                onClick={handleAddLine}
                className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium whitespace-nowrap"
              >
                + Ajouter
              </button>
            </div>
            {lineError && <p className="text-red-500 text-xs">{lineError}</p>}

            {/* Lines list */}
            {lines.length > 0 && (
              <ul className="space-y-1">
                {lines.map((l) => (
                  <li key={l.product} className="flex items-center justify-between bg-gray-50 rounded px-3 py-1.5 text-sm">
                    <span className="text-gray-800">{l._label}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-gray-500 text-xs">Qté: {l.quantity}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveLine(l.product)}
                        className="text-red-400 hover:text-red-600 text-xs"
                      >
                        Retirer
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
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
    </div>
  );
}
