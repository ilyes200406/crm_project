/**
 * DATA TABLE COMPONENT
 * 
 * Table générique avec tri, pagination et actions
 */

import React from 'react';

/**
 * DataTable Component
 * 
 * @param {Object} props
 * @param {Array} props.columns - Column definitions
 * @param {Array} props.data - Table data
 * @param {Function} props.onRowClick - Row click handler (optional)
 * @param {boolean} props.loading - Loading state (optional)
 * @param {Object} props.emptyState - Empty state config (optional)
 * @param {boolean} props.striped - Striped rows (optional)
 */
export function DataTable({
  columns,
  data,
  onRowClick,
  loading = false,
  emptyState,
  striped = true,
}) {
  // Loading skeleton
  if (loading) {
    return (
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {[...Array(5)].map((_, idx) => (
              <tr key={idx}>
                {columns.map((_, colIdx) => (
                  <td key={colIdx} className="px-6 py-4">
                    <div className="h-4 bg-gray-200 rounded animate-pulse" />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  // Empty state
  if (!data || data.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-sm">
          {emptyState?.message || 'Aucune donnée'}
        </p>
        {emptyState?.action && (
          <button
            onClick={emptyState.action.onClick}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
          >
            {emptyState.action.label}
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        {/* Header */}
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col, idx) => (
              <th
                key={idx}
                className={`
                  px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider
                  ${col.className || ''}
                `}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>

        {/* Body */}
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((row, rowIdx) => (
            <tr
              key={rowIdx}
              onClick={() => onRowClick?.(row)}
              className={`
                ${onRowClick ? 'cursor-pointer hover:bg-gray-50' : ''}
                ${striped && rowIdx % 2 === 1 ? 'bg-gray-50' : 'bg-white'}
              `}
            >
              {columns.map((col, colIdx) => (
                <td
                  key={colIdx}
                  className={`px-6 py-4 whitespace-nowrap ${col.cellClassName || ''}`}
                >
                  {col.render ? col.render(row) : row[col.accessor]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}