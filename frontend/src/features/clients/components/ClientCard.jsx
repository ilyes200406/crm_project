import React from 'react';
import { Mail, Phone, Globe, MapPin, Cloud, Users, Activity } from 'lucide-react';
import { Badge } from '../../../shared/components';

export function ClientCard({ client }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-xl font-bold text-gray-900 mb-1">{client.company_name}</h3>
          <div className="text-sm text-gray-500">{client.industry_display || client.industry}</div>
        </div>
        <Badge variant={client.is_active ? 'green' : 'red'}>
          {client.is_active ? 'Actif' : 'Inactif'}
        </Badge>
      </div>

      {/* Contact Info */}
      <div className="space-y-2.5">
        {client.email && (
          <div className="flex items-center gap-2.5">
            <Mail size={14} className="text-gray-400 shrink-0" />
            <a href={`mailto:${client.email}`} className="text-sm text-blue-600 hover:underline truncate">
              {client.email}
            </a>
          </div>
        )}
        {client.phone && (
          <div className="flex items-center gap-2.5">
            <Phone size={14} className="text-gray-400 shrink-0" />
            <a href={`tel:${client.phone}`} className="text-sm text-gray-700">
              {client.phone}
            </a>
          </div>
        )}
        {client.website && (
          <div className="flex items-center gap-2.5">
            <Globe size={14} className="text-gray-400 shrink-0" />
            <a
              href={client.website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:underline truncate"
            >
              {client.website}
            </a>
          </div>
        )}
        {client.address && (
          <div className="flex items-start gap-2.5">
            <MapPin size={14} className="text-gray-400 shrink-0 mt-0.5" />
            <div className="text-sm text-gray-700">{client.address}</div>
          </div>
        )}
        {client.tenant_microsoft && (
          <div className="flex items-center gap-2.5">
            <Cloud size={14} className="text-gray-400 shrink-0" />
            <div className="text-sm text-gray-700">{client.tenant_microsoft}</div>
          </div>
        )}
      </div>

      {/* Assigned To */}
      {client.assigned_to_detail && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="text-xs text-gray-400 mb-1">Assigné à</div>
          <div className="text-sm font-medium text-gray-900">{client.assigned_to_detail.full_name}</div>
          <div className="text-xs text-gray-500">{client.assigned_to_detail.email}</div>
        </div>
      )}

      {/* Stats */}
      {(client.contacts_count > 0 || client.activities_count > 0) && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center gap-2">
              <Users size={13} className="text-gray-400" />
              <div>
                <div className="text-xs text-gray-500">Contacts</div>
                <div className="text-lg font-semibold text-gray-900">{client.contacts_count || 0}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Activity size={13} className="text-gray-400" />
              <div>
                <div className="text-xs text-gray-500">Activités</div>
                <div className="text-lg font-semibold text-gray-900">{client.activities_count || 0}</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
