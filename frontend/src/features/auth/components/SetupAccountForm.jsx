import { useState, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { User, Lock, Eye, EyeOff, AlertCircle } from 'lucide-react';

import { Button } from '../../../shared/components/Button';
import { FieldError } from '../../../shared/components/FieldError';
import { Input } from '../../../shared/components/Input';
import { useAuth } from '../hooks/useAuth';

export function SetupAccountForm() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = useMemo(() => searchParams.get('token') ?? '', [searchParams]);
  const { setupMutation } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [apiError, setApiError] = useState(null);

  const { register, handleSubmit, setError, formState: { errors } } = useForm({
    defaultValues: { first_name: '', last_name: '', password: '', password_confirm: '' },
  });

  const FIELDS = ['first_name', 'last_name', 'password', 'password_confirm', 'token'];

  const onSubmit = async (values) => {
    setApiError(null);
    try {
      await setupMutation.mutateAsync({ token, ...values });
      navigate('/app', { replace: true });
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
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1">
          <Input
            label="Prénom"
            icon={User}
            error={!!errors.first_name}
            {...register('first_name')}
          />
          <FieldError message={errors.first_name?.message} />
        </div>
        <div className="flex flex-col gap-1">
          <Input
            label="Nom"
            icon={User}
            error={!!errors.last_name}
            {...register('last_name')}
          />
          <FieldError message={errors.last_name?.message} />
        </div>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-sm font-semibold text-gray-700" htmlFor="password">
          Mot de passe
        </label>
        <div className="relative">
          <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
          <input
            id="password"
            type={showPassword ? 'text' : 'password'}
            autoComplete="new-password"
            className={`border ${errors.password ? 'border-red-400 focus:ring-red-400' : 'border-gray-300 focus:ring-sky-400 focus:border-sky-400'} rounded-lg pl-9 pr-10 py-2.5 text-sm w-full focus:outline-none focus:ring-2 transition-colors`}
            {...register('password', { required: 'Le mot de passe est requis.' })}
          />
          <button type="button" tabIndex={-1}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
            onClick={() => setShowPassword((v) => !v)}>
            {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
          </button>
        </div>
        <FieldError message={errors.password?.message} />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-sm font-semibold text-gray-700" htmlFor="password_confirm">
          Confirmer le mot de passe
        </label>
        <div className="relative">
          <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
          <input
            id="password_confirm"
            type={showConfirm ? 'text' : 'password'}
            autoComplete="new-password"
            className={`border ${errors.password_confirm ? 'border-red-400 focus:ring-red-400' : 'border-gray-300 focus:ring-sky-400 focus:border-sky-400'} rounded-lg pl-9 pr-10 py-2.5 text-sm w-full focus:outline-none focus:ring-2 transition-colors`}
            {...register('password_confirm', { required: 'Veuillez confirmer votre mot de passe.' })}
          />
          <button type="button" tabIndex={-1}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
            onClick={() => setShowConfirm((v) => !v)}>
            {showConfirm ? <EyeOff size={15} /> : <Eye size={15} />}
          </button>
        </div>
        <FieldError message={errors.password_confirm?.message} />
      </div>

      {apiError && (
        <div className="flex items-start gap-2.5 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertCircle size={15} className="shrink-0 mt-0.5" />
          <span>{apiError}</span>
        </div>
      )}

      <Button type="submit" loading={setupMutation.isPending} disabled={!token}>
        Configurer mon compte
      </Button>
    </form>
  );
}
