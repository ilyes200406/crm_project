/**
 * TECH DASHBOARD
 * 
 * Dashboard principal pour le rôle TECHNICIEN
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

import { Card, Badge } from '../../../shared/components';
import {
  TechStatsCards,
  ProvisionsWidget,
  ProvisionsInProgressWidget,
} from '../components';
import { useProvisions } from '../hooks';

export function TechDashboard() {
  const navigate = useNavigate();

  // Fetch completed provisions (last 10)
  const { data: completedProvisions, isLoading: completedLoading } = useProvisions({
    status: 'PROVISIONED',
    limit: 10,
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">🔧 Dashboard Technicien</h1>
        <p className="text-sm text-gray-600 mt-1">
          Gestion des provisions et provisioning
        </p>
      </div>

      {/* Stats Cards */}
      <TechStatsCards />

      {/* Row 1: Provisions Waiting */}
      <ProvisionsWidget status="WAITING_PROVISION" limit={10} />

      {/* Row 2: Provisions In Progress */}
      <ProvisionsInProgressWidget />

      {/* Row 3: Timeline Provisioning */}
      <Card title="📊 Timeline Provisioning (10 dernières)">
        {completedLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, idx) => (
              <div key={idx} className="h-16 bg-gray-200 rounded animate-pulse" />
            ))}
          </div>
        ) : !completedProvisions?.results || completedProvisions.results.length === 0 ? (
          <div className="text-center py-8 text-gray-500 text-sm">
            Aucune provision complétée récemment
          </div>
        ) : (
          <div className="space-y-3">
            {completedProvisions.results.map((provision) => {
              const opp = provision.opportunity_line?.opportunity;
              const product = provision.opportunity_line?.product;

              // Calculate provisioning time
              const startTime = new Date(provision.started_at);
              const endTime = new Date(provision.provisioned_at);
              const durationMinutes = Math.round((endTime - startTime) / (1000 * 60));

              return (
                <div
                  key={provision.id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/provisions/${provision.id}`)}
                >
                  {/* Left: Status + Info */}
                  <div className="flex items-center gap-4">
                    <div className="text-2xl">✅</div>
                    <div>
                      <div className="font-semibold text-gray-900">
                        {opp?.reference || '-'} - {opp?.client?.name || '-'}
                      </div>
                      <div className="text-sm text-gray-600">
                        {product?.title || '-'}
                      </div>
                    </div>
                  </div>

                  {/* Right: Time info */}
                  <div className="text-right">
                    <div className="text-sm text-gray-900">
                      {formatDistanceToNow(endTime, {
                        addSuffix: true,
                        locale: fr,
                      })}
                    </div>
                    <div className="text-xs text-gray-500">
                      Temps: {durationMinutes} min
                    </div>
                  </div>
                </div>
              );
            })}

            {/* Average time */}
            {completedProvisions.results.length > 0 && (
              <div className="pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">⏱️ Temps moyen provisioning:</span>
                  <span className="font-semibold text-gray-900">
                    {calculateAverageTime(completedProvisions.results)} min
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

/**
 * Calculate average provisioning time
 */
function calculateAverageTime(provisions) {
  if (!provisions || provisions.length === 0) return 0;

  const totalMinutes = provisions.reduce((sum, provision) => {
    const startTime = new Date(provision.started_at);
    const endTime = new Date(provision.provisioned_at);
    const durationMinutes = Math.round((endTime - startTime) / (1000 * 60));
    return sum + durationMinutes;
  }, 0);

  return Math.round(totalMinutes / provisions.length);
}