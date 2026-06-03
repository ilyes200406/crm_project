/**
 * SUBSCRIPTIONS LIST PAGE
 *
 * Accessible by: All roles
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ClipboardList, Search, RotateCcw, ChevronLeft, ChevronRight, AlertTriangle } from 'lucide-react';

import { Card, DataTable, StatusBadge, Badge } from '../../../shared/components';
import { useSubscriptions } from '../hooks';

const STATUS_OPTIONS = [
  { value: '',               label: 'Tous les statuts' },
  { value: 'ACTIVE',         label: 'Actif' },
  { value: 'PENDING_RENEWAL', label: 'Renouvellement en attente' },
  { value: 'EXPIRED',        label: 'Expiré' },
  { value: 'CANCELLED',      label: 'Annulé' },
];

function ExpiryBadge({ days }) {
  if (days == null) return <span className="text-gray-400 text-xs">—</span>;
  if (days < 0) return <span className="text-xs text-red-600 font-medium">Expiré</span>;
  if (days <= 7)  return <span className="inline-flex items-center gap-1 text-xs font-medium text-red-600"><AlertTriangle size={11} />{days}j</span>;
  if (days <= 30) return <span className="text-xs font-medium text-amber-600">{days}j</span>;
  return <span className="text-xs text-gray-500">{days}j</span>;
}

export function SubscriptionsListPage() {
  const navigate = useNavigate();

  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage]     = useState(1);

  const PAGE_SIZE = 20;

  const params = {
    page,
    page_size: PAGE_SIZE,
    ...(search && { search }),
    ...(status ? { status } : { exclude_cancelled: 'true' }),
  };

  const { data, isLoading } = useSubscriptions(params);

  const columns = [
    {
      header: 'Subscription',
      render: (row) => (
        <span className="font-mono text-sm font-semibold text-gray-900">
          {row.subscription_number}
        </span>
      ),
    },
    {
      header: 'Client',
      render: (row) => (
        <span className="text-sm text-gray-700">{row.client_name || '—'}</span>
      ),
    },
    {
      header: 'Produit',
      render: (row) => (
        <span className="text-sm text-gray-700">{row.product_title || '—'}</span>
      ),
    },
    {
      header: 'Qté',
      render: (row) => (
        <span className="text-sm text-gray-600 tabular-nums">{row.quantity}</span>
      ),
    },
    {
      header: 'Terme actuel',
      render: (row) => (
        <div className="text-xs text-gray-500 space-y-0.5">
          {row.current_term_start && (
            <div>{new Date(row.current_term_start).toLocaleDateString('fr-FR')}</div>
          )}
          {row.current_term_end && (
            <div className="text-gray-400">→ {new Date(row.current_term_end).toLocaleDateString('fr-FR')}</div>
          )}
        </div>
      ),
    },
    {
      header: 'Statut',
      render: (row) => (
        <div className="flex flex-col gap-1">
          <StatusBadge status={row.status} />
          {row.is_expiring_soon && row.status === 'ACTIVE' && (
            <Badge variant="yellow" size="xs">Expire bientôt</Badge>
          )}
        </div>
      ),
    },
    {
      header: 'Expiration',
      render: (row) => <ExpiryBadge days={row.days_until_expiration} />,
    },
    {
      header: 'Cycle',
      render: (row) => (
        <span className="text-xs text-gray-500">{row.billing_cycle_display || '—'}</span>
      ),
    },
    {
      header: 'Provisionné par',
      render: (row) => (
        <span className="text-sm text-gray-600">{row.provisionned_by_name || '—'}</span>
      ),
    },
  ];

  const totalPages = data ? Math.ceil(data.count / PAGE_SIZE) : 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center">
          <ClipboardList size={18} className="text-blue-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Abonnements</h1>
          <p className="text-sm text-gray-500">
            {data?.count ?? '—'} abonnement{data?.count !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-48">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Numéro, client, produit..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full border border-gray-300 rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        {(search || status) && (
          <button
            onClick={() => { setSearch(''); setStatus(''); setPage(1); }}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RotateCcw size={13} />
            Réinitialiser
          </button>
        )}
      </div>

      {/* Table */}
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.results || []}
          loading={isLoading}
          onRowClick={(row) => navigate(`/app/ventes/subscriptions/${row.id}`)}
          emptyState={{ message: 'Aucune subscription trouvée' }}
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
                className="inline-flex items-center gap-1 px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-colors"
              >
                <ChevronLeft size={14} />
                Précédent
              </button>
              <button
                disabled={page === totalPages}
                onClick={() => setPage(page + 1)}
                className="inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg disabled:opacity-40 hover:bg-blue-700 transition-colors"
              >
                Suivant
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
