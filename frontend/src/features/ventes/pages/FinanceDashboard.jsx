/**
 * FINANCE DASHBOARD
 * 
 * Dashboard principal pour le rôle FINANCE
 */

import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

import { Briefcase, DollarSign, BarChart3 } from 'lucide-react';

import { Card } from '../../../shared/components';
import {
  FinanceStatsCards,
  OpportunitiesApprovalWidget,
} from '../components';
import {
  useRevenueChart,
  useSubscriptionsStats,
} from '../hooks';

export function FinanceDashboard() {
  // Fetch revenue chart (12 months)
  const { data: revenueData, isLoading: revenueLoading } = useRevenueChart(12);

  // Fetch subscriptions stats
  const { data: subStats, isLoading: subStatsLoading } = useSubscriptionsStats();

  // Prepare subscriptions pie chart data
  const subscriptionsPieData = subStats
    ? [
        { name: 'Actives', value: subStats.active, color: '#10b981' },
        { name: 'Pending Renewal', value: subStats.pending_renewal, color: '#f59e0b' },
        { name: 'Expirées', value: subStats.expired, color: '#ef4444' },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center">
            <Briefcase size={18} className="text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard Finance</h1>
            <p className="text-sm text-gray-500">Approbations, revenue et marges</p>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <FinanceStatsCards />

      {/* Row 1: Opportunities to Approve (Full width) */}
      <OpportunitiesApprovalWidget />

      {/* Row 2: Revenue Chart + Subscriptions Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Monthly Chart */}
        <Card title={<span className="flex items-center gap-2"><DollarSign size={16} className="text-green-500" />Revenue Mensuel (12 mois)</span>}>
          {revenueLoading ? (
            <div className="h-80 bg-gray-200 rounded animate-pulse" />
          ) : (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={revenueData || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="month_display"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  tick={{ fontSize: 12 }}
                />
                <YAxis />
                <Tooltip
                  formatter={(value) => `${value.toLocaleString()} DT`}
                />
                <Legend />
                <Bar dataKey="revenue" fill="#3b82f6" name="Revenue" />
              </BarChart>
            </ResponsiveContainer>
          )}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-blue-500 rounded" />
                <span className="text-gray-600">Initial</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded" />
                <span className="text-gray-600">Renewal</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-purple-500 rounded" />
                <span className="text-gray-600">Upsell</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Subscriptions Overview */}
        <Card title={<span className="flex items-center gap-2"><BarChart3 size={16} className="text-blue-500" />Subscriptions Overview</span>}>
          {subStatsLoading ? (
            <div className="h-80 bg-gray-200 rounded animate-pulse" />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={subscriptionsPieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {subscriptionsPieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>

              {/* Stats summary */}
              <div className="mt-4 pt-4 border-t border-gray-200 space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span className="flex items-center gap-1.5 text-gray-600"><span className="w-2 h-2 rounded-full bg-green-500 inline-block" />Actives</span>
                  <span className="font-semibold">{subStats?.active || 0}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="flex items-center gap-1.5 text-gray-600"><span className="w-2 h-2 rounded-full bg-orange-500 inline-block" />Pending Renewal</span>
                  <span className="font-semibold">{subStats?.pending_renewal || 0}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="flex items-center gap-1.5 text-gray-600"><span className="w-2 h-2 rounded-full bg-red-500 inline-block" />Expirées</span>
                  <span className="font-semibold">{subStats?.expired || 0}</span>
                </div>
                <div className="flex justify-between text-sm pt-2 border-t border-gray-200">
                  <span className="text-gray-600 font-medium">Total:</span>
                  <span className="font-bold">{subStats?.total || 0}</span>
                </div>
              </div>
            </>
          )}
        </Card>
      </div>

    </div>
  );
}