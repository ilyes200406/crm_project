/**
 * SUPPLIER CARD COMPONENT
 * 
 * Card display for supplier information
 */

import React from 'react';
import { Badge } from '../../../../shared/components';

/**
 * SupplierCard Component
 * 
 * @param {Object} props
 * @param {Object} props.supplier - Supplier data
 */
export function SupplierCard({ supplier }) {
  // Get type badge variant
  const getTypeBadgeVariant = (type) => {
    const variants = {
      DIRECT: 'blue',
      DISTRIBUTOR: 'purple',
      RESELLER: 'green',
    };
    return variants[type] || 'gray';
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-xl font-bold text-gray-900 mb-2">
            {supplier.name}
          </h3>
          <Badge variant={getTypeBadgeVariant(supplier.type)}>
            {supplier.type_display || supplier.type}
          </Badge>
        </div>
        <Badge variant={supplier.is_active ? 'green' : 'red'}>
          {supplier.is_active ? 'Actif' : 'Inactif'}
        </Badge>
      </div>

      {/* Contact Info */}
      <div className="space-y-3">
        {/* Website */}
        {supplier.website && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 text-sm">🌐</span>
            <a
              href={supplier.website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:underline"
            >
              {supplier.website}
            </a>
          </div>
        )}

        {/* Email */}
        {supplier.support_email && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 text-sm">📧</span>
            <a
              href={`mailto:${supplier.support_email}`}
              className="text-sm text-blue-600 hover:underline"
            >
              {supplier.support_email}
            </a>
          </div>
        )}

        {/* Phone */}
        {supplier.support_phone && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 text-sm">📞</span>
            <a
              href={`tel:${supplier.support_phone}`}
              className="text-sm text-gray-700"
            >
              {supplier.support_phone}
            </a>
          </div>
        )}
      </div>

      {/* Notes */}
      {supplier.notes && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="text-sm text-gray-500 mb-1">Notes</div>
          <p className="text-sm text-gray-700">{supplier.notes}</p>
        </div>
      )}

      {/* Dates */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-4 text-xs text-gray-500">
          <div>
            <div>Créé le</div>
            <div className="text-gray-700 mt-1">
              {new Date(supplier.created_at).toLocaleDateString('fr-FR')}
            </div>
          </div>
          {supplier.updated_at && (
            <div>
              <div>Modifié le</div>
              <div className="text-gray-700 mt-1">
                {new Date(supplier.updated_at).toLocaleDateString('fr-FR')}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}