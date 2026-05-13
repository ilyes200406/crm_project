import React from 'react';
import {
  TrendingUp, Calendar, DollarSign, CheckCircle2,
  AlertTriangle, BarChart3, RefreshCw,
} from 'lucide-react';
import { StatCard } from '../../../shared/components';
import {
  useOpportunitiesStats,
  useSubscriptionsStats,
  useProvisions,
} from '../hooks';

export function CommercialStatsCards() {
  const { data: oppStats, isLoading: oppLoading } = useOpportunitiesStats();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard
        Icon={TrendingUp}
        iconColor="blue"
        label="Total Opportunités"
        value={oppStats?.total_opportunities || 0}
        loading={oppLoading}
      />
      <StatCard
        Icon={Calendar}
        iconColor="blue"
        label="Ce Mois"
        value={oppStats?.opportunities_this_month || 0}
        trend="+12%"
        trendType="up"
        loading={oppLoading}
      />
      <StatCard
        Icon={DollarSign}
        iconColor="green"
        label="Revenue Prévu"
        value={
          oppStats?.revenue_forecast
            ? `${oppStats.revenue_forecast.toLocaleString()} DT`
            : '0 DT'
        }
        trend="+15K"
        trendType="up"
        loading={oppLoading}
      />
      <StatCard
        Icon={CheckCircle2}
        iconColor="green"
        label="Taux Conversion"
        value={oppStats?.conversion_rate ? `${(oppStats.conversion_rate * 100).toFixed(0)}%` : '0%'}
        trend="+5%"
        trendType="up"
        loading={oppLoading}
      />
    </div>
  );
}

export function FinanceStatsCards() {
  const { data: oppStats, isLoading: oppLoading } = useOpportunitiesStats();

  const toApprove = oppStats?.by_status?.CLIENT_PO_RECIEVED || 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard
        Icon={AlertTriangle}
        iconColor={toApprove > 0 ? 'amber' : 'gray'}
        label="À Approuver"
        value={toApprove}
        badge={toApprove > 0 ? 'URGENT' : undefined}
        badgeColor="red"
        loading={oppLoading}
      />
      <StatCard
        Icon={DollarSign}
        iconColor="green"
        label="Revenue Ce Mois"
        value={
          oppStats?.revenue_confirmed
            ? `${oppStats.revenue_confirmed.toLocaleString()} DT`
            : '0 DT'
        }
        trend="+8K"
        trendType="up"
        loading={oppLoading}
      />
      <StatCard
        Icon={BarChart3}
        iconColor="blue"
        label="Revenue YTD"
        value="450K DT"
        trend="+120K"
        trendType="up"
        loading={oppLoading}
      />
      <StatCard
        Icon={TrendingUp}
        iconColor="green"
        label="Marge Moyenne"
        value="32%"
        trend="+2%"
        trendType="up"
        loading={oppLoading}
      />
    </div>
  );
}

export function TechStatsCards() {
  const { data: waitingData,    isLoading: waitingLoading    } = useProvisions({ status: 'WAITING_PROVISION', page_size: 1 });
  const { data: inProgressData, isLoading: inProgressLoading } = useProvisions({ status: 'PROVISIONING',      page_size: 1 });

  const waitingCount    = waitingData?.count ?? 0;
  const inProgressCount = inProgressData?.count ?? 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <StatCard
        Icon={AlertTriangle}
        iconColor={waitingCount > 0 ? 'amber' : 'gray'}
        label="En Attente"
        value={waitingCount}
        badge={waitingCount > 0 ? 'ACTION' : undefined}
        badgeColor="red"
        loading={waitingLoading}
      />
      <StatCard
        Icon={RefreshCw}
        iconColor="blue"
        label="En Cours"
        value={inProgressCount}
        loading={inProgressLoading}
      />
      <StatCard
        Icon={CheckCircle2}
        iconColor="green"
        label="Ce Mois"
        value="—"
        loading={false}
      />
    </div>
  );
}
