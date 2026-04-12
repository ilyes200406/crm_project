/**
 * OPPORTUNITIES LIST PAGE
 *
 * Accessible by: COMMERCIAL (own), FINANCE (advanced statuses), ADMIN (all)
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Card, DataTable, StatusBadge, Badge } from '../../../shared/components';
import { useOpportunities } from '../hooks';
import { useAuth } from '../../auth/hooks/useAuth';

const STATUS_OPTIONS = [
  { value: '', label: 'Tous les statuts' },
  { value: 'DRAFT', label: 'Brouillon' },
  { value: 'SUPPLIER_QUOTE_REQUEST', label: 'Devis fournisseur demandé' },
  { value: 'SUPPLIER_QUOTE_RECIEVED', label: 'Devis fournisseur reçu' },
  { value: 'INSOMEA_QUOTE_CREATED', label: 'Devis Insomea créé' },
  { value: 'CLIENT_PO_REQUEST', label: 'Demande BC client' },
  { value: 'CLIENT_PO_RECIEVED', label: 'BC client reçu' },
  { value: 'APPROUVED', label: 'Approuvé' },
  { value: 'INSOMEA_POS_SENT', label: 'BC Insomea envoyés' },
  { value: 'INSOMEA_POS_CONFIRMED', label: 'BC Insomea confirmés' },
  { value: 'CANCELLED', label: 'Annulé' },
];

const TYPE_OPTIONS = [
  { value: '', label: 'Tous les types' },
  { value: 'INITIAL', label: 'Initial' },
  { value: 'RENEWAL', label: 'Renewal' },
  { value: 'UPSELL', label: 'Upsell' },
  { value: 'DOWNGRADE', label: 'Downgrade' },
];

export function OpportunitiesListPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [search, setSearch]   = useState('');
  const [status, setStatus]   = useState('');
  const [type, setType]       = useState('');
  const [page, setPage]       = useState(1);

  const PAGE_SIZE = 20;

  const params = {
    page,
    page_size: PAGE_SIZE,
    ...(search && { search }),
    ...(status && { status }),
    ...(type   && { type }),
  };

  const { data, isLoading } = useOpportunities(params);

  const columns = [
    {
      header: 'Référence',
      render: (row) => (
        <div>
          <div className="font-semibold text-gray-900">{row.reference}</div>
          <div className="text-xs text-gray-500">{row.name}</div>
        </div>
      ),
    },
    {
      header: 'Client',
      render: (row) => (
        <span className="text-sm text-gray-700">{row.client_name || '—'}</span>
      ),
    },
    {
      header: 'Type',
      render: (row) => (
        <Badge variant={row.type === 'RENEWAL' ? 'purple' : 'blue'} size="sm">
          {row.type_display}
        </Badge>
      ),
    },
    {
      header: 'Assigné à',
      render: (row) => (
        <span className="text-sm text-gray-600">
          {row.assigned_to_name || row.created_by_name || '—'}
        </span>
      ),
    },
    {
      header: 'Statut',
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      header: 'Montant',
      render: (row) => {
        const total = row.insomea_quote?.total_sale;
        return (
          <span className="text-sm font-semibold text-gray-900">
            {total != null ? `${Number(total).toLocaleString('fr-FR')} DT` : '—'}
          </span>
        );
      },
    },
    {
      header: 'Créé le',
      render: (row) => (
        <span className="text-xs text-gray-500">
          {new Date(row.created_at).toLocaleDateString('fr-FR')}
        </span>
      ),
    },
    {
      header: 'Actions',
      render: (row) => (
        <button
          onClick={(e) => { e.stopPropagation(); navigate(`/app/ventes/opportunities/${row.id}`); }}
          className="px-3 py-1 border border-gray-300 text-gray-600 text-xs rounded-lg hover:bg-gray-50"
        >
          Voir →
        </button>
      ),
    },
  ];

  const totalPages = data ? Math.ceil(data.count / PAGE_SIZE) : 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">📋 Opportunités</h1>
          <p className="text-sm text-gray-500 mt-1">
            {data?.count ?? '—'} opportunité{data?.count !== 1 ? 's' : ''}
          </p>
        </div>
        {['COMMERCIAL', 'ADMIN'].includes(user?.role) && (
          <button
            onClick={() => navigate('/app/ventes/opportunities/new')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm"
          >
            + Nouvelle Opportunité
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="🔍 Référence, client, nom..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm flex-1 min-w-48 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <select
          value={type}
          onChange={(e) => { setType(e.target.value); setPage(1); }}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {TYPE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        {(search || status || type) && (
          <button
            onClick={() => { setSearch(''); setStatus(''); setType(''); setPage(1); }}
            className="px-3 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            ✕ Réinitialiser
          </button>
        )}
      </div>

      {/* Table */}
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.results || []}
          loading={isLoading}
          onRowClick={(row) => navigate(`/app/ventes/opportunities/${row.id}`)}
          emptyState={{ message: 'Aucune opportunité trouvée' }}
        />

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
            <span className="text-xs text-gray-500">
              Page {page} sur {totalPages} · {data?.count} résultats
            </span>
            <div className="flex gap-2">
              <button
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
                className="px-3 py-1 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
              >
                ← Précédent
              </button>
              <button
                disabled={page === totalPages}
                onClick={() => setPage(page + 1)}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded-lg disabled:opacity-40 hover:bg-blue-700"
              >
                Suivant →
              </button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
