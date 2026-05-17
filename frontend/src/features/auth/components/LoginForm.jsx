import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, Eye, EyeOff, AlertCircle } from 'lucide-react';

import { Button } from '../../../shared/components/Button';
import { Input } from '../../../shared/components/Input';
import { FieldError } from '../../../shared/components/FieldError';
import { useAuth } from '../hooks/useAuth';

export function LoginForm() {
  const navigate = useNavigate();
  const { loginMutation } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [apiError, setApiError] = useState(null);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm({
    defaultValues: { email: '', password: '' },
  });

  const onSubmit = async (values) => {
    setApiError(null);
    try {
      await loginMutation.mutateAsync(values);
      navigate('/app', { replace: true });
    } catch (error) {
      const data = error?.response?.data;
      if (!data) { setApiError('Une erreur est survenue. Veuillez réessayer.'); return; }
      for (const [field, msgs] of Object.entries(data)) {
        const msg = Array.isArray(msgs) ? msgs[0] : msgs;
        if (field === 'non_field_errors' || field === 'detail') {
          setApiError(typeof msg === 'string' ? msg : 'Une erreur est survenue.');
        } else if (field === 'email') {
          setError('email', { message: typeof msg === 'string' ? msg : String(msg) });
        } else if (field === 'password') {
          setError('password', { message: typeof msg === 'string' ? msg : String(msg) });
        } else {
          setApiError(typeof msg === 'string' ? msg : 'Une erreur est survenue.');
        }
      }
    }
  };

  return (
    <form className="flex flex-col gap-5" onSubmit={handleSubmit(onSubmit)}>
      <div className="flex flex-col gap-1">
        <Input
          label="Adresse e-mail"
          type="email"
          autoComplete="email"
          icon={Mail}
          error={!!errors.email}
          {...register('email', { required: "L'adresse e-mail est requise." })}
        />
        <FieldError message={errors.email?.message} />
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
            autoComplete="current-password"
            className={`border ${errors.password ? 'border-red-400 focus:ring-red-400' : 'border-gray-300 focus:ring-sky-400 focus:border-sky-400'} rounded-lg pl-9 pr-10 py-2.5 text-sm w-full focus:outline-none focus:ring-2 transition-colors`}
            {...register('password', { required: 'Le mot de passe est requis.' })}
          />
          <button
            type="button"
            tabIndex={-1}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
            onClick={() => setShowPassword((v) => !v)}
          >
            {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
          </button>
        </div>
        <FieldError message={errors.password?.message} />
      </div>

      {apiError && (
        <div className="flex items-start gap-2.5 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertCircle size={15} className="shrink-0 mt-0.5" />
          <span>{apiError}</span>
        </div>
      )}

      <Button type="submit" loading={loginMutation.isPending}>
        Se connecter
      </Button>

      <Link to="/forgot-password" className="text-sm text-blue-600 hover:underline text-center">
        Mot de passe oublié ?
      </Link>
    </form>
  );
}
