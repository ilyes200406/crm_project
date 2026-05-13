/**
 * PROVISION DETAIL PAGE
 *
 * Accessible by: TECHNICIEN, ADMIN
 *
 * FSM flow:
 *   WAITING → start() → PROVISIONING
 *   PROVISIONING → complete({subscription_number?, start_date, end_date}) → PROVISIONED
 *   PROVISIONING → fail({error_message}) → ERROR
 */

import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';

import { Clock, RefreshCw, XCircle, Info, Play, CheckCircle2, AlertTriangle, ChevronRight } from 'lucide-react';

import { Card, StatusBadge, Badge } from '../../../shared/components';
import { useProvision, useStartProvisioning, useCompleteProvisioning, useFailProvisioning, useRetryProvisioning } from '../hooks';
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

function SectionCard({ title, children }) {
  return (
    <div className="border border-gray-200 rounded-xl p-5 space-y-4">
      <h3 className="font-semibold text-gray-700 text-sm uppercase tracking-wide">{title}</h3>
      {children}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// ACTION PANELS
// ─────────────────────────────────────────────────────────────

function ReadOnlyStatusPanel({ provision }) {
  const labels = {
    WAITING_PROVISION: { Icon: Clock,     text: 'En attente de prise en charge par un technicien.', cls: 'bg-amber-50 border-amber-200 text-amber-800' },
    PROVISIONING:      { Icon: RefreshCw, text: 'Provisioning en cours par le technicien.',         cls: 'bg-blue-50 border-blue-200 text-blue-800' },
    ERROR:             { Icon: XCircle,   text: 'Provisioning en échec. Un technicien doit intervenir.', cls: 'bg-red-50 border-red-200 text-red-800' },
  };
  const info = labels[provision.status] || { Icon: Info, text: provision.status, cls: 'bg-gray-50 border-gray-200 text-gray-700' };
  const StatusIcon = info.Icon;

  return (
    <SectionCard title="Statut">
      <div className={`flex items-start gap-2.5 border rounded-lg p-4 text-sm ${info.cls}`}>
        <StatusIcon size={15} className="shrink-0 mt-0.5" />
        <span>{info.text}</span>
      </div>
      {provision.provisioning_error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700 mt-2">
          {provision.provisioning_error}
        </div>
      )}
    </SectionCard>
  );
}

function WaitingPanel({ provision }) {
  const startMutation = useStartProvisioning();

  return (
    <SectionCard title="Action requise">
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800">
        Cette provision est en attente. Démarrez le provisioning quand vous êtes prêt.
      </div>
      <div className="space-y-2 text-sm">
        <div><span className="text-gray-500">Client :</span> <span className="font-medium">{provision.opportunity_line?.opportunity?.client?.company_name}</span></div>
        <div><span className="text-gray-500">Produit :</span> <span className="font-medium">{provision.opportunity_line?.product?.title}</span></div>
        <div><span className="text-gray-500">Quantité :</span> <span className="font-medium">{provision.opportunity_line?.quantity}</span></div>
        {provision.is_renewal && (
          <div><span className="text-gray-500">Subscription existante :</span> <span className="font-mono font-medium text-purple-700">{provision.subscription?.subscription_number}</span></div>
        )}
      </div>
      <button
        onClick={() => startMutation.mutate(provision.id)}
        disabled={startMutation.isPending}
        className="inline-flex items-center gap-1.5 px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm disabled:opacity-50"
      >
        <Play size={15} className="shrink-0" />
        {startMutation.isPending ? 'Démarrage...' : 'Démarrer le provisioning'}
      </button>
    </SectionCard>
  );
}

function ProvisioningPanel({ provision }) {
  const completeMutation = useCompleteProvisioning();
  const failMutation     = useFailProvisioning();
  const navigate         = useNavigate();

  const isInitial = provision.is_initial;

  const [form, setForm]       = useState({ subscription_number: '', start_date: '', end_date: '' });
  const [errors, setErrors]   = useState({});
  const [showFail, setShowFail] = useState(false);
  const [failReason, setFailReason] = useState('');

  const set = (field) => (e) => setForm((p) => ({ ...p, [field]: e.target.value }));

  const validate = () => {
    const err = {};
    if (isInitial && !form.subscription_number.trim()) err.subscription_number = 'Requis pour provisioning initial';
    if (!form.start_date) err.start_date = 'Date de début requise';
    if (!form.end_date)   err.end_date   = 'Date de fin requise';
    if (form.start_date && form.end_date && form.end_date <= form.start_date)
      err.end_date = 'La date de fin doit être après la date de début';
    return err;
  };

  const handleComplete = async (e) => {
    e.preventDefault();
    const err = validate();
    if (Object.keys(err).length) { setErrors(err); return; }

    const payload = {
      start_date: form.start_date,
      end_date:   form.end_date,
      ...(isInitial && { subscription_number: form.subscription_number.trim() }),
    };

    const result = await completeMutation.mutateAsync({ id: provision.id, data: payload });
    if (result?.data?.subscription) {
      navigate(`/app/ventes/subscriptions/${result.data.subscription.id}`);
    }
  };

  const handleFail = async () => {
    if (!failReason.trim()) return;
    await failMutation.mutateAsync({ id: provision.id, errorMessage: failReason.trim() });
    setShowFail(false);
  };

  return (
    <SectionCard title="Provisioning en cours">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700">
        {isInitial
          ? 'Provisioning initial — saisir le numéro de subscription Microsoft et les dates du terme.'
          : 'Provisioning renouvellement — saisir les nouvelles dates du terme.'}
      </div>

      <form onSubmit={handleComplete} className="space-y-4">
        {/* Subscription number — INITIAL only */}
        {isInitial && (
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
              Numéro de Subscription Microsoft *
            </label>
            <input
              type="text"
              value={form.subscription_number}
              onChange={set('subscription_number')}
              placeholder="ex: MS-XXXX-XXXX-XXXX"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.subscription_number && (
              <p className="text-red-500 text-xs mt-1">{errors.subscription_number}</p>
            )}
          </div>
        )}

        {/* Dates */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
              Date de début *
            </label>
            <input
              type="date"
              value={form.start_date}
              onChange={set('start_date')}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.start_date && <p className="text-red-500 text-xs mt-1">{errors.start_date}</p>}
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
              Date de fin *
            </label>
            <input
              type="date"
              value={form.end_date}
              onChange={set('end_date')}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.end_date && <p className="text-red-500 text-xs mt-1">{errors.end_date}</p>}
          </div>
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={completeMutation.isPending}
            className="inline-flex items-center gap-1.5 px-5 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium text-sm disabled:opacity-50"
          >
            <CheckCircle2 size={15} className="shrink-0" />
            {completeMutation.isPending ? 'En cours...' : 'Marquer comme provisionné'}
          </button>
          <button
            type="button"
            onClick={() => setShowFail(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 text-sm"
          >
            <AlertTriangle size={14} className="shrink-0" />
            Signaler une erreur
          </button>
        </div>
      </form>

      {/* Fail modal */}
      {showFail && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md space-y-4">
            <h3 className="font-semibold text-gray-900">Signaler une erreur</h3>
            <textarea
              value={failReason}
              onChange={(e) => setFailReason(e.target.value)}
              rows={4}
              placeholder="Décrivez l'erreur rencontrée..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-red-500"
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowFail(false)}
                className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Annuler
              </button>
              <button
                onClick={handleFail}
                disabled={!failReason.trim() || failMutation.isPending}
                className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {failMutation.isPending ? 'Envoi...' : 'Confirmer l\'erreur'}
              </button>
            </div>
          </div>
        </div>
      )}
    </SectionCard>
  );
}

