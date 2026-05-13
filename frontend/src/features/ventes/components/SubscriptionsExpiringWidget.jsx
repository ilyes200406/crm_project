import React from 'react';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import { AlertTriangle, RefreshCw, ChevronRight } from 'lucide-react';

import { Card, Badge, EmptyStates } from '../../../shared/components';
import { useExpiringSubscriptions } from '../hooks';

export function SubscriptionsExpiringWidget({ days = 30, limit = 5 }) {
  const navigate = useNavigate();

  const { data, isLoading } = useExpiringSubscriptions(days, { limit });

  const getUrgencyConfig = (endDate) => {
    const daysRemaining = Math.ceil(
      (new Date(endDate) - new Date()) / (1000 * 60 * 60 * 24)
    );

    if (daysRemaining <= 7) {
      return { variant: 'red',    dotClass: 'bg-red-500',    label: `${daysRemaining}j restants` };
    } else if (daysRemaining <= 15) {
      return { variant: 'orange', dotClass: 'bg-orange-500', label: `${daysRemaining}j restants` };
    } else {
      return { variant: 'yellow', dotClass: 'bg-yellow-500', label: `${daysRemaining}j restants` };
    }
  };

  const cardTitle = (
    <span className="flex items-center gap-2">
      <AlertTriangle size={16} className="text-amber-500 shrink-0" />
      Abonnements Expirant ({days}j)
    </span>
  );

  if (isLoading) {
    return (
      <Card title={cardTitle}>
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

  if (!data?.results || data.results.length === 0) {
    return (
      <Card title={cardTitle}>
        <EmptyStates.NoSubscriptions />
      </Card>
    );
  }

  return (
    <Card
      title={cardTitle}
      footer={
        <button
          onClick={() => navigate('/ventes?tab=subscriptions&filter=expiring')}
          className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          Voir tout ({data.count || 0})
          <ChevronRight size={14} />
        </button>
      }
    >
      <div className="space-y-3">
        {data.results.map((subscription) => {
          const urgency = getUrgencyConfig(subscription.current_term?.end_date);

          return (
            <div
              key={subscription.id}
              className="border border-gray-200 rounded-xl p-4 hover:bg-gray-50 cursor-pointer transition-colors"
              onClick={() => navigate(`/ventes/subscriptions/${subscription.id}`)}
            >
              {/* Urgency badge with CSS dot */}
              <div className="flex items-center justify-between mb-2">
                <Badge
                  variant={urgency.variant}
                  icon={<span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${urgency.dotClass}`} />}
                  size="sm"
                >
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

              <div className="text-xs text-gray-500 mb-3">
                {subscription.subscription_number}
              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/app/ventes/subscriptions/${subscription.id}`);
                }}
                className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
              >
                <RefreshCw size={13} />
                Créer Renewal
              </button>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
