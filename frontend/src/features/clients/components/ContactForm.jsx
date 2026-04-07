/**
 * CONTACT FORM COMPONENT
 * 
 * Form for creating/editing contacts
 */

import React from 'react';
import { useForm } from 'react-hook-form';

import { Input, FieldError } from '../../../shared/components';

/**
 * ContactForm Component
 * 
 * @param {Object} props
 * @param {Object} props.defaultValues - Default form values
 * @param {Function} props.onSubmit - Submit handler
 * @param {boolean} props.isSubmitting - Submitting state
 * @param {Function} props.onCancel - Cancel handler
 */
export function ContactForm({ defaultValues, onSubmit, isSubmitting, onCancel }) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: defaultValues || {
      first_name: '',
      last_name: '',
      position: '',
      email: '',
      phone: '',
      is_primary: false,
      notes: '',
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Name */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* First Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Prénom *
          </label>
          <Input
            {...register('first_name', {
              required: 'Le prénom est requis',
            })}
            error={!!errors.first_name}
          />
          {errors.first_name && (
            <FieldError>{errors.first_name.message}</FieldError>
          )}
        </div>

        {/* Last Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Nom *
          </label>
          <Input
            {...register('last_name', {
              required: 'Le nom est requis',
            })}
            error={!!errors.last_name}
          />
          {errors.last_name && (
            <FieldError>{errors.last_name.message}</FieldError>
          )}
        </div>
      </div>

      {/* Position */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Poste
        </label>
        <Input
          {...register('position')}
          placeholder="Directeur Commercial, CEO, etc."
        />
      </div>

      {/* Contact Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Email */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Email *
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
      </div>

      {/* Is Primary */}
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          {...register('is_primary')}
          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
        />
        <label className="text-sm font-medium text-gray-700">
          Contact principal
        </label>
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