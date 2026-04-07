/**
 * PRODUCT CARD COMPONENT
 * 
 * Card display for product information (avec link supplier)
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '../../../../shared/components';

/**
 * ProductCard Component
 * 
 * @param {Object} props
 * @param {Object} props.product - Product data
 */
export function ProductCard({ product }) {
  const navigate = useNavigate();

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-xl font-bold text-gray-900 mb-1">
            {product.title}
            {product.version && (
              <span className="ml-2 text-base font-normal text-gray-600">
                {product.version}
              </span>
            )}
          </h3>
          <div className="text-sm text-gray-600">
            {product.category_display || product.category}
          </div>
        </div>
        <div className="flex flex-col gap-2">
          <Badge 
            variant={product.is_active ? 'green' : 'red'}
          >
            {product.is_active ? 'Actif' : 'Inactif'}
          </Badge>
          {product.is_deprecated && (
            <Badge variant="yellow" size="sm">
              Obsolète
            </Badge>
          )}
        </div>
      </div>

      {/* Details */}
      <div className="space-y-3">
        {/* SKU */}
        {product.sku && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 text-sm font-medium">SKU:</span>
            <span className="text-sm text-gray-700 font-mono">{product.sku}</span>
          </div>
        )}

        {/* Publisher */}
        {product.publisher && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 text-sm font-medium">Éditeur:</span>
            <span className="text-sm text-gray-700">{product.publisher}</span>
          </div>
        )}

        {/* Supplier - CLICKABLE */}
        {product.supplier && (
          <div className="pt-3 border-t border-gray-200">
            <div className="text-xs text-gray-500 mb-2">Fournisseur</div>
            <button
              onClick={() => navigate(`/app/catalogue/suppliers/${product.supplier.id}`)}
              className="w-full text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors group"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-gray-900 group-hover:text-blue-600">
                    📦 {product.supplier.name}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">
                    {product.supplier.type_display || product.supplier.type}
                  </div>
                </div>
                <div className="text-gray-400 group-hover:text-blue-600">
                  →
                </div>
              </div>
            </button>
          </div>
        )}

        {/* Description technique */}
        {product.description_technique && (
          <div className="pt-3 border-t border-gray-200">
            <div className="text-sm text-gray-500 mb-1">Description technique</div>
            <p className="text-sm text-gray-700 line-clamp-3">
              {product.description_technique}
            </p>
          </div>
        )}

        {/* Description commerciale */}
        {product.description_commerciale && (
          <div className="pt-3 border-t border-gray-200">
            <div className="text-sm text-gray-500 mb-1">Description commerciale</div>
            <p className="text-sm text-gray-700 line-clamp-3">
              {product.description_commerciale}
            </p>
          </div>
        )}
      </div>

      {/* Successor (si obsolète) */}
      {product.successor && (
        <div className="mt-4 pt-4 border-t border-yellow-200 bg-yellow-50 -mx-6 -mb-6 px-6 py-3 rounded-b-lg">
          <div className="flex items-start gap-2">
            <span className="text-yellow-600">⚠️</span>
            <div className="flex-1">
              <div className="text-sm font-medium text-yellow-900">
                Produit obsolète
              </div>
              <div className="text-xs text-yellow-700 mt-1">
                Remplacé par: {product.successor.title}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}