function ProvisionedPanel({ provision }) {
  return (
    <SectionCard title="Provisioning complété">
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 space-y-2">
        <p className="flex items-center gap-1.5 text-green-700 font-semibold text-sm"><CheckCircle2 size={15} /> Provisioning réalisé avec succès</p>
        {provision.provisioning_completed_at && (
          <p className="text-green-600 text-xs">
            Complété le {new Date(provision.provisioning_completed_at).toLocaleString('fr-FR')}
          </p>
        )}
        {provision.microsoft_subscription_id && (
          <p className="text-sm text-gray-700">
            <span className="text-gray-500">Subscription ID : </span>
            <span className="font-mono font-medium">{provision.microsoft_subscription_id}</span>
          </p>
        )}
      </div>
      {provision.subscription && (
        <Link
          to={`/app/ventes/subscriptions/${provision.subscription.id}`}
          className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          Voir la subscription →
        </Link>
      )}
    </SectionCard>
  );
}

function ErrorPanel({ provision }) {
  const retryMutation = useRetryProvisioning();

  return (
    <SectionCard title="Erreur de provisioning">
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 space-y-2">
        <p className="flex items-center gap-1.5 text-red-700 font-semibold text-sm"><XCircle size={15} /> Provisioning en échec</p>
        {provision.provisioning_error && (
          <p className="text-red-600 text-sm">{provision.provisioning_error}</p>
        )}
      </div>
      <button
        onClick={() => retryMutation.mutate(provision.id)}
        disabled={retryMutation.isPending}
        className="inline-flex items-center gap-1.5 px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm disabled:opacity-50"
      >
        <RefreshCw size={15} className="shrink-0" />
        {retryMutation.isPending ? 'Relance...' : 'Relancer le provisioning'}
      </button>
    </SectionCard>
  );
}

// ─────────────────────────────────────────────────────────────
// STATUS TIMELINE
// ─────────────────────────────────────────────────────────────

