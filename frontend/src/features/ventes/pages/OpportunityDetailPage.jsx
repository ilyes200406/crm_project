/**
 * OPPORTUNITY DETAIL PAGE
 *
 * Single page that renders FSM-state-specific content.
 * Role (COMMERCIAL / FINANCE / ADMIN) determines which actions are visible.
 */

import { useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

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
    <div className="flex items-center overflow-x-auto pb-1 mb-6">
      {STEPS.map((step, i) => (
        <div key={step.key} className="flex items-center flex-1 min-w-0">
          <div className="flex flex-col items-center flex-1 min-w-0">
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold z-10 shrink-0
                ${i < current  ? 'bg-green-500 text-white'
                : i === current ? 'bg-blue-600 text-white ring-4 ring-blue-100'
                :                 'bg-gray-200 text-gray-500'}`}
            >
              {i < current ? '✓' : i + 1}
            </div>
            <span
              className={`mt-1 text-[10px] font-semibold text-center leading-tight px-1 whitespace-nowrap
                ${i === current ? 'text-blue-600' : 'text-gray-400'}`}
            >
              {step.label}
            </span>
          </div>
          {i < STEPS.length - 1 && (
            <div className={`h-0.5 flex-1 mx-1 shrink-0 ${i < current ? 'bg-green-500' : 'bg-gray-200'}`} />
          )}
        </div>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// SIDEBAR
// ─────────────────────────────────────────────────────────────

function Sidebar({ opportunity }) {
  const iq = opportunity.insomea_quote;
  return (
    <div className="space-y-4">
      {/* Client */}
      <Card>
        <h4 className="text-sm font-bold text-gray-800 mb-3">👤 Client</h4>
        <div className="space-y-2 text-sm">
          <Row label="Société"   value={opportunity.client?.company_name} />
          <Row label="Type"      value={<Badge variant="blue" size="sm">{opportunity.type_display}</Badge>} />
          <Row label="Assigné à" value={opportunity.assigned_to?.full_name || '—'} />
          <Row label="Créé par"  value={opportunity.created_by?.full_name || '—'} />
          <Row label="Créé le"   value={new Date(opportunity.created_at).toLocaleDateString('fr-FR')} />
        </div>
      </Card>

      {/* Financier */}
      {iq && (
        <Card>
          <h4 className="text-sm font-bold text-gray-800 mb-3">💰 Financier</h4>
          <div className="space-y-2 text-sm">
            <Row label="Total achat"   value={`${Number(iq.total_purchase).toFixed(2)} DT`} />
            <Row label="Total vente"   value={<span className="font-bold text-blue-700">{Number(iq.total_sale).toFixed(2)} DT</span>} />
            <Row label="Remise"        value={`${iq.discount_percent || 0}%`} />
            <Row label="Marge"         value={<span className="text-green-600 font-semibold">{Number(iq.margin).toFixed(2)} DT ({Number(iq.margin_percent).toFixed(1)}%)</span>} />
          </div>
        </Card>
      )}

      {/* Notes */}
      {opportunity.notes && (
        <Card>
          <h4 className="text-sm font-bold text-gray-800 mb-2">📝 Notes</h4>
          <p className="text-sm text-gray-600 whitespace-pre-wrap">{opportunity.notes}</p>
        </Card>
      )}
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between items-start gap-2">
      <span className="text-gray-500 shrink-0">{label}</span>
      <span className="text-gray-900 text-right">{value || '—'}</span>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// LINES TABLE (always visible)
// ─────────────────────────────────────────────────────────────

function LinesTable({ lines }) {
  if (!lines?.length) return (
    <p className="text-sm text-gray-400 py-4 text-center">Aucune ligne ajoutée</p>
  );

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 text-xs uppercase tracking-wide text-gray-500">
            <th className="px-3 py-2 text-left">Produit</th>
            <th className="px-3 py-2 text-left">Fournisseur</th>
            <th className="px-3 py-2 text-center">Qté</th>
            <th className="px-3 py-2 text-right">Prix achat unit.</th>
            <th className="px-3 py-2 text-right">Prix vente unit.</th>
            <th className="px-3 py-2 text-center">Statut</th>
          </tr>
        </thead>
        <tbody>
          {lines.map((line) => (
            <tr key={line.id} className="border-t border-gray-100 hover:bg-gray-50">
              <td className="px-3 py-2 font-medium">{line.product?.title || '—'}</td>
              <td className="px-3 py-2 text-gray-500">{line.product?.supplier?.name || '—'}</td>
              <td className="px-3 py-2 text-center">{line.quantity}</td>
              <td className="px-3 py-2 text-right text-gray-500">
                {line.supplier_quote_line?.unit_price_purchase
                  ? `${Number(line.supplier_quote_line.unit_price_purchase).toFixed(2)} DT`
                  : '—'}
              </td>
              <td className="px-3 py-2 text-right">
                {line.insomea_quote_line?.unit_price_sale
                  ? `${Number(line.insomea_quote_line.unit_price_sale).toFixed(2)} DT`
                  : '—'}
              </td>
              <td className="px-3 py-2 text-center">
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
      opportunity: opportunity.id,
      product:     form.product,
      quantity:    Number(form.quantity),
      notes:       form.notes,
    });
    setForm({ product: '', quantity: 1, notes: '' });
  };

  const handleRequest = async () => {
    await requestQuotes.mutateAsync(opportunity.id);
    refetch();
  };

  const lines = opportunity.lines || [];

  return (
    <div className="space-y-4">
      {/* Add line */}
      <Card>
        <h4 className="text-sm font-bold text-gray-800 mb-3">➕ Ajouter une ligne produit</h4>
        <form onSubmit={handleAdd} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label-xs">Produit *</label>
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
              <label className="label-xs">Quantité *</label>
              <input
                type="number" min={1}
                value={form.quantity}
                onChange={(e) => setForm({ ...form, quantity: e.target.value })}
                className="input w-full"
              />
            </div>
          </div>
          <div>
            <label className="label-xs">Notes</label>
            <input
              type="text"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              placeholder="Notes optionnelles..."
              className="input w-full"
            />
          </div>
          <button
            type="submit"
            disabled={!form.product || addLine.isPending}
            className="btn-primary text-sm"
          >
            + Ajouter
          </button>
        </form>
      </Card>

      {/* Lines list with delete */}
      {lines.length > 0 && (
        <Card>
          <div className="space-y-2">
            {lines.map((line) => (
              <div key={line.id} className="flex items-center justify-between p-2 border border-gray-100 rounded-lg">
                <div>
                  <span className="text-sm font-medium">{line.product?.title}</span>
                  <span className="text-xs text-gray-500 ml-2">× {line.quantity}</span>
                  <span className="text-xs text-gray-400 ml-2">{line.product?.supplier?.name}</span>
                </div>
                <button
                  onClick={() => deleteLine.mutateAsync(line.id)}
                  className="text-red-500 hover:text-red-700 text-xs font-medium px-2 py-1"
                >
                  ✕ Supprimer
                </button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Request supplier quotes */}
      {lines.length > 0 && (
        <>
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
            ✅ {lines.length} ligne{lines.length > 1 ? 's' : ''} ajoutée{lines.length > 1 ? 's' : ''}. Envoyez les demandes de devis aux fournisseurs.
          </div>
          <button
            onClick={handleRequest}
            disabled={requestQuotes.isPending}
            className="w-full py-3 bg-amber-500 text-white rounded-lg font-semibold hover:bg-amber-600 disabled:opacity-50"
          >
            📧 {requestQuotes.isPending ? 'Envoi en cours...' : 'Demander devis fournisseurs'}
          </button>
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

  // Separate lines into those with a known product supplier and those without
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
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
        ⏳ Demandes envoyées aux fournisseurs. En attente des devis...
      </div>
    );
  }

  const handleSubmit = async (formData) => {
    await createQuote.mutateAsync(formData);
    refetch();
  };

  return (
    <div className="space-y-4">
      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
        ⏳ Demandes envoyées. Uploadez les devis reçus ci-dessous.
      </div>
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
  const fileRef = useRef();
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
    <Card>
      <h4 className="text-sm font-bold text-gray-800 mb-3 flex items-center gap-2 flex-wrap">
        📤 Devis —{' '}
        {supplier ? (
          <span className="text-blue-600">{supplier.name}</span>
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
        <span className="text-gray-500 font-normal">({lines.length} ligne{lines.length > 1 ? 's' : ''})</span>
      </h4>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label-xs">Fichier PDF *</label>
            <input ref={fileRef} type="file" accept=".pdf" required className="input w-full text-xs" />
          </div>
          <div>
            <label className="label-xs">Référence devis</label>
            <input type="text" value={reference} onChange={(e) => setReference(e.target.value)} className="input w-full" placeholder="ex: REF-2024-001" />
          </div>
        </div>

        <div className="border border-gray-100 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs text-gray-500">Produit</th>
                <th className="px-3 py-2 text-center text-xs text-gray-500">Qté</th>
                <th className="px-3 py-2 text-right text-xs text-gray-500">Prix unit. achat (DT) *</th>
              </tr>
            </thead>
            <tbody>
              {lines.map((line) => (
                <tr key={line.id} className="border-t border-gray-100">
                  <td className="px-3 py-2 font-medium">{line.product?.title}</td>
                  <td className="px-3 py-2 text-center text-gray-500">{line.quantity}</td>
                  <td className="px-3 py-2">
                    <input
                      type="number" min={0} step="0.01" required
                      value={prices[line.id] || ''}
                      onChange={(e) => setPrices({ ...prices, [line.id]: e.target.value })}
                      className="input w-28 ml-auto block text-right"
                      placeholder="0.00"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <button type="submit" disabled={isPending} className="w-full py-2.5 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 text-sm">
          {isPending ? 'Enregistrement...' : '✅ Enregistrer le devis fournisseur'}
        </button>
      </form>
    </Card>
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
    refetch();
  };

  // Live margin preview
  const totalPurchase = lines.reduce((s, l) => s + Number(l.supplier_quote_line?.unit_price_purchase || 0) * l.quantity, 0);
  const totalSale     = lines.reduce((s, l) => s + Number(salePrices[l.id] || 0) * l.quantity, 0);
  const discountAmt   = totalSale * Number(discount) / 100;
  const netSale       = totalSale - discountAmt;
  const margin        = netSale - totalPurchase;

  return (
    <Card>
      <h4 className="text-sm font-bold text-gray-800 mb-3">💰 Créer le devis Insomea — Saisir les prix de vente</h4>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="border border-gray-100 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs text-gray-500">Produit</th>
                <th className="px-3 py-2 text-center text-xs text-gray-500">Qté</th>
                <th className="px-3 py-2 text-right text-xs text-gray-500">Achat unit.</th>
                <th className="px-3 py-2 text-right text-xs text-gray-500">Vente unit. *</th>
                <th className="px-3 py-2 text-right text-xs text-gray-500">Marge</th>
              </tr>
            </thead>
            <tbody>
              {lines.map((line) => {
                const buy  = Number(line.supplier_quote_line?.unit_price_purchase || 0);
                const sell = Number(salePrices[line.id] || 0);
                const marginPct = buy > 0 ? ((sell - buy) / buy * 100).toFixed(1) : '—';
                return (
                  <tr key={line.id} className="border-t border-gray-100">
                    <td className="px-3 py-2 font-medium">{line.product?.title}</td>
                    <td className="px-3 py-2 text-center text-gray-500">{line.quantity}</td>
                    <td className="px-3 py-2 text-right text-gray-500">{buy.toFixed(2)} DT</td>
                    <td className="px-3 py-2">
                      <input
                        type="number" min={0} step="0.01" required
                        value={salePrices[line.id] || ''}
                        onChange={(e) => setSalePrices({ ...salePrices, [line.id]: e.target.value })}
                        className="input w-24 ml-auto block text-right"
                        placeholder="0.00"
                      />
                    </td>
                    <td className={`px-3 py-2 text-right font-semibold ${sell > buy ? 'text-green-600' : 'text-red-500'}`}>
                      {typeof marginPct === 'string' ? marginPct : `${marginPct}%`}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-600 shrink-0">Remise globale (%)</label>
          <input type="number" min={0} max={100} step="0.1" value={discount} onChange={(e) => setDiscount(e.target.value)} className="input w-24" />
        </div>

        {/* Live preview */}
        <div className="grid grid-cols-4 gap-3 p-3 bg-gray-50 rounded-lg text-sm">
          <div className="text-center"><div className="text-xs text-gray-500">Achat</div><div className="font-bold">{totalPurchase.toFixed(2)} DT</div></div>
          <div className="text-center"><div className="text-xs text-gray-500">Vente brut</div><div className="font-bold">{totalSale.toFixed(2)} DT</div></div>
          <div className="text-center"><div className="text-xs text-gray-500">Net vente</div><div className="font-bold text-blue-600">{netSale.toFixed(2)} DT</div></div>
          <div className="text-center"><div className="text-xs text-gray-500">Marge</div><div className={`font-bold ${margin >= 0 ? 'text-green-600' : 'text-red-500'}`}>{margin.toFixed(2)} DT</div></div>
        </div>

        <button type="submit" disabled={createIQ.isPending || !lines.length} className="w-full py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50">
          {createIQ.isPending ? 'Génération du devis...' : '✅ Générer le devis Insomea (PDF auto)'}
        </button>
      </form>
    </Card>
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
    <div className="space-y-4">
      <Card>
        <h4 className="text-sm font-bold text-gray-800 mb-3">📄 Devis Insomea — {iq?.reference}</h4>
        <div className="space-y-2 text-sm mb-4">
          <Row label="Référence"   value={iq?.reference} />
          <Row label="Total vente" value={<span className="font-bold text-blue-700">{Number(iq?.total_sale || 0).toFixed(2)} DT</span>} />
          <Row label="Remise"      value={`${iq?.discount_percent || 0}%`} />
          <Row label="Marge"       value={<span className="text-green-600">{Number(iq?.margin || 0).toFixed(2)} DT</span>} />
        </div>

        {/* PDF actions */}
        <div className="flex gap-2 mb-1">
          {iq?.document_url ? (
            <button
              onClick={() => window.open(iq.document_url, '_blank')}
              className="flex-1 py-2 bg-blue-50 border border-blue-300 text-blue-700 rounded-lg text-sm hover:bg-blue-100"
            >
              👁️ Prévisualiser
            </button>
          ) : (
            <button
              onClick={async () => { await regenPdf.mutateAsync(opportunity.id); refetch(); }}
              disabled={regenPdf.isPending}
              className="flex-1 py-2 bg-orange-50 border border-orange-300 text-orange-700 rounded-lg text-sm hover:bg-orange-100 disabled:opacity-50"
            >
              {regenPdf.isPending ? '⏳ Génération...' : '🔄 Générer le PDF'}
            </button>
          )}
          <button
            onClick={handleDownload}
            disabled={!iq?.document_url}
            className="flex-1 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            ⬇️ Télécharger
          </button>
        </div>
      </Card>

      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        📧 En cliquant ci-dessous, le devis sera envoyé par email à <strong>{opportunity.client?.email || 'client'}</strong> avec le PDF en pièce jointe.
      </div>

      <button
        onClick={async () => { await requestPO.mutateAsync(opportunity.id); refetch(); }}
        disabled={requestPO.isPending}
        className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
      >
        {requestPO.isPending ? 'Envoi...' : '📧 Envoyer au client — Demander BC'}
      </button>

      <button
        onClick={async () => { await rollbackIQ.mutateAsync(opportunity.id); refetch(); }}
        disabled={rollbackIQ.isPending}
        className="w-full py-2 border border-orange-300 text-orange-600 rounded-lg text-sm hover:bg-orange-50 disabled:opacity-50"
      >
        {rollbackIQ.isPending ? 'Retour...' : '✏️ Modifier devis'}
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
    refetch();
  };

  return (
    <div className="space-y-4">
      {/* Insomea quote summary — so commercial can see what was sent */}
      {iq && (
        <Card>
          <h4 className="text-sm font-bold text-gray-800 mb-3">📄 Devis envoyé — {iq.reference}</h4>
          <div className="space-y-2 text-sm mb-3">
            <Row label="Total vente" value={<span className="font-bold text-blue-700">{Number(iq.total_sale || 0).toFixed(2)} DT</span>} />
            <Row label="Remise"      value={`${iq.discount_percent || 0}%`} />
            <Row label="Marge"       value={<span className="text-green-600">{Number(iq.margin || 0).toFixed(2)} DT</span>} />
          </div>
          <div className="flex gap-2 mb-2">
            {iq.document_url && (
              <button
                onClick={() => window.open(iq.document_url, '_blank')}
                className="flex-1 py-2 bg-blue-50 border border-blue-300 text-blue-700 rounded-lg text-sm hover:bg-blue-100"
              >
                👁️ Prévisualiser
              </button>
            )}
            <button onClick={handleDownloadQuote} className="flex-1 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-50">
              ⬇️ Télécharger
            </button>
          </div>
          <button
            onClick={async () => { await rollbackIQ.mutateAsync(opportunity.id); refetch(); }}
            disabled={rollbackIQ.isPending}
            className="w-full py-2 border border-orange-300 text-orange-600 rounded-lg text-sm hover:bg-orange-50 disabled:opacity-50"
          >
            {rollbackIQ.isPending ? 'Retour...' : '✏️ Modifier le devis'}
          </button>
        </Card>
      )}

      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
        ⏳ Devis envoyé au client. En attente du bon de commande signé.
      </div>
      <Card>
        <h4 className="text-sm font-bold text-gray-800 mb-3">📤 Uploader le BC Client reçu</h4>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="label-xs">Numéro BC *</label>
            <input type="text" required value={poNumber} onChange={(e) => setPoNumber(e.target.value)} placeholder="ex: BC-CLIENT-2024-001" className="input w-full" />
          </div>
          <div>
            <label className="label-xs">Fichier PDF signé *</label>
            <input ref={fileRef} type="file" accept=".pdf" required className="input w-full text-xs" />
          </div>
          <button type="submit" disabled={uploadPO.isPending} className="w-full py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 text-sm">
            {uploadPO.isPending ? 'Upload en cours...' : '✅ Uploader BC Client → Notifier Finance'}
          </button>
        </form>
        <p className="text-xs text-gray-400 mt-2 text-center">Le service Finance sera notifié automatiquement.</p>
      </Card>
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
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
        ⏳ BC client reçu. En attente d'approbation Finance.
      </div>
    );
  }

  const handleReject = async () => {
    if (!rejectReason.trim()) return;
    await cancelMutation.mutateAsync({ id: opportunity.id, reason: rejectReason.trim() });
    navigate('/app/ventes/opportunities');
  };

  return (
    <div className="space-y-4">
      {/* Documents to review — Finance only */}
      <Card>
        <h4 className="text-sm font-bold text-gray-800 mb-3">📎 Documents à vérifier</h4>
        <div className="space-y-2">
          {/* Supplier quotes */}
          {(opportunity.supplier_quotes || []).map((sq) => (
            <div key={sq.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg text-sm">
              <span className="text-gray-700 truncate">📋 Devis fournisseur — {sq.reference || sq.supplier?.name || sq.id}</span>
              {sq.document_url && (
                <button
                  onClick={() => window.open(sq.document_url, '_blank')}
                  className="ml-2 shrink-0 px-3 py-1 bg-blue-50 text-blue-600 border border-blue-200 rounded text-xs hover:bg-blue-100"
                >
                  👁️ Voir
                </button>
              )}
            </div>
          ))}
          {/* Insomea quote */}
          {opportunity.insomea_quote && (
            <div className="flex items-center justify-between p-2 bg-gray-50 rounded-lg text-sm">
              <span className="text-gray-700">📄 Devis Insomea — {opportunity.insomea_quote.reference}</span>
              {opportunity.insomea_quote.document_url && (
                <button
                  onClick={() => window.open(opportunity.insomea_quote.document_url, '_blank')}
                  className="ml-2 shrink-0 px-3 py-1 bg-green-50 text-green-600 border border-green-200 rounded text-xs hover:bg-green-100"
                >
                  👁️ Voir
                </button>
              )}
            </div>
          )}
          {/* Client PO */}
          {po && (
            <div className="flex items-center justify-between p-2 bg-gray-50 rounded-lg text-sm">
              <span className="text-gray-700">📤 BC Client — {po.po_number}</span>
              {po.document_url && (
                <button
                  onClick={() => window.open(po.document_url, '_blank')}
                  className="ml-2 shrink-0 px-3 py-1 bg-amber-50 text-amber-600 border border-amber-200 rounded text-xs hover:bg-amber-100"
                >
                  👁️ Voir
                </button>
              )}
            </div>
          )}
        </div>
      </Card>

      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
        ⚠️ Vérifiez les documents ci-dessus avant d'approuver. L'approbation enverra automatiquement les BC Insomea aux fournisseurs par email.
      </div>
      <div className="flex gap-3">
        <button
          onClick={async () => { await approveMutation.mutateAsync(opportunity.id); refetch(); }}
          disabled={approveMutation.isPending}
          className="flex-1 py-3 bg-green-600 text-white rounded-lg font-bold hover:bg-green-700 disabled:opacity-50"
        >
          {approveMutation.isPending ? 'Approbation en cours...' : '✅ Approuver — Envoyer BC Insomea aux fournisseurs'}
        </button>
        <button
          onClick={() => setShowReject(!showReject)}
          className="px-5 py-3 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 font-medium"
        >
          ❌ Rejeter
        </button>
      </div>
      {showReject && (
        <div className="space-y-2 p-4 border border-red-200 bg-red-50 rounded-lg">
          <label className="block text-xs font-semibold text-red-700 uppercase tracking-wide">
            Motif du rejet *
          </label>
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            rows={3}
            placeholder="Expliquez la raison du rejet..."
            className="w-full border border-red-300 bg-white rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-red-500"
          />
          <div className="flex gap-2">
            <button
              onClick={handleReject}
              disabled={!rejectReason.trim() || cancelMutation.isPending}
              className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 disabled:opacity-50"
            >
              {cancelMutation.isPending ? 'Annulation...' : 'Confirmer le rejet'}
            </button>
            <button
              onClick={() => { setShowReject(false); setRejectReason(''); }}
              className="px-4 py-2 border border-gray-300 text-gray-600 rounded-lg text-sm hover:bg-gray-50"
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
    <div className="space-y-4">
      <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-800">
        ✅ Opportunité approuvée — BC Insomea créés et prêts à envoyer.
      </div>

      {pos.length === 0 && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
          ⚠️ Aucun BC Insomea trouvé. Vérifiez que toutes les lignes ont un devis fournisseur.
        </div>
      )}

      {pos.map((po) => (
        <Card key={po.id}>
          <h4 className="text-sm font-bold text-gray-800 mb-2">
            📄 BC — {po.supplier_name || po.supplier?.name}
          </h4>
          <div className="space-y-1 text-sm mb-3">
            <Row label="Référence"   value={po.po_number} />
            <Row label="Lignes"      value={po.lines_count} />
            <Row label="Total achat" value={`${Number(po.total_purchase || 0).toFixed(2)} DT`} />
            <Row label="Créé le"     value={new Date(po.created_at).toLocaleDateString('fr-FR')} />
          </div>
          {po.document_url ? (
            <div className="flex gap-2">
              <button
                onClick={() => window.open(po.document_url, '_blank')}
                className="flex-1 py-2 bg-blue-50 border border-blue-300 text-blue-700 rounded-lg text-sm hover:bg-blue-100"
              >
                👁️ Prévisualiser
              </button>
              <a
                href={po.document_url}
                download
                className="flex-1 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-50 text-center"
              >
                ⬇️ Télécharger
              </a>
            </div>
          ) : (
            <p className="text-xs text-gray-400 italic">PDF en cours de génération...</p>
          )}
        </Card>
      ))}

      {isFinance && pos.length > 0 && (
        <>
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
            ℹ️ Vérifiez les BCs ci-dessus puis envoyez-les aux fournisseurs par email.
          </div>
          <button
            onClick={async () => { await sendPOs.mutateAsync(opportunity.id); refetch(); }}
            disabled={sendPOs.isPending}
            className="w-full py-3 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 disabled:opacity-50"
          >
            {sendPOs.isPending ? 'Envoi en cours...' : '📧 Envoyer les BCs aux fournisseurs'}
          </button>
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
    <div className="space-y-4">
      <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-800">
        ✅ Approuvé. BC Insomea envoyés aux fournisseurs.
      </div>

      {pos.map((po) => (
        <Card key={po.id}>
          <h4 className="text-sm font-bold text-gray-800 mb-2">📬 BC — {po.supplier?.name}</h4>
          <div className="space-y-1 text-sm">
            <Row label="Référence"  value={po.po_number} />
            <Row label="Envoyé le"  value={new Date(po.sent_at).toLocaleDateString('fr-FR')} />
            <Row label="Confirmé"   value={po.confirmed_at ? new Date(po.confirmed_at).toLocaleDateString('fr-FR') : <span className="text-amber-600">En attente</span>} />
          </div>
        </Card>
      ))}

      {isFinance && opportunity.status !== 'INSOMEA_POS_CONFIRMED' && (
        <>
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
            ℹ️ Quand les fournisseurs confirment réception des BC, cliquez ci-dessous pour créer les provisions de provisioning.
          </div>
          <button
            onClick={async () => { await confirmAll.mutateAsync(opportunity.id); refetch(); }}
            disabled={confirmAll.isPending}
            className="w-full py-3 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 disabled:opacity-50"
          >
            {confirmAll.isPending ? 'Confirmation...' : '✅ Confirmer réception BC — Créer provisions'}
          </button>
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
    PROVISIONED:       { text: 'Provisionné',   cls: 'bg-green-100 text-green-700'},
    ERROR:             { text: 'Erreur',         cls: 'bg-red-100 text-red-700'   },
  };

  return (
    <div className="space-y-3">
      <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-center">
        <div className="text-3xl mb-2">✅</div>
        <p className="text-sm font-semibold text-green-800">BC Insomea confirmés — Provisions créées</p>
        <p className="text-xs text-green-600 mt-1">Les techniciens ont été notifiés et peuvent commencer le provisioning.</p>
      </div>

      {provisions.length > 0 && (
        <Card noPadding>
          <div className="px-4 py-3 border-b border-gray-100">
            <h4 className="text-sm font-semibold text-gray-700">🔧 Provisions ({provisions.length})</h4>
          </div>
          <div className="divide-y divide-gray-100">
            {provisions.map((prov) => {
              const line = opportunity.lines.find((l) => l.provision?.id === prov.id);
              const badge = statusLabel[prov.status] || { text: prov.status, cls: 'bg-gray-100 text-gray-600' };
              return (
                <div key={prov.id} className="flex items-center justify-between px-4 py-3">
                  <div>
                    <div className="text-sm font-medium text-gray-800">
                      {line?.product?.title || prov.product_title || '—'}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      Qté: {line?.quantity ?? '—'} ·{' '}
                      <span className={`inline-block px-1.5 py-0.5 rounded text-xs font-medium ${badge.cls}`}>
                        {badge.text}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => navigate(`/app/ventes/provisions/${prov.id}`)}
                    className="ml-4 px-3 py-1 border border-gray-300 text-gray-600 text-xs rounded-lg hover:bg-gray-50 shrink-0"
                  >
                    Voir détails →
                  </button>
                </div>
              );
            })}
          </div>
        </Card>
      )}
    </div>
  );
}

/** CANCELLED */
function CancelledSection({ opportunity }) {
  return (
    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
      <p className="text-sm font-semibold text-red-800">❌ Opportunité annulée</p>
      {opportunity.cancellation_reason && (
        <p className="text-sm text-red-600 mt-1">Raison : {opportunity.cancellation_reason}</p>
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

  const { data: opportunity, isLoading, refetch } = useOpportunity(id);

  const [showCancelModal, setShowCancelModal] = useState(false);
  const [cancelReason, setCancelReason]       = useState('');

  const handleCancel = async () => {
    await cancelMut.mutateAsync({ id, reason: cancelReason });
    setShowCancelModal(false);
    refetch();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        Chargement...
      </div>
    );
  }

  if (!opportunity) {
    return (
      <div className="text-center py-16 text-gray-500">
        <p className="text-lg">Opportunité introuvable.</p>
        <button onClick={() => navigate('/app/ventes/opportunities')} className="mt-3 text-blue-600 text-sm hover:underline">
          ← Retour à la liste
        </button>
      </div>
    );
  }

  const canCancel = ['COMMERCIAL', 'ADMIN'].includes(role) && !['CANCELLED', 'INSOMEA_POS_CONFIRMED'].includes(opportunity.status);

  return (
    <div className="space-y-4">
      {/* Breadcrumb */}
      <div className="text-xs text-gray-500">
        <button onClick={() => navigate('/app/ventes/opportunities')} className="hover:text-blue-600">Opportunités</button>
        {' / '}
        <span className="text-gray-800 font-medium">{opportunity.reference}</span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900">{opportunity.reference} — {opportunity.client?.company_name}</h1>
          <p className="text-sm text-gray-500 mt-0.5">{opportunity.name} · {opportunity.type_display}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <StatusBadge status={opportunity.status} />
          {canCancel && (
            <button onClick={() => setShowCancelModal(true)} className="px-3 py-1.5 text-xs border border-red-300 text-red-600 rounded-lg hover:bg-red-50">
              Annuler
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
        {/* Action panel (2/3) */}
        <div className="lg:col-span-2">
          <StatusSection opportunity={opportunity} role={role} refetch={refetch} navigate={navigate} />
        </div>
        {/* Sidebar (1/3) */}
        <div>
          <Sidebar opportunity={opportunity} />
        </div>
      </div>

      {/* Lines table */}
      {(opportunity.lines || []).length > 0 && (
        <Card>
          <h4 className="text-sm font-bold text-gray-800 mb-3">📦 Lignes ({opportunity.lines.length})</h4>
          <LinesTable lines={opportunity.lines} />
        </Card>
      )}

      {/* Cancel modal */}
      {showCancelModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-sm">
            <h3 className="text-base font-bold text-gray-900 mb-4">Annuler l'opportunité</h3>
            <textarea
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              rows={3}
              placeholder="Raison de l'annulation..."
              className="input w-full mb-4 resize-none"
            />
            <div className="flex gap-3">
              <button onClick={handleCancel} disabled={cancelMut.isPending} className="flex-1 py-2 bg-red-600 text-white rounded-lg font-semibold text-sm hover:bg-red-700 disabled:opacity-50">
                {cancelMut.isPending ? 'Annulation...' : 'Confirmer'}
              </button>
              <button onClick={() => setShowCancelModal(false)} className="flex-1 py-2 border border-gray-300 text-gray-600 rounded-lg text-sm hover:bg-gray-50">
                Retour
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
