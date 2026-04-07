/**
 * PRODUCT DETAIL PAGE
 * 
 * Page showing product details with supplier link
 */

import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

import { Card, Badge } from '../../../../shared/components';
import { ProductCard } from '../../components/products';
import { useProduct } from '../../hooks';

export function ProductDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams();

  // Active tab
  const [activeTab, setActiveTab] = useState('info');

  // Fetch product
  const { data: product, isLoading } = useProduct(id);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Chargement...</div>
      </div>
    );
  }

  // Not found
  if (!product) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-gray-500 mb-4">Produit non trouvé</div>
          <button
            onClick={() => navigate('/app/catalogue')}
            className="text-blue-600 hover:text-blue-800"
          >
            ← Retour au catalogue
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
          onClick={() => navigate('/app/catalogue')}
          className="text-sm text-blue-600 hover:text-blue-800 mb-2"
        >
          ← Retour au catalogue
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {product.title}
              {product.version && (
                <span className="ml-2 text-xl font-normal text-gray-600">
                  {product.version}
                </span>
              )}
            </h1>
            {product.created_at && (
              <p className="text-sm text-gray-600 mt-1">
                Ajouté {formatDistanceToNow(new Date(product.created_at), { 
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
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'info' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ProductCard product={product} />
          </div>
          <div className="space-y-4">
            {/* Status */}
            <Card title="Statut">
              <div className="space-y-3">
                <div>
                  <div className="text-sm text-gray-500 mb-1">Disponibilité</div>
                  <Badge variant={product.is_active ? 'green' : 'red'}>
                    {product.is_active ? 'Actif' : 'Inactif'}
                  </Badge>
                </div>
                {product.is_deprecated && (
                  <div>
                    <div className="text-sm text-gray-500 mb-1">État</div>
                    <Badge variant="yellow">
                      Obsolète
                    </Badge>
                  </div>
                )}
              </div>
            </Card>

            {/* Supplier Link */}
            {product.supplier && (
              <Card title="Fournisseur">
                <button
                  onClick={() => navigate(`/app/catalogue/suppliers/${product.supplier.id}`)}
                  className="w-full text-left p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors group"
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
                    <div className="text-gray-400 group-hover:text-blue-600 text-xl">
                      →
                    </div>
                  </div>
                </button>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}