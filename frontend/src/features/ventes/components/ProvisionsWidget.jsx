/**
 * PROVISIONS WIDGET
 * 
 * Widget affichant les provisions en attente (Technicien)
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

import { Card, DataTable, StatusBadge, EmptyStates } from '../../../shared/components';
import { useProvisions, useStartProvisioning } from '../hooks';

/**
 * ProvisionsWidget Component
 * 
 * @param {Object} props
 * @param {string} props.status - Filter by status (default: 'WAITING_PROVISION')
 * @param {number} props.limit - Number of items to display (default: 5)
 */
export function ProvisionsWidget({ status = 'WAITING_PROVISION', limit = 5 }) {
  const navigate = useNavigate();

  // Fetch provisions
  const { data, isLoading } = useProvisions({
    status,
    limit,
  });

  // Start provisioning mutation
  const startMutation = useStartProvisioning();

  // Handle start provisioning
  const handleStart = async (provision) => {
    try {
      await startMutation.mutateAsync(provision.id);
      navigate(`/provisions/${provision.id}`);
    } catch (error) {
      // Error handled by mutation
    }
  };

  const columns = [
    {
      header: 'Opportunité',
      render: (row) => {
        const opp = row.opportunity_line?.opportunity;
        return (
          <div>
            <div className="font-medium text-gray-900">
              {opp?.reference || '-'}
            </div>
            <div className="text-xs text-gray-500">
              {formatDistanceToNow(new Date(row.created_at), {
                addSuffix: true,
                locale: fr,
              })}
            </div>
          </div>
        );
      },
    },
    {
      header: 'Client',
      render: (row) => {
        const client = row.opportunity_line?.opportunity?.client;
        return (
          <div className="font-medium text-gray-700">
            {client?.name || '-'}
          </div>
        );
      },
    },
    {
      header: 'Produit',
      render: (row) => {
        const product = row.opportunity_line?.product;
        return (
          <div>
            <div className="text-sm font-medium text-gray-900">
              {product?.title || '-'}
            </div>
            <div className="text-xs text-gray-500">
              Qté: {row.opportunity_line?.quantity || 0}
            </div>
          </div>
        );
      },
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
          className="px-3 py-1 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          ▶️ Start
        </button>
      ),
    },
  ];

  const handleRowClick = (provision) => {
    navigate(`/provisions/${provision.id}`);
  };

  return (
    <Card title="⚠️ Provisions en Attente" noPadding>
      <DataTable
        columns={columns}
        data={data?.results || []}
        onRowClick={handleRowClick}
        loading={isLoading}
        emptyState={{
          message: 'Aucune provision en attente',
        }}
        striped={false}
      />
    </Card>
  );
}

/**
 * ProvisionsInProgressWidget - Kanban view
 * 
 * Widget showing provisions in progress
 */
export function ProvisionsInProgressWidget() {
  const navigate = useNavigate();

  // Fetch provisions in progress
  const { data, isLoading } = useProvisions({
    status: 'PROVISIONING',
    limit: 10,
  });

  if (isLoading) {
    return (
      <Card title="🔄 Mes Provisions en Cours">
        <div className="h-64 bg-gray-200 rounded animate-pulse" />
      </Card>
    );
  }

  if (!data?.results || data.results.length === 0) {
    return (
      <Card title="🔄 Mes Provisions en Cours">
        <EmptyStates.NoProvisions />
      </Card>
    );
  }

  return (
    <Card title="🔄 Mes Provisions en Cours">
      <div className="space-y-3">
        {data.results.map((provision) => {
          const opp = provision.opportunity_line?.opportunity;
          const product = provision.opportunity_line?.product;

          return (
            <div
              key={provision.id}
              className="border border-blue-200 bg-blue-50 rounded-lg p-4 hover:bg-blue-100 cursor-pointer"
              onClick={() => navigate(`/provisions/${provision.id}`)}
            >
              {/* Status badge */}
              <div className="mb-2">
                <StatusBadge status={provision.status} />
              </div>

              {/* Opportunity info */}
              <div className="mb-1">
                <div className="font-semibold text-gray-900">
                  {opp?.reference || '-'}
                </div>
                <div className="text-sm text-gray-600">
                  {opp?.client?.name || '-'}
                </div>
              </div>

              {/* Product info */}
              <div className="text-sm text-gray-700 mb-3">
                {product?.title || '-'}
              </div>

              {/* Started time */}
              <div className="text-xs text-gray-500">
                Démarré{' '}
                {formatDistanceToNow(new Date(provision.started_at), {
                  addSuffix: true,
                  locale: fr,
                })}
              </div>

              {/* Complete button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/provisions/${provision.id}/complete`);
                }}
                className="mt-3 w-full px-3 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 font-medium"
              >
                ✅ Compléter
              </button>
            </div>
          );
        })}
      </div>
    </Card>
  );
}