function Timeline({ provision }) {
  const events = [
    { label: 'Créé',         date: provision.created_at,                   done: true },
    { label: 'Démarré',      date: provision.provisioning_started_at,       done: !!provision.provisioning_started_at },
    { label: 'Complété',     date: provision.provisioning_completed_at,     done: provision.status === 'PROVISIONED' },
  ];

  return (
    <div className="space-y-2">
      {events.map((ev, i) => (
        <div key={i} className="flex items-start gap-3">
          <div className={`mt-0.5 w-3 h-3 rounded-full flex-shrink-0 ${ev.done ? 'bg-green-500' : 'bg-gray-200'}`} />
          <div>
            <p className={`text-xs font-medium ${ev.done ? 'text-gray-700' : 'text-gray-400'}`}>{ev.label}</p>
            {ev.date && (
              <p className="text-xs text-gray-400">{new Date(ev.date).toLocaleString('fr-FR')}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// MAIN PAGE
// ─────────────────────────────────────────────────────────────

export function ProvisionDetailPage() {
  const { id }     = useParams();
  const navigate   = useNavigate();
  const { user }   = useAuth();
  const canAct     = ['TECHNICIEN', 'ADMIN'].includes(user?.role);
  const { data: provision, isLoading, isError } = useProvision(id);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (isError || !provision) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-500">Provision introuvable.</p>
        <button onClick={() => navigate('/app/ventes/provisions')} className="mt-4 text-blue-600 hover:underline text-sm">
          ← Retour aux provisions
        </button>
      </div>
    );
  }

  const opp  = provision.opportunity_line?.opportunity;
  const line = provision.opportunity_line;

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="text-xs text-gray-500 flex items-center gap-1">
        {opp && (
          <>
            <button onClick={() => navigate(`/app/ventes/opportunities/${opp.id}`)} className="hover:text-blue-600">
              {opp.reference}
            </button>
            {' / '}
          </>
        )}
        {canAct && (
          <>
            <button onClick={() => navigate('/app/ventes/provisions')} className="hover:text-blue-600">
              Provisions
            </button>
            {' / '}
          </>
        )}
        <span className="text-gray-800 font-medium">
          {line?.product?.title || provision.id}
        </span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {line?.product?.title || 'Provision'}
          </h1>
          <div className="flex items-center gap-3 mt-2">
            <StatusBadge status={provision.status} />
            <Badge variant={provision.is_renewal ? 'purple' : 'blue'} size="sm">
              {provision.is_renewal ? 'Renewal' : 'Initial'}
            </Badge>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="grid grid-cols-3 gap-6">
        {/* Action panel — 2/3 */}
        <div className="col-span-2 space-y-4">
          {provision.status === 'WAITING_PROVISION' && (canAct ? <WaitingPanel provision={provision} /> : <ReadOnlyStatusPanel provision={provision} />)}
          {provision.status === 'PROVISIONING'     && (canAct ? <ProvisioningPanel provision={provision} /> : <ReadOnlyStatusPanel provision={provision} />)}
          {provision.status === 'PROVISIONED'      && <ProvisionedPanel provision={provision} />}
          {provision.status === 'ERROR'            && (canAct ? <ErrorPanel provision={provision} /> : <ReadOnlyStatusPanel provision={provision} />)}

          {/* Line details */}
          {line && (
            <Card>
              <h3 className="font-semibold text-gray-700 text-sm mb-4">Détail de la ligne</h3>
              <dl className="grid grid-cols-2 gap-x-8 gap-y-3">
                <Field label="Produit">{line.product?.title}</Field>
                <Field label="Fournisseur">{line.product?.supplier?.name}</Field>
                <Field label="Quantité">{line.quantity}</Field>
                <Field label="Prix achat unitaire">
                  {line.unit_price_purchase != null
                    ? `${parseFloat(line.unit_price_purchase).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}`
                    : '—'}
                </Field>
                <Field label="Prix vente unitaire">
                  {line.unit_price_sale != null
                    ? `${parseFloat(line.unit_price_sale).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}`
                    : '—'}
                </Field>
              </dl>
            </Card>
          )}
        </div>

        {/* Sidebar — 1/3 */}
        <div className="space-y-4">
          {/* Client & Opportunity */}
          <Card>
            <h3 className="font-semibold text-gray-700 text-sm mb-4">Opportunité</h3>
            <dl className="space-y-3">
              <Field label="Client">{opp?.client?.company_name}</Field>
              <Field label="Référence">
                {opp ? (
                  <Link
                    to={`/app/ventes/opportunities/${opp.id}`}
                    className="text-blue-600 hover:underline font-mono"
                  >
                    {opp.reference}
                  </Link>
                ) : '—'}
              </Field>
              <Field label="Nom opportunité">{opp?.name}</Field>
            </dl>
          </Card>

          {/* Subscription (if exists) */}
          {provision.subscription && (
            <Card>
              <h3 className="font-semibold text-gray-700 text-sm mb-4">Subscription</h3>
              <dl className="space-y-3">
                <Field label="Numéro">
                  <Link
                    to={`/app/ventes/subscriptions/${provision.subscription.id}`}
                    className="text-blue-600 hover:underline font-mono"
                  >
                    {provision.subscription.subscription_number}
                  </Link>
                </Field>
                <Field label="Statut">
                  <StatusBadge status={provision.subscription.status} />
                </Field>
              </dl>
            </Card>
          )}

          {/* Timeline */}
          <Card>
            <h3 className="font-semibold text-gray-700 text-sm mb-4">Historique</h3>
            <Timeline provision={provision} />
          </Card>
        </div>
      </div>
    </div>
  );
}
