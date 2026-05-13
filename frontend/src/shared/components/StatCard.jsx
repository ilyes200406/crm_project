import React from 'react';

/**
 * @param {React.ComponentType} Icon - Lucide icon component
 * @param {string} iconColor - 'blue' | 'green' | 'amber' | 'red' | 'purple' | 'gray'
 * @param {string} label
 * @param {string|number} value
 * @param {string} [trend]
 * @param {'up'|'down'|'neutral'} [trendType]
 * @param {string} [badge]
 * @param {'red'|'orange'|'yellow'|'green'|'blue'|'gray'} [badgeColor]
 * @param {Function} [onClick]
 * @param {boolean} [loading]
 */
export function StatCard({
  Icon,
  iconColor = 'blue',
  label,
  value,
  trend,
  trendType = 'neutral',
  badge,
  badgeColor = 'gray',
  onClick,
  loading = false,
}) {
  const iconBg = {
    blue:   'bg-blue-50',
    green:  'bg-green-50',
    amber:  'bg-amber-50',
    red:    'bg-red-50',
    purple: 'bg-purple-50',
    gray:   'bg-gray-100',
  };
  const iconFg = {
    blue:   'text-blue-600',
    green:  'text-green-600',
    amber:  'text-amber-600',
    red:    'text-red-600',
    purple: 'text-purple-600',
    gray:   'text-gray-500',
  };

  const trendColors = {
    up:      'text-green-600',
    down:    'text-red-600',
    neutral: 'text-gray-500',
  };

  const badgeColors = {
    red:    'bg-red-100 text-red-800',
    orange: 'bg-orange-100 text-orange-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    green:  'bg-green-100 text-green-800',
    blue:   'bg-blue-100 text-blue-800',
    gray:   'bg-gray-100 text-gray-800',
  };

  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-xl border border-gray-200 p-5 shadow-sm ${
        onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        {Icon && (
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${iconBg[iconColor]}`}>
            <Icon size={20} className={iconFg[iconColor]} />
          </div>
        )}
        {badge && (
          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${badgeColors[badgeColor]}`}>
            {badge}
          </span>
        )}
      </div>

      {/* Label */}
      <div className="text-sm font-medium text-gray-500 mb-1">{label}</div>

      {/* Value */}
      {loading ? (
        <div className="h-8 bg-gray-200 rounded animate-pulse mb-2" />
      ) : (
        <div className="text-2xl font-bold text-gray-900 mb-1">{value}</div>
      )}

      {/* Trend */}
      {trend && !loading && (
        <div className={`text-xs font-semibold ${trendColors[trendType]}`}>{trend}</div>
      )}
    </div>
  );
}
