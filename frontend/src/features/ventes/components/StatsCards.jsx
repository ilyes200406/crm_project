/**
 * STATS CARDS COMPONENTS
 * 
 * Cartes de statistiques pour les dashboards
 */

import React from 'react';
import { StatCard } from '../../../shared/components';
import {
  useOpportunitiesStats,
  useSubscriptionsStats,
  useProvisions,
} from '../hooks';

/**
 * Commercial Stats Cards
 */
export function CommercialStatsCards() {
  const { data: oppStats, isLoading: oppLoading } = useOpportunitiesStats();
  const { data: subStats, isLoading: subLoading } = useSubscriptionsStats();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {/* Total Opportunities */}
      <StatCard
        icon="📈"
        label="Total Opportunités"
        value={oppStats?.total_opportunities || 0}
        loading={oppLoading}
      />

      {/* This Month */}
      <StatCard
        icon="📅"
        label="Ce Mois"
        value={oppStats?.opportunities_this_month || 0}
        trend="+12%"
        trendType="up"
        loading={oppLoading}
      />

      {/* Revenue Forecast */}
      <StatCard
        icon="💰"
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

      {/* Conversion Rate */}
      <StatCard
        icon="✅"
        label="Taux Conversion"
        value={oppStats?.conversion_rate ? `${(oppStats.conversion_rate * 100).toFixed(0)}%` : '0%'}
        trend="+5%"
        trendType="up"
        loading={oppLoading}
      />
    </div>
  );
}

/**
 * Finance Stats Cards
 */
export function FinanceStatsCards() {
  const { data: oppStats, isLoading: oppLoading } = useOpportunitiesStats();
  const { data: subStats, isLoading: subLoading } = useSubscriptionsStats();

  // Count opportunities waiting approval
  const toApprove = oppStats?.by_status?.CLIENT_PO_RECIEVED || 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {/* To Approve */}
      <StatCard
        icon="⚠️"
        label="À Approuver"
        value={toApprove}
        badge={toApprove > 0 ? 'URGENT' : undefined}
        badgeColor="red"
        loading={oppLoading}
      />

      {/* Revenue This Month */}
      <StatCard
        icon="💰"
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

      {/* Revenue YTD */}
      <StatCard
        icon="📊"
        label="Revenue YTD"
        value="450K DT"
        trend="+120K"
        trendType="up"
        loading={oppLoading}
      />

      {/* Average Margin */}
      <StatCard
        icon="📈"
        label="Marge Moyenne"
        value="32%"
        trend="+2%"
        trendType="up"
        loading={oppLoading}
      />
    </div>
  );
}

/**
 * Tech Stats Cards
 */
export function TechStatsCards() {
  const { data: waitingData, isLoading: waitingLoading } = useProvisions({ status: 'WAITING_PROVISION', page_size: 1 });
  const { data: inProgressData, isLoading: inProgressLoading } = useProvisions({ status: 'PROVISIONING', page_size: 1 });

  const waitingCount    = waitingData?.count ?? 0;
  const inProgressCount = inProgressData?.count ?? 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Waiting */}
      <StatCard
        icon="⚠️"
        label="En Attente"
        value={waitingCount}
        badge={waitingCount > 0 ? 'ACTION' : undefined}
        badgeColor="red"
        loading={waitingLoading}
      />

      {/* In Progress */}
      <StatCard
        icon="🔄"
        label="En Cours"
        value={inProgressCount}
        loading={inProgressLoading}
      />

      {/* This Month — no filter endpoint yet, keep static */}
      <StatCard
        icon="✅"
        label="Ce Mois"
        value="—"
        loading={false}
      />
    </div>
  );
}