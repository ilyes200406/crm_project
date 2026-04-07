/**
 * COMMERCIAL DASHBOARD
 * 
 * Dashboard principal pour le rôle COMMERCIAL
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

import { Card } from '../../../shared/components';
import {
  CommercialStatsCards,
  OpportunitiesWidget,
  SubscriptionsExpiringWidget,
} from '../components';
import {
  useOpportunitiesPipeline,
  useRevenueChart,
} from '../hooks';

export function CommercialDashboard() {
  const navigate = useNavigate();

  // Fetch pipeline data
  const { data: pipelineData, isLoading: pipelineLoading } = useOpportunitiesPipeline();

  // Fetch revenue chart data
  const { data: revenueData, isLoading: revenueLoading } = useRevenueChart(6);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">📊 Dashboard Commercial</h1>
          <p className="text-sm text-gray-600 mt-1">
            Vue d'ensemble de vos opportunités et subscriptions
          </p>
        </div>
        <button
          onClick={() => navigate('/ventes/opportunities/new')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
        >
          + Nouvelle Opportunité
        </button>
      </div>

      {/* Stats Cards */}
      <CommercialStatsCards />

      {/* Row 1: Opportunities + Subscriptions Expiring */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Opportunities Widget */}
        <OpportunitiesWidget
          title="Mes Opportunités Actives"
          params={{ status__ne: 'CANCELLED' }}
          limit={5}
        />

        {/* Subscriptions Expiring Widget */}
        <SubscriptionsExpiringWidget days={30} limit={5} />
      </div>

      {/* Row 2: Pipeline Chart + Revenue Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pipeline Chart */}
        <Card title="📊 Pipeline">
          {pipelineLoading ? (
            <div className="h-80 bg-gray-200 rounded animate-pulse" />
          ) : (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={pipelineData || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="status_display"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  tick={{ fontSize: 12 }}
                />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#3b82f6" name="Opportunités" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        {/* Revenue Chart */}
        <Card title="💰 Revenue (6 mois)">
          {revenueLoading ? (
            <div className="h-80 bg-gray-200 rounded animate-pulse" />
          ) : (
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={revenueData || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="month_display"
                  tick={{ fontSize: 12 }}
                />
                <YAxis />
                <Tooltip
                  formatter={(value) => `${value.toLocaleString()} DT`}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.6}
                  name="Revenue"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      {/* Row 3: Activities */}
      <Card title="🕐 Activités Récentes">
        <div className="space-y-4">
          {/* Recent activities - Placeholder for now */}
          <ActivityItem
            icon="📝"
            title="OPP-001 créée"
            description="Migration Office 365 ACME"
            time="Il y a 5 min"
          />
          <ActivityItem
            icon="📧"
            title="BC client uploadé"
            description="OPP-002 - TechCo"
            time="Il y a 2h"
          />
          <ActivityItem
            icon="✅"
            title="Provisioning complété"
            description="SUB-MS-001 - ACME Office 365"
            time="Hier"
          />
          <ActivityItem
            icon="🔄"
            title="Renewal créé"
            description="OPP-015 - BigCorp Dynamics 365"
            time="Il y a 2 jours"
          />
          <ActivityItem
            icon="📊"
            title="Devis client envoyé"
            description="OPP-003 - StartUp"
            time="Il y a 3 jours"
          />
        </div>
      </Card>
    </div>
  );
}

/**
 * Activity Item Component
 */
function ActivityItem({ icon, title, description, time }) {
  return (
    <div className="flex items-start gap-3 pb-4 border-b border-gray-200 last:border-0 last:pb-0">
      <div className="text-2xl">{icon}</div>
      <div className="flex-1">
        <div className="font-medium text-gray-900">{title}</div>
        <div className="text-sm text-gray-600">{description}</div>
      </div>
      <div className="text-xs text-gray-500">{time}</div>
    </div>
  );
}