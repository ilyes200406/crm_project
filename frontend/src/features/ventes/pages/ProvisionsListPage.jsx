/**
 * PROVISIONS LIST PAGE
 *
 * Accessible by: TECHNICIEN, ADMIN
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Card, DataTable, StatusBadge, Badge } from '../../../shared/components';
import { useProvisions, useStartProvisioning } from '../hooks';

const STATUS_OPTIONS = [
  { value: '',                label: 'Tous les statuts' },
  { value: 'WAITING_PROVISION', label: 'En attente' },
  { value: 'PROVISIONING',   label: 'En cours' },
  { value: 'PROVISIONED',    label: 'Provisionné' },
  { value: 'ERROR',          label: 'Erreur' },
];

const TYPE_OPTIONS = [
  { value: '',        label: 'Tous les types' },
  { value: 'false',   label: 'Initial' },
  { value: 'true',    label: 'Renewal' },
];

function ActionsCell({ row, navigate }) {
  const startMutation = useStartProvisioning();

  const handleStart = async (e) => {
    e.stopPropagation();
    await startMutation.mutateAsync(row.id);
    navigate(`/app/ventes/provisions/${row.id}`);
  };

  if (row.status === 'WAITING_PROVISION') {
    return (
      <button
        onClick={handleStart}
        disabled={startMutation.isPending}
        className="px-3 py-1 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        ▶ Start
      </button>
    );
  }
  if (row.status === 'PROVISIONING') {
    return (
      <button
        onClick={(e) => { e.stopPropagation(); navigate(`/app/ventes/provisions/${row.id}`); }}
        className="px-3 py-1 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700"
      >
        ✅ Compléter
      </button>
    );
  }
  return (
    <button
      onClick={(e) => { e.stopPropagation(); navigate(`/app/ventes/provisions/${row.id}`); }}
      className="px-3 py-1 border border-gray-300 text-gray-600 text-xs rounded-lg hover:bg-gray-50"
    >
      Voir →
    </button>
  );
}

export function ProvisionsListPage() {
  const navigate = useNavigate();

  const [search, setSearch]     = useState('');
  const [status, setStatus]     = useState('');
  const [isRenewal, setIsRenewal] = useState('');
  const [page, setPage]         = useState(1);

  const PAGE_SIZE = 20;

  const params = {
    page,
    page_size: PAGE_SIZE,
    ...(search    && { search }),
    ...(status    && { status }),
    ...(isRenewal && { is_renewal: isRenewal }),
  };

  const { data, isLoading } = useProvisions(params);

  const columns = [
    {
      header: 'Client',
      render: (row) => (
        <div className="font-semibold text-gray-900 text-sm">{row.client_name || '—'}</div>
      ),
    },
    {
      header: 'Produit',
      render: (row) => (
        <span className="text-sm text-gray-700">{row.product_title || '—'}</span>
      ),
    },
    {
      header: 'Opportunité',
      render: (row) => (
        <span className="text-xs text-gray-500 font-mono">{row.opportunity_reference || '—'}</span>
      ),
    },
    {
      header: 'Type',
      render: (row) => (
        <Badge variant={row.is_renewal ? 'purple' : 'blue'} size="sm">
          {row.is_renewal ? 'Renewal' : 'Initial'}
        </Badge>
      ),
    },
    {
      header: 'Statut',
      render: (row) => <StatusBadge status={row.status} />,
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
      render: (row) => <ActionsCell row={row} navigate={navigate} />,
    },
  ];

  const totalPages = data ? Math.ceil(data.count / PAGE_SIZE) : 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">⚙️ Provisions</h1>
        <p className="text-sm text-gray-500 mt-1">
          {data?.count ?? '—'} provision{data?.count !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="🔍 Client, produit..."
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
          value={isRenewal}
          onChange={(e) => { setIsRenewal(e.target.value); setPage(1); }}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {TYPE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        {(search || status || isRenewal) && (
          <button
            onClick={() => { setSearch(''); setStatus(''); setIsRenewal(''); setPage(1); }}
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
          onRowClick={(row) => navigate(`/app/ventes/provisions/${row.id}`)}
          emptyState={{ message: 'Aucune provision trouvée' }}
        />

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
