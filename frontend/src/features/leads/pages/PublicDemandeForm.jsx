import { useState } from 'react';
import { CheckCircle2, Send, Building2, User, Mail, Phone, MessageSquare, Package } from 'lucide-react';

import { leadsApi } from '../api/leadsApi';

const INITIAL = { nom_entreprise: '', nom_contact: '', email: '', telephone: '', message: '', produits_suggeres: '' };

export function PublicDemandeForm() {
  const [form, setForm] = useState(INITIAL);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = () => {
    const e = {};
    if (!form.nom_entreprise.trim()) e.nom_entreprise = "Requis";
    if (!form.nom_contact.trim()) e.nom_contact = "Requis";
    if (!form.email.trim()) e.email = "Requis";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = "Email invalide";
    if (!form.message.trim() || form.message.trim().length < 10)
      e.message = "Le message doit contenir au moins 10 caractères";
    return e;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    setSubmitting(true);
    try {
      await leadsApi.submitPublic(form);
      setSubmitted(true);
    } catch (err) {
      const data = err.response?.data || {};
      if (typeof data === 'object') {
        const mapped = {};
        Object.entries(data).forEach(([k, v]) => { mapped[k] = Array.isArray(v) ? v[0] : v; });
        setErrors(mapped);
      } else {
        setErrors({ non_field: "Une erreur est survenue. Veuillez réessayer." });
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg p-10 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 size={32} className="text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Demande envoyée !</h2>
          <p className="text-gray-600">
            Merci pour votre intérêt. Notre équipe commerciale vous contactera dans les plus brefs délais.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-lg w-full max-w-lg">
        {/* Header */}
        <div className="bg-blue-600 rounded-t-2xl px-8 py-6 text-white">
          <h1 className="text-2xl font-bold">Insomea CRM</h1>
          <p className="text-blue-100 text-sm mt-1">Formulaire de demande — Licences Microsoft</p>
        </div>

        <form onSubmit={handleSubmit} className="px-8 py-6 space-y-5">
          <p className="text-gray-600 text-sm">
            Décrivez vos besoins et notre équipe vous recontactera pour un devis personnalisé.
          </p>

          {errors.non_field && (
            <div className="bg-red-50 text-red-700 text-sm px-4 py-2 rounded-lg border border-red-200">
              {errors.non_field}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <Field
              label="Entreprise *"
              icon={<Building2 size={15} />}
              value={form.nom_entreprise}
              onChange={set('nom_entreprise')}
              error={errors.nom_entreprise}
              placeholder="Nom de l'entreprise"
            />
            <Field
              label="Contact *"
              icon={<User size={15} />}
              value={form.nom_contact}
              onChange={set('nom_contact')}
              error={errors.nom_contact}
              placeholder="Nom et prénom"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Field
              label="Email *"
              icon={<Mail size={15} />}
              type="email"
              value={form.email}
              onChange={set('email')}
              error={errors.email}
              placeholder="contact@entreprise.com"
            />
            <Field
              label="Téléphone"
              icon={<Phone size={15} />}
              type="tel"
              value={form.telephone}
              onChange={set('telephone')}
              error={errors.telephone}
              placeholder="+216 XX XXX XXX"
            />
          </div>

          <Field
            label="Produits souhaités (optionnel)"
            icon={<Package size={15} />}
            value={form.produits_suggeres}
            onChange={set('produits_suggeres')}
            error={errors.produits_suggeres}
            placeholder="Ex : Microsoft 365 Business Premium, 50 licences"
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              <span className="flex items-center gap-1.5">
                <MessageSquare size={15} className="text-gray-400" />
                Message *
              </span>
            </label>
            <textarea
              value={form.message}
              onChange={set('message')}
              rows={4}
              placeholder="Décrivez vos besoins, le nombre d'utilisateurs, votre secteur d'activité..."
              className={`w-full px-3 py-2.5 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none ${
                errors.message ? 'border-red-400 bg-red-50' : 'border-gray-300'
              }`}
            />
            {errors.message && <p className="text-red-600 text-xs mt-1">{errors.message}</p>}
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-semibold py-3 rounded-lg transition-colors"
          >
            <Send size={16} />
            {submitting ? 'Envoi en cours...' : 'Envoyer la demande'}
          </button>
        </form>
      </div>
    </div>
  );
}

function Field({ label, icon, type = 'text', value, onChange, error, placeholder }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1.5">
        <span className="flex items-center gap-1.5">
          <span className="text-gray-400">{icon}</span>
          {label}
        </span>
      </label>
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={`w-full px-3 py-2.5 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          error ? 'border-red-400 bg-red-50' : 'border-gray-300'
        }`}
      />
      {error && <p className="text-red-600 text-xs mt-1">{error}</p>}
    </div>
  );
}
