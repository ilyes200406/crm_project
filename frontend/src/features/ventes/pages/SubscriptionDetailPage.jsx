/**
 * SUBSCRIPTION DETAIL PAGE
 *
 * Accessible by: All roles
 *
 * Shows subscription info, all terms history, revenue metrics.
 * COMMERCIAL/ADMIN can create a renewal opportunity if status is PENDING_RENEWAL.
 */

import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';

import { Card, StatusBadge, Badge } from '../../../shared/components';
import { useSubscription, useCreateRenewal } from '../hooks';
import { useAuth } from '../../auth/hooks/useAuth';

// ─────────────────────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────────────────────

function Field({ label, children }) {
  return (
    <div>
      <dt className="text-xs font-semibold text-gray-400 uppercase tracking-wide">{label}</dt>
      <dd className="mt-0.5 text-sm text-gray-800">{children || '—'}</dd>
    </div>
  );
}

function fmt(value, currency = true) {
  if (value == null) return '—';
  const n = parseFloat(value);
  if (currency) return n.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' });
  return n.toLocaleString('fr-FR', { maximumFractionDigits: 1 }) + '%';
}

function fmtDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('fr-FR');
}

// ─────────────────────────────────────────────────────────────
// TERMS TABLE
// ─────────────────────────────────────────────────────────────

function TermRow({ term }) {
  const isCurrentClass = term.is_current ? 'bg-green-50' : '';

  return (
    <tr className={`border-b border-gray-100 hover:bg-gray-50 ${isCurrentClass}`}>
      <td className="px-4 py-3 text-sm font-medium text-gray-700 tabular-nums">
        {term.term_number}
        {term.is_current && (
          <span className="ml-2 text-xs text-green-600 font-medium">● actuel</span>
        )}
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">
        {fmtDate(term.start_date)} → {fmtDate(term.end_date)}
        <div className="text-xs text-gray-400">{term.duration_days}j</div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-600 tabular-nums">
        {fmt(term.unit_price_purchase)} / {fmt(term.unit_price_sale)}
      </td>
      <td className="px-4 py-3 text-sm text-gray-600 tabular-nums">
        {fmt(term.total_purchase)} / {fmt(term.total_sale)}
      </td>
      <td className="px-4 py-3">
        <div className="text-sm text-gray-700 tabular-nums">{fmt(term.margin)}</div>
        <div className="text-xs text-gray-400">{fmt(term.margin_percent, false)}</div>
      </td>
      <td className="px-4 py-3 text-xs text-gray-400 font-mono">
        {term.opportunity_reference || '—'}
      </td>
    </tr>
  );
}

