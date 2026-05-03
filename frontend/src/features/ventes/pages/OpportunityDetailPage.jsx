/**
 * OPPORTUNITY DETAIL PAGE
 *
 * Single page that renders FSM-state-specific content.
 * Role (COMMERCIAL / FINANCE / ADMIN) determines which actions are visible.
 */

import { useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import {
  User,
  Building2,
  DollarSign,
  FileText,
  StickyNote,
  Plus,
  Trash2,
  Send,
  Download,
  Eye,
  Check,
  X,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Package,
  RefreshCw,
  Upload,
  Mail,
  Wrench,
  ChevronRight,
  ArrowLeft,
  Loader2,
  Info,
  TrendingUp,
  FileCheck,
  ClipboardList,
  Banknote,
  ShoppingCart,
  RotateCcw,
  FileUp,
  CircleDot,
} from 'lucide-react';

import { Card, Badge, StatusBadge } from '../../../shared/components';
import { useAuth } from '../../auth/hooks/useAuth';
import { useProducts } from '../../catalogue/hooks/useProducts';
import { useSuppliers } from '../../catalogue/hooks/useSuppliers';
import {
  useOpportunity,
  useRequestSupplierQuotes,
  useCreateInsomeaQuote,
  useRollbackInsomeaQuote,
  useRegenerateQuotePdf,
  useRequestClientPO,
  useUploadClientPO,
  useApproveOpportunity,
  useSendInsomeaPos,
  useConfirmAllPOs,
  useCancelOpportunity,
} from '../hooks/useOpportunities';
import { useAddLine, useDeleteLine } from '../hooks/useOpportunityLines';
import { useCreateSupplierQuote } from '../hooks/useSupplierQuotes';
import { insomeaQuotesApi } from '../api/insomeaQuotesApi';

// ─────────────────────────────────────────────────────────────
// CONSTANTS
// ─────────────────────────────────────────────────────────────

const STEPS = [
  { key: 'DRAFT',                  label: 'Brouillon'       },
  { key: 'SUPPLIER_QUOTE_REQUEST', label: 'Devis Four.'     },
  { key: 'SUPPLIER_QUOTE_RECIEVED',label: 'Devis Reçu'      },
  { key: 'INSOMEA_QUOTE_CREATED',  label: 'Devis Insomea'   },
  { key: 'CLIENT_PO_REQUEST',      label: 'Envoyé Client'   },
  { key: 'CLIENT_PO_RECIEVED',     label: 'BC Client'       },
  { key: 'APPROUVED',              label: 'Approuvé'        },
  { key: 'INSOMEA_POS_SENT',       label: 'BC Insomea'      },
  { key: 'INSOMEA_POS_CONFIRMED',  label: 'Confirmé'        },
];

const STEP_INDEX = Object.fromEntries(STEPS.map((s, i) => [s.key, i]));

// ─────────────────────────────────────────────────────────────
// WORKFLOW INDICATOR
// ─────────────────────────────────────────────────────────────

function WorkflowIndicator({ status }) {
  const current = STEP_INDEX[status] ?? -1;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm overflow-x-auto">
      <div className="flex items-center min-w-max">
        {STEPS.map((step, i) => (
          <div key={step.key} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 transition-all
                  ${i < current
                    ? 'bg-emerald-500 text-white shadow-sm shadow-emerald-200'
                    : i === current
                    ? 'bg-blue-600 text-white ring-4 ring-blue-100 shadow-sm shadow-blue-200'
                    : 'bg-gray-100 text-gray-400 border border-gray-200'
                  }`}
              >
                {i < current ? <Check size={14} strokeWidth={3} /> : <span>{i + 1}</span>}
              </div>
              <span
                className={`mt-1.5 text-[10px] font-semibold text-center leading-tight whitespace-nowrap px-1
                  ${i === current ? 'text-blue-600' : i < current ? 'text-emerald-600' : 'text-gray-400'}`}
              >
                {step.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={`w-8 h-px mx-1 shrink-0 transition-all ${
                  i < current ? 'bg-emerald-400' : 'bg-gray-200'
                }`}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// SHARED UI
// ─────────────────────────────────────────────────────────────

function Row({ label, value }) {
  return (
    <div className="flex justify-between items-start gap-3">
      <span className="text-gray-500 text-xs shrink-0">{label}</span>
      <span className="text-gray-900 text-xs text-right font-medium">{value || '—'}</span>
    </div>
  );
}

function SectionHeader({ icon: Icon, title, subtitle }) {
  return (
    <div className="flex items-center gap-2.5 mb-4">
      <div className="w-7 h-7 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
        <Icon size={14} className="text-blue-600" />
      </div>
      <div>
        <h4 className="text-sm font-semibold text-gray-800 leading-none">{title}</h4>
        {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

function InfoBanner({ variant, icon: Icon, children }) {
  const styles = {
    blue:  'bg-blue-50 border-blue-200 text-blue-800',
    amber: 'bg-amber-50 border-amber-200 text-amber-800',
    green: 'bg-emerald-50 border-emerald-200 text-emerald-800',
    red:   'bg-red-50 border-red-200 text-red-800',
  };
  const iconStyles = {
    blue:  'text-blue-500',
    amber: 'text-amber-500',
    green: 'text-emerald-500',
    red:   'text-red-500',
  };
  return (
    <div className={`flex items-start gap-2.5 px-3.5 py-3 border rounded-xl text-sm ${styles[variant]}`}>
      <Icon size={15} className={`shrink-0 mt-0.5 ${iconStyles[variant]}`} />
      <div className="leading-relaxed">{children}</div>
    </div>
  );
}

function ActionButton({
  onClick,
  type = 'button',
  disabled,
  loading,
  variant = 'primary',
  icon: Icon,
  loadingText,
  children,
  className = '',
  size = 'md',
}) {
  const base = 'inline-flex items-center justify-center gap-2 font-semibold rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed';
  const sizes = { sm: 'px-3 py-1.5 text-xs', md: 'px-4 py-2.5 text-sm', lg: 'px-5 py-3 text-sm' };
  const variants = {
    primary:   'bg-blue-600 text-white hover:bg-blue-700 shadow-sm shadow-blue-200',
    secondary: 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50',
    success:   'bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm shadow-emerald-200',
    danger:    'bg-red-600 text-white hover:bg-red-700 shadow-sm shadow-red-200',
    ghost:     'text-gray-600 hover:bg-gray-100',
  };
  const ButtonIcon = loading ? Loader2 : Icon;
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`${base} ${sizes[size]} ${variants[variant]} ${className}`}
    >
      {ButtonIcon && (
        <ButtonIcon size={size === 'sm' ? 13 : 15} className={loading ? 'animate-spin' : ''} />
      )}
      {loading && loadingText ? loadingText : children}
    </button>
  );
}

// ─────────────────────────────────────────────────────────────
// SIDEBAR
// ─────────────────────────────────────────────────────────────

function Sidebar({ opportunity }) {
  const iq = opportunity.insomea_quote;
  return (
    <div className="space-y-3">
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
        <SectionHeader icon={User} title="Client" />
        <div className="space-y-2.5">
          <Row label="Société"   value={<span className="flex items-center gap-1"><Building2 size={11} className="text-gray-400" />{opportunity.client?.company_name}</span>} />
          <Row label="Type"      value={<Badge variant="blue" size="sm">{opportunity.type_display}</Badge>} />
          <Row label="Assigné à" value={opportunity.assigned_to?.full_name} />
          <Row label="Créé par"  value={opportunity.created_by?.full_name} />
          <Row label="Créé le"   value={new Date(opportunity.created_at).toLocaleDateString('fr-FR')} />
        </div>
      </div>

      {iq && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <SectionHeader icon={DollarSign} title="Financier" />
          <div className="space-y-2.5">
            <Row label="Total achat" value={`${Number(iq.total_purchase).toFixed(2)} DT`} />
            <Row label="Total vente" value={<span className="font-bold text-blue-700">{Number(iq.total_sale).toFixed(2)} DT</span>} />
            <Row label="Remise"      value={`${iq.discount_percent || 0}%`} />
            <Row
              label="Marge"
              value={
                <span className="text-emerald-600 font-semibold">
                  {Number(iq.margin).toFixed(2)} DT
                  <span className="text-gray-400 font-normal ml-1">({Number(iq.margin_percent).toFixed(1)}%)</span>
                </span>
              }
            />
          </div>
        </div>
      )}

      {opportunity.notes && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <SectionHeader icon={StickyNote} title="Notes" />
          <p className="text-xs text-gray-600 whitespace-pre-wrap leading-relaxed">{opportunity.notes}</p>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// LINES TABLE (always visible)
// ─────────────────────────────────────────────────────────────

function LinesTable({ lines }) {
  if (!lines?.length) return (
    <div className="py-8 text-center">
      <Package size={32} className="text-gray-300 mx-auto mb-2" />
      <p className="text-sm text-gray-400">Aucune ligne ajoutée</p>
    </div>
  );

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-100">
            <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Produit</th>
            <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Fournisseur</th>
            <th className="px-3 py-2.5 text-center text-xs font-semibold text-gray-500 uppercase tracking-wide">Qté</th>
            <th className="px-3 py-2.5 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">Prix achat unit.</th>
            <th className="px-3 py-2.5 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">Prix vente unit.</th>
            <th className="px-3 py-2.5 text-center text-xs font-semibold text-gray-500 uppercase tracking-wide">Statut</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {lines.map((line) => (
            <tr key={line.id} className="hover:bg-gray-50/60 transition-colors">
              <td className="px-3 py-2.5 font-medium text-gray-900">{line.product?.title || '—'}</td>
              <td className="px-3 py-2.5 text-gray-500 text-xs">{line.product?.supplier?.name || '—'}</td>
              <td className="px-3 py-2.5 text-center">
                <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 text-gray-700 text-xs font-semibold">
                  {line.quantity}
                </span>
              </td>
              <td className="px-3 py-2.5 text-right text-gray-500 tabular-nums">
                {line.supplier_quote_line?.unit_price_purchase
                  ? `${Number(line.supplier_quote_line.unit_price_purchase).toFixed(2)} DT`
                  : '—'}
              </td>
              <td className="px-3 py-2.5 text-right font-medium tabular-nums">
                {line.insomea_quote_line?.unit_price_sale
                  ? `${Number(line.insomea_quote_line.unit_price_sale).toFixed(2)} DT`
                  : '—'}
              </td>
              <td className="px-3 py-2.5 text-center">
                <StatusBadge status={line.status} size="sm" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// FSM SECTIONS
// ─────────────────────────────────────────────────────────────

/** DRAFT — add / remove lines, then request supplier quotes */
function DraftSection({ opportunity, refetch }) {
  const addLine        = useAddLine(opportunity.id);
  const deleteLine     = useDeleteLine(opportunity.id);
  const requestQuotes  = useRequestSupplierQuotes();

  const { data: productsData } = useProducts({ page_size: 200, is_active: true });
  const products = productsData?.results || [];

  const [form, setForm] = useState({ product: '', quantity: 1, notes: '' });

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!form.product) return;
    await addLine.mutateAsync({
      product:  form.product,
      quantity: Number(form.quantity),
      notes:    form.notes,
    });
    setForm({ product: '', quantity: 1, notes: '' });
  };

  const handleRequest = async () => {
    await requestQuotes.mutateAsync(opportunity.id);
  };

  const lines = opportunity.lines || [];

  return (
    <div className="space-y-3">
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
        <SectionHeader icon={Plus} title="Ajouter une ligne produit" />
        <form onSubmit={handleAdd} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Produit *</label>
              <select
                value={form.product}
                onChange={(e) => setForm({ ...form, product: e.target.value })}
                className="input w-full"
              >
                <option value="">Sélectionner un produit...</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>{p.title} — {p.supplier?.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Quantité *</label>
              <input
                type="number" min={1}
                value={form.quantity}
                onChange={(e) => setForm({ ...form, quantity: e.target.value })}
                className="input w-full"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
            <input
              type="text"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              placeholder="Notes optionnelles..."
              className="input w-full"
            />
          </div>
          <ActionButton
            type="submit"
            disabled={!form.product}
            loading={addLine.isPending}
            loadingText="Ajout..."
            icon={Plus}
            variant="primary"
            size="sm"
          >
            Ajouter la ligne
          </ActionButton>
        </form>
      </div>

      {lines.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm divide-y divide-gray-100 overflow-hidden">
          {lines.map((line) => (
            <div key={line.id} className="flex items-center justify-between px-4 py-3 hover:bg-gray-50/60 transition-colors">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center shrink-0">
                  <Package size={14} className="text-gray-500" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{line.product?.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {line.product?.supplier?.name} · <span className="font-medium">×{line.quantity}</span>
                  </p>
                </div>
              </div>
              <button
                onClick={() => deleteLine.mutateAsync(line.id)}
                className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="Supprimer"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}

      {lines.length > 0 && (
        <>
          <InfoBanner variant="blue" icon={Info}>
            <span className="font-semibold">{lines.length} ligne{lines.length > 1 ? 's' : ''}</span> ajoutée{lines.length > 1 ? 's' : ''}.
            Envoyez les demandes de devis aux fournisseurs pour continuer.
          </InfoBanner>
          <ActionButton
            onClick={handleRequest}
            loading={requestQuotes.isPending}
            loadingText="Envoi en cours..."
            icon={Send}
            variant="primary"
            size="lg"
            className="w-full"
          >
            Demander devis fournisseurs
          </ActionButton>
        </>
      )}
    </div>
  );
}

/** SUPPLIER_QUOTE_REQUEST — upload supplier quote PDFs with prices */
function SupplierQuoteRequestSection({ opportunity, refetch }) {
  const lines = (opportunity.lines || []).filter((l) => l.status === 'SUPPLIER_QUOTE_REQUEST');
  const createQuote = useCreateSupplierQuote(opportunity.id);
  const { data: suppliersData } = useSuppliers({ page_size: 200 });
  const supplierOptions = suppliersData?.results || [];

  const grouped = {};
  const ungroupedLines = [];

  lines.forEach((line) => {
    const sup = line.product?.supplier;
    if (sup) {
      if (!grouped[sup.id]) grouped[sup.id] = { supplier: sup, lines: [] };
      grouped[sup.id].lines.push(line);
    } else {
      ungroupedLines.push(line);
    }
  });

  const groups = Object.values(grouped);

  if (!lines.length) {
    return (
      <InfoBanner variant="amber" icon={Clock}>
        Demandes envoyées aux fournisseurs. En attente des devis...
      </InfoBanner>
    );
  }

  const handleSubmit = async (formData) => {
    await createQuote.mutateAsync(formData);
  };

  return (
    <div className="space-y-3">
      <InfoBanner variant="amber" icon={Clock}>
        Demandes envoyées. Uploadez les devis reçus ci-dessous.
      </InfoBanner>
      {groups.map((group) => (
        <SupplierQuoteForm
          key={group.supplier.id}
          supplier={group.supplier}
          lines={group.lines}
          onSubmit={handleSubmit}
          isPending={createQuote.isPending}
        />
      ))}
      {ungroupedLines.length > 0 && (
        <SupplierQuoteForm
          key="ungrouped"
          supplier={null}
          supplierOptions={supplierOptions}
          lines={ungroupedLines}
          onSubmit={handleSubmit}
          isPending={createQuote.isPending}
        />
      )}
    </div>
  );
}

function SupplierQuoteForm({ supplier, supplierOptions = [], lines, onSubmit, isPending }) {
  const fileRef = useRef(null);
  const [reference, setReference] = useState('');
  const [prices, setPrices] = useState({});
  const [selectedSupplierId, setSelectedSupplierId] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const supplierId = supplier ? supplier.id : selectedSupplierId;
    if (!supplierId) return;

    const fd = new FormData();
    fd.append('supplier_id', supplierId);
    fd.append('reference', reference);
    if (fileRef.current.files[0]) fd.append('document', fileRef.current.files[0]);

    const linesData = lines.map((l) => ({
      line_id:             l.id,
      unit_price_purchase: Number(prices[l.id] || 0),
    }));
    fd.append('lines', JSON.stringify(linesData));

    await onSubmit(fd);
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <div className="flex items-center gap-2.5 mb-4">
        <div className="w-7 h-7 rounded-lg bg-amber-50 flex items-center justify-center shrink-0">
          <FileUp size={14} className="text-amber-600" />
        </div>
        <div className="flex items-center gap-2 flex-wrap min-w-0">
          <span className="text-sm font-semibold text-gray-800">Devis fournisseur —</span>
          {supplier ? (
            <span className="text-sm font-semibold text-blue-600">{supplier.name}</span>
          ) : (
            <select
              value={selectedSupplierId}
              onChange={(e) => setSelectedSupplierId(e.target.value)}
              required
              className="input text-sm"
            >
              <option value="">Sélectionner un fournisseur...</option>
              {supplierOptions.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          )}
          <span className="text-xs text-gray-400 font-normal">({lines.length} ligne{lines.length > 1 ? 's' : ''})</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Fichier PDF *</label>
            <input ref={fileRef} type="file" accept=".pdf" required className="input w-full text-xs" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Référence devis</label>
            <input
              type="text"
              value={reference}
              onChange={(e) => setReference(e.target.value)}
              className="input w-full"
              placeholder="ex: REF-2024-001"
            />
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Produit</th>
                <th className="px-3 py-2.5 text-center text-xs font-semibold text-gray-500 uppercase tracking-wide">Qté</th>
                <th className="px-3 py-2.5 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">Prix unit. achat (DT) *</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {lines.map((line) => (
                <tr key={line.id} className="hover:bg-gray-50/60">
                  <td className="px-3 py-2.5 font-medium text-gray-900">{line.product?.title}</td>
                  <td className="px-3 py-2.5 text-center">
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 text-gray-700 text-xs font-semibold">
                      {line.quantity}
                    </span>
                  </td>
                  <td className="px-3 py-2.5">
                    <input
                      type="number" min={0} step="0.01" required
                      value={prices[line.id] || ''}
                      onChange={(e) => setPrices({ ...prices, [line.id]: e.target.value })}
                      className="input w-28 ml-auto block text-right tabular-nums"
                      placeholder="0.00"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <ActionButton
          type="submit"
          loading={isPending}
          loadingText="Enregistrement..."
          icon={FileCheck}
          variant="success"
          size="md"
          className="w-full"
        >
          Enregistrer le devis fournisseur
        </ActionButton>
        
      </form>
    </div>
  );
}

/** SUPPLIER_QUOTE_RECIEVED — create Insomea Quote */
function SupplierQuoteReceivedSection({ opportunity, refetch }) {
  const createIQ = useCreateInsomeaQuote();
  const lines = (opportunity.lines || []).filter((l) => l.supplier_quote_line);

  const [salePrices, setSalePrices] = useState({});
  const [discount, setDiscount] = useState(0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const linesPricing = lines.map((l) => ({
      line_id:         l.id,
      unit_price_sale: Number(salePrices[l.id] || 0),
    }));
    await createIQ.mutateAsync({
      id:   opportunity.id,
      data: { lines_pricing: linesPricing, discount_percent: Number(discount) },
    });
  };

  const totalPurchase = lines.reduce((s, l) => s + Number(l.supplier_quote_line?.unit_price_purchase || 0) * l.quantity, 0);
  const totalSale     = lines.reduce((s, l) => s + Number(salePrices[l.id] || 0) * l.quantity, 0);
  const discountAmt   = totalSale * Number(discount) / 100;
  const netSale       = totalSale - discountAmt;
  const margin        = netSale - totalPurchase;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <SectionHeader icon={TrendingUp} title="Créer le devis Insomea" subtitle="Saisir les prix de vente" />
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Produit</th>
                <th className="px-3 py-2.5 text-center text-xs font-semibold text-gray-500 uppercase tracking-wide">Qté</th>
                <th className="px-3 py-2.5 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">Achat unit.</th>
                <th className="px-3 py-2.5 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">Vente unit. *</th>
                <th className="px-3 py-2.5 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">Marge</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {lines.map((line) => {
                const buy  = Number(line.supplier_quote_line?.unit_price_purchase || 0);
                const sell = Number(salePrices[line.id] || 0);
                const marginPct = buy > 0 ? ((sell - buy) / buy * 100).toFixed(1) : null;
                const isPositive = sell > buy;
                return (
                  <tr key={line.id} className="hover:bg-gray-50/60">
                    <td className="px-3 py-2.5 font-medium text-gray-900">{line.product?.title}</td>
                    <td className="px-3 py-2.5 text-center">
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 text-gray-700 text-xs font-semibold">
                        {line.quantity}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-right text-gray-500 tabular-nums">{buy.toFixed(2)} DT</td>
                    <td className="px-3 py-2.5">
                      <input
                        type="number" min={0} step="0.01" required
                        value={salePrices[line.id] || ''}
                        onChange={(e) => setSalePrices({ ...salePrices, [line.id]: e.target.value })}
                        className="input w-24 ml-auto block text-right tabular-nums"
                        placeholder="0.00"
                      />
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      {marginPct !== null ? (
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${isPositive ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-600'}`}>
                          {marginPct}%
                        </span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-600 shrink-0 font-medium">Remise globale (%)</label>
          <input
            type="number" min={0} max={100} step="0.1"
            value={discount}
            onChange={(e) => setDiscount(e.target.value)}
            className="input w-24"
          />
        </div>

        <div className="grid grid-cols-4 gap-2">
          {[
            { label: 'Achat',      value: `${totalPurchase.toFixed(2)} DT`, color: 'text-gray-800' },
            { label: 'Vente brut', value: `${totalSale.toFixed(2)} DT`,     color: 'text-gray-800' },
            { label: 'Net vente',  value: `${netSale.toFixed(2)} DT`,       color: 'text-blue-600' },
            { label: 'Marge',      value: `${margin.toFixed(2)} DT`,        color: margin >= 0 ? 'text-emerald-600' : 'text-red-500' },
          ].map((item) => (
            <div key={item.label} className="bg-gray-50 rounded-xl p-3 text-center border border-gray-100">
              <p className="text-xs text-gray-500 mb-1">{item.label}</p>
              <p className={`text-sm font-bold tabular-nums ${item.color}`}>{item.value}</p>
            </div>
          ))}
        </div>

        <ActionButton
          type="submit"
          loading={createIQ.isPending}
          loadingText="Génération du devis..."
          disabled={!lines.length}
          icon={FileText}
          variant="success"
          size="lg"
          className="w-full"
        >
          Générer le devis Insomea (PDF auto)
        </ActionButton>
      </form>
    </div>
  );
}

/** INSOMEA_QUOTE_CREATED — view quote, download PDF, send to client */
function InsomeaQuoteCreatedSection({ opportunity, refetch }) {
  const requestPO   = useRequestClientPO();
  const rollbackIQ  = useRollbackInsomeaQuote();
  const regenPdf    = useRegenerateQuotePdf();
  const iq          = opportunity.insomea_quote;

  const handleDownload = async () => {
    if (!iq) return;
    try {
      const res = await insomeaQuotesApi.download(iq.id);
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url; a.download = `${iq.reference}.pdf`; a.click();
      URL.revokeObjectURL(url);
    } catch {
      // document not yet generated
    }
  };

  return (
    <div className="space-y-3">
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
        <SectionHeader icon={FileText} title={`Devis Insomea — ${iq?.reference}`} />
        <div className="space-y-2.5 mb-4">
          <Row label="Référence"   value={iq?.reference} />
          <Row label="Total vente" value={<span className="font-bold text-blue-700 tabular-nums">{Number(iq?.total_sale || 0).toFixed(2)} DT</span>} />
          <Row label="Remise"      value={`${iq?.discount_percent || 0}%`} />
          <Row label="Marge"       value={<span className="text-emerald-600 font-semibold tabular-nums">{Number(iq?.margin || 0).toFixed(2)} DT</span>} />
        </div>

        <div className="flex gap-2">
          {iq?.document_url ? (
            <button
              onClick={() => window.open(iq.document_url, '_blank')}
              className="flex-1 inline-flex items-center justify-center gap-2 py-2 bg-blue-50 border border-blue-200 text-blue-700 rounded-xl text-sm hover:bg-blue-100 transition-colors font-medium"
            >
              <Eye size={14} /> Prévisualiser
            </button>
          ) : (
            <button
              onClick={async () => { await regenPdf.mutateAsync(opportunity.id); }}
              disabled={regenPdf.isPending}
              className="flex-1 inline-flex items-center justify-center gap-2 py-2 bg-amber-50 border border-amber-200 text-amber-700 rounded-xl text-sm hover:bg-amber-100 transition-colors font-medium disabled:opacity-50"
            >
              {regenPdf.isPending ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              {regenPdf.isPending ? 'Génération...' : 'Générer le PDF'}
            </button>
          )}
          <button
            onClick={handleDownload}
            disabled={!iq?.document_url}
            className="flex-1 inline-flex items-center justify-center gap-2 py-2 border border-gray-200 text-gray-700 rounded-xl text-sm hover:bg-gray-50 transition-colors font-medium disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Download size={14} /> Télécharger
          </button>
        </div>
      </div>

      <InfoBanner variant="blue" icon={Mail}>
        En cliquant ci-dessous, le devis sera envoyé par email à <strong>{opportunity.client?.email || 'client'}</strong> avec le PDF en pièce jointe.
      </InfoBanner>

      <ActionButton
        onClick={async () => { await requestPO.mutateAsync(opportunity.id); }}
        loading={requestPO.isPending}
        loadingText="Envoi..."
        icon={Send}
        variant="primary"
        size="lg"
        className="w-full"
      >
        Envoyer au client — Demander BC
      </ActionButton>

      <button
        onClick={async () => { await rollbackIQ.mutateAsync(opportunity.id); }}
        disabled={rollbackIQ.isPending}
        className="w-full inline-flex items-center justify-center gap-2 py-2.5 border border-gray-300 text-gray-600 rounded-xl text-sm hover:bg-gray-50 transition-colors font-medium disabled:opacity-50"
      >
        {rollbackIQ.isPending ? <Loader2 size={14} className="animate-spin" /> : <RotateCcw size={14} />}
        {rollbackIQ.isPending ? 'Retour...' : 'Modifier le devis'}
      </button>
    </div>
  );
}

/** CLIENT_PO_REQUEST — waiting or upload signed PO */
function ClientPORequestSection({ opportunity, refetch }) {
  const uploadPO   = useUploadClientPO();
  const rollbackIQ = useRollbackInsomeaQuote();
  const fileRef    = useRef();
  const [poNumber, setPoNumber] = useState('');
  const iq         = opportunity.insomea_quote;

  const handleDownloadQuote = async () => {
    if (!iq) return;
    try {
      const res = await insomeaQuotesApi.download(iq.id);
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url; a.download = `${iq.reference}.pdf`; a.click();
      URL.revokeObjectURL(url);
    } catch { /* document not yet generated */ }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData();
    fd.append('po_number', poNumber);
    if (fileRef.current.files[0]) fd.append('document', fileRef.current.files[0]);
    await uploadPO.mutateAsync({ id: opportunity.id, data: fd });
  };

  return (
    <div className="space-y-3">
      {iq && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <SectionHeader icon={FileText} title={`Devis envoyé — ${iq.reference}`} />
          <div className="space-y-2.5 mb-3">
            <Row label="Total vente" value={<span className="font-bold text-blue-700 tabular-nums">{Number(iq.total_sale || 0).toFixed(2)} DT</span>} />
            <Row label="Remise"      value={`${iq.discount_percent || 0}%`} />
            <Row label="Marge"       value={<span className="text-emerald-600 font-semibold tabular-nums">{Number(iq.margin || 0).toFixed(2)} DT</span>} />
          </div>
          <div className="flex gap-2 mb-2">
            {iq.document_url && (
              <button
                onClick={() => window.open(iq.document_url, '_blank')}
                className="flex-1 inline-flex items-center justify-center gap-2 py-2 bg-blue-50 border border-blue-200 text-blue-700 rounded-xl text-sm hover:bg-blue-100 transition-colors font-medium"
              >
                <Eye size={14} /> Prévisualiser
              </button>
            )}
            <button
              onClick={handleDownloadQuote}
              className="flex-1 inline-flex items-center justify-center gap-2 py-2 border border-gray-200 text-gray-700 rounded-xl text-sm hover:bg-gray-50 transition-colors font-medium"
            >
              <Download size={14} /> Télécharger
            </button>
          </div>
          <button
            onClick={async () => { await rollbackIQ.mutateAsync(opportunity.id); }}
            disabled={rollbackIQ.isPending}
            className="w-full inline-flex items-center justify-center gap-2 py-2 border border-amber-200 text-amber-700 rounded-xl text-sm hover:bg-amber-50 transition-colors font-medium disabled:opacity-50"
          >
            {rollbackIQ.isPending ? <Loader2 size={14} className="animate-spin" /> : <RotateCcw size={14} />}
            {rollbackIQ.isPending ? 'Retour...' : 'Modifier le devis'}
          </button>
        </div>
      )}

      <InfoBanner variant="amber" icon={Clock}>
        Devis envoyé au client. En attente du bon de commande signé.
      </InfoBanner>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
        <SectionHeader icon={Upload} title="Uploader le BC Client reçu" />
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Numéro BC *</label>
            <input
              type="text" required
              value={poNumber}
              onChange={(e) => setPoNumber(e.target.value)}
              placeholder="ex: BC-CLIENT-2024-001"
              className="input w-full"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Fichier PDF signé *</label>
            <input ref={fileRef} type="file" accept=".pdf" required className="input w-full text-xs" />
          </div>
          <ActionButton
            type="submit"
            loading={uploadPO.isPending}
            loadingText="Upload en cours..."
            icon={FileCheck}
            variant="success"
            size="md"
            className="w-full"
          >
            Uploader BC Client — Notifier Finance
          </ActionButton>
        </form>
        <p className="text-xs text-gray-400 mt-2.5 text-center">Le service Finance sera notifié automatiquement.</p>
      </div>
    </div>
  );
}

/** CLIENT_PO_RECIEVED — Finance approves, Commercial waits */
function ClientPOReceivedSection({ opportunity, role, refetch }) {
  const navigate        = useNavigate();
  const approveMutation = useApproveOpportunity();
  const cancelMutation  = useCancelOpportunity();
  const [showReject, setShowReject] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const po = opportunity.client_po;

  if (!['FINANCE', 'ADMIN'].includes(role)) {
    return (
      <InfoBanner variant="amber" icon={Clock}>
        BC client reçu. En attente d'approbation Finance.
      </InfoBanner>
    );
  }

  const handleReject = async () => {
    if (!rejectReason.trim()) return;
    await cancelMutation.mutateAsync({ id: opportunity.id, reason: rejectReason.trim() });
    navigate('/app/ventes/opportunities');
  };

  return (
    <div className="space-y-3">
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
        <SectionHeader icon={ClipboardList} title="Documents à vérifier" />
        <div className="space-y-2">
          {(opportunity.supplier_quotes || []).map((sq) => (
            <div key={sq.id} className="flex items-center justify-between p-2.5 bg-gray-50 rounded-xl border border-gray-100 text-sm">
              <div className="flex items-center gap-2 min-w-0">
                <FileText size={13} className="text-gray-400 shrink-0" />
                <span className="text-gray-700 truncate">Devis fournisseur — {sq.reference || sq.supplier?.name || sq.id}</span>
              </div>
              {sq.document_url && (
                <button
                  onClick={() => window.open(sq.document_url, '_blank')}
                  className="ml-2 shrink-0 inline-flex items-center gap-1.5 px-2.5 py-1 bg-blue-50 text-blue-600 border border-blue-200 rounded-lg text-xs hover:bg-blue-100 transition-colors font-medium"
                >
                  <Eye size={11} /> Voir
                </button>
              )}
            </div>
          ))}
          {opportunity.insomea_quote && (
            <div className="flex items-center justify-between p-2.5 bg-gray-50 rounded-xl border border-gray-100 text-sm">
              <div className="flex items-center gap-2">
                <FileText size={13} className="text-gray-400 shrink-0" />
                <span className="text-gray-700">Devis Insomea — {opportunity.insomea_quote.reference}</span>
              </div>
              {opportunity.insomea_quote.document_url && (
                <button
                  onClick={() => window.open(opportunity.insomea_quote.document_url, '_blank')}
                  className="ml-2 shrink-0 inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg text-xs hover:bg-emerald-100 transition-colors font-medium"
                >
                  <Eye size={11} /> Voir
                </button>
              )}
            </div>
          )}
          {po && (
            <div className="flex items-center justify-between p-2.5 bg-gray-50 rounded-xl border border-gray-100 text-sm">
              <div className="flex items-center gap-2">
                <FileCheck size={13} className="text-gray-400 shrink-0" />
                <span className="text-gray-700">BC Client — {po.po_number}</span>
              </div>
              {po.document_url && (
                <button
                  onClick={() => window.open(po.document_url, '_blank')}
                  className="ml-2 shrink-0 inline-flex items-center gap-1.5 px-2.5 py-1 bg-amber-50 text-amber-700 border border-amber-200 rounded-lg text-xs hover:bg-amber-100 transition-colors font-medium"
                >
                  <Eye size={11} /> Voir
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      <InfoBanner variant="amber" icon={AlertTriangle}>
        Vérifiez les documents ci-dessus avant d'approuver. L'approbation enverra automatiquement les BC Insomea aux fournisseurs par email.
      </InfoBanner>

      <div className="flex gap-3">
        <ActionButton
          onClick={async () => { await approveMutation.mutateAsync(opportunity.id); }}
          loading={approveMutation.isPending}
          loadingText="Approbation en cours..."
          icon={CheckCircle}
          variant="success"
          size="lg"
          className="flex-1"
        >
          Approuver — Envoyer BC Insomea
        </ActionButton>
        <button
          onClick={() => setShowReject(!showReject)}
          className="px-5 py-3 border border-red-200 text-red-600 rounded-xl hover:bg-red-50 transition-colors font-semibold text-sm inline-flex items-center gap-2"
        >
          <XCircle size={15} /> Rejeter
        </button>
      </div>

      {showReject && (
        <div className="space-y-3 p-4 border border-red-200 bg-red-50 rounded-xl">
          <label className="block text-xs font-semibold text-red-700 uppercase tracking-wide">
            Motif du rejet *
          </label>
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            rows={3}
            placeholder="Expliquez la raison du rejet..."
            className="w-full border border-red-300 bg-white rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-red-400 focus:border-transparent"
          />
          <div className="flex gap-2">
            <ActionButton
              onClick={handleReject}
              disabled={!rejectReason.trim()}
              loading={cancelMutation.isPending}
              loadingText="Annulation..."
              icon={X}
              variant="danger"
              size="sm"
            >
              Confirmer le rejet
            </ActionButton>
            <button
              onClick={() => { setShowReject(false); setRejectReason(''); }}
              className="px-3 py-1.5 border border-gray-300 text-gray-600 rounded-xl text-xs hover:bg-white transition-colors font-medium"
            >
              Annuler
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/** APPROUVED — Finance reviews created POs then sends them */
function ApprovedSection({ opportunity, role, refetch }) {
  const sendPOs   = useSendInsomeaPos();
  const pos       = opportunity.insomea_pos || [];
  const isFinance = ['FINANCE', 'ADMIN'].includes(role);

  return (
    <div className="space-y-3">
      <InfoBanner variant="green" icon={CheckCircle}>
        Opportunité approuvée — BC Insomea créés et prêts à envoyer.
      </InfoBanner>

      {pos.length === 0 && (
        <InfoBanner variant="amber" icon={AlertTriangle}>
          Aucun BC Insomea trouvé. Vérifiez que toutes les lignes ont un devis fournisseur.
        </InfoBanner>
      )}

      {pos.map((po) => (
        <div key={po.id} className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="flex items-center gap-2.5 mb-3">
            <div className="w-7 h-7 rounded-lg bg-gray-100 flex items-center justify-center shrink-0">
              <Banknote size={14} className="text-gray-600" />
            </div>
            <span className="text-sm font-semibold text-gray-800">BC — {po.supplier_name || po.supplier?.name}</span>
          </div>
          <div className="space-y-2 mb-3">
            <Row label="Référence"   value={po.po_number} />
            <Row label="Lignes"      value={po.lines_count} />
            <Row label="Total achat" value={<span className="tabular-nums">{Number(po.total_purchase || 0).toFixed(2)} DT</span>} />
            <Row label="Créé le"     value={new Date(po.created_at).toLocaleDateString('fr-FR')} />
          </div>
          {po.document_url ? (
            <div className="flex gap-2">
              <button
                onClick={() => window.open(po.document_url, '_blank')}
                className="flex-1 inline-flex items-center justify-center gap-2 py-2 bg-blue-50 border border-blue-200 text-blue-700 rounded-xl text-sm hover:bg-blue-100 transition-colors font-medium"
              >
                <Eye size={14} /> Prévisualiser
              </button>
              <a
                href={po.document_url}
                download
                className="flex-1 inline-flex items-center justify-center gap-2 py-2 border border-gray-200 text-gray-700 rounded-xl text-sm hover:bg-gray-50 transition-colors font-medium"
              >
                <Download size={14} /> Télécharger
              </a>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-xs text-gray-400 italic">
              <Loader2 size={12} className="animate-spin" /> PDF en cours de génération...
            </div>
          )}
        </div>
      ))}

      {isFinance && pos.length > 0 && (
        <>
          <InfoBanner variant="blue" icon={Info}>
            Vérifiez les BCs ci-dessus puis envoyez-les aux fournisseurs par email.
          </InfoBanner>
          <ActionButton
            onClick={async () => { await sendPOs.mutateAsync(opportunity.id); }}
            loading={sendPOs.isPending}
            loadingText="Envoi en cours..."
            icon={Send}
            variant="primary"
            size="lg"
            className="w-full"
          >
            Envoyer les BCs aux fournisseurs
          </ActionButton>
        </>
      )}
    </div>
  );
}

/** INSOMEA_POS_SENT — Finance confirms supplier receipt */
function InsomeaPOsSection({ opportunity, role, refetch }) {
  const confirmAll = useConfirmAllPOs();
  const pos        = opportunity.insomea_pos || [];
  const isFinance  = ['FINANCE', 'ADMIN'].includes(role);

  return (
    <div className="space-y-3">
      <InfoBanner variant="green" icon={CheckCircle}>
        BC Insomea envoyés aux fournisseurs.
      </InfoBanner>

      {pos.map((po) => (
        <div key={po.id} className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="flex items-center gap-2.5 mb-3">
            <div className="w-7 h-7 rounded-lg bg-gray-100 flex items-center justify-center shrink-0">
              <Mail size={14} className="text-gray-600" />
            </div>
            <span className="text-sm font-semibold text-gray-800">BC — {po.supplier?.name}</span>
          </div>
          <div className="space-y-2">
            <Row label="Référence" value={po.po_number} />
            <Row label="Envoyé le" value={new Date(po.sent_at).toLocaleDateString('fr-FR')} />
            <Row
              label="Confirmé"
              value={
                po.confirmed_at
                  ? <span className="text-emerald-600 font-medium">{new Date(po.confirmed_at).toLocaleDateString('fr-FR')}</span>
                  : <span className="inline-flex items-center gap-1 text-amber-600 text-xs font-medium"><Clock size={11} /> En attente</span>
              }
            />
          </div>
        </div>
      ))}

      {isFinance && opportunity.status !== 'INSOMEA_POS_CONFIRMED' && (
        <>
          <InfoBanner variant="blue" icon={Info}>
            Quand les fournisseurs confirment réception des BC, cliquez ci-dessous pour créer les provisions de provisioning.
          </InfoBanner>
          <ActionButton
            onClick={async () => { await confirmAll.mutateAsync(opportunity.id); }}
            loading={confirmAll.isPending}
            loadingText="Confirmation..."
            icon={CheckCircle}
            variant="primary"
            size="lg"
            className="w-full"
          >
            Confirmer réception BC — Créer provisions
          </ActionButton>
        </>
      )}
    </div>
  );
}

/** INSOMEA_POS_CONFIRMED — all done, show inline provisions table */
function ConfirmedSection({ opportunity, navigate }) {
  const provisions = (opportunity.lines || [])
    .map((line) => line.provision)
    .filter(Boolean);

  const statusLabel = {
    WAITING_PROVISION: { text: 'En attente',   cls: 'bg-amber-100 text-amber-700' },
    PROVISIONING:      { text: 'En cours',      cls: 'bg-blue-100 text-blue-700'  },
    PROVISIONED:       { text: 'Provisionné',   cls: 'bg-emerald-100 text-emerald-700' },
    ERROR:             { text: 'Erreur',         cls: 'bg-red-100 text-red-700'   },
  };

  return (
    <div className="space-y-3">
      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5 text-center">
        <div className="w-12 h-12 bg-emerald-500 rounded-full flex items-center justify-center mx-auto mb-3">
          <Check size={24} strokeWidth={3} className="text-white" />
        </div>
        <p className="text-sm font-bold text-emerald-800">BC Insomea confirmés — Provisions créées</p>
        <p className="text-xs text-emerald-600 mt-1 leading-relaxed">Les techniciens ont été notifiés et peuvent commencer le provisioning.</p>
      </div>

      {provisions.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="flex items-center gap-2.5 px-4 py-3 border-b border-gray-100">
            <Wrench size={14} className="text-gray-500" />
            <h4 className="text-sm font-semibold text-gray-700">Provisions ({provisions.length})</h4>
          </div>
          <div className="divide-y divide-gray-100">
            {provisions.map((prov) => {
              const line = opportunity.lines.find((l) => l.provision?.id === prov.id);
              const badge = statusLabel[prov.status] || { text: prov.status, cls: 'bg-gray-100 text-gray-600' };
              return (
                <div key={prov.id} className="flex items-center justify-between px-4 py-3 hover:bg-gray-50/60 transition-colors">
                  <div>
                    <p className="text-sm font-medium text-gray-800">
                      {line?.product?.title || prov.product_title || '—'}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-gray-500">Qté: {line?.quantity ?? '—'}</span>
                      <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${badge.cls}`}>
                        {badge.text}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => navigate(`/app/ventes/provisions/${prov.id}`)}
                    className="ml-4 inline-flex items-center gap-1.5 px-3 py-1.5 border border-gray-200 text-gray-600 text-xs rounded-lg hover:bg-gray-100 transition-colors shrink-0 font-medium"
                  >
                    Voir détails <ChevronRight size={12} />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

/** CANCELLED */
function CancelledSection({ opportunity }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-5">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center shrink-0">
          <XCircle size={16} className="text-red-600" />
        </div>
        <p className="text-sm font-bold text-red-800">Opportunité annulée</p>
      </div>
      {opportunity.cancellation_reason && (
        <p className="text-sm text-red-600 ml-11 leading-relaxed">Raison : {opportunity.cancellation_reason}</p>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// STATUS ROUTER
// ─────────────────────────────────────────────────────────────

function StatusSection({ opportunity, role, refetch, navigate }) {
  const props = { opportunity, role, refetch, navigate };

  switch (opportunity.status) {
    case 'DRAFT':                   return <DraftSection {...props} />;
    case 'SUPPLIER_QUOTE_REQUEST':  return <SupplierQuoteRequestSection {...props} />;
    case 'SUPPLIER_QUOTE_RECIEVED': return <SupplierQuoteReceivedSection {...props} />;
    case 'INSOMEA_QUOTE_CREATED':   return <InsomeaQuoteCreatedSection {...props} />;
    case 'CLIENT_PO_REQUEST':       return <ClientPORequestSection {...props} />;
    case 'CLIENT_PO_RECIEVED':      return <ClientPOReceivedSection {...props} />;
    case 'APPROUVED':                return <ApprovedSection {...props} />;
    case 'INSOMEA_POS_SENT':        return <InsomeaPOsSection {...props} />;
    case 'INSOMEA_POS_CONFIRMED':   return <ConfirmedSection opportunity={opportunity} navigate={navigate} />;
    case 'CANCELLED':               return <CancelledSection opportunity={opportunity} />;
    default:                        return null;
  }
}

// ─────────────────────────────────────────────────────────────
// PAGE
// ─────────────────────────────────────────────────────────────

export function OpportunityDetailPage() {
  const { id }      = useParams();
  const navigate    = useNavigate();
  const { user }    = useAuth();
  const role        = user?.role || 'COMMERCIAL';
  const cancelMut   = useCancelOpportunity();

  const { data: opportunity, isLoading } = useOpportunity(id);

  const [showCancelModal, setShowCancelModal] = useState(false);
  const [cancelReason, setCancelReason]       = useState('');

  const handleCancel = async () => {
    await cancelMut.mutateAsync({ id, reason: cancelReason });
    setShowCancelModal(false);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 gap-3 text-gray-400">
        <Loader2 size={20} className="animate-spin" />
        <span className="text-sm">Chargement...</span>
      </div>
    );
  }

  if (!opportunity) {
    return (
      <div className="text-center py-20">
        <CircleDot size={40} className="text-gray-300 mx-auto mb-3" />
        <p className="text-base font-medium text-gray-600">Opportunité introuvable.</p>
        <button
          onClick={() => navigate('/app/ventes/opportunities')}
          className="mt-3 inline-flex items-center gap-1.5 text-blue-600 text-sm hover:underline"
        >
          <ArrowLeft size={14} /> Retour à la liste
        </button>
      </div>
    );
  }

  const canCancel = ['COMMERCIAL', 'ADMIN'].includes(role) && !['CANCELLED', 'INSOMEA_POS_CONFIRMED'].includes(opportunity.status);

  return (
    <div className="space-y-4 max-w-7xl mx-auto">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-xs text-gray-500">
        <button
          onClick={() => navigate('/app/ventes/opportunities')}
          className="inline-flex items-center gap-1 hover:text-blue-600 transition-colors"
        >
          <ArrowLeft size={12} /> Opportunités
        </button>
        <ChevronRight size={12} className="text-gray-300" />
        <span className="text-gray-800 font-semibold">{opportunity.reference}</span>
      </nav>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900 leading-tight">
            {opportunity.reference}
            <span className="text-gray-400 font-normal mx-2">—</span>
            {opportunity.client?.company_name}
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">{opportunity.name} · {opportunity.type_display}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <StatusBadge status={opportunity.status} />
          {canCancel && (
            <button
              onClick={() => setShowCancelModal(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs border border-red-200 text-red-600 rounded-xl hover:bg-red-50 transition-colors font-medium"
            >
              <X size={12} /> Annuler
            </button>
          )}
        </div>
      </div>

      {/* Workflow indicator */}
      {opportunity.status !== 'CANCELLED' && (
        <WorkflowIndicator status={opportunity.status} />
      )}

      {/* Main layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <StatusSection opportunity={opportunity} role={role} navigate={navigate} />
        </div>
        <div>
          <Sidebar opportunity={opportunity} />
        </div>
      </div>

      {/* Lines table */}
      {(opportunity.lines || []).length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="flex items-center gap-2.5 mb-4">
            <div className="w-7 h-7 rounded-lg bg-gray-100 flex items-center justify-center shrink-0">
              <ShoppingCart size={14} className="text-gray-600" />
            </div>
            <h4 className="text-sm font-semibold text-gray-800">
              Lignes <span className="text-gray-400 font-normal">({opportunity.lines.length})</span>
            </h4>
          </div>
          <LinesTable lines={opportunity.lines} />
        </div>
      )}

      {/* Cancel modal */}
      {showCancelModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-sm border border-gray-200">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 bg-red-100 rounded-xl flex items-center justify-center shrink-0">
                <XCircle size={18} className="text-red-600" />
              </div>
              <h3 className="text-base font-bold text-gray-900">Annuler l'opportunité</h3>
            </div>
            <textarea
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              rows={3}
              placeholder="Raison de l'annulation..."
              className="input w-full mb-4 resize-none"
            />
            <div className="flex gap-3">
              <ActionButton
                onClick={handleCancel}
                loading={cancelMut.isPending}
                loadingText="Annulation..."
                icon={X}
                variant="danger"
                size="md"
                className="flex-1"
              >
                Confirmer
              </ActionButton>
              <button
                onClick={() => setShowCancelModal(false)}
                className="flex-1 py-2.5 border border-gray-300 text-gray-600 rounded-xl text-sm hover:bg-gray-50 transition-colors font-medium"
              >
                Retour
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
