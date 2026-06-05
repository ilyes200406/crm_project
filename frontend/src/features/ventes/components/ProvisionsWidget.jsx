import React from 'react';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import { Play, AlertTriangle, RefreshCw, CheckCircle2 } from 'lucide-react';

import { Card, DataTable, StatusBadge, EmptyStates } from '../../../shared/components';
import { useProvisions, useStartProvisioning } from '../hooks';

export function ProvisionsWidget({ status = 'WAITING_PROVISION', limit = 5 }) {
  const navigate = useNavigate();

  const { data, isLoading } = useProvisions({ status, limit });
  const startMutation = useStartProvisioning();

  const handleStart = async (provision) => {
    try {
      await startMutation.mutateAsync(provision.id);
      navigate(`/app/ventes/provisions/${provision.id}`);
    } catch (error) {
      // Error handled by mutation
    }
  };

  const columns = [
    {
      header: 'Opportunité',
      render: (row) => (
        <div>
          <div className="font-medium text-gray-900">{row.opportunity_reference || '-'}</div>
          <div className="text-xs text-gray-500">
            {formatDistanceToNow(new Date(row.created_at), { addSuffix: true, locale: fr })}
          </div>
        </div>
      ),
    },
    {
      header: 'Client',
      render: (row) => (
        <div className="font-medium text-gray-700">{row.client_name || '-'}</div>
      ),
    },
    {
      header: 'Produit',
      render: (row) => (
        <div>
          <div className="text-sm font-medium text-gray-900">{row.product_title || '-'}</div>
          <div className="text-xs text-gray-500">Qté: {row.opportunity_line?.quantity || 0}</div>
        </div>
      ),
    },
    {
      header: 'Actions',
      render: (row) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            handleStart(row);
          }}
          disabled={startMutation.isPending}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          <Play size={12} />
          Démarrer
        </button>
      ),
    },
  ];

  const handleRowClick = (provision) => {
    navigate(`/app/ventes/provisions/${provision.id}`);
  };

  const cardTitle = (
    <span className="flex items-center gap-2">
      <AlertTriangle size={16} className="text-amber-500 shrink-0" />
      Provisions en Attente
    </span>
  );

  return (
    <Card title={cardTitle} noPadding>
      <DataTable
        columns={columns}
        data={data?.results || []}
        onRowClick={handleRowClick}
        loading={isLoading}
        emptyState={{ message: 'Aucune provision en attente' }}
        striped={false}
      />
    </Card>
  );
}

export function ProvisionsInProgressWidget() {
  const navigate = useNavigate();

  const { data, isLoading } = useProvisions({ status: 'PROVISIONING', limit: 10 });

  const cardTitle = (
    <span className="flex items-center gap-2">
      <RefreshCw size={16} className="text-blue-500 shrink-0" />
      Mes Provisions en Cours
    </span>
  );

  if (isLoading) {
    return (
      <Card title={cardTitle}>
        <div className="h-64 bg-gray-200 rounded animate-pulse" />
      </Card>
    );
  }

  if (!data?.results || data.results.length === 0) {
    return (
      <Card title={cardTitle}>
        <EmptyStates.NoProvisions />
      </Card>
    );
  }

  return (
    <Card title={cardTitle}>
      <div className="space-y-3">
        {data.results.map((provision) => (
            <div
              key={provision.id}
              className="border border-blue-200 bg-blue-50 rounded-xl p-4 hover:bg-blue-100 cursor-pointer transition-colors"
              onClick={() => navigate(`/app/ventes/provisions/${provision.id}`)}
            >
              <div className="mb-2">
                <StatusBadge status={provision.status} />
              </div>
              <div className="mb-1">
                <div className="font-semibold text-gray-900">{provision.opportunity_reference || '-'}</div>
                <div className="text-sm text-gray-600">{provision.client_name || '-'}</div>
              </div>
              <div className="text-sm text-gray-700 mb-3">{provision.product_title || '-'}</div>
              <div className="text-xs text-gray-500">
                Démarré{' '}
                {formatDistanceToNow(new Date(provision.provisioning_started_at), {
                  addSuffix: true,
                  locale: fr,
                })}
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/app/ventes/provisions/${provision.id}`);
                }}
                className="mt-3 w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors"
              >
                <CheckCircle2 size={14} />
                Compléter
              </button>
            </div>
          ))}

      </div>
    </Card>
  );
}
