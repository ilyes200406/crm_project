/**
 * CLIENTS LIST PAGE
 * 
 * Page listing all clients with search and filters
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Plus } from 'lucide-react';

import { Card } from '../../../shared/components';
import { ClientsTable } from '../components';
import { useClients } from '../hooks';

export function ClientsListPage() {
  const navigate = useNavigate();

  // State for filters
  const [search, setSearch] = useState('');
  const [industry, setIndustry] = useState('');
  const [isActive, setIsActive] = useState('true');

  // Build query params
  const params = {
    ...(search && { search }),
    ...(industry && { industry }),
    ...(isActive && { is_active: isActive }),
  };

  // Fetch clients
  const { data, isLoading } = useClients(params);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center">
              <Users size={18} className="text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Clients</h1>
              <p className="text-sm text-gray-500">Gérez vos clients et contacts</p>
            </div>
          </div>
        </div>
        <button
          onClick={() => navigate('/app/clients/new')}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm transition-colors"
        >
          <Plus size={15} />
          Nouveau Client
        </button>
      </div>

      {/* Filters */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Recherche
            </label>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher par nom, email, téléphone..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Industry Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Secteur
            </label>
            <select
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Tous</option>
              <option value="IT">Technologies</option>
              <option value="TELECOM">Télécommunications</option>
              <option value="FINANCE">Finance</option>
              <option value="MANUFACTURING">Industrie</option>
              <option value="RETAIL">Commerce</option>
              <option value="HEALTHCARE">Santé</option>
              <option value="EDUCATION">Éducation</option>
              <option value="GOVERNMENT">Secteur public</option>
              <option value="ENERGY">Énergie</option>
              <option value="AGRICULTURE">Agriculture</option>
              <option value="TOURISM">Tourisme</option>
              <option value="TRANSPORT">Transport</option>
              <option value="OTHER">Autre</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Statut
            </label>
            <select
              value={isActive}
              onChange={(e) => setIsActive(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Tous</option>
              <option value="true">Actifs</option>
              <option value="false">Inactifs</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Results Count */}
      {!isLoading && data && (
        <div className="text-sm text-gray-600">
          {data.count || 0} client(s) trouvé(s)
        </div>
      )}

      {/* Clients Table */}
      <Card noPadding>
        <ClientsTable
          clients={data?.results || []}
          loading={isLoading}
        />
      </Card>
    </div>
  );
}