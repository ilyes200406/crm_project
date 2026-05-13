import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, CheckCircle2, AlertTriangle, ChevronRight } from 'lucide-react';

import { Card, DataTable, StatusBadge, EmptyStates } from '../../../shared/components';
import { useOpportunities } from '../hooks';

export function OpportunitiesWidget({
  title = 'Mes Opportunités Actives',
  params = {},
  limit = 5,
  showViewAll = true,
}) {
  const navigate = useNavigate();

  const { data, isLoading } = useOpportunities({ ...params, limit });

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
        <div className="font-medium text-gray-700">{row.client?.name || '-'}</div>
      ),
    },
    {
      header: 'Statut',
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

  const handleRowClick = (opportunity) => {
    navigate(`/app/ventes/opportunities/${opportunity.id}`);
  };

  const footer = showViewAll && data?.results?.length > 0 && (
    <button
      onClick={() => navigate('/app/ventes/opportunities')}
      className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 font-medium"
    >
      Voir tout ({data.count || 0})
      <ChevronRight size={14} />
    </button>
  );

  return (
    <Card title={title} footer={footer} noPadding>
      <DataTable
        columns={columns}
        data={data?.results || []}
        onRowClick={handleRowClick}
        loading={isLoading}
        emptyState={{ message: 'Aucune opportunité active' }}
      />
    </Card>
  );
}

export function OpportunitiesApprovalWidget() {
  const navigate = useNavigate();

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
        <div className="font-medium text-gray-700">{row.client?.name || '-'}</div>
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
                window.open(po.document, '_blank');
              }}
              className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
            >
              <FileText size={12} />
              Voir
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
          <div className="font-semibold text-gray-900">{total.toLocaleString()} DT</div>
        );
      },
    },
    {
      header: 'Commercial',
      render: (row) => (
        <span className="text-sm text-gray-600">
          {row.created_by_name || row.assigned_to_name || '—'}
        </span>
      ),
    },
    {
      header: 'Actions',
      render: (row) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/app/ventes/opportunities/${row.id}`);
          }}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white text-xs font-medium rounded-lg hover:bg-green-700 transition-colors"
        >
          <CheckCircle2 size={13} />
          Approuver
        </button>
      ),
    },
  ];

  const handleRowClick = (opportunity) => {
    navigate(`/app/ventes/opportunities/${opportunity.id}`);
  };

  const cardTitle = (
    <span className="flex items-center gap-2">
      <AlertTriangle size={16} className="text-amber-500 shrink-0" />
      Opportunités à Approuver
    </span>
  );

  return (
    <Card title={cardTitle} noPadding>
      <DataTable
        columns={columns}
        data={data?.results || []}
        onRowClick={handleRowClick}
        loading={isLoading}
        emptyState={{ message: "Aucune opportunité en attente d'approbation" }}
        striped={false}
      />
    </Card>
  );
}
