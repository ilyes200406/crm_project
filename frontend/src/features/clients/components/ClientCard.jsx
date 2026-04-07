/**
 * CLIENT CARD COMPONENT
 * 
 * Card display for client information
 */

import React from 'react';
import { Badge } from '../../../shared/components';

/**
 * ClientCard Component
 * 
 * @param {Object} props
 * @param {Object} props.client - Client data
 */
export function ClientCard({ client }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-xl font-bold text-gray-900 mb-1">
            {client.company_name}
          </h3>
          <div className="text-sm text-gray-600">
            {client.industry_display || client.industry}
          </div>
        </div>
        <Badge variant={client.is_active ? 'green' : 'red'}>
          {client.is_active ? 'Actif' : 'Inactif'}
        </Badge>
      </div>

      {/* Contact Info */}
      <div className="space-y-3">
        {/* Email */}
        {client.email && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 text-sm">📧</span>
            <a
              href={`mailto:${client.email}`}
              className="text-sm text-blue-600 hover:underline"
            >
              {client.email}
            </a>
          </div>
        )}

        {/* Phone */}
        {client.phone && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 text-sm">📞</span>
            <a
              href={`tel:${client.phone}`}
              className="text-sm text-gray-700"
            >
              {client.phone}
            </a>
          </div>
        )}

        {/* Website */}
        {client.website && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 text-sm">🌐</span>
            <a
              href={client.website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:underline"
            >
              {client.website}
            </a>
          </div>
        )}

        {/* Address */}
        {client.address && (
          <div className="flex items-start gap-2">
            <span className="text-gray-500 text-sm">📍</span>
            <div className="text-sm text-gray-700">
              {client.address}
            </div>
          </div>
        )}

        {/* Microsoft Tenant */}
        {client.tenant_microsoft && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 text-sm">☁️</span>
            <div className="text-sm text-gray-700">
              {client.tenant_microsoft}
            </div>
          </div>
        )}
      </div>

      {/* Assigned To */}
      {client.assigned_to_detail && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="text-xs text-gray-500 mb-1">Assigné à</div>
          <div className="text-sm font-medium text-gray-900">
            {client.assigned_to_detail.full_name}
          </div>
          <div className="text-xs text-gray-500">
            {client.assigned_to_detail.email}
          </div>
        </div>
      )}

      {/* Stats */}
      {(client.contacts_count > 0 || client.activities_count > 0) && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-gray-500">Contacts</div>
              <div className="text-lg font-semibold text-gray-900">
                {client.contacts_count || 0}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Activités</div>
              <div className="text-lg font-semibold text-gray-900">
                {client.activities_count || 0}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}