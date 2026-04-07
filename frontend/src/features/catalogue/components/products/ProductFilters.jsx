/**
 * PRODUCT FILTERS COMPONENT
 *
 * Filters for products list
 */

import React from 'react';

import { Card } from '../../../../shared/components';

/**
 * ProductFilters Component
 *
 * @param {Object} props
 * @param {string} props.search - Search value
 * @param {Function} props.onSearchChange - Search change handler
 * @param {string} props.category - Category filter
 * @param {Function} props.onCategoryChange - Category change handler
 * @param {Array} props.categories - Categories list
 */
export function ProductFilters({
  search,
  onSearchChange,
  category,
  onCategoryChange,
  categories = [],
}) {
  return (
    <Card>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Search */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Recherche
          </label>
          <input
            type="text"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Nom, SKU..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Category Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Catégorie
          </label>
          <select
            value={category}
            onChange={(e) => onCategoryChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Toutes</option>
            {categories.map((cat) => (
              <option key={cat.value || cat} value={cat.value || cat}>
                {cat.label || cat}
              </option>
            ))}
          </select>
        </div>
      </div>
    </Card>
  );
}
