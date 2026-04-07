/**
 * SUPPLIER FILTERS COMPONENT
 * 
 * Filters for suppliers list
 */

import React from 'react';

import { Card } from '../../../../shared/components';

/**
 * SupplierFilters Component
 * 
 * @param {Object} props
 * @param {string} props.search - Search value
 * @param {Function} props.onSearchChange - Search change handler
 * @param {string} props.type - Type filter
 * @param {Function} props.onTypeChange - Type change handler
 * @param {string} props.isActive - Active filter
 * @param {Function} props.onIsActiveChange - Active change handler
 */
export function SupplierFilters({
  search,
  onSearchChange,
  type,
  onTypeChange,
  isActive,
  onIsActiveChange,
}) {
  return (
    <Card>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Search */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Recherche
          </label>
          <input
            type="text"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Nom, email..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Type Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Type
          </label>
          <select
            value={type}
            onChange={(e) => onTypeChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Tous</option>
            <option value="DIRECT">Direct (Microsoft)</option>
            <option value="DISTRIBUTOR">Distributeur</option>
            <option value="RESELLER">Revendeur</option>
          </select>
        </div>

        {/* Status Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Statut
          </label>
          <select
            value={isActive}
            onChange={(e) => onIsActiveChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Tous</option>
            <option value="true">Actifs</option>
            <option value="false">Inactifs</option>
          </select>
        </div>
      </div>
    </Card>
  );
}