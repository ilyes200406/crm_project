/**
 * CLIENT FORM COMPONENT
 * 
 * Form for creating/editing clients
 */

import React from 'react';
import { useForm } from 'react-hook-form';

import { Input, FieldError } from '../../../shared/components';

// Industry choices (matching backend)
const INDUSTRY_CHOICES = [
  { value: 'IT', label: "Technologies de l'information" },
  { value: 'TELECOM', label: 'Télécommunications' },
  { value: 'FINANCE', label: 'Finance et banque' },
  { value: 'MANUFACTURING', label: 'Industrie manufacturière' },
  { value: 'RETAIL', label: 'Commerce et distribution' },
  { value: 'HEALTHCARE', label: 'Santé' },
  { value: 'EDUCATION', label: 'Éducation' },
  { value: 'GOVERNMENT', label: 'Secteur public' },
  { value: 'ENERGY', label: 'Énergie' },
  { value: 'AGRICULTURE', label: 'Agriculture' },
  { value: 'TOURISM', label: 'Tourisme et hôtellerie' },
  { value: 'TRANSPORT', label: 'Transport et logistique' },
  { value: 'OTHER', label: 'Autre' },
];

/**
 * ClientForm Component
 * 
 * @param {Object} props
 * @param {Object} props.defaultValues - Default form values
 * @param {Function} props.onSubmit - Submit handler
 * @param {boolean} props.isSubmitting - Submitting state
 * @param {Function} props.onCancel - Cancel handler
 */
export function ClientForm({ defaultValues, onSubmit, isSubmitting, onCancel }) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: defaultValues || {
      company_name: '',
      industry: 'OTHER',
      email: '',
      phone: '',
      website: '',
      address: '',
      tenant_microsoft: '',
      notes: '',
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Company Info */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Informations Entreprise
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Company Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Raison sociale *
            </label>
            <Input
              {...register('company_name', {
                required: 'La raison sociale est requise',
              })}
              error={!!errors.company_name}
            />
            {errors.company_name && (
              <FieldError>{errors.company_name.message}</FieldError>
            )}
          </div>

          {/* Industry */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Secteur d'activité *
            </label>
            <select
              {...register('industry', {
                required: "Le secteur d'activité est requis",
              })}
              className={`
                w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500
                ${errors.industry ? 'border-red-500' : 'border-gray-300'}
              `}
            >
              {INDUSTRY_CHOICES.map((choice) => (
                <option key={choice.value} value={choice.value}>
                  {choice.label}
                </option>
              ))}
            </select>
            {errors.industry && (
              <FieldError>{errors.industry.message}</FieldError>
            )}
          </div>
        </div>
      </div>

      {/* Contact Info */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Contact Principal
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email principal *
            </label>
            <Input
              type="email"
              {...register('email', {
                required: "L'email est requis",
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: 'Email invalide',
                },
              })}
              error={!!errors.email}
            />
            {errors.email && <FieldError>{errors.email.message}</FieldError>}
          </div>

          {/* Phone */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Téléphone
            </label>
            <Input type="tel" {...register('phone')} />
          </div>

          {/* Website */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Site web
            </label>
            <Input
              type="url"
              {...register('website', {
                pattern: {
                  value: /^https?:\/\/.+/,
                  message: 'URL invalide (doit commencer par http:// ou https://)',
                },
              })}
              placeholder="https://example.com"
              error={!!errors.website}
            />
            {errors.website && <FieldError>{errors.website.message}</FieldError>}
          </div>

          {/* Microsoft Tenant */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tenant Microsoft
            </label>
            <Input
              {...register('tenant_microsoft')}
              placeholder="nom-entreprise.onmicrosoft.com"
            />
          </div>
        </div>
      </div>

      {/* Address */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Adresse</h3>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Adresse complète
          </label>
          <textarea
            {...register('address')}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="123 Rue Exemple, Tunis 1000, Tunisie"
          />
        </div>
      </div>

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Notes
        </label>
        <textarea
          {...register('notes')}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Notes internes..."
        />
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={onCancel}
          disabled={isSubmitting}
          className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
        >
          Annuler
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {isSubmitting ? 'Enregistrement...' : 'Enregistrer'}
        </button>
      </div>
    </form>
  );
}