function TermsTable({ terms }) {
  if (!terms?.length) {
    return (
      <div className="text-center py-8 text-gray-400 text-sm">Aucun terme enregistré</div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-gray-200 bg-gray-50">
            <th className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">Terme</th>
            <th className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">Période</th>
            <th className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">PU Achat / Vente</th>
            <th className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">Total Achat / Vente</th>
            <th className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">Marge</th>
            <th className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">Opportunité</th>
          </tr>
        </thead>
        <tbody>
          {[...terms].sort((a, b) => b.term_number - a.term_number).map((term) => (
            <TermRow key={term.id} term={term} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// RENEWAL PANEL
// ─────────────────────────────────────────────────────────────

function RenewalPanel({ subscription }) {
  const navigate = useNavigate();
  const createRenewalMutation = useCreateRenewal();
  const [showForm, setShowForm] = useState(false);
  const [notes, setNotes] = useState('');

  const handleCreate = async () => {
    const result = await createRenewalMutation.mutateAsync({
      id: subscription.id,
      data: { ...(notes.trim() && { notes: notes.trim() }) },
    });
    if (result?.data?.opportunity) {
      navigate(`/app/ventes/opportunities/${result.data.opportunity.id}`);
    }
  };

  const daysLeft = subscription.days_until_expiration;

  return (
    <div className="border border-amber-300 bg-amber-50 rounded-xl p-5 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-amber-800 text-sm">🔔 Renouvellement requis</h3>
          {daysLeft != null && (
            <p className="text-amber-700 text-xs mt-0.5">
              Expire dans <span className="font-semibold">{daysLeft} jour{daysLeft !== 1 ? 's' : ''}</span>
            </p>
          )}
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 text-sm font-medium"
        >
          {showForm ? 'Annuler' : '+ Créer opportunité renewal'}
        </button>
      </div>

      {showForm && (
        <div className="space-y-3 pt-2 border-t border-amber-200">
          <div>
            <label className="block text-xs font-semibold text-amber-700 uppercase tracking-wide mb-1">
              Notes (optionnel)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              placeholder="Contexte pour le renewal..."
              className="w-full border border-amber-300 bg-white rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>
          <button
            onClick={handleCreate}
            disabled={createRenewalMutation.isPending}
            className="px-5 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 font-medium text-sm disabled:opacity-50"
          >
            {createRenewalMutation.isPending ? 'Création...' : 'Confirmer et créer →'}
          </button>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// MAIN PAGE
// ─────────────────────────────────────────────────────────────

export function SubscriptionDetailPage() {
  const { id }   = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const { data: subscription, isLoading, isError } = useSubscription(id);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (isError || !subscription) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-500">Subscription introuvable.</p>
        <button onClick={() => navigate('/app/ventes/subscriptions')} className="mt-4 text-blue-600 hover:underline text-sm">
          ← Retour aux subscriptions
        </button>
      </div>
    );
  }

  const canRenew =
    subscription.status === 'PENDING_RENEWAL' &&
    ['COMMERCIAL', 'ADMIN'].includes(user?.role);

  const metrics = subscription.revenue_metrics;

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="text-xs text-gray-500">
        <button onClick={() => navigate('/app/ventes/subscriptions')} className="hover:text-blue-600">
          Subscriptions
        </button>
        {' / '}
        <span className="text-gray-800 font-mono font-medium">{subscription.subscription_number}</span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 font-mono">
            {subscription.subscription_number}
          </h1>
          <div className="flex items-center gap-3 mt-2">
            <StatusBadge status={subscription.status} />
            {subscription.is_expiring_soon && (
              <Badge variant="yellow" size="sm">Expire bientôt</Badge>
            )}
            {subscription.auto_renew && (
              <Badge variant="green" size="sm">Auto-renew</Badge>
            )}
          </div>
        </div>
      </div>

      {/* Renewal banner */}
      {canRenew && <RenewalPanel subscription={subscription} />}

      {/* Content */}
      <div className="grid grid-cols-3 gap-6">
        {/* Main — terms table */}
        <div className="col-span-2 space-y-4">
          <Card noPadding>
            <div className="px-5 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-800">Historique des termes</h2>
            </div>
            <TermsTable terms={subscription.terms} />
          </Card>

          {/* Provisions */}
          {subscription.provisions?.length > 0 && (
            <Card noPadding>
              <div className="px-5 py-4 border-b border-gray-100">
                <h2 className="font-semibold text-gray-800">Provisions liées</h2>
              </div>
              <div className="divide-y divide-gray-100">
                {subscription.provisions.map((prov) => (
                  <Link
                    key={prov.id}
                    to={`/app/ventes/provisions/${prov.id}`}
                    className="flex items-center justify-between px-5 py-3 hover:bg-gray-50"
                  >
                    <div className="text-sm text-gray-700">
                      {new Date(prov.created_at).toLocaleDateString('fr-FR')}
                      <span className="ml-2 text-gray-400 text-xs">
                        {prov.is_renewal ? 'Renewal' : 'Initial'}
                      </span>
                    </div>
                    <StatusBadge status={prov.status} />
                  </Link>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Subscription info */}
          <Card>
            <h3 className="font-semibold text-gray-700 text-sm mb-4">Informations</h3>
            <dl className="space-y-3">
              <Field label="Client">
                {subscription.client?.id ? (
                  <Link to={`/app/clients/${subscription.client.id}`} className="text-blue-600 hover:underline">
                    {subscription.client.company_name}
                  </Link>
                ) : subscription.client?.company_name || '—'}
              </Field>
              <Field label="Produit">
                {subscription.product?.id ? (
                  <Link to={`/app/catalogue/products/${subscription.product.id}`} className="text-blue-600 hover:underline">
                    {subscription.product.title}
                  </Link>
                ) : subscription.product?.title || '—'}
              </Field>
              <Field label="Quantité">{subscription.quantity}</Field>
              <Field label="Cycle de facturation">{subscription.billing_cycle_display}</Field>
              <Field label="Terme en cours">
                {subscription.current_term_start && subscription.current_term_end
                  ? `${fmtDate(subscription.current_term_start)} → ${fmtDate(subscription.current_term_end)}`
                  : '—'}
              </Field>
              <Field label="Jours restants">
                {subscription.days_until_expiration != null
                  ? `${subscription.days_until_expiration} jour${subscription.days_until_expiration !== 1 ? 's' : ''}`
                  : '—'}
              </Field>
            </dl>
          </Card>

          {/* Revenue metrics */}
          {metrics && (
            <Card>
              <h3 className="font-semibold text-gray-700 text-sm mb-4">Métriques</h3>
              <dl className="space-y-3">
                <Field label="Total achat">{fmt(metrics.total_purchase)}</Field>
                <Field label="Total vente">{fmt(metrics.total_sale)}</Field>
                <Field label="Marge totale">{fmt(metrics.total_margin)}</Field>
                <Field label="Marge %">
                  {metrics.avg_margin_percent != null
                    ? `${parseFloat(metrics.avg_margin_percent).toFixed(1)}%`
                    : '—'}
                </Field>
                <Field label="Nb termes">{metrics.terms_count ?? '—'}</Field>
              </dl>
            </Card>
          )}

          {/* Current term detail */}
          {subscription.current_term && (
            <Card>
              <h3 className="font-semibold text-gray-700 text-sm mb-4">Terme actuel</h3>
              <dl className="space-y-3">
                <Field label="PU Achat">{fmt(subscription.current_term.unit_price_purchase)}</Field>
                <Field label="PU Vente">{fmt(subscription.current_term.unit_price_sale)}</Field>
                <Field label="Total achat">{fmt(subscription.current_term.total_purchase)}</Field>
                <Field label="Total vente">{fmt(subscription.current_term.total_sale)}</Field>
                <Field label="Marge">{fmt(subscription.current_term.margin)}</Field>
              </dl>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
