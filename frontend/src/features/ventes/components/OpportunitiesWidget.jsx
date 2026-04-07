/**
 * OPPORTUNITIES WIDGET
 * 
 * Widget affichant les opportunités actives (Commercial/Finance)
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';

import { Card, DataTable, StatusBadge, EmptyStates } from '../../../shared/components';
import { useOpportunities } from '../hooks';

/**
 * OpportunitiesWidget Component
 * 
 * @param {Object} props
 * @param {string} props.title - Widget title (optional)
 * @param {Object} props.params - API query params (optional)
 * @param {number} props.limit - Number of rows to display (default: 5)
 * @param {boolean} props.showViewAll - Show "View all" link (default: true)
 */
export function OpportunitiesWidget({
  title = 'Mes Opportunités Actives',
  params = {},
  limit = 5,
  showViewAll = true,
}) {
  const navigate = useNavigate();

  // Fetch opportunities
  const { data, isLoading } = useOpportunities({
    ...params,
    limit,
  });

  // Columns definition
  const columns = [
    {
      header: 'Référence',
      accessor: 'reference',
      render: (row) => (
        <div>
          <div className="font-medium text-gray-900">{row.reference}</div>
          <div className="text-xs text-gray-500">{row.type_display}</div>
        </div>
      ),
    },
    {
      header: 'Client',
      accessor: 'client',
      render: (row) => (
        <div className="font-medium text-gray-700">
          {row.client?.name || '-'}
        </div>
      ),
    },
    {
      header: 'Status',
      accessor: 'status',
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      header: 'Montant',
      accessor: 'total',
      render: (row) => {
        const total = row.insomea_quote?.total_sale || 0;
        return (
          <div className="font-semibold text-gray-900">
            {total > 0 ? `${total.toLocaleString()} DT` : '-'}
          </div>
        );
      },
    },
  ];

  // Handle row click
  const handleRowClick = (opportunity) => {
    navigate(`/ventes/opportunities/${opportunity.id}`);
  };

  // Footer action
  const footer = showViewAll && data?.results?.length > 0 && (
    <button
      onClick={() => navigate('/ventes?tab=opportunities')}
      className="text-sm text-blue-600 hover:text-blue-800 font-medium"
    >
      Voir tout ({data.count || 0}) →
    </button>
  );

  return (
    <Card title={title} footer={footer} noPadding>
      <DataTable
        columns={columns}
        data={data?.results || []}
        onRowClick={handleRowClick}
        loading={isLoading}
        emptyState={{
          message: 'Aucune opportunité active',
        }}
      />
    </Card>
  );
}

/**
 * OpportunitiesApprovalWidget - For Finance
 * 
 * Widget showing opportunities waiting for approval
 */
export function OpportunitiesApprovalWidget() {
  const navigate = useNavigate();

  // Fetch opportunities waiting approval
  const { data, isLoading } = useOpportunities({
    status: 'CLIENT_PO_RECIEVED',
    limit: 10,
  });

  const columns = [
    {
      header: 'Référence',
      accessor: 'reference',
      render: (row) => (
        <div className="font-medium text-gray-900">{row.reference}</div>
      ),
    },
    {
      header: 'Client',
      accessor: 'client',
      render: (row) => (
        <div className="font-medium text-gray-700">
          {row.client?.name || '-'}
        </div>
      ),
    },
    {
      header: 'BC Client',
      accessor: 'client_po',
      render: (row) => {
        const po = row.client_po;
        return po ? (
          <div>
            <div className="text-sm font-medium text-gray-900">{po.po_number}</div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                // Open PDF in new tab
                window.open(po.document, '_blank');
              }}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              📄 Voir
            </button>
          </div>
        ) : (
          '-'
        );
      },
    },
    {
      header: 'Montant',
      accessor: 'total',
      render: (row) => {
        const total = row.insomea_quote?.total_sale || 0;
        return (
          <div className="font-semibold text-gray-900">
            {total.toLocaleString()} DT
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
            navigate(`/ventes/opportunities/${row.id}?tab=approval`);
          }}
          className="px-3 py-1 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700"
        >
          ✅ Approuver
        </button>
      ),
    },
  ];

  const handleRowClick = (opportunity) => {
    navigate(`/ventes/opportunities/${opportunity.id}?tab=approval`);
  };

  return (
    <Card title="⚠️ Opportunités à Approuver" noPadding>
      <DataTable
        columns={columns}
        data={data?.results || []}
        onRowClick={handleRowClick}
        loading={isLoading}
        emptyState={{
          message: 'Aucune opportunité en attente d\'approbation',
        }}
        striped={false}
      />
    </Card>
  );
}