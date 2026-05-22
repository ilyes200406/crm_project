import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Inbox, UserCheck, ExternalLink, XCircle, CheckCircle2 } from 'lucide-react';

import { Card, Badge, EmptyState } from '../../../shared/components';
import { useAuth } from '../../auth/hooks/useAuth';
import { leadsApi } from '../api/leadsApi';

const STATUT_CONFIG = {
  NOUVELLE:        { label: 'Nouvelle',         variant: 'blue' },
  PRISE_EN_CHARGE: { label: 'Prise en charge',  variant: 'yellow' },
  CONVERTIE:       { label: 'Convertie',        variant: 'green' },
  ANNULEE:         { label: 'Annulée',          variant: 'red' },
};

export function DemandesListPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [selected, setSelected] = useState(null);

  const { data, isLoading } = useQuery({
    queryKey: ['leads'],
    queryFn: () => leadsApi.getAll().then((r) => r.data),
  });

  const prendreEnCharge = useMutation({
    mutationFn: (id) => leadsApi.prendreEnCharge(id),
    onSuccess: () => qc.invalidateQueries(['leads']),
  });

  const annuler = useMutation({
    mutationFn: (id) => leadsApi.annuler(id),
    onSuccess: () => { qc.invalidateQueries(['leads']); setSelected(null); },
  });

  const demandes = data?.results ?? data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center">
            <Inbox size={20} className="text-blue-600" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Demandes clients</h1>
            <p className="text-sm text-gray-500">Prospects ayant soumis une demande via le formulaire public</p>
          </div>
        </div>
      </div>

      <Card>
        {isLoading ? (
          <div className="py-12 text-center text-gray-400">Chargement...</div>
        ) : demandes.length === 0 ? (
          <EmptyState
            title="Aucune demande"
            description="Les nouvelles demandes soumises via le formulaire public apparaîtront ici."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  {['Entreprise', 'Contact', 'Email', 'Produits', 'Statut', 'Date', 'Actions'].map((h) => (
                    <th key={h} className="text-left text-xs font-medium text-gray-500 uppercase tracking-wide px-4 py-3">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {demandes.map((d) => {
                  const cfg = STATUT_CONFIG[d.statut] || { label: d.statut, variant: 'gray' };
                  const isNew = d.statut === 'NOUVELLE';
                  const isMine = d.statut === 'PRISE_EN_CHARGE';
                  return (
                    <tr
                      key={d.id}
                      className="hover:bg-gray-50 cursor-pointer"
                      onClick={() => setSelected(selected?.id === d.id ? null : d)}
                    >
                      <td className="px-4 py-3 font-medium text-gray-900">{d.nom_entreprise}</td>
                      <td className="px-4 py-3 text-gray-600">{d.nom_contact}</td>
                      <td className="px-4 py-3 text-gray-600">{d.email}</td>
                      <td className="px-4 py-3 text-gray-500 max-w-xs truncate">{d.prise_en_charge_par_nom || '—'}</td>
                      <td className="px-4 py-3">
                        <Badge variant={cfg.variant} size="sm">{cfg.label}</Badge>
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {new Date(d.created_at).toLocaleDateString('fr-FR')}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                          {isNew && (
                            <button
                              onClick={() => prendreEnCharge.mutate(d.id)}
                              disabled={prendreEnCharge.isPending}
                              className="flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-800 px-2 py-1 rounded bg-blue-50 hover:bg-blue-100 transition-colors"
                            >
                              <UserCheck size={13} />
                              Prendre en charge
                            </button>
                          )}
                          {isMine && (
                            <button
                              onClick={() => annuler.mutate(d.id)}
                              disabled={annuler.isPending}
                              className="flex items-center gap-1 text-xs font-medium text-red-600 hover:text-red-800 px-2 py-1 rounded bg-red-50 hover:bg-red-100 transition-colors"
                            >
                              <XCircle size={13} />
                              Annuler
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Detail panel */}
      {selected && (
        <Card>
          <div className="p-2 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-900">{selected.nom_entreprise}</h2>
              <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-gray-600">
                <XCircle size={18} />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><span className="text-gray-500">Contact :</span> <span className="text-gray-900">{selected.nom_contact}</span></div>
              <div><span className="text-gray-500">Email :</span> <span className="text-gray-900">{selected.email}</span></div>
              {selected.telephone && (
                <div><span className="text-gray-500">Tél :</span> <span className="text-gray-900">{selected.telephone}</span></div>
              )}
              {selected.prise_en_charge_par_nom && (
                <div><span className="text-gray-500">Assignée à :</span> <span className="text-gray-900">{selected.prise_en_charge_par_nom}</span></div>
              )}
            </div>
            {selected.produits_suggeres && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Produits souhaités</p>
                <p className="text-sm text-gray-700 bg-gray-50 rounded px-3 py-2">{selected.produits_suggeres}</p>
              </div>
            )}
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Message</p>
              <p className="text-sm text-gray-700 bg-gray-50 rounded px-3 py-2 whitespace-pre-wrap">{selected.message}</p>
            </div>
            {selected.statut === 'PRISE_EN_CHARGE' && (
              <div className="flex gap-2 pt-1">
                <a
                  href="/app/ventes/opportunities/new"
                  className="flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:text-blue-800 px-3 py-1.5 rounded bg-blue-50 hover:bg-blue-100 transition-colors"
                >
                  <CheckCircle2 size={14} />
                  Créer l'opportunité
                </a>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
