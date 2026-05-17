import { useState, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { useSearchParams, Link } from 'react-router-dom';
import { Lock, Eye, EyeOff, AlertCircle } from 'lucide-react';

import { Button } from '../../../shared/components/Button';
import { FieldError } from '../../../shared/components/FieldError';
import { useAuth } from '../hooks/useAuth';

export function ResetPasswordForm() {
  const [searchParams] = useSearchParams();
  const token = useMemo(() => searchParams.get('token') ?? '', [searchParams]);
  const { resetPasswordMutation } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [apiError, setApiError] = useState(null);

  const { register, handleSubmit, setError, reset, formState: { errors } } = useForm({
    defaultValues: { new_password: '', new_password_confirm: '' },
  });

  const FIELDS = ['new_password', 'new_password_confirm'];

  const onSubmit = async (values) => {
    setApiError(null);
    try {
      await resetPasswordMutation.mutateAsync({ token, ...values });
      reset();
    } catch (error) {
      const data = error?.response?.data;
      if (!data) { setApiError('Une erreur est survenue. Veuillez réessayer.'); return; }
      for (const [field, msgs] of Object.entries(data)) {
        const msg = Array.isArray(msgs) ? msgs[0] : msgs;
        if (field === 'non_field_errors' || field === 'detail' || field === 'token') {
          setApiError(typeof msg === 'string' ? msg : 'Une erreur est survenue.');
        } else if (FIELDS.includes(field)) {
          setError(field, { message: typeof msg === 'string' ? msg : String(msg) });
        } else {
          setApiError(typeof msg === 'string' ? msg : 'Une erreur est survenue.');
        }
      }
    }
  };

  return (
    <form className="flex flex-col gap-5" onSubmit={handleSubmit(onSubmit)}>
      <div className="flex flex-col gap-1">
        <label className="text-sm font-semibold text-gray-700" htmlFor="new_password">
          Nouveau mot de passe
        </label>
        <div className="relative">
          <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
          <input
            id="new_password"
            type={showPassword ? 'text' : 'password'}
            autoComplete="new-password"
            className={`border ${errors.new_password ? 'border-red-400 focus:ring-red-400' : 'border-gray-300 focus:ring-sky-400 focus:border-sky-400'} rounded-lg pl-9 pr-10 py-2.5 text-sm w-full focus:outline-none focus:ring-2 transition-colors`}
            {...register('new_password', { required: 'Le mot de passe est requis.' })}
          />
          <button type="button" tabIndex={-1}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
            onClick={() => setShowPassword((v) => !v)}>
            {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
          </button>
        </div>
        <FieldError message={errors.new_password?.message} />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-sm font-semibold text-gray-700" htmlFor="new_password_confirm">
          Confirmer le mot de passe
        </label>
        <div className="relative">
          <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
          <input
            id="new_password_confirm"
            type={showConfirm ? 'text' : 'password'}
            autoComplete="new-password"
            className={`border ${errors.new_password_confirm ? 'border-red-400 focus:ring-red-400' : 'border-gray-300 focus:ring-sky-400 focus:border-sky-400'} rounded-lg pl-9 pr-10 py-2.5 text-sm w-full focus:outline-none focus:ring-2 transition-colors`}
            {...register('new_password_confirm', { required: 'Veuillez confirmer le mot de passe.' })}
          />
          <button type="button" tabIndex={-1}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
            onClick={() => setShowConfirm((v) => !v)}>
            {showConfirm ? <EyeOff size={15} /> : <Eye size={15} />}
          </button>
        </div>
        <FieldError message={errors.new_password_confirm?.message} />
      </div>

      {apiError && (
        <div className="flex items-start gap-2.5 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertCircle size={15} className="shrink-0 mt-0.5" />
          <span>{apiError}</span>
        </div>
      )}

      <Button type="submit" loading={resetPasswordMutation.isPending} disabled={!token}>
        Réinitialiser le mot de passe
      </Button>

      <Link to="/login" className="text-sm text-blue-600 hover:underline text-center">
        Retour à la connexion
      </Link>
    </form>
  );
}
