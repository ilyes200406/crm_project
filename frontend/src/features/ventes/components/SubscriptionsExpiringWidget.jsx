/**
 * SUBSCRIPTIONS EXPIRING WIDGET
 * 
 * Widget affichant les subscriptions expirant bientôt
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

import { Card, Badge, EmptyStates } from '../../../shared/components';
import { useExpiringSubscriptions } from '../hooks';

/**
 * SubscriptionsExpiringWidget Component
 * 
 * @param {Object} props
 * @param {number} props.days - Days threshold (default: 30)
 * @param {number} props.limit - Number of items to display (default: 5)
 */
export function SubscriptionsExpiringWidget({ days = 30, limit = 5 }) {
  const navigate = useNavigate();

  // Fetch expiring subscriptions
  const { data, isLoading } = useExpiringSubscriptions(days, { limit });

  // Get urgency level based on days remaining
  const getUrgencyConfig = (endDate) => {
    const daysRemaining = Math.ceil(
      (new Date(endDate) - new Date()) / (1000 * 60 * 60 * 24)
    );

    if (daysRemaining <= 7) {
      return { variant: 'red', icon: '🔴', label: `${daysRemaining}j restants` };
    } else if (daysRemaining <= 15) {
      return { variant: 'orange', icon: '🟠', label: `${daysRemaining}j restants` };
    } else {
      return { variant: 'yellow', icon: '🟡', label: `${daysRemaining}j restants` };
    }
  };

  // Handle create renewal
  const handleCreateRenewal = (subscription) => {
    navigate(`/app/ventes/subscriptions/${subscription.id}`);
  };

  // Loading state
  if (isLoading) {
    return (
      <Card title="⚠️ Subscriptions Expirant (30j)">
        <div className="space-y-4">
          {[...Array(3)].map((_, idx) => (
            <div key={idx} className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded mb-2" />
              <div className="h-3 bg-gray-200 rounded w-3/4" />
            </div>
          ))}
        </div>
      </Card>
    );
  }

  // Empty state
  if (!data?.results || data.results.length === 0) {
    return (
      <Card title="⚠️ Subscriptions Expirant (30j)">
        <EmptyStates.NoSubscriptions />
      </Card>
    );
  }

  return (
    <Card
      title="⚠️ Subscriptions Expirant (30j)"
      footer={
        <button
          onClick={() => navigate('/ventes?tab=subscriptions&filter=expiring')}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          Voir tout ({data.count || 0}) →
        </button>
      }
    >
      <div className="space-y-4">
        {data.results.map((subscription) => {
          const urgency = getUrgencyConfig(subscription.current_term?.end_date);

          return (
            <div
              key={subscription.id}
              className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
              onClick={() => navigate(`/ventes/subscriptions/${subscription.id}`)}
            >
              {/* Urgency badge */}
              <div className="flex items-center justify-between mb-2">
                <Badge variant={urgency.variant} icon={urgency.icon} size="sm">
                  {urgency.label}
                </Badge>
              </div>

              {/* Product info */}
              <div className="mb-2">
                <div className="font-semibold text-gray-900">
                  {subscription.product?.title || 'Produit inconnu'}
                </div>
                <div className="text-sm text-gray-600">
                  {subscription.client?.name || 'Client inconnu'}
                </div>
              </div>

              {/* Subscription number */}
              <div className="text-xs text-gray-500 mb-3">
                {subscription.subscription_number}
              </div>

              {/* Action button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleCreateRenewal(subscription);
                }}
                className="w-full px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 font-medium"
              >
                🔄 Créer Renewal
              </button>
            </div>
          );
        })}
      </div>
    </Card>
  );
}