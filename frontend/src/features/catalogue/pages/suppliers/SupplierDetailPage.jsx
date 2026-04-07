/**
 * SUPPLIER DETAIL PAGE
 * 
 * Page showing supplier details with tabs (Informations, Produits)
 */

import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

import { Card, EmptyState } from '../../../../shared/components';
import { SupplierCard } from '../../components/suppliers';
import { ProductsTable } from '../../components/products';
import { useSupplier, useSupplierProducts } from '../../hooks';

export function SupplierDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams();

  // Active tab
  const [activeTab, setActiveTab] = useState('info');

  // Fetch supplier
  const { data: supplier, isLoading } = useSupplier(id);

  // Fetch supplier products (only when tab active)
  const { data: productsData, isLoading: productsLoading } = useSupplierProducts(
    id,
    {},
    { enabled: activeTab === 'products' }
  );

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Chargement...</div>
      </div>
    );
  }

  // Not found
  if (!supplier) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-gray-500 mb-4">Fournisseur non trouvé</div>
          <button
            onClick={() => navigate('/app/catalogue/suppliers')}
            className="text-blue-600 hover:text-blue-800"
          >
            ← Retour aux fournisseurs
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <button
          onClick={() => navigate('/app/catalogue/suppliers')}
          className="text-sm text-blue-600 hover:text-blue-800 mb-2"
        >
          ← Retour aux fournisseurs
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {supplier.name}
            </h1>
            {supplier.created_at && (
              <p className="text-sm text-gray-600 mt-1">
                Ajouté {formatDistanceToNow(new Date(supplier.created_at), { 
                  addSuffix: true, 
                  locale: fr 
                })}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('info')}
            className={`
              px-4 py-2 border-b-2 font-medium text-sm transition-colors
              ${activeTab === 'info'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
              }
            `}
          >
            Informations
          </button>
          <button
            onClick={() => setActiveTab('products')}
            className={`
              px-4 py-2 border-b-2 font-medium text-sm transition-colors
              ${activeTab === 'products'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
              }
            `}
          >
            Produits ({productsData?.count || 0})
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'info' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <SupplierCard supplier={supplier} />
          </div>
          <div>
            <Card title="Statistiques">
              <div className="space-y-3">
                <div>
                  <div className="text-sm text-gray-500">Produits</div>
                  <div className="text-2xl font-bold text-gray-900">
                    {productsData?.count || 0}
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}

      {activeTab === 'products' && (
        <div className="space-y-4">
          {/* Results Count */}
          {!productsLoading && productsData && (
            <div className="text-sm text-gray-600">
              {productsData.count || 0} produit(s) de ce fournisseur
            </div>
          )}

          {/* Products Table */}
          <Card noPadding>
            {productsData && productsData.results && productsData.results.length > 0 ? (
              <ProductsTable
                products={productsData.results}
                loading={productsLoading}
              />
            ) : (
              <EmptyState
                icon="📦"
                title="Aucun produit"
                message="Ce fournisseur n'a pas encore de produits enregistrés."
              />
            )}
          </Card>
        </div>
      )}
    </div>
  );
}