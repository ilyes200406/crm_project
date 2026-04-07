/**
 * STAT CARD COMPONENT
 * 
 * Carte de statistique avec icône, valeur, label et variation
 */

import React from 'react';

/**
 * StatCard Component
 * 
 * @param {Object} props
 * @param {string} props.icon - Emoji icon
 * @param {string} props.label - Stat label
 * @param {string|number} props.value - Main value
 * @param {string} props.trend - Trend text (optional)
 * @param {string} props.trendType - Trend type: 'up', 'down', 'neutral' (optional)
 * @param {string} props.badge - Badge text (optional)
 * @param {string} props.badgeColor - Badge color: 'red', 'orange', 'yellow', 'green', 'blue', 'gray' (optional)
 * @param {Function} props.onClick - Click handler (optional)
 * @param {boolean} props.loading - Loading state (optional)
 */
export function StatCard({
  icon,
  label,
  value,
  trend,
  trendType = 'neutral',
  badge,
  badgeColor = 'gray',
  onClick,
  loading = false,
}) {
  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-600',
  };

  const badgeColors = {
    red: 'bg-red-100 text-red-800',
    orange: 'bg-orange-100 text-orange-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    green: 'bg-green-100 text-green-800',
    blue: 'bg-blue-100 text-blue-800',
    gray: 'bg-gray-100 text-gray-800',
  };

  return (
    <div
      onClick={onClick}
      className={`
        bg-white rounded-lg border border-gray-200 p-6 shadow-sm
        ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="text-3xl">{icon}</div>
        {badge && (
          <span
            className={`
              px-2 py-1 text-xs font-semibold rounded-full
              ${badgeColors[badgeColor]}
            `}
          >
            {badge}
          </span>
        )}
      </div>

      {/* Label */}
      <div className="text-sm font-medium text-gray-600 mb-1">{label}</div>

      {/* Value */}
      {loading ? (
        <div className="h-8 bg-gray-200 rounded animate-pulse mb-2" />
      ) : (
        <div className="text-2xl font-bold text-gray-900 mb-2">{value}</div>
      )}

      {/* Trend */}
      {trend && !loading && (
        <div className={`text-sm font-medium ${trendColors[trendType]}`}>
          {trend}
        </div>
      )}
    </div>
  );
}